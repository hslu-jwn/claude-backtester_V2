"""Research pieces and manifests follow declared references (design/multi-symbol.md > 1b)."""

from datetime import date, timedelta

from backtester.core.market import ReferenceInput
from backtester.core.models import Timeframe as TF
from backtester.data.cache import cache_path
from backtester.data.sources import SymbolSources
from backtester.runner import RunSettings
from backtester.strategy.base import MarketAwareStrategy
from backtester.tools import research

MON = date(2026, 1, 5)


class Declared(MarketAwareStrategy):
    base_timeframe = TF.M1
    timeframes = (TF.M1,)
    references = (ReferenceInput("REF", "r", (TF.M1,), max_age=timedelta(minutes=1)),
                  ReferenceInput("OPT", "o", (TF.M1,), max_age=timedelta(minutes=1),
                                 required=False))

    def on_market_candle(self, now, views, market):
        return []


def _touch(folder, symbol, days):
    for day in days:
        path = cache_path(folder, symbol, day)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")


def test_reference_symbols_from_market_aware_strategies_only(monkeypatch):
    monkeypatch.setattr(research, "make_strategy", lambda *a: Declared())
    assert research.reference_symbols(["TEST"], [RunSettings()]) == ("REF", "OPT")
    assert research.reference_symbols(["TEST"], [RunSettings()], required=True) == ("REF",)
    monkeypatch.undo()
    assert research.reference_symbols(["US500"], [RunSettings()]) == ()  # legacy strategy


def test_reference_gap_splits_primary_piece(tmp_path):
    week = [MON + timedelta(days=i) for i in range(5)]
    _touch(tmp_path, "TEST", week)
    _touch(tmp_path, "REF", [d for d in week if d != week[2]])
    sources = SymbolSources.single(tmp_path, ["TEST", "REF"])
    assert research._pieces(["TEST"], week[0], week[-1], sources) == {(week[0], week[-1]): ["TEST"]}
    assert research._pieces(["TEST"], week[0], week[-1], sources, ("REF",)) == {
        (week[0], week[1]): ["TEST"], (week[3], week[4]): ["TEST"],
    }
