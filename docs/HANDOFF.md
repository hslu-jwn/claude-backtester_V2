# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

## Last session (2026-10-13/14): strategy 3, no-wick candle in the trend
- **Rules (user, spec `docs/strategy-no-wick.md`):** uptrend: a green candle with no lower wick is a long
  signal; downtrend: a red candle with no upper wick is a short. SL beyond the last confirmed swing of the entry
  timeframe + 10% buffer of the distance, TP 1R, no break-even, no position cap, no filters. Trend = next higher
  timeframe (5m→15m, 15m→1h, 30m→4h, 1h→4h) or the same timeframe. Entry: close, or limit at the candle's open
  (`body_end`) or middle, expiry 6 candles.
- **Built:** `strategy/no_wick/` (config, strategy), registry entry `no_wick`, settings-panel groups, engine
  support for limit fills (`Order.limit_fill`: fills at its level inside the candle, a gap fills at the open or
  drops the order if beyond the stop, in the fill candle only the SL counts), `python -m
  backtester.tools.no_wick_grid`. 1064 tests pass; ruff clean except the old RUF007 in `core/series.py`.
- **Result (ROADMAP 9.1):** all 24 variants (5m / 15m / 30m / 1h × higher / same × close / body_end / middle)
  are negative gross and net on 5 symbols 2020-2026, in 2020-22 and 2023-26 alike. Close entry gross about
  -0.03 R per trade, costs another 0.1-0.14 R on 5m / 15m. `body_end` worst (win rate 33-36%). The user dropped
  the strategy.
- Not built: chart Trades overlay for strategy 3 (ROADMAP C.3); cancelling pending limit orders on a trend flip
  (a rule change, his call).

## Accepted by the user (do not ask again)
- The ROADMAP order and the cleanup backlog; C.1-C.4 and 8.6a done.
- Tests first, small commits on the session branch, no PR unless asked.
- Strategy 1 is paused; strategy 3 dropped. A BOS in a downtrend with the trend is no BOS, so a sweep without a
  BOS is no sweep.
- The with-trend sweep scene on 4h (no sweep) is fine; defaults of all new options stay off.
- The temporary Sweep menu on the chart stays; doji share stays off; ROADMAP 8.3 / 8.4 stay unreleased.
- "End." accepted everything built in this session as it is.

## Open (needs the user)
- **A new strategy**, which the user wants to try next (he has not described it yet). Start with `Continue.`,
  ask him for the rules, write the spec first, tests first, one folder `strategy/<name>/` (copy `_template/`).
  Then compare with `tools/no_wick_grid.py` as the pattern (variants, 2020-22 vs 2023-26).
- After that, his earlier order: (1) cost-aware filter (skip entries where spread + commission is a large share
  of the stop; costs dominate strategies 2 and 3), (2) new edge sources with the study framework (session open
  range breakout, previous day / week high-low sweeps, regime filters).
- Parked: structure cut; ROADMAP 8.3 / 8.4 window settings and best-time tag removal (wait for his go); 8.6b /
  8.6c / 6.1 as before.

## Next step (suggested)
Ask the user for the new strategy's rules (all open questions at once, numbered), then spec -> tests -> code.

## First prompt for the next chat
`Continue.`
