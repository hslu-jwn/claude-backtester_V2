"""Literal outputs captured from the legacy tools before extraction."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import numpy as np

from backtester.tools.alternating_path_gates import block_bootstrap
from backtester.tools.timed_hold_gates import difference_bootstrap
from backtester.tools.us_close_de_open_gates import control_difference

X = np.array([-2., 1., 3., -1., 4., 0., 2., -3., 5., 1., 2.])


def trades(values, month, alternating=False):
    return [SimpleNamespace(
        entry_time=datetime(2019, month, 1, 8, tzinfo=UTC) + timedelta(days=i),
        r_net=v, direction="short" if alternating and i % 2 else "long",
    ) for i, v in enumerate(values)]


def test_pinned_block_bootstrap():
    assert block_bootstrap(X, 5, 10_000, 2026110) == {
        "lower_2_5": 0.45454545454545453, "lower_5": 0.5454545454545454,
        "mean": 1.0909090909090908,
    }


def test_pinned_difference_bootstrap():
    assert difference_bootstrap(trades(X, 3), trades(X / 2, 4)) == {
        "difference": 0.5454545454545454, "lower_2_5": -0.18181818181818182,
        "lower_5": -0.09090909090909083,
    }


def test_pinned_control_difference():
    assert control_difference(trades(X, 3, True), trades(X / 2, 4), trades(-X / 3, 5)) == {
        "difference": 0.9586776859504131, "lower_2_5": 0.2672176308539945,
        "lower_5": 0.3856749311294766, "n_long": 6, "n_short": 5,
        "control_long_trades": 11, "control_short_trades": 11,
    }


def test_shared_helpers_and_wraparound():
    from backtester.analytics.bootstrap import block_indices, block_means

    np.testing.assert_array_equal(block_indices(4, 3, np.array([3, 1])), [3, 0, 1, 1])
    np.testing.assert_array_equal(block_means(np.array([7.]), 5, 3,
                                            np.random.default_rng(1)), [7., 7., 7.])
    rng = np.random.default_rng(2026110)
    means = block_means(X, 5, 10_000, rng)
    assert float(np.quantile(means, .025)) == 0.45454545454545453


def _legacy_interleaved(arrays, block, resamples, seed):
    """The pre-vectorization loop: one draw per series per resample, empty series give 0."""
    from backtester.analytics.bootstrap import block_indices

    rng = np.random.default_rng(seed)
    out = np.zeros((resamples, len(arrays)))
    for i in range(resamples):
        for j, x in enumerate(arrays):
            if len(x):
                n = len(x)
                out[i, j] = x[block_indices(n, block, rng.integers(0, n, size=-(-n // block)))].mean()
    return out


def test_interleaved_means_match_the_legacy_draw_order_bit_for_bit():
    from backtester.analytics.bootstrap import block_means, interleaved_block_means

    gen = np.random.default_rng(7)
    cases = [  # (series lengths, block, resamples): odd sizes, block > n, an empty series, chunk edges
        ((11, 0, 7), 5, 300), ((1, 3), 5, 50), ((5000, 13), 5, 1000), ((2, 9, 4), 1, 200)]
    for lengths, block, resamples in cases:
        arrays = [gen.normal(size=n) for n in lengths]
        got = interleaved_block_means(arrays, block, resamples, np.random.default_rng(99))
        np.testing.assert_array_equal(got, _legacy_interleaved(arrays, block, resamples, 99))
    x = gen.normal(size=37)
    np.testing.assert_array_equal(block_means(x, 5, 400, np.random.default_rng(3)),
                                  _legacy_interleaved([x], 5, 400, 3)[:, 0])
    assert interleaved_block_means([x], 5, 0, np.random.default_rng(3)).shape == (0, 1)
    assert np.isnan(block_means(np.array([]), 5, 3, np.random.default_rng(3))).all()  # legacy: NaN, not 0
