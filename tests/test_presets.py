"""Settings presets in results/presets/. Spec: ROADMAP.md › 4.2."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from backtester.presets import (
    PresetError,
    delete_preset,
    list_presets,
    load_preset,
    rename_preset,
    save_preset,
)
from backtester.runner import RunSettings


def tight():
    s = RunSettings()
    return replace(s, strategy=replace(s.strategy, max_sl_atr_mult=2.0, zone_kill=False))


def test_save_load_list(tmp_path):
    assert list_presets(tmp_path / "missing") == ["Default"]
    assert save_preset(" Tight SL ", tight(), tmp_path) == "Tight SL"
    save_preset("aggressive", RunSettings(), tmp_path)
    assert list_presets(tmp_path) == ["Default", "aggressive", "Tight SL"]
    assert load_preset("Tight SL", tmp_path) == tight()
    assert load_preset("tight sl", tmp_path) == tight()  # names ignore case (Windows)
    data = json.loads((tmp_path / "Tight SL.json").read_text())
    assert data["name"] == "Tight SL" and data["settings"]["strategy"]["zone_kill"] is False


def test_default_is_the_spec_defaults_and_is_protected(tmp_path):
    assert load_preset("Default", tmp_path) == RunSettings()
    for action in (
        lambda: save_preset("Default", tight(), tmp_path),
        lambda: save_preset("default", tight(), tmp_path),
        lambda: rename_preset("Default", "X", tmp_path),
        lambda: delete_preset("Default", tmp_path),
    ):
        with pytest.raises(PresetError):
            action()


def test_overwrite_rename_delete(tmp_path):
    save_preset("A", RunSettings(), tmp_path)
    save_preset("a", tight(), tmp_path)  # same preset, overwritten
    assert list_presets(tmp_path) == ["Default", "A"] and load_preset("A", tmp_path) == tight()
    save_preset("B", RunSettings(), tmp_path)
    with pytest.raises(PresetError, match="exists already"):
        rename_preset("A", "b", tmp_path)
    assert rename_preset("A", "C", tmp_path) == "C"
    assert list_presets(tmp_path) == ["Default", "B", "C"]
    delete_preset("C", tmp_path)
    assert list_presets(tmp_path) == ["Default", "B"]
    with pytest.raises(PresetError):
        load_preset("C", tmp_path)


@pytest.mark.parametrize("name", ["", "   ", "a/b", "..", "x" * 61, "a:b"])
def test_bad_names(tmp_path, name):
    with pytest.raises(PresetError):
        save_preset(name, RunSettings(), tmp_path)


def test_a_broken_file_is_skipped_and_reported(tmp_path):
    (tmp_path / "junk.json").write_text("not json")
    (tmp_path / "Old.json").write_text(json.dumps({"name": "Old", "settings": {"strategy": 5}}))
    assert list_presets(tmp_path) == ["Default", "Old"]
    with pytest.raises(PresetError, match="can't be read"):
        load_preset("Old", tmp_path)


# --- CLI = app: a preset belongs to one strategy (ROADMAP V2.6d step 5) ---------------------


def _nw():
    from backtester.strategy.registry import default_config

    cfg = default_config("no_wick")
    return RunSettings(strategy=cfg, warmup_days=7)


def test_load_preset_refuses_another_strategys_preset(tmp_path):
    save_preset("nw", _nw(), tmp_path)
    assert load_preset("nw", tmp_path, "no_wick") == _nw()
    assert load_preset("nw", tmp_path) == _nw()  # no strategy asked: whatever it holds
    with pytest.raises(PresetError, match="is for no_wick, not session_zone_sweep"):
        load_preset("nw", tmp_path, "session_zone_sweep")


def _run_cli(monkeypatch, tmp_path, argv):
    from backtester import run

    seen = {}

    def fake(symbols, start, end, settings, *a, **k):
        seen["settings"] = settings
        raise run.UnsupportedSymbolError("stop here")

    monkeypatch.setattr(run, "run_backtests", fake)
    base = ["XAUUSD", "--start", "2026-01-05", "--end", "2026-01-05"]
    base += ["--presets-dir", str(tmp_path), "--out", str(tmp_path / "out")]
    with pytest.raises(SystemExit):
        run.main([*base, *argv])
    return seen.get("settings")


def test_cli_loads_a_preset_of_any_strategy_like_the_app(monkeypatch, tmp_path):
    save_preset("nw", _nw(), tmp_path)
    # strategy omitted: taken from the preset; given and equal: same; both = the app's load
    for extra in ([], ["--strategy", "no_wick"]):
        assert _run_cli(monkeypatch, tmp_path, ["--preset", "NW", *extra]) == _nw()


def test_cli_refuses_a_preset_of_another_strategy(monkeypatch, tmp_path, capsys):
    save_preset("nw", _nw(), tmp_path)
    got = _run_cli(monkeypatch, tmp_path, ["--preset", "nw", "--strategy", "trend_following"])
    assert got is None
    assert "is for no_wick, not trend_following" in capsys.readouterr().err
    got = _run_cli(monkeypatch, tmp_path, ["--preset", "nw", "--strategy", "session_zone_sweep"])
    assert got is None


def test_cli_default_preset_is_the_strategys_spec_defaults(monkeypatch, tmp_path):
    from backtester.strategy.registry import default_config

    got = _run_cli(monkeypatch, tmp_path, ["--strategy", "no_wick"])
    assert got.strategy == default_config("no_wick")
    assert _run_cli(monkeypatch, tmp_path, ["--preset", "default"]).strategy == (
        RunSettings().strategy
    )


def test_cli_missing_preset_message(monkeypatch, tmp_path, capsys):
    assert _run_cli(monkeypatch, tmp_path, ["--preset", "nope"]) is None
    assert "no preset 'nope'" in capsys.readouterr().err
