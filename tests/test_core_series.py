import pytest

from backtester.core.errors import LookaheadError
from backtester.core.models import Candle

OHLC = [
    (1.00, 1.05, 0.99, 1.04),
    (1.04, 1.06, 1.01, 1.02),
    (1.02, 1.03, 0.98, 0.99),
    (0.99, 1.02, 0.97, 1.01),
]


def test_view_cannot_read_future(make_series):
    view = make_series(OHLC).view(1)
    assert view.current.close == 1.02
    assert len(view) == 2
    with pytest.raises(LookaheadError):
        view[2]
    with pytest.raises(LookaheadError):
        view.window(0, 3)


def test_negative_index_and_last(make_series):
    view = make_series(OHLC).view(2)
    assert view[-1].close == 0.99
    assert view[-3].close == 1.04
    assert [c.close for c in view.last(2)] == [1.02, 0.99]
    assert [c.close for c in view] == [1.04, 1.02, 0.99]


def test_slicing_is_refused(make_series):
    with pytest.raises(TypeError):
        make_series(OHLC).view(3)[0:2]


def test_series_rejects_unordered(make_candles):
    from backtester.core.models import Timeframe
    from backtester.core.series import CandleSeries

    candles = make_candles(OHLC)
    with pytest.raises(ValueError):
        CandleSeries("TEST", Timeframe.M5, [candles[1], candles[0]])


def test_candle_rejects_inconsistent_ohlc(make_candles):
    ts = make_candles(OHLC)[0].ts
    with pytest.raises(ValueError):
        Candle(ts=ts, open=1.0, high=0.9, low=0.8, close=1.0)
