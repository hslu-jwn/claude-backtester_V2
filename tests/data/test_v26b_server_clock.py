"""Shared server clock, per user addendum A-C; all caches are synthetic."""

from datetime import date

import pandas as pd
import pytest
from test_v26b_data import frame

from backtester.data.cache import cache_path, read_cached_day, write_atomic
from backtester.data.cache_repair import build_server_clock_table, repair_mt5


def put(root, symbol, day, shift=0, n=180):
    write_atomic(frame(day, n=n, shift=shift), cache_path(root, symbol, day))


@pytest.mark.parametrize("day", [date(2018, 3, 14), date(2020, 3, 18), date(2021, 9, 13)])
def test_mt5_only_symbol_inherits_reference_and_reruns(tmp_path, day):
    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    put(hist, "GBPUSD", day)
    put(mt5, "GBPUSD", day, -1)
    put(mt5, "US30", day, -1)
    table = build_server_clock_table(mt5, hist)
    assert table[str(day)]["shift"] == 1
    repair_mt5("GBPUSD", mt5, hist, server_table=table)
    repair_mt5("US30", mt5, hist, server_table=table)
    corrected = read_cached_day(cache_path(mt5, "US30", day))
    assert corrected.ts.iloc[0].hour == 10
    assert build_server_clock_table(mt5, hist) == table
    repair_mt5("US30", mt5, hist, server_table=table)
    assert corrected.equals(read_cached_day(cache_path(mt5, "US30", day)))


def test_disagreeing_references_drop_every_symbol_and_list_readings(tmp_path):
    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    day = date(2021, 3, 17)
    for symbol, shift in [("GBPUSD", 0), ("XAUUSD", -1)]:
        put(hist, symbol, day)
        put(mt5, symbol, day, shift)
    put(mt5, "US30", day)
    table = build_server_clock_table(mt5, hist)
    assert table[str(day)] == {
        "status": "ambiguous",
        "shift": None,
        "readings": {"GBPUSD": 0, "XAUUSD": 1},
    }
    for symbol in ["GBPUSD", "XAUUSD", "US30"]:
        decisions = repair_mt5(symbol, mt5, hist, server_table=table)
        assert "ambiguous" in decisions[0]["decision"]
        assert not cache_path(mt5, symbol, day).exists()


def test_no_reference_drops_development_but_test_period_is_untouched(tmp_path):
    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    days = [date(2021, 9, 13), date(2021, 9, 14), date(2023, 3, 15)]
    for day in days:
        put(mt5, "US30", day)
    before = {d: cache_path(mt5, "US30", d).read_bytes() for d in days[1:]}
    table = build_server_clock_table(mt5, hist)
    assert table == {str(days[0]): {"status": "no reference", "shift": None, "readings": {}}}
    repair_mt5("US30", mt5, hist, server_table=table)
    assert not cache_path(mt5, "US30", days[0]).exists()
    for day in days[1:]:
        assert cache_path(mt5, "US30", day).read_bytes() == before[day]


def test_sparse_reference_cannot_prove_server_date(tmp_path):
    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    for day, n in [(date(2020, 1, 6), 400), (date(2020, 1, 7), 400), (date(2020, 1, 8), 180)]:
        put(mt5, "GBPUSD", day, n=n)
        put(hist, "GBPUSD", day, n=n)
    table = build_server_clock_table(mt5, hist)
    assert table["2020-01-08"]["status"] == "no reference"


def test_correction_cannot_overwrite_test_period_at_boundary(tmp_path):
    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    day, test_day = date(2021, 9, 13), date(2021, 9, 14)
    bars = frame(day)
    bars["ts"] = bars.ts + pd.Timedelta(hours=12)
    write_atomic(bars, cache_path(mt5, "US30", day))
    put(mt5, "US30", test_day)
    before = {d: cache_path(mt5, "US30", d).read_bytes() for d in [day, test_day]}
    table = {str(day): {"status": "proven", "shift": 1, "readings": {"GBPUSD": 1}}}
    with pytest.raises(ValueError, match="test-period boundary"):
        repair_mt5("US30", mt5, hist, server_table=table)
    for d, original in before.items():
        assert cache_path(mt5, "US30", d).read_bytes() == original
