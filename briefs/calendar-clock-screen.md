# Brief: two-stage calendar x clock screen, discover on 2008-2014, confirm on 2015-2021

Pre-registered by Opus 2026-11-09 (design, thresholds and cell list fixed before any run). Read `AGENTS.md`
first; hard limits apply (no commits, no servers, no `live/`, no `.env`, no downloads). Analysis only: no
strategy code, grids or spec edits. Never touch data after 2021-09-13.

## Why

Literature ideas at our cost level are used up (research log 2026-11-09); Gotobi showed a real flow edge
that decayed after it became popular. A data screen is acceptable only with an out-of-sample stage:
discover on the pre-sample, confirm on development, the test period stays unspent.

## Data

Pairs EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, EURJPY. Discovery: `data/cache/histdata_presample/`
2008-01-01..2014-12-31 (clock-checked, `results/presample_2008_2014/clock_check_*`). Confirmation: the
default cache (MT5 preferred) 2015-01-02..2021-09-13. Load with the existing loaders (`load_m1`).

## Cells (fixed)

- Clock blocks: 12 two-hour UTC blocks 00-02, 02-04, ..., 22-24 (return = log close at block end / close
  at block start, both exact M1 closes; skip a day if either is missing; skip blocks containing 21:00-22:00
  UTC on any day, the rollover, i.e. blocks 20-22 and 22-24 are reported but never selected).
- Day classes (by the UTC date of the block start; Tokyo business day rules from
  `strategy/timed_hold/day_filter.py` for the gotobi class): Monday, Tuesday, Wednesday, Thursday, Friday,
  gotobi day, last weekday of month, first weekday of month, 15th +-1 weekday, day after a US (NYSE)
  full closure, day after a Japanese holiday. 11 classes.
- 6 pairs x 12 blocks x 11 classes = 792 cells. Signed return in bp, sign free (long or short).

## Stage 1, discovery (2008-2014)

Per cell: n, mean bp, t (day-clustered, one value per day), cost bp (round trip from the cost model at the
pair's median price that year range, as `tools/time_of_day_profile` computes). Survivor: n >= 60,
|t| >= 4.0 (about Bonferroni 0.05 / 792 two-sided), |mean| >= 2 x cost, block not a rollover block.

## Stage 2, confirmation (2015-2021), survivors only

Confirmed: same sign, |mean| >= 1.5 x cost, t >= 2.0 in the same direction, and the difference to the
same block on all other days of that pair has the same sign. Report every survivor, confirmed or not.

## Output

`knowledge/research/reports/2026-11-09_calendar_clock_screen.md`: design (copy this brief's numbers), the
count of cells, survivors table (stage 1 and stage 2 numbers side by side), confirmed list, the 20 largest
|t| cells of stage 1 for context. Opus decides which confirmed cell, if any, becomes a hypothesis (its
test period stays unspent). Report counts and the confirmed list.

## Definitions decided by Opus (2026-11-09, after Codex's question, before any run)

- "15th +-1 weekday" = Monday-Friday dates 14, 15 or 16 of the month.
- "Day after a US (NYSE) full closure" / "day after a Japanese holiday" = the first Monday-Friday after a
  holiday that is not itself a holiday of that calendar; a run of consecutive holidays (with or without a
  weekend inside) yields one day, the business day after the run's last holiday. Weekends alone do not
  count as closures. Japanese holidays include Dec 31 and Jan 2-3 as in `day_filter.py`.
