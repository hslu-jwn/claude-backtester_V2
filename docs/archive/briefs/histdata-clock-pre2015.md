# Brief: histdata clock rule for years before 2015

Read `AGENTS.md` first; its hard limits apply (no commits, no servers, no `live/`, no `.env`).

## Why

`src/backtester/data/histdata.py` `histdata_to_utc` applies the US DST rule only for 2015-2018
(hard-coded `between(2015, 2018)` or similar) and the European rule for every other year. A clock
check of 2008-2014 EURUSD (`knowledge/research/reports/2026-11-09_clock_check_pre2015.md`) shows those
years follow the US rule too: every NFP / FOMC release in a US-summer / Europe-winter week is exactly
one hour late with the European rule, all other weeks are correct. Years 2019+ keep the European
rule (verified earlier, `results/clock_check_histdata.md`; ROADMAP 13.12 "histdata clock 2015-2018").

## Files

- `src/backtester/data/histdata.py` (the year condition of the US rule only)
- `tests/data/test_histdata.py` (next to the existing clock tests, e.g.
  `test_clock_changes_on_europes_dates`)
- `docs/ARCHITECTURE.md`: the sentence on the histdata clock rule ("unverified" for years before
  2015 -> US rule verified for 2008-2018 on 2026-11-09 with the report above)

## Change

US DST rule for every year up to and including 2018 (2008-2018 verified; earlier years: the same
rule, noted as unverified in the comment). 2019 onward unchanged.

## Tests (write first)

1. A 2012-03-14 timestamp (US summer, Europe winter) converts with the US rule (same offset as a
   2016-03-16 timestamp in the existing 2015-2018 test).
2. A 2012-10-31 timestamp (Europe winter, US summer) converts with the US rule.
3. Existing 2015-2018 and 2019+ tests unchanged and green.

## Done =

`python -m pytest tests/data -q` green, `python -m ruff check .` clean. The main cache is not
re-imported (no change for 2015+). Report files changed and test results.
