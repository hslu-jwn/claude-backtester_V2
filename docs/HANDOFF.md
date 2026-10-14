# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

## Last session (2026-10-14): strategy 4, trend following after Kaufman; swap costs
- **Source:** the user's request referred to Kaufman, *Trading Systems and Methods*, pp. 152-154 and "Appendix B" pp. 329-332.
  In the 5th edition (2013), which the user supplied, pp. 152-154 cover Dunnigan's thrust method / Ruggiero's Dunnigan
  trend, and pp. 329-332 (ch. 8) cover band vs delay, calculation period, n-day momentum and MPTDI. There is no
  Appendix B. Spec: `docs/strategy-trend-following.md` (book findings and Claude's choices marked).
- **Built:**
  - **Engine:** signal exits (`Strategy.exits()`, `ExitReason.SIGNAL`) and orders without a TP.
  - **Swap:** one night per 17:00 New York rollover, triple weekday, net R only, `TradeResult.swap_r`,
    `CostConfig.swap_enabled`.
  - **Strategy 4:** `strategy/trend_following/`, signals breakout / sma (+ ATR band) / momentum / kama /
    dunnigan, 3 x ATR(20) stop, stop-and-reverse, 15m-1d.
  - **Grid:** `python -m backtester.tools.trend_grid` with `--swap-file`.
  - 1206 tests pass.
- **FTMO swap rates (MT5, 2026-10-14)** are recorded in ROADMAP 10.4 and in `results/ftmo_swap_2026-10-14.json`
  (git-ignored; recreate it from the ROADMAP table if it is missing).
- **Result (ROADMAP 10.3 / 10.4):**
  - Without swap, 4h / 1d and 1h sma + band are slightly positive. With FTMO swap, nothing on 15m-4h is
    positive, because XAUUSD longs cost $61 per lot per night.
  - Robustness check on XAUUSD + GBPJPY + NAS100 (chosen after the fact), 1h sma 40-60 x band 0.75-1.25: all 9
    are positive with swap (+13 to +107 R). But each symbol is positive in only one half (XAU in 2023-26,
    GBPJPY in 2020-22), and the drawdown is 47 R against 1.3 R per month. Not tradeable.
- **MT5:** `python -m backtester.tools.mt5_info` failed with "Authorization failed". A plain
  `mt5.initialize()` against the running terminal worked after the user logged in by hand in MT5. The login
  saved in Settings ⚙ → Trading is probably outdated. The user posted a trial password in the chat; Claude did
  not use it and advised changing it.

## Accepted by the user (do not ask again)
- Everything built this session, as it is ("End." 2026-10-14). ROADMAP 10.1-10.4 ☑.
- Earlier: tests first, small commits, no PR; strategy 1 paused, strategy 3 dropped; sweep option defaults
  stay off; temporary Sweep menu stays.

## Open (needs the user)
1. **Strategy 4:** drop it, or keep it as a filter (e.g. strategy 2 trades only in the direction of the 1h trend)?
2. **Swap defaults:** should FTMO's rates become the app's default `SymbolCosts`? That would change the net
   results of strategies 1-3. Until then the rates are 0.
3. **Next:** the cost filter (skip entries where costs are a large share of the stop), or new edge sources
   (session opening-range breakout, previous day / week high-low sweeps, regime filters).
4. **Login:** update the MT5 login in Settings ⚙ → Trading (the user does this; never ask for credentials in chat).
- **Known issues:**
  - ruff: the old RUF007 in `core/series.py`.
  - `tools/no_wick_grid.py` is not ruff-formatted (unchanged since strategy 3).
  - An untracked stray file `C:Usersjusti.claudeclaude-notify-signalsstop` in the repo root, from a notify
    hook. It is not the project's; ask before deleting.

## Next step (suggested)
Ask the open questions 1-3 together, then follow the user's choice (spec -> tests -> code).

## First prompt for the next chat
`Continue.`
