"""Strategy 10 (timed hold): entry at a clock time, stop = stop_atr x daily ATR, time exit, day
filters from CSV calendars, ATR on its own clock, no lookahead.
Spec: docs/strategy-timed-hold.md.

Fixtures are sparse 1m candles. Every warm-up day has range 100-110 and closes at 105, so the
daily ATR is exactly 10 and a 0.5 ATR stop is 5 away from the entry."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.timed_hold.config import TimedHoldConfig
from backtester.strategy.timed_hold.strategy import TimedHold

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
NY, LONDON = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))
M1 = Timeframe.M1
TRADE_DAY = date(2026, 1, 23)  # the 15th weekday from 2026-01-05


def at(day: date, hhmm: str, tz: ZoneInfo = NY) -> datetime:
    """Local clock time as the UTC datetime of a candle CLOSE."""
    h, m = map(int, hhmm.split(":"))
    return datetime.combine(day, time(h, m), tzinfo=tz).astimezone(UTC)


def candle(day: date, close_at: str, o, h, lo, c, tz: ZoneInfo = NY) -> Candle:
    return Candle(ts=at(day, close_at, tz) - M1.duration, open=o, high=h, low=lo, close=c)


def weekdays(start: date, n: int) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def warm_day(day: date, with_close: bool = True) -> list[Candle]:
    """New York session: open 105, range 100-110, close 105 -> true range 10."""
    return [
        candle(day, "09:30", 105, 105, 105, 105),
        candle(day, "12:00", 105, 110, 100, 105),
        candle(day, "16:00" if with_close else "15:00", 105, 106, 104, 105),
    ]


def trade_day(day: date, price: float, rest=(), entry="09:30") -> list[Candle]:
    """The `entry` candle closes at `price`; `rest` = (close_at, high, low, close)."""
    out = [candle(day, entry, price, price, price, price)]
    out += [candle(day, at_, c, h, lo, c) for at_, h, lo, c in rest]
    return out


def run(candles: list[Candle], **config):
    series = CandleSeries("TEST", M1, candles)
    return run_backtest(TimedHold("TEST", TimedHoldConfig(**config)), [series], NO_COSTS)


QUIET = [("12:00", 109.0, 107.0, 108.0), ("16:00", 109.0, 107.0, 107.5)]


def scenario(price=108.0, rest=QUIET, warm=14, start=date(2026, 1, 5), **cfg):
    """`warm` ATR days, then a trade day on the next weekday. Returns the trades."""
    days = weekdays(start, warm + 1)
    candles: list[Candle] = []
    for d in days[:warm]:
        candles += warm_day(d)
    candles += trade_day(days[warm], price, rest)
    return run(candles, **cfg)


# --- entry, stop ------------------------------------------------------------------------------


def test_long_enters_at_the_entry_candle_close_with_a_half_atr_stop():
    [t] = scenario()
    assert t.direction is LONG and t.entry == 108.0
    assert t.initial_stop == 103.0 and t.take_profit is None
    assert t.entry_time == at(TRADE_DAY, "09:30")


def test_short_is_the_mirror():
    [t] = scenario(direction="short")
    assert t.direction is SHORT and t.entry == 108.0
    assert t.initial_stop == 113.0 and t.take_profit is None


def test_stop_distance_is_stop_atr_times_atr():
    [t] = scenario(stop_atr=1.5)
    assert t.initial_stop == 108.0 - 15.0
    [t] = scenario(stop_atr=0.25, direction="short")
    assert t.initial_stop == 108.0 + 2.5


@pytest.mark.parametrize("start", [date(2026, 1, 5), date(2026, 6, 1), date(2026, 10, 12)])
def test_same_trade_in_winter_summer_and_across_a_dst_change(start):
    """The 09:30 New York entry follows New York time (2026-03-08 and 2026-11-01 are changes)."""
    [t] = scenario(start=start)
    assert (t.entry, t.initial_stop) == (108.0, 103.0)
    assert t.entry_time.astimezone(NY).time() == time(9, 30)


def test_custom_entry_and_exit_time():
    rest = [("11:00", 109.0, 107.0, 108.4), ("16:00", 109.0, 107.0, 107.5)]
    days = weekdays(date(2026, 1, 5), 15)
    candles = [c for d in days[:14] for c in warm_day(d)]
    candles += [candle(days[14], "10:30", 108, 108, 108, 108)]
    candles += [candle(days[14], at_, c, h, lo, c) for at_, h, lo, c in rest]
    [t] = run(candles, entry_time=time(10, 30), exit_time=time(11, 0))
    assert t.entry_time == at(TRADE_DAY, "10:30")
    assert t.exit_time == at(TRADE_DAY, "11:00") and t.exit_price == 108.4


# --- with_day / against_day (vs the last finished session close, 105) ------------------------


@pytest.mark.parametrize(
    ("mode", "price", "side", "stop"),
    [
        ("with_day", 108.0, LONG, 103.0),
        ("with_day", 102.0, SHORT, 107.0),
        ("against_day", 108.0, SHORT, 113.0),
        ("against_day", 102.0, LONG, 97.0),
    ],
)
def test_with_and_against_the_day(mode, price, side, stop):
    [t] = scenario(price, rest=QUIET_WIDE, direction=mode)
    assert t.direction is side and t.initial_stop == stop


QUIET_WIDE = [("12:00", 104.0, 103.0, 103.5), ("16:00", 104.0, 103.0, 103.5)]


@pytest.mark.parametrize("mode", ["with_day", "against_day"])
def test_day_direction_equal_to_prev_close_or_without_one_is_no_trade(mode):
    assert scenario(105.0, rest=QUIET_WIDE, direction=mode) == []
    # no finished session at all: no ATR either, so also no trade
    assert scenario(108.0, warm=0, direction=mode) == []


def test_day_direction_ignores_the_session_in_progress():
    """Entry 11:00; today's 10:00 candle closes at 90 (below 105) but is not finished."""
    days = weekdays(date(2026, 1, 5), 15)
    candles = [c for d in days[:14] for c in warm_day(d)]
    candles += [
        candle(days[14], "10:00", 90, 91, 89, 90),
        candle(days[14], "11:00", 108, 108, 108, 108),
        candle(days[14], "16:00", 108, 109, 107, 108),
    ]
    [t] = run(candles, entry_time=time(11, 0), direction="with_day")
    assert t.direction is LONG  # 108 > 105, not compared with 90


@pytest.mark.parametrize(
    ("price", "k", "trades"),
    [
        (108.0, 0.3, 1),  # |108 - 105| = 0.3 ATR: at the threshold (inclusive)
        (108.0, 0.31, 0),  # below
        (100.0, 0.5, 1),  # |100 - 105| = 0.5 ATR, short side
        (100.0, 0.51, 0),
        (108.0, 0.0, 1),  # 0 = no filter (default)
    ],
)
def test_min_move_atr_filters_small_day_moves(price, k, trades):
    assert len(scenario(price, rest=QUIET_WIDE, direction="with_day", min_move_atr=k)) == trades


def _fx_week_with_sunday_stub(sunday_range: float) -> list[Candle]:
    """3 weeks of UTC days (range 10 each, close 105 at 20:59 on Fridays, 23:59 otherwise), each
    week preceded by a Sunday-evening stub (21:00-23:59 UTC) of `sunday_range`; then a Monday
    trade at 07:00 London."""
    utc = ZoneInfo("UTC")
    out: list[Candle] = []
    for d in weekdays(date(2026, 1, 5), 15):
        if d.weekday() == 0:  # the Sunday before
            s = d - timedelta(days=1)
            half = sunday_range / 2
            out.append(candle(s, "22:00", 105, 105 + half, 105 - half, 105, utc))
            out.append(candle(s, "23:59", 105, 105, 105, 105, utc))
        out.append(candle(d, "08:00", 105, 110, 100, 105, utc))
        out.append(candle(d, "20:59" if d.weekday() == 4 else "23:59", 105, 105, 105, 105, utc))
    monday = date(2026, 1, 26)
    stub = monday - timedelta(days=1)
    out.append(candle(stub, "22:00", 105, 105, 105, 105, utc))
    out.append(candle(monday, "07:00", 105, 105, 105, 105, LONDON))
    out.append(candle(monday, "13:00", 105, 106, 104, 105, LONDON))
    return out


FX_ATR = {
    "zone": "Europe/London",
    "entry_time": time(7, 0),
    "exit_time": time(13, 0),
    "direction": "short",
    "atr_zone": "UTC",
    "atr_open": time(0, 0),
    "atr_close": time(23, 59),
}


def test_fx_atr_skip_weekend_counts_fridays_and_drops_sunday_stubs():
    # weekdays only, Fridays regular (tolerance 180): every true range is 10 -> stop 105 + 5
    [t] = run(_fx_week_with_sunday_stub(1.0), **FX_ATR, atr_close_tolerance_min=180,
              atr_skip_weekend=True)  # fmt: skip
    assert t.initial_stop == pytest.approx(110.0)
    # without the switch the 1-point Sunday stubs enter the ATR and shrink the stop
    [t] = run(_fx_week_with_sunday_stub(1.0), **FX_ATR, atr_close_tolerance_min=180)
    assert t.initial_stop < 110.0


def test_min_move_atr_needs_a_day_direction():
    with pytest.raises(ValueError):
        TimedHoldConfig(direction="long", min_move_atr=0.5)
    with pytest.raises(ValueError):
        TimedHoldConfig(direction="with_day", min_move_atr=-0.1)


# --- no trade ---------------------------------------------------------------------------------


def test_no_trade_before_the_atr_has_atr_period_days():
    assert scenario(warm=13) == []
    assert len(scenario(warm=14)) == 1


def test_atr_period_is_a_setting():
    assert len(scenario(warm=3, atr_period=3)) == 1
    assert scenario(warm=2, atr_period=3) == []


def test_irregular_session_gives_no_atr():
    days = weekdays(date(2026, 1, 5), 15)
    candles = []
    for i, d in enumerate(days[:14]):
        candles += warm_day(d, with_close=i != 5)  # one day without the closing candle
    candles += trade_day(days[14], 108.0, QUIET)
    assert run(candles) == []


def test_no_trade_when_the_entry_candle_is_missing():
    days = weekdays(date(2026, 1, 5), 15)
    candles = [c for d in days[:14] for c in warm_day(d)]
    candles += [candle(days[14], "09:31", 108, 108, 108, 108)] + trade_day(days[14], 108.0, QUIET)[
        1:
    ]
    assert run(candles) == []


def test_one_trade_per_day_and_one_on_each_of_two_days():
    days = weekdays(date(2026, 1, 5), 16)
    candles = [c for d in days[:14] for c in warm_day(d)]
    candles += trade_day(
        days[14], 108.0, [("10:00", 109.0, 102.0, 103.0), ("16:00", 105, 104, 104)]
    )
    candles += trade_day(days[15], 105.0, QUIET)
    trades = run(candles)
    assert [t.entry_time.astimezone(NY).date() for t in trades] == [days[14], days[15]]
    assert trades[0].exit_reason is ExitReason.STOP_LOSS  # no second trade after the stop


# --- exits ------------------------------------------------------------------------------------


def test_stop_hit_before_the_time_exit():
    [t] = scenario(rest=[("10:00", 109.0, 102.5, 103.5), ("16:00", 109.0, 107.0, 107.5)])
    assert t.exit_reason is ExitReason.STOP_LOSS and t.exit_price == 103.0
    [t] = scenario(
        direction="short", rest=[("10:00", 113.5, 108.0, 112.0), ("16:00", 109.0, 107.0, 107.5)]
    )
    assert t.exit_reason is ExitReason.STOP_LOSS and t.exit_price == 113.0


def test_time_exit_at_exit_time_closes_at_that_candles_close():
    [t] = scenario()
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 107.5
    assert t.exit_time == at(TRADE_DAY, "16:00")


def test_time_exit_falls_back_to_the_first_later_candle():
    rest = [
        ("12:00", 109.0, 107.0, 108.0),
        ("18:00", 109.0, 107.0, 107.1),
        ("19:00", 109.0, 107.0, 107.9),
    ]
    [t] = scenario(rest=rest)
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 107.1
    assert t.exit_time == at(TRADE_DAY, "18:00")


# --- day filters ------------------------------------------------------------------------------

HOLIDAYS = """date,name,type,source_url
2026-01-01,New Year,closed,x
2026-01-03,Saturday closure,closed,x
2026-01-06,Early,early_close_13:00,x
2026-01-19,MLK,closed,x
"""
FOMC = """date,scheduled,statement_time_et,press_conference,source_url
2026-01-14,false,14:00,false,x
2026-01-28,true,14:00,true,x
2026-02-18,TRUE,14:00,true,x
"""


def entry_dates(first: date, n: int, tmp_path: Path, **cfg) -> list[date]:
    """Weekdays from `first`, every one a full warm-up day; the dates a trade was entered."""
    candles = [c for d in weekdays(first, n) for c in warm_day(d)]
    trades = run(candles, atr_period=1, stop_atr=2.0, calendar_dir=str(tmp_path), **cfg)
    return [t.entry_time.astimezone(NY).date() for t in trades]


def calendars(tmp_path: Path, holidays=HOLIDAYS, fomc=FOMC) -> Path:
    (tmp_path / "nyse_holidays.csv").write_text(holidays)
    (tmp_path / "fomc_statements.csv").write_text(fomc)
    return tmp_path


def test_all_trades_every_day_with_an_atr(tmp_path):
    got = entry_dates(date(2026, 1, 5), 5, tmp_path)
    assert got == weekdays(date(2026, 1, 6), 4)  # the first day has no finished session


def test_fomc_only_on_scheduled_dates(tmp_path):
    calendars(tmp_path)
    assert entry_dates(date(2026, 1, 5), 35, tmp_path, day_filter="fomc") == [
        date(2026, 1, 28),
        date(2026, 2, 18),
    ]


def test_turn_of_month_with_holidays(tmp_path):
    calendars(tmp_path)
    # last trading day of December, then the first 3 trading days of January
    # (2026-01-01 is closed, 2026-01-06 is only an early close: still a trading day)
    got = entry_dates(date(2025, 12, 22), 16, tmp_path, day_filter="turn_of_month")
    assert got == [date(2025, 12, 31), date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 6)]


def test_turn_of_month_days_after_is_a_setting(tmp_path):
    calendars(tmp_path)
    got = entry_dates(
        date(2025, 12, 22), 12, tmp_path, day_filter="turn_of_month", tom_days_after=0
    )
    assert got == [date(2025, 12, 31)]


def test_turn_of_month_last_trading_day_when_the_month_end_is_closed(tmp_path):
    calendars(tmp_path, holidays="date,name,type,source_url\n2026-01-30,x,closed,x\n")
    got = entry_dates(date(2026, 1, 20), 12, tmp_path, day_filter="turn_of_month", tom_days_after=1)
    assert got == [date(2026, 1, 29), date(2026, 2, 2)]  # the closed 01-30 is skipped


def test_pre_holiday_including_monday_closure_and_ignoring_weekend_closure(tmp_path):
    calendars(tmp_path)
    got = entry_dates(date(2025, 12, 22), 24, tmp_path, day_filter="pre_holiday")
    # 12-31 before Thursday 01-01; Friday 01-16 before Monday 01-19; the Saturday closure
    # 01-03 does not make Friday 01-02 a pre-holiday day
    assert got == [date(2025, 12, 31), date(2026, 1, 16)]


def test_missing_calendar_file_is_a_clear_error_only_for_a_filter_that_needs_it(tmp_path):
    TimedHold("T", TimedHoldConfig(calendar_dir=str(tmp_path)))  # "all": no file read
    for kind in ("fomc", "turn_of_month", "pre_holiday"):
        with pytest.raises(FileNotFoundError, match="calendar"):
            TimedHold("T", TimedHoldConfig(day_filter=kind, calendar_dir=str(tmp_path)))
    (tmp_path / "fomc_statements.csv").write_text(FOMC)
    TimedHold("T", TimedHoldConfig(day_filter="fomc", calendar_dir=str(tmp_path)))  # only fomc


# --- ATR sessions: finished only, own clock ---------------------------------------------------


def test_a_session_in_progress_never_counts():
    """Entry at 11:00, a huge candle at 10:00 of the same day lies in the unfinished session."""
    days = weekdays(date(2026, 1, 5), 15)
    candles = [c for d in days[:14] for c in warm_day(d)]
    candles += [
        candle(days[14], "10:00", 105, 900, -900, 105),
        candle(days[14], "11:00", 108, 108, 108, 108),
        candle(days[14], "16:00", 108, 109, 107, 108),
    ]
    [t] = run(candles, entry_time=time(11, 0))
    assert t.entry == 108.0 and t.initial_stop == 103.0  # ATR still 10


def fx_candles(start: date, warm: int, price: float, entry: str, rest=()):
    """Warm-up days on the UTC clock (range 100-110, last candle 23:59), then a trade day with
    the entry candle on the London clock."""
    days = weekdays(start, warm + 1)
    out = []
    for d in days[:warm]:
        out += [
            candle(d, "12:00", 105, 110, 100, 105, UTC),
            candle(d, "23:59", 105, 106, 104, 105, UTC),
        ]
    out += [candle(days[warm], entry, price, price, price, price, LONDON)]
    out += [candle(days[warm], a, c, h, lo, c, LONDON) for a, h, lo, c in rest]
    return out


FX = {
    "zone": "Europe/London",
    "entry_time": time(8, 0),
    "exit_time": time(16, 0),
    "atr_zone": "UTC",
    "atr_open": time(0, 0),
    "atr_close": time(23, 59),
    "atr_close_tolerance_min": 30,
}
FX_REST = [("12:00", 109.0, 107.0, 108.0), ("16:00", 109.0, 107.0, 107.5)]


@pytest.mark.parametrize("start", [date(2026, 1, 5), date(2026, 6, 1)])  # London winter / summer
def test_fx_setup_london_clock_with_a_utc_24h_atr(start):
    [t] = run(fx_candles(start, 14, 108.0, "08:00", FX_REST), **FX)
    assert (t.direction, t.entry, t.initial_stop) == (LONG, 108.0, 103.0)
    assert t.entry_time.astimezone(LONDON).time() == time(8, 0)
    assert t.exit_price == 107.5 and t.exit_time.astimezone(LONDON).time() == time(16, 0)


def test_fx_no_trade_before_the_atr_exists_and_in_progress_day_does_not_count():
    assert run(fx_candles(date(2026, 1, 5), 13, 108.0, "08:00", FX_REST), **FX) == []
    candles = fx_candles(date(2026, 1, 5), 14, 108.0, "08:00", FX_REST)
    huge = candle(TRADE_DAY, "04:00", 105, 900, -900, 105, UTC)  # today's UTC session so far
    candles.insert(-3, huge)
    [t] = run(candles, **FX)
    assert t.initial_stop == 103.0


def test_fx_session_without_a_late_candle_is_irregular():
    candles = fx_candles(date(2026, 1, 5), 14, 108.0, "08:00", FX_REST)
    bad = [c for c in candles if c.ts != at(date(2026, 1, 9), "23:59", UTC) - M1.duration]
    assert len(bad) == len(candles) - 1
    assert run(bad, **FX) == []


# --- strategy contract and config -------------------------------------------------------------


def test_strategy_attributes():
    s = TimedHold("NAS100", TimedHoldConfig())
    assert s.base_timeframe is Timeframe.M1 and s.timeframes == (Timeframe.M1,)
    assert s.uses_session_break_even is False
    assert s.min_warmup_days == 30
    assert TimedHold("NAS100", TimedHoldConfig(atr_period=28)).min_warmup_days > 30


@pytest.mark.parametrize(
    "kwargs",
    [
        {"exit_time": time(9, 30)},
        {"exit_time": time(8, 0)},
        {"stop_atr": 0},
        {"stop_atr": -1},
        {"atr_period": 0},
        {"direction": "both"},
        {"direction": "with_day "},
        {"day_filter": "friday"},
        {"tom_days_after": -1},
        {"atr_close": time(9, 30)},
        {"atr_close_tolerance_min": -1},
        {"zone": "Nowhere/Land"},
        {"atr_zone": "Nowhere/Land"},
    ],
)
def test_config_validation(kwargs):
    with pytest.raises(Exception):  # noqa: B017 - ValueError or ZoneInfoNotFoundError
        TimedHoldConfig(**kwargs)


def test_config_defaults_are_the_spec():
    c = TimedHoldConfig()
    assert (c.zone, c.entry_time, c.exit_time, c.direction) == (
        "America/New_York", time(9, 30), time(16, 0), "long",
    )  # fmt: skip
    assert (c.stop_atr, c.atr_period, c.atr_zone) == (0.5, 14, "America/New_York")
    assert (c.atr_open, c.atr_close, c.atr_close_tolerance_min) == (time(9, 30), time(16, 0), 0)
    assert (c.day_filter, c.tom_days_after, c.calendar_dir) == ("all", 3, "")
    assert c.min_move_atr == 0.0


# --- no lookahead -----------------------------------------------------------------------------


def orders_by_index(candles: list[Candle]) -> dict[int, list]:
    series = CandleSeries("T", M1, candles)
    strategy = TimedHold("T", TimedHoldConfig())
    out = {}
    for i, c in enumerate(candles):
        orders = strategy.on_candle(c.ts + M1.duration, {M1: series.view(i)})
        strategy.exits()
        if orders:
            out[i] = orders
    return out


def many_days() -> list[Candle]:
    days = weekdays(date(2026, 3, 2), 22)
    candles = []
    for k, d in enumerate(days):
        candles += warm_day(d) if k < 14 else trade_day(d, 105.0 + k, QUIET)
    return candles


def test_orders_only_come_from_the_entry_candle():
    candles = many_days()
    out = orders_by_index(candles)
    assert out
    for i in out:
        assert (candles[i].ts + M1.duration).astimezone(NY).time() == time(9, 30)


def test_appending_future_candles_never_changes_orders_already_given():
    candles = many_days()
    full = orders_by_index(candles)
    for cut in (len(candles) - 1, len(candles) - 5, len(candles) // 2, 20):
        prefix = orders_by_index(candles[:cut])
        assert prefix == {i: o for i, o in full.items() if i < cut}


def test_skip_nyse_short_days_defaults_off_and_excludes_both_types(tmp_path):
    calendars(tmp_path)
    assert TimedHoldConfig().skip_nyse_short_days is False
    normal = entry_dates(date(2026, 1, 5), 12, tmp_path)
    filtered = entry_dates(date(2026, 1, 5), 12, tmp_path, skip_nyse_short_days=True)
    for day in (date(2026, 1, 6), date(2026, 1, 19)):
        assert day in normal
        assert day not in filtered


def test_skip_nyse_short_days_also_applies_to_fomc(tmp_path):
    calendars(tmp_path, fomc="date,scheduled\n2026-01-06,true\n2026-01-19,true\n")
    assert entry_dates(date(2026, 1, 5), 12, tmp_path, day_filter="fomc") == [
        date(2026, 1, 6), date(2026, 1, 19)
    ]
    assert entry_dates(date(2026, 1, 5), 12, tmp_path, day_filter="fomc",
                       skip_nyse_short_days=True) == []
