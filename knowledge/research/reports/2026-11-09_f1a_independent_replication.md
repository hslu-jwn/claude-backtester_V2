# F1a independent replication (2026-11-09)

Development data only (2015-01-02..2021-09-13). Method: M1 loader only (`load_m1`, `DEFAULT_SOURCES`); no engine, no strategy code.
Price = close of the M1 candle whose close time is 07:00 / 13:00 Europe/London (DST-aware). Short gross pips = (P07 - P13) x 10,000, stop ignored. No day was skipped for a missing candle (13:00 always present). Script: scratchpad `replicate/rep.py`.

Verdict: the engine's F1a result is reproduced exactly in sign and size. Entry and exit prices equal the raw candle closes (0.00 pip difference); the engine's fill offsets (bid/spread) are applied separately and do not touch `entry`/`exit_price`. No sign of a time-zone, DST, or missing-candle error. Caveat: this only shows the engine computes the 07->13 move correctly; the edge itself is a mean of 3.3 pips/day gross, fading over time (2015 5.6 -> 2020 1.5), and the engine's net result is much smaller after costs.

### EURUSD short 07:00->13:00 London, gross pips, no stop (days with 13:00 lag>0: 0)

| year | days | sum pips | mean/day | t |
|---|---|---|---|---|
| 2015 | 258 | 1446 | 5.60 | 2.14 |
| 2016 | 259 | 956 | 3.69 | 1.77 |
| 2017 | 259 | 969 | 3.74 | 2.08 |
| 2018 | 259 | 888 | 3.43 | 1.76 |
| 2019 | 258 | 641 | 2.49 | 2.08 |
| 2020 | 259 | 394 | 1.52 | 0.71 |
| 2021 | 180 | 389 | 2.16 | 1.25 |
| total | 1732 | 5683 | 3.28 | 4.34 |

### GBPUSD short 07:00->13:00 London, gross pips, no stop (days with 13:00 lag>0: 0)

| year | days | sum pips | mean/day | t |
|---|---|---|---|---|
| 2015 | 258 | 1748 | 6.78 | 2.16 |
| 2016 | 259 | 375 | 1.45 | 0.41 |
| 2017 | 259 | 635 | 2.45 | 0.88 |
| 2018 | 259 | 744 | 2.87 | 0.93 |
| 2019 | 258 | -16 | -0.06 | -0.02 |
| 2020 | 259 | 423 | 1.63 | 0.50 |
| 2021 | 180 | -9 | -0.05 | -0.02 |
| total | 1732 | 3902 | 2.25 | 1.96 |

## Engine comparison, stop_atr=1.0 (v0001), 3445 trades

EURUSD: engine trades 1723, matched 1719, time-exit 1692, stops 27; entry within 0.5 pip 1719/1719 (median abs diff 0.00); exit within 0.5 pip 1692/1692 (median 0.00); corr(my pips, engine entry-exit pips) = 1.0000; engine mean pips 4.30 vs mine same days 4.30; mean signed (engine-mine) pips 0.000; entry hours UTC [np.int64(6), np.int64(7)], exit hours UTC [np.int64(12), np.int64(13)]
  r_gross sum 53.4, r_net sum 34.8
  my pips on stop-out days sum -1903; unmatched my days 13

GBPUSD: engine trades 1722, matched 1719, time-exit 1678, stops 41; entry within 0.5 pip 1719/1719 (median abs diff 0.00); exit within 0.5 pip 1678/1678 (median 0.00); corr(my pips, engine entry-exit pips) = 1.0000; engine mean pips 4.96 vs mine same days 4.96; mean signed (engine-mine) pips 0.000; entry hours UTC [np.int64(6), np.int64(7)], exit hours UTC [np.int64(12), np.int64(13)]
  r_gross sum 31.9, r_net sum -11.5
  my pips on stop-out days sum -4470; unmatched my days 13

### EURUSD mean pips per London hour h->h+1, 2015-2017

| h | n | mean pips | t |
|---|---|---|---|
| 00-01 | 774 | -0.38 | -1.38 |
| 01-02 | 774 | -0.01 | -0.03 |
| 02-03 | 776 | 0.64 | 1.91 |
| 03-04 | 776 | 0.62 | 1.47 |
| 04-05 | 775 | 0.12 | 0.54 |
| 05-06 | 775 | 0.32 | 1.51 |
| 06-07 | 777 | -0.38 | -1.19 |
| 07-08 | 776 | -0.13 | -0.25 |
| 08-09 | 777 | -0.39 | -0.56 |
| 09-10 | 777 | -0.70 | -1.32 |
| 10-11 | 777 | -0.22 | -0.49 |
| 11-12 | 777 | -1.21 | -2.58 |
| 12-13 | 776 | -1.71 | -3.50 |
| 13-14 | 777 | 0.98 | 1.09 |
| 14-15 | 775 | 0.30 | 0.42 |
| 15-16 | 775 | 0.05 | 0.06 |
| 16-17 | 776 | 1.07 | 2.08 |
| 17-18 | 775 | 0.25 | 0.54 |
| 18-19 | 774 | 0.82 | 1.52 |
| 19-20 | 775 | 0.75 | 1.54 |
| 20-21 | 774 | 0.06 | 0.15 |
| 21-22 | 749 | -0.98 | -3.75 |
| 22-23 | 570 | -0.20 | -0.76 |

### EURUSD mean pips per London hour h->h+1, 2018-2021

| h | n | mean pips | t |
|---|---|---|---|
| 00-01 | 955 | -0.04 | -0.20 |
| 01-02 | 955 | 0.37 | 1.42 |
| 02-03 | 958 | 0.36 | 1.62 |
| 03-04 | 958 | 0.29 | 1.54 |
| 04-05 | 958 | -0.19 | -1.14 |
| 05-06 | 959 | 0.05 | 0.27 |
| 06-07 | 959 | 0.10 | 0.42 |
| 07-08 | 959 | -1.17 | -3.33 |
| 08-09 | 957 | 1.07 | 2.47 |
| 09-10 | 956 | -0.97 | -2.50 |
| 10-11 | 954 | 0.08 | 0.24 |
| 11-12 | 955 | -0.79 | -2.53 |
| 12-13 | 956 | -0.64 | -1.66 |
| 13-14 | 956 | 0.78 | 1.67 |
| 14-15 | 956 | -0.20 | -0.42 |
| 15-16 | 956 | -0.97 | -1.89 |
| 16-17 | 956 | -0.02 | -0.05 |
| 17-18 | 955 | 0.43 | 1.41 |
| 18-19 | 956 | 0.23 | 0.76 |
| 19-20 | 953 | -0.06 | -0.18 |
| 20-21 | 949 | -0.12 | -0.51 |
| 21-22 | 800 | -0.86 | -4.59 |
| 22-23 | 431 | 1.25 | 5.30 |