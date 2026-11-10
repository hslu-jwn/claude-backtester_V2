"""Hand-built cash sessions; no market data or research runner is executed."""

import tomllib
from datetime import UTC, date, datetime, time, timedelta
from itertools import product
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts, rollover_nights
from backtester.engine.trade import ExitReason
from backtester.strategy.base import UnsupportedSymbolError
from backtester.strategy.daily_reversal.config import DailyReversalConfig
from backtester.strategy.daily_reversal.strategy import SESSIONS, DailyReversal

M1 = Timeframe.M1
NY = ZoneInfo("America/New_York")
DAYS = []
d = date(2026, 1, 5)
while len(DAYS) < 40:
    if d.weekday() < 5:
        DAYS.append(d)
    d += timedelta(days=1)


def bar(day, clock, o, h, lo, c, zone=NY):
    now = datetime.combine(day, time.fromisoformat(clock), zone).astimezone(UTC)
    return Candle(now - M1.duration, o, h, lo, c)


def session(i, o=105, h=110, lo=100, c=105):
    return [bar(DAYS[i], "09:31", o, h, lo, c), bar(DAYS[i], "16:00", c, c, c, c)]


def e8(confirm=3):
    """7 prior lows=100; D1 low=95; D2 high=112, low=98; D3..6 low=97."""
    out = [c for i in range(7) for c in session(i)]
    out += session(7, 105, 110, 95, 105)
    out += session(8, 105, 112, 98, 105)
    for day in range(3, confirm):
        out += session(day + 6, 105, 110, 99, 105)
    out += session(confirm + 6, 105, 111, 97, 105)
    return out


def cap():
    # signal range=20 vs 10, low=90 <100, close=106 >=105 (top quarter)
    return [c for i in range(9) for c in session(i)] + session(9, 100, 110, 90, 106)


def feed(candles, strategy=None, **config):
    strategy = strategy or DailyReversal("US500", DailyReversalConfig(**config))
    series = CandleSeries("US500", M1, candles)
    orders, exits = [], []
    for i, candle in enumerate(candles):
        now = candle.ts + M1.duration
        orders += [(now, o) for o in strategy.on_candle(now, {M1: series.view(i)})]
        exits += [(now, ref) for ref in strategy.exits()]
    return strategy, orders, exits


def execute(candles, **config):
    costs = CostConfig(
        symbols={
            "US500": SymbolCosts(
                0,
                0,
                1,
                swap_long_per_lot=-1,
                swap_short_per_lot=-2,
                swap_triple_weekday=4,
                tick_size=0.01,
            )
        },
        spread_table=None,
        conversion_adjustment=0,
        tp_penetration=0,
    )
    strategy = DailyReversal("US500", DailyReversalConfig(**config))
    trades = run_backtest(
        strategy,
        [CandleSeries("US500", M1, candles)],
        EngineConfig(costs=costs, intrabar="sl_first"),
    )
    return strategy, trades


@pytest.mark.parametrize("confirm", [3, 4, 5, 6])
@pytest.mark.parametrize("short", [False, True])
def test_e8_all_confirmation_days_and_mirror(confirm, short):
    candles = e8(confirm) + session(confirm + 7, 114, 116, 113, 115)
    if short:
        candles = [
            Candle(c.ts, 220 - c.open, 220 - c.low, 220 - c.high, 220 - c.close) for c in candles
        ]
    _, orders, _ = feed(candles)
    assert len(orders) == 1
    now, order = orders[0]
    assert now == candles[-2].ts + M1.duration
    assert order.direction is (Direction.BEARISH if short else Direction.BULLISH)
    assert order.entry == (105 if short else 115)
    assert order.stop_loss == pytest.approx(122.01 if short else 97.99)
    assert order.take_profit == pytest.approx(70.98 if short else 149.02)
    assert not order.limit_fill


def test_e8_day7_is_too_late_and_equal_extremes_do_not_qualify():
    assert feed(e8(7) + session(14, 115, 116, 114, 115))[1] == []
    candles = e8()
    # Day 1 ties the old lows, rather than breaking them.
    candles[14] = bar(DAYS[7], "09:31", 105, 110, 100, 105)
    assert feed(candles + session(10, 115, 116, 114, 115))[1] == []


def test_cap_next_session_only_and_gap_uses_close_not_open_or_trigger():
    candles = cap()
    assert feed(candles, setup="CAP")[1] == []
    _, orders, _ = feed(candles + session(10, 120, 123, 119, 122), setup="CAP")
    assert len(orders) == 1
    assert orders[0][1].entry == 122  # decision 3: even a gap fills at close
    assert orders[0][1].stop_loss == pytest.approx(89.99)


@pytest.mark.parametrize("h,lo,c", [(110, 100, 109), (100, 90, 99), (110, 90, 104.99)])
def test_cap_rejects_tied_low_tied_range_or_close_below_quarter(h, lo, c):
    candles = cap()[:-2] + session(9, c, h, lo, c)
    assert feed(candles + session(10, 120, 123, 119, 122), setup="CAP")[1] == []


@pytest.mark.parametrize("setup,valid", [("E8", 4), ("CAP", 2)])
@pytest.mark.parametrize("late", [False, True])
def test_pending_expiry_includes_last_valid_session(setup, valid, late):
    candles = e8() if setup == "E8" else cap()
    for i in range(10, 10 + valid - 1 + int(late)):
        candles += session(i, 105, 109, 101, 105)
    candles += session(10 + valid - 1 + int(late), 115, 116, 114, 115)
    assert len(feed(candles, setup=setup)[1]) == (0 if late else 1)


def test_trigger_rejects_close_behind_stop_and_same_candle_stop_touch():
    assert feed(e8() + [bar(DAYS[10], "10:00", 105, 114, 96, 97)])[1] == []
    assert feed(e8() + [bar(DAYS[10], "10:00", 105, 114, 97, 113)])[1] == []


def test_both_directions_crossed_cancel_both_and_no_later_entry():
    # A long E8 is armed, then its mirrored pattern arms a short while long remains valid.
    strategy, _, _ = feed(e8())
    from backtester.strategy.daily_reversal.strategy import Pending

    strategy._pending[Direction.BEARISH] = Pending(Direction.BEARISH, 100, 120, 13)
    candles = [
        bar(DAYS[10], "10:00", 105, 114, 99, 113),
        bar(DAYS[10], "10:01", 113, 115, 112, 114),
    ]
    assert feed(candles, strategy)[1] == []
    assert strategy._pending == {}


def test_no_target_and_five_full_sessions_after_fill_not_including_fill():
    candles = e8() + session(10, 114, 116, 113, 115)
    for i in range(11, 16):
        candles += session(i, 115, 118, 113, 116)
    _, trades = execute(candles, target_r=0)
    assert len(trades) == 1
    t = trades[0]
    assert t.take_profit is None
    assert t.exit_reason is ExitReason.SIGNAL
    assert t.exit_time == candles[-1].ts + M1.duration
    nights = rollover_nights(t.entry_time, t.exit_time, 4)
    assert nights == 7  # Thursday entry, Friday triple + Monday..Thursday
    assert t.swap_r == pytest.approx(-7 / 17.01)
    assert t.r_net == pytest.approx(t.r_gross + t.swap_r)


@pytest.mark.parametrize("stop", [False, True])
def test_target_before_timer_and_stop_first_when_both_hit(stop):
    candles = e8() + session(10, 114, 116, 113, 115)
    candles += [bar(DAYS[11], "09:31", 115, 151, 97 if stop else 114, 120)]
    _, trades = execute(candles)
    assert len(trades) == 1
    assert trades[0].exit_reason is (ExitReason.STOP_LOSS if stop else ExitReason.TAKE_PROFIT)


def test_missing_exit_close_falls_back_and_is_flagged():
    candles = e8() + session(10, 114, 116, 113, 115)
    candles += session(11, 115, 118, 113, 116)[:-1]
    candles += session(12, 115, 118, 113, 116)
    strategy, trades = execute(candles, hold_sessions=1, target_r=0)
    assert trades[0].exit_time == candles[-2].ts + M1.duration
    assert any(r["kind"] == "missing_exit_candle" for r in strategy.integrity_records())


def test_incomplete_signal_session_cannot_arm_and_resets_history():
    candles = cap()[:-1] + session(10, 120, 123, 119, 122)
    strategy, orders, _ = feed(candles, setup="CAP")
    assert orders == []
    assert any(r["kind"] == "incomplete_session" for r in strategy.integrity_records())


def test_newer_setup_replaces_pending_same_direction():
    candles = cap() + session(10, 100, 111, 80, 105)
    _, orders, _ = feed(candles + session(11, 112, 114, 111, 113), setup="CAP")
    assert len(orders) == 1
    assert orders[0][1].stop_loss == pytest.approx(79.99)


def test_callbacks_release_single_position_and_instances_are_independent():
    strategy, orders, _ = feed(cap() + session(10, 112, 114, 111, 113), setup="CAP")
    assert len(orders) == 1
    ref = orders[0][1].ref
    assert strategy._position is not None
    strategy.on_order_skipped(ref, orders[0][0])
    assert strategy._position is None
    strategy.on_trade_closed(ref, None)
    assert DailyReversal("US500")._pending == {}


def test_no_lookahead_prefixes_preserve_orders_and_exits():
    candles = e8() + session(10, 114, 116, 113, 115)
    for i in range(11, 17):
        candles += session(i, 115, 118, 113, 116)
    _, expected, expected_exits = feed(candles, target_r=0)
    assert expected and expected_exits
    for n in range(1, len(candles) + 1):
        _, orders, exits = feed(candles[:n], target_r=0)
        cutoff = candles[n - 1].ts + M1.duration
        assert orders == [x for x in expected if x[0] <= cutoff]
        assert exits == [x for x in expected_exits if x[0] <= cutoff]


@pytest.mark.parametrize("symbol", list(SESSIONS))
def test_all_cash_clocks_and_dst_are_local(symbol):
    strategy = DailyReversal(symbol, DailyReversalConfig(setup="CAP"))
    zone, opening, closing = SESSIONS[symbol]
    tz = ZoneInfo(zone)
    candles = []
    for i in range(10):
        start = datetime.combine(DAYS[i], opening, tz) + M1.duration
        end = datetime.combine(DAYS[i], closing, tz)
        lo, c = (90, 106) if i == 9 else (100, 105)
        candles += [
            Candle(start.astimezone(UTC) - M1.duration, 105, 110, lo, c),
            Candle(end.astimezone(UTC) - M1.duration, c, c, c, c),
        ]
    feed(candles, strategy)
    assert Direction.BULLISH in strategy._pending
    assert strategy.uses_session_break_even is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"setup": "bad"},
        {"target_r": -1},
        {"target_r": float("nan")},
        {"target_r": float("inf")},
        {"hold_sessions": 0},
        {"hold_sessions": True},
        {"hold_sessions": 1.5},
        {"tick_size": 0},
    ],
)
def test_config_rejects_invalid_values(kwargs):
    with pytest.raises(ValueError):
        DailyReversalConfig(**kwargs)


def test_unsupported_symbol_and_candle_validation():
    with pytest.raises(UnsupportedSymbolError):
        DailyReversal("EURUSD")
    with pytest.raises(ValueError):
        bar(DAYS[0], "10:00", 100, 99, 95, 100)
    with pytest.raises(ValueError):
        bar(DAYS[0], "10:00", 100, float("nan"), 95, 100)


def test_grid_has_exactly_four_pooled_cells_and_diagnostics_off():
    data = tomllib.loads(Path("research/grids/daily_reversal.toml").read_text())
    assert data["strategy"] == "daily_reversal"
    assert set(data["symbols"]) == set(SESSIONS)
    assert data["min_trades"] == 80
    for name in ("monkeys", "sensitivity", "entry_screen", "shocks"):
        assert data[name] is False
    cells = list(product(data["grid"]["setup"], data["grid"]["target_r"]))
    assert cells == [("E8", 2.0), ("E8", 0.0), ("CAP", 2.0), ("CAP", 0.0)]
    assert data["base"]["hold_sessions"] == 5


def test_e8_uses_exactly_seven_prior_days_not_eighth():
    candles = session(0, 105, 110, 80, 105)
    candles += [c for i in range(1, 8) for c in session(i)]
    candles += session(8, 105, 110, 95, 105)
    candles += session(9, 105, 112, 98, 105)
    candles += session(10, 105, 111, 97, 105)
    candles += session(11, 115, 116, 114, 115)
    _, orders, _ = feed(candles)
    assert len(orders) == 1  # the low of 80 was eight days before day 1, so is irrelevant


def test_missing_first_minute_cannot_fill_pending_trigger():
    candles = e8() + [bar(DAYS[10], "11:00", 114, 116, 113, 115)]
    strategy, orders, _ = feed(candles)
    assert orders == []
    assert any(r["kind"] == "incomplete_session" for r in strategy.integrity_records())


def test_retracing_trigger_still_uses_close_per_decision3():
    _, orders, _ = feed(e8() + [bar(DAYS[10], "09:31", 105, 114, 100, 105)])
    assert len(orders) == 1
    assert orders[0][1].entry == 105  # explicitly exposes approximation's better-fill case


def test_session_records_have_runner_overlap_fields_and_censoring_flag():
    candles = e8() + session(10, 114, 116, 113, 115)
    strategy, trades = execute(candles)
    assert trades[0].exit_reason is ExitReason.END_OF_DATA
    records = strategy.session_records(candles[-1].ts + M1.duration)
    assert any(r["kind"] == "censored_position" for r in records)
    for record in records:
        assert datetime.fromisoformat(record["end"]) > datetime.fromisoformat(record["start"])
        assert record["integrity_failed"] is True


def test_real_grid_parser_expands_without_running_or_editing_registry(monkeypatch):
    from backtester import settings
    from backtester.strategy import registry
    from backtester.tools import research_grid

    temporary = {
        **registry.REGISTRY,
        "daily_reversal": registry.StrategySpec(
            "daily_reversal", "Strategy 13", DailyReversalConfig, DailyReversal
        ),
    }
    for module in (registry, settings, research_grid):
        monkeypatch.setattr(module, "REGISTRY", temporary)
    spec = research_grid.load_grid("research/grids/daily_reversal.toml")
    variants, size, sampled = research_grid.expand(spec)
    assert size == len(variants) == 4
    assert not sampled
    configs = [research_grid.variant_settings(spec, v).strategy for v in variants]
    assert [(c.setup, c.target_r, c.hold_sessions) for c in configs] == [
        ("E8", 2.0, 5),
        ("E8", 0.0, 5),
        ("CAP", 2.0, 5),
        ("CAP", 0.0, 5),
    ]


def test_cap_remains_long_only_and_no_new_signal_while_position_open():
    candles = cap() + session(10, 112, 114, 111, 113)
    # This would be a new CAP if flat: low 70, range 50 >20, close in top quarter.
    candles += session(11, 100, 120, 70, 112)
    strategy, orders, _ = feed(candles, setup="CAP")
    assert len(orders) == 1
    assert orders[0][1].direction is Direction.BULLISH
    assert strategy._pending == {}
    strategy.on_trade_closed(orders[0][1].ref, None)
    assert feed(session(12, 122, 124, 121, 123), strategy)[1] == []
    mirrored = [Candle(c.ts, 220 - c.open, 220 - c.low, 220 - c.high, 220 - c.close) for c in cap()]
    assert feed(mirrored + session(10, 100, 104, 90, 99), setup="CAP")[1] == []


def test_confirmed_e8_sequence_is_not_rearmed_on_later_lower_low():
    strategy, _, _ = feed(e8())
    assert len(strategy._pending) == 1
    original = strategy._pending[Direction.BULLISH]
    feed(session(10, 105, 111, 96, 105), strategy)
    assert strategy._pending[Direction.BULLISH] == original


@pytest.mark.parametrize("start,offset", [(date(2026, 1, 5), 5), (date(2026, 7, 6), 4)])
def test_new_york_dst_conversion_uses_zoneinfo(start, offset):
    now = bar(start, "09:31", 105, 110, 100, 105).ts + M1.duration
    assert now.hour == 9 + offset
    strategy = DailyReversal("US500")
    feed(
        [bar(start, "09:31", 105, 110, 100, 105), bar(start, "16:00", 105, 105, 105, 105)], strategy
    )
    assert len(strategy._history) == 1


def test_zero_price_invalidates_session_and_cancels_pending():
    candles = e8() + [bar(DAYS[10], "09:31", 0, 0, 0, 0)]
    strategy, orders, _ = feed(candles)
    assert orders == []
    assert strategy._pending == {}
    assert any(r["kind"] == "invalid_candle" for r in strategy.integrity_records())


def test_tick_metadata_overrides_default_but_explicit_tick_is_preserved():
    costs = CostConfig(symbols={"US500": SymbolCosts(0, 0, 1, tick_size=0.5)})
    strategy = DailyReversal("US500")
    strategy.configure_costs(costs)
    _, orders, _ = feed(e8() + session(10, 115, 116, 114, 115), strategy)
    assert orders[0][1].stop_loss == 97.5
    strategy = DailyReversal("US500", DailyReversalConfig(tick_size=1.0))
    strategy.configure_costs(costs)
    _, orders, _ = feed(e8() + session(10, 115, 116, 114, 115), strategy)
    assert orders[0][1].stop_loss == 97.0


def test_short_swap_is_side_specific_and_weekends_do_not_count_as_sessions():
    candles = e8() + session(10, 114, 116, 113, 115)
    for i in range(11, 16):
        candles += session(i, 115, 118, 113, 116)
    candles = [
        Candle(c.ts, 220 - c.open, 220 - c.low, 220 - c.high, 220 - c.close) for c in candles
    ]
    _, trades = execute(candles, target_r=0)
    assert len(trades) == 1
    assert trades[0].direction is Direction.BEARISH
    assert trades[0].exit_time == candles[-1].ts + M1.duration
    assert trades[0].swap_r == pytest.approx(-14 / 17.01)


def test_duplicate_candle_rejected_and_session_records_do_not_mutate_state():
    strategy, _, _ = feed(cap(), setup="CAP")
    first = strategy.integrity_records()
    assert strategy.session_records(cap()[-1].ts + M1.duration) == first
    assert strategy.integrity_records() == first
    with pytest.raises(ValueError, match="strictly increasing"):
        feed(cap()[-1:], strategy)
