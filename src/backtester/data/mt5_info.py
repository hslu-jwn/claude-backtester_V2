"""FTMO's symbol names and specs, and the server clock. Spec: ROADMAP.md › 0.4.

    python -m backtester.data.mt5_info [XAUUSD GBPUSD GBPJPY] [--no-save]

Connects with the login saved in Settings ⚙ → Trading (or the account the running
terminal is logged in to), then:

1. Symbols: the server's name for each of ours (suffixes possible) and its specs
   (contract size, digits, tick size / value, volume min / step / max, stops level, swap,
   trade mode, filling).
2. Server clock: per week of MT5's H1 history, the whole-hour offset that lines it up with
   the histdata cache (`mt5_compare.weekly_offsets`), the rule that predicts every week
   (`fit_clock`), the weeks where only the US or only Europe is on summer time, and the
   latest tick against real UTC.

Saves the symbol names and, when one rule predicts every week, the clock to
`results/trading.json` (not with --no-save). Prints no login, password or server name.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pandas as pd

from backtester.cli import utf8_output
from backtester.core.models import Timeframe
from backtester.data.adapters.mt5_adapter import EPOCH, Mt5Adapter, ServerClock
from backtester.data.mt5_compare import (
    cached_frame,
    discriminating_weeks,
    fit_clock,
    live_offset_hours,
    predicted_offset,
    symbol_candidates,
    symbol_specs,
    tick_age,
    weekly_offsets,
)
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.live.trading_settings import (
    SYMBOLS,
    load_trading_settings,
    save_trading_settings,
)

CLOCK_TIMEFRAME = Timeframe.H1
MAX_TICK_AGE = timedelta(minutes=5)  # a fresher tick confirms the clock live


def find_symbols(mt5, wanted: list[str]) -> dict[str, list[str]]:
    available = [s.name for s in (mt5.symbols_get() or ())]
    return {w: symbol_candidates(available, w) for w in wanted}


def raw_history(mt5, name: str, timeframe: Timeframe, now: datetime) -> pd.DataFrame:
    """All bars of `name` in server seconds (no clock needed: the identity is enough to
    ask for "everything")."""
    adapter = Mt5Adapter(mt5, ServerClock(), {})
    far = now + timedelta(days=2)
    return adapter.raw_frame(name, timeframe, EPOCH + timedelta(days=1), far.replace(tzinfo=UTC))


def measure_clock(
    mt5, names: dict[str, str], sources: SymbolSources, now: datetime
) -> tuple[pd.DataFrame, list[str]]:
    """Weekly offsets of every symbol (column `symbol` added) and the report lines."""
    lines, frames = [], []
    for symbol, name in names.items():
        raw = raw_history(mt5, name, CLOCK_TIMEFRAME, now)
        if raw.empty:
            lines.append(f"{symbol}: no {CLOCK_TIMEFRAME.name} history on the server")
            continue
        first = datetime.fromtimestamp(int(raw["time"].iloc[0]), UTC).date()
        last = datetime.fromtimestamp(int(raw["time"].iloc[-1]), UTC).date()
        ref = cached_frame(
            sources, symbol, CLOCK_TIMEFRAME, first - timedelta(days=1), last + timedelta(days=1)
        )
        weeks = weekly_offsets(raw, ref)
        lines.append(
            f"{symbol} ({name}): MT5 {CLOCK_TIMEFRAME.name} from {first} (server date), "
            f"{len(raw):,} bars; {len(weeks)} weeks overlap the cache"
        )
        if not weeks.empty:
            frames.append(weeks.assign(symbol=symbol))
    weeks = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return weeks, lines


def clock_report(weeks: pd.DataFrame) -> tuple[ServerClock | None, list[str]]:
    if weeks.empty:
        return None, ["No week of MT5 history overlaps the cache: the clock can't be measured."]
    lines = []
    for symbol, group in weeks.groupby("symbol"):
        counts = group["offset_h"].value_counts().sort_index()
        found = ", ".join(f"UTC{h:+d} h: {n} weeks" for h, n in counts.items())
        rel = (group["error"] / group["range"]).median()
        margin = (group["runner_up_error"] / group["error"].clip(lower=1e-12)).median()
        lines.append(
            f"{symbol}: {found}; median |close diff| at the best offset {rel:.1%} of the "
            f"candle range, next best offset {margin:.0f}x worse"
        )
    fits = fit_clock(weeks.drop_duplicates(["symbol", "week"]))
    best = fits[0]
    lines.append("Rules (server time = zone time + shift), weeks predicted:")
    for fit in fits[:3]:
        lines.append(f"  {fit.clock.label}: {fit.matched_weeks} / {fit.weeks}")
    if best.misses:
        lines.append(f"  {best.clock.label} misses: {', '.join(map(str, best.misses[:12]))}")
    deciding = discriminating_weeks(weeks)
    if deciding.empty:
        lines.append("No week with only the US or only Europe on summer time in the overlap.")
    else:
        lines.append("Weeks with only the US or only Europe on summer time (they decide):")
        for row in deciding.drop_duplicates(["week", "offset_h"]).itertuples():
            lines.append(
                f"  {row.week} ({row.symbol}): measured UTC{row.offset_h:+d} h, "
                f"rule says UTC{predicted_offset(best.clock, row.week):+d} h"
            )
    unique = best.matched_weeks == best.weeks and (
        len(fits) < 2 or fits[1].matched_weeks < best.weeks
    )
    if not unique:
        lines.append("No single rule predicts every week: nothing saved, check the misses.")
        return None, lines
    return best.clock, lines


def live_check(mt5, names: list[str], clock: ServerClock | None, now: datetime) -> list[str]:
    ticks = [t for t in (mt5.symbol_info_tick(n) for n in names) if t is not None]
    if not ticks:
        return ["Latest tick: none."]
    latest = max(t.time for t in ticks)
    hours = live_offset_hours(latest, now)
    lines = [f"Latest tick: server time − UTC now = {hours:+.2f} h"]
    if clock is not None:
        age = tick_age(latest, clock, now)
        expected = clock.offset_at(now) / timedelta(hours=1)
        verdict = (
            "agrees (market open, tick is fresh)"
            if timedelta(0) <= age <= MAX_TICK_AGE
            else f"tick is {age} old for this rule (market closed?), no live confirmation"
        )
        lines.append(f"  rule {clock.label} says UTC{expected:+.0f} h now: {verdict}")
    return lines


def main(argv: list[str] | None = None) -> int:
    from backtester.live.connection import session
    from backtester.live.credentials import CredentialStoreError, load_credentials

    utf8_output()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("symbols", nargs="*", default=list(SYMBOLS))
    p.add_argument("--no-save", action="store_true", help="only print, change no setting")
    args = p.parse_args(argv)
    settings = load_trading_settings()
    try:
        credentials = load_credentials(settings.platform)
    except CredentialStoreError as e:
        print(f"Credential store: {e}; using the terminal's logged-in account.")
        credentials = None
    now = datetime.now(UTC)
    with session(settings, credentials) as mt5:
        print("== Symbols")
        found = find_symbols(mt5, args.symbols)
        names: dict[str, str] = {}
        for symbol, candidates in found.items():
            if not candidates:
                print(f"{symbol}: not found on the server")
                continue
            name = candidates[0]
            names[symbol] = name
            others = f" (also: {', '.join(candidates[1:])})" if len(candidates) > 1 else ""
            print(f"{symbol} → {name}{others}")
            mt5.symbol_select(name, True)
            for key, value in symbol_specs(mt5.symbol_info(name)).items():
                print(f"    {key}: {value}")
        print("\n== Server clock")
        weeks, lines = measure_clock(mt5, names, DEFAULT_SOURCES, now)
        clock, fit_lines = clock_report(weeks)
        print("\n".join(lines + fit_lines))
        print("\n".join(live_check(mt5, list(names.values()), clock, now)))
    if args.no_save:
        return 0
    settings = settings.with_symbols(names)
    if clock is not None:
        first, last = weeks["week"].min(), weeks["week"].max()
        note = f"measured {now:%Y-%m-%d} on {weeks['week'].nunique()} weeks {first}..{last}"
        settings = replace(settings, server_clock=clock, server_clock_note=note)
    save_trading_settings(settings)
    print(
        "\nSaved to results/trading.json: symbol names"
        + (f", server clock {clock.label}" if clock else " (clock not saved)")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
