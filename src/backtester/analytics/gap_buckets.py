"""Gap-bucket study of strategy 7: open-to-close return per gap size, momentum against fade.

Spec: docs/strategy-gap-momentum.md > Backtest options (study part, ROADMAP 11.12, I-09 / C-5).
One record per regular session day (`gap_days`, the same `SessionStats` as the strategy, so the
sd, the ATR and the prior range are exactly what the strategy sees at the open): open price,
prior high / low / close, sd of the daily log returns, daily ATR and the close of the session's
closing candle. `bucket_rows` groups them by the size of the gap to the previous close in sd
units, by up / down and by beyond / inside the prior range, and gives the move after the open
in sd units for both sides (momentum = with the gap, fade = against it) on the same days.
Pure functions, no pandas.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from itertools import pairwise, product
from zoneinfo import ZoneInfo

from backtester.analytics.open_gap import mean_t
from backtester.core.models import Candle
from backtester.strategy.gap_momentum.config import GapMomentumConfig
from backtester.strategy.session_stats import SessionStats

# lower edges in sd units; the last bucket is open-ended (spec: 0-0.1, 0.1-0.25, 0.25-0.5, 0.5-1, >1)
BUCKET_EDGES = (0.0, 0.1, 0.25, 0.5, 1.0)
ALL = "all"
HALVES = ("all", "first", "second")
LOCATIONS = ("beyond", "inside")
DIRECTIONS = ("up", "down")


@dataclass(frozen=True, slots=True)
class GapDay:
    day: date
    open: float  # close of the candle closing at the session open
    prev_high: float
    prev_low: float
    prev_close: float
    sd: float
    atr: float
    close: float  # close of the candle closing at the session close


def gap_days(
    bars: Iterable[tuple[datetime, float, float, float]], config: GapMomentumConfig
) -> list[GapDay]:
    """Regular days with all inputs known. `bars` = (close time, high, low, close) of the 1m
    candles closing in [session open, session close], in time order."""
    tz = ZoneInfo(config.zone)
    stats = SessionStats(
        config.session_open,
        config.session_close,
        config.atr_period,
        config.vol_days,
        config.close_tolerance_min,
    )
    out: list[GapDay] = []
    pending: dict | None = None
    last: tuple[datetime, float] | None = None

    def finalize() -> None:
        if pending is None or last is None or last[0].date() != pending["day"]:
            return
        deadline = datetime.combine(pending["day"], config.session_close)
        lag = (deadline - last[0].replace(tzinfo=None)).total_seconds()
        if 0 <= lag <= config.close_tolerance_min * 60:
            out.append(GapDay(close=last[1], **pending))

    for close_time, high, low, close in bars:
        local = close_time.astimezone(tz)
        t = local.time()
        if pending and (local.date() != pending["day"] or t > config.session_close):
            finalize()
            pending, last = None, None
        if t == config.session_open:
            finalize()
            last = None
            stats.finish()
            sd, atr = stats.vol_sd(), stats.atr
            known = stats.prev_regular and sd is not None and atr is not None and atr > 0
            pending = None
            if known:
                pending = {
                    "day": local.date(), "open": close, "prev_high": stats.prev_high,
                    "prev_low": stats.prev_low, "prev_close": stats.prev_close, "sd": sd,
                    "atr": atr,
                }  # fmt: skip
        elif config.session_open < t <= config.session_close:
            candle = Candle(ts=close_time, open=close, high=high, low=low, close=close)
            stats.take_in(local.date(), t, candle)
            last = local, close
    finalize()
    return out


def bucket_label(gap_sd: float) -> str:
    """Bucket of an absolute gap in sd units (lower edge inclusive)."""
    gap_sd = abs(gap_sd)
    for lo, hi in pairwise(BUCKET_EDGES):
        if lo <= gap_sd < hi:
            return f"{lo:g}-{hi:g}"
    return f">{BUCKET_EDGES[-1]:g}"


def bucket_labels() -> list[str]:
    return [bucket_label(lo) for lo in BUCKET_EDGES]


def _row(symbol: str, half: str, bucket: str, location: str, direction: str, moves, atrs) -> dict:
    """`moves` / `atrs` = momentum move in sd / ATR units of the days in the cell."""
    mean, t = mean_t(moves)
    return {
        "symbol": symbol,
        "half": half,
        "bucket": bucket,
        "location": location,
        "direction": direction,
        "n": len(moves),
        "mean_sd_momentum": mean,
        "t_momentum": t,
        "share_positive_momentum": sum(m > 0 for m in moves) / len(moves),
        "mean_atr_momentum": sum(atrs) / len(atrs),
        "mean_sd_fade": -mean,
        "t_fade": None if t is None else -t,
    }


def bucket_rows(days: Iterable[GapDay], symbol: str, middle: date) -> list[dict]:
    """Rows per half x bucket x location x direction, each also as an `all` roll-up; a cell
    without days has no row. A zero gap has no direction and is left out. `middle` is the last
    day of the first half."""
    cells = []
    for g in days:
        if g.open == g.prev_close:
            continue
        up = g.open > g.prev_close
        sign = 1 if up else -1
        beyond = g.open > g.prev_high if up else g.open < g.prev_low
        gap_sd = math.log(g.open / g.prev_close) / g.sd
        move_sd = sign * math.log(g.close / g.open) / g.sd
        move_atr = sign * (g.close - g.open) / g.atr
        cells.append((
            "first" if g.day <= middle else "second", bucket_label(gap_sd),
            "beyond" if beyond else "inside", "up" if up else "down", move_sd, move_atr,
        ))  # fmt: skip
    rows = []
    for half, bucket, location, direction in product(
        HALVES, [*bucket_labels(), ALL], [*LOCATIONS, ALL], [*DIRECTIONS, ALL]
    ):
        picked = [
            c for c in cells
            if half in (ALL, c[0]) and bucket in (ALL, c[1])
            and location in (ALL, c[2]) and direction in (ALL, c[3])
        ]  # fmt: skip
        if picked:
            rows.append(_row(symbol, half, bucket, location, direction,
                             [c[4] for c in picked], [c[5] for c in picked]))  # fmt: skip
    return rows
