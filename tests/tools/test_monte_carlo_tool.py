"""Monte Carlo report tool: CLI, summary.json and report.html with a stubbed backtest.
Spec: risk-management.md > Monte Carlo report (ROADMAP 12.7)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.engine.costs import CostConfig
from backtester.tools import monte_carlo as tool
from backtester.tools.monte_carlo import ToolConfig, parse_args, path_row

START, END = date(2021, 1, 4), date(2021, 4, 30)


def trade(symbol, day, r_net, r_gross=None, mode_bonus=0.0):
    entry = datetime(day.year, day.month, day.day, 14, 30, tzinfo=UTC)
    return SimpleNamespace(
        symbol=symbol, entry_time=entry, exit_time=entry + timedelta(hours=2),
        entry=100.0, initial_stop=99.0, direction="long", exit_reason="signal", swap_r=0.0,
        r_gross=r_net + 0.05 if r_gross is None else r_gross, r_net=r_net + mode_bonus,
    )  # fmt: skip


def weekdays(n=60):
    d, out = START, []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


@pytest.fixture
def stub(monkeypatch):
    import numpy as np

    from backtester.analytics.entry_screen import M1Data
    from backtester.tools import entry_screen, skill_bounds

    monkeypatch.setattr(
        skill_bounds, "load_drifts", lambda symbols, *a: dict.fromkeys(symbols, 0.0)
    )

    def fake_m1(*args):
        stamps = [
            datetime(d.year, d.month, d.day, 14, 29, tzinfo=UTC).timestamp() + i * 60
            for d in weekdays()
            for i in range(122)
        ]
        prices = np.full(len(stamps), 100.0)
        return M1Data(np.array(stamps), prices, prices, prices, prices)

    monkeypatch.setattr(entry_screen, "load_m1", fake_m1)
    calls = {"run": [], "profile": 0, "path": 0}

    def fake_run(symbols, start, end, settings, *args, **kwargs):
        calls["run"].append(settings.strategy)
        mode = getattr(settings.strategy, "mode", "fade")
        sign = -1.0 if mode == "follow" else 1.0
        trades = tuple(
            trade(s, d, sign * (1.0 if i % 3 else -0.8))
            for s in symbols for i, d in enumerate(weekdays())
        )  # fmt: skip
        return SimpleNamespace(trades=trades, runs={s: SimpleNamespace() for s in symbols})

    def fake_profile(*a, **k):
        calls["profile"] += 1
        return object()

    def fake_write(*a, **k):
        calls["path"] += 1
        return object()

    monkeypatch.setattr(tool, "run_backtests", fake_run)
    monkeypatch.setattr(tool, "load_profile", fake_profile)
    monkeypatch.setattr(tool, "write_path", fake_write)
    return calls


def argv(tmp_path, *extra, strategy="gap_fade"):
    return [
        "NAS100", "US500", "--start", START.isoformat(), "--end", END.isoformat(),
        "--strategy", strategy, "--runs", "30", "--out", str(tmp_path), *extra,
    ]  # fmt: skip


def test_parse_args_defaults():
    a = parse_args(["nas100", "--start", "2020-01-01", "--end", "2020-02-01"])
    assert a.symbols == ["NAS100"] and a.paths == 20 and a.seed == 42 and a.runs == 1000
    assert a.source == "histdata" and a.out is None


def test_default_out_folder_names_strategy_symbols_and_period():
    a = parse_args(["NAS100", "US500", "--start", "2020-01-01", "--end", "2021-09-13",
                    "--strategy", "gap_fade"])  # fmt: skip
    assert tool.default_out(a).parts[-2:] == (
        "monte_carlo",
        "gap_fade_NAS100-US500_2020-01-01_2021-09-13",
    )


def test_gap_fade_run_writes_report_and_summary(tmp_path, stub):
    assert tool.main(argv(tmp_path, "--paths", "2")) == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    v = summary["verdict"]
    assert v["label"] in {"EDGE", "WEAK", "NO EDGE"}
    assert [c["key"] for c in v["checks"]] == [
        "t_stat",
        "random_entries",
        "halves",
        "cost_stress",
        "without_best",
        "random_fills",
        "deflated_sharpe",
    ]
    assert summary["random_entries"]["available"] is True
    assert 0 <= summary["random_entries"]["percentile"] <= 100
    assert set(summary["monte_carlo"]["risks"]) == {"0.005", "0.01", "0.015"}
    assert {r["symbol"] for r in summary["random_paths"]["rows"]} == {"NAS100", "US500"}
    assert stub["profile"] == 2 and stub["path"] == 2 * 2  # 2 symbols x 2 paths
    # the follow run only for the gap fade
    assert sorted(getattr(c, "mode", None) for c in stub["run"][:2]) == ["fade", "follow"]
    for text in (v["label"], "How to read this", "FTMO 2-Step", "Random fills", "Random paths"):
        assert text in html
    assert "NaN" not in (tmp_path / "summary.json").read_text(encoding="utf-8")


def test_other_strategy_kind_b_is_not_available(tmp_path, stub):
    tool.main(argv(tmp_path, "--paths", "0", strategy="ny_index_sweep"))
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert summary["random_entries"]["available"] is False
    check = next(c for c in summary["verdict"]["checks"] if c["key"] == "random_entries")
    # T-14 explicitly replaces the former n/a verdict with monkey kind 1 for this strategy.
    assert check["available"] and check["passed"]
    assert check["value"] == summary["monkeys"]["kinds"][0]["net_r"]["percentile"] == 100.0
    assert "random_entries" not in summary["verdict"]["failed"]
    assert "random_entries" not in summary["verdict"]["not_available"]
    assert "not available for this strategy yet" in html
    assert len(stub["run"]) == 1  # no follow run


def test_paths_zero_skips_kind_d(tmp_path, stub):
    tool.main(argv(tmp_path, "--paths", "0"))
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["random_paths"] is None
    assert stub["profile"] == 0 and stub["path"] == 0
    assert "skipped" in (tmp_path / "report.html").read_text(encoding="utf-8").lower()


def test_same_seed_same_numbers(tmp_path, stub):
    tool.main(argv(tmp_path / "a", "--paths", "0"))
    tool.main(argv(tmp_path / "b", "--paths", "0"))
    a = json.loads((tmp_path / "a" / "summary.json").read_text(encoding="utf-8"))
    b = json.loads((tmp_path / "b" / "summary.json").read_text(encoding="utf-8"))
    assert a == b


def test_path_row_warns_when_net_r_is_above_zero():
    up = [trade("NAS100", d, 0.2, r_gross=0.25) for d in weekdays(5)]
    down = [trade("NAS100", d, -0.1, r_gross=-0.05) for d in weekdays(5)]
    r_up, r_down = (
        path_row("NAS100", up, 2, ToolConfig()),
        path_row("NAS100", down, 2, ToolConfig()),
    )
    assert r_up["warning"] is True and r_down["warning"] is False
    assert r_down["mean_net_r"] == pytest.approx(-0.1)
    assert r_down["mean_cost_r"] == pytest.approx(0.05)
    assert r_down["trades"] == 5 and r_down["paths"] == 2


def test_path_row_without_trades_has_no_warning():
    r = path_row("NAS100", [], 3, ToolConfig())
    assert r["trades"] == 0 and r["mean_net_r"] is None and r["warning"] is False


def test_halves_check_uses_the_middle_date_of_the_run(tmp_path, stub):
    # 2021-01-04..2021-04-30: the middle date is 2021-03-03; the old rule (year 2022) would put
    # every trade into the first half. The stub's trades span weekdays from the start.
    tool.main(argv(tmp_path, "--paths", "0"))
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    r = summary["robustness"]
    assert r["half_split_date"] == "2021-03-03"
    assert r["half_first_trades"] > 0 and r["half_second_trades"] > 0
    assert r["half_first_trades"] + r["half_second_trades"] == summary["meta"]["trades"]


def test_build_summary_takes_a_ready_trade_list_without_kind_d():
    trades = [trade("NAS100", d, 1.0 if i % 3 else -0.8) for i, d in enumerate(weekdays())]
    follow = [trade("NAS100", d, -1.0 if i % 3 else 0.8) for i, d in enumerate(weekdays())]
    from dataclasses import replace

    from backtester.runner import RunSettings

    s = tool.build_summary(
        trades, follow, {"strategy": "x", "symbols": ["NAS100"], "start": START, "end": END,
                         "source": "histdata"},
        RunSettings(), ToolConfig(runs=20), log=lambda *_: None,
    )  # fmt: skip
    assert s["random_paths"] is None and s["random_entries"]["available"] is True
    s2 = tool.build_summary(
        trades, None, {"strategy": "x", "symbols": ["NAS100"], "start": START, "end": END,
                       "source": "histdata"},
        replace(RunSettings()), ToolConfig(runs=20), log=lambda *_: None,
    )  # fmt: skip
    assert s2["random_entries"]["available"] is False


# ----- trial log and deflated Sharpe (ROADMAP 12.10) -----------------------------------------


def test_parse_args_family_defaults_to_none_and_can_be_set():
    base = ["NAS100", "--start", "2020-01-01", "--end", "2020-02-01"]
    assert parse_args(base).family is None
    assert parse_args([*base, "--family", "gap grid"]).family == "gap grid"


def test_run_is_logged_with_family_defaulting_to_the_strategy(tmp_path, stub):
    from backtester.analytics.trial_log import family_trials

    tool.main(argv(tmp_path, "--paths", "0"))
    (line,) = family_trials("gap_fade")
    assert line.strategy == "gap_fade" and line.symbols == ["NAS100", "US500"]
    assert line.start == START.isoformat() and line.end == END.isoformat()
    assert line.source == "histdata" and line.trades == 120 and line.sharpe is not None
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["meta"]["family"] == "gap_fade"


def test_family_option_overrides_and_rerun_is_not_a_new_trial(tmp_path, stub):
    from backtester.analytics.trial_log import family_summary, family_trials, read_all

    tool.main(argv(tmp_path / "a", "--paths", "0", "--family", "mine"))
    tool.main(argv(tmp_path / "b", "--paths", "0", "--family", "mine"))
    assert family_trials("gap_fade") == []
    assert family_summary(family_trials("mine"))[0] == 1 and len(read_all()) == 1


def test_deflated_sharpe_uses_the_family_and_is_in_summary_and_report(tmp_path, stub):
    from backtester.analytics.trial_log import append, count_only

    append(count_only("gap_fade", "gap_fade", 9, note="old"))
    tool.main(argv(tmp_path, "--paths", "0"))
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    d = summary["deflated"]
    assert d["n_trials"] == 10 and d["family"] == "gap_fade"
    n_days = len([x for x in weekdays(200) if START <= x <= END])
    assert d["variance"] == pytest.approx(1 / n_days)  # one daily Sharpe: V = 1/days
    assert 0 <= d["psr0"] <= 1 and 0 <= d["dsr"] <= 1 and d["sr0"] > 0
    check = next(c for c in summary["verdict"]["checks"] if c["key"] == "deflated_sharpe")
    assert check["available"] and check["value"] == pytest.approx(d["dsr"])
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    for text in ("Deflated Sharpe", "PSR(0)", "DSR", "gap_fade", "daily"):
        assert text in html


def test_build_summary_without_a_deflated_result_makes_check_7_not_available():
    trades = [trade("NAS100", d, 1.0 if i % 3 else -0.8) for i, d in enumerate(weekdays())]
    from backtester.runner import RunSettings

    s = tool.build_summary(
        trades, None, {"strategy": "x", "symbols": ["NAS100"], "start": START, "end": END,
                       "source": "histdata"},
        RunSettings(), ToolConfig(runs=20), log=lambda *_: None,
    )  # fmt: skip
    assert "deflated_sharpe" in s["verdict"].not_available
    assert s["deflated"] is None


# ---- --run: the Full Monte Carlo button of the results page ------------------------------


def make_run(tmp_path, strategy="gap_fade"):
    """A finished run folder: summary.json, settings.json and a trades.csv of 120 trades (the stub's days)."""
    import csv
    from dataclasses import replace

    from backtester.runner import TRADE_COLUMNS, RunSettings
    from backtester.settings import to_dict
    from backtester.strategy.registry import default_config

    folder = tmp_path / "results" / "20261020-120000_NAS100-US500"
    folder.mkdir(parents=True)
    rows = []
    for i, d in enumerate(weekdays()):
        for symbol in ("NAS100", "US500"):
            t = trade(symbol, d, 1.0 if i % 3 else -0.8)
            row = dict.fromkeys(TRADE_COLUMNS, "")
            row.update(
                id=len(rows) + 1, symbol=symbol, direction="long", session="",
                entry_time=t.entry_time.isoformat(), entry_candle=t.entry_time.isoformat(),
                entry=100.0, initial_stop=99.0, take_profit=101.0, tp1_share=1.0,
                planned_rr=1.0, exit_time=t.exit_time.isoformat(), exit_price=101.0,
                exit_reason="take_profit", r_gross=t.r_gross, r_net=t.r_net, confluence="",
                parts=json.dumps([{"share": 1.0, "reason": "take_profit",
                                   "time": t.exit_time.isoformat(), "price": 101.0}]),
            )  # fmt: skip
            rows.append(row)
    with open(folder / "trades.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, TRADE_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    summary = {"symbols": ["NAS100", "US500"], "start": START.isoformat(), "end": END.isoformat()}
    (folder / "summary.json").write_text(json.dumps(summary))
    settings = replace(RunSettings(), strategy=default_config(strategy))
    (folder / "settings.json").write_text(json.dumps(to_dict(settings)))
    return folder


def run_argv(folder, out, *extra):
    return ["--run", folder.name, "--results-dir", str(folder.parent), "--paths", "0",
            "--runs", "30", "--out", str(out), *extra]  # fmt: skip


def test_run_option_needs_no_symbols_or_dates_but_otherwise_they_are_required():
    a = parse_args(["--run", "20261020-120000_X"])
    assert a.run == "20261020-120000_X" and a.symbols == [] and a.start is None
    with pytest.raises(SystemExit):
        parse_args(["NAS100"])  # no --start / --end / --run


def test_run_option_uses_the_runs_own_trades_and_settings(tmp_path, stub):
    folder = make_run(tmp_path)
    out = tmp_path / "out"
    assert tool.main(run_argv(folder, out)) == 0
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    meta = summary["meta"]
    assert meta["strategy"] == "gap_fade" and meta["symbols"] == ["NAS100", "US500"]
    assert meta["start"] == START.isoformat() and meta["end"] == END.isoformat()
    assert meta["trades"] == 120 and meta["run"] == folder.name
    # the base backtest is not run again: only the gap fade's follow run (kind B) is
    assert [getattr(c, "mode", None) for c in stub["run"]] == ["follow"]
    assert summary["random_entries"]["available"] is True
    assert (out / "report.html").is_file()
    assert "Skill vs trend, and bounds" in (out / "report.html").read_text(encoding="utf-8")
    assert (
        json.loads((out / "skill_bounds.json").read_text(encoding="utf-8"))
        == summary["skill_bounds"]
    )
    assert summary["skill_bounds"]["daily_mean"]["n"] > 60  # include empty weekdays


def test_run_bounds_use_saved_mtm_and_cli_configuration(tmp_path, stub):
    from backtester.analytics.daily import weekdays as period_weekdays

    folder = make_run(tmp_path)
    (folder / "daily.csv").write_text(
        "date,net_r_mtm\n" + "".join(f"{d},1\n" for d in period_weekdays(START, END)),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    assert (
        tool.main(
            run_argv(
                folder,
                out,
                "--sampling",
                "permutation",
                "--block-days",
                "2",
                "--bounds-outer",
                "3",
                "--bounds-inner",
                "8",
                "--horizon-days",
                "4",
            )
        )
        == 0
    )
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    bounds = summary["drawdown_bounds"]
    assert bounds["source"] == "marked_to_market"
    assert bounds["config"]["outer"] == 3 and bounds["config"]["inner"] == 8
    assert bounds["config"]["horizon_days"] == 4 and bounds["config"]["block_days"] == 2
    assert all(v == 0 for row in bounds["rows"] for v in row["bounds_r"].values())
    assert summary["monte_carlo"]["config"]["sampling"] == "permutation"


def test_run_option_writes_a_trial_line_and_check_7_uses_the_trial_count(tmp_path, stub):
    from backtester.analytics.trial_log import append, count_only, family_trials, read_all

    append(count_only("gap_fade", "gap_fade", 9, "earlier variants"))
    folder = make_run(tmp_path)
    tool.main(run_argv(folder, tmp_path / "out"))
    (line,) = [r for r in read_all() if r.count == 1]
    assert line.family == "gap_fade" and line.source == "run" and line.trades == 120
    assert len(family_trials("gap_fade")) == 2
    summary = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert summary["deflated"]["n_trials"] == 10 and summary["deflated"]["family"] == "gap_fade"
    assert "deflated_sharpe" not in summary["verdict"]["not_available"]


def test_run_option_again_is_not_a_new_trial_and_family_overrides(tmp_path, stub):
    from backtester.analytics.trial_log import family_trials, read_all

    folder = make_run(tmp_path)
    tool.main(run_argv(folder, tmp_path / "out"))
    tool.main(run_argv(folder, tmp_path / "out"))
    assert len(read_all()) == 1
    tool.main(run_argv(folder, tmp_path / "out", "--family", "mine"))
    assert len(family_trials("mine")) == 1 and len(read_all()) == 2


def test_run_option_other_strategy_has_no_kind_b(tmp_path, stub):
    folder = make_run(tmp_path, strategy="ny_index_sweep")
    tool.main(run_argv(folder, tmp_path / "out"))
    assert stub["run"] == []
    summary = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert summary["random_entries"]["available"] is False and summary["meta"]["trades"] == 120


def test_run_option_default_out_is_the_runs_folder_under_monte_carlo(tmp_path, stub):
    folder = make_run(tmp_path)
    args = parse_args(["--run", folder.name, "--results-dir", str(folder.parent)])
    assert tool.default_out(args) == folder.parent / "monte_carlo" / folder.name


def test_run_option_unknown_run_is_a_clear_error(tmp_path, stub):
    with pytest.raises(SystemExit) as e:
        tool.main(["--run", "nope", "--results-dir", str(tmp_path)])
    assert "nope" in str(e.value)


# --- gap momentum: kind B coin flips the side (ROADMAP 11.12) -------------------------------------


def test_gap_momentum_kind_b_runs_the_fade_side_on_the_same_days(tmp_path, stub):
    assert tool.main(argv(tmp_path, "--paths", "0", strategy="gap_momentum")) == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["random_entries"]["available"] is True
    assert [c.side for c in stub["run"][:2]] == ["momentum", "fade"]
    assert {c.mode for c in stub["run"][:2]} == {"index"}


def test_set_overrides_the_strategy_defaults_and_goes_into_the_trial_log(tmp_path, stub):
    from datetime import time

    from backtester.analytics.trial_log import family_trials

    extra = ("--paths", "0", "--set", "entry_z=0.25", "stop_atr=2", "exit_time=11:00", "mode=fx")
    assert tool.main(argv(tmp_path, *extra, strategy="gap_momentum")) == 0
    cfg = stub["run"][0]
    assert (cfg.entry_z, cfg.stop_atr, cfg.exit_time, cfg.mode) == (0.25, 2.0, time(11), "fx")
    assert stub["run"][1].side == "fade" and stub["run"][1].entry_z == 0.25
    [line] = family_trials("gap_momentum")
    assert line.settings["entry_z"] == 0.25


def test_set_refuses_an_unknown_setting_or_a_bad_item():
    with pytest.raises(SystemExit):
        tool.apply_overrides(tool.default_config("gap_momentum"), ["nope=1"])
    with pytest.raises(SystemExit):
        tool.apply_overrides(tool.default_config("gap_momentum"), ["entry_z"])


def test_cache_dir_is_the_source_of_every_symbol(tmp_path, monkeypatch, stub):
    seen = []
    orig = tool.run_backtests

    def spy(symbols, start, end, settings, *a, **k):
        seen.append(k["sources"])
        return orig(symbols, start, end, settings, *a, **k)

    monkeypatch.setattr(tool, "run_backtests", spy)
    cache = tmp_path / "cache"
    assert tool.main(argv(tmp_path, "--paths", "0", "--cache-dir", str(cache))) == 0
    assert seen[0].cache_dir("NAS100") == seen[0].cache_dir("US500") == cache


def test_spread_table_option_goes_into_the_costs_of_every_run(tmp_path, monkeypatch, stub):
    assert (
        parse_args(["NAS100", "--start", "2020-01-01", "--end", "2020-02-01"]).spread_table is None
    )
    table = tmp_path / "spreads.json"
    table.write_text(json.dumps({
        "stat": "median", "note": "test",
        "values": {"NAS100": {"2021": {"9": 1.5}}},
    }), encoding="utf-8")  # fmt: skip
    seen = []
    orig = tool.run_backtests

    def spy(symbols, start, end, settings, *a, **k):
        seen.append(settings.engine.costs.spread_table)
        return orig(symbols, start, end, settings, *a, **k)

    monkeypatch.setattr(tool, "run_backtests", spy)
    assert tool.main(argv(tmp_path, "--paths", "0", "--spread-table", str(table))) == 0
    assert seen and all(t is not None for t in seen)
    seen.clear()
    assert tool.main(argv(tmp_path, "--paths", "0")) == 0
    assert all(t == CostConfig().spread_table for t in seen)  # no option: the default table


# ----- enum overrides and ready kind B / C results (ROADMAP 12.9) -------------------------------


def test_apply_overrides_sets_an_enum_setting_by_value():
    from backtester.strategy.opening_range.config import EntryMode

    cfg = tool.apply_overrides(
        tool.default_config("opening_range"), ["entry_mode=band", "band_atr=0.25"]
    )
    assert cfg.entry_mode is EntryMode.BAND and cfg.band_atr == 0.25
    with pytest.raises(SystemExit):
        tool.apply_overrides(tool.default_config("opening_range"), ["entry_mode=nope"])


def test_build_summary_takes_ready_kind_b_and_c_results():
    from backtester.analytics.random_baseline import RandomBaselineResult
    from backtester.analytics.random_fills import RandomFillsResult
    from backtester.runner import RunSettings

    trades = [trade("NAS100", d, 1.0 if i % 3 else -0.8) for i, d in enumerate(weekdays())]
    base = RandomBaselineResult(10.0, (1.0, 2.0), 97.0, 1.5, 1.0, 2.0, 30)
    fills = RandomFillsResult(10.0, (7.0, 8.0), 7.0, 7.5, 8.0)
    s = tool.build_summary(
        trades, None, {"strategy": "x", "symbols": ["NAS100"], "start": START, "end": END,
                       "source": "mt5"},
        RunSettings(), ToolConfig(runs=20), log=lambda *_: None, baseline=base, fills=fills,
    )  # fmt: skip
    assert s["random_entries"]["percentile"] == 97.0 and s["random_fills"]["p50"] == 7.5
    checks = {c.key: c for c in s["verdict"].checks}
    assert checks["random_entries"].passed and checks["random_fills"].value == 7.5


def test_monkey_percentile_in_verdict_and_html():
    from backtester.runner import RunSettings

    trades = [trade("NAS100", d, 0.5) for d in weekdays()[:3]]
    monkeys = {
        "available": True,
        "trades": 3,
        "config": {"runs": 20},
        "passed": False,
        "kinds": [
            {
                "kind": 1,
                "name": "random entry",
                "passed": False,
                "net_r": {"real": 1.5, "median": 0.0, "p5": -1.0, "p95": 2.0, "percentile": 94.0},
                "max_dd_r": {"real": 0.0, "median": 1.0, "p5": 0.0, "p95": 3.0, "percentile": 89.0},
            }
        ],
    }
    summary = tool.build_summary(
        trades,
        None,
        {
            "strategy": "trend_following",
            "symbols": ["NAS100"],
            "start": START,
            "end": END,
            "source": "histdata",
        },
        RunSettings(),
        ToolConfig(runs=2),
        log=lambda *_: None,
        monkeys=monkeys,
    )
    check = next(c for c in summary["verdict"].checks if c.key == "random_entries")
    assert check.available and check.value == 94 and not check.passed  # MC still needs 95
    rendered = tool.monkeys_html(summary)
    assert "Matched monkeys" in rendered and "94.0" in rendered and "89.0" in rendered
