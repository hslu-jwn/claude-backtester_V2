# Brief: grid merge 3 of 3 — walk-forward, gap-bucket study, old sweeps as grid files, archive removed

Context: briefs 1 and 2 (`briefs/grid-merge-1.md`, `-2.md`) brought combined grids,
diagnostics, sensitivity and filter twins into the research runner (`tools/research.py`,
`research_grid.py`, `research_diagnostics.py`, spec `docs/research-runner.md`). This brief
finishes ROADMAP V2.4's grid-tool merge (decisions of the user, 2026-10-23: walk-forward as an
option, the gap-bucket study as its own tool, the archive deleted once reproduced).

## What to build

1. **Walk-forward option** (`--walk-forward`, or grid option `walk_forward = "anchored" |
   "rolling"` with `train_years`): uses the development trades already stored per variant (no
   new backtest runs) and `analytics/walk_forward.py` (yearly windows, pick = max net R on the
   train years). Output `walk_forward.csv` (test year, picked variant, its net R in that year,
   the default / chosen variant's net R in that year) and a report block with the chained
   out-of-sample scorecard ("walk-forward efficiency": chained OOS net R per year / mean
   in-sample net R per year of the picks). Development period only: the test period stays
   untouched.
2. **Gap-bucket study** out of `tools/gap_momentum_grid.py` into
   `tools/gap_bucket_study.py` (same output `gap_buckets.csv`, same analytics in
   `analytics/gap_buckets.py`), with its tests moved; like the other `*_study.py` tools.
3. **Old sweeps as grid files** in `research/grids/`: one file per archived sweep, using
   `[[grids]]` families where the old tool combined sweeps:
   `orb.toml` (base grid + filter variants with `compare_to`; volume twins as a family),
   `gap_fade.toml`, `no_wick.toml`, `trend_following.toml` (one family per signal),
   `ny_index_sweep.toml` (the sweep-rule variants), `ny_index_volume.toml` (volume A/B),
   `gap_momentum_index.toml`, `gap_momentum_fx.toml`. Each file's header comment names the old
   tool and its default command. Grid-only options with no runner equivalent (e.g. `--source`,
   `--spread-table`, start / end) are listed in the header as "not carried over" with the reason.
4. **Reproduction check** before deleting: run the old tool and the runner (`--dev-only
   --results-dir results\gm3_check`) on the same 2 variants for strategy 6 (NAS100, first
   cached day to 2021-09-13, `--no-shocks`) and strategy 4 (XAUUSD, 2 trend variants) and
   compare trades and net R per variant. They must be identical; if not, find and report the
   cause, do not delete anything. Output to log files (`> results\gm3_*.log 2>&1`).
5. **Delete** `tools/archive/` (all files, README), `tools/gap_momentum_grid.py` after its
   study moved, `tests/tools/archive/`, `tests/tools/test_gap_momentum_grid.py` (except the
   moved study tests), and `tools/grid_common.py` if nothing else imports it. Update every
   mention (`AGENTS.md` › Commands / Layout, `docs/research-runner.md`, `docs/ARCHITECTURE.md`,
   strategy specs that cite an archived command) to the runner command with the grid file.

## Rules

Spec first, test-case list, failing tests, then code. Selection, the test run and its guard,
the trial log and the DSR stay unchanged. Never edit `src/backtester/live/`. Long runs to log
files.

Done = full suite green (`pytest -q > results\pytest_gm3.log 2>&1`), `ruff check .` clean,
`git grep -n "tools.archive\|gap_momentum_grid\|grid_common"` empty outside `docs/archive/`
and `results/`. Report: files changed / deleted, test count, the reproduction numbers (old vs
new per variant), decisions the spec did not settle, open questions.
