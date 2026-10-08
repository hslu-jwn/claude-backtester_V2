"""SessionZoneSweep strategy: wires zones, setups, detectors and targets together.

Spec: strategy-session-zones.md. Timeframes: 30m zones + reaction, 5m BOS + entry (base),
1h TP levels, 4H OBs as the TP limit. Per closed 5m candle: the setup side (signals.py) may
emit entry signals; each gets SL / TP1 / TP2 (targets.py) and becomes an order filled at
the 5m close, unless targets.py rejects it (SL too wide, 4H OB below the minimum R).
`tp1_share` of the position closes at TP1, the rest at TP2 with its SL at break-even after
TP1 (`break_even_after_tp1`). Trades entered in the last
`tag_last_minutes_before_next_session` minutes before the next session start are tagged
`LAST_MINUTES_TAG` (or skipped when `include_last_minutes_trades` is off). Every signal
and what became of it is kept in `decisions`, for checking against the chart and for the
results file (ROADMAP 3.4); per session, the zones and setup confluences are kept in
`journal` (journal.py, `session_records()`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from backtester.core.models import Timeframe
from backtester.core.series import SeriesView
from backtester.sessions import session_of
from backtester.strategy.base import Order, Strategy
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.journal import SessionJournal
from backtester.strategy.session_zone_sweep.setup import EntrySignal
from backtester.strategy.session_zone_sweep.signals import SetupTracker
from backtester.strategy.session_zone_sweep.targets import (
    ObstacleTracker,
    Rejected,
    Targets,
    UnmitigatedOrderBlocks,
    targets,
)

LAST_MINUTES_TAG = "last_90m"


@dataclass(frozen=True, slots=True)
class Decision:
    signal: EntrySignal
    targets: Targets | None  # None: no trade (see `rejected`)
    order: Order | None  # None: no trade
    rejected: str = ""  # why there is no trade


class SessionZoneSweep(Strategy):
    base_timeframe = Timeframe.M5

    def __init__(self, symbol: str, config: SessionZoneSweepConfig | None = None):
        self.symbol = symbol
        self.config = config = config or SessionZoneSweepConfig()
        self.timeframes = (
            Timeframe.M5,
            config.zone_timeframe,
            config.obstacle_timeframe,
            config.limit_timeframe,
        )
        self.setups = SetupTracker(symbol, config)
        doji = self.setups.doji_max_body
        self.obstacles = ObstacleTracker(doji, config)
        self.limits = UnmitigatedOrderBlocks(doji, config)
        self._cursors = {config.obstacle_timeframe: -1, config.limit_timeframe: -1}
        self.decisions: list[Decision] = []
        self.journal = SessionJournal()

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        v5 = views[Timeframe.M5]
        if v5.symbol != self.symbol:
            raise ValueError(f"{v5.symbol} candles for a {self.symbol} strategy")
        self._catch_up(self.obstacles, views[self.config.obstacle_timeframe])
        self._catch_up(self.limits, views[self.config.limit_timeframe])
        v30 = views[self.config.zone_timeframe]
        setups = self.setups
        signals = setups.update(now, v5, v30)
        journal = self.journal
        journal.on_candle(
            now, v5, v30, setups.session_zone_events, setups.zone_transitions, setups.links
        )
        orders = []
        for signal in signals:
            order = self._order(signal, now)
            journal.on_signal(signal.zone.active_in, signal.confluence, order is not None)
            if order is not None:
                orders.append(order)
        return orders

    def session_records(self, run_end: datetime | None = None) -> list[dict]:
        return self.journal.records(run_end)

    def _catch_up(self, tracker, view: SeriesView | None) -> None:
        """Feed `tracker` every candle of `view`'s timeframe closed since the last call."""
        if view is None:
            return
        for cursor in range(self._cursors[view.timeframe] + 1, view.cursor + 1):
            tracker.update(view.at(cursor))
        self._cursors[view.timeframe] = view.cursor

    def _order(self, signal: EntrySignal, now: datetime) -> Order | None:
        state = self.setups.state
        zones = [(lz.role, lz.zone.top, lz.zone.bottom) for lz in state.live_zones]
        found = targets(signal, state.atr, zones, self.obstacles, self.limits, self.config)
        if isinstance(found, Rejected):
            self.decisions.append(Decision(signal, None, None, found.reason))
            return None
        tags = self._tags(now)
        order, rejected = None, ""
        if self.config.include_last_minutes_trades or LAST_MINUTES_TAG not in tags:
            two = found.take_profit_2 is not None
            order = Order(
                signal.direction,
                signal.close,
                found.stop_loss,
                found.take_profit,
                tags,
                _reason(signal, found),
                take_profit_2=found.take_profit_2,
                tp1_share=self.config.tp1_share if two else 1.0,
                break_even_after_tp1=self.config.break_even_after_tp1,
            )
        else:
            rejected = "last minutes before the next session (excluded)"
        self.decisions.append(Decision(signal, found, order, rejected))
        return order

    def _tags(self, now: datetime) -> frozenset[str]:
        session = session_of(now, self.config.sessions)
        last = timedelta(minutes=self.config.tag_last_minutes_before_next_session)
        if session is not None and session.end - now <= last:
            return frozenset({LAST_MINUTES_TAG})
        return frozenset()


def _reason(signal: EntrySignal, found: Targets) -> str:
    zone = signal.zone
    tp = f"TP1 {found.tp1_from}"
    if found.tp2_from is not None:
        tp += f", TP2 {found.tp2_from}"
    return (
        f"{zone.formed_in.session.value} {zone.side.value} zone, 30m reaction "
        f"{signal.reaction_open:%H:%M}, 5m BOS {signal.bos.at:%H:%M}"
        f"{'' if signal.bos.is_bos else ' (with trend)'}, "
        f"{signal.confluence.kind.value}, {tp}"
    )
