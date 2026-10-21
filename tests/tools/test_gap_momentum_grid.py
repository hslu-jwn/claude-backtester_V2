"""Strategy 7 grid tool: variants (entry_z x stop_atr x exit time per mode), development-period
guard, cost modes, output files, trial log, gap-bucket study; backtest stubbed.
Spec: strategy-gap-momentum.md > Backtest options (ROADMAP 11.12)."""

from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace

import pytest
from m1_frames import m1

from backtester.core.models import Direction
from backtester.data.cache import cache_path
from backtester.strategy.gap_momentum.config import GapMomentumConfig
from backtester.tools import gap_momentum_grid
from backtester.tools.gap_momentum_grid import (
    DEV_END,
    family_key,
    load_session_bars,
    variant_name,
    variants,
)


@pytest.fixture(autouse=True)
def no_real_data(monkeypatch):
    monkeypatch.setattr(gap_momentum_grid, "load_shocks", lambda *a, **k: ({}, ""))
    monkeypatch.setattr(gap_momentum_grid, "study_rows", lambda *a, **k: [{"symbol": "x", "n": 1}])
    monkeypatch.setattr(gap_momentum_grid, "data_start", lambda symbols, sources, start: start)


def trade(symbol="NAS100", year=2017, r_gross=1.0, r_net=0.9, swap_r=0.0, month=3):
    entry = datetime(year, month, 1, 14, 30, tzinfo=UTC)
    return SimpleNamespace(
        symbol=symbol, direction=Direction.BULLISH, entry_time=entry,
        exit_time=entry + timedelta(hours=2), r_gross=r_gross, r_net=r_net,
        swap_r=swap_r, planned_r=None,
    )  # fmt: skip


def fake_run_factory(seen):
    def fake_run(symbols, start, end, settings, *args, **kwargs):
        seen.append((tuple(symbols), start, end, settings, kwargs))
        trades = (trade(year=2016, r_net=1.0), trade(year=2020, r_net=-0.5))
        return SimpleNamespace(
            trades=trades, runs={s: SimpleNamespace(trades=trades) for s in symbols}
        )

    return fake_run


def args_for(tmp_path, *extra):
    return ["--out", str(tmp_path), *extra]


# --- variants --------------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["index", "fx"])
def test_default_grid_is_36_variants_per_mode_and_contains_the_spec_default(mode):
    configs = variants(mode)
    names = [variant_name(c) for c in configs]
    assert len(configs) == len(set(names)) == 36
    assert {c.entry_z for c in configs} == {0.0, 0.1, 0.25, 0.5}
    assert {c.stop_atr for c in configs} == {0.5, 1.0, 2.0}
    assert {c.mode for c in configs} == {mode}
    assert (
        GapMomentumConfig(mode=mode, exit_time=GapMomentumConfig(mode=mode).exit_time_resolved)
        in configs
    )


def test_exit_times_per_mode():
    assert {c.exit_time for c in variants("index")} == {time(11), time(12), time(15, 59)}
    assert {c.exit_time for c in variants("fx")} == {time(8), time(11), time(16, 59)}


def test_without_sweep_only_the_spec_default():
    assert variants("index", sweep=False) == [GapMomentumConfig()]
    assert variants("fx", sweep=False) == [GapMomentumConfig(mode="fx")]


def test_names_and_families():
    cfg = GapMomentumConfig(entry_z=0.25, stop_atr=2.0, exit_time=time(11))
    assert variant_name(cfg) == "z 0.25 stop 2 exit 11:00"
    assert family_key(cfg) == ("stop 2 exit 11:00", 0.25)
    assert variant_name(GapMomentumConfig()) == "z 0.1 stop 1 exit 15:59"


# --- command line --------------------------------------------------------------------------------


def test_cli_defaults_are_the_development_period_and_the_symbols_of_the_mode():
    args = gap_momentum_grid.parse_args([])
    assert args.mode == "index" and args.start == date(2015, 1, 1) and args.end == DEV_END
    assert DEV_END == date(2021, 9, 13)
    assert gap_momentum_grid.symbols_for(args) == ["NAS100", "US500"]
    fx = gap_momentum_grid.parse_args(["--mode", "fx"])
    assert gap_momentum_grid.symbols_for(fx) == ["GBPUSD", "EURUSD", "XAUUSD"]
    custom = gap_momentum_grid.parse_args(["--symbols", "xauusd"])
    assert gap_momentum_grid.symbols_for(custom) == ["XAUUSD"]


def test_an_end_after_the_cut_off_is_refused_unless_the_test_period_is_allowed(
    tmp_path, monkeypatch
):
    seen = []
    monkeypatch.setattr(gap_momentum_grid, "run_backtests", fake_run_factory(seen))
    with pytest.raises(SystemExit, match="2021-09-13"):
        gap_momentum_grid.main(args_for(tmp_path, "--no-sweep", "--end", "2021-09-14"))
    assert seen == []
    assert (
        gap_momentum_grid.main(
            args_for(tmp_path, "--no-sweep", "--end", "2021-09-14", "--allow-test-period")
        )
        == 0
    )
    assert seen[0][2] == date(2021, 9, 14)
    assert gap_momentum_grid.main(args_for(tmp_path, "--no-sweep", "--end", "2021-09-13")) == 0


# --- runs and outputs ----------------------------------------------------------------------


def test_smoke_run_writes_all_files_with_the_spec_default_and_fixed_spread(
    tmp_path, monkeypatch, capsys
):
    seen = []
    monkeypatch.setattr(gap_momentum_grid, "run_backtests", fake_run_factory(seen))
    assert gap_momentum_grid.main(args_for(tmp_path, "--no-sweep")) == 0
    assert len(seen) == 1
    symbols, start, end, settings, kwargs = seen[0]
    assert symbols == ("NAS100", "US500") and start == date(2015, 1, 1) and end == DEV_END
    assert settings.engine.costs.spread_table is None and kwargs["workers"] == 1
    assert isinstance(settings.strategy, GapMomentumConfig)
    for name in ("summary.csv", "split.csv", "robustness.csv", "grid.csv", "gap_buckets.csv"):
        with (tmp_path / name).open(encoding="utf-8") as f:
            assert list(csv.DictReader(f)), name
    with (tmp_path / "summary.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert {r["symbol"] for r in rows} == {"ALL", "NAS100", "US500"}
    assert {"swap_r", "net_r_per_trade", "win_rate", "sum_r_gross"} <= set(rows[0])
    assert "profit" in capsys.readouterr().out.lower()


def test_halves_split_at_the_middle_of_the_period(tmp_path, monkeypatch):
    monkeypatch.setattr(gap_momentum_grid, "run_backtests", fake_run_factory([]))
    # 2015-01-01..2021-09-13: middle 2018-05-07; the 2016 trade is in the first half, 2020 in the second
    assert gap_momentum_grid.main(args_for(tmp_path, "--no-sweep")) == 0
    with (tmp_path / "split.csv").open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["symbol"] == "ALL"]
    by_half = {r["half"]: r for r in rows}
    assert (
        float(by_half["first"]["sum_r_net"]) == 1.0
        and float(by_half["second"]["sum_r_net"]) == -0.5
    )
    with (tmp_path / "robustness.csv").open(encoding="utf-8") as f:
        rob = next(r for r in csv.DictReader(f) if r["symbol"] == "ALL")
    assert float(rob["half_first_net_r"]) == 1.0 and float(rob["half_second_net_r"]) == -0.5


def test_cost_mode_decides_the_default_folder_and_reads_the_table(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(gap_momentum_grid, "run_backtests", fake_run_factory(seen))
    monkeypatch.setattr(gap_momentum_grid, "RESULTS_DIR", tmp_path)
    from backtester.engine.spread_table import SpreadTable

    f = tmp_path / "s.json"
    table = SpreadTable(values={"NAS100": {2021: {9: 1.0}}}, stat="median", note="t")
    f.write_text(json.dumps(table.to_dict()), encoding="utf-8")
    assert gap_momentum_grid.main(["--no-sweep"]) == 0
    assert (tmp_path / "gap_momentum" / "index" / "fixed" / "summary.csv").exists()
    assert gap_momentum_grid.main(["--no-sweep", "--spread-table", str(f)]) == 0
    assert (tmp_path / "gap_momentum" / "index" / "table" / "summary.csv").exists()
    assert seen[-1][3].engine.costs.spread_table == table
    assert gap_momentum_grid.main(["--no-sweep", "--mode", "fx"]) == 0
    assert (tmp_path / "gap_momentum" / "fx" / "fixed" / "summary.csv").exists()
    assert seen[-1][0] == ("GBPUSD", "EURUSD", "XAUUSD")
    assert seen[-1][3].strategy.mode == "fx"


def test_cache_dir_is_passed_as_the_source_of_every_symbol(tmp_path, monkeypatch):
    seen, shock_sources = [], []
    monkeypatch.setattr(gap_momentum_grid, "run_backtests", fake_run_factory(seen))
    monkeypatch.setattr(
        gap_momentum_grid,
        "load_shocks",
        lambda s, st, en, cfg=None, sources=None: shock_sources.append(sources) or ({}, ""),
    )
    assert (
        gap_momentum_grid.main(args_for(tmp_path, "--no-sweep", "--cache-dir", str(tmp_path / "c")))
        == 0
    )
    sources = seen[0][4]["sources"]
    assert sources.cache_dir("NAS100") == sources.cache_dir("US500") == tmp_path / "c"
    assert shock_sources[0] is sources


def test_full_sweep_runs_36_variants_and_the_grid_has_the_all_row(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(gap_momentum_grid, "run_backtests", fake_run_factory(seen))
    assert gap_momentum_grid.main(args_for(tmp_path)) == 0
    assert len(seen) == 36
    with (tmp_path / "grid.csv").open(encoding="utf-8") as f:
        assert "ALL VARIANTS" in {r["family"] for r in csv.DictReader(f)}


@pytest.mark.parametrize(
    ("mode", "family"), [("index", "gap_momentum_index"), ("fx", "gap_momentum_fx")]
)
def test_every_variant_is_logged_once_with_the_family_of_its_mode(
    tmp_path, monkeypatch, mode, family
):
    from backtester.analytics.trial_log import family_trials

    monkeypatch.setattr(gap_momentum_grid, "run_backtests", fake_run_factory([]))
    assert gap_momentum_grid.main(args_for(tmp_path, "--mode", mode)) == 0
    lines = family_trials(family)
    assert len(lines) == 36 and {r.strategy for r in lines} == {"gap_momentum"}
    assert len({r.key for r in lines}) == 36 and all(r.trades == 2 for r in lines)
    gap_momentum_grid.main(args_for(tmp_path, "--mode", mode))  # rerun: not new trials
    assert len(family_trials(family)) == 36
    assert gap_momentum_grid.main(args_for(tmp_path, "--no-sweep", "--family", "x")) == 0
    assert len(family_trials("x")) == 1


def test_no_study_flag_skips_the_gap_bucket_file(tmp_path, monkeypatch):
    monkeypatch.setattr(gap_momentum_grid, "run_backtests", fake_run_factory([]))
    assert gap_momentum_grid.main(args_for(tmp_path, "--no-sweep", "--no-study")) == 0
    assert not (tmp_path / "gap_buckets.csv").exists()


# --- the study's candle loader --------------------------------------------------------------------


def test_load_session_bars_reads_the_session_window_in_new_york_time(tmp_path):
    day = date(2026, 1, 12)  # winter: 09:30 ET = 14:30 UTC, 16:00 ET = 21:00 UTC
    frame = m1(
        ("14:28", 100, 101, 99, 100, 1.0, 0.1),  # closes 09:29: before the open
        ("14:29", 100, 101, 99, 100.5, 1.0, 0.1),  # closes 09:30: the open
        ("14:30", 100.5, 102, 100, 101, 1.0, 0.1),
        ("20:59", 101, 103, 100.9, 102, 1.0, 0.1),  # closes 16:00: the session close
        ("21:00", 102, 102.5, 101.5, 102.2, 1.0, 0.1),  # closes 16:01: after
        day=day.isoformat(),
    )
    path = cache_path(tmp_path, "NAS100", day)
    path.parent.mkdir(parents=True)
    frame.to_parquet(path, index=False)
    cfg = GapMomentumConfig()
    bars = load_session_bars("NAS100", tmp_path, day, day, cfg)
    assert [b[0] for b in bars] == [
        datetime(2026, 1, 12, 14, 30, tzinfo=UTC),
        datetime(2026, 1, 12, 14, 31, tzinfo=UTC),
        datetime(2026, 1, 12, 21, 0, tzinfo=UTC),
    ]
    assert bars[0][3] == 100.5 and bars[2] == (bars[2][0], 103.0, 100.9, 102.0)
