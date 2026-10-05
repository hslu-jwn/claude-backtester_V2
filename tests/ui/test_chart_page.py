"""Chart page logic without a browser: loading, error messages, zoom handling.
Spec: ROADMAP.md › 1.1."""

from __future__ import annotations

from datetime import date

import pytest
from m1_frames import m1

from backtester.data.dukascopy import _empty_cache_frame, cache_path
from backtester.ui.chart_figure import ChartConfig
from backtester.ui.pages.chart import load_chart, visible_axes


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
    return tmp_path


def test_end_day_is_inclusive_and_flat_minutes_are_dropped(cache):
    fig, message, store = load_chart(cache, "XAUUSD", "M5", "2026-09-01", "2026-09-02")
    assert store["ts"] == ["2026-09-01T10:00:00Z", "2026-09-01T10:05:00Z", "2026-09-02T09:00:00Z"]
    assert list(fig.data[0].x) == [0, 1, 2]
    assert message.startswith("3 M5 candles")


def test_range_with_a_day_never_downloaded_shows_the_error_and_no_chart(cache):
    fig, message, store = load_chart(cache, "XAUUSD", "M5", "2026-09-02", "2026-09-04")
    assert fig is None and store is None
    assert "2026-09-04" in message and "backtester.data.download" in message


def test_too_many_candles_asks_for_a_shorter_range(cache):
    config = ChartConfig(max_candles=2)
    fig, message, _ = load_chart(cache, "XAUUSD", "M5", "2026-09-01", "2026-09-02", config)
    assert fig is None and "more than the limit of 2" in message


@pytest.mark.parametrize(
    "inputs, expected",
    [
        (("XAUUSD", "M5", "2026-09-03", "2026-09-03"), "No XAUUSD candles"),
        (("XAUUSD", "M5", "2026-09-02", "2026-09-01"), "end date is before"),
        ((None, "M5", "2026-09-01", "2026-09-02"), "Pick a symbol"),
    ],
)
def test_nothing_to_draw_gives_a_message(cache, inputs, expected):
    fig, message, store = load_chart(cache, *inputs)
    assert fig is None and store is None and expected in message


def test_zoom_refits_ticks_and_price_range_to_visible_candles(cache):
    _, _, store = load_chart(cache, "XAUUSD", "M5", "2026-09-01", "2026-09-02")
    tickvals, ticktext, yrange = visible_axes(
        {"xaxis.range[0]": 1.6, "xaxis.range[1]": 2.4}, store, ChartConfig(y_padding=0.0)
    )
    assert tickvals == [2] and ticktext == ["2026-09-02 09:00"]
    assert yrange == [100.0, 101.5]


def test_reset_zoom_shows_all_and_other_events_change_nothing(cache):
    _, _, store = load_chart(cache, "XAUUSD", "M5", "2026-09-01", "2026-09-02")
    _, _, yrange = visible_axes({"xaxis.autorange": True}, store, ChartConfig(y_padding=0.0))
    assert yrange == [99.0, 102.0]
    assert visible_axes({"dragmode": "zoom"}, store) is None
    assert visible_axes({"xaxis.autorange": True}, None) is None
