# Brief V2.6k: fast research loop (Codex gpt-6.1-terra, medium)

Decided by the user 2026-10-28 (ROADMAP V2.6k). The pilot `london_fix` (9 variants, 10,397
trades each) took 3 minutes for backtests + sensitivity and then > 5.5 h on one core in the
matched monkeys (`tools/research_monkeys.py` -> `analytics/monkeys.py`, 200 runs x 3 kinds);
the entry screen (1,000 random runs) would have followed. With hundreds of submissions this
must be minutes. **Test first.** No engine, cost, strategy or `live/` change; no spec default
of the null tests changes (runs, seeds, pass rules).

## 1. Fail fast (gate before the null tests)

- `ResearchConfig.fail_fast: bool = True` and `ResearchConfig.gate_net_min: float = 0.0`.
- In `tools/research.py` `finish()`: monkeys and the entry screen run only when the chosen
  development variant's net R (after costs) is > `gate_net_min`. Otherwise each is written as
  `{"skipped": "gate", "reason": "chosen development net R <= 0 after costs", "net_r": x}`
  into `monkeys.json` / `entry_screen.json`, the report block says "skipped (failed the cost
  gate)", and no `monkey_beaten` / `entry_screen_failed` flag is added (a new flag
  `nulls_skipped` instead; UI label "null tests skipped (lost after costs)").
- Grid key `fail_fast = true|false` (default true) overrides the config, validated like
  `monkeys`; `monkeys = false` / `entry_screen = false` keep switching them off entirely.
- Everything else (significance, Bayes, sensitivity, diagnostics) runs as today: they are
  cheap. Measure that claim on the fixture run and report it.

## 2. Parallel null tests, identical numbers

- `analytics/monkeys.py` `matched_monkeys(..., workers: int | None = None)` and
  `analytics/entry_screen.py` random-exit runs and shuffled scans (`_random_summary`,
  `_hit_scan`, or wherever the per-run loop is) get a `workers` argument.
- **The random draws stay in the parent, in exactly today's order and RNG streams**
  (`default_rng([seed, kind])` etc.); only the per-run re-simulation (`replay` /
  exit scans, the expensive part) goes to a process pool (`concurrent.futures`
  ProcessPoolExecutor, like `runner.iter_symbol_runs`). Results must be **bit-identical** to
  `workers=1` for any worker count; `workers=1` must keep today's in-process path (no pool).
- M1 data is large: pass it to workers once (pool initializer / module global), not per task.
  Chunk runs (e.g. `ceil(runs / (4 x workers))` per task).
- Default workers: the runner's existing `--workers` value (see how `run_backtests` gets it);
  `None` = `os.cpu_count() - 1`, at least 1.
- Wire `workers` through `tools/research_monkeys.calculate`, `tools/research_entry_screen.calculate`
  and the standalone `tools/entry_screen.py` CLI.

## 3. Criteria inputs (generic, for the result envelope)

New `criteria_inputs.json` in the research folder, written by the runner for every grid with a
`[submission]` block (and harmless for others), from saved trades only, development period:
`variants_positive_net` (count), `variants` (n), chosen `net_r`, `gross_r`, `gross_by_symbol`,
`symbols_positive_gross`, `net_r_costs_x2` (`robustness.stressed_net(trades, 2.0)`),
`net_r_costs_stress` (the configured 1.5) with both factors named, the two halves (as the
scorecard), `net_r_without_best_days` for k = 1, 5, 10 (days = UTC exit date, sum of net R per
day), `stop_share` (exit reason stop_loss), `trade_tags` counts and net R per tag (e.g.
`month_end`). Pure helpers in `analytics/` (e.g. `analytics/criteria.py`), tools only wire.
Add a short report block "Criteria inputs".

## Test cases

1. Gate: chosen net R -5 -> monkeys and entry screen not called (assert with a stub), both
   JSON files say skipped, flag `nulls_skipped`, report says skipped.
2. Gate: chosen net R +5 -> both called as today.
3. `fail_fast = false` in the grid -> called even at -5; `fail_fast = "no"` -> GridError.
4. `gate_net_min = 10`, net +5 -> skipped.
5. Monkeys: `workers=1` vs `workers=3` on a fixture -> identical dicts (exact equality,
   every float).
6. Entry screen random-exit runs and shuffled scan: `workers=1` vs `workers=3` identical.
7. `workers=1` creates no process pool (patch the executor and assert not used).
8. A worker exception propagates (no silent partial result).
9. `criteria_inputs`: hand-built trades with known gross / net / tags / days -> exact values,
   incl. k larger than the number of days (-> 0 net), a symbol with no trades absent, the x2
   stress equal to `stressed_net(trades, 2.0)`.
10. `criteria_inputs.json` written for a submission grid fixture; keys present.
11. Existing monkey / entry-screen tests stay green **unchanged** (identical numbers is the
    proof).

## Existing tests

Runner tests that compare file lists may need `criteria_inputs.json` added, or
`fail_fast = false` where a fixture's chosen variant is negative but the test checks monkey /
entry-screen output. Never change numeric expectations. List every touched test and why.

## Docs

`docs/research-runner.md`: subsection "Fast loop (V2.6k, 2026-10-28)" (gate, grid key,
workers, identical numbers, criteria inputs) and the Output list; `docs/research-intake.md`
› Pipeline step 7: the criteria inputs file feeds the result envelope.

Done = new tests green; `pytest tests/analytics tests/tools -q` green; ruff check + format
clean. Report: files changed, tests added / touched, the speed-up measured on the fixture
(workers 1 vs 4), open questions. Do not commit.
