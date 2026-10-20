"""Gap-bucket study of strategy 7 (open-to-close return per gap bucket, momentum against fade).
Spec: docs/strategy-gap-momentum.md > Backtest options (study part, I-09 / C-5)."""

from __future__ import annotations

import itertools
import math
import statistics
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from backtester.analytics.gap_buckets import GapDay, bucket_label, bucket_rows, gap_days
from backtester.strategy.gap_momentum.config import GapMomentumConfig

NY = ZoneInfo("America/New_York")
CLOSES = (104.0, 106.0)
CFG = GapMomentumConfig(vol_days=4, atr_period=3)


def at(day: date, hhmm: str) -> datetime:
    h, m = map(int, hhmm.split(":"))
    return datetime.combine(day, time(h, m), tzinfo=NY).astimezone(UTC)


def weekdays(start: date, n: int) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def warm(day: date, k: int, with_close=True):
    c = CLOSES[k % 2]
    return [
        (at(day, "09:30"), c, c, c),
        (at(day, "12:00"), 110.0, 100.0, c),
        (at(day, "16:00" if with_close else "15:00"), c + 0.5, c - 0.5, c),
    ]


def bars(opens_and_closes, warm_days=5, last_warm_close=True):
    """warm days, then one day per (open, session close) pair; the session range is 100-110."""
    days = weekdays(date(2026, 1, 5), warm_days + len(opens_and_closes))
    out = []
    for k, d in enumerate(days[:warm_days]):
        out += warm(d, k, last_warm_close or k < warm_days - 1)
    for d, (o, c) in zip(days[warm_days:], opens_and_closes, strict=True):
        out += [(at(d, "09:30"), o, o, o), (at(d, "12:00"), 110.0, 100.0, 105.0),
                (at(d, "16:00"), c + 0.5, c - 0.5, c)]  # fmt: skip
    return out, days


def sd_last4():
    closes = [CLOSES[k % 2] for k in range(5)]
    return statistics.stdev(math.log(b / a) for a, b in itertools.pairwise(closes))


def test_gap_day_record_has_the_open_the_prior_range_sd_atr_and_the_session_close():
    data, days = bars([(115.0, 118.0)])
    [g] = gap_days(data, CFG)
    assert g.day == days[5] and g.open == 115.0 and g.close == 118.0
    assert (g.prev_high, g.prev_low, g.prev_close) == (110.0, 100.0, 104.0)
    assert g.sd == pytest.approx(sd_last4()) and g.atr == pytest.approx(10.0)


def test_no_record_before_the_history_exists_or_after_a_session_without_a_close():
    data, _ = bars([(115.0, 118.0)], warm_days=4)
    assert gap_days(data, CFG) == []
    data, _ = bars([(115.0, 118.0)], last_warm_close=False)
    assert gap_days(data, CFG) == []


def test_a_day_without_its_closing_candle_has_no_record():
    data, days = bars([(115.0, 118.0)])
    data = [b for b in data if b[0] != at(days[5], "16:00")]
    assert gap_days(data, CFG) == []


def test_fx_mode_uses_its_own_session():
    cfg = GapMomentumConfig(mode="fx", vol_days=4, atr_period=3)
    days = weekdays(date(2026, 1, 5), 6)
    data = []
    for k, d in enumerate(days[:5]):
        c = CLOSES[k % 2]
        data += [
            (at(d, "05:00"), c, c, c),
            (at(d, "12:00"), 110.0, 100.0, c),
            (at(d, "17:00"), c, c, c),
        ]
    data += [(at(days[5], "05:00"), 99.0, 99.0, 99.0), (at(days[5], "17:00"), 97.0, 96.0, 97.0)]
    [g] = gap_days(data, cfg)
    assert g.open == 99.0 and g.close == 97.0 and g.prev_low == 100.0


@pytest.mark.parametrize(
    ("gap_sd", "label"),
    [(0.0, "0-0.1"), (0.0999, "0-0.1"), (0.1, "0.1-0.25"), (0.2499, "0.1-0.25"), (0.25, "0.25-0.5"),
     (0.5, "0.5-1"), (0.999, "0.5-1"), (1.0, ">1"), (7.0, ">1")],
)  # fmt: skip
def test_bucket_edges_are_lower_inclusive(gap_sd, label):
    assert bucket_label(gap_sd) == label


def day(d, o, c, prev_close=104.0, high=110.0, low=100.0, sd=0.02, atr=10.0):
    return GapDay(d, o, high, low, prev_close, sd, atr, c)


def find(rows, **match):
    [r] = [r for r in rows if all(r[k] == v for k, v in match.items())]
    return r


def test_beyond_up_gap_momentum_is_the_move_with_the_gap_and_fade_is_its_negative():
    d = date(2026, 1, 12)
    # gap = ln(115/104)/0.02 = 5.0 sd -> bucket >1; beyond the high 110
    rows = bucket_rows([day(d, 115.0, 118.0)], "T", d)
    r = find(rows, symbol="T", half="all", bucket=">1", location="beyond", direction="up")
    move = math.log(118 / 115) / 0.02
    assert r["n"] == 1
    assert r["mean_sd_momentum"] == pytest.approx(move)
    assert r["mean_sd_fade"] == pytest.approx(-move)
    assert r["mean_atr_momentum"] == pytest.approx(0.3)
    assert r["share_positive_momentum"] == 1.0


def test_down_gap_momentum_is_the_negative_price_move():
    d = date(2026, 1, 12)
    rows = bucket_rows([day(d, 95.0, 90.0)], "T", d)
    r = find(rows, bucket=">1", location="beyond", direction="down", half="all")
    assert r["mean_sd_momentum"] == pytest.approx(-math.log(90 / 95) / 0.02)
    assert r["mean_atr_momentum"] == pytest.approx(0.5)


def test_inside_versus_beyond_the_prior_range():
    d = date(2026, 1, 12)
    # up gaps from prev close 104: open 108 is inside the range (below the high 110), 112 beyond
    rows = bucket_rows([day(d, 108.0, 109.0), day(d + timedelta(1), 112.0, 111.0)], "T", d)
    assert find(rows, bucket=">1", location="inside", direction="up", half="all")["n"] == 1
    assert find(rows, bucket=">1", location="beyond", direction="up", half="all")["n"] == 1
    assert find(rows, bucket=">1", location="all", direction="up", half="all")["n"] == 2


def test_open_exactly_at_the_prior_high_is_inside_and_a_zero_gap_is_skipped():
    d = date(2026, 1, 12)
    rows = bucket_rows([day(d, 110.0, 111.0), day(d + timedelta(1), 104.0, 105.0)], "T", d)
    assert find(rows, bucket=">1", location="inside", direction="up", half="all")["n"] == 1
    assert find(rows, direction="all", bucket="all", location="all", half="all")["n"] == 1


def test_halves_split_at_the_middle_date_which_belongs_to_the_first_half():
    d1, d2, d3 = date(2026, 1, 12), date(2026, 1, 13), date(2026, 1, 14)
    rows = bucket_rows(
        [day(d1, 115.0, 116.0), day(d2, 115.0, 117.0), day(d3, 115.0, 118.0)], "T", d2
    )
    got = {h: find(rows, bucket="all", location="all", direction="all", half=h)["n"]
           for h in ("all", "first", "second")}  # fmt: skip
    assert got == {"all": 3, "first": 2, "second": 1}


def test_buckets_use_the_absolute_gap_in_sd_units():
    d = date(2026, 1, 12)
    # gap ln(104.5/104)/0.02 = 0.24 sd -> 0.1-0.25
    rows = bucket_rows([day(d, 104.5, 105.0)], "T", d)
    assert find(rows, bucket="0.1-0.25", location="inside", direction="up", half="all")["n"] == 1
    assert not [r for r in rows if r["bucket"] == ">1"]
