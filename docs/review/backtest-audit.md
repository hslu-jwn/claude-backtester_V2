# Backtest completeness audit (2026-10-23)

The 32-point checklist of `knowledge/topics/testing-and-robustness.md` › Checklist, checked
against the code by Opus (no other model; plain grep and reading). Asked for by the user
before the grid-tool merge: "what exactly do we need to consider for a realistic simulation".

Status: ☑ built and used · ◐ built but not wired into the research runner, or only in part ·
☐ missing. "Runner" = `tools/research.py`, which every V2.6 research run goes through.

## Re-check 2026-10-28 (the table below is the 2026-10-23 state)

Checked against the code and git log (Sonnet subagent, read-only; Opus spot checks).
**Done since:** #7, #8, #14 (51a99ce), #9, #10, #15, #16, #31 (4d9be45), #11 per class
(51a99ce), #12 walk-forward in months (02a0735, 43caff6), #14a / #26 monkeys (78b2225), #14b
intrabar M1 default (6718191, 43a4375), #14c TP penetration (42329c8, off by default), #21 demo
bot running, #28 Bayes (b03ac0a), #29 effective N (84ce14a), spread table default (bd5a125),
news calendar + research news split (0276bac, `tools/news_diagnostics.py`), block bootstrap
for kind A + Masters bounds (30630b9).
**V2.4c runner checks (2026-10-28):** #2 swept-setting count (`research.json`), #6 chosen
development entry screen (`entry_screen.json`), #13 returns slope and top-10 trades
(`returns_slope.csv`, `top_trades.csv`) implemented; verification is recorded in the task report.
**Still partial:** #1 expected numbers, #3 no sibling-symbol OOS, #11 neighbouring timeframes,
#21a trade-by-trade reconciliation (12.5 / T-06; fill report exists), #25
CSCV + PBO built but no CPCV and no time-reversed run, #30 pre-registered gates (T-17),
slippage p90 stress (parked, V2.4b).
**Still open:** #17 vol-targeted sizing, #20 Kelly / optimal f (T-16), #22 live binomial /
chi-square monitoring, #32 quit rule, performance cone, incubation (T-17).

## Checklist against the code

| # | Point | Status | Where / what is missing |
|---|---|---|---|
| 1 | Premise + expected numbers written down | ◐ | strategy specs in `docs/`; no fixed "expected trades / win rate / DD" section. Process: T-17 |
| 2 | Pre-declared ranges, ≤ 4 free params, metric fixed | ☑ | `tools/research_grid.py`, `research.json`: swept names/count, warning above 4; grid file + net R ranking |
| 3 | Data split fixed, sibling symbols as extra OOS | ◐ | split 2021-09-14 ☑; sibling-symbol OOS not built |
| 4 | Rules checked by hand on the chart, no-lookahead tests | ☑ | chart replay, trades overlay (all strategies since V2.4a), detector tests |
| 5 | Costs 0 / realistic / stressed | ☑ | gross vs net, `net_r_stressed` (costs × 1.5) in the scorecard |
| 6 | Core signal profitable before stop / filter tuning | ☑ | `tools/research_entry_screen.py`, `entry_screen.json`: chosen development screen in the runner |
| 7 | Heat map: plateau, not spike | ◐ | `analytics/robustness.py` plateau; only in the archived grid tools -> grid merge (A) |
| 8 | Mean, st.dev, % profitable combos (≥ 70 %) | ◐ | `grid_stats`; archived tools only -> grid merge (A) |
| 9 | Sensitivity ±10-20 % around the chosen point | ☐ | = "parameter stability" of V2.6; belongs in the runner -> grid merge |
| 10 | Every filter lifts the average of all combos | ☐ | the archived ORB / volume A/B did it by hand -> grid merge (D, twin comparison) |
| 11 | All symbols of the class, neighbouring timeframes | ◐ | per-class table only in the archived ORB tool -> grid merge (C) |
| 12 | Walk-forward, final hold-out untouched | ◐ | `analytics/walk_forward.py`; gap fade only -> grid merge (E) |
| 13 | Year / half table, slope, best removed, top 10 | ☑ | `by_year.csv`, `returns_slope.csv`, `top_trades.csv`, `report.md`; `analytics/robustness.py`, `tools/research_diagnostics.py` |
| 14 | Shock-day check | ◐ | `robustness.shock_report`; archived tools only -> grid merge (B) |
| 14a | Random-entry baseline | ◐ | Monte Carlo kind B exists for gap fade only (needs a "follow" mode per strategy); generic version = T-14 |
| 14b | SL and TP in one candle resolved from M1 | ☐ | engine takes SL first (conservative). T-03 / ROADMAP 12.2 |
| 14c | Stressed fills, seeded random slippage | ☑ | Monte Carlo kind C (`analytics/random_fills.py`); "touch is not a fill" for TP limits ☐ |
| 15 | Enough trades, standard error of expectancy | ◐ | `min_trades` flag, t-stat in the verdict; SE not on the scorecard |
| 16 | Time in market and swap in R separately | ◐ | swap / spread / commission R per trade ☑; time in market ☐ |
| 17 | Fixed fraction + vol-targeted sizing; MC block bootstrap + real sequence | ◐ | fixed fraction, adaptive risk, day reshuffle ☑; vol-targeted sizing ☐; block bootstrap ☐ (day reshuffle keeps intraday order only) |
| 18 | Plan for 1.5-2 × max DD; P(FTMO breach) | ☑ | Monte Carlo + prop-firm pass card |
| 19 | Risk of ruin vs FTMO limits | ☑ | breach probability in `risk/monte_carlo.py` |
| 20 | Kelly / optimal f as upper bound | ☐ | small; T-16 |
| 21 | Demo with the same rules and data | ◐ | demo bot built, **not running** since 2026-10-21; 3 days of orders |
| 21a | Reconcile demo trades with the engine | ☐ | T-06 / V2.4b; needs demo fills. **Largest realism unknown** |
| 22 | Live monitoring: binomial loss streak, chi-square win rate | ☐ | T-17 |
| 23 | Trial log, effective number of trials | ☑ | `results/trials.jsonl`, runner appends every variant |
| 24 | PSR and DSR > 0.95 | ☑ | `analytics/deflated_sharpe.py`, runner + verdict |
| 25 | CPCV, PBO < 0.5, time-reversed run | ☐ | T-09 (López de Prado AFML ch. 7, 11-12; book notes present) |
| 26 | Matched monkeys: random entry / exit / both, net R and DD | ◐ | random exit in the entry screen ☑; full monkey test ☐ (T-14) |
| 27 | Entry-only screen | ☑ | `analytics/entry_screen.py`, `tools/entry_screen.py` (not in the runner) |
| 28 | Bayesian report under 3 priors, trades needed before the MT5 test | ☐ | T-10 ★, prior set by the user 2026-10-16 (book notes: Kurt) |
| 29 | Effective N for overlapping trades | ☐ | T-19 |
| 30 | Gates written into `docs/` before the run | ◐ | verdict thresholds in code; per-idea pre-registration ☐ (T-17) |
| 31 | Expectation haircut (live ≤ 50-75 % of backtest) | ☐ | one line on the research card |
| 32 | Quit rule, performance cone, incubation | ☐ | T-17 |

Count: 8 ☑, 17 ◐, 11 ☐ (of 36 incl. 14a-c and 21a).

## Realism of the simulation itself (engine, costs, data)

Checked beyond the checklist:

- ☑ No lookahead (views, HTF clock, tests per detector), entries at the confirming candle's close.
- ☑ Gaps: a candle opening beyond the stop fills at its open (weekends, cash opens).
- ☑ Spread (bid candles, ask = bid + spread), commission (per lot or % of notional), swap at
  17:00 New York with the triple day, Binance funding, slippage on market fills (since B4).
- ◐ **Spread at the time of the trade:** the default is a fixed spread per symbol, scaled by
  price. Strategies 2, 5, 6, 7 trade at the index cash open, where FTMO's spread is wider than
  average. A spread table by year and hour exists (ROADMAP 6.7) but is **off by default** (the
  user's default). The exit pays the entry's spread, not the spread at the exit time.
  Proposal for the user: measure how much the table changes the golden lists; if it matters,
  make it the default for MT5-period runs.
- ◐ Slippage: a preset (~half the spread), not measured. V2.4b (from demo fills).
- ☐ News: no economic calendar, so no check of results with / without high-impact news
  minutes (where spreads and slippage blow up). Proposal: a news-day split like the shock-day
  check, from a free calendar export.
- ◐ Data: histdata (2015-2021, bid, no real spread / volume) vs MT5 (2021+). The development
  period therefore runs on a different feed than the test period; `tools/feed_compare.py`
  measured the difference once. Acceptable, but the research card should name the feed per
  period.
- ☑ Account side: lot sizing per symbol, FTMO daily loss on the initial balance, adaptive
  risk, prop-firm pass simulation.

## Order proposed (Opus)

1. **Grid merge (V2.4, now), extended:** A-E as agreed plus, because they are runner-level:
   parameter sensitivity ±10-20 % around the chosen variant (#9), filter twin comparison (#10),
   standard error of expectancy and time in market on the scorecard (#15, #16), expectation
   haircut line (#31).
2. **V2.4c Honesty tooling, before V2.6 research starts** (already ideas T-xx, sources in
   `knowledge/`): T-10 Bayesian report (★, prior already set), T-09 CPCV + PBO, T-19 effective
   N, T-14 matched monkeys (generic random entry for every strategy), T-03 intrabar order from
   M1 (12.2). Then the spread-table measurement and the news split.
3. **V2.4b** demo fills -> slippage + reconciliation (T-06): needs the demo bot running.
4. T-17 gates / quit rule / performance cone and vol-targeted sizing with V2.7 (portfolio, live).

## Books

The method books behind the checklist are already summarised in `knowledge/books/`
(Kaufman, Davey, López de Prado AFML, Carver, Chan, Kurt). No book is required for the order
above. Three would add depth where the notes are thin (optional, for `Continue.Knowledge`):

- Robert Pardo, *The Evaluation and Optimization of Trading Strategies* (2nd ed.): walk-forward
  analysis and its efficiency measure, the standard reference for #12.
- David Aronson, *Evidence-Based Technical Analysis*: data-mining bias, White's reality check,
  Monte Carlo permutation tests (#25, #26).
- Timothy Masters, *Testing and Tuning Market Trading Systems*: permutation tests, selection
  bias, stationarity, with code-level detail.
