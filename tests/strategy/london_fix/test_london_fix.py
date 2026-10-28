"""Hand-built M1 cases for submission FX_LONDON_FIX_REV v1.0.0.

Spec: docs/strategy-london-fix.md. Constant high-low 0.0010, previous
close 1.1000: every true range, and therefore Wilder ATR, is 0.0010.
"""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.london_fix.config import LondonFixConfig
from backtester.strategy.london_fix.strategy import LondonFix
from backtester.strategy.registry import default_config, make_strategy
from backtester.tools.entry_screen import STRATEGY_SYMBOLS
from backtester.tools.research_grid import (
    ResearchConfig,
    expand,
    load_grid,
    swept_params,
    variant_settings,
)

M1 = Timeframe.M1
SYMBOLS = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD")
NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))


def stamp(value):
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def fixture(make_candles, ending="2019-01-07T16:03", count=60, flat=False):
    end = stamp(ending)
    prices = (1.1, 1.1, 1.1, 1.1) if flat else (1.1, 1.1005, 1.0995, 1.1)
    return make_candles([prices] * count, M1, end - timedelta(minutes=count))


def tail(make_candles, ending, prices=(1.1, 1.1005, 1.0995, 1.1)):
    return make_candles([prices], M1, stamp(ending) - M1.duration)


def feed(strategy, candles):
    series = CandleSeries(strategy.symbol, M1, candles)
    out = []
    for i in range(len(series)):
        view = series.view(i)
        out.extend(strategy.on_candle(view.current.ts + M1.duration, {M1: view}))
    return out


def run(candles, symbol="EURUSD", **config):
    return run_backtest(
        LondonFix(symbol, LondonFixConfig(**config)),
        [CandleSeries(symbol, M1, candles)],
        NO_COSTS,
    )


@pytest.mark.parametrize(
    "ending",
    [
        "2019-01-07T16:03",  # GMT
        "2019-07-01T15:03",  # BST
        "2019-04-01T15:03",  # Monday after March DST transition
        "2019-10-28T16:03",  # Monday after October DST transition
    ],
)
def test_exact_signal_close_and_dst(make_candles, ending):
    candles = fixture(make_candles, ending)
    [trade] = run(candles)
    assert trade.entry_time == stamp(ending)
    assert trade.entry_candle == stamp(ending) - M1.duration
    assert trade.entry == 1.1


@pytest.mark.parametrize(
    "symbol,side,stop",
    [
        ("EURUSD", Direction.BULLISH, 1.096),
        ("GBPUSD", Direction.BULLISH, 1.096),
        ("AUDUSD", Direction.BULLISH, 1.096),
        ("NZDUSD", Direction.BULLISH, 1.096),
        ("USDCHF", Direction.BEARISH, 1.104),
        ("USDCAD", Direction.BEARISH, 1.104),
    ],
)
def test_side_map_and_frozen_stop(make_candles, symbol, side, stop):
    [order] = feed(LondonFix(symbol), fixture(make_candles))
    assert order.direction is side
    assert order.entry == 1.1
    assert order.stop_loss == pytest.approx(stop)
    assert order.take_profit is None
    assert not order.limit_fill


def test_wilder_includes_signal_candle(make_candles):
    candles = fixture(make_candles, count=61)
    candles[-1] = replace(candles[-1], high=1.101, low=1.099)
    [order] = feed(LondonFix("EURUSD"), candles)
    # SMA seed = .001; 61st TR = .002; Wilder = (.001*59+.002)/60.
    assert order.stop_loss == pytest.approx(1.1 - 4 * (0.001 * 59 + 0.002) / 60)


@pytest.mark.parametrize("symbol", ["USDJPY", "UNKNOWN"])
def test_unsupported_symbol(make_candles, symbol):
    assert feed(LondonFix(symbol), fixture(make_candles)) == []


@pytest.mark.parametrize("count,flat", [(59, False), (60, True)])
def test_incomplete_or_zero_atr(make_candles, count, flat):
    assert feed(LondonFix("EURUSD"), fixture(make_candles, count=count, flat=flat)) == []


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.0])
def test_invalid_atr_skips(make_candles, monkeypatch, value):
    strategy = LondonFix("EURUSD")
    monkeypatch.setattr(strategy._atr, "update", lambda view: value)
    assert feed(strategy, fixture(make_candles)) == []


def test_missing_signal_never_uses_later_bar(make_candles):
    candles = fixture(make_candles)[:-1] + tail(make_candles, "2019-01-07T16:04")
    assert feed(LondonFix("EURUSD"), candles) == []


@pytest.mark.parametrize("ending", ["2019-01-05T16:03", "2019-01-06T16:03"])
def test_weekend(make_candles, ending):
    assert feed(LondonFix("EURUSD"), fixture(make_candles, ending)) == []


@pytest.mark.parametrize("exit_at", ["2019-01-07T17:03", "2019-01-07T17:07"])
def test_time_exit_first_available_close(make_candles, exit_at):
    candles = fixture(make_candles)
    candles += tail(make_candles, "2019-01-07T17:02")
    candles += tail(make_candles, exit_at, (1.101, 1.1015, 1.1005, 1.101))
    candles += tail(make_candles, "2019-01-07T17:10")
    [trade] = run(candles, holding_minutes=60)
    assert trade.exit_time == stamp(exit_at)
    assert trade.exit_reason is ExitReason.SIGNAL
    assert trade.exit_price == 1.101


def test_force_close(make_candles):
    candles = fixture(make_candles, "2019-01-07T23:00")
    candles += tail(make_candles, "2019-01-07T23:54")
    candles += tail(make_candles, "2019-01-07T23:55")
    candles += tail(make_candles, "2019-01-08T00:00")
    [trade] = run(candles, entry_time_london="23:00", holding_minutes=360)
    assert trade.exit_time == stamp("2019-01-07T23:55")
    assert trade.exit_reason is ExitReason.SIGNAL


@pytest.mark.parametrize("low,expected", [(1.095, 1.096), (1.09, 1.09)])
def test_stop_before_time_exit_and_adverse_gap(make_candles, low, expected):
    candles = fixture(make_candles)
    opening = 1.1 if low == 1.095 else low
    candles += tail(make_candles, "2019-01-07T17:03", (opening, 1.101, low, 1.1))
    [trade] = run(candles, holding_minutes=60)
    assert trade.exit_reason is ExitReason.STOP_LOSS
    assert trade.exit_price == pytest.approx(expected)


def test_one_entry_per_day_and_open_position_blocks(make_candles):
    strategy = LondonFix("EURUSD")
    first = fixture(make_candles)
    [order] = feed(strategy, first)
    series = CandleSeries("EURUSD", M1, first)
    assert strategy.on_candle(stamp("2019-01-07T16:03"), {M1: series.view(59)}) == []
    # No engine callback: yesterday's position remains open even when its exit is due.
    both = first + fixture(make_candles, "2019-01-08T16:03")
    series = CandleSeries("EURUSD", M1, both)
    for i in range(60, len(series)):
        view = series.view(i)
        assert strategy.on_candle(view.current.ts + M1.duration, {M1: view}) == []
    assert strategy.exits() == [order.ref]


def test_closed_and_skipped_callbacks_allow_next_day(make_candles):
    for callback in ("on_order_skipped", "on_trade_closed"):
        strategy = LondonFix("EURUSD")
        [order] = feed(strategy, fixture(make_candles))
        getattr(strategy, callback)(order.ref, None)
        candles = fixture(make_candles) + fixture(make_candles, "2019-01-08T16:03")
        series = CandleSeries("EURUSD", M1, candles)
        orders = []
        for i in range(60, len(series)):
            view = series.view(i)
            orders += strategy.on_candle(view.current.ts + M1.duration, {M1: view})
        assert len(orders) == 1


@pytest.mark.parametrize(
    "ending,tagged",
    [
        ("2019-05-31T15:03", True),
        ("2019-08-30T15:03", True),
        ("2019-08-29T15:03", False),
        ("2019-01-07T16:03", False),
    ],
)
def test_month_end_tag(make_candles, ending, tagged):
    [trade] = run(fixture(make_candles, ending))
    assert ("month_end" in trade.tags) is tagged


def test_no_lookahead_incremental_prefix(make_candles):
    candles = fixture(make_candles)
    assert feed(LondonFix("EURUSD"), candles[:-1]) == []
    earlier = feed(LondonFix("EURUSD"), candles)
    assert len(earlier) == 1
    future = tail(make_candles, "2019-01-07T16:04", (2.0, 3.0, 0.5, 2.0))
    assert feed(LondonFix("EURUSD"), candles + future) == earlier


def test_bad_timestamps_rejected_and_stale_call_skipped(make_candles):
    candles = fixture(make_candles)
    for bad in (candles + candles[-1:], candles[::-1]):
        with pytest.raises(ValueError, match="strictly increasing"):
            CandleSeries("EURUSD", M1, bad)
    series = CandleSeries("EURUSD", M1, candles)
    strategy = LondonFix("EURUSD")
    assert strategy.on_candle(stamp("2019-01-07T16:04"), {M1: series.view(59)}) == []


def test_defaults_fixed_map_and_registry():
    cfg = LondonFixConfig()
    assert cfg.entry_time_london == "16:03"
    assert cfg.atr_period == 60
    assert cfg.stop_atr_multiplier == 4.0
    assert cfg.holding_minutes == 360
    assert cfg.force_close_london == "23:55"
    assert isinstance(cfg.side_map, tuple)
    with pytest.raises(FrozenInstanceError):
        cfg.holding_minutes = 60
    with pytest.raises(ValueError):
        replace(cfg, side_map=())
    assert default_config("london_fix") == cfg
    assert isinstance(make_strategy("EURUSD", cfg), LondonFix)
    assert STRATEGY_SYMBOLS["london_fix"] == SYMBOLS


@pytest.mark.parametrize(
    "override",
    [
        {"atr_period": 0},
        {"atr_period": 1.5},
        {"holding_minutes": 0},
        {"holding_minutes": 1.5},
        {"stop_atr_multiplier": 0},
        {"stop_atr_multiplier": float("nan")},
        {"stop_atr_multiplier": float("inf")},
        {"entry_time_london": "25:00"},
        {"entry_time_london": "16:03:01"},
        {"force_close_london": "15:00"},
    ],
)
def test_invalid_config(override):
    with pytest.raises(ValueError):
        LondonFixConfig(**override)


def test_grid_identity_and_nine_variants():
    path = Path(__file__).resolve().parents[3] / "research/grids/london_fix.toml"
    grid = load_grid(path)
    variants, size, sampled = expand(grid)
    assert len(variants) == size == 9
    assert not sampled
    assert grid.symbols == SYMBOLS
    assert grid.min_trades == ResearchConfig().min_trades
    assert swept_params(grid) == ["holding_minutes", "stop_atr_multiplier"]
    assert grid.submission == {
        "strategy_id": "FX_LONDON_FIX_REV",
        "specification_version": "1.0.0",
        "submission_sha256": "8ec6b914e7669cc28b3eeb1008271dae8df264453934d6ce5c099b3d70ae6263",
        "experiment_id": "FX_LONDON_FIX_REV__v1.0.0__DEVELOPMENT__1",
    }
    configs = [variant_settings(grid, v).strategy for v in variants]
    assert {(c.stop_atr_multiplier, c.holding_minutes) for c in configs} == {
        (s, h) for s in (3.0, 4.0, 5.0) for h in (60, 180, 360)
    }
