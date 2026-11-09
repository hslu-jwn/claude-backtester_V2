"""Hand-built M1 tests. Spec: strategy-h1-shock.md (including Opus decisions)."""
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, time, timedelta
from math import exp, log
from zoneinfo import ZoneInfo

import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.engine.trade import ExitReason
from backtester.strategy.h1_shock.config import H1ShockConfig
from backtester.strategy.h1_shock.strategy import H1Shock

M1 = Timeframe.M1
LONDON = ZoneInfo("Europe/London")
NY = ZoneInfo("America/New_York")
COSTS = CostConfig(symbols={"GBPUSD": SymbolCosts(.01, 0, 1)},
                   spread_price_scaling=False, spread_table=None, round_to_tick=False)


def hour(day, hh=10, ret=.001, tz=LONDON, missing=(), flat=0):
    """H1 open 100, close 100*exp(ret), range [99, 111]; never stale unless requested."""
    start = datetime.combine(day, time(hh), tzinfo=tz).astimezone(UTC)
    out = []
    for m in range(60):
        if m in missing:
            continue
        close = 100 * exp(ret) if m == 59 else 100
        o, h, lo = 100, max(111, close), min(99, close)
        if 10 <= m < 10 + flat:
            o = h = lo = close = 100
        out.append(Candle(start + timedelta(minutes=m), o, h, lo, close))
    return out


def days(n=61, start=date(2026, 1, 5)):
    out = []
    while len(out) < n:
        if start.weekday() < 5:
            out.append(start)
        start += timedelta(days=1)
    return out


def history(ret=.05, **kw):
    ds = days()
    bars = [c for i, d in enumerate(ds[:60])
            for c in hour(d, ret=(-.001 if i % 2 == 0 else .001))]
    return bars + hour(ds[-1], ret=ret, **kw)


def feed(bars, strategy=None):
    s = strategy or H1Shock("GBPUSD")
    s.configure_costs(COSTS)
    series = CandleSeries(s.symbol, M1, bars)
    orders, exits = {}, {}
    for i, c in enumerate(bars):
        found = s.on_candle(c.ts + M1.duration, {M1: series.view(i)})
        if found:
            orders[i] = found
        closed = s.exits()
        if closed:
            exits[i] = closed
    return s, orders, exits


@pytest.mark.parametrize("mode,ret,side", [
    ("CONTINUATION", .05, Direction.BULLISH),
    ("CONTINUATION", -.05, Direction.BEARISH),
    ("REVERSAL", .05, Direction.BEARISH),
    ("REVERSAL", -.05, Direction.BULLISH),
])
def test_event_signal_close_both_modes_and_fixed_stop(mode, ret, side):
    bars = history(ret)
    s, orders, _ = feed(bars, H1Shock("GBPUSD", H1ShockConfig(response_mode=mode)))
    assert list(orders) == [len(bars) - 1]
    [o] = orders[len(bars) - 1]
    assert o.direction is side
    assert o.entry == pytest.approx(100 * exp(ret))
    tr = max(111, o.entry) - min(99, o.entry)
    atr = (19 * 12 + tr) / 20
    assert abs(o.entry - o.stop_loss) == pytest.approx(6 * atr)
    assert o.take_profit is None
    assert s.signals[-1]["robust_z"] == pytest.approx(ret / (1.4826 * .001))


def test_past_only_normalization_and_future_append_invariance():
    bars = history()
    future = hour(days()[-1], 11, ret=.5)
    _, prefix, _ = feed(bars)
    _, full, _ = feed(bars + future)
    assert prefix == {i: orders for i, orders in full.items() if i < len(bars)}
    assert feed(bars[:-1])[1] == {}
    assert prefix


@pytest.mark.parametrize("missing,flat,valid", [
    ((), 0, True), ((5, 6, 7, 8, 9), 0, True),
    ((5, 6, 7, 8, 9, 10), 0, False), ((0,), 0, False), ((59,), 0, False),
    ((), 14, True), ((), 15, False),
])
def test_integrity_boundary_missing_tolerance_and_stale(missing, flat, valid):
    _, orders, _ = feed(history(missing=missing, flat=flat))
    assert bool(orders) is valid


def test_invalid_baseline_bar_does_not_count_toward_sixty():
    bars = history()
    del bars[10]  # a tolerable interior gap still counts
    assert feed(bars)[1]
    del bars[0]  # missing first candle invalidates one W60 observation
    assert not feed(bars)[1]


def test_zero_mad_zero_return_and_insufficient_history():
    ds = days()
    bars = [c for d in ds[:60] for c in hour(d, ret=.001)]
    assert not feed(bars + hour(ds[-1], ret=.05))[1]
    assert not feed(history(ret=0))[1]
    assert not feed(history()[60:])[1]


@pytest.mark.parametrize("h", [1, 2, 3])
def test_engine_time_exit_exact_h_hours(h):
    bars = history() + [c for hh in range(11, 11 + h) for c in hour(days()[-1], hh)]
    s = H1Shock("GBPUSD", H1ShockConfig(holding_hours=h))
    [trade] = run_backtest(s, [CandleSeries("GBPUSD", M1, bars)], EngineConfig(costs=COSTS))
    assert trade.exit_time - trade.entry_time == timedelta(hours=h)
    assert trade.exit_reason is ExitReason.SIGNAL
    assert trade.exit_price == pytest.approx(100 * exp(.001))


def test_cost_floor_uses_engine_costs_and_skips_zero_denominator():
    bars = history()
    costly = replace(COSTS, symbols={"GBPUSD": SymbolCosts(2, 0, 1)})
    for costs in (costly, replace(COSTS, spread_enabled=False)):
        s = H1Shock("GBPUSD")
        assert not run_backtest(s, [CandleSeries("GBPUSD", M1, bars)], EngineConfig(costs=costs))


@pytest.mark.parametrize("early_stop", [False, True])
def test_one_position_and_cooldown_persist_after_stop(early_stop):
    ds = days()
    bars = [c for i, day in enumerate(ds[:60]) for hh in (10, 11)
            for c in hour(day, hh, ret=(-.001 if i % 2 == 0 else .001))]
    first_signal = len(bars) + 59
    bars += hour(ds[-1], 10, ret=.05) + hour(ds[-1], 11, ret=.05)
    s = H1Shock("GBPUSD", H1ShockConfig(holding_hours=3))
    s.configure_costs(COSTS)
    series = CandleSeries("GBPUSD", M1, bars)
    found = []
    for i, c in enumerate(bars):
        out = s.on_candle(c.ts + M1.duration, {M1: series.view(i)})
        found += out
        if out and early_stop:
            s.on_trade_closed(out[0].ref, None)
    assert len(found) == 1
    assert s.cooldown_until == bars[first_signal].ts + timedelta(minutes=1, hours=3)


@pytest.mark.parametrize("symbol,tz,day,start,h,eligible", [
    ("NAS100", NY, date(2026, 1, 5), 9, 1, False),
    ("US500", NY, date(2026, 1, 5), 10, 1, True),
    ("US500", NY, date(2026, 1, 5), 14, 1, False),
    ("US500", NY, date(2026, 1, 5), 15, 1, False),
    ("US500", NY, date(2026, 1, 19), 10, 1, False),  # MLK full closure
    ("US500", NY, date(2026, 11, 27), 10, 1, False),  # early close
    ("GBPUSD", LONDON, date(2026, 1, 5), 8, 1, True),  # old mask superseded
    ("GBPJPY", LONDON, date(2026, 1, 5), 19, 1, True),
    ("XAUUSD", LONDON, date(2026, 1, 5), 20, 1, False),
    ("GBPUSD", LONDON, date(2026, 1, 5), 21, 1, False),
    ("GBPUSD", LONDON, date(2026, 1, 4), 22, 1, False),
    ("GBPUSD", LONDON, date(2026, 1, 3), 10, 1, False),
    ("GBPUSD", LONDON, date(2026, 1, 5), 0, 1, True),
])
def test_session_exclusions(symbol, tz, day, start, h, eligible):
    s = H1Shock(symbol)
    begin = datetime.combine(day, time(start), tzinfo=tz).astimezone(UTC)
    assert s.eligible_interval(begin, begin + timedelta(hours=1 + h)) is eligible


@pytest.mark.parametrize("symbol,tz,winter_utc,summer_utc", [
    ("GBPUSD", LONDON, 10, 9), ("NAS100", NY, 15, 14),
])
def test_dst_clocks_and_transition_days(symbol, tz, winter_utc, summer_utc):
    s = H1Shock(symbol)
    for day, utc_hour in [(date(2026, 1, 5), winter_utc), (date(2026, 6, 1), summer_utc)]:
        begin = datetime.combine(day, time(10), tzinfo=tz).astimezone(UTC)
        assert begin.hour == utc_hour
        assert s.eligible_interval(begin, begin + timedelta(hours=2))
    transition = date(2026, 3, 29) if tz == LONDON else date(2026, 3, 8)
    begin = datetime.combine(transition, time(0), tzinfo=tz).astimezone(UTC)
    assert not s.eligible_interval(begin, begin + timedelta(hours=2))


def test_later_data_defect_keeps_trade_and_reports_missing_exit():
    bars = history() + hour(days()[-1], 11, missing=range(50, 60)) + hour(days()[-1], 12)
    s = H1Shock("GBPUSD")
    [t] = run_backtest(s, [CandleSeries("GBPUSD", M1, bars)], EngineConfig(costs=COSTS))
    assert t.exit_time > t.entry_time + timedelta(hours=1)
    assert any("missing_exit" in r["defects"] for r in s.session_records())


def test_data_ending_before_planned_exit_keeps_trade_and_reports_defect():
    s = H1Shock("GBPUSD")
    [t] = run_backtest(s, [CandleSeries("GBPUSD", M1, history())], EngineConfig(costs=COSTS))
    assert t.exit_reason is ExitReason.END_OF_DATA
    assert any("missing_exit" in r["defects"] for r in s.session_records())


def test_gap_ending_on_stop_candle_is_reported_before_engine_close_callback():
    rest = hour(days()[-1], 11, missing=range(6))
    rest[0] = replace(rest[0], low=1)
    s = H1Shock("GBPUSD")
    [t] = run_backtest(s, [CandleSeries("GBPUSD", M1, history() + rest)],
                       EngineConfig(costs=COSTS))
    assert t.exit_reason is ExitReason.STOP_LOSS
    assert any("missing_run" in r["defects"] for r in s.session_records())


@pytest.mark.parametrize("kwargs", [
    {"response_mode": "other"}, {"event_z_threshold": 0}, {"event_z_threshold": float("nan")},
    {"holding_hours": 0}, {"holding_hours": 4}, {"same_clock_lookback": 0},
    {"atr_period_h1": 0}, {"stop_atr_multiplier": -1},
])
def test_frozen_validated_config(kwargs):
    with pytest.raises(ValueError):
        H1ShockConfig(**kwargs)
    with pytest.raises(FrozenInstanceError):
        H1ShockConfig().holding_hours = 2


def test_default_parameters_and_symbol_validation():
    c = H1ShockConfig()
    assert (c.event_z_threshold, c.holding_hours, c.same_clock_lookback) == (3, 1, 60)
    assert (c.atr_period_h1, c.stop_atr_multiplier, c.minimum_event_cost_multiple) == (20, 6, 5)
    with pytest.raises(ValueError):
        H1Shock("EURUSD")
    assert log(exp(.05)) == pytest.approx(.05)


def test_session_records_follow_runner_contract():
    from backtester.runner import session_label

    s, _, _ = feed(history())
    [record] = s.session_records()
    assert datetime.fromisoformat(record["start"]) < datetime.fromisoformat(record["end"])
    assert record["symbol"] == "GBPUSD"
    assert session_label(record).startswith("h1_shock")


def test_signal_cost_converts_commission_and_slippage_to_one_way_price_units():
    s = H1Shock("GBPUSD")
    costs = replace(COSTS, symbols={"GBPUSD": SymbolCosts(.2, .4, 2, slippage=.3)})
    s.configure_costs(costs)
    assert s.signal_price_cost("GBPUSD", datetime(2026, 1, 5, tzinfo=UTC), 100) == (
        pytest.approx(.2 + .1 + .3))


def test_grid_has_exactly_the_json_cartesian_product_without_running_it():
    from pathlib import Path

    from backtester.tools.research_grid import family_variants, load_grid

    spec = load_grid(Path("research/grids/h1_shock.toml"))
    variants = list(family_variants(spec))
    assert len(variants) == 18
    assert {(v.overrides["response_mode"], v.overrides["event_z_threshold"],
             v.overrides["holding_hours"]) for v in variants} == {
        (mode, k, h) for mode in ("CONTINUATION", "REVERSAL")
        for k in (2., 3., 4.) for h in (1, 2, 3)}
    assert not spec.monkeys and not spec.sensitivity and not spec.entry_screen


def test_prior_large_returns_and_entry_excluded_hours_remain_in_w60():
    bars = history()
    bars[:60] = hour(days()[0], ret=.2)
    assert feed(bars)[1]  # exactly 60 earlier observations, including the .2 outlier
    excluded = [c for i, d in enumerate(days()[:60])
                for c in hour(d, 20, ret=(-.001 if i % 2 == 0 else .001))]
    s, orders, _ = feed(excluded)
    assert not orders
    assert len(s._window[20]) == 60  # structurally valid, but a 1h hold would cross 21:00


def test_stale_run_outside_expected_session_cannot_invalidate_next_open():
    ds = days()
    bars = [c for i, d in enumerate(ds[:60])
            for c in hour(d, 0, ret=(-.001 if i % 2 == 0 else .001))]
    previous = datetime.combine(ds[-1], time(), tzinfo=LONDON).astimezone(UTC) - HOUR
    bars += [Candle(previous + timedelta(minutes=m), 100, 100, 100, 100) for m in range(60)]
    bars += hour(ds[-1], 0, ret=.05, flat=14)
    assert feed(bars)[1]


HOUR = timedelta(hours=1)
