# Brief: Phase 4 code review of one module (read-only)

You review ONE module (named in the task line below) of the backtester. Read `AGENTS.md`
first (no lookahead, SL-first rule, UTC / zoneinfo, no magic numbers, R only in strategies),
then the module's code, its tests and the spec sections it cites (`docs/...`). Change no
files. You may run its tests and small read-only Python snippets.

Rank findings in this order:
1. **Correctness:** lookahead (any use of a candle not closed at simulated time `now`, a
   higher timeframe read before its close, events acting before their confirming candle,
   detectors rewriting the past), fills (entry price / time, limit vs stop vs market, gaps
   through levels), SL / TP order inside one candle, costs (spread, commission, slippage),
   swap (17:00 New York rollover, triple day), time zones / DST, off-by-one in day ranges,
   silent exception swallowing, wrong results on empty / edge data.
2. **Speed:** hot loops (per candle / per trade), repeated work, Python where numpy fits,
   avoidable copies, file I/O in loops. Only where it matters for a research sweep.
3. **Cleanup:** dead code, duplication, unclear names. Keep this short.

Known audit findings 13.6-13.23 are listed in `docs/ROADMAP.md` (details in
`docs/archive/ROADMAP-v1.md` › Phase 13): confirm or refute those that touch this module.

## Answer

A table: `# | severity (critical / high / medium / low) | category (correctness / speed /
cleanup) | file:line | finding (one line) | evidence (the code path, or a failing input) |
fix (one line) | changes results? (yes / no / unknown)`. Max 25 rows, most severe first.
"changes results? = yes" means the golden trade lists (`tests/golden/`) would change. Then
max 5 lines: what you checked and found fine. No speculation without evidence: say
"unverified" if you could not confirm.
