"""Regression cases for the V2.6 step 5 review fixes; no app/server starts."""

import json
import multiprocessing as mp
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from dash import Dash, no_update

from backtester.core.errors import LookaheadError
from backtester.ui import review, trade_focus
from backtester.ui import review_callbacks as callbacks
from backtester.ui.chart_config import DEFAULT_CONFIG

ARGS = ("XAUUSD", "2020-01-01", "2020-01-02", '{"x":1}', "gap_fade")
COUNTS = {"total": 1, "take_exists": 1, "skip_absent": 0, "agreed": 1, "percent": 100.0}


def order(minute=0, symbol="XAUUSD", day="2020-01-01"):
    return {
        "symbol": symbol,
        "direction": "long",
        "entry_time": f"{day}T10:{minute:02}:00Z",
        "entry": 100,
        "sl": 99,
        "tp": 102,
        "exit_time": f"{day}T11:00:00Z",
        "exit": 102,
    }


@pytest.fixture
def fake_run(monkeypatch):
    orders = [order(0), order(1)]
    calls = []

    def run(*args):
        calls.append(args)
        return [SimpleNamespace(order=o, r_net=2) for o in orders]

    monkeypatch.setattr(callbacks, "review_orders", run)
    monkeypatch.setattr(trade_focus, "inspection_order", lambda t: t.order)
    return orders, calls


@pytest.mark.parametrize("choice", ["take", "skip"])
@pytest.mark.parametrize(
    "change",
    ["missing", "settings", "symbol", "strategy", "hash", "period", "entry", "direction", "index"],
)
def test_unseen_trade_cannot_be_labelled(tmp_path, fake_run, choice, change):
    state = callbacks.transition(None, "run", None, *ARGS, folder=tmp_path)[0]
    if change == "missing":
        state = None
    elif change == "settings":
        state["settings"] = '{"x":2}'
    elif change == "symbol":
        state["symbol"] = "OTHER"
    elif change == "strategy":
        state["strategy"] = "other"
    elif change == "hash":
        state["settings_hash"] = "stale"
    elif change == "period":
        state["first"] = "2019-01-01"
    elif change == "entry":
        state["entry_time"] = order(5)["entry_time"]
    elif change == "direction":
        state["order"]["direction"] = "short"
    else:
        state["index"] = 90
    result = callbacks.transition(None, choice, state, *ARGS, folder=tmp_path)
    assert review.load_labels("gap_fade", tmp_path) == []
    assert "ignored" in result[3].lower()


def test_visible_trade_can_be_labelled(tmp_path, fake_run):
    state = callbacks.transition(None, "run", None, *ARGS, folder=tmp_path)[0]
    result = callbacks.transition(None, "take", state, *ARGS, folder=tmp_path)
    assert "saved" in result[3].lower()
    assert review.load_labels("gap_fade", tmp_path)[0]["entry_time"] == state["entry_time"]


def append_worker(folder, worker):
    for i in range(30):
        row = review.label("gap_fade", order(i), str(worker), "take", "x" * 200)
        review.save_label(row, folder)
        review.history("gap_fade", f"{worker}-{i}", COUNTS, folder)


def test_process_safe_labels_and_history(tmp_path):
    folder = tmp_path / "review"
    ctx = mp.get_context("spawn")
    processes = [ctx.Process(target=append_worker, args=(folder, i)) for i in range(4)]
    try:
        for process in processes:
            process.start()
        for process in processes:
            process.join(120)  # spawn imports the whole package; slow under full-suite load
        assert [p.exitcode for p in processes] == [0, 0, 0, 0]  # None = still running
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join()
    labels = [json.loads(line) for line in (folder / "gap_fade.jsonl").read_text().splitlines()]
    snapshots = [
        json.loads(line) for line in (folder / "_history/gap_fade.jsonl").read_text().splitlines()
    ]
    assert len(labels) == len(snapshots) == 120
    assert len({r["settings_hash"] for r in snapshots}) == 120
    assert len(review.load_labels("gap_fade", folder)) == 30
    assert list((tmp_path / ".locks").rglob("*.lock"))
    assert not list(folder.rglob("*.lock"))


@pytest.mark.parametrize("fragment", ['{"unfinished":', "[]\n", '{"choice":"take"}\n', "\xff\n"])
def test_corrupt_labels_warn_in_panel_and_appends_survive(tmp_path, fake_run, fragment):
    path = tmp_path / "gap_fade.jsonl"
    path.write_bytes(fragment.encode("latin1"))
    state = callbacks.transition(None, "run", None, *ARGS, folder=tmp_path)
    assert "warning" in state[3].lower() and "skip" in state[3].lower()
    result = callbacks.transition(None, "take", state[0], *ARGS, folder=tmp_path)
    assert "warning" in result[3].lower()
    assert len(review.load_labels("gap_fade", tmp_path)) == 1


def test_corrupt_history_warns_in_panel(tmp_path, fake_run):
    path = tmp_path / "_history/gap_fade.jsonl"
    path.parent.mkdir()
    path.write_text('{"partial":')
    result = callbacks.transition(None, "run", None, *ARGS, folder=tmp_path)
    assert "warning" in result[3].lower()
    assert len(result[5]) == 1
    assert len(callbacks.transition(None, "run", None, *ARGS, folder=tmp_path)[5]) == 1


def test_agreement_only_runs_current_view_and_counts_other_labels(tmp_path, fake_run):
    for o, choice in [
        (order(0), "take"),
        (order(2, day="2020-01-02"), "skip"),
        (order(0, "OTHER"), "take"),
        (order(0, day="2010-01-01"), "take"),
        (order(0, day="2020-01-03"), "skip"),
    ]:
        review.save_label(review.label("gap_fade", o, "old", choice), tmp_path)
    result = callbacks.transition(None, "run", None, *ARGS, folder=tmp_path)
    assert len(fake_run[1]) == 1
    assert "2 of 5 labels in this view" in result[4]
    assert result[5][0]["percent"] == 100
    assert result[5][0]["total"] == 2


def test_legacy_history_migrates_once(tmp_path):
    old = tmp_path / "gap_fade-history.jsonl"
    old.write_text(
        json.dumps(dict(settings_hash="old", evaluated="2020-01-01T00:00:00Z", **COUNTS)) + "\n"
    )
    rows = review.history("gap_fade", "new", COUNTS, tmp_path)
    assert {r["settings_hash"] for r in rows} == {"old", "new"}
    assert not old.exists()
    new = tmp_path / "_history/gap_fade.jsonl"
    assert new.exists()
    review.history("gap_fade", "new", COUNTS, tmp_path)
    assert len(new.read_text().splitlines()) == 2


def test_history_strategy_name_collision_preserves_labels(tmp_path):
    row = review.label("gap_fade-history", order(), "a", "take")
    review.save_label(row, tmp_path)
    review.history("gap_fade", "a", COUNTS, tmp_path)
    assert review.load_labels("gap_fade-history", tmp_path) == [row]
    assert (tmp_path / "_history/gap_fade.jsonl").exists()


@pytest.mark.parametrize("strategy", ["_history", "_private"])
def test_reserved_strategy_names_rejected(tmp_path, strategy):
    with pytest.raises(ValueError):
        review.save_label(review.label(strategy, order(), "a", "take"), tmp_path)


def control_callback(tmp_path, monkeypatch, error):
    app = Dash(__name__)
    callbacks.register_callbacks(app, None, DEFAULT_CONFIG, tmp_path)
    control = next(
        c["callback"].__wrapped__
        for c in app.callback_map.values()
        if any(i["id"] == "review-run" for i in c["inputs"])
    )
    monkeypatch.setattr(callbacks, "ctx", SimpleNamespace(triggered_id="review-run"))
    monkeypatch.setattr(callbacks.settings_panel, "store_json", lambda s: ARGS[3])
    monkeypatch.setattr(callbacks.settings_panel, "store_strategy", lambda s: ARGS[4])

    def fail(*args):
        raise error

    monkeypatch.setattr(callbacks, "review_orders", fail)
    return control


def test_run_error_is_panel_message(tmp_path, monkeypatch):
    control = control_callback(tmp_path, monkeypatch, RuntimeError("Run unavailable"))
    result = control(*([0] * 8), {}, ARGS[0], None, ARGS[1], ARGS[2], None, None)
    assert "Run unavailable" in result[3]
    assert result[0] is no_update


def test_lookahead_error_is_never_swallowed(tmp_path, monkeypatch):
    control = control_callback(tmp_path, monkeypatch, LookaheadError("future"))
    with pytest.raises(LookaheadError):
        control(*([0] * 8), {}, ARGS[0], None, ARGS[1], ARGS[2], None, None)


def test_document_click_clears_only_active_focus():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable")
    source = Path("src/backtester/ui/assets/chart.js").read_text(encoding="utf-8")
    start = source.index(
        '  document.addEventListener("keydown", (e) => {\n    if (e.key === "Escape"'
    )
    end = source.index('  document.addEventListener("dblclick"', start)
    script = (
        """
const listeners = {};
const document = {addEventListener: (name, fn) => {listeners[name] = fn;}};
let calls = 0;
const setProps = () => {calls++;};
const S = {el: {contains: () => false}, orderDraw: null, nonce: 0};
"""
        + source[start:end]
        + """
const event = {target: {closest: () => false}};
listeners.click(event);
if (calls !== 0) throw Error("outside click with no focus");
S.orderDraw = {focused: true, items: [], inspections: [{order: {symbol: "XAUUSD"}}]};
listeners.click(event);
if (calls !== 1) throw Error("active focus not cleared");
S.orderDraw = {focused: false, items: [], inspections: [{order: {symbol: "XAUUSD"}}]};
listeners.click(event);
if (calls !== 1) throw Error("run drawings are not a focus");
S.orderDraw = null;
listeners.keydown({key: "Escape"});
if (calls !== 1) throw Error("Escape with no focus");
"""
    )
    result = subprocess.run(
        [node, "-e", script], capture_output=True, text=True, timeout=10, check=False
    )
    assert result.returncode == 0, result.stderr


def test_order_payload_marks_focus_separately_from_run_drawings(monkeypatch):
    from datetime import UTC, datetime, timedelta

    from backtester.core.models import Candle, Timeframe
    from backtester.core.series import CandleSeries
    from backtester.engine.replay import Replay
    from backtester.ui.pages import chart

    start = datetime(2020, 1, 1, 10, tzinfo=UTC)
    replay = Replay(
        CandleSeries(
            "XAUUSD",
            Timeframe.M1,
            [Candle(start + timedelta(minutes=i), 100, 104, 98, 100) for i in range(4)],
        )
    )
    monkeypatch.setattr(chart, "load_replay", lambda *a: (replay, ""))
    selected = order(1)
    monkeypatch.setattr(trade_focus, "inspection_order", lambda t: selected)
    args = (None, "XAUUSD", "M1", "2020-01-01", "2020-01-01")
    focused = chart.order_draw_payload(args[0], selected, *args[1:])
    run = chart.order_draw_payload(
        *args[:1], None, *args[1:], run_trades=[SimpleNamespace(symbol="XAUUSD")]
    )
    assert focused["focused"] is True
    assert run["focused"] is False
