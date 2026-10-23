# Timothy Masters, *Testing and Tuning Market Trading Systems: Algorithms in C++* (Apress 2018)

Short: **TM**. The ebook has no page numbers, so cite by chapter and section: `TM ch.6 "Bounding Drawdown"`.
Source PDF: `X:\Dokumente\Archiv\Trading\Testing_and_Tuning_market_trading_systems_-_Timothy_Masters.pdf`.
C++ source for every program is on the publisher's GitHub (see the book's product page). Notes written
2026-10-23, in our own words. Focus: algorithms the **application** should get. No strategies are
endorsed in the book.

## Overview
- An algorithm book for honest testing: is the optimized system real or fitted to noise; how
  biased are IS results; how to walk forward correctly (including nested walk-forward); lower
  bounds on future returns; the probability of catastrophic drawdown; permutation tests that also
  handle selection bias.
- The demos use day bars, decisions on the close (he says a real system should decide on the close
  and fill at the next open) and **no costs**, to keep the focus on the statistics.
- Every return is a **difference of log prices**. Percent returns are asymmetric: +10 % then the
  move back to the start is −9.1 %, so a system that went nowhere looks like it made almost +1 %.
- Main messages: future leak is deadlier than people think; trade-level statistics are misleading;
  optimize on bar returns; use permutation tests to judge the training process; bound drawdown with
  a double bootstrap, not a plain one.

## Chapter notes

### Ch 1 - Introduction
- Rule-based vs model-based systems (indicators → predictive model → target, e.g. "profit target
  hit before the stop"). The book covers both.
- **Future leak:** even a tiny leak is enough. A random win-1/lose-1 system with a 1 % edge already
  produces an impressive equity curve.
- **Percent-wins fallacy:** E = P(win) × W − P(loss) × L. On a random walk, a target of 1 and a
  stop of 9 win 90 % of the time and still have E = 0. A win rate means nothing without the
  win/loss sizes.

### Ch 2 - Pre-optimization: stationarity and indicator information
- Markets are always non-stationary; formal tests always say so and therefore tell us nothing. The
  danger is **slow wandering** of an indicator's mean or variance: the model goes silent or wrong
  for months or years. Plot indicators and the equity curve. Profit concentrated in one stretch of
  time (especially long ago) is a warning.
- **STATN test:** for an indicator (trend = least-squares slope, volatility = ATR) count how many
  bars in a row it stays above or below its median, in bins of 1, 2, 4, … 512, > 512. Many runs
  longer than 256 bars = slow wandering. On OEX, raw volatility had six runs longer than 512 bars.
- Fixes: indicator minus its value `lookback` bars ago; short-lookback minus long-lookback version;
  in the extreme case, subtract a moving median and divide by a moving IQR. A shorter window gives
  more stationarity but loses level information.
- **Relative entropy** of an indicator: H / log(K) over about 20 equal-width bins of its range. Aim
  for ≥ 0.5; below 0.1 is serious. Low entropy usually means outliers or clumps, and it goes with
  poor model training.
- Fixes for low entropy: avoid dividing by values that can be tiny; use only **monotonic**
  transforms (keep the order); no truncation; tail-only compression (log-compress only the outer
  1-10 % / 90-99 %); sqrt, cube root or log for skew; tanh or logistic (after scaling) for heavy
  tails; normal CDF for nearly normal indicators; **rank transform** (percentile within a
  representative sample, minus 0.5), optionally followed by the inverse normal CDF to keep moderate
  extremes.
- Example on S&P, lookback 20: trend 0.58, volatility 0.64, "expansion" (a ratio of ranges) 0.46
  (and 0.00 at lookback 7), raw jump 0.48 → 0.96 after cleaning only the outer 5 % tails.

### Ch 3 - Optimization (mostly for model-based systems)
- Indicator quality matters far more than model power. Start with linear models (less overfitting,
  easy to understand, fast to retrain, which matters for permutation tests).
- Elastic-net regularized regression (alpha 0 = ridge, 1 = lasso; lambda chosen by 5-10-fold
  cross-validation along a lambda path; coordinate descent). Demo on OEX: no regularization had the
  best IS fit and the worst OOS; alpha 0.1 was the best OOS.
- **Differential evolution (DE)**, a general optimizer for rule-based systems too. A child =
  primary parent crossed with (secondary parent + F × (diff1 − diff2)); the better of child and
  parent survives. Masters' additions: over-initialization (about popsize extra random candidates
  replace the worst); reject candidates below a minimum trade count (scale the criterion so that
  0 is the rejection threshold, e.g. log profit factor); stop after about 50 or more generations
  without improvement; crossover probability 0.1-0.5; an occasional hill-climb on one parameter of
  the best individual; integer parameters first; hard bounds with a penalty. DE adapts its step
  sizes to the shape of the criterion surface.
- Clean architecture: a generic optimizer calls a criterion wrapper; the strategy-specific data
  lives behind the wrapper.

### Ch 4 - Post-optimization checks
- **Training bias** = IS performance − OOS performance. It comes from noise learned as pattern and
  from patterns missing from the IS data.
- **Cheap bias estimate (StocBias):** needs the bar-by-bar returns of every random or grid trial
  (never of guided-search children). For each bar b, a trial's "IS" = total − r_b; per bar, keep
  the trial with the best IS and note its r_b ("OOS"). Bias ≈ mean best IS per bar − mean OOS.
  Needs thousands of trials. OEX: optimized 2.671 − bias 0.322 = expected 2.349.
- **Parameter relationships (PARAMCOR):** fit a quadratic surface to the final DE population near
  the optimum (parameters scaled to comparable ranges). The Hessian gives each parameter's relative
  "slack", parameter correlations, and the directions of most and least sensitivity. A
  non-positive diagonal = that parameter is not at an optimum, or the performance jumps around with
  it.
- **Parameter sensitivity curves = minimum due diligence:** vary each parameter alone across its
  range, the others held at the optimum, and plot the performance. Broad smooth peak = good; narrow
  peak = will fall off as the market drifts; several nearby peaks = luck (catching or missing a few
  big trades).
- Demo detail: every parameter combination starts trading on the **same bar** (fair comparison).

### Ch 5 - Unbiased trade simulation (walk-forward done right)
- Realistic goal: weed out systems with a small expected return, not predict the future.
- **Choice of criterion:** with plenty of data it barely matters; with little data it matters a
  lot. Optimizing the mean return gives the largest training bias. **Profit factor** usually gives
  the smallest bias and often the best OOS (his favourite); the Sharpe ratio is also fine.
- **Selection bias:** picking the best of several systems by their OOS results makes that OOS
  figure optimistic again. The fix is a second untouched OOS period to measure the chosen system.
- Walk-forward: train up to OOS_START, test NTEST bars, step by NTEST, pool all OOS (contiguous, so
  the drawdown is valid). The fold size should match how often the system will be retrained live.
- **Overlap leak (model datasets):** if the indicator lookback and the target lookahead are both
  longer than 1 bar, drop OMIT = min(lookahead, max lookback) − 1 training cases before each OOS
  block. Overlapping targets also make OOS returns serially correlated, which inflates the error
  variance and makes p-values too optimistic. Fix: NTEST = 1 and advance by the lookahead
  (EXTRA = lookahead − 1). Prefer a 1-bar lookahead.
- **OVERLAP experiment** (random walk, lookahead 10): no omission → median t 5.35 (ntest 50) or
  74.6 (ntest 1); omit 8 instead of 9 → t 1.88; omit 9 → t ≈ 0 but 31 % "significant" at 0.1;
  omit 9 + skip 9 → t ≈ 0 and 10.1 % (correct). Purging must be exact.
- **Robustness against non-stationarity:** rerun the walk-forward with longer and longer test
  periods (retrain every 1, 2, … bars) and plot OOS performance against test length. The drop shows
  how often retraining is needed. More sensitive: score only the last bar of each test fold.
- **Open-ended trades at the IS/OOS boundary (rule-based systems):** with "hold until the exit
  rule fires" the lookahead is unknown, so the lookback sets the guard. Five options:
  1. Let IS trades run past the IS end: **future leak**, never do it.
  2. Force-close and mark to market at the IS end.
  3. Add a maximum holding time H and stop opening trades H bars before the IS end (Masters'
     choice; trades turn into coin flips after a while anyway).
  4. Let trades run, but stop opening (max lookback − 1) bars before the IS end.
  5. **Bar-by-bar mark-to-market returns** (see ch.6). Best granularity; needed for CSCV.
- **Unbounded lookback traps:** EMAs and recursive filters (they depend on all history); rules that
  depend on earlier trades (pause after four losers; "open only if no trade is open").
- Cross-validation vs walk-forward on the same system gives significantly different, often wildly
  different, results. Masters does not trust CV for performance estimates (it uses future data and
  is optimistic under non-stationarity).
- **CSCV / probability of backtest overfitting** (Bailey et al. 2015): returns matrix (rows =
  competing parameter sets from a grid or random draw, never from a guided search; columns = bar
  returns at the same granularity). Split the columns into S blocks (S even); for each of the
  C(S, S/2) splits, find the best IS row and its OOS rank fractile; count the share ≤ 0.5 ≈ the
  probability that the IS winner is below the OOS median. It is relative to the competitor set:
  absurd parameters make it look good, a set that is too narrow makes it look bad. SPX MA
  crossover: 0.004-0.036. It says nothing about risk/reward.
- **Nested walk-forward:** needed whenever a second decision (choose the best system, market,
  criterion, portfolio members, or regime switching between trend, mean-reversion and breakout)
  uses results of the first stage. Level 1 walk-forward produces OOS1 returns per competitor per
  bar; the Level 2 selector uses the last OOS1_n of them; its next bar is OOS2 (fully OOS). Compare
  competitors only over the OOS2 bars. Markets must be time-aligned. Demo (65 S&P 100 stocks,
  2 decades): equal-weight basket 8.7 %/yr; best market by total return 17.9 % (p .076); choosing
  the criterion by its recent OOS: 19.1 % (p .027).
- CV nested inside walk-forward is fine for structure choices (model complexity, predictor
  selection).

### Ch 6 - Trade analysis: bounds on returns and drawdown
- **Bar returns, not trade returns.** Convert open-ended systems to marked-to-market bar returns.
  Hand the last training position over to the first OOS bar; the same handover takes the last fold
  into live trading.
- Ways to package OOS returns: bars with a position (the usual), all bars (includes time in the
  market), fixed blocks or weekly/monthly sums (dilute wild bars; good for monitoring), completed
  trades (bad for statistics: N divided by the holding time, intra-trade volatility lost, extreme
  metrics). Example: two trades of +101/−100 bar-wise → trade PF infinite, bar PF 1.01. **Never
  optimize on completed trades.** Completed-trade accounting in an OOS block must start flat.
- **Lower bound for the mean future return:** a great backtest is not enough. LB = mean − t_p ×
  SD / √n (n=100, mean 8, SD 5, p .95 → 7.17). H0 is rejected exactly when LB > 0. Large samples
  detect tiny real skill (0.5 %/yr): significant is not the same as tradable. A t-test is robust to
  skew but one wild outlier ruins it: plot a histogram first.
- p-values: fix alpha in advance. A p-value is not the probability that the system is worthless,
  and p-values cannot rank systems (they depend on the sample length).
- **Bootstrap:** percentile, pivot (least reliable), **BCa** (bias-corrected and accelerated:
  z0 from the share of bootstrap statistics below the original, acceleration from a jackknife,
  adjusted percentiles). Each bootstrap sample has the original size; B ≥ 10,000 for serious work.
  Demo SPX MA breakout: open-position bars ≈ 9.9 %/yr, but p 0.10 and the 90 % lower bound ≈ 0 →
  "not tradable".
- **Bootstrapping ratios** (Sharpe, PF) is unreliable with few returns: with 50 returns the PF
  lower bound is useless and the upper bound is violated 4× too often. **Bootstrap log(PF)**
  instead; in general, tame heavy tails before bootstrapping.
- **Bounding future grouped returns** (monthly/quarterly) for monitoring: lower bound = m-th
  smallest of n OOS returns (m = n·p conservative, (n+1)·p unbiased); needs ≥ 100, better several
  hundred returns. The bound is itself uncertain: P(m-th smallest > q-quantile) = 1 − I_q(m, n−m+1)
  (incomplete beta). Example n=200, p .1: with probability .999 the real failure rate ≤ 18 %.
  Also set an **upper bound with a large "failure" rate** (e.g. 40 % of periods should reach it);
  too few periods reaching it is also a sign of decay. Demo OEX (quarterly, 124 returns, a poor
  system at 1 %/yr): 10 % of quarters worse than −38.9 % annualized.
- **Bounding drawdown:**
  - The plain bootstrap (resample OOS returns, compute DD, take a percentile) ignores that the OOS
    sample is itself a random draw. It **underestimates the probability of catastrophic drawdown by
    more than 10×** for small samples (63 returns, p .001: 13.65×) and about 2× for moderate ones.
    It is acceptable only with a large OOS set (2,520 returns: 1.04-1.54×) and modest
    probabilities (0.10).
  - **Correct = double bootstrap:** the outer loop resamples the full OOS set; the inner loop
    (≈10,000) draws drawdown-period-long sequences (e.g. 252 bars) from that outer sample and takes
    the DD quantile at DD_conf (0.90/0.95/0.99/0.999); the Bound_conf percentile (0.6-0.9, higher
    for extreme DD_conf) of the outer quantiles is the bound. With Bound_conf 0.8 it is
    conservative except for a tiny sample at p .001. It costs about 100 M iterations: seconds to a
    minute per system, too slow inside an optimizer.
  - Drawdown measured in log-equity units (no dependence on starting equity); % DD = 100 ×
    (1 − e^−dd). The bound applies to one specified future period (e.g. the next year), not to
    "ever".

### Ch 7 - Permutation tests (MCPT)
- Permuting destroys real patterns. Compare the original result with m permuted runs:
  **p = (k+1)/(m+1)**, k = permuted runs ≥ the original. m ≥ 100, 1,000+ is typical. Every
  permutation must be a plausible real-world outcome under the null.
- **Three uses:**
  1. A fully specified system on OOS data: permute only the OOS price changes (not the warm-up bars
     before the OOS).
  2. **The training process:** re-optimize on each permuted IS dataset. An overfit system also
     looks great on permuted data, so the original does not stand out. Require p ≤ 0.05; otherwise
     distrust the specification or the optimization ("one of the most valuable tools").
  3. **The model factory** (the whole walk-forward procedure): permute everything after the first
     training fold (that fold is never OOS; he permutes it separately).
- **Selection-bias version:** for each permutation run all competitors; "unbiased p" for a
  competitor = the share of permutations whose **best** result ≥ that competitor's original. It is
  exact for the best competitor and conservative for the others.
- **Return partition:** total IS return = Skill + Trend + TrainingBias. TrendPerReturn = (log
  last − log first)/n; Trend part = (n_long − n_short) × TrendPerReturn. On permuted retrains,
  Skill = 0, so TrainingBias = permuted total − permuted Trend (averaged over hundreds of runs).
  Unbiased future return = total − TrainingBias; Skill = total − Trend − TrainingBias. An option:
  subtract TrendPerReturn from every bar return inside the optimization criterion.
- **How to permute:** a Fisher-Yates shuffle of **log-price changes**, rebuilt from the first price
  (start and end are preserved, so the trend is too). Several markets: align the dates and apply
  the **same permutation to all** (keeps the cross-correlation). Sections (first training fold,
  inner OOS, outer OOS) are permuted separately so that nothing that was not OOS in the original
  can leak into a permuted OOS area.
- **OHLC bars:** store (high−open, low−open, close−open) per bar as one unit; permute the gaps
  (previous close → open) and the intra-bar moves as **two separate series**; rebuild. A naive
  open-to-open permutation creates absurd gaps and breaks the test. Option: keep the first gap and
  the last intra-bar move fixed.
- Demos: conservative returns = next open → following open after a decision on the close. MA
  crossover p .001 on SPX, mean-reversion p ≈ 1.0 on SPX: very different results on similar
  indices.

## For the application (what to build)
| Item | Source |
|---|---|
| Bar-by-bar marked-to-market return series per run (with time-in-market flags) as the base for every statistic; trade-level stats only for display | ch.5-6 |
| Walk-forward with the boundary rule for open trades (max holding time + stop opening H bars early, or a lookback guard) and the position handed from IS to OOS | ch.5-6 |
| Nested walk-forward for any "choose the best X" step (selector, portfolio, regime switch) | ch.5 |
| Retrain-frequency study: OOS performance vs test-window length | ch.5 |
| **MCPT on the training process** (re-optimize on permuted data; p = (k+1)/(m+1)) and on the walk-forward factory | ch.7 |
| Selection-bias permutation p (best-of-N) for sweeps and trial logs | ch.7 |
| Correct OHLC bar permutation (gap and intra-bar series separate; the same permutation across symbols) | ch.7 |
| Skill / Trend / TrainingBias partition | ch.7 |
| CSCV / PBO on the returns matrix of a grid (random or grid trials only) | ch.5 |
| Lower confidence bound for the mean bar return (t and BCa bootstrap); bootstrap log PF, not PF | ch.6 |
| **Double-bootstrap drawdown bounds** (DD_conf × Bound_conf table for the next N bars) | ch.6 |
| Grouped-return monitoring bounds (lower at p 0.05-0.1, upper at p 0.4) with order-statistic confidence | ch.6 |
| Parameter sensitivity curves (one parameter at a time) | ch.4 |
| Cheap training-bias estimate from random/grid trials (StocBias) | ch.4 |
| Optional: differential-evolution optimizer with a minimum trade count; criterion wrapper | ch.3 |
| Indicator diagnostics: STATN run-length table and relative entropy per indicator | ch.2 |
| Optimization criterion default: profit factor (or log PF) on bar returns; never on completed trades | ch.5-6 |
| Same start bar for all parameter sets in a grid (warm-up = max lookback) | ch.4, 6 |

## Testable ideas (not now)
The demo systems are deliberately primitive (thresholded MA crossover, MA breakout, "long-term
uptrend + sharp 1-bar drop → long next bar" mean reversion, best-recent-performer rotation). They
are not offered as edges.

## Warnings / pitfalls
- No costs in any demo: every return figure is gross.
- A plain bootstrap of drawdown is anti-conservative: our current Monte Carlo kinds should be
  checked against this (see app-requirements.md).
- Bootstrapped Sharpe or PF bounds with fewer than about 100 returns are unreliable.
- CSCV and the cheap bias estimate are invalid with guided-search (GA/DE) trials.
- An exact purge matters: being off by one bar still leaks.
