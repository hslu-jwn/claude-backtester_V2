"""Resampling M1 cache rows into 5m / 30m / 1h candles. Spec: ROADMAP.md › 0.2."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest
from m1_frames import m1

from backtester.core.models import Timeframe
from backtester.data.resample import drop_flat_minutes, resample, supported


def flat(hhmm: str, price: float = 100.0) -> tuple:
    return (hhmm, price, price, price, price, 0.0, 0.5)


def utc(hhmm: str) -> datetime:
    h, m = map(int, hhmm.split(":"))
    return datetime(2026, 9, 2, h, m, tzinfo=UTC)


def test_ten_minutes_make_two_5m_candles():
    rows = m1(
        ("10:00", 100.0, 101.0, 99.5, 100.5, 1.0, 0.2),
        ("10:01", 100.5, 102.0, 100.0, 101.5, 1.0, 0.2),
        ("10:02", 101.5, 101.8, 98.0, 99.0, 1.0, 0.4),  # low of the first candle
        ("10:03", 99.0, 99.5, 98.5, 99.2, 1.0, 0.2),
        ("10:04", 99.2, 100.0, 99.0, 99.8, 1.0, 0.3),  # close of the first candle
        ("10:05", 99.8, 103.0, 99.7, 102.5, 2.0, 0.1),  # high and low of the second candle
        ("10:06", 102.5, 102.6, 101.0, 101.2, 2.0, 0.1),
        ("10:07", 101.2, 101.5, 100.5, 100.8, 2.0, 0.1),
        ("10:08", 100.8, 101.0, 100.1, 100.4, 2.0, 0.1),
        ("10:09", 100.4, 100.9, 100.2, 100.6, 2.0, 0.1),
    )
    out = resample(rows, Timeframe.M5)
    assert out["ts"].tolist() == [utc("10:00"), utc("10:05")]
    first, second = out.iloc[0], out.iloc[1]
    assert (first.open, first.high, first.low, first.close) == (100.0, 102.0, 98.0, 99.8)
    assert first.volume == 5.0
    assert first.spread == pytest.approx((0.2 + 0.2 + 0.4 + 0.2 + 0.3) / 5)
    assert (second.open, second.high, second.low, second.close) == (99.8, 103.0, 99.7, 100.6)
    assert second.volume == 10.0
    assert second.spread == pytest.approx(0.1)


def test_buckets_are_utc_aligned_not_aligned_to_first_minute():
    rows = m1(
        ("10:03", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),
        ("10:07", 100.5, 100.6, 100.1, 100.2, 1.0, 0.2),
    )
    assert resample(rows, Timeframe.M5)["ts"].tolist() == [utc("10:00"), utc("10:05")]
    assert resample(rows, Timeframe.H1)["ts"].tolist() == [utc("10:00")]


def test_flat_zero_volume_minutes_are_dropped_but_flat_minutes_with_volume_kept():
    rows = m1(
        ("21:00", 100.0, 100.0, 100.0, 100.0, 0.0, 0.5),  # break filler: dropped
        ("21:01", 100.0, 100.0, 100.0, 100.0, 0.3, 0.5),  # quiet real minute: kept
        ("21:02", 100.0, 100.5, 99.5, 100.2, 0.0, 0.5),  # zero volume but moved: kept
    )
    kept = drop_flat_minutes(rows)
    assert kept["ts"].tolist() == [utc("21:01"), utc("21:02")]


def test_minutes_without_bid_are_dropped():
    rows = m1(("10:00", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2), ("10:01", 1, 1, 1, 1, 1.0, 0.2))
    rows.loc[1, ["bid_open", "bid_high", "bid_low", "bid_close"]] = float("nan")
    assert drop_flat_minutes(rows)["ts"].tolist() == [utc("10:00")]


def test_fully_flat_hour_gives_no_candle_and_half_flat_hour_uses_live_minutes_only():
    # 20:00-20:01 live, 20:02 onward flat (break starts mid-hour), 21:xx all flat, 22:00 live.
    rows = m1(
        ("20:00", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),
        ("20:01", 100.5, 100.8, 100.1, 100.3, 1.0, 0.4),
        flat("20:02", 100.3),
        flat("20:30", 100.3),
        flat("21:00", 100.3),
        flat("21:59", 100.3),
        ("22:00", 100.4, 100.9, 100.2, 100.7, 1.0, 0.9),
    )
    out = resample(drop_flat_minutes(rows), Timeframe.H1)
    assert out["ts"].tolist() == [utc("20:00"), utc("22:00")]
    partial = out.iloc[0]
    assert (partial.open, partial.high, partial.low, partial.close) == (100.0, 101.0, 99.0, 100.3)
    assert partial.spread == pytest.approx(0.3)  # filler minutes don't count

    m30 = resample(drop_flat_minutes(rows), Timeframe.M30)
    assert m30["ts"].tolist() == [utc("20:00"), utc("22:00")]  # 20:30 bucket was all flat


def test_spread_ignores_minutes_without_ask_and_is_nan_if_none_has_one():
    rows = m1(
        ("10:00", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),
        ("10:01", 100.5, 100.8, 100.1, 100.3, 1.0, 9.9),
        ("10:05", 100.3, 100.4, 100.0, 100.1, 1.0, 9.9),
    )
    rows.loc[[1, 2], ["ask_open", "ask_high", "ask_low", "ask_close"]] = float("nan")
    out = resample(rows, Timeframe.M5)
    assert out.iloc[0].spread == pytest.approx(0.2)
    assert pd.isna(out.iloc[1].spread)


def test_1h_from_m1_equals_1h_from_its_5m_candles():
    rows = m1(
        *[
            (
                f"10:{i:02d}",
                100 + i * 0.1,
                100 + i * 0.1 + (i % 7) * 0.05,
                100 - (i % 5) * 0.1,
                100 + i * 0.1 - 0.02,
                1.0,
                0.1 + (i % 3) * 0.1,
            )
            for i in range(60)
        ]
    )
    h1 = resample(rows, Timeframe.H1).iloc[0]
    m5 = resample(rows, Timeframe.M5)
    assert len(m5) == 12
    assert h1.open == m5.iloc[0].open
    assert h1.high == m5["high"].max()
    assert h1.low == m5["low"].min()
    assert h1.close == m5.iloc[-1].close
    assert h1.volume == pytest.approx(m5["volume"].sum())


def test_empty_input_gives_empty_frame_with_candle_columns():
    out = resample(m1(), Timeframe.M5)
    assert out.empty
    assert list(out.columns) == ["ts", "open", "high", "low", "close", "volume", "spread"]


def test_d1_is_not_supported():
    assert not supported(Timeframe.D1)
    assert all(supported(tf) for tf in (Timeframe.M1, Timeframe.M5, Timeframe.M30, Timeframe.H1))
    with pytest.raises(ValueError):
        resample(m1(("10:00", 1, 1, 1, 1, 1.0, 0.1)), Timeframe.D1)
