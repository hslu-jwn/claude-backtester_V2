"""Trades overlay: position boxes and trade confluences from strategy 1 + the engine.
Spec: ROADMAP.md › 3.3b, strategy-session-zones.md › Trades on the chart.

Data: the hand-built London / New York day of the strategy tests (scenario.py), served by a
fake `SymbolSources`: a long entered at 110.0 (13:40 close, the FVG confirmation), SL 109.1,
TP 112.7 (3R cap), hit by the next candle.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parents[1] / "strategy" / "session_zone_sweep"))
import scenario
from scenario import ENTRY_INDEX, LONDON, NY_FIRST, NY_SETUP, TO_TARGET

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.replay import Replay
from backtester.engine.trade import ExitReason
from backtester.ui.chart_figure import frame_from_candles
from backtester.ui.overlays import OverlayContext
from backtester.ui.pages.chart import chart_overlays
from backtester.ui.trades_overlay import detect_trades, draw_trades

TF = {Timeframe.M5: 0, Timeframe.M30: 1, Timeframe.H1: 2}


class FakeSources:
    """Serves the scenario's 5m / 30m / 1h candles like `SymbolSources` (hash = identity,
    so every test gets a fresh cached run)."""

    def __init__(self, ohlc):
        self.series = scenario.series(ohlc)

    def cached_days(self, symbol):
        return [date(2026, 1, 5)]

    def adapter(self, symbol):
        return self

    def fetch_frame(self, symbol, timeframe, start, end):
        candles = [c for c in self.series[TF[timeframe]].view(len(self.series[TF[timeframe]]) - 1)]
        return frame_from_candles([c for c in candles if start <= c.ts < end])

    def chart(self, timeframe=Timeframe.M5) -> Replay:
        s = self.series[TF[timeframe]]
        return Replay(CandleSeries(s.symbol, timeframe, list(s.view(len(s) - 1))))


FULL = LONDON + NY_SETUP + TO_TARGET


def one_trade(ohlc=FULL, timeframe=Timeframe.M5):
    sources = FakeSources(ohlc)
    replay = sources.chart(timeframe)
    [e] = detect_trades(replay, sources=sources)
    return e, replay, sources


def test_the_scenario_trade_with_its_chart_positions():
    e, _, _ = one_trade()
    t = e.trade
    assert (t.entry, t.initial_stop, t.take_profit) == (110.0, 109.1, pytest.approx(112.7))
    assert t.exit_reason is ExitReason.TAKE_PROFIT and t.r_gross == pytest.approx(3.0)
    # costs on (XAUUSD): spread 0.25 / 0.9 and $6 / (0.9 x $100)
    assert t.r_net == pytest.approx(3.0 - 0.25 / 0.9 - 6 / 90)
    assert e.entry_x == ENTRY_INDEX and e.exit_x == ENTRY_INDEX + 1
    assert e.decision.signal.confluence.kind.value == "fvg"
    assert e.zone_x0 == 6  # the London 08:00 swing candle (5m 08:00 is candle 6)
    assert e.zone_fill_x == NY_FIRST - 1  # 12:55 closes at New York's start
    assert (e.bos_x0, e.bos_x1) == (NY_FIRST + 2, NY_FIRST + 3)  # swing high c, BOS d
    assert e.confluence_x0 == NY_FIRST + 3  # FVG candle 1 (d)
    assert e.leg_x == NY_FIRST + 2


def test_higher_chart_places_the_trade_on_the_candle_containing_it():
    e, replay, _ = one_trade(timeframe=Timeframe.M30)
    # entry 13:40 is in the 13:30 30m candle, the TP hit (13:45 close) too
    assert replay.view(e.entry_x).current.ts == datetime(2026, 1, 5, 13, 30, tzinfo=UTC)
    assert e.exit_x == e.entry_x


def by_name(traces):
    out = {}
    for t in traces:
        out.setdefault(t.name, []).append(t)
    return out


def ctx(cursor, parts=frozenset()):
    return OverlayContext("XAUUSD", cursor, 0, parts=parts)


def test_box_green_to_tp_red_to_sl_entry_line_and_rr_label():
    e, _, _ = one_trade()
    traces = by_name(draw_trades([e], ctx(len(FULL) - 1)))
    [target], [risk] = traces["Trade target"], traces["Trade risk"]
    assert target.x[:5] == (ENTRY_INDEX, ENTRY_INDEX + 1, ENTRY_INDEX + 1, ENTRY_INDEX, ENTRY_INDEX)
    assert sorted(target.y[:5]) == pytest.approx([110.0, 110.0, 110.0, 112.7, 112.7])
    assert set(risk.y[:5]) == {109.1, 110.0}
    assert "rgba(8,153,129" in target.fillcolor and "rgba(242,54,69" in risk.fillcolor
    assert traces["Trade entry"][0].y[:2] == (110.0, 110.0)
    assert traces["Trade R:R"][0].text == ("R:R 3.00",)
    hover = traces["Trade"][0].text[-1]
    assert "Long · FVG · London low zone" in hover
    assert "TP at 112.700" in hover and "+3.00R before costs" in hover
    assert "SL from the confluence · TP from zone cap" in hover
    assert "Trade zone" not in traces  # confluences only with the sub-entry


def test_trade_confluences_sub_entry():
    e, _, _ = one_trade()
    traces = by_name(draw_trades([e], ctx(len(FULL) - 1, frozenset({"confluences"}))))
    zone = traces["Trade zone"][0]
    assert min(x for x in zone.x if x is not None) == 6
    assert {y for y in zone.y if y is not None} == {107.0, 108.0}
    assert traces["Trade BOS"][0].y[:2] == (108.8, 108.8)
    fvg = traces["Trade fvg"][0]
    assert {y for y in fvg.y if y is not None} == {109.1, 109.5}
    assert "Trade SL ref" not in traces  # the SL is at the FVG, not the BOS move's low


def test_replay_shows_the_trade_from_its_entry_close_and_grows_until_the_exit():
    _, replay, sources = one_trade()

    def drawn(cursor):
        traces, _ = chart_overlays(replay, ["trades"], cursor, 0, sources=sources)
        return by_name(traces)

    assert drawn(ENTRY_INDEX - 1) == {}  # not entered yet
    at_entry = drawn(ENTRY_INDEX)
    assert max(x for x in at_entry["Trade target"][0].x if x is not None) == ENTRY_INDEX
    hover = at_entry["Trade"][0].text[-1]
    assert "still open at the cursor" in hover and "TP at" not in hover
    later = drawn(ENTRY_INDEX + 5)
    assert max(x for x in later["Trade target"][0].x if x is not None) == ENTRY_INDEX + 1
    assert "TP at" in later["Trade"][0].text[-1]


def test_break_even_line_only_from_the_candle_it_moved_on():
    e, _, _ = one_trade()
    moved = replace(
        e,
        trade=replace(
            e.trade,
            break_even_time=e.trade.entry_time,
            break_even_stop=110.31,
            exit_reason=ExitReason.BREAK_EVEN,
        ),
        break_even_x=ENTRY_INDEX + 1,
        exit_x=ENTRY_INDEX + 3,
    )
    assert "Trade break-even" not in by_name(draw_trades([moved], ctx(ENTRY_INDEX)))
    [line] = by_name(draw_trades([moved], ctx(ENTRY_INDEX + 3)))["Trade break-even"]
    assert line.x[:2] == (ENTRY_INDEX + 1, ENTRY_INDEX + 3) and line.y[:2] == (110.31, 110.31)


def test_sl_ref_line_when_the_sl_used_the_bos_move_low():
    e, _, _ = one_trade()
    targets = replace(e.decision.targets, sl_at_bos_leg=True)
    e = replace(e, decision=replace(e.decision, targets=targets))
    traces = by_name(draw_trades([e], ctx(len(FULL) - 1, frozenset({"confluences"}))))
    [line] = traces["Trade SL ref"]
    assert line.x[:2] == (NY_FIRST + 2, ENTRY_INDEX) and line.y[:2] == (108.1, 108.1)
    assert line.line.dash == "dot"
    assert traces["Trade SL ref label"][0].text == ("SL ref",)


def test_no_lookahead_later_candles_never_change_what_was_known():
    """Cut the data right after the entry: the trade is the same entry, still open."""
    cut, _, _ = one_trade(LONDON + NY_SETUP)
    full, _, _ = one_trade()
    assert cut.entry_x == full.entry_x and cut.decision == full.decision
    assert cut.trade.exit_reason is ExitReason.END_OF_DATA
    t, f = cut.trade, full.trade
    assert (t.entry, t.initial_stop, t.take_profit, t.entry_time) == (
        f.entry,
        f.initial_stop,
        f.take_profit,
        f.entry_time,
    )
