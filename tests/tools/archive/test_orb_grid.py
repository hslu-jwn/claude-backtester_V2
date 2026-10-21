"""Strategy 6 grid tool: variants (base, filters, volume A/B), market classes, volume pairs,
configurable halves, CLI and output files with a stubbed backtest.
Spec: strategy-opening-range.md > Data and test (ROADMAP 11.10)."""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.core.models import Direction
from backtester.strategy.opening_range.config import EntryMode, NarrowDay, OpeningRangeConfig
from backtester.tools import grid_common
from backtester.tools.archive import orb_grid
from backtester.tools.archive.orb_grid import (
    family_key,
    half_labels,
    market_class,
    variant_name,
    variants,
    volume_pairs,
)

real_segments = orb_grid.segments


@pytest.fixture(autouse=True)
def no_real_data(monkeypatch):
    monkeypatch.setattr(grid_common, "segments", lambda symbol, start, end, sources: [(start, end)])
    monkeypatch.setattr(orb_grid, "load_shocks", lambda *a, **k: ({}, ""))
    monkeypatch.setattr(
        orb_grid, "last_cached_day", lambda symbols, sources=None: date(2021, 9, 13)
    )


def trade(symbol="NAS100", year=2016, r_gross=1.0, r_net=0.9, session="new_york"):
    entry = datetime(year, 3, 1, 14, 30, tzinfo=UTC)
    return SimpleNamespace(
        symbol=symbol, direction=Direction.BULLISH, entry_time=entry,
        exit_time=entry + timedelta(hours=2), r_gross=r_gross, r_net=r_net,
        swap_r=0.0, planned_r=None, reason=f"opening range range {session}",
    )  # fmt: skip


def fake_run_factory(seen):
    def fake_run(symbols, start, end, settings, *args, **kwargs):
        seen.append((tuple(symbols), start, end, settings))
        assert kwargs.get("workers") == 1
        runs = {
            s: SimpleNamespace(
                trades=(trade(s, 2016, 1.0, 1.0), trade(s, 2020, 0.5, -0.5, "london"))
            )
            for s in symbols
        }
        return SimpleNamespace(trades=tuple(t for r in runs.values() for t in r.trades), runs=runs)

    return fake_run


def test_base_grid_is_18_plus_5_filter_variants_all_distinct():
    configs = variants()
    names = [variant_name(c) for c in configs]
    assert len(configs) == len(set(names)) == 23
    base = configs[:18]
    assert {c.target_r for c in base} == {0.0, 1.0, 2.0}
    assert {c.range_minutes for c in base if c.entry_mode is EntryMode.RANGE} == {5, 15, 30}
    assert {c.band_atr for c in base if c.entry_mode is EntryMode.BAND} == {0.25, 0.5, 1.0}
    assert sum(c.entry_mode is EntryMode.BAND for c in base) == 9
    assert OpeningRangeConfig() in configs


def test_filter_variants_are_on_the_spec_default_entry_only():
    filters = variants()[18:]
    assert {c.max_range_atr for c in filters} == {0.0, 0.15, 0.3}
    assert {c.narrow_day_filter for c in filters} == {
        NarrowDay.OFF, NarrowDay.NR4, NarrowDay.INSIDE,
    }  # fmt: skip
    assert {c.max_reversals for c in filters} == {0, 1}
    fields = ("max_range_atr", "narrow_day_filter", "max_reversals", "target_r",
              "range_minutes", "entry_mode", "min_rel_volume")  # fmt: skip
    d = OpeningRangeConfig()
    for c in filters:  # each differs from the default in exactly one field
        assert len([f for f in fields if getattr(c, f) != getattr(d, f)]) == 1, c


def test_volume_adds_the_18_base_variants_with_min_rel_volume_1_5():
    configs = variants(volume=True)
    assert len(configs) == 41 and len({variant_name(c) for c in configs}) == 41
    vol = [c for c in configs if c.min_rel_volume > 0]
    assert len(vol) == 18 and {c.min_rel_volume for c in vol} == {1.5}
    assert variants(volume=False) == configs[:23]


def test_no_filters_and_no_sweep():
    assert len(variants(filters=False)) == 18
    assert len(variants(volume=True, filters=False)) == 36
    assert variants(sweep=False) == [OpeningRangeConfig()]


def test_names_and_families():
    assert variant_name(OpeningRangeConfig()) == "range 15m T0"
    band = OpeningRangeConfig(entry_mode=EntryMode.BAND, band_atr=0.25, target_r=2.0)
    assert variant_name(band) == "band 0.25atr T2"
    assert variant_name(OpeningRangeConfig(max_range_atr=0.3)) == "range 15m T0 maxrange0.3"
    assert variant_name(OpeningRangeConfig(narrow_day_filter=NarrowDay.NR4)) == "range 15m T0 nr4"
    assert variant_name(OpeningRangeConfig(max_reversals=1)) == "range 15m T0 reversal1"
    assert variant_name(OpeningRangeConfig(min_rel_volume=1.5)) == "range 15m T0 vol1.5"
    assert family_key(OpeningRangeConfig(range_minutes=30, target_r=1.0)) == ("range T1", 30)
    assert family_key(band) == ("band T2", 0.25)
    assert family_key(OpeningRangeConfig(min_rel_volume=1.5))[0] == "range T0 vol1.5"
    # a filter variant is its own family (no plateau across different filters)
    assert family_key(OpeningRangeConfig(narrow_day_filter=NarrowDay.NR4))[0] == "filters"


def test_market_classes():
    assert market_class("US2000", None) == "US indices"
    assert market_class("NAS100", "new_york") == "US indices"
    for s in ("GER40", "EU50", "UK100", "JP225"):
        assert market_class(s, "frankfurt") == "EU/UK/JP indices"
    assert market_class("EURUSD", "london") == "FX London"
    assert market_class("USDJPY", "new_york") == "FX New York"
    assert market_class("XAUUSD", "london") == "Metals London"
    assert market_class("XAGUSD", "new_york") == "Metals NY"
    assert market_class("EURUSD", None) is None  # a trade of unknown session is in no class
    assert market_class("BTCUSD", "london") is None


def test_half_labels_follow_the_configured_split_year():
    assert half_labels(date(2015, 1, 1), date(2021, 9, 13), 2018) == ("2015-2018", "2019-2021")
    assert half_labels(date(2020, 1, 1), date(2026, 9, 30), 2022) == ("2020-2022", "2023-2026")


def test_volume_pairs_compare_each_base_variant_with_its_volume_twin():
    def row(variant, trades, net):
        return {"variant": variant, "symbol": "ALL", "trades": trades, "sum_r_net": net}

    summary = [
        row("range 5m T0", 100, -10.0), row("range 5m T0 vol1.5", 40, 4.0),
        row("range 15m T0", 100, 5.0), row("range 15m T0 vol1.5", 50, -5.0),
        row("range 30m T0", 10, 1.0),  # no twin: ignored
        row("range 15m T0 nr4", 10, 1.0),  # a filter variant is not a twin
    ]  # fmt: skip
    pairs = volume_pairs(summary)
    assert [p["variant"] for p in pairs] == ["range 5m T0", "range 15m T0"]
    p = pairs[0]
    assert p["net_per_trade"] == pytest.approx(-0.1)
    assert p["net_per_trade_vol"] == pytest.approx(0.1)
    assert p["delta_net_per_trade"] == pytest.approx(0.2) and p["improved"] is True
    assert pairs[1]["improved"] is False
    assert volume_pairs([row("range 5m T0", 0, 0.0), row("range 5m T0 vol1.5", 0, 0.0)]) == []


def test_cli_defaults_and_custom_values():
    args = orb_grid.parse_args([])
    assert args.start == date(2015, 1, 1) and args.first_half_end_year == 2022
    assert args.workers == 1 and args.source == "histdata" and not args.volume
    assert "XAUUSD" in args.symbols and "JP225" in args.symbols
    args = orb_grid.parse_args(
        ["--first-half-end-year", "2018", "--volume", "--no-filters", "--symbols", "eurusd"]
    )
    assert args.first_half_end_year == 2018 and args.volume and args.no_filters
    assert args.symbols == ["eurusd"]


def test_smoke_run_writes_all_files_with_symbol_class_and_configured_halves(
    tmp_path, monkeypatch, capsys
):
    seen = []
    monkeypatch.setattr(grid_common, "run_backtests", fake_run_factory(seen))
    out = tmp_path / "o"
    argv = ["--no-sweep", "--symbols", "NAS100", "EURUSD", "--first-half-end-year", "2018",
            "--start", "2015-01-01", "--out", str(out)]  # fmt: skip
    assert orb_grid.main(argv) == 0
    assert len(seen) == 1 and seen[0][2] == date(2021, 9, 13)
    assert seen[0][3].engine.costs.spread_table is None
    assert isinstance(seen[0][3].strategy, OpeningRangeConfig)
    for name in ("summary.csv", "split.csv", "robustness.csv", "grid.csv", "classes.csv"):
        with (out / name).open(encoding="utf-8") as f:
            assert list(csv.DictReader(f)), name
    with (out / "summary.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert {r["symbol"] for r in rows} == {"ALL", "NAS100", "EURUSD"}
    assert {"swap_r", "net_r_per_trade", "win_rate"} <= set(rows[0])
    with (out / "split.csv").open(encoding="utf-8") as f:
        split = list(csv.DictReader(f))
    assert {r["half"] for r in split} == {"2015-2018", "2019-2021"}
    all_rows = {r["half"]: r for r in split if r["symbol"] == "ALL"}
    assert float(all_rows["2015-2018"]["sum_r_net"]) == pytest.approx(2.0)  # 1 trade per symbol
    assert float(all_rows["2019-2021"]["sum_r_net"]) == pytest.approx(-1.0)
    with (out / "robustness.csv").open(encoding="utf-8") as f:
        rob = next(r for r in csv.DictReader(f) if r["symbol"] == "ALL")
    assert rob["half_first_trades"] == "2" and rob["half_second_trades"] == "2"
    with (out / "classes.csv").open(encoding="utf-8") as f:
        classes = {r["market_class"]: r for r in csv.DictReader(f)}
    # NAS100 trades of any session text count as US indices; EURUSD splits
    assert {"US indices", "FX London", "FX New York"} == set(classes)
    assert classes["US indices"]["trades"] == "2"
    assert classes["FX London"]["trades"] == "1" and classes["FX New York"]["trades"] == "1"
    assert "net_r_without_best" in classes["FX London"]
    assert "half_first_net_r" in classes["FX London"]
    assert "profit" in capsys.readouterr().out.lower()


def test_default_output_folder_depends_on_cost_mode_and_source(tmp_path, monkeypatch):
    monkeypatch.setattr(grid_common, "run_backtests", fake_run_factory([]))
    monkeypatch.setattr(orb_grid, "RESULTS_DIR", tmp_path)
    assert orb_grid.main(["--no-sweep", "--symbols", "NAS100"]) == 0
    assert (tmp_path / "orb" / "fixed" / "summary.csv").exists()
    assert orb_grid.main(["--no-sweep", "--symbols", "NAS100", "--source", "mt5"]) == 0
    assert (tmp_path / "orb_mt5" / "fixed" / "summary.csv").exists()


def test_full_sweep_with_volume_runs_41_variants_and_writes_ab(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(grid_common, "run_backtests", fake_run_factory(seen))
    assert orb_grid.main(["--volume", "--symbols", "NAS100", "--out", str(tmp_path)]) == 0
    assert len(seen) == 41
    with (tmp_path / "ab_volume.csv").open(encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 18
    with (tmp_path / "grid.csv").open(encoding="utf-8") as f:
        assert "ALL VARIANTS" in {r["family"] for r in csv.DictReader(f)}


def test_source_option_reads_the_mt5_cache(tmp_path, monkeypatch):
    from backtester.data.cache import MT5_CACHE_DIR
    from backtester.data.sources import DEFAULT_SOURCES

    used = []

    def fake_run(symbols, start, end, settings, *args, **kwargs):
        used.append(kwargs.get("sources", DEFAULT_SOURCES))
        return SimpleNamespace(trades=(), runs={s: SimpleNamespace(trades=()) for s in symbols})

    monkeypatch.setattr(grid_common, "run_backtests", fake_run)
    monkeypatch.setattr(orb_grid, "RESULTS_DIR", tmp_path)
    assert orb_grid.main(["--no-sweep", "--symbols", "US30"]) == 0
    assert used[-1] is DEFAULT_SOURCES
    assert orb_grid.main(["--no-sweep", "--symbols", "US30", "--source", "mt5"]) == 0
    assert used[-1].cache_dir("US30") == MT5_CACHE_DIR


class FakeSources:
    def __init__(self, days):
        self.days = days

    def cached_days(self, symbol):
        return self.days[symbol]


def days(a, b):
    return [a + timedelta(i) for i in range((b - a).days + 1)]


def test_segments_split_at_a_missing_cached_day_and_clip_to_the_range():
    cached = days(date(2020, 12, 20), date(2020, 12, 31)) + days(
        date(2021, 1, 2), date(2021, 1, 20)
    )
    src = FakeSources({"A": cached, "B": days(date(2021, 1, 2), date(2021, 1, 20))})
    assert real_segments("A", date(2020, 12, 1), date(2021, 1, 10), src) == [
        (date(2020, 12, 20), date(2020, 12, 31)),
        (date(2021, 1, 2), date(2021, 1, 10)),
    ]
    assert real_segments("B", date(2020, 1, 1), date(2021, 2, 1), src) == [
        (date(2021, 1, 2), date(2021, 1, 20))
    ]
    assert real_segments("B", date(2022, 1, 1), date(2022, 2, 1), src) == []


def test_run_variant_runs_each_distinct_segment_and_merges_the_trades(monkeypatch):
    src = FakeSources(
        {
            "A": days(date(2020, 1, 1), date(2020, 1, 10))
            + days(date(2020, 1, 12), date(2020, 1, 20)),
            "B": days(date(2020, 1, 1), date(2020, 1, 20)),
        }
    )
    calls = []

    def fake_run(symbols, start, end, settings, *args, **kwargs):
        calls.append((tuple(symbols), start, end))
        runs = {s: SimpleNamespace(trades=(trade(s, 2020, r_net=start.day),)) for s in symbols}
        return SimpleNamespace(trades=tuple(t for r in runs.values() for t in r.trades), runs=runs)

    monkeypatch.setattr(grid_common, "run_backtests", fake_run)
    monkeypatch.setattr(grid_common, "segments", real_segments)
    result = orb_grid.run_variant(
        ["A", "B"], date(2020, 1, 1), date(2020, 1, 20), RunSettingsStub(), src, 1
    )
    assert sorted(calls) == [
        (("A",), date(2020, 1, 1), date(2020, 1, 10)),
        (("A",), date(2020, 1, 12), date(2020, 1, 20)),
        (("B",), date(2020, 1, 1), date(2020, 1, 20)),
    ]
    assert len(result.runs["A"].trades) == 2 and len(result.runs["B"].trades) == 1
    assert len(result.trades) == 3
    assert result.runs["A"].trades[0].r_net == 1 and result.runs["A"].trades[1].r_net == 12


def RunSettingsStub():
    return SimpleNamespace()


def test_part_runs_every_nth_variant_and_merge_rebuilds_grid_and_ab(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(grid_common, "run_backtests", fake_run_factory(seen))
    for k in (1, 2, 3):
        argv = [
            "--volume",
            "--symbols",
            "NAS100",
            "--part",
            f"{k}/3",
            "--out",
            str(tmp_path / f"p{k}"),
        ]
        assert orb_grid.main(argv) == 0
    assert len(seen) == 41
    with (tmp_path / "p1" / "summary.csv").open(encoding="utf-8") as f:
        first = {r["variant"] for r in csv.DictReader(f)}
    assert len(first) == 14  # variants[0::3] of 41
    merged = tmp_path / "m"
    argv = ["--merge", str(tmp_path / "p1"), str(tmp_path / "p2"), str(tmp_path / "p3"),
            "--out", str(merged), "--first-half-end-year", "2018"]  # fmt: skip
    assert orb_grid.main(argv) == 0
    for name in ("summary.csv", "split.csv", "robustness.csv", "classes.csv"):
        with (merged / name).open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert {r["variant"] for r in rows} == {variant_name(c) for c in variants(volume=True)}
    with (merged / "grid.csv").open(encoding="utf-8") as f:
        grid = {r["family"]: r for r in csv.DictReader(f)}
    assert grid["ALL VARIANTS"]["n"] == "41" and "filters" in grid
    with (merged / "ab_volume.csv").open(encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 18


def test_part_argument_is_validated():
    with pytest.raises(SystemExit):
        orb_grid.parse_args(["--part", "0/3"])
    with pytest.raises(SystemExit):
        orb_grid.parse_args(["--part", "4/3"])
    assert orb_grid.parse_args(["--part", "2/4"]).part == (2, 4)


def test_variants_option_runs_only_the_named_variants_without_other_flags(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(grid_common, "run_backtests", fake_run_factory(seen))
    names = ["band 0.5atr T0 vol1.5", "band 0.25atr T0 vol1.5"]
    argv = ["--variants", *names, "--symbols", "NAS100", "--out", str(tmp_path)]
    assert orb_grid.main(argv) == 0
    assert [(s[3].strategy.band_atr, s[3].strategy.min_rel_volume) for s in seen] == [
        (0.5, 1.5), (0.25, 1.5),
    ]  # fmt: skip
    with (tmp_path / "summary.csv").open(encoding="utf-8") as f:
        assert {r["variant"] for r in csv.DictReader(f)} == set(names)


def test_variants_option_rejects_an_unknown_name_and_lists_the_valid_ones(capsys):
    with pytest.raises(SystemExit):
        orb_grid.parse_args(["--variants", "band 9atr T0"])
    err = capsys.readouterr().err
    assert "band 9atr T0" in err
    assert "band 0.25atr T0 vol1.5" in err and "range 15m T0" in err
