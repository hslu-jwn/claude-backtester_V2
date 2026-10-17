"""What the chart page sends to the browser: full payloads and replay deltas.
Spec: ROADMAP.md › 4.0a (parts 2-4), CLAUDE.md › Invariant #1 (no lookahead).

Data: the hand-built London / New York day of the strategy tests (scenario.py) with its
30m and 4h candles, every overlay on (swings, BOS + trend badges, FVG, OB, BPR, session
zones, sweeps and the strategy 1 trade), served by the trades test's fake sources.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parents[1] / "strategy" / "session_zone_sweep"))
from scenario import ENTRY_INDEX, LONDON, NY_FIRST, NY_SETUP, TO_TARGET
from test_trades_overlay import TF, FakeSources

from backtester.core.models import Timeframe
from backtester.engine.replay import Replay
from backtester.ui.chart_data import ChartData, encode
from backtester.ui.drawing import Box, Line
from backtester.ui.overlays import DEFAULT_SETTINGS, OVERLAYS
from backtester.ui.pages import chart  # noqa: F401  (registers every overlay)

FULL = LONDON + NY_SETUP + TO_TARGET
KEYS = list(OVERLAYS)
STAMP = re.compile(r"(\d{4}-)?(\d{2}-\d{2} \d{2}:\d{2})")


def scenario_replay():
    sources = FakeSources(FULL)
    m5, m30, _, h4 = (sources.series[TF[tf]] for tf in TF)
    return Replay(m5, [m30], overall=h4), sources


def new_data():
    replay, sources = scenario_replay()
    events = {}

    def events_for(overlay):
        if overlay.key not in events:
            args = (replay, DEFAULT_SETTINGS) + ((sources,) if overlay.needs_sources else ())
            events[overlay.key] = overlay.detect(*args)
        return events[overlay.key]

    return ChartData(replay, events_for), replay


@pytest.fixture(scope="module")
def data():
    return new_data()


def drawings(payload):
    return [d for ds in payload["types"].values() for d in ds]


def badges(payload):
    return [b for bs in payload["badges"].values() for b in bs]


def times_in(text: str):
    """Every "YYYY-MM-DD HH:MM" / "MM-DD HH:MM" in a hover or badge text (year 2026)."""
    for m in STAMP.finditer(text):
        yield datetime.strptime("2026-" + m.group(2), "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


def assert_known_at(payload_drawings, badges, cursor, replay):
    close = replay.close_time(cursor)
    for d in payload_drawings:
        for x in ("x", "x0", "x1"):
            if d.get(x) is not None:
                assert d[x] <= cursor, (d, cursor)
        for text in (d.get("s"), d.get("h")):
            if d["k"] in ("h", "m") and text:
                assert all(t <= close for t in times_in(text)), (text, cursor)
    for b in badges:
        assert all(t <= close for t in times_in(b["t"])), (b, cursor)


def test_the_scenario_has_every_overlay(data):
    data, replay = data
    payload = data.full(KEYS, len(replay) - 1)
    assert payload["messages"] == []
    counts = {k: len(v) for k, v in payload["types"].items()}
    assert all(counts[k] for k in KEYS if k != "sweep"), counts  # the day has no sweep
    assert [b["t"].split(":")[0] for b in payload["badges"]["bos"]] == [
        "Overall trend (H4)",
        "M5 trend",
    ]


def test_payload_carries_the_feed_switch_day(data):
    data, replay = data
    assert data.full(KEYS, 0)["feed_switch"] is None
    marked = ChartData(replay, data.events_for, feed_switch=date(2026, 10, 4))
    assert marked.full(KEYS, 0)["feed_switch"] == "2026-10-04"


def test_full_payload_at_any_cursor_has_nothing_after_it(data):
    data, replay = data
    for cursor in range(len(replay)):
        payload = data.full(KEYS, cursor)
        assert payload["cursor"] == cursor
        assert_known_at(drawings(payload), badges(payload), cursor, replay)
        candles = data.candles(0, cursor + 1)
        assert len(candles["t"]) == cursor + 1
        assert candles["t"][-1] == int(replay.view(cursor).current.ts.timestamp())
        assert all(x <= cursor for x, _, _ in data.sessions(0, cursor + 1))


def test_deltas_contain_nothing_after_their_cursor(data):
    data, replay = data
    for cursor in range(len(replay) - 1):
        delta = data.delta(KEYS, cursor, cursor + 1)
        assert delta["candles"]["x0"] == cursor + 1 and len(delta["candles"]["t"]) == 1
        assert all(x == cursor + 1 for x, _, _ in delta["sessions"])
        assert_known_at(delta["add"], badges(delta), cursor + 1, replay)


class Browser:
    """What the browser holds: candle count, session lines, drawing ids per type, badges."""

    def __init__(self, data, base_cursor):
        self.n = base_cursor + 1
        self.sessions = data.sessions(0, self.n)
        full = data.full(KEYS, base_cursor)
        self.ids = {k: Counter(d["id"] for d in v) for k, v in full["types"].items()}
        self.badges = full["badges"]
        self.cursor = base_cursor

    def apply(self, delta):
        assert delta["from"] == self.cursor
        if "candles" in delta:
            assert delta["candles"]["x0"] == self.n
            self.n += len(delta["candles"]["t"])
            self.sessions += delta["sessions"]
        if "drop" in delta:
            self.n -= delta["drop"]
            self.sessions = [s for s in self.sessions if s[0] <= delta["to"]]
        all_ids = Counter()
        for ids in self.ids.values():
            all_ids += ids
        for i in delta["remove"]:
            assert all_ids[i] > 0, "removes a drawing the browser doesn't have"
            for ids in self.ids.values():
                if ids[i]:
                    ids[i] -= 1
                    ids += Counter()  # drop zero counts
                    break
        for d in delta["add"]:
            self.ids[d["o"]][d["id"]] += 1
        self.badges = {**self.badges, **delta["badges"]}
        self.cursor = delta["to"]

    def equals_full(self, data):
        full = new_data()[0].full(KEYS, self.cursor)  # fresh: computed without any step
        assert self.n == self.cursor + 1
        assert self.sessions == data.sessions(0, self.n)
        for k in KEYS:
            assert +self.ids[k] == Counter(d["id"] for d in full["types"][k]), (k, self.cursor)
        assert self.badges == full["badges"]


def test_steps_forward_add_up_to_the_full_payload_at_every_cursor():
    data, replay = new_data()
    browser = Browser(data, 0)
    for cursor in range(1, len(replay)):
        browser.apply(data.delta(KEYS, cursor - 1, cursor))
        browser.equals_full(data)


def test_steps_back_and_jumps_add_up_too():
    data, replay = new_data()
    last = len(replay) - 1
    browser = Browser(data, NY_FIRST)
    path = [NY_FIRST + 1, NY_FIRST + 2, NY_FIRST + 1, NY_FIRST, ENTRY_INDEX, ENTRY_INDEX + 1,
            ENTRY_INDEX, 3, last, last - 1, NY_FIRST + 5]  # fmt: skip
    for to in path:
        browser.apply(data.delta(KEYS, browser.cursor, to))
        browser.equals_full(data)


def test_a_step_sends_only_what_changed():
    data, _ = new_data()
    data.full(KEYS, ENTRY_INDEX + 3)
    quiet = data.delta(KEYS, ENTRY_INDEX + 3, ENTRY_INDEX + 4)  # dojis after the target
    assert quiet["add"] == [] and quiet["remove"] == []
    entry = data.delta(KEYS, ENTRY_INDEX - 1, ENTRY_INDEX)
    assert any(d["o"] == "trades" for d in entry["add"])
    assert len(entry["add"]) < 40


def test_an_open_zone_runs_to_the_cursor_and_gets_its_end_when_it_closes(data):
    data, _ = data
    # the trade's FVG (109.1-109.5) is tapped at g and confirmed at h = the entry candle
    fvg = [d for d in data.full(["fvg"], ENTRY_INDEX - 1)["types"]["fvg"] if d["k"] == "b"]
    [open_box] = [d for d in fvg if (d["y0"], d["y1"]) == (109.1, 109.5)]
    assert open_box["x1"] is None  # live: drawn to the browser's latest candle
    later = [d for d in data.full(["fvg"], ENTRY_INDEX + 2)["types"]["fvg"] if d["k"] == "b"]
    [closed] = [d for d in later if (d["y0"], d["y1"]) == (109.1, 109.5)]
    assert closed["x1"] == ENTRY_INDEX


def test_sub_entries_are_tagged_so_the_browser_can_hide_them(data):
    data, replay = data
    payload = data.full(["fvg", "trades"], len(replay) - 1)
    parts = {(d["o"], d.get("p")) for d in drawings(payload)}
    assert ("fvg", "confirmed") in parts and ("fvg", None) in parts
    assert ("trades", "confluences") in parts and ("trades", None) in parts


def test_encoding_is_compact_and_ids_follow_the_content():
    box = Box(1, 5, 1.0, 2.0, "Z box", fill="#089981", fill_opacity=0.2, edge="#089981")
    a, b = encode("fvg", box), encode("fvg", box)
    assert a["id"] == b["id"]
    assert a == {"k": "b", "x0": 1, "x1": 5, "y0": 1.0, "y1": 2.0, "f": "rgba(8,153,129,0.2)",
                 "e": "#089981", "ew": 1, "o": "fvg", "id": a["id"]}  # fmt: skip
    line = encode("bos", Line(1, 4, 3.0, 3.0, "BOS", "#f23645", dash="dash"))
    assert line["d"] == "dash" and line["id"] != a["id"]
    assert encode("bos", Line(1, float("inf"), 3.0, 3.0, "BOS", "#f23645"))["x1"] is None


def test_session_lines_up_to_the_cursor_only():
    replay, _ = scenario_replay()
    data = ChartData(replay, lambda o: [])
    lines = data.sessions(0, len(replay))
    assert [label for _, _, label in lines] == ["London", "NY"]
    ny_x = next(x for x, _, label in lines if label == "NY")
    assert data.sessions(0, ny_x) == [lines[0]]
    assert data.sessions(ny_x, ny_x + 1) == [lines[1]]
    assert replay.timeframe is Timeframe.M5
