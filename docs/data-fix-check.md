# Data fixes 13.12-13.18: the user's check (prepared 2026-11-12)

The fixes were built on 2026-10-26 (V2.6 step 2; `docs/archive/briefs/v26b-report.md`) and waited
for the user's check. Opus checked the **current cache** read-only with `scripts/data_fix_check.py`
(about 2 min; reruns give the same numbers) and the tests behind each fix (116 passed). Per item:
what was wrong, what the evidence says, and the proposed verdict.

| Item | Was wrong | Evidence now | Verdict |
|---|---|---|---|
| 13.12 histdata clock 2015-2018 | 3-4 US-only-DST weeks a year 1 h late | histdata vs MT5 minute returns line up at lag 0 in every US-only-DST week 2015-2018 (EURUSD, GBPUSD, XAUUSD, 6-9 days each) and in June | accept |
| 13.13 wrong instruments | GER40 histdata became Euro Stoxx on 2020-06-15; DXY was the Dow until 2018-12-14; EU50 became IBEX | histdata GER40 ends 2020-06-14, 2020-21 closes 7,973-13,827 (no ~3,100); DXY starts 2018-12-16; EU50 ends 2018-12-14 | accept |
| 13.14 MT5 cache before 2020 | server clock assumed NY+7 for all years; sparse / empty days cached as valid | 2010-2014: 0 days kept (no clock reference); 2015-2021 kept only on proven dates (EURUSD 304-311 a year); US30 2019 234 days (empty days gone); 60 ambiguous dates dropped for every symbol | accept, **but see the GBPUSD 2019 finding** |
| 13.15 1 January holes | first day of a year missing from year-by-year imports | 1 Jan present where markets traded (GBPUSD 2020: 118 bars, NAS100 2018: 59); 1 Jan 2021 is 0 bars in histdata and absent in MT5 (market closed; Sunday 3 Jan open present: EURUSD 115 bars in both) | accept |
| 13.16 MT5 downloader swallows errors | any first-chunk error counted as "before history"; wrong broker reported success | tests: first-chunk error is not "no history", errors after history starts are never swallowed, incomplete / reversed days rejected (`tests/data/test_v26b_data.py`) | accept |
| 13.18 output folders | grid `--part` runs overwrote each other; Monte Carlo folder lacked source / seed / runs; Windows file races | per-strategy grid tools replaced by the research runner; Monte Carlo folder is e.g. `gap_fade_NAS100-US500_..._histdata_seed42_runs1000` (test); PermissionError retries in `data/cache.py` and `filelock.py` (tests, incl. an 8-process race) | accept |

## New finding: MT5 GBPUSD is wrong on ~150 days, February-September 2019

- MT5 GBPUSD vs MT5's own GBPJPY / USDJPY cross: median 5-10 pips apart on those days (normal days
  0.1-0.4 pips); histdata GBPUSD matches the same cross within 1 pip. Day-end closes differ by 10-20
  pips; the best minute lag to histdata is 60-88 min instead of 0. Off days by month: 2019-02: 9,
  03: 15, 04: 22, 05: 23, 06: 20, 07: 23, 08: 22, 09: 15; elsewhere 1-3 a month, mostly thin holiday
  days. EURUSD (control, vs EURJPY / USDJPY): 28 such days in 6.7 years, all scattered thin days.
- The clock proof did not catch it because it tests time shifts on reference days, not prices.
- **Impact:** MT5 is preferred day by day (`data/sources.py`), so every GBPUSD backtest since 2026-10-26
  has read these days: strategy 1, London fix, R014, F1a / F1b (F1a's joint rule failed on GBPUSD
  -25.8 R; F1a is closed anyway by its pre-sample check, 2026-11-11). No verdict changes by itself:
  closed stays closed. The GBPUSD spread table (HANDOFF Open 3) is a separate issue.
- **Proposed fix (needs your go, it changes data every GBPUSD run reads):** quarantine the MT5 days
  that fail the own-cross check (> 2 pips; GBPUSD, and the same test on the other FX symbols that
  have a cross) with the existing quarantine in `data/cache_repair.py`, so histdata fills them; rerun
  the golden lists and report every change.

## What you decide

1. Accept 13.12, 13.13, 13.15, 13.16, 13.18 (and 13.14 with the finding above handled separately).
2. Go / no go for the GBPUSD 2019 quarantine fix.
