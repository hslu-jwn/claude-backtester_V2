# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history in git, results in
`research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-19, `End.` of the third session 2026-11-18/19, Mode=auto)

- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. Full suite 6,053 passed,
  14 skipped, 4 xfailed (End. 2026-11-19; last code change: harvest UTF-8 output); ruff clean. `src/backtester/tools/notify.py` has the
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
- **Second session 2026-11-18:** 12 books (Tier 1 / 2), harvest batches 19-20; cards I-120 .. I-128 parked or closed.
- **Third session 2026-11-18/19:** 31 books read by Codex terra (all of Tier 3 and 4, plus Kakushadze, Evans,
  Foucault, Alpha Trader, Mehrling, Fabozzi; notes in `knowledge/books/`, README rows); harvest batches 21 (rates /
  energy data) and 22 (first Chinese / Korean batch): canaries pass, nothing kept. Cards I-129, I-130, I-131 parked
  before any data; then, on the user's word, **I-129 / momentum / I-130 built and run** (`docs/strategy-share_book_factors.md`,
  H1-H4): all KILLED in development (H1 low idio vol -65 bp/month t -0.83; H2 12-1 momentum +71 t 0.71; H3 / H4
  tax-loss 4-5 events, |t| < 1). Free US share history before 2016: none usable (WIKI 1996-2018 survivor-biased).
- **Built:** T-24 `analytics/fat_tail_power.py`, T-22 `analytics/causal_sim.py`, T-26 diagnostics; third session:
  `research/screens/2026-11-19_v27_goal2_portfolio.py` (S19, S20, I-109: monthly correlations -0.23 .. +0.26, combined
  2024+ Sharpe 3.0 raw, plan on about half), `2026-11-19_i109_order_calendar.py` (hand-order dates, side, contract),
  `2026-11-19_share_book_factors_screen.py`; `harvest` prints UTF-8.

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-19: build and test the parked book cards with the same framework (done: H1-H4 killed).
- 2026-11-19: everything of the third session accepted at `End.`.
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
   Telegram summary. Its read-only steps were dry-run on 2026-11-19 (shelf canary OK).
2. I-109 live path once the IBKR account exists (demo first, 1 Micro 10Y contract); dates and contract per month:
   `python research/screens/2026-11-19_i109_order_calendar.py` (SELL the yield contract = long duration).
3. New idea supply needs a user lever (IBKR account, missing Tier 1 books, paid data); the whole library is read.

## First prompt for the next chat

> Read `docs/HANDOFF.md`. Then propose, in max 10 lines, the next step (the 2026-12-03 forward rows, I-109 live path,
> a new book or data lever), with your pick, and start it after my ok.
