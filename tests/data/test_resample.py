"""Resampling M1 cache rows into 5m / 30m / 1h candles. Spec: ROADMAP.md › 0.2."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd
import pytest
from m1_frames import m1

from backtester.core.models import Timeframe
from backtester.data.resample import (
    DayBoundary,
    calendar_label,
    drop_flat_minutes,
    resample,
    supported,
)


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


def test_d1_and_w1_are_supported_and_intraday_unchanged():
    assert supported(Timeframe.D1) and supported(Timeframe.W1)
    assert all(supported(tf) for tf in (Timeframe.M1, Timeframe.M5, Timeframe.M30, Timeframe.H4))


# --- D and W: trading days (ROADMAP 4.0b part 2) ---------------------------------------


def minutes(*stamps: str) -> pd.DataFrame:
    """One M1 row per "YYYY-MM-DD HH:MM" (UTC); price = its position, so open / close show
    which minutes a candle got."""
    frames = [
        m1((t[11:], i, i + 0.5, i - 0.5, i, 1.0, 0.1), day=t[:10]) for i, t in enumerate(stamps)
    ]
    return pd.concat(frames, ignore_index=True)


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def candles(frame, tf, boundary=DayBoundary.NEW_YORK_17):
    out = resample(frame, tf, boundary)
    return [
        (t.to_pydatetime() + tf.duration, row.open, row.close)
        for t, row in zip(out.ts, out.itertuples())
    ]


def test_daily_candle_runs_17_00_to_17_00_new_york_in_winter_and_summer():
    # winter (EST, UTC-5): 17:00 NY = 22:00 UTC; summer (EDT, UTC-4): 21:00 UTC
    winter = minutes("2026-01-13 21:59", "2026-01-13 22:00", "2026-01-14 21:59")
    assert candles(winter, Timeframe.D1) == [
        (ts("2026-01-13 22:00"), 0, 0),  # Tuesday's trading day closes at 22:00 UTC
        (ts("2026-01-14 22:00"), 1, 2),  # 22:00 already belongs to Wednesday
    ]
    summer = minutes("2026-07-14 20:59", "2026-07-14 21:00")
    assert [c[0] for c in candles(summer, Timeframe.D1)] == [
        ts("2026-07-14 21:00"),
        ts("2026-07-15 21:00"),
    ]


def test_dst_start_week_march_2026():
    # US DST starts Sunday 2026-03-08. Friday 03-06 closes 22:00 UTC (EST); the Sunday
    # open 17:00 EDT = 21:00 UTC belongs to Monday 03-09, which closes 21:00 UTC (EDT)
    frame = minutes("2026-03-06 21:59", "2026-03-08 21:00", "2026-03-09 20:59")
    assert candles(frame, Timeframe.D1) == [
        (ts("2026-03-06 22:00"), 0, 0),
        (ts("2026-03-09 21:00"), 1, 2),
    ]
    assert candles(frame, Timeframe.W1) == [
        (ts("2026-03-06 22:00"), 0, 0),  # the week of 03-02 closes Friday 17:00 EST
        (ts("2026-03-13 21:00"), 1, 2),  # the week of 03-09 closes Friday 17:00 EDT
    ]


def test_dst_end_week_november_2026():
    # US DST ends Sunday 2026-11-01: Friday 10-30 closes 21:00 UTC (EDT), the Sunday open
    # 17:00 EST = 22:00 UTC; a minute at 21:30 UTC on that Sunday is still before the open
    frame = minutes("2026-10-30 20:59", "2026-11-01 21:30", "2026-11-01 22:00", "2026-11-02 21:59")
    daily = candles(frame, Timeframe.D1)
    assert daily[0] == (ts("2026-10-30 21:00"), 0, 0)
    assert daily[-1] == (ts("2026-11-02 22:00"), 2, 3)  # Monday: Sunday 22:00 .. Monday 22:00
    weekly = candles(frame, Timeframe.W1)
    assert weekly[0] == (ts("2026-10-30 21:00"), 0, 0)
    assert weekly[-1][0] == ts("2026-11-06 22:00")


def test_a_weekend_makes_no_candle_and_monday_starts_on_sunday_evening():
    # last Friday minute, then the Sunday 17:00 EDT open (21:00 UTC) and Monday
    frame = minutes("2026-09-11 20:59", "2026-09-13 21:00", "2026-09-14 12:00")
    assert candles(frame, Timeframe.D1) == [
        (ts("2026-09-11 21:00"), 0, 0),
        (ts("2026-09-14 21:00"), 1, 2),
    ]
    assert [c[0] for c in candles(frame, Timeframe.W1)] == [
        ts("2026-09-11 21:00"),
        ts("2026-09-18 21:00"),
    ]


def test_ts_plus_duration_is_the_close_and_labels_name_the_trading_day():
    out = resample(minutes("2026-09-13 21:00"), Timeframe.D1)
    assert out.ts[0].to_pydatetime() == ts("2026-09-13 21:00")  # close 09-14 21:00 - 1 day
    assert calendar_label(ts("2026-09-13 21:00"), Timeframe.D1, DayBoundary.NEW_YORK_17) == (
        date(2026, 9, 14)
    )
    week = resample(minutes("2026-09-13 21:00"), Timeframe.W1).ts[0].to_pydatetime()
    assert week == ts("2026-09-11 21:00")  # close Friday 09-18 21:00 - 7 days
    assert calendar_label(week, Timeframe.W1, DayBoundary.NEW_YORK_17) == date(2026, 9, 14)


def test_utc_midnight_option():
    frame = minutes("2026-09-13 21:00", "2026-09-13 23:59", "2026-09-14 00:00")
    assert [c[0] for c in candles(frame, Timeframe.D1, DayBoundary.UTC)] == [
        ts("2026-09-14 00:00"),
        ts("2026-09-15 00:00"),
    ]
    weekly = resample(frame, Timeframe.W1, DayBoundary.UTC)
    assert weekly.ts.tolist() == [ts("2026-09-13 00:00")]  # Sunday 00:00 .. Sunday 00:00 UTC
    assert calendar_label(ts("2026-09-13 00:00"), Timeframe.W1, DayBoundary.UTC) == (
        date(2026, 9, 14)
    )
