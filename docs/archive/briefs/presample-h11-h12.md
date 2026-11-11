# Brief: import the new pre-sample histdata; run the H12 four-pair and the Gotobi pre-sample checks

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`, no downloads).
Spec: `docs/strategy-timed-hold.md` › Hypothesis 11 (› Pre-sample check 2008-2014) and Hypothesis 12
(› Amendment). Do not change rules, grids or criteria. Never touch data after 2021-09-13.

1. Import `data/raw/histdata_presample/` AUDUSD, NZDUSD, USDJPY, EURJPY (2008-2014) into
   `data/cache/histdata_presample/` the way EURUSD / GBPUSD were (research log, F1a pre-sample; the
   histdata clock rule US DST through 2018 applies). Per-year clock check for the new pairs and years
   (method of the F1a check: release spikes at NFP / FOMC times); name any excluded year.
2. H12: run `research/grids/timed_hold_me_fix.toml` (all four pairs) on 2008-01-01..2014-12-31 from the
   pre-sample cache into `results/presample_2008_2014/` (as the previous EURUSD + GBPUSD run did, see
   `results/ai/20261109-211523_codex_me_fix_presample.md`); evaluate the five criteria over the 4 pairs
   (criterion 2 = at least 3 of 4 net R > 0; halves 2008-2011 / 2012-2014). Append "Confirmation
   2008-2014, four pairs" to `knowledge/research/reports/2026-11-09_me_fix_h12.md`.
3. Gotobi: run `research/grids/timed_hold_gotobi.toml` on 2008-2014 from the pre-sample cache, gates tool
   (`--primary-symbol USDJPY --min-trades 200 --min-breadth 1`, rollover tolerance is built in), then the
   four pre-registered criteria for G1 gotobi stop 1.0 USDJPY. Write
   `knowledge/research/reports/2026-11-09_gotobi_presample.md`: per symbol trades, net R normal / doubled,
   mean, halves, bootstrap, gate-3 difference, gate 7 counts (tolerant and strict), per year, verdict
   per criterion; G2 reported too.
Report both verdicts and the files.
