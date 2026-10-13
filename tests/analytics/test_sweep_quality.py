"""How good a liquidity sweep was: what price does after the sweep exists.

Entry = close of the BOS candle (the sweep exists from there), stop = the sweeping wick,
risk = their distance. Candles are (open, high, low, close); a candle holding both the stop
and a target counts as the stop (conservative, CLAUDE.md invariant).
"""

from __future__ import annotations

import pytest
from conftest import build_series

from backtester.analytics.sweep_quality import sweep_outcome
from backtester.core.models import Direction

BEAR, BULL = Direction.BEARISH, Direction.BULLISH


def candles(ohlc):
    return list(build_series(ohlc).view(len(ohlc) - 1))


# bearish sweep: BOS candle 0 closes 100, sweeping wick 104 -> risk 4, 1R = 96, 2R = 92
def test_both_targets_reached_before_the_stop():
    c = candles([(101, 102, 99, 100), (100, 101, 97, 98), (98, 99, 95, 96), (96, 97, 91, 92)])
    out = sweep_outcome(c, BEAR, extreme=104.0, index=0, horizon=10)
    assert (out.risk, out.stopped) == (4.0, False)
    assert (out.r1, out.r2) == (1.0, 2.0)
    assert out.mfe_r == pytest.approx(9 / 4)


def test_stop_hit_first_is_minus_one_for_both_targets():
    c = candles([(101, 102, 99, 100), (100, 104.5, 99, 103), (103, 104, 90, 91)])
    out = sweep_outcome(c, BEAR, extreme=104.0, index=0, horizon=10)
    assert (out.r1, out.r2, out.stopped, out.mfe_r) == (-1.0, -1.0, True, 0.0)


def test_a_candle_with_stop_and_target_counts_as_the_stop():
    c = candles([(101, 102, 99, 100), (100, 104.0, 90, 95)])
    out = sweep_outcome(c, BEAR, extreme=104.0, index=0, horizon=10)
    assert (out.r1, out.r2, out.stopped) == (-1.0, -1.0, True)
    assert out.mfe_r == 0.0  # the stop candle's low is not counted


def test_timeout_is_the_close_in_r_limited_to_minus_one_and_the_target():
    c = candles([(101, 102, 99, 100), (100, 101, 97.5, 98), (98, 99, 97, 98)])
    out = sweep_outcome(c, BEAR, extreme=104.0, index=0, horizon=2)
    assert not out.stopped
    assert out.r1 == out.r2 == pytest.approx(0.5)  # (100 - 98) / 4
    c = candles([(101, 102, 99, 100), (100, 103, 99, 103), (103, 103.5, 102, 103.2)])
    assert sweep_outcome(c, BEAR, extreme=104.0, index=0, horizon=2).r1 == pytest.approx(-0.8)


def test_the_horizon_limits_the_candles_looked_at():
    c = candles([(101, 102, 99, 100), (100, 101, 99, 100), (100, 101, 90, 91)])
    assert sweep_outcome(c, BEAR, extreme=104.0, index=0, horizon=1).r1 == 0.0
    assert sweep_outcome(c, BEAR, extreme=104.0, index=0, horizon=2).r1 == 1.0


def test_bullish_sweep_is_mirrored():
    # entry 100, wick low 96 -> risk 4; up to 104 = 1R
    c = candles([(99, 101, 98, 100), (100, 103, 99, 102), (102, 105, 101, 104)])
    out = sweep_outcome(c, BULL, extreme=96.0, index=0, horizon=10)
    assert (out.risk, out.r1, out.r2) == (4.0, 1.0, 1.0)  # 2R = 108 never reached: timeout
    assert out.mfe_r == pytest.approx(5 / 4)


def test_no_risk_means_no_outcome():
    c = candles([(101, 102, 99, 100), (100, 101, 97, 98)])
    assert sweep_outcome(c, BEAR, extreme=100.0, index=0, horizon=5) is None  # entry at the wick
    assert sweep_outcome(c, BEAR, extreme=104.0, index=1, horizon=5) is None  # nothing after


def test_unstopped_excursions_and_drift_over_the_whole_horizon():
    # entry 100: favorable up to 9 (low 91), adverse up to 3 (high 103), last close 92
    c = candles([(101, 102, 99, 100), (100, 103, 97, 98), (98, 99, 91, 92)])
    out = sweep_outcome(c, BEAR, extreme=104.0, index=0, horizon=10)
    assert (out.fav, out.adv, out.drift) == (9.0, 3.0, 8.0)
    # these ignore the stop: the stop candle still counts
    c = candles([(101, 102, 99, 100), (100, 105, 90, 95)])
    out = sweep_outcome(c, BEAR, extreme=104.0, index=0, horizon=10)
    assert out.stopped and (out.fav, out.adv, out.drift) == (10.0, 5.0, 5.0)
