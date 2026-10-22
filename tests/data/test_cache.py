"""The Parquet day cache (data/cache.py): layout, empty frame, atomic write, bulk read.

Pins the behavior of the helpers that moved out of the removed Dukascopy downloader (ROADMAP C.1).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from backtester.data.cache import (
    COLUMNS,
    DEFAULT_CACHE_DIR,
    cache_path,
    empty_cache_frame,
    read_cached_day,
    read_cached_days,
    write_atomic,
)
from backtester.paths import DATA_DIR


def day_frame(day: date, minutes: int, price: float = 1.0) -> pd.DataFrame:
    ts = pd.date_range(
        datetime(day.year, day.month, day.day, tzinfo=UTC), periods=minutes, freq="min"
    )
    frame = pd.DataFrame({"ts": ts})
    for c in COLUMNS[1:]:
        frame[c] = price
    return frame[COLUMNS]


def test_columns_are_ts_then_bid_then_ask_ohlcv():
    assert COLUMNS == [
        "ts",
        "bid_open", "bid_high", "bid_low", "bid_close", "bid_volume",
        "ask_open", "ask_high", "ask_low", "ask_close", "ask_volume",
    ]  # fmt: skip


def test_default_cache_dir_is_the_histdata_cache():
    # anchored to the project root, not the working folder (audit 13.17, 2026-10-23)
    assert DEFAULT_CACHE_DIR == DATA_DIR / "cache" / "histdata"


def test_cache_path_layout():
    p = cache_path(Path("c"), "XAUUSD", date(2026, 9, 3))
    assert p == Path("c") / "XAUUSD" / "2026" / "2026-09-03.parquet"


def test_cache_path_zero_pads_the_year():
    assert cache_path(Path("c"), "X", date(999, 1, 2)).parts[-2] == "0999"


def test_empty_frame_has_the_columns_and_utc_ts():
    frame = empty_cache_frame()
    assert list(frame.columns) == COLUMNS
    assert len(frame) == 0
    assert str(frame["ts"].dtype) == "datetime64[ns, UTC]"
    assert all(str(frame[c].dtype) == "float64" for c in COLUMNS[1:])


def test_write_atomic_round_trip_and_no_temp_file(tmp_path):
    path = cache_path(tmp_path, "XAUUSD", date(2026, 9, 3))
    frame = day_frame(date(2026, 9, 3), 3)
    write_atomic(frame, path)  # creates the parent folders
    assert list(path.parent.iterdir()) == [path]
    pd.testing.assert_frame_equal(read_cached_day(path), frame)


def test_write_atomic_replaces_an_existing_file(tmp_path):
    path = tmp_path / "d.parquet"
    write_atomic(day_frame(date(2026, 9, 3), 3), path)
    write_atomic(day_frame(date(2026, 9, 3), 2, price=2.0), path)
    assert len(read_cached_day(path)) == 2


def test_read_cached_days_no_files_gives_the_empty_frame():
    frame = read_cached_days([])
    assert list(frame.columns) == COLUMNS and frame.empty


def test_read_cached_days_one_file(tmp_path):
    path = tmp_path / "a.parquet"
    write_atomic(day_frame(date(2026, 9, 3), 4), path)
    assert len(read_cached_days([path])) == 4


def test_read_cached_days_keeps_file_order_and_column_order(tmp_path):
    a, b = tmp_path / "a.parquet", tmp_path / "b.parquet"
    write_atomic(day_frame(date(2026, 9, 3), 2, 1.0), a)
    write_atomic(day_frame(date(2026, 9, 4), 3, 2.0), b)
    frame = read_cached_days([a, b])
    assert list(frame.columns) == COLUMNS
    assert list(frame["bid_open"]) == [1.0, 1.0, 2.0, 2.0, 2.0]
    assert frame["ts"].is_monotonic_increasing


def test_read_cached_days_with_only_empty_days_gives_the_empty_frame(tmp_path):
    a, b = tmp_path / "a.parquet", tmp_path / "b.parquet"
    write_atomic(empty_cache_frame(), a)
    write_atomic(empty_cache_frame(), b)
    frame = read_cached_days([a, b])
    assert frame.empty and list(frame.columns) == COLUMNS


def test_read_cached_days_missing_file_raises(tmp_path):
    with pytest.raises(Exception):  # noqa: B017 - pyarrow / OS error type is not part of the contract
        read_cached_days([tmp_path / "a.parquet", tmp_path / "missing.parquet"])


def test_read_cached_days_in_chunks_reports_files_and_gives_the_same_frame(tmp_path):
    paths = []
    for i in range(5):
        path = tmp_path / f"{i}.parquet"
        write_atomic(day_frame(date(2026, 9, 3 + i), 2 + i, float(i)), path)
        paths.append(path)
    steps = []
    chunked = read_cached_days(paths, on_chunk=lambda d, t: steps.append((d, t)), chunk_files=2)
    assert steps == [(2, 5), (4, 5), (5, 5)]
    assert chunked.equals(read_cached_days(paths))


def test_read_cached_days_reports_a_single_file_and_a_callback_may_stop_it(tmp_path):
    path = tmp_path / "a.parquet"
    write_atomic(day_frame(date(2026, 9, 3), 2), path)
    steps = []
    read_cached_days([path], on_chunk=lambda d, t: steps.append((d, t)))
    assert steps == [(1, 1)]
    paths = [path, path, path]

    def stop(done, total):
        raise RuntimeError("stop")

    with pytest.raises(RuntimeError):
        read_cached_days(paths, on_chunk=stop, chunk_files=1)


def test_chunked_read_mixes_day_files_with_different_timestamp_units(tmp_path):
    a, b = tmp_path / "a.parquet", tmp_path / "b.parquet"
    first, second = day_frame(date(2026, 9, 3), 2), day_frame(date(2026, 9, 4), 2)
    first["ts"] = first["ts"].astype("datetime64[us, UTC]")
    second["ts"] = second["ts"].astype("datetime64[ms, UTC]")
    write_atomic(first, a)
    write_atomic(second, b)
    chunked = read_cached_days([a, b], on_chunk=lambda d, t: None, chunk_files=1)
    assert len(chunked) == 4 and chunked["ts"].is_monotonic_increasing
    assert (
        chunked["ts"].astype("int64").tolist()
        == read_cached_days([a, b])["ts"].astype("int64").tolist()
    )
