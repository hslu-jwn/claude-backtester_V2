"""Stationarity / mean-reversion diagnostics of the price series (research only).
Spec: ROADMAP.md > 11.11; knowledge/ideas.md T-11 (Chan, *Algorithmic Trading* ch.2).

All statistics run on the LOG close of closed bars. Returns are bar-to-bar log returns of the
continuous series of existing bars, so a weekend, a holiday or a missing bar is one ordinary
return (the same choice as the noise study, `analytics/noise.py`); only the time-of-day part
needs real 5-minute returns and drops every return whose previous bar is not exactly 5
minutes earlier.

  * `adf`: Augmented Dickey-Fuller with a constant and `adf_lags` lags,
    dy_t = a + lam y_(t-1) + b dy_(t-1) + e; ADF stat = t of lam (p-value: MacKinnon 1994
    response surface, constant case); half-life = -ln 2 / lam in bars (None if lam >= 0).
  * `hurst`: H from std(y_(t+tau) - y_t) ~ tau^H over tau = 2..100 (log-log slope; 0.5 random walk,
    < 0.5 mean-reverting, > 0.5 trending).
  * `variance_ratio`: Lo-MacKinlay VR(q) (unbiased, overlapping) with the
    heteroskedasticity-robust z.
  * `lag_corr`: correlation of the past k-bar return with the next h-bar return on
    NON-overlapping pairs (blocks of k + h bars, so pairs = N // (k + h)); t = c sqrt(n-2) / sqrt(1-c^2).
  * `time_of_day_rows`: per 30-minute UTC bucket the mean 5-minute return, its t and the
    first-order autocorrelation of the 5-minute returns inside the bucket. The 2015-2018
    "US-only DST" weeks (second Sunday of March to the last Sunday of March, last Sunday of
    October to the first Sunday of November) are dropped, histdata is one hour late there
    (ROADMAP 13.12).
  * `random_walk`: seeded reference with the same length and per-bar volatility.
  * `find_findings`: Benjamini-Hochberg per family (every statistic type is one family; the
    cells are the whole-period cells of all symbols x timeframes x parameters of that type), then
    the same sign in both halves and at least `min_siblings` symbols of a sibling group (the
    symbol itself plus siblings whose whole-period value has the same sign). Hurst has no
    p-value and is only reported.

Student-t and normal p-values are computed here (no scipy); numpy only.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

EPOCH = date(1970, 1, 1)
SECONDS_PER_DAY = 86_400
PERIODS = ("whole", "first_half", "second_half")

# MacKinnon (1994) p-value approximation, constant-only case, one variable (as statsmodels).
_TAU_SMALL = (2.1659, 1.4412, 0.038269)  # polynomial in the stat for stat <= _TAU_STAR
_TAU_LARGE = (1.7339, 0.93202, -0.12745, -0.010368)
_TAU_STAR = -1.61
_TAU_MIN = -18.83
_TAU_MAX = 2.74


@dataclass(frozen=True)
class StationarityConfig:
    adf_lags: int = 1
    adf_min_obs: int = 30  # regression rows needed
    hurst_min_lag: int = 2
    hurst_max_lag: int = 100
    hurst_min_bars: int = 400
    hurst_min_lags_used: int = 5
    vr_qs: tuple[int, ...] = (2, 5, 10, 20)
    vr_min_returns: int = 100
    lag_ks: tuple[int, ...] = (1, 5, 10, 25, 60, 120, 250)
    min_pairs: int = 30
    bh_q: float = 0.05
    seed: int = 42
    bucket_minutes: int = 30
    bar_seconds: int = 300  # M5 for the time-of-day part
    min_bucket_obs: int = 30
    dst_first_year: int = 2010
    dst_last_year: int = 2018
    symbol_ends: tuple[tuple[str, date], ...] = (("GER40", date(2020, 6, 12)),)  # ROADMAP 13.13
    gap_bars: int = 3  # a return over more than this many bars is a gap (weekend, holiday, hole)
    winsor_sd: float = (
        5.0  # robust variants clip returns at this many robust sd (MAD) around the median
    )
    min_siblings: int = 2  # the symbol itself plus at least one sibling
    sibling_groups: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "fx": ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "EURGBP"),
            "jpy": ("USDJPY", "GBPJPY", "EURJPY"),
            "metals": ("XAUUSD", "XAGUSD"),
            "us_indices": ("NAS100", "US500"),
            "other_indices": ("GER40", "UK100", "JP225", "EU50"),
            "oils": ("USOIL", "UKOIL"),
        }
    )


# --- p-values -------------------------------------------------------------------------------------------


def normal_p_value(z: float) -> float:
    """Two-sided p of a standard normal statistic."""
    return math.erfc(abs(z) / math.sqrt(2))


def _betacf(a: float, b: float, x: float) -> float:
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1) < 3e-14:
            break
    return h


def _betainc(a: float, b: float, x: float) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1 - bt * _betacf(b, a, 1 - x) / b


def t_p_value(t: float, df: float) -> float:
    """Two-sided p of a Student-t statistic."""
    if not math.isfinite(t):
        return 0.0
    return _betainc(df / 2, 0.5, df / (df + t * t))


def mackinnon_p(stat: float) -> float:
    """p-value of an ADF statistic (constant, no trend); left-tail test of a unit root."""
    if stat > _TAU_MAX:
        return 1.0
    if stat < _TAU_MIN:
        return 0.0
    coef = _TAU_SMALL if stat <= _TAU_STAR else _TAU_LARGE
    poly = sum(c * stat**i for i, c in enumerate(coef))
    return 0.5 * math.erfc(-poly / math.sqrt(2))


def benjamini_hochberg(p_values: Sequence[float | None], q: float) -> list[bool]:
    """Benjamini-Hochberg step-up at false discovery rate `q`. Flags aligned to the input;
    None / NaN p-values are never rejected and are not counted."""
    valid = [(p, i) for i, p in enumerate(p_values) if p is not None and not math.isnan(p)]
    valid.sort()
    m = len(valid)
    cut = 0
    for rank, (p, _) in enumerate(valid, start=1):
        if p <= rank / m * q:
            cut = rank
    flags = [False] * len(p_values)
    for _, i in valid[:cut]:
        flags[i] = True
    return flags


# --- the statistics -----------------------------------------------------------------------------------------


def _clean(y) -> np.ndarray:
    a = np.asarray(y, dtype=float)
    return a[np.isfinite(a)]


def adf(y, cfg: StationarityConfig) -> dict | None:
    """{lam, adf_t, p_value, half_life, obs} or None (too short, constant, singular)."""
    y = _clean(y)
    k = cfg.adf_lags
    dy = np.diff(y)
    obs = len(dy) - k
    if obs < max(cfg.adf_min_obs, k + 3):
        return None
    yc = y - y.mean()
    cols = [np.ones(obs), yc[k : k + obs]] + [dy[k - j : k - j + obs] for j in range(1, k + 1)]
    x = np.column_stack(cols)
    target = dy[k:]
    try:
        xtx_inv = np.linalg.inv(x.T @ x)
    except np.linalg.LinAlgError:
        return None
    beta = xtx_inv @ (x.T @ target)
    resid = target - x @ beta
    dof = obs - x.shape[1]
    s2 = float(resid @ resid) / dof
    se = math.sqrt(s2 * xtx_inv[1, 1]) if s2 > 0 and xtx_inv[1, 1] > 0 else 0.0
    if se <= 0 or float(np.ptp(y)) == 0:
        return None
    lam = float(beta[1])
    stat = lam / se
    return {
        "lam": lam,
        "adf_t": stat,
        "p_value": mackinnon_p(stat),
        "half_life": -math.log(2) / lam if lam < 0 else None,
        "obs": obs,
    }


def hurst(y, cfg: StationarityConfig) -> float | None:
    y = _clean(y)
    n = len(y)
    if n < cfg.hurst_min_bars:
        return None
    lags = np.arange(cfg.hurst_min_lag, min(cfg.hurst_max_lag, n // 4) + 1)
    if len(lags) < cfg.hurst_min_lags_used:
        return None
    stds = np.array([float(np.std(y[t:] - y[:-t])) for t in lags])
    if not np.all(stds > 0):
        return None
    return float(np.polyfit(np.log(lags), np.log(stds), 1)[0])


def robust_sd(x) -> float:
    """1.4826 x median absolute deviation (std of a normal sample, not moved by outliers);
    the plain std if the MAD is 0 (many flat bars)."""
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return 0.0
    mad = 1.4826 * float(np.median(np.abs(x - np.median(x))))
    return mad if mad > 0 else float(np.std(x))


def winsorize(x, sd_limit: float) -> np.ndarray:
    """`x` clipped to median +- sd_limit x robust sd (unchanged if x has no spread)."""
    x = np.asarray(x, dtype=float)
    sd = robust_sd(x)
    if sd <= 0:
        return x.copy()
    mid = float(np.median(x))
    return np.clip(x, mid - sd_limit * sd, mid + sd_limit * sd)


def ranks(values) -> np.ndarray:
    """1-based ranks, ties get the mean of their positions."""
    v = np.asarray(values, dtype=float)
    _, inverse, counts = np.unique(v, return_inverse=True, return_counts=True)
    upper = np.cumsum(counts)
    return (upper - (counts - 1) / 2.0)[inverse]


def gap_returns(secs, bar_seconds: int, cfg: StationarityConfig) -> np.ndarray:
    """True for each return (len(secs) - 1) whose two bars are more than `gap_bars` bars
    apart: a weekend, holiday or bridged cache hole, not a normal bar-to-bar move."""
    s = np.asarray(secs, dtype=np.int64)
    return np.diff(s) > cfg.gap_bars * bar_seconds


def variance_ratio(
    y, q: int, cfg: StationarityConfig, winsor_sd: float | None = None
) -> dict | None:
    """Lo-MacKinlay VR(q) of the log price series `y` with the robust z: {vr, z, p_value, obs}.
    With `winsor_sd` the returns are clipped at that many sd first (a robust variant)."""
    y = _clean(y)
    if winsor_sd is not None and len(y) > 1:
        y = np.concatenate([[y[0]], y[0] + np.cumsum(winsorize(np.diff(y), winsor_sd))])
    r = np.diff(y)
    n = len(r)
    if n < max(cfg.vr_min_returns, 2 * q) or q < 2:
        return None
    mu = (y[-1] - y[0]) / n
    dev = r - mu
    sigma_a = float(dev @ dev) / (n - 1)
    if sigma_a <= 0:
        return None
    qsum = y[q:] - y[:-q] - q * mu  # n - q + 1 overlapping q-bar returns
    m = q * (n - q + 1) * (1 - q / n)
    sigma_c = float(qsum @ qsum) / m
    vr = sigma_c / sigma_a
    sq = dev**2
    denom = float(sq.sum()) ** 2
    theta = 0.0
    for j in range(1, q):
        delta = float(sq[j:] @ sq[:-j]) / denom
        theta += (2 * (q - j) / q) ** 2 * delta
    if theta <= 0:
        return None
    z = (vr - 1) / math.sqrt(theta)
    return {"vr": vr, "z": z, "p_value": normal_p_value(z), "obs": n}


def lag_corr(returns, k: int, h: int, min_pairs: int) -> dict | None:
    """Correlation of the past k-bar return with the next h-bar return on non-overlapping
    blocks of k + h bars: Pearson {corr, t, p_value}, Spearman {spearman, spearman_t,
    p_spearman} and pairs, or None."""
    r = _clean(returns)
    block = k + h
    pairs = len(r) // block
    if pairs < max(min_pairs, 3):
        return None
    blocks = r[: pairs * block].reshape(pairs, block)
    past, nxt = blocks[:, :k].sum(axis=1), blocks[:, k:].sum(axis=1)
    if past.std() == 0 or nxt.std() == 0:
        return None
    corr = float(np.corrcoef(past, nxt)[0, 1])
    t = corr * math.sqrt((pairs - 2) / max(1 - corr * corr, 1e-12))
    rho = float(np.corrcoef(ranks(past), ranks(nxt))[0, 1])  # robust to one extreme pair
    rho_t = rho * math.sqrt((pairs - 2) / max(1 - rho * rho, 1e-12))
    return {
        "corr": corr, "pairs": pairs, "t": t, "p_value": t_p_value(t, pairs - 2),
        "spearman": rho, "spearman_t": rho_t, "p_spearman": t_p_value(rho_t, pairs - 2),
    }  # fmt: skip


# --- DST weeks, symbol end, reference ------------------------------------------------------------------------------


def _nth_sunday(year: int, month: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(6 - first.weekday()) % 7 + 7 * (n - 1))


def _last_sunday(year: int, month: int) -> date:
    last = date(year + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
    return last - timedelta(days=(last.weekday() + 1) % 7)


def us_only_dst_ranges(year: int) -> list[tuple[date, date]]:
    """Half-open date ranges [from, to) in which the US is on summer time and Europe is not:
    second Sunday of March to the last Sunday of March, last Sunday of October to the first
    Sunday of November."""
    return [
        (_nth_sunday(year, 3, 2), _last_sunday(year, 3)),
        (_last_sunday(year, 10), _nth_sunday(year, 11, 1)),
    ]


def us_only_dst_days(cfg: StationarityConfig) -> frozenset[int]:
    """Day numbers (days since 1970-01-01) of those weeks for the years up to `dst_last_year`."""
    days: set[int] = set()
    for year in range(cfg.dst_first_year, cfg.dst_last_year + 1):
        for start, end in us_only_dst_ranges(year):
            days.update(range((start - EPOCH).days, (end - EPOCH).days))
    return frozenset(days)


def symbol_end(symbol: str, end: date, cfg: StationarityConfig) -> date:
    caps = dict(cfg.symbol_ends)
    return min(end, caps[symbol]) if symbol in caps else end


def shuffle_returns(y, cfg: StationarityConfig) -> np.ndarray:
    """Log prices with the same returns in a seeded random order (same start and end): the
    second reference, it keeps fat tails and the size of the moves but no order."""
    y = np.asarray(y, dtype=float)
    if len(y) < 2:
        return y.copy()
    r = np.random.default_rng(cfg.seed).permutation(np.diff(y))
    return np.concatenate([[y[0]], y[0] + np.cumsum(r)])


def random_walk(n: int, sigma: float, cfg: StationarityConfig) -> np.ndarray:
    """Log prices (n + 1 points) of a seeded Gaussian random walk with per-bar std `sigma`."""
    steps = np.random.default_rng(cfg.seed).normal(0.0, sigma, n)
    return math.log(100.0) + np.concatenate([[0.0], np.cumsum(steps)])


# --- time of day ---------------------------------------------------------------------------------------------------------------


def _mean_stats(v: np.ndarray) -> tuple[float, float | None, float | None]:
    n = len(v)
    mean = float(v.mean())
    sd = float(v.std(ddof=1)) if n > 1 else 0.0
    if sd <= 0:
        return mean, None, None
    t = mean / (sd / math.sqrt(n))
    return mean, t, t_p_value(t, n - 1)


def _ac_stats(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float] | None:
    m = len(x)
    if m < 3 or x.std() == 0 or y.std() == 0:
        return None
    c = max(-1.0, min(1.0, float(np.corrcoef(x, y)[0, 1])))
    t = c * math.sqrt((m - 2) / max(1 - c * c, 1e-12))
    return c, t, t_p_value(t, m - 2)


def time_of_day_rows(secs, closes, excluded_days, cfg: StationarityConfig) -> list[dict]:
    """Per UTC bucket of `bucket_minutes`: obs, mean 5-minute log return and its t / p, the
    median, and the first-order autocorrelation of the returns inside the bucket (ac1, pairs,
    t, p). The `_w` columns (mean_w, mean_w_t, p_mean_w, ac1_w, ac_w_t, p_ac_w) are the same
    statistics with the bucket's returns clipped at `winsor_sd` robust sd (robust to a few
    extreme bars); the findings use them. `secs`: bar open times (epoch seconds);
    `excluded_days`: day numbers to drop. Buckets with fewer than `min_bucket_obs` returns are
    left out; the autocorrelation is None below that many pairs."""
    secs = np.asarray(secs, dtype=np.int64)
    price = np.asarray(closes, dtype=float)
    if len(secs) < 3:
        return []
    r = np.diff(np.log(price))
    valid = (np.diff(secs) == cfg.bar_seconds) & np.isfinite(r)
    day = secs[1:] // SECONDS_PER_DAY
    if excluded_days:
        valid &= ~np.isin(day, np.fromiter(excluded_days, dtype=np.int64))
    width = cfg.bucket_minutes * 60
    nb = SECONDS_PER_DAY // width
    bucket = (secs[1:] % SECONDS_PER_DAY) // width
    pair = valid[1:] & valid[:-1] & (bucket[1:] == bucket[:-1])
    rows = []
    for b in range(nb):
        v = r[valid & (bucket == b)]
        n = len(v)
        if n < max(cfg.min_bucket_obs, 3):
            continue
        sd = robust_sd(v)
        mid = float(np.median(v))
        clip = (mid - cfg.winsor_sd * sd, mid + cfg.winsor_sd * sd) if sd > 0 else (-np.inf, np.inf)
        mean, mean_t, p_mean = _mean_stats(v)
        mean_w, mean_w_t, p_mean_w = _mean_stats(np.clip(v, *clip))
        sel = pair & (bucket[1:] == b)
        x, y = r[:-1][sel], r[1:][sel]
        row = {
            "bucket": f"{b * cfg.bucket_minutes // 60:02d}:{b * cfg.bucket_minutes % 60:02d}",
            "obs": n,
            "mean_return": mean, "mean_t": mean_t, "p_mean": p_mean,
            "median_return": mid,
            "mean_w": mean_w, "mean_w_t": mean_w_t, "p_mean_w": p_mean_w,
            "ac_pairs": len(x),
            "ac1": None, "ac_t": None, "p_ac": None,
            "ac1_w": None, "ac_w_t": None, "p_ac_w": None,
        }  # fmt: skip
        if len(x) >= max(cfg.min_bucket_obs, 3):
            raw = _ac_stats(x, y)
            if raw:
                row.update(ac1=raw[0], ac_t=raw[1], p_ac=raw[2])
            wins = _ac_stats(np.clip(x, *clip), np.clip(y, *clip))
            if wins:
                row.update(ac1_w=wins[0], ac_w_t=wins[1], p_ac_w=wins[2])
        rows.append(row)
    return rows


# --- one series, three periods, real and reference -----------------------------------------------------------------------------


def _period_rows(symbol, timeframe, source, period, y, cfg, gaps=None) -> dict[str, list[dict]]:
    base = {
        "symbol": symbol, "timeframe": timeframe, "period": period, "source": source,
        "bars": len(y),
    }  # fmt: skip
    out: dict[str, list[dict]] = {"adf": [], "hurst": [], "vr": [], "lagcorr": []}
    res = adf(y, cfg)
    if res:
        out["adf"].append(
            {**base, "lam": res["lam"], "adf_t": res["adf_t"], "p_value": res["p_value"],
             "half_life_bars": res["half_life"]}
        )  # fmt: skip
    h = hurst(y, cfg)
    if h is not None:
        out["hurst"].append({**base, "hurst": h})
    for q in cfg.vr_qs:
        res = variance_ratio(y, q, cfg)
        if res:
            wins = variance_ratio(y, q, cfg, winsor_sd=cfg.winsor_sd) or {}
            out["vr"].append(
                {**base, "q": q, "vr": res["vr"], "z": res["z"], "p_value": res["p_value"],
                 "vr_w": wins.get("vr"), "z_w": wins.get("z"), "p_value_w": wins.get("p_value")}
            )  # fmt: skip
    returns = np.diff(y)
    if gaps is not None:
        returns = np.where(gaps, 0.0, returns)  # gap returns are not used in lag pairs
    for k in cfg.lag_ks:
        for h_ in cfg.lag_ks:
            res = lag_corr(returns, k, h_, cfg.min_pairs)
            if res:
                out["lagcorr"].append({**base, "k": k, "h": h_, **res})
    return out


def series_rows(
    symbol: str, timeframe: str, y, split: int, cfg: StationarityConfig,
    secs=None, bar_seconds: int | None = None,
) -> dict[str, list[dict]]:  # fmt: skip
    """ADF / Hurst / VR / lag-correlation rows of the log-price series `y` for the whole
    period and its halves (`y[:split]`, `y[split:]`), for the real series and for a seeded
    random walk of the same length and per-bar volatility (source = real / random_walk).
    With `secs` (bar open times) and `bar_seconds`, a return over a gap of more than
    `gap_bars` bars (weekend, holiday, bridged hole) is set to 0 in the lag-correlation pairs,
    for the real series and the reference alike."""
    y = np.asarray(y, dtype=float)
    gap_all = None if secs is None else gap_returns(secs, bar_seconds, cfg)
    out: dict[str, list[dict]] = {"adf": [], "hurst": [], "vr": [], "lagcorr": []}
    sources = [("real", y)]
    sigma = float(np.std(np.diff(y))) if len(y) > 2 else 0.0
    if sigma > 0:
        sources.append(("random_walk", random_walk(len(y) - 1, sigma, cfg)))
        sources.append(("shuffled", shuffle_returns(y, cfg)))
    for source, series in sources:
        parts = {"whole": series, "first_half": series[:split], "second_half": series[split:]}
        gap_parts = (
            dict.fromkeys(parts)
            if gap_all is None
            else {"whole": gap_all, "first_half": gap_all[: max(split - 1, 0)],
                  "second_half": gap_all[split:]}
        )  # fmt: skip
        for period, part in parts.items():
            found = _period_rows(symbol, timeframe, source, period, part, cfg, gap_parts[period])
            for fam, rows in found.items():
                out[fam] += rows
    return out


# --- findings ------------------------------------------------------------------------------------------------------------------------


def cells_from_rows(rows: dict[str, list[dict]], source: str = "real") -> list[dict]:
    """Test cells of the rows of one `source` (real or shuffled): family, symbol, timeframe, cell, period, p_value, value.
    `rows` keys: adf, vr, lagcorr, time_of_day (rows with a `timeframe` of M5)."""
    cells = []

    def add(family, r, key, p, value):
        cells.append({"family": family, "symbol": r["symbol"], "timeframe": r["timeframe"],
                      "cell": key, "period": r["period"], "p_value": p, "value": value})  # fmt: skip

    for r in rows.get("adf", []):
        if r["source"] == source:
            add("adf", r, "adf", r["p_value"], r["lam"])
    for r in rows.get("vr", []):
        if r["source"] == source:
            add("vr", r, f"q={r['q']}", r["p_value_w"], r["vr_w"] - 1)
    for r in rows.get("lagcorr", []):
        if r["source"] == source:
            add("lagcorr", r, f"k={r['k']},h={r['h']}", r["p_spearman"], r["spearman"])
    for r in rows.get("time_of_day", []):
        if r.get("source", "real") != source:
            continue
        add("tod_mean", r, r["bucket"], r["p_mean_w"], r["mean_w"])
        add("tod_ac", r, r["bucket"], r["p_ac_w"], r["ac1_w"])
    return cells


def _sign(v) -> int:
    return 0 if v is None or v == 0 else (1 if v > 0 else -1)


def find_findings(cells: Sequence[dict], cfg: StationarityConfig) -> tuple[list[dict], dict]:
    """(findings, counts). See the module docstring. counts[family] = cells (whole-period
    cells with a p-value), bh_significant, findings."""
    group_of = {s: g for g, members in cfg.sibling_groups.items() for s in members}
    index = {(c["family"], c["symbol"], c["timeframe"], c["cell"], c["period"]): c for c in cells}
    families = list(dict.fromkeys(c["family"] for c in cells))
    findings, counts = [], {}
    for fam in families:
        whole = [
            c for c in cells
            if c["family"] == fam and c["period"] == "whole" and c["p_value"] is not None
        ]  # fmt: skip
        flags = benjamini_hochberg([c["p_value"] for c in whole], cfg.bh_q)
        counts[fam] = {"cells": len(whole), "bh_significant": sum(flags), "findings": 0}
        for c, hit in zip(whole, flags, strict=True):
            if not hit:
                continue
            sign = _sign(c["value"])
            key = (c["symbol"], c["timeframe"], c["cell"])
            halves = [index.get((fam, *key, p)) for p in ("first_half", "second_half")]
            if sign == 0 or any(h is None or _sign(h["value"]) != sign for h in halves):
                continue
            group = group_of.get(c["symbol"])
            siblings = []
            for other in cfg.sibling_groups.get(group, ()):
                o = index.get((fam, other, c["timeframe"], c["cell"], "whole"))
                if other != c["symbol"] and o is not None and _sign(o["value"]) == sign:
                    siblings.append(o)
            if 1 + len(siblings) < cfg.min_siblings:
                continue
            counts[fam]["findings"] += 1
            sib_txt = "; ".join(f"{o['symbol']} {o['value']:+.4g} (p="
                                + ("n/a" if o['p_value'] is None else f"{o['p_value']:.2g}") + ")"
                                for o in siblings)  # fmt: skip
            findings.append(
                {
                    "family": fam, "symbol": c["symbol"], "timeframe": c["timeframe"],
                    "cell": c["cell"], "value": c["value"], "p_value": c["p_value"],
                    "first_half": halves[0]["value"], "second_half": halves[1]["value"],
                    "siblings": sib_txt,
                    "reason": (
                        f"BH-significant at q={cfg.bh_q} (p={c['p_value']:.2g}, "
                        f"{counts[fam]['cells']} cells), same sign in both halves, "
                        f"{len(siblings)} sibling(s) of group {group} with the same sign"
                    ),
                }
            )  # fmt: skip
    return findings, counts
