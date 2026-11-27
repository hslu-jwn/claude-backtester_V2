# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history in git, results in
`research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-27, `End.` of the lead-review intake session, Mode=auto from 2026-11-27)

- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. Full suite 6,110 passed,
  14 skipped, 4 xfailed (End. 2026-11-27); ruff clean. Untouched on purpose: `src/backtester/tools/notify.py`
  (the user's uncommitted lines).
- **Strategies alive (goal 2):** Strategy 20 crypto taker-flow sort (test passed +147 bp a week, t 3.76; plan on ~+60 to
  +90, M10; forward logs from 2026-11-16); Strategy 19 carry forward only; I-109 Treasury month-end (dev +18.4 bp t 4.42,
  causal check passed via I-132).
- **Shelf (M3 forward logs):** I-100, I-84, I-98, H11, I-71, I-143, I-109 (DGS10 and IEF); first rows 2026-12-03.
  Forward-only: I-134, I-135, and **I-147** (frozen flow + carry composite, top-100 perps, rule P members P1 / P2 at 0.4,
  forward at 1.0; logger `research/screens/2026-11-27_i147_composite_forward.py`, canary reproduces I-78).
- **Forward book (FBK):** `research/screens/2026-11-27_forward_book.py report`: one weekly book over the shelf logs and
  Strategies 19 / 20, registered numbers only, weights by shrunk Sharpe (M10), correlations assumed 0. Reporting only.
- **New method rules (accepted 2026-11-27):** M13 rule P (pooled-evidence verdicts, new cards only), forward book,
  goal 1 frozen (no FTMO CFD signal research): `docs/research-runner.md` › Method rules.
- **This session's research (all no-card or parked, every look in the ledger):** R10 ledger effect columns + backfill;
  empirical-Bayes prior descriptive only (pooled pi 0.52, n 38; not adopted); fast-track lead closed (N-PORT recall
  28 %); I-71 test look not taken (pass chance ~8-12 %, c 0.07-0.10); three harvest batches T0154-T0171 (US share
  data, crypto data sets, new source types): canaries pass, no new card; I-148 Lazy Prices filing-text sort PARKED on
  M4 (halved +17 bp a month, 66 development months, pass chance ~1 %).
- **Reading:** free non-price data sets for our venues (US shares, crypto, futures) now look largely mined; the binding
  constraints are sample length (shares start 2016) and verdict power, not idea supply.

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-27: R11 / R12 picks 1-5 ("yes"): M13 rule P, I-147 forward composite, forward book, goal-1 freeze;
  empirical priors not yet (revisit after ~20 more looks). Mode=auto for that session.
- 2026-11-26: Codex out; route its work to Claude sonnet / haiku subagents.
- 2026-11-26: lead-review intake R1, R3-R6 and their downloads; fusion session 2026-11-19 accepted.
- 2026-11-18: I-109 on CME Micro 10-Year Yield futures via IBKR (1 contract, first 6 month-ends, orders by hand);
  Strategy 20 at a prop firm not pursued; no paid futures data; rules M2, M4-M12, T-21, T-24, T-25.
- 2026-11-17 and earlier: M1, M3; shelf loggers and the monthly task; crypto split; Mode=manual|auto.

## Open (needs the user)

0. **Scheduled task edit:** add to `monthly-forward-logs` step 5: `research/screens/2026-11-19_i134_i135_forward_checks.py
   download`, then `... check`, and after the Binance update `research/screens/2026-11-27_i147_composite_forward.py
   forward` (I-147), or allow Opus's edit (the classifier blocked it).
1. **Codex:** tell Opus when it is back.
2. **R12 (the user only):** Swiss tax check of goal-2 derivative streams (ESTV KS 36); SSRN 7601879 PDF by hand (I-109
   legs); reopen Databento / HyroTrader only if wanted.
3. **Next lever:** settle the ICT rules (report `knowledge/research/reports/2026-11-19_idea-sources-and-ict.md` B), or
   paid data (pre-2016 US share prices would reopen I-148-type share cards; futures data reopens I-142), or the IBKR
   account for I-109.
4. **Books:** Tier 1 missing: Burghardt, Bouchaud, Madhavan / Abner; broken files: Williams *Long-Term Secrets*, Vince
   *Leverage Space*, Johnson *DMA* (scans).
5. Older: strike the two spent MT5 tests; B4 dividends question to FTMO; GBPUSD 2020-21 placeholder spreads; stressed
   p90 refresh; USDCHF 2015.

## Next step

1. **2026-12-03 (task `monthly-forward-logs`, Claude app and MT5 terminal open):** first forward rows for Strategies
   19 / 20, the shelf incl. I-109, the I-134 / I-135 check; I-147 rows once the December Binance archive is loaded
   (Open 0); then the first `forward_book.py report` with rows.
2. Then the lever the user picks (Open 3); I-109 live path once the IBKR account exists.

## First prompt for the next chat

> Read `docs/HANDOFF.md`. Then propose, in max 10 lines, the next step (the 2026-12-03 forward rows and forward book,
> my lever from Open 3), with your pick, and start it after my ok.
