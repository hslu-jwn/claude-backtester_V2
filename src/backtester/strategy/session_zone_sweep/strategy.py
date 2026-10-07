"""SessionZoneSweep strategy: wires zones, setups, detectors and targets together.

Spec: strategy-session-zones.md. Timeframes: 30m zones + reaction, 5m BOS + entry (base),
1h TP obstacles. Per closed 5m candle: the setup side (signals.py) may emit entry signals;
each gets SL / TP (targets.py) and becomes an order filled at the 5m close, unless the TP
is below the minimum R:R. Trades entered in the last `tag_last_minutes_before_next_session`
minutes before the next session start are tagged `LAST_MINUTES_TAG` (or skipped when
`include_last_minutes_trades` is off). Every signal and what became of it is kept in
`decisions`, for checking against the chart and for the results file (ROADMAP 3.4).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from backtester.core.models import Timeframe
from backtester.core.series import SeriesView
from backtester.sessions import session_of
from backtester.strategy.base import Order, Strategy
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import EntrySignal
from backtester.strategy.session_zone_sweep.signals import SetupTracker
from backtester.strategy.session_zone_sweep.targets import ObstacleTracker, Targets, targets

LAST_MINUTES_TAG = "last_90m"


@dataclass(frozen=True, slots=True)
class Decision:
    signal: EntrySignal
    targets: Targets | None  # None: no trade (TP below the minimum R:R)
    order: Order | None  # None: no trade


class SessionZoneSweep(Strategy):
    base_timeframe = Timeframe.M5

    def __init__(self, symbol: str, config: SessionZoneSweepConfig | None = None):
        self.symbol = symbol
        self.config = config = config or SessionZoneSweepConfig()
        self.timeframes = (Timeframe.M5, config.zone_timeframe, config.obstacle_timeframe)
        self.setups = SetupTracker(symbol, config)
        self.obstacles = ObstacleTracker(self.setups.doji_max_body, config)
        self._obstacle_cursor = -1
        self.decisions: list[Decision] = []

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        v5 = views[Timeframe.M5]
        if v5.symbol != self.symbol:
            raise ValueError(f"{v5.symbol} candles for a {self.symbol} strategy")
        self._update_obstacles(views[self.config.obstacle_timeframe])
        signals = self.setups.update(now, v5, views[self.config.zone_timeframe])
        orders = []
        for signal in signals:
            order = self._order(signal, now)
            if order is not None:
                orders.append(order)
        return orders

    def _update_obstacles(self, view: SeriesView | None) -> None:
        if view is None:
            return
        for cursor in range(self._obstacle_cursor + 1, view.cursor + 1):
            self.obstacles.update(view.at(cursor))
        self._obstacle_cursor = view.cursor

    def _order(self, signal: EntrySignal, now: datetime) -> Order | None:
        state = self.setups.state
        zones = [(lz.role, lz.zone.top, lz.zone.bottom) for lz in state.live_zones]
        found = targets(signal, state.atr, zones, self.obstacles, self.config)
        order = None
        if found is not None:
            tags = self._tags(now)
            if self.config.include_last_minutes_trades or LAST_MINUTES_TAG not in tags:
                order = Order(
                    signal.direction,
                    signal.close,
                    found.stop_loss,
                    found.take_profit,
                    tags,
                    _reason(signal, found),
                )
        self.decisions.append(Decision(signal, found, order))
        return order

    def _tags(self, now: datetime) -> frozenset[str]:
        session = session_of(now, self.config.sessions)
        last = timedelta(minutes=self.config.tag_last_minutes_before_next_session)
        if session is not None and session.end - now <= last:
            return frozenset({LAST_MINUTES_TAG})
        return frozenset()


def _reason(signal: EntrySignal, found: Targets) -> str:
    zone = signal.zone
    return (
        f"{zone.formed_in.session.value} {zone.side.value} zone, 30m reaction "
        f"{signal.reaction_open:%H:%M}, 5m BOS {signal.bos.at:%H:%M}"
        f"{'' if signal.bos.is_bos else ' (with trend)'}, "
        f"{signal.confluence.kind.value}, TP {found.target}"
    )
