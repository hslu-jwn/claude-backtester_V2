"""FTMO's MT5 feed vs the histdata cache, and FTMO's spreads. Spec: ROADMAP.md › 0.4.

    python -m backtester.data.feed_compare [XAUUSD GBPUSD GBPJPY]

Needs the server clock and symbol names in `results/trading.json`
(`python -m backtester.data.mt5_info` first). Per symbol and timeframe (M1, M5, M30, H1),
over the days both MT5's history and the cache have:

- time alignment: the shift of MT5's candle times that matches the cache best (0 when the
  clock is right),
- average |difference| of open / high / low / close, in price and as a share of the median
  candle range,
- how often the candle color differs (and how often it is the opposite color, flat
  candles not counted),
- candles only MT5 or only the cache has.

Spreads: MT5's spread per candle (M1, else M5) per UTC hour: median and 90th percentile,
next to the cost defaults (ROADMAP 3.1). Report only; nothing is changed.

Printed and written to `results/feed_compare/<time>/` (report.md, compare.csv,
spread_<SYMBOL>.csv).
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from backtester.cli import utf8_output
from backtester.core.models import Timeframe
from backtester.data.adapters.mt5_adapter import Mt5Adapter
from backtester.data.mt5_compare import (
    COMPARE_TIMEFRAMES,
    best_shift,
    cached_frame,
    compare_frames,
    on_days,
    spread_by_hour,
)
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.costs import DEFAULT_SYMBOL_COSTS
from backtester.live.trading_settings import SYMBOLS, load_trading_settings
from backtester.runner import RESULTS_DIR

OUT_DIR = RESULTS_DIR / "feed_compare"
SPREAD_TIMEFRAMES = (Timeframe.M1, Timeframe.M5)


def _shift_text(shift: timedelta) -> str:
    minutes = int(shift / timedelta(minutes=1))
    return "0" if minutes == 0 else f"{minutes:+d} min"


def compare_symbol(
    adapter: Mt5Adapter,
    sources: SymbolSources,
    symbol: str,
    timeframes=COMPARE_TIMEFRAMES,
) -> tuple[list[dict], dict[Timeframe, pd.DataFrame]]:
    """One row per timeframe and MT5's full history per timeframe (for the spreads)."""
    cached = set(sources.cached_days(symbol))
    rows, history = [], {}
    for tf in timeframes:
        mt5 = adapter.history(symbol, tf)
        history[tf] = mt5
        row = {"symbol": symbol, "timeframe": tf.name, "mt5_candles_all": len(mt5)}
        if mt5.empty:
            rows.append(row)
            continue
        row["mt5_first"], row["mt5_last"] = mt5["ts"].iloc[0], mt5["ts"].iloc[-1]
        days = sorted({ts.date() for ts in mt5["ts"]} & cached)
        row["days_both"] = len(days)
        if not days:
            rows.append(row)
            continue
        mt5_on = on_days(mt5, days)
        ref = on_days(cached_frame(sources, symbol, tf, days[0], days[-1]), days)
        shift, shift_error, zero_error = best_shift(mt5_on, ref, tf)
        row.update(best_shift=shift, best_shift_error=shift_error, zero_shift_error=zero_error)
        row.update(compare_frames(mt5_on, ref))
        rows.append(row)
    return rows, history


def compare_table(rows: list[dict]) -> list[str]:
    head = (
        "| symbol | TF | MT5 history (UTC) | days in both | matched | best shift "
        "| avg abs diff O / H / L / C | in % of median range | color differs | opposite "
        "| only MT5 | only cache |"
    )
    lines = [head, "|" + "---|" * 12]
    for r in rows:
        if not r.get("matched"):
            span = f"{r['mt5_first']:%Y-%m-%d %H:%M} ..." if "mt5_first" in r else "none"
            lines.append(
                f"| {r['symbol']} | {r['timeframe']} | {span} | {r.get('days_both', 0)} "
                "| 0 | | | | | | | |"
            )
            continue
        diffs = " / ".join(f"{r[f'{f}_diff']:.5g}" for f in ("open", "high", "low", "close"))
        rel = " / ".join(f"{r[f'{f}_diff_rel']:.1%}" for f in ("open", "high", "low", "close"))
        lines.append(
            f"| {r['symbol']} | {r['timeframe']} "
            f"| {r['mt5_first']:%Y-%m-%d %H:%M} .. {r['mt5_last']:%Y-%m-%d %H:%M} "
            f"| {r['days_both']} | {r['matched']:,} | {_shift_text(r['best_shift'])} "
            f"| {diffs} | {rel} | {r['color_differs']:.1%} | {r['color_opposite']:.1%} "
            f"| {r['only_mt5']:,} | {r['only_cache']:,} |"
        )
    return lines


def missing_examples(rows: list[dict]) -> list[str]:
    lines = []
    for r in rows:
        for side, label in (("only_mt5", "only MT5"), ("only_cache", "only cache")):
            examples = r.get(f"{side}_examples") or []
            if examples:
                times = ", ".join(f"{t:%Y-%m-%d %H:%M}" for t in examples)
                lines.append(f"- {r['symbol']} {r['timeframe']} {label} (first): {times}")
    return lines


def spread_report(symbol: str, history: dict[Timeframe, pd.DataFrame], point: float):
    """(table lines, per-hour frame) of the spreads, M1 if MT5 has it, else M5."""
    tf = next((t for t in SPREAD_TIMEFRAMES if not history.get(t, pd.DataFrame()).empty), None)
    if tf is None:
        return [f"{symbol}: no M1 / M5 history for spreads."], pd.DataFrame()
    candles = history[tf]
    table = spread_by_hour(candles)
    default = DEFAULT_SYMBOL_COSTS[symbol].spread if symbol in DEFAULT_SYMBOL_COSTS else None
    first, last = candles["ts"].iloc[0], candles["ts"].iloc[-1]
    lines = [
        f"**{symbol}** ({tf.name} candles {first:%Y-%m-%d} .. {last:%Y-%m-%d}, price units; "
        f"points = / {point:g}). Cost default (3.1): "
        + (f"{default:g}" if default is not None else "none"),
        "",
        "| UTC hour | candles | median | 90% | median / default |",
        "|---|---|---|---|---|",
    ]
    for r in table.itertuples():
        ratio = f"{r.median / default:.2f}x" if default else ""
        lines.append(
            f"| {r.hour} | {r.candles:,} | {r.median:.5g} ({r.median / point:.0f} pt) "
            f"| {r.p90:.5g} ({r.p90 / point:.0f} pt) | {ratio} |"
        )
    return lines, table


def main(argv: list[str] | None = None) -> int:
    from backtester.live.connection import session
    from backtester.live.credentials import CredentialStoreError, load_credentials

    utf8_output()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("symbols", nargs="*", default=list(SYMBOLS))
    args = p.parse_args(argv)
    settings = load_trading_settings()
    if settings.server_clock is None:
        print("The server clock is not measured yet: run python -m backtester.data.mt5_info")
        return 1
    try:
        credentials = load_credentials(settings.platform)
    except CredentialStoreError as e:
        print(f"Credential store: {e}; using the terminal's logged-in account.")
        credentials = None
    rows, spread_lines, spreads = [], [], {}
    with session(settings, credentials) as mt5:
        adapter = Mt5Adapter(mt5, settings.server_clock, settings.symbols)
        for symbol in args.symbols:
            print(f"{symbol} ({adapter.broker_symbol(symbol)}) …", flush=True)
            symbol_rows, history = compare_symbol(adapter, DEFAULT_SOURCES, symbol)
            rows += symbol_rows
            lines, table = spread_report(symbol, history, adapter.point(symbol))
            spread_lines += [*lines, ""]
            spreads[symbol] = table
    report = [
        f"# Feed comparison {datetime.now(UTC):%Y-%m-%d %H:%M} UTC",
        "",
        (
            f"FTMO (MT5, server clock {settings.server_clock.label}) vs the histdata cache, "
            "on the days both have; differences are |FTMO − cache|."
        ),
        "",
        *compare_table(rows),
        "",
        *missing_examples(rows),
        "",
        "## FTMO spreads per UTC hour",
        "",
        *spread_lines,
    ]
    text = "\n".join(report)
    print(text)
    out = Path(OUT_DIR) / datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(text, encoding="utf-8")
    flat = [{k: v for k, v in r.items() if not k.endswith("_examples")} for r in rows]
    pd.DataFrame(flat).to_csv(out / "compare.csv", index=False)
    for symbol, table in spreads.items():
        table.to_csv(out / f"spread_{symbol}.csv", index=False)
    print(f"\nWritten to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
