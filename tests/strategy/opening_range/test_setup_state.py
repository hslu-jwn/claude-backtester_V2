"""Read-only `OpeningRange.setup_state(now)`: the phase of today's session for the Live page.

Band mode, ATR 10 (warm-up sessions 100-110, close 105): band 105 +/- 2.5 = 102.5 / 107.5.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from test_opening_range import NY, START, flat, row, session, warm_rows, weekdays

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.strategy.opening_range.config import EntryMode, OpeningRangeConfig
from backtester.strategy.opening_range.strategy import OpeningRange

M1 = Timeframe.M1
NYZ = ZoneInfo("America/New_York")


def drive(trade_rows, mode=EntryMode.BAND, warm_vol=100.0, **cfg):
    """Feed warm-up days and a trade day; return (strategy, {offset: state after that candle},
    the session open instant)."""
    cfg = {"entry_mode": mode, "band_atr": 0.25, "volume_lookback": 3, **cfg}
    days = weekdays(START, 15)
    candles = []
    for d in days[:14]:
        candles += session(d, NY, warm_rows(NY, vol=warm_vol))
    candles += session(days[14], NY, trade_rows)
    candles.sort(key=lambda c: c.ts)
    strat = OpeningRange("NAS100", OpeningRangeConfig(**cfg))
    series = CandleSeries("NAS100", M1, candles)
    open_at = datetime.combine(days[14], time(9, 30), tzinfo=NYZ).astimezone(UTC)
    states = {}
    for i, c in enumerate(candles):
        now = c.ts + M1.duration
        strat.on_candle(now, {M1: series.view(i)})
        if now >= open_at:
            states[int((now - open_at).total_seconds() // 60)] = strat.setup_state(now)
    return strat, states, open_at


def test_phases_in_band_mode_with_a_volume_passing_breakout():
    rows = [
        flat(0), row(1, 105, 106, 104, 105), row(5, 105, 106, 104, 105),
        row(16, 105, 109, 105, 108, 150.0), flat(385),
    ]  # fmt: skip
    _, s, _ = drive(rows, min_rel_volume=1.5)
    assert s[0].phase == "range_forming"
    assert s[1].phase == "range_set" and (s[1].down, s[1].up) == (102.5, 107.5)
    assert s[5].phase == "waiting_breakout"
    assert s[16].phase == "ordered" and s[16].rel_volume == pytest.approx(1.5)
    assert s[16].traded is True


def test_before_the_first_candle_of_the_day_and_after_the_exit():
    rows = [flat(0), row(1, 105, 106, 104, 105), flat(385)]
    strat, s, open_at = drive(rows)
    assert strat.setup_state(open_at - timedelta(minutes=1)).phase == "waiting_session"
    assert s[385].phase == "done"
    assert strat.setup_state(open_at + timedelta(hours=7)).phase == "done"


def test_weekend_is_waiting_session():
    strat, _, open_at = drive([flat(0), flat(385)])
    saturday = open_at + timedelta(days=5 - open_at.weekday(), hours=1)
    assert strat.setup_state(saturday).phase == "waiting_session"


def test_failed_volume_filter_is_done_with_the_ratio_kept():
    rows = [flat(0), row(1, 105, 106, 104, 105), row(16, 105, 109, 105, 108, 100.0), flat(385)]
    _, s, _ = drive(rows, min_rel_volume=1.5)
    assert s[16].phase == "done" and s[16].traded is False
    assert s[16].rel_volume == pytest.approx(1.0)


def test_range_mode_phases():
    rows = [flat(0), row(1, 105, 110, 100, 105), row(16, 105, 109, 104, 108), flat(385)]
    _, s, _ = drive(rows, mode=EntryMode.RANGE)
    assert s[1].phase == "range_forming"
    assert s[16].phase == "range_set" and (s[16].down, s[16].up) == (100.0, 110.0)


def test_a_skipped_order_ends_the_session():
    rows = [flat(0), row(1, 105, 106, 104, 105), row(16, 105, 109, 105, 108)]
    strat, s, open_at = drive(rows)
    assert s[16].phase == "ordered"
    strat.on_order_skipped(0, open_at + timedelta(minutes=16))
    assert strat.setup_state(open_at + timedelta(minutes=17)).phase == "done"


def test_setup_state_changes_nothing():
    rows = [flat(0), row(1, 105, 106, 104, 105), row(16, 105, 109, 105, 108), flat(385)]
    strat, _, open_at = drive(rows)
    before = [strat.setup_state(open_at + timedelta(minutes=m)) for m in (3, 20, 400)]
    after = [strat.setup_state(open_at + timedelta(minutes=m)) for m in (3, 20, 400)]
    assert before == after
