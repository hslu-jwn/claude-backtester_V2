# Brief: grid merge 2 of 3 — sensitivity, filter twins, scorecard additions

Context: `docs/review/backtest-audit.md` (2026-10-23) › Order 1 lists checklist points that
belong in the research runner. Brief 1 (`docs/archive/briefs/grid-merge-1.md`) is in the working tree and
reviewed: combined grids (`[[grids]]`, families), `tools/research_diagnostics.py`, grid.csv,
breakdowns, shock days. Build on it; spec `docs/research-runner.md`.

## What to build

1. **Scorecard additions** (`analytics/scorecard.py`, used by the runner and by plain backtest
   runs; checklist #15, #16):
   - `se_avg_r`: standard error of the average net R per trade (sample sd / sqrt(n); None
     below 2 trades);
   - `time_in_market`: share of the period's weekday time (Mon-Fri, UTC) with at least one
     position open (union of [entry_time, exit_time) intervals over all symbols);
   - `avg_hold_hours`: mean of exit - entry in hours.
   New keys go at the end of `SCORE_KEYS`; old result files without them still load (missing
   = empty cell).
2. **Parameter sensitivity around the chosen variant** (checklist #9): after selection, every
   numeric grid setting of the chosen variant is moved by -20 %, -10 %, +10 %, +20 % one at a
   time (ints rounded to the nearest valid value, at least one step away from the chosen
   value; a value the config rejects is skipped and named), run on the development period,
   and written to `sensitivity.csv` (setting, change, value, the scorecard, net R as a share
   of the chosen variant's). Report block: "gentle" when every neighbour keeps >= 50 % of the
   chosen net R and stays > 0, else "sharp", listing the settings that fail. Neighbours are
   trials: each goes into the trial log with family `<grid name>-sensitivity` (they do not
   change the selection or the DSR's N of the selection). Resumable like variants
   (`sensitivity/<id>/scorecard.json`). Grid option `sensitivity = false` skips it (default
   true); `--dev-only` runs it.
3. **Filter twins** (checklist #10): a `[[grids]]` table may name `compare_to = "<family>"`.
   Each variant of that family is paired with the variant of `compare_to` that has the same
   values for every setting except the ones this family's `base` sets (no match = listed as
   unmatched). Output `twins.csv` (pair, net R both, difference, trades both) and per family:
   mean net R of the family vs the mean of its matched twins ("lifts the average": yes / no).
4. **Expectation haircut line** (checklist #31) in `report.md` under the chosen variant:
   "Live expectation: 50-75 % of the backtest's average R per trade = <a> to <b> R per trade"
   from the development scorecard (and from the test once run). The 50-75 % range is a
   `ResearchConfig` field with that default.

## Rules

Spec first (`docs/research-runner.md`), then the test-case list at the top of the test file,
tests failing, then code. Selection, the test run, the once-only test guard, the trial log of
the grid variants and the DSR stay exactly as they are; existing tests unchanged except new
columns. Hand-built inputs in tests (as `tests/tools/test_research.py` /
`test_research_merge.py`), no real-data runs. Long runs write to a log file.

Done = full suite green (`pytest -q > results\pytest_gm2.log 2>&1`), `ruff check .` and
`ruff format --check` on changed files clean. Report: files changed, test count, decisions the
spec did not settle, open questions.
