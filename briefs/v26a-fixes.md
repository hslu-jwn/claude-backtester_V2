# Brief: V2.6a fixes after review (Opus, 2026-10-26)

Your V2.6a job queue (`briefs/v26a-job-queue.md`) was reviewed (Sonnet) and checked by Opus.
Fix these in `src/backtester/jobs/` and `src/backtester/tools/queue.py`, test-first (a failing
test for each defect before the fix). Same rules as the V2.6a brief (AGENTS.md; no lingering
processes; run only `pytest -q tests/jobs tests/analytics > results\pytest_v26a_fix.log 2>&1`;
ruff on touched files).

## Defects

1. **Windows replace race (high, reproduced by Opus):** `os.replace(tmp, target)` raises
   `PermissionError` (winerror 5) while another process has `target` open for reading. The CLI
   (`status`, `add`, `jobs()`) reads job files and `status.json` without a lock while the
   runner writes them every poll -> the runner raises, sends the crash Telegram and dies.
   Fix: `atomic_json` retries `os.replace` on `PermissionError` with a short backoff (up to
   ~5 s total, then raise); readers retry an open / JSON read on `PermissionError` the same
   way. Test: a reader process holding the file open in a loop while the writer replaces it
   many times -> no exception, every read is valid JSON.
2. **Runner lock refuses after PID reuse (medium):** `RunnerLock` already holds the exclusive
   `runner.guard` byte lock, so no runner can be alive; the extra `process_identity(pid)`
   check (queue.py ~293) only refuses falsely when Windows reused the PID. Drop that check
   (the byte lock is the truth). Test: lock file with the PID of a live unrelated process and
   no guard held -> the runner starts.
3. **Crash between `Popen` and `save(running)` (medium):** a runner death there leaves an
   orphan child and a `pending` job -> it runs twice. Fix: save the job as `running` with
   `pid=None` and a `starting` timestamp *before* `Popen`, then the PID right after; recovery
   treats `running` + no PID as dead (attempt counted, back to pending). Test with an injected
   failure between the two steps.
4. **One bad job file stops the queue (low-medium):** bad JSON or an unknown key in a job file
   makes `Queue.get` raise and the runner dies in `recover` / `tick`. Fix: `jobs()` skips such
   files, logs one warning per file and lists them in `status` (`broken: [...]`); `get(id)` of
   a broken file gives a clear error for the CLI. Test.
5. **Stale status (low):** when no runner holds the guard, `status` says `runner: not running`
   and does not report `paused` / temperature from an old `status.json` as current (show it as
   `last seen <time>`).

## Minor (do them too)

- `clean` also deletes the job's `<id>.lock`.
- A `stop` flag written just before a runner starts must not be deleted silently: on start,
  an existing stop flag older than the runner lock's last release is stale and removed, a
  newer one makes the runner exit at once with a message. Keep it simple; document it.
- Use `QueueConfig.sensor_timeout` in `read_temperature` (now unused); also catch
  `http.client.HTTPException`.
- Store the job `log` path relative to the results folder (no absolute paths with the user
  name in job files); resolve it when reading.
- Move `file_lock` (used by `analytics/trial_log.py`, `tools/research.py`,
  `tools/research_series.py`) into a neutral module `src/backtester/filelock.py` so
  `analytics/` does not import from `jobs/`; `jobs/storage.py` re-uses it.
- Tests: cancel of a real short-lived child that itself starts a grandchild (both gone after
  `cancel`, use a child that sleeps <= 30 s and always clean up in a `finally`); the CLI
  `status` while a runner writes (defect 1).

Report: files changed, test results, anything you could not fix.

## Full-suite failures (Opus ran it: 39 failed)

6. **Lock files inside listed folders:** the per-grid lock `results/research/<rid>.lock` sits
   next to the grid folders; 31 research tests (and any code that lists `results/research/`,
   e.g. the Research page / cards loader) now see an extra entry. Put every lock file in one
   place outside listed folders: `results/.locks/` (e.g. `results/.locks/research/<rid>.lock`,
   `results/.locks/trials.jsonl.lock`, series locks keyed by the variant folder's relative
   path). Check every lister of `results/`, `results/research/`, run folders and variant folders
   (grep for `iterdir`, `glob`) so no lock or temp file ever shows up. The queue's own lock
   files stay in `results/queue/`.
7. **`tests/test_layers.py`:** register `jobs` (and the new neutral `filelock` module) in the
   layer map (`LAYERS`, `UTIL` or `APP`, whichever fits: `filelock` is a utility with no
   backtester imports; `jobs` is app-level, used by `tools/`), and keep the import rules
   (`analytics/` must not import `jobs/`; it may import `filelock`).

After the fixes run, besides your tests: `pytest -q tests/test_layers.py tests/tools > results\pytest_v26a_fix_tools.log 2>&1`
(the research tests take a few minutes).
