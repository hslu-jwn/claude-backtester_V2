"""Spec: risk-management.md > Costs, V2.4d item 3.

Test-case list (written before implementation):
- Long/short touch, insufficient penetration and exact threshold; d=0 legacy fills.
- Partial TP1, TP2 and TP3 each require penetration; BE waits for filled TP1.
- Gap beyond TP fills at its limit; SL-first and MAE/MFE stay unchanged.
- Ask-triggered short TP fills at TP without extra spread, independently of d.
- Count levels once even across repeated touches and later fills; CSV/summary round trip.
- Pending buy/sell limit survives a touch, then fills or expires; gap entry unchanged.
- Spread fixed/scaled/table, frozen at entry; disabled spread means zero distance.
- Settings leaves, panel and research grid round trip; invalid distances rejected.
- Golden comparison preserves every historic field and validates new diagnostics.
- Future candles cannot change a trade already closed by penetration.
"""

import json
from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

import pytest
from conftest import DEFAULT_START, build_series

from backtester.analytics.metrics import summarize
from backtester.analytics.records import TradeRecord
from backtester.core.models import Direction, Timeframe
from backtester.detectors.settings import DetectorSettings
from backtester.detectors.swings import SwingConfig
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.engine.spread_table import SpreadTable
from backtester.engine.trade import ExitReason
from backtester.runner import trade_rows
from backtester.settings import form_values, leaves, settings_from_values
from backtester.strategy.base import Order, Strategy
from backtester.strategy.no_wick.config import NoWickConfig, TrendSource
from backtester.strategy.no_wick.strategy import NoWick, Pending
from backtester.tools.golden import compare_trades, serialize_trade

ENTRY = (100, 100, 100, 100)


class Scripted(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)
    uses_session_break_even = False

    def __init__(self, order):
        self.order = order

    def on_candle(self, now, views):
        return [self.order] if views[self.base_timeframe].cursor == 0 else []


def costs(**kwargs):
    return CostConfig(symbols={"TEST": SymbolCosts(2, 0, 1)}, **kwargs)


def mirror(candles, sign):
    if sign > 0:
        return candles
    return [(200 - o, 200 - low, 200 - high, 200 - c) for o, high, low, c in candles]


def run(candles, sign=1, config=None, **order_kwargs):
    order = Order(
        Direction.BULLISH if sign > 0 else Direction.BEARISH,
        100,
        100 - sign * 10,
        100 + sign * 10,
        **order_kwargs,
    )
    return run_backtest(
        Scripted(order),
        [build_series(mirror([ENTRY, *candles], sign))],
        EngineConfig(costs=config or costs()),
    )[0]


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize(
    "penetration,extreme,filled",
    [(0, 110, True), (1, 110, False), (1, 111.99, False), (1, 112, True)],
)
def test_tp_threshold_and_legacy_defaults(sign, penetration, extreme, filled):
    t = run([(100, extreme, 99, 105)], sign, costs(tp_penetration=penetration))
    assert (t.exit_reason is ExitReason.TAKE_PROFIT) is filled
    assert t.tp_levels_touched == 1
    assert t.tp_levels_touched_not_filled == int(not filled)
    if filled:
        assert t.exit_price == 100 + sign * 10
        assert t.exit_fill == t.exit_price + (2 if sign < 0 else 0)


@pytest.mark.parametrize("sign", [1, -1])
def test_partial_targets_and_be_wait_for_penetration(sign):
    kwargs = {"take_profit_2": 100 + sign * 20, "tp1_share": 0.5, "break_even_after_tp1": True}
    first = run([(100, 110, 99, 105)], sign, costs(tp_penetration=1), **kwargs)
    assert first.break_even_time is None
    assert first.parts[0].reason is ExitReason.END_OF_DATA
    candles = [
        (100, 110, 99, 105),
        (105, 112, 103, 111),
        (111, 120, 105, 118),
        (118, 122, 105, 120),
    ]
    t = run(candles, sign, costs(tp_penetration=1), **kwargs)
    assert [p.price for p in t.parts] == [100 + sign * 10, 100 + sign * 20]
    assert t.break_even_time == DEFAULT_START + Timeframe.M5.duration * 3
    assert (t.tp_levels_touched, t.tp_levels_touched_not_filled) == (2, 2)
    assert t.parts[-1].time == DEFAULT_START + Timeframe.M5.duration * 5


@pytest.mark.parametrize("sign", [1, -1])
def test_three_targets_and_same_candle_break_even(sign):
    kwargs = {
        "take_profit_2": 100 + sign * 20,
        "take_profit_3": 100 + sign * 30,
        "tp1_share": 0.3,
        "tp2_share": 0.3,
    }
    t = run([(100, 132, 99, 131)], sign, costs(tp_penetration=1), **kwargs)
    assert len(t.parts) == 3 and all(p.reason is ExitReason.TAKE_PROFIT for p in t.parts)
    assert t.tp_levels_touched == 3 and t.tp_levels_touched_not_filled == 0
    t = run(
        [(100, 112, 99, 100)],
        sign,
        costs(tp_penetration=1),
        take_profit_2=100 + sign * 20,
        tp1_share=0.5,
        break_even_after_tp1=True,
    )
    assert [p.reason for p in t.parts] == [ExitReason.TAKE_PROFIT, ExitReason.BREAK_EVEN]


@pytest.mark.parametrize("sign", [1, -1])
def test_gap_limit_price_sl_first_and_unchanged_excursions(sign):
    gap = [(115, 120, 105, 116)]
    t = run(gap, sign, costs(tp_penetration=1))
    assert t.exit_price == 100 + sign * 10
    assert (t.mae_r, t.mfe_r) == (0, 1.5)
    assert run(gap + [(100, 1000, 1, 100)], sign, costs(tp_penetration=1)) == t
    t = run([(115, 120, 85, 100)], sign, costs(tp_penetration=1))
    assert t.exit_reason is ExitReason.STOP_LOSS
    old = run([(100, 110, 99, 105)], sign)
    new = run([(100, 110, 99, 105)], sign, costs(tp_penetration=1))
    assert (new.mae_r, new.mfe_r) == (old.mae_r, old.mfe_r)


@pytest.mark.parametrize(
    "penetration,low,filled", [(0, 90, False), (0, 88, True), (1, 87, False), (1, 86, True)]
)
def test_short_ask_threshold_and_fill_price(penetration, low, filled):
    t = run(
        [(100, 200 - low, 99, 105)], -1, costs(tp_penetration=penetration, short_tp_on_ask=True)
    )
    assert (t.exit_reason is ExitReason.TAKE_PROFIT) is filled
    if filled:
        assert t.exit_fill == t.exit_price == 90
    assert t.tp_levels_touched_not_filled == int(not filled)


def test_ask_switch_does_not_change_long_tp():
    assert run([(100, 110, 99, 105)]) == run(
        [(100, 110, 99, 105)], config=costs(short_tp_on_ask=True)
    )


def test_unique_counts_later_fill_csv_and_aggregate_share():
    t = run(
        [(100, 110, 99, 105), (105, 111, 99, 105), (105, 112, 99, 110)],
        config=costs(tp_penetration=1),
    )
    clean = run([(100, 112, 99, 110)], config=costs(tp_penetration=1))
    assert (t.tp_levels_touched, t.tp_levels_touched_not_filled) == (1, 1)
    result = SimpleNamespace(trades=[t, clean], runs={"TEST": SimpleNamespace(sessions=[])})
    records = [TradeRecord.from_row(row) for row in trade_rows(result)]
    assert records[0].tp_levels_touched_not_filled == 1
    for ts in ([t, clean], records):
        summary = summarize(ts)
        assert summary["tp_touched_not_filled_share"] == 0.5
    assert summarize([])["tp_touched_not_filled_share"] == 0
    row = trade_rows(result)[0]
    row.pop("tp_levels_touched")
    row.pop("tp_levels_touched_not_filled")
    assert TradeRecord.from_row(row).tp_levels_touched == 0


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("expiry,expected", [(1, 0), (3, 1)])
def test_real_no_wick_limit_waits_for_penetration_or_expires(sign, expiry, expected):
    trades = pending_run(
        [(105, 106, 100, 105), (105, 106, 98, 104)], sign, costs(tp_penetration=1), expiry
    )
    assert len(trades) == expected
    if trades:
        assert trades[0].entry_time == DEFAULT_START + Timeframe.M5.duration * 3
        assert trades[0].entry == 100


def pending_run(candles, sign, cfg, expiry=3):
    strategy = NoWick(
        "TEST",
        NoWickConfig(timeframe=Timeframe.M5, trend_source=TrendSource.SAME),
        DetectorSettings(swings=SwingConfig(doji_max_body={"TEST": 0})),
    )
    strategy._signal = lambda candle: None
    order = Order(
        Direction.BULLISH if sign > 0 else Direction.BEARISH,
        100,
        100 - sign * 10,
        100 + sign * 10,
        limit_fill=True,
    )
    # Install after candle 0, so the engine snapshots prior placement normally.
    original = strategy.on_candle

    def on_candle(now, views):
        orders = original(now, views)
        if views[Timeframe.M5].cursor == 0:
            strategy._pending.append(Pending(order, expiry))
        return orders

    strategy.on_candle = on_candle
    series = build_series(mirror([ENTRY, *candles], sign))
    return run_backtest(strategy, [series], EngineConfig(costs=cfg))


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("penetration,filled", [(0, True), (0.5, True), (1, False)])
def test_limit_entry_threshold_and_zero_matches_legacy(sign, penetration, filled):
    trades = pending_run([(105, 106, 99, 104)], sign, costs(tp_penetration=penetration))
    assert bool(trades) is filled  # spread 2: low 99 exactly penetrates by .5 spread


@pytest.mark.parametrize("sign", [1, -1])
def test_limit_gap_uses_placed_level_and_preserves_gap_entry_price(sign):
    trades = pending_run([(97, 98, 96, 97)], sign, costs(tp_penetration=1))
    assert len(trades) == 1
    assert trades[0].entry == 100 - sign * 3
    # Entire candle below/above original entry, but insufficient penetration of 2 points.
    assert not pending_run([(99, 99.5, 98.5, 99)], sign, costs(tp_penetration=1))


@pytest.mark.parametrize("sign", [1, -1])
def test_limit_uses_scaled_or_table_spread(sign):
    scaled = replace(
        costs(tp_penetration=1), symbols={"TEST": SymbolCosts(2, 0, 1, reference_price=200)}
    )
    assert pending_run([(105, 106, 99, 104)], sign, scaled)
    table = replace(
        scaled, spread_table=SpreadTable(values={"TEST": {2026: {h: 3 for h in range(24)}}})
    )
    assert not pending_run([(105, 106, 99, 104)], sign, table)
    assert pending_run([(105, 106, 97, 104)], sign, table)


@pytest.mark.parametrize("sign", [1, -1])
def test_tp_spread_is_frozen_at_entry_when_table_changes_hour(sign):
    cfg = costs(
        tp_penetration=1, spread_table=SpreadTable(values={"TEST": {2026: {19: 2, 20: 20}}})
    )
    order = Order(
        Direction.BULLISH if sign > 0 else Direction.BEARISH, 100, 100 - sign * 10, 100 + sign * 10
    )
    series = build_series(
        mirror([ENTRY, (100, 112, 99, 110)], sign), start=DEFAULT_START + timedelta(minutes=50)
    )
    t = run_backtest(Scripted(order), [series], EngineConfig(costs=cfg))[0]
    assert t.spread_r == 0.2 and t.exit_reason is ExitReason.TAKE_PROFIT


@pytest.mark.parametrize(
    "mode,spread,threshold",
    [("fixed", 2, 112), ("scaled", 1, 111), ("table", 3, 113), ("off", 0, 110)],
)
def test_penetration_uses_actual_entry_spread(mode, spread, threshold):
    cfg = costs(tp_penetration=1)
    if mode == "scaled":
        cfg = replace(cfg, symbols={"TEST": SymbolCosts(2, 0, 1, reference_price=200)})
    elif mode == "table":
        cfg = replace(
            cfg,
            spread_table=SpreadTable(
                values={"TEST": {DEFAULT_START.year: {h: 3 for h in range(24)}}}
            ),
        )
    elif mode == "off":
        cfg = replace(cfg, spread_enabled=False)
    t = run([(100, threshold, 99, 105)], config=cfg)
    assert t.spread_r == spread / 10
    assert t.exit_reason is ExitReason.TAKE_PROFIT
    if spread:
        t = run([(100, threshold - 0.01, 99, 105)], config=cfg)
        assert t.exit_reason is ExitReason.END_OF_DATA


@pytest.mark.parametrize("bad", [-1, float("nan"), float("inf"), -float("inf")])
def test_invalid_penetration_is_rejected(bad):
    with pytest.raises(ValueError, match="tp_penetration"):
        costs(tp_penetration=bad)


def test_settings_leaves_and_values():
    found = {leaf.path: leaf for leaf in leaves()}
    assert found["engine.costs.tp_penetration"].default == 0
    assert found["engine.costs.short_tp_on_ask"].default is False
    values = form_values()
    values.update({"engine.costs.tp_penetration": 0.5, "engine.costs.short_tp_on_ask": True})
    cfg = settings_from_values(values).engine.costs
    assert cfg.tp_penetration == 0.5 and cfg.short_tp_on_ask


def test_panel_and_research_grid_expose_both_settings(tmp_path):
    from backtester.tools.research_grid import expand, load_grid, variant_settings
    from backtester.ui.settings_panel import group_of, label_of

    path = tmp_path / "penetration.toml"
    path.write_text(
        'strategy = "no_wick"\nsymbols = ["XAUUSD"]\n'
        '[grid]\n"engine.costs.tp_penetration" = [0.0, 0.5]\n'
        '"engine.costs.short_tp_on_ask" = [false, true]\n'
    )
    spec = load_grid(path)
    variants, size, sampled = expand(spec)
    assert size == 4 and not sampled
    assert {
        (
            variant_settings(spec, v).engine.costs.tp_penetration,
            variant_settings(spec, v).engine.costs.short_tp_on_ask,
        )
        for v in variants
    } == {(0, False), (0, True), (0.5, False), (0.5, True)}
    for setting in ("tp_penetration", "short_tp_on_ask"):
        key = f"engine.costs.{setting}"
        assert group_of(key) == "Costs"
        assert "TP" in label_of(key)


def test_golden_legacy_diagnostics_do_not_hide_historic_changes():
    t = run([(100, 110, 99, 105)])
    new = json.loads(serialize_trade(t))
    old = {k: v for k, v in new.items() if not k.startswith("tp_levels_")}
    assert compare_trades([old], [new]) is None
    assert compare_trades([old], [{**new, "r_net": 123}]) is not None
    assert compare_trades([old], [{**new, "tp_levels_touched_not_filled": 1}]) is not None
    assert compare_trades([new], [{**new, "tp_levels_touched": 3}]) is not None
