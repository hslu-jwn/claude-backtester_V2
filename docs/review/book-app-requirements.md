# What the three new books ask of the application (synthesis, 2026-10-23)

Sources: **RP** = Pardo, *The Evaluation and Optimization of Trading Strategies* (2008);
**TM** = Masters, *Testing and Tuning Market Trading Systems* (2018); **DA** = Aronson,
*Evidence-Based Technical Analysis* (2007). Details and page/chapter refs are in the three book files
next to this one.

**Scope (the user, 2026-10-23):** set up the main application first, strategies later. So this file
lists engine, testing and reporting capabilities, not trading ideas. It is background: nothing here
is a rule until the user picks it and it is written into a spec in `docs/`. Nothing in the V2 repo
was changed.

"V2 today" is based on a quick look at file names and docstrings in
`backtester-claude_V2/src/backtester` on 2026-10-23. Verify each item before building on it.

## A. Engine accuracy
| # | Requirement | Books | V2 today (to verify) |
|---|---|---|---|
| A1 | Decide on the bar close, fill at the next bar open (or the next tradable price); never at the signal bar's close when the signal needs that close | DA ch.1, TM ch.6-7 | engine docstring: market entries at "the close of the current base candle"; check that this is the next decision step and not a look-ahead |
| A2 | **Limit fills only on penetration** by X ticks/points (not on a touch); report the share of limits that were "touched but not filled" | RP ch.6 | `engine/backtest.py` `_fill`: a limit fills if `low <= entry <= high`, i.e. **on a touch** |
| A3 | Stops/targets gapped through fill at the open (stop worse, limit better); report gap slippage separately | RP ch.5-6 | V2.4 B-fixes mention "MAE at gap exits"; check whether the fills use the open |
| A4 | Same-bar SL/TP or entry/SL ambiguity resolved from a lower timeframe (M1) | RP ch.6 | ROADMAP 12.2 / T-03 open |
| A5 | Prices and orders rounded to the instrument tick | RP ch.6 | tick handling exists in `risk/sizer.py`, `live/`; check the engine |
| A6 | Unbounded lookback traps: EMAs / recursive filters need a long warm-up; rules depending on earlier trades make walk-forward boundaries leak | TM ch.5 | check the warm-up handling per strategy |
| A7 | All parameter sets in a grid start trading on the **same bar** (warm-up = max lookback of the grid) | TM ch.4, RP ch.13 | check the grid tools / research runner |

## B. Return series and statistics
| # | Requirement | Books | V2 today |
|---|---|---|---|
| B1 | A **bar-by-bar (or daily) marked-to-market return series** per run, with time-in-market flags, as the base for every statistic. Trade-level stats only for display. Never optimize on completed trades | TM ch.5-6 | daily net R exists (`analytics/daily.py`); check whether it is marked to market or booked at exit |
| B2 | **Detrended benchmark:** rule return minus the no-skill return of the same long/short bias, [p(L) − p(S)] × average change; or returns computed on detrended market changes. Show raw and detrended | DA ch.1 | not found (no "detrend" in the code) |
| B3 | Report position bias (share of time long vs short) and the Trend / Skill split | DA ch.1, TM ch.7 | not found |
| B4 | Lower confidence bound of the mean bar/daily return (t-based and BCa bootstrap); significance shown next to the effect size (statistical vs practical) | TM ch.6, DA ch.5, 8 | t-stat exists; no bootstrap found |
| B5 | Bootstrap **log(PF)**, never raw PF or Sharpe with few returns | TM ch.6 | — |
| B6 | Objective functions for optimization: profit factor / log PF on bar returns (TM's favourite), PROM and its strict variants, CECPP, neighbour-averaged objective; floors (min trades/year) and ceilings (max DD) | RP ch.9-10, TM ch.5 | pick = max net R (walk-forward docstring) |
| B7 | Consistency: remove-the-max test, year table with the trend of profit and DD, MDD vs average DD, conditions during the MDD and the max run-up, model efficiency vs Perfect Profit | RP ch.12 | partly (`robustness.py`: without_best, halves, kurtosis) |

## C. Optimization and robustness of the parameter space
| # | Requirement | Books | V2 today |
|---|---|---|---|
| C1 | Optimization profile report: % profitable, mean/SD/min/max, top within 1 SD of the mean, mean − 1 SD and − 3 SD > 0, shape (plateau vs spike) | RP ch.10 | partly (`robustness.py`: profitable_share, plateau, smoothing) |
| C2 | **Parameter sensitivity curves**: one parameter varied at a time around the chosen point | TM ch.4, RP ch.9 | ROADMAP 12.4 heat map open; audit item "sensitivity around the chosen variant" |
| C3 | Scan-range hygiene: proportional (%) steps, similar candidate counts, a degrees-of-freedom check (≥ 90 % left after warm-up, lookbacks and rules) | RP ch.6, 10, 13 | — |
| C4 | Prioritized one-at-a-time scan (parameter-impact report, cheap for many parameters) | RP ch.9 | — |
| C5 | Optional faster optimizers (differential evolution with a minimum trade count; GA, annealing). Guided search **cannot** feed CSCV or the cheap bias estimate | TM ch.3, RP ch.9 | grid only |
| C6 | Multimarket × multiperiod table: one parameter set, markets × 2-year segments | RP ch.8, 10 | year/halves tables exist per run |

## D. Out-of-sample procedure
| # | Requirement | Books | V2 today |
|---|---|---|---|
| D1 | Walk-forward with **configurable IS / OOS / step lengths** (not only whole years), many windows, a per-window table (period, chosen params, IS and OOS result, WFE, DD) and a concatenated-OOS summary | RP ch.11, TM ch.5 | `analytics/walk_forward.py`: yearly windows, anchored or rolling, pick = max net R |
| D2 | **Walk-forward efficiency** (annualized OOS / IS) and the expected live return ≈ WFE × latest IS | RP ch.11 | not found |
| D3 | Window length as a parameter: study OOS performance against retrain frequency / test length | RP ch.11, TM ch.5 | — |
| D4 | Open-trade boundary rule at IS end: max holding time + stop opening H bars early (TM's choice), or close and mark to market; carry the last IS position into the OOS | TM ch.5-6 | check `walk_forward.py` (it works on finished trade lists per variant) |
| D5 | **Nested walk-forward** whenever a "choose the best X" step sits on top (portfolio members, selector, regime switch, choice of criterion) | TM ch.5 | not found |
| D6 | **Selection bias:** a second untouched OOS segment, or train / test / validation segments, when choosing among systems or adding complexity | TM ch.5, DA ch.9 | data split 2021-09-14 + one MT5 test exists |
| D7 | Purge/embargo (model or overlapping-target setups) | TM ch.5 (also LP) | not found ("purg/embargo" absent) |

## E. Significance with data mining (the biggest gap)
| # | Requirement | Books | V2 today |
|---|---|---|---|
| E1 | **Trial log keeps the full daily return series (and position series) of every variant**, not only summary statistics | DA ch.6, TM ch.5, 7 | `analytics/trial_log.py` stores summaries only (trades, net R, mean, SD, skew, kurt, Sharpe, daily stats) |
| E2 | **White's Reality Check** (best-of-N bootstrap: zero-centred returns, the same resampled day indices for all variants, distribution of the max) | DA ch.6 | not found |
| E3 | **Monte Carlo permutation, best-of-N** (one permutation of detrended market changes applied to all variants' positions; distribution of the max) | DA ch.6, TM ch.7 | `risk/monte_carlo.py` permutes days (kind A); no best-of-N version |
| E4 | **MCPT of the training process:** re-optimize the whole grid on each permuted dataset; p = (k+1)/(m+1); also for the whole walk-forward procedure | TM ch.7 | not found |
| E5 | Correct permutation of OHLC bars: gaps (close → open) and intra-bar moves (O→H/L/C kept together) as two series; the same permutation for all symbols in a multi-symbol test; first training fold / inner OOS / outer OOS permuted separately | TM ch.7 | check how `random_walk.py` / kind D paths are built |
| E6 | CSCV / PBO on the variant returns matrix | TM ch.5 (also LP) | T-09 open |
| E7 | Romano-Wolf stepwise test and joint confidence intervals for all variants (later) | DA ch.6, 9 | — |
| E8 | Markowitz-Xu shrinkage of the best variant toward the average variant (a rough guide) | DA ch.6 | — |
| E9 | Data-mining bias drivers shown with every sweep: number of variants, observations per variant, average correlation between variant returns (effective N), outlier share | DA ch.6 | effective N is audit item T-19 |
| E10 | Trial-log IDs that encode family-type-input-parameters (Aronson's E-4-30-20-60 style); count inverse rules and rules borrowed from books as trials | DA ch.8 | key = family, strategy, settings, symbols, period, source |

## F. Risk projection and live monitoring
| # | Requirement | Books | V2 today |
|---|---|---|---|
| F1 | **Double-bootstrap drawdown bounds** (outer resample of the OOS set, inner DD quantiles over the next N bars; a DD_conf × Bound_conf table). A plain bootstrap underestimates catastrophic DD by up to 10× on short samples | TM ch.6 | Monte Carlo kinds A-D exist; check whether any is a plain bootstrap used for DD or FTMO-breach probability |
| F2 | Required capital / strategy stop: MDD × safety factor 1.5-3; quit rule written before going live | RP ch.5, 12, 14 | quit rule in the checklist (KD) |
| F3 | Live vs test profile: about 25 statistics, alarm below 50 % / above 150 % of the test value, scaled by volatility | RP ch.14 | demo reconciliation 12.5 open |
| F4 | Grouped-return bounds for monitoring: lower (p 0.05-0.1) and upper (p 0.4) bounds on weekly/monthly returns, with the order-statistic confidence of the bounds | TM ch.6 | — |

## G. Indicator diagnostics (for later strategy work, cheap to add to the app)
| # | Requirement | Books |
|---|---|---|
| G1 | STATN run-length table (how long an indicator stays above/below its median) | TM ch.2 |
| G2 | Relative entropy per indicator (≥ 0.5 wanted) and tail-only cleaning / rank transform helpers | TM ch.2 |

## Suggested order (my reading of the books; the user decides)
1. **E1** (store the daily series of every variant). Most later tests depend on it.
2. **B1 / B2 / B3** (marked-to-market daily returns, detrended benchmark, position bias): the base
   statistics.
3. **A2 / A4** (limit-fill penetration, same-bar ambiguity from M1): engine honesty; both change
   results, so measure them on the golden lists.
4. **D1 / D2 / D4** (flexible walk-forward with WFE and the open-trade boundary rule).
5. **E2 / E3 / E4** (best-of-N significance and MCPT of the training process).
6. **F1** (double-bootstrap drawdown), then **C1-C3**, **D5**, **E6**, **F3-F4**.

## Where the books disagree with each other or with the knowledge base
- **Parameters per market and periodic re-optimization** (Pardo) vs one parameter set pooled across
  markets (Kaufman, Carver in `knowledge/`). This needs the user's decision.
- **Optimization criterion:** Pardo PROM, Masters profit factor on bar returns, our runner max net
  R. They agree on avoiding raw net profit alone.
- **Cross-validation:** Masters distrusts CV for performance estimates (fine for structure choices);
  López de Prado (already in `knowledge/`) prefers purged CPCV. Both reject a single unpurged
  split.
- **Monte Carlo of drawdown:** the knowledge base (Davey) uses resampling of the walk-forward trade
  list; Masters shows that a plain resample is anti-conservative for rare large drawdowns, so use
  his double bootstrap.

## Merge hints for `knowledge/` (for the session that integrates this)
- `topics/testing-and-robustness.md`: WFE, the optimization profile, PROM/CECPP, DF/warm-up, the
  open-trade boundary rule, nested WF, MCPT of training, best-of-N tests (WRC, MCP), the five bias
  factors, selection bias / three segments, the retrain-frequency study.
- `topics/statistics-and-bayes.md`: max-of-N sampling distribution, bootstrap/BCa, log PF,
  order-statistic bounds, double-bootstrap DD, Markowitz-Xu shrinkage, p-value pitfalls.
- `topics/costs-and-execution.md`: limit penetration, gap slippage, silent open/close slippage,
  tick math, same-bar ambiguity.
- `topics/position-sizing-and-risk.md`: required capital and the strategy stop, Kelly caveats.
- `topics/backtest-frameworks.md`: platform feature list (RP ch.4), the differential-evolution
  optimizer, the criterion wrapper.
- `topics/markets-and-regimes.md`: risk-premium explanations (DA ch.7), market types (RP ch.6),
  STATN/entropy.
- `README.md` › Books read: add RP, TM, DA with short descriptions (see `README.md` in this folder).

## Verified against the code (Opus, 2026-10-23)

| # | Claim | Verified |
|---|---|---|
| A1 | entries at the signal candle's close | **true** (`engine/backtest.py` `_fill`), plus adverse slippage on market entries. No lookahead (the decision uses that close); the books' "next open" differs only at gaps between candles (session opens) |
| A2 | limits fill on a touch | **true, and wider than stated:** limit entries (only strategy 3) **and every take profit** (`engine/trade.py` `_beyond`: long `price >= level`) fill on a touch. Affects all strategies with a TP |
| A3 | gaps through stops / targets fill at the open | **true** (`trade.py` `gap_fill`, `stop_at_open`); gap slippage is not reported separately |
| A4 | same-bar SL / TP from M1 | **open** (SL first; ROADMAP 12.2 / audit V2.4c) |
| A5 | prices rounded to the tick in the engine | **no:** tick / digits only in `risk/sizer.py` and `live/` |
| A7 | all grid variants start on the same bar | **mostly:** every variant gets the same period and warm-up days; a long lookback (D1 SMA 200) still starts trading later in the first cached year |
| B1 | daily return series marked to market | **no:** `analytics/daily.py` books a trade on its exit day |
| B2 / B3 | detrended benchmark, position bias | **not found** |
| B4 / B5 | bootstrap / BCa bounds, log PF | **not found** (t-statistic only) |
| D1 / D2 | walk-forward windows, WFE | **yearly only, no WFE**; grid merge 3 (running) adds WFE on yearly windows in the runner |
| D5 | nested walk-forward | **not found** (needed by V2.7 when the portfolio picks members) |
| E1 | daily series of every variant kept | **partly:** the trial log keeps summaries only; runner variants keep their trades (`variants/<id>/trades.csv`), so their daily series can be rebuilt; older trials cannot |
| E2-E4 | best-of-N tests, MCPT of training | **not found** |
| E6 / E9 | CSCV / PBO, effective N | **open**, already in audit V2.4c (T-09, T-19) |
| F1 | drawdown Monte Carlo | **anti-conservative, worse than a plain bootstrap:** kind A is a *permutation* of the same days (`risk/monte_carlo.py` `rng.permutation`), so no simulated path holds a day worse than the history; drawdown and FTMO-breach probability are optimistic |
| C2 | sensitivity around the chosen point | **built** in grid merge 2 (runner `sensitivity.csv`) |
