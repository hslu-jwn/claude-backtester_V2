"""Gap fade walk-forward tool with stubbed backtests (no real data).
Spec: ROADMAP 11.7 / 12.3, strategy-gap-fade.md."""

from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from backtester.core.models import Direction
from backtester.strategy.gap_fade.config import GapFadeConfig
from backtester.tools.archive import gap_fade_walk_forward as tool
from backtester.tools.archive.gap_fade_grid import variant_name

DEFAULT = variant_name(GapFadeConfig())
# best every year; its three exit times tie, the first in the variant order (11:00) wins
GOOD = GapFadeConfig(min_gap_atr=0.25, max_gap_atr=0.5, stop_gap_mult=1.5, exit_time=time(11, 0))


def trade(symbol, year, day, r):
    entry = datetime(year, 3, 1, 14, 30, tzinfo=UTC) + timedelta(days=day)
    return SimpleNamespace(
        symbol=symbol, direction=Direction.BULLISH, entry_time=entry,
        exit_time=entry + timedelta(hours=2), entry=100.0, initial_stop=99.0,
        exit_reason="signal", swap_r=0.0, r_gross=r + 0.05, r_net=r, planned_r=None,
    )  # fmt: skip


@pytest.fixture
def stub(monkeypatch):
    calls = []

    def fake_run(symbols, start, end, settings, *args, **kwargs):
        cfg = settings.strategy
        calls.append((cfg.mode, cfg.min_gap_atr, cfg.max_gap_atr, cfg.stop_gap_mult))
        good = (cfg.min_gap_atr, cfg.max_gap_atr, cfg.stop_gap_mult) == (0.25, 0.5, 1.5)
        sign = -1.0 if cfg.mode == "follow" else 1.0
        trades = tuple(
            trade(s, y, d, sign * (0.4 if good else (-0.1 if d % 2 else 0.05)))
            for s in symbols for y in range(2018, 2023) for d in range(40)
        )  # fmt: skip
        return SimpleNamespace(trades=trades, runs={s: SimpleNamespace() for s in symbols})

    monkeypatch.setattr(tool, "run_backtests", fake_run)
    monkeypatch.setattr(tool, "last_cached_day", lambda symbols, sources=None: date(2022, 12, 31))
    return calls


def args(out, *extra):
    return ["--runs", "20", "--out", str(out), *extra]


def run_tool(out):
    return tool.main(args(out), log=lambda *_: None)


def test_writes_years_csv_summary_and_two_reports(tmp_path, stub):
    assert run_tool(tmp_path) == 0
    rows = list(csv.DictReader((tmp_path / "years.csv").open(encoding="utf-8")))
    assert list(rows[0]) == [
        "year", "chosen_variant", "train_net_r", "test_net_r", "default_net_r", "trades",
    ]  # fmt: skip
    assert [r["year"] for r in rows] == ["2019", "2020", "2021", "2022"]
    assert all(r["chosen_variant"] == variant_name(GOOD) for r in rows)
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    chained_net = sum(float(r["test_net_r"]) for r in rows)
    assert summary["chained_net_r"] == pytest.approx(chained_net)
    assert summary["chained_trades"] == sum(int(r["trades"]) for r in rows)
    assert summary["default_variant"] == DEFAULT
    for sub in ("monte_carlo", "monte_carlo_default"):
        assert (tmp_path / sub / "report.html").exists()
        assert (tmp_path / sub / "summary.json").exists()
    mc = json.loads((tmp_path / "monte_carlo" / "summary.json").read_text(encoding="utf-8"))
    assert mc["meta"]["trades"] == summary["chained_trades"]
    assert mc["random_paths"] is None and mc["random_entries"]["available"] is True
    assert mc["meta"]["start"] == "2019-01-01"


def test_runs_each_variant_once_and_follow_only_for_chosen(tmp_path, stub):
    run_tool(tmp_path)
    fade = [c for c in stub if c[0] == "fade"]
    follow = [c for c in stub if c[0] == "follow"]
    assert len(fade) == 36
    # the chosen variant + the default variant (for the comparison report)
    assert len(follow) == 2 and len(set(follow)) == 2


def test_chained_trades_are_the_chosen_variants_test_year_trades(tmp_path, stub):
    run_tool(tmp_path)
    mc = json.loads((tmp_path / "monte_carlo" / "summary.json").read_text(encoding="utf-8"))
    # GOOD has 40 trades per symbol and year, 2 symbols, 4 test years
    assert mc["meta"]["trades"] == 40 * 2 * 4
    default = json.loads(
        (tmp_path / "monte_carlo_default" / "summary.json").read_text(encoding="utf-8")
    )
    assert default["meta"]["trades"] == 40 * 2 * 4
    assert default["meta"]["start"] == "2019-01-01"
