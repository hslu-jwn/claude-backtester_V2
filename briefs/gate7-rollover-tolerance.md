# Brief: gate 7 rollover tolerance in `tools/timed_hold_gates.py` (rule set by the user, 2026-11-09)

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). Rule:
`docs/strategy-timed-hold.md` › Hypothesis 11 › "Gate 7 decision" (read it). Never weaken an existing test.

## Rule to implement

For a trade whose `(entry, exit]` crosses the FTMO daily rollover (17:00 America/New_York, i.e. 21:00 UTC
in US summer / 22:00 UTC in US winter; use zoneinfo, never a fixed offset), an M1 gap does not fail gate 7
when either (a) every missing minute lies inside the rollover hour window 21:00-23:00 UTC, or (b) the gap
is at most 6 minutes. A missing exit candle, no candles at all, or an invalid present candle still fail.
Trades that do not cross the rollover keep today's rule exactly (gap > 5 minutes fails).

## Files

- `src/backtester/tools/timed_hold_gates.py` (apply the rule; report per symbol both
  `data_integrity_failures` (tolerant, used by the gate) and `data_integrity_failures_strict` (today's
  count) so nothing is hidden; add `"rollover_tolerance": true` to the settings block).
- The shared `integrity_failures` in `tools/alternating_path_gates.py` is used by other tools: do not
  change its behaviour; add an optional parameter or a new helper next to it.
- `docs/research-runner.md` or the timed_hold spec Gates section: one line pointing to the rule.

## Tests (first, `tests/tools/test_timed_hold_gates.py`)

Hand-built M1 data: a crossing trade with a 30-min gap at 21:10 UTC (summer) passes; the same in winter at
22:10 passes; a crossing trade with a 6-min gap at 18:40 passes, a 7-min gap there fails; a non-crossing
trade with a 6-min gap fails (unchanged); missing exit candle fails; invalid candle fails; the strict
count is still reported. Existing tests unchanged.

## Done =

`python -m pytest tests/tools -q` green, `python -m ruff check .` clean. Then rerun
`python -m backtester.tools.timed_hold_gates results/research/timed_hold_gotobi_d9ea62c1 --primary-symbol
USDJPY --min-trades 200 --min-breadth 1` and report the G1 primary's gates and both failure counts
(expected: 0 tolerant failures, 9 strict on USDJPY). Report files, tests, anything unclear.
