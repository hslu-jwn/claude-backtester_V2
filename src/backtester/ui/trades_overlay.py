"""Trades overlay (strategy 1). Spec: ROADMAP.md › 3.3b,
strategy-session-zones.md › Trades on the chart.

Runs strategy 1 (`SessionZoneSweep`) and the backtest engine on the shown symbol: 5m base
candles with 30m and 1h, through the engine's own `Replay`, over the whole run of
consecutive cached days that contains the shown range (`cached_block`). Starting at the
block's first day, not a fixed number of days before the range, means every range and
timeframe shows the same trades: long-lived state (1h obstacles, setups) depends on where
a run starts, and with no lookahead the trades up to a time never depend on later candles.
The run is cached per symbol and block. Trades entered on the shown range are drawn on any
timeframe: a 5m time is placed on the chart candle that contains it.

Per trade, a TradingView-style position box from the entry candle to the candle in which
the last part closed (TP, SL or break-even): green between entry and the furthest TP, red
between entry and SL (a short is flipped automatically: its TP is below), a grey entry
line, "R:R" on the box (TP1 / TP2 with two TPs, 3.3c), a dashed TP1 line inside the green
part when there is a TP2, and the break-even line at the moved SL from the candle it moved
on. Hover along the entry line: entry, SL, TP1 / TP2 with their shares, each closed part
with its result, the total in R (before and after costs), exit reason, confluence.

Sub-entry "↳ trade confluences" (one switch for all trades): what led to each trade, in the
normal overlay colors: the swept session zone (session-zone style, from where it formed to
the entry, filled from its active session's start), the 5m BOS (red line from the broken
swing to the BOS candle), the entry confluence (FVG green, OB yellow, BPR purple, from its
first candle to the entry; equilibrium indigo: the BOS move's discount half) and, when the SL was placed below the BOS move's low because the
confluence was small, a thin dashed "SL ref" line at that low.

No lookahead: a trade is an event confirmed by its entry candle, so in replay it appears
at the close of the candle containing the entry. Its box then grows with the cursor until
the exit candle; the result, exit and break-even line only show once the cursor is past
them. Everything in the confluences is known at the entry.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache

import plotly.graph_objects as go

from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import candles_from_frame
from backtester.data.sources import SymbolSources, cached_block
from backtester.detectors.base import Event
from backtester.detectors.zone import ZoneKind
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.replay import Replay
from backtester.engine.trade import ExitReason, TradeResult
from backtester.strategy.session_zone_sweep.strategy import Decision, SessionZoneSweep
from backtester.ui.chart_figure import DEFAULT_CONFIG, SESSION_LABELS, ChartConfig
from backtester.ui.overlays import (
    DEFAULT_SETTINGS,
    OverlayContext,
    OverlaySettings,
    OverlayType,
    OverlayUnavailable,
    register,
)
from backtester.ui.zone_overlay import Box, hover_xs, rgba, stack_lanes

CONFLUENCES = "confluences"  # the sub-entry's part key
EXIT_LABELS = {
    ExitReason.TAKE_PROFIT: "TP",
    ExitReason.STOP_LOSS: "SL",
    ExitReason.BREAK_EVEN: "break-even",
    ExitReason.END_OF_DATA: "end of data",
}


@dataclass(frozen=True)
class StrategyRun:
    trades: tuple[TradeResult, ...]
    decisions: dict[tuple[datetime, Direction], Decision]  # by entry time and direction
    m5: CandleSeries
    m30: CandleSeries


def run_strategy(
    sources: SymbolSources, symbol: str, first_day: date, last_day: date
) -> StrategyRun:
    """Strategy 1 + engine over [first_day, last_day] (UTC days, inclusive)."""
    start = datetime.combine(first_day, time(), UTC)
    end = datetime.combine(last_day + timedelta(days=1), time(), UTC)
    adapter = sources.adapter(symbol)
    strategy = SessionZoneSweep(symbol)
    series = {
        tf: CandleSeries(
            symbol, tf, candles_from_frame(adapter.fetch_frame(symbol, tf, start, end))
        )
        for tf in strategy.timeframes
    }
    trades = run_backtest(strategy, list(series.values()), EngineConfig())
    decisions = {
        (d.signal.at, d.signal.direction): d for d in strategy.decisions if d.order is not None
    }
    zone_tf = strategy.config.zone_timeframe
    return StrategyRun(tuple(trades), decisions, series[Timeframe.M5], series[zone_tf])


def block_run(sources: SymbolSources, symbol: str, day: date) -> StrategyRun:
    """The run over the cached block containing `day`."""
    first, last = cached_block(set(sources.cached_days(symbol)), day)
    return _cached_run(sources, symbol, first, last)


@lru_cache(maxsize=8)
def _cached_run(sources, symbol, first_day, last_day) -> StrategyRun:
    return run_strategy(sources, symbol, first_day, last_day)


@dataclass(frozen=True, slots=True)
class ChartTrade(Event):
    """A trade placed on the chart. `confirmed_index` is the chart candle containing the
    entry (its close is at or after the entry time); the other x are chart candles too."""

    trade: TradeResult
    decision: Decision | None
    exit_x: int  # candle in which the last part closed (or the last one)
    part_xs: tuple[int, ...]  # candle in which each part closed (trade.parts order)
    break_even_x: int | None  # candle whose close moved the SL to break-even
    zone_x0: int  # the swept session zone: where it formed (clipped to the chart's start)
    zone_fill_x: int  # ... first candle of the session it is used in
    bos_x0: int  # the broken swing's wick candle
    bos_x1: int  # the BOS candle
    confluence_x0: int  # the entry confluence's first candle
    leg_x: int  # the BOS move's low (high for a short)

    @property
    def entry_x(self) -> int:
        return self.confirmed_index


def detect_trades(
    replay: Replay,
    settings: OverlaySettings = DEFAULT_SETTINGS,
    sources: SymbolSources | None = None,
    config: ChartConfig = DEFAULT_CONFIG,
) -> list[ChartTrade]:
    if sources is None:
        raise OverlayUnavailable("needs the chart's data sources")
    candles = list(replay.view(len(replay) - 1))
    opens = [c.ts for c in candles]
    duration = replay.timeframe.duration
    closes = [t + duration for t in opens]
    try:
        run = block_run(sources, replay.symbol, opens[0].date())
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e
    except ValueError as e:  # e.g. no 5m candles
        raise OverlayUnavailable(str(e)) from e

    def containing(close: datetime) -> int:
        """Chart candle containing the instant just before `close` (a 5m close time)."""
        return bisect_left(opens, close) - 1

    def at_open(ts: datetime) -> int:
        """Chart candle containing `ts` (an open time); 0 if before the chart."""
        return max(bisect_right(opens, ts) - 1, 0)

    m5 = run.m5.view(len(run.m5) - 1)
    m30 = run.m30.view(len(run.m30) - 1)
    out = []
    for trade in run.trades:
        if not opens[0] < trade.entry_time <= closes[-1]:
            continue  # entered in the warm-up or after the chart
        entry_x = containing(trade.entry_time)
        decision = run.decisions.get((trade.entry_time, trade.direction))
        be_x = None if trade.break_even_time is None else containing(trade.break_even_time)
        exit_x = min(containing(trade.exit_time), len(opens) - 1)
        part_xs = tuple(min(containing(p.time), len(opens) - 1) for p in trade.parts)
        zone_x0 = zone_fill_x = bos_x0 = bos_x1 = confluence_x0 = leg_x = entry_x
        if decision is not None:
            signal = decision.signal
            zone = signal.zone
            zone_x0 = at_open(m30[zone.start_index].ts)
            zone_fill_x = min(bisect_left(closes, zone.active_in.start), entry_x)
            bos_x0 = at_open(signal.bos.swing.ts)
            bos_x1 = containing(signal.bos.at)
            confluence_x0 = at_open(m5[signal.confluence.start_index].ts)
            leg_x = at_open(m5[signal.bos.leg_index].ts)
        out.append(
            ChartTrade(
                entry_x,
                closes[entry_x],
                trade,
                decision,
                exit_x,
                part_xs,
                be_x,
                zone_x0,
                zone_fill_x,
                bos_x0,
                bos_x1,
                confluence_x0,
                leg_x,
            )
        )
    return out


# --- drawing ------------------------------------------------------------------------------


def _path(boxes: Sequence[Box]) -> tuple[list, list]:
    xs, ys = [], []
    for x0, x1, bottom, top in boxes:
        xs += [x0, x1, x1, x0, x0, None]
        ys += [bottom, bottom, top, top, bottom, None]
    return xs, ys


def _filled(boxes: Sequence[Box], color: str, opacity: float, name: str, line=None):
    """Boxes as filled traces, spread over lanes so overlapping ones stack."""
    if not boxes:
        return []
    lanes = stack_lanes(boxes)
    traces = []
    for lane in range(max(lanes) + 1):
        xs, ys = _path([b for b, n in zip(boxes, lanes, strict=True) if n == lane])
        traces.append(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                fill="toself",
                fillcolor=rgba(color, opacity),
                line=line or {"width": 0},
                hoverinfo="skip",
                name=name,
            )
        )
    return traces


def _lines(segments: Sequence[tuple[float, float, float]], color: str, name: str, dash="solid"):
    """Horizontal lines (x0, x1, y) as one trace."""
    if not segments:
        return []
    xs, ys = [], []
    for x0, x1, y in segments:
        xs += [x0, x1, None]
        ys += [y, y, None]
    return [
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            line={"color": color, "width": 1, "dash": dash},
            hoverinfo="skip",
            name=name,
        )
    ]


def _labels(points: Sequence[tuple[float, float, str, str]], color: str, name: str, size=10):
    """Text labels (x, y, text, position) as one trace."""
    if not points:
        return []
    return [
        go.Scatter(
            x=[p[0] for p in points],
            y=[p[1] for p in points],
            mode="text",
            text=[p[2] for p in points],
            textposition=[p[3] for p in points],
            textfont={"color": color, "size": size},
            hoverinfo="skip",
            name=name,
        )
    ]


def _r(value: float) -> str:
    return f"{value:+.2f}R"


def rr_label(t: TradeResult) -> str:
    if t.take_profit_2 is None:
        return f"R:R {t.r_at(t.take_profit):.2f}"
    return f"R:R {t.r_at(t.take_profit):.2f} / {t.r_at(t.take_profit_2):.2f}"


def hover_text(e: ChartTrade, ctx: OverlayContext) -> str:
    t, d = e.trade, ctx.digits
    side = "Long" if t.direction is Direction.BULLISH else "Short"
    head = side
    if e.decision is not None:
        signal = e.decision.signal
        zone = signal.zone
        head += (
            f" · {signal.confluence.kind.value.upper().replace('_', ' ')} · "
            f"{SESSION_LABELS[zone.formed_in.session]} {zone.side.value} zone"
        )
    if t.take_profit_2 is None:
        tps = f"TP {t.take_profit:.{d}f} · R:R {t.planned_r:.2f}"
    else:
        tps = (
            f"TP1 {t.take_profit:.{d}f} ({t.tp1_share:.0%}, {t.r_at(t.take_profit):.2f}R) · "
            f"TP2 {t.take_profit_2:.{d}f} ({1 - t.tp1_share:.0%}, "
            f"{t.r_at(t.take_profit_2):.2f}R)"
        )
    lines = [
        head,
        f"entry {t.entry:.{d}f} (candle closed {t.entry_time:%Y-%m-%d %H:%M} UTC)",
        f"SL {t.initial_stop:.{d}f} · {tps}",
    ]
    if e.decision is not None and e.decision.targets is not None:
        targets = e.decision.targets
        sl_from = "BOS move's low" if targets.sl_at_bos_leg else "confluence"
        if t.direction is Direction.BEARISH:
            sl_from = sl_from.replace("low", "high")
        if targets.sl_widened:
            sl_from += " (widened to the minimum SL)"
        tp_from = f"TP from {targets.tp1_from}"
        if targets.tp2_from is not None:
            tp_from = f"TP1 from {targets.tp1_from} · TP2 from {targets.tp2_from}"
        lines.append(f"SL from the {sl_from} · {tp_from}")
    if e.break_even_x is not None and e.break_even_x <= ctx.cursor:
        lines.append(
            f"SL to break-even {t.break_even_stop:.{d}f} at {t.break_even_time:%m-%d %H:%M} UTC"
        )
    two = len(t.parts) > 1
    for i, (part, x) in enumerate(zip(t.parts, e.part_xs, strict=True)):
        if x > ctx.cursor:
            break
        what = f"{EXIT_LABELS[part.reason]} at {part.price:.{d}f}"
        if two:
            what = f"{'TP1 part' if i == 0 else 'rest'} ({part.share:.0%}): {what}"
        lines.append(f"{what} (candle closed {part.time:%Y-%m-%d %H:%M} UTC): {_r(part.r_gross)}")
    if e.exit_x <= ctx.cursor:
        lines.append(f"result {_r(t.r_gross)} before costs, {_r(t.r_net)} after costs")
    else:
        lines.append("still open at the cursor")
    if t.tags:
        lines.append(f"tags: {', '.join(sorted(t.tags))}")
    return "<br>".join(lines)


def draw_trades(events: Sequence[ChartTrade], ctx: OverlayContext) -> list[go.Scatter]:
    if not events:
        return []
    cfg = ctx.config
    profit, loss, entries, break_even, tp1_lines, labels = [], [], [], [], [], []
    hover_x, hover_y, hover_text_ = [], [], []
    for e in events:
        t = e.trade
        x0, x1 = e.entry_x, min(e.exit_x, ctx.cursor)  # grows with the cursor in replay
        far_tp = t.take_profit if t.take_profit_2 is None else t.take_profit_2
        profit.append((x0, x1, min(t.entry, far_tp), max(t.entry, far_tp)))
        if t.take_profit_2 is not None:
            tp1_lines.append((x0, x1, t.take_profit))
        loss.append((x0, x1, min(t.entry, t.initial_stop), max(t.entry, t.initial_stop)))
        entries.append((x0, x1, t.entry))
        if e.break_even_x is not None and e.break_even_x <= ctx.cursor:
            break_even.append((e.break_even_x, x1, t.break_even_stop))
        labels.append(
            (
                (x0 + x1) / 2,
                (t.entry + far_tp) / 2,
                rr_label(t),
                "middle center",
            )
        )
        hx = hover_xs(x0, x1, cfg.zone_hover_step, cfg.zone_hover_ends)
        text = hover_text(e, ctx)
        hover_x += hx
        hover_y += [t.entry] * len(hx)
        hover_text_ += [text] * len(hx)
    traces = [
        *_filled(profit, cfg.trade_profit_color, cfg.trade_box_opacity, "Trade target"),
        *_filled(loss, cfg.trade_loss_color, cfg.trade_box_opacity, "Trade risk"),
        *_lines(entries, cfg.trade_entry_color, "Trade entry"),
        *_lines(break_even, cfg.trade_break_even_color, "Trade break-even", dash="dash"),
        *_lines(tp1_lines, cfg.trade_tp1_color, "Trade TP1", dash="dash"),
        *_labels(labels, cfg.text_color, "Trade R:R"),
    ]
    if CONFLUENCES in ctx.parts:
        traces += _confluences(events, ctx)
    traces.append(
        go.Scatter(
            x=hover_x,
            y=hover_y,
            mode="markers",
            marker={"size": cfg.marker_size, "opacity": 0},  # invisible, only for hover
            text=hover_text_,
            hovertemplate="%{text}<extra></extra>",
            name="Trade",
        )
    )
    return traces


def _confluences(events: Sequence[ChartTrade], ctx: OverlayContext) -> list[go.Scatter]:
    cfg = ctx.config
    kind_style = {
        ZoneKind.FVG: (cfg.fvg_color, cfg.fvg_fill_opacity),
        ZoneKind.ORDER_BLOCK: (cfg.ob_color, cfg.ob_fill_opacity),
        ZoneKind.BPR: (cfg.bpr_color, cfg.bpr_fill_opacity),
        ZoneKind.EQUILIBRIUM: (cfg.equilibrium_color, cfg.equilibrium_fill_opacity),
    }
    zone_outlines: dict[str, list[Box]] = {}
    zone_fills: dict[str, list[Box]] = {}
    confluences: dict[ZoneKind, list[Box]] = {}
    bos, bos_labels, sl_ref, sl_ref_labels = [], [], [], []
    for e in events:
        if e.decision is None:
            continue
        signal, x = e.decision.signal, e.entry_x
        zone = signal.zone
        color = cfg.session_color(zone.active_in.session)
        zone_outlines.setdefault(color, []).append((e.zone_x0, x, zone.bottom, zone.top))
        zone_fills.setdefault(color, []).append((e.zone_fill_x, x, zone.bottom, zone.top))
        c = signal.confluence
        confluences.setdefault(c.kind, []).append((e.confluence_x0, x, c.bottom, c.top))
        price = signal.bos.swing.price
        bos.append((e.bos_x0, e.bos_x1, price))
        above = signal.direction is Direction.BULLISH
        bos_labels.append(
            ((e.bos_x0 + e.bos_x1) / 2, price, "BOS", "top center" if above else "bottom center")
        )
        targets = e.decision.targets
        if targets is not None and targets.sl_at_bos_leg:
            low = signal.bos.leg_extreme
            sl_ref.append((e.leg_x, x, low))
            sl_ref_labels.append((e.leg_x, low, "SL ref", "bottom right" if above else "top right"))
    traces = []
    for color, boxes in zone_fills.items():
        traces += _filled(boxes, color, cfg.session_zone_fill_opacity, "Trade zone fill")
    for color, boxes in zone_outlines.items():
        xs, ys = _path(boxes)
        traces.append(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                line={"color": color, "width": 1, "dash": cfg.session_zone_line_dash},
                hoverinfo="skip",
                name="Trade zone",
            )
        )
    for kind, boxes in confluences.items():
        color, opacity = kind_style.get(kind, (cfg.trade_entry_color, cfg.trade_box_opacity))
        traces += _filled(
            boxes, color, opacity, f"Trade {kind.value}", line={"color": color, "width": 1}
        )
    traces += _lines(bos, cfg.bos_color, "Trade BOS")
    traces += _labels(bos_labels, cfg.bos_color, "Trade BOS label")
    traces += _lines(sl_ref, cfg.sl_ref_color, "Trade SL ref", dash="dot")
    traces += _labels(sl_ref_labels, cfg.sl_ref_color, "Trade SL ref label", size=9)
    return traces


TRADES = register(
    OverlayType(
        "trades",
        "Trades",
        lambda replay, settings, sources: detect_trades(replay, settings, sources),
        draw_trades,
        parts=((CONFLUENCES, "trade confluences"),),
        order="3.3",
        needs_sources=True,
    )
)
