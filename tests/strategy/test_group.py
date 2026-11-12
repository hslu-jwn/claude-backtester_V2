"""Group contracts. Spec: design/multi-symbol.md › B."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from backtester.core.models import Direction
from backtester.strategy.group import EntryPolicy, ExitPolicy, GroupLeg, GroupOrder

NOW = datetime(2026, 11, 11, 20, tzinfo=UTC)


def order():
    return GroupOrder(
        group_id="pair-1",
        legs=(GroupLeg("XAUUSD", Direction.BULLISH, 1, 2),
              GroupLeg("XAGUSD", Direction.BEARISH, 1, 1)),
        intent_time=NOW,
        entry_policy=EntryPolicy.NEXT_OPEN_ALL_OR_NONE,
        exit_policy=ExitPolicy.ALL_LEGS_NEXT_OPEN_AFTER_STOP,
        expiry_minutes=5,
        reason="pair",
        tags=frozenset({"test"}),
    )


def test_order_is_ordered_and_frozen_with_only_declared_policies():
    intent = order()
    assert tuple(leg.symbol for leg in intent.legs) == ("XAUUSD", "XAGUSD")
    assert len(EntryPolicy) == len(ExitPolicy) == 1
    with pytest.raises(FrozenInstanceError):
        intent.group_id = "changed"
    with pytest.raises(FrozenInstanceError):
        intent.legs[0].quantity = 2


@pytest.mark.parametrize("name", ["quantity", "stop_distance", "take_profit_distance"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), 0, -1])
def test_leg_rejects_invalid_distances_and_quantity(name, bad):
    with pytest.raises(ValueError, match=name):
        replace(order().legs[0], **{name: bad})


def test_group_rejects_missing_or_duplicate_legs_and_non_tuple():
    intent = order()
    for legs in ((intent.legs[0],), (), (intent.legs[0], intent.legs[0]), list(intent.legs)):
        with pytest.raises(ValueError, match="legs|symbols|tuple"):
            replace(intent, legs=legs)


@pytest.mark.parametrize("at", [NOW.replace(tzinfo=None),
                               NOW.astimezone(timezone(timedelta(hours=1)))])
def test_intent_requires_utc(at):
    with pytest.raises(ValueError, match="UTC"):
        replace(order(), intent_time=at)


@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf")])
def test_expiry_is_finite_positive(bad):
    with pytest.raises(ValueError, match="expiry_minutes"):
        replace(order(), expiry_minutes=bad)


def test_importing_group_modules_preserves_legacy_fields():
    from backtester.engine import group_trade  # noqa: F401
    from backtester.engine.trade import TradeResult
    from backtester.strategy.base import Order

    assert tuple(f.name for f in fields(Order)) == (
        "direction", "entry", "stop_loss", "take_profit", "tags", "reason", "confluence",
        "take_profit_2", "tp1_share", "break_even_after_tp1", "take_profit_3", "tp2_share",
        "ref", "limit_fill",
    )
    assert tuple(f.name for f in fields(TradeResult)) == (
        "symbol", "direction", "entry_time", "entry_candle", "entry", "entry_fill",
        "initial_stop", "take_profit", "exit_time", "exit_candle", "exit_price", "exit_fill",
        "exit_reason", "r_gross", "r_net", "spread_r", "commission_r", "break_even_time",
        "break_even_stop", "mae_r", "mfe_r", "tags", "reason", "confluence", "take_profit_2",
        "tp1_share", "parts", "take_profit_3", "tp2_share", "swap_r", "funding_r",
        "conversion_r", "risk_weight", "limit_fill", "tp_levels_touched",
        "tp_levels_touched_not_filled", "intrabar", "intrabar_ambiguous", "intrabar_tp_first",
        "intrabar_sl_first", "intrabar_fallbacks",
    )


def test_group_strategy_requires_callback_and_has_optional_noops():
    from backtester.strategy.group import GroupStrategy

    with pytest.raises(TypeError, match="abstract"):
        GroupStrategy()

    class Minimal(GroupStrategy):
        legs = ("A", "B")

        def on_group_candle(self, now, market):
            return []

    strategy = Minimal()
    assert strategy.references == ()
    assert strategy.group_exits(NOW, None, ()) == []
    assert strategy.on_group_closed(None) is None
