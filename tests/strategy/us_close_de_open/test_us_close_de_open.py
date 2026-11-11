"""Hand-built close-time fixtures. Spec: strategy-us_close_de_open.md › Definitions."""

import tomllib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest
from conftest import build_candles

from backtester.core.market import MarketView
from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import Backtest, EngineConfig
from backtester.engine.costs import CostConfig
from backtester.engine.market_replay import MarketReplay
from backtester.engine.trade import ExitReason
from backtester.strategy.base import MarketAwareStrategy
from backtester.strategy.us_close_de_open import UsCloseDeOpen, UsCloseDeOpenConfig

MINUTE = timedelta(minutes=1)
MONDAY = date(2019, 3, 18)
FRIDAY = date(2019, 3, 15)


def close_at(day, clock, zone="Europe/Berlin"):
    return datetime.combine(day, clock, ZoneInfo(zone)).astimezone(UTC)


def bar(day, clock, price=100, zone="Europe/Berlin", high=None, low=None):
    return build_candles(
        [(price, high if high is not None else price + 1,
          low if low is not None else price - 1, price)],
        Timeframe.M1, close_at(day, clock, zone) - MINUTE,
    )[0]


def previous_weekday(day):
    day -= timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def primary(day=MONDAY, cfg=None, sessions=14, entry=True, exit_clock=None):
    cfg = cfg or UsCloseDeOpenConfig()
    days, prior = [], day
    for _ in range(sessions):
        prior = previous_weekday(prior)
        days.append(prior)
    candles = []
    # Every finished daily TR is exactly 105 - 95 = 10; Wilder ATR(14) = 10.
    for prior in reversed(days):
        for clock in (time(cfg.atr_open.hour, cfg.atr_open.minute + 1), cfg.atr_close):
            candles.append(bar(prior, clock, zone=cfg.atr_zone, high=105, low=95))
    candles.append(bar(day, (datetime.combine(day, cfg.entry_time) - MINUTE).time(),
                       zone=cfg.zone))
    if entry:
        candles.append(bar(day, cfg.entry_time, zone=cfg.zone))
    candles.append(bar(day, exit_clock or cfg.exit_time, price=102, zone=cfg.zone))
    return CandleSeries("UK100" if cfg.zone == "Europe/London" else "GER40",
                        Timeframe.M1, candles)


def signal(day=FRIDAY, end=100.2, cfg=None, missing=None, extra=()):
    cfg = cfg or UsCloseDeOpenConfig()
    candles = [bar(day, clock, price, cfg.ref_zone)
               for clock, price in ((cfg.ref_from, 100), (cfg.ref_to, end))
               if clock != missing]
    return CandleSeries(cfg.ref_symbol, Timeframe.M1,
                        sorted([*candles, *extra], key=lambda c: c.ts))


def replay(cfg=None, traded=None, reference=None, day=MONDAY):
    cfg = cfg or UsCloseDeOpenConfig()
    traded = primary(day, cfg) if traded is None else traded
    reference = signal(previous_weekday(day), cfg=cfg) if reference is None else reference
    strategy = UsCloseDeOpen(traded.symbol, cfg)
    market = MarketReplay(strategy.references, [reference])
    orders, exits, entry_snapshots = [], [], []
    for index in range(len(traded)):
        view = traded.view(index)
        now = view.current.ts + MINUTE
        snapshot = market.advance(now)
        if now.astimezone(ZoneInfo(cfg.zone)).time() == cfg.entry_time:
            entry_snapshots.append(snapshot)
        orders.extend((now, order) for order in
                      strategy.on_market_candle(now, {Timeframe.M1: view}, snapshot))
        exits.extend((now, ref) for ref in strategy.exits())
    return strategy, orders, exits, entry_snapshots


@pytest.mark.parametrize("end,expected", [
    (100.2, Direction.BULLISH), (99.8, Direction.BEARISH),
    (100.1, Direction.BULLISH), (99.9, Direction.BEARISH),
    (100.099, None), (99.901, None), (100, None),
])
def test_threshold_equality_and_below(end, expected):
    _, orders, _, _ = replay(reference=signal(end=end))
    assert [order.direction for _, order in orders] == ([] if expected is None else [expected])
    if orders:
        order = orders[0][1]
        assert order.entry == 100
        assert order.stop_loss == (95 if expected is Direction.BULLISH else 105)
        assert order.take_profit is None


def test_no_lookahead_future_append_and_same_day_signal():
    first = replay()
    future = [bar(MONDAY, time(15, 30), 100, "America/New_York"),
              bar(MONDAY, time(16), 50, "America/New_York")]
    other = replay(reference=signal(extra=future))
    assert other[1:3] == first[1:3]
    for snapshot in other[3]:
        view = snapshot.views["US500"][Timeframe.M1]
        assert all(c.ts + MINUTE <= snapshot.now for c in view)
        assert view.current.ts + MINUTE == close_at(FRIDAY, time(16), "America/New_York")
    only_today = CandleSeries("US500", Timeframe.M1, future)
    assert replay(reference=only_today)[1] == []


def test_monday_uses_friday_even_with_opposite_thursday():
    thursday = [bar(date(2019, 3, 14), time(15, 30), 100, "America/New_York"),
                bar(date(2019, 3, 14), time(16), 99, "America/New_York")]
    assert replay(reference=signal(extra=thursday))[1][0][1].direction is Direction.BULLISH


@pytest.mark.parametrize("day,status", [
    (FRIDAY, "closed"), (MONDAY, "closed"),
    (FRIDAY, "early_close_13:00"), (MONDAY, "early_close_13:00"),
])
@pytest.mark.parametrize("direction", ["with_ref", "long", "short"])
def test_both_days_must_be_full_nyse_sessions(tmp_path, day, status, direction):
    (tmp_path / "nyse_holidays.csv").write_text(f"date,type\n{day},{status}\n")
    cfg = UsCloseDeOpenConfig(calendar_dir=str(tmp_path), direction=direction)
    assert replay(cfg)[1] == []
    assert len(replay(replace(cfg, skip_nyse_short_days=False))[1]) == 1


def test_tuesday_after_closed_monday_does_not_roll_back_to_friday():
    # Memorial Day Monday 2019-05-27 is closed in the shipped calendar.
    assert replay(day=date(2019, 5, 28))[1] == []


@pytest.mark.parametrize("missing", [time(15, 30), time(16)])
def test_missing_signal_endpoint_has_no_neighbour_fallback(missing):
    neighbours = [bar(FRIDAY, (datetime.combine(FRIDAY, missing) + MINUTE).time(),
                      102, "America/New_York")]
    assert replay(reference=signal(missing=missing, extra=neighbours))[1] == []


def test_no_reference_and_no_entry_candle():
    assert replay(reference=CandleSeries("US500", Timeframe.M1, []))[1] == []
    assert replay(traded=primary(entry=False))[1] == []


@pytest.mark.parametrize("day", [date(2019, 3, 12), date(2019, 3, 18), date(2019, 3, 29)])
def test_dst_mismatch_uses_new_york_local_closes(day):
    ds = previous_weekday(day)
    # During the mismatch, 16:00 NY is 20:00 UTC, not the winter 21:00 UTC.
    wrong = [bar(ds, time(20, 30), 100, "UTC"), bar(ds, time(21), 90, "UTC")]
    _, orders, _, _ = replay(day=day, reference=signal(ds, extra=wrong))
    assert orders[0][1].direction is Direction.BULLISH
    assert orders[0][0] == close_at(day, time(9))


def test_no_trade_before_fourteen_finished_regular_sessions():
    assert replay(traded=primary(sessions=13))[1] == []
    assert len(replay(traded=primary(sessions=14))[1]) == 1
    # A previous session missing its exact 17:30 close cannot seed the 14th TR.
    series = primary()
    candles = [series.view(i).current for i in range(len(series))]
    candles.pop(27)
    assert replay(traded=CandleSeries("GER40", Timeframe.M1, candles))[1] == []


def test_wilder_update_and_entry_candle_excluded_from_atr():
    cfg = UsCloseDeOpenConfig(atr_period=2)
    series = primary(cfg=cfg, sessions=3)
    candles = [series.view(i).current for i in range(len(series))]
    # First two finished TRs = 10; third = 20. Wilder(2) = (10 + 20) / 2 = 15.
    candles[4] = replace(candles[4], high=110, low=90)
    candles[7] = replace(candles[7], high=1000, low=1)  # entry close remains 100
    orders = replay(cfg, traded=CandleSeries("GER40", Timeframe.M1, candles))[1]
    assert len(orders) == 1
    assert orders[0][1].stop_loss == 92.5  # 100 - 0.5 * 15, unaffected by entry range


def test_atr_close_tolerance_can_accept_last_minute_before_session_close():
    series = primary()
    candles = [series.view(i).current for i in range(len(series))]
    candles[27] = replace(candles[27], ts=candles[27].ts - MINUTE)
    traded = CandleSeries("GER40", Timeframe.M1, candles)
    assert replay(traded=traded)[1] == []
    cfg = UsCloseDeOpenConfig(atr_close_tolerance_min=1)
    assert replay(cfg, traded=traded)[1][0][1].stop_loss == 95


def test_optional_stale_status_does_not_block_exact_signal_candles():
    strategy = UsCloseDeOpen("GER40")
    # Force a freshness failure while preserving the real signal candles. U2 says
    # optional readiness is never an entry condition; only the endpoints decide.
    reference = replace(strategy.references[0], max_age=timedelta(0))
    market = MarketReplay((reference,), [signal()])
    traded = primary()
    orders = []
    for i in range(len(traded)):
        view = traded.view(i)
        now = view.current.ts + MINUTE
        snapshot = market.advance(now)
        if now == close_at(MONDAY, time(9)):
            assert snapshot.availability["US500"][Timeframe.M1].ready is False
            assert snapshot.ready is True
        orders.extend(strategy.on_market_candle(now, {Timeframe.M1: view}, snapshot))
    assert len(orders) == 1 and orders[0].direction is Direction.BULLISH


@pytest.mark.parametrize("day", [date(2019, 3, 16), date(2019, 3, 17)])
def test_weekend_entry_is_never_traded(day):
    assert replay(day=day)[1] == []


@pytest.mark.parametrize("exit_clock", [time(9, 30), time(9, 31)])
def test_engine_entry_stop_and_timed_exit(exit_clock):
    strategy = UsCloseDeOpen("GER40")
    engine = Backtest(
        strategy, [primary(exit_clock=exit_clock)],
        EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False),
                     break_even_at_next_session=False),
        market=MarketReplay(strategy.references, [signal()]),
    )
    trades = engine.run()
    assert len(trades) == 1
    trade = trades[0]
    assert trade.entry_time == close_at(MONDAY, time(9))
    assert trade.entry == 100 and trade.initial_stop == 95
    assert trade.exit_time == close_at(MONDAY, exit_clock)
    assert trade.exit_price == 102 and trade.r_gross == pytest.approx(0.4)
    assert trade.exit_reason is ExitReason.SIGNAL
    assert not engine.market_blocked


@pytest.mark.parametrize("direction,expected", [("long", Direction.BULLISH),
                                                ("short", Direction.BEARISH)])
def test_controls_need_no_us500_data(direction, expected):
    cfg = UsCloseDeOpenConfig(direction=direction)
    empty = CandleSeries("US500", Timeframe.M1, [])
    assert replay(cfg, reference=empty)[1][0][1].direction is expected
    assert replay(cfg, reference=empty, day=date(2019, 5, 28))[1] == []
    strategy = UsCloseDeOpen("GER40", cfg)
    trades = Backtest(strategy, [primary(cfg=cfg)],
                      EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False)),
                      market=MarketReplay(strategy.references, [empty])).run()
    assert len(trades) == 1


def test_reference_is_not_touched_outside_entry_or_in_controls():
    class Untouchable(dict):
        def __getitem__(self, key):
            pytest.fail("reference view touched outside a signal entry")

        def get(self, *args):
            pytest.fail("reference view touched outside a signal entry")

    for direction in ("with_ref", "long"):
        cfg = UsCloseDeOpenConfig(direction=direction)
        series = primary(cfg=cfg)
        strategy = UsCloseDeOpen("GER40", cfg)
        for i in range(len(series)):
            view = series.view(i)
            now = view.current.ts + MINUTE
            if direction == "with_ref" and now == close_at(MONDAY, time(9)):
                continue
            strategy.on_market_candle(now, {Timeframe.M1: view},
                                      MarketView(now, Untouchable(), {}, {}, True, ()))


def test_one_trade_per_day_even_after_stop_or_skipped_order():
    for skipped in (False, True):
        strategy, orders, _, snapshots = replay()
        now, order = orders[0]
        if skipped:
            strategy.on_order_skipped(order.ref, now)
        else:
            strategy.on_trade_closed(order.ref, None)
        series = primary()
        entry = series.view(len(series) - 2)
        assert strategy.on_market_candle(now, {Timeframe.M1: entry}, snapshots[0]) == []


@pytest.mark.parametrize("kwargs", [
    {"direction": "random"}, {"exit_time": time(9)}, {"exit_time": time(8)},
    {"stop_atr": 0}, {"stop_atr": -1}, {"stop_atr": float("nan")},
    {"stop_atr": float("inf")}, {"min_ref_return_pct": -0.1},
    {"min_ref_return_pct": float("nan")}, {"atr_period": 0}, {"atr_period": 1.5},
    {"atr_close": time(8)}, {"atr_close_tolerance_min": -1},
    {"ref_to": time(15)}, {"ref_symbol": ""},
])
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        UsCloseDeOpenConfig(**kwargs)


@pytest.mark.parametrize("field", ["zone", "atr_zone", "ref_zone"])
def test_unknown_zone(field):
    with pytest.raises(ZoneInfoNotFoundError):
        UsCloseDeOpenConfig(**{field: "Unknown/Nowhere"})


def test_frozen_config_and_reference_declaration():
    cfg = UsCloseDeOpenConfig(ref_symbol="SPX500")
    with pytest.raises(FrozenInstanceError):
        cfg.stop_atr = 2
    strategy = UsCloseDeOpen("GER40", cfg)
    assert isinstance(strategy, MarketAwareStrategy)
    assert strategy.base_timeframe is Timeframe.M1
    assert strategy.timeframes == (Timeframe.M1,)
    assert strategy.uses_session_break_even is False
    assert strategy.min_warmup_days == 30
    ref, = strategy.references
    assert ref.symbol == "SPX500" and ref.role == "signal"
    assert ref.timeframes == (Timeframe.M1,)
    assert ref.required is False and ref.max_age == timedelta(days=7)
    assert replay(cfg, reference=signal(cfg=cfg))[1][0][1].direction is Direction.BULLISH


def test_uk100_london_entry_and_atr():
    cfg = UsCloseDeOpenConfig(zone="Europe/London", atr_zone="Europe/London",
                             entry_time=time(8), exit_time=time(8, 30),
                             atr_open=time(8), atr_close=time(16, 30))
    _, orders, exits, _ = replay(cfg)
    assert orders[0][0] == close_at(MONDAY, time(8), "Europe/London")
    assert orders[0][1].direction is Direction.BULLISH
    assert orders[0][1].stop_loss == 95
    assert exits == [(close_at(MONDAY, time(8, 30), "Europe/London"), orders[0][1].ref)]


def test_grids_match_config_and_separate_uk_breadth():
    root = Path(__file__).resolve().parents[3]
    for suffix, symbol, zone, entry, exits in (
        ("", "GER40", "Europe/Berlin", "09:00", ["09:30", "10:00"]),
        ("_uk", "UK100", "Europe/London", "08:00", ["08:30", "09:00"]),
    ):
        data = tomllib.loads((root / f"research/grids/us_close_de_open{suffix}.toml")
                             .read_text(encoding="utf-8"))
        assert data["symbols"] == [symbol] and data["min_trades"] == 200
        assert data["base"]["zone"] == data["base"]["atr_zone"] == zone
        assert data["base"]["entry_time"] == entry
        assert [g["name"] for g in data["grids"]] == ["S", "C"]
        for family in data["grids"]:
            values = {**data["base"], **family["base"],
                      **{k: v[0] for k, v in family["grid"].items()}}
            for key in ("entry_time", "exit_time", "atr_open", "atr_close", "ref_from", "ref_to"):
                values[key] = time.fromisoformat(values[key])
            UsCloseDeOpenConfig(**values)
            assert family["grid"]["exit_time"] == exits
