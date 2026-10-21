# ruff: noqa: C408
"""No-wick retest study: signals, limit fills on M1, stop / target paths, time exit, costs and
scoring. Research tool, changes no setting. Written test first (the user's rule)."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import pytest
from conftest import build_candles

from backtester.core.models import Candle, Direction, Timeframe
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.tools import no_wick_retest_study as study
from backtester.tools.no_wick_retest_study import (
    Signal,
    StudyConfig,
    clean_structure,
    cost_price,
    evaluate_signal,
    exit_index,
    find_fill,
    four_hour_ok,
    in_pdf_window,
    m1_from_candles,
    no_wick_direction,
    scan_signals,
    score_trades,
    stop_prices,
    study_frames,
    target_outcomes,
    walk,
)

CFG = StudyConfig()
LONG, SHORT = Direction.BULLISH, Direction.BEARISH
START = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)  # a Monday
TEST_COSTS = CostConfig(
    symbols={"TEST": SymbolCosts(spread=0.2, commission_per_lot=7.0, contract_size=100.0)}
)


def candle(o, h, low, c, ts=START):
    return Candle(ts=ts, open=o, high=h, low=low, close=c)


def mirror(ohlc, k=30.0):
    """Price p -> k - p: green becomes red, highs become lows."""
    return [(k - o, k - lo, k - h, k - c) for o, h, lo, c in ohlc]


def m1(rows, start=START):

    return m1_from_candles(build_candles(rows, Timeframe.M1, start), CFG)


# --- 1. no-wick detection -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ohlc", "share", "expected"),
    [
        ((1.00, 1.05, 1.00, 1.04), 0.0, LONG),  # green, no lower wick
        ((1.00, 1.05, 0.99, 1.04), 0.0, None),  # green with a lower wick
        ((1.04, 1.05, 1.00, 1.00), 0.0, None),  # red with a lower wick only = not a short
        ((1.04, 1.04, 1.00, 1.01), 0.0, SHORT),  # red, no upper wick
        ((1.04, 1.05, 1.00, 1.01), 0.0, None),  # red with an upper wick
        ((1.00, 1.05, 1.00, 1.00), 0.0, None),  # open = close: no colour
        ((1.00, 1.00, 1.00, 1.00), 0.05, None),  # no range
        ((100.0, 120.0, 99.0, 119.0), 0.0, None),  # wick 1 / 21 = 0.0476 > 0
        ((100.0, 120.0, 99.0, 119.0), 0.05, LONG),  # ... <= 0.05
        ((100.0, 120.0, 98.0, 119.0), 0.05, None),  # 2 / 22 = 0.09 > 0.05
        ((119.0, 120.0, 99.0, 100.0), 0.05, SHORT),  # mirrored wick 1 / 21
        ((100.0, 125.0, 100.0, 105.0), 0.0, LONG),  # an upper wick does not matter for a long
    ],
)
def test_no_wick_direction(ohlc, share, expected):
    found = no_wick_direction(candle(*ohlc), share)
    assert (found[0] if found else None) is expected


def test_no_wick_direction_reports_the_share():
    direction, wick = no_wick_direction(candle(100.0, 120.0, 99.0, 119.0), 0.05)
    assert direction is LONG
    assert wick == pytest.approx(1 / 21)


# --- 2. limit fill on M1 --------------------------------------------------------------------------


def test_long_limit_fills_at_the_level_when_a_later_bar_trades_down_to_it():
    data = m1([(10.5, 10.8, 10.2, 10.6), (10.6, 10.7, 9.95, 10.1)])
    assert find_fill(data, START, Timeframe.M15, 10.0, LONG, CFG) == (1, 10.0)


def test_long_limit_touching_the_level_exactly_fills():
    data = m1([(10.5, 10.8, 10.2, 10.6), (10.6, 10.7, 10.0, 10.1)])
    assert find_fill(data, START, Timeframe.M15, 10.0, LONG, CFG) == (1, 10.0)


def test_long_gap_through_the_level_fills_at_the_open():
    data = m1([(9.0, 9.5, 8.9, 9.2)])
    assert find_fill(data, START, Timeframe.M15, 10.0, LONG, CFG) == (0, 9.0)


def test_short_mirrors_fill_and_gap():
    data = m1([(9.5, 9.8, 9.2, 9.6), (9.6, 10.2, 9.5, 10.1)])
    assert find_fill(data, START, Timeframe.M15, 10.0, SHORT, CFG) == (1, 10.0)
    data = m1([(11.0, 11.4, 10.8, 11.1)])
    assert find_fill(data, START, Timeframe.M15, 10.0, SHORT, CFG) == (0, 11.0)


def test_no_fill_when_price_never_returns():
    data = m1([(10.5, 10.8, 10.2, 10.6)] * 10)
    assert find_fill(data, START, Timeframe.M15, 10.0, LONG, CFG) is None


def test_bars_before_the_signal_close_do_not_fill():
    data = m1([(9.0, 9.5, 8.9, 9.2), (10.5, 10.8, 10.2, 10.6)])
    close = START + timedelta(minutes=1)  # the touching bar 0 is before the close
    assert find_fill(data, close, Timeframe.M15, 10.0, LONG, CFG) is None


def sig(**kw):
    base = dict(
        index=0, direction=LONG, close_time=START, level=10.0, wick_share=0.0, bos=False,
        bos_clean=False, bos_4h=False, pdf_skip=False,
    )  # fmt: skip
    return Signal(**{**base, **kw})


def test_gap_open_at_or_beyond_a_stop_drops_that_stop_variant_only():
    data = m1([(8.9, 9.0, 8.8, 8.95)] + [(8.95, 9.0, 8.9, 8.95)] * 5)
    cols, counts = {}, {}
    evaluate_signal(data, sig(atr=1.0), Timeframe.M15, CFG, TEST_COSTS, "TEST", cols, counts)
    stops = set(cols["stop"])
    assert "atr1" not in stops  # stop 9.0, the order fills at 8.9 below it
    assert "atr0.5" not in stops  # stop 9.5
    assert {"atr1.5", "atr2"} <= stops  # stops 8.5 and 8.0 are still below the fill
    assert counts["gap_dropped"] == 2


# --- 3. expiry: five candles -------------------------------------------------------------------------


@pytest.mark.parametrize(("touch", "fills"), [(74, True), (75, False)])
def test_order_expires_after_exactly_five_candles(touch, fills):
    rows = [(10.5, 10.6, 10.4, 10.5)] * 90
    rows[touch] = (10.5, 10.6, 9.9, 10.5)
    found = find_fill(m1(rows), START, Timeframe.M15, 10.0, LONG, CFG)
    assert (found is not None) is fills
    if fills:
        assert found[0] == touch


def test_expired_orders_are_counted():
    data = m1([(10.5, 10.6, 10.4, 10.5)] * 90)
    cols, counts = {}, {}
    evaluate_signal(data, sig(atr=1.0), Timeframe.M15, CFG, TEST_COSTS, "TEST", cols, counts)
    assert counts["expired"] == 1
    assert not cols.get("stop")


# --- 4. path on M1: stop first -------------------------------------------------------------------------


def test_stop_in_the_fill_bar_is_a_loss_and_its_target_side_is_not_counted():
    data = m1([(10.0, 11.0, 8.9, 9.5)])  # fill bar: high 11 would be 1R, low 8.9 hits stop 9
    stopped, mfe, _ = walk(data, 0, 0, 10.0, LONG, np.array([9.0]))
    assert stopped.tolist() == [True]
    assert mfe[0] == 0.0


def test_target_in_the_fill_bar_is_not_counted_but_later_bars_are():
    rows = [(10.0, 11.0, 9.6, 10.2), (10.2, 10.6, 10.0, 10.4)]
    data = m1(rows)
    stopped, mfe, exit_r = walk(data, 0, 1, 10.0, LONG, np.array([9.0]))
    assert stopped.tolist() == [False]
    assert mfe[0] == pytest.approx(0.6)  # bar 1's high 10.6 only: (10.6 - 10) / 1
    assert exit_r[0] == pytest.approx(0.4)  # close of the last bar


def test_stop_and_target_in_one_later_bar_is_a_loss():
    rows = [
        (10.0, 11.0, 8.9, 9.5),   # fill bar, stop 9 hit
        (9.5, 10.6, 9.4, 10.5),
        (10.5, 12.5, 7.9, 12.0),  # high far above, low below stop 8: stop first
    ]  # fmt: skip
    data = m1(rows)
    stopped, mfe, exit_r = walk(data, 0, 2, 10.0, LONG, np.array([9.0, 8.0, 5.0]))
    assert stopped.tolist() == [True, True, False]
    assert mfe[0] == 0.0  # stopped in the fill bar
    assert mfe[1] == pytest.approx(0.3)  # bar 1 only: 0.6 / 2
    assert mfe[2] == pytest.approx(0.5)  # bars 1-2: 2.5 / 5
    assert exit_r[2] == pytest.approx(0.4)  # (12 - 10) / 5


def test_short_walk_mirrors_the_long_walk():
    rows = [(10.0, 11.0, 8.9, 9.5), (9.5, 10.6, 9.4, 10.5), (10.5, 12.5, 7.9, 12.0)]
    long_res = walk(m1(rows), 0, 2, 10.0, LONG, np.array([9.0, 8.0, 5.0]))
    short_res = walk(m1(mirror(rows, 20.0)), 0, 2, 10.0, SHORT, np.array([11.0, 12.0, 15.0]))
    for a, b in zip(long_res, short_res, strict=True):
        assert np.allclose(a, b)


# --- 5. targets from the records -------------------------------------------------------------------------

MFE = np.array([0.6, 1.2, 0.2, 2.5])
STOPPED = np.array([False, False, True, False])
EXIT = np.array([0.1, 0.5, math.nan, -0.3])
SWING = np.array([math.nan, 1.0, 0.5, 3.0])


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        (1.0, [0.1, 1.0, -1.0, 1.0]),
        (0.5, [0.5, 0.5, -1.0, 0.5]),
        (3.0, [0.1, 0.5, -1.0, -0.3]),
        ("none", [0.1, 0.5, -1.0, -0.3]),
    ],
)
def test_target_outcomes(target, expected):
    gross, valid = target_outcomes(target, MFE, STOPPED, EXIT, SWING)
    assert valid.all()
    assert gross.tolist() == pytest.approx(expected)


def test_swing_target_uses_its_own_r_and_skips_rows_without_one():
    gross, valid = target_outcomes("swing", MFE, STOPPED, EXIT, SWING)
    assert valid.tolist() == [False, True, True, True]
    assert gross[valid].tolist() == pytest.approx([1.0, -1.0, -0.3])


def test_a_time_exit_never_pays_more_than_the_target():
    gross, _ = target_outcomes(
        0.5, np.array([0.0]), np.array([False]), np.array([0.9]), np.array([math.nan])
    )
    assert gross.tolist() == [0.5]


# --- 6. time exit 16:55 New York -------------------------------------------------------------------------


def contiguous(start, hours):
    return m1([(10.0, 10.1, 9.9, 10.0)] * (hours * 60), start)


@pytest.mark.parametrize(
    ("day", "exit_utc_hour"),
    [(datetime(2026, 1, 12, tzinfo=UTC), 21), (datetime(2026, 7, 13, tzinfo=UTC), 20)],
)
def test_exit_is_the_last_bar_before_1655_new_york(day, exit_utc_hour):
    start = day.replace(hour=12, tzinfo=UTC)
    data = contiguous(start, 12)
    fill = 6 * 60  # 18:00 UTC
    end, overnight = exit_index(data, fill, CFG)
    last_ts = datetime.fromtimestamp(data.ts[end] / 1e9, UTC)
    assert last_ts == day.replace(hour=exit_utc_hour, minute=54, tzinfo=UTC)
    assert overnight is False


def test_fill_after_1655_exits_the_next_day():
    start = datetime(2026, 1, 12, 12, tzinfo=UTC)
    data = contiguous(start, 36)
    fill = 10 * 60 + 5  # 22:05 UTC = 17:05 EST
    end, overnight = exit_index(data, fill, CFG)
    last_ts = datetime.fromtimestamp(data.ts[end] / 1e9, UTC)
    assert last_ts == datetime(2026, 1, 13, 21, 54, tzinfo=UTC)
    assert overnight is True


def test_exit_at_the_last_bar_before_a_data_gap_over_two_hours():
    first = datetime(2026, 1, 12, 12, tzinfo=UTC)
    part_a = contiguous(first, 2)  # 12:00-13:59

    part_b = build_candles(
        [(10.0, 10.1, 9.9, 10.0)] * 120, Timeframe.M1, first + timedelta(hours=5)
    )
    data = m1_from_candles(
        build_candles([(10.0, 10.1, 9.9, 10.0)] * 120, Timeframe.M1, first) + part_b, CFG
    )
    assert len(part_a.ts) == 120
    end, _ = exit_index(data, 30, CFG)
    assert end == 119  # 13:59, the bar before the 3 h hole
    end, _ = exit_index(data, 130, CFG)
    assert end == 239  # the second block runs to its own end (no hole, before 16:55)


def test_a_gap_of_exactly_two_hours_is_not_a_hole():

    first = datetime(2026, 1, 12, 12, tzinfo=UTC)
    rows = [(10.0, 10.1, 9.9, 10.0)] * 60
    candles = build_candles(rows, Timeframe.M1, first) + build_candles(
        rows,
        Timeframe.M1,
        first + timedelta(hours=3, minutes=-1),  # 12:59 -> 14:59: 2 h
    )
    end, _ = exit_index(m1_from_candles(candles, CFG), 10, CFG)
    assert end == 119


# --- 7. stop variants -------------------------------------------------------------------------------------


def test_long_stop_prices():
    s = sig(swing_stop=8.0, prev_swing_stop=9.0, prev_candle_extreme=9.5, atr=1.0)
    out = stop_prices(s, CFG)
    assert out["swing10"] == pytest.approx(7.8)
    assert out["swing25"] == pytest.approx(7.5)
    assert out["swing50"] == pytest.approx(7.0)
    assert out["prevswing10"] == pytest.approx(8.9)
    assert out["prevcandle"] == pytest.approx(9.5)
    assert out["atr0.5"] == pytest.approx(9.5)
    assert out["atr1"] == pytest.approx(9.0)
    assert out["atr1.5"] == pytest.approx(8.5)
    assert out["atr2"] == pytest.approx(8.0)
    assert len(out) == 9


def test_short_stop_prices_are_the_mirror():
    s = sig(
        direction=SHORT, swing_stop=12.0, prev_swing_stop=11.0, prev_candle_extreme=10.5, atr=1.0
    )
    out = stop_prices(s, CFG)
    assert out["swing10"] == pytest.approx(12.2)
    assert out["swing50"] == pytest.approx(13.0)
    assert out["prevswing10"] == pytest.approx(11.1)
    assert out["prevcandle"] == pytest.approx(10.5)
    assert out["atr2"] == pytest.approx(12.0)


def test_a_stop_that_is_not_beyond_the_entry_gives_no_trade_for_that_variant():
    s = sig(swing_stop=10.5, prev_swing_stop=9.0, prev_candle_extreme=10.0, atr=1.0)
    out = stop_prices(s, CFG)
    assert not [k for k in out if k.startswith("swing")]  # swing low above the entry
    assert "prevcandle" not in out  # low = entry is not below it
    assert "prevswing10" in out and "atr1" in out
    assert stop_prices(sig(), CFG) == {}  # nothing known: no stop variant


def test_atr_missing_gives_no_atr_stops():
    out = stop_prices(sig(swing_stop=8.0), CFG)
    assert not [k for k in out if k.startswith("atr")]


# --- 8. trend structure ------------------------------------------------------------------------------------


def test_clean_structure_needs_rising_highs_and_rising_lows_for_a_long():
    assert clean_structure(LONG, [11.5, 12.2], [10.4, 11.2])
    assert not clean_structure(LONG, [11.5, 12.2], [10.4, 10.0])  # a lower low: mixed
    assert not clean_structure(LONG, [12.2, 11.5], [10.4, 11.2])  # a lower high: mixed
    assert not clean_structure(LONG, [12.2], [10.4, 11.2])  # not enough swings
    assert clean_structure(SHORT, [12.2, 11.5], [11.2, 10.4])
    assert not clean_structure(SHORT, [12.2, 11.5], [10.4, 11.2])


def test_four_hour_agrees_or_two_breaks_in_the_direction():
    assert four_hour_ok(LONG, LONG, [])
    assert not four_hour_ok(LONG, SHORT, [])
    assert not four_hour_ok(LONG, None, [])
    assert not four_hour_ok(LONG, SHORT, [LONG])  # one break is not enough
    assert four_hour_ok(LONG, SHORT, [SHORT, LONG, LONG])
    assert not four_hour_ok(LONG, SHORT, [LONG, LONG, SHORT])  # the last two must count
    assert four_hour_ok(SHORT, LONG, [SHORT, SHORT])


# Hand-built M5 structure (doji threshold 0): BOS up at 2, swing highs 11.5 / 12.2, swing lows
# 10.4 / 11.2, a no-wick green candle at 4 that also breaks 12.2 again (a continuation break).
UP = [
    (10.0, 11.0, 10.0, 11.0),
    (11.0, 11.5, 10.5, 10.6),
    (10.6, 12.0, 10.4, 11.9),
    (11.9, 12.2, 11.2, 11.3),
    (11.3, 12.5, 11.3, 12.4),
]
UP_MIXED = [*UP[:3], (11.9, 12.2, 10.0, 10.5), (10.5, 12.5, 10.5, 12.4)]  # lower low at 3-4
UP_ONE_BREAK = [*UP[:4], (11.3, 12.1, 11.3, 12.0)]  # candle 4 does not break 12.2 again


def m5(rows):

    return build_candles(rows, Timeframe.M5, START)


def h4_series(ohlc):

    return build_candles(ohlc, Timeframe.H4, START - timedelta(hours=4 * len(ohlc)))


DOWN_H4 = mirror(UP)  # a bearish 4h structure that closes before START
UP_H4 = UP


def signals_of(rows, h4=()):
    return [s for s in scan_signals(m5(rows), 0.0, h4, CFG) if s.index == len(rows) - 1]


def test_clean_hh_hl_signal_passes_every_structure_flag():
    (s,) = signals_of(UP, h4_series(UP_H4))
    assert s.direction is LONG and s.level == 11.3 and s.wick_share == 0.0
    assert s.bos and s.bos_clean and s.bos_4h
    assert (s.swing_stop, s.prev_swing_stop, s.swing_target) == (11.2, 10.4, 12.2)
    assert s.prev_candle_extreme == 11.2


def test_mixed_structure_has_bos_but_not_bos_clean():
    (s,) = signals_of(UP_MIXED, h4_series(UP_H4))
    assert s.bos and not s.bos_clean
    assert s.swing_stop == 10.0


def test_counter_trend_four_hour_needs_two_breaks_in_the_direction():
    (cont,) = signals_of(UP, h4_series(DOWN_H4))  # BOS up at 2 and a continuation break at 4
    assert cont.bos and cont.bos_4h  # 4h is bearish, but the last two breaks are both up
    (one,) = signals_of(UP_ONE_BREAK, h4_series(DOWN_H4))
    assert one.bos and not one.bos_4h
    (agree,) = signals_of(UP_ONE_BREAK, h4_series(UP_H4))
    assert agree.bos_4h


def test_no_bos_means_no_flags_but_the_control_signal_exists():
    flat = [(10.0, 10.5, 10.0, 10.4)]
    (s,) = signals_of(flat)
    assert not (s.bos or s.bos_clean or s.bos_4h)


def test_unclosed_four_hour_candle_is_not_used():
    # two closed 4h candles give no trend; the third opens at START and closes at 04:00, long
    # after the 5m signal at 00:25, so its break of structure must not be seen
    h4 = [*h4_series(UP_H4[:2]), Candle(START, *UP_H4[2])]
    (s,) = signals_of(UP_ONE_BREAK, h4)
    assert s.bos and not s.bos_4h


# --- 9. pdf session boundaries (New York time) --------------------------------------------------------------


@pytest.mark.parametrize(
    ("ny_hm", "skipped"),
    [
        ("09:29", False), ("09:30", True), ("10:29", True), ("10:30", False),
        ("14:59", False), ("15:00", True), ("16:59", True), ("17:00", False),
        ("18:59", False), ("19:00", True), ("21:59", True), ("22:00", False),
    ],
)  # fmt: skip
@pytest.mark.parametrize(
    "day", [datetime(2026, 1, 12, tzinfo=UTC), datetime(2026, 7, 13, tzinfo=UTC)]
)  # EST, EDT
def test_pdf_window_boundaries_follow_new_york_time(ny_hm, skipped, day):
    from zoneinfo import ZoneInfo

    h, m = map(int, ny_hm.split(":"))
    local = day.replace(hour=h, minute=m, tzinfo=ZoneInfo("America/New_York"))
    assert in_pdf_window(local.astimezone(UTC), CFG) is skipped


# --- 10. no lookahead --------------------------------------------------------------------------------------------


def random_candles(n, seed, timeframe=Timeframe.M5, start=START):
    rng = np.random.default_rng(seed)
    price, out = 100.0, []
    for i in range(n):
        o = price
        c = o + 0.5 * rng.integers(-3, 4)
        hi = max(o, c) + 0.5 * rng.integers(0, 2)
        lo = min(o, c) - 0.5 * rng.integers(0, 2)
        out.append(Candle(start + i * timeframe.duration, o, hi, lo, c))
        price = c
    return out


@pytest.mark.parametrize("cut", [120, 260, 410])
def test_signals_do_not_change_when_the_future_is_cut_off(cut):
    candles = random_candles(600, seed=3)
    h4 = random_candles(40, seed=4, timeframe=Timeframe.H4, start=START - timedelta(hours=40))
    full = scan_signals(candles, 0.0, h4, CFG)
    part = scan_signals(candles[: cut + 1], 0.0, h4, CFG)
    assert part == [s for s in full if s.index <= cut]
    assert len(part) > 5  # the fixture really produces signals


def test_a_later_swing_never_changes_an_earlier_signals_stop():
    (early,) = signals_of(UP, h4_series(UP_H4))
    longer = UP + [(12.4, 12.4, 9.0, 9.2), (9.2, 13.0, 9.0, 12.9)]  # a new, much lower swing low
    (again,) = [s for s in scan_signals(m5(longer), 0.0, h4_series(UP_H4), CFG) if s.index == 4]
    assert again == early


# --- 11. costs in R and the short mirror ----------------------------------------------------------------------------


def test_cost_price_is_spread_plus_round_turn_commission():
    assert cost_price(TEST_COSTS, "TEST", 10.0) == pytest.approx(0.2 + 7.0 / 100.0)


def test_cost_in_r_is_the_cost_over_the_stop_distance():
    data = m1([(10.5, 10.8, 10.2, 10.6), (10.6, 10.7, 9.95, 10.1)] + [(10.1, 10.2, 10.0, 10.1)] * 3)
    cols, _ = {}, {}
    evaluate_signal(data, sig(atr=1.0), Timeframe.M15, CFG, TEST_COSTS, "TEST", cols, {})
    i = cols["stop"].index("atr1")
    assert cols["risk"][i] == pytest.approx(1.0)
    assert cols["cost_r"][i] == pytest.approx(0.27 / 1.0)
    j = cols["stop"].index("atr2")
    assert cols["cost_r"][j] == pytest.approx(0.27 / 2.0)


def random_m1_frame(n, seed, flip=None):
    rng = np.random.default_rng(seed)
    price, rows = 100.0, []
    for _ in range(n):
        o = price
        c = o + 0.5 * rng.integers(-1, 2)
        hi = max(o, c) + 0.5 * rng.integers(0, 2)
        lo = min(o, c) - 0.5 * rng.integers(0, 2)
        rows.append((o, hi, lo, c))
        price = c
    if flip:
        rows = mirror(rows, flip)
    ts = pd.date_range(START, periods=n, freq="min", tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"]).assign(ts=ts)


def test_short_results_mirror_long_results_exactly():
    plain = random_m1_frame(5000, seed=7)
    flipped = random_m1_frame(5000, seed=7, flip=200.0)
    costs = CostConfig(symbols={"TEST": SymbolCosts(0.2, 7.0, 100.0)})
    a, _ = study_frames("TEST", Timeframe.M5, plain, 0.0, CFG, costs)
    b, _ = study_frames("TEST", Timeframe.M5, flipped, 0.0, CFG, costs)
    assert len(a) > 50
    assert len(a) == len(b)
    key = ["signal_time", "stop"]
    a, b = a.sort_values(key).reset_index(drop=True), b.sort_values(key).reset_index(drop=True)
    assert (a["direction"] == -b["direction"]).all()
    for col in ("risk", "mfe_r", "exit_r", "cost_r", "swing_target_r", "wick_share"):
        assert np.allclose(a[col], b[col], equal_nan=True), col
    for col in ("stopped", "bos", "bos_clean", "bos_4h", "pdf_skip", "overnight"):
        assert (a[col] == b[col]).all(), col


# --- scoring --------------------------------------------------------------------------------------------------------


def trade(symbol, when, mfe, stopped, cost, **kw):
    row = dict(
        symbol=symbol, tf="M15", signal_time=pd.Timestamp(when, tz="UTC"),
        fill_time=pd.Timestamp(when, tz="UTC"), direction=1, wick_share=0.0, bos=False,
        bos_clean=False, bos_4h=False, pdf_skip=False, overnight=False, stop="atr1", risk=1.0,
        mfe_r=mfe, stopped=stopped, exit_r=0.0, cost_price=cost, cost_r=cost,
        swing_target_r=math.nan,
    )  # fmt: skip
    return {**row, **kw}


def sample_trades():
    return pd.DataFrame(
        [
            trade("EURUSD", "2016-03-01", 1.2, False, 0.1),
            trade("EURUSD", "2019-03-01", 0.3, True, 0.1, pdf_skip=True),
            trade("XAUUSD", "2016-06-01", 1.5, False, 0.2, bos=True),
            trade("XAUUSD", "2020-06-01", 0.1, True, 0.2),
        ]
    )


def pick(summary, **kw):
    q = summary
    for k, v in kw.items():
        q = q[q[k] == v]
    assert len(q) == 1, kw
    return q.iloc[0]


def test_score_trades_numbers_for_a_target_of_1r():
    s = score_trades(sample_trades(), CFG)
    row = pick(s, group="ALL", tf="M15", trend="none", session="all", wick=0.05, stop="atr1",
               target="1")  # fmt: skip
    assert row["trades"] == 4
    assert row["win_pct"] == pytest.approx(50.0)
    assert row["gross_r_per_trade"] == pytest.approx(0.0)
    assert row["net_r_per_trade"] == pytest.approx(-0.15)
    assert row["net_r_total"] == pytest.approx(-0.6)
    assert row["net_r_per_trade_h1"] == pytest.approx(0.85)  # 2016 trades: 0.9 and 0.8
    assert row["net_r_per_trade_h2"] == pytest.approx(-1.15)
    assert row["symbols_pos_share"] == pytest.approx(0.0)


def test_score_trades_filters_session_trend_and_groups():
    s = score_trades(sample_trades(), CFG)
    pdf = pick(s, group="ALL", tf="M15", trend="none", session="pdf", wick=0.0, stop="atr1",
               target="1")  # fmt: skip
    assert pdf["trades"] == 3  # the pdf-window signal is dropped
    bos = pick(s, group="ALL", tf="M15", trend="bos", session="all", wick=0.0, stop="atr1",
               target="1")  # fmt: skip
    assert bos["trades"] == 1 and bos["net_r_per_trade"] == pytest.approx(0.8)
    metals = pick(s, group="metals", tf="M15", trend="none", session="all", wick=0.0,
                  stop="atr1", target="1")  # fmt: skip
    assert metals["trades"] == 2 and metals["symbols_pos_share"] == 0.0
    assert pick(s, group="fx", tf="M15", trend="none", session="all", wick=0.0, stop="atr1",
                target="1")["trades"] == 2  # fmt: skip


def test_wick_zero_variant_excludes_wicked_signals():
    t = sample_trades()
    t.loc[0, "wick_share"] = 0.03
    s = score_trades(t, CFG)
    kw = dict(group="ALL", tf="M15", trend="none", session="all", stop="atr1", target="1")
    assert pick(s, wick=0.0, **kw)["trades"] == 3
    assert pick(s, wick=0.05, **kw)["trades"] == 4


def test_score_drops_expensive_and_overnight_trades():
    t = sample_trades()
    t.loc[0, "cost_r"] = 5.0  # a tiny stop: costs far above the cap
    t.loc[2, "overnight"] = True  # held across the rollover, swap not modelled
    s = score_trades(t, StudyConfig(max_cost_r=0.3))
    row = pick(s, group="ALL", tf="M15", trend="none", session="all", wick=0.05, stop="atr1",
               target="1")  # fmt: skip
    assert row["trades"] == 2
    s = score_trades(t, StudyConfig(max_cost_r=None, drop_overnight=False))
    assert pick(s, group="ALL", tf="M15", trend="none", session="all", wick=0.05, stop="atr1",
                target="1")["trades"] == 4  # fmt: skip


def test_swing_target_rows_without_a_swing_target_are_left_out():
    t = sample_trades()
    t.loc[0, "swing_target_r"] = 1.0
    s = score_trades(t, CFG)
    row = pick(s, group="ALL", tf="M15", trend="none", session="all", wick=0.05, stop="atr1",
               target="swing")  # fmt: skip
    assert row["trades"] == 1 and row["gross_r_per_trade"] == pytest.approx(1.0)


def test_score_mode_rewrites_summary_from_a_trades_file(tmp_path, capsys):
    sample_trades().to_parquet(tmp_path / "trades.parquet")
    assert study.main(["--score", "--out", str(tmp_path)]) == 0
    summary = pd.read_csv(tmp_path / "summary.csv")
    assert {"trades", "net_r_per_trade", "tstat"} <= set(summary.columns)
    assert "share of variants with net > 0" in capsys.readouterr().out
