# Calendar × clock screen — 2008–2014 discovery, 2015–2021 confirmation

Pre-registered by Opus on 2026-11-09. Analysis only; the period from 2021-09-14 onward remains unspent.

## Design

- Six pairs: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY and EURJPY. Discovery: 2008-01-01–2014-12-31, `data/cache/histdata_presample/` (clock checks in `results/presample_2008_2014/clock_check_*`). Confirmation: 2015-01-02–2021-09-13, default cache with MT5 preferred by day. Both use `load_m1`.
- Twelve two-hour UTC blocks, 00–02 through 22–24; signed return is 10,000 × log(end close / start close), using exact M1 closes. Missing or invalid endpoints are skipped. The date is the UTC start date. The 20–22 and 22–24 blocks are reported but ineligible for selection as pre-registered.
- Eleven overlapping classes: Monday through Friday; gotobi using `day_filter.py` Tokyo business-day rules; last and first weekday of month; Monday–Friday dates 14, 15 or 16; first weekday after a NYSE full closure; first weekday after a Japanese holiday. Post-holiday days must not themselves be holidays; consecutive holidays, including a weekend within a run, produce one subsequent business day. Weekends alone do not count. Japanese bank holidays include Dec 31 and Jan 2–3.
- Discovery: n ≥ 60, |t| ≥ 4.0 and |mean| ≥ 2 × cost, excluding the two ineligible blocks. Confirmation: same sign, |mean| ≥ 1.5 × cost, signed t ≥ 2.0 in the discovery direction, and the class mean minus the same block’s mean on all other days has that same sign. All other days include weekends where valid endpoints exist.
- t is the mean divided by its sample standard error (one observation per UTC day per cell). Costs are round-trip default spread + twice slippage + commission at the median valid M1 close of each pair and period, using `time_of_day_profile.cost_bp`. Returns and costs are in basis points; means are gross.

**Cells:** 792 (6 × 12 × 11). **Discovery survivors:** 0. **Confirmed:** 0.

## Discovery survivors and confirmation

| Pair | UTC | Class | Discovery n | Mean bp | t | Cost bp | Confirmation n | Mean bp | t | Cost bp | Other-day n | Other-day mean bp | Difference bp | Confirmed |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| None | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

## Confirmed cells

None.

## Top 20 discovery cells by |t|

| Rank | Pair | UTC | Class | n | Mean bp | t | Cost bp | Eligible block |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | USDJPY | 02-04 | Thursday | 310 | -3.749 | -3.387 | 1.310 | Yes |
| 2 | AUDUSD | 00-02 | last weekday of month | 80 | 8.743 | 3.168 | 1.266 | Yes |
| 3 | AUDUSD | 22-24 | Thursday | 302 | -3.994 | -3.102 | 1.266 | No |
| 4 | GBPUSD | 18-20 | Monday | 341 | 2.225 | 2.995 | 1.047 | Yes |
| 5 | NZDUSD | 00-02 | Wednesday | 302 | -4.378 | -2.959 | 1.677 | Yes |
| 6 | EURUSD | 02-04 | Friday | 330 | 2.105 | 2.957 | 0.717 | Yes |
| 7 | GBPUSD | 20-22 | Monday | 301 | -1.920 | -2.851 | 1.047 | No |
| 8 | NZDUSD | 00-02 | last weekday of month | 68 | 8.811 | 2.837 | 1.677 | Yes |
| 9 | AUDUSD | 14-16 | day after NYSE full closure | 62 | 11.616 | 2.828 | 1.266 | Yes |
| 10 | EURUSD | 10-12 | Wednesday | 359 | -2.868 | -2.763 | 0.717 | Yes |
| 11 | USDJPY | 10-12 | Wednesday | 342 | 2.880 | 2.699 | 1.310 | Yes |
| 12 | AUDUSD | 00-02 | Thursday | 338 | 5.783 | 2.669 | 1.266 | Yes |
| 13 | NZDUSD | 04-06 | Tuesday | 305 | 3.154 | 2.667 | 1.677 | Yes |
| 14 | EURUSD | 18-20 | first weekday of month | 76 | -5.202 | -2.658 | 0.717 | Yes |
| 15 | GBPUSD | 02-04 | Friday | 309 | 1.744 | 2.631 | 1.047 | Yes |
| 16 | NZDUSD | 14-16 | first weekday of month | 75 | 11.612 | 2.574 | 1.677 | Yes |
| 17 | EURJPY | 16-18 | Thursday | 361 | 4.107 | 2.532 | 1.741 | Yes |
| 18 | EURUSD | 00-02 | Friday | 338 | -1.861 | -2.502 | 0.717 | Yes |
| 19 | GBPUSD | 12-14 | 15th +/-1 weekday | 180 | 4.361 | 2.495 | 1.047 | Yes |
| 20 | EURUSD | 16-18 | Wednesday | 360 | 2.498 | 2.482 | 0.717 | Yes |

## Data coverage

Valid M1 closes are used for the median cost; block observations count all UTC dates with both exact endpoints. The range boundary does not load candles outside its dates, so unavailable midnight endpoints are skipped.

| Pair | Stage | Valid closes | Block observations |
|---|---|---:|---:|
| EURUSD | discovery | 2,523,173 | 20,430 |
| GBPUSD | discovery | 2,495,805 | 19,985 |
| AUDUSD | discovery | 2,494,988 | 20,093 |
| NZDUSD | discovery | 2,356,178 | 18,388 |
| USDJPY | discovery | 2,424,039 | 19,413 |
| EURJPY | discovery | 2,577,633 | 21,062 |

Confirmation data were loaded only for pairs with discovery survivors. Opus decides whether any confirmed cell becomes a hypothesis.
