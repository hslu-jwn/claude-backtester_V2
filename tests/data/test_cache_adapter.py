"""CacheAdapter: reads cached M1 days and returns resampled candles. Spec: ROADMAP.md › 0.2."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd
import pytest
from m1_frames import m1

from backtester.core.models import Candle, Timeframe
from backtester.data import show
from backtester.data.adapters.cache_adapter import (
    CacheAdapter,
    MissingCacheError,
    available_symbols,
    cached_days,
    latest_run,
)
from backtester.data.dukascopy import _empty_cache_frame, cache_path
from backtester.data.resample import H4Alignment


def write_day(cache_dir, day: date, frame: pd.DataFrame, symbol: str = "XAUUSD") -> None:
    path = cache_path(cache_dir, symbol, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


@pytest.fixture
def cache(tmp_path):
    """Two cached days. 09-02 ends with the daily break (flat 21:00-21:59), 09-03 is empty."""
    write_day(
        tmp_path,
        date(2026, 9, 2),
        m1(
            ("20:55", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),
            ("20:59", 100.5, 102.0, 100.4, 101.0, 1.0, 0.4),
            ("21:00", 101.0, 101.0, 101.0, 101.0, 0.0, 0.6),  # break filler
            ("21:59", 101.0, 101.0, 101.0, 101.0, 0.0, 0.6),  # break filler
            ("22:00", 101.2, 101.6, 101.1, 101.5, 1.0, 0.8),
            ("23:07", 101.5, 101.9, 101.3, 101.4, 1.0, 0.3),
        ),
    )
    write_day(tmp_path, date(2026, 9, 3), _empty_cache_frame())
    return tmp_path


def ts(day: int, hh: int, mm: int = 0) -> datetime:
    return datetime(2026, 9, day, hh, mm, tzinfo=UTC)


def test_fetch_returns_candles_with_spread_and_break_gap(cache):
    candles = CacheAdapter(cache).fetch("XAUUSD", Timeframe.H1, ts(2, 0), ts(4, 0))
    assert [c.ts for c in candles] == [ts(2, 20), ts(2, 22), ts(2, 23)]  # no 21:00 candle
    assert candles[0] == Candle(
        ts=ts(2, 20),
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.0,
        volume=2.0,
        spread=pytest.approx(0.3),
    )
    assert all(isinstance(c.ts, datetime) and c.ts.tzinfo is not None for c in candles)


def test_fetch_keeps_candles_with_start_le_ts_lt_end(cache):
    adapter = CacheAdapter(cache)
    # start inside the 20:00 hour: that candle opened before start and is left out, not cut
    assert [c.ts for c in adapter.fetch("XAUUSD", Timeframe.H1, ts(2, 20, 30), ts(2, 23))] == [
        ts(2, 22)
    ]
    # the 5m candle at 20:55 is built from all its minutes even though start is 20:55
    m5 = adapter.fetch("XAUUSD", Timeframe.M5, ts(2, 20, 55), ts(2, 22, 5))
    assert [c.ts for c in m5] == [ts(2, 20, 55), ts(2, 22)]
    assert (m5[0].high, m5[0].close) == (102.0, 101.0)


def test_naive_datetimes_are_treated_as_utc(cache):
    naive = CacheAdapter(cache).fetch(
        "XAUUSD",
        Timeframe.M30,
        datetime(2026, 9, 2, 22),  # noqa: DTZ001
        datetime(2026, 9, 3),  # noqa: DTZ001
    )
    assert [c.ts for c in naive] == [ts(2, 22), ts(2, 23)]


def test_m1_drops_flat_minutes(cache):
    m1_candles = CacheAdapter(cache).fetch("XAUUSD", Timeframe.M1, ts(2, 20), ts(2, 23))
    assert [c.ts for c in m1_candles] == [ts(2, 20, 55), ts(2, 20, 59), ts(2, 22)]


def test_empty_cached_day_gives_no_candles(cache):
    assert CacheAdapter(cache).fetch("XAUUSD", Timeframe.M5, ts(3, 0), ts(4, 0)) == []


def test_day_not_in_cache_raises_and_names_it(cache):
    with pytest.raises(MissingCacheError, match=r"2026-09-04\.\.2026-09-05"):
        CacheAdapter(cache).fetch("XAUUSD", Timeframe.M5, ts(2, 0), ts(6, 0))


def test_end_at_midnight_does_not_need_the_next_day(cache):
    # [09-03 00:00, 09-04 00:00) touches only 09-03; 09-04 is not cached and not needed
    CacheAdapter(cache).fetch("XAUUSD", Timeframe.H1, ts(3, 0), ts(4, 0))


def test_daily_candles_close_in_the_range_and_need_every_day_they_cover(tmp_path):
    # 09-01 .. 09-04 cached (Tue .. Fri); a NY trading day closes 21:00 UTC (EDT)
    for d in range(1, 5):
        write_day(tmp_path, date(2026, 9, d), m1(("12:00", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),
                                                   day=f"2026-09-0{d}"))  # fmt: skip
    found = CacheAdapter(tmp_path).fetch_frame("XAUUSD", Timeframe.D1, ts(2, 0), ts(4, 0))
    closes = [t + Timeframe.D1.duration for t in found.ts]
    # trading days 09-02 and 09-03 close in [09-02, 09-04); 09-01's needs 08-31 (missing)
    assert closes == [pd.Timestamp("2026-09-02 21:00", tz="UTC"),
                      pd.Timestamp("2026-09-03 21:00", tz="UTC")]  # fmt: skip
    first = CacheAdapter(tmp_path).fetch_frame("XAUUSD", Timeframe.D1, ts(1, 0), ts(2, 0))
    assert first.empty  # its open 08-31 21:00 is not cached: no half candle
    week = CacheAdapter(tmp_path).fetch_frame("XAUUSD", Timeframe.W1, ts(1, 0), ts(5, 0))
    assert week.empty  # the week of 08-31 started on uncached days


def test_show_prints_candles_with_extra_time_zone(cache, capsys):
    code = show.main(
        [
            "XAUUSD",
            "H1",
            "2026-09-02T20:00",
            "2026-09-03",
            "--tz",
            "Etc/GMT-3",
            "--cache-dir",
            str(cache),
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "2026-09-02 20:00    2026-09-02 23:00" in out
    assert "21:00 " not in out.split("\n", 1)[1].split("    ")[0]
    assert "3 H1 candles" in out


def test_show_reports_missing_days(cache, capsys):
    code = show.main(["XAUUSD", "M5", "2026-09-04", "2026-09-05", "--cache-dir", str(cache)])
    assert code == 1
    assert (
        "python -m backtester.data.download XAUUSD 2026-09-04 2026-09-05" in capsys.readouterr().out
    )


def test_available_symbols_lists_only_symbols_with_cached_days(cache):
    (cache / "GBPUSD" / "2026").mkdir(parents=True)  # folder without any cached day
    write_day(cache, date(2026, 9, 2), _empty_cache_frame(), symbol="GBPJPY")
    assert available_symbols(cache) == ["GBPJPY", "XAUUSD"]
    assert available_symbols(cache / "nowhere") == []


def test_cached_days_sorted_and_empty_days_count(cache):
    write_day(cache, date(2025, 12, 31), _empty_cache_frame())
    assert cached_days("XAUUSD", cache) == [date(2025, 12, 31), date(2026, 9, 2), date(2026, 9, 3)]
    assert cached_days("GBPUSD", cache) == []


def test_latest_run_is_newest_block_of_consecutive_days():
    d = date.fromisoformat
    days = [d("2020-01-01"), d("2020-01-02"), d("2026-09-01"), d("2026-09-02"), d("2026-09-03")]
    assert latest_run(days) == (d("2026-09-01"), d("2026-09-03"))
    assert latest_run([d("2020-01-01")]) == (d("2020-01-01"), d("2020-01-01"))
    assert latest_run([]) is None


def test_new_york_4h_candles_span_utc_midnight_and_need_both_days(tmp_path):
    # 09-01 .. 09-03 cached; the 18:00-22:00 ET candle opens 22:00 UTC and closes 02:00 UTC
    for d in range(1, 4):
        write_day(tmp_path, date(2026, 9, d), m1(("22:30", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),
                                                   ("01:30", 100.5, 102.0, 100.0, 101.0, 1.0, 0.2),
                                                   day=f"2026-09-0{d}"))  # fmt: skip
    adapter = CacheAdapter(tmp_path)
    found = adapter.fetch_frame("XAUUSD", Timeframe.H4, ts(1, 0), ts(4, 0), h4=H4Alignment.NEW_YORK)
    opens = [t.to_pydatetime() for t in found.ts]
    # 09-01 01:30 UTC is in the candle opening 08-31 22:00 (08-31 not cached): left out;
    # 09-03 22:30 is in the candle closing 09-04 02:00 (09-04 not cached): left out
    assert opens == [ts(1, 22), ts(2, 22)]
    row = found.iloc[0]
    assert (row.open, row.high, row.close) == (100.0, 102.0, 101.0)  # 22:30 + next day 01:30
    utc_aligned = adapter.fetch_frame("XAUUSD", Timeframe.H4, ts(1, 0), ts(4, 0))
    assert utc_aligned.ts.tolist()[0] == pd.Timestamp("2026-09-01 00:00", tz="UTC")
