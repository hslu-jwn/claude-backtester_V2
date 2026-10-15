"""Strategy 6 (opening-range breakout): range / band entry, stop, target, session-end exit,
reversal, filters (range width, NR4 / inside, tick volume), sessions per symbol with DST,
warm-up, no lookahead. Spec: docs/strategy-opening-range.md.

Fixtures are sparse 1m candles given as offsets in minutes after the session open (the
candle CLOSING at open + offset). Every warm-up session has range 100-110 and closes at
105, so the daily ATR is exactly 10 and the previous close is 105. The New York session
opens 09:30 and ends 15:55 (offset 385); the London FX session 08:00-12:00 (offset 240).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.opening_range.config import (
    SYMBOL_CLASS,
    EntryMode,
    NarrowDay,
    OpeningRangeConfig,
    SessionSpec,
)
from backtester.strategy.opening_range.strategy import OpeningRange

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
M1 = Timeframe.M1
NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))
START = date(2026, 1, 5)  # a Monday, winter time everywhere
TRADE_DAY = date(2026, 1, 23)  # the 15th weekday from START


@dataclass(frozen=True)
class Sess:
    zone: str
    open: time
    exit_off: int  # minutes from the open to the exit candle


NY = Sess("America/New_York", time(9, 30), 385)  # 09:30 - 15:55
LON = Sess("Europe/London", time(8, 0), 240)  # 08:00 - 12:00
BERLIN = Sess("Europe/Berlin", time(9, 0), 505)  # 09:00 - 17:25


def close_at(day: date, s: Sess, offset: int) -> datetime:
    local = datetime.combine(day, s.open, tzinfo=ZoneInfo(s.zone)) + timedelta(minutes=offset)
    return local.astimezone(UTC)


def row(off, o, h, lo, c, v=0.0):
    return (off, o, h, lo, c, v)


def flat(off, p=105.0, v=0.0):
    return row(off, p, p, p, p, v)


def session(day: date, s: Sess, rows) -> list[Candle]:
    return [
        Candle(
            ts=close_at(day, s, off) - M1.duration,
            open=o,
            high=h,
            low=lo,
            close=c,
            volume=v,
        )
        for off, o, h, lo, c, v in rows
    ]


def weekdays(start: date, n: int) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def warm_rows(s: Sess, lo=100.0, hi=110.0, vol=None):
    rows = [flat(0), row(10, 105, hi, lo, 105)]
    if vol is not None:
        rows.append(flat(16, 105, vol))  # the minute whose volume the signal is compared with
    return [*rows, flat(s.exit_off)]


def run(candles: list[Candle], symbol="NAS100", **config):
    candles = sorted(candles, key=lambda c: c.ts)
    series = CandleSeries(symbol, M1, candles)
    return run_backtest(OpeningRange(symbol, OpeningRangeConfig(**config)), [series], NO_COSTS)


def scenario(trade_rows, warm=14, warm_ranges=None, warm_vol=None, s=NY, symbol="NAS100", **cfg):
    """`warm` ordinary sessions, then a trade session on the next weekday."""
    days = weekdays(START, warm + 1)
    ranges = warm_ranges or [(100.0, 110.0)] * warm
    candles: list[Candle] = []
    for d, (lo, hi) in zip(days[:warm], ranges, strict=True):
        candles += session(d, s, warm_rows(s, lo, hi, warm_vol))
    candles += session(days[warm], s, trade_rows)
    return run(candles, symbol, **cfg)


def end(p=105.0, off=NY.exit_off):
    return flat(off, p)


RANGE = row(1, 105, 110, 100, 105)  # the opening range 100-110 (inside the first 15 minutes)
LONG_BREAK = row(16, 105, 112, 105, 111)
SHORT_BREAK = row(16, 105, 105, 98, 99)


# --- range mode: entry and stop ---------------------------------------------------------


def test_range_long_exact_entry_stop_and_session_end_exit():
    [t] = scenario([flat(0), RANGE, LONG_BREAK, row(385, 111, 114, 110, 113)])
    assert t.direction is LONG and t.entry == 111.0 and t.initial_stop == 100.0
    assert t.take_profit is None
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 113.0


def test_range_short_is_the_mirror():
    [t] = scenario([flat(0), RANGE, SHORT_BREAK, row(385, 99, 100, 96, 97)])
    assert t.direction is SHORT and t.entry == 99.0 and t.initial_stop == 110.0
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 97.0


def test_entry_is_the_close_of_the_signal_candle_in_new_york_time():
    [t] = scenario([flat(0), RANGE, LONG_BREAK, end()])
    ny = ZoneInfo("America/New_York")
    assert t.entry_time.astimezone(ny).time() == time(9, 46)
    assert t.exit_time.astimezone(ny).time() == time(15, 55)


def test_wick_beyond_the_range_without_a_close_beyond_gives_no_trade():
    rows = [
        flat(0),
        RANGE,
        row(16, 105, 115, 104, 109),  # high wick above 110, closes inside
        row(20, 105, 106, 95, 101),  # low wick below 100, closes inside
        row(30, 105, 110, 104, 110.0),  # closes exactly on the high: not beyond
        row(31, 105, 106, 100, 100.0),  # closes exactly on the low: not beyond
        end(),
    ]
    assert scenario(rows) == []


def test_the_first_close_beyond_is_the_signal_later_ones_do_not_add_trades():
    rows = [flat(0), RANGE, row(16, 105, 109, 104, 108), row(40, 108, 113, 108, 112), end()]
    [t] = scenario(rows)
    assert t.entry == 112.0 and t.entry_time == close_at(TRADE_DAY, NY, 40)


def test_candle_closing_at_the_end_of_the_range_belongs_to_the_range():
    rows = [flat(0), row(15, 105, 112, 100, 111), row(16, 105, 112, 105, 111.5), end()]
    assert scenario(rows) == []  # the range high is 112: 111.5 is not beyond it
    rows = [flat(0), row(15, 105, 112, 100, 111), row(16, 105, 113, 105, 112.5), end()]
    [t] = scenario(rows)
    assert t.entry == 112.5 and t.initial_stop == 100.0


def test_range_minutes_is_a_setting():
    rows = [flat(0), RANGE, row(15, 105, 112, 105, 111), end()]
    assert scenario(rows) == []  # 15 min: the candle at +15 is still range
    [t] = scenario(rows, range_minutes=10)
    assert t.entry == 111.0 and t.initial_stop == 100.0


@pytest.mark.parametrize(("offset", "trades"), [(119, 1), (120, 1), (121, 0), (300, 0)])
def test_signal_after_the_entry_window_gives_no_trade(offset, trades):
    rows = [flat(0), RANGE, row(offset, 105, 112, 105, 111), end()]
    assert len(scenario(rows)) == trades


def test_entry_window_is_a_setting():
    rows = [flat(0), RANGE, row(60, 105, 112, 105, 111), end()]
    assert scenario(rows, entry_window_minutes=45) == []
    assert len(scenario(rows, entry_window_minutes=60)) == 1


def test_no_candle_in_the_range_gives_no_trade():
    assert scenario([flat(0), row(16, 105, 112, 105, 111), end()]) == []


# --- band mode ---------------------------------------------------------------------------


def band(**kw):
    return {"entry_mode": EntryMode.BAND, **kw}


def test_band_long_exact_entry_and_stop():
    # O = 105 (close at the open), ATR 10, band 0.5 -> 110 / 100
    rows = [flat(0), row(5, 105, 108, 104, 107), row(40, 107, 112, 107, 111), end()]
    [t] = scenario(rows, **band())
    assert t.direction is LONG and t.entry == 111.0 and t.initial_stop == 100.0


def test_band_short_is_the_mirror():
    rows = [flat(0), row(40, 105, 105, 98, 99), end()]
    [t] = scenario(rows, **band())
    assert t.direction is SHORT and t.entry == 99.0 and t.initial_stop == 110.0


def test_band_close_exactly_on_the_band_does_not_count():
    rows = [flat(0), row(40, 105, 111, 105, 110.0), row(41, 105, 105, 99, 100.0), end()]
    assert scenario(rows, **band()) == []


def test_band_atr_is_a_setting():
    rows = [flat(0), row(40, 105, 112, 105, 111), end()]
    assert scenario(rows, **band(band_atr=1.0)) == []  # band at 115
    [t] = scenario(rows, **band(band_atr=0.2))  # band at 107 / 103
    assert t.entry == 111.0 and t.initial_stop == 103.0


def test_band_uses_the_wilder_atr_of_the_sessions_before_today():
    # 14 sessions with TR 10, a 15th with range 96-120 (TR 24): ATR = (10*13 + 24) / 14 = 11
    ranges = [(100.0, 110.0)] * 14 + [(96.0, 120.0)]
    rows = [flat(0), row(40, 105, 111, 105, 110.4), end()]
    assert scenario(rows, warm=15, warm_ranges=ranges, **band()) == []  # band at 110.5
    rows = [flat(0), row(40, 105, 111, 105, 110.6), end()]
    [t] = scenario(rows, warm=15, warm_ranges=ranges, **band())
    assert t.initial_stop == 105 - 5.5


def test_band_without_the_candle_closing_at_the_open_gives_no_trade():
    assert scenario([row(40, 105, 112, 105, 111), end()], **band()) == []


def test_band_signal_window():
    assert len(scenario([flat(0), row(120, 105, 112, 105, 111), end()], **band())) == 1
    assert scenario([flat(0), row(121, 105, 112, 105, 111), end()], **band()) == []


# --- ATR warm-up -------------------------------------------------------------------------


@pytest.mark.parametrize(("warm", "trades"), [(13, 0), (14, 1)])
def test_no_trade_until_the_daily_atr_exists(warm, trades):
    rows = [flat(0), RANGE, LONG_BREAK, end()]
    assert len(scenario(rows, warm=warm)) == trades


def test_atr_period_is_a_setting():
    rows = [flat(0), RANGE, LONG_BREAK, end()]
    assert len(scenario(rows, warm=3, atr_period=3)) == 1
    assert scenario(rows, warm=2, atr_period=3) == []


def test_todays_own_range_is_not_in_todays_atr():
    # the trade session has a huge range, but the band still comes from the 14 earlier
    # sessions (ATR 10)
    rows = [flat(0), row(5, 105, 150, 60, 105), row(40, 105, 112, 105, 111), end()]
    [t] = scenario(rows, **band())
    assert t.initial_stop == 100.0


# --- target and session end ---------------------------------------------------------------


def test_target_2r_exact_take_profit():
    rows = [flat(0), RANGE, LONG_BREAK, row(30, 111, 134, 111, 133), end()]
    [t] = scenario(rows, target_r=2.0)  # risk 11 -> TP 111 + 22
    assert t.take_profit == 133.0
    assert t.exit_reason is ExitReason.TAKE_PROFIT and t.exit_price == 133.0


def test_target_1r_short_mirror():
    rows = [flat(0), RANGE, SHORT_BREAK, row(30, 99, 99, 80, 90), end()]
    [t] = scenario(rows, target_r=1.0)  # risk 11 -> TP 88
    assert t.direction is SHORT and t.take_profit == 88.0
    assert t.exit_reason is ExitReason.TAKE_PROFIT and t.exit_price == 88.0


def test_target_not_reached_exits_at_the_session_end():
    rows = [flat(0), RANGE, LONG_BREAK, row(385, 111, 120, 110, 118)]
    [t] = scenario(rows, target_r=2.0)
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 118.0


def test_stop_and_target_in_one_candle_stops_first():
    rows = [flat(0), RANGE, LONG_BREAK, row(30, 111, 140, 90, 100), end()]
    [t] = scenario(rows, target_r=2.0)
    assert t.exit_reason is ExitReason.STOP_LOSS and t.exit_price == 100.0


def test_session_end_falls_back_to_the_first_later_candle():
    rows = [flat(0), RANGE, LONG_BREAK, row(200, 111, 115, 110, 114), row(388, 114, 116, 113, 115)]
    [t] = scenario(rows)  # nothing closes at 15:55; the feed goes on at 15:58
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 115.0
    assert t.exit_time == close_at(TRADE_DAY, NY, 388)


def test_session_end_fallback_on_the_next_day():
    days = weekdays(START, 16)
    candles: list[Candle] = []
    for d in days[:14]:
        candles += session(d, NY, warm_rows(NY))
    candles += session(days[14], NY, [flat(0), RANGE, LONG_BREAK, row(200, 111, 115, 110, 114)])
    candles += session(days[15], NY, [row(3, 114, 115, 113, 114.5)])
    [t] = run(candles)
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 114.5


def test_one_trade_per_session_with_reversal_off():
    rows = [
        flat(0),
        RANGE,
        LONG_BREAK,
        row(30, 111, 134, 111, 133),  # target hit
        row(60, 133, 134, 90, 95),  # a close below the range afterwards: nothing new
        end(),
    ]
    assert len(scenario(rows, target_r=2.0)) == 1
    rows = [flat(0), RANGE, LONG_BREAK, row(30, 111, 112, 95, 98), row(60, 98, 99, 90, 95), end()]
    [t] = scenario(rows)
    assert t.exit_reason is ExitReason.STOP_LOSS


# --- reversal -----------------------------------------------------------------------------


def test_reversal_after_a_stop_out_opens_one_trade_the_other_way():
    rows = [
        flat(0),
        RANGE,
        LONG_BREAK,  # long 111, stop 100
        row(30, 108, 109, 98, 99),  # stopped at 100; the candle closes below the range
        row(385, 99, 100, 90, 95),
    ]
    first, second = scenario(rows, max_reversals=1)
    assert first.direction is LONG and first.exit_reason is ExitReason.STOP_LOSS
    assert first.exit_price == 100.0
    assert second.direction is SHORT and second.entry == 99.0 and second.initial_stop == 110.0
    assert second.exit_reason is ExitReason.SIGNAL and second.exit_price == 95.0


def test_reversal_waits_for_a_close_beyond_the_other_side():
    rows = [
        flat(0),
        RANGE,
        LONG_BREAK,
        row(30, 108, 109, 98, 101),  # stopped, but closes inside the range
        row(60, 101, 102, 97, 98),  # now closes below 100
        end(),
    ]
    first, second = scenario(rows, max_reversals=1)
    assert first.exit_reason is ExitReason.STOP_LOSS
    assert second.direction is SHORT and second.entry == 98.0 and second.initial_stop == 110.0


def test_reversal_only_inside_the_entry_window():
    rows = [
        flat(0),
        RANGE,
        LONG_BREAK,
        row(30, 108, 109, 98, 101),
        row(121, 101, 102, 97, 98),
        end(),
    ]
    [only] = scenario(rows, max_reversals=1)
    assert only.exit_reason is ExitReason.STOP_LOSS


def test_no_reversal_after_a_target_or_a_session_end_exit():
    rows = [
        flat(0),
        RANGE,
        LONG_BREAK,
        row(30, 111, 134, 111, 133),
        row(60, 133, 134, 90, 95),
        end(),
    ]
    assert len(scenario(rows, max_reversals=1, target_r=2.0)) == 1
    rows = [flat(0), RANGE, LONG_BREAK, end(114)]
    assert len(scenario(rows, max_reversals=1)) == 1


def test_at_most_one_reversal():
    rows = [
        flat(0),
        RANGE,
        LONG_BREAK,
        row(30, 108, 109, 98, 99),  # stop-out, reversal short at 99, stop 110
        row(60, 99, 112, 99, 111),  # the reversal is stopped; 111 is beyond the first side
        end(),
    ]
    trades = scenario(rows, max_reversals=1)
    assert [t.direction for t in trades] == [LONG, SHORT]
    assert trades[1].exit_reason is ExitReason.STOP_LOSS


def test_reversal_target_uses_its_own_risk():
    rows = [flat(0), RANGE, LONG_BREAK, row(30, 108, 109, 98, 99), row(40, 99, 99, 70, 80), end()]
    first, second = scenario(rows, max_reversals=1, target_r=1.0)
    assert first.take_profit == 122.0
    assert second.take_profit == 88.0  # risk 110 - 99 = 11 -> 99 - 11


def test_band_reversal_stops_at_the_other_band():
    rows = [
        flat(0),
        row(40, 105, 112, 105, 111),  # long 111, stop 100 (lower band)
        row(50, 108, 109, 98, 99.5),  # stopped, closes below the lower band
        end(),
    ]
    first, second = scenario(rows, **band(max_reversals=1))
    assert first.direction is LONG and first.initial_stop == 100.0
    assert second.direction is SHORT and second.entry == 99.5 and second.initial_stop == 110.0


# --- filters ------------------------------------------------------------------------------


@pytest.mark.parametrize(("limit", "trades"), [(0.0, 1), (1.0, 1), (0.99, 0), (0.3, 0), (0.15, 0)])
def test_max_range_atr_skips_a_wide_range(limit, trades):
    rows = [flat(0), RANGE, LONG_BREAK, end()]  # range 10 = 1.0 x ATR 10
    assert len(scenario(rows, max_range_atr=limit)) == trades


def test_max_range_atr_passes_a_narrow_range():
    rows = [flat(0), row(1, 105, 106, 104, 105), row(16, 105, 107.5, 105, 107), end()]  # range 2
    [t] = scenario(rows, max_range_atr=0.3)
    assert t.entry == 107.0 and t.initial_stop == 104.0


def test_max_range_atr_does_not_apply_to_band_mode():
    rows = [flat(0), row(40, 105, 112, 105, 111), end()]
    assert len(scenario(rows, **band(max_range_atr=0.01))) == 1


NARROW = [(100.0, 110.0)] * 13


@pytest.mark.parametrize(
    ("prev", "trades"),
    [
        ((102.0, 108.0), 1),  # range 6 < 10, 10, 10: the narrowest of the last 4
        ((100.0, 110.0), 0),  # a tie is not narrower
        ((101.0, 110.0), 1),  # range 9
    ],
)
def test_nr4_filter(prev, trades):
    rows = [flat(0), RANGE, LONG_BREAK, end()]
    out = scenario(rows, warm_ranges=[*NARROW, prev], narrow_day_filter=NarrowDay.NR4)
    assert len(out) == trades


def test_nr4_not_the_narrowest_of_four():
    ranges = [*NARROW[:10], (102.0, 108.0), (100.0, 110.0), (100.0, 110.0), (101.0, 109.0)]
    rows = [flat(0), RANGE, LONG_BREAK, end()]
    # last 4: 6, 10, 10, 8 -> the previous session (8) is not the narrowest
    assert scenario(rows, warm_ranges=ranges, narrow_day_filter=NarrowDay.NR4) == []


def test_nr4_needs_four_sessions_of_history():
    rows = [flat(0), RANGE, LONG_BREAK, end()]
    cfg = {"atr_period": 3, "narrow_day_filter": NarrowDay.NR4}
    short = [(100.0, 110.0)] * 2 + [(102.0, 108.0)]
    assert scenario(rows, warm=3, warm_ranges=short, **cfg) == []
    enough = [(100.0, 110.0)] * 3 + [(102.0, 108.0)]
    assert len(scenario(rows, warm=4, warm_ranges=enough, **cfg)) == 1


@pytest.mark.parametrize(
    ("prev", "trades"),
    [
        ((102.0, 108.0), 1),  # inside (100, 110)
        ((100.0, 108.0), 0),  # the low is equal: not inside
        ((102.0, 110.0), 0),  # the high is equal
        ((99.0, 108.0), 0),  # breaks the low
        ((102.0, 111.0), 0),  # breaks the high
    ],
)
def test_inside_filter(prev, trades):
    rows = [flat(0), RANGE, LONG_BREAK, end()]
    out = scenario(rows, warm_ranges=[*NARROW, prev], narrow_day_filter=NarrowDay.INSIDE)
    assert len(out) == trades


def test_narrow_filter_off_by_default_trades_everywhere():
    rows = [flat(0), RANGE, LONG_BREAK, end()]
    assert len(scenario(rows, warm_ranges=[*NARROW, (90.0, 120.0)])) == 1


# volume: signal candle at +16, reference = mean volume of the candle at +16 of the previous
# `volume_lookback` sessions (here 3 sessions of 100)
def vol_rows(v):
    return [flat(0), RANGE, row(16, 105, 112, 105, 111, v), end()]


@pytest.mark.parametrize(("vol", "trades"), [(150.0, 1), (149.9, 0), (300.0, 1), (10.0, 0)])
def test_volume_filter_pass_and_fail(vol, trades):
    out = scenario(vol_rows(vol), warm_vol=100.0, min_rel_volume=1.5, volume_lookback=3)
    assert len(out) == trades


def test_volume_filter_off_ignores_volume():
    assert len(scenario(vol_rows(1.0), warm_vol=100.0, volume_lookback=3)) == 1


def test_volume_filter_averages_the_lookback_sessions():
    days = weekdays(START, 15)
    candles: list[Candle] = []
    for k, d in enumerate(days[:14]):
        candles += session(d, NY, warm_rows(NY, vol=100.0 if k < 12 else 200.0))
    candles += session(days[14], NY, vol_rows(300.0))
    # lookback 2 -> mean 200 -> needs 1.5 x = 300 (inclusive)
    assert len(run(candles, min_rel_volume=1.5, volume_lookback=2)) == 1
    assert run(candles, min_rel_volume=1.6, volume_lookback=2) == []


def test_volume_filter_without_data_volume_skips_the_session_not_passes_it():
    rows = [flat(0), RANGE, row(16, 105, 112, 105, 111, 0.0), end()]
    assert scenario(rows, warm_vol=0.0, min_rel_volume=1.5, volume_lookback=3) == []
    # a signal candle with volume but no reference volume (histdata-style history) also skips
    assert scenario(vol_rows(500.0), warm_vol=0.0, min_rel_volume=1.5, volume_lookback=3) == []


def test_volume_filter_needs_lookback_sessions_of_history():
    out = scenario(vol_rows(500.0), warm_vol=100.0, min_rel_volume=1.5, volume_lookback=20)
    assert out == []


def test_a_failed_filter_on_the_first_signal_skips_the_whole_session():
    # the first breakout (+16) has too little volume; a later breakout with enough volume is
    # not taken: the signal candle is the first one beyond the range
    rows = [
        flat(0),
        RANGE,
        row(16, 105, 112, 105, 111, 10.0),
        row(30, 111, 115, 111, 114, 500.0),
        end(),
    ]
    assert scenario(rows, warm_vol=100.0, min_rel_volume=1.5, volume_lookback=3) == []


# --- sessions per symbol, DST --------------------------------------------------------------


FX = "EURUSD"


def fx_scenario(trade_day: date, london_rows=None, ny_rows=None, warm=14, ny_warm=None, **cfg):
    days = [d for d in weekdays(trade_day - timedelta(days=40), 60) if d < trade_day][-warm:]
    ny_days = days if ny_warm is None else days[-ny_warm:]
    candles: list[Candle] = []
    for d in days:
        candles += session(d, LON, warm_rows(LON))
    for d in ny_days:
        candles += session(d, NY, warm_rows(NY))
    if london_rows:
        candles += session(trade_day, LON, london_rows)
    if ny_rows:
        candles += session(trade_day, NY, ny_rows)
    return run(candles, FX, **cfg)


LON_ROWS = [flat(0), RANGE, LONG_BREAK, flat(240, 112)]
NY_ROWS = [flat(0), RANGE, SHORT_BREAK, flat(385, 97)]


def test_fx_trades_both_sessions_each_with_its_own_trade():
    [london, new_york] = fx_scenario(TRADE_DAY, LON_ROWS, NY_ROWS)
    assert london.direction is LONG and (london.entry, london.initial_stop) == (111.0, 100.0)
    assert london.exit_price == 112.0
    assert new_york.direction is SHORT and (new_york.entry, new_york.initial_stop) == (99.0, 110.0)
    assert new_york.exit_price == 97.0
    assert london.exit_time < new_york.entry_time


def test_fx_sessions_have_independent_atr_and_state():
    # New York has only 13 sessions of history: no ATR -> no NY trade; London still trades
    [london] = fx_scenario(TRADE_DAY, LON_ROWS, NY_ROWS, ny_warm=13)
    assert london.direction is LONG
    # a quiet London session does not use up New York's trade
    trades = fx_scenario(TRADE_DAY, [flat(0), RANGE, flat(240)], NY_ROWS)
    assert [t.direction for t in trades] == [SHORT]


def test_fx_band_uses_each_sessions_own_atr():
    days = weekdays(START, 15)
    day = days[14]
    candles: list[Candle] = []
    for d in days[:14]:
        candles += session(d, LON, warm_rows(LON))  # ATR 10
        candles += session(d, NY, warm_rows(NY, 100.0, 130.0))  # ATR 30
    candles += session(day, LON, [flat(0), row(40, 105, 112, 105, 111), flat(240)])
    candles += session(day, NY, [flat(0), row(40, 105, 112, 105, 111), flat(385)])
    trades = run(candles, FX, entry_mode=EntryMode.BAND)
    assert len(trades) == 1  # London's band at 110 is broken; New York's at 120 is not
    assert trades[0].entry_time == close_at(day, LON, 40)


@pytest.mark.parametrize(
    ("day", "london_utc", "ny_utc"),
    [
        (date(2026, 3, 2), time(8, 16), time(14, 46)),  # both winter: NY 6.5 h after London
        (date(2026, 3, 16), time(8, 16), time(13, 46)),  # US summer time, UK still winter
        (date(2026, 4, 6), time(7, 16), time(13, 46)),  # both summer
    ],
)
def test_sessions_follow_their_own_citys_dst(day, london_utc, ny_utc):
    """2026-03-08: US clocks change; 2026-03-29: UK clocks change. In between London and
    New York are one hour closer. Entry and stop are the same every time."""
    [london, new_york] = fx_scenario(day, LON_ROWS, NY_ROWS)
    assert (london.entry, london.initial_stop) == (111.0, 100.0)
    assert (new_york.entry, new_york.initial_stop) == (99.0, 110.0)
    assert london.entry_time.timetz().replace(tzinfo=None) == london_utc
    assert new_york.entry_time.timetz().replace(tzinfo=None) == ny_utc


def test_session_end_after_the_march_dst_change():
    day = date(2026, 3, 16)  # New York is on summer time: 15:55 EDT = 19:55 UTC
    [_, new_york] = fx_scenario(day, LON_ROWS, NY_ROWS)
    assert new_york.exit_time == datetime(2026, 3, 16, 19, 55, tzinfo=UTC)


@pytest.mark.parametrize(
    ("symbol", "s"),
    [
        ("GER40", BERLIN),
        ("EU50", BERLIN),
        ("UK100", Sess("Europe/London", time(8, 0), 505)),  # 08:00 - 16:25
        ("JP225", Sess("Asia/Tokyo", time(9, 0), 355)),  # 09:00 - 14:55
    ],
)
def test_index_sessions_by_symbol(symbol, s):
    rows = [flat(0), RANGE, LONG_BREAK, flat(s.exit_off, 113)]
    [t] = scenario(rows, s=s, symbol=symbol)
    assert t.entry == 111.0 and t.exit_price == 113.0
    assert t.entry_time == close_at(TRADE_DAY, s, 16)


def test_symbol_classes_cover_the_spec_symbols():
    for sym in ("NAS100", "US500", "US30", "US2000"):
        assert SYMBOL_CLASS[sym] == "us_index"
    assert SYMBOL_CLASS["GER40"] == SYMBOL_CLASS["EU50"] == "frankfurt_index"
    assert SYMBOL_CLASS["UK100"] == "london_index" and SYMBOL_CLASS["JP225"] == "tokyo_index"
    fx = "GBPUSD GBPJPY EURUSD USDJPY AUDUSD USDCAD USDCHF NZDUSD EURJPY EURGBP XAUUSD XAGUSD"
    for sym in fx.split():
        assert SYMBOL_CLASS[sym] == "fx_metal"


def test_default_sessions_are_the_spec_table():
    c = OpeningRangeConfig()
    ny = SessionSpec("America/New_York", time(9, 30), time(15, 55))
    assert c.sessions["us_index"]["new_york"] == ny
    assert c.sessions["frankfurt_index"]["frankfurt"] == SessionSpec(
        "Europe/Berlin", time(9, 0), time(17, 25)
    )
    assert c.sessions["london_index"]["london"] == SessionSpec(
        "Europe/London", time(8, 0), time(16, 25)
    )
    assert c.sessions["tokyo_index"]["tokyo"] == SessionSpec("Asia/Tokyo", time(9, 0), time(14, 55))
    assert c.sessions["fx_metal"]["london"] == SessionSpec("Europe/London", time(8, 0), time(12, 0))
    assert c.sessions["fx_metal"]["new_york"] == ny


def test_unknown_symbol_is_refused():
    with pytest.raises(ValueError, match="USOIL"):
        OpeningRange("USOIL", OpeningRangeConfig())


# --- strategy contract and config ----------------------------------------------------------


def test_strategy_attributes():
    s = OpeningRange("NAS100", OpeningRangeConfig())
    assert s.base_timeframe is M1 and s.timeframes == (M1,)
    assert s.uses_session_break_even is False
    assert s.min_warmup_days >= 30  # 14 sessions + 1, in calendar days with a margin
    longer = OpeningRange("NAS100", OpeningRangeConfig(atr_period=28))
    assert longer.min_warmup_days > s.min_warmup_days


def test_config_defaults_are_the_spec():
    c = OpeningRangeConfig()
    assert c.entry_mode is EntryMode.RANGE and c.range_minutes == 15 and c.band_atr == 0.5
    assert c.atr_period == 14 and c.entry_window_minutes == 120 and c.max_reversals == 0
    assert c.target_r == 0.0 and c.max_range_atr == 0.0
    assert c.narrow_day_filter is NarrowDay.OFF
    assert c.min_rel_volume == 0.0 and c.volume_lookback == 20


@pytest.mark.parametrize(
    "kwargs",
    [
        {"range_minutes": 0},
        {"band_atr": 0},
        {"band_atr": -0.5},
        {"atr_period": 0},
        {"entry_window_minutes": 0},
        {"entry_window_minutes": 15},  # range mode: must be longer than the range
        {"entry_window_minutes": 400},  # not before the session end
        {"max_reversals": -1},
        {"max_reversals": 2},
        {"target_r": -1.0},
        {"max_range_atr": -0.1},
        {"min_rel_volume": -1.0},
        {"volume_lookback": 0},
    ],
)
def test_config_validation(kwargs):
    with pytest.raises(Exception):  # noqa: B017 - ValueError or ZoneInfoNotFoundError
        OpeningRangeConfig(**kwargs)


@pytest.mark.parametrize(
    ("zone", "open_", "exit_"),
    [
        ("Nowhere/Land", time(9, 30), time(15, 55)),
        ("America/New_York", time(9, 30), time(9, 30)),
        ("America/New_York", time(9, 30), time(9, 0)),
    ],
)
def test_session_validation(zone, open_, exit_):
    with pytest.raises(Exception):  # noqa: B017 - ValueError or ZoneInfoNotFoundError
        SessionSpec(zone, open_, exit_)


def test_a_window_longer_than_a_custom_session_is_refused():
    short = {"us_index": {"x": SessionSpec("America/New_York", time(9, 30), time(10, 30))}}
    with pytest.raises(ValueError):
        OpeningRangeConfig(sessions=short)  # entry window 120 min > 60 min session


# --- no lookahead ---------------------------------------------------------------------------


def many_days() -> list[Candle]:
    days = weekdays(date(2026, 3, 2), 24)
    candles: list[Candle] = []
    for k, d in enumerate(days):
        if k < 14:
            candles += session(d, NY, warm_rows(NY))
        elif k % 2:
            rows = [flat(0), RANGE, LONG_BREAK, row(60, 111, 112, 95, 98), end(100)]
            candles += session(d, NY, rows)
        else:
            rows = [flat(0), RANGE, SHORT_BREAK, row(60, 99, 112, 98, 111), end(100)]
            candles += session(d, NY, rows)
    return candles


def orders_by_index(candles: list[Candle], **cfg) -> dict[int, list]:
    series = CandleSeries("NAS100", M1, candles)
    strategy = OpeningRange("NAS100", OpeningRangeConfig(**cfg))
    out = {}
    for i, c in enumerate(candles):
        orders = strategy.on_candle(c.ts + M1.duration, {M1: series.view(i)})
        strategy.exits()
        if orders:
            out[i] = orders
    return out


CONFIGS = [{}, {"entry_mode": EntryMode.BAND}, {"max_reversals": 1}]


@pytest.mark.parametrize("cfg", CONFIGS)
def test_orders_only_come_from_the_confirming_candle(cfg):
    candles = many_days()
    out = orders_by_index(candles, **cfg)
    # one per trade day (band mode: the trade days widen the ATR, a late long may miss its band)
    assert len(out) == 10 or (cfg.get("entry_mode") and len(out) >= 8)
    for i, orders in out.items():
        (order,) = orders
        c = candles[i]
        assert order.entry == c.close  # the order is the signal candle's close
        assert c.close > 110 or c.close < 100  # beyond the range / band of the earlier candles
        ny_time = (c.ts + M1.duration).astimezone(ZoneInfo("America/New_York")).time()
        assert ny_time == time(9, 46) or (cfg.get("entry_mode") and ny_time == time(10, 30))


@pytest.mark.parametrize("cfg", CONFIGS)
def test_appending_future_candles_never_changes_orders_already_given(cfg):
    candles = many_days()
    full = orders_by_index(candles, **cfg)
    for cut in (len(candles) - 1, len(candles) - 5, len(candles) // 2, 20, 70):
        prefix = orders_by_index(candles[:cut], **cfg)
        assert prefix == {i: o for i, o in full.items() if i < cut}
