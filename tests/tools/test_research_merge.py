"""Spec: research-runner.md, V2.4 grid merge 1.

Test cases (written before implementation):
1. Combined products inherit bases, preserve file IDs, deduplicate resolved defaults.
2. Reject malformed families, mixed forms, bad settings and non-boolean shocks.
3. Sampling caps unique settings, is repeatable, and keeps product IDs.
4. Family statistics include unranked variants; 1D/2D plateaus retain missing cells;
   >2 axes have no plateau; empty and singleton families are valid.
5. Every cached symbol has a class; ORB session classes and generic classes coexist.
6. Daily shock input reads each cached day once; exit date and symbol determine shocks.
7. Chosen breakdowns and shocks cover development/test, survive resume/retest, and
   disabling shocks performs no daily reads. Legacy selection and CSVs stay unchanged.
"""

import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest
from test_research import GRID, read_csv, research_folder, run_research, write_grid
from test_research import fakes as research_fakes

from backtester.tools import research_grid

fakes = research_fakes

COMBINED = """
strategy = "opening_range"
symbols = ["US500", "NAS100"]
sensitivity = false  # these tests count the grid runs only (brief 2)
min_trades = 4
[base]
entry_mode = "range"
[[grids]]
name = "ranges"
[grids.grid]
range_minutes = [5, 15]
[[grids]]
name = "filters"
[grids.base]
range_minutes = 15
[grids.grid]
target_r = [0, 1]
"""


def test_combined_resolved_duplicates_and_ids(tmp_path):
    spec = research_grid.load_grid(write_grid(tmp_path, COMBINED))
    variants, size, sampled = research_grid.expand(spec)
    assert size == 4 and not sampled
    assert [v.id for v in variants] == ["v0000", "v0001", "v0003"]
    assert [v.family for v in variants] == ["ranges", "ranges", "filters"]
    assert research_grid.variant_settings(spec, variants[-1]).strategy.target_r == 1
    # Explicit default and omitted default are the same resolved run settings.
    assert spec.duplicates == [{"id": "v0002", "family": "filters", "retained": "v0001"}]


@pytest.mark.parametrize(
    "change",
    [
        lambda s: s.replace('name = "filters"', 'name = "ranges"'),
        lambda s: s.replace('name = "ranges"', 'name = ""'),
        lambda s: s.replace("[base]", "[grid]\ntarget_r = [0]\n[base]", 1),
        lambda s: s.replace("min_trades = 4", "min_trades = 4\nshocks = 1"),
        lambda s: s.replace("range_minutes = [5, 15]", "bad_setting = [1]"),
        lambda s: s.replace('name = "ranges"', 'name = "ranges"\nunknown = 1'),
        lambda s: s[: s.index("[base]")] + "grids = []\n",
    ],
)
def test_combined_validation(tmp_path, change):
    with pytest.raises(research_grid.GridError):
        research_grid.expand(research_grid.load_grid(write_grid(tmp_path, change(COMBINED))))


def test_sampling_and_diagnostic_option_do_not_change_identity(tmp_path):
    spec = research_grid.load_grid(
        write_grid(tmp_path, COMBINED.replace("min_trades = 4", "min_trades = 4\nmax_variants = 2"))
    )
    variants, size, sampled = research_grid.expand(spec)
    assert size == 4 and sampled and len(variants) == 2
    assert variants == research_grid.expand(spec)[0]
    assert {v.id for v in variants} <= {"v0000", "v0001", "v0003"}
    other = research_grid.load_grid(
        write_grid(
            tmp_path,
            COMBINED.replace("min_trades = 4", "min_trades = 4\nmax_variants = 2\nshocks = false"),
        )
    )
    assert research_grid.grid_id(spec, variants) == research_grid.grid_id(other, variants)


def test_grid_statistics_and_plateaus(tmp_path):
    from backtester.tools.research_diagnostics import grid_rows

    spec = research_grid.load_grid(write_grid(tmp_path, GRID))
    variants, _, _ = research_grid.expand(spec)
    rows = [{"variant_id": v.id, "net_r": n} for v, n in zip(variants, [1, 1, 1, 1, -1, 1])]
    stats = grid_rows(spec, variants, rows)
    assert stats[0]["n"] == 6
    assert stats[0]["profitable_share"] == pytest.approx(5 / 6)
    assert stats[0]["mean"] == pytest.approx(2 / 3)
    assert stats[0]["robust"] is True
    assert stats[1]["plateau_variant"] == "v0000"
    assert stats[1]["plateau_net_r"] == 1
    assert grid_rows(spec, variants, [])[0]["n"] == 0
    # Missing cells remain absent rather than becoming artificial zero-valued candidates.
    sparse = grid_rows(spec, variants, [rows[-1]])[1]
    assert sparse["plateau_variant"] == "v0005"
    high = research_grid.load_grid(write_grid(tmp_path, GRID + "warmup_days = [7, 14]\n"))
    hv = research_grid.expand(high)[0]
    assert (
        grid_rows(high, hv, [{"variant_id": v.id, "net_r": 1} for v in hv])[1]["plateau_variant"]
        is None
    )


def test_symbol_classes():
    from backtester.data.sources import PRICE_DIGITS
    from backtester.tools.research_diagnostics import MARKET_CLASSES, market_class

    assert set(PRICE_DIGITS) <= set(MARKET_CLASSES)
    assert (
        market_class(SimpleNamespace(symbol="GBPUSD", reason="opening range london")) == "FX London"
    )
    assert (
        market_class(SimpleNamespace(symbol="XAUUSD", reason="opening range new_york"))
        == "Metals NY"
    )
    assert market_class(SimpleNamespace(symbol="NATGAS")) == "Energy"
    assert market_class(SimpleNamespace(symbol="GBPUSD")) == "FX"
    assert market_class(SimpleNamespace(symbol="UNKNOWN")) == "Other"


def test_daily_shocks_one_read_per_cached_block_and_utc_days():
    import pandas as pd

    from backtester.tools.research_diagnostics import load_shocks

    first = date(2020, 1, 1)
    days = [first + timedelta(days=i) for i in range(12)]  # 10 cached days before the last
    cached = days[:5] + days[6:]  # a gap on day 6
    calls = []

    def fetch_frame(symbol, tf, start, end):
        calls.append((start.date(), end.date()))
        rows = []
        for d in cached:
            if start.date() <= d < end.date():
                width = 100 if d == days[-1] else 1
                for hour in (0, 23):  # both inside the same UTC day
                    ts = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=hour)
                    rows.append((ts, width, 0.0, 1.0))
        return pd.DataFrame(rows, columns=["ts", "high", "low", "close"])

    sources = SimpleNamespace(
        cached_days=lambda s: cached, adapter=lambda s: SimpleNamespace(fetch_frame=fetch_frame)
    )
    shocks = load_shocks(["US500"], days[-1], sources)
    assert calls == [(days[0], days[5]), (days[6], days[-1] + timedelta(days=1))]
    assert shocks == {"US500": {days[-1]}}


def test_runner_diagnostics_resume_and_retest(tmp_path, fakes, monkeypatch):
    from backtester.tools import research_diagnostics as diagnostics

    calls = []
    monkeypatch.setattr(
        diagnostics,
        "load_shocks",
        lambda *a: calls.append(a) or {"US500": {date(2015, 3, 1), date(2021, 3, 1)}},
    )
    out = run_research(tmp_path, COMBINED)
    folder = research_folder(tmp_path)
    assert out["variants"] == 3 and len(fakes.calls) == 4
    assert len(calls) == 1
    grid = read_csv(folder / "grid.csv")
    assert [r["family"] for r in grid] == ["all", "ranges", "filters"]
    assert [r["n"] for r in grid] == ["3", "2", "1"]
    assert "v0002" in (folder / "report.md").read_text()
    symbols = read_csv(folder / "breakdown_symbols.csv")
    assert {r["period"] for r in symbols} == {"development", "test"}
    assert len(symbols) == 4
    shocks = read_csv(folder / "shocks.csv")
    assert len(shocks) == 2
    assert float(shocks[0]["net_r_without_shocks"]) < float(shocks[0]["net_r_total"])
    assert {r["market_class"] for r in read_csv(folder / "breakdown_classes.csv")} == {"US indices"}
    assert {r["year"] for r in read_csv(folder / "by_year.csv")} == {"2015", "2021", "2026"}
    run_research(tmp_path, COMBINED, retest=True)
    assert len(fakes.calls) == 5
    assert len(read_csv(folder / "shocks.csv")) == 3
    assert len(read_csv(folder / "breakdown_symbols.csv")) == 6
    # Diagnostics survive cached development runs and do not modify trial/DSR counts.
    assert json.loads((folder / "research.json").read_text())["test"]["n_variants"] == 3


def test_shocks_disabled_and_legacy_columns(tmp_path, fakes, monkeypatch):
    from backtester.tools import research_diagnostics as diagnostics

    def forbidden(*args):
        pytest.fail("shocks=false must not read daily bars")

    monkeypatch.setattr(diagnostics, "load_shocks", forbidden)
    run_research(tmp_path, GRID.replace("min_trades = 4", "min_trades = 4\nshocks = false"))
    folder = research_folder(tmp_path)
    assert not (folder / "shocks.csv").exists()
    assert "family" not in read_csv(folder / "variants.csv")[0]
    assert (folder / "grid.csv").is_file()


def test_one_axis_plateau_singleton_and_no_ranked_variants(tmp_path, fakes):
    from backtester.tools.research_diagnostics import grid_rows

    text = GRID[: GRID.index("[grid]")] + "[grid]\nrange_minutes = [5, 10, 15, 20, 25]\n"
    spec = research_grid.load_grid(write_grid(tmp_path, text))
    variants = research_grid.expand(spec)[0]
    rows = [{"variant_id": v.id, "net_r": n} for v, n in zip(variants, [10, -10, 5, 5, 5])]
    result = grid_rows(spec, variants, rows)[1]
    assert result["plateau_variant"] == "v0003"
    assert result["plateau_net_r"] == 5
    base = research_grid.load_grid(write_grid(tmp_path, GRID[: GRID.index("[grid]")]))
    singleton = grid_rows(
        base, research_grid.expand(base)[0], [{"variant_id": "v0000", "net_r": -2}]
    )[1]
    assert singleton["std"] == 0 and singleton["plateau_variant"] == "v0000"
    assert singleton["robust"] is False
    out = run_research(tmp_path, GRID.replace("min_trades = 4", "min_trades = 500"))
    assert out["status"] == "no_test"
    folder = research_folder(tmp_path)
    assert read_csv(folder / "grid.csv")[0]["n"] == "6"
    assert read_csv(folder / "breakdown_symbols.csv") == []


def test_shock_attribution_and_diagnostic_toggle(tmp_path, fakes, monkeypatch):
    from test_research import make_trade

    from backtester.tools import research_diagnostics as diagnostics

    trade = make_trade("US500", 2015, 2, 0)
    trade.exit_time = datetime(2015, 3, 2, tzinfo=UTC)
    snapshot = diagnostics.snapshot([trade])
    shocks = {"US500": {date(2015, 3, 2)}, "NAS100": {date(2015, 3, 1)}}
    assert snapshot["shock_trades"][0][1].startswith("2015-03-02")
    monkeypatch.setattr(diagnostics, "load_shocks", lambda *a: shocks)
    first = run_research(tmp_path)
    folder = research_folder(tmp_path)
    calls = len(fakes.calls)
    second = run_research(
        tmp_path, GRID.replace("min_trades = 4", "min_trades = 4\nshocks = false")
    )
    assert first["id"] == second["id"] and second["status"] == "refused"
    assert len(fakes.calls) == calls
    assert not (folder / "shocks.csv").exists()


def test_duplicate_family_reuses_plateau_without_extra_run(tmp_path, fakes):
    out = run_research(tmp_path, COMBINED.replace("target_r = [0, 1]", "target_r = [0]"))
    assert out["variants"] == 2
    rows = read_csv(research_folder(tmp_path) / "grid.csv")
    assert rows[-1]["n"] == "0"
    assert rows[-1]["plateau_variant"] == "v0001"


def test_reporting_failure_cannot_spend_test_again(tmp_path, fakes, monkeypatch):
    from backtester.tools import research_diagnostics as diagnostics

    def fail(*args):
        raise OSError("diagnostic input unavailable")

    monkeypatch.setattr(diagnostics, "load_shocks", fail)
    with pytest.raises(OSError, match="diagnostic input"):
        run_research(tmp_path)
    info = json.loads((research_folder(tmp_path) / "research.json").read_text())
    assert info["test"]["status"] == "done"
    monkeypatch.setattr(diagnostics, "load_shocks", lambda *args: {})
    assert run_research(tmp_path)["status"] == "refused"
    assert len(fakes.calls) == 7


def test_development_only_shock_reads_stop_at_development_end(tmp_path, fakes, monkeypatch):
    from backtester.tools import research_diagnostics as diagnostics

    calls = []
    monkeypatch.setattr(diagnostics, "load_shocks", lambda *args: calls.append(args) or {})
    run_research(tmp_path, dev_only=True)
    assert calls[0][1] == date(2021, 9, 13)
