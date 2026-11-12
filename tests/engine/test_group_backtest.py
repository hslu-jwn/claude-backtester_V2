"""Paired M1 execution acceptance. Spec: design/multi-symbol.md › B."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from backtester.core.errors import LookaheadError
from backtester.core.market import ReferenceInput
from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.engine.group_backtest import run_group_backtest
from backtester.engine.trade import ExitReason
from backtester.strategy.group import EntryPolicy, ExitPolicy, GroupLeg, GroupOrder, GroupStrategy

START = datetime(2026, 1, 5, 10, tzinfo=UTC)
MINUTE = timedelta(minutes=1)
LONG, SHORT = Direction.BULLISH, Direction.BEARISH


def at(minute):
    return START + minute * MINUTE


def series(symbol, rows):
    """Rows are (opening minute, open, high, low, close), deliberately hand built."""
    return CandleSeries(symbol, Timeframe.M1, [
        Candle(at(m), o, h, lo, c) for m, o, h, lo, c in rows
    ])


def quiet(symbol, minutes=range(7), price=100):
    return series(symbol, [(m, price, price + .1, price - .1, price) for m in minutes])


def costs(spread=0, slippage=0, commission=0, **kwargs):
    return CostConfig(symbols={s: SymbolCosts(spread, commission, 1, slippage=slippage)
                               for s in ("A", "B")}, **kwargs)


def intent(**kwargs):
    return replace(GroupOrder("g", (GroupLeg("A", LONG, 1, 2), GroupLeg("B", SHORT, 1, 1)),
                              at(1), EntryPolicy.NEXT_OPEN_ALL_OR_NONE,
                              ExitPolicy.ALL_LEGS_NEXT_OPEN_AFTER_STOP, 3), **kwargs)


class Script(GroupStrategy):
    legs = ("A", "B")

    def __init__(self, order=None, exit_at=None):
        self.order = order or intent()
        self.exit_at = exit_at
        self.seen = []
        self.closed = []
        self.open_seen = []

    def on_group_candle(self, now, market):
        self.seen.append((now, market))
        return [self.order] if now == self.order.intent_time else []

    def group_exits(self, now, market, open_groups):
        self.open_seen.append((now, open_groups))
        return ["g"] if now == self.exit_at else []

    def on_group_closed(self, result):
        self.closed.append(result)


def run(a=None, b=None, strategy=None, cfg=None, **kwargs):
    return run_group_backtest(strategy or Script(exit_at=at(3)),
                              {"A": a or quiet("A"), "B": b or quiet("B")},
                              cfg or costs(), **kwargs)


def test_cross_symbol_prefix_and_retained_snapshot():
    strategy = Script(exit_at=at(3))
    # Explicitly permit the older B observation so readiness allows this callback.
    strategy.references = (ReferenceInput("B", "leg", (Timeframe.M1,), 2 * MINUTE),)
    # B has an older close, then its next candle closes at 10:02.
    run(b=quiet("B", [-1, 1, 2, 3, 4]), strategy=strategy)
    snapshot = dict(strategy.seen)[at(1)]
    b = snapshot.views["B"][Timeframe.M1]
    assert b.current.ts == at(-1)
    with pytest.raises(LookaheadError):
        _ = b[1]
    assert b.cursor == 0  # retained snapshot did not advance with the replay


@pytest.mark.parametrize("extended", ["A", "B"])
def test_future_append_preserves_decisions_fills_and_closed_results(extended):
    base = {s: quiet(s, range(5)) for s in ("A", "B")}
    first = Script(exit_at=at(3))
    old = run_group_backtest(first, base, costs())
    base[extended] = quiet(extended, range(10))
    second = Script(exit_at=at(3))
    new = run_group_backtest(second, base, costs())
    assert old.closed == new.closed
    assert old.fills == new.fills
    assert [(t, tuple((s, m.views[s][Timeframe.M1].cursor) for s in first.legs))
            for t, m in first.seen] == [
        (t, tuple((s, m.views[s][Timeframe.M1].cursor) for s in second.legs))
        for t, m in second.seen if t <= at(5)]


def test_next_open_exact_market_fills_and_signal_callback_once():
    a = series("A", [(0, 90, 100, 90, 100), (1, 101, 101.1, 100.9, 101),
                     (2, 101, 101.1, 100.9, 101), (3, 102, 102.1, 101.9, 102)])
    strategy = Script(exit_at=at(3))
    result = run(a=a, strategy=strategy, cfg=costs(.2, .05))
    fa, fb = result.fills["g"]
    assert (fa.chart_entry, fa.entry_fill, fa.entry_time) == (101, 101.25, at(1))
    assert fb.entry_fill == pytest.approx(99.95)
    assert (fa.chart_exit, fa.exit_time, fa.exit_reason) == (102, at(3), ExitReason.SIGNAL)
    assert fa.exit_fill == pytest.approx(101.95)
    assert fb.exit_fill == pytest.approx(100.25)
    assert strategy.closed == list(result.closed)
    assert len(strategy.closed) == 1
    assert all(isinstance(o, GroupOrder) for _, groups in strategy.open_seen for o in groups)


def test_missing_entry_minute_waits_for_first_common_open():
    result = run(b=quiet("B", [0, 2, 3, 4, 5]))
    assert {f.entry_time for f in result.fills["g"]} == {at(2)}


def test_expiry_and_end_of_data_pending_are_rejected():
    result = run(b=quiet("B", [0, 5, 6]))
    assert [(r.group_id, r.reason) for r in result.rejected] == [("g", "expired")]
    assert not result.closed and not result.unresolved and not result.fills
    result = run(a=quiet("A", [0]), b=quiet("B", [0]))
    assert result.rejected[0].reason == "expired"


def test_expiry_boundary_is_inclusive():
    result = run(b=quiet("B", [0, 4, 5]), strategy=Script(exit_at=at(5)))
    assert result.fills["g"][0].entry_time == at(4)


def test_missing_cost_settings_rejects_whole_group():
    result = run(cfg=CostConfig(symbols={"A": SymbolCosts(0, 0, 1)}))
    assert result.rejected[0].reason.startswith("leg rejected: ")
    assert "B" in result.rejected[0].reason
    assert not result.unresolved and not result.fills


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_nonfinite_entry_open_rejects_atomically(bad):
    a = quiet("A", [0, 1])
    # Model construction rejects bad OHLC; inject corruption to test engine defence.
    object.__setattr__(a._candles[1], "open", bad)
    result = run(a=a)
    assert result.rejected[0].reason.startswith("leg rejected: ")
    assert not result.unresolved and not result.fills


def test_tick_rounding_zero_risk_rejects_atomically():
    cfg = costs(round_to_tick=True)
    cfg = replace(cfg, symbols={s: replace(c, tick_size=1) for s, c in cfg.symbols.items()})
    order = intent(legs=(GroupLeg("A", LONG, 1, .1), GroupLeg("B", SHORT, 1, 1)))
    result = run(strategy=Script(order), cfg=cfg)
    assert result.rejected[0].reason.startswith("leg rejected: ")
    assert not result.fills


def test_stop_confirmation_schedules_other_leg_next_open_not_same_minute_extremes():
    a = series("A", [(m, 100, 100.1, 97 if m == 4 else 99.9, 100) for m in range(7)])
    b = series("B", [(m, 100 if m < 5 else 99, 100.5, 80, 99) for m in range(7)])
    result = run(a=a, b=b, strategy=Script())
    fa, fb = result.fills["g"]
    assert (fa.chart_exit, fa.exit_time, fa.exit_reason) == (98, at(5), ExitReason.STOP_LOSS)
    assert (fb.chart_exit, fb.exit_time, fb.exit_reason) == (99, at(5), ExitReason.SIGNAL)


def test_both_stops_same_minute_and_stop_before_tp():
    a = series("A", [(0, 100, 100, 100, 100), (1, 100, 105, 95, 100)])
    b = series("B", [(0, 100, 100, 100, 100), (1, 100, 105, 95, 100)])
    order = intent(legs=tuple(replace(l, take_profit_distance=2) for l in intent().legs))
    result = run(a=a, b=b, strategy=Script(order))
    assert result.closed[0].r_gross == -1
    assert result.closed[0].exit_reasons == (ExitReason.STOP_LOSS,) * 2


@pytest.mark.parametrize("direction, gap, expected", [(LONG, 95, 94.95), (SHORT, 105, 105.25)])
def test_gap_stop_adverse_fill(direction, gap, expected):
    a = series("A", [(0, 100, 100, 100, 100), (1, 100, 100.1, 99.9, 100),
                     (2, gap, gap + .1, gap - .1, gap), (3, gap, gap, gap, gap)])
    order = intent(legs=(GroupLeg("A", direction, 1, 2), intent().legs[1]))
    result = run(a=a, strategy=Script(order), cfg=costs(.2, .05))
    assert result.fills["g"][0].exit_fill == pytest.approx(expected)


def test_short_stop_ask_trigger_matches_legacy():
    b = series("B", [(0, 100, 100, 100, 100), (1, 100, 100.85, 100, 100),
                     (2, 100, 100, 100, 100)])
    result = run(b=b, strategy=Script(), cfg=costs(.2, .05, short_sl_on_ask=True))
    fb = result.fills["g"][1]
    assert fb.exit_reason is ExitReason.STOP_LOSS
    assert fb.chart_exit == pytest.approx(100.8)
    assert fb.exit_fill == pytest.approx(101.05)


def test_residual_uses_stale_mark_and_waits_for_actual_next_candle():
    a = series("A", [(0, 100, 100, 100, 100), (1, 100, 100, 99.9, 100),
                     (4, 100, 100, 97, 99), (5, 99, 99, 99, 99)])
    b = quiet("B", [0, 1, 2])
    result = run(a=a, b=b, strategy=Script())
    residual = result.unresolved[0]
    assert residual.group_id == "g" and residual.residual
    assert len(residual.open_legs) == 1
    leg = residual.open_legs[0]
    assert (leg.symbol, leg.mark, leg.mark_time) == ("B", 100, at(3))
    assert not result.closed
    extended = run(a=a, b=quiet("B", [0, 1, 2, 10]), strategy=Script())
    assert extended.fills["g"][1].exit_time == at(10)
    assert len(extended.closed) == 1 and not extended.unresolved


def test_explicit_costed_example_reconciles_gross_and_net():
    # D = 2 + 1 = 3. Long +2, short +1 gross. Each pays .2 spread,
    # .1 round-trip slippage and .4 commission: net money 3 - 1.4 = 1.6.
    a = series("A", [(0, 100, 100, 100, 100), (1, 100, 100.1, 99.9, 100),
                     (2, 102, 102, 102, 102)])
    b = series("B", [(0, 100, 100, 100, 100), (1, 100, 100.1, 99.9, 100),
                     (2, 99, 99, 99, 99)])
    result = run(a=a, b=b, strategy=Script(exit_at=at(2)), cfg=costs(.2, .05, .4))
    group = result.closed[0]
    assert group.D == 3 and group.weights == (2 / 3, 1 / 3)
    assert group.r_gross == 1
    assert group.r_net == pytest.approx(1.6 / 3)
    assert group.reconcile()


def test_declared_higher_timeframe_and_readonly_reference_share_clock():
    strategy = Script()
    strategy.references = (
        ReferenceInput("A", "leg", (Timeframe.M1, Timeframe.H1), timedelta(hours=1),
                       require_contiguous=False),
        ReferenceInput("C", "reference", (Timeframe.M1,), MINUTE),
    )
    h1 = CandleSeries("A", Timeframe.H1, [Candle(at(-59), 100, 100, 100, 100)])
    result = run_group_backtest(strategy, {"A": (quiet("A"), h1), "B": quiet("B"),
                                           "C": quiet("C")}, costs())
    assert result.unresolved
    assert dict(strategy.seen)[at(1)].views["A"][Timeframe.H1].current.ts == at(-59)


def test_legacy_fixture_identical_across_new_module_import():
    import subprocess
    import sys
    from pathlib import Path
    from textwrap import dedent

    # Fresh interpreter ensures the first run really precedes the new engine import.
    script = dedent('''
        import sys
        sys.path.insert(0, sys.argv[1])
        from datetime import UTC, datetime, timedelta
        from backtester.core.models import Candle, Direction, Timeframe
        from backtester.core.series import CandleSeries
        from backtester.engine.backtest import EngineConfig, run_backtest
        from backtester.engine.costs import CostConfig, SymbolCosts
        from backtester.strategy.base import Order, Strategy

        start = datetime(2026, 1, 5, 10, tzinfo=UTC)
        class Legacy(Strategy):
            base_timeframe = Timeframe.M1
            timeframes = (Timeframe.M1,)
            def on_candle(self, now, views):
                if now == start + timedelta(minutes=1):
                    return [Order(Direction.BULLISH, 100, 98, 102)]
                return []

        data = CandleSeries("A", Timeframe.M1, [
            Candle(start, 100, 100, 100, 100),
            Candle(start + timedelta(minutes=1), 100, 102, 100, 102)])
        cfg = EngineConfig(costs=CostConfig(symbols={"A": SymbolCosts(0, 0, 1)}))
        assert "backtester.engine.group_backtest" not in sys.modules
        before = run_backtest(Legacy(), [data], cfg)
        import backtester.engine.group_backtest
        after = run_backtest(Legacy(), [data], cfg)
        assert before == after and before[0].r_gross == 1
    ''')
    source = str(Path(__file__).resolve().parents[2] / "src")
    completed = subprocess.run([sys.executable, "-c", script, source], capture_output=True, text=True,
                               timeout=30, check=False)
    assert completed.returncode == 0, completed.stderr


def test_protective_stop_and_peer_exit_continue_when_reference_is_missing():
    strategy = Script()
    strategy.references = (ReferenceInput("C", "reference", (Timeframe.M1,), timedelta(0)),)
    a = series("A", [(0, 100, 100, 100, 100), (1, 100, 100, 99.9, 100),
                     (2, 100, 100, 97, 99), (3, 99, 99, 99, 99)])
    result = run_group_backtest(strategy, {"A": a, "B": quiet("B"), "C": quiet("C", [0])},
                                costs())
    assert [now for now, _ in strategy.seen] == [at(1)]
    assert result.fills["g"][0].exit_reason is ExitReason.STOP_LOSS
    assert result.fills["g"][1].exit_time == at(3)
    assert strategy.closed == list(result.closed)


def test_queued_exit_uses_open_even_if_later_extreme_would_stop():
    b = series("B", [(0, 100, 100, 100, 100), (1, 100, 100, 100, 100),
                     (2, 100, 1000, 1, 100)])
    result = run(b=b, strategy=Script(exit_at=at(2)))
    assert result.fills["g"][1].chart_exit == 100
    assert result.fills["g"][1].exit_reason is ExitReason.SIGNAL


@pytest.mark.parametrize("on_ask", [False, True])
def test_short_take_profit_uses_configured_ask_and_no_adverse_slippage(on_ask):
    order = intent(legs=(intent().legs[0], replace(intent().legs[1], take_profit_distance=2)))
    b = series("B", [(0, 100, 100, 100, 100), (1, 100, 100, 97, 98)])
    result = run(b=b, strategy=Script(order), cfg=costs(.2, .05, short_tp_on_ask=on_ask))
    fill = result.fills["g"][1]
    assert fill.exit_reason is ExitReason.TAKE_PROFIT
    assert fill.exit_fill == pytest.approx(98 if on_ask else 98.2)
    assert result.unresolved[0].open_legs[0].symbol == "A"


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_invalid_constant_valuation_rejects_all_legs(value):
    result = run(values={"A": 1, "B": value})
    assert result.rejected[0].reason.startswith("leg rejected: ")
    assert not result.fills and not result.unresolved


def test_explicit_values_and_tick_rounded_risk_are_frozen():
    cfg = costs(round_to_tick=True)
    cfg = replace(cfg, symbols={s: replace(c, tick_size=1) for s, c in cfg.symbols.items()})
    order = intent(legs=(GroupLeg("A", LONG, 1, 2.2), GroupLeg("B", SHORT, 1, 1.2)))
    result = run(strategy=Script(order, exit_at=at(3)), cfg=cfg, values=(2, 3))
    assert result.closed[0].D == 7  # rounded chart risks 2 and 1, values 2 and 3
    assert result.closed[0].weights == (4 / 7, 3 / 7)


def test_delayed_residual_accrues_actual_swap_and_funding_interval():
    from backtester.engine.costs import FundingSeries

    a = series("A", [(0, 100, 100, 100, 100), (1, 100, 100, 100, 100),
                     (2, 100, 100, 97, 99)])
    # B reopens next day: crosses Monday 22:00 UTC rollover and the funding timestamp.
    b = quiet("B", [0, 1, 1440])
    cfg = costs()
    cfg = replace(cfg, symbols={
        "A": cfg.symbols["A"],
        "B": replace(cfg.symbols["B"], swap_short_per_lot=-.3, funding=True),
    }, funding={"B": FundingSeries((at(720),), (.001,))})
    result = run(a=a, b=b, strategy=Script(), cfg=cfg)
    part = result.closed[0].attributions[1]
    assert part.swap_r == pytest.approx(-.3 / 3)
    assert part.funding_r == pytest.approx(.1 / 3)
    assert result.fills["g"][1].exit_time == at(1440)


def test_undeclared_reference_cannot_be_traded():
    strategy = Script(intent(legs=(intent().legs[0], GroupLeg("C", SHORT, 1, 1))))
    strategy.references = (ReferenceInput("C", "reference", (Timeframe.M1,), MINUTE),)
    result = run_group_backtest(strategy, {s: quiet(s) for s in ("A", "B", "C")}, costs())
    assert result.rejected[0].reason == "leg rejected: undeclared symbol"
    assert not result.fills
