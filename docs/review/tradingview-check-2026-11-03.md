# TradingView candle check 2026-11-03 (data and chart, not strategy)

Goal: our cached candles (FTMO MT5, bid prices) line up in time and shape with another chart.
Source: `python -m backtester.tools.show SYMBOL TF START END --tz ZONE`.

**TradingView setup:** chart time zone UTC (right-click the time axis > Time zone > UTC), or
read the New York / local column. Suggested feeds: OANDA (XAUUSD, NAS100USD, EURUSD, DE30EUR,
WTICOUSD). Other feeds differ by a few ticks; volume is not comparable. A real error looks like
a candle off by an hour, a different move, or a missing / extra candle.

| # | Symbol | TF | Open UTC | Local open | Why this one | Open | High | Low | Close | Same? |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | XAUUSD | M5 | 2026-10-28 13:30 | 09:30 New York | NY open, US still on summer time | 4051.32 | 4052.53 | 4047.24 | 4047.24 | |
| 2 | NAS100 | M5 | 2026-11-02 14:30 | 09:30 New York | first cash open after the US clock change (11-01) | 28582.13 | 28600.63 | 28536.43 | 28571.13 | |
| 3 | NAS100 | H1 | 2026-10-29 14:00 | 10:00 New York | H1 built from M1 (bar boundaries) | 29396.33 | 29476.93 | 29296.73 | 29373.83 | |
| 4 | EURUSD | M15 | 2026-10-27 08:00 | 08:00 London | London open, UK already on winter time, US not | 1.11606 | 1.11606 | 1.11547 | 1.11568 | |
| 5 | GER40 | M30 | 2026-10-30 08:00 | 09:00 Berlin | Frankfurt cash open | 25970.74 | 25993.24 | 25907.74 | 25964.74 | |
| 6 | XAUUSD | M5 | 2026-11-01 23:05 | 18:05 New York | first candle after the weekend (ours starts 23:05, not 23:00) | 3895.08 | 3901.08 | 3890.93 | 3894.70 | |
| 7 | EURUSD | M5 | 2026-10-29 21:05 | 17:05 New York | first candle after rollover (ours has none 17:00-17:05 NY) | 1.11747 | 1.11749 | 1.11732 | 1.11741 | |
| 8 | USOIL | M15 | 2026-10-30 14:30 | 10:30 New York | oil CFD; level may differ from spot / futures feeds, shape should match | 104.886 | 105.057 | 104.649 | 104.833 | |

Rows 6 and 7: also check whether TradingView shows a candle at 23:00 (row 6) or at 21:00 UTC
(row 7). Its feed may trade there while FTMO does not; that is a broker difference, not an error.
