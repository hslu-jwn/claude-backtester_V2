"""Research runner: grid file validation and expansion, development run (resumable), selection,
the single test run, retest guard, trial log and output files, with a faked backtest.
Spec: research-runner.md (ROADMAP 6.1 + 6.2)."""

from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from backtester.analytics import trial_log
from backtester.engine.ticks import TickRoundingStats
from backtester.runner import RunSettings
from backtester.settings import leaves
from backtester.strategy.registry import default_config
from backtester.tools import research, research_grid
from backtester.tools.research_grid import (
    GridError,
    ResearchConfig,
    expand,
    load_grid,
    variant_settings,
)

GRID = """
strategy = "opening_range"
symbols = ["US500", "NAS100"]
sensitivity = false  # these tests count the grid runs only (brief 2)
entry_screen = false  # V2.4c: entry screening has its own synthetic M1 tests
min_trades = 4

[base]
entry_mode = "range"

[grid]
range_minutes = [5, 15, 30]
target_r = [0, 1]
"""


def write_grid(tmp_path: Path, text: str = GRID, name: str = "idea.toml") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


# --- grid file -------------------------------------------------------------------------


def test_load_and_expand_the_full_product(tmp_path):
    spec = load_grid(write_grid(tmp_path))
    assert spec.name == "idea" and spec.strategy == "opening_range"
    assert spec.symbols == ("US500", "NAS100") and spec.min_trades == 4
    variants, size, sampled = expand(spec)
    assert size == 6 and len(variants) == 6 and sampled is False
    assert [v.overrides["range_minutes"] for v in variants] == [5, 5, 15, 15, 30, 30]
    assert len({v.id for v in variants}) == len({v.name for v in variants}) == 6


def test_defaults_when_the_file_leaves_them_out(tmp_path):
    spec = load_grid(write_grid(tmp_path, 'strategy = "opening_range"\nsymbols = ["US500"]\n'))
    cfg = ResearchConfig()
    assert spec.min_trades == cfg.min_trades == 100
    assert spec.max_variants == cfg.max_variants and spec.seed == cfg.seed
    variants, size, _ = expand(spec)  # no grid = the base settings only
    assert size == 1 and len(variants) == 1


def test_variant_ids_and_names_are_stable(tmp_path):
    a = expand(load_grid(write_grid(tmp_path)))[0]
    b = expand(load_grid(write_grid(tmp_path)))[0]
    assert [(v.id, v.name) for v in a] == [(v.id, v.name) for v in b]
    assert a[0].name == "range_minutes=5 target_r=0"


def test_settings_are_applied_to_the_defaults(tmp_path):
    spec = load_grid(write_grid(tmp_path))
    variants, _, _ = expand(spec)
    s = variant_settings(spec, variants[-1])
    assert s.strategy.range_minutes == 30 and s.strategy.target_r == 1
    assert s.strategy.entry_mode.name == "RANGE"  # base, enum given by value
    assert s.strategy.band_atr == default_config("opening_range").band_atr  # untouched


def test_unknown_setting_name_lists_the_valid_names(tmp_path):
    text = GRID.replace("range_minutes", "range_minute")
    with pytest.raises(GridError) as e:
        load_grid(write_grid(tmp_path, text))
    msg = str(e.value)
    assert "range_minute" in msg and "range_minutes" in msg and "target_r" in msg
    assert "warmup_days" in msg and "engine.costs" in msg  # shared settings are named too


def test_unknown_base_name_is_an_error_too(tmp_path):
    with pytest.raises(GridError, match="nonsense"):
        load_grid(write_grid(tmp_path, GRID.replace("entry_mode", "nonsense")))


def test_wrong_type_is_an_error_naming_the_setting(tmp_path):
    with pytest.raises(GridError, match="range_minutes"):
        load_grid(write_grid(tmp_path, GRID.replace("[5, 15, 30]", '[5, "ten"]')))
    with pytest.raises(GridError, match="target_r"):
        load_grid(write_grid(tmp_path, GRID.replace("target_r = [0, 1]", "target_r = [true]")))
    with pytest.raises(GridError, match="range_minutes"):
        load_grid(write_grid(tmp_path, GRID.replace("[5, 15, 30]", "[5.5]")))  # not whole


def test_unknown_enum_value_lists_the_options(tmp_path):
    with pytest.raises(GridError, match="BAND"):
        load_grid(write_grid(tmp_path, GRID.replace('"range"', '"sideways"')))


def test_grid_values_must_be_a_non_empty_list_without_duplicates(tmp_path):
    with pytest.raises(GridError, match="range_minutes"):
        load_grid(write_grid(tmp_path, GRID.replace("[5, 15, 30]", "5")))
    with pytest.raises(GridError, match="range_minutes"):
        load_grid(write_grid(tmp_path, GRID.replace("[5, 15, 30]", "[]")))
    with pytest.raises(GridError, match="duplicate"):
        load_grid(write_grid(tmp_path, GRID.replace("[5, 15, 30]", "[5, 15, 15]")))


@pytest.mark.parametrize(
    "text, match",
    [
        ('strategy = "nope"\nsymbols = ["US500"]\n', "nope"),
        ('strategy = "opening_range"\nsymbols = []\n', "symbols"),
        ('strategy = "opening_range"\n', "symbols"),
        ('symbols = ["US500"]\n', "strategy"),
        ('strategy = "opening_range"\nsymbols = ["US500"]\nmax_variant = 3\n', "max_variant"),
        ('strategy = "opening_range"\nsymbols = ["US500"]\nmin_trades = -1\n', "min_trades"),
        ('strategy = "opening_range"\nsymbols = ["US500"]\nmax_variants = 0\n', "max_variants"),
    ],
)
def test_bad_top_level_entries(tmp_path, text, match):
    with pytest.raises(GridError, match=match):
        load_grid(write_grid(tmp_path, text))


def test_missing_and_unreadable_files(tmp_path):
    with pytest.raises(GridError, match="no grid file"):
        load_grid(tmp_path / "none.toml")
    with pytest.raises(GridError, match="not valid TOML"):
        load_grid(write_grid(tmp_path, "strategy = = 1"))


def test_a_combination_the_config_rejects_stops_with_the_variant_named(tmp_path):
    text = GRID.replace("[5, 15, 30]", "[15, 200]")  # the entry window (120) must exceed it
    spec = load_grid(write_grid(tmp_path, text))
    with pytest.raises(GridError, match="range_minutes=200"):
        expand(spec)


def test_dotted_shared_and_nested_names(tmp_path):
    shared = 'strategy = "opening_range"\nsymbols = ["US500"]\n[grid]\nwarmup_days = [7, 14]\n'
    assert expand(load_grid(write_grid(tmp_path, shared)))[1] == 2
    s1 = RunSettings(strategy=default_config("session_zone_sweep"))
    nested = next(
        leaf for leaf in leaves(s1)
        if leaf.path.startswith("strategy.") and leaf.path.count(".") >= 2
        and leaf.kind == "int"
    )  # fmt: skip
    name = nested.path.removeprefix("strategy.")
    text = (
        f'strategy = "session_zone_sweep"\nsymbols = ["XAUUSD"]\n[grid]\n'
        f'"{name}" = [{nested.default}, {nested.default + 1}]\n'
    )
    spec = load_grid(write_grid(tmp_path, text, "nested.toml"))
    variants, size, _ = expand(spec)
    assert size == 2
    assert variant_settings(spec, variants[1]) != variant_settings(spec, variants[0])
    # a shared cost setting by its full dotted path
    cost = 'strategy = "opening_range"\nsymbols = ["US500"]\n[grid]\n"engine.costs.swap_enabled" = [true, false]\n'
    assert expand(load_grid(write_grid(tmp_path, cost, "cost.toml")))[1] == 2


def test_sampling_above_max_variants_is_seeded_and_keeps_ids(tmp_path):
    big = GRID.replace("min_trades = 4", "min_trades = 4\nmax_variants = 4\nseed = 7")
    spec = load_grid(write_grid(tmp_path, big))
    variants, size, sampled = expand(spec)
    assert size == 6 and len(variants) == 4 and sampled is True
    again, _, _ = expand(spec)
    assert [v.id for v in variants] == [v.id for v in again]
    full = {v.id: v.name for v in expand(load_grid(write_grid(tmp_path, GRID, "full.toml")))[0]}
    assert all(full[v.id] == v.name for v in variants)  # ids are the full product's
    picks = set()
    for seed in range(20):
        other = load_grid(write_grid(tmp_path, big.replace("seed = 7", f"seed = {seed}"), "o.toml"))
        picks.add(tuple(v.id for v in expand(other)[0]))
    assert len(picks) > 1  # the seed changes the sample


def test_the_grid_id_follows_the_tested_set_not_the_file_name(tmp_path):
    a = load_grid(write_grid(tmp_path, GRID, "a.toml"))
    b = load_grid(write_grid(tmp_path, GRID, "b.toml"))
    changed = load_grid(write_grid(tmp_path, GRID.replace("[5, 15, 30]", "[5, 15, 45]"), "c.toml"))
    ida = research_grid.grid_id(a, expand(a)[0])
    assert ida.startswith("a_") and research_grid.grid_id(b, expand(b)[0]).startswith("b_")
    assert ida.split("_")[-1] == research_grid.grid_id(b, expand(b)[0]).split("_")[-1]
    assert ida.split("_")[-1] != research_grid.grid_id(changed, expand(changed)[0]).split("_")[-1]
    # min_trades is selection only: the same id
    more = load_grid(
        write_grid(tmp_path, GRID.replace("min_trades = 4", "min_trades = 9"), "a.toml")
    )
    assert research_grid.grid_id(more, expand(more)[0]) == ida


# --- the run, with a faked backtest ------------------------------------------------------


def make_trade(symbol, year, r_net, n):
    entry = datetime(year, 3, 1 + n, 14, 30, tzinfo=UTC)
    return SimpleNamespace(
        symbol=symbol, entry_time=entry, exit_time=entry + timedelta(hours=2),
        direction="long",
        entry=100.0, initial_stop=99.0,
        r_gross=r_net + 0.05, r_net=r_net, planned_r=None,
    )  # fmt: skip


class Fakes:
    """Replaces the data and the backtest: edge per trade = range_minutes / 100 + target_r / 1000; a variant with
    range_minutes in `thin` gets only 2 trades per symbol; `fail_after` raises on that call."""

    def __init__(self):
        self.calls = []
        self.thin = set()
        self.fail_after = None
        self.span = (date(2015, 1, 1), date(2026, 9, 30))

    def run(self, symbols, start, end, settings, sources=None, workers=None, **kw):
        if self.fail_after is not None and len(self.calls) >= self.fail_after:
            raise RuntimeError("interrupted")
        self.calls.append(SimpleNamespace(symbols=tuple(symbols), start=start, end=end,
                                          settings=settings, workers=workers))  # fmt: skip
        m = settings.strategy.range_minutes
        e = m / 100 + settings.strategy.target_r / 1000
        loss = -e / 2
        runs = {}
        for s in symbols:
            rs = [2 * e, loss, 2 * e, loss] if m not in self.thin else [2 * e, loss]
            years = [start.year, end.year, start.year, end.year][: len(rs)]
            trades = tuple(make_trade(s, y, r, i) for i, (y, r) in enumerate(zip(years, rs)))
            runs[s] = SimpleNamespace(
                symbol=s, first_day=start, last_day=end, warmup_from=start, trades=trades,
                sessions=(), notes=(), tick_rounding=TickRoundingStats(),
            )  # fmt: skip
        merged = tuple(t for r in runs.values() for t in r.trades)
        return SimpleNamespace(
            symbols=tuple(symbols), start=start, end=end, settings=settings,
            sources=sources, runs=runs, trades=merged, notes=(),
        )  # fmt: skip

    def run_many(self, symbols, start, end, settings_list, sources, workers):
        for i, settings in enumerate(settings_list):
            yield i, self.run(symbols, start, end, settings, sources, workers)

    def write(self, result, out_dir=None, run_id=None, preset=None):
        from backtester.runner import new_run_id

        out_dir = Path(out_dir)
        folder = out_dir / (run_id or new_run_id(result.symbols, out_dir))
        folder.mkdir(parents=True, exist_ok=False)
        columns = (
            "id",
            "symbol",
            "direction",
            "entry_time",
            "entry_candle",
            "entry",
            "initial_stop",
            "exit_time",
            "exit_price",
            "exit_reason",
            "r_gross",
            "r_net",
        )
        with (folder / "trades.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, columns)
            writer.writeheader()
            for i, t in enumerate(result.trades):
                writer.writerow(
                    {k: getattr(t, k, None) for k in columns}
                    | {
                        "id": i,
                        "entry_candle": t.entry_time,
                        "exit_price": t.entry,
                        "exit_reason": "signal",
                    }
                )
        (folder / "settings.json").write_text(json.dumps({"preset": preset}), encoding="utf-8")
        (folder / "summary.json").write_text(
            json.dumps({"run_id": folder.name, "start": str(result.start), "end": str(result.end)}),
            encoding="utf-8",
        )
        return folder


def _small_diagnostics(monkeypatch):
    """Runner tests check wiring and resume, not the statistics (their own tests use the real
    sizes): small resample counts keep the suite fast (speed rule of 2026-10-24)."""
    from backtester.analytics.bayes import BayesConfig
    from backtester.analytics.best_of_n import RealityCheckConfig
    from backtester.analytics.bounds import BoundsConfig
    from backtester.analytics.pbo import PBOConfig
    from backtester.risk.drawdown_bounds import DrawdownBoundsConfig
    from backtester.tools import (
        drawdown_report,
        research_bayes,
        research_significance,
        skill_bounds,
    )

    significance = research_significance.SignificanceConfig
    monkeypatch.setattr(
        research_significance,
        "SignificanceConfig",
        lambda **kw: significance(
            **{"reality_check": RealityCheckConfig(boots=50), "pbo": PBOConfig(blocks=4), **kw}
        ),
    )
    monkeypatch.setattr(
        skill_bounds, "BoundsConfig", lambda **kw: BoundsConfig(**{"boots": 100, **kw})
    )
    monkeypatch.setattr(
        research_bayes, "BayesConfig", lambda **kw: BayesConfig(**{"draws": 500, **kw})
    )
    bounds = drawdown_report.drawdown_bounds
    monkeypatch.setattr(
        drawdown_report,
        "drawdown_bounds",
        lambda values, config=None: bounds(
            values, config or DrawdownBoundsConfig(outer=5, inner=50)
        ),
    )


@pytest.fixture
def fakes(monkeypatch):
    from backtester.analytics import profile
    from backtester.analytics.regime import RegimeLabel
    from backtester.tools import research_diagnostics, research_monkeys, skill_bounds

    f = Fakes()
    _small_diagnostics(monkeypatch)
    # Synthetic executions have a flat benchmark, without reading the real price cache.
    monkeypatch.setattr(
        skill_bounds, "load_drifts", lambda symbols, *a: dict.fromkeys(symbols, 0.0)
    )
    monkeypatch.setattr(profile, "load_drifts", lambda symbols, *a: dict.fromkeys(symbols, 0.0))
    monkeypatch.setattr(profile, "label_trades", lambda trades, *a: [RegimeLabel()] * len(trades))
    monkeypatch.setattr(research_monkeys, "calculate", lambda *a, **kw: {"available": False})
    monkeypatch.setattr(research_diagnostics, "load_shocks", lambda *args: {})
    monkeypatch.setattr(research, "run_backtests", f.run)
    monkeypatch.setattr(research, "run_period_many", f.run_many)
    monkeypatch.setattr(research, "write_results", f.write)
    monkeypatch.setattr(research, "cached_span", lambda symbols, sources: f.span)
    monkeypatch.setattr(research, "segments", lambda symbol, a, b, sources: [(a, b)])
    return f


def run_research(tmp_path, text=GRID, **kw):
    kw.setdefault("log", lambda *a, **k: None)
    return research.run_research(write_grid(tmp_path, text), results_dir=tmp_path / "results", **kw)


def test_condition_profiles_chosen_only_and_saved_test(tmp_path, fakes):
    out = run_research(tmp_path, dev_only=True)
    folder = research_folder(tmp_path)
    profiles = json.loads((folder / "profile.json").read_text())
    assert set(profiles) == {"development"}
    assert len(list((folder / "variants").glob("*/profile.json"))) == 1
    assert (tmp_path / "results" / out["chosen"]["dev_run"] / "profile.json").is_file()
    out = run_research(tmp_path)
    profiles = json.loads((folder / "profile.json").read_text())
    assert set(profiles) == {"development", "test 1"}
    assert (tmp_path / "results" / out["test"]["run_folder"] / "profile.json").is_file()
    report = (folder / "report.md").read_text()
    assert "Strategy condition profile development" in report
    assert "Strategy condition profile test 1" in report
    count = len(fakes.calls)
    assert run_research(tmp_path)["status"] == "refused"
    assert len(fakes.calls) == count


def test_monkeys_chosen_development_only_and_flag(tmp_path, fakes, monkeypatch):
    from backtester.tools import research_monkeys

    calls = []

    def calculate(*args, **kwargs):
        calls.append((args, kwargs))
        return {"available": False, "flags": ["monkey_beaten"]}

    monkeypatch.setattr(research_monkeys, "calculate", calculate)
    out = run_research(tmp_path, dev_only=True)
    assert len(calls) == 1
    assert calls[0][0][2] == out["chosen"]["id"]
    assert calls[0][0][4] == date(2021, 9, 13)
    folder = out["folder"]
    assert (folder / "monkeys.json").is_file()
    assert "monkey_beaten" in (folder / "variants.csv").read_text()
    assert "Matched monkeys" in (folder / "report.md").read_text()
    assert out["test"]["status"] == "not_run"


def test_monkeys_opt_out(tmp_path, fakes, monkeypatch):
    from backtester.tools import research_monkeys

    def forbidden(*a, **kw):
        pytest.fail("monkeys=false must skip M1 loading and simulations")

    monkeypatch.setattr(research_monkeys, "calculate", forbidden)
    out = run_research(tmp_path, GRID.replace("[base]", "monkeys = false\n\n[base]"), dev_only=True)
    assert out["chosen"] is not None


def research_folder(tmp_path) -> Path:
    (folder,) = (tmp_path / "results" / "research").iterdir()
    return folder


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_development_runs_every_variant_on_the_development_period(tmp_path, fakes):
    out = run_research(tmp_path, dev_only=True)
    dev_calls = [c for c in fakes.calls]
    assert len(dev_calls) == 6 and out["variants"] == 6
    assert all(c.start == date(2015, 1, 1) and c.end == date(2021, 9, 13) for c in dev_calls)
    assert all(c.symbols == ("US500", "NAS100") for c in dev_calls)


def test_workers_are_passed_to_the_runner(tmp_path, fakes):
    run_research(tmp_path, dev_only=True, workers=3)
    assert {c.workers for c in fakes.calls} == {3}


def test_ranked_by_dev_net_r_and_only_with_min_trades(tmp_path, fakes):
    fakes.thin = {30}  # the best edge gets 4 trades in all, below min_trades 5
    out = run_research(tmp_path, GRID.replace("min_trades = 4", "min_trades = 5"), dev_only=True)
    folder = research_folder(tmp_path)
    rows = read_csv(folder / "variants.csv")
    ranked = [r for r in rows if r["rank"]]
    assert [r["rank"] for r in ranked] == ["1", "2", "3", "4"]
    assert all("range_minutes=30" not in r["variant"] for r in ranked)  # 4 trades < 5
    nets = [float(r["net_r"]) for r in ranked]
    assert nets == sorted(nets, reverse=True)
    assert out["chosen"]["name"].startswith("range_minutes=15")
    unranked = [r for r in rows if not r["rank"]]
    assert len(unranked) == 2 and all("too_few_trades" in r["flags"] for r in unranked)


def test_all_variants_below_min_trades_means_no_test_run(tmp_path, fakes):
    out = run_research(tmp_path, GRID.replace("min_trades = 4", "min_trades = 500"))
    assert out["status"] == "no_test" and out["chosen"] is None
    assert "500" in out["message"] and "no variant" in out["message"].lower()
    assert all(c.start == date(2015, 1, 1) for c in fakes.calls)  # nothing ran on the test period
    info = json.loads((research_folder(tmp_path) / "research.json").read_text())
    assert info["chosen"] is None and info["test"]["status"] == "skipped"
    assert not (research_folder(tmp_path) / "test.csv").exists()
    # a later run with a lower min_trades may still use the test (it was not spent)
    again = run_research(tmp_path, GRID.replace("min_trades = 4", "min_trades = 4"))
    assert again["status"] == "done"


def test_one_test_run_for_the_best_variant_on_the_test_period(tmp_path, fakes):
    out = run_research(tmp_path)
    assert out["status"] == "done" and len(fakes.calls) == 7
    test = fakes.calls[-1]
    assert test.start == date(2021, 9, 14) and test.end == date(2026, 9, 30)
    assert test.settings.strategy.range_minutes == 30 and test.settings.strategy.target_r == 1
    assert out["chosen"]["name"] == "range_minutes=30 target_r=1"


def test_test_run_uses_the_cutoff_even_when_data_ends_early(tmp_path, fakes):
    fakes.span = (date(2015, 1, 1), date(2021, 9, 20))
    run_research(tmp_path)
    assert fakes.calls[-1].start == date(2021, 9, 14) and fakes.calls[-1].end == date(2021, 9, 20)


def test_no_test_data_after_the_cutoff_is_a_clear_message(tmp_path, fakes):
    fakes.span = (date(2015, 1, 1), date(2021, 9, 13))
    out = run_research(tmp_path)
    assert out["status"] == "no_test" and "2021-09-14" in out["message"]


def test_second_test_of_the_same_grid_is_refused_without_retest(tmp_path, fakes):
    first = run_research(tmp_path)
    calls = len(fakes.calls)
    second = run_research(tmp_path)
    assert second["status"] == "refused" and "--retest" in second["message"]
    assert len(fakes.calls) == calls  # no dev rerun, no test run
    info = json.loads((research_folder(tmp_path) / "research.json").read_text())
    assert info["test"]["status"] == "done" and info["test"]["retests"] == 0
    assert first["test"]["verdict"] == second["test"]["verdict"]  # the first result stays


def test_retest_runs_the_test_again_and_is_logged_as_a_retest(tmp_path, fakes):
    run_research(tmp_path)
    calls = len(fakes.calls)
    out = run_research(tmp_path, retest=True)
    assert out["status"] == "done" and len(fakes.calls) == calls + 1  # only the test run
    info = json.loads((research_folder(tmp_path) / "research.json").read_text())
    assert info["test"]["retests"] == 1 and info["test"]["run"] == 2
    lines = [
        r for r in trial_log.read_all(tmp_path / "results" / "trials.jsonl") if r.family == "idea"
    ]
    assert any("retest" in r.note and "retest" in r.source for r in lines)
    assert [r["test_run"] for r in read_csv(research_folder(tmp_path) / "test.csv")] == ["1", "2"]


def test_dev_only_does_not_spend_the_test(tmp_path, fakes):
    out = run_research(tmp_path, dev_only=True)
    assert out["status"] == "dev_only" and not (research_folder(tmp_path) / "test.csv").exists()
    info = json.loads((research_folder(tmp_path) / "research.json").read_text())
    assert info["test"]["status"] == "not_run"
    assert run_research(tmp_path)["status"] == "done"  # now the test runs, dev is not rerun
    assert len(fakes.calls) == 7


def test_resume_skips_finished_variants(tmp_path, fakes):
    fakes.fail_after = 2
    with pytest.raises(RuntimeError):
        run_research(tmp_path)
    assert len(fakes.calls) == 2
    fakes.fail_after = None
    out = run_research(tmp_path)
    assert len(fakes.calls) == 2 + 4 + 1  # four missing variants and the test
    assert out["status"] == "done"
    assert len(read_csv(research_folder(tmp_path) / "variants.csv")) == 6
    # a variant folder left half-written (no scorecard) is run again
    done = min((research_folder(tmp_path) / "variants").iterdir())
    (done / "scorecard.json").unlink()
    run_research(tmp_path, retest=True)
    assert len(fakes.calls) == 7 + 1 + 1


def test_progress_is_printed(tmp_path, fakes):
    lines = []
    run_research(tmp_path, dev_only=True, log=lines.append)
    assert sum("v000" in str(line) or "/6" in str(line) for line in lines) >= 6


def test_output_files_and_their_fields(tmp_path, fakes):
    out = run_research(tmp_path)
    folder = research_folder(tmp_path)
    assert folder.name == out["id"] and folder.name.startswith("idea_")
    info = json.loads((folder / "research.json").read_text(encoding="utf-8"))
    for key in ("id", "name", "strategy", "symbols", "base", "grid", "grid_size", "variants",
                "sampled", "seed", "min_trades", "max_variants", "periods", "ranked", "chosen",
                "test", "created", "updated"):  # fmt: skip
        assert key in info, key
    assert info["periods"]["development"] == {"start": "2015-01-01", "end": "2021-09-13"}
    assert info["periods"]["test"]["start"] == "2021-09-14"
    assert info["grid"] == {"range_minutes": [5, 15, 30], "target_r": [0, 1]}
    assert info["grid_size"] == 6 and info["variants"] == 6 and info["seed"] == 1
    assert info["chosen"]["id"] and info["chosen"]["overrides"] == {
        "entry_mode": "RANGE", "range_minutes": 30, "target_r": 1,
    }  # fmt: skip
    assert info["test"]["status"] == "done" and info["test"]["verdict"] in (
        "green", "yellow", "red",
    )  # fmt: skip

    variants = read_csv(folder / "variants.csv")
    assert list(variants[0]) == [
        "variant_id", "variant", "rank", "trades", "win_rate", "avg_r", "net_r", "profit_factor",
        "max_dd_r", "half_first_net_r", "half_second_net_r", "net_r_stressed",
        "net_r_without_best", "se_avg_r", "time_in_market", "avg_hold_hours",
        "detrended_net_r", "lower95_mean_daily_r", "log_pf",
        "flags", "set.range_minutes", "set.target_r",
    ]  # fmt: skip
    assert variants[0]["rank"] == "1" and variants[0]["set.range_minutes"] == "30"
    test = read_csv(folder / "test.csv")
    assert len(test) == 1
    assert list(test[0]) == [
        "test_run", "variant_id", "variant", "start", "end", "trades", "win_rate", "avg_r",
        "net_r", "profit_factor", "max_dd_r", "half_first_net_r", "half_second_net_r",
        "net_r_stressed", "net_r_without_best", "se_avg_r", "time_in_market", "avg_hold_hours",
        "detrended_net_r", "lower95_mean_daily_r", "log_pf",
        "t_stat", "deflated_sharpe", "verdict",
        "verdict_label", "n_variants", "flags", "run_folder", "set.range_minutes", "set.target_r",
    ]  # fmt: skip
    assert test[0]["n_variants"] == "6" and test[0]["variant_id"] == info["chosen"]["id"]
    report = (folder / "report.md").read_text(encoding="utf-8")
    assert "range_minutes=30 target_r=1" in report and "6 variants" in report
    assert "Skill vs trend, and bounds development" in report
    assert "Skill vs trend, and bounds test 1" in report
    skill = json.loads((folder / "skill_bounds.json").read_text(encoding="utf-8"))
    assert set(skill) == {"development", "test 1"}
    assert skill["development"]["trend"]["total"]["net_r"] == pytest.approx(
        float(variants[0]["net_r"])
    )
    assert float(variants[0]["detrended_net_r"]) == pytest.approx(float(variants[0]["net_r"]))
    assert all(r["detrended_net_r"] == "" for r in variants[1:])
    assert float(test[0]["detrended_net_r"]) == pytest.approx(float(test[0]["net_r"]))


def test_chosen_runs_are_normal_run_folders_and_a_preset(tmp_path, fakes):
    out = run_research(tmp_path)
    results = tmp_path / "results"
    runs = sorted(p.name for p in results.iterdir() if (p / "summary.json").is_file())
    assert len(runs) == 2  # the chosen variant's development run and its test run
    assert out["chosen"]["dev_run"] in runs and out["test"]["run_folder"] in runs
    dev = json.loads((results / out["chosen"]["dev_run"] / "summary.json").read_text())
    assert dev["run_id"] == out["chosen"]["dev_run"]  # the copy is a run of its own
    preset = out["chosen"]["preset"]
    saved = json.loads((results / "presets" / f"{preset}.json").read_text(encoding="utf-8"))
    assert saved["settings"]["strategy"]["range_minutes"] == 30
    assert (
        json.loads((results / out["test"]["run_folder"] / "settings.json").read_text())["preset"]
        == preset
    )
    # resuming does not create the development folder a second time
    run_research(tmp_path, retest=True)
    assert len([p for p in results.iterdir() if (p / "summary.json").is_file()]) == 3


def test_test_scorecard_has_deflated_sharpe_and_a_verdict(tmp_path, fakes):
    out = run_research(tmp_path)
    test = out["test"]
    assert test["n_variants"] == 6
    assert test["verdict"] in ("green", "yellow", "red")
    assert test["verdict_label"] in ("EDGE", "WEAK", "NO EDGE")
    row = read_csv(research_folder(tmp_path) / "test.csv")[0]
    assert row["verdict"] == test["verdict"]


def test_deflated_sharpe_is_the_daily_one_as_the_trial_log(tmp_path, fakes):
    from backtester.analytics.deflated_sharpe import TradeStats, deflated_sharpe

    out = run_research(tmp_path)
    test = out["test"]
    lines = [
        r for r in trial_log.read_all(tmp_path / "results" / "trials.jsonl") if r.family == "idea"
    ]
    dev = [r for r in lines if r.source == "research"]
    (rec,) = [r for r in lines if r.source == "research-test"]
    sharpes = [r.day_sharpe for r in dev if r.day_sharpe is not None]
    daily = deflated_sharpe(
        TradeStats(rec.days, rec.day_mean, rec.day_sd, rec.day_skew, rec.day_kurt, rec.day_sharpe),
        len(dev),
        sharpes,
    ).dsr
    per_trade = deflated_sharpe(
        TradeStats(rec.trades, rec.mean, rec.sd, rec.skew, rec.kurt, rec.sharpe),
        len(dev),
        [r.sharpe for r in dev if r.sharpe is not None],
    ).dsr
    assert daily is not None and per_trade is not None and daily != pytest.approx(per_trade)
    assert test["deflated_sharpe"] == pytest.approx(daily)


def test_trial_log_gets_every_variant_and_the_test(tmp_path, fakes):
    run_research(tmp_path)
    lines = [
        r for r in trial_log.read_all(tmp_path / "results" / "trials.jsonl") if r.family == "idea"
    ]
    assert len(lines) == 6 + 1
    assert {r.strategy for r in lines} == {"opening_range"}
    dev = [r for r in lines if r.end == "2021-09-13"]
    assert len(dev) == 6 and all(r.trades == 8 for r in dev)  # 4 trades x 2 symbols
    (test,) = [r for r in lines if r.start == "2021-09-14"]
    assert test.end == "2026-09-30" and test.source == "research-test"
    run_research(tmp_path, dev_only=True)  # a rerun is not a new trial (last line per key wins)
    assert (
        len(
            [
                r
                for r in trial_log.read_all(tmp_path / "results" / "trials.jsonl")
                if r.family == "idea"
            ]
        )
        == 7
    )


def test_main_exit_codes_and_messages(tmp_path, fakes, capsys):
    path = write_grid(tmp_path)
    out_dir = ["--results-dir", str(tmp_path / "results")]
    assert research.main([str(path), *out_dir]) == 0
    assert research.main([str(path), *out_dir]) == 2  # the test is spent
    assert "--retest" in capsys.readouterr().err
    assert research.main([str(path), *out_dir, "--retest"]) == 0
    bad = write_grid(tmp_path, GRID.replace("range_minutes", "range_minute"), "bad.toml")
    assert research.main([str(bad), *out_dir]) == 2
    assert "range_minutes" in capsys.readouterr().err
    assert research.main([str(tmp_path / "missing.toml"), *out_dir]) == 2


def test_trial_log_follows_the_results_dir(tmp_path, fakes):
    run_research(tmp_path, dev_only=True)
    assert (tmp_path / "results" / "trials.jsonl").is_file()
    assert trial_log.read_all() == []  # the default log (results/trials.jsonl) is untouched
