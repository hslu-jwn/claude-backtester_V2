# Testing and robustness

How to test a strategy so the result can be trusted. This is the most useful part of the books for us.
Sources: K = Kaufman *TSM* (ch. 1-2, 5, 8, 21-23 mainly), D = Douglas, H = Hougaard, LP = López de Prado (chapter.section),
RC = Carver, EC = Chan, KD = Davey, WK = Kurt. Page numbers are the book's own; the math is in [statistics-and-bayes.md](statistics-and-bayes.md).

## Core principles
- **Test to validate an idea, not to find one.** Start from a premise with a reason (behaviour, flows,
  structure). A computer scan over everything finds chance patterns (K p.18-19, 331, 470: the
  "18 years of coffee/wheat" story that failed in year 19). López de Prado: a backtest is not a research tool, it
  only discards bad models; if it fails, start over instead of patching (LP 8.2, 11.4); every patch is hidden curve
  fitting (KD ch.8). A strategy needs a named reason why someone else loses money to us (LP 1.3.1.3; KD p.150).
- **Write the expectation first:** trade count, win rate, avg R, holding time, drawdown. A result far
  from the expectation, good or bad, means a bug or a wrong premise (K p.907). Be as suspicious of good
  results as of bad ones (K p.19).
- **The best optimisation result never comes true.** Expect the *average* of all tests over a sensible,
  pre-declared parameter range; better still, mean minus 1 standard deviation (K p.938-945).
- **Simple beats complex:** at most about 4 free parameters (K p.938, Futures Truth). Start simple, add
  complexity slowly, stop early.
- **The market matters more than the formula.** All simple trend methods have about the same profit
  factor on a given market (K ch.8 comparison, p.336-349). Choosing *where* to trade (low-noise
  markets) beats choosing *how*.

## Data and sample
- Sample error is about 1/sqrt(N): 4 trades 50 %, 100 trades 10 %, 400 trades 5 % (K p.28; WK ch.14). In years:
  proving a true Sharpe of 0.3 takes ~37 years (RC Table 5); in trades see [statistics-and-bayes.md](statistics-and-bayes.md). Ignore
  profit factor below about 30 trades; PF 76 on 8 trades means nothing (K p.946).
- Data must contain bull, bear and sideways phases. A one-way history flatters any biased system (K p.29).
- Use daily equity for drawdown and risk; monthly data hides risk (K p.53).
- Test and trade on the same data source (K p.980): for us histdata vs FTMO feed (see `tools/feed_compare`).
- Douglas's 20-trade sample is an alarm for gross failure only, not a test (D ch.11; with 20 trades the
  win-rate error is about ±20 points).

## In-sample / out-of-sample
- Reserve about **50 %** of the data out-of-sample, decided **before** development. Best split:
  alternating random blocks fixed in advance; stitch daily returns, not block totals (K p.916-917).
- OOS is used **once**. Changing anything after seeing OOS turns it into in-sample (K p.27, 917).
- Typical OOS result is about half the in-sample return; information ratio 2.0 -> 1.0 is fine,
  2.0 -> 0.4 is a fail (K p.917).
- **Sibling markets are free OOS:** an S&P idea should work on Nasdaq. For us: NAS100 <-> US500,
  GBPUSD <-> GBPJPY (K p.945).
- Walk-forward: windows long enough that the best parameter does not jump between fast and slow;
  chain only OOS pieces; keep a final untouched hold-out (K p.918-919). Davey (KD ch.13): fix in-period, out-period
  and fitness **before** the run (in = 25-50 trades per optimised input, out = 10-50 % of in, unanchored, net profit);
  if you must choose the windows, do a nested walk-forward on early data and run the chosen pair once on the last
  ~3 years; if it fails, abandon. He holds back only 10-20 % (the newest) as plain OOS (KD ch.5).
- Walk-forward is **one path** and can be re-run until it looks good (LP 11.6, 12.2); a rule that works only forward
  in time and fails on the time-reversed series is suspect (LP 12.2). Chan: true OOS starts only when the rule is
  frozen; expect live Sharpe at best about half the backtest (EC p.2-7).
- **Walk-forward efficiency (WFE)** = annualized OOS profit / annualized IS profit: about 25 % = overfit or unsound, 50-60 % or
  more = robust, above 100 % happens and proves nothing alone. Expected live profit ≈ WFE × the latest IS annual profit; live
  efficiency below the WFE hints at mild overfit (RP ch.11, 13). Fits K's "OOS about half of IS" above; the cut-offs are Pardo's
  rules of thumb, no data shown.
- **Many windows, short IS:** 10-20 years of data and 10-20+ walk-forwards; the strength comes from the total concatenated OOS
  length. IS 1-2 years for fast systems, 3-6 for slow; OOS 25-35 % of IS; step = OOS length so every bar is OOS exactly once.
  Report a per-window table (IS period, chosen parameters, IS and OOS result, WFE, DD) and max DD per IS and OOS window: OOS DD is
  more realistic because optimization rejects high-DD sets (RP ch.11). Live trading re-optimizes on the same schedule.
- **Window sizes are parameters**, so tuning them is itself a search; one walk-forward path can still be overfit (RP ch.13; LP 11.6,
  12.2). Retrain-frequency study: rerun the walk-forward with test windows of 1, 2, ... bars and plot OOS performance against test
  length; the fall-off shows how often retraining is needed (TM ch.5; RP ch.11: trade 1/8 to 1/3 of the optimization window).
- **Open trades at the IS end** (rule systems with "hold until the exit fires"): letting IS trades run past the IS end is a future
  leak. Options: force-close at the IS end; max holding time H plus no new trades H bars before the end (Masters' choice); best,
  bar-by-bar marked-to-market returns with the last IS position handed to the first OOS bar (TM ch.5-6). EMAs and rules that depend
  on earlier trades have an unbounded lookback and leak across window edges (TM ch.5). Every grid variant starts on the same bar
  and warm-up history is loaded before each window (TM ch.4; RP ch.13).
- **Nested walk-forward** whenever a "choose the best X" step sits on top of the first stage (market, portfolio member, criterion,
  regime switch): level 1 gives OOS returns per competitor, the selector picks from their recent OOS, and only the level-2 OOS bars
  count (TM ch.5). Choosing among systems by their OOS result makes that OOS optimistic again: keep a second untouched OOS, or use
  train / test / validation segments (test chooses the complexity, validation stays untouched) (TM ch.5; DA p.441-475).

## Parameter grids and surfaces
- Pre-declare ranges; use **geometric spacing** (5, 10, 20, 40, 80, 160 or ×1.5), not equal steps,
  which overweight the slow end (K p.908-910, 299-301, 330).
- One parameter at a time, most important first (trend speed), then filters, then stops. Stops and
  filters refine; they must not rescue a losing core (K p.908-910; "vertical development" p.989).
- Look at the 1-D curve / 2-D heat map. Accept only **broad plateaus**; a lone spike surrounded by
  losses is a fluke; an erratic map means no edge or a bug (K p.922-931). Smooth each cell with its
  neighbours (3 in 1-D, 9 in 2-D) and pick the centre of the plateau.
- **Robustness score:** share of combinations in the declared range that are profitable. About 70 %
  = robust; under 50 % = reject (K p.945; valid only if the range was not narrowed afterwards).
- A new rule must improve the **average of all tests** (or cut dispersion at the same mean). If it
  only lifts the peak or touches 1-2 trades, it is overfit (K p.937). Compare % profitable combos
  with and without the filter (K p.989).
- **Optimization profile** (RP ch.10): share of profitable sets (< 5 % reject, >= 20 % with significant profit marginal); mean > 0,
  mean - 1 SD > 0, mean - 3 SD > 0 (very strong), top set within 1 SD of the mean, small max-min range; shape = smooth hill whose
  top has profitable neighbours. **Disagreement:** Pardo's 20 % bar is far looser than K's about 70 % and Davey's 70 % gate (K p.945;
  KD p.106); our checklist keeps the stricter one. Overscanning (steps too fine) fills the set with near-copies and inflates the
  % profitable while shrinking the SD (RP ch.13).
- **Neighbour-averaged objective** (RP ch.10): average each cell with its two neighbours; his spike (12.5k, neighbours -0.5k and 3k
  → 5.0k) loses to the plateau (7k, 6.5k, 5k → 6.2k). Same idea as K's smoothing above.
- **Objective function:** Pardo ranks by PROM (pessimistic return on margin; penalises small samples) or CECPP with floors and
  ceilings (min trades a year, max DD); Masters finds profit factor on bar returns gives the smallest training bias and mean return
  the largest, with little difference when data is plentiful (RP ch.9; TM ch.5). They differ, and our runner uses max net R; all
  agree not to rank by raw net profit alone.
- **Sensitivity curves** (minimum due diligence): vary one parameter at a time around the optimum; a broad smooth peak is good, a
  narrow one falls off as the market drifts, several close peaks are luck (TM ch.4). A prioritized one-at-a-time scan costs the sum
  of the steps, not their product, and shows each parameter's impact; a flat one is fixed or dropped (RP ch.9).
- **Degrees of freedom:** remaining DF % = 100 × (1 - used/available), each lookback bar and rule uses one; keep >= 90 % (a 30-bar
  MA on 100 bars leaves 70 %: skip it). Warm-up bars bias small-sample optimization toward short lookbacks. Scan steps proportional
  in %, with similar candidate counts per parameter (RP ch.6, 10, 13).
- **Per-market parameters + periodic re-optimization (RP ch.6, 11) vs one pooled parameter set (Kaufman; Carver, see "Whole
  classes" below):** open conflict; Pardo's preference is untested here. Needs the user's decision.
- Count every variant ever tried. One good configuration in 1000 is not significant (K p.945). Log them all with
  their return series, so the Sharpe can be deflated (LP 11.5, 14.7; RC Tables 3-4); see the next section.

## Stability checks
- **Halves / years table:** P/L per year and per half; slope of periodic returns (declining = decay)
  (K p.941, 1046). 2-sample (Welch) t-test of trade R between halves (K p.47-48).
- **Cross-market:** same rules and parameters on every symbol of a class and on neighbouring
  timeframes; profitable in at least half the markets (K p.954-970; Lukac et al.: only a third of
  systems were consistently profitable).
- **Outliers:** remove the best trade / best move and look again; study the 10 biggest wins and
  losses. Many big wins and no big losses = overfit (K p.941). Kurtosis of daily returns above about
  7-8 is a warning sign (K p.43).
- **Consistency (Pardo):** remove the maximum and recompute the mean; a drop of more than 1-2 SD means one outlier carries the
  result. Year table: falling profit with rising DD = decay, one big year hiding losses = reject. MDD above about 3 × the average DD
  needs an explanation; it should occur in hostile conditions (chop), an MDD in run-up-like conditions is an alarm. Model efficiency
  = net / Perfect Profit (sum of all swings), 5 %+ very good, stable per year (RP ch.12). One parameter set on 5-10 uncorrelated
  markets × five 2-year segments as a table (RP ch.8, 10).
- **Shocks:** mark shock days (range > 3.5-5 × ATR(10)). If more than half of them were profitable,
  the risk is understated; show P/L with shock days removed or reversed (K p.970-975).
- **Surprisingly small max drawdown** = overfit or tiny sample (K p.941).
- Regimes are only known after the fact; a pattern that works in 3 of 4 regimes may fail in the
  current one (K p.694). Several edges in the books flipped sign over time (RSI(2) around 1998,
  outside-day rule in the mid-1980s, ORB after 2000, fast Turtle breakout after the early 1980s).

## False discoveries: trials, deflation, distribution of paths
Sources: LP ch.7, 11-14, RC ch.3, KD ch.12-14, EC ch.1. Math in [statistics-and-bayes.md](statistics-and-bayes.md).
- **Trial log.** Record every variant, symbol, timeframe and filter ever run, with its return series. Without
  the number of trials FWER, PBO and DSR cannot be computed ("third law of backtesting", LP 14.7.3, 12.5). The best
  of N null trials has a Sharpe of about sqrt(2 ln N); about 20 tries produce one false "significant" strategy at 5 %
  (LP 8.1). Pool of 100 zero-skill rules, 1 year of data, accept at SR 0.5: ~30 accepted (RC Table 3). → T-08
- **Deflated Sharpe.** PSR (short sample, skew, fat tails) and DSR (also the trial count and the spread of trial
  Sharpes) on the non-annualised per-trade or daily R series, pass > 0.95 (LP 14.7.2-14.7.3). Complements our
  "share of profitable variants" (a count) with a probability. → T-08
- **Distribution instead of one path (CPCV).** Split the data into N ordered groups, test on every combination of
  k groups: C(N,k) splits, phi = C(N-1,k-1) full backtest paths, one Sharpe per path (N=6, k=2 gives 15 splits and
  5 paths; for k=2, N = phi + 1). Every training set is purged and embargoed (LP 12.4). More, less correlated paths
  mean less selection bias (LP 12.5). → T-09
- **Disagreement on cross-validation:** Masters distrusts CV for performance estimates (it uses future data, optimistic under
  non-stationarity, wildly different from walk-forward) and keeps it only for structure choices nested inside a walk-forward
  (TM ch.5); López de Prado prefers purged CPCV above. Both reject a single unpurged split.
- **PBO via CSCV** (LP 11.6): matrix of PnL series (T periods x N trial configurations); split time into S blocks
  (S=16 gives 12,780 half-half combinations); pick the in-sample best, take its out-of-sample rank omega, logit =
  ln(omega/(1-omega)); PBO = share of combinations with logit < 0 (the in-sample winner ends below the OOS median).
  Needs every trial's synchronous PnL, so it relies on the trial log. → T-09
  Masters' version: rows must come from grid or random trials, never a guided search (GA, DE); the result is relative to the
  competitor set (absurd candidates flatter it, a too narrow set hurts) and says nothing about risk/reward (TM ch.5).
- **Purging and embargo.** For any split of trades whose outcomes span time: purge training trades whose span
  overlaps a test span, and drop about 1 % of bars after each test block (embargo). No embargo needed before the test
  block; in plain walk-forward only purging. If performance keeps improving as the number of folds grows toward T,
  the split leaks (LP 7.4). Shuffled k-fold gives scores far above the realistic purged ones (LP 7 exercises).
  Purging must be exact: off by one bar still leaks (random walk, lookahead 10: omit 8 → median t 1.88; omit 9 → 31 % "significant"
  at 0.1; omit 9 and skip 9 → 10.1 %, correct) (TM ch.5).
- **Overlapping trades** are not independent: the effective sample is lower than the trade count; count bets, weight
  by uniqueness (LP 4, 14.3). → T-19
- **Whole classes, not one instrument.** An effect that appears in one instrument only is probably false; model asset
  classes and bag/resample: if bagging changes the result sharply the strategy rests on a few outliers (LP 11.5).
  Pool instruments to fit; per-instrument fits need decades to separate (RC ch.3).
- **Synthetic null for exits.** Fit an Ornstein-Uhlenbeck process (phi, sigma, half-life), simulate 100,000 paths and
  read the Sharpe heat map over (profit-take, stop-loss). On a random walk (long half-life) the map is flat: any
  optimum found on history is overfit; compare our best SL/TP grid cell with the best cell on synthetic random walks of
  equal length (LP 13.5-13.6). → T-15
- **Tests that use every bar.** ADF, Hurst, variance ratio and half-life do not depend on entry and exit rules and
  have far more power than a backtest with few round trips; run them before writing rules (EC p.41-48). → T-11
- **Best-of-N has its own null.** The best of N rules is the maximum of N means; judged against a single-rule distribution it looks
  significant, against the max-of-N distribution it does not (50 useless rules, best +37 %: p < 0.05 vs p > 0.45). Aronson's 6,402
  S&P rules (1980-2005): best +10.25 %/yr, White's Reality Check p 0.816; a naive test gave p 0.0005 and about 320 rules looked
  significant (DA p.255-330, 441-475). Five factors set the bias: more rules, fewer observations (maybe the biggest), lower
  correlation between rules, heavier positive tails, similar true merit (DA p.255-330). Observed performance is a fine **selection**
  criterion but a biased **estimate** of the winner.
- **White's Reality Check** (zero-centred daily returns, the same resampled day indices for all variants, distribution of the
  max, >= 500 replications) and the **Monte Carlo permutation best-of-N** (one permutation of the detrended market changes applied
  to every variant's positions, distribution of the max). Both need the full daily series (and positions) of every variant ever
  tested; Romano-Wolf stepwise adds power and joint CIs. Rules borrowed from books count as trials (DA p.255-330, 389-440;
  TM ch.7). → T-08
- **Detrended benchmark** (DA p.15-31): a no-skill rule earns [p(long) - p(short)] × average daily change, so a long bias looks good
  in a bull market. Compute rule returns on market returns minus their mean (signals still use real prices) and report raw and
  detrended; report the long / short time share. S&P 1976-2004: random rule 90 % long 7.31 %/yr, 60 % long 1.78 %/yr.
- **MCPT of the training process** (TM ch.7): re-optimize the whole grid on each permuted IS dataset; p = (k+1)/(m+1), m >= 100,
  p <= 0.05 wanted. An overfit system also looks great on permuted data, so the original does not stand out. Same for the whole
  walk-forward (permute everything after the first training fold, which gets its own permutation). Selection-bias version: p for a
  competitor = share of permutations whose best result >= its original. Return partition: total = Skill + Trend + TrainingBias,
  with TrainingBias read from permuted retrains (Skill 0) and Trend = (n_long - n_short) × mean log change. Permute log-price
  changes (same permutation for all symbols; OHLC bars as two series, gaps and intra-bar moves). Where Davey's matched monkeys test a
  fixed system, this also tests the optimization. → T-14

## The Davey funnel: screening before building
Source: KD ch.5-14, 17-19 (futures, one 4-year example; the gates are the useful part, numbers are his).
- Base rate: 100-200 entry/exit ideas per system worth real money; about 9 of 10 ideas on 1-5 minute bars fail and
  moving to 60 minutes nearly always helps (KD p.73, 88, 244). Write every idea down, test the opposite of bad ideas,
  scrap failures instead of patching them.
- **Goals first**, written before any testing (SMART), so failures are rejected without argument (KD ch.9).
- **Limited test:** 1-2 randomly chosen years (about 25 % of the data, not the crisis years); every look "burns"
  the data. Costs always on (zero-cost reports are invalid); 1 unit per trade; 30-100 trades per rule (KD ch.6, 11-12).
- **Entry only, exit stripped (KD p.105-106):** (a) fixed stop and target of equal size: a no-edge entry wins ~50 % before
  costs; (b) exit after X bars (1-5): a good entry shows profit almost at once, profit only after 10+ bars means the entry
  is early; (c) random exit. Win rate 52-60 % plus positive average trade; sweep a small grid and read **all** cells.
- **70 % gate (KD p.106-109):** >= 70 % of grid cells profitable = pass; 30-70 % = at most 1-2 added rules, else scrap;
  < 30 % = try the reversed signal but pay costs twice (a -$50 system with $30 costs is -$20 gross; reversed it is
  +$20 gross and -$10 net). Matches K's >= 70 % robustness share.
- **Matched monkeys (KD p.109-114):** 8,000 random runs matched on trade count, long / short share and mean bars in
  trade: random entry with the real exit, random exit with the real entry, both random. Pass = beat ~90 % of monkeys on
  net profit **and** max drawdown. The same test live on the last 6-12 months: most percentiles at 60-70 % is a warning,
  below 50 % the edge is gone (example 99-100 % in development, then 49-73 %, then ~1-72 % before a stop). → T-14
- **Walk-forward, Monte Carlo, incubation:** the walk-forward trade list is resampled for one year (2,500 runs):
  ruin < 10 %, median max DD < ~40 % (traders tolerate about half the DD they claim), return/DD > 2, P(profit year)
  reported (KD ch.7, 14); then 3-6 months incubation as another OOS period, compare walk-forward and incubation trades
  by t-test and equity curve (KD ch.14, 19). Red flags in any backtest: fills at exact bar lows/highs, limit orders filled
  on touch, same-bar stop and target, exotic bars (KD ch.14).
  **Disagreement:** Davey resamples the walk-forward trade list; Masters shows a plain resample underestimates catastrophic
  drawdown (by more than 10× on short samples), so use his double bootstrap for DD bounds (TM ch.6;
  [statistics-and-bayes.md](statistics-and-bayes.md)).
- **Live monitoring:** performance cone of cumulative P&L against Monte Carlo percentile bands (10 % line = warning,
  below the 0 percentile = stop), return efficiency and drawdown efficiency on a one-unit basis, quit rule written in
  advance (KD ch.20, 23). → T-17
- Outlier dependence: removing the 20 days above $1,000 (of 614) left his day system barely profitable, so every signal
  must be taken (KD ch.19); compare K's "best trade removed".

## Bayesian and expectation checks
- Beta posterior of the win rate, A/B posterior comparison, Bayes factor and the trade count needed to convince a
  skeptic: [statistics-and-bayes.md](statistics-and-bayes.md) (WK ch.5, 15-17). → T-10
- Pessimism factor: expect 65-75 % of a backtested Sharpe live, never above 1.0 for a diversified book (RC Table 14,
  epilogue); a "too good" result is a bug (EC p.22-24: steady Sharpe 6, high return with Sharpe 0.3 and a 2-year drawdown).
- Time-frame lift: an intraday rule that fails on 1-5 min bars should be rerun on 15m / 60m / 4h / daily before it is
  scrapped, because costs per move and noise fall with larger bars (KD p.88). → T-13

## Costs in tests
- Costs on from the start. Run **three levels**: 0, realistic (spread + commission + swap), stressed
  (+50 %). Show how the profitable parameter range shrinks (K p.949: Nasdaq MA zone shrank from
  ">15 days" to "45-75 days" with costs).
- Nearly all of Kaufman's published numbers are **gross of costs** and on 1990-2011 futures. Treat
  them as hypotheses.

## Checklist for every backtest (use this)
Derived from K ch.21-24 (full version with page refs: `books/kaufman-tsm-ch21-24.md` › Checklist).

**Before running**
1. Premise written down (why the edge exists) plus expected trades, win rate, avg R, hold time, DD.
2. Parameter ranges pre-declared, geometric spacing, ≤ 4 free parameters, success metric fixed
   (net expectancy in R, R per month, max DD in R, Calmar/Ulcer; not net profit alone).
3. Data split fixed: OOS blocks chosen in advance, sibling symbols named as extra OOS.
4. Rules checked by hand on the chart for a sample of trades; no-lookahead tests green.
5. Costs at 0 / realistic / stressed.

**Robustness**
6. Core signal profitable before any stop/filter tuning.
7. Heat map: plateau, not spike; pick the plateau centre.
8. Report the average and st.dev over the whole range; robustness = % profitable combos (target ≥ 70 %).
9. Sensitivity ±10-20 % around the chosen point: gentle degradation.
10. Every filter must lift the average of all combos, not the peak.
11. All symbols of the class and neighbouring timeframes, same parameters.
12. Walk-forward with stable parameters; final hold-out untouched.
13. Year/half table, slope of returns, best trade removed, top 10 wins/losses studied.
14. Shock-day check.
14a. Random-entry baseline: net R percentile against 1,000 seeded random-entry runs with the same
    exits and costs (T-02; [backtest-frameworks.md](backtest-frameworks.md)).
14b. SL and TP in one candle: resolved from M1, not "SL first" (T-03).
14c. Stressed fills: seeded random slippage; the result must survive it (T-07).
15. Enough trades (dozens to hundreds); standard error of expectancy reported.
16. Time in market and swap in R reported separately.

**Risk (R list -> account)**
17. Fixed fraction (0.25-1 % per trade) and volatility-targeted sizing; Monte Carlo with block
    bootstrap plus the real sequence.
18. Plan for 1.5-2 × the historic max DD; FTMO: P(5 % daily or 10 % total breach) below a stated limit.
19. Risk of ruin against the FTMO limits.
20. Kelly / optimal f only as an upper bound.

**Before live**
21. Paper/demo with worst-of-5-minutes fills, same rules, same data source; compare to expectation.
21a. Reconcile demo trades with the engine on the same candles before trusting either (T-06).
22. Live monitoring: binomial test of the loss streak and chi-square of live vs expected win rate
    decide whether a system is "broken" (K p.1092-1097). Retest only after 5-10 % new data.

**False-discovery and gate checks (LP, KD, RC, WK, EC; added 2026-10-16)**
23. Trial log: every variant, symbol, timeframe and filter tried is recorded with its return series; the effective
    number of independent trials N is stated (T-08).
24. PSR(0) and DSR (N trials, variance across trials) both > 0.95 on the non-annualised per-trade / daily net R; a
    selected best-of-N variant is judged by DSR, not by its raw Sharpe.
25. Distribution, not one path: CPCV Sharpe per path (N 8-10, k=2, purged and embargoed) and PBO below 0.5 when one
    variant was selected; the time-reversed run is reported (T-09).
26. Matched monkeys: beats >= 90 % of 8,000 random runs on net R and on max DD for random entry, random exit and both
    (T-14); the same percentiles are tracked on the last 6-12 months once live.
27. Entry-only screen with the exit stripped (fixed-bar exits, equal-R stop and target): net R positive in >= 70 % of the
    grid; 30-70 % allows at most two added filters, < 30 % allows the reversed signal with costs paid twice (T-13).
28. Bayesian report under flat, weak-skeptical and strong-skeptical priors: the verdict must not flip; the required
    trade count for the MT5 test is computed before it is run (T-10).
29. Effective N: trades counted as bets, overlapping trades down-weighted, before any t-statistic is quoted (T-19).
30. Gates and the result that counts as "no edge" are written into `docs/` before the run; a failed idea is scrapped,
    not patched, and its number of looks is added to the trial log (KD ch.8; LP 11.4; WK M10).
31. Expectation haircut: live Sharpe at most 50-75 % of the backtest; a diversified Sharpe above 1.0 or a 5-sigma
    result is treated as a bug (RC, EC p.7, WK ch.12).
32. Live: written quit rule (1.5 x worst walk-forward DD averaged with the 95th-percentile Monte Carlo DD), performance
    cone with Monte Carlo bands, incubation of 3-6 months on MT5 data (KD ch.14, 20, 23; T-17).
33. Walk-forward efficiency (annualized OOS / IS) per run and over the concatenated OOS windows (many windows, step = OOS); about
    25 % = overfit, 50-60 %+ = robust; expected live profit ≈ WFE × latest IS (RP ch.11).
34. Best-of-N significance: White's Reality Check or Monte Carlo permutation max-test over the daily series of every variant in
    the trial log, not a single-rule p-value (DA p.255-330; TM ch.7).
35. MCPT of the training process: re-optimize on >= 100-1,000 permuted datasets, p = (k+1)/(m+1) <= 0.05 (TM ch.7).
36. Detrended benchmark and position bias: raw and detrended returns side by side, share of time long vs short (DA p.15-31; TM ch.7).
37. Drawdown bounds from a double bootstrap (outer: the OOS set, inner: next-N-bar sequences), not a plain resample (TM ch.6).
38. Limit orders fill only on penetration by X ticks, not on a touch; report the share touched but not filled (RP ch.6).

See also: [costs-and-execution.md](costs-and-execution.md), [position-sizing-and-risk.md](position-sizing-and-risk.md),
`.claude/skills/backtest-evaluation-research` (online research on the same question).

## Discretionary books: how to read them
- Volman, Aziz and Coulling give **no statistics at all** (no win rates, samples or costs); every example
  is a hand-picked chart. Treat their rules as hypotheses.
- Their real "edge" sits in judgement filters (chart resistance, squeeze quality, "holds support",
  "high volume"). When coding them: fixed numeric thresholds in a config, pre-declared, and check for
  lookahead (equal highs, "first pullback of a new trend" and the surge origin are easy to define with
  hindsight).
- Good use: A/B tests that isolate one claim (breakeven vs no breakeven, with vs without the tension
  filter, price-only vs tick-volume version), and exit modules on a random-entry baseline to separate
  exit edge from entry edge (Volman notes, idea B).
