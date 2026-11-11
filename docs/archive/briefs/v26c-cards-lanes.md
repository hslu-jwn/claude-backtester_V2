# Brief: V2.6 step 3 — research pipeline through the queue, queue panel, lanes

Context: ROADMAP › V2.6 build order step 3 (accepted by the user 2026-10-26) and
› V2.5-V2.7 in detail › V2.6 (pipeline per idea step 5, parallel lanes, job queue). V2.6a
built the queue (`jobs/`, `tools/queue.py`, `docs/research-runner.md` › Job queue); V2.5b
the Research cards (`ui/pages/research.py`, `ui/research_model.py`, which already read
Monte Carlo, profile / regime and stability results when their files exist). This step
makes those files appear automatically and lets the user drive the queue from the app.
No trading rule, default or strategy changes.

## A. Research pipeline per grid

`python -m backtester.tools.research_pipeline <grid.toml>`: one resumable command that
1. runs the research runner on the grid, **development period only** (`--dev-only`,
   `--workers 1`), never `--retest`;
2. for the chosen variant, produces every card input the runner does not already write:
   Monte Carlo (default settings; written where `research_model` reads it), the strategy
   profile / regime breakdown, parameter stability, warning flags. First check what the
   runner already writes (profile block, sensitivity, flags) and reuse it; never compute
   the same thing twice;
3. writes `pipeline.json` in the grid's research folder: step names, state per step
   (`pending | running | done | failed`), start / end times, error text; a rerun skips done
   steps (resumable after a crash or a queue restart).
`queue add-grid <toml>` queues this pipeline (instead of the bare runner). The card shows the
pipeline state (queued / step x of n / done / failed + error) next to the existing metrics.

## B. Queue jobs in a lane folder

Jobs get an optional `cwd`: the V2 root (default) or a registered lane worktree (section D);
any other folder is refused. Jobs in a lane run with `BACKTESTER_HOME` = the V2 root, so data
and results are shared (`paths.py` already reads it). `queue add --cwd <lane>`.

## C. Queue panel on the Research page (decisions of the user 2026-10-26)

- Key strip: pending / running / done / failed counts, CPU temperature (or "no sensor"),
  paused yes / no, runner running yes / no (from `status.json` + the runner lock).
- Buttons: **Start runner** (the user allows the app to start it: a detached background
  `queue run --workers 8` that keeps running after the page closes; never a second runner,
  the runner lock decides; reuse the detached-process pattern of `ui/process_job.py` /
  `backtest_job.py`), **Stop** (graceful: finish running jobs), per job **Cancel** / **Retry**.
- **Queue a grid:** dropdown of `research/grids/*.toml`, queues the pipeline (A). The
  one-time MT5 test (`--retest`) is **CLI only** (user): no button, no hidden path.
- Job list (compact rows: name, state chip, elapsed, attempts; a log link opens the job's
  log tail in a `details()`), auto-refresh every 5 s with `dcc.Interval`, only while the page
  is open. Look follows V2.5 (`ui/layout.py` helpers, tokens, tooltips via `info()`).

## D. Lanes in worktrees (decision of the user: next to V2)

`python -m backtester.tools.lanes create <name> | list | check <name> | remove <name>`:
- `create`: `git worktree add <V2 parent>/bt-lane-<name> -b lane/<name>` from the current
  branch; registers it in a git-ignored `lanes.json` in the V2 root (name, path, branch,
  base commit, created); copies nothing from `data/` (shared via `BACKTESTER_HOME`).
- `check <name>`: the lane's diff against its base touches only `src/backtester/strategy/<name>/`,
  `docs/strategy-<name>.md`, `tests/strategy/<name>/`, `research/grids/<name>*.toml`;
  anything else -> exit 1 listing the files (shared code goes through Opus; the
  `strategy/registry.py` entry is merged by Opus).
- `list`: name, path, branch, ahead / behind, dirty yes / no, `check` result.
- `remove <name>`: refuses with uncommitted changes or an unmerged branch unless `--force`;
  removes the worktree and the registry entry; never deletes an unmerged branch.
- Names: `[a-z0-9_]+`, must not collide with an existing strategy unless `--existing`.
Docs: `docs/research-runner.md` › Lanes and › Pipeline; one line in `AGENTS.md` › Team
pointing to `tools/lanes.py` and the allowed paths.

## Answers given up front (Opus, 2026-10-26)

- Tests for lanes use a temporary git repo (`git init` in `tmp_path`); never create a
  worktree or branch in this repository (AGENTS.md: no branches; the dispatcher checks it).
- Tests never start a real runner that outlives the test; the Start button test injects a
  fake spawner; process tests use short-lived children and always clean up.
- No new dependencies. UTC, `backtester.paths`, the V2.6a file locks.
- Monte Carlo defaults: the tool's own defaults (do not change them); kind and runs recorded
  in `pipeline.json`.
- Keep ids used by existing callbacks / tests of the Research page.

## Rules

AGENTS.md (no commit / push / branch, no lingering processes, never `src/backtester/live/`,
no credentials). Test-case list first (`briefs/v26c-test-cases.md`), then tests, then code.
Run only your tests (`pytest -q tests/jobs tests/tools tests/ui > results\pytest_v26c.log 2>&1`;
the tools tests take a few minutes) + ruff on touched files. Opus runs the full suite and the
golden check. Report: files changed, test results, what the runner already produced (A.2),
open questions.
