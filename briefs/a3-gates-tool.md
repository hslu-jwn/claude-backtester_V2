# Brief: A3, one gates tool driven by a `[gates]` table, test-first

Read `AGENTS.md` first; hard limits apply (no commits, no branches, no servers, no `live/`, no `.env`).
You work in the worktree `bt-lane-a3_gates`. No backtest or research run. If a rule is unclear, stop and
report it with the spec line; never guess a statistical rule.

## Why

Every strategy so far got its own gates tool (`tools/alternating_path_gates.py`, `timed_hold_gates.py`,
`h1_shock_gates.py`, `us_close_de_open_gates.py`, 1,312 lines) and the circular block bootstrap is copied
in several places (review A3, `knowledge/reviews/2026-11-11-fable-review.md` lines 146-148 and 275).
Goal of this step: ONE generic tool a new strategy uses by adding a `[gates]` table to its grid file, plus
ONE block bootstrap. The old tools stay (they are pinned by tests and past results); do not delete them.

## Files you may create / change (nothing else)

- `src/backtester/analytics/bootstrap.py` (add), `tests/analytics/test_block_bootstrap.py` (new)
- `src/backtester/tools/gates.py` (new), `tests/tools/test_gates.py` (new)
- `src/backtester/tools/alternating_path_gates.py`, `timed_hold_gates.py`, `us_close_de_open_gates.py`:
  ONLY to import the moved bootstrap helpers instead of their own copies (re-export the old names so all
  existing imports keep working). Their numbers must not change.
- `src/backtester/tools/research_grid.py` (+ its test file `tests/tools/test_research_grid.py`): accept a
  top-level `gates` table, validate nothing in it, and keep it OUT of the research id / version hash.
- `research/grids/us_close_de_open.toml`: append the `[gates]` table below (equivalence target).
- `docs/research-runner.md`: one new section "Gates table (one gates tool)".

## Part 1: one block bootstrap (`analytics/bootstrap.py`)

Move `block_indices(n, block, starts)` and `block_bootstrap(x, block, resamples, seed)` from
`alternating_path_gates.py`, and add `block_means(x, block, resamples, rng)` = the per-resample circular
block means used by `timed_hold_gates.difference_bootstrap` and `us_close_de_open_gates.control_difference`
(same draw order: per resample, per series `rng.integers(0, len(x), size=ceil(len(x)/block))`). Callers keep
their exact RNG call order. `date_cluster_bootstrap` (seed 13) and `h1_shock_gates`' clustered bootstrap are
different algorithms: leave them.
**Test first:** pin the current outputs (compute them from the current code before you move anything and
write the literal numbers into the test): `block_bootstrap` on a fixed array (seed 2026110, 10,000
resamples), `difference_bootstrap` and `control_difference` on small hand-built trade lists. After the move
the same tests pass unchanged, and `tests/tools/test_*gates*.py` stay green.

## Part 2: generic tool `tools/gates.py`

CLI: `python -m backtester.tools.gates <research folder> [--breadth-folder <folder>] [--skip-integrity]
[--controls N]`. It reads `research.json` -> `grid_file` -> the `[gates]` table, loads the cells like
`us_close_de_open_gates.load_variants`, writes `gates.json` into the folder and prints one line per cell.
Reuse by import: `timed_hold_gates.variant_report`, `_name`, `BEST_DATES`, `BLOCK`, `RESAMPLES`, `SEED`;
`alternating_path_gates.STRESSES`, `net`, `integrity_failures`; `entry_screen.load_m1`.

`[gates]` keys. **Always applied, no key (answer to the worker's question, 2026-11-12):**
`positive_normal_and_doubled` (net R > 0 at normal costs and every `STRESSES` doubling),
`best_date_removal_positive` (normal and all-doubled), `min_trades` (key required), and the cell's own
bootstrap lower 2.5 % in the falsification rule. **Optional, a missing key = that gate is not part of the
verdict and is reported as `null`:** `halves`, `[gates.control]` (effect_not_drift), `[gates.breadth]`,
`integrity_max_gap` (no_data_integrity_failure), `primary` (without it no cell can advance). `symbol`
only selects trades:

```toml
[gates]
symbol = "GER40"              # trades counted; default: every symbol of the run, pooled
min_trades = 200              # below -> verdict not_enough_evidence (never falsified, never a pass)
halves = "2017-10-08"         # fixed UTC entry-date split, or "midpoint" (period midpoint)
primary = { family = "S", min_ref_return_pct = 0.10, stop_atr = 0.5, exit_time = "09:30" }
integrity_max_gap = 5         # minutes; --skip-integrity -> gate False, skipped_integrity true
[gates.control]               # effect_not_drift, as us_close_de_open_gates.control_difference
family = "C"
match = ["stop_atr", "exit_time"]
[gates.breadth]               # either a second research folder (--breadth-folder) ...
primary = { family = "S", min_ref_return_pct = 0.10, stop_atr = 0.5, exit_time = "08:30" }
symbol = "UK100"
# ... or, without a folder: min_positive = 4 (at least 4 symbols of the run with net R > 0)
```

Gates per signal cell (every cell whose family is not the control family): `positive_normal_and_doubled`,
`positive_both_halves`, `effect_not_drift`, `breadth`, `best_date_removal_positive` (normal and all-doubled),
`min_trades`, `no_data_integrity_failure`. Verdict exactly as `us_close_de_open_gates.evaluate`:
`not_enough_evidence` if min_trades fails; else `falsified` if mean net R <= 0, or the cell's bootstrap
lower 2.5 % <= 0, or `effect_not_drift` is False (when a control is configured); else `advances` only for
the primary cell with every configured gate True; else `rejected`. Control cells: verdict `control`.
Cell settings values compare as numbers when both parse as numbers (0.1 == 0.10), else as strings.

`--controls N` (pipeline controls, review tip 2, `.claude/skills/continue-research/SKILL.md` › Pipeline
controls): for the primary cell, draw N fake signal cells from its matched control cells (same long/short
counts, random distinct entry dates present in both controls, seed 20261112); negative = no drift, positive
= + the minimum detectable edge `2.8 * sd / sqrt(n)` added to each fake trade's `r_net`. Report pass rates of
mean > 0, bootstrap lower > 0, effect_not_drift, and all three, under `controls` in `gates.json`. The
reference is this description (the 2026-11-12 strategy 14 control run: negative 0 % / 200, positive effect gate 69.5 %).

## Equivalence (the acceptance test)

`tests/tools/test_gates.py` builds hand-made trade lists for an S/C grid (reuse the fixtures style of
`tests/tools/test_us_close_de_open_gates.py`) and asserts that `gates.evaluate(...)` with the
strategy-14 `[gates]` table above gives the same verdicts, gates and key numbers (net R, halves,
control difference and lower bounds, breadth) as `us_close_de_open_gates.evaluate(...)` on the same input.
Also test: `halves = "midpoint"`; `min_positive` breadth without a folder; a missing `[gates]` table -> clear
error; `--skip-integrity`; non-primary never advances; 199 trades -> not_enough_evidence; numeric setting
comparison; `--controls` on synthetic trades (negative all-pass rate <= 5 %, positive with a large planted
drift >= 80 %; small N for speed); CLI end-to-end on a tmp research folder writes `gates.json`; the research
id of a grid with and without a `[gates]` table is the same.

## Done =

`python -m pytest -q -p no:cacheprovider -n 8 tests/tools tests/analytics` green and
`python -m ruff check src tests` clean (run from the worktree with
`..\backtester-claude_V2\.venv\Scripts\python.exe`). Module docstrings with the CLI and
`Spec: research-runner.md › Gates table`. Report: files, test results, every number you pinned in Part 1,
any spec question.
