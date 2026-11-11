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
