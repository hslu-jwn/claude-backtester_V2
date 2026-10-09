"""Data check report. Spec: ROADMAP.md › 0.3."""

from __future__ import annotations

from datetime import UTC, date, datetime

import numpy as np
import pandas as pd
import pytest
from m1_frames import m1

from backtester.data import check
from backtester.data.check import DataCheckConfig, GapKind, classify_gap, daily_closes
from backtester.data.dukascopy import _empty_cache_frame, cache_path
from backtester.data.sources import SymbolSources

CFG = DataCheckConfig()


def utc(y, mo, d, h, mi=0) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=UTC)


def kind(start: datetime, end: datetime, missing: set[date] = frozenset()) -> GapKind:
    return classify_gap(start, end, set(missing), CFG)


# --- gap classification ---------------------------------------------------------------


def test_daily_close_follows_new_york_dst():
    # 17:00 New York = 21:00 UTC in summer (EDT), 22:00 UTC in winter (EST).
    assert daily_closes(utc(2026, 9, 2, 0), utc(2026, 9, 3, 0), CFG) == [
        datetime(2026, 9, 2, 17, tzinfo=check.NEW_YORK)
    ]
    winter = daily_closes(utc(2026, 1, 14, 0), utc(2026, 1, 15, 0), CFG)
    assert [c.astimezone(UTC) for c in winter] == [utc(2026, 1, 14, 22)]


def test_gold_daily_break_summer_and_winter():
    assert kind(utc(2026, 9, 2, 21), utc(2026, 9, 2, 22)) is GapKind.DAILY_BREAK
    assert kind(utc(2026, 1, 14, 22), utc(2026, 1, 14, 23)) is GapKind.DAILY_BREAK


def test_one_hour_gap_not_at_the_close_is_unexpected():
    # Same 60 minutes as a break, but at 09:00-10:00 NY: no close inside.
    assert kind(utc(2026, 9, 2, 13), utc(2026, 9, 2, 14)) is GapKind.UNEXPECTED


def test_short_gap_without_close_is_only_counted():
    assert kind(utc(2026, 9, 2, 13), utc(2026, 9, 2, 13, 4)) is GapKind.SHORT
    assert kind(utc(2026, 9, 2, 13), utc(2026, 9, 2, 13, 5)) is GapKind.UNEXPECTED


def test_weekend_gold_and_fx():
    # Gold: Fri 17:00 -> Sun 18:00 NY (49 h); FX: Fri 17:00 -> Sun 17:00 NY (48 h).
    assert kind(utc(2026, 9, 4, 21), utc(2026, 9, 6, 22)) is GapKind.WEEKEND
    assert kind(utc(2026, 9, 4, 21), utc(2026, 9, 6, 21)) is GapKind.WEEKEND


def test_weekend_extended_by_holiday():
    # Closed Fri 17:00 NY through Monday's session (e.g. a Monday holiday): 73 h.
    assert kind(utc(2026, 9, 4, 21), utc(2026, 9, 7, 22)) is GapKind.WEEKEND_HOLIDAY


def test_us_holiday_early_close_is_shortened_day():
    # 2026-09-07 Labor Day: last minute 14:28 NY, reopens 18:00 NY (real cache data).
    assert kind(utc(2026, 9, 7, 18, 29), utc(2026, 9, 7, 22)) is GapKind.SHORTENED_DAY


def test_full_closed_day_midweek():
    # Christmas on a Friday is a weekend case; on a Thursday (2025-12-25): closed from
    # Wed 17:00 NY (22:00 UTC) to Thu 18:00 NY = 25 h, no Friday close inside.
    assert kind(utc(2025, 12, 24, 22), utc(2025, 12, 25, 23)) is GapKind.CLOSED_DAY


def test_gap_touching_an_uncached_day_is_not_downloaded():
    gap = (utc(2026, 9, 2, 21), utc(2026, 9, 4, 0))
    assert kind(*gap, missing={date(2026, 9, 3)}) is GapKind.NOT_DOWNLOADED
    # A gap ending exactly at midnight does not touch the next day.
    assert kind(utc(2026, 9, 2, 21), utc(2026, 9, 3, 0), {date(2026, 9, 3)}) is not (
        GapKind.NOT_DOWNLOADED
    )


# --- integrity and outliers -----------------------------------------------------------


def findings(raw: pd.DataFrame, day: date = date(2026, 9, 2)) -> dict[str, int]:
    file_day = pd.Series(day, index=raw.index)
    return {f.name: f.count for f in check.integrity_findings(raw, file_day, CFG)}


def test_clean_day_has_no_integrity_findings():
    raw = m1(
        ("13:00", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),
        ("13:01", 100.5, 100.9, 100.1, 100.2, 1.0, 0.2),
    )
    assert set(findings(raw).values()) == {0}


def test_planted_problems_are_each_found_once():
    raw = m1(
        ("13:00", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),
        ("13:00", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),  # duplicate (both rows count)
        ("13:02", 100.0, 99.0, 101.0, 100.0, 1.0, 0.2),  # high < low (+ close outside)
        ("13:03", 100.0, 101.0, 99.0, 100.5, 1.0, -0.3),  # ask < bid
        ("13:04", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2),  # ask missing
        ("13:05", 100.0, 101.0, 99.0, 102.0, 1.0, 0.2),  # close above high
    )
    for f in check._FIELDS:
        raw.loc[4, f"ask_{f}"] = np.nan
    raw.loc[5, "ts"] += pd.Timedelta(seconds=30)  # not on a whole minute
    got = findings(raw)
    assert got["duplicate timestamps"] == 2
    assert got["bid: high < low"] == 1
    assert got["bid: open/close outside high-low"] == 2
    assert got["ask < bid (negative spread)"] == 1
    assert got["bid without ask (in a day file that has asks)"] == 1
    assert got["ask without bid"] == 0
    assert got["not on a whole minute"] == 1
    assert got["bid: price <= 0"] == 0


def test_row_in_wrong_day_file():
    raw = m1(("13:00", 100.0, 101.0, 99.0, 100.5, 1.0, 0.2), day="2026-09-03")
    assert findings(raw, day=date(2026, 9, 2))["row in the wrong day file"] == 1


def test_flat_filler_with_tiny_negative_spread_is_ignored():
    # Break filler is not traded, so its spread is irrelevant.
    raw = m1(("21:00", 100.0, 100.0, 100.0, 100.0, 0.0, -0.1))
    assert findings(raw)["ask < bid (negative spread)"] == 0


def test_outliers_spread_and_jump():
    rows = [(f"13:{i:02d}", 100.0, 100.5, 99.5, 100.0, 1.0, 0.2) for i in range(10)]
    rows[3] = ("13:03", 100.0, 100.5, 99.5, 100.0, 1.0, 5.0)  # spread 25 x median
    rows[6] = ("13:06", 130.0, 130.5, 129.5, 130.0, 1.0, 0.2)  # +30 jump (median range 1)
    rows[7] = ("13:07", 130.0, 130.5, 129.5, 130.0, 1.0, 0.2)
    traded = m1(*rows)
    spread, jump = check.outlier_findings(traded, CFG)
    assert spread.count == 1 and spread.examples[0].startswith("2026-09-02 13:03")
    assert jump.count == 2  # up at 13:06, back down at 13:08
    assert jump.examples[0].startswith("2026-09-02 13:06")


def test_jump_across_a_gap_is_not_an_outlier():
    traded = m1(
        ("13:00", 100.0, 100.5, 99.5, 100.0, 1.0, 0.2),
        ("13:01", 100.0, 100.5, 99.5, 100.0, 1.0, 0.2),
        ("13:30", 150.0, 150.5, 149.5, 150.0, 1.0, 0.2),  # after a gap: not consecutive
    )
    assert check.outlier_findings(traded, CFG)[1].count == 0


# --- whole report from a cache --------------------------------------------------------


def write_day(cache_dir, day: date, frame: pd.DataFrame, symbol: str = "XAUUSD") -> None:
    path = cache_path(cache_dir, symbol, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


def full_day(day: str, break_utc: tuple[int, int] | None = (21, 22)) -> pd.DataFrame:
    """1440 minutes like a real file; flat zero-volume filler in the break hour(s)."""
    rows = []
    for i in range(1440):
        h, mi = divmod(i, 60)
        flat = break_utc is not None and break_utc[0] <= h < break_utc[1]
        rows.append(
            (f"{h:02d}:{mi:02d}", 100.0, 100.0, 100.0, 100.0, 0.0, 0.2)
            if flat
            else (f"{h:02d}:{mi:02d}", 100.0, 100.5, 99.5, 100.2, 1.0, 0.2)
        )
    return m1(*rows, day=day)


@pytest.fixture
def cache(tmp_path):
    """Tue 09-01 and Wed 09-02 full gold days, Thu 09-03 never downloaded,
    Fri 09-04 closes for the weekend at 21:00 UTC, Sat 09-05 cached empty."""
    for d in ("2026-09-01", "2026-09-02"):
        write_day(tmp_path, date.fromisoformat(d), full_day(d))
    write_day(tmp_path, date(2026, 9, 4), full_day("2026-09-04", break_utc=(21, 24)))
    write_day(tmp_path, date(2026, 9, 5), _empty_cache_frame())
    return tmp_path


def test_report_on_cache(cache):
    r = check.check_symbol(cache, "XAUUSD")
    assert r.cached_days == [date(2026, 9, d) for d in (1, 2, 4, 5)]
    assert r.empty_days == [date(2026, 9, 5)]
    assert r.missing_days == [date(2026, 9, 3)]
    assert r.first_traded == utc(2026, 9, 1, 0)
    assert r.last_traded == utc(2026, 9, 4, 20, 59)
    assert r.traded_minutes == 2 * (1440 - 60) + (1440 - 180)
    assert [(g.start, g.end, g.kind) for g in r.gaps] == [
        (utc(2026, 9, 1, 21), utc(2026, 9, 1, 22), GapKind.DAILY_BREAK),
        (utc(2026, 9, 2, 21), utc(2026, 9, 2, 22), GapKind.DAILY_BREAK),
        (utc(2026, 9, 3, 0), utc(2026, 9, 4, 0), GapKind.NOT_DOWNLOADED),
    ]  # nothing after Fri 20:59: the weekend gap only shows once Sunday is cached
    assert all(f.count == 0 for f in r.integrity)
    assert list(r.price_range.loc[2026]) == [99.5, 100.5]
    # Default spot check: latest cached Tue-Thu with trading = Wed 09-02.
    assert list(r.spot["UTC"]) == ["2026-09-02 01:00", "2026-09-02 08:00", "2026-09-02 13:30"]
    assert list(r.spot["MT5 server"]) == [
        "2026-09-02 04:00",
        "2026-09-02 11:00",
        "2026-09-02 16:30",
    ]  # UTC+3 in summer
    assert r.spot.iloc[0][["open", "high", "low", "close"]].tolist() == [100.0, 100.5, 99.5, 100.2]
    assert r.median_m5_range == 1.0  # every traded minute spans 99.5..100.5


def test_report_start_end_limit_days(cache):
    r = check.check_symbol(cache, "XAUUSD", start=date(2026, 9, 2), end=date(2026, 9, 3))
    assert r.cached_days == [date(2026, 9, 2)]
    assert r.missing_days == []


def test_short_file_is_an_integrity_finding(tmp_path):
    write_day(tmp_path, date(2026, 9, 2), full_day("2026-09-02").iloc[:-1])
    r = check.check_symbol(tmp_path, "XAUUSD")
    assert {f.name: f.count for f in r.integrity}["non-empty file without 1440 rows"] == 1


def test_cli_prints_report_and_flags_problems(cache, capsys):
    code = check.main(["XAUUSD", "GBPUSD", "--cache-dir", str(cache), "--spot", "2026-09-04T13:30"])
    out = capsys.readouterr().out
    assert code == 1  # 09-03 not downloaded
    assert "NOT DOWNLOADED   1  (2026-09-03)" in out
    assert "daily break" in out and "2026-09-04 13:30" in out
    assert "===== GBPUSD =====" in out and "No cached days" in out
    # swing doji threshold section: 1.53% of the median 5m range (1.0) vs gold's 0.065
    assert "median 5m range  1.000" in out
    assert "gold rule gives  0.01528" in out and "configured       0.06500" in out


def test_cli_reads_each_symbol_from_its_source(tmp_path, monkeypatch, capsys):
    gold, fx = tmp_path / "dukascopy", tmp_path / "histdata"
    write_day(gold, date(2026, 9, 2), full_day("2026-09-02"))
    write_day(fx, date(2026, 9, 3), full_day("2026-09-03"), symbol="GBPUSD")
    sources = SymbolSources({"XAUUSD": gold, "GBPUSD": fx})
    monkeypatch.setattr(check, "DEFAULT_SOURCES", sources)
    assert check.main(["XAUUSD", "GBPUSD"]) == 0
    out = capsys.readouterr().out
    assert "cached days      1  (2026-09-02 .. 2026-09-02)" in out
    assert "cached days      1  (2026-09-03 .. 2026-09-03)" in out


def test_cli_clean_cache_exits_zero(tmp_path, capsys):
    write_day(tmp_path, date(2026, 9, 2), full_day("2026-09-02"))
    assert check.main(["XAUUSD", "--cache-dir", str(tmp_path)]) == 0


# --- spot candles over a long history (full history, 2026-10-09) -----------------------


def test_dst_seasons_including_the_weeks_where_only_the_us_is_on_summer_time():
    assert check.dst_season(datetime(2024, 7, 16, 14, tzinfo=UTC)) == check.SUMMER
    assert check.dst_season(datetime(2025, 1, 15, 14, tzinfo=UTC)) == check.WINTER
    # 2026: US summer time from 03-08, EU from 03-29; US until 11-01, EU until 10-25
    assert check.dst_season(datetime(2026, 3, 18, 14, tzinfo=UTC)) == check.US_ONLY
    assert check.dst_season(datetime(2026, 10, 28, 14, tzinfo=UTC)) == check.US_ONLY
    assert check.dst_season(datetime(2026, 3, 31, 14, tzinfo=UTC)) == check.SUMMER


def test_history_spot_times_spread_over_years_and_seasons():
    days = {date(2020, 1, 1) + pd.Timedelta(days=i).to_pytimedelta() for i in range(2400)}
    times = check.history_spot_times(days, check.DEFAULT_CONFIG)
    assert len(times) == 6
    assert {t.year for t in times} >= {2020, 2026}
    assert {check.dst_season(t) for t in times} == {check.SUMMER, check.WINTER, check.US_ONLY}
    assert all(t.weekday() in (1, 2, 3) and t.hour == 14 for t in times)


def test_doji_share_and_median_range_per_year_and_last_year_per_quarter():
    m5 = pd.DataFrame(
        {
            "ts": pd.to_datetime(
                ["2025-03-03 10:00", "2025-03-03 10:05", "2026-01-05 10:00", "2026-07-06 10:00"],
                utc=True,
            ),
            "open": [100.0, 100.0, 100.0, 100.0],
            "close": [100.05, 101.0, 100.0, 102.0],  # bodies 0.05, 1, 0, 2
            "high": [101.0, 102.0, 104.0, 106.0],
            "low": [100.0, 99.0, 100.0, 100.0],  # ranges 1, 3, 4, 6
        }
    )
    out = check.doji_by_period(m5, max_body=0.065)
    assert list(out.index) == ["2025", "2026 Q1", "2026 Q3"]
    assert out.loc["2025", "candles"] == 2 and out.loc["2025", "median_range"] == 2.0
    assert out.loc["2025", "doji_share"] == 0.5 and out.loc["2026 Q1", "doji_share"] == 1.0
    assert out.loc["2026 Q3", "gold_rule"] == pytest.approx(6 * 0.065 / 4.255)
