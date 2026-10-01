from datetime import timedelta

from backtester.core.models import Timeframe
from backtester.core.mtf import HigherTimeframeClock


def test_htf_candle_visible_only_after_close(make_series):
    h1 = make_series([(1.0, 1.1, 0.9, 1.05), (1.05, 1.2, 1.0, 1.1)], Timeframe.H1)
    clock = HigherTimeframeClock(h1)
    start = h1.view(0).current.ts  # H1 candle opening at 00:00

    # close of the 00:50 M5 candle = 00:55 -> the first H1 candle is still open
    assert clock.view_at(start + timedelta(minutes=55)) is None
    # close of the 00:55 M5 candle = 01:00 -> now it has closed
    view = clock.view_at(start + timedelta(hours=1))
    assert view is not None and view.cursor == 0
    assert clock.view_at(start + timedelta(hours=2)).cursor == 1
