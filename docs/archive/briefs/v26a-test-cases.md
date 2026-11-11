# V2.6a test cases (written before implementation)

- JSON job round trip; atomic replacement leaves no temporary file; reject unsafe modules.
- Priority descending, ID ascending; worker capacity; successful exit and bounded retries.
- Dead/reused PID recovery; surviving child monitored; exhausted recovery fails.
- Runner lock: stale takeover, live refusal, simultaneous acquisition has one winner.
- Stop drains children; pending/running cancellation; retry resets attempts; cancellation
  and runner updates serialize under a per-job lock.
- LHM CPU tree: Package/Tctl/Tdie/Core Max, degree symbol, comma decimal, unrelated GPU
  ignored, missing sensors, timeout; hysteresis 85/83/80; unreadable clears pause and warns once.
- Fake Telegram: final failure, continuously held pending jobs for 30 minutes, crash,
  missing config and failed sender; no normal-completion notification.
- Four processes append 200 trial records each: 800 complete JSON lines.
- Concurrent run-folder allocation and development publishing reserve distinct folders.
- Concurrent daily-series writers leave one complete CSV and no temporary files.
- CLI add/grid/status/cancel/retry/stop/clean; duplicate argv warning; UTC times and anchored paths.

Only new/changed tests and tests/analytics run here; Opus reviews and runs the full suite.
