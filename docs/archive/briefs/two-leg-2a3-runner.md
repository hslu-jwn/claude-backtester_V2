# Brief: two-leg trades, increment 2a-3 — group runner and result files, test-first

Read `AGENTS.md` first. Hard limits apply (no commits, no branches, no servers, no `live/`, no `.env`).
Worktree `bt-lane-two_leg3`. No backtest or research run on real data. Accepted by the user 2026-11-12.
Spec: `docs/design/multi-symbol.md` › B and › "Runner, research, artifacts and UI". Builds on 2a-1 / 2a-2
(`strategy/group.py`, `engine/group_trade.py`, `engine/group_backtest.py`; read them and their tests).
Unclear and not answered here: choose the reading closest to the design and to the legacy runner, write
it in the module docstring as an assumption, list it in your report.

## Files you may create / change (nothing else)

- `src/backtester/group_runner.py` (new), `tests/test_group_runner.py` (new).
- `docs/ARCHITECTURE.md` (a few lines), `docs/research-runner.md` (one short section "Group runs").
Legacy `runner.py`, `run.py`, `engine/*`, `strategy/base.py`, registry, UI: NOT changed (import their helpers).

## `group_runner.py`

1. `load_group_inputs(strategy, start, end, sources=DEFAULT_SOURCES, warmup_days=...)`: M1 (and declared
   higher timeframes) for every leg and reference symbol between the warm-up start and `end`, through the
   existing loaders (`runner._load_timeframe` / `SeriesCache` / `sources.adapter(...).fetch_frame`, as
   `runner._load_references` does); never data after `end`. A leg with no data -> a clear `NoDataError`.
2. `run_group(strategy, start, end, sources=..., cfg=CostConfig(), values=None) -> GroupRunResult`:
   loads, calls `run_group_backtest`, and keeps only groups whose entry falls in [start, end] for results
   (warm-up decisions are not results; say how in the docstring).
3. `group_trade_rows(result) -> list[dict]`: ONE row per closed group (never one per leg: the design forbids
   counting legs as independent trades), in the `trades.csv` schema that `analytics.records.read_trades` /
   `TradeRecord.from_row` reads, so `tools/gates.py`, `timed_hold_gates.variant_report` and the stress
   tests work unchanged on group runs. Mapping: `symbol` = leg symbols joined with "/" in leg order,
   `direction` = the first leg's direction, `entry_time` / `entry_candle` = the group entry (first leg
   fill), `exit_time` = the last leg exit, `r_gross` / `r_net` = group R, `spread_r`, `commission_r`,
   `swap_r`, `funding_r`, `conversion_r` = the leg attributions summed, with the SAME sign conventions as
   the legacy single-leg rows (read `runner.trade_rows` and `alternating_path_gates.components`: costs
   there are positive magnitudes where the legacy code stores them that way). `entry` / `initial_stop`
   must give risk 1.0 in the row's own units (e.g. entry 1.0, initial_stop 0.0 for a long) and be
   documented as synthetic. Test: `components(row)` returns (spread, commission, slippage) of the group in
   group R, slippage = fill cost beyond the spread, and `trade_net(row, "all")` equals the hand-computed
   doubled-cost group R.
4. `write_group_results(result, out_dir, run_id, settings) -> Path`: a run folder with `trades.csv` (the
   rows above, via the same CSV writer conventions as `runner.write_results`), `group_legs.csv` (per leg:
   group id, symbol, direction, quantity, weight, entry / exit time and fill, exit reason, gross / net /
   cost attribution in group R), `rejected.csv`, `unresolved.json` (open legs, stale marks and their
   times), `settings.json` (strategy class name, legs, references, period, `cache_dirs` of EVERY leg and
   reference symbol, cost-config flags, values used, D convention note). Same folder naming as
   `runner.new_run_id`.

## Tests first (tmp_path caches with hand-built M1 frames, as `tests/test_runner_market.py` does)

1. A toy `GroupStrategy` on two symbols in a tmp cache: `run_group` gives the expected single group, its
   R equals `group_result` computed by hand; data after `end` is never loaded (assert on the loader calls
   or the last candle time).
2. `group_trade_rows` round-trips through `read_trades` (all fields), one row per group, legs never rows.
3. Stress: `components` / `trade_net(row, "all")` exact on a costed group (custom `CostConfig`).
4. `tools/gates.py`-style use: `timed_hold_gates.variant_report` accepts the rows (no exception, n = groups).
5. `write_group_results` writes all five files; `settings.json` lists the cache dirs of both legs and a
   reference; `unresolved.json` holds a residual leg with its stale mark time.
6. Missing leg data -> `NoDataError` naming the symbol; warm-up groups are not in the results.

## Done =

`python -m pytest -q -p no:cacheprovider -n 8 tests/test_group_runner.py tests/engine tests/strategy tests/tools`
green and `python -m ruff check src tests` clean (worktree, `..\backtester-claude_V2\.venv\Scripts\python.exe`).
Report: files, tests, every assumption (especially the sign conventions you matched), open questions for 2b.
