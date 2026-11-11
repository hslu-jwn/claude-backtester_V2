# Brief: V2.4c T-14 — matched-monkey test for every strategy

Context: ROADMAP › V2.4c (accepted by the user 2026-10-23); idea card T-14 in `knowledge/ideas.md`
(Davey p.109-114, App.A; Carver ch.13); checklist #26 in
`knowledge/topics/testing-and-robustness.md`. Today the random-entry baseline (Monte Carlo kind B,
`analytics/random_baseline.py`) exists only for the gap fade, and the entry screen
(`analytics/entry_screen.py`) already re-simulates exits on M1 with the engine's rules
(stop fill at the open on a gap, SL first, spread, commission, swap, slippage; its `M1Data`,
`_scan`, `_costed`, `rollover_schedule`, `random_exit_runs`, `_window_candidates`). Reuse that
machinery; do not write a second M1 exit simulator.

## What to build (`analytics/monkeys.py`, a tool, runner wiring)

For one trade list (a strategy run) and its symbols' M1 candles:

1. **Random entry, real exit rule shape**: per run, the same number of trades per symbol, the
   same long share, entry times drawn uniformly from the strategy's own trading window
   (`_window_candidates`: the New York weekdays and time-of-day buckets in which it entered),
   each with the stop distance and the hold time of a real trade drawn at random (paired, so the
   hold / stop distribution matches); exit at the stop, else after that hold (no target).
2. **Real entry, random exit**: the real entries and stops, exit after a random hold drawn
   from the real hold distribution (the entry screen's random exit, matched hold).
3. **Both random**: 1 and 2 combined.
4. Per kind, `runs` (default 1000; the card's 8000 is a setting, slow runs go in the job queue
   later) seeded runs; statistic = total net R and max drawdown in R (exit order); report the
   real result's percentile on each (ties count half), median and 5 / 95 % of the runs.
   Pass rule from the card: the real result beats >= 90 % of the runs on net R **and** on
   max DD (lower DD is better), per kind.
5. **Tool** `python -m backtester.tools.monkeys --strategy <name> [--symbols ...] [--start
   --end] [--runs N] [--set KEY=VALUE]` (development period by default, the test period refused
   without `--allow-test-period`, like `tools/entry_screen.py`), output
   `results/monkeys/<strategy>_<time>/summary.json + report.md`, one trial-log line per run
   source like the entry screen does.
6. **Research runner**: for the chosen variant, kinds 1-3 with `runs = 200` on the development
   period (grid option `monkeys = false` skips it), `monkeys.json` + report block, flag
   `monkey_beaten` when any kind fails the 90 % rule. **Monte Carlo verdict** (`analytics/verdict.py`,
   check 2 `random_entries`): fed by kind 1's net-R percentile for every strategy (the gap
   fade's kind B stays as it is where it exists; say in the spec which wins: kind B for the
   gap fade, the monkey kind 1 for all others).

## Rules

Spec first (`docs/risk-management.md` › Monte Carlo report, a "Matched monkeys" section), the
test-case list at the top of the test file, failing tests, then code. Tests on small hand-built
M1 data: counts, long share and the hold / stop pairs are matched exactly; no random entry
outside the window; seeded runs are reproducible; a planted perfect-foresight trade list beats
~100 % of the runs; a list that is itself random sits near the 50th percentile (loose, seeded);
costs are charged like the engine (compare one hand-computed trade). No lookahead: a random
entry uses the close of an M1 candle as its fill time, exits only on later candles. Selection,
trial-log semantics, DSR, golden lists unchanged. Never edit `src/backtester/live/`. Long runs
to log files; the sandbox cannot run process pools, so keep a `--workers 1` path.

Done = full suite green (`pytest -q > results\pytest_t14.log 2>&1`), `ruff check .` clean, and
one real run: `python -m backtester.tools.monkeys --strategy trend_following --symbols XAUUSD
--runs 200 > results\monkeys_check.log 2>&1` with its percentile table in the report. Report:
files changed, test count, decisions the spec did not settle, open questions.

## Answer from Opus (your question of 19:59)

Yes, exactly as you proposed, per symbol, by permutation (distributions preserved exactly):
1. random entries, the real (stop, hold) **pairs** permuted onto them;
2. real entries and stops, the real holds permuted independently;
3. random entries, stops and holds permuted **independently**.
Write this into the spec. Go ahead with the brief.
