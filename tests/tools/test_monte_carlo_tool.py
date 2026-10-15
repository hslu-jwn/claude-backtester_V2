"""Monte Carlo report tool: CLI, summary.json and report.html with a stubbed backtest.
Spec: risk-management.md > Monte Carlo report (ROADMAP 12.7)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.tools import monte_carlo as tool
from backtester.tools.monte_carlo import ToolConfig, parse_args, path_row

START, END = date(2021, 1, 4), date(2021, 4, 30)


def trade(symbol, day, r_net, r_gross=None, mode_bonus=0.0):
    entry = datetime(day.year, day.month, day.day, 14, 30, tzinfo=UTC)
    return SimpleNamespace(
        symbol=symbol, entry_time=entry, exit_time=entry + timedelta(hours=2),
        entry=100.0, initial_stop=99.0, exit_reason="signal", swap_r=0.0,
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
    assert check["available"] is False and check["passed"] is False
    assert "random_entries" not in summary["verdict"]["failed"]
    assert "random_entries" in summary["verdict"]["not_available"]
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
