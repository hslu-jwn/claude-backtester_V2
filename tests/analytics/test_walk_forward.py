"""Walk-forward splitter: anchored / rolling yearly windows, best-variant pick on the train years.
Spec: ROADMAP 12.3 / 11.7."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from backtester.analytics.walk_forward import WalkForwardConfig, walk_forward


def t(year, r, month=3):
    return SimpleNamespace(entry_time=datetime(year, month, 10, 14, 30, tzinfo=UTC), r_net=r)


def test_anchored_picks_best_on_all_years_before():
    variants = {
        "a": [t(2019, 1.0), t(2020, 1.0), t(2021, -5.0)],
        "b": [t(2019, 0.5), t(2020, 0.5), t(2021, 3.0)],
    }
    res = walk_forward(variants)
    assert [p.year for p in res.picks] == [2020, 2021]
    assert [p.variant for p in res.picks] == ["a", "a"]  # 2021: a has 2.0 vs b 1.0 on 2019-20
    assert res.picks[0].train_net == pytest.approx(1.0)
    assert res.picks[1].train_net == pytest.approx(2.0)
    assert [x.r_net for x in res.picks[1].test_trades] == [-5.0]


def test_choice_ignores_test_year_trades():
    base = {"a": [t(2019, 1.0), t(2020, 0.0)], "b": [t(2019, 0.5), t(2020, 0.0)]}
    changed = {"a": [t(2019, 1.0), t(2020, -99.0)], "b": [t(2019, 0.5), t(2020, 99.0)]}
    assert walk_forward(base).picks[0].variant == walk_forward(changed).picks[0].variant == "a"


def test_rolling_window_forgets_old_years():
    variants = {
        "a": [t(2018, 10.0), t(2019, -1.0), t(2020, -1.0), t(2021, 0.0)],
        "b": [t(2018, 0.0), t(2019, 1.0), t(2020, 1.0), t(2021, 0.0)],
    }
    anchored = walk_forward(variants)
    rolling = walk_forward(variants, WalkForwardConfig(mode="rolling", train_years=2))
    assert anchored.picks[-1].variant == "a"  # 2018-20: a +8 vs b +2
    assert rolling.picks[-1].variant == "b"  # 2019-20 only: a -2 vs b +2
    assert rolling.picks[-1].train_years == (2019, 2020)
    assert anchored.picks[-1].train_years == (2018, 2019, 2020)


def test_tie_goes_to_first_variant_in_order():
    variants = {"first": [t(2019, 1.0), t(2020, 1.0)], "second": [t(2019, 1.0), t(2020, 2.0)]}
    assert walk_forward(variants).picks[0].variant == "first"
    swapped = {"second": variants["second"], "first": variants["first"]}
    assert walk_forward(swapped).picks[0].variant == "second"


def test_year_without_trades_is_a_test_year_with_no_trades():
    variants = {"a": [t(2019, 1.0), t(2021, 1.0)], "b": [t(2019, 0.0), t(2021, 0.0)]}
    res = walk_forward(variants)
    assert [p.year for p in res.picks] == [2020, 2021]
    assert res.picks[0].test_trades == ()
    assert res.picks[1].train_net == pytest.approx(1.0)


def test_chained_trades_are_the_union_of_the_chosen_test_year_trades():
    variants = {
        "a": [t(2019, 1.0), t(2020, 0.1), t(2021, 0.2)],
        "b": [t(2019, 0.0), t(2020, 0.3), t(2021, 0.4)],
    }
    res = walk_forward(variants)
    assert [x.r_net for x in res.chained] == [0.1, 0.2]  # a is chosen both years


def test_min_train_years_delays_the_first_test_year():
    variants = {"a": [t(2018, 1.0), t(2019, 1.0), t(2020, 1.0)]}
    res = walk_forward(variants, WalkForwardConfig(min_train_years=2))
    assert [p.year for p in res.picks] == [2020]


def test_explicit_year_range_and_empty_input():
    variants = {"a": [t(2019, 1.0)]}
    res = walk_forward(variants, first_year=2018, last_year=2020)
    assert [p.year for p in res.picks] == [2019, 2020]
    assert walk_forward({"a": []}).picks == ()
    assert walk_forward({"a": []}).chained == ()


def test_config_validation():
    with pytest.raises(ValueError):
        WalkForwardConfig(mode="other")
    with pytest.raises(ValueError):
        WalkForwardConfig(min_train_years=0)
    with pytest.raises(ValueError):
        WalkForwardConfig(mode="rolling", train_years=0)
    with pytest.raises(ValueError):
        walk_forward({})
