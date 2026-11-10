# Brief: hypothesis 15 "daily failed 20-day extreme" (Turtle Soup) as setup `TS` of strategy 13 `daily_reversal`

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). Test first; never
weaken a test. Do NOT run the grid (pre-registration first; Opus commits before any run). Existing setups
E8 / CAP and their results stay untouched (`docs/strategy-daily_reversal.md`).

## Source (`knowledge/research/reports/2026-11-10_idea_harvest_round2.md` idea 1; Raschke / Connors "Turtle Soup",
https://therighttrader.com/learn/trading-strategies/turtle-soup). Label PRACTITIONER. Related falsified
families: session zone sweeps (intraday), Connors E8 / CAP: say how TS differs in the spec.

## Rule (write a "Setup TS (hypothesis 15, pre-registered 2026-11-10)" section in the spec)

- Daily bars: FX / metals: 17:00 New York to 17:00 New York (weekend stubs excluded, as timed_hold's
  ATR); indices: the regular cash sessions already in the strategy.
- Long: today's low < the lowest low of the previous 20 days, the bar holding that 20-day low is at least
  4 sessions old, and today closes above that old low; skip if today's range > 3 x ATR(14). Enter at the open
  of the first M1 candle of the next session (the engine's close-price entry at that candle's close is
  acceptable if it is how the strategy enters; state which). Stop one tick below today's low; exit at the next
  daily close (or the stop). Short mirrored. Skip a day with both signals. One position per symbol.
- Symbols: EURUSD (primary), GBPUSD, USDJPY, AUDUSD, XAUUSD, US500, NAS100 (pooled, one parameter set).
- Cells (fixed): lookback {20, 55} x exit {next daily close, 2 sessions} = 4 cells; primary lookback 20, next
  close. Swap counted (one or two nights).
- Gates (fixed now, `timed_hold_gates --mode daily_reversal`-style pooled): pooled net R > 0 normal and
  doubled costs; both halves; at least 5 of 7 symbols net > 0; best 5 dates removed > 0; pooled bootstrap
  2.5 % > 0; min 150 trades pooled; integrity; long / short reported.

## Code

Config switch `setup = "TS"` and its fields (defaults keep E8 behaviour), FX / metal daily session, tests
(hand-built 20-day low pattern, age >= 4 rule, close-back-above, range filter, both-signal skip, exits, no
lookahead), grid `research/grids/daily_reversal_ts.toml` (diagnostics off), gates command (extend the
existing daily_reversal mode with the 7-symbol pool / 5-of-7 breadth if needed). `python -m pytest
tests/strategy/daily_reversal tests/tools -q` green, ruff clean. Report files, assumptions, commands.
Pre-authorized: for minor ambiguities choose the more conservative option and list it as an assumption.
