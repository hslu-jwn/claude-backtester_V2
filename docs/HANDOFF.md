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

## Last session, second chat (2026-10-14/15): books, knowledge base, research tools, spread table
- **Knowledge base** `knowledge/` (index `README.md`, `books/` notes of Kaufman *Trading Systems and Methods*,
  Douglas, Hougaard, Volman, Aziz, Coulling, `topics/`, `ideas.md` backlog with status, `reading-brief.md`;
  pointer and the trigger **`Continue.Knowledge`** in CLAUDE.md). Background, not rules.
- **Built (all accepted by the user, "End." 2026-10-15; ROADMAP ☑):**
  - **6.4 robustness report** `analytics/robustness.py` (+ `trend_grid` `robustness.csv`, `grid.csv`).
  - **6.5 time splits** (hour, weekday, month part, NY window) on the results page.
  - **6.6 MT5 history**: `MaxBars` set to Unlimited in common.ini by Claude (backup next to it), MT5 restarted;
    FTMO serves M1 with tick volume and spread from 2015-16 (FX, gold) and 2017-12 (indices).
  - **6.7 spread table** `engine/spread_table.py`, `CostConfig.spread_table` (off by default),
    `tools/spread_table.py` -> `data/spreads/` (git-ignored), `trend_grid --spread-table`.
  - **11.1 noise study**: all markets near random-walk noise; indices not noisier; noise decides the sign of
    strategy 4's gross R, not enough to pay costs. Noise gate I-02 dropped by the user.
  - **11.2 open / gap / trend-day study**: gap fill is mostly the random-walk touch; no first-30-minute
    continuation; 7 % trend days; one candidate: gaps of 0.1-1 ATR touch the previous close before the mirror
    level 44 vs 37 % (NAS100), 43 vs 38 % (US500), same sign in both halves.
- **No edge found yet.** Books' claims mostly not reproduced; strategies 1-4 negative (other chat).
- **Facts to remember:** histdata has no volume (MT5 tick volume only); FTMO spreads moved a lot over the
  years (gold 0.07 in 2021-23, 0.42 in 2026; NAS100 0.6 -> 1.45) and some years before 2022 look wrong
  (GBPUSD 2020-21 5 pips); server clock NY + 7 h (920 of 948 weeks, misses 2020-03..2021-03).
- 1449 tests pass; ruff: only the old RUF007 in `core/series.py`.

**Open (needs the user), this chat:**
1. Spread table: make it the default (changes the net R of every strategy)? From which year (the years before
   2022 look wrong)? Also: add a news mark-up later (needs a calendar)?
2. Gap fade (ROADMAP 11.4): Claude decided it is next. Entry at the open with target previous close and stop at
   the mirror level is the simplest form: should the first version also use the opening range (wait 5-30
   minutes) or stay at the open?
3. Volume (I-44): FTMO tick volume exists from 2015-16; worth an A/B test of the price-only ideas with and
   without volume, or park it until an idea survives without volume?
4. Should the book research continue with more books (technical, price-only: e.g. on intraday statistics,
   market microstructure, systematic trading)? Which titles do you have?
5. 11.3 time-of-day drift (XAUUSD / FX): keep it after 11.4, or drop it (the indices' open study showed
   mostly no effects)?

**Next step (Claude's decision):** write `docs/strategy-gap-fade.md` (11.4), tests first, run with the
spread table and the robustness report; first prompt `Continue.Knowledge`.

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
`Continue.` for the strategy work (strategy 2 area), `Continue.Knowledge` for
the research from the knowledge base (gap fade 11.4 next).
