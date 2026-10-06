"""histdata.com MT M1 import. Spec: ARCHITECTURE.md › Data sources › histdata.com.

Times in the files are New York local time with DST (checked against TradingView):
UTC−4 in summer (00:00 = 04:00 UTC), UTC−5 in winter.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd
import pytest

from backtester.core.models import Timeframe
from backtester.data.adapters.cache_adapter import CacheAdapter, MissingCacheError
from backtester.data.check import check_symbol
from backtester.data.dukascopy import _COLUMNS, cache_path, read_cached_day
from backtester.data.histdata import (
    HistdataError,
    import_files,
    month_file,
    parse_histdata_mt,
)
from backtester.data.resample import drop_flat_minutes


def write(tmp_path, name: str, lines: list[str]):
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n")
    return path


SEPT = [
    "2026.09.01,00:00,1.354050,1.354070,1.354020,1.354060,0",  # Tue 04:00 UTC (Sep 1: partial)
    "2026.09.02,08:00,1.350000,1.350000,1.350000,1.350000,0",  # flat, real quiet minute
    "2026.09.02,08:01,1.350000,1.350300,1.349900,1.350200,0",
    "2026.09.02,08:03,1.350200,1.350400,1.350100,1.350300,0",  # 08:02 missing (no ticks)
    "2026.09.04,20:30,1.351000,1.351100,1.350900,1.351000,0",  # Fri 20:30 EDT = Sat 00:30 UTC
    "2026.09.30,23:59,1.360000,1.360100,1.359900,1.360000,0",  # = Oct 1 03:59 UTC (partial)
]


def test_new_york_time_is_utc_minus_4_in_summer_and_minus_5_in_winter(tmp_path):
    summer = parse_histdata_mt(write(tmp_path, "a.csv", SEPT[:1]))
    winter = parse_histdata_mt(
        write(tmp_path, "b.csv", ["2026.01.15,12:00,1.25,1.26,1.24,1.255,0"])
    )
    assert summer["ts"][0] == pd.Timestamp("2026-09-01 04:00", tz="UTC")
    assert winter["ts"][0] == pd.Timestamp("2026-01-15 17:00", tz="UTC")


def test_same_columns_as_dukascopy_cache_bid_only_volume_unknown(tmp_path):
    frame = parse_histdata_mt(write(tmp_path, "a.csv", SEPT[:1]))
    assert list(frame.columns) == _COLUMNS
    row = frame.iloc[0]
    assert (row.bid_open, row.bid_high, row.bid_low, row.bid_close) == (
        1.35405,
        1.35407,
        1.35402,
        1.35406,
    )
    assert pd.isna(row.bid_volume)
    assert frame.filter(like="ask_").isna().all().all()


def test_flat_minutes_are_real_and_never_dropped_as_filler(tmp_path):
    frame = parse_histdata_mt(write(tmp_path, "a.csv", SEPT[1:3]))
    assert len(drop_flat_minutes(frame)) == 2


def test_import_writes_only_complete_utc_days_and_weekends_as_empty(tmp_path):
    src = write(tmp_path, "DAT_MT_GBPUSD_M1_202609.csv", SEPT)
    cache = tmp_path / "cache"
    (r,) = import_files([src], cache)
    assert r.symbol == "GBPUSD"
    # Sep 1 UTC starts at 00:00 but the file starts at 04:00 UTC; Oct 1 ends at 03:59
    assert r.days_partial == [date(2026, 9, 1), date(2026, 10, 1)]
    assert r.days_written[0] == date(2026, 9, 2) and r.days_written[-1] == date(2026, 9, 5)
    assert date(2026, 9, 6) in r.days_empty and date(2026, 9, 30) in r.days_empty
    assert not cache_path(cache, "GBPUSD", date(2026, 9, 1)).exists()
    sat = read_cached_day(cache_path(cache, "GBPUSD", date(2026, 9, 5)))
    assert list(sat["ts"]) == [pd.Timestamp("2026-09-05 00:30", tz="UTC")]


def test_neighbouring_month_completes_the_first_day(tmp_path):
    aug = write(
        tmp_path, "DAT_MT_GBPUSD_M1_202608.csv", ["2026.08.31,22:00,1.35,1.36,1.34,1.355,0"]
    )
    sep = write(tmp_path, "DAT_MT_GBPUSD_M1_202609.csv", SEPT)
    (r,) = import_files([sep, aug], tmp_path / "cache")
    assert date(2026, 9, 1) in r.days_written
    day = read_cached_day(cache_path(tmp_path / "cache", "GBPUSD", date(2026, 9, 1)))
    assert list(day["ts"].dt.strftime("%H:%M")) == ["02:00", "04:00"]


def test_cache_adapter_builds_candles_without_spread_and_misses_partial_days(tmp_path):
    src = write(tmp_path, "DAT_MT_GBPUSD_M1_202609.csv", SEPT)
    cache = tmp_path / "cache"
    import_files([src], cache)
    m5 = CacheAdapter(cache).fetch_frame(
        "GBPUSD", Timeframe.M5, datetime(2026, 9, 2, tzinfo=UTC), datetime(2026, 9, 3, tzinfo=UTC)
    )
    assert len(m5) == 1  # 12:00 UTC candle from 08:00, 08:01, 08:03 EDT
    c = m5.iloc[0]
    assert c.ts == pd.Timestamp("2026-09-02 12:00", tz="UTC")
    assert (c.open, c.high, c.low, c.close) == (1.35, 1.3504, 1.3499, 1.3503)
    assert pd.isna(c.spread)
    with pytest.raises(MissingCacheError):
        CacheAdapter(cache).fetch_frame(
            "GBPUSD",
            Timeframe.M5,
            datetime(2026, 9, 1, tzinfo=UTC),
            datetime(2026, 9, 2, tzinfo=UTC),
        )


def test_data_check_has_no_integrity_findings_for_bid_only_data(tmp_path):
    src = write(tmp_path, "DAT_MT_GBPUSD_M1_202609.csv", SEPT)
    import_files([src], tmp_path / "cache")
    report = check_symbol(tmp_path / "cache", "GBPUSD")
    assert [f for f in report.integrity if f.count] == []
    assert not any("spread" in f.name for f in report.outliers)


def test_broken_rows_and_rows_outside_the_month_fail_and_cache_nothing(tmp_path):
    cache = tmp_path / "cache"
    broken = write(
        tmp_path, "DAT_MT_GBPUSD_M1_202609.csv", ["2026.09.02,08:00,1.35,1.34,1.36,1.35,0"]
    )
    with pytest.raises(HistdataError, match="broken"):
        import_files([broken], cache)
    outside = write(
        tmp_path, "DAT_MT_GBPJPY_M1_202609.csv", ["2026.10.01,00:00,216.0,216.1,215.9,216.0,0"]
    )
    with pytest.raises(HistdataError, match="outside"):
        import_files([outside], cache)
    assert not cache.exists()


def test_repeated_minutes_are_merged_in_file_order(tmp_path):
    # real pattern from DAT_MT_GBPUSD_M1_202609.csv lines 2088-2091
    lines = [
        "2026.09.02,10:57,1.35021,1.35057,1.35000,1.35032,0",
        "2026.09.02,10:58,1.35032,1.35032,1.35032,1.35032,0",
        "2026.09.02,10:57,1.35033,1.35033,1.35033,1.35033,0",
        "2026.09.02,10:58,1.35032,1.35049,1.35029,1.35047,0",
    ]
    frame = parse_histdata_mt(write(tmp_path, "a.csv", lines))
    assert frame.attrs["merged_minutes"] == 2
    assert list(frame["ts"].dt.strftime("%H:%M")) == ["14:57", "14:58"]
    first, second = frame.iloc[0], frame.iloc[1]
    assert (first.bid_open, first.bid_high, first.bid_low, first.bid_close) == (
        1.35021,
        1.35057,
        1.35,
        1.35033,
    )
    assert (second.bid_open, second.bid_high, second.bid_low, second.bid_close) == (
        1.35032,
        1.35049,
        1.35029,
        1.35047,
    )
    (r,) = import_files([write(tmp_path, "DAT_MT_GBPUSD_M1_202609.csv", lines)], tmp_path / "cache")
    assert r.merged_minutes == 2


def test_file_name_gives_symbol_and_month(tmp_path):
    mf = month_file(tmp_path / "DAT_MT_GBPJPY_M1_202609.csv")
    assert (mf.symbol, mf.month) == ("GBPJPY", date(2026, 9, 1))
    assert mf.utc_start == datetime(2026, 9, 1, 4, tzinfo=UTC)
    assert mf.utc_end == datetime(2026, 10, 1, 4, tzinfo=UTC)
    with pytest.raises(HistdataError):
        month_file(tmp_path / "GBPJPY.csv")


def test_winter_month_starts_at_new_york_midnight_after_the_clock_change(tmp_path):
    # DST ends Sun 2026-11-01 02:00 New York: Nov 1 00:00 is still EDT, Dec 1 00:00 is EST
    mf = month_file(tmp_path / "DAT_MT_GBPUSD_M1_202611.csv")
    assert mf.utc_start == datetime(2026, 11, 1, 4, tzinfo=UTC)
    assert mf.utc_end == datetime(2026, 12, 1, 5, tzinfo=UTC)


@pytest.mark.parametrize(
    "local",
    ["2026.11.01,01:30", "2026.03.08,02:30"],  # repeated hour (fall back), skipped hour (spring)
)
def test_minute_on_a_dst_change_night_stops_the_import(tmp_path, local):
    path = write(tmp_path, "a.csv", [f"{local},1.30,1.31,1.29,1.305,0"])
    with pytest.raises(HistdataError, match="DST"):
        parse_histdata_mt(path)
