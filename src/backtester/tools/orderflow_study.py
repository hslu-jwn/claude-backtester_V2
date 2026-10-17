"""Order-flow study on Binance futures BTCUSDT / ETHUSDT. Research only, it changes no setting.

    python -m backtester.tools.orderflow_study
    python -m backtester.tools.orderflow_study --symbols BTCUSDT --shuffles 50

Development period only: 2020-01-01 .. 2021-09-13 (ROADMAP 11.16; later data is never read).
For the bars of 5m / 15m / 1h / 4h the features of `analytics/orderflow.py` (imbalance, cumulative
delta and its z-score, CVD-price divergence, relative volume, funding) are cut into deciles and
compared with the forward return of the next 1 / 3 / 6 bars (percent and ATR units).

Writes `results/orderflow_study/`:
- `summary.csv`: one row per symbol, timeframe, feature, horizon and target with the top-minus-bottom
  decile spread, the shuffle 95th percentile (and the circular-shift one, which keeps
  autocorrelation and is the fairer noise level), the spread in each half (2020 / 2021-01..09), sign
  stability and whether the best decile's excess move beats the round-trip taker (0.10 %) and
  maker (0.04 %) fee;
- `deciles.csv`: every decile table (n, mean, median, hit rate, t-stat).
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.analytics.orderflow import (
    OrderflowConfig,
    add_features,
    add_targets,
    aggregate,
    bucket,
    decile_table,
    half_spreads,
    shift_p95,
    shuffle_p95,
    spread,
)
from backtester.data.binance import CACHE_DIR, DEFAULT_SYMBOLS, FLOW_DIR, FUNDING_DIR
from backtester.paths import RESULTS_DIR
from backtester.tools.trend_grid import write_csv

DEV_START = date(2020, 1, 1)
DEV_END_DATE = date(2021, 9, 13)
DEV_END = pd.Timestamp("2021-09-13 23:59", tz="UTC")
OUT_DIR = RESULTS_DIR / "orderflow_study"
TARGETS = (("ret_pct", "ret"), ("atr", "atr"))  # (label, column prefix)
M1_COLUMNS = ["open", "high", "low", "close", "volume", "delta"]


def load_m1(symbol: str, start: date = DEV_START, end: date = DEV_END_DATE) -> pd.DataFrame:
    """M1 bars + taker delta from the cache, day files from `start` to `end` only."""
    frames = []
    day = start
    while day <= end:
        rel = Path(symbol) / str(day.year) / f"{day.isoformat()}.parquet"
        bars_f, flow_f = CACHE_DIR / rel, FLOW_DIR / rel
        if bars_f.exists() and flow_f.exists():
            b = pd.read_parquet(bars_f)
            f = pd.read_parquet(flow_f)[["ts", "delta"]]
            if len(b):
                m = b.merge(f, on="ts", how="inner")
                frames.append(
                    pd.DataFrame(
                        {
                            "ts": m["ts"],
                            "open": m["bid_open"],
                            "high": m["bid_high"],
                            "low": m["bid_low"],
                            "close": m["bid_close"],
                            "volume": m["bid_volume"],
                            "delta": m["delta"],
                        }
                    )
                )
        day += timedelta(days=1)
    out = pd.concat(frames, ignore_index=True).set_index("ts").sort_index()
    out.index = pd.DatetimeIndex(out.index).tz_convert("UTC")
    return out[M1_COLUMNS]


def load_funding(symbol: str) -> pd.Series:
    """Funding rate by funding time; rows after the development period are dropped on read."""
    df = pd.read_csv(FUNDING_DIR / f"{symbol}.csv", usecols=["calc_time", "last_funding_rate"])
    t = pd.to_datetime(df["calc_time"], utc=True)
    keep = t <= DEV_END
    return pd.Series(df.loc[keep, "last_funding_rate"].to_numpy(), index=pd.DatetimeIndex(t[keep]))


def feature_columns(frame: pd.DataFrame) -> list[str]:
    skip = {"open", "high", "low", "close", "volume", "delta", "close_time"}
    return [
        c for c in frame.columns
        if c not in skip and not c.startswith(("ret_", "atr_"))
    ]  # fmt: skip


def study_frame(
    m1: pd.DataFrame, funding: pd.Series | None, tf: str, symbol: str, cfg: OrderflowConfig
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summary rows and decile rows for one symbol and timeframe."""
    period = pd.Timedelta(tf)
    frame = add_targets(add_features(aggregate(m1, tf), cfg, funding, period), cfg, period)
    first = np.asarray(frame.index < pd.Timestamp(cfg.half_split, tz="UTC"))
    summary, deciles = [], []
    for feat in feature_columns(frame):
        x = frame[feat].to_numpy(dtype=float)
        if np.isnan(x).all():
            continue
        codes = bucket(x, cfg.buckets)
        for h in cfg.horizons:
            for label, prefix in TARGETS:
                y = frame[f"{prefix}_{h}"].to_numpy(dtype=float)
                tab = decile_table(x, y, cfg.buckets, overlap=h)
                if tab.empty:
                    continue
                for col, val in (("symbol", symbol), ("timeframe", tf), ("feature", feat),
                                 ("horizon", h), ("target", label)):  # fmt: skip
                    tab.insert(0, col, val)
                deciles.append(tab)
                sp = spread(codes, y)
                p95 = shuffle_p95(codes, y, cfg.shuffles, cfg.seed, cfg.shuffle_quantile)
                sh95 = shift_p95(codes, y, cfg.shuffles, cfg.seed, cfg.shuffle_quantile)
                h1, h2 = half_spreads(codes, y, first)
                top, bot = tab["mean"].iloc[-1], tab["mean"].iloc[0]
                overall = float(np.nanmean(y))
                ex_top, ex_bot = top - overall, bot - overall
                best = ex_top if abs(ex_top) >= abs(ex_bot) else ex_bot
                money = label == "ret_pct"
                summary.append(
                    {
                        "symbol": symbol, "timeframe": tf, "feature": feat, "horizon": h,
                        "target": label, "n": int(tab["n"].sum()), "spread": sp,
                        "shuffle_p95": p95, "ratio": abs(sp) / p95 if p95 else np.nan,
                        "beats_shuffle": bool(abs(sp) > p95),
                        "shift_p95": sh95,
                        "beats_shift": bool(abs(sp) > sh95),
                        "best_side": "top" if abs(ex_top) >= abs(ex_bot) else "bottom",
                        "best_excess_pct": best if money else np.nan,
                        "beats_taker": bool(abs(best) > cfg.taker_fee_pct) if money else None,
                        "beats_maker": bool(abs(best) > cfg.maker_fee_pct) if money else None,
                        "spread_h1": h1, "spread_h2": h2,
                        "sign_stable": bool(np.sign(h1) == np.sign(h2) == np.sign(sp))
                        if not (np.isnan(h1) or np.isnan(h2)) else False,
                    }
                )  # fmt: skip
    return pd.DataFrame(summary), pd.concat(deciles, ignore_index=True)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    ap.add_argument("--timeframes", nargs="+", default=None)
    ap.add_argument("--shuffles", type=int, default=None)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args(argv)
    cfg = OrderflowConfig()
    over = {}
    if args.timeframes:
        over["timeframes"] = tuple(args.timeframes)
    if args.shuffles:
        over["shuffles"] = args.shuffles
    if over:
        cfg = replace(cfg, **over)
    args.out.mkdir(parents=True, exist_ok=True)
    sums, decs = [], []
    for sym in args.symbols:
        m1 = load_m1(sym)
        funding = load_funding(sym)
        print(f"{sym}: {len(m1)} M1 bars {m1.index[0]} .. {m1.index[-1]}")
        for tf in cfg.timeframes:
            s, d = study_frame(m1, funding, tf, sym, cfg)
            sums.append(s)
            decs.append(d)
            print(f"  {tf}: {len(s)} rows")
    summary = pd.concat(sums, ignore_index=True)
    write_csv(args.out / "summary.csv", summary.to_dict("records"))
    write_csv(args.out / "deciles.csv", pd.concat(decs, ignore_index=True).to_dict("records"))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
