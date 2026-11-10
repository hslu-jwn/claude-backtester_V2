"""Pooled daily-reversal gates, preserving date clusters across symbols."""
from datetime import date

from test_energy_report_gates import trade

from backtester.tools import timed_hold_gates as gates

SYMBOLS = ("US500", "NAS100", "GER40", "UK100", "JP225", "AUS200")


def test_cluster_bootstrap_resamples_whole_utc_dates_and_is_deterministic():
    trades = [trade(0, 2, "US500"), trade(0, -1, "NAS100"), trade(1, 1, "US500")]
    a = gates.date_cluster_bootstrap(trades)
    assert a == gates.date_cluster_bootstrap(list(reversed(trades)))
    assert a["trades"] == 3 and a["clusters"] == 2
    assert 0.5 <= a["lower_2_5"] <= 1.0
    assert gates.date_cluster_bootstrap([]) is None


def test_daily_reversal_requires_six_symbols_stress_and_known_integrity():
    normal = [trade(day, 1, symbol) for symbol in SYMBOLS for day in range(0, 360, 14)]
    stressed = [trade(day, 0.5, symbol) for symbol in SYMBOLS for day in range(0, 360, 14)]
    row = gates.evaluate_daily_reversal(normal, stressed, date(2020, 1, 1),
                                       date(2020, 12, 31), None, SYMBOLS)
    assert row["gates"]["min_trades"]
    assert row["gates"]["breadth"]
    assert not row["gates"]["integrity"] and not row["advances"]
    missing = gates.evaluate_daily_reversal(normal, None, date(2020, 1, 1),
                                           date(2020, 12, 31), False, SYMBOLS)
    assert not missing["gates"]["positive_normal_and_doubled"]
    assert not missing["gates"]["integrity"]


def test_daily_reversal_reports_directions_by_symbol_and_half():
    a = trade(1, 2, "US500")
    b = trade(220, -1, "US500")
    a.direction, b.direction = "long", "short"
    row = gates.evaluate_daily_reversal([a, b], [a, b], date(2020, 1, 1),
                                       date(2020, 12, 31), None, SYMBOLS)
    assert row["symbols"]["US500"]["by_direction"]["long"]["halves_net_r"] == [2, 0]
    assert row["symbols"]["US500"]["by_direction"]["short"]["halves_net_r"] == [0, -1]


def test_daily_reversal_half_is_attributed_to_entry_not_exit():
    from datetime import UTC, datetime, timedelta

    crossing = trade(1, 2, "US500")
    crossing.entry_time = datetime(2020, 7, 1, 23, 30, tzinfo=UTC)
    crossing.exit_time = crossing.entry_time + timedelta(hours=1)
    row = gates.evaluate_daily_reversal([crossing], [crossing], date(2020, 1, 1),
                                       date(2020, 12, 31), None, SYMBOLS)
    assert row["pooled"]["halves_net_r"] == [2, 0]



def test_daily_doubled_costs_preserve_other_fields():
    from backtester.engine.costs import CostConfig
    costs = CostConfig()
    doubled = gates.daily_doubled_costs(costs)
    for symbol in SYMBOLS:
        old, new = costs.for_symbol(symbol), doubled.for_symbol(symbol)
        assert new.spread == 2 * old.spread
        assert new.slippage == 2 * old.slippage
        assert new.swap_long_per_lot == 2 * old.swap_long_per_lot
        assert new.commission_pct_per_side == 2 * old.commission_pct_per_side
        assert new.tick_size == old.tick_size
    if costs.spread_table:
        symbol = next(iter(costs.spread_table.values))
        year = next(iter(costs.spread_table.values[symbol]))
        hour = next(iter(costs.spread_table.values[symbol][year]))
        assert doubled.spread_table.values[symbol][year][hour] == 2 * costs.spread_table.values[symbol][year][hour]


def test_daily_integrity_ignores_weekend_gaps_but_checks_exit_and_invalid():
    from test_timed_hold_gates import _m1_for_trade
    t = trade(0, 1, "US500")
    data = _m1_for_trade(t)
    assert gates.daily_integrity_failures([t], data) == []
    data.high[0] = 0.1
    assert gates.daily_integrity_failures([t], data) == [t]
    missing_exit = _m1_for_trade(t, {t.exit_time - __import__("datetime").timedelta(minutes=1)})
    assert gates.daily_integrity_failures([t], missing_exit) == [t]
