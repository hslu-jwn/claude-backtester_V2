"""Hypothesis 10: hand-calculated Wilder RSI, session closes, filters and causality."""

from datetime import date, time
from pathlib import Path

import pytest
from test_timed_hold import LONG, M1, SHORT, at, candle, run, weekdays

from backtester.core.series import CandleSeries
from backtester.engine.trade import ExitReason
from backtester.strategy.timed_hold.config import TimedHoldConfig
from backtester.strategy.timed_hold.strategy import TimedHold
from backtester.tools.research_grid import expand, load_grid, variant_settings


def config(**overrides):
    return TimedHoldConfig(**{
        "direction": "rsi", "entry_time": time(16), "exit_time": time(16),
        "hold_days": 1, "atr_period": 1, "stop_atr": 2.0, **overrides,
    })


def sessions(closes):
    days = weekdays(date(2026, 1, 5), len(closes))
    return [c for d, p in zip(days, closes, strict=True) for c in (
        candle(d, "12:00", p, p + 10, p - 10, p),
        candle(d, "16:00", p, p, p, p),
    )]


def replay(candles, cfg=None, stop=None):
    strategy = TimedHold("TEST", cfg or config())
    series = CandleSeries("TEST", M1, candles)
    orders = []
    for i, c in enumerate(candles[:stop]):
        now = c.ts + M1.duration
        orders.extend((now, o) for o in strategy.on_candle(now, {M1: series.view(i)}))
    return strategy, orders


def test_hand_calculated_wilder_rsi_not_a_rolling_simple_average():
    # 100,102,101 seeds gains=1, losses=.5. Next +3 -> gains=2, losses=.25:
    # RSI=100*2/2.25=88.888...; next -2 -> gains=1, losses=1.125 -> 47.0588.
    strategy, _ = replay(sessions([100, 102, 101, 104])[:-1])
    assert strategy._rsi(104) == pytest.approx(100 * 2 / 2.25)
    strategy, _ = replay(sessions([100, 102, 101, 104, 102])[:-1])
    assert strategy._rsi(102) == pytest.approx(100 / 2.125)


@pytest.mark.parametrize(("closes", "side"), [
    ([103, 102, 101], LONG), ([101, 102, 103], SHORT), ([100, 102, 100], None),
])
def test_threshold_long_short_or_none(closes, side):
    _, orders = replay(sessions(closes))
    assert [o.direction for _, o in orders] == ([] if side is None else [side])


@pytest.mark.parametrize(("kwargs", "closes"), [
    ({"rsi_long_below": 0}, [103, 102, 101]),
    ({"rsi_short_above": 0}, [101, 102, 103]),
    ({"rsi_short_above": 100}, [101, 102, 103]),
    ({"rsi_long_below": 50, "rsi_short_above": 50}, [100, 102, 100]),
])
def test_disabled_sides_and_strict_thresholds(kwargs, closes):
    assert replay(sessions(closes), config(**kwargs))[1] == []


@pytest.mark.parametrize(("closes", "side"), [
    ([50, 100, 99, 98], LONG), ([150, 100, 101, 102], SHORT),
])
def test_sma_includes_signal_close_and_is_symmetric(closes, side):
    # Last 3 closes would reject; last 4 INCLUDING today admit the signal.
    # Day 3 RSI is 98.04 (mirror 1.96); only day 4 crosses 97 (mirror 3).
    cfg = ({"rsi_long_below": 97, "rsi_short_above": 0} if side is LONG
           else {"rsi_long_below": 0, "rsi_short_above": 3})
    _, orders = replay(sessions(closes), config(sma_filter_days=4, **cfg))
    assert orders[-1][1].direction is side
    assert replay(sessions(closes), config(sma_filter_days=3, **cfg))[1] == []


@pytest.mark.parametrize("closes", [[103, 102, 101], [101, 102, 103]])
def test_one_day_sma_is_signal_close_and_equality_rejects_both_sides(closes):
    assert replay(sessions(closes), config(sma_filter_days=1))[1] == []


def test_no_signal_until_rsi_and_sma_have_enough_closes():
    assert replay(sessions([103, 102]))[1] == []
    assert replay(sessions([103, 102, 101]), config(sma_filter_days=4))[1] == []
    assert len(replay(sessions([103, 102, 101]))[1]) == 1


def test_flat_closes_produce_no_order():
    assert replay(sessions([100, 100, 100, 100]))[1] == []


def test_only_regular_session_closes_count_once_not_intraday_or_late_candles():
    candles = sessions([103, 1000, 102, 101])
    del candles[3]  # missing 16:00: irregular day, its 1000 close must be excluded
    d = weekdays(date(2026, 1, 5), 4)[-1]
    candles.append(candle(d, "16:01", 2000, 2000, 2000, 2000))
    strategy, orders = replay(candles)
    assert [(t, o.direction, o.entry) for t, o in orders] == [(at(d, "16:00"), LONG, 101)]
    assert list(strategy._closes) == [103, 102]  # today remains a preview until finished


@pytest.mark.parametrize("hold", [1, 3])
def test_rsi_trade_exits_after_hold_days_without_intervening_entries(hold):
    closes = [103, 102, 101] + [101] * hold
    trades = run(sessions(closes), **{
        f: getattr(config(hold_days=hold), f) for f in (
            "direction", "entry_time", "exit_time", "hold_days", "atr_period", "stop_atr"
        )
    })
    [trade] = trades
    days = weekdays(date(2026, 1, 5), len(closes))
    assert trade.direction is LONG
    assert trade.entry_time == at(days[2], "16:00")
    assert trade.exit_time == at(days[2 + hold], "16:00")
    assert trade.exit_reason is ExitReason.SIGNAL


def test_appending_future_candles_never_changes_earlier_orders():
    prefix = sessions([103, 102, 101])
    longer = sessions([103, 102, 101, 900, 1])
    _, before = replay(prefix)
    _, after = replay(longer, stop=len(prefix))
    assert before == after
    _, all_orders = replay(longer)
    assert all_orders[:len(before)] == before


def test_history_is_bounded_and_warmup_covers_sma():
    strategy, _ = replay(sessions([100 + i % 3 for i in range(250)]))
    assert strategy._closes.maxlen == 3
    assert len(strategy._closes) == 3
    assert TimedHold("TEST", config(sma_filter_days=200)).min_warmup_days >= 300


@pytest.mark.parametrize("kwargs", [
    {"rsi_period": 0}, {"rsi_period": 1.5}, {"rsi_period": True},
    {"rsi_long_below": -1}, {"rsi_short_above": 101},
    {"rsi_long_below": float("nan")}, {"rsi_short_above": float("inf")},
    {"sma_filter_days": -1}, {"sma_filter_days": 1.5}, {"sma_filter_days": True},
    {"min_move_atr": 0.5},
])
def test_invalid_research_settings_fail_clearly(kwargs):
    with pytest.raises(ValueError):
        config(**kwargs)


def test_rsi_grid_has_exactly_eight_paired_cells_without_running_it():
    spec = load_grid(Path("research/grids/timed_hold_rsi2.toml"))
    variants, size, sampled = expand(spec)
    assert size == len(variants) == 8 and not sampled
    assert spec.symbols == ("US500", "NAS100")
    assert spec.min_trades == 100
    assert not spec.monkeys and not spec.sensitivity and not spec.entry_screen
    cells = [variant_settings(spec, v).strategy for v in variants]
    assert {(c.rsi_long_below, c.rsi_short_above, c.sma_filter_days, c.hold_days)
            for c in cells} == {
        (lo, hi, sma, hold) for lo, hi, sma in (
            (10, 90, 0), (5, 95, 0), (10, 0, 200), (5, 0, 200)
        ) for hold in (1, 3)
    }
    assert cells[0].rsi_long_below == 10 and cells[0].hold_days == 1
