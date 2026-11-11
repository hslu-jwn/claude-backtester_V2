# Brief: V2.4d items 7 + 8 — detrended benchmark, position bias, bootstrap bounds, log profit factor

Context: ROADMAP › V2.4d (7) and (8) (accepted by the user 2026-10-23);
`docs/review/book-app-requirements.md` B2-B5; `knowledge/books/aronson-evidence-based-ta.md`
(detrending, the no-skill benchmark, ch.1), `knowledge/books/masters-testing-tuning.md` (ch.6:
BCa bounds of the mean, bootstrap of log PF); `knowledge/topics/statistics-and-bayes.md` ›
Bootstrap, permutation and bounds. Pure analytics, no trading rule or engine change.

## What to build

1. **Detrended result** (`analytics/detrend.py`): a rule that is long more often than short in
   a rising market earns the trend without skill (Aronson). Per symbol and period, the drift =
   (last close - first close) / elapsed seconds of the period's cached M1 (or daily) closes.
   Per trade: `trend_r` = direction x drift x (exit_time - entry_time in seconds) / stop
   distance, share-weighted over partial exits by each part's own exit time; `detrended_r` =
   r_net - trend_r. Report net R raw and detrended, and avg R raw and detrended, per symbol and
   total. Prices through `SymbolSources` (one read per symbol and run of cached days, the same
   pattern as `research_diagnostics.load_shocks`); a pure core takes the drift per symbol.
2. **Position bias** from the daily `position` series of V2.4d 1+2 (`variants/<id>/daily.csv`,
   or computed from trades): share of time long, short and flat; Aronson's no-skill expected
   return [p(long) - p(short)] x average market change, shown next to the raw result.
3. **Bootstrap bounds** (`analytics/bounds.py`): BCa (bias-corrected and accelerated, jackknife
   acceleration) lower bound at 90 / 95 % of (a) the mean daily marked-to-market net R and
   (b) the mean net R per trade; seeded, `boots` default 5000; with the plain t-based lower
   bound beside it. **Log profit factor** = log(sum wins / |sum losses|) on the daily MTM
   series, with its BCa 90 / 95 % lower bound (Masters: bootstrap log PF, never raw PF; None
   without a loss day).
4. **Wiring**: research runner report block "Skill vs trend, and bounds" for the chosen variant
   (development, test once run) + `skill_bounds.json`; the Monte Carlo tool's report gets the
   same block; scorecard keys `detrended_net_r`, `lower95_mean_daily_r`, `log_pf` at the end of
   `SCORE_KEYS` (old result files without them still load). Flag `skill_is_trend` when net R
   > 0 but detrended net R <= 0.

## Rules

Spec first (`docs/research-runner.md` and `docs/risk-management.md` › Monte Carlo report),
test-case list at the top of each new test file, failing tests, then code. Known answers: a long
held over a straight-line rising market has detrended R ~ 0; a short in it has negative trend_r;
partial exits weight by share; zero drift -> detrended = raw; BCa on a symmetric normal sample is
close to the t bound; BCa is reproducible with the seed; log PF of equal wins and losses = 0;
no loss -> None. Selection, test run, trial log, DSR, golden lists unchanged. Never edit
`src/backtester/live/`. Long runs to log files.

Done = full suite green (`pytest -q > results\pytest_v24d78.log 2>&1`), `ruff check .` clean;
then one real run: `python -m backtester.tools.monte_carlo` on the golden trend-following setup
(or the research runner on a 2-variant trend grid, dev-only, results to `results\v24d78_check`)
with the new block in the report. Report: files changed, test count, decisions the spec did not
settle, open questions.
