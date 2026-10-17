"""Daily guard: FTMO day = midnight Europe/Prague; day P/L = equity - balance at day start."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backtester.risk.prop_rules import GuardConfig, evaluate, prague_day_start

CFG = GuardConfig()


def utc(*a) -> datetime:
    return datetime(*a, tzinfo=UTC)


def test_defaults_are_the_spec():
    assert (CFG.daily_stop_percent, CFG.ftmo_daily_loss_percent, CFG.ftmo_max_loss_percent) == (
        2.0,
        5.0,
        10.0,
    )
    assert CFG.initial_balance == 100_000.0


def test_day_start_in_winter_and_summer():
    # CET = UTC+1: Prague midnight is 23:00 UTC the evening before
    assert prague_day_start(utc(2026, 1, 12, 10, 0)) == utc(2026, 1, 11, 23, 0)
    # CEST = UTC+2
    assert prague_day_start(utc(2026, 7, 13, 10, 0)) == utc(2026, 7, 12, 22, 0)


def test_boundary_minute_winter():
    assert prague_day_start(utc(2026, 1, 11, 22, 59)) == utc(2026, 1, 10, 23, 0)
    assert prague_day_start(utc(2026, 1, 11, 23, 0)) == utc(2026, 1, 11, 23, 0)


def test_dst_change_days_have_23_and_25_hours():
    # spring forward 2026-03-29: that Prague day starts 23:00 UTC on the 28th and the next one
    # at 22:00 UTC on the 29th (the day is 23 h long)
    assert prague_day_start(utc(2026, 3, 29, 12, 0)) == utc(2026, 3, 28, 23, 0)
    assert prague_day_start(utc(2026, 3, 30, 1, 0)) == utc(2026, 3, 29, 22, 0)
    # fall back 2026-10-25: starts 22:00 UTC on the 24th; the next day 23:00 UTC on the 25th
    assert prague_day_start(utc(2026, 10, 25, 12, 0)) == utc(2026, 10, 24, 22, 0)
    assert prague_day_start(utc(2026, 10, 26, 0, 30)) == utc(2026, 10, 25, 23, 0)


def test_naive_time_is_rejected():
    with pytest.raises(ValueError):
        prague_day_start(datetime(2026, 1, 1))  # noqa: DTZ001


def test_no_loss_no_stop():
    s = evaluate(CFG, 100_000, 100_500)
    assert not s.stop_trading and not s.breach and s.day_pl == 500
    assert s.day_pl_percent == pytest.approx(0.5)


def test_floating_loss_counts_and_stops_at_minus_two_percent():
    s = evaluate(CFG, 100_000, 98_000)  # exactly -2 %: reached
    assert s.stop_trading and not s.breach and "daily stop" in s.reason
    assert not evaluate(CFG, 100_000, 98_001).stop_trading


def test_ftmo_daily_loss_is_a_breach():
    s = evaluate(CFG, 100_000, 95_000)
    assert s.breach and s.stop_trading and "FTMO daily loss" in s.reason
    assert not evaluate(CFG, 100_000, 95_001).breach


def test_max_loss_is_static_on_the_initial_balance():
    s = evaluate(CFG, 90_500, 90_000)  # day P/L small, equity at 90 % of 100k
    assert s.breach and "FTMO max loss" in s.reason
    assert not evaluate(CFG, 90_500, 90_001).breach


def test_daily_stop_uses_the_day_start_balance_not_the_initial():
    s = evaluate(CFG, 110_000, 107_800)  # -2 % of 110k = 2200
    assert s.stop_trading
    assert not evaluate(CFG, 110_000, 107_801).stop_trading


def test_invalid_config_and_balance():
    with pytest.raises(ValueError):
        GuardConfig(daily_stop_percent=0)
    with pytest.raises(ValueError):
        evaluate(CFG, 0, 100)
