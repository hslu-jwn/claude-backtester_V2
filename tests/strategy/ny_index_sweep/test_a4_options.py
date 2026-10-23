"""A4 regressions for optional strategy behavior; spec defaults stay unchanged."""

from dataclasses import replace
from datetime import UTC, datetime

import pytest
from test_setup_steps import (
    DOJI,
    LONG,
    M1,
    M5,
    NO_EQ,
    Frame,
    bos,
    drive,
    harness,
    minute,
)

from backtester.core.models import Candle, Timeframe
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.setup import Context, Step
from backtester.strategy.ny_index_sweep.strategy import NyIndexSweep
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.strategy import SessionZoneSweep


@pytest.mark.parametrize("step", [Step.BOS, Step.TAPPED, Step.ENTRY, Step.IN_TRADE])
def test_htf_close_beyond_cancels_after_setup_bos(step):
    m1, frames, setup = harness()
    drive(m1, frames, setup, until=minute(8))
    setup.step = step
    setup.entry_bos = bos(LONG, 100.2, 8, minute(9))
    setup.sweep_tf = Timeframe.H1
    frames[Timeframe.H1] = Frame(Timeframe.H1, [Candle(minute(-50), 100, 101, 98, 98.9)])
    frames[Timeframe.H1].step(minute(10))
    for tf in (M1, M5):
        frames[tf].step(minute(10))
    cfg = replace(NO_EQ, sweep_close_beyond_counts=False)
    setup.advance(Context(minute(10), m1[9], frames, cfg, DOJI))
    assert setup.step is Step.DONE
    assert setup.ended == "sweep-TF close beyond the swept level"


@pytest.mark.parametrize(
    "entry,next_close",
    [
        ("2026-09-02T18:00", "2026-09-03T13:00"),
        ("2026-01-14T19:00", "2026-01-15T14:00"),
    ],
)
def test_rollover_cutoff_survives_missing_entry_day_candles(entry, next_close):
    strategy = NyIndexSweep("NAS100", NyIndexSweepConfig(close_before_rollover=True))
    ref = object()
    strategy._open = [(ref, datetime.fromisoformat(entry).replace(tzinfo=UTC))]
    strategy._close_before_rollover(datetime.fromisoformat(next_close).replace(tzinfo=UTC))
    assert strategy.exits() == [ref]


def test_equal_timeframes_feed_both_trackers_once(monkeypatch):
    strategy = SessionZoneSweep("XAUUSD", SessionZoneSweepConfig(limit_timeframe=Timeframe.H1))
    frame = Frame(Timeframe.H1, [Candle(minute(0), 100, 101, 99, 100)])
    frame.step(minute(60))
    seen = [[], []]
    for i, tracker in enumerate((strategy.obstacles, strategy.limits)):
        monkeypatch.setattr(tracker, "update", lambda view, i=i: seen[i].append(view.cursor))
    for _ in range(2):
        strategy._catch_up(strategy.obstacles, frame.view)
        strategy._catch_up(strategy.limits, frame.view)
    assert seen == [[0], [0]]
