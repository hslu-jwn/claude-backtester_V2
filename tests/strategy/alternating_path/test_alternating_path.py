"""Hand-built causal M1 cases. Spec: strategy-alternating-path.md, A1-A9."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries, SeriesView
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.alternating_path.config import SYMBOLS, AlternatingPathConfig
from backtester.strategy.alternating_path.strategy import (
    AlternatingPath,
    _M15Aggregator,
    _ObservedAtr,
)
from backtester.strategy.registry import default_config, make_strategy
from backtester.tools.research_grid import expand, load_grid, variant_settings

M1 = Timeframe.M1
STEP = timedelta(minutes=15)
END = datetime(2019, 1, 8, 9, tzinfo=UTC)


def bars(make_candles, closes, end=END):
    start = end - len(closes) * STEP
    return [
        c
        for i, p in enumerate(closes)
        for c in make_candles([(p, p + 2, p - 2, p)] * 15, M1, start + i * STEP)
    ]


def history(make_candles, end=END, path=(10, 11, 10, 11, 10)):
    return bars(make_candles, [10] * 93 + list(path), end)


def feed(strategy, candles):
    series = CandleSeries(strategy.symbol, M1, candles)
    orders = []
    for i in range(len(series)):
        view = series.view(i)
        assert isinstance(view, SeriesView)
        orders.extend(strategy.on_candle(view.current.ts + M1.duration, {M1: view}))
    return orders


def test_complete_aggregation(make_candles):
    candles = bars(make_candles, [10])
    candles[0] = replace(candles[0], open=9, high=13)
    candles[-1] = replace(candles[-1], close=11, low=7)
    agg = _M15Aggregator()
    assert all(agg.update(c) is None for c in candles[:-1])
    bar = agg.update(candles[-1])
    assert (bar.ts, bar.open, bar.high, bar.low, bar.close) == (END - STEP, 9, 13, 7, 11)


@pytest.mark.parametrize("defect", ["missing", "shifted", "negative", "nan", "inf", "high", "low"])
def test_invalid_bucket_is_not_observed(make_candles, defect):
    candles = bars(make_candles, [10])
    if defect == "missing":
        del candles[5]
    elif defect == "shifted":
        candles[5] = replace(candles[5], ts=candles[5].ts + timedelta(seconds=1))
    else:
        # Fault injection past Candle's constructor validation.
        field, value = {
            "negative": ("low", -1),
            "nan": ("close", float("nan")),
            "inf": ("open", float("inf")),
            "high": ("high", 9),
            "low": ("low", 11),
        }[defect]
        object.__setattr__(candles[5], field, value)
    agg = _M15Aggregator()
    assert [bar for c in candles if (bar := agg.update(c)) is not None] == []
    assert agg.update(bars(make_candles, [10], END + STEP)[-1]) is None


def test_observed_atr_seed_recursion_and_gap():
    atr = _ObservedAtr(96)

    def bar(i, close=10, high=12, low=8):
        return Candle(END + i * STEP, close, high, low, close)

    assert atr.update(bar(0)) is None
    for i in range(1, 96):
        assert atr.update(bar(i)) is None
    assert atr.update(bar(96)) == 4
    assert atr.update(bar(100, 20, 21, 19)) == pytest.approx((95 * 4 + 11) / 96)


def test_prior_atr_and_first_possible_signal(make_candles):
    candles = history(make_candles)
    for c in candles[-15:]:
        object.__setattr__(c, "high", 20)
        object.__setattr__(c, "low", 1)
    assert feed(AlternatingPath("EURUSD"), candles[:-15]) == []
    [order] = feed(AlternatingPath("EURUSD"), candles)
    assert order.entry == 10
    assert order.stop_loss == 14


@pytest.mark.parametrize(
    "path,expected",
    [
        ((10, 11, 10, 11, 10), True),
        ((10, 10.999, 10, 10.999, 10), False),
        ((10, 11, 11, 12, 11), False),
        ((10, 11, 12, 11, 12), False),
    ],
)
def test_event_threshold_and_signs(make_candles, path, expected):
    assert bool(feed(AlternatingPath("EURUSD"), history(make_candles, path=path))) == expected


def test_event_window_gap(make_candles):
    candles = history(make_candles)
    del candles[-45:-30]
    assert feed(AlternatingPath("EURUSD"), candles) == []


def test_gap_suppresses_event_even_with_ready_atr(make_candles):
    candles = bars(make_candles, [10] * 95 + [10, 11, 10, 11, 10])
    del candles[-45:-30]
    strategy = AlternatingPath("EURUSD")
    assert feed(strategy, candles) == []
    assert strategy._atr.value == 4


def test_97th_valid_bar_cannot_signal_even_with_alternating_path(make_candles):
    candles = bars(make_candles, [10] * 92 + [10, 11, 10, 11, 10])
    strategy = AlternatingPath("EURUSD")
    assert feed(strategy, candles) == []
    assert strategy._atr.value == 4  # just seeded; not available through t-1


@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan")])
def test_invalid_prior_atr_cannot_signal(make_candles, value):
    strategy = AlternatingPath("EURUSD")
    candles = history(make_candles)
    assert feed(strategy, candles[:-15]) == []
    strategy._atr.value = value
    assert feed(strategy, candles[-15:]) == []


@pytest.mark.parametrize(
    "mode,direction,stop",
    [
        ("FOLLOW_LAST", Direction.BULLISH, 7),
        ("FADE_LAST", Direction.BEARISH, 15),
    ],
)
@pytest.mark.parametrize("symbol", SYMBOLS)
def test_direction_and_market_stop(make_candles, mode, direction, stop, symbol):
    [order] = feed(
        AlternatingPath(symbol, AlternatingPathConfig(response_mode=mode)),
        history(make_candles, path=(11, 10, 11, 10, 11)),
    )
    assert order.direction is direction
    assert order.entry == 11
    assert order.stop_loss == stop
    assert order.take_profit is None
    assert not order.limit_fill


@pytest.mark.parametrize("month,utc_hour", [(1, 9), (7, 8)])
@pytest.mark.parametrize("offset,expected", [(-15, False), (0, True), (285, True), (300, False)])
def test_london_window_dst(make_candles, month, utc_hour, offset, expected):
    end = datetime(2019, month, 8, utc_hour, tzinfo=UTC) + timedelta(minutes=offset)
    assert bool(feed(AlternatingPath("EURUSD"), history(make_candles, end))) == expected


def test_weekend_and_unsupported(make_candles):
    assert feed(AlternatingPath("EURUSD"), history(make_candles, END.replace(day=12))) == []
    assert feed(AlternatingPath("USDJPY"), history(make_candles)) == []


@pytest.mark.parametrize("holding", [30, 60])
@pytest.mark.parametrize("late", [0, 3])
def test_time_exit_and_position_guard(make_candles, holding, late):
    strategy = AlternatingPath("EURUSD", AlternatingPathConfig(holding_minutes=holding))
    [order] = feed(strategy, history(make_candles))
    assert feed(strategy, bars(make_candles, [11], END + STEP)) == []
    assert strategy.exits() == []
    due = END + timedelta(minutes=holding)
    assert feed(strategy, make_candles([(10, 12, 8, 10)], M1, due - timedelta(minutes=2))) == []
    assert strategy.exits() == []
    assert (
        feed(strategy, make_candles([(10, 12, 8, 10)], M1, due + timedelta(minutes=late - 1))) == []
    )
    assert strategy.exits() == [order.ref]
    assert feed(strategy, bars(make_candles, [11, 10, 11, 10, 11], END + timedelta(hours=3))) == []


@pytest.mark.parametrize("callback", ["on_trade_closed", "on_order_skipped"])
def test_features_continue_and_callback_releases(make_candles, callback):
    strategy = AlternatingPath("EURUSD")
    [order] = feed(strategy, history(make_candles))
    assert feed(strategy, bars(make_candles, [11, 10, 11], END + 3 * STEP)) == []
    getattr(strategy, callback)("unrelated", None)
    assert feed(strategy, bars(make_candles, [10], END + 4 * STEP)) == []
    getattr(strategy, callback)(order.ref, None)
    [second] = feed(strategy, bars(make_candles, [11], END + 5 * STEP))
    assert second.ref != order.ref


def test_no_lookahead_and_stale_callback(make_candles):
    candles = history(make_candles)
    assert feed(AlternatingPath("EURUSD"), candles[:-1]) == []
    original = feed(AlternatingPath("EURUSD"), candles)
    assert len(original) == 1
    assert (
        feed(AlternatingPath("EURUSD"), candles + bars(make_candles, [100], END + STEP)) == original
    )
    strategy = AlternatingPath("EURUSD")
    view = CandleSeries("EURUSD", M1, candles).view(len(candles) - 1)
    assert strategy.on_candle(END + M1.duration, {M1: view}) == []
    assert strategy.on_candle(END, {M1: None}) == []
    assert len(feed(strategy, candles)) == 1
    assert strategy.on_candle(END, {M1: view}) == []


def test_config_registry_and_settings():
    from backtester.runner import RunSettings
    from backtester.settings import from_json, to_json

    cfg = AlternatingPathConfig()
    assert default_config("alternating_path") == cfg
    strategy = make_strategy("EURUSD", cfg)
    assert isinstance(strategy, AlternatingPath)
    assert strategy.timeframes == (M1,)
    assert not strategy.uses_session_break_even
    assert strategy.min_warmup_days >= 5
    with pytest.raises(FrozenInstanceError):
        cfg.holding_minutes = 30
    cfg = replace(cfg, response_mode="FADE_LAST", holding_minutes=30)
    assert from_json(to_json(RunSettings(strategy=cfg))).strategy == cfg


@pytest.mark.parametrize(
    "override",
    [
        {"response_mode": "follow_last"},
        {"response_mode": None},
        {"holding_minutes": 45},
        {"holding_minutes": True},
        {"holding_minutes": 30.0},
    ]
    + [
        {f.name: None}
        for f in fields(AlternatingPathConfig)
        if f.name not in ("response_mode", "holding_minutes")
    ]
    + [
        {f.name: True if isinstance(f.default, (int, float)) else "10:00"}
        for f in fields(AlternatingPathConfig)
        if f.name not in ("response_mode", "holding_minutes")
    ],
)
def test_config_validation(override):
    with pytest.raises(ValueError):
        AlternatingPathConfig(**override)


@pytest.mark.parametrize("stop_at", ["next", "due", "none"])
def test_engine_short_stop_and_time_exit(make_candles, stop_at):
    candles = history(make_candles)
    candles[-1] = replace(candles[-1], high=20)
    end = END + timedelta(minutes=60)
    candles += make_candles([(10, 15 if stop_at == "next" else 12, 8, 10)], M1, END)
    candles += make_candles([(10, 15 if stop_at == "due" else 12, 8, 10)], M1, end - M1.duration)
    [trade] = run_backtest(
        AlternatingPath("EURUSD"),
        [CandleSeries("EURUSD", M1, candles)],
        EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False)),
    )
    assert trade.entry_time == END
    assert trade.entry == 10
    assert trade.exit_time == (END + M1.duration if stop_at == "next" else end)
    assert trade.exit_reason is (ExitReason.SIGNAL if stop_at == "none" else ExitReason.STOP_LOSS)
    assert trade.exit_price == (10 if stop_at == "none" else 14)


def test_grid_four_cells():
    grid = load_grid(Path(__file__).resolve().parents[3] / "research/grids/alternating_path.toml")
    variants, size, sampled = expand(grid)
    assert len(variants) == size == 4
    assert not sampled
    assert grid.symbols == SYMBOLS
    assert grid.min_trades == 300
    assert grid.submission == {
        "strategy_id": "M15_ALTERNATING_PATH_BATCH",
        "specification_version": "0.2.0",
        "submission_sha256": "d09d44b96cde33f45b718803eb385cc9a9fd908641d06148ea47de61acff31c5",
        "experiment_id": "M15_ALTERNATING_PATH_BATCH__v0.2.0__DEVELOPMENT__1",
    }
    assert {
        (s.strategy.response_mode, s.strategy.holding_minutes)
        for v in variants
        for s in [variant_settings(grid, v)]
    } == {(m, h) for m in ("FOLLOW_LAST", "FADE_LAST") for h in (30, 60)}
