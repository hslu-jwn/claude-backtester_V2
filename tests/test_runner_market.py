"""Runner dependency bundle loading without changing legacy symbol semantics."""

from datetime import date, timedelta

import pytest
from engine.test_market_backtest import Observer
from m1_frames import m1

from backtester import runner
from backtester.core.market import ReferenceInput
from backtester.core.models import Timeframe as TF
from backtester.data.resample import DayBoundary
from backtester.data.sources import SymbolSources
from backtester.strategy.base import Strategy

DAY = date(2026, 1, 5)


def test_explicit_references_load_bundle_and_missing_days_are_status_not_fabrication(
    tmp_path, monkeypatch,
):
    from backtester.data.cache import cache_path

    for symbol in ("TEST", "B"):
        path = cache_path(tmp_path, symbol, DAY)
        path.parent.mkdir(parents=True, exist_ok=True)
        m1(*[(f"10:{i:02}", 100, 101, 99, 100, 1, 0) for i in range(10)],
           day=DAY.isoformat()).to_parquet(path, index=False)
    sources = SymbolSources.single(tmp_path, ["TEST", "B", "EMPTY"])
    made = []

    def factory(*args):
        strategy = Observer()
        made.append(strategy)
        return strategy

    monkeypatch.setattr(runner, "make_strategy", factory)
    refs = (ReferenceInput("B", "b", (TF.M1, TF.D1), max_age=timedelta(minutes=1),
                           boundary=DayBoundary.NEW_YORK_17),
            ReferenceInput("EMPTY", "missing", (TF.M1,), max_age=timedelta(minutes=1)))
    result = runner.run_backtests(["TEST"], DAY, DAY, sources=sources, workers=1,
                                 references=refs)
    assert result.symbols == ("TEST",) and not result.trades
    seen = next(s.seen for s in made if s.seen)
    assert seen[0].views["EMPTY"][TF.M1] is None
    assert seen[0].views["B"][TF.M1].cursor == 4
    assert seen[0].views["B"][TF.D1] is None
    assert any("reference" in note for note in result.runs["TEST"].notes)
    assert any("EMPTY/M1: no closed observations" in note for note in result.runs["TEST"].notes)


def test_references_rejected_before_loading_for_legacy(monkeypatch):
    class Legacy(Strategy):
        base_timeframe = TF.M1
        timeframes = (TF.M1,)

        def on_candle(self, now, views):
            return []

    monkeypatch.setattr(runner, "make_strategy", lambda *args: Legacy())
    with pytest.raises(ValueError, match="market"):
        runner.run_backtests(["TEST"], DAY, DAY, workers=1,
                             references=(ReferenceInput("B", "b", (TF.M1,),
                                                        max_age=timedelta(minutes=1)),))


# --- 1b: references declared by the strategy (design/multi-symbol.md > A, Delivery 1b) ---


class Declared(Observer):
    references = (ReferenceInput("B", "b", (TF.M1,), max_age=timedelta(minutes=1)),)

    def on_market_candle(self, now, views, market):
        super().on_market_candle(now, views, market)
        return []  # observation only: no cost table needed for TEST


def _cache(tmp_path, symbol, *days):
    from backtester.data.cache import cache_path

    for day in days:
        path = cache_path(tmp_path, symbol, day)
        path.parent.mkdir(parents=True, exist_ok=True)
        m1(*[(f"10:{i:02}", 100, 101, 99, 100, 1, 0) for i in range(10)],
           day=day.isoformat()).to_parquet(path, index=False)


def test_strategy_declared_references_load_in_run_and_research_paths(tmp_path, monkeypatch):
    _cache(tmp_path, "TEST", DAY)
    _cache(tmp_path, "B", DAY)
    sources = SymbolSources.single(tmp_path, ["TEST", "B"])
    made = []
    monkeypatch.setattr(runner, "make_strategy", lambda *a: made.append(Declared()) or made[-1])
    result = runner.run_backtests(["TEST"], DAY, DAY, sources=sources, workers=1)
    assert next(s.seen for s in made if s.seen)[-1].views["B"][TF.M1] is not None
    assert any("reference inputs: B" in n for n in result.runs["TEST"].notes)
    made.clear()
    # the research runner's path (iter_symbol_runs -> _chunk_symbol_run -> _load)
    (_, many), = runner.run_backtests_many(["TEST"], DAY, DAY, [runner.RunSettings()],
                                           sources, workers=1)
    assert next(s.seen for s in made if s.seen)[-1].views["B"][TF.M1] is not None
    assert any("reference inputs: B" in n for n in many.runs["TEST"].notes)


def test_legacy_strategy_loads_no_reference(tmp_path, monkeypatch):
    class Legacy(Strategy):
        base_timeframe = TF.M1
        timeframes = (TF.M1,)

        def on_candle(self, now, views):
            return []

    _cache(tmp_path, "TEST", DAY)
    sources = SymbolSources.single(tmp_path, ["TEST"])
    monkeypatch.setattr(runner, "make_strategy", lambda *a: Legacy())
    job = runner._load(sources, "TEST", DAY, DAY, runner.RunSettings())
    assert job.references == () and job.reference_series == ()


def test_reference_data_ends_with_the_primary_range(tmp_path, monkeypatch):
    nxt = DAY + timedelta(days=1)
    _cache(tmp_path, "TEST", DAY)
    _cache(tmp_path, "B", DAY, nxt)
    sources = SymbolSources.single(tmp_path, ["TEST", "B"])
    monkeypatch.setattr(runner, "make_strategy", lambda *a: Declared())
    job = runner._load(sources, "TEST", DAY, DAY, runner.RunSettings())
    assert [s.symbol for s in job.reference_series] == ["B"]
    assert max(c.ts for s in job.reference_series for c in s._candles).date() == DAY


def test_blocked_decisions_are_counted_in_notes(tmp_path, monkeypatch):
    _cache(tmp_path, "TEST", DAY)
    sources = SymbolSources.single(tmp_path, ["TEST", "B"])  # B has no data: always blocked
    monkeypatch.setattr(runner, "make_strategy", lambda *a: Declared())
    result = runner.run_backtests(["TEST"], DAY, DAY, sources=sources, workers=1)
    assert any(n.startswith("reference decisions blocked: 2 x ") for n in result.runs["TEST"].notes)
