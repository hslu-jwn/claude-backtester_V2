"""Review B1 (the user, 2026-11-11): the default spread table wins over the fixed spread, so the
live under-charge measured against the table (fill probe runs 3 + 4, ratio of means of bar spread
to table value, `results/fill_report_2026-11-09/fills.csv`) scales the table's value.
Spec: risk-management.md › Costs."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from backtester.engine.costs import CostConfig

AT = datetime(2026, 10, 6, 14, tzinfo=UTC)
ROLLOVER = datetime(2026, 10, 6, 21, tzinfo=UTC)


@pytest.mark.parametrize(
    "symbol, factor",
    [
        ("GBPJPY", 1.09), ("GBPUSD", 1.38), ("NAS100", 1.12), ("US500", 1.07),
        # extended table (the user, 2026-11-13, "A: full table"): live / table >= 1.05
        ("GER40", 1.07), ("UK100", 1.09), ("UKOIL", 1.09), ("US30", 1.10), ("USDCAD", 1.09),
        ("USOIL", 1.08),
    ],
)
def test_table_value_is_scaled_by_the_measured_live_ratio(symbol, factor):
    cfg = CostConfig()
    raw = cfg.spread_table.spread_at(symbol, AT)
    assert raw is not None
    assert cfg.spread(symbol, AT) == pytest.approx(raw * factor)


@pytest.mark.parametrize("symbol", ["XAUUSD", "EURUSD", "XAGUSD", "AUS200"])
def test_symbols_without_a_raise_keep_the_table_value(symbol):
    cfg = CostConfig()
    assert cfg.spread(symbol, AT) == cfg.spread_table.spread_at(symbol, AT)


def test_factor_applies_at_every_hour_and_not_to_the_fixed_fallback():
    cfg = CostConfig()
    assert cfg.spread("GBPJPY", ROLLOVER) == pytest.approx(
        cfg.spread_table.spread_at("GBPJPY", ROLLOVER) * 1.09
    )
    assert cfg.spread_table.spread_at("NAS100", ROLLOVER) is None
    assert cfg.spread("NAS100", ROLLOVER) == cfg.for_symbol("NAS100").spread  # fixed, unscaled


def test_empty_factor_reproduces_the_plain_table():
    cfg = replace(CostConfig(), spread_table_factor={})
    assert cfg.spread("GBPJPY", AT) == cfg.spread_table.spread_at("GBPJPY", AT)


def test_gb_factors_are_the_live_ratio_at_the_bar_close_lookup():
    """The user's go 2026-11-13 ("Yes, 1.09 / 1.38"): with a fill looked up at the bar that just closed
    (fill_spread_time), the 18:00 New York fills are compared with the hour-17 value, so the ratio of
    means over all fill probe entries is one factor for every hour: GBPJPY 1.09 (1.40 at the old
    lookup), GBPUSD 1.38 (2.18 at the old lookup; 1.33 without hour 18)."""
    from backtester.engine.costs import LIVE_TABLE_FACTOR

    assert (LIVE_TABLE_FACTOR["GBPJPY"], LIVE_TABLE_FACTOR["GBPUSD"]) == (1.09, 1.38)
