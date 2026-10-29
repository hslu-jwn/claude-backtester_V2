# Research runner and Research page (ROADMAP 6.1 + 6.2)

## Skill vs trend, and bounds (V2.4d 7 + 8)

After selection, report the chosen development variant and each already executed test
in `skill_bounds.json` and the report. Never open an unspent test period for diagnostics.
Append `detrended_net_r`, `lower95_mean_daily_r`, `log_pf` to SCORE_KEYS; unavailable
values are null and historic scorecards without these fields remain readable.
Flag `skill_is_trend` when raw net R > 0 and detrended net R <= 0. Diagnostics change
neither ranking, execution, trial logging, DSR nor the seven-check verdict.

Per symbol, use the first and last cached M1 closes inside the inclusive UTC period:
drift = price change / elapsed seconds between those closes (weekends included).
Read SymbolSources once per symbol/consecutive cached-day block. Fewer than two
distinct close times makes that symbol unavailable, never silently zero drift.
Pure detrending accepts supplied drifts. Subtract direction * drift * holding seconds /
initial stop distance from saved net R, weighting partial exits by share and their own
exit time and the remaining share by final exit time; apply saved risk_weight.
Report raw/detrended net and mean R by symbol and total; unavailable symbols make
total detrended R unavailable. Costs remain in net R.

Compute position bias from trade intervals (signed daily averages lose intraday reversals).
Integrate signed remaining share per symbol over Prague weekdays in the period,
clipping simultaneous net exposure to [-1, 1]. Positive/negative magnitude gives
long/short time, remainder flat. Average shares equally across symbols. Show each
symbol's no-skill expected price change per day = (p(long)-p(short)) * drift * 86400
next to raw R; price units must not be pooled across symbols.

For daily marked-to-market net R (including zero weekdays) and trade net R show mean,
one-sided 90/95% BCa lower bounds and Student-t lower bounds. Frozen config defaults:
seed 42, 5000 iid samples of original length. Use jackknife acceleration, midpoint
ties for bias correction and linearly interpolated empirical quantiles. These are iid
descriptive bounds, not dependence or selection corrections. Constant samples have
bounds equal to their value; fewer than two observations have no bounds.
Log PF = log(sum positive daily MTM R / abs(sum negative daily MTM R)). Without both
wins and losses it and its bounds are null. Undefined bootstrap or jackknife log PF
replicates make its bounds unavailable with a reason; never discard replicates or
bootstrap raw PF. Reject nonfinite inputs. Prefer complete saved daily MTM; otherwise
compute MTM from trades and cached marks, never substitute exit-booked daily R.
JSON records sample count, method, seed, replicate count and unavailable reasons.

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
- Optional `idea = "..."` supplies the Research card's one-line idea and is saved in
  `research.json`. Without it, the card uses the strategy label. This text does not change grid IDs.
- Setting names are the strategy config's field names (dotted for nested fields); shared run settings
  (costs, detectors) may be swept the same way. An unknown name or a wrong type stops the run with an error
  that lists the valid names.
- Variants = the full product of the grid values; above `max_variants` a seeded random sample (the seed and
  the full grid size are recorded).

### Submission identity (V2.6i step 2)

Grids handed over through research intake may add exactly these four fields:

```toml
[submission]
strategy_id = "US500_FINAL30_CONT"
specification_version = "0.2.0"
submission_sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
experiment_id = "US500_FINAL30_CONT__v0.2.0__DEVELOPMENT__1"
```

The strategy ID matches `[A-Z][A-Z0-9_]{2,63}`, the version is three numeric components,
and the digest is 64 lowercase hex characters. The experiment must match the strategy/version
and use `DEVELOPMENT__n`, n >= 1. Invalid or extra fields stop loading with a named `GridError`.
Submission identity participates in the research folder hash so versions cannot share resume state.
Without this table, existing grid IDs, trial JSON lines and test behavior stay unchanged.

`research.json` records the submission and, for these grids only, a `dataset` manifest:
`dataset_id = "v2-cache"`, sorted symbols, inclusive start/end dates, cache directories in
`source_summary`, and a SHA256 version of sorted `symbol<TAB>relative path<TAB>size` lines
(joined by newlines, without a trailing newline). Paths are relative to the V2 home
(other Windows volumes use a relative label such as `C/cache/...`);
only resolved preferred/main/fallback day files for the run's symbols and period contribute.
This fingerprints file sizes, not candle contents. Every research run records `code_commit`
and `code_dirty` (both null if git fails). Old reports without these fields remain readable.
Submission grids also write `info.json` in the research folder and in each recorded run folder;
run manifests use that run's dates. Each trial carries `submission`, excluded from its key;
the field is omitted entirely when absent.

The first test and every `--retest` require
`results/intake/<strategy_id>__v<version>/test_authorization.json` containing
`authorized_by = "user"`, a nonempty `quote`, an ISO `authorized_at`, and the grid's
development `experiment_id`. Opus writes this file only after the user's explicit go,
quoting their words; no runner code creates it. Missing or invalid authorization keeps the
runner in development-only mode and logs/reports
`test skipped: no user authorization for <strategy_id>__v<version>`.
`--dev-only` never spends the test, even with authorization. Holdout run identities replace
the development experiment with `<strategy_id>__v<version>__FINAL_HOLDOUT__1`, then `__2`,
etc., counting earlier tests in saved info or the trial log. Test run `info.json` and trial
metadata carry the holdout identity; the research folder retains the development identity.

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
- **Exception, costs only:** the median spread table fills years it has no measurement for from the
  nearest measured year, so the development period may use spreads measured later (NAS100 / US500 in
  2015-2020 use the 2021 values, and 2021 is measured over the whole year, across the cutoff). Accepted
  because costs are no trading signal (rule set by the user, 2026-10-27; full check finding 7).

## Ranking and selection

- Ranked by **net R on the development period** (user), only variants with at least `min_trades`
  (default **100**) development trades; the others are listed but not ranked.
- The chosen variant is the top-ranked one. The number of variants tried goes into the deflated Sharpe of
  the test result.
- **One DSR definition: daily net R, as the trial log** (the user, 2026-10-27; ROADMAP 12.13). The
  Sharpe and DSR here use `daily_net_r` over the weekdays of the period (development: dev start..end;
  test: test start..end), the same helper and periods as `trial_log.make_record`. The stored
  per-variant `day_sharpe` (family Sharpes V) and the test row's DSR follow it; the per-trade Sharpe
  is no longer stored. A variant stored with the old per-trade `sharpe` runs again on resume.

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

Additional runner-check outputs: `entry_screen.json`, `returns_slope.csv` and `top_trades.csv`
(details below), `monkeys.json`, and `criteria_inputs.json` (development criteria inputs).

### Fast loop (V2.6k, 2026-10-28)

By default the chosen development variant must have net R after costs above
`ResearchConfig.gate_net_min` (default 0) before matched monkeys or the entry screen run.
Set the grid key `fail_fast = false` to run the enabled null tests regardless of this gate.
The existing `monkeys` and `entry_screen` switches still disable their respective tests.
When gated, enabled null-test JSON files record the threshold, chosen net R and skip reason;
the chosen row receives `nulls_skipped` and the report records the skip.

The runner's `--workers` also controls matched monkeys and entry screening. Random draws
remain in the parent process in their original seeded order; re-simulation uses workers and
produces identical numbers for every worker count. `--workers 1` runs in process; the default
uses one fewer than the available CPUs, at least one. The standalone entry-screen command
accepts the same option.

`criteria_inputs.json` records development variant counts, chosen gross and net R, gross R
by symbol, stressed costs, scorecard halves, net R excluding the best 1, 5 and 10 UTC exit
days, stop share, and counts and net R by trade tag. It feeds submission result envelopes.

### Runner checks (V2.4c, 2026-10-28)

These are reporting warnings; they do not alter selection, verdict thresholds, strategy,
engine or cost settings.

- **Free parameters:** `swept_params` in `research.json` lists sorted distinct setting names
  with more than one distinct value within any grid family (or `[grid]` without families).
  Single-value settings and differences between fixed family bases do not count.
  `free_params` is their count. `ResearchConfig.max_free_params=4` (must be >= 1) adds
  `too_many_parameters` to every development variant row and the run-level `flags` in
  `research.json` above the limit. The report prints
  the count, limit and names; the grid still runs.
- **Entry screen:** top-level grid key `entry_screen = true|false`, default `true`, runs
  immediately after matched monkeys on the chosen development variant only. It reads that
  variant's saved trades and M1 candles only within the development start/end, using its
  strategy base timeframe and unchanged engine costs. `EntryScreenConfig` defaults stay
  unchanged (1,000 random/shuffle runs, seed 42). `entry_screen.json` stores pass/fail,
  reasons, positive-cell share, 1R/1R bracket win rate and random-exit percentile, plus counts
  and period metadata. Failed screens add `entry_screen_failed` to the chosen row.
  Missing M1 records an `error` in the JSON and report without stopping the run. Disabling
  the screen, or having no chosen variant, removes any stale file. The report block is
  "Entry screen (chosen development variant)". Existing screening thresholds are unchanged:
  at least 70% positive cells, at least 52% bracket win rate and random-exit percentile > 90.
- **Decay and extreme trades:** `returns_slope.csv` and `top_trades.csv` cover the chosen
  development variant and each saved test/retest, identified by `period`, `variant_id` and
  `test_run` (0 for development). These diagnostics use saved trades, without a new test run
  or new test-period candle reads. Monthly net R uses UTC entry months and fills months
  between the first and last trade with zero. Each slope CSV row contains the `monthly_net`
  month-to-R JSON map and OLS `slope_per_year`, `standard_error` (also R/year), `t_stat` and
  `n_months`. Below six months, slope/SE/t are empty. Perfect fits have empty SE/t (JSON
  `null`) and `perfect_fit=true`, including constant series with slope zero.
  `ResearchConfig.decay_t=-2.0` adds `declining_returns` only to the chosen development row
  when t <= -2.0. `top_trades.csv` lists the 10 best descending and 10 worst ascending by
  net R, ties by entry time, with rank, side, symbol, direction, entry/exit times, exit reason,
  net R and hold hours. Small samples may appear on both sides. "Decay and extreme trades"
  reports the slope, total net R, net R without the 10 best and their share of total net R;
  the share is unavailable when total net R <= 0.

UI warning labels: "more than 4 swept settings", "entries not better than chance" and
"returns falling over time".

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

## Walk-forward (V2.4d item 6)

The runner defaults to calendar-month windows in UTC: `train_months = 24`,
`test_months = 6`, `step_months = test_months`. All lengths are positive integers;
step shorter than test is refused (overlapping OOS would double count). Longer
steps leave gaps. `walk_forward = "anchored" | "rolling"` and `--walk-forward`
enable this saved-development-trade diagnostic; it never loads hold-out trades.
Anchored training grows from the first full development month; rolling training
uses exactly train_months. The first test starts after train_months. All starts
are the first of a UTC month; skip an initial partial month. Keep the last partial
test window, clipped to the inclusive development end. A fractional calendar month
is elapsed UTC time divided by that month's length (including leap days).

A trade belongs to the window in which it entered. For picking, include only
training entries with exit strictly before the training end. A test entry keeps
its entire saved outcome even if it exits after its test window; do not force-close
it or move it to another window. Saved development runs supply these outcomes;
no hold-out data is loaded. This diagnostic stitches independently saved variant
trades; it does not rerun or reset indicators, or simulate position handovers.
Pick maximum training net R, including zero for a variant without trades; ties
keep original variant order, including when all variants are nonpositive.

`walk_forward.csv` includes window number, train/test periods (end exclusive),
picked and normally chosen variant, train/test net R, net R per month, window
WFE (test rate / train rate), trades and test max DD R (existing scorecard).
Window WFE is n/a when train net R <= 0. Overall WFE is mean test R/month /
mean train R/month over only windows with positive training net R; exclude the
other windows from both means. All test windows still enter the chained scorecard
and positive-window share (strict test net R > 0). Report pick changes across
adjacent windows as a count and a share of transitions (n/a with fewer than two).
Chained net R/month divides total OOS net R by total actual test months, excluding
gaps. No windows yields an empty table and an explanatory reason.

`walk_forward_study = true` enables anchored diagnostics when no mode is supplied
and repeats the same saved-trade analysis for train lengths (12, 24, 36) crossed
with test lengths (3, 6, 12), step = test length, retaining the selected mode.
`walk_forward_study.csv` and the report show overall WFE, chained net R/month,
positive-window share, window count and any no-window reason. These lengths are
diagnostics, not a new selection search. Selection, hold-out execution, trial log,
DSR and research identity remain unchanged.

Compatibility: explicit 12/12 monthly windows reproduce the former yearly picks
and numbers on full calendar years. The legacy year API and grids explicitly
using `train_years` retain the following original semantics; do not combine
train_years with month options. New grids should use months.

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
## Job queue

Spec: ROADMAP V2.6, build order step 1 (V2.6a). The persistent Python queue runs
heavy repository tools without AI calls. It does not change trading rules or defaults.

```console
python -m backtester.tools.queue add --name orb --priority 2 -- backtester.tools.research research/grids/orb.toml --workers 1
python -m backtester.tools.queue add-grid research/grids/orb.toml --dev-only
python -m backtester.tools.queue run --workers 8 --max-temp 85 --resume-temp 80 --poll 10
python -m backtester.tools.queue run --drain
python -m backtester.tools.queue status --json
python -m backtester.tools.queue cancel JOB_ID
python -m backtester.tools.queue retry JOB_ID
python -m backtester.tools.queue stop
python -m backtester.tools.queue clean --done-older-than 30
```

`add-grid` queues the research pipeline (`backtester.tools.research_pipeline <toml>`, see
Pipeline below; job name `pipeline <grid>`); `--dev-only` is accepted and changes nothing
(the pipeline is always development only). `add-grid --retest` queues the bare runner
(`tools.research <toml> --workers 1 --retest`): the one-time MT5 test is CLI only and not part
of the pipeline. `add` preserves the supplied argument list, accepts `--max-attempts`
(default 2), and only accepts module names below `backtester.`. Duplicate pending/running
argument lists (same cwd) produce a warning. Commands use the current Python interpreter, no
shell, and by default the repository root as cwd. `add` and `add-grid` take
`--cwd <lane name or path>`: a job runs in the V2 root (default) or in a registered lane
worktree (see Lanes below); any other folder is refused.

Files live under the anchored `backtester.paths.RESULTS_DIR/queue`: `jobs/<id>.json`,
`logs/<id>.log` (combined child output, appended across retries), `runner.log`,
`runner.lock` (PID), `runner.guard` (OS exclusive lock), `stop`, and `status.json`.
Job and status JSON files use unique temporary files and atomic replacement. Reads and
replacement retry Windows permission/sharing errors for up to five seconds. Stored job
log paths are relative to the results folder; readers resolve them to absolute paths. Job changes
use per-job sidecar locks; job order is priority descending, then sortable UTC ID ascending.
Status includes counts, running elapsed seconds, CPU reading/warning, pause state, and
`broken` filenames (invalid job records are skipped with one warning per file per queue
instance; direct lookup gives a clear error). The guard lock determines runner liveness,
not its PID. When the guard is free, sensor/pause data is historical (`last_seen`), not current.

One runner owns the queue through the OS byte lock. A stale PID file can be taken over.
Before spawning, a job is saved as running with a `starting` timestamp, no PID and the
attempt counted; its PID and process identity are saved immediately after spawning.
A running record without a PID is recovered as a dead attempt. A failed PID save terminates
and waits for the launched child before propagating the failure. A forced OS kill between
process creation and PID persistence can still leave an unidentified child: durable intent
counts the attempt but cannot guarantee exactly-once execution in that window.
Nonzero exits retry up to the limit, then fail. On restart, dead or reused child
PIDs return to pending, or fail if attempts are exhausted. A surviving child with matching
process creation time is monitored without being launched again; after it exits, its
unknown exit result consumes that attempt and follows the same retry limit. If identity
cannot be verified, it is treated as dead. Ctrl+C and `stop` stop new launches and drain
running children. Each runner records its last release time in `runner.release.json`.
At startup, only a stop flag older than that release is stale and removed. A newer flag
(or any flag with no recorded release) is honored immediately and logged; no new jobs start.
`clean` removes completed job records, logs and their per-job locks. Without `--drain`,
the runner waits for new jobs indefinitely. `cancel` kills the child process tree and marks
the job cancelled; `retry` resets attempts for a failed/cancelled job once its child exits.

Install LibreHardwareMonitor and enable its **Remote Web Server**. The default sensor URL
is `http://localhost:8085/data.json`, configurable with `--sensor-url` (2-second timeout).
The guard takes the highest CPU Package / Tctl / Tdie / Core Max temperature. At 85 °C
it holds new jobs until 80 °C; existing jobs continue. An unreadable sensor clears the
pause and allows work, records one warning per outage in the runner log, and exposes it
in status until readings return. No running job is killed for temperature.

Using the existing Telegram configuration, the runner sends only final job failures,
continuous temperature holds of pending jobs longer than 30 minutes (once per pause),
and runner crashes (which are re-raised). Missing configuration skips sends silently;
send errors are logged without configuration or exception details.

Concurrent writer audit: trial-log appends hold `.locks/trials.jsonl.lock` using Windows
`msvcrt.locking` / POSIX `flock`, with a 30-second acquisition timeout. Automatically
named run folders and development publication reserve folders using atomic `mkdir`
with collision retries. Daily series use locks and unique temporary files under
`.locks/series/<variant-relative-path>/`, with atomic replacement into the variant folder;
their trial-link appends also take the trial-log lock.
Each grid holds `.locks/research/<grid-id>.lock` across its resume state and report writes
(the same 30-second lock timeout), so two processes cannot modify one grid concurrently.
All these locks live below the results folder in `.locks/`, outside listed research, run
and variant folders; queue locks remain inside `queue/`. Results listings require report
files (or use explicit filename patterns), so the central lock directory is not a result.

**Do not queue two jobs with the same destination.** Grid locking protects `research.json`,
variant and sensitivity folders, scorecards, significance, monkey and Bayes reports and
`report.md` resume state; overlapping long runs of the same grid can time out on the lock.
Preset publication, Monte Carlo default
destinations (`summary.json`, `report.html`), golden `--write` fixtures/manifest and standalone
strategy profile destinations (`profile.json`, `profile.md`) are also shared writers;
their destination isolation is the caller's responsibility in this step. Different argv
can still target the same destination; the duplicate-argv warning is advisory only.

### Job folder (cwd) and lane jobs (V2.6 step 3)

`Job.cwd` is `None` (the V2 root, the default; also every job file written before V2.6 step 3)
or the absolute path of a registered lane worktree. `Queue.add(argv, ..., cwd=None)` accepts
a lane name or path (or the V2 root, stored as `None`) and raises `ValueError` for any other
folder; `Queue(root, home=HOME_DIR)` knows the V2 root and reads its `lanes.json`. The runner
checks the registry again when it starts a job: a job whose lane was removed meanwhile fails
at once (exit code -1, reason in the job log, no retry). A lane job runs with
`BACKTESTER_HOME` = the V2 root (data, results and the queue stay shared; `paths.py` reads it)
and with the lane's `src` first on `PYTHONPATH`, so it imports the lane's strategy code and not
the V2 install. The rest of the environment is unchanged; default jobs get no environment change.

## Pipeline

Spec: ROADMAP V2.6 step 3 (accepted by the user 2026-10-26). One resumable command per grid
fills a research card without AI calls and without computing again anything the runner
already writes:

```console
python -m backtester.tools.research_pipeline research/grids/orb.toml
python -m backtester.tools.queue add-grid research/grids/orb.toml      # the same, in the queue
```

| Step | What it does |
|---|---|
| `research` | `run_research(grid, workers=1, retest=False, dev_only=True)`: development period only, never a retest, the test period stays unspent. Writes everything the card reads from the research folder (below). |
| `monte_carlo` | `tools/monte_carlo --run <chosen dev run> --results-dir <results> --out <results>/monte_carlo/<dev run> --light`: the light run (rule set by the user, 2026-10-27): no kind D random paths and no matched monkeys (the runner's `monkeys.json` already covers the card's monkey check), everything else at the tool's defaults (1000 runs, seed 42, block bootstrap). The card reads only kind A from it, so its numbers equal a full run's. `summary.json` records `"light": true`; the Results page treats a light report as missing, so its **Full Monte Carlo** button runs the full one (which replaces it). Measured 2026-10-27 on one US500 year: matched monkeys 432 s, kind D 183 s, all the rest 3 s. This is where `ui/research_model.py` reads it. Not run (step done, with a note) when that `summary.json` already exists (for example from the Results page button) or when no variant was ranked. |
| `card_inputs` | read-only: lists which card input files exist / are missing, the stability status and the chosen variant's flags. Computes nothing. |

What the runner already writes and the pipeline reuses (in `results/research/<id>/` unless
noted): `profile.json` (strategy profile / regime breakdown of the chosen development run, via
`strategy_profile.research_results`), `research.json` -> `sensitivity` and `sensitivity.csv`
(parameter stability, status gentle / sharp), the `flags` column of `variants.csv` (scorecard
flags plus the significance, monkey and Bayes flags of the chosen variant), `significance.json`
(Reality Check, PBO, effective trials), `bayes.json`, `skill_bounds.json`, `monkeys.json`,
`grid.csv`, `walk_forward.csv` (when the grid asks for it) and
`<results>/<dev run>/drawdown_bounds.json`. Only the Monte Carlo summary was missing, so it is
the only new computation. A grid with `sensitivity = false` or `monkeys = false` has no such
file (listed as missing, not an error).

### pipeline.json

`results/research/<id>/pipeline.json` (`<id>` = the runner's grid folder, `grid_id`), written
atomically before and after every step:

```json
{
  "version": 1,
  "grid": "research/grids/orb.toml",
  "id": "orb_ab12cd34",
  "created": "2026-10-26T12:00:00+00:00",
  "updated": "2026-10-26T12:41:00+00:00",
  "state": "running",
  "current": "monte_carlo",
  "steps": [
    {"name": "research", "state": "done", "started": "...", "ended": "...", "error": null,
     "note": "development done; the test run was not started (--dev-only)"},
    {"name": "monte_carlo", "state": "running", "started": "...", "ended": null,
     "error": null, "note": null},
    {"name": "card_inputs", "state": "pending", "started": null, "ended": null,
     "error": null, "note": null}
  ],
  "chosen": {"id": "v003", "dev_run": "20261026-120000_US500-NAS100"},
  "monte_carlo": {"kind": "monte_carlo --run --light (kinds A-C, tool defaults; no kind D, no monkeys)",
                  "light": true, "runs": 1000, "paths": 0, "seed": 42,
                  "out": "monte_carlo/20261026-120000_US500-NAS100"},
  "inputs": null
}
```

Step `state` is `pending | running | done | failed`; `error` is `"<ExceptionType>: <text>"`
(at most 2000 characters). The overall `state` is `failed` when any step failed, `done` when
all are done, `running` when one started, else `pending`; `current` is the running step. After
`card_inputs`, `inputs` is `{"present": [...], "missing": [...], "stability": "gentle" |
"sharp" | null, "flags": [...]}`. `chosen` is null when no variant had enough trades (Monte
Carlo is then skipped). A failed step stops the pipeline (later steps stay `pending`) and the
command exits 1. A rerun skips `done` steps and runs `failed`, `running` (killed process) and
`pending` steps again, so a crash, Ctrl+C or a queue restart (job retry) continues where it
stopped; the research runner itself resumes per variant. Exit codes: 0 done, 1 a step failed
or another process runs this grid's pipeline (`.locks/pipeline/<id>.lock`), 2 grid file error
(no `pipeline.json`, the folder is unknown). A `running` state whose queue job was cancelled or
failed is stale (a killed process cannot update the file): show the job's state then.

Functions for readers (the Research card): `research_pipeline.research_folder(grid, results_dir)`
(grid file -> its folder), `read_state(folder) -> dict | None` (None before the first run or for
a broken file) and `progress(state) -> str`: `"queued"` (no state, or all pending),
`"step 2 of 3: monte_carlo"`, `"done"`, `"failed: monte_carlo: <error>"`. The folder (and so
`pipeline.json`) exists only once the research step has started: treat a missing state as
queued while a pipeline job for the grid is pending in the queue. To queue a grid from code
use `tools.queue.add_grid(queue, toml, cwd=None) -> Job` (what `add-grid` calls; job name
`pipeline <grid stem>`, argv `["backtester.tools.research_pipeline", "<toml>"]`).

### Queue panel (Research page)

The Research page shows the queue above the cards (`ui/queue_panel.py`, `ui/queue_model.py`):
key strip (pending / running / done / failed, CPU temperature or "no sensor", paused, runner
alive), **Start runner** (a detached `queue run --workers 8` that keeps running after the page
closes; refused while a runner is alive; user 2026-10-26), **Stop** (graceful), per job
**Cancel** / **Retry**, **Queue a grid** (`research/grids/*.toml` -> the development-only
pipeline; the one-time MT5 test stays CLI only, user 2026-10-26). Running, pending and failed
jobs are listed; finished and cancelled ones sit in a closed "Finished (N)" section. Every card
of a grid shows its pipeline state (queued / step x of n / done / failed + error). Refresh every
5 s while the page is open.

## Lanes

Spec: ROADMAP V2.6 step 3, decision of the user 2026-10-26: parallel strategy work in git
worktrees next to V2, `tools/lanes.py`.

```console
python -m backtester.tools.lanes create <name> [--existing]
python -m backtester.tools.lanes list
python -m backtester.tools.lanes check <name>
python -m backtester.tools.lanes remove <name> [--force]
```

- **create** runs `git worktree add <V2 parent>/bt-lane-<name> -b lane/<name>` from the
  current commit and registers the lane in `lanes.json` in the V2 root (git-ignored; entries
  `name`, `path`, `branch`, `base_commit`, `created`). Nothing from `data/` or `results/` is
  copied: lane jobs run with `BACKTESTER_HOME` = the V2 root (Job queue above). Names are
  `[a-z0-9_]+`; a name that is an existing folder under `src/backtester/strategy/` is refused
  unless `--existing`. A registered name, an existing target folder or an existing branch
  `lane/<name>` is refused (no half state).
- **check** compares the lane's working tree with its base commit (committed, staged, edited
  and untracked files; a rename counts as delete + add). Allowed: `src/backtester/strategy/<name>/`,
  `docs/strategy-<name>.md`, `tests/strategy/<name>/`, `research/grids/<name>*.toml`. Anything
  else prints the files and exits 1: shared code (engine, detectors, risk, ...) is changed by
  Opus, and the `strategy/registry.py` entry is merged by Opus.
- **list** prints per lane: name, path, branch, ahead / behind (commits of the lane branch not
  in the V2 HEAD / commits of the V2 HEAD not in the lane), dirty yes / no, check result.
  `lanes.list_lanes(root=None) -> list[dict]` gives the same as data (`ahead`, `behind`,
  `dirty`, `check_ok`, `offending`, `missing`).
- **remove** removes the worktree and the registry entry. Refuses uncommitted changes
  (tracked or untracked) and commits not in the V2 HEAD unless `--force`. The branch is never
  deleted (a merged lane's branch can be deleted by hand). A lane whose folder is gone is
  pruned and unregistered.

Queue use: `queue add --cwd <name> -- backtester.tools.research_pipeline research/grids/<name>.toml`
runs in the lane. None of these commands switches the branch checked out in the V2 root.
