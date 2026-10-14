"""Swap in the engine: one night per 17:00 America/New_York rollover between entry and exit
(3 on the triple weekday), in R, net only. Spec: risk-management.md › Costs › Swap in the
engine. 17:00 New York is 22:00 UTC in winter and 21:00 UTC in summer."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from conftest import build_series

from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts, rollover_nights
from backtester.strategy.base import Order, Strategy

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
M5 = timedelta(minutes=5)
MON, WED, SAT = 0, 2, 5
FLAT = (100.0, 100.1, 99.9, 100.0)  # never reaches SL 98 / TP 102 / 104
LONG_RATE, SHORT_RATE = -7.0, 3.0  # USD per lot per night
# risk 2 (entry 100, SL 98) x 100 per price unit and lot = 200 USD per lot and R
LONG_NIGHT_R, SHORT_NIGHT_R = LONG_RATE / 200, SHORT_RATE / 200


class Scripted(Strategy):
    """At base cursor k, enter each (direction, SL, TP) or Order-field dict of script[k]."""

    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)

    def __init__(self, script):
        self.script = script

    def on_candle(self, now, views):
        base = views[Timeframe.M5]
        close = base.current.close
        return [
            Order(item["direction"], close, **{k: v for k, v in item.items() if k != "direction"})
            if isinstance(item, dict)
            else Order(item[0], close, *item[1:])
            for item in self.script.get(base.cursor, [])
        ]


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=UTC)


def costs(**kw) -> CostConfig:
    sym = SymbolCosts(
        spread=0.0,
        commission_per_lot=0.0,
        contract_size=100,
        swap_long_per_lot=LONG_RATE,
        swap_short_per_lot=SHORT_RATE,
        **kw.pop("symbol", {}),
    )
    return CostConfig(spread_enabled=False, commission_enabled=False, symbols={"TEST": sym}, **kw)


def run(start, n, direction=LONG, cost=None, tp=None):
    """One trade entered at the first candle's close, held `n` candles in total (end of data)."""
    cost = cost or costs()
    sl = 98.0 if direction is LONG else 102.0
    series = build_series([FLAT] * n, start=start)
    [t] = run_backtest(Scripted({0: [(direction, sl, tp)]}), [series], EngineConfig(costs=cost))
    return t


# --- rollover_nights: counting ----------------------------------------------------------


def test_no_rollover_inside_the_trade_is_zero_nights():
    assert rollover_nights(utc(2026, 1, 5, 10), utc(2026, 1, 5, 20), WED) == 0


def test_rollover_is_2200_utc_in_winter_and_2100_utc_in_summer():
    w_before, w_after = utc(2026, 1, 5, 21, 59), utc(2026, 1, 5, 22, 1)
    s_before, s_after = utc(2026, 7, 6, 20, 59), utc(2026, 7, 6, 21, 1)
    assert rollover_nights(utc(2026, 1, 5, 12), w_before, WED) == 0
    assert rollover_nights(utc(2026, 1, 5, 12), w_after, WED) == 1
    assert rollover_nights(utc(2026, 7, 6, 12), s_before, WED) == 0
    assert rollover_nights(utc(2026, 7, 6, 12), s_after, WED) == 1
    # the summer instant is still before the rollover in winter
    assert rollover_nights(utc(2026, 1, 5, 12), utc(2026, 1, 5, 21, 30), WED) == 0


def test_rollover_exactly_at_entry_does_not_count_exactly_at_exit_counts():
    rollover = utc(2026, 1, 5, 22)
    assert rollover_nights(rollover, rollover + timedelta(hours=1), WED) == 0
    assert rollover_nights(rollover - timedelta(hours=1), rollover, WED) == 1
    assert rollover_nights(rollover, rollover, WED) == 0


def test_dst_changeover_week_follows_new_york_not_a_fixed_offset():
    # US DST starts Sun 2026-03-08; Fri 3/6 rollover = 22:00 UTC, Mon 3/9 = 21:00 UTC
    assert rollover_nights(utc(2026, 3, 6, 21, 59), utc(2026, 3, 6, 22), WED) == 1
    assert rollover_nights(utc(2026, 3, 9, 12), utc(2026, 3, 9, 20, 59), WED) == 0
    assert rollover_nights(utc(2026, 3, 9, 12), utc(2026, 3, 9, 21), WED) == 1


def test_friday_to_monday_counts_only_the_friday_rollover():
    # Fri 2026-01-09 20:00 UTC to Mon 2026-01-12 12:00 UTC: Fri 17:00 NY only
    assert rollover_nights(utc(2026, 1, 9, 20), utc(2026, 1, 12, 12), WED) == 1
    # Saturday and Sunday dates never count, even if the triple weekday is Saturday
    assert rollover_nights(utc(2026, 1, 10, 0), utc(2026, 1, 12, 12), SAT) == 0


def test_triple_weekday_counts_three_nights_on_the_new_york_date_of_the_rollover():
    # Wed 2026-01-07 17:00 NY = 22:00 UTC (the same instant is Thursday only in UTC+2 or more)
    assert rollover_nights(utc(2026, 1, 7, 12), utc(2026, 1, 7, 23), WED) == 3
    assert rollover_nights(utc(2026, 1, 6, 12), utc(2026, 1, 7, 12), WED) == 1  # Tue
    assert rollover_nights(utc(2026, 1, 6, 12), utc(2026, 1, 8, 12), WED) == 4  # Tue + Wed
    assert rollover_nights(utc(2026, 1, 5, 12), utc(2026, 1, 5, 23), MON) == 3  # configurable
    assert rollover_nights(utc(2026, 1, 7, 12), utc(2026, 1, 7, 23), MON) == 1


def test_a_week_is_seven_nights():
    assert rollover_nights(utc(2026, 1, 5, 12), utc(2026, 1, 12, 12), WED) == 1 + 1 + 3 + 1 + 1


def test_default_triple_weekday_is_wednesday():
    assert SymbolCosts(spread=0, commission_per_lot=0, contract_size=1).swap_triple_weekday == WED


# --- engine: swap_r on the trade ----------------------------------------------------------


def test_no_rollover_inside_the_trade_has_no_swap():
    t = run(utc(2026, 1, 5, 10), 12)
    assert t.swap_r == 0.0 and t.r_net == t.r_gross


def test_one_night_long_pays_exactly_the_rate_in_r():
    t = run(utc(2026, 1, 5, 20), 24)  # exit 22:00 UTC = the rollover, which counts
    assert t.swap_r == pytest.approx(LONG_NIGHT_R)
    assert t.r_gross == pytest.approx(0.0)
    assert t.r_net == pytest.approx(t.r_gross + LONG_NIGHT_R)  # negative = cost


def test_one_night_short_uses_the_short_rate_and_a_credit_adds_to_net():
    t = run(utc(2026, 1, 5, 20), 24, direction=SHORT)
    assert t.swap_r == pytest.approx(SHORT_NIGHT_R) and t.swap_r > 0
    assert t.r_net == pytest.approx(t.r_gross + SHORT_NIGHT_R)


def test_rollover_at_the_entry_close_does_not_count():
    t = run(utc(2026, 1, 5, 21, 55), 12)  # entry close 22:00 UTC
    assert t.entry_time == utc(2026, 1, 5, 22) and t.swap_r == 0.0


def test_exit_one_candle_before_the_rollover_has_no_swap():
    assert run(utc(2026, 1, 5, 20), 23).swap_r == 0.0  # exit 21:55 UTC


def test_dst_winter_and_summer_in_the_engine():
    # 12 candles from 20:00 UTC: exit 21:00 UTC. Summer rollover 21:00 counts, winter 22:00 not.
    assert run(utc(2026, 1, 5, 20), 12).swap_r == 0.0
    assert run(utc(2026, 7, 6, 20), 12).swap_r == pytest.approx(LONG_NIGHT_R)
    # 24 candles: exit 22:00 UTC, both seasons have passed their rollover
    assert run(utc(2026, 1, 5, 20), 24).swap_r == pytest.approx(LONG_NIGHT_R)
    assert run(utc(2026, 7, 6, 20), 24).swap_r == pytest.approx(LONG_NIGHT_R)


def test_friday_to_monday_position_pays_one_night_in_the_engine():
    t = run(utc(2026, 1, 9, 20), 648)  # Fri 20:00 UTC to Mon 02:00 UTC
    assert t.swap_r == pytest.approx(LONG_NIGHT_R)


def test_triple_weekday_is_three_nights_in_the_engine():
    wed = run(utc(2026, 1, 7, 20), 24)  # Wednesday 22:00 UTC rollover
    assert wed.swap_r == pytest.approx(3 * LONG_NIGHT_R)
    tue = run(utc(2026, 1, 6, 20), 24)
    assert tue.swap_r == pytest.approx(LONG_NIGHT_R)
    monday_triple = run(utc(2026, 1, 5, 20), 24, cost=costs(symbol={"swap_triple_weekday": MON}))
    assert monday_triple.swap_r == pytest.approx(3 * LONG_NIGHT_R)


def test_swap_disabled_gives_zero_and_leaves_net_alone():
    t = run(utc(2026, 1, 5, 20), 24, cost=replace(costs(), swap_enabled=False))
    assert t.swap_r == 0.0 and t.r_net == pytest.approx(t.r_gross)


def test_swap_never_changes_gross():
    on = run(utc(2026, 1, 5, 20), 24)
    off = run(utc(2026, 1, 5, 20), 24, cost=replace(costs(), swap_enabled=False))
    assert on.r_gross == off.r_gross and on.r_net == pytest.approx(off.r_net + on.swap_r)


def test_swap_is_added_to_spread_and_commission_in_net():
    cost = CostConfig(
        symbols={
            "TEST": SymbolCosts(
                spread=0.2, commission_per_lot=4.0, contract_size=100,
                swap_long_per_lot=LONG_RATE,
            )
        }
    )  # fmt: skip
    t = run(utc(2026, 1, 5, 20), 24, cost=cost)
    spread_r, commission_r = 0.2 / 2, 4.0 / 200
    assert t.r_net == pytest.approx(t.r_gross - spread_r - commission_r + LONG_NIGHT_R)
    assert t.commission_r == pytest.approx(commission_r) and t.spread_r == pytest.approx(spread_r)


def test_default_rates_are_zero_so_nothing_changes():
    from backtester.engine.costs import DEFAULT_SYMBOL_COSTS

    assert all(
        c.swap_long_per_lot == c.swap_short_per_lot == 0 for c in DEFAULT_SYMBOL_COSTS.values()
    )
    t = run(
        utc(2026, 1, 5, 20), 24, cost=CostConfig(spread_enabled=False, commission_enabled=False)
    )
    assert t.swap_r == 0.0  # a symbol without cost settings has no swap, as without spread


def test_partial_exits_each_part_uses_its_own_exit_time_and_share():
    # TP1 (half) at 21:05 UTC before the 22:00 rollover, TP2 (half) at 22:35 after it:
    # only the second half pays its night
    ohlc = [FLAT] * 40
    ohlc[12] = (100.0, 102.2, 99.9, 100.0)  # candle 21:00-21:05: TP1 102
    ohlc[30] = (100.0, 104.2, 99.9, 100.0)  # candle 22:30-22:35: TP2 104
    series = build_series(ohlc, start=utc(2026, 1, 5, 20))
    order = {"direction": LONG, "stop_loss": 98.0, "take_profit": 102.0,
             "take_profit_2": 104.0, "tp1_share": 0.5}  # fmt: skip
    [t] = run_backtest(Scripted({0: [order]}), [series], EngineConfig(costs=costs()))
    assert [p.time for p in t.parts] == [utc(2026, 1, 5, 21, 5), utc(2026, 1, 5, 22, 35)]
    assert t.swap_r == pytest.approx(0.5 * LONG_NIGHT_R)
    assert t.r_net == pytest.approx(t.r_gross + 0.5 * LONG_NIGHT_R)


def test_partial_exits_both_after_the_rollover_pay_the_whole_night():
    ohlc = [FLAT] * 40
    ohlc[30] = (100.0, 102.2, 99.9, 100.0)
    ohlc[35] = (100.0, 104.2, 99.9, 100.0)
    series = build_series(ohlc, start=utc(2026, 1, 5, 20))
    order = {"direction": LONG, "stop_loss": 98.0, "take_profit": 102.0,
             "take_profit_2": 104.0, "tp1_share": 0.25}  # fmt: skip
    [t] = run_backtest(Scripted({0: [order]}), [series], EngineConfig(costs=costs()))
    assert t.swap_r == pytest.approx(LONG_NIGHT_R)


def test_cost_config_swap_r_unit():
    cfg = costs()
    exits = [(0.5, utc(2026, 1, 5, 12)), (0.5, utc(2026, 1, 7, 23))]
    # half pays 0 nights, half pays Mon (1) + Tue (1) + Wed (3) = 5 nights
    got = cfg.swap_r("TEST", LONG, 2.0, utc(2026, 1, 5, 11), exits)
    assert got == pytest.approx(0.5 * 5 * LONG_NIGHT_R)
