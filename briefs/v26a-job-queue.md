# Brief: V2.6a — Job queue, temperature guard, trial-log lock

Context: ROADMAP › V2.6 (build order step 1, accepted by the user 2026-10-26) and › V2.5-V2.7
in detail › V2.6 "Job queue". Plain Python, no AI tokens at run time. The queue runs the
heavy jobs (research runner grids, strategy profiles, golden checks, Monte Carlo) so the
AI lanes, the app and Windows keep room. Nothing here changes a trading rule or a default.

## What to build

New module `src/backtester/jobs/` (queue logic, no Dash / Plotly imports) and CLI
`src/backtester/tools/queue.py`:

1. **Job** = one command line of this repo's Python tools, stored as a JSON file in
   `results/queue/jobs/<id>.json`: `id` (sortable: UTC time + short random), `name`, `argv`
   (list, run as `[sys.executable, "-m", ...]`; only modules under `backtester.` are accepted),
   `priority` (int, default 0; higher first, then oldest first), `state`
   (`pending | running | done | failed | cancelled`), `attempts`, `max_attempts` (default 2),
   `pid`, `started`, `ended`, `exit_code`, `log` (path `results/queue/logs/<id>.log`, stdout +
   stderr of the child). Writes are atomic (write temp file, `os.replace`).
2. **Runner** `python -m backtester.tools.queue run [--workers 8] [--max-temp 85]
   [--resume-temp 80] [--poll 10]`: starts pending jobs up to `--workers` children at once,
   polls, records exit codes (0 -> done; else retried until `max_attempts`, then failed).
   One runner at a time: a lock file `results/queue/runner.lock` with the runner's PID; a
   second runner exits with a clear message unless the PID in the lock is dead (stale lock is
   taken over). Ctrl+C / `stop`: start no new jobs, let running children finish, exit cleanly.
   `--drain` exits when nothing is pending or running (for tests and scripts); without it the
   runner keeps waiting for new jobs.
3. **Resume after a restart / crash:** on start, a job in state `running` whose PID is dead (or
   reused by a non-child: compare the stored start time with the process creation time where
   available, else treat as dead) goes back to `pending` and counts the attempt.
4. **Temperature guard:** read the CPU temperature from LibreHardwareMonitor's built-in web
   server (`http://localhost:8085/data.json`, configurable `--sensor-url`; the user installs
   LHM and enables "Remote Web Server"). Parse the JSON tree; take the highest value among the
   CPU hardware node's temperature sensors whose names contain "Package", "Tctl", "Tdie" or
   "Core Max" (values look like `"72.5 °C"`; tolerate `,` decimals). At or above `--max-temp`:
   start no new jobs (running ones continue) until the reading is at or below
   `--resume-temp` (hysteresis). Sensor unreadable (no LHM, timeout 2 s, no matching sensor):
   keep working, write a warning once to the runner log and into `status` until it reads
   again. Never kill running jobs for temperature.
5. **Telegram** (only these, rule of the user): the runner sends one message when (a) a job
   fails for good, (b) new jobs have been held back by the temperature guard for more than 30
   minutes continuously (once per pause), (c) the runner itself crashes (top-level exception,
   then re-raise). Use `backtester.live.telegram.load_telegram()` + `TelegramClient(config).send(text)`;
   no Telegram config -> skip silently; a send error is logged, never raised. Import only, do
   not edit `src/backtester/live/`. Tests use a fake sender (inject a callable).
6. **CLI subcommands:** `add [--name N] [--priority P] [--max-attempts K] -- <module> <args...>`
   (e.g. `add --name orb -- backtester.tools.research research/grids/orb.toml --workers 1`),
   `add-grid <toml> [--retest/--dev-only passthrough]` (shortcut for the research runner with
   `--workers 1`), `status` (counts per state, running jobs with elapsed time, temperature
   reading or warning, paused yes/no; plus `--json`), `cancel <id>` (pending -> cancelled;
   running -> terminate the child, state cancelled), `retry <id>` (failed / cancelled ->
   pending, attempts reset), `stop` (asks a running runner to stop: a `stop` flag file the
   runner polls), `clean --done-older-than DAYS`.
   The runner's own state for the UI later: `results/queue/status.json` (rewritten every poll).
7. **Trial-log lock:** `analytics/trial_log.append` must be safe when several processes append
   at once: hold an exclusive lock around the write. Use a sidecar lock file
   (`trials.jsonl.lock`) with `msvcrt.locking` on Windows and `fcntl.flock` elsewhere, retry
   with a short sleep up to 30 s, then raise a clear error. One complete line per record, never
   interleaved. Also check every other writer of shared files in `results/` that parallel
   research jobs would hit at the same time (e.g. the research runner's per-grid folders, the
   series files written next to the trial log); list them in your report and lock or separate
   them the same way if two jobs can write the same file.

## Answers given up front (Opus, 2026-10-26)

- Workers default 8 (20 cores; room for AI lanes, the app, Windows). Each research job runs
  with `--workers 1` by default; `add` keeps whatever argv the caller gives.
- Child processes: `subprocess.Popen` with the repo root as cwd, `CREATE_NEW_PROCESS_GROUP` on
  Windows so `cancel` can terminate one child without the runner; output appended to the job's
  log file. No shell, no string commands.
- Job order: priority desc, then id asc. A job never runs twice at once.
- Times in UTC ISO strings. Paths through `backtester.paths` (`RESULTS_DIR`), never relative
  to the current working folder (13.17).
- No new dependencies (`urllib` for the sensor, `psutil` only if it is already installed in the
  venv; otherwise `os.kill(pid, 0)` / `OpenProcess` via `ctypes` for the liveness check).
- No UI in this step (the Research page shows the queue in step 3).
- Telegram text: short, plain, no paths with user names, e.g. `Queue: job orb failed (exit 1,
  2 attempts)`; `Queue: paused 30 min, CPU 88 °C`.

## Rules

AGENTS.md applies (never commit, push, branch; never start a process that outlives your answer
— tests start only short-lived fake children like `python -c "import sys; sys.exit(0)"` and
always wait for them; never edit `src/backtester/live/`; no credentials).
Test-case list first, in `briefs/v26a-test-cases.md`, then tests in `tests/jobs/` and
`tests/analytics/` (or the existing trial-log test file), then code. Cases at least: job file
round trip and atomic write; order by priority then age; workers limit respected; exit 0 ->
done, non-zero -> retry then failed; resume of a `running` job with a dead PID; stale runner
lock taken over, live lock refused; `stop` flag drains cleanly; `cancel` pending and running;
`retry`; only `backtester.` modules accepted; temperature parse (real LHM JSON sample with
`°C`, comma decimal, missing sensor, timeout) and hysteresis (85 pause, 80 resume, readings in
between keep the state); unreadable sensor keeps working + one warning; Telegram on final
failure / 30-min pause (fake clock) / crash, nothing without config; trial-log append from
several processes at once (e.g. 4 processes x 200 lines) gives 800 whole lines.
Run only the new / changed tests (`pytest -q tests/jobs tests/analytics > results\pytest_v26a.log 2>&1`);
ruff check + format on the files you touched. Opus runs the full suite.
Docs: add a section "Job queue" to `docs/research-runner.md` (commands, files, guard, Telegram)
in the same change.

Report: files changed, test results, the list of shared-file writers you found (point 7),
open questions.

## Addendum after the read-only pass (Opus, 2026-10-26 15:30)

Your first pass (results/ai/20261026-152735_codex_task.md) ran read-only by mistake; now
implement. Answers to your questions:

- **Surviving child after a runner crash** (PID alive and identity matches): do not start it
  again; the new runner monitors it until the PID exits, then sets the job back to `pending`
  with the attempt counted (its exit code is unknown; the research runner resumes from its
  own saved progress, so a re-run is cheap). If attempts are exhausted -> `failed`.
- **Sensor unreadable while paused:** clear the pause (keep working) and write the warning.
- **Cancel** terminates the job's whole process tree (Windows: `taskkill /T /F /PID`;
  elsewhere: the process group), so workers it spawned do not survive.

Shared-file writers, scope of this step:
- fix: trial-log lock (point 7); run-ID / run-folder allocation in `runner.py` (atomic
  `mkdir` with retry on collision, also for development publishing); unique temporary files
  in the series writer (`daily.csv.tmp` -> unique name + `os.replace`, under the trial-log
  lock or its own lock). Tests for each with several processes.
- not now (document in `docs/research-runner.md` › Job queue as "do not queue two jobs with
  the same destination"): presets publication, Monte Carlo default destinations, golden
  `--write`, standalone strategy profiles. The queue's `add` warns when a pending / running
  job has exactly the same argv.
- Also test: concurrent runner acquisition (two runners race: exactly one wins), runner vs
  `cancel` updating the same job file (use a per-job lock so no update is lost), exhausted
  attempts during crash recovery.
