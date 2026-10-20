"""Strategy 6 (opening-range breakout) as the `Strategy` the engine runs.

Spec: docs/strategy-opening-range.md. Per symbol the config names one or two sessions (FX and
metals: London and New York). Each session is tracked on its own, in its own time zone, from
the 1m candles that close in (open, exit]:

- `range` mode: the high / low of the candles closing in (open, open + range_minutes];
  `band` mode: the close of the candle closing at the open +/- band_atr x daily ATR.
- The signal is the first 1m candle after that (until open + entry_window_minutes) whose CLOSE
  is beyond the upper (long) or lower (short) level; entry at its close, stop at the opposite
  level, optional target in R. One trade a session; with `max_reversals` = 1 a stop-out arms
  one trade the other way (close beyond the other side, stop at the first side).
- A trade still open at the session end is closed by `exits()` at the close of the candle
  closing at `exit_time` (or at the first later candle).
- The daily ATR is the Wilder ATR of this session's own daily ranges (high - low of the
  candles in (open, exit], with the previous session's last close), known before today's
  session. A session counts as soon as it has one candle (the spec names no "regular day"
  test). No ATR, no trade.
- Filters, evaluated once on the first candle after the range (band: after the open): range
  width, NR4 / inside (strict comparisons of the previous sessions' high - low) and tick
  volume. A failed filter skips the whole session, also when a later breakout would pass.
  The volume filter applies to the first signal only, not to a reversal. It needs
  `Candle.volume`: histdata candles carry 0, then the filter skips every session (it never
  passes silently), and it also skips while fewer than `volume_lookback` sessions of history
  exist or the usual volume of that minute is 0.

Everything is read from the current candle only; state is built incrementally (no lookahead).
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import Order, Strategy, UnsupportedSymbolError
from backtester.strategy.opening_range.config import (
    SYMBOL_CLASS,
    EntryMode,
    NarrowDay,
    OpeningRangeConfig,
    SessionSpec,
)

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult

# warm-up in calendar days: trading days are 5 of 7 days, plus a margin for holidays
CALENDAR_PER_TRADING_DAY = 1.5
WARMUP_MARGIN_DAYS = 7
STOP_LOSS = "stop_loss"  # ExitReason.STOP_LOSS.value (strategy/ may not import engine/ at runtime)
NR_SESSIONS = 4  # NR4: the previous session is the narrowest of this many


@dataclass(slots=True)
class _Session:
    """One session (e.g. FX London) of the symbol: its history and the day in progress."""

    name: str
    spec: SessionSpec
    tz: ZoneInfo
    # history of the sessions finished so far
    prev_close: float | None = None
    atr: float | None = None
    trs: list[float] = field(default_factory=list)  # true ranges until the ATR exists
    ranges: deque[tuple[float, float]] = field(default_factory=lambda: deque(maxlen=NR_SESSIONS))
    volumes: deque[dict[int, float]] = field(default_factory=deque)  # offset -> tick volume
    # the day in progress
    day: date | None = None
    high: float = 0.0
    low: float = 0.0
    last_close: float = 0.0
    seen: bool = False  # a candle closing in (open, exit] has been taken in
    day_volume: dict[int, float] = field(default_factory=dict)
    open_close: float | None = None  # band mode: close of the candle closing at the open
    range_high: float = 0.0
    range_low: float = 0.0
    range_seen: bool = False
    armed: bool = False  # the levels below are set and the filters passed
    done: bool = False  # nothing more to trade this session
    up: float = 0.0  # a close above breaks out long; a long's stop is `down`
    down: float = 0.0
    taken: bool = False  # the first trade was ordered
    ref: int | None = None  # the open (or just ordered) trade
    reversal: Direction | None = None  # armed: the direction of the one reversal trade
    reversals_left: int = 0
    # read-only bookkeeping for `OpeningRange.setup_state` (never used by the trading logic)
    last_offset: int = -1  # offset of the latest candle taken in
    armed_offset: int = -1  # offset of the candle that set the levels
    rel_volume: float | None = None  # signal volume / usual volume at the last volume check


@dataclass(frozen=True, slots=True)
class SetupState:
    """Where today's session stands (for the Live page). Read-only; see `setup_state`."""

    phase: str  # waiting_session, range_forming, range_set, waiting_breakout, ordered, done
    up: float | None = None  # breakout levels, once set
    down: float | None = None
    rel_volume: float | None = None  # tick volume of the signal candle vs its usual value
    traded: bool = False  # a trade was ordered today


class OpeningRange(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False  # a day trade: no break-even at the next session

    def __init__(
        self,
        symbol: str,
        config: OpeningRangeConfig | None = None,
        detectors: DetectorSettings | None = None,  # unused: no shared detector is needed
    ):
        self.symbol = symbol
        self.config = config = config or OpeningRangeConfig()
        market = SYMBOL_CLASS.get(symbol)
        if market is None or market not in config.sessions:
            raise UnsupportedSymbolError(
                f"opening_range: no session for {symbol}. "
                f"It trades: {', '.join(sorted(SYMBOL_CLASS))}"
            )
        self._sessions = [
            _Session(name, spec, ZoneInfo(spec.zone))
            for name, spec in config.sessions[market].items()
        ]
        self._open: dict[int, tuple[_Session, datetime]] = {}  # ref -> (session, exit instant)
        self._to_close: list[object] = []
        self._next_ref = 0
        history = max(
            config.atr_period,
            config.volume_lookback if config.min_rel_volume > 0 else 0,
            NR_SESSIONS if config.narrow_day_filter is not NarrowDay.OFF else 0,
        )
        self.min_warmup_days = math.ceil((history + 1) * CALENDAR_PER_TRADING_DAY) + (
            WARMUP_MARGIN_DAYS
        )

    # --- the loop -------------------------------------------------------------------------

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        candle = views[self.base_timeframe].current
        self._queue_exits(now)
        orders: list[Order] = []
        for st in self._sessions:
            local = now.astimezone(st.tz)
            t = local.time()
            if not st.spec.open_time <= t <= st.spec.exit_time:
                continue
            today = local.date()
            if today != st.day:
                self._finish(st)
                self._start(st, today)
            offset = int(
                (
                    datetime.combine(today, t) - datetime.combine(today, st.spec.open_time)
                ).total_seconds()
                // 60
            )
            st.last_offset = offset
            if offset == 0:
                st.open_close = candle.close
                continue
            self._take_in(st, offset, candle)
            order = self._signal(st, offset, candle, now)
            if order is not None:
                orders.append(order)
        return orders

    # --- the session in progress ------------------------------------------------------------

    @staticmethod
    def _start(st: _Session, day: date) -> None:
        st.day, st.seen, st.day_volume = day, False, {}
        st.open_close, st.range_seen, st.armed, st.done = None, False, False, False
        st.taken, st.ref, st.reversal = False, None, None
        st.reversals_left = 0
        st.last_offset, st.armed_offset, st.rel_volume = -1, -1, None

    def _take_in(self, st: _Session, offset: int, candle: Candle) -> None:
        if not st.seen:
            st.high, st.low, st.seen = candle.high, candle.low, True
        else:
            st.high, st.low = max(st.high, candle.high), min(st.low, candle.low)
        st.last_close = candle.close
        st.day_volume[offset] = candle.volume
        if self.config.entry_mode is EntryMode.RANGE and offset <= self.config.range_minutes:
            if not st.range_seen:
                st.range_high, st.range_low, st.range_seen = candle.high, candle.low, True
            else:
                st.range_high = max(st.range_high, candle.high)
                st.range_low = min(st.range_low, candle.low)

    def _finish(self, st: _Session) -> None:
        """Close the day in progress: it feeds the ATR and the filters' history."""
        if st.day is None or not st.seen:
            return
        tr = st.high - st.low
        if st.prev_close is not None:
            tr = max(tr, abs(st.high - st.prev_close), abs(st.low - st.prev_close))
        st.prev_close = st.last_close
        period = self.config.atr_period
        if st.atr is None:
            st.trs.append(tr)
            if len(st.trs) == period:
                st.atr = sum(st.trs) / period
        else:
            st.atr = (st.atr * (period - 1) + tr) / period
        st.ranges.append((st.high, st.low))
        st.volumes.append(st.day_volume)
        while len(st.volumes) > self.config.volume_lookback:
            st.volumes.popleft()

    # --- signals -----------------------------------------------------------------------------

    def _arm(self, st: _Session) -> None:
        """First candle after the range (band: after the open): levels and filters, once."""
        cfg = self.config
        st.armed = True
        atr = st.atr
        if atr is None or atr <= 0:
            st.done = True
            return
        if cfg.entry_mode is EntryMode.RANGE:
            if not st.range_seen:
                st.done = True
                return
            st.up, st.down = st.range_high, st.range_low
            if cfg.max_range_atr > 0 and (st.up - st.down) > cfg.max_range_atr * atr:
                st.done = True
                return
        else:
            if st.open_close is None:
                st.done = True
                return
            st.up = st.open_close + cfg.band_atr * atr
            st.down = st.open_close - cfg.band_atr * atr
        if not self._narrow_day_ok(st):
            st.done = True
            return
        st.reversals_left = cfg.max_reversals

    def _narrow_day_ok(self, st: _Session) -> bool:
        mode = self.config.narrow_day_filter
        if mode is NarrowDay.OFF:
            return True
        if mode is NarrowDay.NR4:
            if len(st.ranges) < NR_SESSIONS:
                return False
            widths = [h - lo for h, lo in st.ranges]
            return all(widths[-1] < w for w in widths[:-1])
        if len(st.ranges) < 2:
            return False
        (before_high, before_low), (prev_high, prev_low) = st.ranges[-2], st.ranges[-1]
        return prev_high < before_high and prev_low > before_low

    def _volume_ok(self, st: _Session, offset: int, candle: Candle) -> bool:
        cfg = self.config
        if cfg.min_rel_volume <= 0:
            return True
        if len(st.volumes) < cfg.volume_lookback or candle.volume <= 0:
            return False  # no volume (histdata) or too little history: skip, never pass
        usual = [v[offset] for v in st.volumes if offset in v]
        if not usual or sum(usual) <= 0:
            return False
        mean = sum(usual) / len(usual)
        st.rel_volume = candle.volume / mean
        return candle.volume >= cfg.min_rel_volume * mean

    def _signal(self, st: _Session, offset: int, candle: Candle, now: datetime) -> Order | None:
        cfg = self.config
        if st.done:
            return None
        if not st.armed:
            if cfg.entry_mode is EntryMode.RANGE and offset <= cfg.range_minutes:
                return None  # still inside the opening range
            self._arm(st)
            st.armed_offset = offset
            if st.done:
                return None
        if offset > cfg.entry_window_minutes:
            st.done = True
            return None
        if st.ref is not None:
            return None  # a trade is open (or ordered)
        if st.reversal is not None:
            direction = st.reversal
        elif st.taken:
            return None
        elif candle.close > st.up:
            direction = Direction.BULLISH
        elif candle.close < st.down:
            direction = Direction.BEARISH
        else:
            return None
        beyond = candle.close > st.up if direction is Direction.BULLISH else candle.close < st.down
        if not beyond:
            return None
        if not st.taken and not self._volume_ok(st, offset, candle):
            st.done = True  # the signal candle failed the volume filter: skip the session
            return None
        return self._order(st, direction, candle, now)

    def _order(self, st: _Session, direction: Direction, candle: Candle, now: datetime) -> Order:
        bullish = direction is Direction.BULLISH
        stop = st.down if bullish else st.up
        entry = candle.close
        take_profit = None
        if self.config.target_r > 0:
            sign = 1 if bullish else -1
            take_profit = entry + sign * self.config.target_r * abs(entry - stop)
        ref = self._next_ref
        self._next_ref += 1
        st.ref, st.taken, st.reversal = ref, True, None
        exit_local = datetime.combine(st.day, st.spec.exit_time, tzinfo=st.tz)
        self._open[ref] = (st, exit_local.astimezone(now.tzinfo))
        return Order(
            direction,
            entry,
            stop,
            take_profit,
            reason=f"opening range {self.config.entry_mode.value} {st.name}",
            ref=ref,
        )

    # --- read-only view for the Live page --------------------------------------------------

    def setup_state(self, now: datetime) -> SetupState:
        """Phase of the session of `now` (the one whose window holds `now`, else the first).
        Reads state only; changes nothing and decides nothing."""
        st = next(
            (
                s
                for s in self._sessions
                if s.spec.open_time <= now.astimezone(s.tz).time() <= s.spec.exit_time
            ),
            self._sessions[0],
        )
        local = now.astimezone(st.tz)
        t = local.time()
        if local.weekday() >= 5 or t < st.spec.open_time:
            return SetupState("waiting_session")
        if t > st.spec.exit_time:
            return SetupState(
                "done", rel_volume=self._rel(st, local), traded=self._today(st, local)
            )
        if st.day != local.date():
            return SetupState("waiting_session")  # no candle of today yet
        levels = (st.up, st.down) if st.armed and st.up != st.down else (None, None)
        up, down = levels
        traded = st.taken
        if st.ref is not None:
            phase = "ordered"
        elif st.done or (st.taken and st.reversal is None):
            phase = "done"
        elif not st.armed:
            phase = "range_forming"
        elif st.last_offset == st.armed_offset:
            phase = "range_set"
        else:
            phase = "waiting_breakout"
        return SetupState(phase, up, down, st.rel_volume, traded)

    @staticmethod
    def _today(st: _Session, local: datetime) -> bool:
        return st.day == local.date() and st.taken

    @staticmethod
    def _rel(st: _Session, local: datetime) -> float | None:
        return st.rel_volume if st.day == local.date() else None

    # --- exits and the engine's callbacks ---------------------------------------------------

    def _queue_exits(self, now: datetime) -> None:
        """Queue open trades for `exits` at the session end, or at the first later candle."""
        for ref, (_, exit_at) in list(self._open.items()):
            if now >= exit_at:
                self._to_close.append(ref)
                del self._open[ref]

    def exits(self) -> list[object]:
        out, self._to_close = self._to_close, []
        return out

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        entry = self._open.pop(ref, None)  # never filled (cost filter): the session is used up
        if entry is not None:
            entry[0].ref = None

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        entry = self._open.pop(ref, None)
        if entry is None:  # closed by the session-end exit (already out of `_open`)
            for st in self._sessions:
                if st.ref == ref:
                    st.ref = None
            return
        st = entry[0]
        st.ref = None
        if result.exit_reason.value == STOP_LOSS and st.reversals_left > 0:
            st.reversals_left -= 1
            st.reversal = (
                Direction.BEARISH if result.direction is Direction.BULLISH else Direction.BULLISH
            )
