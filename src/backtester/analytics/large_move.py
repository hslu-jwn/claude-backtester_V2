"""Large-move momentum study (research only). Spec: ROADMAP.md > 11.13; knowledge/ideas.md I-61.

Question: after a bar whose return is larger than k robust standard deviations, does the price
continue (or reverse) over the next h bars, by more than the cost of a spread?

  * Returns are bar-to-bar log returns of the continuous series of existing bars (as 11.11).
  * Event: bar b with |ret_b| > k x sd_b. `sd_b` = 1.4826 x MAD of the `window` returns BEFORE
    bar b (the current bar is not in it, so a bar can never move its own threshold; no
    lookahead, appending future bars never changes sd_b or an event). Events right after a gap
    (more than `gap_bars` bars between bar b-1 and b: weekend, holiday, cache hole) are dropped.
    The forward window and the trailing window may cross a gap (a weekend in a 24-bar forward
    return is part of what a held position would earn).
  * Forward return: log(close_(b+h) / close_b) x sign(ret_b), in units of `sd_b` (per-bar sd, not
    scaled with sqrt(h)), in return units and in spreads of the symbol (one spread =
    `SymbolCosts.spread / reference_price`, the same price-scaled spread the cost model uses
    for any year). Continuation is positive.
  * Null: event times shuffled. For every hour of day (UTC, of the bar's open) as many bars as
    the real events have, drawn at random (with replacement) from the bars that could have been
    events (usable sd, not after a gap, forward window available), with the real up / down signs
    drawn the same way; `n_null` runs, seeded. p = two-sided normal p of the real mean against
    the null mean and sd (the empirical p of 1,000 runs cannot go below 0.001, too coarse for
    Benjamini-Hochberg over hundreds of cells); the percentile of the real mean among the null
    means is reported.
  * A finding (whole period): Benjamini-Hochberg over all cells, the same sign in both halves,
    >= 1 same-sign sibling (all three from `stationarity.find_findings`) and the mean survives
    removing the top `top_share` events (those that push the mean most, in its direction): same
    sign and trimmed |t| >= `survive_t`. Tradeable only if the mean continuation is above
    `tradeable_spreads` spreads.

numpy only.
"""

from __future__ import annotations

import math
import zlib
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from backtester.analytics.stationarity import (
    StationarityConfig,
    benjamini_hochberg,
    find_findings,
    gap_returns,
    normal_p_value,
)

FAMILY = "large_move"
HOUR_SECONDS = 3600
_CHUNK = 10_000


@dataclass(frozen=True)
class LargeMoveConfig:
    window: int = 500  # trailing returns for the robust sd
    ks: tuple[float, ...] = (2.0, 3.0, 4.0)
    hs: tuple[int, ...] = (1, 2, 4, 8, 24)
    n_null: int = 1000
    seed: int = 42
    top_share: float = 0.01  # share of events removed for the survival test (at least one)
    survive_t: float = 1.96  # |t| of the trimmed mean needed to survive
    tradeable_spreads: float = 1.5
    min_events: int = 30  # whole period; fewer: no p-value
    min_half_events: int = 10  # a half needs this many events to count for its sign


def cell_name(k: float, h: int) -> str:
    return f"k={k:g},h={h}"


def bar_returns(y) -> np.ndarray:
    """Log returns aligned to the bar: ret[b] = y[b] - y[b-1], ret[0] = NaN."""
    y = np.asarray(y, dtype=float)
    ret = np.full(len(y), np.nan)
    ret[1:] = np.diff(y)
    return ret


def trailing_robust_sd(ret, window: int) -> np.ndarray:
    """sd[b] = 1.4826 x MAD of ret[b-window:b] (the window BEFORE bar b); NaN until `window`
    returns exist (b < window + 1). The plain std if the MAD is 0 (many flat bars)."""
    ret = np.asarray(ret, dtype=float)
    n = len(ret)
    sd = np.full(n, np.nan)
    if n < window + 2:
        return sd
    windows = np.lib.stride_tricks.sliding_window_view(ret[1:], window)[: n - window - 1]
    for lo in range(0, len(windows), _CHUNK):
        w = windows[lo : lo + _CHUNK]
        med = np.median(w, axis=1)
        mad = 1.4826 * np.median(np.abs(w - med[:, None]), axis=1)
        flat = mad <= 0
        if flat.any():
            mad[flat] = np.std(w[flat], axis=1)
        sd[window + 1 + lo : window + 1 + lo + len(w)] = mad
    return sd


def forward_log_return(y, h: int) -> np.ndarray:
    """fwd[b] = y[b+h] - y[b]; NaN where bar b+h does not exist."""
    y = np.asarray(y, dtype=float)
    fwd = np.full(len(y), np.nan)
    if h < len(y):
        fwd[: len(y) - h] = y[h:] - y[:-h]
    return fwd


def signed(sign, fwd):
    """Forward return signed by the move: continuation is positive."""
    return sign * fwd


def prepare(y, secs, bar_seconds: int, cfg: LargeMoveConfig, scfg: StationarityConfig) -> dict:
    """Per-series arrays shared by all (k, h) cells."""
    y = np.asarray(y, dtype=float)
    secs = np.asarray(secs, dtype=np.int64)
    ret = bar_returns(y)
    sd = trailing_robust_sd(ret, cfg.window)
    after_gap = np.zeros(len(y), dtype=bool)
    if len(y) > 1:
        after_gap[1:] = gap_returns(secs, bar_seconds, scfg)
    with np.errstate(invalid="ignore"):
        ok = np.isfinite(sd) & (sd > 0) & ~after_gap & np.isfinite(ret)
    return {
        "y": y, "ret": ret, "sd": sd, "ok": ok, "secs": secs, "n": len(y), "fwd": {},
        "sign": np.sign(np.nan_to_num(ret)), "hour": (secs // HOUR_SECONDS) % 24,
    }  # fmt: skip


def _fwd(ctx: dict, h: int) -> np.ndarray:
    if h not in ctx["fwd"]:
        ctx["fwd"][h] = forward_log_return(ctx["y"], h)
    return ctx["fwd"][h]


def events_for(ctx: dict, k: float, h: int | None = None) -> np.ndarray:
    """Boolean mask of the event bars (with a forward window of `h` bars when h is given)."""
    with np.errstate(invalid="ignore"):
        ev = ctx["ok"] & (np.abs(ctx["ret"]) > k * ctx["sd"])
    if h is not None:
        ev &= np.isfinite(_fwd(ctx, h))
    return ev


def event_mask(y, secs, bar_seconds: int, k: float, cfg: LargeMoveConfig, scfg) -> np.ndarray:
    return events_for(prepare(y, secs, bar_seconds, cfg, scfg), k)


def spread_return(symbol: str) -> float:
    """One spread as a fraction of the price: the cost model's price-scaled spread over the
    price (= spread / reference price), the same for every year."""
    from backtester.engine.costs import CostConfig

    costs = CostConfig()
    ref = costs.for_symbol(symbol).reference_price
    price = ref if ref else 1.0
    return costs.spread(symbol, price=price) / price


# --- null ------------------------------------------------------------------------------------


def _draw(ctx: dict, ev: np.ndarray, cfg: LargeMoveConfig, seed_key: str, h: int | None):
    """(indices, signs), both (n_null, n_events): per hour of day as many random candidate
    bars (and real signs) as the real events have."""
    cand_mask = ctx["ok"].copy()
    if h is not None:
        cand_mask &= np.isfinite(_fwd(ctx, h))
    ev_idx = np.flatnonzero(ev)
    rng = np.random.default_rng([cfg.seed, zlib.crc32(seed_key.encode())])
    idx = np.empty((cfg.n_null, len(ev_idx)), dtype=np.int64)
    sgn = np.empty((cfg.n_null, len(ev_idx)))
    col = 0
    for hour in range(24):
        real = ev_idx[ctx["hour"][ev_idx] == hour]
        m = len(real)
        if m == 0:
            continue
        cands = np.flatnonzero(cand_mask & (ctx["hour"] == hour))
        idx[:, col : col + m] = cands[rng.integers(0, len(cands), (cfg.n_null, m))]
        sgn[:, col : col + m] = ctx["sign"][real][rng.integers(0, m, (cfg.n_null, m))]
        col += m
    return idx, sgn


def null_indices(ctx, ev, cfg: LargeMoveConfig, seed_key: str, h: int | None = None):
    return _draw(ctx, ev, cfg, seed_key, h)[0]


def null_means(ctx, ev, h: int, cfg: LargeMoveConfig, seed_key: str) -> np.ndarray:
    """Mean signed forward return (sd units) of each shuffled-time run."""
    idx, sgn = _draw(ctx, ev, cfg, seed_key, h)
    x = _fwd(ctx, h) / ctx["sd"]
    return (sgn * x[idx]).mean(axis=1)


# --- survival --------------------------------------------------------------------------------


def trim_top(values, direction: float, share: float) -> np.ndarray:
    """`values` without the top `share` (at least one) events in the direction of the mean
    (direction > 0: the largest values; < 0: the smallest)."""
    v = np.sort(np.asarray(values, dtype=float))
    cut = max(1, math.ceil(share * len(v)))
    return v[:-cut] if direction >= 0 else v[cut:]


def _t(v: np.ndarray) -> float:
    if len(v) < 2:
        return 0.0
    sd = float(np.std(v, ddof=1))
    return float(np.mean(v)) / (sd / math.sqrt(len(v))) if sd > 0 else 0.0


def trimmed_mean_t(values, share: float) -> tuple[float, float]:
    v = np.asarray(values, dtype=float)
    out = trim_top(v, float(np.mean(v)), share)
    return float(np.mean(out)) if len(out) else 0.0, _t(out)


# --- cells -----------------------------------------------------------------------------------


def _stats(vals_sd, vals_ret, spread: float) -> dict:
    return {
        "n": len(vals_sd),
        "mean_sd": float(np.mean(vals_sd)) if len(vals_sd) else None,
        "mean_ret": float(np.mean(vals_ret)) if len(vals_ret) else None,
        "mean_spreads": float(np.mean(vals_ret)) / spread if len(vals_ret) else None,
    }


def cell_rows(
    y, secs, bar_seconds: int, split: int, spread: float, cfg: LargeMoveConfig,
    scfg: StationarityConfig, seed_key: str,
) -> list[dict]:  # fmt: skip
    """One row per (k, h, period): whole, first_half (event bars < split), second_half."""
    ctx = prepare(y, secs, bar_seconds, cfg, scfg)
    rows = []
    for k in cfg.ks:
        for h in cfg.hs:
            ev = events_for(ctx, k, h)
            idx = np.flatnonzero(ev)
            fwd = _fwd(ctx, h)[idx]
            sgn = ctx["sign"][idx]
            x_sd = signed(sgn, fwd) / ctx["sd"][idx]
            x_ret = signed(sgn, fwd)
            base = {"k": k, "h": h}
            whole = {**base, "period": "whole", **_stats(x_sd, x_ret, spread)}
            whole.update({"t": None, "null_mean": None, "null_sd": None, "z": None, "p": None,
                          "pct": None, "up_share": None, "trim_mean": None, "trim_t": None})  # fmt: skip
            if len(idx):
                whole["up_share"] = float(np.mean(sgn > 0))
                whole["t"] = _t(x_sd)
            if len(idx) >= cfg.min_events:
                nm = null_means(ctx, ev, h, cfg, f"{seed_key}|{k:g}|{h}")
                mu, sd_null = float(nm.mean()), float(nm.std())
                whole["null_mean"], whole["null_sd"] = mu, sd_null
                if sd_null > 0:
                    whole["z"] = (whole["mean_sd"] - mu) / sd_null
                    whole["p"] = normal_p_value(whole["z"])
                whole["pct"] = float(np.mean(nm < whole["mean_sd"]))
                whole["trim_mean"], whole["trim_t"] = trimmed_mean_t(x_sd, cfg.top_share)
            rows.append(whole)
            for name, sel in (("first_half", idx < split), ("second_half", idx >= split)):
                half = {**base, "period": name, **_stats(x_sd[sel], x_ret[sel], spread)}
                if half["n"] < cfg.min_half_events:
                    half["mean_sd"] = half["mean_ret"] = half["mean_spreads"] = None
                rows.append(half)
    return rows


def cells_for_findings(rows: Sequence[dict]) -> list[dict]:
    """Rows (with `symbol` and `timeframe` set) as `stationarity.find_findings` cells."""
    return [
        {"family": FAMILY, "symbol": r["symbol"], "timeframe": r["timeframe"],
         "cell": cell_name(r["k"], r["h"]), "period": r["period"],
         "p_value": r["p"] if r["period"] == "whole" else None, "value": r["mean_sd"]}
        for r in rows
    ]  # fmt: skip


def find_move_findings(cells: Sequence[dict], scfg: StationarityConfig):
    """BH, halves and siblings: the stationarity study's rule, unchanged."""
    return find_findings(cells, scfg)


def _sign(v) -> int:
    return 0 if not v else (1 if v > 0 else -1)


def annotate(
    rows: Sequence[dict], findings: Sequence[dict], scfg: StationarityConfig,
    cfg: LargeMoveConfig | None = None,
) -> list[dict]:  # fmt: skip
    """Copies of `rows` with `finding`, `above_cost`, `tradeable` and `reason`. A finding is
    what `find_move_findings` returned AND survives the top-event removal (same sign, trimmed
    |t| >= `survive_t`); tradeable = a finding with continuation above `tradeable_spreads`.
    The reason names the first rule a cell fails."""
    cfg = cfg or LargeMoveConfig()
    out = [dict(r) for r in rows]
    whole = [r for r in out if r["period"] == "whole" and r["p"] is not None]
    bh = benjamini_hochberg([r["p"] for r in whole], scfg.bh_q)
    flagged = {id(r): hit for r, hit in zip(whole, bh, strict=True)}
    found = {(f["symbol"], f["timeframe"], f["cell"]) for f in findings}
    by_key = {(r["symbol"], r["timeframe"], r["k"], r["h"], r["period"]): r for r in out}
    for r in out:
        r.update({"finding": False, "above_cost": False, "tradeable": False, "reason": ""})
        if r["period"] != "whole":
            continue
        r["above_cost"] = (
            r["mean_spreads"] is not None and r["mean_spreads"] > cfg.tradeable_spreads
        )
        sign = _sign(r["mean_sd"])
        key = (r["symbol"], r["timeframe"], r["k"], r["h"])
        halves = [by_key.get((*key, p)) for p in ("first_half", "second_half")]
        if r["p"] is None:
            r["reason"] = f"too few events ({r['n']})"
        elif not flagged[id(r)]:
            r["reason"] = f"not BH-significant (p={r['p']:.2g})"
        elif sign == 0 or any(h is None or _sign(h["mean_sd"]) != sign for h in halves):
            r["reason"] = "halves differ in sign (or a half has too few events)"
        elif (r["symbol"], r["timeframe"], cell_name(r["k"], r["h"])) not in found:
            r["reason"] = "no same-sign sibling"
        elif _sign(r["trim_mean"]) != sign or abs(r["trim_t"]) < cfg.survive_t:
            r["reason"] = f"fails top {cfg.top_share:.0%} removal (trimmed t={r['trim_t']:.2f})"
        else:
            r["finding"] = True
            r["tradeable"] = r["above_cost"] and sign > 0
            r["reason"] = (
                f"finding: BH-significant (p={r['p']:.2g}), same sign in both halves, a "
                f"sibling, survives top removal (trimmed t={r['trim_t']:.2f})"
            )
    return out
