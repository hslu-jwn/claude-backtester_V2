# ROADMAP 12.5 demo reconciliation (Codex gpt-6.1-terra, medium)

Read `AGENTS.md` first. Rule: ROADMAP 12.5 (`docs/archive/ROADMAP-v1.md`: "demo trades from MT5
next to the engine's trades on the same candles (entry, exit, spread, swap, R), every
difference explained"); scope set by the user 2026-11-02 (ROADMAP V2.8 night run): the
fill-probe trades 2026-10-27..31 trade by trade against the engine on the same M1 bars.
Fill-probe spec: `docs/strategy-fill-probe.md`; fill report (same inputs, slippage only):
`src/backtester/tools/fill_report.py`.

## Idea

The fill probe's direction is a pure function of the signal time and its stop comes from the
M1 ATR, so running the real `FillProbe` (`strategy/fill_probe/`) through the engine
(`engine/backtest.py` `run_backtest`, default `EngineConfig`, i.e. the default costs) on the
same cached M1 bars must regenerate the bot's orders. Match demo trades to engine trades by
(symbol, signal time) and explain every difference.

## Inputs (read-only)

- Demo: `<live-dir>/<YYYY-MM-DD>/paper.csv` (one row per order: `time_utc` = signal bar close,
  `symbol`, `side`, `signal_entry`, `sl`, `spread`, `status` filled / skipped, `reason`,
  `real_fill`, `ticket`, `comment`) and `trades.csv` (`ticket`, `entry_time`, `exit_time`,
  `entry_fill`, `exit_price`, `sl`, `exit_reason`, `r_gross`, `r_net`). Only rows whose comment
  starts with `--comment-prefix` (default `fp`) and `time_utc >= --since`. Reuse the
  fill_report readers (`_read` etc.) instead of new CSV code.
- Engine: M1 candles of each traded symbol from `data.sources.DEFAULT_SOURCES` (the bot also
  wrote today's bars to the live cache; use the same source selection the chart uses for the
  symbol, `data/sources.py`), from `since - FillProbe.min_warmup_days` to the last demo day.
  Strategy: `FillProbe(symbol, FillProbeConfig())` (the bot's config: `live/bot.py`
  `parse_config(["--strategy", "fill_probe"])` gives it; do not edit `live/`).

## Output (`--out`, default `results/reconcile/`)

- `trades.csv`: one row per demo or engine trade: symbol, signal time, side, match status
  (`matched` / `demo_only` / `engine_only`), demo and engine: sl, entry fill, exit time, exit
  reason, exit price, r_gross, r_net; differences: sl, entry (price and in units of the model
  slippage `CostConfig().slippage`), exit seconds, exit price, r_net; `explanation`.
- `report.md`: counts per status; per symbol and per exit reason: matched n, exit-reason
  agreement share, median / p90 of the entry, exit and r_net differences, sum of r_net demo vs
  engine; the unexplained list (max 50 rows, the rest counted).
- Explanation rules, first match wins:
  `engine_only`: a demo `skipped` row for that symbol and signal time -> its `reason`;
  the signal time falls outside the bot's running window that day (before the first or after
  the last paper row of that day, or inside a gap of > 60 min without any paper row for any
  symbol) -> "bot not running"; else "unexplained".
  `demo_only`: no engine candle at the signal time -> "bar missing in cache"; else
  "unexplained".
  `matched`: exit reasons differ -> "exit reason: demo <x>, engine <y>"; sl differs by more
  than one tick (`symbol_info`-free: use 1e-9 relative) -> "different stop (ATR / bars
  differ)"; else "" (difference = slippage / spread / commission, already in the columns).
- CLI: `python -m backtester.tools.reconcile [--live-dir results/live] [--since
  2026-10-27T16:00] [--until ISO] [--comment-prefix fp] [--symbols ...] [--out
  results/reconcile]`; prints the counts and the report path. Never connects to MT5, never
  writes into the live folder or the trial log.

## Tests first (`tests/tools/test_reconcile.py`, small hand-built fixtures in `tmp_path`)

1. A demo trade and the engine trade at the same (symbol, signal time) are `matched`; the
   entry difference is demo `entry_fill` - engine entry fill, signed adverse-positive like
   fill_report (buy above / sell below is positive).
2. Exit reason stop_loss (demo) vs time exit (engine) -> explanation names both.
3. Engine trade with a demo `skipped` row at the same time -> `engine_only`, explanation = that
   row's reason.
4. Engine trade in a 2-hour gap without paper rows -> "bot not running"; after the last row
   of the day -> "bot not running".
5. Demo trade without an engine candle at its time -> `demo_only`, "bar missing in cache".
6. Rows of another comment prefix (`orb`) and before `--since` are ignored.
7. Different stop -> "different stop (ATR / bars differ)".
8. Report: counts, the per-symbol table and the unexplained list cap (51 unexplained -> 50
   rows + "1 more").
9. Empty live folder -> exit 1 with a clear message, no output files.
10. One real-engine test on a synthetic M1 series (a few hundred hand-built candles,
    `tests/conftest.py` `make_candles`): `FillProbe` through `run_backtest` produces trades
    whose signal times are multiples of 30 min, so matching on the signal time works.

## Then run it on the real data

`python -m backtester.tools.reconcile --since 2026-10-27T16:00 --out
results/reconcile_2026-11-02` and include the report's counts and the five largest
unexplained groups in your answer (no fixing of the bot or the engine: report only).

## Limits

New files `src/backtester/tools/reconcile.py`, `tests/tools/test_reconcile.py`; a short
section "Demo reconciliation (ROADMAP 12.5)" in `docs/live-trading.md` (command, columns,
explanation rules). No change to `engine/`, `strategy/`, `live/`, costs or any default. Never
start a server, never connect to MT5, never commit / push / branch.

**Done =** the new tests green, `python -m pytest tests/tools -q` green, `ruff check .` and
`ruff format --check` clean, the real run done. Report: files changed, test results, the real
run's counts, open questions.
