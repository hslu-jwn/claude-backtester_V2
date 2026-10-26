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
from backtester.strategy.base import UnsupportedSymbolError
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
            spread_table=None,
            symbols=MappingProxyType(
                {**DEFAULT_SYMBOL_COSTS, "GOLD": DEFAULT_SYMBOL_COSTS["XAUUSD"]}
            ),
        )
    ),
)
# Spread and market entry slippage; commission 0.0007 % per side on actual fills (B4/B6).
# (FTMO's percentage fee since 2026-10-15; it was $6 / (0.9 x $100) before)
# the fixed spread 0.25 is scaled to the entry price 110 (rule of 2026-10-16: x price / reference)
SPREAD_AT_110 = 0.25 * 110.0 / DEFAULT_SYMBOL_COSTS["XAUUSD"].reference_price
SLIPPAGE_AT_110 = 0.1 * 110.0 / DEFAULT_SYMBOL_COSTS["XAUUSD"].reference_price
NET = (
    1.2
    - (SPREAD_AT_110 + SLIPPAGE_AT_110) / 0.9
    - 0.000007 * (110.0 + SPREAD_AT_110 + SLIPPAGE_AT_110 + 111.08) / 0.9
)


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


def test_unsupported_symbol_is_a_clean_one_line_error(monkeypatch, capsys):
    def refuse(*args, **kwargs):
        raise UnsupportedSymbolError("opening_range: no session for BTCUSD (SYMBOL_CLASS in x)")

    monkeypatch.setattr("backtester.run.run_backtests", refuse)
    argv = ["AUDUSD", "BTCUSD", "--start", "2026-01-05", "--end", "2026-01-06"]
    with pytest.raises(SystemExit) as e:
        main([*argv, "--strategy", "opening_range"])
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "opening_range: no session for BTCUSD" in err and "Traceback" not in err


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


# --- cancel, left-out symbols (ROADMAP 7.6, Backtest page) -------------------------------

import threading

from backtester.runner import RunCancelled
from backtester.strategy.opening_range.config import OpeningRangeConfig

OPENING = RunSettings(strategy=OpeningRangeConfig())


@pytest.fixture
def mixed(tmp_path):
    folder = tmp_path / "cache"
    for symbol in ("XAUUSD", "BTCUSD", "ETHUSD"):
        write_day(folder, symbol, MON, FULL)
    write_day(folder, "GOLD", TUE, FULL)
    return SymbolSources.single(folder, ["XAUUSD", "BTCUSD", "ETHUSD", "GOLD"])


def test_a_symbol_without_rules_is_left_out_with_a_note_when_others_can_run(mixed):
    result = run_backtests(["XAUUSD", "BTCUSD"], MON, MON, OPENING, mixed, workers=1)
    assert result.symbols == ("XAUUSD",) and list(result.runs) == ["XAUUSD"]
    assert len(result.notes) == 1
    assert result.notes[0].startswith("BTCUSD left out: opening_range: no session for BTCUSD")


def test_a_symbol_without_data_in_the_range_is_left_out_with_a_note(mixed):
    result = run_backtests(["XAUUSD", "GOLD"], MON, MON, SETTINGS, mixed, workers=1)
    assert result.symbols == ("XAUUSD",)
    assert result.notes == ("GOLD left out: GOLD: no cached day between 2026-01-05 and 2026-01-05",)


def test_when_no_symbol_can_run_the_error_is_raised(mixed):
    with pytest.raises(UnsupportedSymbolError, match="no session for BTCUSD"):
        run_backtests(["BTCUSD"], MON, MON, OPENING, mixed, workers=1)
    with pytest.raises(ValueError, match="no cached day"):
        run_backtests(["XAUUSD", "GOLD"], WED, WED, SETTINGS, mixed, workers=1)
    with pytest.raises(UnsupportedSymbolError) as e:  # two reasons in one message
        run_backtests(["BTCUSD", "ETHUSD"], MON, MON, OPENING, mixed, workers=1)
    assert "BTCUSD" in str(e.value) and "ETHUSD" in str(e.value)


def test_left_out_symbols_are_in_the_written_notes(mixed, tmp_path):
    run = start_run(["XAUUSD", "BTCUSD"], MON, MON, OPENING, mixed, tmp_path / "r", workers=1)
    run.join(60)
    assert run.error is None
    notes = json.loads((run.folder / "summary.json").read_text())["notes"]
    assert any(n.startswith("BTCUSD left out") for n in notes)
    assert run.folder.name.endswith("_XAUUSD")  # only the symbols that ran


def test_cancel_before_start_stops_the_run(cache):
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(RunCancelled):
        run_backtests(["XAUUSD"], MON, MON, SETTINGS, cache, workers=1, cancel=cancel)


def test_cancel_during_the_run_stops_at_the_next_progress_step(cache):
    cancel, calls = threading.Event(), []

    def progress(done, total):
        calls.append(done)
        cancel.set()

    with pytest.raises(RunCancelled):
        run_backtests(["XAUUSD", "GOLD"], MON, TUE, SETTINGS, cache, progress, 1, cancel)
    assert len(calls) == 1  # the second symbol never ran


def test_cancel_stops_parallel_workers(cache):
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(RunCancelled):
        run_backtests(["XAUUSD", "GOLD"], MON, TUE, SETTINGS, cache, workers=2, cancel=cancel)


def test_cancelled_background_run_writes_nothing(cache, tmp_path):
    out = tmp_path / "results"
    run = start_run(["XAUUSD"], MON, MON, SETTINGS, cache, out, workers=1)
    run.cancel()  # may land before or after the end of this tiny run
    run.join(60)
    if run.cancelled:
        assert run.folder is None and run.error is None
        assert not out.exists() or not list(out.iterdir())
    else:
        assert run.folder is not None


def test_a_failed_write_leaves_no_half_folder(cache, tmp_path, monkeypatch):
    result = run_backtests(["XAUUSD"], MON, MON, SETTINGS, cache, workers=1)
    monkeypatch.setattr("backtester.runner._dump", lambda *a: (_ for _ in ()).throw(OSError("x")))
    with pytest.raises(OSError):
        write_results(result, tmp_path / "r", run_id="fail")
    assert not (tmp_path / "r" / "fail").exists()


# --- loading progress, cancel while loading, unmapped symbols (ROADMAP 7.6) -------------------


def test_loading_progress_is_monotonic_and_reaches_the_total(cache):
    load, run = [], []
    run_backtests(
        ["XAUUSD", "GOLD"], MON, TUE, SETTINGS, cache, lambda d, t: run.append(d), 1,
        load_progress=lambda d, t: load.append((d, t)),
    )  # fmt: skip
    assert load and load[-1][0] == load[-1][1] > 0
    assert len({t for _, t in load}) == 1  # the total never changes
    assert [d for d, _ in load] == sorted(d for d, _ in load)
    assert all(d <= t for d, t in load)
    assert run  # the run phase came after


def test_loading_progress_counts_a_symbol_left_out(mixed):
    load = []
    run_backtests(
        ["XAUUSD", "BTCUSD"], MON, MON, OPENING, mixed, workers=1,
        load_progress=lambda d, t: load.append((d, t)),
    )  # fmt: skip
    assert load[-1][0] == load[-1][1]  # the skipped symbol's share is done too


def test_cancel_while_loading_stops_before_the_run_phase(cache):
    cancel, run, load = threading.Event(), [], []

    def on_load(done, total):
        load.append(done)
        cancel.set()

    with pytest.raises(RunCancelled):
        run_backtests(
            ["XAUUSD", "GOLD"], MON, TUE, SETTINGS, cache, lambda d, t: run.append(d), 1, cancel,
            load_progress=on_load,
        )  # fmt: skip
    assert len(load) == 1 and run == []  # stopped at the very next loading step


def test_cancelled_while_loading_background_run_saves_nothing(cache, tmp_path, monkeypatch):
    from backtester import runner

    started, release = threading.Event(), threading.Event()
    real = runner.candles_from_frame

    def slow(frame, *a, **k):
        started.set()
        release.wait(10)
        return real(frame, *a, **k)

    monkeypatch.setattr(runner, "candles_from_frame", slow)
    out = tmp_path / "results"
    run = start_run(["XAUUSD"], MON, MON, SETTINGS, cache, out, workers=1)
    assert started.wait(10)
    assert run.total == 0  # still loading
    run.cancel()
    release.set()
    run.join(30)
    assert run.cancelled and run.folder is None and run.error is None
    assert not out.exists() or not list(out.iterdir())


def test_background_run_reports_loading_progress(cache, tmp_path):
    run = start_run(["XAUUSD"], MON, MON, SETTINGS, cache, tmp_path / "r", workers=1)
    run.join(60)
    assert run.error is None and run.load_total > 0 and run.load_done == run.load_total


def test_an_unmapped_symbol_is_left_out_with_a_readable_note(mixed):
    result = run_backtests(["XAUUSD", "NOPE"], MON, MON, SETTINGS, mixed, workers=1)
    assert result.symbols == ("XAUUSD",)
    assert len(result.notes) == 1
    assert result.notes[0].startswith("NOPE left out: no data source for NOPE")
    assert "'" not in result.notes[0].split(":")[1]  # no KeyError quotes around the text


def test_when_the_only_symbol_is_unmapped_the_error_is_raised(mixed):
    with pytest.raises(KeyError, match="no data source for NOPE"):
        run_backtests(["NOPE"], MON, MON, SETTINGS, mixed, workers=1)
    with pytest.raises(ValueError, match="NOPE.*NOPE2"):
        run_backtests(["NOPE", "NOPE2"], MON, MON, SETTINGS, mixed, workers=1)
