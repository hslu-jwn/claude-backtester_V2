"""Open / gap / trend-day study: cash days, gap fill, first 30 minutes, trend days, timing of
the extremes, last hour. Spec: ROADMAP.md › 11.2 (knowledge base I-09, I-39)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from backtester.analytics.open_gap import (
    FEATURE_FIELDS,
    Bar,
    OpenGapConfig,
    arcsine_share,
    cash_days,
    day_records,
    known_at,
    mean_t,
    wilson,
)

NY = ZoneInfo("America/New_York")
CFG = OpenGapConfig(atr_period=2)  # two warm-up days instead of 14


def at(d: date, hh: int, mm: int) -> datetime:
    return datetime.combine(d, time(hh, mm), NY).astimezone(UTC)


def session(d, base=100.0, minutes=range(390), over=None, skip=()):
    """M1 bars of a day from 09:30 New York; minute m is 09:30 + m minutes. Default bar:
    open = close = base, high base + 0.5, low base - 0.5. `over`: {minute: (o, h, l, c)}."""
    over = over or {}
    out = []
    for m in minutes:
        if m in skip:
            continue
        o, h, lo, c = over.get(m, (base, base + 0.5, base - 0.5, base))
        out.append(Bar(at(d, 9, 30) + timedelta(minutes=m), o, h, lo, c))
    return out


MON = date(2026, 9, 14)  # a Monday, US summer time


def days_of(*sessions):
    bars = [b for s in sessions for b in s]
    return cash_days(bars, CFG)


def warm(n=2, start=MON, base=100.0):
    """n regular days at `base`, each range 1.0 and no gap: ATR = 1.0 afterwards."""
    return [session(start + timedelta(days=i), base) for i in range(n)]


def rec(days, d):
    records, _ = day_records(days, CFG)
    return next(r for r in records if r["date"] == d)


def d_(n):
    """The date n days after the first warm-up day (MON)."""
    return MON + timedelta(days=n)


# --- cash days -------------------------------------------------------------------------------


def test_full_day_is_regular_with_390_cash_bars():
    (day,) = days_of(session(MON))
    assert day.cls == "regular"
    assert len(day.bars) == 390
    assert day.date == MON


def test_bars_outside_09_30_to_16_00_new_york_are_ignored():
    extra = session(MON, minutes=range(390, 405))  # 16:00 .. 16:14
    evening = [Bar(at(MON, 18, 0) + timedelta(minutes=i), 1, 1, 1, 1) for i in range(5)]
    early = [Bar(at(MON, 9, 0) + timedelta(minutes=i), 1, 1, 1, 1) for i in range(5)]
    (day,) = days_of(early, session(MON), extra, evening)
    assert len(day.bars) == 390
    assert day.cls == "regular"


def test_a_few_missing_bars_are_still_regular_more_are_a_data_hole():
    (five,) = days_of(session(MON, skip=range(100, 105)))
    (six,) = days_of(session(MON, skip=range(100, 106)))
    assert five.cls == "regular"
    assert six.cls == "data_hole"


def test_missing_first_bar():
    (day,) = days_of(session(MON, minutes=range(1, 390)))
    assert day.cls == "first_bar_missing"


@pytest.mark.parametrize("last_minute", [209, 224])  # 12:59 holiday CFD, 13:14 half day
def test_a_session_that_stops_early_is_an_early_close(last_minute):
    (day,) = days_of(session(MON, minutes=range(last_minute + 1)))
    assert day.cls == "early_close"


def test_an_early_session_with_a_hole_is_a_data_hole():
    (day,) = days_of(session(MON, minutes=range(210), skip=range(50, 70)))
    assert day.cls == "data_hole"


@pytest.mark.parametrize("day", [date(2026, 1, 14), date(2026, 3, 6), date(2026, 3, 9)])
def test_winter_summer_and_the_dst_week_all_map_09_30_new_york(day):
    (cd,) = days_of(session(day))
    assert cd.cls == "regular"
    assert len(cd.bars) == 390
    assert cd.bars[0].ts == at(day, 9, 30)
    assert cd.bars[0].ts.hour in (13, 14)


def test_days_come_out_in_date_order():
    days = days_of(session(d_(2)), session(MON), session(d_(1)))
    assert [d.date for d in days] == [MON, d_(1), d_(2)]


# --- previous close and the days that are left out ----------------------------------------------


def test_previous_close_skips_early_close_and_empty_weekdays():
    s1 = session(MON, base=100.0)
    s_early = session(d_(1), base=101.0, minutes=range(210))
    # Wednesday has no bars at all; Thursday is the day under test
    s3 = session(d_(3), base=105.0)
    records, excl = day_records(days_of(s1, s_early, s3), CFG)
    assert records == []  # ATR warm-up: only two regular days
    reasons = {(e["date"], e["reason"]) for e in excl}
    assert (d_(1), "early_close") in reasons
    assert (MON, "atr_warmup") in reasons and (d_(3), "atr_warmup") in reasons


def test_record_has_the_last_regular_close_as_previous_close_and_the_skipped_days():
    sessions = [*warm(2), session(d_(2), 100.0, minutes=range(210)), session(d_(4), 102.0)]
    r = rec(days_of(*sessions), d_(4))
    assert r["prev_close"] == pytest.approx(100.0)
    assert r["skipped_days"] == 2  # Wednesday early close, Thursday no bars


def test_a_data_hole_between_makes_the_next_day_unusable():
    sessions = [*warm(2), session(d_(2), skip=range(50, 80)), session(d_(3), 100.0)]
    records, excl = day_records(days_of(*sessions), CFG)
    assert records == []
    assert {"data_hole", "prev_not_regular"} <= {e["reason"] for e in excl}


def test_first_day_has_no_previous_close_and_the_atr_needs_its_warmup():
    records, excl = day_records(days_of(*warm(3)), CFG)
    assert [r["date"] for r in records] == [d_(2)]  # day 3: ATR known after 2 days
    assert {e["reason"] for e in excl} == {"atr_warmup"}


# --- ATR ----------------------------------------------------------------------------------------


def test_atr_is_wilder_over_regular_days_and_known_before_the_day():
    # day 1 range 1 (no previous close), day 2 range 2 (high 101.5, low 99.5, prev close 100)
    d2 = session(d_(1), over={10: (100.0, 101.5, 99.5, 100.0)})
    d3 = session(d_(2))
    d4 = session(d_(3))
    days = days_of(session(MON), d2, d3, d4)
    r3 = rec(days, d_(2))
    assert r3["atr"] == pytest.approx(1.5)  # (1 + 2) / 2
    # Wilder with n = 2: after day 3 (TR 1): (1.5 * 1 + 1) / 2 = 1.25
    assert rec(days, d_(3))["atr"] == pytest.approx(1.25)


def test_the_atr_of_a_day_does_not_depend_on_its_own_range():
    base = [session(MON), session(d_(1))]
    quiet = rec(days_of(*base, session(d_(2))), d_(2))["atr"]
    wild = rec(days_of(*base, session(d_(2), over={5: (100, 130, 70, 100)})), d_(2))["atr"]
    assert quiet == wild


# --- gaps ----------------------------------------------------------------------------------------


def gap_up_day(d, fill_minute=None, base=101.0, extra=None):
    over = dict(extra or {})
    if fill_minute is not None:
        over[fill_minute] = (base, base + 0.5, 99.8, base - 0.1)  # trades through 100
    return session(d, base=base, over=over)


def test_up_gap_is_sized_in_atr_and_filled_at_the_first_bar_through_the_previous_close():
    days = days_of(*warm(2), gap_up_day(d_(2), fill_minute=45))
    r = rec(days, d_(2))
    assert r["gap"] == pytest.approx(1.0)
    assert r["gap_atr"] == pytest.approx(1.0)
    assert r["gap_dir"] == "up"
    assert r["gap_bucket"] == "1+"
    assert r["filled_same_day"] is True
    assert r["fill_minute"] == 45


def test_gap_not_filled_when_price_stays_on_the_far_side():
    r = rec(days_of(*warm(2), gap_up_day(d_(2))), d_(2))
    assert r["filled_same_day"] is False
    assert r["fill_minute"] is None


def test_down_gap_is_the_mirror():
    over = {20: (99.0, 100.1, 98.5, 99.0)}  # high 100.1 >= previous close 100
    r = rec(days_of(*warm(2), session(d_(2), base=99.0, over=over)), d_(2))
    assert r["gap_dir"] == "down"
    assert r["gap"] == pytest.approx(-1.0)
    assert r["filled_same_day"] is True
    assert r["fill_minute"] == 20


def test_filled_by_day_three_counts_the_two_following_regular_days_only():
    # day 3 not filled, day 4 filled -> True; filled only on day 6 -> False
    quiet = gap_up_day(d_(2))
    # keep the later days away from the first gap's previous close: base stays 101
    filled_d4 = gap_up_day(d_(3), fill_minute=10)
    r = rec(days_of(*warm(2), quiet, filled_d4, gap_up_day(d_(4)), gap_up_day(d_(7))), d_(2))
    assert r["filled_same_day"] is False
    assert r["filled_by_day3"] is True
    late = [gap_up_day(d_(3)), gap_up_day(d_(4)), gap_up_day(d_(7), fill_minute=10)]
    r = rec(days_of(*warm(2), gap_up_day(d_(2)), *late), d_(2))
    assert r["filled_by_day3"] is False  # filled on the 4th day: too late


def test_a_data_hole_inside_the_window_makes_day_three_unknown_unless_already_filled():
    hole = session(d_(3), base=101.0, skip=range(50, 80))
    r = rec(days_of(*warm(2), gap_up_day(d_(2)), hole, gap_up_day(d_(4))), d_(2))
    assert r["filled_by_day3"] is None
    filled_first = gap_up_day(d_(2), fill_minute=10)
    r = rec(days_of(*warm(2), filled_first, hole, gap_up_day(d_(4))), d_(2))
    assert r["filled_by_day3"] is True


def test_window_stops_at_the_end_of_the_data():
    r = rec(days_of(*warm(2), gap_up_day(d_(2))), d_(2))
    assert r["filled_by_day3"] is None  # no following days to look at


def test_early_close_days_are_not_part_of_the_window():
    early = session(d_(3), base=101.0, minutes=range(210), over={5: (101, 101.5, 99.5, 100.5)})
    r = rec(
        days_of(*warm(2), gap_up_day(d_(2)), early, gap_up_day(d_(4)), gap_up_day(d_(7))), d_(2)
    )
    assert r["filled_by_day3"] is False  # the early day was skipped, so it did not fill


def test_which_level_is_touched_first_the_previous_close_or_its_mirror():
    def first(over):
        return rec(days_of(*warm(2), session(d_(2), base=101.0, over=over)), d_(2))["first_touch"]

    assert first({45: (101.0, 101.5, 99.8, 100.9)}) == "fill"  # low reaches 100
    assert first({10: (101.0, 102.1, 100.8, 102.0), 50: (101.0, 101.5, 99.8, 101.0)}) == "extend"
    assert first({}) == "neither"
    assert first({5: (101.0, 102.1, 99.8, 101.0)}) == "same_bar"  # both inside one bar


def test_first_touch_of_a_down_gap_and_a_flat_gap():
    over = {20: (99.0, 100.1, 98.5, 99.0)}  # high reaches 100 = the previous close
    r = rec(days_of(*warm(2), session(d_(2), base=99.0, over=over)), d_(2))
    assert r["first_touch"] == "fill"
    assert rec(days_of(*warm(3)), d_(2))["first_touch"] is None


def test_a_flat_gap_has_no_fill_statistics():
    r = rec(days_of(*warm(3)), d_(2))
    assert r["gap_dir"] == "flat"
    assert r["flat"] is True
    assert r["filled_same_day"] is None


def test_extend_baseline_is_the_same_size_move_in_the_gap_direction():
    over = {60: (101.0, 102.1, 100.8, 102.0)}  # open + gap = 102
    r = rec(days_of(*warm(2), session(d_(2), base=101.0, over=over)), d_(2))
    assert r["extend_same_day"] is True
    r = rec(days_of(*warm(2), session(d_(2), base=101.0)), d_(2))
    assert r["extend_same_day"] is False


def test_gap_buckets_by_atr_size():
    def bucket(gap):
        return rec(days_of(*warm(2), session(d_(2), base=100.0 + gap)), d_(2))["gap_bucket"]

    assert bucket(0.05) == "<0.1"
    assert bucket(0.2) == "0.1-0.25"
    assert bucket(0.4) == "0.25-0.5"
    assert bucket(0.8) == "0.5-1"
    assert bucket(1.5) == "1+"


# --- first 30 minutes ----------------------------------------------------------------------------------


def test_first30_and_rest_in_atr_units_and_continuation():
    over = {389: (101, 102.5, 100.5, 102.0)}  # last bar closes at 102
    r = rec(days_of(*warm(2), session(d_(2), base=101.0, over=over)), d_(2))
    assert r["first30_atr"] == pytest.approx(1.0)  # 10:00 close 101 - previous close 100
    assert r["rest_atr"] == pytest.approx(1.0)
    assert r["continued"] is True
    over = {389: (101, 101.5, 100.0, 100.5)}
    r = rec(days_of(*warm(2), session(d_(2), base=101.0, over=over)), d_(2))
    assert r["continued"] is False


def test_zero_rest_move_is_neither_continuation_nor_reversal():
    r = rec(days_of(*warm(2), session(d_(2), base=101.0)), d_(2))
    assert r["rest_atr"] == pytest.approx(0.0)
    assert r["continued"] is None


def test_first30_never_reads_the_10_00_bar():
    wild = {30: (101.0, 150.0, 90.0, 140.0)}  # the 10:00 bar
    a = rec(days_of(*warm(2), session(d_(2), base=101.0)), d_(2))["first30_atr"]
    b = rec(days_of(*warm(2), session(d_(2), base=101.0, over=wild)), d_(2))["first30_atr"]
    assert a == b


# --- trend day ---------------------------------------------------------------------------------------------


def trend_up_day(d, last_close=109.5, base=105.0):
    over = {0: (100.0, 100.5, 100.0, 100.2), 389: (base, 110.0, base - 0.5, last_close)}
    return session(d, base=base, over=over)


def test_up_trend_day_open_at_the_low_and_close_at_the_high():
    r = rec(days_of(*warm(2), trend_up_day(d_(2))), d_(2))
    assert r["range"] == pytest.approx(10.0)
    assert r["trend"] == "up"
    assert r["trend_day"] is True


def test_close_too_far_from_the_high_is_not_a_trend_day():
    r = rec(days_of(*warm(2), trend_up_day(d_(2), last_close=108.0)), d_(2))
    assert r["trend"] == "none"
    assert r["trend_day"] is False


def test_down_trend_day_is_the_mirror():
    over = {0: (110.0, 110.0, 109.5, 109.8), 389: (105.0, 105.5, 100.0, 100.5)}
    r = rec(days_of(*warm(2, base=110.0), session(d_(2), base=105.0, over=over)), d_(2))
    assert r["trend"] == "down"
    assert r["trend_day"] is True


def test_zero_range_day_has_no_trend_label():
    flat = session(d_(2), over={m: (100, 100, 100, 100) for m in range(390)})
    r = rec(days_of(*warm(2), flat), d_(2))
    assert r["trend_day"] is None


# --- features at 11:00 -----------------------------------------------------------------------------------------


def test_filled_by_11_and_new_extreme_and_position_in_the_range_so_far():
    over = {
        40: (101.0, 101.5, 100.8, 101.4),  # 10:10 breaks the first-30-minute high 101.5? equal
        50: (101.0, 103.0, 100.8, 102.9),  # 10:20 new high
        89: (102.9, 103.0, 102.5, 103.0),  # 10:59 close 103.0
    }
    r = rec(days_of(*warm(2), session(d_(2), base=101.0, over=over)), d_(2))
    assert r["new_extreme_10_11"] is True
    assert r["filled_by_11"] is False
    assert r["pos_11"] == pytest.approx((103.0 - 100.5) / (103.0 - 100.5))  # close = high


def test_features_at_11_ignore_everything_from_11_00_on():
    a = days_of(*warm(2), session(d_(2), base=101.0))
    wild = {m: (101, 140, 60, 70) for m in range(90, 390)}
    b = days_of(*warm(2), session(d_(2), base=101.0, over=wild))
    ra, rb = rec(a, d_(2)), rec(b, d_(2))
    for key in ("filled_by_11", "new_extreme_10_11", "pos_11", "first30_atr", "gap_atr"):
        assert ra[key] == rb[key], key


def test_known_at_returns_only_bars_closed_by_the_time():
    (day,) = days_of(session(MON))
    cut = known_at(day, time(11, 0), CFG)
    assert len(cut) == 90
    assert cut[-1].ts == at(MON, 10, 59)


def test_earlier_days_do_not_change_when_later_days_are_appended():
    sessions = [*warm(2), gap_up_day(d_(2), fill_minute=45), gap_up_day(d_(3))]
    short = day_records(days_of(*sessions[:3]), CFG)[0]
    full = day_records(days_of(*sessions, gap_up_day(d_(4)), trend_up_day(d_(7))), CFG)[0]
    first = next(r for r in full if r["date"] == d_(2))
    ref = next(r for r in short if r["date"] == d_(2))
    for key in FEATURE_FIELDS:
        assert first[key] == ref[key], key


# --- when the extremes print -----------------------------------------------------------------------------------------


def test_high_in_the_10_59_bar_is_inside_the_first_90_minutes_11_00_is_not():
    inside = {89: (100, 120.0, 99.8, 100)}
    outside = {90: (100, 120.0, 99.8, 100)}
    ri = rec(days_of(*warm(2), session(d_(2), over=inside)), d_(2))
    ro = rec(days_of(*warm(2), session(d_(2), over=outside)), d_(2))
    assert ri["high_minute"] == 89 and ri["high_in_first90"] is True
    assert ro["high_minute"] == 90 and ro["high_in_first90"] is False
    assert ri["high_in_first_hour"] is False


def test_equal_highs_go_to_the_earliest_bar():
    over = {200: (100, 120.0, 99.8, 100), 89: (100, 120.0, 99.8, 100)}
    r = rec(days_of(*warm(2), session(d_(2), over=over)), d_(2))
    assert r["high_minute"] == 89


def test_low_timing_and_last_hour_flags():
    over = {350: (100, 100.2, 80.0, 99)}  # 15:20
    r = rec(days_of(*warm(2), session(d_(2), over=over)), d_(2))
    assert r["low_minute"] == 350
    assert r["low_in_last_hour"] is True
    assert r["low_in_first90"] is False


# --- last hour ----------------------------------------------------------------------------------------------------------


def test_new_high_in_the_last_hour_is_an_event_with_close_position_and_move():
    over = {350: (100, 103.0, 99.9, 102.0), 389: (102, 102.5, 101.5, 102.0)}
    r = rec(days_of(*warm(2), session(d_(2), over=over)), d_(2))
    assert r["last_hour_event"] == "high"
    # level = highest high before 15:00 = 100.5; close 102.0; ATR 1.0
    assert r["last_hour_move_atr"] == pytest.approx(1.5)
    assert r["close_pos"] == pytest.approx((102.0 - 99.5) / (103.0 - 99.5))


def test_a_high_in_the_14_59_bar_is_not_a_last_hour_event():
    over = {329: (100, 103.0, 99.9, 100.0)}
    r = rec(days_of(*warm(2), session(d_(2), over=over)), d_(2))
    assert r["last_hour_event"] == "none"
    assert r["last_hour_move_atr"] is None


def test_new_low_event_is_measured_downwards():
    over = {345: (100, 100.2, 98.0, 98.5), 389: (98.5, 98.9, 98.2, 98.5)}
    r = rec(days_of(*warm(2), session(d_(2), over=over)), d_(2))
    assert r["last_hour_event"] == "low"
    assert r["last_hour_move_atr"] == pytest.approx((99.5 - 98.5) / 1.0)


def test_high_and_low_in_the_last_hour_is_both():
    over = {340: (100, 103.0, 99.9, 102.0), 345: (100, 100.2, 97.0, 98.0)}
    r = rec(days_of(*warm(2), session(d_(2), over=over)), d_(2))
    assert r["last_hour_event"] == "both"
    assert r["last_hour_move_atr"] is None


# --- small statistics -----------------------------------------------------------------------------------------------------


def test_wilson_interval_known_values():
    lo, hi = wilson(50, 100)
    assert lo == pytest.approx(0.4038, abs=1e-3)
    assert hi == pytest.approx(0.5962, abs=1e-3)
    assert wilson(0, 0) == (None, None)
    lo, hi = wilson(10, 10)
    assert hi == pytest.approx(1.0)
    assert lo < 1.0


def test_arcsine_share():
    assert arcsine_share(0.5) == pytest.approx(0.5)
    assert arcsine_share(0.0) == 0.0
    assert arcsine_share(1.0) == pytest.approx(1.0)
    assert arcsine_share(90 / 390) == pytest.approx(0.319, abs=1e-3)


def test_mean_t():
    m, t = mean_t([1.0, 2.0, 3.0])
    assert m == pytest.approx(2.0)
    assert t == pytest.approx(2.0 / (1.0 / 3**0.5))
    assert mean_t([5.0]) == (5.0, None)
    assert mean_t([]) == (None, None)
    assert mean_t([2.0, 2.0])[1] is None  # no variance


def test_config_validation():
    with pytest.raises(ValueError):
        OpenGapConfig(atr_period=0)
    with pytest.raises(ValueError):
        OpenGapConfig(trend_extreme_frac=0.6)
    with pytest.raises(ValueError):
        OpenGapConfig(gap_buckets=(0.5, 0.2))
    with pytest.raises(ValueError):
        OpenGapConfig(fill_horizon_days=0)
