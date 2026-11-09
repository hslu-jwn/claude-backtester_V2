# FX fixing W-pattern development screen — 2026-11-09

## Method

Development data only: 2015-01-02 through 2021-09-13 inclusive, weekdays by the local date of each window. The existing `load_m1` loader uses the default sources (MT5 preferred by UTC day, histdata otherwise). The 120-minute return is 10,000 × log(end close / start close), multiplied by -1 for EURUSD, GBPUSD, AUDUSD and NZDUSD, and +1 for USDJPY, USDCAD and USDCHF, so positive means USD appreciation. Candle timestamps are opens; prices are exact M1 closes at each endpoint; a window is omitted if either endpoint is missing or invalid. No interpolation is used.

Tokyo uses Asia/Tokyo, ECB uses Europe/Berlin (CET/CEST), and London uses Europe/London (GMT/BST); daylight saving follows the named local zone. Month-end means the last Monday–Friday of each calendar month, without a holiday calendar. The all-weekday group includes those month-end dates. Windows are 07:55–09:55 and 09:55–11:55 Tokyo; 12:15–14:15 and 14:15–16:15 ECB; 14:00–16:00 and 16:00–18:00 London.

One return per local day and window: t = mean / (sample standard deviation / sqrt(n)), equivalent to clustering at the day level for this single-observation-per-day mean, without serial-correlation adjustment. Cost is the profiler’s `cost_bp`: default fixed spread + twice slippage + round-trip commission at the median positive M1 close for the loaded period, in bp. Candidate requires |mean| > 1.5 × cost and |t| ≥ 3, evaluated on unrounded values; otherwise screened out. This two-sided screen is descriptive and does not establish a tradable strategy, account for multiple testing, or authorize the held-out test.

| Group | Window | Symbol | n | Mean USD bp | t | Cost bp | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| All weekdays | Tokyo pre | EURUSD | 1717 | 0.058 | 0.26 | 0.789 | Screened out |
| Month-end | Tokyo pre | EURUSD | 80 | 0.674 | 0.53 | 0.789 | Screened out |
| All weekdays | Tokyo post | EURUSD | 1730 | -0.984 | -3.44 | 0.789 | Screened out |
| Month-end | Tokyo post | EURUSD | 80 | -1.562 | -1.33 | 0.789 | Screened out |
| All weekdays | ECB pre | EURUSD | 1731 | 1.234 | 3.39 | 0.789 | Candidate |
| Month-end | ECB pre | EURUSD | 78 | 0.885 | 0.49 | 0.789 | Screened out |
| All weekdays | ECB post | EURUSD | 1730 | -0.759 | -1.25 | 0.789 | Screened out |
| Month-end | ECB post | EURUSD | 78 | -0.809 | -0.29 | 0.789 | Screened out |
| All weekdays | London pre | EURUSD | 1730 | 0.399 | 0.74 | 0.789 | Screened out |
| Month-end | London pre | EURUSD | 78 | -0.335 | -0.12 | 0.789 | Screened out |
| All weekdays | London post | EURUSD | 1731 | -0.715 | -2.06 | 0.789 | Screened out |
| Month-end | London post | EURUSD | 78 | 5.479 | 3.15 | 0.789 | Candidate |
| All weekdays | Tokyo pre | GBPUSD | 1709 | -0.091 | -0.30 | 1.114 | Screened out |
| Month-end | Tokyo pre | GBPUSD | 80 | 0.041 | 0.02 | 1.114 | Screened out |
| All weekdays | Tokyo post | GBPUSD | 1732 | -0.401 | -0.90 | 1.114 | Screened out |
| Month-end | Tokyo post | GBPUSD | 80 | -2.152 | -1.51 | 1.114 | Screened out |
| All weekdays | ECB pre | GBPUSD | 1731 | 0.586 | 1.18 | 1.114 | Screened out |
| Month-end | ECB pre | GBPUSD | 78 | -3.979 | -2.10 | 1.114 | Screened out |
| All weekdays | ECB post | GBPUSD | 1731 | 0.086 | 0.15 | 1.114 | Screened out |
| Month-end | ECB post | GBPUSD | 78 | -1.370 | -0.52 | 1.114 | Screened out |
| All weekdays | London pre | GBPUSD | 1732 | -0.047 | -0.08 | 1.114 | Screened out |
| Month-end | London pre | GBPUSD | 78 | -7.367 | -2.08 | 1.114 | Screened out |
| All weekdays | London post | GBPUSD | 1731 | -0.417 | -1.00 | 1.114 | Screened out |
| Month-end | London post | GBPUSD | 78 | 7.881 | 3.57 | 1.114 | Candidate |
| All weekdays | Tokyo pre | USDJPY | 1720 | 0.624 | 1.81 | 1.181 | Screened out |
| Month-end | Tokyo pre | USDJPY | 79 | -1.411 | -0.78 | 1.181 | Screened out |
| All weekdays | Tokyo post | USDJPY | 1730 | -2.160 | -4.76 | 1.181 | Candidate |
| Month-end | Tokyo post | USDJPY | 79 | -4.351 | -3.31 | 1.181 | Candidate |
| All weekdays | ECB pre | USDJPY | 1731 | 0.466 | 1.53 | 1.181 | Screened out |
| Month-end | ECB pre | USDJPY | 78 | 1.863 | 1.58 | 1.181 | Screened out |
| All weekdays | ECB post | USDJPY | 1730 | -0.215 | -0.41 | 1.181 | Screened out |
| Month-end | ECB post | USDJPY | 78 | -1.804 | -0.69 | 1.181 | Screened out |
| All weekdays | London pre | USDJPY | 1732 | -0.771 | -1.58 | 1.181 | Screened out |
| Month-end | London pre | USDJPY | 78 | -0.945 | -0.35 | 1.181 | Screened out |
| All weekdays | London post | USDJPY | 1731 | 0.253 | 0.72 | 1.181 | Screened out |
| Month-end | London post | USDJPY | 78 | 2.541 | 1.54 | 1.181 | Screened out |
| All weekdays | Tokyo pre | AUDUSD | 1721 | -0.122 | -0.28 | 1.407 | Screened out |
| Month-end | Tokyo pre | AUDUSD | 80 | -1.092 | -0.44 | 1.407 | Screened out |
| All weekdays | Tokyo post | AUDUSD | 1731 | -0.834 | -1.46 | 1.407 | Screened out |
| Month-end | Tokyo post | AUDUSD | 80 | -3.617 | -1.24 | 1.407 | Screened out |
| All weekdays | ECB pre | AUDUSD | 1731 | 0.202 | 0.49 | 1.407 | Screened out |
| Month-end | ECB pre | AUDUSD | 78 | 0.301 | 0.18 | 1.407 | Screened out |
| All weekdays | ECB post | AUDUSD | 1731 | 0.514 | 0.84 | 1.407 | Screened out |
| Month-end | ECB post | AUDUSD | 78 | -1.479 | -0.48 | 1.407 | Screened out |
| All weekdays | London pre | AUDUSD | 1732 | 0.381 | 0.61 | 1.407 | Screened out |
| Month-end | London pre | AUDUSD | 78 | -3.402 | -1.04 | 1.407 | Screened out |
| All weekdays | London post | AUDUSD | 1732 | -0.175 | -0.41 | 1.407 | Screened out |
| Month-end | London post | AUDUSD | 78 | 8.109 | 3.42 | 1.407 | Candidate |
| All weekdays | Tokyo pre | NZDUSD | 1720 | 0.324 | 0.75 | 1.768 | Screened out |
| Month-end | Tokyo pre | NZDUSD | 79 | 1.488 | 0.63 | 1.768 | Screened out |
| All weekdays | Tokyo post | NZDUSD | 1729 | -1.076 | -1.95 | 1.768 | Screened out |
| Month-end | Tokyo post | NZDUSD | 79 | 1.072 | 0.41 | 1.768 | Screened out |
| All weekdays | ECB pre | NZDUSD | 1731 | 0.096 | 0.23 | 1.768 | Screened out |
| Month-end | ECB pre | NZDUSD | 78 | -1.585 | -0.82 | 1.768 | Screened out |
| All weekdays | ECB post | NZDUSD | 1730 | -0.172 | -0.26 | 1.768 | Screened out |
| Month-end | ECB post | NZDUSD | 78 | -2.723 | -0.90 | 1.768 | Screened out |
| All weekdays | London pre | NZDUSD | 1732 | -0.086 | -0.13 | 1.768 | Screened out |
| Month-end | London pre | NZDUSD | 78 | -4.372 | -1.33 | 1.768 | Screened out |
| All weekdays | London post | NZDUSD | 1732 | -0.052 | -0.12 | 1.768 | Screened out |
| Month-end | London post | NZDUSD | 78 | 8.023 | 3.63 | 1.768 | Candidate |
| All weekdays | Tokyo pre | USDCAD | 1709 | 0.905 | 4.32 | 1.123 | Screened out |
| Month-end | Tokyo pre | USDCAD | 79 | 1.490 | 1.37 | 1.123 | Screened out |
| All weekdays | Tokyo post | USDCAD | 1728 | -0.742 | -2.83 | 1.123 | Screened out |
| Month-end | Tokyo post | USDCAD | 80 | -0.537 | -0.52 | 1.123 | Screened out |
| All weekdays | ECB pre | USDCAD | 1731 | 0.445 | 1.30 | 1.123 | Screened out |
| Month-end | ECB pre | USDCAD | 78 | 0.069 | 0.04 | 1.123 | Screened out |
| All weekdays | ECB post | USDCAD | 1731 | 0.871 | 1.42 | 1.123 | Screened out |
| Month-end | ECB post | USDCAD | 78 | -0.899 | -0.26 | 1.123 | Screened out |
| All weekdays | London pre | USDCAD | 1732 | 0.102 | 0.17 | 1.123 | Screened out |
| Month-end | London pre | USDCAD | 78 | -0.265 | -0.08 | 1.123 | Screened out |
| All weekdays | London post | USDCAD | 1732 | -0.343 | -0.85 | 1.123 | Screened out |
| Month-end | London post | USDCAD | 78 | 1.799 | 0.78 | 1.123 | Screened out |
| All weekdays | Tokyo pre | USDCHF | 1688 | 1.018 | 4.95 | 1.646 | Screened out |
| Month-end | Tokyo pre | USDCHF | 78 | -0.542 | -0.49 | 1.646 | Screened out |
| All weekdays | Tokyo post | USDCHF | 1726 | -0.242 | -0.94 | 1.646 | Screened out |
| Month-end | Tokyo post | USDCHF | 79 | 0.013 | 0.01 | 1.646 | Screened out |
| All weekdays | ECB pre | USDCHF | 1731 | 0.910 | 2.46 | 1.646 | Screened out |
| Month-end | ECB pre | USDCHF | 78 | 2.572 | 1.41 | 1.646 | Screened out |
| All weekdays | ECB post | USDCHF | 1731 | -1.017 | -1.80 | 1.646 | Screened out |
| Month-end | ECB post | USDCHF | 78 | -2.675 | -1.08 | 1.646 | Screened out |
| All weekdays | London pre | USDCHF | 1732 | -0.426 | -0.72 | 1.646 | Screened out |
| Month-end | London pre | USDCHF | 78 | -6.190 | -1.92 | 1.646 | Screened out |
| All weekdays | London post | USDCHF | 1732 | -0.006 | -0.02 | 1.646 | Screened out |
| Month-end | London post | USDCHF | 78 | 7.197 | 3.49 | 1.646 | Candidate |

## Conclusion

- 8 of 84 group/window/symbol cells pass the prespecified two-sided screen.
- Passing cells: All weekdays, ECB pre, EURUSD (+1.234 bp, t +3.39); Month-end, London post, EURUSD (+5.479 bp, t +3.15); Month-end, London post, GBPUSD (+7.881 bp, t +3.57); All weekdays, Tokyo post, USDJPY (-2.160 bp, t -4.76); Month-end, Tokyo post, USDJPY (-4.351 bp, t -3.31); Month-end, London post, AUDUSD (+8.109 bp, t +3.42); Month-end, London post, NZDUSD (+8.023 bp, t +3.63); Month-end, London post, USDCHF (+7.197 bp, t +3.49).
- These are gross mean returns against modeled costs, not realized backtest results; overlapping groups and windows create multiple-comparison risk.
- Opus decides whether any passing cell merits a pre-registered hypothesis. Previously rejected London reversal and all-days Tokyo/Gotobi variants are not re-proposed.
