# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history in git, results in
`research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-15, `End.` of the Mode=auto research session 2026-11-14/15)

- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. Full suite and ruff: see
  the research log's End entry. `src/backtester/tools/notify.py` has uncommitted hook-trace lines: the user's, untouched.
- **Data (not committed):** Binance wide universe `data/cache/binance_wide` (daily klines + taker volume + funding, all
  USDT perps incl. delisted, to 2023-12), `binance_wide_test` (2024-01..2026-10), `binance_wide_spot` (spot klines,
  243 symbols, to 2023-12); Squeezemetrics DIX / GEX `data/cache/squeezemetrics/DIX.csv` (daily from 2011, use next day).
- **Strategies alive (goal 2, Binance, research tools, no orders):**
  - **Strategy 20 crypto taker-flow sort** (`docs/strategy-crypto_flow.md`, `tools/crypto_flow.py`): weekly long the
    top / short the bottom quintile of 7-day net taker buying, all USDT perps. One-time test 2024-01..2026-10 PASSED
    (+147 bp a week, t 3.76; development +145). About half is pump capture in small perps (+56 bp a week with returns
    capped at 30 %); break-even extra slippage ~37 bp a fill; twin I-83 (flow residual on the 7-day return) also passed
    (+102, t 2.85, correlation 0.83): the edge is not just momentum. Forward log from 2026-11-16.
  - **Strategy 19 crypto carry**: forward log only (replication failed). Correlation with Strategy 20 0.06.
- **Goal 1 (FTMO CFDs): no stream.** This session killed noise-band momentum (incl. the gamma split), SMT divergence,
  NAS100 / US500 rotation, the ICT raid / power of three / CRT rules and the FVG / equal-highs null model; overnight
  premium is below cost (swap). Pass map: zero edge passes ~30 % by luck; a stream needs ~+0.05 R net at ~300 trades a
  year. Prop mechanics: adaptive sizing adds ~0-3 points; K uncorrelated streams cut the time to pass by ~K.
- **Idea backlog:** `research/idea_backlog/2026-11-15-fable-ideas.csv` (335 ideas, Fable), framework and waves in
  `knowledge/reviews/2026-11-15-fable-idea-universe.md`; Waves 0, 1, 2 (partly) and 4 done; family budget via
  `research/screens/family_budget.py` (run at the top of every batch). Reports in `knowledge/research/reports/2026-11-1*`.

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-15: everything of this session accepted at `End.`; crypto split (develop 2020-2023, test once 2024+, wider
  universe incl. delisted; `docs/research-runner.md` › Periods); build Strategy 20 (research tool + forward log); its
  realism check; Fable idea-universe call; Waves 0, 1, 2, 4 and the ICT null model; Mode=auto for the session.
- 2026-11-14: Binance session accepted; Strategy 19 forward log only; Mode=manual|auto rules.

## Open (needs the user)

1. **Crypto prop firm for Strategy 20 (money):** HyroTrader / Crypto Fund Trader (Bybit, 550-700+ perps, weekend holds,
   no stop, own bots) could host it; simulated 2-Step pass 90-100 % at 25 % notional per side in ~10-16 months
   (`knowledge/research/reports/2026-11-15_s20_prop_fit.md`, optimistic). On the perps Bybit lists the frozen book
   still made +133 bp a week, t 3.37, in the test period (diagnostic, addendum). Fair forward expectation after the
   rebalance-day, execution and turnover checks: ~+92 bp a week (taker ~10 bp a fill, but only ~55 % turnover).
   **Decision package:** `knowledge/research/reports/2026-11-15_s20_prop_decision.md` (hourly check done): tranched
   top-100 book at 15 % notional per side passes ~96 % on realistic marks (44 % on a strict wick bound) in ~1.6 years;
   10 % per side ~99 % even on the wick bound but ~2.9 years. Questions to ask the firm are listed there. CFT's reverse-trading rule needs a check before a long-short basket. Before any fee: confirm the low-cap 5 % cap,
   drawdown type and basket fills with the firm.
2. **Forward logs:** a monthly scheduled task for `crypto_carry --update --forward` and `crypto_flow --update --forward`,
   plus the shelf (`research/screens/2026-11-17_shelf_forward.py update` then `log`, `status`; MT5 data for USDJPY /
   UK100 current first), or Opus runs them by hand from about 2026-12-02.
3. ~~Crypto momentum~~: done 2026-11-15 in Mode=auto (I-97 killed, t 0.68; FB-009 / 011 / 220 closed).
4. **Rules:** strike the two spent MT5 tests (strategy 4 GBPJPY, gap momentum); signal-research stop rule (K = 10
   falsified screens -> pause goal-1 signals; **K = 10 reached 2026-11-15**, research log); count test-period uses (t >= 3.0 from the 5th one-time test on a period).
5. **Data / accounts:** US share minute bars: Alpaca account and keys set up by the user (2026-11-16); download
   2016+ of SPY, QQQ, IWM, DIA, the 11 sector ETFs and the 46 FTMO shares into `data/cache/alpaca` (resumable:
   `python -m backtester.data.alpaca <symbols> --start 2016-01`). Still open: a
   scheduled collector of retail positioning (FB-284). Optional books (Telegram 2026-11-14).
6. Older: B4 dividends question to FTMO; GBPUSD 2020-21 placeholder spreads (a default); stressed-cost p90 refresh;
   USDCHF early 2015.
7. **Fable idea sweep 2026-11-16** (`knowledge/reviews/2026-11-16-idea-sweep/`, `fable_part2_directions.md`):
   accept or reject the method proposals M1-M13 line by line (§3: third verdict UNPROVEN-POSITIVE, c-and-name-periods
   power rule, tail / regime gates, alpha spending t 3.0 / 3.3 / 3.5 on a test period, ...); M13 = real US shares as a
   research venue under goal 2 (without it only cards 0, 1, 5, 6, 8 remain); AWS account (requester-pays) for
   Hyperliquid fills (card 6 step C); source for the positioning collector (card 8); contact string for EDGAR.
   Ten cards (0-9) and a first-week plan (§4) are ready for `Continue.Research`. Card 0 done 2026-11-17
   (`card0_s20_audit.md`): S19 and S20 near-independent, S20 planning range ~+90-110 bp/week; feeds Open 1.
   Card 1 = I-100 done 2026-11-17: KILLED on t 2.45 (net +107 bp/week, all other kills passed; UNPROVEN-POSITIVE if
   M1 is accepted); family `crypto_carry_xs` closed. Card 5 pre-registered 2026-11-17 (`strategy-crypto_flow.md` › Crypto book;
   book confirmed by week 104 with 29 %). Card 6 A done (`card6a_hyperliquid_audit.md`): 235 perps incl. 56 delisted with history; step B closed
   on data (4 weeks with 40 names); step C would have ~105 weeks (t 2 needs ~93-128 bp/week). Card 2 questions 1-2 (`card2_alpaca_audit.md`): Alpaca serves delisted names (20 of 20) and the
   official auction prints on the free plan; the inactive-assets list misses pre-2018 delistings. M13 accepted by the user 2026-11-17 (AGENTS.md › Venues). Card 2 done (`docs/share-universe.md`, 1,000 names a month 2016-04+); card 3 = I-101 KILLED
   (gross t 0.16); card 4 = I-102 KILLED (gross
   t 1.04; diagnostic: the 09:30-open timing +12.9 bp/day gross, t 3.94, not tested: a shelf candidate if M1 / M3);
   card 7 = I-103 KILLED (t 0.80; flow adds ~3 bp). Card 9 = I-104 KILLED (gross t -0.27). Card 7 split accepted by the user 2026-11-17 (dev to 2024-12-31, test 2025+). Contact for EDGAR / Wikimedia: the
   user's e-mail (accepted 2026-11-17, stored in the Credential Manager). M1 + M3 accepted 2026-11-17 (research-runner.md › Verdicts and shelf):
   shelf = H11, I71, I73, I84, I98, I100 + I-105 (forward only); forward loggers to build except Strategy 19.
   Waiting on the user: M2, M4-M12, AWS (card 6 C), source for card 8.

## Next step

1. From about **2026-12-02**: the forward logs (`python -m backtester.tools.crypto_flow --update --forward`, the same
   with `--liquid` (FB-017 top-100 variant) and `--liquid --anchor tue` .. `sun` (weekday tranches), and `crypto_carry`), commit `research/forward/*.csv`, report the first weeks.
2. Research (`Continue.Research`): remaining backlog waves: Wave 5 (rare events pooled, power line first), the deferred
   Binance items (maker-fill model from aggTrades, liquid-only Strategy 20 as a frozen forward variant), Wave 3 (shares)
   once outside share data exists; signal stacking (FB-244).

## First prompt for the next chat

> Read `docs/HANDOFF.md`. Then propose, in max 10 lines, the next step (forward logs from ~2026-12-02, crypto prop firm
> for Strategy 20, Wave 5 or the deferred Binance items), with your pick, and start it after my ok.
