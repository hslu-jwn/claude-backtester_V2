"""A5 regressions: replay visibility, complete presets and background jobs."""

import json
from dataclasses import replace

import pytest
from dash import Dash
from fakes import FakeProcess, Spawner
from test_prop_card_job import CARD, FAST, wait_for, write_run
from test_trades_overlay import ENTRY_INDEX, FULL, FakeSources, ctx

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.replay import Replay
from backtester.presets import save_preset
from backtester.runner import RunSettings
from backtester.settings import settings_from_values
from backtester.ui import monte_carlo_job as mj
from backtester.ui import prop_card_job as pj
from backtester.ui import prop_firm_card
from backtester.ui import settings_panel as sp
from backtester.ui.pages import chart, results
from backtester.ui.trades_overlay import detect_trades, hover_text


def test_replay_range_end_hides_future_exit_and_partial(monkeypatch):
    sources = FakeSources(FULL)
    full = sources.chart()
    import backtester.ui.trades_overlay as overlay

    run = overlay.chart_run(
        sources, "XAUUSD", full.view(0).current.ts.date(), full.view(0).current.ts.date()
    )
    trade = run.trades[0]
    part = replace(trade.parts[0], time=trade.exit_time)
    monkeypatch.setattr(
        overlay, "chart_run", lambda *a: replace(run, trades=(replace(trade, parts=(part,)),))
    )
    replay = Replay(CandleSeries("XAUUSD", Timeframe.M5, list(full.view(ENTRY_INDEX))))
    [event] = detect_trades(replay, sources=sources)
    text = hover_text(event, ctx(ENTRY_INDEX))
    assert "still open at the cursor" in text
    assert "result " not in text
    assert "TP at" not in text
    assert event.exit_x > ENTRY_INDEX and event.part_xs[0] > ENTRY_INDEX


def test_trades_in_view_callback_observes_replay():
    app = Dash(__name__)
    chart.register_callbacks(app, None)
    callback = app.callback_map["side-trades.children"]
    assert {"id": "chart-replay", "property": "data"} in callback["inputs"]
    body = callback["callback"].__wrapped__(None, "XAUUSD", {"on": True})
    assert "replay" in str(body).lower()


def test_preset_preserves_hidden_costs_and_modified_state(tmp_path):
    settings = settings_from_values({"engine.costs.symbols.US30.spread": 123}, RunSettings())
    save_preset("Hidden", settings, tmp_path)
    loaded = sp.form_update({"load": "Hidden"}, {}, None, folder=tmp_path)
    assert sp.store_settings(loaded["store"]) == settings
    assert not loaded["modified"]
    edited = sp.form_update(
        "field", {**loaded["widgets"], "strategy.min_rr": 1.5}, loaded["store"], folder=tmp_path
    )
    expected = settings_from_values({"strategy.min_rr": 1.5}, settings)
    assert sp.store_settings(edited["store"]) == expected
    assert edited["modified"]
    assert sp.preset_label(edited["store"], tmp_path) == "Hidden (modified)"
    reopened = sp.form_update(None, {}, edited["store"], folder=tmp_path)
    assert sp.store_settings(reopened["store"] or edited["store"]) == expected


def test_research_variant_card_and_monte_carlo_resolve_same_folder(tmp_path, monkeypatch):
    alias = "research~grid_demo~v2"
    folder = tmp_path / "research" / "grid_demo" / "variants" / "v2"
    folder.mkdir(parents=True)
    (folder / "summary.json").write_text("{}")
    (folder / "trades.csv").write_text("id\n")
    seen = []
    monkeypatch.setattr(
        pj, "request", lambda path, firm: seen.append(path) or {"state": "running", "elapsed": 0}
    )
    prop_firm_card.poll_card(alias, "ftmo_2step", tmp_path)
    assert seen == [folder]
    mj.reset()
    spawn = Spawner()
    original = mj.start
    monkeypatch.setattr(mj, "start", lambda *a, **kw: original(*a, **kw, spawn=spawn))
    try:
        assert prop_firm_card.press_start(1, alias, tmp_path)
        argv = spawn.calls[0][0]
        assert argv[argv.index("--results-dir") + 1] == str(folder.parent)
        assert argv[argv.index("--run") + 1] == folder.name
    finally:
        mj.reset()


def test_changed_card_inputs_start_fresh_job(tmp_path):
    pj.reset()
    folder = write_run(tmp_path / "run")
    proc = FakeProcess()
    spawn = Spawner(proc, FakeProcess())
    try:
        pj.request(folder, preset=FAST, card=CARD, spawn=spawn)
        proc.finish(0)
        (folder / "trades.csv").write_text((folder / "trades.csv").read_text() + "\n")
        state = pj.request(folder, preset=FAST, card=CARD, spawn=spawn)
        assert state["state"] == "running"
        assert len(spawn.calls) == 2
    finally:
        pj.reset()


@pytest.mark.parametrize("root", [[], None, 42, "broken"])
def test_run_listing_skips_non_object_summary(tmp_path, root):
    for name, data in (("bad", root), ("good", {"symbols": ["NAS100"]})):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "summary.json").write_text(json.dumps(data))
    assert [item["value"] for item in results.list_runs(tmp_path)] == ["good"]


def test_monte_carlo_progress_survives_log_retention(tmp_path):
    folder = tmp_path / "run"
    folder.mkdir()
    (folder / "summary.json").write_text('{"symbols": ["XAUUSD", "GBPUSD"]}')
    (folder / "trades.csv").write_text("id\n")
    lines = ["kind D: paths\n"] + [f"XAUUSD path {i}/300\n" for i in range(1, 206)]
    mj.reset()
    try:
        job = mj.start("run", tmp_path, spawn=Spawner(FakeProcess(lines)))
        assert wait_for(lambda: len(job.lines()) == 200)
        snap = mj.snapshot("run", tmp_path)
        assert "Kind D" in snap["detail"] and "205/300" in snap["detail"]
        assert snap["percent"] == pytest.approx(205 / 600 * 100)
    finally:
        mj.reset()
