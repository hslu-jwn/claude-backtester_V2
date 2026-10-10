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


def test_month_starts_follow_europes_summer_time_dates(tmp_path):
    # Europe's summer time ends Sun 2026-10-25 01:00 UTC (the US: 2026-11-01): Oct 1 00:00
    # is UTC-4, Nov 1 00:00 already UTC-5 (TradingView check, 2026-10-09)
    mf = month_file(tmp_path / "DAT_MT_GBPUSD_M1_202610.csv")
    assert mf.utc_start == datetime(2026, 10, 1, 4, tzinfo=UTC)
    assert mf.utc_end == datetime(2026, 11, 1, 5, tzinfo=UTC)


@pytest.mark.parametrize(
    ("local", "utc"),
    [
        # US summer time, Europe not yet: UTC-5. The user's TradingView check: XAUUSD 5m
        # 2026-03-18 14:00 UTC (O 4878.655, H 4887.310, L 4872.340, C 4884.035 on OANDA)
        ("2026.03.18,09:00", "2026-03-18 14:00"),
        ("2026.10.28,09:00", "2026-10-28 14:00"),  # Europe back on winter time, the US not
        ("2026.03.27,09:00", "2026-03-27 14:00"),  # Friday before Europe's change
        ("2026.03.30,09:00", "2026-03-30 13:00"),  # Monday after: both on summer time
        ("2026.10.23,09:00", "2026-10-23 13:00"),  # Friday before Europe's change back
        ("2026.11.02,09:00", "2026-11-02 14:00"),  # both on winter time
    ],
)
def test_clock_changes_on_europes_dates(tmp_path, local, utc):
    frame = parse_histdata_mt(write(tmp_path, "a.csv", [f"{local},1.30,1.31,1.29,1.305,0"]))
    assert frame["ts"][0] == pd.Timestamp(utc, tz="UTC")


@pytest.mark.parametrize(
    "local",
    # Europe's change at 01:00 UTC Sunday = Saturday 20:00 on this clock (FX closed):
    # repeated hour (back to winter time), skipped hour (to summer time)
    ["2026.10.24,20:30", "2026.03.28,20:30"],
)
def test_minute_in_europes_change_hour_stops_the_import(tmp_path, local):
    path = write(tmp_path, "a.csv", [f"{local},1.30,1.31,1.29,1.305,0"])
    with pytest.raises(HistdataError, match="summer time change"):
        parse_histdata_mt(path)


# --- yearly files and zips (full history, 2026-10-09) ----------------------------------


def test_year_file_name_and_period(tmp_path):
    yf = month_file(tmp_path / "DAT_MT_XAUUSD_M1_2023.csv")
    assert (yf.symbol, yf.month, yf.end, yf.yearly) == ("XAUUSD", date(2023, 1, 1),
                                                        date(2024, 1, 1), True)  # fmt: skip
    assert yf.utc_start == datetime(2023, 1, 1, 5, tzinfo=UTC)  # New York midnight, EST
    assert yf.utc_end == datetime(2024, 1, 1, 5, tzinfo=UTC)


YEAR_2023 = [
    "2023.01.02,18:00,1830.000000,1831.000000,1829.000000,1830.500000,0",  # Mon 23:00 UTC
    "2023.07.03,10:00,1920.000000,1921.000000,1919.000000,1920.500000,0",  # EDT: 14:00 UTC
    "2023.12.29,16:59,2062.000000,2063.000000,2061.000000,2062.500000,0",  # Fri 21:59 UTC
    "2023.12.31,18:00,2064.000000,2065.000000,2063.000000,2064.500000,0",  # Sun 23:00 UTC
    "2023.12.31,23:59,2065.000000,2066.000000,2064.000000,2065.500000,0",  # = 01-01 04:59 UTC
]
YEAR_2024 = [
    "2024.01.01,00:00,2066.000000,2067.000000,2065.000000,2066.500000,0",  # 01-01 05:00 UTC
    "2024.01.02,03:00,2070.000000,2071.000000,2069.000000,2070.500000,0",
]


def test_a_year_file_is_imported_like_its_months(tmp_path):
    path = write(tmp_path, "DAT_MT_XAUUSD_M1_2023.csv", YEAR_2023)
    cache = tmp_path / "cache"
    (r,) = import_files([path], cache)
    assert r.days_written[0] == date(2023, 1, 2) and date(2023, 7, 3) in r.days_written
    day = read_cached_day(cache_path(cache, "XAUUSD", date(2023, 7, 3)))
    assert day["ts"].tolist() == [pd.Timestamp("2023-07-03 14:00", tz="UTC")]  # EDT
    # 01-01 of 2023 starts at 05:00 UTC in this file and 2024-01-01 at 00:00 UTC in it:
    # without the neighbouring years both are only partly covered
    assert r.days_partial == [date(2023, 1, 1), date(2024, 1, 1)]


def test_the_year_boundary_is_completed_by_the_next_year(tmp_path):
    a = write(tmp_path, "DAT_MT_XAUUSD_M1_2023.csv", YEAR_2023)
    b = write(tmp_path, "DAT_MT_XAUUSD_M1_202401.csv", YEAR_2024)  # a month of the next year
    cache = tmp_path / "cache"
    (r,) = import_files([a, b], cache)
    assert date(2024, 1, 1) in r.days_written and date(2023, 12, 31) in r.days_written
    new_year = read_cached_day(cache_path(cache, "XAUUSD", date(2024, 1, 1)))
    # 31 Dec 23:59 New York (EST) = 1 Jan 04:59 UTC, from the 2023 file; 1 Jan 00:00 NY =
    # 05:00 UTC, from the 2024 file: one UTC day from two files
    assert new_year["ts"].tolist() == [
        pd.Timestamp("2024-01-01 04:59", tz="UTC"),
        pd.Timestamp("2024-01-01 05:00", tz="UTC"),
    ]
    dec31 = read_cached_day(cache_path(cache, "XAUUSD", date(2023, 12, 31)))
    assert dec31["ts"].tolist() == [pd.Timestamp("2023-12-31 23:00", tz="UTC")]


def test_year_files_inside_zips_and_folders(tmp_path):
    import zipfile

    raw = tmp_path / "raw"
    raw.mkdir()
    with zipfile.ZipFile(raw / "HISTDATA_COM_MT_XAUUSD_M1_2023.zip", "w") as z:
        z.writestr("DAT_MT_XAUUSD_M1_2023.csv", "\n".join(YEAR_2023) + "\n")
        z.writestr("DAT_MT_XAUUSD_M1_2023.txt", "histdata.com readme")
    write(raw, "DAT_MT_XAUUSD_M1_202401.csv", YEAR_2024)
    (r,) = import_files([raw], tmp_path / "cache")
    assert date(2024, 1, 1) in r.days_written and date(2023, 7, 3) in r.days_written


def test_overlapping_periods_are_refused(tmp_path):
    a = write(tmp_path, "DAT_MT_XAUUSD_M1_2024.csv", YEAR_2024)
    b = write(tmp_path, "DAT_MT_XAUUSD_M1_202401.csv", YEAR_2024)
    with pytest.raises(HistdataError, match="overlap"):
        import_files([a, b], tmp_path / "cache")


# --- indices and pair subfolders (2026-10-10) -----------------------------------------

NAS_SEPT = [
    "2026.09.02,09:30,29051.930000,29055.470000,28997.290000,29037.240000,0",  # 13:30 UTC
]


@pytest.mark.parametrize(("theirs", "ours"), [("NSXUSD", "NAS100"), ("SPXUSD", "US500")])
def test_histdata_index_names_are_cached_under_ours(tmp_path, theirs, ours):
    assert month_file(tmp_path / f"DAT_MT_{theirs}_M1_2023.csv").symbol == ours
    path = write(tmp_path, f"DAT_MT_{theirs}_M1_202609.csv", NAS_SEPT)
    (r,) = import_files([path], tmp_path / "cache")
    assert r.symbol == ours
    day = read_cached_day(cache_path(tmp_path / "cache", ours, date(2026, 9, 2)))
    assert day["ts"].tolist() == [pd.Timestamp("2026-09-02 13:30", tz="UTC")]


def test_index_daily_break_moves_with_golds_clock(tmp_path):
    # The indices' break starts 16:15 New York. In the week only the US is on summer time
    # histdata writes it at 15:15 (like gold's 17:00 close at 16:00); converted, both
    # weeks give 16:15 NY = 20:15 UTC (summer time) / 21:15 UTC (winter).
    lines = [
        "2026.03.18,15:14,24400.0,24401.0,24399.0,24400.5,0",  # US-only summer time week
        "2026.01.14,16:14,25400.0,25401.0,25399.0,25400.5,0",  # winter
        "2026.07.15,16:14,26400.0,26401.0,26399.0,26400.5,0",  # US + EU summer time
    ]
    ts = parse_histdata_mt(write(tmp_path, "a.csv", lines))["ts"]
    ny = [t.tz_convert("America/New_York").strftime("%H:%M") for t in ts]
    assert ny == ["16:14", "16:14", "16:14"]


def test_a_folder_of_pair_subfolders_and_single_files(tmp_path):
    import zipfile

    raw = tmp_path / "raw"
    (raw / "XAUUSD").mkdir(parents=True)
    (raw / "NAS100").mkdir()
    with zipfile.ZipFile(raw / "XAUUSD" / "HISTDATA_COM_MT_XAUUSD_M1_2023.zip", "w") as z:
        z.writestr("DAT_MT_XAUUSD_M1_2023.csv", "\n".join(YEAR_2023) + "\n")
    write(raw / "XAUUSD", "DAT_MT_XAUUSD_M1_202401.csv", YEAR_2024)
    write(raw / "NAS100", "DAT_MT_NSXUSD_M1_202609.csv", NAS_SEPT)
    write(raw / "NAS100", "notes.txt", ["not a histdata file"])
    nas, gold = import_files([raw], tmp_path / "cache")
    assert (nas.symbol, gold.symbol) == ("NAS100", "XAUUSD")
    assert date(2026, 9, 2) in nas.days_written and date(2024, 1, 1) in gold.days_written
    # a single file in a subfolder still works on its own
    (single,) = import_files([raw / "NAS100" / "DAT_MT_NSXUSD_M1_202609.csv"], tmp_path / "c2")
    assert single.symbol == "NAS100"


def test_the_same_file_flat_and_in_a_subfolder_is_refused(tmp_path):
    raw = tmp_path / "raw"
    (raw / "NAS100").mkdir(parents=True)
    write(raw, "DAT_MT_NSXUSD_M1_202609.csv", NAS_SEPT)
    write(raw / "NAS100", "DAT_MT_NSXUSD_M1_202609.csv", NAS_SEPT)
    with pytest.raises(HistdataError, match="overlap"):
        import_files([raw], tmp_path / "cache")
