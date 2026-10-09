"""MT5 adapter with a fake MetaTrader5 module (ROADMAP 0.4)."""

from __future__ import annotations

import subprocess
import sys
from datetime import UTC, datetime

import pytest
from fake_mt5 import FakeMt5

from backtester.core.models import Timeframe
from backtester.data.adapters.mt5_adapter import (
    Mt5Adapter,
    Mt5Error,
    Mt5Unavailable,
    ServerClock,
    load_mt5,
)

NY7 = ServerClock("America/New_York", 7)  # UTC+2 in winter, UTC+3 in US summer time


def server_seconds(*args) -> int:
    """Server wall time written as if UTC, like MT5's bar times."""
    return int(datetime(*args, tzinfo=UTC).timestamp())


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=UTC)


# --- server clock ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("server", "expected"),
    [
        ((2026, 1, 14, 10, 0), utc(2026, 1, 14, 8, 0)),  # winter: UTC+2
        ((2026, 7, 15, 10, 0), utc(2026, 7, 15, 7, 0)),  # summer: UTC+3
        # only the US on summer time (Europe changes on 29 March): New York's dates count
        ((2026, 3, 18, 10, 0), utc(2026, 3, 18, 7, 0)),
        ((2026, 10, 28, 10, 0), utc(2026, 10, 28, 7, 0)),  # Europe back, US not yet
        ((2026, 11, 2, 10, 0), utc(2026, 11, 2, 8, 0)),
    ],
)
def test_server_clock_follows_its_zone(server, expected):
    assert NY7.to_utc([server_seconds(*server)])[0] == expected
    assert NY7.to_server(expected) == datetime(*server, tzinfo=UTC)


def test_server_clock_europe_and_fixed():
    athens = ServerClock("Europe/London", 2)  # UTC+2 / +3 on Europe's dates
    assert athens.to_utc([server_seconds(2026, 3, 18, 10)])[0] == utc(2026, 3, 18, 8)
    assert athens.to_utc([server_seconds(2026, 4, 15, 10)])[0] == utc(2026, 4, 15, 7)
    fixed = ServerClock("UTC", 2)
    assert fixed.to_utc([server_seconds(2026, 7, 15, 10)])[0] == utc(2026, 7, 15, 8)
    assert fixed.label == "UTC + 2 h" and NY7.label == "America/New_York + 7 h"


def test_server_clock_round_trips_as_a_setting():
    assert ServerClock.from_dict(NY7.to_dict()) == NY7
    assert ServerClock.from_dict(None) is None


# --- adapter -----------------------------------------------------------------------------


def fake_with_bars(now_server=(2026, 9, 16, 13, 12)):
    fake = FakeMt5()
    fake.initialize()
    fake.add_symbol("XAUUSD.x", point=0.01)
    # M5 bars 2026-09-16 12:50 .. 13:10 server time (UTC+3 → 09:50 .. 10:10 UTC)
    rows = [
        (server_seconds(2026, 9, 16, 12, 50), 3700.0, 3701.0, 3699.0, 3700.5, 15),
        (server_seconds(2026, 9, 16, 12, 55), 3700.5, 3702.0, 3700.0, 3701.5, 12),
        (server_seconds(2026, 9, 16, 13, 0), 3701.5, 3703.0, 3701.0, 3702.0, 20),
        (server_seconds(2026, 9, 16, 13, 5), 3702.0, 3702.5, 3700.0, 3700.2, 25),
        (server_seconds(2026, 9, 16, 13, 10), 3700.2, 3700.9, 3699.5, 3700.8, 18),  # forming
    ]
    fake.set_rates("XAUUSD.x", fake.TIMEFRAME_M5, rows)
    now = NY7.to_utc([server_seconds(*now_server)])[0].to_pydatetime()
    adapter = Mt5Adapter(fake, NY7, {"XAUUSD": "XAUUSD.x"}, now=lambda: now)
    return fake, adapter


def test_fetch_converts_to_utc_and_drops_the_forming_candle():
    _, adapter = fake_with_bars()
    candles = adapter.fetch("XAUUSD", Timeframe.M5, utc(2026, 9, 16), utc(2026, 9, 17))
    assert [c.ts for c in candles] == [
        utc(2026, 9, 16, 9, 50),
        utc(2026, 9, 16, 9, 55),
        utc(2026, 9, 16, 10, 0),
        utc(2026, 9, 16, 10, 5),
    ]  # 10:10 closes at 10:15 UTC, after now (10:12)
    first = candles[0]
    assert (first.open, first.high, first.low, first.close) == (3700.0, 3701.0, 3699.0, 3700.5)
    assert first.spread == pytest.approx(0.15)  # 15 points x 0.01
    assert first.volume == 10


def test_a_candle_closing_exactly_now_is_closed():
    _, adapter = fake_with_bars(now_server=(2026, 9, 16, 13, 15))
    candles = adapter.fetch("XAUUSD", Timeframe.M5, utc(2026, 9, 16), utc(2026, 9, 17))
    assert candles[-1].ts == utc(2026, 9, 16, 10, 10)


def test_fetch_keeps_only_the_requested_utc_range():
    _, adapter = fake_with_bars()
    candles = adapter.fetch(
        "XAUUSD", Timeframe.M5, utc(2026, 9, 16, 9, 55), utc(2026, 9, 16, 10, 5)
    )
    assert [c.ts for c in candles] == [utc(2026, 9, 16, 9, 55), utc(2026, 9, 16, 10, 0)]


def test_fetch_asks_the_terminal_in_server_time():
    fake, adapter = fake_with_bars()
    calls = []
    original = fake.copy_rates_range
    fake.copy_rates_range = lambda *a: calls.append(a) or original(*a)
    adapter.fetch("XAUUSD", Timeframe.M5, utc(2026, 9, 16, 10), utc(2026, 9, 16, 11))
    name, timeframe, start, end = calls[0]
    assert (name, timeframe) == ("XAUUSD.x", fake.TIMEFRAME_M5)
    assert start == datetime(2026, 9, 15, 13, tzinfo=UTC)  # 1 day before, +3 h
    assert end == datetime(2026, 9, 17, 14, tzinfo=UTC)


def test_history_returns_every_closed_candle():
    _, adapter = fake_with_bars()
    frame = adapter.history("XAUUSD", Timeframe.M5)
    assert len(frame) == 4 and frame["ts"].iloc[0] == utc(2026, 9, 16, 9, 50)


def test_unserved_timeframe_unknown_symbol_and_missing_clock():
    fake, adapter = fake_with_bars()
    with pytest.raises(ValueError, match="H4 is not served"):
        adapter.fetch("XAUUSD", Timeframe.H4, utc(2026, 9, 16), utc(2026, 9, 17))
    with pytest.raises(Mt5Error, match="GBPUSD: unknown symbol"):
        adapter.fetch("GBPUSD", Timeframe.M5, utc(2026, 9, 16), utc(2026, 9, 17))
    with pytest.raises(ValueError, match="server time rule is not known"):
        Mt5Adapter(fake, None)


def test_load_mt5_without_the_package(monkeypatch):
    monkeypatch.setitem(sys.modules, "MetaTrader5", None)  # import fails
    with pytest.raises(Mt5Unavailable, match=r"pip install -e \"\.\[mt5\]\""):
        load_mt5()


def test_nothing_else_imports_metatrader5():
    """Backtests, the chart and the CLI modules load without the package."""
    modules = [
        "backtester.ui.app",
        "backtester.run",
        "backtester.data.mt5_info",
        "backtester.data.feed_compare",
        "backtester.live.test_orders",
        "backtester.ui.trading_panel",
    ]
    code = (
        "import importlib, sys; sys.modules['MetaTrader5'] = None\n"
        f"for m in {modules!r}: importlib.import_module(m)\n"
        "print('ok')"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert out.stdout.strip() == "ok", out.stderr
