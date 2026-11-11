# V2.6 step 2 — addendum A-C handoff

Only addendum A-C was changed in this pass; Part 1 is the committed baseline.
Ready for Opus's independent review and user acceptance. No ROADMAP checkbox marked.

## Implemented

- Shared per-date server clock proof from the cache start through 2021-09-13 inclusive.
  Every decisive histdata reference must agree. Its residual applies to EVERY MT5 symbol,
  including MT5-only US30/US2000. Sparse reference days cannot vote.
- Ambiguous dates retain all disagreeing readings and are excluded for all symbols.
  Dates without a decisive reference are also excluded for all symbols.
  Per-symbol/year density filtering remains unchanged.
- From 2021-09-14, the plain NY+7 clock is unchanged. A development correction that
  crosses into the test period fails before active cache writes.
- Queue plan: 21 histdata jobs, then ONE shared proof job, then 26 symbol repairs using
  the SAME frozen JSON table. Quality settings must match. Reruns use retained originals.
  The proof command uses a unique temporary file and atomic replacement.

## Evidence (no cache writes)

Read-only audit: `.venv/Scripts/python.exe scripts/v26b2_clock_evidence.py`.
Elapsed **184.80 seconds**, below the 540-second bound. Proven 2015–2018 histdata
DST-gap corrections are applied in memory to the original cache, using Part 1's
independent weekly-edge anchors. No whole-period clock offset is guessed.

|Year|Dates proven|Ambiguous|No reference|
|---|---:|---:|---:|
|2010|0|0|365|
|2011|0|0|365|
|2012|0|0|366|
|2013|0|0|365|
|2014|0|0|365|
|2015|309|0|56|
|2016|308|1|57|
|2017|304|5|56|
|2018|311|0|54|
|2019|292|18|55|
|2020|287|24|55|
|2021 through September 13|205|12|39|

Total: **4,274 dates: 2,016 proven, 60 ambiguous, 2,198 without a decisive reference**.
Counts include cached empty weekend dates. Proven dates still undergo per-symbol density
filtering. 2010–2014 have no references and are excluded.

`results/clock_check_mt5.md` includes per-symbol/year kept/dropped counts and ALL
ambiguous dates with both/all readings, including March 2021 FX/metals disagreements.
US30 retains 236/285/205 input days in 2019/2020/2021-development; US2000 retains
288/291/285/205 in 2018/2019/2020/2021-development.

Test-period sample: GBPUSD/XAUUSD prove zero residual on 2021-09-14, 2021-11-03,
2022-03-16, 2023-03-15 and 2023-07-12. NAS100/US500 prove zero on 2023-03-15;
other available index samples are inconclusive under unchanged thresholds.
No decisive sample contradicts NY+7. No sample is used to change test-period timestamps.

Artifacts: `results/clock_check_mt5.md`, `results/v26b2_server_clock.json`,
`results/v26b2_clock_measurement.log`, `results/v26b2_clock_console.log`.
The audit JSON is evidence only; queue stage 2a generates
`results/v26b2_rebuild_server_clock.json` from REBUILT histdata.

## Files changed in this addendum

- `src/backtester/data/cache_repair.py`, `src/backtester/tools/cache_repair.py`
- New `tests/data/test_v26b_server_clock.py`
- New `tests/tools/test_v26b_server_clock_cli.py`
- `tests/tools/test_v26b_tools.py` (queue-plan contract includes the shared proof stage)
- New `scripts/v26b2_clock_evidence.py`
- `scripts/rebuild_cache_v26b.md`, `docs/ARCHITECTURE.md` (Data sources)
- `briefs/v26b-test-cases.md`, this report
- Git-ignored evidence artifacts above and `results/pytest_v26b2.log`

## Validation / remaining review

Test-case list first, then tests, then code. Initial shared-table and boundary
regressions failed before implementation; eight new cases now pass. Existing
expectations were not weakened. The first full run had 722 passes and one obsolete
queue-plan failure: it counted the new shared proof as a 27th symbol repair. The updated
contract still requires exactly 26 symbol jobs and now additionally requires one preceding
proof job and the same table path in every repair job. Its focused check passes.
Ruff and formatting checks pass on changed Python files; `git diff --check` passes.
Final command: `.venv/Scripts/python.exe -m pytest -q tests/data tests/tools > results/pytest_v26b2.log 2>&1`.
Result: **723 passed**, 20 existing pandas deprecation warnings, **142.89 seconds**.

No rebuild, production-cache/raw changes, downloads, terminal, servers, commits,
pushes, branches, subagents or protected-path edits. **Removed: nothing.**
Opus runs the rebuild, data check and 2023 golden check afterwards; stop on any
golden difference. No golden lists were run or regenerated here.

Open review: assess the 60 ambiguous dates and inconclusive index samples.
No unclear trading rules. Independent cross-review and user acceptance remain.
