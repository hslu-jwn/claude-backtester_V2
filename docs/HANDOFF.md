# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history in git, results in
`research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-26, `End.` of the fusion session 2026-11-19, Mode=auto)

- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. Full suite 6,053 passed,
  14 skipped, 4 xfailed (End. 2026-11-26); ruff clean. Untouched on purpose: `src/backtester/tools/notify.py` (the
  user's uncommitted lines) and `knowledge/reviews/2026-11-21-lead-research/` (untracked, not from this session).
- **Strategies alive (goal 2):**
  - **Strategy 20 crypto taker-flow sort** (`docs/strategy-crypto_flow.md`): test passed (+147 bp a week, t 3.76);
    plan on ~+60 to +90 bp a week (M10); forward logs from 2026-11-16. Strategy 19 carry: forward only.
  - **I-109 Treasury month-end** (card I-109): long 10-year duration over each month's last 3 trade dates. Dev +18.4 bp
    (t 4.42), test +24.9 (t 2.14, not blind). **New (I-132):** the effect is absent before bond indexing (1962-72 +1.1
    bp, t 0.26), appears in the 1980s (+8.9) and is +20.4 after 1990 (difference t 3.22): the index-extension
    mechanism passes its causal check. Watch weekend month-ends in the forward log (T-26).
- **Shelf (M3 forward logs):** I-100, I-84, I-98, H11, I-71, I-143, I-109 (DGS10 and IEF); first rows 2026-12-03.
  I-105 and I-134 report only from 2026-11-26 (not executable; I-143 is the tradable twin, ranked pre-market).
  **Forward-only fusions:** I-134 (I-105 split by VIX, report only), I-135 (crypto book + I-109, monthly boundary);
  check: `research/screens/2026-11-19_i134_i135_forward_checks.py download | check`.
- **Goal 1 (FTMO CFDs): no stream;** M11 holds, lifted only for fusions with a measured-gross component (2026-11-19).
- **Fusion session 2026-11-19 (the user: combination research):** inventory `knowledge/topics/fusion-inventory.md`;
  ranked cards I-132 .. I-141 in `knowledge/ideas.md` › Fusion run. Results: I-132 SUPPORTED; I-133 crypto flow + carry
  composite KILLED on M7 (net +139 bp a week, t 3.52, second half 0.21 of the mean); I-136 parked; I-137 .. I-141 closed
  before data (M4 cost ratio, power, prior look, selection). Lesson: every positive component's development period is
  already seen, so fusions need unseen data (pre-sample, forward) to be evidence.
- **Data scout (Codex terra, web):** free non-price data with a forced counterparty is exhausted for our venues; the
  one lead (NY Fed securities lending, I-142) needs paid Treasury futures prices. Binance futures metrics (open
  interest) start 2021-12 for the cross-section (BTC only from 2020-09).
- **Report for the user:** `knowledge/research/reports/2026-11-19_idea-sources-and-ict.md` (A: idea sources ranked, pick
  = venue non-price data; B: ICT: what Opus can build alone, 9 ambiguous rules with quotes, where chart examples help).

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-26: lead-review intake: R1 (I-143), R3 + R4, and the downloads for R3 (Binance spot 2017-10 .. 2019-12),
  R5 (IEF M1) and R6 (Binance aggTrades) ("ok").
- 2026-11-26: everything of the fusion session 2026-11-19 accepted at `End.`.
- 2026-11-19: fusion run rules: a combination of killed components is a new counted hypothesis; Codex-only workers
  (terra reading / screens, sol engine / strategy); M11 decision delegated to Opus (lifted for fusions with a
  measured-gross component, `docs/research-runner.md` › M11).
- 2026-11-19: build and test the parked book cards with the same framework (done: H1-H4 killed).
- 2026-11-18: I-109 on CME Micro 10-Year Yield futures (10Y, $10 per bp), Interactive Brokers, 1 contract for the
  first 6 month-ends (2-3 only if the forward log and real fills hold); orders by hand, "good after time" just before
  3 p.m. ET, next-month contract; a broker connection only when needed, demo first.
- 2026-11-18: Strategy 20 at a crypto prop firm: not pursued. No paid futures data for now (Databento declined).
- 2026-11-18: rules M2, M4-M12, T-21 causal check, T-24 report only, T-25 stress scenarios.
- 2026-11-17 and earlier: M1, M3, M13; shelf loggers and the monthly task; crypto split; Mode=manual|auto.

## Open (needs the user)

- **Codex out (2026-11-26):** the user routes its work to Claude sonnet / haiku subagents (`docs/agent-routing.md`);
  tell Opus when Codex is back.
- **Lead review:** R11 / R12, memo with Opus picks `knowledge/reviews/2026-11-27-r11-r12-decisions.md`; list in `knowledge/reviews/2026-11-26-lead-review-intake.md` (pooled verdicts, composite; tax,
  SSRN PDF, FTMO CFD stop).
  With R11: adopt empirical priors per family type for M4 instead of 1:50? First fit (2026-11-27,
  `research/screens/ledger_prior.py`) is descriptive only: pooled pi 0.52 on gross looked-at rows, type e thin.
0. **Scheduled task edit:** the app's auto-mode classifier blocked Opus's edit of `monthly-forward-logs`. Add to its
   step 5: `research/screens/2026-11-19_i134_i135_forward_checks.py download`, then `... check`, or allow the edit.
1. **Next lever (Telegram sent 2026-11-19):** settle the ICT rules (report B, 9 quotes, chart examples), or allow
   paid futures data (reopens goal 1 off the CFD wall and I-142), or the IBKR account.
2. **IBKR account** for I-109 (futures permission); first fills check margin, the 3 p.m. spread and fees.
3. **Books:** Tier 1 missing: Burghardt, Bouchaud, Madhavan / Abner. Broken files: Williams *Long-Term Secrets* (404
   page), Vince *Leverage Space* and Johnson *DMA* (scans, no text layer).
4. **Rules:** strike the two spent MT5 tests (strategy 4 GBPJPY, gap momentum).
5. Older: B4 dividends question to FTMO; GBPUSD 2020-21 placeholder spreads; stressed-cost p90 refresh; USDCHF 2015.

## Next step

0. **Lead-review intake (2026-11-26):** tasks R1-R12 in `knowledge/reviews/2026-11-26-lead-review-intake.md`; R1 done (I-143
   registered 2026-11-26); R11 / R12 wait for the user.
1. The user's own step first (said at `End.` 2026-11-26).
2. **2026-12-03 (task `monthly-forward-logs`, Claude app and MT5 terminal open):** first forward rows for Strategies
   19 / 20 and the shelf incl. I-109; plus the I-134 / I-135 check (Open 0).
3. Then the lever the user picks (Open 1); I-109 live path once the IBKR account exists
   (`research/screens/2026-11-19_i109_order_calendar.py`).

## First prompt for the next chat

> Read `docs/HANDOFF.md`. Then propose, in max 10 lines, the next step (my lever from Open 1, the 2026-12-03 forward
> rows, I-109 live path), with your pick, and start it after my ok.
