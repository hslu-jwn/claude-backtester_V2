# Brief V2.6i i8: first research pilot FX_LONDON_FIX_REV v1.0.0 (Codex, medium)

Submission (claimed 2026-10-28, sha256
`8ec6b914e7669cc28b3eeb1008271dae8df264453934d6ce5c099b3d70ae6263`):
`../Shared_Interface/queue/claimed/FX_LONDON_FIX_REV__v1.0.0.json`. Read it in full; it is the
source of every rule. Process: `docs/research-intake.md` › Pipeline steps 4-5. Read-only on
`../Shared_Interface/` (never edit or move anything there).

**Test first:** tests from the cases below before the code; never weaken a test.
Strategy name / folder: `london_fix` (strategy 8). Do not commit.

## Deliverables

1. `docs/strategy-london-fix.md`: rules from the submission (entries, exits, stop, side map,
   restrictions, edge cases), config defaults, backtest options, and a **Submission** section:
   strategy_id, version, sha256 above, and a mapping table of every parameter, entry / exit
   rule, restriction and edge case -> config field / code location / test name. A section
   **Assumptions (decided by Opus, 2026-10-28)** with the three below.
2. `src/backtester/strategy/london_fix/` (copy `_template/`): `LondonFixConfig` (frozen,
   defaults = the submission's baselines: `entry_time_london="16:03"`, `atr_period=60`,
   `stop_atr_multiplier=4.0`, `holding_minutes=360`, `force_close_london="23:55"`, the side
   map as a fixed tuple field), `LondonFix` strategy on M1.
3. Registry entry (`strategy/registry.py`) and default symbols for it (the six pairs, where the
   other strategies declare theirs, e.g. `STRATEGY_SYMBOLS`).
4. `research/grids/london_fix.toml`: the six symbols, base = baselines, grid
   `stop_atr_multiplier = [3.0, 4.0, 5.0]`, `holding_minutes = [60, 180, 360]` (exactly 9
   variants), `min_trades` default, plus the `[submission]` identity block exactly as the V2.6i
   intake grids require (see `docs/research-runner.md` › Submission identity and
   `tools/research_grid.py` `_submission`).
5. Tests in `tests/strategy/london_fix/`, and a `FIXTURES` entry in
   `tests/strategy/test_contract.py` if needed.

## Rules (from the submission; quote it in the spec)

- Entry: on weekdays, when the M1 candle [16:02, 16:03) Europe/London has closed (its close
  time is 16:03 London, converted with `zoneinfo`, never a fixed offset), market order at its
  close (SIGNAL_CLOSE: the engine's normal order at the base candle's close; never next-bar
  open). Long EURUSD, GBPUSD, AUDUSD, NZDUSD; short USDCHF, USDCAD. Any other symbol (USDJPY
  included): no trades.
- ATR: Wilder ATR(60) of completed M1 candles up to and including the 16:02 candle; skip if
  fewer than 60 true ranges or ATR not finite / <= 0. Use the shared ATR detector if it is
  Wilder; otherwise implement Wilder here (strategy folder only) and test it.
- Stop: entry -/+ `stop_atr_multiplier x ATR`, fixed. No take profit.
- Time exit: close at the close of the first M1 candle whose close time is >= entry time +
  `holding_minutes`; never later than the candle closing at 23:55 London on the entry day
  (force close). Use the engine's existing time-exit / order-expiry mechanics (look at how
  `gap_fade` or `opening_range` close at a fixed time); if the engine cannot express it, stop
  and report instead of changing the engine.
- At most one entry per symbol per London calendar day; none while a position on that symbol
  is open. Missing [16:02, 16:03) candle (data gap, holiday without bars) -> no trade that
  day; never use a later candle.
- Stop and time exit in one candle: the engine's rule (stop first / M1 intrabar) as it is.

## Assumptions (decided by Opus 2026-10-28 with the user's go; Research is told)

1. Month-end = the last weekday (Mon-Fri) of the calendar month, London date of the entry.
   Only a reporting tag: add the trade tag `month_end` to those trades (strategies may set
   `Trade.tags` / order tags; check how ORB sets tags) so the split can be reported.
2. Doubled-cost stress (2x spread, commission, slippage) is a reported number only, computed
   later from the trades; nothing to build here.
3. No London-fix holiday calendar: every weekday with the 16:02 candle trades.

## Test cases (hand-built M1 fixtures, `tests/conftest.py` › `make_candles`)

1. Winter (GMT): signal at 16:03 London = 16:03 UTC; summer (BST): 15:03 UTC. Exact UTC
   timestamps written in the test.
2. DST change weeks: the Monday after the last Sunday of March and of October.
3. Long EURUSD: entry = close of the 16:02 candle, stop = entry - 4 x ATR (ATR value worked
   out in the test from simple ranges, e.g. constant range 0.0010 -> ATR 0.0010).
4. Short USDCAD mirrors 3 (one code path, `Direction`).
5. USDJPY / an unknown symbol: no orders.
6. Fewer than 60 candles before 16:02 -> no order; ATR 0 (flat candles) -> no order.
7. Missing 16:02 candle -> no order that day, also not at 16:04.
8. Saturday / Sunday bars -> no order.
9. Time exit: holding 60 -> the trade closes at the close of the candle ending 17:03 London;
   with a gap in the data the first candle closing after 17:03.
10. Force close: an entry whose time exit would pass 23:55 London is closed at 23:55 (use a
    settings override, e.g. `entry_time_london="23:00"`, `holding_minutes=360`).
11. One entry per day per symbol; an open position blocks a new entry.
12. Month-end tag on the last weekday of a month (e.g. Friday 2019-05-31; and 2019-08-30 when
    the 31st is a Saturday); not on other days.
13. No-lookahead: run incrementally, appending future candles never changes earlier orders.
14. Grid file loads, 9 variants, submission identity present, `swept_params` = the two
    settings.

Done = `pytest tests/strategy -q` and `pytest tests/tools -q -k "research_grid or intake"`
green; ruff check + format clean. Report: files changed, tests, how the time exit / force
close is expressed with the existing engine, any submission rule you could not map (quote the
JSON field), and open questions. Do not change the engine, costs, `live/`, or other strategies.
