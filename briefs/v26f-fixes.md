# Brief: V2.6 step 8 — fixes from the full check (Opus, 2026-10-27 night)

Your read-only review is saved in `docs/review/v26-full-check.md`. Fix findings **1-6** now,
test-first (a failing test reproducing each scenario before the fix), smallest change that
works. Finding 7 is a decision for the user: do not touch the spread table / costs.
AGENTS.md applies (no commit / push / branch, no lingering processes, never
`src/backtester/live/`, no credentials). The queue runner may be running a real pipeline job
right now: do not touch `results/` or `data/` outside `tmp_path` in tests, and do not run any
tool on real data.

- 1: reset reveal whenever the selected index or the complete trade identity (symbol, entry
  time, direction, index) changes; test with two trades at the same entry time.
- 2: development portfolio diagnostics use only development-period trial records (the
  development-only rule of V2.7, user 2026-10-26); keep N-of-trials accounting as it was if it is
  needed for the deflated Sharpe's trial count, documented in `docs/portfolio.md`.
- 3: cache repair rebuilds only from a persisted inventory of the original input days
  (including days absent before the repair); a rerun on the repaired cache is a no-op. Test:
  the +1 h spill case from the review run twice gives identical files.
- 4: one shared per-symbol mutation lock (`filelock.py`, `results/.locks/` or the cache's lock
  folder) used by the MT5 downloader's day writes and by the repair (capture + publication).
- 5: a pipeline input fingerprint (selection / report controls not in `grid_id`, e.g.
  `min_trades`); a change invalidates the affected steps; the permanent test guard stays.
- 6: the portfolio search identity includes a cache-generation / content fingerprint of the
  members' development candles used for the regime attribution.

Run only your tests (`pytest -q tests/data tests/tools tests/ui tests/analytics > results\pytest_v26f.log 2>&1`)
+ ruff on touched files. Report: files changed, test results, anything left open.
