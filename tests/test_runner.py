"""Backtest runs and the results folder. Spec: ROADMAP.md › 3.4.

Data: the hand-built London / New York day of the strategy tests (scenario.py), written as
an M1 cache (one minute per 5m candle) into a temporary folder:
- XAUUSD on Monday 2026-01-05: one long, entry 110.0 at 13:40, SL 109.1, TP 111.08 (1.2R),
  hit at 13:45.
- GOLD (same candles one day later, Tuesday 2026-01-06): the same trade a day later. GOLD
  needs its own doji threshold and costs in the settings.
"""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import MappingProxyType

import pytest
from m1_frames import m1

sys.path.append(str(Path(__file__).parent / "strategy" / "session_zone_sweep"))
import scenario
from scenario import LONDON, NY_SETUP, TO_TARGET, doji

from backtester.core.models import Timeframe
from backtester.data.adapters.cache_adapter import MissingCacheError
from backtester.data.cache import cache_path
from backtester.data.sources import SymbolSources
from backtester.detectors.settings import DetectorSettings
from backtester.detectors.swings import SwingConfig
from backtester.engine.backtest import EngineConfig
from backtester.engine.costs import DEFAULT_SYMBOL_COSTS, CostConfig
from backtester.engine.trade import ExitReason
from backtester.run import main
from backtester.runner import (
    RunSettings,
    jsonable,
    run_backtests,
    start_run,
    write_results,
)
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.trend_following.config import TrendFollowingConfig

FULL = LONDON + NY_SETUP + TO_TARGET
MON, TUE, WED = date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7)
SETTINGS = RunSettings(  # read-only mappings like the defaults (pickled for the workers)
    strategy=SessionZoneSweepConfig(),
    detectors=DetectorSettings(
        swings=SwingConfig(doji_max_body=MappingProxyType({"XAUUSD": 0.065, "GOLD": 0.065}))
    ),
    engine=EngineConfig(
        costs=CostConfig(
            symbols=MappingProxyType(
                {**DEFAULT_SYMBOL_COSTS, "GOLD": DEFAULT_SYMBOL_COSTS["XAUUSD"]}
            )
        )
    ),
)
# spread 0.25 / 1R 0.9; XAUUSD commission 0.0007 % per side of entry 110.0 and exit 111.08
# (FTMO's percentage fee since 2026-10-15; it was $6 / (0.9 x $100) before)
# the fixed spread 0.25 is scaled to the entry price 110 (rule of 2026-10-16: x price / reference)
SPREAD_AT_110 = 0.25 * 110.0 / DEFAULT_SYMBOL_COSTS["XAUUSD"].reference_price
NET = 1.2 - SPREAD_AT_110 / 0.9 - 0.000007 * (110.0 + 111.08) / 0.9


def write_day(cache: Path, symbol: str, day: date, ohlc) -> None:
    """The 5m candles from 07:30 on `day`, one cached M1 row each."""
    start = datetime.combine(day, scenario.START.timetz())
    rows = [
        (f"{c.ts:%H:%M}", c.open, c.high, c.low, c.close, 1.0, 0.0)
        for c in scenario.candles(ohlc, start)
    ]
    path = cache_path(cache, symbol, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    m1(*rows, day=day.isoformat()).to_parquet(path, index=False)


@pytest.fixture
def cache(tmp_path):
    folder = tmp_path / "cache"
    write_day(folder, "XAUUSD", MON, FULL)
    write_day(folder, "GOLD", TUE, FULL)
    return SymbolSources.single(folder, ["XAUUSD", "GOLD"])


def test_two_symbols_per_symbol_and_merged_in_time_order(cache):
    result = run_backtests(["GOLD", "XAUUSD"], MON, TUE, SETTINGS, cache, workers=1)
    assert [t.symbol for t in result.trades] == ["XAUUSD", "GOLD"]  # Monday, then Tuesday
    for symbol, day in (("XAUUSD", MON), ("GOLD", TUE)):
        [t] = result.runs[symbol].trades
        assert t.entry_time == datetime.combine(day, datetime.min.time(), UTC) + timedelta(
            hours=13, minutes=40
        )
        assert (t.entry, t.initial_stop) == (110.0, 109.1)
        assert t.exit_reason is ExitReason.TAKE_PROFIT and t.r_net == pytest.approx(NET)
    summary = result.summary()
    assert summary["per_symbol"]["GOLD"]["trades"] == 1
    assert summary["combined"]["trades"] == 2
    assert summary["combined"]["net_r_net"] == pytest.approx(2 * NET)
    assert summary["combined"]["win_rate"] == 1.0


def test_uncached_days_at_the_ends_are_left_out_with_a_note(cache):
    result = run_backtests(["XAUUSD", "GOLD"], MON, TUE, SETTINGS, cache, workers=1)
    xau, gold = result.runs["XAUUSD"], result.runs["GOLD"]
    assert (xau.first_day, xau.last_day, gold.first_day, gold.last_day) == (MON, MON, TUE, TUE)
    assert xau.notes == ("XAUUSD: 2026-01-06..2026-01-06 not cached, left out",)
    assert gold.notes == ("GOLD: 2026-01-05..2026-01-05 not cached, left out",)


def test_a_gap_inside_the_range_is_an_error(cache):
    write_day(Path(cache.cache_dir("XAUUSD")), "XAUUSD", WED, [doji(110.0)] * 12)
    with pytest.raises(MissingCacheError):
        run_backtests(["XAUUSD"], MON, WED, SETTINGS, cache)


def test_no_cached_day_in_the_range_is_an_error(cache):
    with pytest.raises(ValueError, match="no cached day"):
        run_backtests(["XAUUSD"], WED, WED, SETTINGS, cache)


def test_warm_up_days_run_but_their_trades_and_sessions_are_dropped(cache):
    folder = Path(cache.cache_dir("XAUUSD"))
    write_day(folder, "XAUUSD", TUE, [doji(112.8)] * 12)  # quiet Tuesday morning
    result = run_backtests(["XAUUSD"], TUE, TUE, SETTINGS, cache)
    run = result.runs["XAUUSD"]
    assert (run.warmup_from, run.first_day) == (MON, TUE)
    assert run.trades == ()  # Monday's trade was in the warm-up
    # Monday's New York session ends at Tuesday 00:00, the range's start: not in the run
    assert all(s["trading_date"] != "2026-01-05" for s in run.sessions)
    no_warmup = run_backtests(["XAUUSD"], TUE, TUE, replace(SETTINGS, warmup_days=0), cache)
    assert no_warmup.runs["XAUUSD"].warmup_from == TUE


def test_a_strategy_can_ask_for_more_warm_up_days_than_the_setting(cache):
    """Strategy 4 needs its indicator history (`Strategy.min_warmup_days`), setting is 0."""
    folder = Path(cache.cache_dir("XAUUSD"))
    write_day(folder, "XAUUSD", TUE, [doji(112.8)] * 12)
    settings = replace(SETTINGS, strategy=TrendFollowingConfig(timeframe=Timeframe.M15))
    result = run_backtests(["XAUUSD"], TUE, TUE, replace(settings, warmup_days=0), cache)
    assert result.runs["XAUUSD"].warmup_from == MON  # 0 days set, the strategy asked for more
    result = run_backtests(["XAUUSD"], TUE, TUE, replace(SETTINGS, warmup_days=0), cache)
    assert result.runs["XAUUSD"].warmup_from == TUE  # strategy 1 asks for none


def test_progress_reports_5m_candles_up_to_the_total(cache):
    calls = []
    run_backtests(
        ["XAUUSD", "GOLD"], MON, TUE, SETTINGS, cache, lambda d, t: calls.append((d, t)), 1
    )
    total = 2 * len(FULL)
    assert calls[-1] == (total, total)
    assert [d for d, _ in calls] == sorted(d for d, _ in calls)


def test_parallel_processes_give_the_same_result(cache):
    calls = []
    progress = lambda d, t: calls.append((d, t))
    parallel = run_backtests(["XAUUSD", "GOLD"], MON, TUE, SETTINGS, cache, progress, 2)
    serial = run_backtests(["XAUUSD", "GOLD"], MON, TUE, SETTINGS, cache, workers=1)
    assert parallel.trades == serial.trades
    assert parallel.runs["GOLD"].sessions == serial.runs["GOLD"].sessions
    assert calls[-1] == (2 * len(FULL), 2 * len(FULL))


def test_results_folder(cache, tmp_path):
    result = run_backtests(["XAUUSD", "GOLD"], MON, TUE, SETTINGS, cache, workers=1)
    folder = write_results(result, tmp_path / "results", "test-run")
    assert folder == tmp_path / "results" / "test-run"

    with open(folder / "trades.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert [(r["id"], r["symbol"], r["session"]) for r in rows] == [
        ("1", "XAUUSD", "new_york 2026-01-05"),
        ("2", "GOLD", "new_york 2026-01-06"),
    ]
    assert rows[0]["direction"] == "long" and rows[0]["exit_reason"] == "take_profit"
    assert float(rows[0]["r_net"]) == pytest.approx(NET)
    assert float(rows[0]["planned_rr"]) == pytest.approx(1.2)
    assert json.loads(rows[0]["parts"])[0]["reason"] == "take_profit"
    assert rows[0]["confluence"] in {"fvg", "order_block", "bpr", "equilibrium"}
    assert rows[0]["confluence"] in rows[0]["reason"]

    settings = json.loads((folder / "settings.json").read_text())
    assert settings["run"]["symbols"] == ["XAUUSD", "GOLD"]
    assert settings["run"]["start"] == "2026-01-05" and settings["run"]["warmup_days"] == 14
    assert settings["strategy"]["name"] == "session_zone_sweep"
    assert settings["strategy"]["min_rr"] == 1.2
    assert settings["strategy"]["zone_timeframe"] == "M30"
    assert settings["strategy"]["confluence_kinds"] == ["BPR", "BREAKER", "FVG", "ORDER_BLOCK"]
    assert settings["detectors"]["swings"]["doji_max_body"]["GOLD"] == 0.065
    assert settings["engine"]["costs"]["symbols"]["GOLD"]["spread"] == 0.25
    assert settings["engine"]["sessions"]["london"]["zone"] == "Europe/London"

    summary = json.loads((folder / "summary.json").read_text())
    assert summary["run_id"] == "test-run"
    assert datetime.fromisoformat(summary["created"]).tzinfo is not None
    assert summary["combined"]["trades"] == 2
    assert summary["per_symbol"]["XAUUSD"]["net_r_gross"] == pytest.approx(1.2)
    assert summary["days"]["GOLD"] == {
        "first": "2026-01-06",
        "last": "2026-01-06",
        "warmup_from": "2026-01-06",
    }
    assert len(summary["notes"]) == 2

    sessions = json.loads((folder / "sessions.json").read_text())
    [ny] = [s for s in sessions["XAUUSD"] if s["session"] == "new_york"]
    assert ny["trades"] == [1]
    assert {z["side"] for z in ny["zones"]} == {"high", "low"}
    assert any(c["traded"] for c in ny["confluences"])
    assert [s["trades"] for s in sessions["GOLD"] if s["session"] == "new_york"] == [[2]]


def test_run_ids_are_never_reused(cache, tmp_path):
    result = run_backtests(["XAUUSD"], MON, MON, SETTINGS, cache)
    first = write_results(result, tmp_path)
    second = write_results(result, tmp_path)
    assert first != second and first.name.endswith("_XAUUSD")
    assert second.name == first.name + "_2"


def test_background_run_writes_the_results(cache, tmp_path):
    run = start_run(["XAUUSD"], MON, MON, SETTINGS, cache, tmp_path / "results")
    run.join(60)
    assert run.finished and run.error is None
    assert (run.folder / "summary.json").exists()
    assert run.done == run.total == len(FULL)


def test_background_run_hands_errors_over(cache, tmp_path):
    run = start_run(["XAUUSD"], WED, WED, SETTINGS, cache, tmp_path)
    run.join(60)
    assert isinstance(run.error, ValueError) and run.folder is None


def test_settings_json_is_plain_json():
    data = jsonable(RunSettings())
    assert json.loads(json.dumps(data)) == data


def test_command_prints_the_summary(cache, tmp_path, capsys):
    folder = cache.cache_dir("XAUUSD")
    argv = ["xauusd", "--start", "2026-01-05", "--end", "2026-01-05"]
    assert main([*argv, "--cache-dir", str(folder), "--out", str(tmp_path / "out")]) == 0
    out = capsys.readouterr().out
    assert "XAUUSD" in out and "combined" in out and "100.0%" in out
    assert len(list((tmp_path / "out").iterdir())) == 1
    (run,) = (tmp_path / "out").iterdir()
    assert json.loads((run / "settings.json").read_text())["preset"] == "Default"


def test_command_runs_a_preset_and_records_its_name(cache, tmp_path, capsys):
    from backtester.presets import save_preset

    no_costs = RunSettings(engine=SETTINGS.engine, warmup_days=SETTINGS.warmup_days)
    save_preset("No costs", no_costs, tmp_path / "presets")
    folder = cache.cache_dir("XAUUSD")
    argv = ["xauusd", "--start", "2026-01-05", "--end", "2026-01-05", "--cache-dir", str(folder)]
    argv += ["--out", str(tmp_path / "out"), "--presets-dir", str(tmp_path / "presets")]
    assert main([*argv, "--preset", "No costs"]) == 0
    assert main([*argv, "--preset", "No costs", "--warmup-days", "3"]) == 0
    presets = sorted(
        json.loads((r / "settings.json").read_text())["preset"]
        for r in (tmp_path / "out").iterdir()
    )
    assert presets == ["No costs", "No costs (modified)"]
    with pytest.raises(SystemExit):
        main([*argv, "--preset", "missing"])


def test_per_year_printout(cache, tmp_path, capsys):
    folder = cache.cache_dir("XAUUSD")
    argv = ["xauusd", "--start", "2026-01-05", "--end", "2026-01-05", "--cache-dir", str(folder)]
    assert main([*argv, "--out", str(tmp_path / "out")]) == 0
    out = capsys.readouterr().out
    assert "trades    win    net R  max DD" in out and "\n2026 " in out


def test_command_logs_the_run_as_a_trial(cache, tmp_path):
    from backtester.analytics.trial_log import family_trials

    folder = cache.cache_dir("XAUUSD")
    argv = ["xauusd", "--start", "2026-01-05", "--end", "2026-01-05", "--cache-dir", str(folder)]
    assert main([*argv, "--out", str(tmp_path / "out")]) == 0
    assert main([*argv, "--out", str(tmp_path / "out"), "--family", "mine"]) == 0
    (line,) = family_trials("session_zone_sweep")
    assert line.strategy == "session_zone_sweep" and line.symbols == ["XAUUSD"]
    assert line.start == "2026-01-05" and len(family_trials("mine")) == 1
    assert len(list((tmp_path / "out").iterdir())) == 2  # the log is not in the run folders
