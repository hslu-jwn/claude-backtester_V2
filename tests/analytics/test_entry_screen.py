"""Entry screening battery (ROADMAP 12.12, idea T-13). Spec: risk-management.md > Entry screening."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from backtester.analytics.entry_screen import (
    EntryScreenConfig,
    M1Data,
    ScreenTrade,
    exit_after_bars,
    exit_bracket,
    judge,
    passes,
    random_exit_runs,
    rollover_schedule,
    screen_variant,
)
from backtester.core.models import Candle, Direction
from backtester.engine.costs import CostConfig, SymbolCosts, rollover_nights

MIN = timedelta(minutes=1)
LONG, SHORT = Direction.BULLISH, Direction.BEARISH
FREE = CostConfig(symbols={"X": SymbolCosts(0.0, 0.0, 1)})


def t0(day=5, hour=14, minute=5, month=1) -> datetime:
    return datetime(2026, month, day, hour, minute, tzinfo=UTC)


def m1(start: datetime, rows) -> M1Data:
    """M1 candles from (open, high, low, close) rows, the first one opening at `start`."""
    return M1Data.from_candles(
        [Candle(start + i * MIN, o, h, lo, c) for i, (o, h, lo, c) in enumerate(rows)]
    )


def flat(price: float, n: int):
    return [(price, price, price, price)] * n


def trade(direction=LONG, entry=100.0, stop=None, at=None, symbol="X", r_net=0.0, exit_time=None):
    at = at or t0()
    stop = stop if stop is not None else (entry - 2 if direction is LONG else entry + 2)
    return ScreenTrade(symbol, direction, at, entry, stop, exit_time or at + 5 * MIN, r_net)


def test_parallel_screen_matches_serial():
    data = m1(t0() - 10 * MIN, [(100, 101, 99, 100 + (i % 3) / 4) for i in range(80)])
    ts = [trade(at=t0() + i * MIN, r_net=i / 10) for i in range(4)]
    cfg = EntryScreenConfig(random_runs=12, shuffle_runs=12)
    assert screen_variant(ts, {"X": data}, 5, FREE, cfg, workers=1) == screen_variant(
        ts, {"X": data}, 5, FREE, cfg, workers=3
    )


def test_serial_screen_does_not_create_pool(monkeypatch):
    import backtester.analytics.entry_screen as module

    def forbidden(*args, **kwargs):
        pytest.fail("serial execution must not create a pool")

    monkeypatch.setattr(module, "ProcessPoolExecutor", forbidden)
    screen_variant(
        [trade()],
        {"X": m1(t0(), flat(100, 30))},
        5,
        FREE,
        EntryScreenConfig(random_runs=2, shuffle_runs=2),
        workers=1,
    )


def test_screen_worker_exception_propagates(monkeypatch):
    import backtester.analytics.entry_screen as module

    class Future:
        def result(self):
            raise RuntimeError("worker failed")

    class Pool:
        def __init__(self, *args, **kwargs):
            pass

        def submit(self, *args, **kwargs):
            return Future()

        def shutdown(self, **kwargs):
            pass

    monkeypatch.setattr(module, "ProcessPoolExecutor", Pool)
    with pytest.raises(RuntimeError, match="worker failed"):
        screen_variant(
            [trade()],
            {"X": m1(t0(), flat(100, 30))},
            5,
            FREE,
            EntryScreenConfig(random_runs=2, shuffle_runs=2),
            workers=2,
        )


# --- (a) N bars with the own stop active ------------------------------------------------------


def test_n_bar_exit_long_is_the_close_of_the_last_minute_of_bar_n():
    rows = flat(100, 3) + [(100, 104, 100, 104)] + flat(105, 20)
    data = m1(t0(), rows)  # N=2 of 5-minute bars -> deadline 14:15 -> candle 14:14 (index 9)
    res = exit_after_bars(data, trade(), 2, 5, FREE)
    assert res.exit_time == t0() + 10 * MIN and res.reason == "time"
    assert res.exit_price == 105 and res.r_gross == pytest.approx(2.5)  # (105-100)/2
    res1 = exit_after_bars(data, trade(), 1, 5, FREE)  # N=1: candle 14:09 (index 4) closes 105
    assert res1.exit_time == t0() + 5 * MIN and res1.exit_price == 105


def test_n_bar_exit_short_is_mirrored():
    rows = flat(100, 4) + [(100, 100, 96, 96)] + flat(96, 20)
    res = exit_after_bars(m1(t0(), rows), trade(SHORT), 1, 5, FREE)
    assert res.exit_price == 96 and res.r_gross == pytest.approx(2.0)  # (100-96)/2


def test_stop_hit_before_n_bars_exits_at_the_stop():
    rows = flat(100, 2) + [(100, 100, 97.5, 98.5)] + flat(100, 20)
    res = exit_after_bars(m1(t0(), rows), trade(), 5, 5, FREE)
    assert res.reason == "stop" and res.exit_price == 98 and res.r_gross == pytest.approx(-1.0)
    assert res.exit_time == t0() + 3 * MIN  # close time of the candle that hit it


def test_gap_through_the_stop_fills_at_the_open():
    rows = flat(100, 2) + [(97, 97.5, 96.5, 97)] + flat(100, 20)
    res = exit_after_bars(m1(t0(), rows), trade(), 5, 5, FREE)
    assert res.exit_price == 97 and res.r_gross == pytest.approx(-1.5)


def test_short_stop_hit_mirrored():
    rows = flat(100, 2) + [(100, 102.5, 100, 101)] + flat(100, 20)
    res = exit_after_bars(m1(t0(), rows), trade(SHORT), 5, 5, FREE)
    assert res.reason == "stop" and res.exit_price == 102 and res.r_gross == pytest.approx(-1.0)


def test_exit_uses_the_last_candle_before_a_gap_in_the_data():
    rows = flat(100, 3) + [(100, 101, 100, 101)]  # data ends after 4 minutes, 5-minute bar asked
    res = exit_after_bars(m1(t0(), rows), trade(), 1, 5, FREE)
    assert res.exit_price == 101 and res.exit_time == t0() + 4 * MIN


def test_no_candle_after_the_entry_gives_none():
    assert exit_after_bars(m1(t0() - 10 * MIN, flat(100, 5)), trade(), 1, 5, FREE) is None


# --- (b) 1R / 1R bracket ---------------------------------------------------------------------


def test_bracket_long_target_and_stop():
    up = m1(t0(), flat(100, 2) + [(100, 102.1, 100, 102)] + flat(100, 5))
    res = exit_bracket(up, trade(), FREE)
    assert res.reason == "target" and res.exit_price == 102 and res.r_gross == pytest.approx(1.0)
    down = m1(t0(), flat(100, 2) + [(100, 100, 97.9, 98)] + flat(100, 5))
    res = exit_bracket(down, trade(), FREE)
    assert res.reason == "stop" and res.r_gross == pytest.approx(-1.0)


def test_bracket_short_mirrored():
    down = m1(t0(), [(100, 100, 97.9, 98)] + flat(100, 5))
    res = exit_bracket(down, trade(SHORT), FREE)
    assert res.reason == "target" and res.exit_price == 98 and res.r_gross == pytest.approx(1.0)
    up = m1(t0(), [(100, 102.1, 100, 102)] + flat(100, 5))
    assert exit_bracket(up, trade(SHORT), FREE).r_gross == pytest.approx(-1.0)


@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_stop_and_target_in_one_candle_is_a_stop(direction):
    data = m1(t0(), flat(100, 2) + [(100, 102.5, 97.5, 100)] + flat(100, 5))
    res = exit_bracket(data, trade(direction), FREE)
    assert res.reason == "stop" and res.r_gross == pytest.approx(-1.0)


def test_bracket_unresolved_closes_at_the_last_candle():
    res = exit_bracket(m1(t0(), flat(100, 6)), trade(), FREE)
    assert res.reason == "end_of_data" and res.r_gross == 0.0 and res.exit_time == t0() + 6 * MIN


def test_bracket_target_scales_with_r():
    data = m1(t0(), [(100, 104.1, 100, 104)] + flat(100, 5))
    res = exit_bracket(data, trade(), FREE, r=2.0)
    assert res.reason == "target" and res.r_gross == pytest.approx(2.0)


# --- (d) reversed signal ------------------------------------------------------------------------


def test_reversed_mirrors_gross_and_pays_costs_again():
    costs = CostConfig(symbols={"X": SymbolCosts(0.2, 0.0, 1)})  # spread 0.2 = 0.1 R
    data = m1(t0(), flat(100, 4) + [(100, 101, 100, 101)] + flat(101, 20))  # stays inside +-1R
    fwd = exit_after_bars(data, trade(), 1, 5, costs)
    rev = exit_after_bars(data, trade(), 1, 5, costs, reverse=True)
    assert fwd.r_gross == pytest.approx(0.5) and rev.r_gross == pytest.approx(-0.5)
    assert fwd.r_net == pytest.approx(0.4) and rev.r_net == pytest.approx(-0.6)  # spread each time


def test_reversed_has_the_mirrored_stop():
    data = m1(t0(), flat(100, 2) + [(100, 102.5, 100, 102)] + flat(102, 20))
    rev = exit_after_bars(data, trade(), 5, 5, FREE, reverse=True)  # short, stop at 102
    assert rev.reason == "stop" and rev.exit_price == 102 and rev.r_gross == pytest.approx(-1.0)


def test_reversed_bracket_swaps_stop_and_target():
    data = m1(t0(), [(100, 102.1, 100, 102)] + flat(100, 5))  # the original long wins
    assert exit_bracket(data, trade(), FREE).reason == "target"
    rev = exit_bracket(data, trade(), FREE, reverse=True)
    assert rev.reason == "stop" and rev.r_gross == pytest.approx(-1.0)


def test_reversed_swap_uses_the_other_direction_rate():
    costs = CostConfig(
        symbols={"X": SymbolCosts(0.0, 0.0, 1, swap_long_per_lot=-10.0, swap_short_per_lot=-1.0)}
    )
    at = datetime(2026, 6, 11, 20, 55, tzinfo=UTC)  # Thursday; 17:00 EDT = 21:00 UTC
    data = m1(at, flat(100, 20))
    assert exit_after_bars(data, trade(at=at), 2, 5, costs).r_net == pytest.approx(-5.0)
    rev = exit_after_bars(data, trade(at=at), 2, 5, costs, reverse=True)
    assert rev.r_net == pytest.approx(-0.5)  # 1 night x -1 / risk 2


# --- swap at the 17:00 New York rollover ---------------------------------------------------------


SWAP = CostConfig(symbols={"X": SymbolCosts(0.0, 0.0, 1, swap_long_per_lot=-10.0)})


def test_swap_charged_when_the_exit_crosses_the_summer_rollover():
    at = datetime(2026, 6, 11, 20, 55, tzinfo=UTC)  # 17:00 EDT = 21:00 UTC
    res = exit_after_bars(m1(at, flat(100, 20)), trade(at=at), 2, 5, SWAP)  # exit 21:05
    assert res.swap_r == pytest.approx(-5.0) and res.r_net == pytest.approx(-5.0)  # -10 / risk 2


def test_no_swap_when_the_entry_is_after_the_rollover():
    at = datetime(2026, 6, 11, 21, 55, tzinfo=UTC)
    res = exit_after_bars(m1(at, flat(100, 20)), trade(at=at), 2, 5, SWAP)
    assert res.swap_r == 0.0


def test_winter_rollover_is_at_22_utc_and_wednesday_counts_three():
    at = datetime(2026, 1, 8, 21, 55, tzinfo=UTC)  # Thursday winter: 22:00 UTC
    assert exit_after_bars(m1(at, flat(100, 20)), trade(at=at), 2, 5, SWAP).swap_r == -5.0
    early = datetime(2026, 1, 8, 20, 55, tzinfo=UTC)  # exit 21:05 UTC: before the rollover
    assert exit_after_bars(m1(early, flat(100, 20)), trade(at=early), 2, 5, SWAP).swap_r == 0.0
    wed = datetime(2026, 1, 7, 21, 55, tzinfo=UTC)
    assert exit_after_bars(m1(wed, flat(100, 20)), trade(at=wed), 2, 5, SWAP).swap_r == -15.0


@pytest.mark.parametrize(
    "entry",
    [datetime(2026, 3, 5, 12, 0, tzinfo=UTC), datetime(2026, 11, 1, 20, 0, tzinfo=UTC),
     datetime(2026, 6, 12, 20, 0, tzinfo=UTC)],
)  # fmt: skip
def test_rollover_schedule_matches_the_engine_count(entry):
    times, cum = rollover_schedule(entry, entry + timedelta(days=9), 2)
    for hours in range(0, 9 * 24, 5):
        exit_time = entry + timedelta(hours=hours)
        k = np.searchsorted(times, exit_time.timestamp(), side="right")
        got = cum[k - 1] if k else 0
        assert got == rollover_nights(entry, exit_time, 2)


# --- (c) random time exit ------------------------------------------------------------------------


def test_random_exit_with_explicit_holds_equals_the_scalar_exit():
    costs = CostConfig(
        symbols={"X": SymbolCosts(0.3, 2.0, 1, commission_pct_per_side=0.0001,
                                  swap_long_per_lot=-3.0, swap_short_per_lot=-1.0)}
    )  # fmt: skip
    at = datetime(2026, 6, 11, 20, 50, tzinfo=UTC)
    closes = 100 + np.cumsum(np.tile([0.1, -0.05, 0.07], 40))
    rows = [(c, c + 0.2, c - 0.2, c) for c in closes]
    data = m1(at, rows)
    for direction in (LONG, SHORT):
        tr = trade(direction, entry=100.0, at=at)
        for reverse in (False, True):
            runs = random_exit_runs(data, tr, np.array([600.0, 1200.0]), costs, reverse)
            for hold_s, net, gross in zip([600, 1200], runs.net, runs.gross, strict=True):
                want = exit_after_bars(data, tr, hold_s // 300, 5, costs, reverse)
                assert net == pytest.approx(want.r_net) and gross == pytest.approx(want.r_gross)


def test_random_exit_stop_stays_active():
    rows = flat(100, 10) + [(100, 100, 97.5, 98)] + flat(100, 200)  # stop hit in minute 11
    data = m1(t0(), rows)
    runs = random_exit_runs(data, trade(), np.array([300.0, 3000.0]), FREE)
    assert runs.gross[0] == pytest.approx(0.0) and runs.gross[1] == pytest.approx(-1.0)


def test_random_exits_are_seeded_and_match_the_mean_hold():
    data = m1(t0(), flat(100, 1000))
    trades = [trade(r_net=0.0, exit_time=t0() + 60 * MIN)]
    cfg = EntryScreenConfig(random_runs=1000, shuffle_runs=10)
    a = screen_variant(trades, {"X": data}, 5, FREE, cfg)
    b = screen_variant(trades, {"X": data}, 5, FREE, cfg)
    c = screen_variant(trades, {"X": data}, 5, FREE, EntryScreenConfig(seed=7, shuffle_runs=10))
    assert a.random.mean_hold_s == 3600.0
    assert a.random.sample_mean_hold_s == b.random.sample_mean_hold_s
    assert a.random.sample_mean_hold_s == pytest.approx(a.random.mean_hold_s, rel=0.06)
    assert c.random.sample_mean_hold_s != a.random.sample_mean_hold_s


def test_random_exit_percentile_of_the_strategys_own_result():
    # flat price, no costs: every random run totals 0 R; the strategy's own +1 R beats all of them
    data = m1(t0(), flat(100, 1000))
    cfg = EntryScreenConfig(random_runs=50, shuffle_runs=5)
    good = screen_variant([trade(r_net=1.0)], {"X": data}, 5, FREE, cfg)
    assert good.random.percentile == 100.0 and good.random.median == 0.0
    tie = screen_variant([trade(r_net=0.0)], {"X": data}, 5, FREE, cfg)
    assert tie.random.percentile == 50.0  # ties count half


# --- (e) hit rate vs shuffled entry times ------------------------------------------------------------


def test_hit_rate_real_counts_and_shuffle_stays_in_the_trading_window():
    # Monday 12:00 UTC start. Price rises 1 per minute during 14:30-14:59 UTC (09:30-09:59 New
    # York, the window of the entries) and falls 1 per minute elsewhere.
    start = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
    price, rows = 1000.0, []
    for i in range(6 * 60):
        ts = start + i * MIN
        step = 1.0 if (ts.hour == 14 and ts.minute >= 30) else -1.0
        new = price + step
        rows.append((price, max(price, new), min(price, new), new))
        price = new
    data = m1(start, rows)
    at = datetime(2026, 1, 5, 14, 40, tzinfo=UTC)
    entry = rows[(at - start) // MIN - 1][3]  # close of the candle that ends at 14:40
    trades = [trade(LONG, entry=entry, stop=entry - 1000, at=at),
              trade(LONG, entry=entry, stop=entry - 1000, at=at + 5 * MIN)]  # fmt: skip
    cfg = EntryScreenConfig(bars=(1,), random_runs=5, shuffle_runs=50)
    res = screen_variant(trades, {"X": data}, 1, FREE, cfg)
    row = res.hit_rows[0]
    assert row["real_hit_rate"] == 1.0 and row["trades"] == 2
    # entries shuffled inside 14:30-14:59 UTC always rise; outside the window price falls
    assert row["shuffled_mean"] == pytest.approx(1.0)


def test_hit_rate_ties_and_wrong_direction_are_misses():
    start = datetime(2026, 1, 5, 14, 0, tzinfo=UTC)
    data = m1(start, flat(100, 60))  # nothing moves
    at = datetime(2026, 1, 5, 14, 20, tzinfo=UTC)
    res = screen_variant(
        [trade(LONG, entry=100, at=at)], {"X": data}, 5, FREE,
        EntryScreenConfig(bars=(1,), random_runs=3, shuffle_runs=10),
    )  # fmt: skip
    row = res.hit_rows[0]
    assert row["real_hit_rate"] == 0.0 and row["shuffled_mean"] == 0.0 and row["z"] == 0.0


# --- cells, halves, long / short ---------------------------------------------------------------------


def test_cells_report_trades_win_rate_splits_and_halves():
    start = datetime(2026, 1, 5, 14, 0, tzinfo=UTC)
    rows = flat(100, 30) + [(100, 101, 100, 101)] + flat(101, 3000)  # 100, then 101 from 14:30
    data = m1(start, rows)
    at1 = start + 25 * MIN
    at2 = start + timedelta(days=2) + 25 * MIN
    trades = [
        trade(LONG, 100, 98, at1), trade(SHORT, 100, 102, at1),
        trade(LONG, 101, 99, at2), trade(SHORT, 101, 103, at2),
    ]  # fmt: skip
    cfg = EntryScreenConfig(bars=(1,), random_runs=2, shuffle_runs=2)
    res = screen_variant(trades, {"X": data}, 10, FREE, cfg, period=(at1.date(), at2.date()))
    cell = res.cells[0]
    assert cell["bars"] == 1 and cell["trades"] == 4
    assert cell["long_trades"] == 2 and cell["short_trades"] == 2
    assert cell["long_mean_net"] == pytest.approx(0.25)  # first long +0.5, second 0
    assert cell["short_mean_net"] == pytest.approx(-0.25)
    assert cell["first_half_trades"] == 2 and cell["second_half_trades"] == 2
    assert cell["first_half_mean_net"] == pytest.approx(0.0)
    assert cell["win_rate"] == pytest.approx(0.25)  # only the first long is positive
    assert cell["rev_mean_net"] == pytest.approx(0.0)


def test_trades_without_data_are_counted_as_skipped():
    data = m1(t0() - 60 * MIN, flat(100, 10))
    cfg = EntryScreenConfig(bars=(1,), random_runs=2, shuffle_runs=2)
    res = screen_variant([trade()], {"X": data}, 5, FREE, cfg)
    assert res.skipped == 1 and res.cells[0]["trades"] == 0


# --- no lookahead ------------------------------------------------------------------------------------


def test_exit_uses_only_candles_after_the_entry_and_up_to_the_deadline():
    base = flat(100, 3) + [(100, 101, 100, 101)] + flat(101, 30)
    before = [(100, 200, 1, 100)]  # a wild candle that closed before the entry
    junk = [(101, 500, 1, 3)] * 5  # candles from the deadline on
    a = exit_after_bars(m1(t0(), base), trade(), 1, 5, FREE)
    b = exit_after_bars(m1(t0() - MIN, before + base), trade(), 1, 5, FREE)
    c = exit_after_bars(m1(t0(), base[:5] + junk), trade(), 1, 5, FREE)
    assert (a.exit_price, a.r_gross) == (b.exit_price, b.r_gross) == (101, 0.5)
    assert c.exit_price == 101 and c.exit_time == t0() + 5 * MIN


def test_changing_candles_after_the_exit_never_changes_the_result():
    rows = flat(100, 3) + [(100, 101, 100, 101)] + flat(101, 30)
    one = exit_after_bars(m1(t0(), rows), trade(), 1, 5, FREE)
    two = exit_after_bars(m1(t0(), rows[:5] + [(50, 999, 1, 7)] * 25), trade(), 1, 5, FREE)
    assert one == two


# --- the pass rule ------------------------------------------------------------------------------------


def test_cell_share_boundary_69_9_vs_70_percent():
    cfg = EntryScreenConfig()
    ok, why = passes(0.70, 0.60, 95.0, cfg)
    assert ok and not why
    ok, why = passes(0.699, 0.60, 95.0, cfg)
    assert not ok and any("cells" in w for w in why)


def test_win_rate_boundary_52_percent():
    cfg = EntryScreenConfig()
    assert passes(0.8, 0.52, 95.0, cfg)[0]
    ok, why = passes(0.8, 0.5199, 95.0, cfg)
    assert not ok and any("win rate" in w for w in why)


def test_random_percentile_must_be_above_the_90th():
    cfg = EntryScreenConfig()
    assert passes(0.8, 0.6, 90.1, cfg)[0]
    ok, why = passes(0.8, 0.6, 90.0, cfg)
    assert not ok and any("percentile" in w for w in why)


def test_all_failing_reasons_are_listed():
    ok, why = passes(0.1, 0.4, 10.0, EntryScreenConfig())
    assert not ok and len(why) == 3


def test_judge_pools_cells_over_variants_and_trades_for_the_win_rate():
    data = m1(t0(), flat(100, 400))
    cfg = EntryScreenConfig(bars=(1, 2), random_runs=5, shuffle_runs=5)
    v = screen_variant([trade(r_net=1.0)], {"X": data}, 5, FREE, cfg, label="a")
    verdict = judge([v, v], cfg)
    assert verdict.cells == 4 and verdict.cells_positive == 0
    assert verdict.passed is False and verdict.bracket_win_rate == 0.0


def test_random_exit_includes_the_currency_conversion_like_the_fixed_exit():
    costs = CostConfig(symbols={"X": SymbolCosts(0.0, 0.0, 1, profit_currency="JPY")})
    rows = flat(100, 3) + [(100, 102.1, 100, 102)] + flat(102, 40)  # +1R gross
    data = m1(t0(), rows)
    fixed = exit_after_bars(data, trade(), 2, 5, costs)
    runs = random_exit_runs(data, trade(), np.array([600.0]), costs)
    assert fixed.r_gross == pytest.approx(1.0) and fixed.r_net == pytest.approx(0.993)
    assert runs.net[0] == pytest.approx(fixed.r_net)
