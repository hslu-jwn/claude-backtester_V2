"""SMA cross with an optional ATR band, shared by strategy 4 and strategy 2's trend filter.

Spec: strategy-trend-following.md › Trend signal (`sma`, SMA band).
"""

from __future__ import annotations

import pytest

from backtester.core.models import Direction
from backtester.strategy.trend_following.indicators import SmaBandCross

BULL, BEAR = Direction.BULLISH, Direction.BEARISH


def feed(cross, closes, atrs=None):
    atrs = atrs or [None] * len(closes)
    return [cross.update(c, a) for c, a in zip(closes, atrs, strict=True)]


def test_plain_cross_fires_only_on_the_cross_candle():
    # SMA(3): candle 2 = 1.0 (no previous SMA yet); candle 3 = 2.0, close 4 > 2 after
    # close 1 <= SMA 1 -> long; candle 4 stays above; candle 5 SMA 3.0, close 0 -> short
    out = feed(SmaBandCross(3), [1.0, 1.0, 1.0, 4.0, 5.0, 0.0])
    assert out == [None, None, None, BULL, None, BEAR]


def test_band_moves_the_line_by_band_x_atr():
    # band 1 x ATR 2: candle 3 line = 2 + 2 = 4, close 4 is not above -> nothing;
    # candle 4 SMA 11/3, line 17/3, close 6 above after close 4 <= 4 -> long
    out = feed(SmaBandCross(3, band_atr=1.0), [1.0, 1.0, 1.0, 4.0, 6.0], [2.0] * 5)
    assert out == [None, None, None, None, BULL]


def test_band_needs_the_atr_now_and_at_the_previous_candle():
    closes = [1.0, 1.0, 1.0, 4.0, 6.0]
    out = feed(SmaBandCross(3, band_atr=1.0), closes, [None, None, None, None, 2.0])
    assert out == [None] * 5  # the cross at candle 4 has no ATR at candle 3
    plain = feed(SmaBandCross(3), closes)  # band 0 ignores the ATR
    assert plain == [None, None, None, BULL, None]


def test_bearish_is_the_mirror_of_bullish():
    up = feed(SmaBandCross(3, band_atr=0.5), [1.0, 1.0, 1.0, 4.0, 6.0, 0.0], [2.0] * 6)
    down = feed(SmaBandCross(3, band_atr=0.5), [-1.0, -1.0, -1.0, -4.0, -6.0, 0.0], [2.0] * 6)
    flip = {BULL: BEAR, BEAR: BULL, None: None}
    assert down == [flip[d] for d in up]


@pytest.mark.parametrize(("period", "band"), [(1, 0.0), (3, -0.1)])
def test_rejects_bad_parameters(period, band):
    with pytest.raises(ValueError):
        SmaBandCross(period, band_atr=band)
