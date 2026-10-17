"""Update planning: what is missing per symbol and cache (ROADMAP 7.5). No terminal, no network."""

from __future__ import annotations

from datetime import date

from backtester.data.cache import cache_path, empty_cache_frame, write_atomic
from backtester.data.histdata import MonthFile
from backtester.data.update import (
    UpdateConfig,
    histdata_pair,
    last_cached_day,
    missing_range,
    plan_update,
    select_import_files,
)

D = date.fromisoformat


def put(root, symbol, *days):
    for day in days:
        write_atomic(empty_cache_frame(), cache_path(root, symbol, D(day)))


def dirs(tmp_path):
    return {
        "mt5_dir": tmp_path / "mt5",
        "binance_dir": tmp_path / "binance",
        "histdata_dir": tmp_path / "histdata",
    }


def tasks(plan, source):
    return {t.symbol: (t.first, t.last) for t in plan.tasks if t.source == source}


# --- last cached day / missing range -------------------------------------------------------


def test_last_cached_day_none_for_missing_or_empty_folder(tmp_path):
    assert last_cached_day(tmp_path, "NAS100") is None
    (tmp_path / "NAS100" / "2026").mkdir(parents=True)
    assert last_cached_day(tmp_path, "NAS100") is None


def test_last_cached_day_is_the_newest_across_years_and_ignores_tmp_files(tmp_path):
    put(tmp_path, "NAS100", "2025-12-31", "2026-01-02", "2026-01-05")
    (tmp_path / "NAS100" / "2026" / "2026-01-09.parquet.tmp").write_bytes(b"x")
    assert last_cached_day(tmp_path, "NAS100") == D("2026-01-05")


def test_last_cached_day_skips_a_newest_year_folder_without_files(tmp_path):
    put(tmp_path, "NAS100", "2025-12-31")
    (tmp_path / "NAS100" / "2026").mkdir()
    assert last_cached_day(tmp_path, "NAS100") == D("2025-12-31")


def test_missing_range_is_after_last_up_to_yesterday():
    assert missing_range(D("2026-10-10"), D("2026-10-16")) == (D("2026-10-11"), D("2026-10-16"))
    assert missing_range(D("2026-10-16"), D("2026-10-16")) is None
    assert missing_range(D("2026-10-17"), D("2026-10-16")) is None  # cache ahead of the clock


# --- MT5 -----------------------------------------------------------------------------------


def test_mt5_every_symbol_in_the_cache_gets_its_missing_days(tmp_path):
    d = dirs(tmp_path)
    put(d["mt5_dir"], "NAS100", "2026-10-10")
    put(d["mt5_dir"], "EURUSD", "2026-10-14")  # histdata-fed on the chart, still in the MT5 cache
    plan = plan_update(D("2026-10-17"), **d)
    assert tasks(plan, "mt5") == {
        "NAS100": (D("2026-10-11"), D("2026-10-16")),
        "EURUSD": (D("2026-10-15"), D("2026-10-16")),
    }


def test_nothing_missing_gives_an_empty_plan(tmp_path):
    d = dirs(tmp_path)
    put(d["mt5_dir"], "NAS100", "2026-10-16")
    plan = plan_update(D("2026-10-17"), **d)
    assert plan.tasks == () and plan.is_empty


def test_monday_with_sunday_cached_has_nothing_to_do(tmp_path):
    d = dirs(tmp_path)  # 2026-10-19 is a Monday; weekend days are cached as empty files
    put(d["mt5_dir"], "NAS100", "2026-10-16", "2026-10-17", "2026-10-18")
    assert plan_update(D("2026-10-19"), **d).is_empty


def test_monday_with_friday_cached_asks_for_saturday_and_sunday(tmp_path):
    d = dirs(tmp_path)
    put(d["mt5_dir"], "NAS100", "2026-10-16")
    plan = plan_update(D("2026-10-19"), **d)
    assert tasks(plan, "mt5") == {"NAS100": (D("2026-10-17"), D("2026-10-18"))}


def test_mt5_symbol_folder_without_files_is_skipped_not_downloaded_from_scratch(tmp_path):
    d = dirs(tmp_path)
    (d["mt5_dir"] / "US30" / "2026").mkdir(parents=True)
    plan = plan_update(D("2026-10-17"), **d)
    assert plan.tasks == ()
    (skip,) = [s for s in plan.skipped if s.source == "mt5"]
    assert skip.symbol == "US30" and "full download tool" in skip.reason


def test_missing_cache_folders_give_an_empty_plan(tmp_path):
    plan = plan_update(D("2026-10-17"), **dirs(tmp_path))
    assert plan.tasks == ()
    assert {s.symbol for s in plan.skipped} == {"BTCUSDT", "ETHUSDT"}  # binance: no cache


# --- Binance -------------------------------------------------------------------------------


def test_binance_symbols_with_a_cache_get_their_missing_days(tmp_path):
    d = dirs(tmp_path)
    put(d["binance_dir"], "BTCUSDT", "2026-10-14")
    plan = plan_update(D("2026-10-17"), **d)
    assert tasks(plan, "binance") == {"BTCUSDT": (D("2026-10-15"), D("2026-10-16"))}
    assert [s.symbol for s in plan.skipped] == ["ETHUSDT"]


# --- histdata ------------------------------------------------------------------------------


def test_histdata_pair_names():
    assert histdata_pair("NAS100") == "NSXUSD" and histdata_pair("US500") == "SPXUSD"
    assert histdata_pair("XAUUSD") == "XAUUSD"


def test_histdata_waits_until_the_month_is_over(tmp_path):
    d = dirs(tmp_path)
    put(d["histdata_dir"], "NAS100", "2026-09-29", "2026-09-30")
    assert plan_update(D("2026-10-17"), **d).tasks == ()  # October is running
    assert plan_update(D("2026-10-31"), **d).tasks == ()  # its last day is not over yet
    plan = plan_update(D("2026-11-01"), **d)
    (task,) = [t for t in plan.tasks if t.source == "histdata"]
    assert task.symbol == "NAS100" and task.months == (D("2026-10-01"),)
    assert (task.first, task.last) == (D("2026-10-01"), D("2026-10-31"))


def test_histdata_several_months_after_the_last_one(tmp_path):
    d = dirs(tmp_path)
    put(d["histdata_dir"], "XAUUSD", "2026-08-31")
    (task,) = plan_update(D("2026-11-05"), **d).tasks
    assert task.months == (D("2026-09-01"), D("2026-10-01"))


def test_histdata_last_day_inside_a_month_refetches_that_month(tmp_path):
    d = dirs(tmp_path)
    put(d["histdata_dir"], "XAUUSD", "2026-09-14")
    (task,) = plan_update(D("2026-11-05"), **d).tasks
    assert task.months == (D("2026-09-01"), D("2026-10-01"))


def test_histdata_cache_that_is_not_maintained_is_skipped(tmp_path):
    d = dirs(tmp_path)
    put(d["histdata_dir"], "EURUSD", "2021-12-31")  # a closed archive, MT5 feeds the chart
    plan = plan_update(D("2026-11-05"), **d)
    assert plan.tasks == ()
    assert [(s.source, s.symbol) for s in plan.skipped if s.source == "histdata"] == [
        ("histdata", "EURUSD")
    ]


def test_histdata_stale_limit_is_configurable(tmp_path):
    d = dirs(tmp_path)
    put(d["histdata_dir"], "EURUSD", "2021-12-31")
    assert plan_update(D("2022-04-15"), **d).tasks == ()  # 105 days behind: not maintained
    plan = plan_update(D("2022-04-15"), config=UpdateConfig(histdata_max_stale_days=200), **d)
    (task,) = plan.tasks
    assert task.months == (D("2022-01-01"), D("2022-02-01"), D("2022-03-01"))


def test_select_import_files_keeps_the_period_with_the_last_day_and_later_ones(tmp_path):
    def mf(period, yearly=False):
        return MonthFile(tmp_path / f"{period}.csv", "NAS100", D(period), yearly)

    files = [mf("2024-01-01", True), mf("2025-01-01", True), mf("2026-08-01"), mf("2026-09-01"),
             mf("2026-10-01")]  # fmt: skip
    picked = select_import_files(files, D("2026-09-30"))
    assert [f.month for f in picked] == [D("2026-09-01"), D("2026-10-01")]
    # the last day sits in a year file: that year file and later ones
    picked = select_import_files(files, D("2025-12-31"))
    assert [f.month for f in picked] == [D("2025-01-01"), D("2026-08-01"), D("2026-09-01"),
                                         D("2026-10-01")]  # fmt: skip
