"""Hand-computed group arithmetic. Spec: design/multi-symbol.md › B."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta

import pytest

from backtester.core.models import Direction
from backtester.engine.costs import CostConfig, FundingSeries, SymbolCosts
from backtester.engine.group_trade import LegFill, group_basis, group_result, leg_costs
from backtester.engine.trade import ExitReason
from backtester.strategy.group import EntryPolicy, ExitPolicy, GroupLeg, GroupOrder

ENTRY = datetime(2026, 11, 11, 21, tzinfo=UTC)  # Wednesday, before 22:00 rollover
EXIT = ENTRY + timedelta(hours=2)


def order():
    return GroupOrder(
        "pair", (GroupLeg("XAUUSD", Direction.BULLISH, 1, 2),
                 GroupLeg("XAGUSD", Direction.BEARISH, 1, 1)),
        ENTRY - timedelta(minutes=1), EntryPolicy.NEXT_OPEN_ALL_OR_NONE,
        ExitPolicy.ALL_LEGS_NEXT_OPEN_AFTER_STOP, 5, "test", frozenset(),
    )


def fill(exit_price, **kwargs):
    return replace(LegFill(100, exit_price, ENTRY, EXIT, ExitReason.SIGNAL,
                           1, 1, 100, exit_price), **kwargs)


def free():
    return CostConfig(spread_enabled=False, commission_enabled=False,
                      swap_enabled=False, funding_enabled=False)


def test_asymmetric_design_example_and_reconciliation():
    result = group_result(order(), (fill(102), fill(101)), free(), (1, 1))
    assert result.D == 3
    assert result.weights == (2 / 3, 1 / 3)
    assert sum(result.weights) == 1
    assert result.r_gross == result.r_net == 1 / 3
    assert tuple(part.gross_r for part in result.attributions) == (2 / 3, -1 / 3)
    assert result.reconcile()
    assert not result.residual
    assert result.exit_reasons == (ExitReason.SIGNAL, ExitReason.SIGNAL)
    with pytest.raises(FrozenInstanceError):
        result.r_net = 0
    assert not replace(result, r_net=result.r_net + 1e-6).reconcile()


def test_both_initial_stops_and_non_stop_exit():
    assert group_result(order(), (fill(98), fill(101)), free(), (1, 1)).r_gross == -1
    # Long loses its 2-unit stop; short exits flat: -2 / (2+1).
    result = group_result(order(), (fill(98), fill(100)), free(), (1, 1))
    assert result.r_gross == -2 / 3


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), 0, -1])
def test_invalid_entry_values(bad):
    with pytest.raises(ValueError, match="value"):
        group_basis(order().legs, (1, bad))


def test_bad_lengths_and_overflow():
    with pytest.raises(ValueError):
        group_basis(order().legs, (1,))
    with pytest.raises(ValueError):
        group_basis((), ())
    with pytest.raises(ValueError):
        group_basis(order().legs, (1e308, 1e308))
    with pytest.raises(ValueError):
        group_result(order(), (fill(100),), free(), (1, 1))


@pytest.mark.parametrize("field", ["entry_value", "exit_value"])
@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf")])
def test_fill_rejects_invalid_valuation(field, bad):
    with pytest.raises(ValueError, match=field):
        fill(100, **{field: bad})


def test_fill_rejects_bad_times_prices_and_entry_basis_mismatch():
    for changes in ({"entry_time": ENTRY.replace(tzinfo=None)},
                    {"exit_time": ENTRY - timedelta(seconds=1)},
                    {"exit_fill": float("nan")}, {"chart_entry": float("inf")}):
        with pytest.raises(ValueError):
            fill(100, **changes)
    with pytest.raises(ValueError, match="entry_value"):
        group_result(order(), (fill(100, entry_value=2), fill(100)), free(), (1, 1))


def test_conversion_values_the_price_pl_only_and_freezes_basis():
    # CFD legs: only the price P/L is a quote-currency cashflow, settled at exit.
    # Flat prices give 0 whatever the conversion does (no P/L on the notional).
    flat = group_result(order(), (fill(100, exit_value=1.1), fill(100, exit_value=.9)),
                        free(), (1, 1))
    assert flat.r_net == 0 and flat.r_gross == 0
    # Long +2 at 1.1 = 2.2; short 100 -> 101 = -1 at .9 = -.9; (2.2 - .9) / D 3.
    moved = group_result(order(), (fill(102, exit_value=1.1), fill(101, exit_value=.9)),
                         free(), (1, 1))
    original = group_result(order(), (fill(102), fill(101)), free(), (1, 1))
    assert moved.r_net == pytest.approx(1.3 / 3, abs=1e-12)
    assert moved.r_gross == moved.r_net
    assert (moved.D, moved.weights) == (original.D, original.weights)
    assert moved.reconcile()


def custom_costs(spread=5):
    return CostConfig(symbols={s: SymbolCosts(spread, 2, 10, swap_long_per_lot=-1,
                                             swap_short_per_lot=-1)
                               for s in ("XAUUSD", "XAGUSD")},
                      spread_table=None, swap_price_scaling=False)


def test_exact_costs_and_spread_is_diagnostic_only():
    cfg = custom_costs()
    costs = leg_costs(cfg, order().legs[0], fill(102))
    assert costs == {"commission": -.2, "swap": pytest.approx(-.3),
                     "funding": 0, "spread_diagnostic": -5}
    result = group_result(order(), (fill(102), fill(101)), cfg, (1, 1))
    assert result.r_gross == 1 / 3
    assert result.r_net == pytest.approx(0, abs=1e-12)  # (1 - 2*(.2+.3))/3
    assert result.attributions[0].commission_r == pytest.approx(-.2 / 3)
    assert result.attributions[0].swap_r == pytest.approx(-.3 / 3)
    changed = group_result(order(), (fill(102), fill(101)), custom_costs(50), (1, 1))
    assert changed.r_net == result.r_net
    assert changed.attributions[0].spread_diagnostic_r != result.attributions[0].spread_diagnostic_r


def test_actual_holding_interval_and_real_triple_swap_and_credit_default():
    cfg = CostConfig(spread_table=None, swap_price_scaling=False)
    leg = order().legs[0]
    assert leg_costs(cfg, leg, fill(100))["swap"] == pytest.approx(-3 * 61.27 / 100)
    early = fill(100, exit_time=ENTRY + timedelta(minutes=30))
    assert leg_costs(cfg, leg, early)["swap"] == 0
    later = fill(100, exit_time=EXIT + timedelta(days=1))
    assert leg_costs(cfg, leg, later)["swap"] == pytest.approx(-4 * 61.27 / 100)
    oil = GroupLeg("USOIL", Direction.BULLISH, 1, 1)
    assert leg_costs(cfg, oil, fill(100))["swap"] == 0
    assert leg_costs(replace(cfg, swap_credit=True), oil, fill(100))["swap"] > 0


def test_commission_sides_and_financing_settled_at_exit_conversion():
    # Long flat price (P/L 0), commission -.1*1 -.1*1.1, swap -.3*1.1.
    # Short unchanged prices/valuation, commission -.2, swap -.3.
    result = group_result(order(), (fill(100, exit_value=1.1), fill(100)),
                          custom_costs(), (1, 1))
    assert result.r_net == pytest.approx((0 - .21 - .33 - .2 - .3) / 3)


def test_funding_boundaries_signs_and_net_attribution():
    # Entry timestamp excluded; exit included; later funding excluded.
    series = FundingSeries((ENTRY, EXIT, EXIT + timedelta(hours=1)), (.5, .01, .5))
    cfg = CostConfig(symbols={s: SymbolCosts(0, 0, 1, funding=True)
                               for s in ("XAUUSD", "XAGUSD")},
                     funding={s: series for s in ("XAUUSD", "XAGUSD")},
                     swap_enabled=False, spread_table=None)
    assert leg_costs(cfg, order().legs[0], fill(100))["funding"] == -1
    assert leg_costs(cfg, order().legs[1], fill(100))["funding"] == 1
    result = group_result(order(), (fill(100), fill(100)), cfg, (1, 1))
    assert result.attributions[0].funding_r == -1 / 3
    assert result.attributions[1].funding_r == 1 / 3
    assert result.r_net == 0
    assert result.reconcile()


def test_relative_quantities_and_entry_values_are_not_unweighted_leg_rs():
    intent = replace(order(), legs=(replace(order().legs[0], quantity=2), order().legs[1]))
    result = group_result(intent, (fill(102, entry_value=3, exit_value=3), fill(101)),
                          free(), (3, 1))
    assert result.D == 13
    assert result.weights == (12 / 13, 1 / 13)
    assert result.r_gross == 11 / 13
