# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history in git, results in
`research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-18, `End.` of the session 2026-11-18)

- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. Full suite 6,027 passed,
  14 skipped, 4 xfailed; ruff clean. `src/backtester/tools/notify.py` has the user's uncommitted lines: untouched.
- **Strategies alive (goal 2):**
  - **Strategy 20 crypto taker-flow sort** (`docs/strategy-crypto_flow.md`): test passed (+147 bp a week, t 3.76);
    plan on ~+60 to +90 bp a week (M10); forward logs from 2026-11-16. No prop firm (the user). T-23: development leans
    on one week, the test does not. Strategy 19 carry: forward only.
  - **I-109 Treasury month-end** (card `knowledge/ideas.md` I-109): long 10-year duration over each month's last 3
    trade dates. Dev +18.4 bp (t 4.42), test +24.9 (t 2.14, not blind); on ZN futures dev +19.2 bp. T-23: the test
    leans on a few 2021-22 months (without the 5 best +7.8 bp). Venue decided (below); paper log from 2026-11.
- **Shelf (M3 forward logs, `research/screens/2026-11-17_shelf_forward.py`):** I-100, I-84, I-98, H11, I-71, I-105,
  I-109 (DGS10 and IEF); first rows from the 2026-12-03 task.
- **Goal 1 (FTMO CFDs): no stream;** new signal screens paused (M11).
- **Research this session:** I-113 VIX basis killed, I-114 and I-115 (GSCI roll) falsified at their one-time tests;
  harvest batch 18 kept nothing; data scouts (free flow data, futures data) found nothing testable: I-116 / I-118 / I-74
  parked, I-117 closed on power, I-119 covered by I-115. Free data is close to exhausted.
- **Books:** list of 72 in `knowledge/books-wanted.md` (copy on the user's Desktop); library folder
  `X:\Daten\03_Bibliothek\Trading\Tier 1..4`. Read: López de Prado *Causal Factor Investing* (CF), Taleb *Fat Tails*
  (FT). Downloaded, not read: Gelman *Regression and Other Stories* (Tier 4).
- **Built:** `risk/stress.py` (T-25 shock days beyond the worst seen one for the FTMO simulation; opt-in, not in the
  UI); `research/screens/2026-11-18_t23_tail_concentration.py` (T-23).

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-18 (later): Opus picks the order of the library books itself, no go needed (rule set by the user).
- 2026-11-18 (later): T-24 fat-tail power check is report only, no gate; every new card shows it next to M4.

- 2026-11-18: I-109 on CME Micro 10-Year Yield futures (10Y, $10 per bp), Interactive Brokers, 1 contract for the
  first 6 month-ends (2-3 only if the forward log and real fills hold); orders by hand, placed ahead as "good after
  time" orders just before 3 p.m. ET, held in the next-month contract; a broker connection only when needed, demo first.
- 2026-11-18: Strategy 20 at a crypto prop firm: not pursued (HyroTrader 15 % per side ~85 % pass in ~2.5 years at the
  M10 edge; terms §10.2(i) may bar a long-short book).
- 2026-11-18: no paid futures data for now (Databento declined: card risk); books from the library instead.
- 2026-11-18: rules in `docs/research-runner.md`: Fable methods M2, M4-M12 (› Method rules; M7 new cards only, M8 changed)
  and T-21 causal check per card (› Causal check per card). T-25 stress scenarios built.
- 2026-11-18: everything of the session 2026-11-18 accepted at `End.`.
- 2026-11-17: M1 (three verdicts), M3 (shelf), M13 (real US shares); shelf loggers and the monthly task.
- 2026-11-15 and earlier: crypto split (develop 2020-2023, test 2024+); Strategy 20 build; Mode=manual|auto rules.

## Open (needs the user)

1. **IBKR account** for I-109 (futures permission); first fills check margin, the 3 p.m. spread and fees.
2. **Books:** Tier 1 8 of 12 and Tier 2 13 of 25 are in (2026-11-18); Tier 1 missing: Burghardt *Treasury Bond
   Basis*, Bouchaud *Trades, Quotes and Prices*, Madhavan and Abner (ETFs). Tier 3 / 4 follow (the user notifies).
3. **Fable sweep leftovers:** AWS requester-pays account for Hyperliquid fills (card 6 C); a source for the
   positioning collector (card 8).
4. **Rules:** strike the two spent MT5 tests (strategy 4 GBPJPY, gap momentum).
5. Older: B4 dividends question to FTMO; GBPUSD 2020-21 placeholder spreads; stressed-cost p90 refresh; USDCHF 2015.

## Next step

1. **2026-12-03 (scheduled task `monthly-forward-logs`, needs the Claude app and the MT5 terminal open):** first forward
   rows for Strategies 19 / 20 and the shelf incl. I-109; check the commit and the Telegram summary.
2. Books (order is Opus's call): read 2026-11-18 Donnelly (AC), Carver AFTS, Ilmanen ER, Pedersen (EI), Stigum (SM,
   rates chapters), Harris (TE, draft), Ilmanen 2022 (IL), Tier 2 Tuckman / Rhoads / Sinclair / Schofield. Left:
   Kakushadze (idea list only), Tier 2 Hull, Natenberg, Fabozzi, Mehrling, Foucault, Evans, Johnson, Alpha Trader
   (lower yield: 12 books gave no screenable candidate). New cards: I-120 / I-121 / I-123 parked, I-122 closed, I-124 spin-off
   closed / parked after the source hunt, T-26 done (I-109: no quarter-end effect; watch weekend month-ends).
3. Optional tooling from the books: T-22 (simulation tests for our estimators). T-24 built 2026-11-18
   (`analytics/fat_tail_power.py`): report only, next to M4 on every new card (the user).

## First prompt for the next chat

> Read `docs/HANDOFF.md`. Then propose, in max 10 lines, the next step (a book, the 2026-12-03 forward rows, T-22 /
> T-24, or research), with your pick, and start it after my ok.
