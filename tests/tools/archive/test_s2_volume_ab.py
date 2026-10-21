"""Strategy 2 volume A/B tool: the two variants, CLI and output files with a stubbed backtest.
Spec: strategy-ny-indices.md > Volume filter (ROADMAP 11.12)."""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.core.models import Direction
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.tools.archive import s2_volume_ab


@pytest.fixture(autouse=True)
def no_real_data(monkeypatch):
    monkeypatch.setattr(s2_volume_ab, "load_shocks", lambda *a, **k: ({}, ""))
    monkeypatch.setattr(
        s2_volume_ab, "last_cached_day", lambda symbols, sources=None: date(2026, 9, 30)
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
        seen.append((tuple(symbols), start, end, settings, kwargs))
        n = 2 if settings.strategy.min_rel_volume == 0 else 1
        trades = tuple(trade(year=2021 + i, r_net=1.0 - i) for i in range(n))
        return SimpleNamespace(
            trades=trades, runs={s: SimpleNamespace(trades=trades) for s in symbols}
        )

    return fake_run


def test_variants_are_spec_defaults_and_the_volume_filter():
    configs = s2_volume_ab.variants(1.5, 20)
    assert [n for n, _ in configs] == ["spec defaults", "volume >= 1.5 x usual"]
    base, vol = (c for _, c in configs)
    assert base == NyIndexSweepConfig()
    assert vol == NyIndexSweepConfig(min_rel_volume=1.5, volume_lookback=20)


def test_cli_defaults():
    args = s2_volume_ab.parse_args([])
    assert args.symbols == ["NAS100", "US500"] and args.start == date(2020, 1, 1)
    assert args.min_rel_volume == 1.5 and args.volume_lookback == 20
    assert args.source == "histdata" and args.out is None


def test_smoke_run_writes_files_runs_both_variants_and_prints_the_ab_table(
    tmp_path, monkeypatch, capsys
):
    seen = []
    monkeypatch.setattr(s2_volume_ab, "run_backtests", fake_run_factory(seen))
    out = tmp_path / "o"
    assert s2_volume_ab.main(["--out", str(out)]) == 0
    assert [s[3].strategy.min_rel_volume for s in seen] == [0.0, 1.5]
    assert all(s[2] == date(2026, 9, 30) and s[4]["workers"] == 1 for s in seen)
    for name in ("summary.csv", "split.csv", "robustness.csv", "ab.csv"):
        with (out / name).open(encoding="utf-8") as f:
            assert list(csv.DictReader(f)), name
    with (out / "ab.csv").open(encoding="utf-8") as f:
        rows = {r["variant"]: r for r in csv.DictReader(f)}
    assert rows["spec defaults"]["trades"] == "2" and rows["volume >= 1.5 x usual"]["trades"] == "1"
    assert (
        "net_r_per_trade" in rows["spec defaults"] and "half_2020-22_net" in rows["spec defaults"]
    )
    text = capsys.readouterr().out
    assert "spec defaults" in text and "volume >= 1.5 x usual" in text


def test_symbols_outside_the_spec_are_labelled_as_a_backtest_only_extension(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(s2_volume_ab, "run_backtests", fake_run_factory([]))
    assert s2_volume_ab.main(["--symbols", "US30", "US2000", "--out", str(tmp_path)]) == 0
    assert "backtest-only extension" in capsys.readouterr().out
    assert s2_volume_ab.main(["--out", str(tmp_path)]) == 0
    assert "backtest-only extension" not in capsys.readouterr().out


def test_source_mt5_reads_the_mt5_cache_and_names_the_default_folder(tmp_path, monkeypatch):
    from backtester.data.cache import MT5_CACHE_DIR

    seen = []
    monkeypatch.setattr(s2_volume_ab, "run_backtests", fake_run_factory(seen))
    monkeypatch.setattr(s2_volume_ab, "RESULTS_DIR", tmp_path)
    assert s2_volume_ab.main(["--source", "mt5"]) == 0
    assert (tmp_path / "s2_volume_ab_mt5" / "ab.csv").exists()
    assert seen[0][4]["sources"].cache_dir("NAS100") == MT5_CACHE_DIR


def test_doji_thresholds_for_symbols_without_one_use_the_gold_rule_on_their_median_m5_range():
    import pandas as pd

    from backtester.detectors.swings import SwingConfig, equivalent_doji_body

    class Adapter:
        def fetch_frame(self, symbol, tf, start, end):
            return pd.DataFrame({"high": [11.0, 14.0, 13.0], "low": [10.0, 10.0, 10.0]})  # 1, 4, 3

    sources = SimpleNamespace(adapter=lambda symbol: Adapter())
    base = SwingConfig()
    cfg = s2_volume_ab.swing_config_for(
        ["NAS100", "FOOBAR"], date(2020, 1, 2), date(2021, 9, 13), sources, base
    )
    assert cfg.doji_max_body["FOOBAR"] == pytest.approx(equivalent_doji_body(3.0))
    assert cfg.doji_max_body["NAS100"] == base.doji_max_body["NAS100"]  # specced: untouched
    assert (
        s2_volume_ab.swing_config_for(
            ["NAS100"], date(2020, 1, 2), date(2021, 9, 13), sources, base
        )
        is base
    )


def test_run_passes_the_doji_thresholds_of_extension_symbols(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(s2_volume_ab, "run_backtests", fake_run_factory(seen))
    monkeypatch.setattr(s2_volume_ab, "swing_config_for", lambda *a, **k: "SWINGS")
    assert s2_volume_ab.main(["--symbols", "US30", "--out", str(tmp_path)]) == 0
    assert all(s[3].detectors.swings == "SWINGS" for s in seen)
