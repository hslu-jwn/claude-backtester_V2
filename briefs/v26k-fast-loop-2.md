# Brief V2.6k part 2: finish the fast loop (Codex gpt-6.1-terra, high)

Part 1 (`briefs/v26k-fast-loop.md`, read it) is in the working tree, uncommitted: cost gate,
parallel matched monkeys (identical numbers), `analytics/criteria.py`. Opus reviewed it; keep
it and finish the rest. Same rules: test first, never change numeric expectations, no engine /
cost / strategy / `live/` change. The golden-config failure you saw is fixed (commit e5e21b2).

## To do

1. **Entry screen in parallel** (brief item 2): `analytics/entry_screen.py` random-exit runs
   (`_random_summary`, rng `[seed, 0]`) and the shuffled scan (`_hit_scan`, rng `[seed, 1]`)
   get `workers`; draws stay in the parent in today's order, only the re-simulation goes to
   the pool (pass M1 once via an initializer, like `monkeys._init_worker`; reuse that pattern,
   do not copy it twice: one small shared helper is fine). Bit-identical results for any
   worker count; `workers=1` = today's in-process path. Wire `workers` through
   `tools/research_entry_screen.calculate` (the runner already passes it to monkeys) and the
   standalone `tools/entry_screen.py` CLI (`--workers`).
2. **Fixes in part 1:**
   - `criteria.py` halves: use the scorecard's halves (the same split the variant row shows in
     `variants.csv` `half_first_net_r` / `half_second_net_r`); reuse the scorecard / robustness
     function that computes them instead of a new year split, and test that the two agree.
   - `stop_share`: compare the reason value (`getattr(r, "value", r)`), so engine
     `TradeResult`s and records both work; test both.
   - Gate skip reason: say the configured threshold ("chosen development net R <= {gate}
     after costs").
   - Add a docstring with the spec reference to `criteria_inputs`.
3. **Missing tests from part 1's list:** 3 (`fail_fast = false` runs nulls at negative net;
   `fail_fast = "no"` -> GridError), 4 (`gate_net_min = 10`, net +5 -> skipped), 6 (entry
   screen workers 1 vs 3 identical), 7 for the entry screen (no pool at workers 1), 8 (a worker
   exception propagates, monkeys and entry screen), 9 edge cases (k larger than the number of
   days -> 0, x2 stress equals `stressed_net(trades, 2.0)`), 10 (`criteria_inputs.json` keys
   on a submission grid fixture).
4. **Docs** (brief "Docs" section): `docs/research-runner.md` › "Fast loop (V2.6k,
   2026-10-28)" + Output list; `docs/research-intake.md` › Pipeline step 7.
5. **Timing:** run the monkeys on the largest existing test fixture with workers 1 and 4,
   report both times (on fixtures the pool start-up may dominate; say so).

Done = `pytest tests/analytics tests/tools -q` fully green (run it to the end; it takes a few
minutes), ruff check + format clean. Report: files changed, tests added / touched, timings,
open questions. Do not commit.
