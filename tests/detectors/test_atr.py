"""ATR + strong-move filter. Spec: confluences.md › Strong-move filter."""

from __future__ import annotations

import random

import pandas as pd
import pytest
from conftest import build_series

from backtester.detectors.atr import (
    Atr,
    StrongMoveConfig,
    StrongMoveFilter,
    is_strong_move,
    true_range,
)
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig

# n = 3. True ranges: 2, 2, 1, 3.5 (gap up from 11 to 13.5), 5.5
GAP_SERIES = [
    (10.0, 11.0, 9.0, 10.5),  # TR 2 (first candle: high - low)
    (10.5, 12.0, 10.0, 11.0),  # TR 2
    (11.0, 11.5, 10.5, 11.0),  # TR 1 -> seed ATR = 5/3
    (14.0, 14.5, 13.5, 14.0),  # range 1, TR 3.5 (gap) -> ATR 41/18
    (14.0, 19.0, 13.5, 18.5),  # range 5.5 >= 2 * 41/18 -> strong; ATR 181/54
]


def run_atr(series, period):
    atr = Atr(period)
    return [atr.update(series.view(i)) for i in range(len(series))]


def run_filter(series, config):
    f = StrongMoveFilter(config)
    return f, [f.update(series.view(i)) for i in range(len(series))]


def random_ohlc(count, seed=7):
    rng = random.Random(seed)
    out, close = [], 2000.0
    for i in range(count):
        o = close + (rng.uniform(-3, 3) if i % 50 == 0 else 0.0)  # occasional gaps
        c = o + rng.uniform(-2, 2) * (4 if rng.random() < 0.05 else 1)
        h = max(o, c) + rng.uniform(0, 1)
        lo = min(o, c) - rng.uniform(0, 1)
        out.append((o, h, lo, c))
        close = c
    return out


# --- ATR values ---------------------------------------------------------------------


def test_true_range_uses_previous_close_and_first_candle_uses_range(make_candles):
    c = make_candles([(14.0, 14.5, 13.5, 14.0)])[0]
    assert true_range(c, None) == 1.0
    assert true_range(c, 11.0) == 3.5  # gap up: high - prev close
    assert true_range(c, 17.0) == 3.5  # gap down: prev close - low


def test_warm_up_then_sma_seed_then_wilder_smoothing():
    values = run_atr(build_series(GAP_SERIES), period=3)
    assert values[:2] == [None, None]
    assert values[2] == pytest.approx(5 / 3)
    assert values[3] == pytest.approx(41 / 18)  # (5/3 * 2 + 3.5) / 3, gap counts
    assert values[4] == pytest.approx(181 / 54)  # (41/18 * 2 + 5.5) / 3


def test_period_one_is_just_the_true_range():
    assert run_atr(build_series(GAP_SERIES), period=1) == [2.0, 2.0, 1.0, 3.5, 5.5]


def test_at_returns_value_known_at_that_close_and_refuses_unprocessed():
    series = build_series(GAP_SERIES)
    atr = Atr(3)
    for i in range(3):
        atr.update(series.view(i))
    assert atr.at(2) == pytest.approx(5 / 3)
    assert atr.current == pytest.approx(5 / 3)
    with pytest.raises(IndexError):
        atr.at(3)


def test_matches_pandas_wilder_reference_once_seed_has_decayed():
    """Independent check: pandas ewm(alpha=1/n) on true range = RMA. Seeds differ
    (pandas starts at the first TR), but after hundreds of candles they agree."""
    n = 14
    series = build_series(random_ohlc(600))
    ours = run_atr(series, n)
    df = pd.DataFrame(random_ohlc(600), columns=["o", "h", "l", "c"])
    prev = df["c"].shift()
    tr = pd.concat([df["h"] - df["l"], (df["h"] - prev).abs(), (df["l"] - prev).abs()], axis=1)
    ref = tr.max(axis=1).ewm(alpha=1 / n, adjust=False).mean()
    assert ours[-100:] == pytest.approx(ref.iloc[-100:].tolist(), rel=1e-9)


# --- strong move --------------------------------------------------------------------


def test_is_strong_move_boundary_and_warm_up(make_candles):
    c = make_candles([(10.0, 12.0, 10.0, 11.0)])[0]  # range 2
    assert is_strong_move(c, 1.0, 2.0)  # exactly k * ATR counts
    assert not is_strong_move(c, 1.01, 2.0)
    assert not is_strong_move(c, None, 2.0)


def test_candle_is_compared_with_atr_before_it_not_including_itself():
    f, strong = run_filter(build_series(GAP_SERIES), StrongMoveConfig(atr_period=3, atr_mult=2.0))
    # candle 4: range 5.5 vs 2 * 41/18 = 4.56 -> strong.
    # (Including itself, 2 * 181/54 = 6.70 would reject it.)
    assert strong == [False, False, False, False, True]
    assert f.threshold_at(4) == pytest.approx(2 * 41 / 18)
    assert f.is_strong(4)


def test_gap_raises_atr_but_does_not_make_the_gap_candle_strong():
    _, strong = run_filter(build_series(GAP_SERIES), StrongMoveConfig(atr_period=3))
    assert strong[3] is False  # range 1, the gap is not part of the candle's range


def test_nothing_is_strong_until_n_earlier_candles_exist():
    # huge candle at index 3 with n = 3: ATR of candles 0..2 exists -> may be strong;
    # same candle at index 2 has only 2 earlier candles -> never strong.
    calm = (10.0, 10.5, 9.5, 10.0)
    big = (10.0, 30.0, 9.0, 29.0)
    _, strong = run_filter(build_series([calm, calm, big]), StrongMoveConfig(atr_period=3))
    assert strong == [False, False, False]
    f, strong = run_filter(build_series([calm, calm, calm, big]), StrongMoveConfig(atr_period=3))
    assert strong == [False, False, False, True]
    assert f.threshold_at(0) is None and f.threshold_at(2) is None


def test_exact_threshold_through_the_filter():
    one = (10.0, 11.0, 10.0, 10.5)  # TR 1 each -> ATR exactly 1.0
    _, strong = run_filter(
        build_series([one, one, one, (10.5, 12.0, 10.0, 11.0)]), StrongMoveConfig(atr_period=3)
    )
    assert strong[3] is True  # range 2.0 == 2 * 1.0


def test_config_validation_and_strategy_default():
    with pytest.raises(ValueError):
        StrongMoveConfig(atr_period=0)
    with pytest.raises(ValueError):
        StrongMoveConfig(atr_mult=0)
    cfg = SessionZoneSweepConfig().strong_move
    assert (cfg.atr_period, cfg.atr_mult) == (14, 2.0)


# --- no lookahead -------------------------------------------------------------------


def test_no_lookahead_future_candles_never_change_past_values():
    ohlc = random_ohlc(300)
    cfg = StrongMoveConfig()
    full_atr = run_atr(build_series(ohlc), cfg.atr_period)
    _, full_strong = run_filter(build_series(ohlc), cfg)
    for cut in (1, 13, 14, 15, 100, 299):
        short = build_series(ohlc[:cut])
        assert run_atr(short, cfg.atr_period) == full_atr[:cut]
        assert run_filter(short, cfg)[1] == full_strong[:cut]


def test_no_lookahead_value_is_emitted_at_its_own_candle():
    # each update returns the value for view.current, and nothing beyond is queryable
    series = build_series(GAP_SERIES)
    f = StrongMoveFilter(StrongMoveConfig(atr_period=3))
    for i in range(len(series)):
        f.update(series.view(i))
        with pytest.raises(IndexError):
            f.is_strong(i + 1)
        with pytest.raises(IndexError):
            f.atr.at(i + 1)


def test_update_out_of_order_or_twice_raises():
    series = build_series(GAP_SERIES)
    atr = Atr(3)
    atr.update(series.view(0))
    with pytest.raises(ValueError):
        atr.update(series.view(0))  # same candle twice
    with pytest.raises(ValueError):
        atr.update(series.view(2))  # skipped a candle
