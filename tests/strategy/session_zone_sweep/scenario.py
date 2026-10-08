"""A hand-built XAUUSD day for strategy 1 tests: 5m candles, aggregated to 30m, 1h, 4h.

Monday 2026-01-05 (winter, no DST): London starts 08:00 UTC, New York 13:00 UTC.
Fillers are dojis (body 0), so they form no swings and break nothing.

London (07:30-12:55 5m candles):
- 30m 08:00 red (110 -> 108, low 107.5) + 30m 08:30 green (108 -> 109, low 107): 30m swing
  low 107, London LOW ZONE 107-108. On 5m: swing low 107.
- 30m 09:00 green (109 -> 113, high 114) + 30m 09:30 red (113 -> 112): 30m swing high
  114, London HIGH ZONE 113-114. On 5m: swing high 114.
- Dojis at 109.5 until 13:00: London's last close 109.5 -> low zone support, high zone
  resistance in New York.
New York, 5m from 13:00 (index = NY_FIRST + letter):
  a 13:00 red   109.5 -> 107.6, low 107.4   sweep into the support zone (low < 108)
  b 13:05 green 107.6 -> 108.6              5m swing low 107.4
  c 13:10 red   108.6 -> 108.2, high 108.8  5m swing high 108.8, low 108.1 (the BOS leg's low)
  d 13:15 green 108.2 -> 109.0, high 109.1  bullish 5m BOS (first BOS: no trend yet)
  e 13:20 green 109.0 -> 110.0              FVG candle 2
  f 13:25 green 110.0 -> 110.4, low 109.5   bullish FVG 109.1-109.5 (5m trend up)
  -> 30m 13:00: low 107.4 (sweep), green close 110.4 above 108 (reaction)
  g 13:30 red   110.4 -> 109.6, low 109.3   taps the FVG
  h 13:35 green 109.6 -> 110.0              confirms the FVG: ENTRY at 110.0 (13:40)
  i 13:40 green 110.0 -> 112.8              runs to the target
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backtester.core.models import Candle, Timeframe
from backtester.core.series import CandleSeries

SYMBOL = "XAUUSD"
START = datetime(2026, 1, 5, 7, 30, tzinfo=UTC)
M5 = Timeframe.M5.duration


def doji(p: float) -> tuple[float, float, float, float]:
    return (p, p + 0.02, p - 0.02, p)


def bar(o: float, c: float, hi: float | None = None, lo: float | None = None):
    return (o, max(o, c) + 0.1 if hi is None else hi, min(o, c) - 0.1 if lo is None else lo, c)


def thirty(first, rest_at: float):
    """One 30m candle: its first 5m candle, then 5 dojis at `rest_at`."""
    return [first, *[doji(rest_at)] * 5]


LONDON = [
    *[doji(110.0)] * 6,  # 07:30
    *thirty(bar(110.0, 108.0, lo=107.5), 108.0),  # 08:00 red
    *thirty(bar(108.0, 109.0, lo=107.0), 109.0),  # 08:30 green: swing low 107
    *thirty(bar(109.0, 113.0, hi=114.0), 113.0),  # 09:00 green
    *thirty(bar(113.0, 112.0, hi=113.2), 112.0),  # 09:30 red: swing high 114
    *[doji(109.5)] * (6 * 6),  # 10:00 .. 12:55
]
NY_FIRST = len(LONDON)  # 13:00
NY_SETUP = [
    bar(109.5, 107.6, hi=109.6, lo=107.4),  # a
    bar(107.6, 108.6, lo=107.5, hi=108.7),  # b
    bar(108.6, 108.2, hi=108.8, lo=108.1),  # c
    bar(108.2, 109.0, lo=108.1, hi=109.1),  # d: BOS
    bar(109.0, 110.0, lo=108.9, hi=110.1),  # e
    bar(110.0, 110.4, lo=109.5, hi=110.5),  # f: FVG 109.1-109.5
    bar(110.4, 109.6, hi=110.5, lo=109.3),  # g: tap
    bar(109.6, 110.0, lo=109.5, hi=110.1),  # h: confirm -> entry
]
ENTRY_INDEX = NY_FIRST + 7
BOS_INDEX = NY_FIRST + 3
TO_TARGET = [bar(110.0, 112.8, lo=109.9, hi=112.8), *[doji(112.8)] * 10]


def candles(ohlc, start: datetime = START) -> list[Candle]:
    return [Candle(start + i * M5, o, h, lo, c) for i, (o, h, lo, c) in enumerate(ohlc)]


def aggregate(m5: list[Candle], timeframe: Timeframe) -> list[Candle]:
    """Higher-timeframe candles from 5m ones, bucketed by UTC-floored open time."""
    minutes = timeframe.value
    buckets: dict[datetime, list[Candle]] = {}
    for c in m5:
        floor = c.ts - timedelta(minutes=(c.ts.hour * 60 + c.ts.minute) % minutes)
        buckets.setdefault(floor, []).append(c)
    return [
        Candle(
            ts,
            cs[0].open,
            max(c.high for c in cs),
            min(c.low for c in cs),
            cs[-1].close,
        )
        for ts, cs in sorted(buckets.items())
    ]


def series(ohlc, symbol: str = SYMBOL) -> list[CandleSeries]:
    """5m, 30m, 1h and 4h series of the same 5m candles."""
    m5 = candles(ohlc)
    return [
        CandleSeries(symbol, Timeframe.M5, m5),
        *(CandleSeries(symbol, tf, aggregate(m5, tf)) for tf in HIGHER),
    ]


HIGHER = (Timeframe.M30, Timeframe.H1, Timeframe.H4)
