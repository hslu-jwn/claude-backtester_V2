"""Build higher-timeframe candles from cached Dukascopy M1 rows.

Spec: ARCHITECTURE.md › Data sources › Dukascopy, ROADMAP.md › 0.2.

1. Flat zero-volume minutes (Dukascopy's filler for the daily break, weekends and holidays)
   are dropped, so those periods become gaps like on TradingView.
2. The remaining minutes are grouped into UTC-aligned buckets (`ts` floored to the
   timeframe). A bucket with no minutes left produces no candle; a partly filled bucket keeps
   its regular open time, and its close time stays `ts + timeframe.duration`.

Candles are built from the bid side (what the chart shows). `spread` is the mean of the
per-minute close spreads (ask_close − bid_close) over the candle's minutes; NaN if no minute
in the candle has an ask price.
"""

from __future__ import annotations

import pandas as pd

from backtester.core.models import Timeframe

CANDLE_COLUMNS = ["ts", "open", "high", "low", "close", "volume", "spread"]


def supported(timeframe: Timeframe) -> bool:
    """Timeframes whose UTC buckets tile a day exactly. D1 is excluded: a UTC-midnight day
    does not match the market's trading day (e.g. gold reopens at 22:00/23:00 UTC)."""
    return timeframe is not Timeframe.D1 and Timeframe.D1.value % timeframe.value == 0


def drop_flat_minutes(m1: pd.DataFrame) -> pd.DataFrame:
    """Remove minutes with bid O = H = L = C and zero bid volume, and minutes without a bid.

    A flat minute that has volume is a real (quiet) minute and is kept.
    """
    flat = (
        (m1["bid_open"] == m1["bid_high"])
        & (m1["bid_high"] == m1["bid_low"])
        & (m1["bid_low"] == m1["bid_close"])
        & (m1["bid_volume"] == 0)
    )
    return m1[~flat & m1["bid_close"].notna()]


def resample(m1: pd.DataFrame, timeframe: Timeframe) -> pd.DataFrame:
    """Aggregate cached M1 rows (already without flat minutes) into `timeframe` candles.

    Returns columns CANDLE_COLUMNS, oldest first, `ts` = candle open time (UTC).
    """
    if not supported(timeframe):
        raise ValueError(f"{timeframe.name} cannot be resampled from UTC-aligned minutes")
    if m1.empty:
        return pd.DataFrame({c: pd.Series(dtype="float64") for c in CANDLE_COLUMNS[1:]}).assign(
            ts=pd.Series(dtype="datetime64[ns, UTC]")
        )[CANDLE_COLUMNS]

    frame = m1.sort_values("ts").assign(minute_spread=m1["ask_close"] - m1["bid_close"])
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
