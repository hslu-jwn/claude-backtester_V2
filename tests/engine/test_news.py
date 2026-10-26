"""Synthetic order acceptance integration. Spec: docs/news.md."""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

from conftest import build_series

from backtester.core.models import Direction, Timeframe
from backtester.data.news import Calendar, ImpactWindow, NewsConfig, ScheduleEvent
from backtester.engine.backtest import Backtest, EngineConfig
from backtester.strategy.base import Order, Strategy

RELEASE = datetime(2026, 1, 5, 13, 30, tzinfo=UTC)
FLAT = (100, 100.1, 99.9, 100)


class Entries(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False

    def __init__(self):
        self.skips = []

    def on_candle(self, now, views):
        return [Order(Direction.BULLISH, 100, 99, None, ref=now)]

    def on_order_skipped(self, ref, now):
        self.skips.append((ref, now))


def run(config, schedule=None):
    series = build_series(
        [FLAT] * 5, Timeframe.M1, start=RELEASE - timedelta(minutes=3), symbol="EURUSD"
    )
    strategy = Entries()
    backtest = Backtest(strategy, [series], config, calendar=schedule)
    return backtest.run(), strategy, backtest


def schedule():
    event = ScheduleEvent(
        "synthetic",
        RELEASE,
        RELEASE.date(),
        None,
        None,
        "minute",
        "USD",
        "US",
        "High",
        "Synthetic",
        "test",
    )
    return Calendar((event,), "synthetic-hash", date(2020, 1, 2), date(2026, 10, 23))


def test_off_preserves_complete_trade_list_and_missing_calendar_does_too():
    baseline, _, _ = run(EngineConfig())
    off, strategy, _ = run(EngineConfig(), schedule())
    missing, _, bt = run(EngineConfig(news=NewsConfig(enabled=True)))
    assert off == baseline == missing
    assert strategy.skips == []
    assert bt.news_blocked == 0


def test_on_blocks_inside_and_inclusive_endpoints_allows_adjacent_minutes():
    config = EngineConfig(news=NewsConfig(enabled=True, high=ImpactWindow(1, 1)))
    trades, strategy, bt = run(config, schedule())
    assert [t.entry_time for t in trades] == [
        RELEASE - timedelta(minutes=2),
        RELEASE + timedelta(minutes=2),
    ]
    assert [t for _, t in strategy.skips] == [
        RELEASE - timedelta(minutes=1),
        RELEASE,
        RELEASE + timedelta(minutes=1),
    ]
    assert bt.news_blocked == 3


def test_flag_only_keeps_trades_and_collects_event_ids():
    base, _, _ = run(EngineConfig())
    cfg = NewsConfig(enabled=True, policy="flag_only", high=ImpactWindow(1, 1))
    trades, strategy, bt = run(EngineConfig(news=cfg), schedule())
    assert trades == base
    assert strategy.skips == []
    assert bt.news_blocked == 0
    assert len(bt.news_flags) == 3
    assert all(ids == ("synthetic",) for _, ids in bt.news_flags)


def test_settings_roundtrip():
    from backtester.runner import RunSettings
    from backtester.settings import from_json, leaves, to_json

    config = EngineConfig(news=NewsConfig(enabled=True, high=ImpactWindow(2, 3)))
    settings = RunSettings(engine=config)
    assert from_json(to_json(settings)) == settings
    assert "engine.news.instruments.EURUSD.include_global" in {v.path for v in leaves(settings)}
    assert replace(config.news, enabled=False).enabled is False


def test_unfinished_calendar_config_has_no_settings_panel_widgets():
    from backtester.ui.settings_panel import panel_fields

    assert not any(leaf.path.startswith("engine.news.") for _, leaf, _ in panel_fields())
