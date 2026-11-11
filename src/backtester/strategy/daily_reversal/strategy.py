"""Incremental M1 daily reversal strategy.

Spec: strategy-daily_reversal.md > Cash sessions, E8, CAP, Setup TS, Execution and exits.
Only the current closed candle of the supplied SeriesView is read.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from math import isfinite
from types import MappingProxyType
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.data.sources import PRICE_DIGITS
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import Order, Strategy, UnsupportedSymbolError
from backtester.strategy.daily_reversal.config import DailyReversalConfig

if TYPE_CHECKING:
    from backtester.engine.costs import CostConfig
    from backtester.engine.trade import TradeResult


SESSIONS = MappingProxyType(
    {
        "US500": ("America/New_York", time(9, 30), time(16)),
        "NAS100": ("America/New_York", time(9, 30), time(16)),
        "US30": ("America/New_York", time(9, 30), time(16)),
        "GER40": ("Europe/Berlin", time(9), time(17, 30)),
        "UK100": ("Europe/London", time(8), time(16, 30)),
        "JP225": ("Asia/Tokyo", time(9), time(15)),
        "AUS200": ("Australia/Sydney", time(10), time(16)),
    }
)
TS_FX_SYMBOLS = frozenset({"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"})


@dataclass(frozen=True, slots=True)
class DailyBar:
    high: float
    low: float
    close: float


@dataclass(frozen=True, slots=True)
class Candidate:
    direction: Direction
    day2: int
    high: float  # sign-normalized highs/lows; shorts use -low, -high
    low: float


@dataclass(frozen=True, slots=True)
class Pending:
    direction: Direction
    level: float
    stop: float
    expires: int


def _sign(direction: Direction) -> int:
    return 1 if direction is Direction.BULLISH else -1


def _extremes(bar: DailyBar, sign: int) -> tuple[float, float]:
    return (bar.high, bar.low) if sign == 1 else (-bar.low, -bar.high)


class DailyReversal(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False

    def __init__(
        self,
        symbol: str,
        config: DailyReversalConfig | None = None,
        detectors: DetectorSettings | None = None,
    ):
        self.config = config or DailyReversalConfig()
        self._ts_fx = self.config.setup == "TS" and symbol in TS_FX_SYMBOLS
        if symbol not in SESSIONS and not self._ts_fx:
            raise UnsupportedSymbolError(f"daily_reversal has no cash session for {symbol}")
        self.symbol = symbol
        zone, self._open, self._close = (
            ("America/New_York", time(17), time(17)) if self._ts_fx else SESSIONS[symbol]
        )
        self._tz = ZoneInfo(zone)
        # default before configure_costs supplies the engine's tick (same values, layer rule)
        self._tick = self.config.tick_size or 10 ** -PRICE_DIGITS[symbol]
        self._history: deque[DailyBar] = deque(
            maxlen=max(
                self.config.e8_lookback + 1,
                self.config.cap_lookback,
                self.config.ts_lookback if self.config.setup == "TS" else 0,
            )
        )
        self._session_end: datetime | None = None
        self._ts_atr: float | None = None
        self._ts_trs: list[float] = []
        self._candidates: list[Candidate] = []
        self._pending: dict[Direction, Pending] = {}
        self._position: tuple[int, int] | None = None  # ref, fill-session counter
        self._next_ref = 0
        self._exits: list[object] = []
        self._exit_requested = False
        self._day: date | None = None
        self._index = -1
        self._bar: DailyBar | None = None
        self._has_open = False
        self._finished = False
        self._invalid = False
        self._last_now: datetime | None = None
        self._integrity: list[dict] = []
        self.min_warmup_days = (
            max(self.config.e8_lookback + self.config.e8_last_day, self.config.cap_lookback + 1) * 2
            + 7
        )
        if self.config.setup == "TS":
            self.min_warmup_days = max(self.config.ts_lookback, self.config.ts_atr_period) * 2 + 7

    def _bounds(self, local: datetime) -> tuple[datetime, datetime]:
        """Spec: Setup TS > Sessions. FX session dates name the 17:00 closing day."""
        day = local.date()
        if self._ts_fx and local.time() > self._close:
            day += timedelta(days=1)
        end = datetime.combine(day, self._close, self._tz)
        start_day = day - timedelta(days=1) if self._ts_fx else day
        return datetime.combine(start_day, self._open, self._tz), end

    def configure_costs(self, costs: CostConfig) -> None:
        super().configure_costs(costs)
        tick = costs.for_symbol(self.symbol).tick_size
        if self.config.tick_size is None and tick is not None:
            self._tick = tick

    def _flag(self, kind: str, now: datetime) -> None:
        self._integrity.append(
            {
                "kind": kind,
                "symbol": self.symbol,
                "time": now.isoformat(),
                "session_date": self._day.isoformat() if self._day else None,
                "trading_date": (self._day or now.date()).isoformat(),
                "session": "daily_reversal",
                "start": (now - Timeframe.M1.duration).isoformat(),
                "end": now.isoformat(),
                "integrity_failed": True,
            }
        )

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        """Spec: Execution and exits. Trigger first, then commit this day's close."""
        view = views.get(Timeframe.M1)
        if view is None:
            return []
        if self._last_now is not None and now <= self._last_now:
            raise ValueError("daily_reversal requires strictly increasing candle close times")
        candle = view.current
        if now != candle.ts + Timeframe.M1.duration:
            raise ValueError("now must equal the M1 candle close time")
        self._last_now = now
        local = now.astimezone(self._tz)
        start, end = self._bounds(local)
        session_day = end.date()
        inside = session_day.weekday() < 5 and start < local <= end
        if self.config.setup == "TS":
            self._check_exit(local, now)  # retain the old due close across a session change
        if self._day is not None and session_day > self._day and not self._finished:
            self._discard_session(now)
        if inside and session_day != self._day:
            self._day = session_day
            self._session_end = end
            self._index += 1
            self._bar = None
            self._has_open = self._finished = self._invalid = False
            self._pending = {d: p for d, p in self._pending.items() if self._index <= p.expires}
        self._check_exit(local, now)
        valid = (
            all(isfinite(p) and p > 0 for p in (candle.open, candle.high, candle.low, candle.close))
            and candle.low
            <= min(candle.open, candle.close)
            <= max(candle.open, candle.close)
            <= candle.high
        )
        if not valid:
            self._flag("invalid_candle", now)
            if inside:
                self._invalid = True
                self._pending.clear()
            return []
        if not inside:
            return []
        first_close = start + Timeframe.M1.duration
        if self._bar is None:
            self._has_open = local == first_close
            if not self._has_open:
                self._flag("incomplete_session", now)
                self._invalid = True
                self._pending.clear()
            self._bar = DailyBar(candle.high, candle.low, candle.close)
        else:
            self._bar = DailyBar(
                max(self._bar.high, candle.high), min(self._bar.low, candle.low), candle.close
            )
        orders = [] if self._invalid else self._entry(candle)
        if local == end:
            self._finish(now)
        return orders

    def _check_exit(self, local: datetime, now: datetime) -> None:
        if self._position is None or self._exit_requested:
            return
        ref, filled = self._position
        if self.config.setup == "TS":
            due = filled + self.config.ts_exit_sessions - 1
            if self._index >= due and self._session_end is not None and (
                self._index > due or now >= self._session_end
            ):
                if self._index != due or now != self._session_end:
                    self._flag("missing_exit_candle", now)
                self._exits.append(ref)
                self._exit_requested = True
            return
        due = filled + self.config.hold_sessions
        # Before a new observed session, _day still names the preceding cash day.
        later_date = self._day is not None and local.date() > self._day
        if self._index > due or (
            self._index == due and (later_date or local.time() >= self._close)
        ):
            if self._index != due or later_date or local.time() != self._close:
                self._flag("missing_exit_candle", now)
            self._exits.append(ref)
            self._exit_requested = True

    def _entry(self, candle: Candle) -> list[Order]:
        if self._position is not None:
            return []
        touched = [
            p
            for p in self._pending.values()
            if (
                self.config.setup == "TS"
                or (candle.high >= p.level if p.direction is Direction.BULLISH
                    else candle.low <= p.level)
            )
        ]
        if len(touched) > 1:
            self._pending.clear()
            return []
        if not touched:
            return []
        pending = touched[0]
        del self._pending[pending.direction]
        sign = _sign(pending.direction)
        risk = sign * (candle.close - pending.stop)
        adverse = candle.low if sign == 1 else candle.high
        if risk <= 0 or sign * (adverse - pending.stop) <= 0:
            return []
        ref = self._next_ref
        self._next_ref += 1
        self._position = (ref, self._index)
        self._exit_requested = False
        self._pending.clear()
        self._candidates.clear()
        target = (
            candle.close + sign * self.config.target_r * risk
            if self.config.target_r and self.config.setup != "TS" else None
        )
        execution = (
            "next session first M1 close" if self.config.setup == "TS"
            else "stop trigger / M1 close"
        )
        return [
            Order(
                pending.direction,
                candle.close,
                pending.stop,
                target,
                tags=frozenset({self.config.setup, "daily_reversal"}),
                reason=f"daily reversal {self.config.setup}: {execution}",
                confluence=self.config.setup,
                ref=ref,
            )
        ]

    def _discard_session(self, now: datetime) -> None:
        self._flag("incomplete_session", now)
        self._history.clear()
        self._candidates.clear()
        self._pending.clear()
        if self.config.setup == "TS":
            self._ts_atr = None
            self._ts_trs.clear()
        self._finished = True

    def _finish(self, now: datetime) -> None:
        """Spec: E8 / CAP / Setup TS. Commit only at the confirming session close."""
        if self._invalid or not self._has_open:
            self._discard_session(now)
            return
        self._finished = True
        bar = self._bar
        if self._position is None:
            if self.config.setup == "E8":
                self._e8(bar)
            elif self.config.setup == "TS":
                self._ts(bar)
            else:
                self._cap(bar)
        if self.config.setup == "TS":
            self._ts_update_atr(bar)
        self._history.append(bar)

    def _ts(self, bar: DailyBar) -> None:
        """Spec: Setup TS. Signal uses prior bars/ATR only; both directions cancel."""
        cfg = self.config
        self._pending.clear()
        if (
            len(self._history) < cfg.ts_lookback
            or self._ts_atr is None
            or not isfinite(self._ts_atr)
            or self._ts_atr <= 0
        ):
            return
        if bar.high - bar.low > cfg.ts_range_atr * self._ts_atr:
            return
        previous = list(self._history)[-cfg.ts_lookback:]
        signals = []
        for direction in Direction:
            sign = _sign(direction)
            lows = [_extremes(b, sign)[1] for b in previous]
            old_low = min(lows)
            age = next(i for i, low in enumerate(reversed(lows), 1) if low == old_low)
            _, low = _extremes(bar, sign)
            if age >= cfg.ts_min_age and low < old_low < sign * bar.close:
                stop = sign * (low - self._tick)
                signals.append(Pending(direction, bar.close, stop, self._index + 1))
        if len(signals) == 1 and isfinite(signals[0].stop) and signals[0].stop > 0:
            pending = signals[0]
            self._pending[pending.direction] = pending

    def _ts_update_atr(self, bar: DailyBar) -> None:
        """Spec: Setup TS > Sessions: seed mean TR, then Wilder, after signal evaluation."""
        tr = bar.high - bar.low
        if self._history:
            close = self._history[-1].close
            tr = max(tr, abs(bar.high - close), abs(bar.low - close))
        period = self.config.ts_atr_period
        if self._ts_atr is None:
            self._ts_trs.append(tr)
            if len(self._ts_trs) == period:
                self._ts_atr = sum(self._ts_trs) / period
                self._ts_trs.clear()
        else:
            self._ts_atr = (self._ts_atr * (period - 1) + tr) / period

    def _arm(self, direction: Direction, high: float, low: float, valid: int) -> None:
        sign = _sign(direction)
        level, stop = sign * (high + self._tick), sign * (low - self._tick)
        if sign * (level - stop) > 0 and level > 0 and stop > 0:
            self._pending[direction] = Pending(direction, level, stop, self._index + valid)

    def _e8(self, bar: DailyBar) -> None:
        cfg = self.config
        keep = []
        for candidate in self._candidates:  # chronological: newest confirmation wins ties
            day = self._index - candidate.day2 + 2
            _, low = _extremes(bar, _sign(candidate.direction))
            if cfg.e8_first_day <= day <= cfg.e8_last_day and low < candidate.low:
                self._arm(candidate.direction, candidate.high, candidate.low, cfg.e8_valid_sessions)
            elif day < cfg.e8_last_day:
                keep.append(candidate)
        self._candidates = keep
        if len(self._history) < cfg.e8_lookback + 1:
            return
        previous = list(self._history)[-(cfg.e8_lookback + 1) :]
        for direction in Direction:
            sign = _sign(direction)
            day1_high, day1_low = _extremes(previous[-1], sign)
            high, low = _extremes(bar, sign)
            if day1_low < min(_extremes(b, sign)[1] for b in previous[:-1]) and high > day1_high:
                self._candidates.append(Candidate(direction, self._index, high, low))

    def _cap(self, bar: DailyBar) -> None:
        cfg = self.config
        if len(self._history) < cfg.cap_lookback:
            return
        previous = list(self._history)[-cfg.cap_lookback :]
        width = bar.high - bar.low
        if (
            width > 0
            and bar.low < min(b.low for b in previous)
            and width > max(b.high - b.low for b in previous)
            and bar.close >= bar.high - cfg.cap_top_fraction * width
        ):
            self._arm(Direction.BULLISH, bar.high, bar.low, cfg.cap_valid_sessions)

    def exits(self) -> list[object]:
        out, self._exits = self._exits, []
        return out

    def _forget(self, ref: object) -> None:
        if self._position is not None and self._position[0] == ref:
            self._position = None
            self._exit_requested = False
            self._exits = [r for r in self._exits if r != ref]

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._forget(ref)

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        if (
            self._position is not None
            and self._position[0] == ref
            and result is not None
            and result.exit_reason.value == "end_of_data"
        ):
            self._flag("censored_position", result.exit_time)
        self._forget(ref)

    def integrity_records(self) -> list[dict]:
        """JSON-ready integrity findings for the coordinator's conjunctive gates tool."""
        return [dict(r) for r in self._integrity]

    def session_records(self, run_end: datetime | None = None) -> list[dict]:
        records = self.integrity_records()
        if self._day is not None and not self._finished and run_end is not None:
            records.append(
                {
                    "kind": "incomplete_session",
                    "symbol": self.symbol,
                    "time": run_end.isoformat(),
                    "session_date": self._day.isoformat(),
                    "trading_date": self._day.isoformat(),
                    "session": "daily_reversal",
                    "integrity_failed": True,
                    "start": (run_end - Timeframe.M1.duration).isoformat(),
                    "end": run_end.isoformat(),
                }
            )
        return records
