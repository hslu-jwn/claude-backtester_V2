"""Live candles on an open chart (ROADMAP V2.6d step 5): the server answers which bars to
append after the chart's last bar; only for the latest day of a symbol with live bars, never
for history, replay or a review. The browser side is `chart.js` (`liveAsk`, `live`)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from backtester.data.sources import SymbolSources
from backtester.ui.pages.chart import base_payload, live_bars
from tests.ui.test_chart_feed import LIVE_LEVEL, MINUTES, SYMBOL, put

CHART_JS = Path(__file__).parents[2] / "src/backtester/ui/assets/chart.js"
ON = {
    "on": True,
    "picking": False,
    "playing": False,
    "start": "2026-10-06T10:03:00",
    "now": "2026-10-06T10:05:00",
}
OFF = {"on": False, "picking": False, "playing": False, "start": None, "now": None}


def epoch(hh: int, mm: int, day: str = "2026-10-06") -> int:
    d = date.fromisoformat(day)
    return int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=UTC).timestamp())


@pytest.fixture
def live_sources(tmp_path):
    main, live = tmp_path / "mt5", tmp_path / "live"
    put(main, "2026-10-05", 200.0)
    put(live, "2026-10-06", LIVE_LEVEL)  # today: 10:00 .. 10:09
    return SymbolSources({SYMBOL: main}, fallback_dirs={SYMBOL: live}), live


def test_returns_bars_from_the_last_chart_bar_on(live_sources):
    sources, _ = live_sources
    out = live_bars(sources, SYMBOL, "M1", "2026-10-05", "2026-10-06", epoch(10, 7), OFF, None)
    assert out["candles"]["t"] == [epoch(10, 7), epoch(10, 8), epoch(10, 9)]
    assert out["key"].startswith(f"{SYMBOL}|M1|2026-10-05|2026-10-06")


def test_nothing_new_returns_only_the_last_bar(live_sources):
    sources, _ = live_sources
    out = live_bars(sources, SYMBOL, "M1", "2026-10-05", "2026-10-06", epoch(10, 9), OFF, None)
    assert out["candles"]["t"] == [epoch(10, 9)]


def test_higher_timeframe_gives_the_open_bucket(live_sources):
    sources, _ = live_sources
    out = live_bars(sources, SYMBOL, "M5", "2026-10-05", "2026-10-06", epoch(10, 5), OFF, None)
    assert out["candles"]["t"] == [epoch(10, 5)]
    assert len(out["candles"]["o"]) == 1


def test_historical_view_gets_nothing(live_sources):
    sources, _ = live_sources
    assert (
        live_bars(
            sources, SYMBOL, "M1", "2026-10-05", "2026-10-05", epoch(10, 5, "2026-10-05"), OFF, None
        )
        is None
    )


def test_symbol_without_live_data_gets_nothing(tmp_path):
    main = tmp_path / "mt5"
    put(main, "2026-10-05", 200.0)
    plain = SymbolSources({SYMBOL: main})
    assert (
        live_bars(
            plain, SYMBOL, "M1", "2026-10-05", "2026-10-05", epoch(10, 5, "2026-10-05"), OFF, None
        )
        is None
    )
    empty_live = SymbolSources({SYMBOL: main}, fallback_dirs={SYMBOL: tmp_path / "none"})
    assert (
        live_bars(
            empty_live,
            SYMBOL,
            "M1",
            "2026-10-05",
            "2026-10-05",
            epoch(10, 5, "2026-10-05"),
            OFF,
            None,
        )
        is None
    )


def test_replay_and_review_get_nothing(live_sources):
    sources, _ = live_sources
    args = (sources, SYMBOL, "M1", "2026-10-05", "2026-10-06", epoch(10, 7))
    assert live_bars(*args, ON, None) is None
    assert live_bars(*args, OFF, {"entry_time": "2026-10-06T10:05:00"}) is None


def test_bad_input_gets_nothing(live_sources):
    sources, _ = live_sources
    assert live_bars(sources, SYMBOL, "M1", "2026-10-05", "2026-10-06", None, OFF, None) is None
    assert live_bars(sources, None, "M1", "2026-10-05", "2026-10-06", 1, OFF, None) is None


def test_base_payload_says_whether_live_refresh_applies(live_sources):
    sources, _ = live_sources
    assert base_payload(sources, SYMBOL, "M1", "2026-10-05", "2026-10-06")[0]["live"] is True
    assert base_payload(sources, SYMBOL, "M1", "2026-10-05", "2026-10-05")[0]["live"] is False
    assert MINUTES == 10


def test_chart_js_handles_the_refresh():
    js = CHART_JS.read_text(encoding="utf-8")
    assert "liveAsk(" in js and "live(" in js
    ask = js[js.index("liveAsk(") :]
    ask = ask[: ask.index("\n      },")]
    assert "S.live" in ask and "S.replay" in ask and "S.picking" in ask
    assert "series.update" in js[js.index("      live(") :]
    assert "S.live = " in js  # set from the base payload
