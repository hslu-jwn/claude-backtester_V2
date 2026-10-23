# Research runner and Research page (ROADMAP 6.1 + 6.2)

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
Each sub-grid accepts `name`, `base`, and `grid`; its base overrides the top-level base.
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
