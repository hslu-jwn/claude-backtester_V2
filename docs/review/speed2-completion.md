# Speed 2 completion report (2026-10-23)

Compared `git show a2fa2b2 --stat` and its changes with
`briefs/phase4-speed-2.md`, steps 4-6. All requested production changes were already
implemented in that commit. No partly implemented or missing production item was
found; no further production changes were needed. The remaining work was verification,
measurement and this report. Acceptance and cross-review remain with Opus/the user.

| Brief item | Status in a2fa2b2 | Evidence |
|---|---|---|
| 4: shared FVG/BOS/ATR/swings | Implemented | `detectors/shared.py` caches events for the same closed view and separates unequal configurations. NY `Frame`, session `SetupTracker` and `ObstacleTracker` use the pool. OB consumes the shared BOS/new swings; breaker shares BOS; BPR shares FVG. Each consumer retains its event order and zone state. |
| 4: incremental sweep cancellation | Implemented | `detectors/sweep.py` maintains the last N non-doji candles, rolling wick extrema and ordered closes in `_BreakoutWindow`; cancellation no longer walks backward through doji runs. Existing differential tests compare with the original backward scan. |
| 5: cheap zone membership keys | Implemented | `zone_key` preserves box value identity, including BPR ranges; `session_zone_key` distinguishes forming sessions even when a data gap finalizes them at the same close. Session setup/journal dictionaries use these keys, usable confluences retain insertion order, and equilibrium membership uses retained object identities. |
| 5: one-pass journal grouping | Implemented | `SessionJournal.records` groups zones and confluences by session once, then preserves session, zone and confluence export ordering. Existing tests compare with the original exporter. |
| 6: selected trend signal + ATR | Implemented | `TrendFollowing._event` updates only the configured signal; `on_candle` continues to update ATR. Existing tests cover all five signals against the all-indicator reference. |
| 6: analytics #12 | Implemented | `daily_net_r` uses a date index and `bisect_left` fallback; accumulation order is unchanged. The same fallback is used by risk `build_days`. |
| 6: analytics #13 | Implemented | `random_fills` streams bounded leaves of at most 128 trades, with the original RNG draw order and NumPy pairwise addition tree. No full runs-by-trades working matrix is retained. Existing tests check bit-identical totals and bounded allocation. |
| 6: risk #12 | Implemented | `_run_sequence` builds R arrays, day counts and losing streaks once per permutation and reuses them across risks; FTMO sequence construction is also shared across risks. |

Added `tests/test_speed2_completion.py` (21 parametrized cases):

- All five cached primitives reject a different symbol, timeframe or candle at the
  cached cursor; rejection leaves the correct feed usable, and old cursors still fail.
- Session setup computes FVG, BOS and swings once per close, and ATR once per distinct
  period, including different filter multipliers on the same ATR period.
- Session structure breaks, confirmations, ordered usable zones, equilibria, ATR and
  transitions match independently owned detectors at each close. Short-history prefixes
  match the extended history, with filters and with-trend breaks both on and off.

Validation, run sequentially:

- Full suite: **3742 passed, 5 skipped, 1 xfailed, 44 warnings**, 184.26 s; exit 0.
  Output: `results/profile/speed2_completion_full_suite.txt`.
- `.venv/Scripts/ruff.exe check .`: **All checks passed**, exit 0.
  Output: `results/profile/speed2_completion_ruff.txt`.
- Profiling command: `.venv/Scripts/python.exe scripts/profile_runs.py > results/profile/speed2_after.txt`,
  exit 0, after the suite finished. No concurrent test/profile workload.
- Golden check was not run; Opus runs it. No commits, pushes, branches, subagents,
  credentials or protected-path edits.

| Run | Speed 1 | Speed 2 | Time change | Trades (both runs) |
|---|---:|---:|---:|---:|
| opening_range US500 + NAS100 | 37.0 s | 37.5 s | +0.5 s (+1.4%) | 1362 |
| ny_index_sweep NAS100 | 283.5 s | 223.9 s | -59.6 s (-21.0%) | 367 |
| session_zone_sweep XAUUSD | 94.3 s | 61.0 s | -33.3 s (-35.3%) | 2769 |

Times are the script's cProfile wall totals, using the same development period,
defaults and single worker as `speed1_after.txt`. Matching trade counts are a profiling
sanity check; golden-list equality remains for Opus to verify.

Files added: this report and `tests/test_speed2_completion.py`. Ignored artifacts:
the full-suite and Ruff logs, `speed2_after.txt`, regenerated strategy `.prof` files,
and the initial focused-test log (`speed2_completion_focused.txt`, 61 passed before
the final fixture/format cleanup; the full suite covers the final test file).

Open trading-rule questions: none. Remaining review: Opus's independent diff/test
review and golden check, followed by user acceptance.
