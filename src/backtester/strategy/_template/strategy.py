"""Template strategy: declares its timeframes and never trades. Copy and fill in.

Rules for a real strategy (CLAUDE.md):
- only read the `SeriesView`s handed to `on_candle` (nothing after `now`);
- detectors are incremental: update each once per closed candle of its timeframe;
- everything strategy-only stays in this folder, shared tools come from `detectors/`.

Spec: docs/strategy-<name>.md.
"""

from __future__ import annotations

from datetime import datetime

from backtester.core.models import Timeframe
from backtester.core.series import SeriesView
from backtester.strategy._template.config import TemplateConfig
from backtester.strategy.base import Order, Strategy


class TemplateStrategy(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)
    # Optional, see strategy/base.py: `uses_session_break_even`, `h4_alignment`, `full_history`.

    def __init__(self, symbol: str, config: TemplateConfig):
        self.symbol = symbol
        self.config = config

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        return []
