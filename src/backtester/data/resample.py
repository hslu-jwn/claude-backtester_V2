"""Build higher-timeframe candles from cached M1 rows (Dukascopy or histdata.com).

Spec: ARCHITECTURE.md › Data sources › Dukascopy, ROADMAP.md › 0.2.

1. Flat zero-volume minutes (Dukascopy's filler for the daily break, weekends and holidays)
   are dropped, so those periods become gaps like on TradingView.
2. The remaining minutes are grouped into UTC-aligned buckets (`ts` floored to the
   timeframe). A bucket with no minutes left produces no candle; a partly filled bucket keeps
   its regular open time, and its close time stays `ts + timeframe.duration`.

Candles are built from the bid side (what the chart shows). `spread` is the mean of the
per-minute close spreads (ask_close − bid_close) over the candle's minutes; NaN if no minute
in the candle has an ask price.

Daily and weekly candles (ROADMAP.md › 4.0b part 2) follow the trading day instead
(`DayBoundary`, default like TradingView for forex / gold): a day runs from 17:00 New York
to 17:00 New York (zoneinfo America/New_York, so 21:00 or 22:00 UTC depending on DST), a
week from the Sunday 17:00 open to the Friday 17:00 close; the option `UTC` uses UTC
midnight (weeks Sunday 00:00 to Sunday 00:00 UTC). Their `ts` is the candle's CLOSE minus
the timeframe's duration, so "closed at `ts + duration`" holds exactly (also on DST switch
days, when a trading day isn't 24 hours); `calendar_label` gives the day a candle is named
by on the chart (D: its trading day, W: the Monday of its week).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import Enum

import pandas as pd

from backtester.core.models import Timeframe

CANDLE_COLUMNS = ["ts", "open", "high", "low", "close", "volume", "spread"]
CALENDAR = (Timeframe.D1, Timeframe.W1)  # built from trading days, not UTC buckets
NEW_YORK = "America/New_York"
_ROLLOVER = timedelta(hours=7)  # 17:00 New York + 7 h = midnight of the next trading day


class DayBoundary(Enum):
    NEW_YORK_17 = "17:00 New York"  # TradingView for forex / gold
    UTC = "UTC midnight"


DEFAULT_BOUNDARY = DayBoundary.NEW_YORK_17


def supported(timeframe: Timeframe) -> bool:
    """Timeframes whose UTC buckets tile a day exactly, plus D and W (trading days)."""
    return timeframe in CALENDAR or Timeframe.D1.value % timeframe.value == 0


def candle_close(ts: pd.Series, timeframe: Timeframe, boundary: DayBoundary) -> pd.Series:
    """Close time (UTC) of the D / W candle each minute (open time `ts`, UTC) belongs to."""
    if boundary is DayBoundary.UTC:
        day = ts.dt.floor("D")
        if timeframe is Timeframe.D1:
            return day + pd.Timedelta(days=1)
        sunday = day - pd.to_timedelta((day.dt.weekday + 1) % 7, unit="D")
        return sunday + pd.Timedelta(days=7)
    local = ts.dt.tz_convert(NEW_YORK)
    trading_day = (local + _ROLLOVER).dt.tz_localize(None).dt.normalize()
    if timeframe is Timeframe.W1:  # the Friday that closes the week
        trading_day = trading_day + pd.to_timedelta((4 - trading_day.dt.weekday) % 7, unit="D")
    close_local = (trading_day + pd.Timedelta(hours=17)).dt.tz_localize(NEW_YORK)
    return close_local.dt.tz_convert("UTC")


def calendar_label(ts: datetime, timeframe: Timeframe, boundary: DayBoundary) -> date:
    """The day a D / W candle (open time `ts` as built here) is named by: D its trading day
    (the day it closes), W the Monday of its week."""
    close = ts + timeframe.duration
    if boundary is DayBoundary.UTC:
        day = (close - timedelta(microseconds=1)).date()
        return day if timeframe is Timeframe.D1 else (close - timedelta(days=6)).date()
    day = pd.Timestamp(close).tz_convert(NEW_YORK).date()
    return day if timeframe is Timeframe.D1 else day - timedelta(days=4)


def drop_flat_minutes(m1: pd.DataFrame) -> pd.DataFrame:
    """Remove minutes with bid O = H = L = C and zero bid volume, and minutes without a bid.

    A flat minute that has volume is a real (quiet) minute and is kept. So is a flat minute
    whose volume is unknown (NaN): sources like histdata.com (`data/histdata.py`) leave
    non-trading minutes out instead of filling them, so every minute they have is real.
    """
    flat = (
        (m1["bid_open"] == m1["bid_high"])
        & (m1["bid_high"] == m1["bid_low"])
        & (m1["bid_low"] == m1["bid_close"])
        & (m1["bid_volume"] == 0)
    )
    return m1[~flat & m1["bid_close"].notna()]


def resample(
    m1: pd.DataFrame, timeframe: Timeframe, boundary: DayBoundary = DEFAULT_BOUNDARY
) -> pd.DataFrame:
    """Aggregate cached M1 rows (already without flat minutes) into `timeframe` candles.

    Returns columns CANDLE_COLUMNS, oldest first, `ts` = candle open time (UTC); for D / W
    the close minus the duration (see the module docstring), `boundary` = their day.
    """
    if not supported(timeframe):
        raise ValueError(f"{timeframe.name} cannot be resampled from UTC-aligned minutes")
    if m1.empty:
        return pd.DataFrame({c: pd.Series(dtype="float64") for c in CANDLE_COLUMNS[1:]}).assign(
            ts=pd.Series(dtype="datetime64[ns, UTC]")
        )[CANDLE_COLUMNS]

    frame = m1.sort_values("ts").assign(minute_spread=m1["ask_close"] - m1["bid_close"])
    if timeframe in CALENDAR:
        bucket = candle_close(frame["ts"], timeframe, boundary) - timeframe.duration
    else:
        bucket = frame["ts"].dt.floor(f"{timeframe.value}min")
    out = (
        frame.groupby(bucket, sort=True)
        .agg(
            open=("bid_open", "first"),
            high=("bid_high", "max"),
            low=("bid_low", "min"),
            close=("bid_close", "last"),
            volume=("bid_volume", "sum"),
            spread=("minute_spread", "mean"),
        )
        .reset_index()
    )
    return out[CANDLE_COLUMNS]
