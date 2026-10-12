"""Trades overlay: position boxes and trade confluences from strategy 1 + the engine.
Spec: ROADMAP.md › 3.3b, strategy-session-zones.md › Trades on the chart.

Data: the hand-built London / New York day of the strategy tests (scenario.py), served by a
fake `SymbolSources`: a long entered at 110.0 (13:40 close, the FVG confirmation), SL 109.1,
TP 111.08 (1.2R: the London zone is beyond the 3R cap), hit by the next candle.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

sys.path.append(str(Path(__file__).parents[1] / "strategy" / "session_zone_sweep"))
import scenario
from overlay_helpers import boxes, by_layer, chart_overlays, hovers, lines, texts
from scenario import ENTRY_INDEX, LONDON, NY_FIRST, NY_SETUP, TO_TARGET

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.data.resample import CANDLE_COLUMNS
from backtester.detectors.zone import ZoneKind
from backtester.engine.replay import Replay
from backtester.engine.trade import ExitReason, PartialExit
from backtester.settings import settings_from_values, to_json
from backtester.ui.overlays import OverlayContext, OverlaySettings
from backtester.ui.trades_overlay import detect_trades
from backtester.ui.trades_overlay import draw_trades as draw_trade_drawings

TF = {Timeframe.M5: 0, Timeframe.M30: 1, Timeframe.H1: 2, Timeframe.H4: 3}


def frame_from_candles(candles) -> pd.DataFrame:
    """Candles as a frame with the cache adapter's columns."""
    frame = pd.DataFrame(
        [(c.ts, c.open, c.high, c.low, c.close, c.volume, c.spread) for c in candles],
        columns=CANDLE_COLUMNS,
    )
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    return frame


class FakeSources:
    """Serves the scenario's 5m / 30m / 1h / 4h candles like `SymbolSources` (hash = identity,
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
    assert (t.entry, t.initial_stop, t.take_profit) == (110.0, 109.1, pytest.approx(111.08))
    assert t.exit_reason is ExitReason.TAKE_PROFIT and t.r_gross == pytest.approx(1.2)
    # costs on (XAUUSD): spread 0.25 / 0.9 and $6 / (0.9 x $100)
    assert t.r_net == pytest.approx(1.2 - 0.25 / 0.9 - 6 / 90)
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


def draw_trades(events, ctx):
    return draw_trade_drawings(events, ctx)


def ctx(cursor, parts=frozenset()):
    return OverlayContext("XAUUSD", cursor, 0, parts=parts)


def test_box_green_to_tp_red_to_sl_entry_line_and_rr_label():
    e, _, _ = one_trade()
    layers = by_layer(draw_trades([e], ctx(len(FULL) - 1)))
    [target], [risk] = boxes(layers["Trade target"]), boxes(layers["Trade risk"])
    assert target[:2] == (ENTRY_INDEX, ENTRY_INDEX + 1)
    assert target[2:] == pytest.approx((110.0, 111.08))
    assert risk == (ENTRY_INDEX, ENTRY_INDEX + 1, 109.1, 110.0)
    assert layers["Trade target"][0].fill == "#089981" and layers["Trade risk"][0].fill == "#f23645"
    assert lines(layers["Trade entry"])[0][2:] == (110.0, 110.0)
    assert texts(layers["Trade R:R"]) == ["R:R 1.20"]
    hover = hovers(layers["Trade"])[-1]
    assert "Long · FVG · London low zone" in hover
    assert "TP at 111.080" in hover and "result +1.20R before costs" in hover
    assert "SL from the confluence · TP from min R" in hover
    assert "Trade TP1" not in layers  # one TP only
    assert "Trade zone" not in layers  # confluences only with the sub-entry


def test_trade_confluences_sub_entry():
    e, _, _ = one_trade()
    layers = by_layer(draw_trades([e], ctx(len(FULL) - 1, frozenset({"confluences"}))))
    [zone] = boxes(layers["Trade zone"])
    assert zone == (6, ENTRY_INDEX, 107.0, 108.0)
    assert layers["Trade zone"][0].part == "confluences"
    assert lines(layers["Trade BOS"])[0][2:] == (108.8, 108.8)
    [fvg] = boxes(layers["Trade fvg"])
    assert fvg[2:] == (109.1, 109.5)
    assert "Trade SL ref" not in layers  # the SL is at the FVG, not the BOS move's low


def test_replay_shows_the_trade_from_its_entry_close_and_grows_until_the_exit():
    _, replay, sources = one_trade()

    def drawn(cursor):
        drawings, _ = chart_overlays(replay, ["trades"], cursor, 0, sources=sources)
        return by_layer(drawings)

    assert drawn(ENTRY_INDEX - 1) == {}  # not entered yet
    at_entry = drawn(ENTRY_INDEX)
    assert boxes(at_entry["Trade target"])[0][1] == ENTRY_INDEX
    hover = hovers(at_entry["Trade"])[-1]
    assert "still open at the cursor" in hover and "TP at" not in hover
    later = drawn(ENTRY_INDEX + 5)
    assert boxes(later["Trade target"])[0][1] == ENTRY_INDEX + 1
    assert "TP at" in hovers(later["Trade"])[-1]


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
    assert "Trade break-even" not in by_layer(draw_trades([moved], ctx(ENTRY_INDEX)))
    [line] = lines(by_layer(draw_trades([moved], ctx(ENTRY_INDEX + 3)))["Trade break-even"])
    assert line == (ENTRY_INDEX + 1, ENTRY_INDEX + 3, 110.31, 110.31)


def test_sl_ref_line_when_the_sl_used_the_bos_move_low():
    e, _, _ = one_trade()
    targets = replace(e.decision.targets, sl_at_bos_leg=True)
    e = replace(e, decision=replace(e.decision, targets=targets))
    layers = by_layer(draw_trades([e], ctx(len(FULL) - 1, frozenset({"confluences"}))))
    [ref] = layers["Trade SL ref"]
    assert lines([ref]) == [(NY_FIRST + 2, ENTRY_INDEX, 108.1, 108.1)]
    assert ref.dash == "dot"
    assert texts(layers["Trade SL ref label"]) == ["SL ref"]


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


def test_two_tps_box_lines_and_hover():
    e, _, _ = one_trade()
    t = e.trade
    tp1_time = t.exit_time
    parts = (
        PartialExit(0.5, tp1_time, t.exit_candle, 111.08, 111.08, ExitReason.TAKE_PROFIT, 1.2, 1.2),
        PartialExit(0.5, tp1_time, t.exit_candle, 110.31, 110.31, ExitReason.BREAK_EVEN, 0.34, 0.0),
    )
    two = replace(
        e,
        trade=replace(t, take_profit_2=112.7, tp1_share=0.5, parts=parts, r_gross=0.77),
        part_xs=(ENTRY_INDEX + 1, ENTRY_INDEX + 3),
        exit_x=ENTRY_INDEX + 3,
    )
    layers = by_layer(draw_trades([two], ctx(ENTRY_INDEX + 3)))
    [target] = boxes(layers["Trade target"])
    assert target[3] == pytest.approx(112.7)  # up to TP2
    [tp1] = layers["Trade TP1"]
    assert (tp1.y0, tp1.y1) == pytest.approx((111.08, 111.08)) and tp1.dash == "dash"
    assert texts(layers["Trade R:R"]) == ["R:R 1.20 / 3.00"]
    hover = hovers(layers["Trade"])[-1]
    assert "TP1 111.080 (50%, 1.20R) · TP2 112.700 (50%, 3.00R)" in hover
    assert "TP1 part (50%): TP at 111.080" in hover
    assert "rest (50%): break-even at 110.310" in hover and "result +0.77R" in hover
    # replay: after TP1, before the rest closed -> only the first part
    hover = hovers(by_layer(draw_trades([two], ctx(ENTRY_INDEX + 2)))["Trade"])[-1]
    assert "TP1 part" in hover and "rest (50%)" not in hover
    assert "still open at the cursor" in hover


def test_equilibrium_confluence_is_drawn_in_its_color():
    e, _, _ = one_trade()
    signal = e.decision.signal
    eq = replace(signal.confluence, kind=ZoneKind.EQUILIBRIUM)
    e = replace(e, decision=replace(e.decision, signal=replace(signal, confluence=eq)))
    layers = by_layer(draw_trades([e], ctx(len(FULL) - 1, frozenset({"confluences"}))))
    assert layers["Trade equilibrium"][0].fill == "#3f51b5"
    assert "EQUILIBRIUM" in hovers(layers["Trade"])[-1]


def test_the_settings_panel_settings_reach_the_trades_overlay():
    """ROADMAP 4.1: the strategy and engine settings come in as canonical JSON."""
    sources = FakeSources(FULL)
    replay = sources.chart()
    no_costs = settings_from_values(
        {"engine.costs.spread_enabled": False, "engine.costs.commission_enabled": False}
    )
    [e] = detect_trades(replay, OverlaySettings(strategy=to_json(no_costs)), sources)
    assert e.trade.r_net == pytest.approx(e.trade.r_gross)
    tiny_sl = settings_from_values({"strategy.max_sl_atr_mult": 0.01})  # every SL too wide
    assert detect_trades(replay, OverlaySettings(strategy=to_json(tiny_sl)), sources) == []


def test_strategy_2_settings_say_the_overlay_is_not_there_yet():
    from backtester.runner import RunSettings
    from backtester.settings import to_json
    from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
    from backtester.ui.overlays import OverlayUnavailable

    sources = FakeSources(FULL)
    ny = OverlaySettings(strategy=to_json(RunSettings(strategy=NyIndexSweepConfig())))
    with pytest.raises(OverlayUnavailable, match="strategy 2"):
        detect_trades(sources.chart(), ny, sources)
