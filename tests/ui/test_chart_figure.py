"""Candlestick figure: no gaps on the x-axis, time labels, price range. Spec: ROADMAP.md › 1.1."""

from __future__ import annotations

import pandas as pd
import pytest

from backtester.core.models import Timeframe
from backtester.ui.chart_figure import build_candle_figure, price_digits, time_ticks, y_range


def frame(*rows: tuple[str, float, float, float, float]) -> pd.DataFrame:
    """rows: (open time UTC, open, high, low, close); volume 1, spread 0.3."""
    return pd.DataFrame(
        {
            "ts": [pd.Timestamp(t, tz="UTC") for t, *_ in rows],
            "open": [r[1] for r in rows],
            "high": [r[2] for r in rows],
            "low": [r[3] for r in rows],
            "close": [r[4] for r in rows],
            "volume": 1.0,
            "spread": 0.3,
        }
    )


# Friday close and Sunday reopen of gold (summer): 49 hours without candles in between.
WEEKEND = frame(
    ("2026-09-04 20:00", 2500.0, 2502.0, 2499.0, 2501.0),
    ("2026-09-04 20:30", 2501.0, 2503.0, 2500.0, 2502.5),
    ("2026-09-06 22:00", 2505.0, 2506.0, 2504.0, 2504.5),
    ("2026-09-06 22:30", 2504.5, 2507.5, 2504.0, 2507.0),
)


def five_minute(start: str, periods: int) -> pd.Series:
    return pd.Series(pd.date_range(start, periods=periods, freq="5min", tz="UTC"))


def test_candles_are_numbered_so_weekend_takes_no_space():
    fig = build_candle_figure(WEEKEND, "XAUUSD", Timeframe.M30)
    assert list(fig.data[0].x) == [0, 1, 2, 3]
    assert list(fig.layout.xaxis.range) == [-0.5, 3.5]


def test_hover_shows_exact_utc_open_time_and_spread():
    candle = build_candle_figure(WEEKEND, "XAUUSD", Timeframe.M30).data[0]
    assert [c[0] for c in candle.customdata] == [
        "2026-09-04 20:00",
        "2026-09-04 20:30",
        "2026-09-06 22:00",
        "2026-09-06 22:30",
    ]
    assert candle.customdata[0][1] == pytest.approx(0.3)
    assert "UTC" in candle.hovertemplate and ".3f" in candle.hovertemplate  # gold: 3 decimals


def test_price_axis_fits_candles_with_padding():
    low, high = build_candle_figure(WEEKEND, "XAUUSD", Timeframe.M30).layout.yaxis.range
    assert low == pytest.approx(2499.0 - 0.05 * 8.5)
    assert high == pytest.approx(2507.5 + 0.05 * 8.5)
    assert y_range(WEEKEND, 2, 2, 0.0) == [2504.0, 2506.0]  # only the visible candle
    assert y_range(WEEKEND, 10, 12, 0.05) is None


def test_ticks_mark_first_candle_of_each_step():
    # 13:00..14:55 is a 115-minute span; at most 10 labels -> 15-minute step.
    positions, labels = time_ticks(five_minute("2026-09-02 13:00", 24), 0, 23, max_ticks=10)
    assert positions == [0, 3, 6, 9, 12, 15, 18, 21]
    assert labels == [
        "2026-09-02 13:00",
        "13:15",
        "13:30",
        "13:45",
        "14:00",
        "14:15",
        "14:30",
        "14:45",
    ]


def test_ticks_follow_the_visible_range():
    # Zoomed to 13:30..13:55 -> 5-minute step.
    positions, labels = time_ticks(five_minute("2026-09-02 13:00", 24), 6, 11, max_ticks=10)
    assert positions == [6, 7, 8, 9, 10, 11]
    assert labels == ["2026-09-02 13:30", "13:35", "13:40", "13:45", "13:50", "13:55"]


def test_ticks_across_a_weekend_start_a_new_day_label():
    # 50.5 h span -> 6 h step. Friday 20:00 and 20:30 share the 18:00 step; Sunday 22:00 and
    # 22:30 share the next one.
    positions, labels = time_ticks(WEEKEND["ts"], 0, 3, max_ticks=10)
    assert positions == [0, 2]
    assert labels == ["2026-09-04 20:00", "Sep 06 22:00"]


def test_label_too_close_to_the_next_one_is_dropped():
    # Thursday and Friday 00:00-21:00 hourly, then the Sunday reopen at 22:00, 23:00 and
    # Monday 00:00-21:00. Daily step: the Sunday label (2 candles before Monday's) is dropped.
    ts = pd.Series(
        list(pd.date_range("2026-09-03", periods=22, freq="1h", tz="UTC"))
        + list(pd.date_range("2026-09-04", periods=22, freq="1h", tz="UTC"))
        + list(pd.date_range("2026-09-06 22:00", periods=24, freq="1h", tz="UTC"))
    )
    positions, labels = time_ticks(ts, 0, len(ts) - 1, max_ticks=5)  # 4.9 days -> daily
    assert positions == [0, 22, 46]
    assert labels == ["2026-09-03", "Sep 04", "Sep 07"]


def test_daily_ticks_show_dates_only():
    ts = pd.Series(pd.date_range("2026-09-01", periods=6 * 24, freq="1h", tz="UTC"))
    positions, labels = time_ticks(ts, 0, len(ts) - 1, max_ticks=10)
    assert positions == [0, 24, 48, 72, 96, 120]
    assert labels == ["2026-09-01", "Sep 02", "Sep 03", "Sep 04", "Sep 05", "Sep 06"]


def test_long_ranges_use_multiples_of_a_week_starting_on_monday():
    ts = pd.Series(pd.date_range("2026-01-05", periods=30 * 7, freq="1D", tz="UTC"))
    positions, _ = time_ticks(ts, 0, len(ts) - 1, max_ticks=10)
    assert 1 < len(positions) <= 10
    assert all(ts[p].dayofweek == 0 for p in positions)


def test_price_digits_per_symbol():
    assert (price_digits("XAUUSD"), price_digits("GBPUSD"), price_digits("GBPJPY")) == (3, 5, 3)
