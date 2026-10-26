"""Offline regression cases for V2.6b; written before implementation."""

import io
from datetime import date
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from backtester.data.cache import cache_path, read_cached_day, write_atomic
from backtester.data.histdata import HistdataError, histdata_to_utc, import_files, parse_histdata_mt


@pytest.mark.parametrize("year", range(2015, 2020))
def test_every_gap_week_and_normal_week(year):
    ny, eu = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    sample = [
        d
        for d in days
        if d.weekday() == 2
        and (
            bool(d.replace(tzinfo=ny).dst()) != bool(d.replace(tzinfo=eu).dst())
            or (d.month == 7 and d.day <= 7)
        )
    ]
    local = pd.Series([d + pd.Timedelta(hours=12) for d in sample])
    actual = histdata_to_utc(local)
    expected = []
    for stamp in local:
        if year <= 2018:
            expected.append(stamp.tz_localize(ny).tz_convert("UTC"))
        else:
            # 2019: NY standard offset plus London's summer time.
            expected.append(
                (stamp + pd.Timedelta(hours=5) - stamp.replace(tzinfo=eu).dst()).tz_localize("UTC")
            )
    assert list(actual) == expected


def test_mixed_clock_periods_and_2023_unchanged():
    local = pd.Series(pd.to_datetime(["2018-03-14 12:00", "2019-03-13 12:00", "2023-03-15 12:00"]))
    assert list(histdata_to_utc(local).dt.hour) == [16, 17, 17]


@pytest.mark.parametrize("stamp", ["2018-03-11 02:30", "2018-11-04 01:30"])
def test_us_transition_ambiguity_is_an_error(stamp):
    with pytest.raises(HistdataError):
        histdata_to_utc(pd.Series(pd.to_datetime([stamp])))


def test_two_year_files_complete_january_first(tmp_path):
    a = tmp_path / "DAT_MT_GBPUSD_M1_2019.csv"
    b = tmp_path / "DAT_MT_GBPUSD_M1_2020.csv"
    a.write_text("2019.12.31,23:59,1,1,1,1,0\n")
    b.write_text("2020.01.01,00:00,1,1,1,1,0\n")
    cache = tmp_path / "cache"
    import_files([a, b], cache)
    frame = read_cached_day(cache_path(cache, "GBPUSD", date(2020, 1, 1)))
    assert frame.ts.dt.strftime("%H:%M").tolist() == ["04:59", "05:00"]


def test_continuity_rejects_before_writing_and_names_file_date(tmp_path):
    src = tmp_path / "DAT_MT_GRXEUR_M1_202006.csv"
    src.write_text(
        "2020.06.10,12:00,12000,12000,12000,12000,0\n2020.06.11,12:00,3100,3100,3100,3100,0\n"
    )
    with pytest.raises(HistdataError, match=r"DAT_MT_GRXEUR_M1_202006.csv.*2020-06-11"):
        import_files([src], tmp_path / "cache")
    assert not list((tmp_path / "cache").rglob("*.parquet"))


def test_continuity_has_configurable_limit_and_explicit_explanation(tmp_path):
    from backtester.data.histdata import ImportConfig

    src = tmp_path / "DAT_MT_GBPUSD_M1_202006.csv"
    src.write_text("2020.06.10,12:00,100,100,100,100,0\n2020.06.11,12:00,130,130,130,130,0\n")
    import_files([src], tmp_path / "wide", config=ImportConfig(max_day_close_jump=0.5))
    import_files(
        [src],
        tmp_path / "explained",
        config=ImportConfig(
            explained_jumps=(("GBPUSD", date(2020, 6, 11), "synthetic documented event"),)
        ),
    )


def test_ger40_bad_days_excluded_and_existing_cache_invalidated(tmp_path):
    src = tmp_path / "DAT_MT_GRXEUR_M1_202006.csv"
    src.write_text(
        "2020.06.12,12:00,12000,12000,12000,12000,0\n2020.06.15,12:00,3100,3100,3100,3100,0\n"
    )
    cache = tmp_path / "cache"
    bad = cache_path(cache, "GER40", date(2020, 6, 15))
    write_atomic(parse_histdata_mt(io.StringIO("2020.06.15,12:00,3100,3100,3100,3100,0\n")), bad)
    import_files([src], cache)
    assert not bad.exists()
    assert cache_path(cache, "GER40", date(2020, 6, 12)).exists()
    assert "3100" in src.read_text()


def test_continuity_compares_adjacent_files_but_not_missing_periods(tmp_path):
    first = tmp_path / "DAT_MT_GBPUSD_M1_202001.csv"
    adjacent = tmp_path / "DAT_MT_GBPUSD_M1_202002.csv"
    distant = tmp_path / "DAT_MT_GBPUSD_M1_202101.csv"
    first.write_text("2020.01.31,12:00,100,100,100,100,0\n")
    adjacent.write_text("2020.02.03,12:00,200,200,200,200,0\n")
    distant.write_text("2021.01.04,12:00,200,200,200,200,0\n")
    with pytest.raises(HistdataError, match="2020-02-03"):
        import_files([first, adjacent], tmp_path / "adjacent")
    import_files([first, distant], tmp_path / "distant")


def frame(day, n=100, shift=0):
    ts = pd.date_range(f"{day} 10:00", periods=n, freq="min", tz="UTC") + pd.Timedelta(hours=shift)
    # Irregular deterministic prices make a one-hour alignment unique.
    prices = [100 + (i * 17 % 43) / 10 for i in range(n)]
    bars = pd.DataFrame(
        {
            "ts": ts,
            "open": prices,
            "high": [p + 0.1 for p in prices],
            "low": [p - 0.1 for p in prices],
            "close": prices,
            "volume": 1.0,
            "spread": 0.01,
        }
    )
    from backtester.data.mt5_download import cache_frame

    return cache_frame(bars)


def test_mt5_day_alignment_requires_clear_evidence():
    from backtester.data.cache_repair import proven_shift

    ref = frame("2018-03-14", n=180)
    assert proven_shift(frame("2018-03-14", n=180, shift=-1), ref) == 1
    assert proven_shift(ref, ref) == 0
    assert proven_shift(ref.iloc[:5], ref) is None
    flat = ref.copy()
    flat.loc[:, ["bid_open", "bid_high", "bid_low", "bid_close"]] = 100.0
    assert proven_shift(flat, flat) is None


def test_quality_is_per_symbol_year_and_threshold_strict():
    from backtester.data.cache_repair import QualityConfig, bad_density_days

    counts = {
        date(2019, 1, d): n for d, n in [(7, 100), (8, 100), (9, 50), (10, 49), (11, 0), (12, 0)]
    }
    counts.update({date(2019, 1, 14): 100, date(2019, 1, 15): 100})
    assert bad_density_days(counts) == {date(2019, 1, 10), date(2019, 1, 11)}
    assert date(2019, 1, 9) in bad_density_days(counts, QualityConfig(min_weekday_share=0.6))


def test_repair_quarantines_uncertain_days_idempotently_and_falls_back(tmp_path):
    from backtester.data.adapters.cache_adapter import PreferredCacheAdapter
    from backtester.data.cache_repair import repair_mt5

    mt5, hist = tmp_path / "mt5", tmp_path / "hist"
    for d in [date(2018, 3, 14), date(2018, 3, 15), date(2018, 3, 16)]:
        write_atomic(frame(d, 180), cache_path(hist, "GBPUSD", d))
        write_atomic(frame(d, 180, shift=-1), cache_path(mt5, "GBPUSD", d))
    unknown = date(2014, 1, 6)
    write_atomic(frame(unknown), cache_path(mt5, "GBPUSD", unknown))
    modern = date(2023, 3, 15)
    write_atomic(frame(modern), cache_path(mt5, "GBPUSD", modern))
    original = cache_path(mt5, "GBPUSD", modern).read_bytes()
    repair_mt5("GBPUSD", mt5, hist)
    corrected = read_cached_day(cache_path(mt5, "GBPUSD", date(2018, 3, 14)))
    assert corrected.ts.iloc[0].hour == 10
    assert not cache_path(mt5, "GBPUSD", unknown).exists()
    assert cache_path(mt5, "GBPUSD", modern).read_bytes() == original
    repair_mt5("GBPUSD", mt5, hist)
    pd.testing.assert_frame_equal(
        corrected, read_cached_day(cache_path(mt5, "GBPUSD", date(2018, 3, 14)))
    )
    sparse = date(2021, 1, 6)
    for d, n in [(date(2021, 1, 4), 100), (date(2021, 1, 5), 100), (sparse, 10)]:
        write_atomic(frame(d, n), cache_path(mt5, "GBPUSD", d))
        write_atomic(frame(d), cache_path(hist, "GBPUSD", d))
    repair_mt5("GBPUSD", mt5, hist)
    assert PreferredCacheAdapter(hist, mt5)._path("GBPUSD", sparse) == cache_path(
        hist, "GBPUSD", sparse
    )


@pytest.mark.parametrize("message", ["unknown symbol", "connection failed", "timeout"])
def test_first_chunk_mt5_error_is_not_no_history(tmp_path, monkeypatch, message):
    from test_mt5_download import make

    from backtester.data import mt5_download as dl
    from backtester.data.adapters.mt5_adapter import Mt5Error

    _, adapter = make({})

    def fail(*args):
        raise Mt5Error(message)

    monkeypatch.setattr(dl, "utc_bars", fail)
    with pytest.raises(Mt5Error, match=message):
        dl.download_symbol(adapter, "NAS100", date(2026, 9, 1), date(2026, 9, 2), tmp_path)


def test_explicit_no_history_is_skipped(tmp_path, monkeypatch):
    from test_mt5_download import make

    from backtester.data import mt5_download as dl
    from backtester.data.adapters.mt5_adapter import Mt5NoHistory

    _, adapter = make({})

    def fail(*args):
        raise Mt5NoHistory("no history")

    monkeypatch.setattr(dl, "utc_bars", fail)
    assert (
        dl.download_symbol(adapter, "NAS100", date(2026, 9, 1), date(2026, 9, 2), tmp_path).bars
        == 0
    )


@pytest.mark.parametrize("no_history", [False, True])
def test_errors_after_history_starts_are_never_swallowed(tmp_path, monkeypatch, no_history):
    from test_mt5_download import make

    from backtester.data import mt5_download as dl
    from backtester.data.adapters.mt5_adapter import Mt5Error, Mt5NoHistory

    _, adapter = make({date(2026, 9, 1): 120, date(2026, 9, 2): 120})
    original = dl.utc_bars
    calls = 0

    def fetch(*args):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise (Mt5NoHistory if no_history else Mt5Error)("synthetic later failure")
        return original(*args)

    monkeypatch.setattr(dl, "utc_bars", fetch)
    with pytest.raises(Mt5Error, match="synthetic later failure"):
        dl.download_symbol(
            adapter, "NAS100", date(2026, 9, 1), date(2026, 9, 3), tmp_path, chunk_days=1
        )


@pytest.mark.parametrize("end", [date(2026, 9, 20), date(2026, 9, 21), date(2026, 8, 31)])
def test_download_rejects_incomplete_or_reversed_days(tmp_path, end):
    from test_mt5_download import make

    from backtester.data.mt5_download import download_symbol

    _, adapter = make({})
    with pytest.raises(ValueError):
        download_symbol(adapter, "NAS100", date(2026, 9, 1), end, tmp_path)


@pytest.mark.parametrize("recover", [True, False])
def test_binance_daily_holes_retried_once(tmp_path, monkeypatch, recover):
    from backtester.data import binance as b

    cfg = b.BinanceConfig(
        tmp_path / "cache", tmp_path / "flow", tmp_path / "fund", tmp_path / "tmp"
    )
    calls = []

    def process(cfg, symbol, url, days, fetch, log):
        calls.append(days[0])
        if len(calls) == 1 or not recover:
            raise b.NotFoundError(url)
        return 7

    monkeypatch.setattr(b, "_process_zip", process)
    r = b.download_month("BTCUSDT", date(2026, 9, 1), cfg, None, date(2026, 9, 2))
    assert calls == [date(2026, 9, 1)] * 2
    assert r.missing_days == (0 if recover else 1)
    assert r.bars == (7 if recover else 0)


def test_cache_write_uses_unique_temp_names_and_cleans_failed_write(tmp_path, monkeypatch):
    import pandas as pd

    from backtester.data.cache import empty_cache_frame

    seen = []
    original = pd.DataFrame.to_parquet

    def record(self, path, **kwargs):
        seen.append(str(path))
        return original(self, path, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_parquet", record)
    for _ in range(2):
        write_atomic(empty_cache_frame(), tmp_path / "day.parquet")
    assert len(set(seen)) == 2

    def fail(self, path, **kwargs):
        raise OSError("disk failure")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fail)
    with pytest.raises(OSError, match="disk failure"):
        write_atomic(empty_cache_frame(), tmp_path / "day.parquet")
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize(
    "code,kind", [(-4, "Mt5NoHistory"), (-1, "Mt5Error"), (-10005, "Mt5Error")]
)
def test_mt5_no_history_is_classified_only_by_specific_error(code, kind):
    from datetime import UTC, datetime

    from test_mt5_download import make

    from backtester.core.models import Timeframe
    from backtester.data.adapters import mt5_adapter as m

    fake, adapter = make({})
    fake.copy_rates_range = lambda *args: None
    fake.last_error = lambda: (code, "synthetic error")
    with pytest.raises(m.Mt5Error) as error:
        adapter.raw_frame(
            "NAS100",
            Timeframe.M1,
            datetime(2010, 1, 1, tzinfo=UTC),
            datetime(2010, 2, 1, tzinfo=UTC),
        )
    assert type(error.value).__name__ == kind


def test_repair_preserves_bars_across_midnight(tmp_path):
    from backtester.data.cache_repair import repair_mt5

    hist, mt5 = tmp_path / "hist", tmp_path / "mt5"
    # Both source dates contain the same unique price sequence as the reference,
    # but source timestamps are one hour early. The correction moves bars to the next day.
    reference = frame("2018-03-14", n=2880)
    reference["ts"] = pd.date_range("2018-03-14", periods=2880, freq="min", tz="UTC")
    source = reference.assign(ts=reference.ts - pd.Timedelta(hours=1))
    for folder, f in [(hist, reference), (mt5, source)]:
        for day, part in f.groupby(f.ts.dt.date):
            write_atomic(part, cache_path(folder, "GBPUSD", day))
    repair_mt5("GBPUSD", mt5, hist)
    result = read_cached_day(cache_path(mt5, "GBPUSD", date(2018, 3, 14)))
    # The previous input date has only 60 bars and cannot establish its own clock;
    # it is excluded, while all proved bars from the other input date survive.
    assert result.ts.min() == pd.Timestamp("2018-03-14 01:00", tz="UTC")
    assert result.ts.max() == pd.Timestamp("2018-03-14 23:59", tz="UTC")
    assert len(result) == 1380
    next_day = read_cached_day(cache_path(mt5, "GBPUSD", date(2018, 3, 15)))
    assert len(next_day) == 1440
    assert next_day.ts.min() == pd.Timestamp("2018-03-15 00:00", tz="UTC")
    assert next_day.ts.max() == pd.Timestamp("2018-03-15 23:59", tz="UTC")
