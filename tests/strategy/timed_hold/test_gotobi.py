from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from backtester.core.models import Candle, Timeframe
from backtester.core.series import CandleSeries
from backtester.strategy.timed_hold.config import TimedHoldConfig
from backtester.strategy.timed_hold.day_filter import DayFilter
from backtester.strategy.timed_hold.strategy import TimedHold
from backtester.tools.research_grid import expand, load_grid


@pytest.mark.parametrize(('day', 'expected'), [
    (date(2021, 9, 10), True), (date(2021, 9, 24), True),
    (date(2021, 9, 3), True), (date(2019, 4, 26), True),
    (date(2019, 12, 30), True), (date(2021, 7, 30), True),
    (date(2020, 2, 28), True), (date(2021, 9, 13), False),
    (date(2019, 12, 31), False), (date(2019, 5, 5), False),
])
def test_gotobi_dates(day, expected):
    assert DayFilter(TimedHoldConfig(day_filter='gotobi')).qualifies(day) is expected


def test_calendar_loading_and_independence(tmp_path):
    with pytest.raises(FileNotFoundError):
        DayFilter(TimedHoldConfig(day_filter='gotobi', calendar_dir=str(tmp_path)))
    (tmp_path / 'jp_holidays.csv').write_text('date,type,source_url\n2021-09-10,holiday,x\n')
    filt = DayFilter(TimedHoldConfig(day_filter='gotobi', calendar_dir=str(tmp_path)))
    assert filt.qualifies(date(2021, 9, 9))
    assert not filt.qualifies(date(2021, 9, 10))
    (tmp_path / 'nyse_holidays.csv').write_text('date,type\n2021-09-09,closed\n')
    nyse = DayFilter(TimedHoldConfig(day_filter='gotobi', trading_days='nyse',
                                    calendar_dir=str(tmp_path)))
    assert nyse.qualifies(date(2021, 9, 9))
    DayFilter(TimedHoldConfig(day_filter='all', calendar_dir=str(tmp_path)))


def test_gotobi_grid_expands():
    variants, count, sampled = expand(load_grid(Path('research/grids/timed_hold_gotobi.toml')))
    assert len(variants) == count == 8 and not sampled


def test_tokyo_entries_missing_candle_and_no_lookahead():
    tokyo = ZoneInfo('Asia/Tokyo')
    def candle(day, clock, high=105, low=105):
        close = datetime.combine(day, clock, tzinfo=tokyo).astimezone(UTC)
        return Candle(ts=close - timedelta(minutes=1), open=105, high=high, low=low, close=105)

    candles = [candle(date(2021, 9, 8), time(12), 110, 100),
               candle(date(2021, 9, 8), time(16))]
    for day in (date(2021, 9, 9), date(2021, 9, 10), date(2021, 9, 13),
                date(2021, 9, 15)):
        if day != date(2021, 9, 15):  # qualifying date, missing exact entry candle
            candles.append(candle(day, time(3)))
        candles.extend([candle(day, time(3, 1)), candle(day, time(9, 55)),
                        candle(day, time(12), 110, 100), candle(day, time(16))])
    cfg = TimedHoldConfig(zone='Asia/Tokyo', entry_time=time(3), exit_time=time(9, 55),
                          atr_zone='Asia/Tokyo', atr_open=time(9), atr_close=time(16),
                          atr_period=1, day_filter='gotobi')
    def events(data):
        series = CandleSeries('USDJPY', Timeframe.M1, data)
        strategy = TimedHold('USDJPY', cfg)
        out = []
        for i, c in enumerate(data):
            orders = strategy.on_candle(c.ts + timedelta(minutes=1), {Timeframe.M1: series.view(i)})
            exits = strategy.exits()
            out.append(orders)
            for ref in exits:
                strategy.on_trade_closed(ref, None)
        return out
    full = events(candles)
    assert [(c.ts + timedelta(minutes=1)).astimezone(tokyo).date()
            for c, orders in zip(candles, full, strict=True) if orders] == [date(2021, 9, 10)]
    for cut in range(1, len(candles)):
        assert events(candles[:cut]) == full[:cut]
