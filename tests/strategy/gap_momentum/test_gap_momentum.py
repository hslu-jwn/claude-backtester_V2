"""Strategy 7 (gap momentum): trade WITH an opening gap that lies beyond the previous session's
high / low by `entry_z` x sd, at the open, stop `stop_atr` x ATR, time exit, one trade a day.
Spec: docs/strategy-gap-momentum.md.

Fixtures are sparse 1m candles (the candle closing at the session open, a mid-session candle,
the candle closing at the session close). Every warm-up day has high 110, low 100 and closes at
104 / 106 alternately, so the daily ATR is exactly 10 and the sd of the close-to-close log returns
is known from `statistics.stdev` (independent of the strategy code)."""

from __future__ import annotations

import itertools
import math
import statistics
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, rollover_nights
from backtester.engine.trade import ExitReason
from backtester.strategy.gap_momentum.config import GapMomentumConfig
from backtester.strategy.gap_momentum.strategy import GapMomentum

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
NY = ZoneInfo("America/New_York")
NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))
M1 = Timeframe.M1
HIGH, LOW, ATR = 110.0, 100.0, 10.0
CLOSES = (104.0, 106.0)
SMALL = {"vol_days": 4, "atr_period": 3}  # short history so fixtures stay small
SESSIONS = {"index": ("09:30", "16:00"), "fx": ("05:00", "17:00")}
EXITS = {"index": "15:59", "fx": "16:59"}


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


def warm_day(day: date, k: int, mode="index", with_close=True) -> list[Candle]:
    """High 110, low 100, close 104 (even k) / 106 (odd k) -> true range 10 on every day."""
    open_t, close_t = SESSIONS[mode]
    c = CLOSES[k % 2]
    return [
        candle(day, open_t, c, c, c, c),
        candle(day, "12:00", c, HIGH, LOW, c),
        candle(day, close_t if with_close else "15:00", c, c + 0.5, c - 0.5, c),
    ]


def sd_of(n_returns: int, last_k: int) -> float:
    """sd of the last `n_returns` log returns when the last warm-up day has index last_k."""
    closes = [CLOSES[k % 2] for k in range(last_k - n_returns, last_k + 1)]
    rets = [math.log(b / a) for a, b in itertools.pairwise(closes)]
    return statistics.stdev(rets)


def trade_day(day: date, open_price: float, rest=(), mode="index") -> list[Candle]:
    """The open candle closes at `open_price`; `rest` = (close_at, high, low, close)."""
    open_t = SESSIONS[mode][0]
    out = [candle(day, open_t, open_price, open_price, open_price, open_price)]
    out += [candle(day, at_, c, h, lo, c) for at_, h, lo, c in rest]
    return out


def run(candles: list[Candle], engine=NO_COSTS, **config):
    series = CandleSeries("TEST", M1, candles)
    return run_backtest(GapMomentum("TEST", GapMomentumConfig(**config)), [series], engine)


def scenario(
    open_price, rest=None, warm=5, start=date(2026, 1, 5), last_warm_close=True, mode="index",
    cfg=None,
):  # fmt: skip
    """`warm` regular days, then a trade day on the next weekday. Returns the trades."""
    cfg = {"mode": mode, **SMALL, **(cfg or {})}
    if rest is None:
        rest = [("12:00", 109.0, 107.0, 108.0), (EXITS[mode], 109.0, 107.0, 107.5)]
    days = weekdays(start, warm + 1)
    candles: list[Candle] = []
    for k, d in enumerate(days[:warm]):
        candles += warm_day(d, k, mode, with_close=last_warm_close or k < warm - 1)
    candles += trade_day(days[warm], open_price, rest, mode)
    return run(candles, **cfg)


TRADE_DAY = weekdays(date(2026, 1, 5), 6)[5]
SD5 = sd_of(4, 4)  # warm=5: last warm index 4, 4 returns
THRESH_LONG = HIGH * (1 + 0.1 * SD5)
THRESH_SHORT = LOW * (1 - 0.1 * SD5)


# --- entry, stop ----------------------------------------------------------------------------


def test_sd_fixture_sanity():
    assert 0.0215 < SD5 < 0.0225  # a x sqrt(4/3), a = ln(106/104)


def test_gap_above_the_prior_high_by_the_threshold_goes_long():
    [t] = scenario(THRESH_LONG + 0.01)
    assert t.direction is LONG and t.entry == pytest.approx(THRESH_LONG + 0.01)
    assert t.initial_stop == pytest.approx(THRESH_LONG + 0.01 - 1.0 * ATR)
    assert t.take_profit is None
    assert t.entry_time == at(TRADE_DAY, "09:30")


def test_gap_below_the_prior_low_by_the_threshold_goes_short_mirrored():
    [t] = scenario(THRESH_SHORT - 0.01)
    assert t.direction is SHORT and t.entry == pytest.approx(THRESH_SHORT - 0.01)
    assert t.initial_stop == pytest.approx(THRESH_SHORT - 0.01 + 1.0 * ATR)
    assert t.take_profit is None


@pytest.mark.parametrize(
    "open_price", [THRESH_LONG - 0.01, 110.0, 105.0, 100.0, THRESH_SHORT + 0.01]
)
def test_no_trade_inside_the_range_or_below_the_threshold(open_price):
    assert scenario(open_price) == []


def test_stop_is_stop_atr_times_the_daily_atr():
    [t] = scenario(115.0, cfg={"stop_atr": 2.0})
    assert t.initial_stop == pytest.approx(115.0 - 20.0)
    [t] = scenario(115.0, cfg={"stop_atr": 0.5})
    assert t.initial_stop == pytest.approx(115.0 - 5.0)
    [t] = scenario(95.0, cfg={"stop_atr": 2.0})
    assert t.initial_stop == pytest.approx(95.0 + 20.0)


def test_target_r_makes_a_take_profit_in_r_of_the_stop():
    [t] = scenario(115.0, cfg={"target_r": 2.0, "stop_atr": 0.5})
    assert t.take_profit == pytest.approx(115.0 + 2.0 * 5.0)
    [t] = scenario(95.0, cfg={"target_r": 2.0})
    assert t.take_profit == pytest.approx(95.0 - 2.0 * 10.0)


def test_entry_z_scales_the_threshold_with_the_sd():
    thr = HIGH * (1 + 0.25 * SD5)
    assert scenario(thr - 0.01, cfg={"entry_z": 0.25}) == []
    assert len(scenario(thr + 0.01, cfg={"entry_z": 0.25})) == 1


def test_entry_z_zero_trades_only_strictly_beyond_the_prior_extreme():
    assert scenario(HIGH, cfg={"entry_z": 0.0}) == []  # equal to the high: inside
    assert scenario(LOW, cfg={"entry_z": 0.0}) == []
    assert len(scenario(HIGH + 0.01, cfg={"entry_z": 0.0})) == 1
    [t] = scenario(LOW - 0.01, cfg={"entry_z": 0.0})
    assert t.direction is SHORT
    # between the high and the z = 0.1 threshold: z = 0 trades, z = 0.1 does not
    assert len(scenario(HIGH + 0.1, cfg={"entry_z": 0.0})) == 1
    assert scenario(HIGH + 0.1) == []


def test_side_fade_takes_the_other_direction_with_the_same_stop_distance():
    [t] = scenario(115.0, cfg={"side": "fade"})
    assert t.direction is SHORT and t.entry == 115.0 and t.initial_stop == pytest.approx(125.0)
    [t] = scenario(95.0, cfg={"side": "fade", "stop_atr": 2.0})
    assert t.direction is LONG and t.initial_stop == pytest.approx(75.0)
    assert scenario(105.0, cfg={"side": "fade"}) == []  # same days as momentum


# --- history needed ---------------------------------------------------------------------------


def test_no_trade_before_vol_days_returns_exist():
    assert scenario(115.0, warm=4) == []  # 4 closes = 3 returns, vol_days = 4
    assert len(scenario(115.0, warm=5)) == 1  # 5 closes = 4 returns


def test_no_trade_before_atr_period_days_exist():
    cfg = {"atr_period": 6}
    assert scenario(115.0, warm=5, cfg=cfg) == []
    assert len(scenario(115.0, warm=6, cfg=cfg)) == 1


def test_the_sd_uses_only_the_last_vol_days_returns():
    thr = HIGH * (1 + 0.1 * sd_of(4, 7))
    [t] = scenario(thr + 0.01, warm=8)
    assert t.direction is LONG
    assert scenario(thr - 0.01, warm=8) == []


def test_previous_session_without_a_closing_candle_gives_no_trade():
    assert scenario(115.0, last_warm_close=False) == []


def test_one_trade_per_day():
    rest = [("10:00", 113.0, 104.0, 105.0), ("11:00", 118.0, 100.0, 116.0)]  # stop hit at 10:00
    [t] = scenario(115.0, rest=rest)
    assert t.exit_reason is ExitReason.STOP_LOSS


def test_a_trade_on_each_of_two_days_uses_the_new_prior_high():
    days = weekdays(date(2026, 1, 5), 7)
    candles = []
    for k, d in enumerate(days[:5]):
        candles += warm_day(d, k)
    day1 = [("12:00", 118.0, 112.0, 116.0), ("15:59", 117.0, 114.0, 116.0),
            ("16:00", 117.0, 114.0, 116.0)]  # fmt: skip
    candles += trade_day(days[5], 115.0, day1)
    candles += trade_day(days[6], 120.0, [("15:59", 121.0, 119.0, 120.5)])  # prior high is 118
    trades = run(candles, **SMALL)
    assert [t.direction for t in trades] == [LONG, LONG]
    assert trades[1].entry == 120.0


# --- exits ----------------------------------------------------------------------------------------


def test_time_exit_default_is_1559_in_index_mode_and_is_flat_before_the_rollover():
    [t] = scenario(115.0)
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 107.5
    assert t.exit_time == at(TRADE_DAY, "15:59")
    assert rollover_nights(t.entry_time, t.exit_time) == 0  # no swap


def test_time_exit_at_a_custom_exit_time():
    rest = [("11:00", 118.0, 112.0, 116.5), ("12:00", 118.0, 112.0, 117.0),
            ("15:59", 118.0, 112.0, 114.0)]  # fmt: skip
    [t] = scenario(115.0, rest=rest, cfg={"exit_time": time(12, 0)})
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 117.0
    assert t.exit_time == at(TRADE_DAY, "12:00")


def test_stop_hit_before_the_time_exit():
    rest = [("10:00", 116.0, 104.0, 105.0), ("15:59", 109.0, 107.0, 107.5)]
    [t] = scenario(115.0, rest=rest)
    assert t.exit_reason is ExitReason.STOP_LOSS and t.exit_price == pytest.approx(105.0)


def test_missing_exit_candle_closes_at_the_first_later_candle():
    rest = [("12:00", 118.0, 112.0, 116.0), ("18:00", 118.0, 112.0, 114.1),
            ("19:00", 118.0, 112.0, 115.0)]  # fmt: skip
    [t] = scenario(115.0, rest=rest)
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 114.1
    assert t.exit_time == at(TRADE_DAY, "18:00")


def test_missing_exit_candle_fallback_on_the_next_day():
    days = weekdays(date(2026, 1, 5), 7)
    candles = []
    for k, d in enumerate(days[:5]):
        candles += warm_day(d, k)
    candles += trade_day(days[5], 115.0, [("12:00", 118.0, 112.0, 116.0)])
    candles += [candle(days[6], "03:00", 114, 115, 113, 114.3)]
    [t] = run(candles, **SMALL)
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 114.3


# --- fx mode ----------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "start",
    [date(2026, 1, 5), date(2026, 3, 2), date(2026, 3, 5), date(2026, 10, 26), date(2026, 6, 1)],
)
def test_fx_mode_trades_at_0500_new_york_also_across_dst_changes(start):
    """2026-03-08 and 2026-11-01 are DST changes (US); sessions follow New York time."""
    days = weekdays(start, 6)
    [t] = scenario(115.0, mode="fx", start=start)
    assert t.direction is LONG and t.entry_time == at(days[5], "05:00")
    assert t.entry_time.astimezone(NY).time() == time(5, 0)
    assert t.exit_time == at(days[5], "16:59") and t.exit_price == 107.5
    assert rollover_nights(t.entry_time, t.exit_time) == 0


def test_fx_entry_utc_hour_moves_with_dst_but_the_new_york_time_does_not():
    [winter] = scenario(115.0, mode="fx", start=date(2026, 1, 5))
    [summer] = scenario(115.0, mode="fx", start=date(2026, 6, 1))
    assert winter.entry_time.hour == 10 and summer.entry_time.hour == 9  # 05:00 ET in UTC


def test_exit_time_default_depends_on_the_mode():
    assert GapMomentumConfig(mode="fx").exit_time_resolved == time(16, 59)
    assert GapMomentumConfig().exit_time_resolved == time(15, 59)
    assert GapMomentumConfig(mode="fx", exit_time=time(8, 0)).exit_time_resolved == time(8, 0)


def test_fx_previous_session_without_its_1700_candle_gives_no_trade():
    assert scenario(115.0, mode="fx", last_warm_close=False) == []


# --- strategy contract ----------------------------------------------------------------------------------


def test_strategy_attributes():
    s = GapMomentum("NAS100", GapMomentumConfig())
    assert s.base_timeframe is Timeframe.M1 and s.timeframes == (Timeframe.M1,)
    assert s.uses_session_break_even is False
    assert s.min_warmup_days >= math.ceil(91 * 1.5)  # vol_days + 1 closes


def test_config_defaults_are_the_spec():
    c = GapMomentumConfig()
    assert (c.mode, c.entry_z, c.vol_days, c.atr_period) == ("index", 0.1, 90, 14)
    assert (c.stop_atr, c.target_r, c.side) == (1.0, 0.0, "momentum")
    assert c.exit_time is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": "crypto"}, {"side": "random"}, {"entry_z": -0.1}, {"vol_days": 1},
        {"atr_period": 0}, {"stop_atr": 0}, {"target_r": -1.0}, {"exit_time": time(9, 30)},
        {"exit_time": time(17, 0)}, {"mode": "fx", "exit_time": time(5, 0)},
        {"mode": "fx", "exit_time": time(17, 1)}, {"zone": "Nowhere/Land"},
    ],
)  # fmt: skip
def test_config_validation(kwargs):
    with pytest.raises(Exception):  # noqa: B017 - ValueError or ZoneInfoNotFoundError
        GapMomentumConfig(**kwargs)


# --- no lookahead -----------------------------------------------------------------------------------


def orders_by_index(candles: list[Candle], mode="index", side="momentum") -> dict[int, list]:
    series = CandleSeries("T", M1, candles)
    strategy = GapMomentum("T", GapMomentumConfig(mode=mode, side=side, **SMALL))
    out = {}
    for i, c in enumerate(candles):
        orders = strategy.on_candle(c.ts + M1.duration, {M1: series.view(i)})
        strategy.exits()
        if orders:
            out[i] = orders
    return out


def many_days(mode="index") -> list[Candle]:
    days = weekdays(date(2026, 3, 2), 22)
    candles = []
    for k, d in enumerate(days):
        if k < 6:
            candles += warm_day(d, k, mode)
        else:
            o = 115.0 if k % 3 == 0 else (95.0 if k % 3 == 1 else 105.0)
            rest = [("12:00", HIGH, LOW, 105.0), (EXITS[mode], 105.5, 104.5, 105.0),
                    (SESSIONS[mode][1], 105.5, 104.5, 105.0)]  # fmt: skip
            candles += trade_day(d, o, rest, mode)
    return candles


@pytest.mark.parametrize(("mode", "open_t"), [("index", time(9, 30)), ("fx", time(5, 0))])
@pytest.mark.parametrize("side", ["momentum", "fade"])
def test_orders_only_come_from_the_session_open_candle(mode, open_t, side):
    candles = many_days(mode)
    out = orders_by_index(candles, mode, side)
    assert out
    for i in out:
        assert (candles[i].ts + M1.duration).astimezone(NY).time() == open_t


@pytest.mark.parametrize("mode", ["index", "fx"])
@pytest.mark.parametrize("side", ["momentum", "fade"])
def test_appending_future_candles_never_changes_orders_already_given(mode, side):
    candles = many_days(mode)
    full = orders_by_index(candles, mode, side)
    for cut in (len(candles) - 1, len(candles) - 5, len(candles) // 2, 20):
        prefix = orders_by_index(candles[:cut], mode, side)
        assert prefix == {i: o for i, o in full.items() if i < cut}
