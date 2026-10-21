"""Strategy 5 grid tool: variants (gap bucket x stop multiple x exit time), CLI and output
files with a stubbed backtest. Spec: strategy-gap-fade.md > Backtest options (ROADMAP 11.4)."""

from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from backtester.core.models import Direction
from backtester.strategy.gap_fade.config import GapFadeConfig
from backtester.tools.archive import gap_fade_grid
from backtester.tools.archive.gap_fade_grid import family_key, variant_name, variants


@pytest.fixture(autouse=True)
def no_real_data(monkeypatch):
    monkeypatch.setattr(gap_fade_grid, "load_shocks", lambda *a, **k: ({}, ""))
    monkeypatch.setattr(
        gap_fade_grid, "last_cached_day", lambda symbols, sources=None: date(2026, 9, 30)
    )


def trade(symbol="NAS100", year=2021, r_gross=1.0, r_net=0.9, swap_r=0.0):
    entry = datetime(year, 3, 1, 14, 30, tzinfo=UTC)
    return SimpleNamespace(
        symbol=symbol, direction=Direction.BULLISH, entry_time=entry,
        exit_time=entry + timedelta(hours=2), r_gross=r_gross, r_net=r_net,
        swap_r=swap_r, planned_r=None,
    )  # fmt: skip


def fake_run_factory(seen):
    def fake_run(symbols, start, end, settings, *args, **kwargs):
        seen.append((tuple(symbols), start, end, settings))
        assert kwargs.get("workers") == 1
        trades = (trade(year=2021, r_net=1.0), trade(year=2024, r_net=-0.5))
        return SimpleNamespace(
            trades=trades, runs={s: SimpleNamespace(trades=trades) for s in symbols}
        )

    return fake_run


def test_default_grid_is_36_variants_and_contains_the_spec_default():
    configs = variants()
    names = [variant_name(c) for c in configs]
    assert len(configs) == len(set(names)) == 36
    assert GapFadeConfig() in configs
    assert {(c.min_gap_atr, c.max_gap_atr) for c in configs} == {
        (0.1, 0.25), (0.25, 0.5), (0.5, 1.0), (0.1, 1.0),
    }  # fmt: skip
    assert {c.stop_gap_mult for c in configs} == {0.75, 1.0, 1.5}
    assert {c.exit_time for c in configs} == {time(11), time(12), time(16)}


def test_without_sweep_only_the_spec_default():
    assert variants(sweep=False) == [GapFadeConfig()]


def test_names_and_families():
    cfg = GapFadeConfig(min_gap_atr=0.25, max_gap_atr=0.5, stop_gap_mult=0.75, exit_time=time(11))
    assert variant_name(cfg) == "gap 0.25-0.5 stop 0.75 exit 11:00"
    assert family_key(cfg) == ("gap 0.25-0.5 stop 0.75", 11 * 60)
    assert family_key(GapFadeConfig()) == ("gap 0.1-1 stop 1", 16 * 60)


def test_cli_parsing_defaults_and_custom_values():
    args = gap_fade_grid.parse_args([])
    assert args.symbols == ["NAS100", "US500"] and args.start == date(2020, 1, 1)
    assert args.spread_table is None and args.out is None and not args.no_sweep
    args = gap_fade_grid.parse_args(
        ["--buckets", "0.1-0.3", "--stop-mults", "2", "--exit-times", "10:30", "--no-shocks"]
    )
    assert args.buckets == [(0.1, 0.3)] and args.stop_mults == [2.0]
    assert args.exit_times == [time(10, 30)]


def test_smoke_run_writes_all_four_files_and_defaults_end_to_cache(tmp_path, monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(gap_fade_grid, "run_backtests", fake_run_factory(seen))
    out = tmp_path / "o"
    assert gap_fade_grid.main(["--no-sweep", "--out", str(out)]) == 0
    assert len(seen) == 1 and seen[0][2] == date(2026, 9, 30)
    assert seen[0][3].engine.costs.spread_table is None
    assert isinstance(seen[0][3].strategy, GapFadeConfig)
    for name in ("summary.csv", "split.csv", "robustness.csv", "grid.csv"):
        with (out / name).open(encoding="utf-8") as f:
            assert list(csv.DictReader(f)), name
    with (out / "summary.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert {r["symbol"] for r in rows} == {"ALL", "NAS100", "US500"}
    assert "swap_r" in rows[0] and "net_r_per_trade" in rows[0] and "win_rate" in rows[0]
    assert "profit" in capsys.readouterr().out.lower()


def test_default_output_folder_depends_on_the_cost_mode(tmp_path, monkeypatch):
    monkeypatch.setattr(gap_fade_grid, "run_backtests", fake_run_factory([]))
    monkeypatch.setattr(gap_fade_grid, "RESULTS_DIR", tmp_path)
    f = tmp_path / "s.json"
    from backtester.engine.spread_table import SpreadTable

    table = SpreadTable(values={"NAS100": {2026: {9: 1.0}}}, stat="median", note="t")
    f.write_text(json.dumps(table.to_dict()), encoding="utf-8")
    assert gap_fade_grid.main(["--no-sweep"]) == 0
    assert (tmp_path / "gap_fade" / "fixed" / "summary.csv").exists()
    seen = []
    monkeypatch.setattr(gap_fade_grid, "run_backtests", fake_run_factory(seen))
    assert gap_fade_grid.main(["--no-sweep", "--spread-table", str(f)]) == 0
    assert (tmp_path / "gap_fade" / "table" / "summary.csv").exists()
    assert seen[0][3].engine.costs.spread_table == table


def test_full_sweep_runs_36_variants(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(gap_fade_grid, "run_backtests", fake_run_factory(seen))
    assert gap_fade_grid.main(["--out", str(tmp_path)]) == 0
    assert len(seen) == 36
    with (tmp_path / "grid.csv").open(encoding="utf-8") as f:
        assert "ALL VARIANTS" in {r["family"] for r in csv.DictReader(f)}


def test_source_option_reads_the_mt5_cache_and_histdata_stays_the_default(tmp_path, monkeypatch):
    from backtester.data.cache import MT5_CACHE_DIR
    from backtester.data.sources import DEFAULT_SOURCES

    sources_seen, shock_sources = [], []

    def fake_run(symbols, start, end, settings, *args, **kwargs):
        sources_seen.append(kwargs.get("sources", DEFAULT_SOURCES))
        return SimpleNamespace(trades=(), runs={s: SimpleNamespace(trades=()) for s in symbols})

    def fake_shocks(symbols, start, end, config=None, sources=DEFAULT_SOURCES):
        shock_sources.append(sources)
        return {}, ""

    monkeypatch.setattr(gap_fade_grid, "run_backtests", fake_run)
    monkeypatch.setattr(gap_fade_grid, "load_shocks", fake_shocks)
    monkeypatch.setattr(gap_fade_grid, "RESULTS_DIR", tmp_path)
    assert gap_fade_grid.parse_args([]).source == "histdata"
    assert gap_fade_grid.main(["--no-sweep"]) == 0
    assert sources_seen[-1] is DEFAULT_SOURCES and shock_sources[-1] is DEFAULT_SOURCES
    assert (tmp_path / "gap_fade" / "fixed" / "summary.csv").exists()
    assert gap_fade_grid.main(["--no-sweep", "--source", "mt5"]) == 0
    for used in (sources_seen[-1], shock_sources[-1]):
        assert used.cache_dir("NAS100") == used.cache_dir("US500") == MT5_CACHE_DIR
    assert (tmp_path / "gap_fade_mt5" / "fixed" / "summary.csv").exists()  # not over histdata's


def test_every_variant_is_logged_once_with_family_default_and_override(tmp_path, monkeypatch):
    from backtester.analytics.trial_log import family_trials

    monkeypatch.setattr(gap_fade_grid, "run_backtests", fake_run_factory([]))
    assert gap_fade_grid.main(["--out", str(tmp_path)]) == 0
    lines = family_trials("gap_fade")
    assert len(lines) == 36 and {r.strategy for r in lines} == {"gap_fade"}
    assert all(r.symbols == ["NAS100", "US500"] and r.trades == 2 for r in lines)
    assert len({r.key for r in lines}) == 36
    assert gap_fade_grid.main(["--out", str(tmp_path), "--no-sweep", "--family", "x"]) == 0
    assert len(family_trials("x")) == 1 and len(family_trials("gap_fade")) == 36
    gap_fade_grid.main(["--out", str(tmp_path), "--no-sweep", "--family", "x"])  # rerun
    assert len(family_trials("x")) == 1


def test_family_option_parses():
    assert gap_fade_grid.parse_args([]).family is None
    assert gap_fade_grid.parse_args(["--family", "f"]).family == "f"
