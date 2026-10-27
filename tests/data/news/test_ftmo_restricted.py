"""FTMO restricted-news scope. Spec: docs/news.md > FTMO restricted events.

Source: FTMO FAQ "Can I trade news?" (ftmo.com/en/faq/can-i-trade-news/, read 2026-10-27).
"""

from datetime import UTC, date, datetime, timedelta

import pytest

from backtester.data.news import (
    Calendar,
    ImpactWindow,
    NewsConfig,
    ScheduleEvent,
    matching_events,
    relevant,
)

FTMO = NewsConfig(enabled=True)
IMPACT = NewsConfig(enabled=True, events="impact")
RELEASE = datetime(2024, 3, 8, 13, 30, tzinfo=UTC)
USD_AFFECTED = ("EURUSD", "USDJPY", "USDCAD", "XAUUSD", "US500", "NAS100", "US30", "US2000", "DXY")


def event(name, currency="USD", impact="High", country=""):
    return ScheduleEvent(
        "e", RELEASE, RELEASE.date(), None, None, "minute", currency, country, impact, name, "t"
    )


def test_default_scope_is_ftmo_restricted_and_bad_scope_fails():
    assert NewsConfig().events == "ftmo_restricted"
    with pytest.raises(ValueError):
        NewsConfig(events="everything")
    with pytest.raises(ValueError):
        NewsConfig(restricted={"USD": "(unclosed"})


@pytest.mark.parametrize(
    "name",
    [
        "Non-Farm Employment Change", "Unemployment Rate", "Average Hourly Earnings m/m",
        "Federal Funds Rate", "FOMC Statement", "FOMC Meeting Minutes", "Advance GDP q/q",
        "CPI y/y", "US CPI Report October 2026", "FOMC Rate Decision September 2026",
        "US Employment Situation (Non-Farm Payrolls) May 2026", "fomc statement",
    ],
)  # fmt: skip
def test_restricted_usd_events_hit_usd_pairs_gold_us_indices_and_dxy(name):
    e = event(name)
    assert all(relevant(e, s, FTMO) for s in USD_AFFECTED)
    for symbol in ("XAGUSD", "BTCUSD", "ETHUSD", "EURGBP", "GER40", "USOIL", "AUS200"):
        assert not relevant(e, symbol, FTMO), symbol


@pytest.mark.parametrize(
    "name",
    ["Unemployment Claims", "ADP Non-Farm Employment Change", "CPI m/m", "Core CPI m/m",
     "Prelim GDP q/q", "FOMC Press Conference", "Fed Chair Powell Speaks"],
)  # fmt: skip
def test_other_high_usd_events_are_not_restricted_but_count_in_impact_mode(name):
    e = event(name)
    assert not relevant(e, "EURUSD", FTMO)
    assert relevant(e, "EURUSD", IMPACT)


def test_rules_are_per_currency():
    assert relevant(event("CPI m/m", "CAD"), "USDCAD", FTMO)
    assert not relevant(event("CPI m/m", "USD"), "USDCAD", FTMO)
    assert relevant(event("Main Refinancing Rate", "EUR"), "EURGBP", FTMO)
    assert not relevant(event("Main Refinancing Rate", "EUR"), "GER40", FTMO)
    assert not relevant(event("German Prelim CPI m/m", "EUR"), "EURUSD", FTMO)
    assert relevant(event("SNB Policy Rate", "CHF"), "USDCHF", FTMO)
    assert relevant(event("RBA Rate Decision August 2026", "AUD"), "AUDJPY", FTMO)
    assert relevant(event("CPI q/q", "NZD"), "NZDUSD", FTMO)
    assert not relevant(event("CPI q/q", "AUD"), "AUDUSD", FTMO)


def test_jpy_has_no_restricted_events():
    e = event("Monetary Policy Statement", "JPY")
    assert not relevant(e, "USDJPY", FTMO)
    assert not relevant(e, "EURJPY", FTMO)


def test_crude_oil_inventories_hit_only_oil_even_at_medium_impact():
    e = event("Crude Oil Inventories", "USD", "Medium")
    assert relevant(e, "USOIL", FTMO) and relevant(e, "UKOIL", FTMO)
    assert not relevant(e, "EURUSD", FTMO)
    assert not relevant(e, "NATGAS", FTMO)
    calendar = Calendar((e,), "h", date(2020, 1, 2), date(2026, 10, 23))
    config = NewsConfig(enabled=True, high=ImpactWindow(2, 2), medium=ImpactWindow(0, 0))
    assert matching_events(RELEASE + timedelta(minutes=2), "USOIL", calendar, config) == (e,)
    assert matching_events(RELEASE + timedelta(minutes=3), "USOIL", calendar, config) == ()
    assert matching_events(RELEASE, "USOIL", calendar, replace_scope(config)) == ()


def replace_scope(config):
    from dataclasses import replace

    return replace(config, events="impact")


def test_settings_roundtrip_keeps_scope_and_rules():
    from backtester.engine.backtest import EngineConfig
    from backtester.runner import RunSettings
    from backtester.settings import from_json, to_json

    news = NewsConfig(enabled=True, events="impact", restricted={"USD": "CPI y/y"})
    settings = RunSettings(engine=EngineConfig(news=news))
    assert from_json(to_json(settings)) == settings
