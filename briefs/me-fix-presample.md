# Brief: hypothesis 12 confirmation on 2008-2014 histdata (EURUSD + GBPUSD now)

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`, no downloads).
Spec: `docs/strategy-timed-hold.md` › Hypothesis 12, including its **Amendment** (read both; do not change
rules, grid or criteria). Never touch data after 2021-09-13.

1. Run `research/grids/timed_hold_me_fix.toml` for EURUSD and GBPUSD only on 2008-01-01..2014-12-31 from
   `data/cache/histdata_presample/`, results under `results/presample_2008_2014/` (own trial log), exactly
   the way the F1a pre-sample check ran (spec › F1a pre-sample check: find the commands / flags in the
   research log, `docs/research-runner.md`, `tools/research.py`; reuse the per-year clock check
   `results/clock_check_histdata_pre2015.md` and name any excluded year). If restricting symbols needs a
   grid copy, write it under `results/`, never in `research/grids/`.
2. Gates tool on that folder (`--primary-symbol EURUSD --min-trades 60 --min-breadth 1`), then compute the
   five criteria for the two-pair case as the amendment states (pooled EURUSD + GBPUSD; criterion 2 = both
   pairs net R > 0; halves 2008-2011 / 2012-2014; bootstrap blocks 5, 10,000 resamples, seed 2026110;
   criterion 5 = month-end mean minus the disjoint all-days mean, bootstrap 2.5 % > 0).
3. Append a section "Confirmation 2008-2014, EURUSD + GBPUSD" to
   `knowledge/research/reports/2026-11-09_me_fix_h12.md`: per pair and pooled trades, net R normal and
   doubled, mean, halves, bootstrap bound, criterion-5 difference, per-year net, verdict per criterion.
   Report the verdict.
