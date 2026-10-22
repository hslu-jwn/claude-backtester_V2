"""Spread by year and hour of day in the cost model. Spec: ROADMAP.md › 6.7,
risk-management.md › Costs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from conftest import DEFAULT_START, build_series

from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.engine.spread_table import SpreadTable
from backtester.strategy.base import Order, Strategy

NY = ZoneInfo("America/New_York")
# summer: 13:30 UTC = 09:30 EDT (hour 9); winter: 14:30 UTC = 09:30 EST (hour 9)
SUMMER_0930 = datetime(2026, 7, 1, 13, 30, tzinfo=UTC)
WINTER_0930 = datetime(2026, 1, 14, 14, 30, tzinfo=UTC)


def table(**kw):
    values = {
        "XAUUSD": {
            2024: {9: 0.30, 10: 0.28},
            2026: {9: 0.45, 10: 0.40, 17: 1.20},
        },
        "US500": {2026: {9: 0.6}},
    }
    return SpreadTable(values=values, **kw)


# --- the table ---------------------------------------------------------------------------------


def test_lookup_uses_the_new_york_hour_and_follows_dst():
    t = table()
    assert t.spread_at("XAUUSD", SUMMER_0930) == pytest.approx(0.45)
    assert t.spread_at("XAUUSD", WINTER_0930) == pytest.approx(0.45)
    # 13:59 UTC in summer is still hour 9, 14:00 UTC is hour 10
    assert t.spread_at("XAUUSD", datetime(2026, 7, 1, 14, 0, tzinfo=UTC)) == pytest.approx(0.40)


def test_year_comes_from_the_new_york_date():
    t = SpreadTable(values={"XAUUSD": {2025: {23: 0.9}, 2026: {23: 0.1}}})
    # 2026-01-01 04:30 UTC is 2025-12-31 23:30 in New York: still 2025
    ts = datetime(2026, 1, 1, 4, 30, tzinfo=UTC)
    assert ts.astimezone(NY).year == 2025
    assert t.spread_at("XAUUSD", ts) == pytest.approx(0.9)


def test_a_tie_between_two_years_takes_the_later_one():
    t = table()  # 2024 and 2026
    assert t.spread_at("XAUUSD", datetime(2025, 7, 1, 13, 30, tzinfo=UTC)) == pytest.approx(0.45)


def test_a_year_outside_the_table_takes_the_nearest_year_with_that_hour():
    t = table()
    assert t.spread_at("XAUUSD", datetime(2030, 7, 1, 13, 30, tzinfo=UTC)) == pytest.approx(0.45)
    assert t.spread_at("XAUUSD", datetime(2020, 7, 1, 13, 30, tzinfo=UTC)) == pytest.approx(0.30)


def test_a_missing_hour_falls_back_to_another_year_then_to_none():
    t = table()
    # hour 17 exists only in 2026: asked for 2024 it is found there
    assert t.spread_at("XAUUSD", datetime(2024, 7, 1, 21, 0, tzinfo=UTC)) == pytest.approx(1.20)
    # hour 3 exists in no year
    assert t.spread_at("XAUUSD", datetime(2026, 7, 1, 7, 0, tzinfo=UTC)) is None


def test_unknown_symbol_is_none():
    assert table().spread_at("GBPUSD", SUMMER_0930) is None


def test_naive_time_is_rejected():
    with pytest.raises(ValueError):
        table().spread_at("XAUUSD", datetime(2026, 7, 1, 13, 30))


def test_json_round_trip_keeps_the_values():
    t = table(stat="p90", note="FTMO demo, M1 2020-2026")
    back = SpreadTable.from_dict(json.loads(json.dumps(t.to_dict())))
    assert back == t
    assert back.spread_at("US500", SUMMER_0930) == pytest.approx(0.6)


def test_from_dict_rejects_bad_content():
    with pytest.raises(ValueError):
        SpreadTable.from_dict({"values": {"XAUUSD": {"2026": {"25": 0.3}}}})  # hour 25
    with pytest.raises(ValueError):
        SpreadTable.from_dict({"values": {"XAUUSD": {"2026": {"9": -0.1}}}})  # negative


# --- in the cost model --------------------------------------------------------------------------------


def costs(**kw):
    sym = SymbolCosts(spread=0.25, commission_per_lot=0.0, contract_size=100)
    return CostConfig(symbols={"XAUUSD": sym, "US500": sym}, **kw)


def test_without_a_table_the_fixed_spread_is_used_at_any_time():
    c = costs()
    assert c.spread("XAUUSD") == 0.25
    assert c.spread("XAUUSD", SUMMER_0930) == 0.25


def test_with_a_table_the_spread_at_that_time_is_used():
    c = costs(spread_table=table())
    assert c.spread("XAUUSD", SUMMER_0930) == pytest.approx(0.45)
    assert c.spread("XAUUSD") == 0.25  # no time given: the fixed one


def test_a_symbol_or_hour_without_a_value_falls_back_to_the_fixed_spread():
    c = costs(spread_table=table())
    assert c.spread("XAUUSD", datetime(2026, 7, 1, 7, 0, tzinfo=UTC)) == 0.25
    sym = SymbolCosts(spread=0.7, commission_per_lot=0.0, contract_size=1)
    c = CostConfig(symbols={"NAS100": sym}, spread_table=table())
    assert c.spread("NAS100", SUMMER_0930) == 0.7


def test_spread_switched_off_is_zero_even_with_a_table():
    c = costs(spread_table=table(), spread_enabled=False)
    assert c.spread("XAUUSD", SUMMER_0930) == 0.0


def test_break_even_offset_and_cost_filter_follow_the_table():
    c = costs(spread_table=table(), max_cost_r=0.2)
    assert c.break_even_offset("XAUUSD", SUMMER_0930) == pytest.approx(0.45)
    # SL 1.0 away: 0.45 R of spread > 0.2; at the fixed 0.25 also > 0.2; SL 3 away: 0.15 R
    assert c.too_expensive("XAUUSD", 1.0, SUMMER_0930)
    assert not c.too_expensive("XAUUSD", 3.0, SUMMER_0930)
    assert not costs(spread_table=table(), max_cost_r=0.2).too_expensive("XAUUSD", 3.0)


def test_spread_r_uses_the_time_when_given():
    c = costs(spread_table=table())
    assert c.spread_r("XAUUSD", 1.0, SUMMER_0930) == pytest.approx(0.45)
    assert c.spread_r("XAUUSD", 1.0) == pytest.approx(0.25)


# --- in the engine ------------------------------------------------------------------------------------------------


class EnterAtFirstClose(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)
    uses_session_break_even = False

    def __init__(self, direction):
        self.direction = direction

    def on_candle(self, now, views):
        base = views[Timeframe.M5]
        if base.cursor != 0:
            return []
        close = base.current.close
        sl = close - 2.0 if self.direction is Direction.BULLISH else close + 2.0
        return [Order(self.direction, close, sl, None)]


FLAT = (100.0, 100.1, 99.9, 100.0)


def run(direction, table_=None):
    entry_time = DEFAULT_START + Timeframe.M5.duration
    hour = entry_time.astimezone(NY).hour
    values = {"XAUUSD": {entry_time.astimezone(NY).year: {hour: 0.5}}}
    cfg = costs(spread_table=SpreadTable(values=values)) if table_ is None else costs()
    return run_backtest(
        EnterAtFirstClose(direction), [build_series([FLAT] * 3, symbol="XAUUSD")],
        EngineConfig(costs=cfg),
    )  # fmt: skip


def test_the_engine_charges_the_spread_of_the_entry_hour():
    (long,) = run(Direction.BULLISH)
    assert long.entry_fill == pytest.approx(100.5)  # bid + table spread
    assert long.spread_r == pytest.approx(0.5 / 2.0)
    (short,) = run(Direction.BEARISH)
    assert short.spread_r == pytest.approx(0.5 / 2.0)


def test_the_engine_without_a_table_is_unchanged():
    (long,) = run(Direction.BULLISH, table_=False)
    assert long.entry_fill == pytest.approx(100.25)
    assert long.spread_r == pytest.approx(0.25 / 2.0)
