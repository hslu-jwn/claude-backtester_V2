# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history in git, results in
`research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-18, `End.` of the Mode=auto research session 2026-11-16/17)

- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. Full suite 6,016 passed,
  14 skipped, 4 xfailed; ruff clean. `src/backtester/tools/notify.py` has the user's uncommitted lines: untouched.
- **Strategies alive:**
  - **Strategy 20 crypto taker-flow sort** (goal 2, Binance; `docs/strategy-crypto_flow.md`): one-time test passed
    (+147 bp a week, t 3.76); fair forward ~+92 bp a week; forward logs from 2026-11-16. Strategy 19 carry: forward only.
  - **I-109 Treasury month-end** (goal 2, rates): long 10-year duration over each month's last 3 trade dates (index
    duration extension). Dev 1990-2021 net +18.4 bp per month-end (t 4.42); one-time test 2021-10..2026-10 +24.9 (t 2.14),
    IEF real closes +23.2; test not blind (ohlcv.io 2026 study). Long bonds (I-110) not confirmed; euro / UK / Japan
    (I-112) killed (Japan opposite): the effect is mostly US. Card `knowledge/ideas.md` I-109.
- **Shelf (M3 forward logs, `research/screens/2026-11-17_shelf_forward.py`, all canaries pass):** I-100, I-84, I-98,
  H11, I-71, I-105 and I-109 (`shelf_i109` DGS10, `shelf_i109_ief` IEF); first rows from the 2026-12-03 task.
- **Goal 1 (FTMO CFDs): no stream.** Today also killed threshold rebalancing on US500 (I-111: one crash, 2020).
- **US share venue (M13):** universe `docs/share-universe.md` (top 1,000 and ranks 1,001-2,000); seven cards killed
  (I-101..I-104, I-106..I-108); family `share_insider` closed. Short interest not testable (FINRA free data from 2021-06).
- **New data (git-ignored):** Alpaca daily bars for ~23,700 US symbols (2015-07+), SEC insider / fails / N-PORT files,
  FINRA short volume, Wikipedia views, FRED DGS2/5/10/20/30, ECB / BoE / MOF 10-year yields (`data/cache/intl_yields`).
- **Harvest:** batches 16-17 run (market codes RATES / SHARE-US added); six batches since 12 gave one card (I-109).

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-18: I-109 venue = CME Micro 10-Year Yield futures (10Y, $10 per bp of yield), small size (1-3 contracts)
  (decided by the user 2026-11-18). Hold the next-month contract (the front stops trading at 3 p.m. ET on the month's
  last business day, our exit day).
- 2026-11-18: everything of the 2026-11-16/17 session accepted at `End.`.
- 2026-11-17: M1 (three verdicts) and M3 (shelf); M13 (real US shares); card 7 split; the user's e-mail as the
  EDGAR / Wikimedia contact (Credential Manager only); shelf loggers and the monthly task; threshold rebalancing is its
  own family `rebalancing_threshold` (the calendar month-end signal stays closed in `turn_of_month`).
- 2026-11-15 and earlier: crypto split (develop 2020-2023, test 2024+); Strategy 20 build; Mode=manual|auto rules.

## Open (needs the user)

1. **I-109 on micro yield futures (money; venue decided):** still open: the broker (does it list 10Y, fees), the
   loss the user accepts per month-end, and execution (manual orders from a date calendar, or a broker connection =
   new order code, demo first). Per micro on DGS10 windows: ~+$16-21 net a month-end (cost ~$3 assumed), sd ~$90-96,
   worst -$140 (test) / -$280 (dev), a losing year ~22-27 %. Liquidity and the exact tick not checked yet.
2. **Crypto prop firm for Strategy 20 (money):** decision package `knowledge/research/reports/2026-11-15_s20_prop_decision.md`
   (15 % notional per side tranched: pass ~96 % in ~1.6 years on realistic marks); confirm the firm's rules first.
3. **Fable sweep methods still open:** M2, M4-M12 (`knowledge/reviews/2026-11-16-idea-sweep/fable_part2_directions.md`
   §3); AWS requester-pays account for Hyperliquid fills (card 6 C); a source for the positioning collector (card 8).
4. **Rules:** strike the two spent MT5 tests (strategy 4 GBPJPY, gap momentum); goal-1 signal pause at K = 10 (reached
   2026-11-15); count test-period uses (t >= 3.0 from the 5th one-time test on a period).
5. Older: B4 dividends question to FTMO; GBPUSD 2020-21 placeholder spreads; stressed-cost p90 refresh; USDCHF 2015.

## Next step

1. **2026-12-03 (scheduled task `monthly-forward-logs`, needs the Claude app and the MT5 terminal open):** first forward
   rows for Strategies 19 / 20 and the shelf incl. I-109; check the commit and the Telegram summary.
2. Research: futures history (e.g. daily continuous contracts) would check I-109 on ZN prices (diagnostic; its test is
   spent) and open futures-only ideas for goal 2; otherwise the harvest is close to exhausted for our data.

## First prompt for the next chat

> Read `docs/HANDOFF.md`. Then propose, in max 10 lines, the next step (I-109 venue, the 2026-12-03 forward rows,
> futures data for goal 2, or the Strategy 20 prop firm), with your pick, and start it after my ok.
