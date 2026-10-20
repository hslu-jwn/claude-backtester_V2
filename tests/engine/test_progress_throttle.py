"""Progress steps of the engine loop: every N candles OR every few seconds, whichever comes
first (ROADMAP 7.6), so short and long runs both move smoothly."""

from __future__ import annotations

import pytest
from conftest import build_series
from test_backtest import NO_COSTS, QUIET, Scripted

from backtester.engine.backtest import Backtest, ProgressThrottle

CANDLES = [QUIET] * 1000


class Clock:
    def __init__(self, step: float):
        self.now, self.step = 0.0, step

    def __call__(self) -> float:
        self.now += self.step
        return self.now


def steps(throttle: ProgressThrottle, clock) -> list[int]:
    calls: list[tuple[int, int]] = []
    bt = Backtest(Scripted({}), [build_series(CANDLES)], NO_COSTS)
    bt.run(lambda d, t: calls.append((d, t)), throttle, clock)
    assert calls[-1] == (1000, 1000)  # always one last step at the end
    assert all(t == 1000 for _, t in calls)
    return [d for d, _ in calls]


def test_a_frozen_clock_reports_every_n_candles_only():
    done = steps(
        ProgressThrottle(every_candles=250, every_seconds=0.2, clock_check_candles=1), Clock(0)
    )
    assert done == [250, 500, 750, 1000]


def test_a_slow_clock_reports_by_time_before_the_candle_step():
    # 0.25 s pass per clock reading, checked every candle: a step for every candle
    done = steps(
        ProgressThrottle(every_candles=500, every_seconds=0.2, clock_check_candles=1), Clock(0.25)
    )
    assert len(done) > 900 and done == sorted(set(done))


def test_the_clock_is_read_only_every_few_candles():
    clock = Clock(0.0)
    reads = []

    def counting():
        reads.append(1)
        return clock()

    steps(
        ProgressThrottle(every_candles=10_000, every_seconds=0.2, clock_check_candles=100), counting
    )
    assert len(reads) <= 1000 // 100 + 2  # not once per candle


def test_the_default_throttle_keeps_the_old_500_candle_step():
    t = ProgressThrottle()
    assert t.every_candles == 500 and t.every_seconds == pytest.approx(0.2)
