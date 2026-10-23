"""B9: inclusive dojis survive decimal rounding. Spec: confluences.md › Swing high / low."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from math import inf, nextafter

import pytest
from conftest import build_series

from backtester.core.models import Candle
from backtester.detectors.bos import BosDetector
from backtester.detectors.swings import RangeShare, SwingConfig, SwingDetector, is_doji
from backtester.runner import RunSettings
from backtester.settings import from_json, to_json


@pytest.mark.parametrize("price,body", [(1.0, 0.0000043), (4400.065, 0.065), (100000.0, 0.1)])
@pytest.mark.parametrize("sign", [-1, 1])
def test_exact_decimal_body_is_doji_at_different_price_scales(price, body, sign):
    close = price + sign * body
    candle = Candle(datetime(2026, 1, 5, tzinfo=UTC), price, price + 1, price - 1, close)
    assert is_doji(candle, body)
    # A body materially above the threshold must remain directional.
    close = price + sign * (body + 4e-9 * price)
    larger = Candle(candle.ts, price, price + 1, price - 1, close)
    assert not is_doji(larger, body)


@pytest.mark.parametrize("share", [0.0, 0.1])
def test_configured_tolerance_reaches_shared_doji_consumers_and_round_trips(share):
    config = SwingConfig(doji_range_share=share, doji_relative_tolerance=1e-6)
    threshold = config.doji_threshold("XAUUSD")
    candle = Candle(datetime(2026, 1, 5, tzinfo=UTC), 4400.065, 4400.4, 4399.75, 4400.131)
    assert is_doji(candle, threshold)  # threshold 0.065 plus 0.004400131 tolerance
    strict = SwingConfig(doji_range_share=share, doji_relative_tolerance=0.0)
    assert not is_doji(candle, strict.doji_threshold("XAUUSD"))
    settings = RunSettings()
    settings = replace(settings, detectors=replace(settings.detectors, swings=config))
    assert from_json(to_json(settings)).detectors.swings == config
    with pytest.raises(FrozenInstanceError):
        config.doji_relative_tolerance = 0.0


def test_tolerance_default_and_range_share_decimal_boundary():
    assert SwingConfig().doji_relative_tolerance == 1e-9
    candle = Candle(datetime(2026, 1, 5, tzinfo=UTC), 4400.065, 4400.4, 4399.75, 4400.13)
    assert is_doji(candle, RangeShare(0.1))


def test_tolerance_boundary_is_inclusive_and_next_price_beyond_it_is_not_doji():
    slack = 2**-20
    config = SwingConfig(
        doji_max_body={"TEST": 0.5 - slack}, doji_relative_tolerance=slack / 1024.5
    )
    threshold = config.doji_threshold("TEST")
    candle = Candle(datetime(2026, 1, 5, tzinfo=UTC), 1024.0, 1025.0, 1023.0, 1024.5)
    assert is_doji(candle, threshold)  # body - threshold == tolerance * price exactly
    assert not is_doji(replace(candle, close=nextafter(candle.close, inf)), threshold)


@pytest.mark.parametrize("value", [-1e-9, float("nan"), float("inf"), -float("inf")])
def test_invalid_tolerance_is_rejected(value):
    with pytest.raises(ValueError, match="doji_relative_tolerance"):
        SwingConfig(doji_relative_tolerance=value)


def test_exact_threshold_candle_never_emits_false_bos_and_future_does_not_rewrite_events():
    series = build_series(
        [
            (4399.0, 4400.1, 4398.0, 4400.0),
            (4400.0, 4400.05, 4398.0, 4399.0),  # confirms high 4400.1
            (4400.065, 4400.2, 4400.0, 4400.13),  # exactly 0.065: no BoS
            (4400.13, 4401.0, 4400.0, 4400.8),  # first real bullish break
        ]
    )
    detector = BosDetector.for_symbol("XAUUSD")
    seen = []
    for i in range(len(series)):
        events = detector.update(series.view(i))
        assert all(event.confirmed_index == i for event in events)
        seen.extend(events)
        prefix = BosDetector.for_symbol("XAUUSD")
        assert [e for j in range(i + 1) for e in prefix.update(series.view(j))] == seen
        if i == 2:
            assert seen == []
    assert [e.confirmed_index for e in seen] == [3]


def test_ignored_candle_advances_cursor_without_changing_swing_state():
    series = build_series(
        [
            (110.0, 111.0, 108.0, 109.0),  # red
            (109.0, 120.0, 108.0, 111.0),  # ignored green
            (111.0, 112.0, 109.0, 110.0),  # red: no turn
        ]
    )
    detector = SwingDetector(0.065)
    assert detector.update(series.view(0)) == []
    assert detector.update(series.view(1), ignore=True) == []
    assert detector.update(series.view(2)) == []
    with pytest.raises(ValueError, match="once per candle"):
        detector.update(series.view(2), ignore=True)
