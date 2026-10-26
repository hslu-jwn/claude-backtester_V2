"""Cases: all half-block combinations; planted winner; reversed winner; tied ranks;
noise PBO near half; OOS-only purge at internal boundaries; odd S, short/faulty input.
"""

import numpy as np
import pytest

from backtester.analytics.pbo import PBOConfig, cscv_pbo


def test_known_winner_and_ties():
    x = np.tile([-1.0, 1.0], 40)
    result = cscv_pbo(np.column_stack((x + 4, x)), PBOConfig(blocks=4, purge_days=0))
    assert result["pbo"] == 0
    assert result["median_oos_rank"] == pytest.approx(2 / 3)
    assert len(result["pairs"]) == 6
    # Each pair is the winner's IS/OOS scores, not two competitors' scores.
    expected = 4 / np.std(x[:40], ddof=1)
    for pair in result["pairs"]:
        assert pair == pytest.approx([expected, expected])
    tied = cscv_pbo(np.column_stack((x, x)), PBOConfig(blocks=4, purge_days=0))
    assert tied["pbo"] == 1 and tied["median_oos_rank"] == 0.5
    assert tied["degradation_slope"] is None


def test_reversal_and_boundary_purge():
    x = np.tile([-1.0, 1.0], 10)
    a = np.r_[x + 4, x - 4]
    result = cscv_pbo(np.column_stack((a, -a)), PBOConfig(blocks=2, purge_days=0))
    assert result["pbo"] == 1
    assert result["degradation_slope"] is None  # identical IS scores
    # 4 blocks of 6 days: remove two from each internal OOS edge only.
    rng = np.random.default_rng(4)
    matrix = rng.normal(size=(24, 3))
    purged = cscv_pbo(matrix, PBOConfig(blocks=4, purge_days=2))
    ins = matrix[:12]
    oos = matrix[[14, 15, 20, 21, 22, 23]]
    winner = np.argmax(ins.mean(0) / ins.std(0, ddof=1))
    assert purged["pairs"][0] == pytest.approx(
        [
            (ins.mean(0) / ins.std(0, ddof=1))[winner],
            (oos.mean(0) / oos.std(0, ddof=1))[winner],
        ]
    )


def test_noise_and_edge():
    matrix = np.random.default_rng(42).normal(size=(1600, 20))
    cfg = PBOConfig(blocks=8)
    assert 0.2 < cscv_pbo(matrix, cfg)["pbo"] < 0.8
    matrix[:, 0] += 2
    assert cscv_pbo(matrix, cfg)["pbo"] == 0


def test_constant_decimal_and_large_offset():
    cfg = PBOConfig(blocks=4, purge_days=0)
    constant = cscv_pbo(np.tile([0.1, 0.3], (240, 1)), cfg)
    assert constant["pairs"] == [[0.0, 0.0]] * 6
    assert constant["pbo"] == 1
    matrix = np.random.default_rng(7).normal(size=(80, 3)) + 1e9
    result = cscv_pbo(matrix, cfg)
    ins, oos = matrix[:40], matrix[40:]
    winner = np.argmax(ins.mean(0) / ins.std(0, ddof=1))
    assert result["pairs"][0] == pytest.approx(
        [
            (ins.mean(0) / ins.std(0, ddof=1))[winner],
            (oos.mean(0) / oos.std(0, ddof=1))[winner],
        ],
        rel=1e-6,
    )


def test_invalid_and_short():
    with pytest.raises(ValueError, match="even"):
        PBOConfig(blocks=3)
    with pytest.raises(ValueError):
        PBOConfig(purge_days=-1)
    for matrix in (np.zeros((200, 1)), np.zeros((16, 2)), np.empty((0, 0))):
        result = cscv_pbo(matrix)
        assert result["pbo"] is None and result["reason"]
    with pytest.raises(ValueError):
        cscv_pbo([[1, np.nan]])
