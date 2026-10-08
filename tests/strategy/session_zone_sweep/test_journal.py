"""Per-session journal of strategy 1: session zones and setup confluences.
Spec: ROADMAP.md › 3.4, strategy-session-zones.md › Session inspection view.

Data: the hand-built London / New York day (scenario.py). In New York the long setup on the
London low zone gets its 30m reaction at 13:30 (the 13:00 30m candle) after the 5m BOS
(13:20 close); the FVG 109.1-109.5 is tapped and confirmed at 13:40 -> entry.
"""

from __future__ import annotations

from datetime import UTC, datetime

import scenario
from scenario import LONDON, NY_SETUP, TO_TARGET, doji

from backtester.engine.backtest import run_backtest
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.strategy import SessionZoneSweep

FULL = LONDON + NY_SETUP + TO_TARGET
DAY = "2026-01-05T"


def records(ohlc=FULL, config=None, run_end=None):
    strategy = SessionZoneSweep(scenario.SYMBOL, config)
    run_backtest(strategy, scenario.series(ohlc))
    return strategy.session_records(run_end)


def by_kind(session):
    return {(c["kind"], c["top"], c["bottom"]): c for c in session["confluences"]}


def test_new_york_session_has_the_london_zones_with_their_roles():
    [ny] = records()
    assert (ny["session"], ny["start"]) == ("new_york", DAY + "13:00:00+00:00")
    zones = {z["side"]: z for z in ny["zones"]}
    assert (zones["low"]["top"], zones["low"]["bottom"], zones["low"]["role"]) == (
        108.0,
        107.0,
        "support",
    )
    assert zones["low"]["start_time"] == DAY + "08:00:00+00:00"  # first 30m turn candle
    assert (zones["high"]["top"], zones["high"]["bottom"], zones["high"]["role"]) == (
        114.0,
        113.0,
        "resistance",
    )
    assert zones["high"]["formed_in"] == "london" and zones["high"]["breaks"] == []


def test_the_entry_fvg_is_setup_confirmed_traded_and_ends_at_the_entry():
    [ny] = records()
    fvg = by_kind(ny)[("fvg", 109.5, 109.1)]
    assert fvg["direction"] == "long" and fvg["setup_zones"] == ["low"]
    assert fvg["setup_confirmed"] and fvg["traded"]
    assert fvg["start_time"] == DAY + "13:15:00+00:00"  # FVG candle 1 (d)
    assert (fvg["end"], fvg["end_time"]) == ("confirmed", DAY + "13:40:00+00:00")


def test_other_candidates_of_the_setup_are_kept_unconfirmed():
    [ny] = records()
    confluences = by_kind(ny)
    ob = confluences[("order_block", 108.8, 108.1)]
    assert not ob["setup_confirmed"] and not ob["traded"]
    assert ob["end"] == "run_end" and ob["end_time"] is None
    # part of the setup only from its step 4: the 30m reaction at 13:30 (BOS was before)
    assert all(c["linked_at"] >= DAY + "13:30:00+00:00" for c in ny["confluences"])
    assert ("equilibrium", 109.3, 108.1) in confluences  # the BOS move's discount half


def test_a_rejected_signal_is_setup_confirmed_but_not_traded():
    [ny] = records(LONDON + NY_SETUP, SessionZoneSweepConfig(max_sl_atr_mult=1.0))
    fvg = by_kind(ny)[("fvg", 109.5, 109.1)]
    assert fvg["setup_confirmed"] and not fvg["traded"]


def test_session_end_closes_open_confluences_and_expires_the_zones():
    # dojis from 14:35 until after Tokyo's start (00:00 UTC)
    ohlc = FULL + [doji(112.8)] * 125
    ny = next(s for s in records(ohlc) if s["session"] == "new_york")
    ob = by_kind(ny)[("order_block", 108.8, 108.1)]
    assert (ob["end"], ob["end_time"]) == ("session_end", "2026-01-06T00:00:00+00:00")
    assert {(z["end"], z["end_time"]) for z in ny["zones"]} == {
        ("expired", "2026-01-06T00:00:00+00:00")
    }


def test_records_still_open_end_at_the_run_end():
    end = datetime(2026, 1, 5, 15, tzinfo=UTC)
    [ny] = records(run_end=end)
    ob = by_kind(ny)[("order_block", 108.8, 108.1)]
    assert (ob["end"], ob["end_time"]) == ("run_end", end.isoformat())


def _finished(sessions):
    """Zones and confluences whose end is final, by session."""
    out = set()
    for s in sessions:
        for kind, items in (("zone", s["zones"]), ("confluence", s["confluences"])):
            for item in items:
                if item["end"] != "run_end":
                    out.add((s["start"], kind, repr(sorted(item.items()))))
    return out


def test_no_lookahead_future_candles_never_change_finished_records():
    full_ohlc = FULL + [doji(112.8)] * 125
    full = _finished(records(full_ohlc))
    assert full
    for cut in range(len(LONDON), len(full_ohlc), 7):
        assert _finished(records(full_ohlc[:cut])) <= full
