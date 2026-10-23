"""Trades overlay (every strategy). Spec: ROADMAP.md › 3.3b,
strategy-session-zones.md › Trades on the chart.

Any other strategy than strategy 1 (rule set by the user, 2026-10-23: the trade itself is
enough): its trades come from the backtest runner (`run_backtests`, the same run a backtest
from the shown range's first day gives, with the strategy's own warm-up) over the shown range
plus `RUN_AFTER`, and are drawn as position boxes with hover; no confluences.

Strategy 1:

Runs strategy 1 (`SessionZoneSweep`) and the backtest engine on the shown symbol, with the
current strategy settings (ROADMAP 4.1, `OverlaySettings.strategy`): 5m base
candles with 30m and 1h, through the engine's own `Replay`, over `run_window`: from the
first day of the month before the shown range's month (a fixed anchor, so every range
starting in the same month and every timeframe shows the same trades, with at least a
month of warm-up: long-lived state like 1h obstacles and setups depends on where a run
starts) to a week after the range (trades still open at its end reach their exit), within
the run of consecutive cached days. Until the full history was cached (2026-10-09) the
run covered the whole cached block; with years cached that took minutes. Ranges longer
than `ChartConfig.trades_max_days` show a message instead (a backtest covers them). With no
lookahead, the trades up to a time never depend on later candles. The run is cached per
symbol, window and settings. Trades entered on the shown range are drawn on any
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
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache

from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import candles_from_frame
from backtester.data.sources import SymbolSources, cached_block
from backtester.detectors.base import Event
from backtester.detectors.zone import ZoneKind
from backtester.engine.backtest import run_backtest
from backtester.engine.replay import Replay
from backtester.engine.trade import ExitReason, TradeResult
from backtester.runner import RunSettings, run_backtests
from backtester.settings import from_json
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.strategy import Decision, SessionZoneSweep
from backtester.ui.chart_config import DEFAULT_CONFIG, SESSION_LABELS, ChartConfig
from backtester.ui.drawing import Box, Drawing, Hover, Label, Line
from backtester.ui.overlays import (
    DEFAULT_SETTINGS,
    OverlayContext,
    OverlaySettings,
    OverlayType,
    OverlayUnavailable,
    register,
)

CONFLUENCES = "confluences"  # the sub-entry's part key
EXIT_LABELS = {
    ExitReason.TAKE_PROFIT: "TP",
    ExitReason.STOP_LOSS: "SL",
    ExitReason.BREAK_EVEN: "break-even",
    ExitReason.END_OF_DATA: "end of data",
    ExitReason.SIGNAL: "signal exit",
}


@dataclass(frozen=True)
class StrategyRun:
    trades: tuple[TradeResult, ...]
    decisions: dict[tuple[datetime, Direction], Decision]  # by entry time and direction
    m5: CandleSeries | None  # strategy 1 only (the confluences' candles)
    m30: CandleSeries | None


def run_strategy(
    sources: SymbolSources,
    symbol: str,
    first_day: date,
    last_day: date,
    settings: RunSettings | None = None,
) -> StrategyRun:
    """Strategy 1 + engine over [first_day, last_day] (UTC days, inclusive), with the
    strategy and engine settings of `settings` (default: the spec defaults)."""
    settings = settings or RunSettings()
    start = datetime.combine(first_day, time(), UTC)
    end = datetime.combine(last_day + timedelta(days=1), time(), UTC)
    adapter = sources.adapter(symbol)
    strategy = SessionZoneSweep(symbol, settings.strategy, settings.detectors)
    series = {
        tf: CandleSeries(
            symbol, tf, candles_from_frame(adapter.fetch_frame(symbol, tf, start, end))
        )
        for tf in strategy.timeframes
    }
    trades = run_backtest(strategy, list(series.values()), settings.engine)
    decisions = {
        (d.signal.at, d.signal.direction): d for d in strategy.decisions if d.order is not None
    }
    zone_tf = strategy.config.zone_timeframe
    return StrategyRun(tuple(trades), decisions, series[Timeframe.M5], series[zone_tf])


RUN_AFTER = timedelta(days=7)  # the run goes on this long after the shown range


def run_window(cached: set[date], first_shown: date, last_shown: date) -> tuple[date, date]:
    """(first, last) day of the strategy run for a chart showing first_shown..last_shown:
    from the 1st of the month before first_shown's month to a week after last_shown,
    within the run of cached days containing first_shown."""
    block_first, block_last = cached_block(cached, first_shown)
    month = first_shown.replace(day=1)
    anchor = (month - timedelta(days=1)).replace(day=1)
    return max(anchor, block_first), min(last_shown + RUN_AFTER, block_last)


def chart_run(
    sources: SymbolSources,
    symbol: str,
    first_shown: date,
    last_shown: date,
    settings_json: str = "",
) -> StrategyRun:
    """The run for a chart showing first_shown..last_shown (`run_window`), with the settings
    given as canonical JSON (backtester/settings.py `to_json`; "" = spec defaults)."""
    first, last = run_window(set(sources.cached_days(symbol)), first_shown, last_shown)
    return _cached_run(sources, symbol, first, last, settings_json)


@lru_cache(maxsize=8)
def _cached_run(sources, symbol, first_day, last_day, settings_json="") -> StrategyRun:
    return run_strategy(sources, symbol, first_day, last_day, from_json(settings_json))


def registered_run(
    sources: SymbolSources,
    symbol: str,
    first_shown: date,
    last_shown: date,
    settings_json: str = "",
) -> StrategyRun:
    """Any registered strategy's trades entered from first_shown on, run to a week after
    last_shown (within the cached days), as a backtest over that range gives them."""
    block_last = cached_block(set(sources.cached_days(symbol)), first_shown)[1]
    last = min(last_shown + RUN_AFTER, block_last)
    return _cached_registered(sources, symbol, first_shown, last, settings_json)


@lru_cache(maxsize=8)
def _cached_registered(sources, symbol, first_day, last_day, settings_json="") -> StrategyRun:
    settings = from_json(settings_json)
    result = run_backtests([symbol], first_day, last_day, settings, sources, workers=1)
    return StrategyRun(result.trades, {}, None, None)


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
    strategy_1 = isinstance(from_json(settings.strategy).strategy, SessionZoneSweepConfig)
    candles = list(replay.view(len(replay) - 1))
    opens = [c.ts for c in candles]
    duration = replay.timeframe.duration
    closes = [t + duration for t in opens]
    first_shown, last_shown = opens[0].date(), (closes[-1] - timedelta(microseconds=1)).date()
    if (last_shown - first_shown).days + 1 > config.trades_max_days:
        raise OverlayUnavailable(
            f"Trades: shown for ranges up to {config.trades_max_days} days (the strategy runs "
            "about 40 s per year of 5m candles); pick a shorter range or run a backtest"
        )
    run_for = chart_run if strategy_1 else registered_run
    try:
        run = run_for(sources, replay.symbol, first_shown, last_shown, settings.strategy)
    except KeyError as e:  # also an unmapped symbol
        raise OverlayUnavailable(e.args[0]) from e
    except ValueError as e:  # e.g. no 5m candles, no rules for the symbol, no cached day
        raise OverlayUnavailable(str(e)) from e

    def containing(close: datetime) -> int:
        """Chart candle containing the instant just before `close` (a 5m close time)."""
        return bisect_left(opens, close) - 1

    def at_open(ts: datetime) -> int:
        """Chart candle containing `ts` (an open time); 0 if before the chart."""
        return max(bisect_right(opens, ts) - 1, 0)

    m5 = None if run.m5 is None else run.m5.view(len(run.m5) - 1)
    m30 = None if run.m30 is None else run.m30.view(len(run.m30) - 1)
    out = []
    for trade in run.trades:
        if not opens[0] < trade.entry_time <= closes[-1]:
            continue  # entered in the warm-up or after the chart
        entry_x = containing(trade.entry_time)
        decision = run.decisions.get((trade.entry_time, trade.direction))
        # Event positions use actual close times, including a sentinel beyond the chart.
        # Only drawing geometry is clipped; future outcomes stay hidden in replay.
        be_x = None if trade.break_even_time is None else bisect_left(closes, trade.break_even_time)
        exit_x = bisect_left(closes, trade.exit_time)
        part_xs = tuple(bisect_left(closes, p.time) for p in trade.parts)
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


def _r(value: float) -> str:
    return f"{value:+.2f}R"


def rr_label(t: TradeResult) -> str:
    if t.take_profit is None:
        return "no TP"
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
    if t.take_profit is None:
        tps = "no TP"
    elif t.take_profit_2 is None:
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
    return "\n".join(lines)


def draw_trades(events: Sequence[ChartTrade], ctx: OverlayContext) -> list[Drawing]:
    if not events:
        return []
    cfg = ctx.config
    profit, loss, entries, break_even, tp1_lines, labels, hovers = [], [], [], [], [], [], []
    for e in events:
        t = e.trade
        x0, x1 = e.entry_x, min(e.exit_x, ctx.cursor)  # grows with the cursor in replay
        far_tp = t.take_profit if t.take_profit_2 is None else t.take_profit_2
        if far_tp is None:  # no take profit: the target box is the exit's distance so far
            far_tp = t.exit_price if e.exit_x <= ctx.cursor else t.entry
        profit.append(
            Box(
                x0,
                x1,
                min(t.entry, far_tp),
                max(t.entry, far_tp),
                "Trade target",
                fill=cfg.trade_profit_color,
                fill_opacity=cfg.trade_box_opacity,
            )
        )
        if t.take_profit_2 is not None:
            tp = t.take_profit
            tp1_lines.append(Line(x0, x1, tp, tp, "Trade TP1", cfg.trade_tp1_color, dash="dash"))
        loss.append(
            Box(
                x0,
                x1,
                min(t.entry, t.initial_stop),
                max(t.entry, t.initial_stop),
                "Trade risk",
                fill=cfg.trade_loss_color,
                fill_opacity=cfg.trade_box_opacity,
            )
        )
        entries.append(Line(x0, x1, t.entry, t.entry, "Trade entry", cfg.trade_entry_color))
        if e.break_even_x is not None and e.break_even_x <= ctx.cursor:
            stop, color = t.break_even_stop, cfg.trade_break_even_color
            break_even.append(
                Line(e.break_even_x, x1, stop, stop, "Trade break-even", color, dash="dash")
            )
        labels.append(
            Label((x0 + x1) / 2, (t.entry + far_tp) / 2, rr_label(t), "Trade R:R", cfg.text_color)
        )
        hovers.append(Hover(x0, x1, t.entry, hover_text(e, ctx), "Trade"))
    out: list[Drawing] = [*profit, *loss, *entries, *break_even, *tp1_lines, *labels]
    if CONFLUENCES in ctx.parts:
        out += _confluences(events, ctx)
    return out + hovers


def _confluences(events: Sequence[ChartTrade], ctx: OverlayContext) -> list[Drawing]:
    cfg = ctx.config
    kind_style = {
        ZoneKind.FVG: (cfg.fvg_color, cfg.fvg_fill_opacity),
        ZoneKind.ORDER_BLOCK: (cfg.ob_color, cfg.ob_fill_opacity),
        ZoneKind.BREAKER: (cfg.breaker_color, cfg.breaker_fill_opacity),
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
        zone_outlines.setdefault(color, []).append(
            Box(
                e.zone_x0,
                x,
                zone.bottom,
                zone.top,
                "Trade zone",
                edge=color,
                edge_dash=cfg.session_zone_line_dash,
            )
        )
        zone_fills.setdefault(color, []).append(
            Box(
                e.zone_fill_x,
                x,
                zone.bottom,
                zone.top,
                "Trade zone fill",
                fill=color,
                fill_opacity=cfg.session_zone_fill_opacity,
            )
        )
        c = signal.confluence
        c_color, opacity = kind_style.get(c.kind, (cfg.trade_entry_color, cfg.trade_box_opacity))
        confluences.setdefault(c.kind, []).append(
            Box(
                e.confluence_x0,
                x,
                c.bottom,
                c.top,
                f"Trade {c.kind.value}",
                fill=c_color,
                fill_opacity=opacity,
                edge=c_color,
            )
        )
        price = signal.bos.swing.price
        bos.append(Line(e.bos_x0, e.bos_x1, price, price, "Trade BOS", cfg.bos_color))
        above = signal.direction is Direction.BULLISH
        bos_labels.append(
            Label(
                (e.bos_x0 + e.bos_x1) / 2,
                price,
                "BOS",
                "Trade BOS label",
                cfg.bos_color,
                anchor="top center" if above else "bottom center",
            )
        )
        targets = e.decision.targets
        if targets is not None and targets.sl_at_bos_leg:
            low = signal.bos.leg_extreme
            sl_ref.append(Line(e.leg_x, x, low, low, "Trade SL ref", cfg.sl_ref_color, dash="dot"))
            sl_ref_labels.append(
                Label(
                    e.leg_x,
                    low,
                    "SL ref",
                    "Trade SL ref label",
                    cfg.sl_ref_color,
                    size=9,
                    anchor="bottom right" if above else "top right",
                )
            )
    drawings = [
        *(b for boxes in zone_fills.values() for b in boxes),
        *(b for boxes in zone_outlines.values() for b in boxes),
        *(b for boxes in confluences.values() for b in boxes),
        *bos,
        *bos_labels,
        *sl_ref,
        *sl_ref_labels,
    ]
    return [replace(d, part=CONFLUENCES) for d in drawings]


TRADES = register(
    OverlayType(
        "trades",
        "Trades",
        lambda replay, settings, sources: detect_trades(replay, settings, sources),
        draw_trades,
        parts=((CONFLUENCES, "trade confluences"),),
        order="3.3",
        needs_sources=True,
        strategy_settings=True,
    )
)
