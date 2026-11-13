# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history
in git, results in `research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-12, `End.` of the multi-symbol / research / two-leg session)

- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. No lane
  worktrees. Full suite 5,852 passed, 14 skipped, 4 xfailed (`-n 8`, about 2.5 min); ruff clean; golden
  13 / 13 identical (strategy 14 excluded: its 2023 golden year is in its unspent test period).
- **Built today:** multi-symbol 1b (strategy-declared references); strategy 14 `us_close_de_open` and
  its gates; pytest-xdist (`-n 8` is the standard); `ai_dispatch --search` (Codex web search, read-only
  tasks only); `harvest check` reads PDFs (`pypdf`); A3: one gates tool `tools/gates.py` from a `[gates]`
  table in the grid, with `--controls N` (pipeline controls), one block bootstrap in
  `analytics/bootstrap.py`; two-leg trades 2a-1 to 2a-3 (`strategy/group.py`, `engine/group_trade.py`,
  `engine/group_backtest.py`, `group_runner.py`; one `trades.csv` row per group).
- **Research today: 13 looks, all killed or rejected, no live lead.** Strategy 14 (development run),
  lead-lag L15-L18, I-67 month-end, I-51 trend portfolio, H13f CAP, I-69 bitcoin expiry week, I-70 opex
  week, pairs P01 / P02 (pre-build screens), funding fades (by cost). Families closed: lead_lag,
  turn_of_month, trend, daily_reversal. Why: `knowledge/topics/cost-wall.md` (multi-day holds lose to
  FTMO swap, intraday to the spread). 5 harvest batches (26 tasks, 13 ideas); since batch 4 both
  canaries pass. Ledger: 60 rows; trial log copied to `research/trials.jsonl`.
- **Futures venue:** allowed by the user (AGENTS.md). Cost model and choice in `docs/futures-venue.md`
  (IBKR Pro Ireland: CL / BZ USD 2.35, MCL USD 0.85 per side, verified on IBKR's pages). History: Norgate
  trial only covers 2024-2026; the user decided not to buy, so the P01 WTI / Brent futures check is parked.
- **Uncommitted, not Opus's:** `src/backtester/tools/notify.py` (hook trace log lines); the user decides.

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-12: pytest-xdist `-n 8` standard; one research loop at a time; always propose next steps;
  auto mode (pick and start the next step; still ask for the one-time test, defaults, dependencies,
  downloads); strategy 14 run; harvest web probe + batches and `pypdf`; two-leg trades B (2a built,
  2b deferred, 2c only on the user's go); futures venues allowed; broker / data source chosen by Opus;
  no Norgate subscription.
- 2026-11-11: review picks B1 / B5 / B8 / B9, one ledger, parked (not dropped) ideas without mechanism.

## Open (needs the user)

1. One-time MT5 tests still pre-registered: strategy 4 on GBPJPY; gap momentum in quiet sideways
   markets. Only on your go.
2. **B4 dividends:** message ready to send in `docs/ftmo-dividend-question.md` (2026-11-13). FTMO's dividend booking on index CFDs is unverified (the demo export and web
   lookups settle nothing); the user asks FTMO support, then Opus adds the rule test-first.
3. ~~GBPUSD spread~~ done 2026-11-13 (the user: "do all"): factor 1.33 (without the NY-hour-18 reopen,
   10.25x alone). Rollover fixes a + b + c done 2026-11-13 (the user's go): fill spread = the bar that
   just closed, gate 7 window 16:55-18:00 NY; factors GBPJPY 1.09 / GBPUSD 1.38 (the user's go).
   **Open:** symbols without a table pay one fixed spread at every hour, the rollover hour included;
   proposal A / B / C for the user in `docs/spread-table-extension.md` (2026-11-13).
4. **Direction of research:** cheap ideas are used up under FTMO costs. Options: intraday events with
   >= 20 bp per event (batch 5 found none), futures data (needs a paid history source), or pause
   research and work on app / portfolio items. 2026-11-12 (Continue.Research Test=auto): I-68 oil carry
   closed on power, so no carded idea is left. **Decided by the user 2026-11-12: pause research,
   work on `Continue.Code` items** (research resumes with a new idea source or data).
5. Low priority: stressed-cost p90 refresh (gate 7 window done 2026-11-13);
   (data fixes 13.12-13.18 accepted by the user 2026-11-12; MT5 GBPUSD 2019 quarantined, 149 days,
   `docs/data-fix-check.md`; USDCHF early 2015 borderline, left as it is).

## Next step

1. Research only with a new idea source or a decision on Open 4; the harvest pipeline works
   (`idea-harvest` skill, `ai_dispatch --search`, CA-bundle note for `harvest check` in the skill).
2. Code items left (ROADMAP V2.10): A9 results out of the specs (deferred: rules interleave results),
   shrink the slowest tests; two-leg 2b when a pair idea survives a screen.

## First prompt for the next chat

`Continue.Code` or `Continue.Research` after deciding Open 4 (answer Open 2-3 when convenient).
