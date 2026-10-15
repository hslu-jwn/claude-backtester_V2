"""Strategy 5 (gap fade): fade a 0.1-1 ATR gap at the 09:30 ET close, target = previous cash
close, stop = mirror level, time exit, one trade a day, warm-up, no lookahead.
Spec: docs/strategy-gap-fade.md.

Fixtures are sparse 1m candles (the candle closing at 09:30 ET, a mid-session candle, the
candle closing at 16:00). Every warm-up day has range 100-110 and closes at 105, so the
daily ATR is exactly 10 and the previous cash close is 105."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.gap_fade.config import GapFadeConfig
from backtester.strategy.gap_fade.strategy import GapFade

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
NY = ZoneInfo("America/New_York")
NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))
M1 = Timeframe.M1
TRADE_DAY = date(2026, 1, 23)  # the 15th weekday from 2026-01-05


def at(day: date, hhmm: str) -> datetime:
    """New York clock time as the UTC datetime of a candle CLOSE."""
    h, m = map(int, hhmm.split(":"))
    return datetime.combine(day, time(h, m), tzinfo=NY).astimezone(UTC)


def candle(day: date, close_at: str, o, h, lo, c) -> Candle:
    return Candle(ts=at(day, close_at) - M1.duration, open=o, high=h, low=lo, close=c)


def weekdays(start: date, n: int) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def warm_day(day: date, with_close: bool = True) -> list[Candle]:
    """Open 105, session range 100-110, close 105 -> true range 10."""
    return [
        candle(day, "09:30", 105, 105, 105, 105),
        candle(day, "12:00", 105, 110, 100, 105),
        candle(day, "16:00" if with_close else "15:00", 105, 106, 104, 105),
    ]


def trade_day(day: date, open_price: float, rest=()) -> list[Candle]:
    """The 09:30 candle closes at `open_price`; `rest` = (close_at, high, low, close)."""
    out = [candle(day, "09:30", open_price, open_price, open_price, open_price)]
    out += [candle(day, at_, c, h, lo, c) for at_, h, lo, c in rest]
    return out


def run(candles: list[Candle], **config):
    series = CandleSeries("TEST", M1, candles)
    return run_backtest(GapFade("TEST", GapFadeConfig(**config)), [series], NO_COSTS)


QUIET = [("12:00", 109.0, 107.0, 108.0), ("16:00", 109.0, 107.0, 107.5)]


def scenario(open_price, rest=QUIET, warm=14, start=date(2026, 1, 5), last_warm_close=True, **cfg):
    """`warm` regular days, then a trade day on the next weekday. Returns the trades."""
    days = weekdays(start, warm + 1)
    candles: list[Candle] = []
    for i, d in enumerate(days[:warm]):
        candles += warm_day(d, with_close=last_warm_close or i < warm - 1)
    candles += trade_day(days[warm], open_price, rest)
    return run(candles, **cfg)


# --- entry, stop, target ------------------------------------------------------------------


def test_gap_up_in_range_shorts_with_exact_entry_stop_and_target():
    [t] = scenario(108.0)  # gap +3 = 0.3 ATR
    assert t.direction is SHORT and t.entry == 108.0
    assert t.initial_stop == 111.0 and t.take_profit == 105.0


def test_gap_down_is_the_mirror_and_goes_long():
    [t] = scenario(102.0)  # gap -3
    assert t.direction is LONG and t.entry == 102.0
    assert t.initial_stop == 99.0 and t.take_profit == 105.0


def test_entry_is_the_close_of_the_candle_closing_at_0930():
    [t] = scenario(108.0)
    assert t.entry_time == at(TRADE_DAY, "09:30")


@pytest.mark.parametrize("start", [date(2026, 1, 5), date(2026, 2, 23), date(2026, 10, 12)])
def test_same_trade_in_winter_summer_and_across_the_dst_change(start):
    """2026-03-08 and 2026-11-01 are DST changes; the 09:30 ET entry follows New York time."""
    [t] = scenario(108.0, start=start)
    assert t.direction is SHORT
    assert (t.entry, t.initial_stop, t.take_profit) == (108.0, 111.0, 105.0)
    assert t.entry_time.astimezone(NY).time() == time(9, 30)


def test_stop_gap_mult_moves_the_stop_only():
    [t] = scenario(108.0, stop_gap_mult=1.5)
    assert t.initial_stop == 112.5 and t.take_profit == 105.0
    [t] = scenario(102.0, stop_gap_mult=0.75)
    assert t.initial_stop == 102.0 - 2.25


# --- gap bucket: min inclusive, max exclusive -----------------------------------------------


@pytest.mark.parametrize(
    ("open_price", "trades"),
    [
        (105.99, 0),  # 0.099 ATR: below min
        (106.0, 1),  # exactly 0.1 ATR: min is inclusive
        (114.99, 1),  # 0.999 ATR
        (115.0, 0),  # exactly 1.0 ATR: max is exclusive
        (95.0, 0),  # same on the down side
        (104.0, 1),
        (105.0, 0),  # no gap
    ],
)
def test_gap_bucket_edges(open_price, trades):
    assert len(scenario(open_price)) == trades


def test_custom_bucket():
    assert len(scenario(108.0, min_gap_atr=0.5, max_gap_atr=1.0)) == 0
    assert len(scenario(110.0, min_gap_atr=0.5, max_gap_atr=1.0)) == 1


# --- no trade ---------------------------------------------------------------------------------


def test_no_trade_before_the_atr_has_atr_period_days():
    assert scenario(108.0, warm=13) == []
    assert len(scenario(108.0, warm=14)) == 1


def test_atr_period_is_a_setting():
    assert len(scenario(108.0, warm=3, atr_period=3)) == 1
    assert scenario(108.0, warm=2, atr_period=3) == []


def test_previous_day_without_a_1600_candle_gives_no_trade():
    assert scenario(108.0, last_warm_close=False) == []


def test_one_trade_per_day():
    # the stop is hit at 10:00; later candles of the same day open nothing new
    rest = [
        ("10:00", 112.0, 108.0, 111.5),
        ("11:00", 108.0, 103.0, 104.0),
        ("16:00", 105.0, 104.0, 104.5),
    ]
    [t] = scenario(108.0, rest=rest)
    assert t.exit_reason is ExitReason.STOP_LOSS


def test_a_trade_on_each_of_two_days():
    days = weekdays(date(2026, 1, 5), 16)
    candles = []
    for d in days[:14]:
        candles += warm_day(d)
    candles += trade_day(days[14], 108.0, [("16:00", 109.0, 107.0, 107.5)])
    candles += trade_day(days[15], 105.0, QUIET)  # previous close 107.5: gap -2.5, long
    trades = run(candles)
    assert [t.direction for t in trades] == [SHORT, LONG]
    assert trades[1].take_profit == 107.5


# --- exits --------------------------------------------------------------------------------------


def test_target_hit_before_the_time_exit():
    rest = [("10:00", 108.5, 104.5, 105.5), ("16:00", 109.0, 107.0, 107.5)]
    [t] = scenario(108.0, rest=rest)
    assert t.exit_reason is ExitReason.TAKE_PROFIT and t.exit_price == 105.0


def test_time_exit_at_exit_time_closes_at_that_candles_close():
    [t] = scenario(108.0)
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 107.5
    assert t.exit_time == at(TRADE_DAY, "16:00")


def test_time_exit_at_a_custom_exit_time():
    rest = [
        ("11:00", 109.0, 107.0, 107.2),
        ("12:00", 109.0, 107.0, 108.4),
        ("16:00", 109.0, 107.0, 107.5),
    ]
    [t] = scenario(108.0, rest=rest, exit_time=time(12, 0))
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 108.4
    assert t.exit_time == at(TRADE_DAY, "12:00")


def test_time_exit_falls_back_to_the_first_later_candle():
    # no candle closes at 16:00 (half day / data hole); the feed continues at 18:00
    rest = [
        ("12:00", 109.0, 107.0, 108.0),
        ("18:00", 109.0, 107.0, 107.1),
        ("19:00", 109.0, 107.0, 107.9),
    ]
    [t] = scenario(108.0, rest=rest)
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 107.1
    assert t.exit_time == at(TRADE_DAY, "18:00")


def test_time_exit_fallback_on_the_next_day():
    days = weekdays(date(2026, 1, 5), 16)
    candles = []
    for d in days[:14]:
        candles += warm_day(d)
    candles += trade_day(days[14], 108.0, [("12:00", 109.0, 107.0, 108.0)])
    candles += [candle(days[15], "03:00", 107, 108, 106, 107.3)]
    [t] = run(candles)
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 107.3


# --- strategy contract ------------------------------------------------------------------------


def test_strategy_attributes():
    s = GapFade("NAS100", GapFadeConfig())
    assert s.base_timeframe is Timeframe.M1 and s.timeframes == (Timeframe.M1,)
    assert s.uses_session_break_even is False
    assert s.min_warmup_days == 30
    assert GapFade("NAS100", GapFadeConfig(atr_period=28)).min_warmup_days > 30


# --- config -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"atr_period": 0},
        {"min_gap_atr": 0},
        {"min_gap_atr": -0.1},
        {"max_gap_atr": 0.1},  # not above min
        {"max_gap_atr": 0.05},
        {"stop_gap_mult": 0},
        {"cash_close": time(9, 30)},
        {"cash_close": time(9, 0)},
        {"exit_time": time(9, 30)},
        {"exit_time": time(8, 0)},
        {"zone": "Nowhere/Land"},
    ],
)
def test_config_validation(kwargs):
    with pytest.raises(Exception):  # noqa: B017 - ValueError or ZoneInfoNotFoundError
        GapFadeConfig(**kwargs)


def test_config_defaults_are_the_spec():
    c = GapFadeConfig()
    assert (c.zone, c.cash_open, c.cash_close, c.atr_period) == (
        "America/New_York",
        time(9, 30),
        time(16, 0),
        14,
    )
    assert (c.min_gap_atr, c.max_gap_atr, c.stop_gap_mult) == (0.1, 1.0, 1.0)
    assert c.exit_time == time(16, 0)


# --- no lookahead -----------------------------------------------------------------------------


def orders_by_index(candles: list[Candle]) -> dict[int, list]:
    series = CandleSeries("T", M1, candles)
    strategy = GapFade("T", GapFadeConfig())
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
        if k < 14:
            candles += warm_day(d)
        else:
            candles += trade_day(d, 105.0 + (3 if k % 2 else -3), QUIET)
    return candles


def test_orders_only_come_from_the_candle_closing_at_0930():
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
