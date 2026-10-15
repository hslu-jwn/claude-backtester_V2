"""MT5 history download into the day cache (ROADMAP 11.5), with a fake MetaTrader5 module."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest
from fake_mt5 import FakeMt5

from backtester.core.models import Timeframe
from backtester.data.adapters.cache_adapter import CacheAdapter
from backtester.data.adapters.mt5_adapter import Mt5Adapter, ServerClock
from backtester.data.cache import COLUMNS, cache_path, read_cached_day
from backtester.data.mt5_download import cache_frame, download_symbol

NY7 = ServerClock("America/New_York", 7)
NOW = datetime(2026, 9, 20, 12, tzinfo=UTC)


def server_seconds(*args) -> int:
    return int(datetime(*args, tzinfo=UTC).timestamp())


def make(rows_by_utc_day: dict[date, int], spread_points=20, point=0.01):
    """Fake terminal with `n` M1 bars per UTC day starting 10:00 UTC (server UTC+3 in Sept)."""
    fake = FakeMt5()
    fake.initialize()
    fake.add_symbol("US100.cash", point=point)
    rows = []
    for day, n in rows_by_utc_day.items():
        for i in range(n):
            ts = datetime(day.year, day.month, day.day, 10, tzinfo=UTC) + timedelta(minutes=i)
            server = int((ts + NY7.offset_at(ts)).timestamp())
            price = 100.0 + i
            rows.append((server, price, price + 1, price - 1, price + 0.5, spread_points))
    fake.set_rates("US100.cash", fake.TIMEFRAME_M1, rows)
    adapter = Mt5Adapter(fake, NY7, {"NAS100": "US100.cash"}, now=lambda: NOW)
    return fake, adapter


def test_cache_frame_maps_bid_ask_and_volume():
    bars = pd.DataFrame(
        {
            "ts": pd.to_datetime(["2026-09-01 10:00", "2026-09-01 10:01"], utc=True),
            "open": [1.0, 2.0], "high": [1.5, 2.5], "low": [0.5, 1.5], "close": [1.2, 2.2],
            "volume": [7.0, 9.0], "spread": [0.25, 0.0],
        }
    )  # fmt: skip
    out = cache_frame(bars)
    assert list(out.columns) == COLUMNS
    assert out["bid_close"].tolist() == [1.2, 2.2]
    assert out["ask_close"].iloc[0] == pytest.approx(1.45)  # bid + spread
    assert out["ask_high"].iloc[0] == pytest.approx(1.75)
    assert out["bid_volume"].tolist() == out["ask_volume"].tolist() == [7.0, 9.0]
    # spread 0 = not recorded: the ask is unknown (NaN), never "ask = bid"
    assert np.isnan(out["ask_close"].iloc[1]) and np.isnan(out["ask_open"].iloc[1])


def test_download_writes_the_day_cache_in_the_histdata_layout(tmp_path):
    days = {date(2026, 9, d): 5 for d in (1, 2, 3)}
    _, adapter = make(days)
    result = download_symbol(
        adapter, "NAS100", date(2026, 9, 1), date(2026, 9, 5), tmp_path, min_day_bars=1
    )
    frame = read_cached_day(cache_path(tmp_path, "NAS100", date(2026, 9, 2)))
    assert list(frame.columns) == COLUMNS and len(frame) == 5
    assert frame["ts"].iloc[0] == pd.Timestamp("2026-09-02 10:00", tz="UTC")
    assert frame["bid_open"].iloc[0] == 100.0 and frame["bid_close"].iloc[1] == 101.5
    assert frame["ask_close"].iloc[0] == pytest.approx(100.5 + 0.20)  # 20 points x 0.01
    assert result.bars == 15 - 5  # the first day with data is partial by definition: skipped


def test_empty_days_are_cached_as_empty_after_the_first_data_day(tmp_path):
    days = {date(2026, 9, 1): 5, date(2026, 9, 4): 5}  # 2, 3 have no bars
    _, adapter = make(days)
    result = download_symbol(
        adapter, "NAS100", date(2026, 8, 25), date(2026, 9, 6), tmp_path, min_day_bars=1
    )
    for d in (2, 3):
        empty = read_cached_day(cache_path(tmp_path, "NAS100", date(2026, 9, d)))
        assert list(empty.columns) == COLUMNS and empty.empty
    assert cache_path(tmp_path, "NAS100", date(2026, 9, 4)).exists()
    # before the first bar nothing is claimed (history not available is not "no trading")
    assert not cache_path(tmp_path, "NAS100", date(2026, 8, 30)).exists()
    assert not cache_path(tmp_path, "NAS100", date(2026, 9, 1)).exists()  # first day: partial
    assert result.first_day == date(2026, 9, 2)


def test_chunks_over_a_month_boundary_equal_one_big_request(tmp_path):
    days = {date(2026, 8, 30): 4, date(2026, 8, 31): 4, date(2026, 9, 1): 4, date(2026, 9, 2): 4}
    _, adapter = make(days)
    a, b = tmp_path / "a", tmp_path / "b"
    download_symbol(
        adapter, "NAS100", date(2026, 8, 28), date(2026, 9, 4), a, chunk_days=3, min_day_bars=1
    )
    download_symbol(
        adapter, "NAS100", date(2026, 8, 28), date(2026, 9, 4), b, chunk_days=400, min_day_bars=1
    )
    files_a = sorted(p.relative_to(a) for p in a.rglob("*.parquet"))
    assert files_a == sorted(p.relative_to(b) for p in b.rglob("*.parquet"))
    for rel in files_a:
        pd.testing.assert_frame_equal(read_cached_day(a / rel), read_cached_day(b / rel))
    assert len(read_cached_day(a / "NAS100/2026/2026-08-31.parquet")) == 4


def test_a_utc_day_never_holds_bars_of_the_neighbour_day(tmp_path):
    _, adapter = make({date(2026, 9, 1): 3, date(2026, 9, 2): 3, date(2026, 9, 3): 3})
    download_symbol(adapter, "NAS100", date(2026, 9, 1), date(2026, 9, 4), tmp_path, min_day_bars=1)
    for d in (2, 3):
        frame = read_cached_day(cache_path(tmp_path, "NAS100", date(2026, 9, d)))
        assert (frame["ts"].dt.date == date(2026, 9, d)).all()


def test_the_default_end_is_the_last_closed_day_not_today(tmp_path):
    days = {date(2026, 9, d): 3 for d in range(17, 21)}  # 20th = "today" (NOW)
    _, adapter = make(days)
    result = download_symbol(adapter, "NAS100", date(2026, 9, 16), None, tmp_path, min_day_bars=1)
    assert result.last_day == date(2026, 9, 19)
    assert not cache_path(tmp_path, "NAS100", date(2026, 9, 20)).exists()


def test_rerun_overwrites_and_the_cache_adapter_reads_it(tmp_path):
    days = {date(2026, 9, d): 60 for d in (1, 2, 3)}
    _, adapter = make(days)
    for _ in range(2):
        download_symbol(
            adapter, "NAS100", date(2026, 9, 1), date(2026, 9, 4), tmp_path, min_day_bars=1
        )
    assert not list(tmp_path.rglob("*.tmp"))
    candles = CacheAdapter(tmp_path).fetch_frame(
        "NAS100", Timeframe.M5, datetime(2026, 9, 2, tzinfo=UTC), datetime(2026, 9, 3, tzinfo=UTC)
    )
    assert len(candles) == 12
    assert candles["spread"].iloc[0] == pytest.approx(0.2)


def test_no_history_at_all_writes_nothing(tmp_path):
    fake = FakeMt5()
    fake.initialize()
    fake.add_symbol("US100.cash")
    fake.set_rates("US100.cash", fake.TIMEFRAME_M1, [])
    adapter = Mt5Adapter(fake, NY7, {"NAS100": "US100.cash"}, now=lambda: NOW)
    result = download_symbol(
        adapter, "NAS100", date(2026, 9, 1), date(2026, 9, 4), tmp_path, min_day_bars=1
    )
    assert result.bars == 0 and result.first_day is None
    assert not list(tmp_path.rglob("*.parquet"))


def test_daily_bars_before_the_real_intraday_history_are_not_cached(tmp_path):
    """FTMO's index history is one bar a day (also on M1) until the intraday history starts."""
    days = {date(2026, 9, 1): 1, date(2026, 9, 2): 1}
    days.update({date(2026, 9, d): 120 for d in (3, 4, 5)})
    _, adapter = make(days)
    result = download_symbol(adapter, "NAS100", date(2026, 9, 1), date(2026, 9, 6), tmp_path)
    written = sorted(p.stem for p in tmp_path.rglob("*.parquet"))
    assert written == ["2026-09-04", "2026-09-05", "2026-09-06"]  # 3rd: first dense, partial
    assert result.first_day == date(2026, 9, 4)
    assert len(read_cached_day(cache_path(tmp_path, "NAS100", date(2026, 9, 4)))) == 120
