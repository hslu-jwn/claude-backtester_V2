# Brief: strategy 13 `daily_reversal` (Connors daily reversal setups on indices): spec + code, no run

You work in the lane worktree `bt-lane-daily_reversal` (branch `lane/daily_reversal`). Read `AGENTS.md`
first; hard limits apply (no commits, no servers, no `live/`, no `.env`). A lane may change only
`src/backtester/strategy/daily_reversal/`, `docs/strategy-daily_reversal.md`, `tests/strategy/daily_reversal/`,
`research/grids/daily_reversal*.toml` (`lanes check daily_reversal`). Registry entry by the coordinator.
Do NOT run the grid (pre-registration first).

## Idea (source: `knowledge/research/reports/2026-11-10_idea_harvest_broad.md` ideas 2 and 3; Connors rules
as reproduced in https://michaeltanphd.com/wp-content/uploads/2021/02/technicalstrategies_2002.pdf pp. 26-28)

Label PRACTITIONER. Related family already falsified: RSI(2) mean reversion (`docs/strategy-timed-hold.md`
› Hypothesis 10); these are different setups (failed breakdown then buy-stop trigger), say so in the spec.

## Rules to specify (`docs/strategy-daily_reversal.md`; copy `strategy/_template/`)

- Daily bars from M1 = regular cash sessions per index (as `timed_hold` builds them: US500 / NAS100 / US30
  09:30-16:00 New York, GER40 09:00-17:30 Berlin, UK100 08:00-16:30 London, JP225 09:00-15:00 Tokyo,
  AUS200 10:00-16:00 Sydney). Entry by buy / sell stop on M1 inside later sessions, filled at the stop or the
  worse open (gap), stop and exits as below; one position per symbol.
- Setup E8 (8-day reversal, long; short mirrored): day 1 low < lows of the prior 7 days; day 2 high > day 1
  high; one of days 3-6 has low < day 2 low; after that day's close, buy stop one tick above day 2 high,
  valid 4 sessions; stop one tick below day 2 low (skip if not below entry).
- Setup CAP (capitulation, long only): low < previous 9 lows, range > each previous 9 ranges, close in the
  top quarter of the range; next session buy stop one tick above the signal high, valid 2 sessions; stop
  one tick below the signal low.
- Exit: target `target_r` x R or after `hold_sessions` sessions at the session close, whichever first.
  Cells: setup {E8, CAP} x target_r {2.0, none} x hold_sessions {5} = 4 cells, pooled over the 7 indices
  (one parameter set). Primary: E8, target 2.0. Multi-day holds: swap charged (triple day).
- Gates (fixed before any run): pooled net R > 0 normal and doubled costs; both halves; at least 4 of 7
  indices net > 0; best 5 dates removed > 0; pooled bootstrap 2.5 % of mean net R > 0; min 80 trades
  pooled; integrity (missing exit candle / invalid candles). Long and short reported separately (bull-market
  drift 2015-2021).

## Code

Strategy folder, config dataclass (defaults = primary cell), tests first (hand-built daily patterns for E8 and
CAP, order expiry, gap fill at the open, stop below entry check, target vs timed exit, swap days, no
lookahead), grid `research/grids/daily_reversal.toml` (diagnostics off). Note what a gates tool needs.
`python -m pytest tests/strategy/daily_reversal -q` green, ruff clean. Report files, registry line, assumptions.

## Decisions by Opus (2026-11-10, after Codex's questions, before any code or run; record as assumptions)

1. `hold_sessions` counting starts with the session after the fill session; the timed exit is at the close
   of the `hold_sessions`-th full session after the fill session.
2. If a long and a short entry level are both crossed inside the same M1 candle, skip both (no trade).
3. No engine change: the strategy emulates the stop entry. It watches M1 candles; the first candle whose
   high >= buy level (low <= sell level for shorts) triggers a market entry at that candle's close (the
   engine's close-price entry, costs and slippage as usual). Conservative vs a real stop fill (usually a
   slightly worse price); a candle that opens beyond the level also fills at its close. State this in the spec.
4. Overlapping setups: at most one pending setup per direction and symbol; a newer qualifying setup of
   the same direction replaces (cancels) the older pending one. No new setup is armed while a position is
   open. Any FURTHER minor ambiguity: Opus pre-authorizes you to choose the more conservative option (fewer
   or later trades, worse fills) and list it under Assumptions for review; stop only for a rule that
   changes the hypothesis itself.
