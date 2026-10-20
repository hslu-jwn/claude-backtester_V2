"""The chart toolbar's "Update data" button (ROADMAP 7.5): one background job, polled status."""

from __future__ import annotations

import pytest

from backtester.ui import update_button as ub


class FakeUpdate:
    def __init__(self):
        self.starts = 0
        self.snapshot = {
            "running": False, "line": "", "done": [], "errors": [], "finished_at": None,
        }  # fmt: skip

    def start_background(self):
        if self.snapshot["running"]:
            return False
        self.starts += 1
        self.snapshot = {**self.snapshot, "running": True, "line": "MT5 XAUUSD", "errors": []}
        return True

    def state(self):
        return dict(self.snapshot)


@pytest.fixture
def fake(monkeypatch):
    f = FakeUpdate()
    monkeypatch.setattr(ub, "update_data", f)
    return f


def test_nothing_runs_when_the_page_loads(fake):
    view = ub.refresh(None)
    assert fake.starts == 0
    assert view["text"] == "" and view["button_disabled"] is False
    assert view["interval_disabled"] is True


def test_click_starts_once_and_shows_the_running_line(fake):
    view = ub.refresh(ub.BUTTON_ID)
    assert fake.starts == 1
    assert view["text"] == "MT5 XAUUSD"
    assert view["button_disabled"] is True and view["interval_disabled"] is False
    ub.refresh(ub.BUTTON_ID)  # a second click while running
    assert fake.starts == 1


def test_running_without_a_line_says_updating(fake):
    fake.snapshot.update(running=True, line="")
    assert ub.refresh("tick")["text"] == "Updating..."


def test_finished_shows_count_and_stops_polling(fake):
    fake.snapshot.update(running=False, done=["a", "b", "c"], finished_at="2026-10-17T10:00:00")
    view = ub.refresh("tick")
    assert view["text"] == "Updated 3 · 0 errors"
    assert view["title"] == view["text"]  # no error lines: the tooltip is just the full text
    assert view["button_disabled"] is False and view["interval_disabled"] is True


def test_finished_with_errors_lists_them_in_the_tooltip(fake):
    fake.snapshot.update(
        running=False, done=["a"], errors=["MT5: no login", "Binance: timeout"],
        finished_at="2026-10-17T10:00:00",
    )  # fmt: skip
    view = ub.refresh("tick")
    assert view["text"] == "Updated 1 · 2 errors"
    assert "MT5: no login" in view["title"] and "Binance: timeout" in view["title"]


def test_layout_has_button_and_status_and_callbacks_register():
    from dash import Dash

    text = str(ub.layout())
    assert ub.BUTTON_ID in text and ub.STATUS_ID in text and ub.TICK_ID in text
    app = Dash(__name__)
    ub.register_callbacks(app)
    assert any(ub.STATUS_ID in k for k in app.callback_map)


def test_status_does_not_overlap_and_title_has_the_full_text(fake):
    layout = ub.layout()
    wrap = layout[0]
    assert wrap.className == "tb-update-wrap"  # button + status share one positioned wrapper
    status = wrap.children[1]
    assert status.id == ub.STATUS_ID and "tb-update-status" in status.className
    fake.snapshot = {
        **fake.snapshot, "finished_at": 1, "done": ["a"] * 28, "errors": ["MT5: no login"],
    }  # fmt: skip
    view = ub.refresh(None)
    assert view["text"] in view["title"] and "MT5: no login" in view["title"]
    fake.snapshot = {**fake.snapshot, "running": True, "line": "MT5 " + "X" * 300}
    assert "X" * 300 in ub.refresh(None)["title"]
