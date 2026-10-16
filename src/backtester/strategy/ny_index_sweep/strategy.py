"""Strategy 2 (NY Open index sweep) as the `Strategy` the engine runs.

Spec: strategy-ny-indices.md. Base timeframe 1m; 5m, 15m, 1h and New York-aligned 4h
(closing 02:00, 06:00, ... ET; the runner loads them that way, `h4_alignment`). Per closed
1m candle:
1. Every timeframe's detectors see the candles closed by now (frames.py).
2. Windows (windows.py): the first candle closing in a window freezes the bias and, AM,
   the route, from the candles closed at the window's start: AM bias = 4h trend, route:
   1h trend = 4h trend -> setup 5m / entry 1m, else 15m / 5m (no 1h trend counts as
   different); PM bias = 15m trend, two setup timeframes (5m and 15m), entry 1m, 3rd
   confluences on 5m. No bias (no BoS yet) -> no trades in that window. A candle closing
   after the window ends every setup of it (open trades keep running).
3. Sweeps: a 1m wick beyond one of the last N swings (bias long: lows) of the sweep
   timeframe(s), confirmed by candles closed before that 1m candle opened, starts a setup
   (AM: 1h and 4h together, one setup per wick; PM: one per 5m / 15m). Only one setup per
   route waits for its BoS at a time; a deeper wick moves its extreme (setup.py).
4. Every live setup advances (setup.py). PM: a 15m setup reaching its BoS ends the 5m
   setups of the same sweep (same extreme price, the 5m sweeping candle inside the 15m
   one); their trades keep running.
5. Signals become orders (targets.py) unless the window already had
   `max_trades_per_session` entries, or the entry is in the best time and
   `include_best_time_trades` is off, or the trend filter (if on) points the other way
   (trend_filter.py; the setup stays valid). `decisions` keeps every signal and what happened.
   Volume filter (if on): the entry candle's tick volume against the usual volume of its
   minute after the window's open (see `_volume_ok`); no volume, too little history or a
   usual volume of 0 reject the signal, like the trend filter.
6. `close_before_rollover`: trades still open at 17:00 ET minus `rollover_close_minutes`
   close at that 1m close (`exits`), so they pay no swap.
Trades in R only. TP1 / TP2 / TP3 a third each; break-even with costs after TP1.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from backtester.core.models import Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.data.resample import H4Alignment
from backtester.detectors.settings import DetectorSettings
from backtester.detectors.swings import SwingKind, SwingPoint
from backtester.sessions import ROLLOVER_TIME, ROLLOVER_ZONE
from backtester.strategy.base import Order, Strategy
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.frames import Frame, beyond, candle_open, wick
from backtester.strategy.ny_index_sweep.setup import Context, Route, Setup, Signal, Step
from backtester.strategy.ny_index_sweep.targets import Rejected, Targets, targets
from backtester.strategy.ny_index_sweep.trend_filter import TrendFilter
from backtester.strategy.ny_index_sweep.windows import (
    TradingWindow,
    Window,
    is_best_time,
    window_of,
)

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult  # only the callback's type

M1, M5, M15, H1, H4 = Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.H1, Timeframe.H4
SWEPT_KIND = {Direction.BULLISH: SwingKind.LOW, Direction.BEARISH: SwingKind.HIGH}
BEST_TIME_TAG = "best_time"
# warm-up in calendar days for the volume history: 5 trading days of 7, plus a margin for holidays
CALENDAR_PER_TRADING_DAY = 1.5
WARMUP_MARGIN_DAYS = 7


@dataclass
class WindowState:
    window: TradingWindow
    bias: Direction | None
    routes: tuple[Route, ...]
    setups: list[Setup] = field(default_factory=list)
    trades: int = 0


@dataclass(frozen=True, slots=True)
class Decision:
    signal: Signal
    order: Order | None
    targets: Targets | None
    rejected: str  # why there is no order ("" if there is one)


class NyIndexSweep(Strategy):
    base_timeframe = M1
    timeframes = (M1, M5, M15, H1, H4)
    h4_alignment = H4Alignment.NEW_YORK
    # loaded from the first cached day, not only the warm-up: untouched highs and never
    # tapped zones from long ago are TP levels (spec › Open points: ATH, warm-up)
    full_history = (M15, H1, H4)
    uses_session_break_even = False  # break-even only after TP1

    def __init__(
        self,
        symbol: str,
        config: NyIndexSweepConfig | None = None,
        detectors: DetectorSettings | None = None,
    ):
        self.symbol = symbol
        self.config = config = config or NyIndexSweepConfig()
        self.detectors = detectors = detectors or DetectorSettings()
        self.doji_max_body = doji = detectors.swings.doji_threshold(symbol)
        fvg, ob, atr = detectors.fvg, detectors.order_block, config.atr_period
        self.frames = {
            M1: Frame(M1, doji, fvg, ob),
            M5: Frame(M5, doji, fvg, ob, atr_period=atr),
            M15: Frame(M15, doji, fvg, ob, tp_levels=True, atr_period=atr),
            H1: Frame(H1, doji, fvg, ob, tp_levels=True, atr_period=atr),
            H4: Frame(H4, doji, fvg, ob, tp_levels=True, atr_period=atr),
        }
        self.trend_filter = (
            TrendFilter(config.trend_filter) if config.trend_filter.enabled else None
        )
        # tick volume by minute after the window open, per window kind and New York date
        self._volumes: dict[Window, dict[date, dict[int, float]]] = defaultdict(dict)
        history = config.volume_lookback if config.min_rel_volume > 0 else 0
        if history:
            self.min_warmup_days = math.ceil((history + 1) * CALENDAR_PER_TRADING_DAY) + (
                WARMUP_MARGIN_DAYS
            )
        self._candle_volume = 0.0  # tick volume of the candle being processed
        self.window: WindowState | None = None
        self.decisions: list[Decision] = []
        self.ended: list[Setup] = []  # every setup that ended, for inspection
        self._accepted: set[SwingPoint] = set()  # levels a breakout accepted: not sweepable
        self._open: list[tuple[Setup, datetime]] = []  # (ref, entry time) of each open trade
        self._to_close: list[Setup] = []

    # --- engine interface --------------------------------------------------------------

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        for tf in (H4, H1, M15, M5, M1):
            self.frames[tf].update(views[tf])
        if self.config.close_before_rollover:
            self._close_before_rollover(now)
        if self.trend_filter is not None:
            self.trend_filter.update(views[self.config.trend_filter.timeframe])
        candle = views[M1].current
        self._candle_volume = candle.volume
        self._update_window(now)
        ws = self.window
        if ws is not None and self.config.min_rel_volume > 0:
            self._record_volume(ws.window, now, candle.volume)
        if ws is None or ws.bias is None:
            return []
        ctx = Context(now, candle, self.frames, self.config, self.doji_max_body)
        self._register_sweeps(ctx, ws)
        signals = []
        for setup in ws.setups:
            was = setup.step
            signal = setup.advance(ctx)
            if signal is not None:
                signals.append(signal)
            if was is Step.SWEEP and setup.step is not Step.SWEEP:
                self._replace_5m_setups(ws, setup)
        self._prune(ws)
        return [order for s in signals if (order := self._order(ws, s)) is not None]

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        if isinstance(ref, Setup):
            self._open = [(s, t) for s, t in self._open if s is not ref]
            ref.trade_closed(result.exit_time)

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        """Cost filter: the order was never filled, so it counts no trade and the setup
        may enter again (risk-management.md › Costs › Cost filter)."""
        if not isinstance(ref, Setup):
            return
        self._open = [(s, t) for s, t in self._open if s is not ref]
        if self.window is not None and self.window.window == ref.window:
            self.window.trades -= 1
        ref.trade_closed(now)

    def exits(self) -> list[object]:
        out, self._to_close = self._to_close, []
        return out

    def _close_before_rollover(self, now: datetime) -> None:
        """Open trades entered before today's cutoff (17:00 ET minus the setting) close at
        the first close at or after it (spec › Close before the rollover)."""
        day = now.astimezone(ROLLOVER_ZONE).date()
        cutoff = datetime.combine(day, ROLLOVER_TIME, ROLLOVER_ZONE) - timedelta(
            minutes=self.config.rollover_close_minutes
        )
        if now >= cutoff:
            self._to_close += [ref for ref, entry in self._open if entry < cutoff]

    # --- windows, sweeps -------------------------------------------------------------

    def _update_window(self, now: datetime) -> None:
        w = window_of(now, self.config.windows)
        if self.window is not None and (w is None or w != self.window.window):
            for setup in self.window.setups:
                setup.end("window end")
            self._prune(self.window)
            self.window = None
        if w is not None and self.window is None:
            self.window = self._open_window(w)

    def _open_window(self, w: TradingWindow) -> WindowState:
        cfg, f = self.config, self.frames
        if w.kind is Window.AM:
            bias = f[H4].trend_at(w.start)
            same = bias is not None and f[H1].trend_at(w.start) is bias
            setup_tf, entry_tf = (M5, M1) if same else (M15, M5)
            routes = (Route((H1, H4), setup_tf, entry_tf, setup_tf, cfg.bos_within_am),)
        else:
            bias = f[M15].trend_at(w.start)
            routes = tuple(Route((tf,), tf, M1, M5, cfg.bos_within_pm) for tf in (M5, M15))
        return WindowState(w, bias, routes)

    def _register_sweeps(self, ctx: Context, ws: WindowState) -> None:
        d, candle = ws.bias, ctx.candle
        low = wick(d, candle)
        for route in ws.routes:
            if any(s.route is route and s.step is Step.SWEEP for s in ws.setups):
                continue  # one setup per route waits for its BoS; setup.py moves its extreme
            levels = [
                (s, tf)
                for tf in route.sweep_tfs
                for s in self.frames[tf].last_swings(
                    SWEPT_KIND[d], self.config.sweep_lookback, confirmed_by=candle.ts
                )
            ]
            levels = [(s, tf) for s, tf in levels if s not in self._accepted]
            swept = [(s, tf) for s, tf in levels if beyond(d, low, s.price)]
            if swept and self.config.sweep_equal_highs:
                required = self._required_level(d, levels)
                if required not in swept:
                    swept = []
            if not swept:
                continue
            sign = 1 if d is Direction.BULLISH else -1
            swept.sort(key=lambda p: (sign * -p[0].price, p[1].value))  # least to most extreme
            ws.setups.append(
                Setup(
                    ws.window,
                    d,
                    route,
                    tuple(s for s, _ in swept),
                    swept[-1][1],
                    low,
                    candle.ts,
                )
            )

    def _required_level(
        self, d: Direction, levels: list[tuple[SwingPoint, Timeframe]]
    ) -> tuple[SwingPoint, Timeframe]:
        """`sweep_equal_highs`: the least extreme level within the tolerance (x ATR of the
        sweep TF, 0 while unknown) of the most extreme one."""
        sign = 1 if d is Direction.BEARISH else -1  # most extreme: highest high / lowest low
        top_swing, top_tf = max(levels, key=lambda p: sign * p[0].price)
        atr = self.frames[top_tf].atr()
        tolerance = self.config.sweep_equal_tolerance_atr * (atr or 0.0)
        group = [p for p in levels if sign * (top_swing.price - p[0].price) <= tolerance]
        return min(group, key=lambda p: sign * p[0].price)

    def _replace_5m_setups(self, ws: WindowState, setup: Setup) -> None:
        """PM: a 15m setup's BoS ends the 5m setups of the same sweep."""
        if (
            setup.step is Step.DONE
            or setup.route.setup_tf is not M15
            or ws.window.kind is Window.AM
        ):
            return
        for other in ws.setups:
            if (
                other.route.setup_tf is M5
                and other.step is not Step.DONE
                and other.extreme == setup.extreme
                and _inside(other.extreme_ts, M5, setup.extreme_ts, M15)
            ):
                other.end("replaced by the 15m setup of the same sweep")

    def _prune(self, ws: WindowState) -> None:
        done = [s for s in ws.setups if s.step is Step.DONE]
        if done:
            self.ended += done
            for s in done:
                self._accepted.update(s.accepted)
            ws.setups = [s for s in ws.setups if s.step is not Step.DONE]

    # --- volume filter -----------------------------------------------------------------

    def _record_volume(self, w: TradingWindow, now: datetime, volume: float) -> None:
        days = self._volumes[w.kind]
        days.setdefault(w.trading_date, {})[_minute(now, w)] = volume
        while len(days) > self.config.volume_lookback + 1:
            del days[min(days)]

    def _volume_ok(self, w: TradingWindow, at: datetime, volume: float) -> bool:
        """Entry candle volume >= min_rel_volume x the mean volume of the same minute after
        the window open over the previous `volume_lookback` sessions of this window kind.
        No volume, too little history or a usual volume of 0: False (never passes silently)."""
        cfg = self.config
        days = self._volumes[w.kind]
        previous = sorted(d for d in days if d < w.trading_date)[-cfg.volume_lookback :]
        if len(previous) < cfg.volume_lookback or volume <= 0:
            return False
        usual = [days[d][m] for d in previous if (m := _minute(at, w)) in days[d]]
        if not usual or sum(usual) <= 0:
            return False
        return volume >= cfg.min_rel_volume * (sum(usual) / len(usual))

    # --- orders ------------------------------------------------------------------------

    def _order(self, ws: WindowState, signal: Signal) -> Order | None:
        setup, cfg = signal.setup, self.config
        best = is_best_time(signal.at, ws.window)
        rejected, found, order = "", None, None
        if ws.trades >= cfg.max_trades_per_session:
            rejected = f"max {cfg.max_trades_per_session} trade(s) per session reached"
            setup.end(rejected)
        elif best and not cfg.include_best_time_trades:
            rejected = "best-time trades excluded"
            setup.trade_closed(signal.at)
        elif self.trend_filter is not None and signal.direction is not self.trend_filter.direction:
            trend = self.trend_filter.direction
            rejected = f"against the trend filter ({trend.value if trend else 'no trend yet'})"
            setup.trade_closed(signal.at)
        elif cfg.min_rel_volume > 0 and not self._volume_ok(
            ws.window, signal.at, self._candle_volume
        ):
            rejected = f"volume below {cfg.min_rel_volume:g} x usual"
            setup.trade_closed(signal.at)
        else:
            result = targets(signal, self.frames, cfg, self.detectors.equilibrium)
            if isinstance(result, Rejected):
                rejected = result.reason
                setup.trade_closed(signal.at)
            else:
                found = result
                order = self._make_order(ws, signal, result, best)
                self._open.append((setup, signal.at))
                ws.trades += 1
        self.decisions.append(Decision(signal, order, found, rejected))
        return order

    def _make_order(self, ws: WindowState, signal: Signal, t: Targets, best: bool) -> Order:
        setup, tps = signal.setup, [lv.price for lv in t.take_profits]
        third = 1 / 3
        tp1_share = {1: 1.0, 2: third, 3: third}[len(tps)]
        route = setup.route
        tags = {
            ws.window.kind.value,
            f"route_{route.setup_tf.name}_{route.entry_tf.name}",
            f"z3_{signal.z3.box.kind.value}",
        }
        if signal.entry_zone is not None:
            tags.add(f"entry_{signal.entry_zone.box.kind.value}")
        if best:
            tags.add(BEST_TIME_TAG)
        entry_text = signal.entry_zone.box.kind.value if signal.entry_zone else "entry-TF BoS"
        reason = (
            f"{ws.window.kind.value} {route.setup_tf.name}/{route.entry_tf.name}, sweep "
            f"{setup.level} ({setup.sweep_tf.name}), BoS {setup.bos.confirmed_at:%H:%M}, "
            f"3rd {signal.z3.box.kind.value} ({signal.z3.tf.name}), entry {entry_text}, "
            f"SL {t.sl_from}, TPs " + " / ".join(lv.source for lv in t.take_profits)
        )
        return Order(
            signal.direction,
            signal.close,
            t.stop_loss,
            tps[0],
            tags=frozenset(tags),
            reason=reason,
            confluence=signal.z3.box.kind.value,
            take_profit_2=tps[1] if len(tps) > 1 else None,
            tp1_share=tp1_share,
            break_even_after_tp1=True,
            take_profit_3=tps[2] if len(tps) > 2 else None,
            tp2_share=third if len(tps) > 2 else None,
            ref=setup,
        )


def _minute(t: datetime, w: TradingWindow) -> int:
    """Whole minutes from the window's open to `t` (negative before the open)."""
    return int((t - w.open).total_seconds() // 60)


def _inside(ts: datetime, tf: Timeframe, outer_ts: datetime, outer_tf: Timeframe) -> bool:
    """The `tf` candle containing `ts` lies inside the `outer_tf` candle containing
    `outer_ts` (both UTC-aligned here: 5m inside 15m)."""
    inner, outer = candle_open(tf, ts), candle_open(outer_tf, outer_ts)
    return outer <= inner and inner + tf.duration <= outer + outer_tf.duration
