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

## Output

`results/research/<id>/`: `research.json` (grid, periods, symbols, variant count, seed, chosen variant, test
status), `variants.csv` (development scorecards), `test.csv` (the test scorecard), `report.md` (short
summary). The chosen variant's development and test runs are also written as normal run folders
(`results/<run-id>/`, so the results page and the chart open them) and the chosen settings as a preset.
Runs are resumable: a finished variant is not run again. Every research run is written to the trial log.

## Research page (app)

- One row per research variant and per plain backtest run in `results/`, scrollable, sortable by every
  column, filter by strategy / symbol / flag.
- Default sort: verdict (green first), then test net R, then development net R.
- Flags shown as small warning badges next to the numbers; a row click opens its results page (and from
  there the chart).
- Command-line runner first, then the page (user, 2026-10-21).
