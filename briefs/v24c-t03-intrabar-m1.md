# Brief: V2.4c T-03 / ROADMAP 12.2 — same-candle SL / TP resolved from M1 (a setting, then measured)

Context: ROADMAP › V2.4c (accepted by the user 2026-10-23), old ROADMAP 12.2 / idea T-03
(`knowledge/ideas.md`; NautilusTrader; Pardo ch.6 in `knowledge/topics/costs-and-execution.md`).
Today `engine/trade.py` `OpenTrade.on_candle` assumes **SL first** whenever a base candle
(5m, 15m, 1h, ...) contains both the SL and a TP (and `on_fill_candle` ignores TPs in the
candle a limit filled in). Engine code: Opus reviews every line; the result-changing default is
the user's decision after the measurement (same procedure as V2.4d item 3).

## What to build

1. `EngineConfig.intrabar = "sl_first"` (default, today's behaviour exactly) | `"m1"`.
2. With `"m1"`, only for an **ambiguous** base candle — the SL and at least one not-yet-filled TP
   (with the TP penetration rule of V2.4d 3: `tp_penetration`, `short_tp_on_ask`) both reached,
   or a limit-fill candle that also reaches a TP — the engine replays the M1 candles inside that
   base candle in time order with the same rules (gap at an M1 open fills at the open, SL /
   TP / break-even levels as on the base candle, partial TPs in order) and takes the first event.
   If SL and TP are both inside one **M1** candle, SL first (still conservative). M1 candles
   missing for that base candle -> fall back to SL first and count it.
   - Fills keep today's prices (TP at its level, SL at the stop or the gap open); only *which*
     level comes first changes. The exit time is the close of the M1 candle where it happened,
     but the trade is still processed at the base candle's close (no lookahead: the base candle
     has closed; nothing after it is read).
   - Break-even after TP1 inside the same base candle: decide on M1 too (TP1 on M1 candle k,
     then the remaining part is checked from candle k + 1).
3. **M1 access without loading all M1**: the engine gets an optional `intrabar_source`
   (callable: symbol, start, end -> M1 candles), supplied by the runner from the symbol's adapter
   with a small per-day cache; strategies with a 1m base timeframe never need it. The chart's
   trades overlay and the live bot are not changed (the overlay runs through the runner already
   for strategies 2-7; strategy 1's `run_strategy` passes the source too).
4. Counters per run: ambiguous candles, resolved TP-first, resolved SL-first, fallbacks
   (summary keys and a `trades.csv` column `intrabar` = "", "tp_first", "sl_first", "fallback").
5. Setting in the settings panel / grid files like the other `engine.*` leaves; spec in
   `docs/ARCHITECTURE.md` › How a backtest steps through time and `docs/risk-management.md`.
6. **Measurement** (no default change): `scripts/measure_intrabar.py` runs the golden setup
   (`tools/golden.py`, 7 strategies, 2023, current defaults) with `sl_first` and `m1` and writes
   `results/intrabar.md` + `.csv`: per strategy trades, wins, net R, avg R, ambiguous candles,
   TP-first share, fallbacks, change vs default. Run it (log file) and put the table in the report.

## Rules

Spec first, the test-case list at the top of the new test file (long and short; TP-first and
SL-first on M1; both in one M1 candle -> SL; gap on an M1 open; two TPs and break-even in one
base candle; limit-fill candle; missing M1 -> fallback; `sl_first` identical to today; a 1m-base
strategy unaffected), failing tests, then code. With the default the golden lists must stay
identical (`python -m backtester.tools.golden --check > results\golden_t03.log 2>&1`). No
lookahead: M1 candles read only inside the base candle that has just closed. Never edit
`src/backtester/live/`. Long runs to log files.

Done = full suite green (`pytest -q > results\pytest_t03.log 2>&1`), golden identical,
`ruff check .` clean, the measurement table in the report. Report: files changed, test count,
decisions the spec did not settle, open questions.

## Answers from Opus (your questions of 20:38)

1. Yes. A base candle is also ambiguous when TP1 is reached and, with break-even after TP1 on,
   the break-even level is reached in the same candle (your example: replay it on M1; TP1 on M1
   candle k, then the rest from candle k + 1 against the break-even stop). Today's close-based
   rule stays for `sl_first`.
2. Yes. In the M1 candle that fills the limit only the SL counts (as `on_fill_candle` today);
   TPs count from the next M1 candle.

Write both into the spec. Go ahead with the brief.

## Answer from Opus (your question of 21:02)

Yes: with `intrabar = "m1"`, a replayed limit entry gets `entry_time` = the close of the M1
candle that filled it (so no exit can precede its entry); the strategy's callbacks and the
order's decision stay at the base candle's close (`entry_candle` unchanged). Write it into the
spec, finish the limit replay (remove the `NotImplementedError`), make the 4 failing tests
pass, rerun the measurement and the golden check. Everything else you built stays as reported.
