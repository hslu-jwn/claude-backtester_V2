# Gotobi G1 development diagnostics — 2026-11-09

Exploratory diagnostics only; no gates or selection criteria are changed. Original G1: 03:00–09:55 Asia/Tokyo, long, stop 1 ATR. Development period 2015-01-02 through 2021-09-13. Net R includes recorded costs and swap. Win rate counts net R > 0. Dates, weekdays and years use Tokyo entry date; quarter-end means entry month Mar, Jun, Sep or Dec. Target dates are rolled back using the strategy’s Japanese business calendar. If two targets map to one entry date, the trade appears in both target buckets; all other splits partition trades. An entry date matching one target on-date and another rolled back is classified as on-date in the rollback split. 2021 ends on September 13.

Source: `results/research/timed_hold_gotobi_d9ea62c1/variants/` (G1 gotobi v0000; all v0002).

## USDJPY

Trades: 413; dates with multiple target assignments: 2.

### Target date

| Bucket | Trades | Net R | Mean net R | Win rate |
|---|---:|---:|---:|---:|
| 5 | 67 | -0.298 | -0.0045 | 58.2% |
| 10 | 72 | +3.116 | +0.0433 | 59.7% |
| 15 | 69 | +7.491 | +0.1086 | 69.6% |
| 20 | 70 | +4.540 | +0.0649 | 78.6% |
| 25 | 67 | +3.885 | +0.0580 | 70.1% |
| month-end | 70 | -1.910 | -0.0273 | 47.1% |

### Rollback

| Bucket | Trades | Net R | Mean net R | Win rate |
|---|---:|---:|---:|---:|
| on-date | 263 | +15.557 | +0.0592 | 66.2% |
| rolled-back | 150 | +0.988 | +0.0066 | 59.3% |

### Weekday

| Bucket | Trades | Net R | Mean net R | Win rate |
|---|---:|---:|---:|---:|
| Tuesday | 66 | +5.671 | +0.0859 | 65.2% |
| Wednesday | 72 | +1.712 | +0.0238 | 65.3% |
| Thursday | 70 | +2.519 | +0.0360 | 61.4% |
| Friday | 205 | +6.644 | +0.0324 | 63.4% |

### Quarter-end month

| Bucket | Trades | Net R | Mean net R | Win rate |
|---|---:|---:|---:|---:|
| Mar/Jun/Sep/Dec | 140 | +8.824 | +0.0630 | 66.4% |
| other months | 273 | +7.721 | +0.0283 | 62.3% |

### Year

| Bucket | Trades | Net R | Mean net R | Win rate |
|---|---:|---:|---:|---:|
| 2015 | 60 | +1.008 | +0.0168 | 55.0% |
| 2016 | 61 | +4.094 | +0.0671 | 68.9% |
| 2017 | 63 | +4.248 | +0.0674 | 69.8% |
| 2018 | 63 | +4.920 | +0.0781 | 66.7% |
| 2019 | 62 | -2.561 | -0.0413 | 54.8% |
| 2020 | 62 | +1.571 | +0.0253 | 58.1% |
| 2021 | 42 | +3.265 | +0.0777 | 76.2% |

## EURJPY

Trades: 413; dates with multiple target assignments: 2.

### Target date

| Bucket | Trades | Net R | Mean net R | Win rate |
|---|---:|---:|---:|---:|
| 5 | 67 | -0.368 | -0.0055 | 52.2% |
| 10 | 72 | +2.159 | +0.0300 | 58.3% |
| 15 | 69 | +5.658 | +0.0820 | 72.5% |
| 20 | 70 | +7.007 | +0.1001 | 80.0% |
| 25 | 67 | +2.520 | +0.0376 | 65.7% |
| month-end | 70 | -1.470 | -0.0210 | 55.7% |

### Rollback

| Bucket | Trades | Net R | Mean net R | Win rate |
|---|---:|---:|---:|---:|
| on-date | 263 | +14.455 | +0.0550 | 67.3% |
| rolled-back | 150 | +0.971 | +0.0065 | 58.0% |

### Weekday

| Bucket | Trades | Net R | Mean net R | Win rate |
|---|---:|---:|---:|---:|
| Tuesday | 66 | +3.585 | +0.0543 | 66.7% |
| Wednesday | 72 | +3.160 | +0.0439 | 68.1% |
| Thursday | 70 | +4.463 | +0.0638 | 65.7% |
| Friday | 205 | +4.219 | +0.0206 | 61.0% |

### Quarter-end month

| Bucket | Trades | Net R | Mean net R | Win rate |
|---|---:|---:|---:|---:|
| Mar/Jun/Sep/Dec | 140 | +5.962 | +0.0426 | 65.0% |
| other months | 273 | +9.464 | +0.0347 | 63.4% |

### Year

| Bucket | Trades | Net R | Mean net R | Win rate |
|---|---:|---:|---:|---:|
| 2015 | 60 | +1.138 | +0.0190 | 55.0% |
| 2016 | 61 | +2.381 | +0.0390 | 63.9% |
| 2017 | 63 | +5.047 | +0.0801 | 65.1% |
| 2018 | 63 | +1.914 | +0.0304 | 65.1% |
| 2019 | 62 | +0.900 | +0.0145 | 66.1% |
| 2020 | 62 | +2.296 | +0.0370 | 71.0% |
| 2021 | 42 | +1.751 | +0.0417 | 59.5% |

## Gross price movement, USDJPY

Gross bp = 10,000 × (exit price - entry price) / entry price, before spread, commissions, swap and conversion. Both sets include stopped trades; all-days includes gotobi days.

| Filter | Trades | Mean gross bp/trade |
|---|---:|---:|
| gotobi | 413 | +4.315 |
| all | 1718 | -0.215 |

## Entry / exit sensitivity, USDJPY

Development only; times are Asia/Tokyo. Each cell uses stop 1.0 and the frozen G1 base settings. Total difference is gotobi net R minus all-days net R; mean difference is gotobi mean net R minus all-days mean net R. The all-days baseline includes gotobi trades, so it is not the disjoint comparison used by gate 3. Counts vary with the entry and exit times. These exploratory cells do not retune the candidate.

| Entry | Exit | Gotobi trades | Gotobi net R | All trades | All net R | Total difference R | Mean difference R/trade |
|---|---|---:|---:|---:|---:|---:|---:|
| 01:00 | 09:30 | 414 | -1.106 | 1718 | -53.302 | +52.196 | +0.0284 |
| 01:00 | 09:55 | 414 | +9.929 | 1718 | -37.474 | +47.403 | +0.0458 |
| 01:00 | 10:30 | 414 | +0.997 | 1718 | -52.724 | +53.720 | +0.0331 |
| 02:00 | 09:30 | 414 | +0.002 | 1718 | -57.038 | +57.040 | +0.0332 |
| 02:00 | 09:55 | 414 | +11.335 | 1718 | -41.053 | +52.388 | +0.0513 |
| 02:00 | 10:30 | 414 | +2.047 | 1718 | -57.038 | +59.085 | +0.0381 |
| 04:00 | 09:30 | 413 | +0.200 | 1716 | -51.731 | +51.931 | +0.0306 |
| 04:00 | 09:55 | 413 | +11.595 | 1716 | -35.926 | +47.521 | +0.0490 |
| 04:00 | 10:30 | 413 | +2.491 | 1716 | -52.786 | +55.278 | +0.0368 |
| 06:00 | 09:30 | 331 | -4.206 | 1335 | -37.478 | +33.272 | +0.0154 |
| 06:00 | 09:55 | 331 | +5.298 | 1335 | -23.889 | +29.188 | +0.0339 |
| 06:00 | 10:30 | 331 | -0.073 | 1335 | -35.207 | +35.134 | +0.0262 |
| 08:00 | 09:30 | 471 | -3.978 | 1718 | -33.112 | +29.135 | +0.0108 |
| 08:00 | 09:55 | 471 | +7.329 | 1718 | -17.988 | +25.317 | +0.0260 |
| 08:00 | 10:30 | 471 | -3.679 | 1718 | -38.018 | +34.339 | +0.0143 |

Scratch grid: `results/gotobi_diagnostics_grid.toml`; isolated runner output: `results/gotobi_diagnostics_scratch/research/gotobi_diagnostics_grid_b8494c7d/`. Command used `--dev-only --results-dir results/gotobi_diagnostics_scratch --workers 1`.

## Interpretation

USDJPY gains are spread across four of six target-date buckets, all observed weekdays, both quarter groupings and six of seven years; EURJPY shows the same target-date pattern and seven positive years.  
Both pairs lose on the 5th and month-end buckets, and rolled-back dates contribute little net R compared with on-date entries.  
Of the 15 exploratory timing cells, 10 have positive gotobi net R; these are descriptive development results, not a timing selection rule.  
The yen pairs are related and the 2018-2020 paper sample overlaps development; the one-time test criteria remain unchanged.
