"""Critical cases, written before production changes (research-runner.md > Walk-forward):
1. 12/12 full-year results exactly match the existing yearly API.
2. Training excludes exits at/after the boundary; OOS keeps later exits.
3. Anchored grows, rolling forgets; empty variants rank as zero, ties keep order.
4. Defaults 24/6, strict positive integer lengths, overlap refused, gaps allowed.
5. First full month, fractional final month (leap year), too short gives a reason.
6. UTC membership and chronological chained trades; future outcomes cannot alter picks.
"""

from datetime import UTC, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from backtester.analytics.walk_forward import WalkForwardConfig, walk_forward


def dt(year, month=1, day=1):
    return datetime(year, month, day, tzinfo=UTC)


def trade(entry, r, exit=None):
    return SimpleNamespace(entry_time=entry, exit_time=exit or entry, r_net=r)


def run(variants, mode="anchored", **kwargs):
    return walk_forward(
        variants,
        WalkForwardConfig(mode=mode, train_months=12, test_months=6, **kwargs),
        start=dt(2018),
        end=dt(2021),
    )


def test_yearly_equivalence():
    variants = {
        "a": [trade(dt(y, 3), r) for y, r in [(2018, 4), (2019, -2), (2020, 3)]],
        "b": [trade(dt(y, 3), r) for y, r in [(2018, 2), (2019, 4), (2020, -1)]],
    }
    old = walk_forward(variants, first_year=2018, last_year=2020)
    new = walk_forward(
        variants, WalkForwardConfig(train_months=12, test_months=12), start=dt(2018), end=dt(2021)
    )
    assert [(p.variant, p.train_net, p.test_trades) for p in new.picks] == [
        (p.variant, p.train_net, p.test_trades) for p in old.picks
    ]
    assert new.chained == old.chained


@pytest.mark.parametrize("exit_time", [dt(2019), dt(2019, 2)])
def test_boundaries_and_future_invariance(exit_time):
    late = trade(dt(2018, 12), 100, exit_time)
    held = trade(dt(2019, 2), 7, dt(2020))
    variants = {"a": [late], "b": [trade(dt(2018, 2), 1), held]}
    result = run(variants)
    assert result.picks[0].variant == "b"
    assert result.picks[0].train_net == 1
    assert result.picks[0].test_trades == (held,)
    assert result.chained.count(held) == 1
    late.r_net = 999
    assert run(variants).picks[0] == result.picks[0]


def test_rolling_anchored_and_empty_variants():
    variants = {"a": [trade(dt(2018, 2), 10), trade(dt(2019, 2), -1)], "b": [trade(dt(2019, 2), 2)]}
    anchored, rolling = run(variants), run(variants, "rolling")
    assert anchored.picks[2].variant == "a"
    assert rolling.picks[2].variant == "b"
    assert anchored.picks[2].train_start == dt(2018)
    assert rolling.picks[2].train_start == dt(2019)
    assert run({"empty": [], "loser": [trade(dt(2018, 2), -1)]}).picks[0].variant == "empty"
    assert run({"first": [], "second": []}).picks[0].variant == "first"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"train_months": 0},
        {"test_months": -1},
        {"step_months": 0},
        {"train_months": True},
        {"train_months": None},
        {"test_months": None},
        {"test_months": 1.5},
        {"step_months": 3},
    ],
)
def test_invalid_month_lengths(kwargs):
    with pytest.raises(ValueError):
        WalkForwardConfig(**kwargs)


def test_defaults_and_gaps():
    cfg = WalkForwardConfig()
    assert (cfg.train_months, cfg.test_months, cfg.step_months) == (24, 6, 6)
    result = run({"a": []}, step_months=12)
    assert [p.test_start for p in result.picks] == [dt(2019), dt(2020)]


def test_partial_and_short_period():
    cfg = WalkForwardConfig(train_months=1, test_months=1)
    result = walk_forward({"a": []}, cfg, start=dt(2019, 12, 15), end=dt(2020, 2, 15))
    p = result.picks[0]
    assert p.train_start == dt(2020)
    assert (p.test_start, p.test_end) == (dt(2020, 2), dt(2020, 2, 15))
    assert p.test_months == pytest.approx(14 / 29)
    short = walk_forward({"a": []}, cfg, start=dt(2020), end=dt(2020, 2))
    assert short.picks == () and short.reason


def test_utc_and_sorted_trades():
    offset = timezone(timedelta(hours=2))
    before = trade(datetime(2019, 1, 1, 1, tzinfo=offset), 2)
    first, second = trade(dt(2019, 2), 1), trade(dt(2019, 3), -1)
    result = run({"a": [second, before, first]})
    assert result.picks[0].train_net == 2
    assert result.picks[0].test_trades == (first, second)
