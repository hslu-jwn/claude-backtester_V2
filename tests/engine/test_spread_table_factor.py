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
    "symbol, factor", [("GBPJPY", 1.40), ("NAS100", 1.12), ("US500", 1.07)]
)
def test_table_value_is_scaled_by_the_measured_live_ratio(symbol, factor):
    cfg = CostConfig()
    raw = cfg.spread_table.spread_at(symbol, AT)
    assert raw is not None
    assert cfg.spread(symbol, AT) == pytest.approx(raw * factor)


@pytest.mark.parametrize("symbol", ["GBPUSD", "XAUUSD"])
def test_symbols_without_a_raise_keep_the_table_value(symbol):
    cfg = CostConfig()
    assert cfg.spread(symbol, AT) == cfg.spread_table.spread_at(symbol, AT)


def test_factor_applies_at_every_hour_and_not_to_the_fixed_fallback():
    cfg = CostConfig()
    assert cfg.spread("GBPJPY", ROLLOVER) == pytest.approx(
        cfg.spread_table.spread_at("GBPJPY", ROLLOVER) * 1.40
    )
    assert cfg.spread_table.spread_at("NAS100", ROLLOVER) is None
    assert cfg.spread("NAS100", ROLLOVER) == cfg.for_symbol("NAS100").spread  # fixed, unscaled


def test_empty_factor_reproduces_the_plain_table():
    cfg = replace(CostConfig(), spread_table_factor={})
    assert cfg.spread("GBPJPY", AT) == cfg.spread_table.spread_at("GBPJPY", AT)
