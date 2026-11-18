# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history in git, results in
`research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-18, `End.` of the second session 2026-11-18, Mode=auto)

- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. Full suite 6,053 passed,
  14 skipped, 4 xfailed (after the last code change, T-22); ruff clean. `src/backtester/tools/notify.py` has the
  user's uncommitted lines: untouched.
- **Strategies alive (goal 2):**
  - **Strategy 20 crypto taker-flow sort** (`docs/strategy-crypto_flow.md`): test passed (+147 bp a week, t 3.76);
    plan on ~+60 to +90 bp a week (M10); forward logs from 2026-11-16. Strategy 19 carry: forward only.
  - **I-109 Treasury month-end** (card I-109): long 10-year duration over each month's last 3 trade dates. Dev +18.4 bp
    (t 4.42), test +24.9 (t 2.14, not blind). T-26 (this session): no quarter-end dependence; test months whose
    month-end is a weekend (2/5/7-year notes settle on the 1st) were weak (+2.5 bp, 18 months, difference t 1.48, not
    in development): watch them in the forward log.
- **Shelf (M3 forward logs):** I-100, I-84, I-98, H11, I-71, I-105, I-109 (DGS10 and IEF); first rows 2026-12-03.
- **Goal 1 (FTMO CFDs): no stream;** new signal screens paused (M11).
- **This session:** 12 books read and filed in `knowledge/books/` (Donnelly AC, Carver AFTS, Ilmanen ER and IL, Pedersen
  EI, Stigum SM, Harris TE, Tuckman TK, Rhoads RH, Sinclair VT, Schofield SC; selected chapters where noted); harvest
  batches 19 (crypto data) and 20 (US-share data), canaries passed. New cards, all decided before any data look:
  I-120 FX COT, I-121 crack carry, I-123 FX carry, I-126 token unlocks, I-127 USDT issuance, I-128 days-to-cover
  PARKED on power; I-122 index changes, I-124 spin-off drift (rebound parked), I-125 VIX on FOMC days CLOSED. No
  screenable candidate. Free data and the library's strategy-relevant books are worked through.
- **Third session 2026-11-18 (Mode=auto, running):** 31 more books read by Codex terra (Tier 3, Tier 4, and Kakushadze,
  Evans, Foucault, Alpha Trader, Mehrling, Fabozzi); cards I-129 low idio vol, I-130 tax-loss losers (power), I-131
  fund fire sales (data) PARKED before any data. No screenable candidate. Checkpoint: 6,053 passed, ruff clean.
- **Built:** T-24 `analytics/fat_tail_power.py` (report only), T-22 `analytics/causal_sim.py` (causal simulation
  tests), T-26 `research/screens/2026-11-18_t26_i109_month_end_diagnostics.py`; TreasuryDirect note history cached.

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-18 (later): Opus picks the order of the library books itself, no go needed.
- 2026-11-18 (later): T-24 fat-tail power check is report only, no gate; every new card shows it next to M4.
- 2026-11-18 (later): everything of the second session 2026-11-18 accepted at `End.`.
- 2026-11-18: I-109 on CME Micro 10-Year Yield futures (10Y, $10 per bp), Interactive Brokers, 1 contract for the
  first 6 month-ends (2-3 only if the forward log and real fills hold); orders by hand, "good after time" just before
  3 p.m. ET, next-month contract; a broker connection only when needed, demo first.
- 2026-11-18: Strategy 20 at a crypto prop firm: not pursued. No paid futures data for now (Databento declined).
- 2026-11-18: rules M2, M4-M12 and T-21 causal check per card (`docs/research-runner.md`); T-25 stress scenarios.
- 2026-11-17: M1 (three verdicts), M3 (shelf), M13 (real US shares); shelf loggers and the monthly task.
- 2026-11-15 and earlier: crypto split (develop 2020-2023, test 2024+); Strategy 20 build; Mode=manual|auto rules.

## Open (needs the user)

1. **IBKR account** for I-109 (futures permission); first fills check margin, the 3 p.m. spread and fees.
2. **Books:** Tier 1 missing: Burghardt *Treasury Bond Basis*, Bouchaud *Trades, Quotes and Prices*, Madhavan and
   Abner (ETFs). Broken files (third session): Williams *Long-Term Secrets* is a 404 web page (re-download); Vince
   *Leverage Space* and Johnson *Algorithmic Trading and DMA* have no text layer (scans; a text PDF or OCR needed).
   Unread on purpose (pricing texts): Hull, Natenberg.
3. **Data:** the parked cards above reopen only with longer samples or paid / intraday data (e.g. intraday VX for
   I-125); the user declined paid data on 2026-11-18. Fable leftovers: Hyperliquid AWS account (card 6 C), a source
   for the positioning collector (card 8).
4. **Rules:** strike the two spent MT5 tests (strategy 4 GBPJPY, gap momentum).
5. Older: B4 dividends question to FTMO; GBPUSD 2020-21 placeholder spreads; stressed-cost p90 refresh; USDCHF 2015.

## Next step

1. **2026-12-03 (scheduled task `monthly-forward-logs`, needs the Claude app and the MT5 terminal open):** first forward
   rows for Strategies 19 / 20 and the shelf incl. I-109 (look at weekend month-ends, T-26); check the commit and the
   Telegram summary.
2. I-109 live path once the IBKR account exists (demo first, 1 Micro 10Y contract); dates and contract per month:
   `python research/screens/2026-11-19_i109_order_calendar.py` (SELL the yield contract = long duration).
3. New idea supply needs a user lever (account, data, Tier 3 / 4 books); without one, the forward logs are the work.

## First prompt for the next chat

> Read `docs/HANDOFF.md`. Then propose, in max 10 lines, the next step (the 2026-12-03 forward rows, I-109 live path,
> a new book or data lever), with your pick, and start it after my ok.
