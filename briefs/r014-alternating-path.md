# Brief: strategy 9 `alternating_path` (submission M15_ALTERNATING_PATH_BATCH v0.2.0)

Model: Codex gpt-6.1-sol medium. Read `AGENTS.md` first. Work test-first.

## Source

Claimed submission (read-only, never copy it into V2):
`../Shared_Interface/queue/claimed/M15_ALTERNATING_PATH_BATCH__v0.2.0.json`,
sha256 `d09d44b96cde33f45b718803eb385cc9a9fd908641d06148ea47de61acff31c5`.
Template to follow closely: strategy 8 `london_fix` (`src/backtester/strategy/london_fix/`,
`docs/strategy-london-fix.md`, `tests/strategy/london_fix/`, `research/grids/london_fix.toml`).
It already does M1 signal-close entries, an ATR stop, a time exit through `Strategy.exits()`,
and the six FX symbols.

## Files you may touch

- new `src/backtester/strategy/alternating_path/` (`__init__.py`, `config.py`, `strategy.py`)
- `src/backtester/strategy/registry.py` (one entry `alternating_path`)
- new `tests/strategy/alternating_path/test_alternating_path.py`
- new `docs/strategy-alternating-path.md` (spec, structure like `strategy-london-fix.md`:
  Submission section with id / version / sha256, quotes, rule -> config/code/test mapping table,
  Assumptions section with A1-A9 below verbatim in substance)
- new `research/grids/alternating_path.toml`
- `AGENTS.md` spec table: one row for the new spec (strategy count 7 -> keep wording consistent)
- any registry/settings test that enumerates all strategies, only to add the new one

Never touch `src/backtester/live/`, `.env`, the engine, costs, or defaults of other strategies.
No commits, no branches, no servers.

## Rules (the submission, with Opus's decided assumptions)

Base timeframe M1, `timeframes = (Timeframe.M1,)`, `uses_session_break_even = False`. Symbols:
EURUSD GBPUSD AUDUSD NZDUSD USDCHF USDCAD; other symbols raise `UnsupportedSymbolError`
(check how other strategies do it) or produce no orders, like london_fix.

- **A1 M15 bars.** Built inside the strategy from completed M1 candles in 15-minute buckets
  `[hh:00, hh:15)` etc. (UTC buckets equal Europe/London wall-clock buckets, London's offset is a
  whole hour). A bar is valid only if its bucket has exactly 15 M1 candles with consecutive
  `ts` one minute apart, each with finite positive OHLC, `high >= max(open, close)`,
  `low <= min(open, close)`, `high >= low`. Bar OHLC = first open, max high, min low, last close.
  An invalid or incomplete bucket produces no bar (not observed). V2's cache has unique
  timestamps, so duplicates cannot occur; no extra check.
- **A2 ATR(96) Wilder, observed sequence.** Over valid bars only. `TR_i = max(high, prev_close)
  - min(low, prev_close)` with `prev_close` = the previous valid bar's close, across any gap.
  The first valid bar has no TR. Seed = mean of the first 96 TRs; then
  `ATR_i = (95 * ATR_{i-1} + TR_i) / 96`. The ATR used at signal bar t is the one through t-1
  (frozen before t), so the first possible signal is the 98th valid close. Require finite > 0.
- **A3 Event.** At valid bar t, the bars t-4..t (5 closes) must be physically adjacent: each
  bucket start exactly 15 minutes after the previous one. `delta_j = close_{t-4+j} -
  close_{t-5+j}`, j = 1..4; every delta nonzero (exact float zero invalidates) and signs strictly
  alternate. `path_activity = sum |delta_j| / atr_prior >= 1.0` (equality qualifies).
  `last_direction = sign(delta_4)`. `FOLLOW_LAST` trades `last_direction`, `FADE_LAST` trades
  its negative. One code path, parameterized by side.
- **A4 Eligibility.** London weekday (Mon-Fri, London date), M15 close time in London between
  09:00 and 13:45 inclusive, and `close time + holding_minutes <= 15:00` London.
- **A5 Entry / stop.** Market order at the close of the M1 candle that completes bar t (its
  close = bar t's close; `Order.entry = candle.close`, `limit_fill=False`). Stop =
  `entry - side * stop_atr_multiplier * atr_prior` (multiplier fixed 1.0). No take profit. The
  engine fills at that close and checks stops from the next M1 candle (entry candle cannot stop
  the trade; shorts trigger on the ask by the engine's default `short_sl_on_ask`). Do not change
  the engine.
- **A6 Time exit.** Due at `signal close + holding_minutes`. Request the exit through
  `exits()` on the first M1 candle whose close time is >= due (normally exactly due). The engine
  processes stops before `exits()`, so a stop in the due bar wins (spec priority STOP_LOSS before
  TIME_EXIT). Missing M1 candles inside (entry, due] are not handled in the strategy; they are
  counted after the run from the cache (data-integrity report, a later step).
- **A7 One position per symbol.** While the strategy's trade is open (until `on_trade_closed`
  or `on_order_skipped`), no new signal; no pyramiding, no re-entry from overlapping events.
  Features (M15 bars, ATR, the 5-close window) keep updating while in a trade.
- **A8 Cells.** The four cells (`response_mode` FOLLOW_LAST / FADE_LAST x `holding_minutes`
  30 / 60) are separate grid variants, each its own run, so their state is isolated. Money
  sizing (0.25 %, 1.5 % cap) is the existing account layer; the strategy outputs R only.
- **A9 Warm-up.** `min_warmup_days` large enough for 98 valid M15 bars over a weekend (e.g. 5).

Config (frozen dataclass, defaults = submission baseline, validated in `__post_init__`):
`response_mode: str = "FOLLOW_LAST"` (only FOLLOW_LAST / FADE_LAST), `holding_minutes: int = 60`
(only 30 or 60), and fixed fields `aggregation_minutes = 15`, `alternating_changes = 4`,
`path_activity_atr_min = 1.0`, `stop_atr_multiplier = 1.0`, `atr_period = 96`,
`first_signal_london = "09:00"`, `last_signal_london = "13:45"`, `exit_deadline_london = "15:00"`
(fixed values: reject any other value, like london_fix's `side_map`). If the settings/grid layer
cannot carry a string field, say so and stop rather than inventing an encoding.

Grid `research/grids/alternating_path.toml`: like london_fix.toml, `[submission]` with the
id / version / sha256 above and `experiment_id = "M15_ALTERNATING_PATH_BATCH__v0.2.0__DEVELOPMENT__1"`,
`[base]` the baseline, `[grid] response_mode = ["FOLLOW_LAST", "FADE_LAST"]`,
`holding_minutes = [30, 60]` (exactly 4 variants), `min_trades = 300`.

## Tests (hand-built M1 candles, write them first)

1. M15 aggregation: complete bucket -> OHLC correct; 14 candles -> no bar; a non-consecutive ts
   -> no bar; broken OHLC in one candle -> no bar.
2. ATR seed at the 96th TR and the recursion value (small hand numbers); a gap bar uses the
   previous observed close; ATR frozen at t-1 (bar t's TR not in the ATR used at t).
3. Event: +,-,+,- alternating with activity exactly 1.0 ATR -> signal; 0.999 -> none; a zero
   delta -> none; two same signs -> none; a missing bucket inside t-4..t -> none.
4. FOLLOW_LAST long when delta_4 > 0, FADE_LAST short for the same path; stop = entry -/+ ATR.
5. Eligibility: signal at 09:00 and 13:45 London fire; 08:45 and 14:00 do not; summer and winter
   (DST) both; Saturday none; holding 60 at 13:45 ok (14:45 <= 15:00).
6. Time exit requested at exactly due for 30 and 60; no new order while a trade is open;
   a new order possible after `on_trade_closed`.
7. No-lookahead: feeding more future candles never changes orders already emitted, and the
   strategy reads only `SeriesView`.
8. Config validation: bad response_mode, holding 45, changed fixed fields -> ValueError.
9. One engine-level test (see london_fix tests for how they run the engine): a short entry,
   stop on the next candle, and a time exit at due.

## Done =

`pytest tests/strategy/alternating_path` green, the registry / settings tests green, `ruff check`
and `ruff format --check` clean, the grid file loads with the research runner's parser
(`--dev-only` dry parse if available; do not run the sweep). Report: files changed, test
results, any rule you could not map without guessing.
