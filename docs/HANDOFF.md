# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history
in git, results in `research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-13, `End.` of the costs / challenge path / harvest session)

- **Location (moved by the user 2026-11-13):** umbrella `X:/Daten/02_Projekte/01_Laufend/backtester-claude`,
  V2 in `backtester-claude_V2`. Editable install re-pointed; the Telegram hooks in the user-level
  `settings.json` point here. Claude's memory notes still sit under the old project key (first job below).
- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. No lane
  worktrees. Full suite 5,936 passed, 14 skipped, 4 xfailed (`-n 8`); ruff clean; golden 13 / 13 identical.
- **Built 2026-11-13:** challenge path simulator (`risk/challenge_path.py`, CLI, Results tab; accepted);
  costs: fills pay the spread of the bar that just closed (`engine/costs.fill_spread_time`), gate 7 window
  16:55-18:00 New York, live factors GBPJPY 1.09 / GBPUSD 1.38 (+ GER40 1.07, UK100 1.09, UKOIL 1.09,
  US30 1.10, USDCAD 1.09, USOIL 1.08), hourly spread table for 32 symbols from the MT5 cache
  (`docs/spread-table-extension.md`; 2020-21 placeholder years of seven FX symbols dropped); harvest
  pipeline fixes (`tools/harvest.py`: unreadable pages parked `unfetchable`, `check` appends, seller check
  near the quote and not on papers; canary from the open `fx_carry` family).
- **Research 2026-11-13:** harvest batches 6-9 (32 tasks, every source type): one idea screened, I-71 UK100
  review-auction short, killed on t 2.16 (net +9 bp, sign replicates out of sample, ~8 events a year).
  Cost wall refreshed (`knowledge/topics/cost-wall.md` §3: cheapest at a 0.5 daily-ATR stop now US30
  0.010, GER40 0.012, NAS100 0.023, EURUSD 0.027 R). Ledger 82 rows; trial log copied to `research/`.
- **Uncommitted, not Opus's:** `src/backtester/tools/notify.py` (hook trace log lines); the user decides.

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-14: one-time test of the frozen I-73 rule on 2021-09..2026-10 ("Yes, run I-73 test").
- 2026-11-13 (later): download of 15 more Binance USD-M perps as 1m klines + funding ("Yes, 15 perps").
- 2026-11-13: challenge path simulator accepted; GBPUSD 2019 quarantine and data fixes 13.12-13.18;
  rollover fixes a + b + c; factors GBPJPY 1.09 / GBPUSD 1.38; spread table option A (full table);
  harvest batches 6-9 and the pipeline fix; no paid futures data for now; **Binance futures is the next
  research direction**; project moved to the new folder.
- 2026-11-12: pytest-xdist `-n 8`; one research loop at a time; always propose next steps; auto mode;
  futures venues allowed (method: futures prices + futures cost model, never CFD prices minus swap).

## Open (needs the user)

1. One-time MT5 tests still pre-registered: strategy 4 on GBPJPY; gap momentum in quiet sideways
   markets. Only on your go.
2. **B4 dividends:** send `docs/ftmo-dividend-question.md` to FTMO support; Opus adds the rule test-first.
3. **GBPUSD 2020-21 placeholder spreads** (50 points on 50-74 % of the bars) are still in the original
   table; drop them like the seven FX symbols (2020 -> 2019, 2021 -> 2022 values)? Changes a default.
4. **I-73 crypto funding carry PASSED its one-time test (2026-11-14):** 266 weeks, net +112 bp/week, t 2.93,
   pooled t 3.08, max drawdown -3,967 bp (`knowledge/ideas.md` › I-73). Not stop-defined (no R), Binance only.
   Decide: spec it as a portfolio strategy (how to define risk / R for a weekly long-short book), and whether to
   forward-test it (Binance testnet or paper log; the live bot is FTMO demo only).
5. Low priority: stressed-cost p90 refresh; USDCHF early 2015 borderline data (left as it is).

## Next step

1. **New chat, first:** copy Claude's memory notes from the old project key (prompt below).
2. **`Continue.Research` on Binance futures** with the cached data (`data/cache/binance`, `binance_flow`,
   `binance_funding`: BTCUSDT / ETHUSDT). Start by checking the existing BTCUSDT / ETHUSDT cost model in
   `engine/costs.py` (commission, funding via `load_funding`) against Binance's published USD-M fees
   (about 10 bp taker round trip), then card ideas that fit: funding-rate extremes (parked HV-T0020-1 / -3
   were underpowered on CFD costs), funding-settlement timing, basis / flow effects. Screen first, gates
   pre-registered; venue method per AGENTS.md (futures prices, futures costs, no CFD swap).
3. Code items left (ROADMAP V2.10): A9 results out of the specs (deferred); two-leg 2b when a pair idea
   survives a screen.

## First prompt for the next chat

> The project moved to `X:\Daten\02_Projekte\01_Laufend\backtester-claude` (V2 in `backtester-claude_V2`).
> First, move your memory: copy every file from
> `C:\Users\justi\.claude\projects\X--Dokumente-Projekte-backtester-claude\memory\` into this session's
> memory directory (the path in your system prompt), keep `MEMORY.md` as the index, and confirm the 7
> notes load. Check that nothing in `C:\Users\justi\.claude\settings.json` or the project's `.claude\`
> still points to `X:\Dokumente`. Report in 3 lines, then read `docs/HANDOFF.md` and start
> `Continue.Research` on Binance futures (HANDOFF › Next step 2).
