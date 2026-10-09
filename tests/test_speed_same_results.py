"""The speed-ups for years of data change no result. Spec: ROADMAP.md › 6.3 (full history).

`ZoneBook` only checks the untapped zones a candle reaches (detectors/zone.py). Here the
old book, which checks every open zone on every candle, is kept as `CheckEveryZone`, and
both run on the same candles: a randomized test of the book itself, and strategy 1 + the
engine over three weeks of seeded random-walk candles, compared trade by trade and
session record by session record. (The journal / equilibrium changes in the same step
were also compared on two months of the real cache, see ROADMAP.md › 0.3.)
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import candles_from_frame
from backtester.data.resample import resample
from backtester.detectors import bpr, fvg, order_block, zone
from backtester.detectors.zone import ZoneBook, ZoneBox, ZoneKind, ZoneValidator
from backtester.engine.backtest import run_backtest
from backtester.strategy.session_zone_sweep import signals, targets
from backtester.strategy.session_zone_sweep.strategy import SessionZoneSweep


class CheckEveryZone:
    """The ZoneBook before the speed-up: every open zone checked on every candle."""

    def __init__(self, doji_max_body: float):
        self.doji_max_body = doji_max_body
        self._open: list[ZoneValidator] = []

    def add(self, zone_box: ZoneBox) -> None:
        self._open.append(ZoneValidator(zone_box, self.doji_max_body))

    @property
    def open_zones(self) -> list[ZoneBox]:
        return [v.zone for v in self._open]

    def on_candle(self, view):
        out = [t for v in self._open for t in v.on_candle(view)]
        self._open = [v for v in self._open if not v.state.finished]
        return out


def random_candles(n: int, seed: int) -> list[Candle]:
    rng = random.Random(seed)
    price, out = 100.0, []
    t0 = datetime(2026, 1, 5, tzinfo=UTC)
    for i in range(n):
        o = price
        c = o + rng.gauss(0, 1)
        h = max(o, c) + abs(rng.gauss(0, 0.5))
        lo = min(o, c) - abs(rng.gauss(0, 0.5))
        out.append(Candle(t0 + timedelta(minutes=5 * i), o, h, lo, c))
        price = c
    return out


@pytest.mark.parametrize("seed", range(5))
def test_the_book_gives_the_same_transitions_and_open_zones(seed):
    rng = random.Random(seed)
    series = CandleSeries("X", Timeframe.M5, random_candles(600, seed))
    fast, slow = ZoneBook(0.1), CheckEveryZone(0.1)
    for i in range(len(series)):
        view = series.view(i)
        assert fast.on_candle(view) == slow.on_candle(view), i
        for _ in range(rng.choice((0, 0, 1, 2))):  # zones confirmed by this candle
            direction = rng.choice(list(Direction))
            bottom = view.current.close + rng.uniform(-8, 8)
            box = ZoneBox(
                ZoneKind.FVG, direction, bottom + rng.uniform(0.1, 3), bottom, max(i - 2, 0), i,
                view.current.ts,
            )  # fmt: skip
            fast.add(box)
            slow.add(box)
        assert fast.open_zones == slow.open_zones, i


def random_walk_m1(days: int, seed: int) -> pd.DataFrame:
    """Weekday M1 bid minutes like a cache file (gold-like prices), weekends without."""
    rng = random.Random(seed)
    rows, price = [], 2000.0
    start = datetime(2026, 1, 5, tzinfo=UTC)  # a Monday
    for m in range(days * 1440):
        t = start + timedelta(minutes=m)
        if t.weekday() >= 5:
            continue
        o = price
        c = o + rng.gauss(0, 0.35)
        h = max(o, c) + abs(rng.gauss(0, 0.15))
        lo = min(o, c) - abs(rng.gauss(0, 0.15))
        rows.append((t, o, h, lo, c))
        price = c
    frame = pd.DataFrame(rows, columns=["ts", "bid_open", "bid_high", "bid_low", "bid_close"])
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    nan = float("nan")
    frame["bid_volume"] = nan
    for f in ("open", "high", "low", "close", "volume"):
        frame[f"ask_{f}"] = nan
    return frame


def backtest(m1: pd.DataFrame):
    strategy = SessionZoneSweep("XAUUSD")
    series = [
        CandleSeries("XAUUSD", tf, candles_from_frame(resample(m1, tf)))
        for tf in dict.fromkeys(strategy.timeframes)
    ]
    trades = run_backtest(strategy, series)
    return trades, strategy.session_records()


def test_strategy_and_engine_give_identical_trades_and_records(monkeypatch):
    m1 = random_walk_m1(days=21, seed=7)
    fast_trades, fast_records = backtest(m1)
    for module in (zone, fvg, order_block, bpr, signals, targets):
        if hasattr(module, "ZoneBook"):
            monkeypatch.setattr(module, "ZoneBook", CheckEveryZone)
    slow_trades, slow_records = backtest(m1)
    assert len(fast_trades) > 10  # the random walk does produce setups and trades
    assert fast_trades == slow_trades
    assert fast_records == slow_records
