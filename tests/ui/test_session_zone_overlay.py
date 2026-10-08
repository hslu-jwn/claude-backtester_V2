"""Session zone overlay. Spec: ROADMAP.md › 2.9, strategy-session-zones.md › Session zones
on the chart.

Gold 30m candles from Monday 2026-01-05 08:00 UTC. A candle belongs to the session it
closes in: London = candles 0-8 (08:00-12:00), New York = 9-30 (12:30 closes at the NY
open 13:00). London leaves a low zone 107-108 (swing at candle 1) and a high zone
111-112 (swing at candle 2); dojis (body 0) are fillers.
"""

from __future__ import annotations

from datetime import UTC, datetime

from conftest import build_series
from plotly_helpers import chart_overlays

from backtester.core.models import Timeframe
from backtester.engine.replay import Replay
from backtester.ui.overlays import OVERLAYS

LONDON = datetime(2026, 1, 5, 8, 0, tzinfo=UTC)
NEW_YORK = datetime(2026, 1, 5, 13, 0, tzinfo=UTC)
SWINGS = [
    (110.0, 110.5, 107.5, 108.0),  # 0: red
    (108.0, 109.5, 107.0, 109.0),  # 1: green -> swing low 107, zone 107-108
    (109.0, 112.0, 108.5, 111.0),  # 2: green, high 112
    (111.0, 111.2, 109.5, 110.0),  # 3: red -> swing high 112, zone 111-112
]


def doji(price):
    return (price, price + 0.2, price - 0.2, price)


def replay_of(ohlc, start=LONDON, timeframe=Timeframe.M30):
    return Replay(build_series(ohlc, timeframe, start, symbol="XAUUSD"))


def traces_at(replay, cursor):
    traces, messages = chart_overlays(replay, ["session_zones"], cursor, 0)
    assert messages == []
    return {t.name: t for t in traces}


def boxes(trace):
    xs, ys = list(trace.x), list(trace.y)
    return sorted((xs[i], xs[i + 1], ys[i], ys[i + 2]) for i in range(0, len(xs), 6))


def test_session_zones_in_the_panel_after_bpr_without_sub_entries():
    assert OVERLAYS["session_zones"].label == "Session zones"
    assert list(OVERLAYS)[:6] == ["swings", "bos", "fvg", "ob", "bpr", "session_zones"]
    assert OVERLAYS["session_zones"].parts == ()


def test_zones_appear_when_their_session_ends_colored_by_the_session_they_are_active_in():
    replay = replay_of([*SWINGS, *[doji(109.5)] * 22])
    assert traces_at(replay, 7) == {}  # London not over yet
    t = traces_at(replay, 8)
    assert boxes(t["Session zone box"]) == [(0, 8, 107.0, 108.0), (2, 8, 111.0, 112.0)]
    assert t["Session zone box"].line.color == "#f23645"  # New York red
    assert t["Session zone box"].line.dash == "dot"
    assert "Session zone fill" not in t  # still in London, where they formed: no fill
    text = next(s for s in t["Session zone"].text if "(low)" in s)
    assert "NY Mon 01-05 session zone (low) 107.000 – 108.000" in text
    assert "formed in London Mon 01-05" in text and "role: support" in text
    # in New York the box follows the cursor, filled from New York's first candle
    t = traces_at(replay, 20)
    assert boxes(t["Session zone box"])[0] == (0, 20, 107.0, 108.0)
    assert boxes(t["Session zone fill"]) == [(9, 20, 107.0, 108.0), (9, 20, 111.0, 112.0)]
    assert t["Session zone fill"].fillcolor.startswith("rgba(242,54,69,")


def test_a_new_york_zone_is_yellow_in_tokyo_and_stops_at_its_end():
    ohlc = [*SWINGS, *[doji(109.5)] * 38]  # NY 0-20 (13:00-23:00), Tokyo 21-36 (23:30-07:00)
    replay = replay_of(ohlc, start=NEW_YORK)
    t = traces_at(replay, 41)
    assert t["Session zone box"].line.color == "#f5c518"  # Tokyo yellow
    assert boxes(t["Session zone box"]) == [(0, 36, 107.0, 108.0), (2, 36, 111.0, 112.0)]
    assert boxes(t["Session zone fill"]) == [(21, 36, 107.0, 108.0), (21, 36, 111.0, 112.0)]
    assert "expired" in t["Session zone"].text[-1]


def test_the_box_stops_at_the_candle_that_kills_the_zone():
    breaks = [
        (109.5, 109.6, 107.0, 107.5),
        (107.5, 108.0, 106.3, 106.8),  # 11: red close below 107 -> 1st break
        (106.8, 108.7, 106.6, 108.2),  # 12: green close above 108 -> 2nd break
        (108.2, 108.7, 106.0, 106.5),  # 13: red close below 107 -> 3rd break, killed
    ]
    replay = replay_of([*SWINGS, *[doji(109.5)] * 6, *breaks, *[doji(106.5)] * 18])
    t = traces_at(replay, 29)  # New York's last candle is 30: its own zones come later
    assert boxes(t["Session zone box"])[0] == (0, 13, 107.0, 108.0)
    assert boxes(t["Session zone fill"])[0] == (9, 13, 107.0, 108.0)
    low_text = next(s for s in t["Session zone"].text if "(low)" in s)
    assert "role: killed" in low_text and "break 3" in low_text


def as_m5(ohlc):
    """Six 5m candles per 30m candle: the 30m candle's open/high/low/close in the first,
    then five flat ones at its close, so the 30m candles are exactly `ohlc`."""
    return [c for o, h, lo, cl in ohlc for c in [(o, h, lo, cl), *[(cl, cl, cl, cl)] * 5]]


def test_on_the_5m_chart_from_the_30m_candles_closed_at_each_5m_close():
    m30 = [*SWINGS, *[doji(109.5)] * 30]  # 08:00 .. 00:30
    replay = Replay(
        build_series(as_m5(m30), Timeframe.M5, LONDON, symbol="XAUUSD"),
        [build_series(m30, Timeframe.M30, LONDON, symbol="XAUUSD")],
    )
    assert traces_at(replay, 52) == {}  # London's last 30m candle closes with 5m candle 53
    t = traces_at(replay, 53)
    assert boxes(t["Session zone box"]) == [(0, 53, 107.0, 108.0), (12, 53, 111.0, 112.0)]
    assert "Session zone fill" not in t
    # 5m candles belong to the session they close in: 12:30-12:50 are still London's, the
    # fill starts with the 12:55 candle (59), which closes at the NY open
    t = traces_at(replay, 100)
    assert boxes(t["Session zone fill"]) == [(59, 100, 107.0, 108.0), (59, 100, 111.0, 112.0)]
    # NY's last 30m candle (23:00) closes with 5m candle 185, but the 5m candles up to
    # 23:50 (190) still close in NY; 23:55 closes at Tokyo's start
    assert boxes(traces_at(replay, 188)["Session zone box"])[0] == (0, 188, 107.0, 108.0)
    t = traces_at(replay, 199)
    assert boxes(t["Session zone box"]) == [(0, 190, 107.0, 108.0), (12, 190, 111.0, 112.0)]
    assert boxes(t["Session zone fill"]) == [(59, 190, 107.0, 108.0), (59, 190, 111.0, 112.0)]


def test_only_from_5m_to_30m_charts():
    for tf in (Timeframe.M1, Timeframe.H1):
        replay = replay_of([doji(100.0)] * 3, timeframe=tf)
        traces, messages = chart_overlays(replay, ["session_zones"], 2, 0)
        assert traces == []
        assert messages == ["Session zones: built on M30 candles, shown on M5 to M30 charts"]
    replay = replay_of([doji(100.0)] * 3, timeframe=Timeframe.M5)  # no 30m series loaded
    _, messages = chart_overlays(replay, ["session_zones"], 2, 0)
    assert messages == ["Session zones: no M30 candles for this range"]
