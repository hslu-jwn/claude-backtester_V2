# Gotobi pre-sample check, 2008-2014

2026-11-09. **G1 primary does not pass:** the four numerical criteria pass, but required gate 7 fails with rollover tolerance. Park the result for the user next to the one-time test; it does not cancel that test by itself. EURJPY is descriptive, not a gate.

The unchanged `research/grids/timed_hold_gotobi.toml` ran with `--dev-only --cache-dir data/cache/histdata_presample --results-dir results/presample_2008_2014 --workers 1`. Actual full-day coverage 2008-01-02 through 2014-12-31. Gates: `python -m backtester.tools.timed_hold_gates results/presample_2008_2014/research/timed_hold_gotobi_d9ea62c1 --primary-symbol USDJPY --min-trades 200 --min-breadth 1`. No test-period candles used. The clock check is `results/presample_2008_2014/clock_check_new_pairs.md`; no year excluded. Historical costs use nearest measured spreads and are optimistic.

## G1 gotobi, stop 1.0

| Symbol | Trades | Net R | Doubled R | Mean R | 2008-2011 / 2012-2014 | Bootstrap 2.5% | Gate 3 diff / 2.5% | Gate 7 tolerant / strict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| USDJPY | 415 | +30.889 | +24.603 | +0.0744 | +12.848 / +18.041 | +0.0432 | +0.0748 / +0.0392 | 36 / 102 |
| EURJPY | 435 | +12.368 | +5.453 | +0.0284 | +0.079 / +12.289 | +0.0002 | +0.0340 / +0.0021 | 7 / 19 |
| Pooled | 850 | +43.257 | +30.056 | +0.0509 | +12.927 / +30.330 | +0.0248 | +0.0539 / +0.0247 | 43 / 121 |

Gate 3 compares the gotobi sample to the disjoint all-days control (1,295 USDJPY and 1,359 EURJPY trades), excluding each symbol's gotobi entry dates. Bootstrap uses ordered trades, circular blocks of five, 10,000 resamples, seed 2026110; the difference resamples each series independently. Gate 7 counts failing trades, not gaps; the tolerant result applies the registered rollover exception, while strict uses the five-minute rule. Details and examples are in `gates.json`. The gate tool's midpoint halves differ from the calendar halves shown here.

| Year | USDJPY net R | EURJPY net R |
|---|---:|---:|
| 2008 | +0.038 | -3.885 |
| 2009 | -0.994 | -0.752 |
| 2010 | +6.011 | -0.618 |
| 2011 | +7.793 | +5.334 |
| 2012 | +6.204 | +4.601 |
| 2013 | +9.526 | +6.335 |
| 2014 | +2.310 | +1.354 |

1. **Pass:** USDJPY normal +30.889 R and doubled +24.603 R.
2. **Pass:** bootstrap lower 2.5% +0.0432 R/trade.
3. **Pass:** calendar halves +12.848 / +18.041 R.
4. **Pass:** gotobi minus disjoint control +0.0748 R/trade; bootstrap lower 2.5% +0.0392.
5. **Gate 7 fails:** 36 USDJPY trades still fail with rollover tolerance (102 strict). The gate tool therefore rejects G1, despite passing its other six gates.

## G2 gotobi, stop 1.0 (descriptive)

| Symbol | Trades | Net R | Doubled R | Mean R | 2008-2011 / 2012-2014 | Bootstrap 2.5% | Gate 3 diff / 2.5% | Gate 7 tolerant / strict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| USDJPY | 491 | +13.131 | +5.717 | +0.0267 | +10.240 / +2.891 | +0.0087 | +0.0157 / -0.0051 | 27 / 27 |
| EURJPY | 492 | -0.041 | -7.821 | -0.0001 | +1.866 / -1.907 | -0.0180 | +0.0108 / -0.0097 | 2 / 2 |

USDJPY yearly net R 2008-2014: +2.876, +2.942, +1.403, +3.019, +0.397, +1.813, +0.682. EURJPY: +0.954, +1.623, +0.007, -0.718, -2.377, +0.438, +0.032. G2 fails the tool's effect, breadth, and integrity gates; it remains falsified in the development report.
