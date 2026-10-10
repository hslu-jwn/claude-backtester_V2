"""Chart page: candles for the chosen symbol, timeframe and days. Spec: ROADMAP.md › 1.1, 4.0a.

The page sends the candles to the browser (Lightweight Charts) as columns: open times in
UTC seconds, OHLC, spread; the browser fits the price axis to the visible candles itself.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from m1_frames import m1

from backtester.data.dukascopy import _empty_cache_frame, cache_path
from backtester.data.sources import SymbolSources
from backtester.ui.chart_config import ChartConfig, price_digits
from backtester.ui.pages.chart import base_payload, chart_settings


def write_day(cache_dir, day: str, frame) -> None:
    path = cache_path(cache_dir, "XAUUSD", date.fromisoformat(day))
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


@pytest.fixture
def cache(tmp_path):
    """09-01 and 09-02 have candles, 09-03 is cached as empty, 09-04 was never downloaded."""
    write_day(
        tmp_path,
        "2026-09-01",
        m1(
            ("10:00", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),
            ("10:05", 100.5, 102.0, 100.4, 101.0, 1.0, 0.4),
            day="2026-09-01",
        ),
    )
    write_day(
        tmp_path,
        "2026-09-02",
        m1(
            ("09:00", 101.0, 101.5, 100.0, 101.2, 1.0, 0.3),
            ("21:30", 101.2, 101.2, 101.2, 101.2, 0.0, 0.3),  # daily break filler: dropped
            day="2026-09-02",
        ),
    )
    write_day(tmp_path, "2026-09-03", _empty_cache_frame())
    return SymbolSources({"XAUUSD": tmp_path})


def utc(text: str) -> int:
    return int(datetime.fromisoformat(text).replace(tzinfo=UTC).timestamp())


def test_end_day_is_inclusive_and_flat_minutes_are_dropped(cache):
    payload, message = base_payload(cache, "XAUUSD", "M5", "2026-09-01", "2026-09-02")
    candles = payload["candles"]
    assert candles["t"] == [
        utc("2026-09-01 10:00"),
        utc("2026-09-01 10:05"),
        utc("2026-09-02 09:00"),
    ]
    assert candles["x0"] == 0 and payload["cursor"] == 2  # positions 0, 1, 2: no time gaps
    assert candles["h"] == [101.0, 102.0, 101.5] and candles["s"] == pytest.approx([0.2, 0.4, 0.3])
    assert message.startswith("3 M5 candles")
    assert payload["key"] == "XAUUSD|M5|2026-09-01|2026-09-02"
    assert (payload["tf"], payload["tfmin"], payload["digits"]) == ("M5", 5, 3)
    assert payload["range"] is None  # not in replay: the browser shows all candles


def test_range_with_a_day_never_downloaded_shows_the_error_and_no_chart(cache):
    payload, message = base_payload(cache, "XAUUSD", "M5", "2026-09-02", "2026-09-04")
    assert payload is None
    assert "2026-09-04" in message and "backtester.data.download" in message


def test_too_many_candles_asks_for_a_shorter_range(cache):
    config = ChartConfig(max_candles=2)
    payload, message = base_payload(
        cache, "XAUUSD", "M5", "2026-09-01", "2026-09-02", config=config
    )
    assert payload is None and "more than the limit of 2" in message


@pytest.mark.parametrize(
    "inputs, expected",
    [
        (("XAUUSD", "M5", "2026-09-03", "2026-09-03"), "No XAUUSD candles"),
        (("XAUUSD", "M5", "2026-09-02", "2026-09-01"), "end date is before"),
        ((None, "M5", "2026-09-01", "2026-09-02"), "Pick a symbol"),
    ],
)
def test_nothing_to_draw_gives_a_message(cache, inputs, expected):
    payload, message = base_payload(cache, *inputs)
    assert payload is None and expected in message


def test_price_digits_per_symbol():
    assert (price_digits("XAUUSD"), price_digits("GBPUSD"), price_digits("GBPJPY")) == (3, 5, 3)
    assert (price_digits("NAS100"), price_digits("US500")) == (2, 2)


def test_colors_come_from_the_config():
    custom = ChartConfig(up_body="#00ff00", background="#123456", show_grid=True)
    settings = chart_settings(custom)
    assert (settings["up_body"], settings["background"], settings["show_grid"]) == (
        "#00ff00",
        "#123456",
        True,
    )
    assert chart_settings()["down_body"] == "#000000"  # black down candles, as before
