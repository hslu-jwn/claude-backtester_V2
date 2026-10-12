"""Server clock measurement and symbol finding (ROADMAP 0.4), on synthetic candles."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest
from fake_mt5 import FakeMt5

from backtester.data.adapters.mt5_adapter import ServerClock
from backtester.tools import mt5_info
from backtester.tools.mt5_compare import (
    cached_runs,
    discriminating_weeks,
    fit_clock,
    symbol_candidates,
    symbol_specs,
    tick_age,
    weekly_offsets,
)

NY7 = ServerClock("America/New_York", 7)
# Mondays: winter, US-only summer time (US from 8 March, Europe from 29 March), both summer
WEEKS = (date(2026, 2, 23), date(2026, 3, 9), date(2026, 3, 16), date(2026, 4, 13))


def cache_h1(weeks=WEEKS, seed=1) -> pd.DataFrame:
    """Random-walk H1 candles Monday 00:00 .. Friday 20:00 UTC of each week."""
    rng = np.random.default_rng(seed)
    rows, price = [], 2000.0
    for monday in weeks:
        start = datetime(monday.year, monday.month, monday.day, tzinfo=UTC)
        for i in range(4 * 24 + 21):
            o = price
            c = o + rng.normal(0, 3)
            h, lo = max(o, c) + abs(rng.normal(0, 1)), min(o, c) - abs(rng.normal(0, 1))
            rows.append((start + timedelta(hours=i), o, h, lo, c))
            price = c
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close"])


def as_server(ref: pd.DataFrame, clock: ServerClock, noise=0.05, seed=2) -> pd.DataFrame:
    """The same candles as MT5 would give them: server seconds, slightly different prices."""
    rng = np.random.default_rng(seed)
    times = [int(clock.to_server(ts.to_pydatetime()).timestamp()) for ts in ref["ts"]]
    jitter = rng.normal(0, noise, len(ref))
    return pd.DataFrame(
        {
            "time": times,
            "open": ref["open"] + jitter,
            "high": ref["high"] + jitter,
            "low": ref["low"] + jitter,
            "close": ref["close"] + jitter,
        }
    )


def test_weekly_offsets_find_each_weeks_offset():
    ref = cache_h1()
    weeks = weekly_offsets(as_server(ref, NY7), ref)
    assert list(weeks["week"]) == list(WEEKS)
    assert list(weeks["offset_h"]) == [2, 3, 3, 3]
    assert (weeks["error"] < 0.1).all() and (weeks["runner_up_error"] > 1).all()


def test_fit_clock_tells_us_dates_from_europes():
    ref = cache_h1()
    weeks = weekly_offsets(as_server(ref, NY7), ref)
    fits = fit_clock(weeks)
    assert fits[0].clock == NY7 and fits[0].matched_weeks == 4 and not fits[0].misses
    europe = next(f for f in fits if f.clock == ServerClock("Europe/London", 2))
    assert europe.misses == (date(2026, 3, 9), date(2026, 3, 16))  # only the US on summer time
    assert list(discriminating_weeks(weeks)["week"]) == [date(2026, 3, 9), date(2026, 3, 16)]


def test_fit_clock_prefers_the_fixed_rule_when_all_agree():
    ref = cache_h1(weeks=(date(2026, 1, 12), date(2026, 1, 19)))
    weeks = weekly_offsets(as_server(ref, ServerClock("UTC", 2)), ref)
    assert fit_clock(weeks)[0].clock == ServerClock("UTC", 2)  # winter only: all rules tie


def test_clock_report_saves_only_a_rule_that_predicts_every_week():
    ref = cache_h1()
    weeks = weekly_offsets(as_server(ref, NY7), ref).assign(symbol="XAUUSD")
    clock, lines = mt5_info.clock_report(weeks)
    assert clock == NY7
    assert any("2026-03-09 (XAUUSD): measured UTC+3 h, rule says UTC+3 h" in s for s in lines)
    only_winter = weeks[weeks["week"] == date(2026, 2, 23)]
    clock, lines = mt5_info.clock_report(only_winter)
    assert clock is None and "nothing saved" in lines[-1]  # many rules fit one week


def test_measure_clock_with_a_fake_terminal(monkeypatch):
    ref = cache_h1()
    fake = FakeMt5()
    fake.initialize()
    fake.add_symbol("XAUUSD.r")
    server = as_server(ref, NY7)
    fake.set_rates(
        "XAUUSD.r",
        fake.TIMEFRAME_H1,
        list(server[["time", "open", "high", "low", "close"]].itertuples(index=False)),
    )
    monkeypatch.setattr(mt5_info, "cached_frame", lambda *a: ref)
    weeks, lines = mt5_info.measure_clock(
        fake, {"XAUUSD": "XAUUSD.r"}, None, datetime(2026, 10, 9, tzinfo=UTC)
    )
    assert lines[0].startswith("XAUUSD (XAUUSD.r): MT5 H1 from 2026-02-23")
    assert list(weeks["offset_h"]) == [2, 3, 3, 3]


def test_live_check_with_a_fresh_and_a_stale_tick():
    fake = FakeMt5()
    now = datetime(2026, 10, 7, 12, 0, 30, tzinfo=UTC)
    server_now = int(NY7.to_server(now).timestamp())
    fake.set_tick("XAUUSD", 4000.0, 4000.2, server_now - 20)
    lines = mt5_info.live_check(fake, ["XAUUSD"], NY7, now)
    assert lines[0] == "Latest tick: server time − UTC now = +2.99 h"
    assert "agrees" in lines[1]
    fake.set_tick("XAUUSD", 4000.0, 4000.2, server_now - 3 * 3600)
    assert "no live confirmation" in mt5_info.live_check(fake, ["XAUUSD"], NY7, now)[1]
    assert tick_age(server_now, NY7, now) == timedelta(0)


@pytest.mark.parametrize(
    ("available", "wanted", "expected"),
    [
        (["XAUUSD", "XAUUSD.r", "XAUEUR"], "XAUUSD", ["XAUUSD", "XAUUSD.r"]),
        (["GBPUSD.x", "GBPUSDm", "EURUSD"], "GBPUSD", ["GBPUSDm", "GBPUSD.x"]),
        (["GOLD", "SILVER"], "XAUUSD", ["GOLD"]),
        (["GBPJPY_ecn"], "GBPJPY", ["GBPJPY_ecn"]),
        (["EURUSD"], "GBPJPY", []),
    ],
)
def test_symbol_candidates(available, wanted, expected):
    assert symbol_candidates(available, wanted) == expected


def test_symbol_specs_are_readable():
    fake = FakeMt5()
    fake.add_symbol("XAUUSD", trade_stops_level=20, volume_min=0.01, volume_step=0.01)
    specs = symbol_specs(fake.symbol_info("XAUUSD"))
    assert specs["contract size"] == "100"
    assert specs["stops level"] == "20 points (0.2)"
    assert specs["volume min / step / max"] == "0.01 / 0.01 / 100"
    assert specs["filling"] == "FOK, IOC"
    assert specs["trade mode"] == "full"
    assert specs["swap long / short"] == "-10 / 5 (points)"


def test_find_symbols_on_the_fake_server():
    fake = FakeMt5()
    for name in ("XAUUSD", "GBPUSD.r", "GBPJPY.r", "EURUSD"):
        fake.add_symbol(name)
    found = mt5_info.find_symbols(fake, ["XAUUSD", "GBPUSD", "GBPJPY"])
    assert found == {"XAUUSD": ["XAUUSD"], "GBPUSD": ["GBPUSD.r"], "GBPJPY": ["GBPJPY.r"]}


def test_cached_runs():
    days = [date(2026, 9, d) for d in (1, 2, 3, 7, 8, 30)]
    assert cached_runs(days, date(2026, 9, 2), date(2026, 9, 29)) == [
        (date(2026, 9, 2), date(2026, 9, 3)),
        (date(2026, 9, 7), date(2026, 9, 8)),
    ]
