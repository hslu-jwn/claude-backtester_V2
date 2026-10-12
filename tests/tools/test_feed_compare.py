"""Feed comparison and spread statistics (ROADMAP 0.4), on hand-built candles."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pandas as pd
import pytest
from fake_mt5 import FakeMt5

from backtester.core.models import Timeframe
from backtester.data.adapters.mt5_adapter import Mt5Adapter, ServerClock
from backtester.tools.feed_compare import compare_symbol, compare_table, spread_report
from backtester.tools.mt5_compare import best_shift, compare_frames, spread_by_hour

T0 = datetime(2026, 9, 16, 10, tzinfo=UTC)
M5 = timedelta(minutes=5)


def frame(rows, start=T0, step=M5, spread=None) -> pd.DataFrame:
    """rows: (open, high, low, close); `None` leaves that candle out."""
    data = [(start + i * step, *r) for i, r in enumerate(rows) if r is not None]
    out = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close"])
    out["volume"] = 0.0
    out["spread"] = spread if spread is not None else float("nan")
    return out


CACHE = [
    (100.0, 101.0, 99.0, 100.5),  # green
    (100.5, 101.5, 100.0, 101.0),  # green
    (101.0, 101.2, 100.2, 100.4),  # red
    (100.4, 100.9, 100.1, 100.4),  # flat
    (100.4, 100.8, 99.8, 100.0),  # red
]


def test_compare_frames_differences_colors_and_missing_candles():
    mt5 = frame(
        [
            (100.1, 101.1, 99.1, 100.6),  # +0.1 everywhere
            (100.6, 101.6, 100.1, 101.1),
            (101.1, 101.3, 100.3, 101.2),  # green where the cache is red
            None,  # missing on MT5
            (100.5, 100.9, 99.9, 100.1),
            (100.1, 100.2, 99.9, 100.0),  # after the cache's last candle: not compared
        ]
    )
    extra = frame([(100.1, 100.2, 100.0, 100.1)], start=T0 + 2 * M5 + timedelta(minutes=1))
    out = compare_frames(pd.concat([mt5, extra]).sort_values("ts"), frame(CACHE))
    assert out["matched"] == 4 and out["mt5_candles"] == 5 and out["cache_candles"] == 5
    assert out["open_diff"] == pytest.approx(0.1)
    assert out["close_diff"] == pytest.approx((0.1 + 0.1 + 0.8 + 0.1) / 4)
    assert out["median_range"] == pytest.approx(1.0)
    assert out["color_differs"] == pytest.approx(0.25)
    assert out["color_opposite"] == pytest.approx(0.25)
    assert out["only_mt5"] == 1 and out["only_mt5_examples"] == [T0 + 2 * M5 + timedelta(minutes=1)]
    assert out["only_cache"] == 1 and out["only_cache_examples"] == [T0 + 3 * M5]


def test_a_flat_candle_against_a_colored_one_differs_but_is_not_opposite():
    out = compare_frames(frame([(1.0, 1.1, 0.9, 1.0)]), frame([(1.0, 1.1, 0.9, 1.05)]))
    assert out["color_differs"] == 1.0 and out["color_opposite"] == 0.0


def test_best_shift_finds_a_clock_error():
    closes = [100 + (i % 7) * 0.9 - (i % 3) * 1.3 for i in range(60)]
    cache = frame([(c, c + 1, c - 1, c) for c in closes], step=timedelta(hours=1))
    late = cache.assign(ts=cache["ts"] + timedelta(hours=1))  # MT5 one hour late
    shift, error, at_zero = best_shift(late, cache, Timeframe.H1)
    assert shift == timedelta(hours=-1) and error == 0 and at_zero > 0
    assert best_shift(cache, cache, Timeframe.H1)[0] == timedelta(0)


def test_spread_by_hour():
    candles = pd.DataFrame(
        {
            "ts": [T0, T0 + M5, T0 + 2 * M5, T0 + timedelta(hours=1)],
            "spread": [0.2, 0.3, 0.4, 1.0],
        }
    )
    table = spread_by_hour(candles)
    assert list(table["hour"]) == ["10", "11", "all"]
    assert table.iloc[0]["median"] == pytest.approx(0.3)
    assert table.iloc[0]["p90"] == pytest.approx(0.38)
    assert table.iloc[2]["candles"] == 4


class FakeSources:
    """Duck-typed `SymbolSources` over in-memory cache candles."""

    def __init__(self, candles: dict[Timeframe, pd.DataFrame], days: list[date]):
        self.candles, self.days = candles, days

    def cached_days(self, symbol):
        return self.days

    def adapter(self, symbol):
        sources = self

        class Adapter:
            def fetch_frame(self, symbol, tf, start, end):
                c = sources.candles[tf]
                return c[(c["ts"] >= start) & (c["ts"] < end)].reset_index(drop=True)

        return Adapter()


def test_compare_symbol_end_to_end_with_a_fake_terminal():
    clock = ServerClock("UTC", 3)
    fake = FakeMt5()
    fake.initialize()
    fake.add_symbol("XAUUSD.r", point=0.01)
    server = [
        (int((T0 + i * M5 + timedelta(hours=3)).timestamp()), *r, 25) for i, r in enumerate(CACHE)
    ]
    fake.set_rates("XAUUSD.r", fake.TIMEFRAME_M5, server)
    now = T0 + timedelta(days=1)
    adapter = Mt5Adapter(fake, clock, {"XAUUSD": "XAUUSD.r"}, now=lambda: now)
    sources = FakeSources({Timeframe.M5: frame(CACHE)}, [date(2026, 9, 16)])
    rows, history = compare_symbol(adapter, sources, "XAUUSD", timeframes=(Timeframe.M5,))
    (row,) = rows
    assert row["matched"] == 5 and row["best_shift"] == timedelta(0)
    assert row["close_diff"] == 0 and row["color_differs"] == 0
    assert history[Timeframe.M5]["spread"].iloc[0] == pytest.approx(0.25)
    table = compare_table(rows)
    assert table[2].startswith("| XAUUSD | M5 | 2026-09-16 10:00 .. 2026-09-16 10:20 | 1 | 5 | 0 |")

    lines, _ = spread_report("XAUUSD", history, 0.01)
    assert "Cost default (3.1): 0.25" in lines[0]
    assert lines[-1] == "| all | 5 | 0.25 (25 pt) | 0.25 (25 pt) | 1.00x |"


def test_compare_symbol_without_common_days():
    fake = FakeMt5()
    fake.initialize()
    fake.add_symbol("XAUUSD")
    fake.set_rates("XAUUSD", fake.TIMEFRAME_M5, [(int(T0.timestamp()), 1.0, 1.0, 1.0, 1.0)])
    adapter = Mt5Adapter(fake, ServerClock(), now=lambda: T0 + timedelta(days=1))
    rows, _ = compare_symbol(adapter, FakeSources({}, []), "XAUUSD", timeframes=(Timeframe.M5,))
    assert rows[0]["days_both"] == 0
    assert compare_table(rows)[2] == "| XAUUSD | M5 | 2026-09-16 10:00 ... | 0 | 0 | | | | | | | |"
