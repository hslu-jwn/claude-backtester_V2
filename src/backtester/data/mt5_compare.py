"""Comparing FTMO's MT5 feed with the histdata cache. Spec: ROADMAP.md › 0.4.

Pure functions on DataFrames (no MetaTrader5 import), used by `data/mt5_info.py` (server
clock, symbols) and `data/feed_compare.py` (feed comparison, spreads):

- `weekly_offsets`: per week, the whole-hour offset (server time − UTC) that lines MT5's
  bars up with the cache's best (smallest median |close difference|).
- `fit_clock`: the `ServerClock` rule that predicts those offsets in the most weeks.
- `cached_frame`: cache candles over a range, reading only cached days.
- `compare_frames`, `best_shift`, `spread_by_hour`: the feed comparison.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import numpy as np
import pandas as pd

from backtester.core.models import Timeframe
from backtester.data.adapters.mt5_adapter import ServerClock
from backtester.data.sources import SymbolSources

OFFSETS = range(-12, 15)  # whole hours, server time − UTC
CLOCK_ZONES = ("UTC", "America/New_York", "Europe/London")  # fixed, US dates, EU dates
MIN_MATCHED_SHARE = 0.5  # a week counts when at least half its bars meet a cache candle


# --- cache over a range ------------------------------------------------------------------


def cached_runs(days: Iterable[date], start: date, end: date) -> list[tuple[date, date]]:
    """Runs of consecutive cached days inside [start, end] as (first, last)."""
    runs: list[tuple[date, date]] = []
    for d in sorted(d for d in set(days) if start <= d <= end):
        if runs and d - runs[-1][1] == timedelta(days=1):
            runs[-1] = (runs[-1][0], d)
        else:
            runs.append((d, d))
    return runs


def cached_frame(
    sources: SymbolSources, symbol: str, timeframe: Timeframe, start: date, end: date
) -> pd.DataFrame:
    """Cache candles of the cached days in [start, end] (UTC), oldest first."""
    adapter = sources.adapter(symbol)
    frames = []
    for first, last in cached_runs(sources.cached_days(symbol), start, end):
        lo = datetime(first.year, first.month, first.day, tzinfo=UTC)
        hi = datetime(last.year, last.month, last.day, tzinfo=UTC) + timedelta(days=1)
        frames.append(adapter.fetch_frame(symbol, timeframe, lo, hi))
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume", "spread"])
    return pd.concat(frames, ignore_index=True)


def _seconds(ts: pd.Series) -> np.ndarray:
    """UTC times as whole epoch seconds (whatever the datetime unit)."""
    epoch = pd.Timestamp(0, tz="UTC")
    return ((pd.to_datetime(ts, utc=True) - epoch) // pd.Timedelta(seconds=1)).to_numpy("int64")


# --- server clock ------------------------------------------------------------------------


def weekly_offsets(
    raw: pd.DataFrame, ref: pd.DataFrame, offsets: Sequence[int] = OFFSETS
) -> pd.DataFrame:
    """Per week of MT5 bars (`raw`: server seconds in `time`, `close`) the offset in whole
    hours that matches the cache candles (`ref`: UTC `ts`, `close`, `high`, `low`) best.

    Columns: week (Monday, server date), bars, matched (bars meeting a cache candle at the
    best offset), offset_h, error (median |close difference| there), runner_up_error (the
    next best offset's), range (median cache candle range that week)."""
    ref_close = pd.Series(ref["close"].to_numpy(), index=_seconds(ref["ts"]))
    ref_close = ref_close[~ref_close.index.duplicated()]
    ref_range = pd.Series((ref["high"] - ref["low"]).to_numpy(), index=ref_close.index)
    server = pd.to_datetime(raw["time"], unit="s")
    weeks = (server - pd.to_timedelta(server.dt.weekday, unit="D")).dt.normalize()
    rows = []
    for week, bars in raw.groupby(weeks.to_numpy()):
        times, closes = bars["time"].to_numpy(), bars["close"].to_numpy()
        scores = []
        for h in offsets:
            matched = ref_close.reindex(times - h * 3600).to_numpy()
            ok = ~np.isnan(matched)
            if ok.sum() >= max(10, MIN_MATCHED_SHARE * len(times)):
                error = float(np.median(np.abs(closes[ok] - matched[ok])))
                scores.append((error, h, int(ok.sum())))
        if not scores:
            continue
        scores.sort()
        error, h, matched_n = scores[0]
        week_range = ref_range.reindex(times - h * 3600).dropna()
        rows.append(
            {
                "week": pd.Timestamp(week).date(),
                "bars": len(times),
                "matched": matched_n,
                "offset_h": h,
                "error": error,
                "runner_up_error": scores[1][0] if len(scores) > 1 else float("nan"),
                "range": float(week_range.median()) if len(week_range) else float("nan"),
            }
        )
    return pd.DataFrame(
        rows,
        columns=["week", "bars", "matched", "offset_h", "error", "runner_up_error", "range"],
    )


def week_middle(week: date) -> datetime:
    """Wednesday 12:00 UTC of the week starting on Monday `week`."""
    return datetime(week.year, week.month, week.day, 12, tzinfo=UTC) + timedelta(days=2)


def predicted_offset(clock: ServerClock, week: date) -> int:
    return int(clock.offset_at(week_middle(week)) / timedelta(hours=1))


@dataclass(frozen=True)
class ClockFit:
    clock: ServerClock
    matched_weeks: int
    weeks: int
    misses: tuple[date, ...]  # weeks the rule gets wrong


def fit_clock(weeks: pd.DataFrame, zones: Sequence[str] = CLOCK_ZONES) -> list[ClockFit]:
    """Every candidate rule (zone + whole-hour shift) by how many weeks it predicts,
    best first; ties keep the order of `zones` (the simpler rule first)."""
    fits = []
    for zone_rank, zone in enumerate(zones):
        for shift in range(-14, 15):
            clock = ServerClock(zone, shift)
            misses = tuple(
                row.week
                for row in weeks.itertuples()
                if predicted_offset(clock, row.week) != row.offset_h
            )
            fits.append(
                (
                    len(weeks) - len(misses),
                    -zone_rank,
                    ClockFit(clock, len(weeks) - len(misses), len(weeks), misses),
                )
            )
    fits.sort(key=lambda f: (f[0], f[1]), reverse=True)
    return [f[2] for f in fits if f[2].matched_weeks > 0]


def discriminating_weeks(weeks: pd.DataFrame) -> pd.DataFrame:
    """Weeks where a US-dates rule and a Europe-dates rule give different offsets (only
    one of them on summer time): the weeks that decide between them."""
    us, eu = ServerClock("America/New_York", 0), ServerClock("Europe/London", 0)
    keep = [
        (predicted_offset(us, w) + 5) != predicted_offset(eu, w) for w in weeks["week"]
    ]  # New York is 5 h behind London except in those weeks
    return weeks[keep]


def live_offset_hours(tick_server_seconds: int, now: datetime) -> float:
    """Server time − UTC from the latest tick (only meaningful while the market trades)."""
    return (tick_server_seconds - now.timestamp()) / 3600


def tick_age(tick_server_seconds: int, clock: ServerClock, now: datetime) -> timedelta:
    """How long ago the latest tick was, if `clock` is right (negative: impossible)."""
    tick_utc = clock.to_utc([tick_server_seconds])[0].to_pydatetime()
    return now - tick_utc


# --- symbols -----------------------------------------------------------------------------

ALIASES = {"XAUUSD": ("GOLD",)}


def symbol_candidates(available: Iterable[str], wanted: str) -> list[str]:
    """The server's names for `wanted`: the same name, or it with a suffix (".r", "_x",
    "m", "-ecn", …), or a known alias (GOLD); exact first, then shortest."""
    out = []
    bases = (wanted, *ALIASES.get(wanted, ()))
    for name in available:
        upper = name.upper()
        for base in bases:
            if upper == base or (upper.startswith(base) and len(upper) - len(base) <= 5):
                out.append(name)
                break
    return sorted(out, key=lambda n: (n.upper() not in bases, len(n), n))


SWAP_MODES = {
    0: "disabled",
    1: "points",
    2: "money (base currency)",
    3: "money (margin currency)",
    4: "money (deposit currency)",
    5: "interest (current price)",
    6: "interest (open price)",
    7: "reopen (current price)",
    8: "reopen (bid)",
}
TRADE_MODES = {0: "disabled", 1: "long only", 2: "short only", 3: "close only", 4: "full"}
EXECUTION_MODES = {0: "request", 1: "instant", 2: "market", 3: "exchange"}
WEEKDAYS = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")


def filling_names(flags: int) -> str:
    names = [n for bit, n in ((1, "FOK"), (2, "IOC"), (4, "BOC")) if flags & bit]
    return ", ".join(names) or "RETURN only"


def symbol_specs(info) -> dict[str, str]:
    """The specs of a `symbol_info` result, readable."""
    point = info.point
    triple = getattr(info, "swap_rollover3days", None)
    return {
        "name": info.name,
        "description": getattr(info, "description", ""),
        "contract size": f"{info.trade_contract_size:g}",
        "digits": str(info.digits),
        "point": f"{point:g}",
        "tick size": f"{info.trade_tick_size:g}",
        "tick value": f"{info.trade_tick_value:g} ({info.currency_profit} → account currency)",
        "volume min / step / max": f"{info.volume_min:g} / {info.volume_step:g} / {info.volume_max:g}",
        "stops level": f"{info.trade_stops_level} points ({info.trade_stops_level * point:g})",
        "freeze level": f"{info.trade_freeze_level} points",
        "swap long / short": f"{info.swap_long:g} / {info.swap_short:g} "
        f"({SWAP_MODES.get(info.swap_mode, info.swap_mode)})"
        + (f", triple on {WEEKDAYS[triple]}" if triple is not None and 0 <= triple < 7 else ""),
        "trade mode": TRADE_MODES.get(info.trade_mode, str(info.trade_mode)),
        "execution": EXECUTION_MODES.get(info.trade_exemode, str(info.trade_exemode)),
        "filling": filling_names(info.filling_mode),
        "currencies": f"{info.currency_base} / {info.currency_profit}",
        "spread now": f"{info.spread} points ({info.spread * point:g})",
    }
