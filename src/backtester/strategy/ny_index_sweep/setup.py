"""One strategy-2 setup: sweep -> setup-TF BoS -> 3rd confluence tapped -> entry-TF BoS ->
entry-TF confluence tapped and confirmed -> entry.

Spec: strategy-ny-indices.md › General, › PM Session, › AM Session, › Rules (with the
user's answers of 2026-10-11). Described for a long (bullish bias), short mirrored.
`advance(ctx)` is called once per closed base (1m) candle inside the setup's window:

1. SWEEP: a 1m wick went below one of the last N swing lows of the sweep timeframe
   (strategy.py registers it). A deeper 1m wick moves the sweep extreme and restarts the
   count. Cancelled when no setup-TF BoS comes within X sweep-TF candles of the extreme
   (counted from the close of the sweep-TF candle containing it), or, with the close-beyond
   setting off, when a sweep-TF candle closes below the swept level.
2. BOS: a real bullish BoS on the setup TF (detectors/bos.py: the most recent swing high;
   none while the setup TF is already in an uptrend), closing at or after the extreme's 1m
   candle. The 3rd-confluence candidates are fixed then: the bullish zones of the
   confluence TF (AM: the setup TF; PM: 5m) formed by candles from the extreme's candle up
   to the BoS candle, those the BoS created (breaker, OB; on the setup TF) and the EQ of
   the leg sweep extreme -> BoS candle high. Already invalidated ones are left out; none
   left -> cancelled.
   Wait for the tap: a closed entry-TF candle after the BoS candle whose wick goes into a
   candidate (several at once: RANKING). A candidate closed through (its own TF) drops
   out. No tap within `tap_timeout` setup-TF candles after the BoS close -> cancelled.
3. TAPPED: the 3rd confluence (Z3) is set. Wait for a real bullish entry-TF BoS closing at
   or after the tapping candle (it may be that candle). Entry-TF confluence off: enter at
   its close. Otherwise the entry candidates are fixed: the bullish entry-TF zones formed
   in the entry BoS move (from its start, `move_start`, to the BoS candle), those that BoS
   created and its EQ; each is validated from the next entry-TF candle (zone.py: tap, then
   a green close above).
4. ENTRY: the first confirmation enters at that close (several: RANKING). An invalidated
   candidate drops out; an opposite entry-TF BoS goes back to 3.
5. IN_TRADE: one open trade per setup. When it closes (`trade_closed`), back to 3 with
   the same Z3 if it is still valid (a new entry-TF BoS after the exit), else to 2 with
   the next candidate (the tap timeout still counts from the original BoS).
In every step after the BoS: an opposite setup-TF BoS cancels the setup; Z3 closed through
-> back to 2 without it. The window's end ends every setup (strategy.py); trades keep
running in the engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from backtester.core.models import Candle, Direction, Timeframe
from backtester.detectors.bos import BreakOfStructure
from backtester.detectors.equilibrium import equilibrium_box, move_start
from backtester.detectors.swings import SwingPoint, is_doji
from backtester.detectors.zone import ZoneKind, ZoneState, ZoneValidator
from backtester.strategy.ny_index_sweep.config import RANKING, NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.frames import Frame, Zone, beyond, candle_open, wick
from backtester.strategy.ny_index_sweep.windows import TradingWindow

BASE = Timeframe.M1  # the base timeframe (strategy.py)
CREATED_BY_BOS = {ZoneKind.BREAKER, ZoneKind.ORDER_BLOCK}
OPPOSITE = {Direction.BULLISH: Direction.BEARISH, Direction.BEARISH: Direction.BULLISH}


class Step(Enum):
    SWEEP = "sweep"
    BOS = "bos"  # waiting for the 3rd confluence's tap
    TAPPED = "tapped"  # waiting for the entry-TF BoS
    ENTRY = "entry"  # waiting for an entry-TF confluence's confirmation
    IN_TRADE = "in_trade"
    DONE = "done"


@dataclass(frozen=True, slots=True)
class Route:
    sweep_tfs: tuple[Timeframe, ...]  # AM: 1h + 4h (one setup per wick); PM: 5m or 15m
    setup_tf: Timeframe
    entry_tf: Timeframe
    conf_tf: Timeframe  # where the 3rd confluences come from (AM: setup TF, PM: 5m)
    bos_within: int  # sweep-TF candles


@dataclass(frozen=True, slots=True)
class Signal:
    """Enter at the close of the current base candle."""

    setup: Setup
    direction: Direction
    at: datetime  # entry time (the candle's close)
    close: float  # entry price
    z3: Zone
    entry_zone: Zone | None  # None: entry-TF confluence off
    deepest: float  # deepest 1m wick after the setup BoS up to the entry (EQ stop loss)
    # what led to this entry (the setup moves on after the trade)
    bos: BreakOfStructure | None = None  # the setup-TF BoS
    tap_at: datetime | None = None  # close of the candle that tapped the 3rd confluence
    entry_bos: BreakOfStructure | None = None


@dataclass
class Context:
    """What `advance` sees at one base candle."""

    now: datetime  # its close time
    candle: Candle  # the base (1m) candle
    frames: dict[Timeframe, Frame]
    config: NyIndexSweepConfig
    doji_max_body: float


@dataclass(eq=False)
class Setup:
    window: TradingWindow
    direction: Direction
    route: Route
    swept: tuple[SwingPoint, ...]  # the swings taken (least to most extreme)
    sweep_tf: Timeframe  # timeframe of the most extreme swing taken
    extreme: float
    extreme_ts: datetime  # open time of the base candle with the extreme wick
    step: Step = Step.SWEEP
    bos: BreakOfStructure | None = None
    bos_high: float | None = None  # bullish: the BoS candle's high (the leg's end)
    candidates: list[Zone] = field(default_factory=list)
    z3: Zone | None = None
    tap_at: datetime | None = None
    entry_bos: BreakOfStructure | None = None
    entry_candidates: list[tuple[Zone, ZoneValidator]] = field(default_factory=list)
    deepest: float | None = None  # deepest base wick after the BoS candle
    trades: int = 0
    ended: str = ""  # why the setup ended (DONE)
    accepted: tuple[SwingPoint, ...] = ()  # levels a breakout accepted (strategy.py drops them)

    @property
    def level(self) -> float:
        """The swept level: the most extreme swing taken."""
        return self.swept[-1].price

    def end(self, why: str) -> None:
        self.step, self.ended = Step.DONE, why

    # --- per base candle -------------------------------------------------------------

    def advance(self, ctx: Context) -> Signal | None:
        if self.step is Step.DONE:
            return None
        if self.step is Step.SWEEP:
            self._sweep(ctx)
            return None
        frames, d = ctx.frames, self.direction
        sweep_frame = frames[self.sweep_tf]
        # Spec: strategy-ny-indices.md > AM step 3: valid throughout the setup.
        if (
            not ctx.config.sweep_close_beyond_counts
            and sweep_frame.closed
            and beyond(d, sweep_frame.current.close, self.level)
        ):
            self.end("sweep-TF close beyond the swept level")
            return None
        low = wick(d, ctx.candle)
        if ctx.now > self.bos.confirmed_at and (
            self.deepest is None or beyond(d, low, self.deepest)
        ):
            self.deepest = low
        if any(b.direction is OPPOSITE[d] for b in frames[self.route.setup_tf].breaks):
            self.end("opposite setup-TF BoS")
            return None
        self._drop_invalidated(ctx)
        if self.step is Step.DONE:
            return None
        if self.step is Step.BOS:
            self._wait_tap(ctx)
        if self.step is Step.TAPPED:
            self._wait_entry_bos(ctx)
            if self.step is Step.ENTRY and not ctx.config.entry_tf_confluence:
                return self._signal(ctx, None)
            return None  # the entry candidates are validated from the next candle
        if self.step is Step.ENTRY:
            return self._wait_entry(ctx)
        return None

    def _sweep(self, ctx: Context) -> None:
        d, cfg = self.direction, ctx.config
        low = wick(d, ctx.candle)
        if beyond(d, low, self.extreme):
            self.extreme, self.extreme_ts = low, ctx.candle.ts
        sweep_frame = ctx.frames[self.sweep_tf]
        if cfg.sweep_breakout_closes and sweep_frame.closed and self._breakout(ctx, sweep_frame):
            return
        # Spec: strategy-ny-indices.md › Rules, B8: equality counts, late gap events do not.
        deadline = candle_open(self.sweep_tf, self.extreme_ts) + self.sweep_tf.duration * (
            1 + self.route.bos_within
        )
        if ctx.now > deadline:
            self.end("no setup-TF BoS in time")
            return
        setup_frame = ctx.frames[self.route.setup_tf]
        bos = next((b for b in setup_frame.breaks if b.direction is d), None)
        if bos is not None and bos.confirmed_at >= self.extreme_ts + BASE.duration:
            if cfg.bos_before_top and bos.swing.index >= setup_frame.index_at(self.extreme_ts):
                bos = None  # breaks a swing made by or after the extreme's candle: not it
            if bos is not None:
                self._on_bos(ctx, bos)
                return
        if (
            not cfg.sweep_close_beyond_counts
            and sweep_frame.closed
            and beyond(d, sweep_frame.current.close, self.level)
        ):
            self.end("sweep-TF close beyond the swept level")
            return
        if ctx.now >= deadline:
            self.end("no setup-TF BoS in time")

    def _breakout(self, ctx: Context, frame: Frame) -> bool:
        """`sweep_breakout_closes` consecutive sweep-TF candles (dojis skipped) beyond the
        swept level, the newest closing beyond it (older ones: only the wick, with
        `sweep_breakout_wick_first`). Ends the setup and remembers the accepted levels."""
        d, cfg, level = self.direction, ctx.config, self.level
        view, closes = frame.view, []
        for i in range(view.cursor, -1, -1):
            candle = view[i]
            if is_doji(candle, ctx.doji_max_body):
                continue
            closed = beyond(d, candle.close, level)
            wick_only = cfg.sweep_breakout_wick_first and closes
            if not (beyond(d, wick(d, candle), level) if wick_only else closed):
                return False
            closes.append(candle.close)
            if len(closes) == cfg.sweep_breakout_closes:
                break
        else:
            return False
        accepted = max(closes) if d is Direction.BULLISH else min(closes)
        self.accepted = tuple(s for s in self.swept if beyond(d, accepted, s.price))
        self.end(f"breakout: {len(closes)} sweep-TF closes beyond the swept level")
        return True

    def _on_bos(self, ctx: Context, bos: BreakOfStructure) -> None:
        d, frames, cfg = self.direction, ctx.frames, ctx.config
        setup_frame, conf_frame = frames[self.route.setup_tf], frames[self.route.conf_tf]
        candle = setup_frame.current
        self.bos = bos
        self.bos_high = candle.high if d is Direction.BULLISH else candle.low
        kinds = cfg.confluence_kinds
        start = candle_open(self.route.conf_tf, self.extreme_ts)
        found = [
            z
            for z in conf_frame.recent
            if z.box.direction is d
            and z.box.kind in kinds
            and z.start_ts >= start
            and z.box.created_at <= bos.confirmed_at
        ]
        found += [
            z
            for z in setup_frame.recent
            if z.box.direction is d
            and z.box.kind in kinds & CREATED_BY_BOS
            and z.box.created_at == bos.confirmed_at
            and z not in found
        ]
        if ZoneKind.EQUILIBRIUM in kinds:
            box = equilibrium_box(
                d,
                setup_frame.index_at(self.extreme_ts),
                self.extreme,
                setup_frame.view.cursor,
                self.bos_high,
                bos.confirmed_at,
            )
            found.append(Zone(box, self.route.setup_tf, setup_frame.view[box.start_index].ts))
        self.candidates = [z for z in found if not frames[z.tf].invalidated(z)]
        self.step = Step.BOS
        if not self.candidates:
            self.end("no 3rd confluence in the BoS move")

    def _drop_invalidated(self, ctx: Context) -> None:
        """Candidates closed through by a candle of their own timeframe that closed now."""
        d = self.direction

        def broken(z: Zone) -> bool:
            frame = ctx.frames[z.tf]
            return (
                frame.closed
                and frame.view.cursor > z.box.created_index
                and beyond(d, frame.current.close, z.box.far)
            )

        self.candidates = [z for z in self.candidates if not broken(z)]
        if self.z3 is not None and self.z3 not in self.candidates:
            self.z3, self.tap_at, self.entry_bos, self.entry_candidates = None, None, None, []
            if self.step in (Step.TAPPED, Step.ENTRY):
                self.step = Step.BOS
        if not self.candidates and self.step is not Step.IN_TRADE:
            self.end("every 3rd confluence closed through")

    def _wait_tap(self, ctx: Context) -> None:
        # Spec: strategy-ny-indices.md › Rules, B8: reject post-gap taps before transitioning.
        timeout = self.bos.confirmed_at + self.route.setup_tf.duration * ctx.config.tap_timeout
        if ctx.now > timeout:
            self.end("3rd confluence not tapped in time")
            return
        d, entry = self.direction, ctx.frames[self.route.entry_tf]
        if entry.closed and ctx.now > self.bos.confirmed_at:
            low = wick(d, entry.current)
            tapped = [z for z in self.candidates if beyond(d, low, z.box.near)]
            if tapped:
                self.z3 = best(tapped, d)
                self.tap_at = ctx.now
                self.step = Step.TAPPED
                return
        if ctx.now >= timeout:
            self.end("3rd confluence not tapped in time")

    def _wait_entry_bos(self, ctx: Context) -> None:
        d, frame = self.direction, ctx.frames[self.route.entry_tf]
        bos = next((b for b in frame.breaks if b.direction is d), None)
        if bos is None or bos.confirmed_at < self.tap_at:
            return
        self.entry_bos = bos
        self.step = Step.ENTRY
        if not ctx.config.entry_tf_confluence:
            return
        kinds, candle, view = ctx.config.confluence_kinds, frame.current, frame.view
        start_index, start_price = move_start(view, d, bos.swing.index)
        start = view[start_index].ts
        found = [
            z
            for z in frame.recent
            if z.box.direction is d
            and z.box.kind in kinds
            and (
                (z.start_ts >= start and z.box.created_at <= bos.confirmed_at)
                or (z.box.kind in CREATED_BY_BOS and z.box.created_at == bos.confirmed_at)
            )
        ]
        if ZoneKind.EQUILIBRIUM in kinds:
            end = candle.high if d is Direction.BULLISH else candle.low
            box = equilibrium_box(d, start_index, start_price, view.cursor, end, bos.confirmed_at)
            found.append(Zone(box, frame.tf, start))
        self.entry_candidates = [
            (z, ZoneValidator(z.box, ctx.doji_max_body)) for z in found if not frame.invalidated(z)
        ]

    def _wait_entry(self, ctx: Context) -> Signal | None:
        d, frame = self.direction, ctx.frames[self.route.entry_tf]
        if any(b.direction is OPPOSITE[d] for b in frame.breaks):
            self.step, self.entry_bos, self.entry_candidates = Step.TAPPED, None, []
            self.tap_at = ctx.now  # a new entry-TF BoS from now on
            return None
        if not frame.closed or ctx.now <= self.entry_bos.confirmed_at:
            return None
        confirmed, still = [], []
        for z, validator in self.entry_candidates:
            states = [t.state for t in validator.on_candle(frame.view)]
            if ZoneState.CONFIRMED in states:
                confirmed.append(z)
            elif ZoneState.INVALIDATED not in states:
                still.append((z, validator))
        self.entry_candidates = still
        if confirmed:
            return self._signal(ctx, best(confirmed, d))
        return None

    def _signal(self, ctx: Context, entry_zone: Zone | None) -> Signal:
        self.step = Step.IN_TRADE
        self.trades += 1
        deepest = self.deepest if self.deepest is not None else wick(self.direction, ctx.candle)
        return Signal(
            self,
            self.direction,
            ctx.now,
            ctx.candle.close,
            self.z3,
            entry_zone,
            deepest,
            self.bos,
            self.tap_at,
            self.entry_bos,
        )

    # --- after the trade -------------------------------------------------------------

    def trade_closed(self, at: datetime) -> None:
        """The setup's trade closed at `at`: re-entry possible (strategy.py checks the max
        trades per session)."""
        if self.step is not Step.IN_TRADE:
            return
        self.entry_bos, self.entry_candidates = None, []
        if self.z3 is not None:
            self.step, self.tap_at = Step.TAPPED, at
        else:
            self.step = Step.BOS


def best(zones: list[Zone], direction: Direction) -> Zone:
    """By RANKING; same kind: the one price reaches first (bullish: the highest near edge)."""
    sign = 1 if direction is Direction.BULLISH else -1
    return min(zones, key=lambda z: (RANKING.index(z.box.kind), -sign * z.box.near))
