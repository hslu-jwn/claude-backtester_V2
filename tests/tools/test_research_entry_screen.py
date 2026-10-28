"""Chosen-development entry screen, including bounded synthetic M1 loading."""

import json
import time
from datetime import date

import numpy as np
import pytest

from backtester.analytics.entry_screen import M1Data
from backtester.tools import entry_screen, research_entry_screen, research_grid
from tests.tools.test_research import GRID, read_csv, run_research, write_grid
from tests.tools.test_research import fakes as research_fakes

fakes = research_fakes
SCREEN_GRID = GRID.replace("entry_screen = false", "entry_screen = true")


def test_grid_boolean(tmp_path):
    with pytest.raises(research_grid.GridError, match="entry_screen"):
        research_grid.load_grid(
            write_grid(tmp_path, SCREEN_GRID.replace("entry_screen = true", 'entry_screen="yes"'))
        )


def test_real_screen_on_fixture_and_development_bounds(tmp_path, fakes, monkeypatch):
    calls = []
    timings = []
    configs = []
    calculate = research_entry_screen.calculate
    screen_variant = research_entry_screen.screen_variant

    def timed(*args):
        started = time.perf_counter()
        result = calculate(*args)
        timings.append(time.perf_counter() - started)
        return result

    def screen(*args):
        configs.append(args[4])
        return screen_variant(*args)

    monkeypatch.setattr(research_entry_screen, "calculate", timed)
    monkeypatch.setattr(research_entry_screen, "screen_variant", screen)

    def load(symbol, sources, start, end):
        calls.append((symbol, start, end))
        # Synthetic bars around every development trade, flat bid prices.
        from tests.tools.test_research import make_trade

        starts = [
            make_trade(symbol, y, 0, n).entry_time.timestamp()
            for y in (2015, 2021)
            for n in range(4)
        ]
        seconds = np.unique(np.concatenate([s + np.arange(-1, 301) * 60 for s in starts]))
        prices = np.full(len(seconds), 100.0)
        return M1Data(seconds, prices, prices + 0.1, prices - 0.1, prices)

    monkeypatch.setattr(entry_screen, "load_m1", load)
    started = time.perf_counter()
    out = run_research(tmp_path, SCREEN_GRID, dev_only=True)
    elapsed = time.perf_counter() - started
    print(f"entry-screen synthetic runner fixture: {elapsed:.3f}s")
    print(f"entry-screen calculate only: {timings[0]:.3f}s")
    assert configs[0].random_runs == configs[0].shuffle_runs == 1000
    assert configs[0].seed == 42
    folder = out["folder"]
    data = json.loads((folder / "entry_screen.json").read_text())
    assert set(data) == {
        "variant_id",
        "start",
        "end",
        "bar_minutes",
        "passed",
        "reasons",
        "cells",
        "cells_positive",
        "cell_share",
        "bracket_win_rate",
        "random_percentile",
        "trades",
        "skipped",
        "flags",
    }
    assert isinstance(data["passed"], bool) and data["passed"] is False
    assert data["bar_minutes"] == 1 and data["trades"] == 8
    assert calls and all(end == date(2021, 9, 13) for _, _, end in calls)
    assert "entry_screen_failed" in next(
        r["flags"]
        for r in read_csv(folder / "variants.csv")
        if r["variant_id"] == out["chosen"]["id"]
    )
    assert "Entry screen (chosen development variant)" in (folder / "report.md").read_text()
    json.dumps(data, allow_nan=False)


def test_opt_out_removes_stale_file(tmp_path, fakes, monkeypatch):
    def forbidden(*a):
        pytest.fail("disabled screen must not load M1")

    monkeypatch.setattr(entry_screen, "load_m1", forbidden)
    text = GRID
    out = run_research(tmp_path, text, dev_only=True)
    path = out["folder"] / "entry_screen.json"
    assert not path.exists()
    path.write_text("{}")
    run_research(tmp_path, text, dev_only=True)
    assert not path.exists()


def test_missing_m1_records_error_and_finishes(tmp_path, fakes, monkeypatch):
    def missing(*a):
        raise SystemExit("US500: no cached day")

    monkeypatch.setattr(entry_screen, "load_m1", missing)
    out = run_research(tmp_path, SCREEN_GRID, dev_only=True)
    assert out["status"] == "dev_only"
    data = json.loads((out["folder"] / "entry_screen.json").read_text())
    assert data["error"] == "US500: no cached day"
    assert data["error"] in (out["folder"] / "report.md").read_text()


def test_no_chosen_variant_removes_stale_screen(tmp_path, fakes, monkeypatch):
    def forbidden(*args):
        pytest.fail("no chosen variant must skip entry screening")

    monkeypatch.setattr(research_entry_screen, "calculate", forbidden)
    text = SCREEN_GRID.replace("min_trades = 4", "min_trades = 500")
    out = run_research(tmp_path, text, dev_only=True)
    path = out["folder"] / "entry_screen.json"
    path.write_text("{}")
    out = run_research(tmp_path, text, dev_only=True)
    assert out["chosen"] is None and not path.exists()


def test_strategy_base_timeframe_and_empty_trades_are_json_safe(tmp_path):
    from backtester.runner import RunSettings
    from backtester.strategy.no_wick.config import NoWickConfig

    spec = research_grid.GridSpec("no_wick", "no_wick", ("US500",), {}, {}, 0, 1, 1)
    data = research_entry_screen.calculate(
        tmp_path,
        spec,
        "empty",
        date(2020, 1, 1),
        date(2020, 12, 31),
        RunSettings(strategy=NoWickConfig()),
        None,
    )
    assert data["bar_minutes"] == 15
    assert data["trades"] == data["skipped"] == 0
    assert data["passed"] is False
    json.dumps(data, allow_nan=False)
