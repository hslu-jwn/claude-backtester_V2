"""Summary tables of the open / gap study on hand-made day records. Spec: ROADMAP.md › 11.2."""

from __future__ import annotations

import pytest

from backtester.analytics.open_gap import (
    OpenGapConfig,
    summarize_extremes,
    summarize_first30,
    summarize_gaps,
    summarize_last_hour,
    summarize_trend,
)

CFG = OpenGapConfig()
H1, H2 = CFG.half_labels


def rec(**kw):
    base = {
        "half": H1, "flat": False, "gap_dir": "up", "gap_bucket": "0.1-0.25",
        "filled_same_day": False, "filled_by_day3": False, "extend_same_day": False,
        "first_touch": "neither",
        "first30_atr": 0.5, "rest_atr": 0.5, "continued": True,
        "trend_day": False, "weekday": "3 Wed", "month_part": "mid",
        "filled_by_11": False, "new_extreme_10_11": False, "pos_11": 0.5,
        "high_in_first90": False, "low_in_first90": False,
        "high_in_first_hour": False, "low_in_first_hour": False,
        "high_in_last_hour": False, "low_in_last_hour": False,
        "close_pos": 0.5, "last_hour_event": "none", "last_hour_move_atr": None,
    }  # fmt: skip
    return {**base, **kw}


def row(rows, **match):
    found = [r for r in rows if all(r.get(k) == v for k, v in match.items())]
    assert len(found) == 1, (match, len(found))
    return found[0]


def test_gaps_by_half_direction_and_bucket_with_flat_counted_apart():
    records = [
        rec(filled_same_day=True, filled_by_day3=True, extend_same_day=True),
        rec(filled_same_day=False, filled_by_day3=None),
        rec(gap_dir="down", gap_bucket="1+", filled_same_day=True, filled_by_day3=True),
        rec(flat=True, gap_dir="flat", gap_bucket="flat", filled_same_day=None),
        rec(half=H2, filled_same_day=True, filled_by_day3=True),
    ]
    rows = summarize_gaps(records, CFG)
    up = row(rows, half=H1, direction="up", bucket="0.1-0.25")
    assert up["n"] == 2
    assert up["same_day_fill"] == pytest.approx(0.5)
    assert up["n_day3_known"] == 1
    assert up["by_day3_fill"] == pytest.approx(1.0)
    assert up["extend_same_day"] == pytest.approx(0.5)
    assert up["same_day_ci_low"] < 0.5 < up["same_day_ci_high"]
    assert row(rows, half=H1, direction="both", bucket="all")["n"] == 3
    assert row(rows, half=H1, direction="down", bucket="1+")["same_day_fill"] == 1.0
    assert row(rows, half=H1, direction="flat", bucket="flat")["n"] == 1
    assert row(rows, half="all", direction="both", bucket="all")["n"] == 4  # flat excluded


def test_gap_table_has_the_first_touch_shares():
    records = [
        rec(first_touch="fill"),
        rec(first_touch="fill"),
        rec(first_touch="extend"),
        rec(first_touch="same_bar"),
        rec(first_touch="neither"),
    ]
    r = row(summarize_gaps(records, CFG), half=H1, direction="up", bucket="0.1-0.25")
    assert r["fill_first"] == pytest.approx(0.4)
    assert r["extend_first"] == pytest.approx(0.2)
    assert r["same_bar"] == pytest.approx(0.2)
    assert r["neither"] == pytest.approx(0.2)


def test_gap_table_skips_empty_combinations():
    rows = summarize_gaps([rec()], CFG)
    assert not [r for r in rows if r["half"] == H1 and r["direction"] == "down" and r["n"]]


def test_first30_continuation_share_and_signed_rest_move():
    records = [
        rec(first30_atr=1.0, rest_atr=0.5, continued=True),
        rec(first30_atr=1.0, rest_atr=-0.5, continued=False),
        rec(first30_atr=-1.0, rest_atr=-0.5, continued=True),
        rec(first30_atr=1.0, rest_atr=0.0, continued=None),  # zero rest: left out
    ]
    r = row(summarize_first30(records, CFG), half=H1, bucket="all")
    assert r["n"] == 3
    assert r["continuation_share"] == pytest.approx(2 / 3)
    assert r["mean_rest_signed_atr"] == pytest.approx((0.5 - 0.5 + 0.5) / 3)


def test_trend_day_share_lift_and_wilson_interval():
    records = [
        rec(trend_day=True, filled_by_11=False),
        rec(trend_day=False, filled_by_11=False),
        rec(trend_day=False, filled_by_11=True),
        rec(trend_day=False, filled_by_11=True),
        rec(trend_day=None),  # zero-range day: not counted
    ]
    rows = summarize_trend(records, CFG)
    base = row(rows, half=H1, group="all", feature="(none)")
    assert base["n"] == 4
    assert base["share"] == pytest.approx(0.25)
    unfilled = row(rows, half=H1, group="all", feature="gap_unfilled_at_11")
    assert unfilled["n"] == 2
    assert unfilled["share"] == pytest.approx(0.5)
    assert unfilled["lift"] == pytest.approx(2.0)
    assert unfilled["ci_low"] < unfilled["share"] < unfilled["ci_high"]


def test_trend_groups_by_weekday_and_month_part():
    records = [
        rec(trend_day=True, weekday="5 Fri"),
        rec(trend_day=False, weekday="5 Fri"),
        rec(trend_day=False, weekday="2 Tue", month_part="first 3 days"),
    ]
    rows = summarize_trend(records, CFG)
    assert row(rows, half=H1, group="weekday 5 Fri", feature="(none)")["share"] == pytest.approx(
        0.5
    )
    assert row(rows, half=H1, group="month first 3 days", feature="(none)")["n"] == 1


def test_position_feature_uses_the_extreme_fifth():
    records = [rec(trend_day=True, pos_11=0.9), rec(trend_day=False, pos_11=0.5)]
    r = row(summarize_trend(records, CFG), half=H1, group="all", feature="pos_11_in_extreme_fifth")
    assert r["n"] == 1 and r["share"] == 1.0


def test_extremes_shares_next_to_uniform_and_random_walk():
    records = [
        rec(high_in_first90=True, low_in_first90=False),
        rec(high_in_first90=False, low_in_first90=True),
        rec(high_in_first90=True, low_in_first90=True),
        rec(),
    ]
    r = row(summarize_extremes(records, CFG), half=H1, window="first_90_min")
    assert r["n"] == 4
    assert r["high_share"] == pytest.approx(0.5)
    assert r["low_share"] == pytest.approx(0.5)
    assert r["either_share"] == pytest.approx(0.75)
    assert r["both_share"] == pytest.approx(0.25)
    assert r["uniform_share"] == pytest.approx(90 / 390)
    assert r["random_walk_share"] == pytest.approx(0.319, abs=1e-3)


def test_last_hour_close_position_and_move_by_event():
    records = [
        rec(last_hour_event="high", last_hour_move_atr=1.0, close_pos=0.9),
        rec(last_hour_event="high", last_hour_move_atr=-0.5, close_pos=0.6),
        rec(last_hour_event="none", close_pos=0.4),
        rec(close_pos=None),  # no close position (zero range): left out
    ]
    rows = summarize_last_hour(records, CFG)
    high = row(rows, half=H1, event="high")
    assert high["n"] == 2
    assert high["mean_close_pos"] == pytest.approx(0.75)
    assert high["mean_move_atr"] == pytest.approx(0.25)
    assert row(rows, half=H1, event="all days")["n"] == 3
