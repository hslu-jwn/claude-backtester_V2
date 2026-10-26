"""Spec: risk-management.md > Costs > Tick rounding (V2.4d item 9).

Test-case list, before implementation:
- Long/short SL and all three TPs round toward entry; R uses rounded risk.
- Buy limit down/sell limit up; raw touch stays pending, exact rounded touch fills.
- Market fills, gap opens, M1 replay fills and penetration thresholds stay observed.
- BE long up/short down, including costs, hit >= 0 net; BE behind TP1 guard remains.
- On-tick and within 1e-9 unchanged; None tick no change; off byte-identical trades.
- Rounding SL/TP to/across entry rejects, counts, calls on_order_skipped; TP collapse.
- Invalid original orders still raise; invalid/zero/NaN/infinite tick rejected.
- Moved orders counted once, mean over moved levels; rejects included, warm-up excluded.
- Literal defaults match recorded fallback; panel, settings and grid round trip.
- Runner summary/notes preserve counts; measurement covers seven setups, two variants.
- Future candles cannot change a closed trade; SL-first remains conservative.
"""

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest
from conftest import DEFAULT_START, build_series

from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import Backtest, EngineConfig
from backtester.engine.costs import DEFAULT_SYMBOL_COSTS, CostConfig, SymbolCosts
from backtester.engine.trade import ExitReason
from backtester.settings import form_values, leaves, settings_from_values
from backtester.strategy.base import Order, Strategy
from backtester.tools.golden import serialize_trade


def direction(sign):
    return Direction.BULLISH if sign > 0 else Direction.BEARISH


def mirror(rows, sign):
    return (
        rows
        if sign > 0
        else [(200 - o, 200 - low, 200 - high, 200 - c) for o, high, low, c in rows]
    )


class Scripted(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)
    uses_session_break_even = False

    def __init__(self, order):
        self.order = order
        self.skipped = []
        self.pending = []

    def on_candle(self, now, views):
        candle = views[self.base_timeframe].current
        cursor = views[self.base_timeframe].cursor
        if not self.order.limit_fill:
            return [self.order] if cursor == 0 else []
        if cursor == 0:
            self.pending = [self.order]
        elif self.pending and self.limit_fill_check(self.order, candle, now):
            self.pending = []
            entry = self.order.entry
            if not candle.low <= entry <= candle.high:
                entry = candle.open
            return [replace(self.order, entry=entry)]
        return []

    def pending_limit_orders(self):
        return self.pending

    def on_order_skipped(self, ref, now):
        self.skipped.append(ref)


def setup(order=None, rows=None, *, sign=1, tick=1.0, enabled=True, symbol_costs=None, **kwargs):
    order = order or Order(direction(sign), 100, 100 - sign * 9.6, 100 + sign * 10.6)
    rows = rows or [(100, 100, 100, 100), (100, 112, 99, 110)]
    costs = CostConfig(
        symbols={"TEST": symbol_costs or SymbolCosts(0, 0, 1, tick_size=tick)},
        round_to_tick=enabled,
        tp_penetration=0,
    )
    strategy = Scripted(order)
    engine = Backtest(
        strategy, [build_series(mirror(rows, sign))], EngineConfig(costs=costs), **kwargs
    )
    return engine, strategy


@pytest.mark.parametrize("sign", [1, -1])
def test_round_sl_three_targets_and_r(sign):
    order = Order(
        direction(sign),
        100,
        100 - sign * 9.6,
        100 + sign * 10.6,
        take_profit_2=100 + sign * 20.6,
        take_profit_3=100 + sign * 30.6,
        tp1_share=0.3,
        tp2_share=0.3,
    )
    engine, _ = setup(order, [(100, 100, 100, 100), (100, 135, 99, 130)], sign=sign)
    [trade] = engine.run()
    assert trade.initial_stop == 100 - sign * 9
    assert [p.price for p in trade.parts] == [100 + sign * n for n in (10, 20, 30)]
    assert trade.risk == 9
    assert trade.r_net == pytest.approx((0.3 * 10 + 0.3 * 20 + 0.4 * 30) / 9)
    assert engine.tick_rounding.orders_moved == 1
    assert engine.tick_rounding.levels_moved == 4
    assert engine.tick_rounding.mean_move_ticks == pytest.approx(0.6)


@pytest.mark.parametrize("sign", [1, -1])
def test_limit_waits_for_rounded_level_and_fills_once(sign):
    order = Order(
        direction(sign), 100 + sign * 0.6, 100 - sign * 9.6, 100 + sign * 10.6, limit_fill=True
    )
    rows = [(105, 105, 105, 105), (105, 106, 100.5, 104), (104, 105, 100, 104)]
    engine, _ = setup(order, rows, sign=sign)
    [trade] = engine.run()
    assert trade.entry == 100
    assert trade.entry_candle == DEFAULT_START + Timeframe.M5.duration * 2
    assert engine.tick_rounding.orders_moved == 1
    assert engine.tick_rounding.levels_moved == 3


@pytest.mark.parametrize("sign", [1, -1])
def test_gap_open_is_not_rounded(sign):
    order = Order(
        direction(sign),
        100 + sign * 0.6,
        90 if sign > 0 else 110,
        110 if sign > 0 else 90,
        limit_fill=True,
    )
    engine, _ = setup(order, [(105, 105, 105, 105), (97.3, 98, 96, 97)], sign=sign)
    [trade] = engine.run()
    assert trade.entry == pytest.approx(100 + sign * (97.3 - 100))


@pytest.mark.parametrize("sign", [1, -1])
def test_original_gap_open_kept_even_when_rounded_limit_inside_candle(sign):
    order = Order(
        direction(sign), 100 + sign * 0.6, 100 - sign * 10, 100 + sign * 10, limit_fill=True
    )
    engine, _ = setup(order, [(105, 105, 105, 105), (99.7, 100.4, 99, 100)], sign=sign)
    [trade] = engine.run()
    assert trade.entry == pytest.approx(100 + sign * (99.7 - 100))


@pytest.mark.parametrize("sign", [1, -1])
def test_market_fill_and_stop_gap_remain_observed(sign):
    order = Order(direction(sign), 100 + sign * 0.3, 100 - sign * 9.6, 100 + sign * 10.6)
    engine, _ = setup(order, [(100.3, 100.3, 100.3, 100.3), (85.3, 86, 84, 85)], sign=sign)
    [trade] = engine.run()
    assert trade.entry == trade.entry_fill == pytest.approx(100 + sign * 0.3)
    assert trade.exit_price == pytest.approx(100 + sign * (85.3 - 100))
    assert trade.exit_reason is ExitReason.STOP_LOSS


@pytest.mark.parametrize("sign", [1, -1])
def test_break_even_rounding_covers_costs(sign):
    order = Order(
        direction(sign),
        100,
        100 - sign * 9.6,
        100 + sign * 10.6,
        take_profit_2=100 + sign * 20.6,
        tp1_share=0.5,
        break_even_after_tp1=True,
    )
    costs = SymbolCosts(0.2, 0.1, 1, slippage=0.1, tick_size=1)
    rows = [(100, 100, 100, 100), (100, 111, 99, 110), (105, 106, 100, 103)]
    engine, _ = setup(order, rows, sign=sign, symbol_costs=costs)
    [trade] = engine.run()
    assert trade.break_even_stop == 100 + sign
    assert trade.parts[-1].reason is ExitReason.BREAK_EVEN
    assert trade.parts[-1].r_fills - trade.commission_r >= 0


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("level", ["stop_loss", "take_profit"])
def test_rounding_rejection_notifies_and_counts(sign, level):
    order = Order(direction(sign), 100, 100 - sign * 9.6, 100 + sign * 10.6, ref="ref")
    order = replace(order, **{level: 100 + (-sign if level == "stop_loss" else sign) * 0.4})
    engine, strategy = setup(order, sign=sign)
    assert engine.run() == []
    assert strategy.skipped == ["ref"]
    assert engine.tick_rounding.rejected == 1
    assert engine.tick_rounding.orders_moved == 1
    assert engine.tick_rounding.notes()


def test_tp_collapse_uses_existing_validator_and_skip_path():
    order = Order(Direction.BULLISH, 100, 90, 110.2, take_profit_2=110.8, tp1_share=0.5)
    engine, strategy = setup(order)
    assert engine.run() == [] and strategy.skipped == [None]
    assert engine.tick_rounding.rejected == 1


def test_original_invalid_order_still_raises():
    engine, _ = setup(Order(Direction.BULLISH, 100, 101, 110))
    with pytest.raises(ValueError, match="SL"):
        engine.run()


@pytest.mark.parametrize("tick", [0, -1, float("nan"), float("inf")])
def test_invalid_tick_rejected(tick):
    with pytest.raises(ValueError, match="tick_size"):
        SymbolCosts(0, 0, 1, tick_size=tick)


@pytest.mark.parametrize("noise", [0, 5e-10, -5e-10])
def test_on_tick_float_noise_unchanged(noise):
    engine, _ = setup(Order(Direction.BULLISH, 100, 90 + noise, 110 + noise))
    [trade] = engine.run()
    assert trade.initial_stop == 90 + noise and trade.take_profit == 110 + noise
    assert engine.tick_rounding.orders_moved == 0


def test_off_and_none_are_exact_legacy_trades():
    off, _ = setup(enabled=False)
    missing, _ = setup(tick=None)
    assert [serialize_trade(t) for t in off.run()] == [serialize_trade(t) for t in missing.run()]
    assert off.tick_rounding.orders_moved == missing.tick_rounding.orders_moved == 0
    assert CostConfig().round_to_tick is False


def test_warmup_attempts_excluded():
    engine, _ = setup(diagnostics_start=DEFAULT_START + Timeframe.M5.duration)
    assert engine.run()
    assert engine.tick_rounding.orders_moved == 0


def test_future_candles_and_sl_first():
    rows = [(100, 100, 100, 100), (100, 112, 89, 105)]
    a, _ = setup(rows=rows)
    b, _ = setup(rows=rows + [(100, 1000, 1, 100)])
    assert a.run() == b.run()
    assert a.tick_rounding.orders_moved == 1


def test_default_table_and_settings_grid_panel(tmp_path):
    from backtester.data.sources import BINANCE_SYMBOLS, PRICE_DIGITS
    from backtester.tools.research_grid import expand, load_grid, variant_settings
    from backtester.ui.settings_panel import group_of, label_of

    for symbol, costs in DEFAULT_SYMBOL_COSTS.items():
        assert costs.tick_size == (
            None if symbol in BINANCE_SYMBOLS else 10 ** -PRICE_DIGITS[symbol]
        )
    key = "engine.costs.round_to_tick"
    assert {v.path: v for v in leaves()}[key].default is False
    values = form_values()
    values[key] = True
    assert settings_from_values(values).engine.costs.round_to_tick
    assert group_of(key) == "Costs" and "tick" in label_of(key)
    path = tmp_path / "ticks.toml"
    path.write_text(
        'strategy = "no_wick"\nsymbols = ["XAUUSD"]\n[grid]\n'
        '"engine.costs.round_to_tick" = [false, true]\n'
    )
    spec = load_grid(path)
    variants, size, _ = expand(spec)
    assert size == 2
    assert [variant_settings(spec, v).engine.costs.round_to_tick for v in variants] == [False, True]


def test_runner_diagnostics_and_measurement(tmp_path, monkeypatch):
    from backtester.engine.ticks import TickRoundingStats
    from backtester.runner import RunResult, RunSettings, SymbolRun
    from backtester.tools.golden import GoldenConfig
    from scripts import measure_ticks

    stats = TickRoundingStats(orders_moved=2, levels_moved=4, total_move_ticks=2, rejected=1)
    run = SymbolRun(
        "TEST",
        DEFAULT_START.date(),
        DEFAULT_START.date(),
        DEFAULT_START.date(),
        (),
        (),
        tick_rounding=stats,
    )
    result = RunResult(
        ("TEST",), run.first_day, run.last_day, RunSettings(), None, {"TEST": run}, ()
    )
    assert result.summary()["combined"]["tick_rounding"]["orders_moved"] == 2
    assert result.summary()["per_symbol"]["TEST"]["tick_rounding"]["mean_move_ticks"] == 0.5
    calls = []

    def fake_run(symbols, start, end, settings, sources, workers):
        assert workers == 1
        calls.append(settings.engine.costs.round_to_tick)
        return SimpleNamespace(trades=(), notes=(), runs={"TEST": run}, summary=result.summary)

    monkeypatch.setattr(measure_ticks, "run_backtests", fake_run)
    output = tmp_path / "ticks"
    assert measure_ticks.main(["--output", str(output)]) == 0
    assert calls == [False, True] * len(GoldenConfig().strategies)
    import csv

    with output.with_suffix(".csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 14 and all(float(r["delta_net_r"]) == 0 for r in rows)
    assert "Default remains False" in output.with_suffix(".md").read_text()
    assert json.loads(json.dumps(result.summary()))["combined"]["tick_rounding"]["rejected"] == 1


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("level", ["stop_loss", "take_profit"])
def test_rounding_crosses_observed_entry(sign, level):
    order = Order(direction(sign), 100 + sign * 0.3, 100 - sign * 9, 100 + sign * 10, ref="cross")
    order = replace(order, **{level: 100 + sign * (0.1 if level == "stop_loss" else 0.4)})
    engine, strategy = setup(order, [(100.3, 100.3, 100.3, 100.3)], sign=sign)
    assert engine.run() == [] and strategy.skipped == ["cross"]
    assert engine.tick_rounding.rejected == 1


@pytest.mark.parametrize("sign", [1, -1])
def test_limit_entry_rounding_onto_stop_rejects(sign):
    order = Order(direction(sign), 100 + sign * 0.6, 100, 100 + sign * 10, limit_fill=True)
    engine, strategy = setup(order, [(105, 105, 105, 105), (104, 105, 100, 104)], sign=sign)
    assert engine.run() == [] and strategy.skipped == [None]
    assert engine.tick_rounding.rejected == 1


@pytest.mark.parametrize("sign", [1, -1])
def test_penetration_distance_is_not_rounded(sign):
    order = Order(direction(sign), 100, 100 - sign * 9.6, 100 + sign * 10.6)
    engine, _ = setup(order, [(100, 100, 100, 100), (100, 110.2, 99, 105)], sign=sign)
    engine._config = replace(
        engine._config,
        costs=replace(
            engine._config.costs,
            tp_penetration=0.5,
            short_tp_on_ask=False,
            symbols={"TEST": SymbolCosts(0.6, 0, 1, tick_size=1)},
        ),
    )
    [trade] = engine.run()
    assert trade.exit_reason is ExitReason.END_OF_DATA  # 110 + 0.3, not 110
    assert trade.take_profit == 100 + sign * 10


@pytest.mark.parametrize("sign", [1, -1])
def test_rounded_be_not_behind_tp1_keeps_original_stop(sign):
    order = Order(
        direction(sign),
        100,
        100 - sign * 9.6,
        100 + sign * 1.6,
        take_profit_2=100 + sign * 20,
        tp1_share=0.5,
        break_even_after_tp1=True,
    )
    engine, _ = setup(
        order,
        [(100, 100, 100, 100), (100, 102, 99, 102)],
        sign=sign,
        symbol_costs=SymbolCosts(0.6, 0, 1, tick_size=1),
    )
    [trade] = engine.run()
    assert trade.break_even_time is None  # rounded BE and TP1 both 101 / 99


@pytest.mark.parametrize("sign", [1, -1])
def test_m1_replay_uses_rounded_tp(sign):
    from conftest import build_candles

    start = DEFAULT_START + Timeframe.M5.duration
    minutes = [(100, 111, 99, 110), (85.3, 86, 84, 85)] + [(85, 85, 85, 85)] * 3
    order = Order(direction(sign), 100, 100 - sign * 9.6, 100 + sign * 10.6)
    engine, _ = setup(
        order,
        [(100, 100, 100, 100), (100, 111, 84, 85)],
        sign=sign,
        intrabar_source=lambda *args: build_candles(mirror(minutes, sign), Timeframe.M1, start),
    )
    [trade] = engine.run()
    assert trade.exit_reason is ExitReason.TAKE_PROFIT  # rounded TP first in M1
    assert trade.exit_price == 100 + sign * 10
    assert trade.exit_time == start + Timeframe.M1.duration


@pytest.mark.parametrize("sign", [1, -1])
def test_m1_stop_gap_fill_keeps_observed_price(sign):
    from conftest import build_candles

    start = DEFAULT_START + Timeframe.M5.duration
    minutes = [(85.3, 86, 84, 85), (85, 112, 85, 110)] + [(110, 110, 110, 110)] * 3
    order = Order(direction(sign), 100, 100 - sign * 9.6, 100 + sign * 10.6)
    engine, _ = setup(
        order,
        [(100, 100, 100, 100), (85.3, 112, 84, 110)],
        sign=sign,
        intrabar_source=lambda *args: build_candles(mirror(minutes, sign), Timeframe.M1, start),
    )
    [trade] = engine.run()
    assert trade.exit_reason is ExitReason.STOP_LOSS
    assert trade.initial_stop == 100 - sign * 9
    assert trade.exit_price == pytest.approx(100 + sign * (85.3 - 100))
    assert trade.exit_time == start + Timeframe.M1.duration


@pytest.mark.parametrize("sign", [1, -1])
def test_m1_limit_replay_waits_for_rounded_level(sign):
    from conftest import build_candles

    start = DEFAULT_START + Timeframe.M5.duration
    minutes = [(105, 106, 100.5, 104), (104, 105, 100, 104), (104, 112, 103, 110)]
    minutes += [(110, 110, 110, 110)] * 2
    order = Order(
        direction(sign), 100 + sign * 0.6, 100 - sign * 9.6, 100 + sign * 10.6, limit_fill=True
    )
    engine, _ = setup(
        order,
        [(105, 105, 105, 105), (105, 112, 100, 110)],
        sign=sign,
        intrabar_source=lambda *args: build_candles(mirror(minutes, sign), Timeframe.M1, start),
    )
    [trade] = engine.run()
    assert trade.entry == 100
    assert trade.entry_time == start + Timeframe.M1.duration * 2
    assert trade.exit_time == start + Timeframe.M1.duration * 3
    assert trade.exit_reason is ExitReason.TAKE_PROFIT


def test_runner_counts_rejections_and_excludes_warmup(monkeypatch):
    from datetime import timedelta

    from backtester import runner

    class EveryBar(Scripted):
        def on_candle(self, now, views):
            return [self.order]

    order = Order(Direction.BULLISH, 100, 99.6, 110, ref="reject")
    strategy = EveryBar(order)
    monkeypatch.setattr(runner, "make_strategy", lambda *args: strategy)
    day = DEFAULT_START.date() + timedelta(days=1)
    costs = CostConfig(symbols={"TEST": SymbolCosts(0, 0, 1, tick_size=1)}, round_to_tick=True)
    series = build_series(
        [(100, 100, 100, 100)] * 2, start=DEFAULT_START.replace(hour=23, minute=55)
    )
    job = runner._Job(
        "TEST",
        day,
        day,
        DEFAULT_START.date(),
        (series,),
        runner.RunSettings(engine=EngineConfig(costs=costs, intrabar="sl_first")),
        (),
    )
    run = runner._run_job(job)
    assert len(strategy.skipped) == 2 and run.tick_rounding.rejected == 1
    assert len(run.notes) == 1 and "tick rounding rejected 1" in run.notes[0]


def test_research_segments_preserve_diagnostics():
    from backtester.engine.ticks import TickRoundingStats
    from backtester.runner import SymbolRun
    from backtester.tools.research import _join

    run = SymbolRun(
        "TEST",
        DEFAULT_START.date(),
        DEFAULT_START.date(),
        DEFAULT_START.date(),
        (),
        (),
        tick_rounding=TickRoundingStats(2, 4, 2, 1),
    )
    joined = _join("TEST", [run, run])
    assert joined.tick_rounding.orders_moved == 4
    assert joined.tick_rounding.rejected == 2
    assert joined.tick_rounding.mean_move_ticks == 0.5


def test_panel_exposes_switch_without_tick_metadata_widgets():
    from backtester.ui.settings_panel import panel_fields

    paths = [leaf.path for _, leaf, _ in panel_fields()]
    assert "engine.costs.round_to_tick" in paths
    assert not any(p.endswith(".tick_size") for p in paths)
    assert len(paths) < 250
    values = form_values()
    key = "engine.costs.symbols.XAUUSD.tick_size"
    assert key in values
    values[key] = 0.01
    assert settings_from_values(values).engine.costs.for_symbol("XAUUSD").tick_size == 0.01
