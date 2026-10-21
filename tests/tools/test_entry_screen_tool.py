"""Entry screening tool (ROADMAP 12.12): option parsing, development-period guard, an end-to-end run
on a tiny temp cache with a stubbed backtest, output files, trial log.
Spec: risk-management.md > Entry screening."""

from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace

import pytest
from m1_frames import m1

from backtester.analytics import trial_log
from backtester.core.models import Direction
from backtester.data.cache import cache_path
from backtester.strategy.gap_momentum.config import GapMomentumConfig
from backtester.strategy.registry import REGISTRY
from backtester.tools import entry_screen
from backtester.tools.entry_screen import DEV_END, STRATEGY_SYMBOLS, parse_sets, variant_label


def test_every_registered_strategy_has_default_symbols():
    assert set(STRATEGY_SYMBOLS) == set(REGISTRY)
    assert STRATEGY_SYMBOLS["session_zone_sweep"] == ("XAUUSD", "GBPUSD", "GBPJPY")
    assert STRATEGY_SYMBOLS["gap_momentum"] == ("NAS100", "US500")


def test_set_options_parse_by_the_type_of_the_default_and_sweep_on_commas():
    one = parse_sets(["entry_z=0.25", "exit_time=11:00", "vol_days=60"], GapMomentumConfig)
    assert one == [{"entry_z": 0.25, "exit_time": time(11), "vol_days": 60}]
    grid = parse_sets(["entry_z=0,0.5", "stop_atr=1,2"], GapMomentumConfig)
    assert len(grid) == 4 and {g["entry_z"] for g in grid} == {0.0, 0.5}
    assert parse_sets([], GapMomentumConfig) == [{}]


def test_unknown_or_malformed_set_options_are_errors():
    with pytest.raises(SystemExit, match="nope"):
        parse_sets(["nope=1"], GapMomentumConfig)
    with pytest.raises(SystemExit, match="key=value"):
        parse_sets(["entry_z"], GapMomentumConfig)


def test_variant_label():
    assert variant_label({}) == "default"
    assert variant_label({"entry_z": 0.5, "exit_time": time(11)}) == "entry_z=0.5 exit_time=11:00"


# --- end to end on a tiny cache -----------------------------------------------------------------


def write_day(cache, symbol, day, rows):
    path = cache_path(cache, symbol, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    m1(*rows, day=day.isoformat()).to_parquet(path)


def cache_with_two_days(tmp_path):
    cache = tmp_path / "cache"
    for day in (date(2020, 3, 2), date(2020, 3, 3)):
        # price 100 until 14:30, then 101: a long entered at 14:20 is 1 R (stop 98) ahead by 14:40
        rows = [(f"14:{m:02d}", 100, 100, 100, 100, 1, 0) for m in range(30)]
        rows += [(f"14:{m:02d}", 101, 101, 101, 101, 1, 0) for m in range(30, 60)]
        write_day(cache, "NAS100", day, rows)
    return cache


def fake_trade(day, r_net=0.5):
    entry = datetime(day.year, day.month, day.day, 14, 20, tzinfo=UTC)
    return SimpleNamespace(
        symbol="NAS100", direction=Direction.BULLISH, entry_time=entry, entry=100.0,
        initial_stop=98.0, exit_time=entry + timedelta(minutes=20), r_net=r_net, r_gross=r_net,
    )  # fmt: skip


def fake_run_factory(seen):
    def fake_run(symbols, start, end, settings, *args, **kwargs):
        seen.append((tuple(symbols), start, end, settings, kwargs))
        trades = (fake_trade(date(2020, 3, 2)), fake_trade(date(2020, 3, 3), -1.0))
        return SimpleNamespace(trades=trades, runs={})

    return fake_run


def args_for(tmp_path, cache, *extra):
    return [
        "--strategy", "gap_momentum", "--symbols", "NAS100", "--start", "2020-03-02",
        "--end", "2020-03-03", "--cache-dir", str(cache), "--out", str(tmp_path / "out"),
        "--random-runs", "20", "--shuffle-runs", "20", *extra,
    ]  # fmt: skip


def test_run_writes_the_files_logs_one_trial_and_screens_the_stubbed_trades(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(entry_screen, "run_backtests", fake_run_factory(seen))
    cache = cache_with_two_days(tmp_path)
    assert entry_screen.main(args_for(tmp_path, cache)) == 0
    symbols, start, end, settings, _kw = seen[0]
    assert symbols == ("NAS100",) and (start, end) == (date(2020, 3, 2), date(2020, 3, 3))
    assert isinstance(settings.strategy, GapMomentumConfig)
    out = tmp_path / "out" / "gap_momentum"
    with (out / "cells.csv").open(encoding="utf-8") as f:
        cells = list(csv.DictReader(f))
    assert [c["bars"] for c in cells] == ["1", "2", "3", "5", "10", "20"]
    assert cells[0]["variant"] == "default" and cells[0]["trades"] == "2"
    # bar = 1 minute (strategy 7 runs on M1); 20 bars -> 14:40 -> price 101 -> +0.5 R for the long
    last = cells[-1]
    assert float(last["mean_gross"]) == pytest.approx(0.5)
    assert float(cells[0]["mean_gross"]) == 0.0
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["strategy"] == "gap_momentum" and summary["verdict"]["passed"] is False
    assert summary["variants"][0]["trades"] == 2 and summary["cache_dir"] == str(cache)
    text = (out / "summary.txt").read_text(encoding="utf-8")
    assert "FAIL" in text and "gap_momentum" in text
    for name in ("tests.csv", "hit_scan.csv"):
        assert (out / name).exists()
    logged = trial_log.family_trials("screen_gap_momentum")
    assert len(logged) == 1 and logged[0].trades == 2 and logged[0].net_r == pytest.approx(-0.5)


def test_an_end_after_the_cut_off_is_refused_unless_the_test_period_is_allowed(
    tmp_path, monkeypatch
):
    seen = []
    monkeypatch.setattr(entry_screen, "run_backtests", fake_run_factory(seen))
    cache = cache_with_two_days(tmp_path)
    base = args_for(tmp_path, cache)
    base[base.index("--end") + 1] = "2021-09-14"
    with pytest.raises(SystemExit, match="2021-09-13"):
        entry_screen.main(base)
    assert seen == [] and DEV_END == date(2021, 9, 13)


def test_several_variants_are_pooled_and_each_logged(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(entry_screen, "run_backtests", fake_run_factory(seen))
    cache = cache_with_two_days(tmp_path)
    assert entry_screen.main(args_for(tmp_path, cache, "--set", "entry_z=0,0.5")) == 0
    assert [s[3].strategy.entry_z for s in seen] == [0.0, 0.5]
    summary = json.loads((tmp_path / "out" / "gap_momentum" / "summary.json").read_text("utf-8"))
    assert summary["verdict"]["cells"] == 12 and len(summary["variants"]) == 2
    assert len(trial_log.family_trials("screen_gap_momentum")) == 2
