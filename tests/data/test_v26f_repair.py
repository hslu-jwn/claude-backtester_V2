"""Full-check findings 3 and 4; synthetic caches only."""

from datetime import date

import pandas as pd
import pytest

from backtester.data import cache_repair as repair
from backtester.data import mt5_download as download
from backtester.data.cache import cache_path, read_cached_day, write_atomic
from backtester.filelock import file_lock


def bars(stamp):
    return download.cache_frame(
        pd.DataFrame(
            {
                "ts": pd.to_datetime([stamp], utc=True),
                "open": [100.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1.0],
                "spread": [0.1],
            }
        )
    )


def test_spill_into_absent_day_is_idempotent(tmp_path):
    cache, hist = tmp_path / "cache", tmp_path / "hist"
    day = date(2020, 1, 6)
    write_atomic(bars("2020-01-06T23:30Z"), cache_path(cache, "US30", day))
    table = {d: {"status": "proven", "shift": 1} for d in ("2020-01-06", "2020-01-07")}
    repair.repair_mt5("US30", cache, hist, server_table=table)
    files = {
        p.relative_to(cache): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in (cache / "US30").rglob("*.parquet")
    }
    repair.repair_mt5("US30", cache, hist, server_table=table)
    assert {
        p.relative_to(cache): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in (cache / "US30").rglob("*.parquet")
    } == files
    assert read_cached_day(cache_path(cache, "US30", date(2020, 1, 7))).ts.tolist() == [
        pd.Timestamp("2020-01-07T00:30Z")
    ]
    assert set(repair.original_inputs(cache, "US30")) == {day}


def test_repair_capture_and_download_share_mutation_lock(tmp_path, monkeypatch):
    from contextlib import contextmanager
    from types import SimpleNamespace

    held = []
    repair_paths, download_paths = [], []

    def track(paths):
        @contextmanager
        def lock(path, **kwargs):
            paths.append(path)
            with file_lock(path, **kwargs):
                held.append(path)
                try:
                    yield
                finally:
                    held.pop()

        return lock

    monkeypatch.setattr(repair, "file_lock", track(repair_paths))
    monkeypatch.setattr(download, "file_lock", track(download_paths), raising=False)
    day = date(2020, 1, 6)
    write_atomic(bars("2020-01-06T23:30Z"), cache_path(tmp_path, "US30", day))
    copy = repair.shutil.copy2

    def capture(*args, **kwargs):
        assert held, "original capture must be locked"
        return copy(*args, **kwargs)

    monkeypatch.setattr(repair.shutil, "copy2", capture)
    repair.repair_mt5("US30", tmp_path, tmp_path / "hist", server_table={})

    def publish(frame, path):
        assert held, "download publication must be locked"
        with pytest.raises(TimeoutError), file_lock(repair_paths[0], timeout=0):
            pass
        write_atomic(frame, path)

    monkeypatch.setattr(download, "write_atomic", publish)
    raw = pd.DataFrame(
        {
            "ts": pd.to_datetime(["2020-01-06T10:00Z", "2020-01-07T10:00Z"]),
            "open": [100.0, 100.0],
            "high": [102.0, 102.0],
            "low": [99.0, 99.0],
            "close": [101.0, 101.0],
            "volume": [1.0, 1.0],
            "spread": [0.1, 0.1],
        }
    )
    monkeypatch.setattr(download, "utc_bars", lambda *a: raw)
    adapter = SimpleNamespace(now=lambda: pd.Timestamp("2020-02-01T00:00Z"))
    download.download_symbol(adapter, "US30", day, date(2020, 1, 7), tmp_path, min_day_bars=1)
    assert download_paths and set(download_paths) == set(repair_paths)
