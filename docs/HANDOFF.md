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
   still made +133 bp a week, t 3.37, in the test period (diagnostic, addendum). Before any fee: confirm the low-cap 5 % cap,
   drawdown type and basket fills with the firm.
2. **Forward logs:** a monthly scheduled task for `crypto_carry --update --forward` and `crypto_flow --update --forward`,
   or Opus runs them by hand from about 2026-12-02.
3. **Crypto momentum:** a pre-registered screen on the crypto split; FB-009 / 011 / 220 depend on it.
4. **Rules:** strike the two spent MT5 tests (strategy 4 GBPJPY, gap momentum); signal-research stop rule (K = 10
   falsified screens -> pause goal-1 signals); count test-period uses (t >= 3.0 from the 5th one-time test on a period).
5. **Data / accounts:** free-tier account for US share minute bars (FTMO share history mostly starts 2019-20); a
   scheduled collector of retail positioning (FB-284). Optional books (Telegram 2026-11-14).
6. Older: B4 dividends question to FTMO; GBPUSD 2020-21 placeholder spreads (a default); stressed-cost p90 refresh;
   USDCHF early 2015.

## Next step

1. From about **2026-12-02**: the forward logs (`python -m backtester.tools.crypto_flow --update --forward`, the same
   with `--liquid` (FB-017 top-100 variant), and `crypto_carry`), commit `research/forward/*.csv`, report the first weeks.
2. Research (`Continue.Research`): remaining backlog waves: Wave 5 (rare events pooled, power line first), the deferred
   Binance items (maker-fill model from aggTrades, liquid-only Strategy 20 as a frozen forward variant), Wave 3 (shares)
   once outside share data exists; signal stacking (FB-244).

## First prompt for the next chat

> Read `docs/HANDOFF.md`. Then propose, in max 10 lines, the next step (forward logs from ~2026-12-02, crypto prop firm
> for Strategy 20, Wave 5 or the deferred Binance items), with your pick, and start it after my ok.
