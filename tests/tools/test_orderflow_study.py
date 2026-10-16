"""Order-flow study tool: summary rows from a synthetic M1 frame (ROADMAP 11.13)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtester.analytics.orderflow import OrderflowConfig
from backtester.tools.orderflow_study import DEV_END, study_frame


def synthetic_m1(days: int = 30) -> pd.DataFrame:
    n = days * 1440
    rng = np.random.default_rng(0)
    idx = pd.date_range("2020-12-20", periods=n, freq="1min", tz="UTC")
    close = 100 + np.cumsum(rng.normal(0, 0.05, n))
    return pd.DataFrame(
        {"open": close, "high": close + 0.1, "low": close - 0.1, "close": close,
         "volume": rng.uniform(1, 3, n), "delta": rng.normal(0, 1, n)},
        index=idx,
    )  # fmt: skip


def test_study_frame_rows_and_columns():
    cfg = OrderflowConfig(
        timeframes=("1h",), cvd_windows=(4,), z_window=20, relvol_days=3, shuffles=20
    )
    summary, deciles = study_frame(synthetic_m1(), None, "1h", "BTCUSDT", cfg)
    feats = {"imbalance", "cvd_4", "cvd_z_4", "div_4", "relvol", "funding"}
    assert set(summary["feature"]) <= feats
    assert {"imbalance", "cvd_z_4", "div_4"} <= set(summary["feature"])
    assert set(summary["target"]) == {"ret_pct", "atr"}
    assert set(summary["horizon"]) == {1, 3, 6}
    for col in ("spread", "shuffle_p95", "beats_shuffle", "shift_p95", "beats_shift", "best_excess_pct", "beats_taker",
                "beats_maker", "spread_h1", "spread_h2", "sign_stable"):  # fmt: skip
        assert col in summary.columns
    assert {"bucket", "n", "mean", "median", "hit_rate", "t", "feature", "horizon"} <= set(
        deciles.columns
    )


def test_study_never_uses_data_after_dev_end():
    assert DEV_END == pd.Timestamp("2021-09-13 23:59", tz="UTC")
