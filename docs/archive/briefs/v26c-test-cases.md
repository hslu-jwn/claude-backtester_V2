# V2.6 step 3: test cases (sections A, B, D; section C is appended by the UI agent)

Written before the tests and the code. Brief: `briefs/v26c-cards-lanes.md`.
Tests: `tests/tools/test_research_pipeline.py` (A), `tests/jobs/test_queue_cwd.py` (B),
`tests/tools/test_lanes.py` (D). The research step, Monte Carlo and every follow-up are stubbed
or injected; no real backtest runs and no process outlives a test.

## A. Research pipeline per grid (`tools/research_pipeline.py`)

| # | Case | Expectation |
|---|---|---|
| A1 | Happy path with stubs | steps `research`, `monte_carlo`, `card_inputs` run in order; `pipeline.json` is in the grid's research folder (`results/research/<id>/`); every step `done` with start / end times; overall state `done`; exit code 0 |
| A2 | Research call arguments | the research function is called with `dev_only=True`, `workers=1`, `retest=False`; the pipeline has no `--retest` option (argparse refuses it) |
| A3 | Monte Carlo call | called once with the chosen variant's development run folder name, the results dir and `results/monte_carlo/<dev_run>` as output (where `research_model` reads it); tool defaults only; kind and runs / paths / seed recorded in `pipeline.json` |
| A4 | Resume skips done steps | pipeline.json with `research` done and `monte_carlo` failed: rerun does not call research again, calls Monte Carlo, ends `done`; the chosen variant comes from pipeline.json |
| A5 | Fully done pipeline rerun | nothing is called; exit 0; state stays `done` |
| A6 | Crash while a step runs | a step left `running` (killed process) is run again on the next call |
| A7 | Research step fails (exception) | step `failed` with the error text, later steps stay `pending`, overall `failed`, exit code 1, pipeline.json written; rerun retries the failed step |
| A8 | Monte Carlo fails (`SystemExit` or exception from the tool) | step `failed` with the text; research step stays `done` |
| A9 | No ranked variant (`status: no_test`, no chosen) | Monte Carlo is not run (done with a note), card_inputs done, overall `done` |
| A10 | Monte Carlo summary already present (e.g. the Results page button) | not computed again; step `done` with a note |
| A11 | Card inputs are reused, not recomputed | the step reads profile / stability / flags files the runner wrote and records present / missing; it calls nothing heavy; missing files are listed, not an error |
| A12 | Grid file errors | missing / invalid grid: exit 2, message on stderr, no pipeline.json |
| A13 | Second pipeline on the same grid at the same time | refused (lock), no second run |
| A14 | pipeline.json format | version, grid, id, state, current step, per-step name / state / started / ended / error / note, chosen, monte_carlo block; atomic write (no `.tmp` left); `read_state` / `progress` helpers give the text the card shows ("queued", "step 2 of 3: monte_carlo", "done", "failed: error") |
| A15 | `research_folder(grid)` | the same folder the runner uses (`grid_id`) |
| A16 | `queue add-grid <toml>` | queues `backtester.tools.research_pipeline <toml>` (no `--workers`, no `--retest`); `--dev-only` is accepted and changes nothing; `--retest` keeps the old bare runner job (CLI-only one-time test) |

## B. Queue jobs in a lane folder

| # | Case | Expectation |
|---|---|---|
| B1 | Default cwd | a job without `cwd` runs in the V2 root, no env override; old job files without a `cwd` field still load |
| B2 | Registered lane accepted | `add(cwd=<lane path>)` and `add(cwd=<lane name>)` store the lane path; the runner starts the child with that cwd |
| B3 | Unregistered folder refused | any other existing folder, a folder next to a lane, a lane path with `..` tricks, and a file path raise `ValueError` |
| B4 | V2 root as cwd | accepted and stored as default (no cwd) |
| B5 | Lane job environment | `BACKTESTER_HOME` = the V2 root; `PYTHONPATH` starts with `<lane>/src` so the lane's code is used; default jobs get no env override |
| B6 | Lane removed after queueing | the runner marks the job failed (exit -1, text in the job log) and does not start anything |
| B7 | `queue add --cwd <lane>` CLI | stores the lane; refusing an unregistered folder exits 1 with a message |
| B8 | Duplicate warning | same argv in a different cwd is not a duplicate |

## D. Lanes (`tools/lanes.py`), temporary git repo only

| # | Case | Expectation |
|---|---|---|
| D1 | create | worktree `<root parent>/bt-lane-<name>` on branch `lane/<name>` from the current HEAD; `lanes.json` entry (name, path, branch, base commit, created); nothing copied from `data/` |
| D2 | create twice / existing path / existing branch | refused with a clear message, no half state |
| D3 | name validation | `[a-z0-9_]+` only: uppercase, dash, dot, slash, space, empty, `..` refused |
| D4 | name collides with an existing strategy folder | refused, accepted with `--existing` |
| D5 | `lanes.json` is git-ignored | listed in `.gitignore` of the repo |
| D6 | check passes | a lane that only changes `src/backtester/strategy/<name>/`, `docs/strategy-<name>.md`, `tests/strategy/<name>/`, `research/grids/<name>*.toml` (committed, uncommitted and untracked) exits 0 |
| D7 | check fails | any other file (e.g. `src/backtester/engine/x.py`, `strategy/registry.py`, another lane's strategy folder, `research/grids/other.toml`) exits 1 and lists exactly those files |
| D8 | list | name, path, branch, ahead / behind of the lane branch against the V2 HEAD, dirty yes / no, check result; a missing worktree folder is shown, not a crash |
| D9 | remove clean merged lane | worktree and registry entry removed, the branch stays |
| D10 | remove refuses dirty lane | uncommitted changes -> refused without `--force`; with `--force` removed |
| D11 | remove refuses unmerged branch | commits not in V2 HEAD -> refused without `--force`; with `--force` the worktree goes, the branch is never deleted |
| D12 | unknown lane | `check` / `remove` of an unknown name: clear error, exit 1 |
| D13 | CLI | `main(["create", ...])`, `list`, `check`, `remove` return the exit codes above |
| D14 | no git side effects in this repo | all tests use `tmp_path` repos with a local user.name / email; none touches the repository the tests run from |

## C. Queue panel on the Research page (`ui/queue_model.py`, `ui/queue_panel.py`, `ui/pages/research.py`)

Tests: `tests/ui/test_queue_panel.py`. A real `Queue` in `tmp_path` (jobs written as files, never run); the
runner is never started: the Start button gets an injected fake spawner, a fake queue records
cancel / retry / stop calls.

| # | Case | Expectation |
|---|---|---|
| C1 | Layout, empty queue | the page renders; key strip shows pending / running / done / failed = 0, "no sensor", paused no, runner no; "No jobs." text; Start enabled, Stop disabled; `qp-interval` is 5000 ms |
| C2 | Layout with jobs | pending, running, done, failed and cancelled jobs each show name, state chip (class per state), elapsed, attempts `n / max`; Cancel only on pending / running, Retry only on failed / cancelled; log tail in a `details` (closed) |
| C3 | Key strip values | counts follow `queue_status`; temperature shows e.g. `63 °C` or "no sensor" when `None`; paused yes / no; runner "yes" / "no" (+ "stopping") |
| C4 | Runner alive | Start disabled, Stop enabled; runner not alive: Start enabled, Stop disabled |
| C5 | Start | calls the injected spawner exactly once with `python -m backtester.tools.queue run --workers 8` in the V2 root; message says started |
| C6 | Start while a runner is alive | the spawner is not called; message says a runner is already running |
| C7 | Start twice quickly | the second click inside the start grace period (runner lock not yet taken) does not spawn again; after the grace period it may |
| C8 | Spawner fails (OSError) | message with the error, no crash, no second spawn counted as started |
| C9 | Real spawner flags | `spawn_detached` passes DETACHED_PROCESS / new process group (Windows) or `start_new_session` (POSIX), stdin / stdout redirected to files, no pipe to the page (tested with a fake `Popen`, nothing is started) |
| C10 | Stop | alive runner: `queue.stop()` called once; no runner alive: not called (a stale stop file would stop the next runner), message says so |
| C11 | Cancel / Retry | call `queue.cancel(id)` / `queue.retry(id)`; a `ValueError` from the queue (wrong state, child still exiting) becomes a message, no crash; an id that is not a job id is refused |
| C12 | Queue a grid | calls `add_grid(queue, toml)` once, without `retest` (and no `dev_only` / `cwd`); a path not in the grid dropdown (arbitrary file, `..`) is refused; no value selected -> message, no call |
| C13 | Duplicate grid | the duplicate warning of `Queue.add` is shown in the message, the job is still queued |
| C14 | No retest anywhere | the panel module and the layout contain no "retest" option (text and ids) |
| C15 | Grid dropdown | lists `research/grids/*.toml` sorted, labelled with the file name; missing folder -> empty options |
| C16 | Log tail | last 20 lines of the job log; a missing log -> "no log yet"; a huge log is read from its end only; non-UTF-8 bytes do not crash |
| C17 | Job order and cap | running first, then pending, failed, cancelled, done (newest first inside a state); at most 50 rows, then "N more" |
| C18 | Elapsed | running: now - started; finished: ended - started; pending: "–"; `h m s` formatting; unparsable timestamps -> "–" |
| C19 | Broken job file | listed in the strip tooltip / message, rest of the list still renders |
| C20 | Card shows pipeline state | `queued`, `step 2 of 3: monte_carlo`, `done`, `failed: monte_carlo: boom` appear on the card of a research row; plain runs and research rows with no `pipeline.json` and no job show no pipeline chip |
| C21 | Pending pipeline job | a pending pipeline job for the grid -> card says "queued", even when `pipeline.json` says done / failed from an earlier run |
| C22 | Cancelled / failed job vs stale running | job cancelled or failed while `pipeline.json` still says running -> card shows the job's state ("job cancelled" / "job failed (exit N)"), not "step x of n" |
| C23 | Running job, normal flow | job running + `pipeline.json` running -> "step x of n: name"; job done + pipeline done -> "done"; pipeline failed (job failed after retries) -> "failed: step: error" |
| C24 | Job to folder mapping | a pipeline job's grid file (relative to the V2 root or the job's lane cwd, absolute, unreadable or invalid grid) maps to the research folder id of `research_folder`; an invalid grid is skipped, never raises; non-pipeline jobs are ignored; several jobs for one grid: the active one wins, else the newest |
| C25 | Layout of the existing page | `rr-cards`, `rr-reload`, `rr-keys`, filters and the callbacks of the existing tests still exist; the new callbacks register without duplicate-output errors |
