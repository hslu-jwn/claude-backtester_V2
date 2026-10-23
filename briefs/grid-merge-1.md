# Brief: grid merge 1 of 3 — combined grids, breakdowns, grid robustness, shock days

Context: ROADMAP V2.4 "merge the archived grid tools into the research runner" (accepted by the
user 2026-10-23, `docs/review/backtest-audit.md` › Order 1). The research runner is
`src/backtester/tools/research.py` + `tools/research_grid.py`, spec `docs/research-runner.md`.
The archived per-strategy tools in `src/backtester/tools/archive/` (and
`tools/gap_momentum_grid.py`) can do four things the runner cannot. Port them into the runner,
reusing the existing helpers (`analytics/robustness.py`, `analytics/metrics.py` `split` /
`by_period`, `tools/grid_common.py`); do not copy code from the archive files.

## What to build

A. **Grid robustness** over the development variants: share of profitable variants, mean,
   st.dev, mean - 1 sd, robust flag (>= 70 %), and the plateau variant of the neighbour-smoothed
   net R (`robustness.grid_stats`, `smooth_series` / `smooth_grid`, `plateau_index` /
   `plateau_cell`). Per family (D) and over all variants. Output `grid.csv` + a block in
   `report.md`. A family with 1 or 2 swept settings gets the plateau along its axes; with more
   settings report share / mean / sd only (say so in the spec).
B. **Shock days**: net R with and without the shock days (`robustness.shock_dates`,
   `shock_report`) for the chosen variant's development run and its test run; columns on
   `variants.csv` for every variant only if cheap (the daily bars are read once per symbol).
   Grid option `shocks = false` to skip (default true).
C. **Breakdowns** for the chosen variant (development and test): per symbol, per market class
   (the classes of `archive/orb_grid.py`: move the class map to a shared place, e.g.
   `analytics/` or `tools/grid_common.py`, and give every one of the 26 cached symbols a class)
   and per year. Files `breakdown_symbols.csv`, `breakdown_classes.csv`, `by_year.csv`.
D. **Combined grids**: a grid file may hold several sub-grids as `[[grids]]` tables (each with
   its own optional `name`, `base` overrides and `grid` product); the variants are the union,
   ids stay stable (`v0000` ... in file order), duplicates (same resolved settings) run once and
   are named in the report. The old single `[grid]` form keeps working unchanged. A variant's
   family = its sub-grid name. This replaces e.g. ORB's "base grid + one-change filter variants".

## Rules

- Spec first: update `docs/research-runner.md` (grid file, output) before the code; write the
  test-case list at the top of the new test file, then the tests (they must fail), then the code.
- No change to how variants are run, selected or tested, nor to the trial log or DSR: the
  existing research tests and `research/grids/check_*.toml` results stay identical.
- Small hand-built inputs in tests (fake trade lists / fake sources as in
  `tests/tools/test_research.py`); no real-data runs in tests.
- Long runs write to a log file (`> results\x.log 2>&1`).

Done = full suite green (`pytest -q > results\pytest_gm1.log 2>&1`), `ruff check .` and
`ruff format --check` on changed files clean. Report: files changed, test count, the
decisions you took that the spec did not settle, open questions.
