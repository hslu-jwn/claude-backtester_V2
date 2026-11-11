# B-strategy: B8–B9 implementation (2026-10-23)

Implements the decisions in `README.md` › B (rule set by the user, 2026-10-22).
Implementation and regression tests are ready for independent review; this is not a
cross-review approval. No commits, branches, pushes, or golden-list rewrites.

## Changes

- **B8, strategy 1:** finalizing a session's new zones no longer expires the zones
  active in that session. Entries can occur in the remaining minutes, with exclusive
  expiry at the real end. The base-timeframe setup loop also handles boundaries between
  30m closes. TP candidates include only zones active now, excluding zones finalized
  early for the next session. Drawing expiry retains the last active candle index.
- **B8, strategy 1:** ignored weekend candles advance the swing detector's cursor
  without changing its last eligible non-doji candle or emitting swings.
- **B8, strategy 2:** BoS/tap arrivals after their deadlines are rejected before state
  transitions, including after data gaps. Equality remains eligible; a deeper sweep
  extreme still restarts its BoS clock, while re-entry taps retain the original BoS clock.
- **B9:** frozen `SwingConfig.doji_relative_tolerance`, default `1e-9`, finite and
  nonnegative; zero restores strict comparisons. Fixed and range-share thresholds carry
  the configured tolerance through shared consumers. Slack is the configured value times
  `max(abs(open), abs(close))`; direct float thresholds use the same default.

## Existing test expectations changed (complete list)

| Existing test | Old → new | Decision |
|---|---|---|
| `tests/strategy/session_zone_sweep/test_zones.py::test_zone_expires_at_the_end_of_its_session_and_is_not_checked_after` | `(expired.confirmed_index, expired.last_index)`: `(30, 30)` → `(31, 30)`; observed expiry 23:30 → 00:00 UTC, drawing endpoint unchanged | B8: actual session end |

No other existing test expectation was edited. No existing B9 expected value needed an
update. Golden lists and their manifest are unchanged; market-data golden regeneration
and trade-count comparison remain with Opus after review, as requested.

## Files changed

- Production: `src/backtester/detectors/swings.py`,
  `src/backtester/strategy/session_zone_sweep/{zones,signals}.py`,
  `src/backtester/strategy/ny_index_sweep/setup.py`.
- Specs: `docs/confluences.md`, `docs/strategy-session-zones.md`,
  `docs/strategy-ny-indices.md`.
- New regression files: `tests/detectors/test_b9_doji_tolerance.py`,
  `tests/strategy/session_zone_sweep/test_b8_session_lifetime.py`,
  `tests/strategy/ny_index_sweep/test_b8_deadlines.py`.
- Existing test: `tests/strategy/session_zone_sweep/test_zones.py`.
- Handoff: this report.

## Validation

- Test-first reproduction: `results/b-strategy-test-first.txt` (19 failed, 10 passed
  before production edits); supplemental boundary and TP-eligibility tests were also
  observed failing before their fixes. Tests were not weakened to fit implementation.
- Initial full-suite evidence for the sole existing expectation change:
  `results/b-strategy-before-expected-update.txt`.
- **36 new regression cases.** Final full suite: **3642 passed, 5 skipped, 1 xfailed**,
  44 dependency deprecation warnings, exit 0, 206.35 seconds. Output captured in
  `results/b-strategy-full-suite.txt`; the skip/xfail counts match the initial run.
- `ruff check .`: **All checks passed**, exit 0; output in `results/b-strategy-ruff.txt`.
- `git diff --check`: clean.

Open trading-rule questions: none. Independent review and user acceptance remain pending.
