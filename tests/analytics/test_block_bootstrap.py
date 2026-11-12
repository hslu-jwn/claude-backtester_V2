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
