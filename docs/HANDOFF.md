# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

**Two sessions share this checkout (2026-10-14/15).** Besides this one, a second session works on Phase 6 / 11
(robustness report 6.4, time splits 6.5, noise study 11.1; see their ROADMAP entries and commits). Before committing:
`git status` / `git pull`, stage only your own files, never `git add -A` over the other session's changes. If that
session ends after this one, it may rewrite this file: merge both sections instead of overwriting.

## Last session (2026-10-14/15, strategy 2 costs and filters): swap defaults, trend filter, rollover close, cost filter
- **Swap defaults:** FTMO's MT5 rates of 2026-10-14 are now the default `SymbolCosts` (user, 2026-10-14;
  risk-management.md › Costs). Net results of every strategy now include swap.
- **Strategy 2 trend filter** (user: keep strategy 4 as a filter): `NyIndexSweepConfig.trend_filter`, off by default;
  signals only in the direction of the last SMA ± band x ATR cross (shared class `SmaBandCross` in
  `strategy/trend_following/indicators.py`, strategy 4 uses it too).
- **Close before the rollover** (user: test it): `close_before_rollover`, off by default, closes at **16:15 ET**
  (`rollover_close_minutes` 45) because the histdata index feed has no candles 16:15-18:00 ET. Rollover time constants
  moved to `sessions.py` (layer rule: strategies may not import the engine).
- **Cost filter** (user: build it): `CostConfig.max_cost_r`, off by default; the engine skips an order whose spread +
  commission is above that many R of the stop and calls `Strategy.on_order_skipped` (strategy 2: no trade counted,
  setup stays open; strategy 4: flat). Strategies 1 and 3 have no hook (noted in the spec).
- **Results (ROADMAP 10.5):** strategy 2, 2020-26 with swap: -135 R; best combination close 16:15 + 15m filter -17 R,
  close + cost 0.10 -50 R. Swap was -74 R (654 trades held overnight). No edge -> **strategy 2 parked by the user
  2026-10-15**. CSVs: `results/s2_trend_filter/` (git-ignored).
- 1348 tests pass.

## Accepted by the user (do not ask again)
- Everything built this session ("End." 2026-10-15); ROADMAP 10.5 ☑. FTMO swap rates as defaults. Trend filter code
  stays (off). Strategy 2 parked.
- Earlier: tests first, small commits, no PR; strategy 1 paused, strategy 3 dropped, strategy 4 parked; sweep option
  defaults stay off; temporary Sweep menu stays.

## Open (needs the user)
1. **Next:** Claude recommended the day-trade strategies of Phase 11 (opening-range breakout I-07/I-08, compression
   break I-33) with the cost filter (I-45) and the free-path filter (I-37); no overnight holds, so no swap. The order
   agreed in Phase 11 (after 6.4 / 6.5 / the studies) is the other session's area; check its state first.
2. **Login:** update the MT5 login in Settings ⚙ → Trading (the user does this; never ask for credentials in chat).
- **Known issues:**
  - ruff: the old RUF007 in `core/series.py`.
  - Two hung `python.exe` processes running a scratch script `s2_filter.py` (from a crashed run 2026-10-14) may still
    be open; harmless, close them in Task Manager (auto mode did not allow Claude to stop them).
  - Strategy 2's `decisions` list still shows an order the cost filter skipped as taken (inspection only).

## Next step (suggested)
Read the other session's latest entries (ROADMAP 6.4, 6.5, 11.x), then ask the user which day-trade strategy to spec
first (spec -> tests -> code).

## First prompt for the next chat
`Continue.`
