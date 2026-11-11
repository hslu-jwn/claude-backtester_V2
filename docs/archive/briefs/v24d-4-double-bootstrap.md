# Brief: V2.4d item 4 — drawdown Monte Carlo as a bootstrap, plus Masters' double-bootstrap bounds

Context: ROADMAP › V2.4d (4) (accepted by the user 2026-10-23); `docs/review/book-app-requirements.md`
F1; `knowledge/books/masters-testing-tuning.md` › ch.6 (drawdown bounds) and
`knowledge/topics/statistics-and-bayes.md` › Bootstrap, permutation and bounds. Risk code:
Opus reviews every line.

Today Monte Carlo kind A (`risk/monte_carlo.py`, `reshuffle_orders`) only **permutes** the
historic days: every simulated path holds exactly the historic days, so no path has a worse day
or a worse cluster of days than history. Drawdown, the longest underwater time and the FTMO
pass / breach probabilities are therefore optimistic. Masters: even a plain bootstrap
underestimates rare large drawdowns on short samples; bound them with a double bootstrap.

## What to build

1. **Day sampling with replacement** in kind A: `MonteCarloConfig.sampling` =
   `"block_bootstrap"` (new default, accepted by the user 2026-10-23 as the replacement) or
   `"permutation"` (today's, kept for comparison). Block bootstrap = the stationary bootstrap
   (Politis-Romano: block lengths geometric with mean `block_days`, default 5 = one trading
   week, wrapping at the end), drawing whole `Day`s (their trades and intraday order stay as
   they are), path length = the number of historic days. Seeded like today. Every consumer of
   the day orders (account paths, drawdown, fan, FTMO 2-Step, funded phase, adaptive risk,
   `prop_card.py`, `tools/risk_sweep.py`) uses the same orders, so they all change together.
   The Monte Carlo report names the sampling and block length.
2. **Double-bootstrap drawdown bounds** (new `risk/drawdown_bounds.py`, pure, on a daily R
   series: the marked-to-market series of V2.4d 1+2 when the run has one, else exit-booked):
   - outer loop: `outer` (default 200) stationary-bootstrap resamples of the whole series
     (a plausible "true" history each);
   - inner loop: for each, `inner` (default 1000) future paths of `horizon_days` (default 126,
     the funded window) by the same bootstrap, max drawdown in R of each path;
   - for each drawdown quantile q in (0.5, 0.9, 0.95, 0.99) take the inner q-quantile per
     outer sample, then report the median and the 90 % / 95 % upper bounds of those across the
     outer samples: a table q x bound confidence (Masters ch.6), in R and at each risk level of
     the config as % of the balance (fixed fraction, no compounding: R x risk).
   - Vectorised with numpy; 200 x 1000 x 126 must run in well under a minute.
3. Output: the Monte Carlo tool (`tools/monte_carlo.py`) report gets the table (HTML + JSON)
   and the research runner's chosen variant gets `drawdown_bounds.json` + a report block (dev
   period; test period too once run).
4. **Before / after numbers** (no further default change): a script
   `scripts/measure_bootstrap.py` runs kind A with both samplings on the golden runs of
   strategies 4, 6 and 7 (the ones positive or near zero in 2023 are the interesting ones;
   use the golden setup of `tools/golden.py`) and writes `results/bootstrap_compare.md`:
   median / 95th percentile max DD, P(DD > dd_alert), FTMO pass and breach probability at each
   risk level, permutation vs block bootstrap, plus the double-bootstrap table. Run it (log
   file) and put the table in your report.

## Rules

Spec first (`docs/risk-management.md` › Monte Carlo report), test-case list, failing tests, then
code. Tests: a seeded bootstrap is reproducible; with `sampling="permutation"` every existing
Monte Carlo test and number stays identical; a bootstrap path can contain a day twice and can be
worse than the historic worst drawdown; block lengths have the configured mean; the double
bootstrap's bounds rise with q and with the bound confidence; an all-positive series gives
drawdown 0; a hand-made series with a known drawdown. Existing Monte Carlo tests that assert
permutation-specific numbers pin `sampling="permutation"` explicitly instead of being weakened.
Never edit `src/backtester/live/`. Long runs to log files.

Done = full suite green (`pytest -q > results\pytest_v24d4.log 2>&1`), golden lists unchanged
(`python -m backtester.tools.golden --check > results\golden_v24d4.log 2>&1`; trades do not
depend on the Monte Carlo), `ruff check .` clean, the comparison table in the report. Report:
files changed, test count, decisions the spec did not settle, open questions.
