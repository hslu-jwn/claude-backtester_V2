# Brief: run hypothesis 12 (month-end post-fix USD rise): development + 2010-2014 confirmation

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). Spec:
`docs/strategy-timed-hold.md` › Hypothesis 12 (pre-registered; do not change rules, grid or criteria).
Never touch data after 2021-09-13 (the test period).

## Task

1. Development run: `python -m backtester.tools.research research/grids/timed_hold_me_fix.toml --dev-only`.
   If config validation rejects `month_day = -1` with `day_filter = "all"`, report it and stop (do not
   edit the grid).
2. Confirmation run on 2010-01-01..2014-12-31 from the MT5 cache, results under
   `results/presample_2010_2014/` (own trial log), the way the F1a pre-sample check ran (spec › F1a
   pre-sample check; find its mechanism in `tools/research.py` flags / `docs/research-runner.md`). Check
   the cache really covers 2010-2014 for all four pairs (report missing months).
3. Gates: `python -m backtester.tools.timed_hold_gates <folder> --primary-symbol EURUSD --min-trades 60
   --min-breadth 3` on both folders (report the pooled block too). Then compute the five pre-registered
   confirmation criteria on the 2010-2014 folder exactly as written (pooled over the 4 pairs; halves
   2010-2012 / 2013-2014; bootstrap blocks of 5, 10,000 resamples, seed 2026110; criterion 5 = month-end
   mean minus disjoint all-days mean), with a small script under `results/` if the tool has no pooled
   variant.
4. Write `knowledge/research/reports/2026-11-09_me_fix_h12.md`: per pair and pooled trades, net R
   (normal, doubled), mean net R, halves, bootstrap bound, difference vs all-days, per-year net, and the
   verdict per criterion. Report the verdict and the file; do not edit the spec.
