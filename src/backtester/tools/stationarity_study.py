"""Stationarity / half-life diagnostic study (ROADMAP 11.11, idea T-11). Research only, it
changes no setting and runs no strategy.

    python -m backtester.tools.stationarity_study --cache-dir data/cache/histdata
    python -m backtester.tools.stationarity_study --cache-dir <path> --symbols XAUUSD NAS100 \\
        --timeframes H1 D1 --start 2015-01-01 --end 2021-09-13 --workers 4 --out results/stationarity

Per symbol x timeframe (M5 M15 H1 H4 D1, resampled from the M1 cache) and period (whole,
first half, second half; halves split at the middle date of the period, GER40 only up to
2020-06-12) the ADF test with half-life, the Hurst exponent, the Lo-MacKinlay variance ratios
and the lag-correlation grid on the log close (statistics and choices: `analytics/stationarity`),
each next to a seeded random walk of the same length and volatility. On M5 also the
time-of-day part (30-minute UTC buckets; the 2015-2018 US-only-DST weeks are dropped).

Written to `<out>/`: adf.csv, hurst.csv, vr.csv, lagcorr.csv, time_of_day.csv, findings.csv
(Benjamini-Hochberg over each family, same sign in both halves, >= 2 sibling symbols) and
summary.txt. The cache folder is only read.

Spec: ROADMAP.md > 11.11; knowledge/ideas.md T-11.
"""

from __future__ import annotations

import argparse
import csv
import math
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.analytics.stationarity import (
    EPOCH,
    SECONDS_PER_DAY,
    StationarityConfig,
    cells_from_rows,
    find_findings,
    series_rows,
    shuffle_returns,
    symbol_end,
    time_of_day_rows,
    us_only_dst_days,
)
from backtester.analytics.verdict import middle_date
from backtester.core.models import Timeframe
from backtester.data.adapters.cache_adapter import CacheAdapter, cached_days
from backtester.paths import RESULTS_DIR

ALL_SYMBOLS = (
    "XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500",  # the five core symbols first
    "EURUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "EURGBP",
    "XAGUSD", "GER40", "UK100", "JP225", "EU50", "USOIL", "UKOIL", "DXY",
)  # fmt: skip
CORE = ALL_SYMBOLS[:5]
TIMEFRAMES = ("M5", "M15", "H1", "H4", "D1")
START = date(2015, 1, 1)
END = date(2021, 9, 13)  # day before the data split cut-off 2021-09-14
TOD_TIMEFRAME = "M5"
PERIOD_LABELS = ("whole", "first_half", "second_half")
EPOCH_TS = pd.Timestamp("1970-01-01", tz="UTC")
FINDING_COLUMNS = ["family", "symbol", "timeframe", "cell", "value", "p_value", "first_half",
                   "second_half", "siblings", "reason"]  # fmt: skip
MAX_LISTED_FINDINGS = 60


def _runs(days: Sequence[date]) -> list[tuple[date, date]]:
    """(first, last) of each run of consecutive days."""
    runs: list[list[date]] = []
    for d in days:
        if runs and d - runs[-1][1] == timedelta(days=1):
            runs[-1][1] = d
        else:
            runs.append([d, d])
    return [(a, b) for a, b in runs]


def missing_days(symbol: str, cache_dir: Path, start: date, end: date) -> list[date]:
    """Days between the first and last cached day in start..end that have no cache file
    (histdata.com has none for some New Year days)."""
    cached = sorted(d for d in cached_days(symbol, cache_dir) if start <= d <= end)
    have = set(cached)
    return [
        cached[0] + timedelta(days=i)
        for i in range((cached[-1] - cached[0]).days + 1)
        if cached[0] + timedelta(days=i) not in have
    ] if cached else []  # fmt: skip


def load_series(
    symbol: str, cache_dir: Path, timeframe: Timeframe, start: date, end: date
) -> tuple[np.ndarray, np.ndarray]:
    """(bar open times as epoch seconds, closes) of the cached days between `start` and `end`
    (both included). A day without a cache file splits the load into runs of consecutive
    days; the runs are joined, so the bar after the hole is an ordinary next bar. Reads the
    cache only."""
    cached = sorted(d for d in cached_days(symbol, cache_dir) if start <= d <= end)
    if not cached:
        raise ValueError(f"{symbol}: no cached days between {start} and {end}")
    adapter = CacheAdapter(cache_dir)
    frames = []
    for first, last in _runs(cached):
        stop = last + timedelta(days=1)
        frames.append(
            adapter.fetch_frame(
                symbol,
                timeframe,
                datetime(first.year, first.month, first.day, tzinfo=UTC),
                datetime(stop.year, stop.month, stop.day, tzinfo=UTC),
            )
        )
    frame = pd.concat(frames, ignore_index=True)
    secs = ((frame["ts"] - EPOCH_TS) // pd.Timedelta(seconds=1)).to_numpy(dtype="int64")
    return secs, frame["close"].to_numpy(dtype=float)


def analyze_symbol(job: tuple) -> dict:
    """One worker job: (symbol, cache_dir, timeframes, start, end, cfg) ->
    {"symbol", "rows": {family: [rows]}, "messages": [str]}."""
    symbol, cache_dir, timeframes, start, end, cfg = job
    rows: dict[str, list[dict]] = {
        "adf": [],
        "hurst": [],
        "vr": [],
        "lagcorr": [],
        "time_of_day": [],
    }
    messages: list[str] = []
    end = symbol_end(symbol, end, cfg)
    mid_day = (middle_date(start, end) - EPOCH).days
    dst_days = us_only_dst_days(cfg)
    holes = missing_days(symbol, Path(cache_dir), start, end)
    if holes:
        shown = ", ".join(d.isoformat() for d in holes[:8])
        messages.append(f"{symbol}: {len(holes)} day(s) without a cache file (bridged): {shown}")
    for tf_name in timeframes:
        try:
            secs, closes = load_series(symbol, Path(cache_dir), Timeframe[tf_name], start, end)
        except Exception as e:  # noqa: BLE001 - research tool: say what is missing, go on
            messages.append(f"{symbol} {tf_name}: skipped ({type(e).__name__}: {e})")
            continue
        ok = closes > 0
        secs, closes = secs[ok], closes[ok]
        split = int(np.searchsorted(secs // SECONDS_PER_DAY, mid_day, side="right"))
        for fam, found in series_rows(
            symbol, tf_name, np.log(closes), split, cfg, secs, Timeframe[tf_name].value * 60
        ).items():
            rows[fam] += found
        if tf_name == TOD_TIMEFRAME:
            parts = {
                "whole": slice(None),
                "first_half": slice(0, split),
                "second_half": slice(split, None),
            }
            shuffled = np.exp(shuffle_returns(np.log(closes), cfg))
            for source, series in (("real", closes), ("shuffled", shuffled)):
                for period, sl in parts.items():
                    for r in time_of_day_rows(secs[sl], series[sl], dst_days, cfg):
                        rows["time_of_day"].append(
                            {"symbol": symbol, "timeframe": tf_name, "period": period,
                             "source": source, **r}
                        )  # fmt: skip
        messages.append(f"{symbol} {tf_name}: {len(closes)} bars")
    return {"symbol": symbol, "rows": rows, "messages": messages}


def write_rows(path: Path, rows: Sequence[dict], columns: Sequence[str] | None = None) -> None:
    cols = list(columns or dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _pick(rows, symbol, tf, source, period="whole", **match):
    for r in rows:
        if (r["symbol"], r["timeframe"], r["source"], r["period"]) == (
            symbol,
            tf,
            source,
            period,
        ) and all(r.get(k) == v for k, v in match.items()):
            return r
    return None


def _num(r, key, fmt="{:.3f}"):
    return "-" if r is None or r.get(key) is None else fmt.format(r[key])


def summary_text(
    rows: dict[str, list[dict]], findings: list[dict], counts: dict, symbols: Sequence[str],
    timeframes: Sequence[str], cfg: StationarityConfig, shuffled_counts: dict | None = None,
) -> str:  # fmt: skip
    lines = [
        "STATIONARITY STUDY (ROADMAP 11.11, idea T-11)",
        (
            "Reading: ADF p < 0.05 = prices pull back to a mean (stationary); half-life in bars. "
            "Hurst < 0.5 = mean-reverting, > 0.5 = trending, 0.5 = random walk. VR(q) < 1 = "
            "reversal, > 1 = trend over q bars. 'RW' = a seeded random walk of the same length "
            "and volatility (the answer for no structure at all). The findings use the robust variants (Spearman rank correlation for the lag grid, returns clipped at 5 robust sd for VR and the time-of-day part); the plain columns stay in the CSV files."
        ),
        "",
        "CORE SYMBOLS FIRST, whole period (real vs RW), per timeframe:",
    ]
    ordered = [s for s in CORE if s in symbols] + [s for s in symbols if s not in CORE]
    for sym in ordered:
        for tf in timeframes:
            a, ar = _pick(rows["adf"], sym, tf, "real"), _pick(rows["adf"], sym, tf, "random_walk")
            h, hr = (
                _pick(rows["hurst"], sym, tf, "real"),
                _pick(rows["hurst"], sym, tf, "random_walk"),
            )
            if a is None and h is None:
                continue
            hl = _num(a, "half_life_bars", "{:.0f}")
            text = f"{sym} {tf}: ADF p {_num(a, 'p_value', '{:.2f}')} (RW {_num(ar, 'p_value', '{:.2f}')})"
            text += f", half-life {hl} bars, Hurst {_num(h, 'hurst')} (RW {_num(hr, 'hurst')})"
            for q in (cfg.vr_qs[0], cfg.vr_qs[-1]):
                v = _pick(rows["vr"], sym, tf, "real", q=q)
                vr = _pick(rows["vr"], sym, tf, "random_walk", q=q)
                text += (
                    f", VR({q}) {_num(v, 'vr')} z {_num(v, 'z', '{:+.1f}')} (RW {_num(vr, 'vr')})"
                )
            lines.append(text)
        if sym == CORE[-1] and len(ordered) > len(CORE):
            lines.append("-- other symbols --")
    lines += ["", "RANDOM-WALK SANITY (share of RW whole-period cells with p < 0.05, expect ~5 %):"]
    for fam, key in (("adf", "p_value"), ("vr", "p_value"), ("lagcorr", "p_value")):
        rw = [r[key] for r in rows[fam] if r["source"] == "random_walk" and r["period"] == "whole"]
        lines.append(f"  {fam}: {sum(p < 0.05 for p in rw)} of {len(rw)}" if rw else f"  {fam}: -")
    lines += [
        "",
        f"FAMILIES (Benjamini-Hochberg at q={cfg.bh_q} over the real whole-period cells):",
    ]
    for fam, c in counts.items():
        lines.append(
            f"  {fam}: {c['cells']} cells, {c['bh_significant']} BH-significant, {c['findings']} findings"
        )
    if shuffled_counts is not None:
        lines += [
            "",
            "SHUFFLED REFERENCE (the real returns in random order, same statistics, same rule;",
            "the honest answer is about 0 findings):",
        ]
        for fam, c in shuffled_counts.items():
            real = counts.get(fam, {}).get("findings", 0)
            lines.append(
                f"  {fam}: shuffled {c['findings']} findings ({c['bh_significant']} BH-significant "
                f"of {c['cells']} cells) vs real {real}"
            )
    lines.append(
        "  (finding = BH-significant, same sign in both halves, and the symbol plus >= "
        f"{cfg.min_siblings - 1} same-sign sibling in its group; Hurst has no p-value, not a family)"
    )
    lines += ["", f"FINDINGS ({len(findings)}; first {MAX_LISTED_FINDINGS} by p-value):"]
    for f in sorted(findings, key=lambda f: f["p_value"])[:MAX_LISTED_FINDINGS]:
        lines.append(
            f"  {f['family']} {f['symbol']} {f['timeframe']} {f['cell']}: value {f['value']:+.4g}, "
            f"p {f['p_value']:.2g}, halves {f['first_half']:+.4g} / {f['second_half']:+.4g}; "
            f"siblings {f['siblings']}"
        )
    if not findings:
        lines.append("  none")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument(
        "--cache-dir", type=Path, required=True, help="histdata cache folder (read only)"
    )
    p.add_argument("--symbols", nargs="+", default=list(ALL_SYMBOLS))
    p.add_argument("--timeframes", nargs="+", choices=TIMEFRAMES, default=list(TIMEFRAMES))
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=END)
    p.add_argument("--workers", type=int, default=1, help="processes, one symbol each")
    p.add_argument("--out", type=Path, default=RESULTS_DIR / "stationarity")
    args = p.parse_args(argv)

    cfg = StationarityConfig()
    symbols = [s.upper() for s in args.symbols]
    jobs = [
        (s, str(args.cache_dir), tuple(args.timeframes), args.start, args.end, cfg) for s in symbols
    ]
    started = time.time()
    if args.workers > 1 and len(jobs) > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(analyze_symbol, jobs))
    else:
        results = [analyze_symbol(j) for j in jobs]
    rows: dict[str, list[dict]] = {k: [] for k in ("adf", "hurst", "vr", "lagcorr", "time_of_day")}
    for res in results:
        for line in res["messages"]:
            print(line, flush=True)
        for fam, found in res["rows"].items():
            rows[fam] += found

    args.out.mkdir(parents=True, exist_ok=True)
    for fam in ("adf", "hurst", "vr", "lagcorr", "time_of_day"):
        name = {"adf": "adf", "hurst": "hurst", "vr": "vr", "lagcorr": "lagcorr"}.get(fam, fam)
        write_rows(args.out / f"{name}.csv", rows[fam])
    findings, counts = find_findings(cells_from_rows(rows), cfg)
    write_rows(args.out / "findings.csv", findings, FINDING_COLUMNS)
    shuffled_findings, shuffled_counts = find_findings(cells_from_rows(rows, "shuffled"), cfg)
    write_rows(args.out / "findings_shuffled.csv", shuffled_findings, FINDING_COLUMNS)
    done = [s for s in symbols if any(r["symbol"] == s for r in rows["adf"])]
    text = summary_text(
        rows, findings, counts, done, [t for t in args.timeframes], cfg, shuffled_counts
    )
    (args.out / "summary.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"written to {args.out} ({math.ceil(time.time() - started)} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
