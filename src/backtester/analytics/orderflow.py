"""Order-flow study on Binance futures (BTCUSDT, ETHUSDT). Spec: ROADMAP.md > 11.16.

Research only: no trading rule, no setting. M1 bars with taker delta are aggregated to 5m / 15m /
1h / 4h bars. Every feature is known at the bar's close; every target starts at that close and
looks `h` bars ahead (`ret_h` in percent, `atr_h` in units of the ATR known at the feature
bar's close). Features are sorted into deciles (a feature with few distinct values, e.g. the
divergence flag, uses its values as buckets); the effect is the mean target of the top bucket
minus the bottom bucket. The shuffle baseline permutes the bucket codes and reports the 95th
percentile of the absolute spread, i.e. what noise produces.

A forward return of h bars overlaps its neighbours, so the t-stat uses n / h as the sample size.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class OrderflowConfig:
    timeframes: tuple[str, ...] = ("5min", "15min", "1h", "4h")
    cvd_windows: tuple[int, ...] = (4, 12, 24)  # bars of cumulative delta / divergence lookback
    z_window: int = 100  # bars for the z-score of the cumulative delta
    relvol_days: int = 20  # days for the same-time-of-day mean volume
    atr_period: int = 14
    horizons: tuple[int, ...] = (1, 3, 6)  # forward bars
    buckets: int = 10  # deciles
    shuffles: int = 200
    seed: int = 42
    shuffle_quantile: float = 0.95
    taker_fee_pct: float = 0.10  # round trip, 2 x 0.05 % (risk-management.md > Costs)
    maker_fee_pct: float = 0.04  # round trip, 2 x 0.02 %
    half_split: str = "2021-01-01"  # first half = before, second half = from this date (UTC)


def aggregate(m1: pd.DataFrame, rule: str) -> pd.DataFrame:
    """M1 (index = open time UTC; open, high, low, close, volume, delta) -> bars of `rule`.

    Bars without any M1 row are dropped; `close_time` = open time + the bar length.
    """
    grp = m1.resample(rule, label="left", closed="left")
    bars = pd.DataFrame(
        {
            "open": grp["open"].first(),
            "high": grp["high"].max(),
            "low": grp["low"].min(),
            "close": grp["close"].last(),
            "volume": grp["volume"].sum(),
            "delta": grp["delta"].sum(),
            "n": grp["close"].count(),
        }
    )
    bars = bars[bars["n"] > 0].drop(columns="n")
    bars["close_time"] = bars.index + pd.Timedelta(rule)
    return bars


def add_features(
    bars: pd.DataFrame, cfg: OrderflowConfig, funding: pd.Series | None, period: pd.Timedelta
) -> pd.DataFrame:
    """Add imbalance, cvd_N, cvd_z_N, div_N, relvol and funding (all known at the bar's close).

    `funding`: rate indexed by funding time (UTC); each bar gets the last rate at or before
    its close time.
    """
    out = bars.copy()
    out["imbalance"] = out["delta"] / out["volume"].where(out["volume"] > 0)
    run = out["delta"].cumsum()
    for n in cfg.cvd_windows:
        s = out["delta"].rolling(n).sum()
        out[f"cvd_{n}"] = s
        z = s.rolling(cfg.z_window)
        out[f"cvd_z_{n}"] = (s - z.mean()) / z.std()
        new_high = (out["close"] > out["close"].shift(1).rolling(n).max()) & (
            run <= run.shift(1).rolling(n).max()
        )
        new_low = (out["close"] < out["close"].shift(1).rolling(n).min()) & (
            run >= run.shift(1).rolling(n).min()
        )
        out[f"div_{n}"] = new_low.astype(int) - new_high.astype(int)
    slot = (out.index - out.index.normalize()) // period
    base = (
        out["volume"].groupby(slot).transform(lambda v: v.shift(1).rolling(cfg.relvol_days).mean())
    )
    out["relvol"] = out["volume"] / base.where(base > 0)
    out["funding"] = np.nan
    if funding is not None and len(funding):
        f = funding.sort_index()
        f.index = pd.DatetimeIndex(f.index)
        pos = f.index.searchsorted(pd.DatetimeIndex(out.index + period), side="right") - 1
        vals = np.where(pos >= 0, f.to_numpy()[np.clip(pos, 0, None)], np.nan)
        out["funding"] = vals
    return out


def add_targets(bars: pd.DataFrame, cfg: OrderflowConfig, period: pd.Timedelta) -> pd.DataFrame:
    """Add ret_h (percent) and atr_h (price move / ATR at the feature bar) for each horizon.

    The move runs from the feature bar's close to the close h bars later; it is NaN if the
    h-th next row is not exactly h bars later (a gap in the data).
    """
    out = bars.copy()
    prev = out["close"].shift(1)
    tr = pd.concat(
        [out["high"] - out["low"], (out["high"] - prev).abs(), (out["low"] - prev).abs()], axis=1
    ).max(axis=1, skipna=False)
    atr = tr.rolling(cfg.atr_period).mean()
    for h in cfg.horizons:
        ahead = out["close"].shift(-h)
        ok = (out.index.to_series().shift(-h) - out.index.to_series()) == h * period
        move = (ahead - out["close"]).where(ok)
        out[f"ret_{h}"] = move / out["close"] * 100
        out[f"atr_{h}"] = move / atr
    return out


def bucket(values, n: int) -> np.ndarray:
    """Bucket codes 0..n-1 by rank (equal counts); -1 for NaN. Few distinct values: by value."""
    x = pd.Series(np.asarray(values, dtype=float))
    codes = np.full(len(x), -1, dtype=int)
    ok = x.notna().to_numpy()
    if not ok.any():
        return codes
    uniq = np.sort(x[ok].unique())
    if len(uniq) <= n:
        codes[ok] = np.searchsorted(uniq, x[ok].to_numpy())
        return codes
    rank = x[ok].rank(method="first").to_numpy()
    codes[ok] = np.floor((rank - 1) * n / ok.sum()).astype(int)
    return codes


def _clean(x, y) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ok = ~(np.isnan(x) | np.isnan(y))
    return x[ok], y[ok]


def decile_table(feature, target, n: int, overlap: int = 1) -> pd.DataFrame:
    """Per bucket: n, mean, median, hit_rate (share target > 0), t (mean / (sd / sqrt(n / overlap)))."""
    x, y = _clean(feature, target)
    codes = bucket(x, n)
    rows = []
    for c in range(codes.max() + 1 if len(codes) else 0):
        v = y[codes == c]
        if len(v) == 0:
            continue
        sd = v.std(ddof=1) if len(v) > 1 else np.nan
        t = v.mean() / (sd / np.sqrt(len(v) / overlap)) if sd and sd > 0 else np.nan
        rows.append(
            {"bucket": c, "n": len(v), "mean": v.mean(), "median": float(np.median(v)),
             "hit_rate": float((v > 0).mean()), "t": t}
        )  # fmt: skip
    return pd.DataFrame(rows)


def spread(codes: np.ndarray, target) -> float:
    """Mean target of the top bucket minus the bottom bucket (NaN if either is empty)."""
    y = np.asarray(target, dtype=float)
    ok = (codes >= 0) & ~np.isnan(y)
    c, y = codes[ok], y[ok]
    if len(c) == 0:
        return float("nan")
    lo, hi = c.min(), c.max()
    if lo == hi:
        return float("nan")
    return float(y[c == hi].mean() - y[c == lo].mean())


def half_spreads(codes: np.ndarray, target, first_half: np.ndarray) -> tuple[float, float]:
    """Spread in each half using the whole-sample buckets (top / bottom of the whole sample)."""
    y = np.asarray(target, dtype=float)
    top, bottom = codes.max(), 0
    res = []
    for mask in (first_half, ~first_half):
        ok = mask & (codes >= 0) & ~np.isnan(y)
        a, b = y[ok & (codes == top)], y[ok & (codes == bottom)]
        res.append(float(a.mean() - b.mean()) if len(a) and len(b) and top != bottom else np.nan)
    return res[0], res[1]


def shuffle_p95(codes: np.ndarray, target, shuffles: int, seed: int, q: float = 0.95) -> float:
    """q-quantile of the absolute spread when the bucket codes are randomly permuted."""
    y = np.asarray(target, dtype=float)
    ok = (codes >= 0) & ~np.isnan(y)
    c, y = codes[ok], y[ok]
    if len(c) == 0 or c.min() == c.max():
        return float("nan")
    lo, hi = c.min(), c.max()
    rng = np.random.default_rng(seed)
    vals = np.empty(shuffles)
    for i in range(shuffles):
        p = rng.permutation(c)
        vals[i] = abs(y[p == hi].mean() - y[p == lo].mean())
    return float(np.quantile(vals, q))


def shift_p95(
    codes: np.ndarray, target, shuffles: int, seed: int, q: float = 0.95, min_frac: float = 0.05
) -> float:
    """q-quantile of the absolute spread when the codes are circularly shifted against the target.

    Keeps the autocorrelation of the feature and of the (overlapping) forward returns, so it is
    the fairer noise level for persistent features; the shift is at least `min_frac` of the
    sample away from zero.
    """
    y = np.asarray(target, dtype=float)
    ok = (codes >= 0) & ~np.isnan(y)
    c, y = codes[ok], y[ok]
    if len(c) < 4 or c.min() == c.max():
        return float("nan")
    lo, hi = c.min(), c.max()
    rng = np.random.default_rng(seed)
    low = max(1, int(len(c) * min_frac))
    vals = np.empty(shuffles)
    for i in range(shuffles):
        p = np.roll(c, int(rng.integers(low, len(c) - low + 1)))
        vals[i] = abs(y[p == hi].mean() - y[p == lo].mean())
    return float(np.quantile(vals, q))
