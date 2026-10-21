"""Many variants on one loaded series (research-speed plan step 2): `run_backtests_many` and
`research.run_period_many` give exactly the trades of one `run_backtests` / `run_period` per
variant, candles are loaded once per symbol and piece, and variants do not leak state."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest
from test_runner import FULL, MON, OPENING, SETTINGS, TUE, WED, write_day

from backtester import runner
from backtester.core.models import Timeframe
from backtester.data.sources import SymbolSources
from backtester.runner import run_backtests, run_backtests_many
from backtester.strategy.trend_following.config import TrendFollowingConfig
from backtester.tools import research

# min_rr 3.0 takes the same entry with another target; trend following loads another
# timeframe and asks for more warm-up (a different load plan)
VARIANTS = [
    SETTINGS,
    replace(SETTINGS, strategy=replace(SETTINGS.strategy, min_rr=3.0)),
    replace(SETTINGS, strategy=TrendFollowingConfig(timeframe=Timeframe.M15)),
]


@pytest.fixture
def cache(tmp_path):
    folder = tmp_path / "cache"
    write_day(folder, "XAUUSD", MON, FULL)
    write_day(folder, "GOLD", TUE, FULL)
    return SymbolSources.single(folder, ["XAUUSD", "GOLD", "BTCUSD"])


def old_way(settings_list, cache, symbols=("XAUUSD", "GOLD")):
    return [run_backtests(symbols, MON, TUE, s, cache, workers=1) for s in settings_list]


def same(a, b):
    assert a.symbols == b.symbols and a.notes == b.notes
    assert a.trades == b.trades  # every field of every trade
    assert a.runs == b.runs  # sessions, notes, days


@pytest.mark.parametrize("workers", [1, 2])
def test_many_gives_the_same_results_as_one_run_per_variant(cache, workers):
    new = dict(run_backtests_many(["XAUUSD", "GOLD"], MON, TUE, VARIANTS, cache, workers))
    assert sorted(new) == [0, 1, 2]
    old = old_way(VARIANTS, cache)
    for i, expected in enumerate(old):
        same(new[i], expected)
    assert len(new[0].trades) == 2 and new[0].trades != new[1].trades  # variants differ


@pytest.mark.parametrize("workers", [1, 2])
def test_the_run_order_does_not_change_a_variant(cache, workers):
    forward = dict(run_backtests_many(["XAUUSD", "GOLD"], MON, TUE, VARIANTS, cache, workers))
    back = dict(run_backtests_many(["XAUUSD", "GOLD"], MON, TUE, VARIANTS[::-1], cache, workers))
    for i in range(3):
        same(forward[i], back[2 - i])


def test_left_out_symbols_and_notes_are_the_same(cache):
    write_day(cache.cache_dir("BTCUSD"), "BTCUSD", MON, FULL)
    for settings, symbols in ((OPENING, ["XAUUSD", "BTCUSD"]), (SETTINGS, ["XAUUSD", "GOLD"])):
        [(_, new)] = run_backtests_many(symbols, MON, MON, [settings], cache, 1)
        same(new, run_backtests(symbols, MON, MON, settings, cache, workers=1))
        assert new.symbols == ("XAUUSD",) and len(new.notes) == 1  # left out, with a note


def test_no_runnable_symbol_raises_like_a_single_run(cache):
    with pytest.raises(ValueError, match="no cached day"):
        list(run_backtests_many(["XAUUSD"], WED, WED, VARIANTS, cache, 1))


def test_candles_are_loaded_once_per_symbol_for_variants_with_the_same_plan(cache, monkeypatch):
    calls = []
    real = runner._load_timeframe

    def counting(adapter, symbol, tf, *a, **k):
        calls.append((symbol, tf))
        return real(adapter, symbol, tf, *a, **k)

    monkeypatch.setattr(runner, "_load_timeframe", counting)
    same_plan = VARIANTS[:2] * 2
    list(run_backtests_many(["XAUUSD"], MON, MON, same_plan, cache, 1))
    assert (
        len(calls)
        == len(set(calls))
        == len(runner.make_strategy("XAUUSD", SETTINGS.strategy, SETTINGS.detectors).timeframes)
    )


def test_run_period_many_equals_run_period_with_a_gap_in_the_cache(cache):
    write_day(cache.cache_dir("XAUUSD"), "XAUUSD", date(2026, 1, 8), FULL)  # Tue..Wed missing
    for workers in (1, 2):
        new = dict(research.run_period_many(
            ["XAUUSD", "GOLD"], MON, date(2026, 1, 8), VARIANTS[:2], cache, workers
        ))  # fmt: skip
        for i, s in enumerate(VARIANTS[:2]):
            old = research.run_period(["XAUUSD", "GOLD"], MON, date(2026, 1, 8), s, cache, 1)
            same(new[i], old)
    assert any("pieces" in n for n in new[0].runs["XAUUSD"].notes)


def test_run_period_many_raises_without_cached_days(cache):
    with pytest.raises(research.ResearchError, match="no cached day"):
        list(research.run_period_many(["XAUUSD"], WED, WED, VARIANTS, cache, 1))
