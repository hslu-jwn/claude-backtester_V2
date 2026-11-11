# Brief: explain the M1 integrity flags on the Gotobi test trades (diagnostic only, never a retest)

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). The one-time test
of Gotobi G1 is spent (spec › Hypothesis 11 › One-time test result: not confirmed). Nothing here may
re-run or re-tune it.

Facts: run `results/20261109-215845_USDJPY-EURJPY/` (trades 2021-09-14..2026-11-08, 03:00 -> 09:55 JST,
i.e. 18:00 -> 00:55 UTC). A scratch check (`tools/timed_hold_gates.rollover_integrity_failures` on
`load_m1` with the run's cache dirs) flagged 302 of 321 USDJPY trades (303 strict); in development
(MT5 2015-2021) the same check flagged 9 strict / 0 tolerant.

Task: find out why. Check whether the check itself is wrong for this period (cache source mix, loader date
range, timestamps, a weekend/rollover pattern in MT5 data after 2021) or the data really has gaps in
18:00-01:00 UTC (list the typical gap positions and lengths, by year). Check whether the engine's trades
used candles that the loader does not see. Write `knowledge/research/reports/2026-11-09_gotobi_test_integrity.md`
(cause, evidence, whether the test's net R could be affected, a fix proposal if a tool is wrong; do not
apply fixes to shared code). Report the cause in 3 lines.
