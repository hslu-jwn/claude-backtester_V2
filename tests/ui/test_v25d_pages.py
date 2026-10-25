"""V2.5d cases, written before layout changes.

Backtest: running/done/error/cancelled, empty and populated lists, compact
columns, error-only message, one cancel control. Live: absent/running/paused/
error status, unique controls and confirm, chart/main and setup/side, five tabs
with positions default. Connection notes survive as titles and sub-folds.
Existing UI tests cover control callbacks, connection storage and trade links.
"""

import pytest
from dash import Dash, dcc, html

from backtester.ui import trading_panel
from backtester.ui.pages import backtest, live
from tests.ui.test_backtest_page import begin, make_run
from tests.ui.test_live_page import NOW, status
from tests.ui.test_v25c_pages import find, unique_ids, walk


@pytest.mark.parametrize("state", ["running", "done", "error", "cancelled"])
def test_job_strip_and_error_only_message(state):
    backtest.bj.reset()
    begin()
    try:
        snap = backtest.bj.snapshot(backtest.bj.current(), now=105)
        snap.update(state=state, message="example message")
        page = backtest.layout(snap)
        unique_ids(page)
        strip = find(page, "bj-key-strip")
        for id_ in ("bj-title", "bj-elapsed", "bj-eta", "bj-cancel"):
            find(strip, id_)
        assert find(page, "bj-message").children == ("example message" if state == "error" else "")
        assert "Risk & prop firm: open a run's results" in str(page)
    finally:
        backtest.bj.reset()


def test_list_columns_and_cancel_toast(tmp_path):
    assert "No backtest yet" in str(backtest.runs_list(tmp_path))
    make_run(tmp_path / "20261008-120000_XAUUSD")
    page = backtest.runs_list(tmp_path, backtest.CANCELLED_TOAST)
    assert find(page, "bj-toast").children == "Cancelled"
    toggle = find(page, "bj-more-columns")
    assert isinstance(toggle, html.Details) and not toggle.open
    assert "Days (UTC)" in str(toggle)
    assert "rs-down" in str(page)


@pytest.mark.parametrize("mode", ["none", "running", "paused", "error"])
def test_live_skeleton_and_controls(tmp_path, monkeypatch, mode):
    data = (
        None
        if mode == "none"
        else status(paused=mode == "paused", last_error="example error" if mode == "error" else "")
    )
    view = {
        "status": data,
        "state": "none" if mode == "none" else "paused" if mode == "paused" else "running",
        "age": None if data is None else 10,
        "log": [],
    }
    monkeypatch.setattr(live, "live_view", lambda *_: view)
    page = live.layout(tmp_path, NOW)
    unique_ids(page)
    tabs = find(page, "lv-tabs")
    assert isinstance(tabs, dcc.Tabs) and tabs.value == "positions"
    assert [t.label for t in tabs.children] == [
        "Open positions",
        "Closed trades",
        "Signals & skips",
        "Event log",
        "Settings",
    ]
    strip = find(page, "lv-key-strip")
    for id_ in ("lv-head", "lv-cards", "lv-start", "lv-pause", "lv-stop", "lv-emergency"):
        find(strip, id_)
    assert "Close ALL positions" in find(page, "lv-emergency").message
    main = next(n for n in walk(page) if isinstance(n, html.Main))
    side = next(n for n in walk(page) if isinstance(n, html.Aside))
    find(main, "lv-trades")
    find(side, "lv-setup")
    titles = [getattr(n, "title", "") for n in walk(page)]
    assert "Click a bar to open the trade on the chart." in titles
    assert any("Editable only while" in t for t in titles)


def test_connection_notes_and_folds():
    page = trading_panel.layout()
    unique_ids(page)
    titles = [getattr(n, "title", "") for n in walk(page)]
    for note in (
        "The account number.",
        "Never shown again after saving.",
        "A number.",
        "MetaTrader 5 now; others later.",
        "Pick one the terminal knows or type the name.",
        "Empty: the installed / running MetaTrader 5.",
        "The broker's name for each symbol (e.g. with a suffix). python -m backtester.tools.mt5_info finds them.",
        "Messages and commands (/status, /stop, /emergency) for the live bot. Create a bot with @BotFather for the token; the chat id is your chat with that bot. Stored only in the Windows Credential Manager.",
        "Demo accounts only (DEMO LOCK): buy and sell 2 x the minimum lot with SL and TP, move the SL, close half, close the rest. Nothing stays open.",
    ):
        assert note in titles
    folds = [n for n in walk(page) if isinstance(n, html.Details)]
    for label in ("Telegram", "Demo test orders"):
        assert any(
            isinstance(n.children[0], html.Summary) and n.children[0].children == label
            for n in folds
        )


def test_live_tabs_callback_keeps_all_controls_mounted():
    app = Dash(__name__)
    live.register_callbacks(app)
    switch = next(
        v["callback"].__wrapped__
        for k, v in app.callback_map.items()
        if "lv-tab-positions.style" in k
    )
    for i, name in enumerate(("positions", "closed", "signals", "log", "settings")):
        styles = switch(name)
        assert styles[i] == {}
        assert sum(s == {"display": "none"} for s in styles) == 4
