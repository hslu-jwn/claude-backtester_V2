# Research runner and Research page (ROADMAP 6.1 + 6.2)

Matched monkeys (V2.4c T-14): after selection, the chosen development trade list is compared
with three matched null models (200 seeded runs each). `monkeys = false` at grid top level
skips this diagnostic. `monkeys.json` and the report show net-R and max-DD percentiles;
`monkey_beaten` flags any kind failing the >= 90% rule on either statistic. Selection,
test-period access and trial/DSR accounting stay unchanged. Full rules and permutation
definitions: `risk-management.md` > Monte Carlo report > Matched monkeys.

Rules set by the user, 2026-10-21. Goal: test many strategy ideas fast, with one tool for every registered
strategy instead of a grid tool per strategy, and see at a glance which variants have an edge.

## Grid file

- One file per idea: `research/grids/<name>.toml` (written by Claude; the user does no file work).
- Contents: `strategy` (a `strategy/registry.py` name), `symbols`, optional `base` settings (start values,
  else the config defaults), `grid` (setting name -> list of values), optional `min_trades`, `max_variants`.
- Setting names are the strategy config's field names (dotted for nested fields); shared run settings
  (costs, detectors) may be swept the same way. An unknown name or a wrong type stops the run with an error
  that lists the valid names.
- Variants = the full product of the grid values; above `max_variants` a seeded random sample (the seed and
  the full grid size are recorded).

### Combined grids (V2.4, grid merge 1)

Use either `[grid]` or a non-empty array of `[[grids]]` tables, never both.
Each sub-grid accepts `name`, `base`, `grid`, and optional `compare_to`; its base overrides the top-level base.
Missing names become `grid1`, `grid2`, etc.; names must be unique non-empty strings
(`all` is reserved for the overall diagnostic row).
Products follow file order and each axis's value order. IDs retain full product positions,
including gaps after deduplication or sampling. Equal resolved run settings run once,
owned by the first family; the report names duplicate occurrences and retained IDs.
Deduplicate before seeded sampling; `max_variants` caps unique runs. Single grids keep
their existing IDs, sampling, research hash and CSV scorecard columns. Combined grids add
`family` and the union of swept setting columns (resolved values, including defaults).
Top-level `shocks` is boolean, default true; it controls diagnostics, not the research ID.

## Periods (data split rule of 2026-10-15)

- **Development:** from the first cached day to **2021-09-13**. All variants run here.
- **Test:** from **2021-09-14** to the last cached day (MT5 preferred day by day, `DEFAULT_SOURCES`).
  Only the **single best development variant** runs here, **once**.
- A second test run of the same grid (same strategy, symbols, grid and base) is refused unless `--retest`
  is given; a retest is recorded in the trial log as such.

## Ranking and selection

- Ranked by **net R on the development period** (user), only variants with at least `min_trades`
  (default **100**) development trades; the others are listed but not ranked.
- The chosen variant is the top-ranked one. The number of variants tried goes into the deflated Sharpe of
  the test result.

## Scorecard (one row per variant and period; also for every plain backtest run)

trades, win rate, average net R per trade, net R, profit factor (gross win R / gross loss R), max drawdown
in R, net R of the two halves (split at the period's middle year), net R with costs x 1.5, net R without the
best trade; for the test row also t, deflated Sharpe and the verdict (`analytics/verdict.py`, green / yellow /
red). Net R includes the swap.

### Scorecard additions (grid merge 2)

Append `se_avg_r`, `time_in_market`, `avg_hold_hours` to `SCORE_KEYS`. SE is sample standard
deviation of net R divided by sqrt(n), empty for fewer than two trades. Mean holding time is
exit minus entry in elapsed hours, empty without trades. Time in market is the union of
all symbols' [entry, exit) intervals, clipped to the period and UTC weekdays, divided by
the period's UTC weekday seconds. Period dates are inclusive (end means next midnight);
without explicit dates use the earliest entry day through the latest exit day. No trades
means zero occupancy for a positive denominator; zero weekday time means empty. Reject
negative holding durations. Legacy saved scorecards load with empty cells for absent keys.

### Parameter sensitivity (grid merge 2)

Top-level `sensitivity` is boolean, default true; false disables sensitivity. It does not
change the research ID or test guard. After development selection, including `--dev-only`,
perturb each numeric axis in the chosen variant's own family grid by -20%, -10%, +10%, +20%,
one setting at a time. Booleans, enums and other nonnumeric settings are excluded.
Integers round to nearest (ties away from zero), at least one integer step in the requested
direction; zero integers therefore get -1/-1/+1/+1. Zero floats have zero-valued neighbours.
Repeated rounded settings reuse one run and trial, retaining a CSV row per requested change.
Rejected configurations are skipped with setting, value and rejection reason recorded.

`sensitivity.csv` has id, setting, change (fraction), value, status, reason, scorecard columns,
and `net_r_share` (neighbour net R / chosen development net R, empty if chosen net R is zero).
Completed runs resume from `sensitivity/<id>/scorecard.json`; IDs include chosen ID, setting
and value. Each unique valid neighbour is a trial in family `<grid name>-sensitivity`.
Sensitivity trials never enter ranking, chosen settings, selection's DSR N or its Sharpes.
The report says **gentle** only if at least one neighbour ran and every requested neighbour
is valid, positive and retains >=50% of chosen net R with a positive chosen baseline;
otherwise **sharp**, listing failed settings (or no numeric settings). Skips are failures.

### Filter twins (grid merge 2)

A `[[grids]]` table may set `compare_to = "<family>"`, naming another existing family;
self-reference and unknown names are errors. Match each family product occurrence to the
first product occurrence in the target family with identical resolved settings except keys
in the comparing family's own `base` (top-level base is not excluded). Deduplicated runs
can supply either occurrence's score; sampled-out settings cannot and are unmatched.
`twins.csv` records family, variant ID, twin ID, matched/unmatched status, both net R,
difference (family minus twin), and both trade counts. Per-family report means use matched
pairs only, weighting each occurrence equally. "lifts the average": yes only when family
mean strictly exceeds twin mean; no for ties; empty/n/a without matched pairs. Diagnostics
do not change the research ID, selection, trial logging or DSR.

### Expectation haircut (grid merge 2)

`ResearchConfig.live_expectation_range` defaults to `(0.50, 0.75)`, with finite bounds
0 <= lower <= upper <= 1. Under the chosen variant and completed test, print:
"Live expectation: 50-75 % of the backtest's average R per trade = <a> to <b> R per trade".
Use that period's average net R and configured bounds; empty averages print n/a. A zero or
negative average prints "no positive edge to discount" (a haircut would make a loss look
smaller; Opus, 2026-10-23).

**Warning flags** (thresholds in a config dataclass, these defaults): too few trades (< `min_trades`);
high win rate but small edge (win rate >= 70 % and average R < 0.1); one half not profitable; not profitable
with costs x 1.5; not profitable without the best trade; test failed (test net R <= 0 or verdict red).

## Defaults decided while building (2026-10-21)

`max_variants` 200, seed 1; enum values by name, any case; a combination the config rejects stops the run
naming the variant; the test row's verdict uses the 5 available checks (random-entry and random-fill checks
n/a), deflated Sharpe with N = variants run and their development Sharpes; profit factor empty without a
losing trade; "test failed" only on the test row; research id = `<grid file>_<hash of strategy, symbols,
base, variants>` (re-running resumes; the retest guard uses it).

## Output

`results/research/<id>/`: `research.json` (grid, periods, symbols, variant count, seed, chosen variant, test
status), `variants.csv` (development scorecards), `test.csv` (the test scorecard), `report.md` (short
summary). The chosen variant's development and test runs are also written as normal run folders
(`results/<run-id>/`, so the results page and the chart open them) and the chosen settings as a preset.
Runs are resumable: a finished variant is not run again. Every research run is written to the trial log.

### Daily series (V2.4d items 1?2)

The chosen development variant and each completed test run also retain
`drawdown_bounds.json` (V2.4d item 4). The chosen development file is copied to its
published run folder. `report.md` includes the double-bootstrap tables for development
and completed tests; this reporting never starts an unspent test. Defaults and the
MTM/exit-booked fallback follow `risk-management.md` > Monte Carlo report.

Every development variant retains variants/<id>/daily.csv: date, net_r_exit_booked,
net_r_mtm, position, including empty weekdays. Sensitivity neighbours retain the same
file in sensitivity/<id>/; each test/retest retains it in its own normal run folder.
Trial-log series paths are relative to results/. Resume backfills missing files from
saved trades, including historical tests, without backtests. Existing files are retained;
trial-log links are refreshed with the same trial identity (no additional trials).
No scorecard, ranking, golden list, daily statistic or DSR changes: statistics continue
using exit-booked daily net R. Valuation follows risk-management.md > Trial log and
deflated Sharpe. Older CSVs lacking entry fill reconstruct it from the saved spread;
older partial exits lacking fill details use their saved chart prices and spread, with
unrecoverable fill-cost residuals settled on final exit day. New CSVs retain fill details.

### Significance of the best variant

V2.4d item 5 / V2.4c T-09, T-19: after development, recompute
`significance.json` from all completed development grid variants' aligned `net_r_mtm`
daily series, including unranked variants, excluding sensitivity neighbours and tests.
The report block "Is the best variant better than luck?" is diagnostic only: selection,
test guard, trial log, DSR and all existing statistics retain their current definitions.
Missing series are unavailable, never silently replaced with exit-booked returns.

- **White's Reality Check:** observed statistic = maximum mean daily R. Centre each
  column separately to zero; stationary-bootstrap day indices with mean block length
  5, the same indices across every variant. Default 2,000 resamples, seed 42;
  p = (1 + count(null maximum >= observed maximum)) / (boots + 1).
  At least two days and one variant are required. No SPA approximation is reported.
  The unchanged stationary sampler lives in analytics/bootstrap.py and is re-exported
  by risk/bootstrap.py, preserving the risk API/random stream and the layer direction.
- **CSCV / PBO:** default S = 16 even ordered blocks; distribute remainder days to
  the earliest blocks without discarding observations. Evaluate every C(S,S/2) IS
  combination. Rank by nonannualised daily sample Sharpe; constant columns have score
  zero (Sharpe is unestimable). IS ties choose the first input variant; OOS ties use
  average ascending ranks (worst = 1), relative rank = rank / (N + 1).
  Logit = log(rank_fraction / (1 - rank_fraction)); PBO = share <= 0, including ties
  at the median. Report median relative OOS rank, IS/OOS Sharpe pairs, and OLS slope
  of OOS on IS (n/a for constant IS scores). Purge 5 observations from the OOS side
  of every internal block boundary: trim both ends of an OOS block where a neighbour
  exists, including an OOS neighbour; do not trim outer dataset endpoints.
  Require >= 2 variants and >= 2 observations in every block after its potential
  purge; otherwise n/a with a reason. Odd S or invalid inputs raise clear errors.
- **Effective trials:** report N, average pairwise daily correlation and
  N_eff = max(1, N / (1 + (N - 1) * mean correlation)). Identical columns correlate
  one, including identical constants; other constant pairs correlate zero. N=1 gives
  one; no observations or a nonpositive denominator gives n/a with a reason.
  Negative correlation may give N_eff > N; do not silently cap it or substitute it
  into DSR.
- **Effective trades:** use the chosen development variant's saved trade intervals,
  rather than net signed positions (opposite trades can cancel). On each Prague
  calendar day touched by [entry, exit), count concurrent trades without direction or
  size netting; average reciprocal concurrency over each trade's days. A zero-duration
  trade occupies its entry day. Include weekends for held trades. Report all uniqueness
  weights, their average, and their sum (effective trade count); no trades gives zero.
- Add chosen development row flags `rc_not_significant` for p > 0.05 and `pbo_high`
  for PBO >= 0.5. Thresholds and sampling settings live in frozen config dataclasses.
  Unavailable diagnostics never add a flag. Recompute on resume without new trials.

No saved-return sign-flip or permutation test is valid here. Monte Carlo permutation
of the **whole optimisation**, re-running variants on permuted prices, is deferred
to V2.6 with the job queue (Aronson ch.6 / Masters ch.7).

### Bayesian view (V2.4c T-10)

Diagnostic only: recompute `bayes.json` from saved trades on resume, for the chosen
development variant, every completed test/retest, and development `compare_to` twins.
Never spend a test, add trials, change selection, DSR or existing statistics.

- Win = net R > 0; scratches are nonwins. Estimate p* = L / (W + L) from the same
  list's positive-win mean W and absolute strictly-negative-loss mean L. Without
  both signs p* and win-rate inference are unavailable, with a reason (no invented payoff).
  Report Beta(1,1), weak Beta(20*p*,20*(1-p*)), and strong skeptical Beta with
  strength 100. **100 is the Opus choice requested in the brief**, configurable via
  frozen `BayesConfig.strong_strength`; the user can change it (card range 100-200),
  passed to `run_research(..., bayes_config=BayesConfig(...))`.
  Flat is uniform, not generally centred at p*. Add actual wins and nonwins to
  each prior; show posterior parameters, mean, equal-tail 95% interval, P(p > p*).
- Mean R: Normal(0, 0.075 R) prior (0.075 is standard deviation), normal-normal
  update treating the sample variance (ddof=1) as known. Likelihood variance of
  the mean = sample variance / effective trades, using `trade_uniqueness` in
  `analytics/effective_n.py`; report raw and effective counts, shrinkage, posterior
  mean, sd, equal-tail 95% interval and P(mean R > 0). Fewer than two trades or
  zero sample variance is unavailable rather than falsely certain. Nonfinite R
  or invalid intervals are errors. Empty lists are explicitly unavailable.
- Edge Bayes factor: H0 is point p*. H1 is the **strong skeptical Beta prior
  restricted to p > p***. Integrate its likelihood once; do not reuse a fitted
  posterior as a prior. Log BF = log B(a+w,b+l) - log B(a,b) - log likelihood(H0)
  + log posterior Beta upper-tail mass - log prior Beta upper-tail mass.
  Prior edge:no-edge odds are **1:50** (user, 2026-10-16); posterior odds = BF/50.
  Retain log values for extreme evidence; unrepresentable numeric odds are null.
  Required trades is the total expected count, ceil(log(10/(1/50))/KL(p_hat||p*)),
  using the observed positive edge as a fixed hypothetical alternative. Also show
  remaining trades beyond raw n. This planning approximation differs from integrated
  BF. No positive edge gives n/a. 55% vs 50% gives 1,241 for target 10:1;
  the card's approximately 1,400 uses target 20:1 (1,380).
- Twins: A = compare_to, B = comparing family. Sample independent mean-R and strong
  Beta posteriors, seed 42, 20,000 draws; report P(B > A) per matched occurrence.
  Family probabilities are equal-weight means of available pair probabilities;
  report unavailable/unmatched counts. Resolve deduplicated occurrences to saved
  retained runs. Do not pool repeated trades across grid settings. Independent
  posterior draws are an approximation: filters share signals, so this is not a
  paired causal filter test and does not adjust for selection or multiple testing.
- Add `bayes_weak` only to the chosen development row if available skeptical
  P(mean R > 0) < 0.9 (strict). All settings above live in frozen `BayesConfig`.
  The report block **Bayesian view** shows periods, priors, odds, sample planning,
  twin probabilities and limitations. Unavailable results never add a flag.

### Additional diagnostics (V2.4, grid merge 1)

- `grid.csv` and a report block: development `grid_stats` over all variants, including
  unranked ones, and per family: n, mean, sample standard deviation, mean minus one sd,
  profitable share, robust (share >= 70%). Families with one or two swept settings also
  report the neighbour-smoothed plateau variant ID and net R. Axis order follows TOML;
  unsampled cells stay missing. Duplicate cells reuse the retained result for plateaus,
  while statistics count owned variants only. Zero-axis families use their sole variant;
  more than two axes get statistics only. The overall row has no cross-family plateau.
- `breakdown_symbols.csv`, `breakdown_classes.csv`, `by_year.csv`: chosen development
  and test summaries using analytics metrics, including swap. Rows identify period,
  variant ID and test run (development = 0); retests are retained. Years use UTC entry
  year and include all-symbol and per-symbol summaries. Empty groups are omitted.
- Shared market classes preserve ORB's US indices / EU/UK/JP indices and session-specific
  FX London / FX New York and Metals London / Metals NY for ORB trades carrying a session.
  Otherwise FX and Metals are generic. Energy, Crypto and Dollar index cover the remaining
  cached symbols; future unknown symbols use Other. All 26 MT5 symbols and Binance
  BTCUSDT / ETHUSDT are mapped.
- `shocks.csv` and a report block: chosen development and each test's `shock_report`,
  including net R with and without shocks and zero-trade results. UTC daily OHLC is
  aggregated through the configured source once per cached symbol/day across both periods.
  Preceding cached bars supply ATR warmup; classification uses preceding days only.
  `shocks = false` skips daily reads and removes shock output. Per-variant shock columns
  are deferred to preserve existing scorecard CSVs. Diagnostics are cached alongside
  scorecards so resuming never replays completed variants. The completed test status is
  persisted before diagnostics are refreshed, so a reporting failure cannot allow a
  second test. Development-only diagnostics stop daily reads at the development end.

## Research page (app)

- One row per research variant and per plain backtest run in `results/`, scrollable, sortable by every
  column, filter by strategy / symbol / flag.
- Default sort: verdict (green first), then test net R, then development net R.
- Flags shown as small warning badges next to the numbers; a row click opens its results page (and from
  there the chart).
- Command-line runner first, then the page (user, 2026-10-21).

## Walk-forward (V2.4, grid merge 3)

Optional top-level `walk_forward = "anchored" | "rolling"`, with `train_years`
(a positive integer, default 3, rolling window length). `--walk-forward` enables
anchored mode when the grid does not specify a mode. Disabled by default.
Use only the saved development trades, never additional backtests or test-period data.
Yearly windows and max training net R selection use `analytics/walk_forward.py`:
anchored trains on all preceding development years; rolling uses up to train_years
preceding years. One training year is sufficient. Ties keep file variant order;
all development variants participate, independent of the overall min_trades ranking.
Only trades closed before the test year's start contribute to training net R.

`walk_forward.csv`: test_year, picked_variant, train_years, train_net_r, net_r,
chosen_variant, chosen_net_r, trades. The comparison is the overall development
selection (empty if no variant qualifies), not an extra run of default settings.
Include calendar years from the development start to end, including empty and partial
years. The report includes the chained OOS scorecard over the OOS dates, clipped to
the development end. Efficiency = (chained OOS net R / number of OOS years) /
mean(pick's training net R / number of its training years). Calendar years count
as one even when partial. Efficiency is n/a when mean annual training net R <= 0
or no OOS years exist. No picks yields an empty CSV and an explanatory report.
This diagnostic does not change the research ID, ranking, trials, DSR or test guard.

## Standalone gap-bucket study and sweep grids (grid merge 3)

`python -m backtester.tools.gap_bucket_study --mode index` (or `--mode fx`)
writes `gap_buckets.csv`, preserving the gap-bucket analytics, warmup and session
loader. Supports symbols, start/end, cache-dir and out; end after 2021-09-13
requires explicit `--allow-test-period`. Default start is 2015-01-01.
No strategies are backtested and no trials are logged by this descriptive study.

Replacements for the previous sweep commands live in `research/grids/`:
orb, gap_fade, no_wick, trend_following, ny_index_sweep, ny_index_volume,
gap_momentum_index and gap_momentum_fx. Run each with
`python -m backtester.tools.research research/grids/<name>.toml --dev-only`.
Headers record former commands and options without runner equivalents.
Archive deletion requires identical trade counts and net R for two NAS100 ORB
and two XAUUSD trend variants using the same development data and costs.

Migration details: SMA plain and banded products have separate families because
only periods 50 and 200 had bands in the former sweep; a single Cartesian family
would introduce extra configurations. The eight replacement files resolve to
41 / 36 / 24 / 95 / 8 / 2 / 36 / 36 variants respectively (order listed above).
Active studies retain their existing CSV and segmented-run behavior through
`tools/research_helpers.py`. Historical briefs and former command provenance are
preserved under `docs/archive/`.
