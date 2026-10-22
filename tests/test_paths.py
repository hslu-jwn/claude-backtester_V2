"""Tests for repository-anchored paths (audit 13.17)."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from backtester import paths
from backtester.analytics import trial_log
from backtester.data import cache
from backtester.engine import costs


def test_paths_are_absolute(monkeypatch):
    # Undo the suite's autouse trial-log isolation for this read-only path check.
    monkeypatch.setattr(trial_log, "RESULTS_DIR", paths.RESULTS_DIR)
    assert paths.HOME_DIR.is_absolute()
    assert paths.RESULTS_DIR.is_absolute()
    assert paths.DATA_DIR.is_absolute()
    assert costs.FUNDING_DIR.is_absolute()
    assert cache.DEFAULT_CACHE_DIR.is_absolute()
    assert cache.MT5_CACHE_DIR.is_absolute()
    assert cache.LIVE_CACHE_DIR.is_absolute()
    assert trial_log.default_path().is_absolute()


def test_paths_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(trial_log, "RESULTS_DIR", paths.RESULTS_DIR)
    orig_home = paths.HOME_DIR
    orig_results = paths.RESULTS_DIR
    orig_data = paths.DATA_DIR
    orig_funding = costs.FUNDING_DIR
    orig_cache = cache.DEFAULT_CACHE_DIR
    orig_mt5 = cache.MT5_CACHE_DIR
    orig_live = cache.LIVE_CACHE_DIR
    orig_trials = trial_log.default_path()

    monkeypatch.chdir(tmp_path)

    # Re-evaluate or check that paths remain anchored to project root, not tmp_path
    assert paths.home() == orig_home
    assert paths.RESULTS_DIR == orig_results
    assert paths.DATA_DIR == orig_data
    assert costs.FUNDING_DIR == orig_funding
    assert cache.DEFAULT_CACHE_DIR == orig_cache
    assert cache.MT5_CACHE_DIR == orig_mt5
    assert cache.LIVE_CACHE_DIR == orig_live
    assert trial_log.default_path() == orig_trials
    assert not trial_log.default_path().is_relative_to(tmp_path)


def test_backtester_home_env_override(tmp_path, monkeypatch):
    custom = tmp_path / "custom_repo"
    custom.mkdir()
    monkeypatch.setenv("BACKTESTER_HOME", str(custom))

    assert paths.home() == custom.resolve()
    assert paths.results_dir() == custom.resolve() / "results"
    assert paths.data_dir() == custom.resolve() / "data"


@pytest.mark.parametrize(
    "module,attribute,suffix",
    [
        ("data.binance", "CACHE_DIR", "data/cache/binance"),
        ("data.binance", "FLOW_DIR", "data/cache/binance_flow"),
        ("data.binance", "FUNDING_DIR", "data/cache/binance_funding"),
        ("data.binance", "TMP_DIR", "data/raw/binance_tmp"),
        ("tools.histdata_download", "DEFAULT_ROOT", "data/raw/histdata"),
        ("tools.spread_table", "DEFAULT_OUT", "data/spreads"),
        ("risk.prop_card", "RESULTS_DIR", "results"),
        ("ui.pages.results", "RESULTS_DIR", "results"),
    ],
)
def test_consumer_defaults_are_anchored(module, attribute, suffix, tmp_path, monkeypatch):
    consumer = importlib.import_module("backtester." + module)
    monkeypatch.chdir(tmp_path)
    assert getattr(consumer, attribute) == paths.home() / suffix


def test_home_override_before_import_reaches_consumers(tmp_path):
    env = dict(os.environ, BACKTESTER_HOME=str(tmp_path), PYTHONPATH=str(paths.home() / "src"))
    code = (
        "import json; from backtester.data.cache import DEFAULT_CACHE_DIR; "
        "from backtester.analytics.trial_log import default_path; "
        "print(json.dumps([str(DEFAULT_CACHE_DIR), str(default_path())]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert [Path(p) for p in json.loads(result.stdout)] == [
        tmp_path / "data/cache/histdata",
        tmp_path / "results/trials.jsonl",
    ]


def test_explicit_trial_path_stays_relative(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    trial_log.append(trial_log.count_only("a2", "x", 1), Path("explicit/trials.jsonl"))
    assert (tmp_path / "explicit/trials.jsonl").exists()


@pytest.mark.parametrize("explicit", [False, True])
def test_dispatch_cli_default_is_anchored_explicit_is_relative(tmp_path, monkeypatch, explicit):
    from backtester.tools import ai_dispatch

    received = []
    monkeypatch.setattr(
        ai_dispatch, "run", lambda task, cfg, results, label: received.append(results) or 0
    )
    monkeypatch.chdir(tmp_path)
    args = ["codex", "--prompt", "path test"]
    if explicit:
        args += ["--results", "custom"]
    assert ai_dispatch.main(args) == 0
    assert received == [Path("custom") if explicit else paths.RESULTS_DIR]
