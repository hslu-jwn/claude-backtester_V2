"""Test cases: preserved session loader, development guard, mode/cache CLI, CSV output.
The standalone descriptive tool must not backtest or log strategy trials.
"""

import csv
from datetime import UTC, date, datetime

import pytest
from m1_frames import m1

from backtester.data.cache import cache_path
from backtester.strategy.gap_momentum.config import GapMomentumConfig
from backtester.tools import gap_bucket_study as tool
from backtester.tools.gap_bucket_study import load_session_bars


def test_study_cli_guard_and_output(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(tool, "data_start", lambda symbols, sources, start: start)
    monkeypatch.setattr(
        tool, "study_rows", lambda *args: seen.append(args) or [{"symbol": "ALL", "n": 2}]
    )
    with pytest.raises(SystemExit, match="2021-09-13"):
        tool.main(["--end", "2021-09-14", "--out", str(tmp_path)])
    assert seen == []
    assert tool.main(["--mode", "fx", "--cache-dir", str(tmp_path), "--out", str(tmp_path)]) == 0
    assert seen[0][0] == ["GBPUSD", "EURUSD", "XAUUSD"]
    assert seen[0][1].cache_dir("GBPUSD") == tmp_path
    with (tmp_path / "gap_buckets.csv").open(encoding="utf-8") as f:
        assert list(csv.DictReader(f)) == [{"symbol": "ALL", "n": "2"}]
    assert tool.main(["--end", "2021-09-14", "--allow-test-period", "--out", str(tmp_path)]) == 0


def test_load_session_bars_reads_the_session_window_in_new_york_time(tmp_path):
    day = date(2026, 1, 12)  # winter: 09:30 ET = 14:30 UTC, 16:00 ET = 21:00 UTC
    frame = m1(
        ("14:28", 100, 101, 99, 100, 1.0, 0.1),  # closes 09:29: before the open
        ("14:29", 100, 101, 99, 100.5, 1.0, 0.1),  # closes 09:30: the open
        ("14:30", 100.5, 102, 100, 101, 1.0, 0.1),
        ("20:59", 101, 103, 100.9, 102, 1.0, 0.1),  # closes 16:00: the session close
        ("21:00", 102, 102.5, 101.5, 102.2, 1.0, 0.1),  # closes 16:01: after
        day=day.isoformat(),
    )
    path = cache_path(tmp_path, "NAS100", day)
    path.parent.mkdir(parents=True)
    frame.to_parquet(path, index=False)
    cfg = GapMomentumConfig()
    bars = load_session_bars("NAS100", tmp_path, day, day, cfg)
    assert [b[0] for b in bars] == [
        datetime(2026, 1, 12, 14, 30, tzinfo=UTC),
        datetime(2026, 1, 12, 14, 31, tzinfo=UTC),
        datetime(2026, 1, 12, 21, 0, tzinfo=UTC),
    ]
    assert bars[0][3] == 100.5 and bars[2] == (bars[2][0], 103.0, 100.9, 102.0)


def test_study_rows_preserves_warmup_and_symbol_pooling(monkeypatch):
    from backtester.analytics.gap_buckets import GapDay, bucket_rows

    days = [GapDay(date(2020, 1, 2), 102, 101, 99, 100, 0.01, 2, 104)]
    seen = []
    monkeypatch.setattr(tool, "load_session_bars", lambda *args: seen.append(args) or [])
    monkeypatch.setattr(
        tool,
        "gap_days",
        lambda bars, cfg: [GapDay(date(2019, 12, 31), 102, 101, 99, 100, 0.01, 2, 80), *days],
    )
    from pathlib import Path

    from backtester.data.sources import SymbolSources

    sources = SymbolSources.single(Path("fake"), ["NAS100", "US500"])
    start, end, middle = date(2020, 1, 1), date(2020, 1, 10), date(2020, 1, 5)
    rows = tool.study_rows(["NAS100", "US500"], sources, start, end, "index", middle)
    assert rows == bucket_rows(days, "NAS100", middle) + bucket_rows(
        days, "US500", middle
    ) + bucket_rows(days * 2, "ALL", middle)
    assert all(args[2] < start and args[3] == end for args in seen)


def test_invalid_date_range_stops_before_study(tmp_path, monkeypatch):
    monkeypatch.setattr(tool, "study_rows", lambda *a: pytest.fail("invalid dates read data"))
    with pytest.raises(SystemExit, match="start"):
        tool.main(["--start", "2021-09-13", "--end", "2021-09-12", "--out", str(tmp_path)])
