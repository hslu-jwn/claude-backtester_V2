# Index calendar × clock screen — 2010–2014 discovery, 2015–2021 confirmation

Pre-registered by Opus on 2026-11-09. Analysis only; data after 2021-09-13 were not loaded.

## Design

- Five indices (US500, NAS100, GER40, UK100, JP225), 12 two-hour UTC blocks and 11 overlapping classes: **660 cells**. Discovery uses the already-imported histdata pre-sample, 2010-11-01 through 2014-12-31; confirmation uses the default cache, MT5 preferred by day, 2015-01-02 through 2021-09-13. Both use `load_m1`.
- Return = 10,000 × log(end / start), using exact M1 closing timestamps; missing, non-positive or non-finite endpoints are skipped. The UTC block-start date assigns the class. The 20–22 and 22–24 blocks are reported but ineligible. Blocks with fewer than 60% of all discovery weekdays having both valid endpoints are also ineligible. The discovery denominator is all weekdays in the full 2010-11-01–2014-12-31 window, including holidays and missing data.
- Classes: Monday–Friday; gotobi via `day_filter.py`; last and first weekday of the month; weekdays dated 14–16; first weekday after a NYSE full closure or a Japanese holiday, with consecutive holidays and intervening weekends treated as one run. Japanese bank holidays include Dec 31 and Jan 2–3. Weekend dates do not belong to a class.
- Discovery: n ≥ 60, |t| ≥ 4, |mean| ≥ 2 × cost, eligible block. Confirmation, survivors only: same sign, |mean| ≥ 1.5 × cost, t ≥ 2 in the discovery direction, and class mean minus the mean on all other dates (including weekends with valid endpoints) has the same sign. t uses sample standard error, one return per UTC day. Costs are spread + twice slippage + round-trip commission at the median valid M1 close in the respective symbol and period, using `time_of_day_profile.cost_bp`; means are gross.

**Cells:** 660. **Discovery survivors:** 0. **Confirmed:** 0. No confirmation data were loaded because there were no discovery survivors.

Discovery cost (bp): US500 1.442, NAS100 1.318, GER40 1.498, UK100 3.778, JP225 3.178.

## Clock check

For each weekday, find the largest absolute M1 open-to-close log move in the 60-minute window centered on the local cash open: New York 09:30 (US500/NAS100), Frankfurt 09:00 (GER40), London 08:00 (UK100), Tokyo 09:00 (JP225). The table shows how often its candle **opens** at minute 0, 1 or 2 relative to that open, out of days with at least one candle in the window. Offsets use the named local timezone and its historical DST. Tokyo also has a recurring peak at −15 minutes, consistent with its earlier futures open. The 2010 rows are partial, beginning in November.

| Index | 2010 | 2011 | 2012 | 2013 | 2014 |
|---|---:|---:|---:|---:|---:|
| US500 | 7/34 | 30/258 | 49/259 | 54/258 | 35/257 |
| NAS100 | 6/34 | 49/258 | 65/259 | 70/258 | 38/257 |
| GER40 | 3/33 | 44/257 | 48/254 | 56/253 | 47/251 |
| UK100 | 9/33 | 95/251 | 158/252 | 123/252 | 127/251 |
| JP225 | 3/33 | 34/256 | 56/257 | 49/255 | 62/255 |

For US500/NAS100, additionally find the largest absolute M1 open-to-close move within ±90 minutes of 08:30 New York on each first Friday, corresponding to 12:30/13:30 UTC depending on US DST (not 13:30/14:30); the table counts candle **close** offsets 0 to +3 minutes. First-Friday NFP dates shifted for holidays are not corrected. A larger cash-open or unrelated move can dominate the window. Only one first Friday has data in 2010.

| Index | 2010 | 2011 | 2012 | 2013 | 2014 |
|---|---:|---:|---:|---:|---:|
| US500 | 1/1 | 7/12 | 7/12 | 7/12 | 8/12 |
| NAS100 | 1/1 | 2/12 | 4/12 | 2/12 | 7/12 |

Cash-open clustering and the available US release spikes support the imported clock for every index-year; **excluded years: none**. These are statistical checks, not proof of every timestamp; the 2010 checks, particularly the single US release, are less conclusive. A ±30-minute cash-open window cannot itself rule out all possible one-hour shifts; the US release check supplies a wider window.

The histdata importer uses the US DST clock rule through 2018. Its GER40 rule discards GRXEUR from 2020-06-15 after an instrument switch; it does not affect discovery, but limits the histdata component of confirmation from that date.

## Discovery block coverage

Valid endpoint pairs / all discovery weekdays; percentage in parentheses. Asterisks mark blocks below 60%; the last two blocks are ineligible regardless of coverage.

| Index | 00-02 | 02-04 | 04-06 | 06-08 | 08-10 | 10-12 | 12-14 | 14-16 | 16-18 | 18-20 | 20-22 | 22-24 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| US500 | 371/1088 (34.1%) * | 274/1088 (25.2%) * | 311/1088 (28.6%) * | 563/1088 (51.7%) * | 665/1088 (61.1%) | 632/1088 (58.1%) * | 761/1088 (69.9%) | 904/1088 (83.1%) | 865/1088 (79.5%) | 874/1088 (80.3%) | 144/1088 (13.2%) * | 87/1088 (8.0%) * |
| NAS100 | 818/1088 (75.2%) | 754/1088 (69.3%) | 780/1088 (71.7%) | 928/1088 (85.3%) | 988/1088 (90.8%) | 982/1088 (90.3%) | 1012/1088 (93.0%) | 1037/1088 (95.3%) | 1033/1088 (94.9%) | 1021/1088 (93.8%) | 282/1088 (25.9%) * | 213/1088 (19.6%) * |
| GER40 | 0/1088 (0.0%) * | 0/1088 (0.0%) * | 0/1088 (0.0%) * | 0/1088 (0.0%) * | 1045/1088 (96.0%) | 1045/1088 (96.0%) | 1038/1088 (95.4%) | 1041/1088 (95.7%) | 1033/1088 (94.9%) | 1021/1088 (93.8%) | 0/1088 (0.0%) * | 0/1088 (0.0%) * |
| UK100 | 0/1088 (0.0%) * | 0/1088 (0.0%) * | 0/1088 (0.0%) * | 0/1088 (0.0%) * | 583/1088 (53.6%) * | 1030/1088 (94.7%) | 1022/1088 (93.9%) | 1019/1088 (93.7%) | 996/1088 (91.5%) | 982/1088 (90.3%) | 0/1088 (0.0%) * | 0/1088 (0.0%) * |
| JP225 | 739/1088 (67.9%) | 573/1088 (52.7%) * | 676/1088 (62.1%) | 579/1088 (53.2%) * | 378/1088 (34.7%) * | 318/1088 (29.2%) * | 392/1088 (36.0%) * | 505/1088 (46.4%) * | 471/1088 (43.3%) * | 515/1088 (47.3%) * | 101/1088 (9.3%) * | 124/1088 (11.4%) * |

## Discovery survivors and confirmation

| Index | UTC | Class | Discovery n | Mean bp | t | Cost bp | Confirmation n | Mean bp | t | Cost bp | Other n | Other mean bp | Difference bp | Confirmed |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| None | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

## Confirmed cells

None.

## Top 20 discovery cells by |t|

| Rank | Index | UTC | Class | n | Mean bp | t | Cost bp | Eligible block |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | JP225 | 22-24 | after Japanese holiday | 9 | -19.257 | -4.080 | 3.178 | No |
| 2 | UK100 | 08-10 | Thursday | 121 | -13.806 | -3.513 | 3.778 | No |
| 3 | JP225 | 08-10 | after NYSE closure | 8 | -36.069 | -3.278 | 3.178 | No |
| 4 | NAS100 | 18-20 | after NYSE closure | 33 | 15.219 | 2.948 | 1.318 | Yes |
| 5 | UK100 | 14-16 | Tuesday | 207 | 8.645 | 2.702 | 3.778 | Yes |
| 6 | UK100 | 18-20 | after NYSE closure | 26 | 11.055 | 2.681 | 3.778 | Yes |
| 7 | JP225 | 00-02 | gotobi | 212 | -9.646 | -2.675 | 3.178 | Yes |
| 8 | NAS100 | 14-16 | Tuesday | 210 | 9.206 | 2.594 | 1.318 | Yes |
| 9 | US500 | 02-04 | gotobi | 69 | -8.512 | -2.582 | 1.442 | No |
| 10 | US500 | 14-16 | Tuesday | 183 | 8.266 | 2.563 | 1.442 | Yes |
| 11 | US500 | 18-20 | after NYSE closure | 22 | 14.225 | 2.518 | 1.442 | Yes |
| 12 | JP225 | 00-02 | Monday | 146 | -11.348 | -2.396 | 3.178 | Yes |
| 13 | JP225 | 22-24 | first weekday | 5 | 18.402 | 2.306 | 3.178 | No |
| 14 | NAS100 | 20-22 | after Japanese holiday | 15 | -9.591 | -2.266 | 1.318 | No |
| 15 | NAS100 | 14-16 | last weekday | 47 | 13.602 | 2.249 | 1.318 | Yes |
| 16 | NAS100 | 22-24 | first weekday | 7 | 7.005 | 2.247 | 1.318 | No |
| 17 | GER40 | 12-14 | gotobi | 285 | -8.106 | -2.212 | 1.498 | Yes |
| 18 | JP225 | 00-02 | after NYSE closure | 20 | 29.794 | 2.205 | 3.178 | Yes |
| 19 | GER40 | 16-18 | Thursday | 208 | 5.167 | 2.169 | 1.498 | Yes |
| 20 | NAS100 | 18-20 | gotobi | 281 | -5.249 | -2.138 | 1.318 | Yes |
