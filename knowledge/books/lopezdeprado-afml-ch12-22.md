> Reading notes, own words, made 2026-10-16 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

> Cited as LP, by chapter.section (e.g. LP 14.7.3); the ebook text has no page numbers and formulas were stripped, so formulas are marked standard form.

# Notes: Marcos Lopez de Prado, Advances in Financial Machine Learning (Wiley 2018), part 2 (Ch. 12-22)

Source text: lopez2.txt. The extracted text has NO book page numbers and all formulas are stripped (only prose and snippet titles survive). References below use chapter and section numbers (e.g. "14.7.3"). Formulas given here are from the text's wording plus the standard published forms (Bailey and Lopez de Prado 2012/2014), marked "(standard form)" where the text itself did not show them.

## Overview
- Covers the backtesting half of the book: backtest by cross-validation (CPCV, Ch. 12), backtest on synthetic data to fix profit-take / stop-loss without overfitting (Ch. 13), backtest statistics incl. probabilistic and deflated Sharpe (Ch. 14), "strategy risk" as a binomial precision/payoff problem (Ch. 15), then portfolio allocation with hierarchical risk parity (Ch. 16), structural-break / bubble tests as features (Ch. 17), entropy features (Ch. 18), microstructure features (Ch. 19) and HPC/quantum recipes (Ch. 20-22).
- Author's stance: a single historical backtest (walk-forward) is one path and is very easy to overfit; selection bias from many trials is the main reason most published results are false. The cure is (a) report every trial, (b) deflate the Sharpe ratio for the number of trials, (c) test on many paths/scenarios (CPCV) or on synthetic data, (d) model the strategy as a bet process (precision, payoff, frequency) and ask how fragile its Sharpe is to small precision changes.
- Heavy ML/high-frequency orientation. For our project (price only, no volume, no order book, R-multiples) the valuable parts are Ch. 12-15 and parts of Ch. 16-17. Ch. 18-19 mostly need tick/volume/order-flow data we do not have. Ch. 20-22 are engineering (multiprocessing, quantum, HPC) and irrelevant.

## Chapter notes

### Ch 12 - Backtesting through Cross-Validation (12.1-12.5)
- Walk-forward (WF, 12.2): clear historical interpretation, no leakage if purged, no embargo needed. Three weaknesses: only ONE path (easy to overfit); outcome depends on the particular sequence of data (running it on the reversed series often gives a different answer, which is itself evidence of overfitting); early decisions use little data (a warm-up period cuts the sample).
- Plain CV backtest (12.3): train on everything except the test period; every observation is tested exactly once, equal-size training sets, no warm-up. Not "historically accurate", but answers how the strategy copes with a scenario it never saw (e.g. 2008). Needs purging + embargo to avoid leakage because training data is not all before test data.
- CPCV (12.4): split T observations into N ordered groups (no shuffle); test sets are all combinations of k groups; number of splits = C(N,k); each group appears in C(N-1,k-1) test sets; number of distinct full backtest paths phi = C(N,k)*k/N = C(N-1,k-1). Example N=6, k=2: 15 splits, 5 paths, training share 1-k/N = 2/3. For k=2: paths = N-1; rule of thumb: to get phi paths set N = phi+1 with k=2. Each training set is purged (drop training labels whose span overlaps a test label) and embargoed. Result: one Sharpe per path, so you get a DISTRIBUTION of Sharpe ratios, not one number.
- Why CPCV fights overfitting (12.5): expected maximum of I IID standard-normal Sharpe estimates grows like sqrt(2 ln I) even when the true SR is 0 (formula uses Euler-Mascheroni constant 0.5772: E[max] ~ (1-g)*Z^-1[1-1/I] + g*Z^-1[1-1/(I*e)]). A WF backtest has high variance, so picking the max across trials produces false discoveries. CPCV averages many paths: variance of the mean is sigma^2/phi * (1+(phi-1)*rho_bar) where rho_bar = average correlation between paths, so more (and less correlated) paths = less selection bias. Author says reviewers could demand CPCV with N, k they choose, which defeats trial-targeted overfitting.
- Necessity stressed: without the NUMBER OF TRIALS you cannot compute FWER, FDR, PBO or DSR.
- Exercise worth noting: 100,000 forecasts and 1,000 paths -> pick (N,k) so C(N-1,k-1) = 1000.

### Ch 13 - Backtesting on Synthetic Data (13.1-13.7)  [relevant to our R-based SL/TP]
- Premise: exit rules (profit-take pi+, stop-loss pi-, plus a max holding period = vertical barrier) are free parameters; calibrating them on one historical path overfits. Alternative: estimate the stochastic process behind the P&L from history, simulate 100,000 paths, and pick the (pt, sl) pair on the simulated Sharpe heat map, with no historical simulation of the trading rule.
- Model (13.4): discrete Ornstein-Uhlenbeck on P&L/price: P_t = (1-phi)*E0[P_T] + phi*P_{t-1} + sigma*eps, eps ~ N(0,1), phi in (-1,1) for stationarity; E0[P_T] = "forecast" (long-run equilibrium), half-life tau = -ln2/ln(phi) so phi = 2^(-1/tau).
- Algorithm (13.5.1): (1) estimate phi, sigma by OLS of P_t - E[P_T] on P_{t-1} - E[P_T] (linearised OU); (2) build a mesh of (pt, sl) pairs, e.g. 20x20 multiples of sigma (e.g. 0.5..10); (3) simulate e.g. 100,000 paths from observed seed values, each ending at first of: profit-take, stop-loss, or max holding period (100 bars); (4) for each node compute the Sharpe of the exit P&L across paths; (5a) pick best node; (5b) if the strategy gives a profit target, read off the optimal stop; (5c) if a max stop is imposed, read off the best profit-take within it. Snippets 13.1/13.2 do exactly this (the code loops over grid nodes, simulates, stores first-barrier exit, computes Sharpe).
- Results (13.6; non-annualised Sharpe heat maps, costs excluded): 
  - Zero long-run equilibrium (market-maker-like, forecast 0): best region is SMALL profit-take with LARGE stop (take small gains, tolerate 5-7x loss); Sharpe up to about 3.2 at half-life 5; worst is the opposite (short stop, big target). Diagonal (symmetric pt = sl) is near neutral. Matches the "asymmetric payoff dilemma".
  - Positive equilibrium (forecast > 0, position-taker): optimum rectangle, pt about 5-6, sl 4-10; Sharpe about 12 at half-life 5, falls to 9 (hl 10), 2.7 (hl 25), 0.8 (hl 50), 0.32 (hl 100).
  - Negative equilibrium: mirror image (best region becomes worst, Sharpe about -12 to -9).
  - As half-life grows, process approaches a random walk: heat map flattens, "no recognisable area of optimum", so any optimised pt/sl on a random walk is pure overfit. Synthetic procedure correctly tells you there is no optimal rule.
- Conjecture stated (not proven): for OU prices there is a unique optimal (pt, sl) combination. Author argues it is rational to trust the synthetic result over an in-sample optimised one.
- Practical read for us: with a random-walk-like instrument, no (SL, TP) choice adds edge; any apparent edge in an SL/TP grid is noise. Edge must come from the signal (forecast/half-life), and the exit just shapes the payoff distribution.

### Ch 14 - Backtest Statistics (14.1-14.9)
- Report classes: general characteristics, performance, runs/drawdowns, implementation shortfall, efficiency, classification scores, attribution.
- General (14.3): time range must contain many regimes; capacity; leverage; max position size (prefer max close to average = no reliance on outliers); ratio of longs (about 0.5 for neutral strategies); frequency of bets (a bet = consecutive same-side positions until flat or flip; bets < trades, count bets as the independent opportunities); average holding period; turnover; correlation to underlying (high = just holding the market). Snippets 14.1/14.2 derive bet timestamps and the average holding period from a target-position series.
- Performance (14.4): P&L, P&L long/short split, time-weighted rate of return, hit ratio, average win, average loss.
- Runs (14.5): returns are not IID so runs of same-sign returns raise downside risk. Concentration of returns via a Herfindahl-type index: h+ for positive returns, h- for negative, h[t] for bets per month (0 = uniform, 1 = one return dominates). Want low h+ (no right fat tail), low h-, low time concentration, plus high Sharpe, many bets, high hit ratio. Drawdown (between high-water marks) and time under water (TuW); use the 95th percentile of DD and of TuW as stats (Snippets 14.3, 14.4).
- Implementation shortfall (14.6): broker fees per turnover, slippage per turnover, dollar performance per turnover (how much costlier execution can get before break-even), return on execution costs (should be a large multiple).
- Sharpe ratio (14.7): SR = mu/sigma on excess returns; annualise by sqrt(a), a = returns per year (valid only for IID).
- Probabilistic Sharpe ratio, PSR (14.7.2), standard form: PSR(SR*) = Z[ (SR_hat - SR*) * sqrt(T-1) / sqrt(1 - g3*SR_hat + ((g4-1)/4)*SR_hat^2) ]. Inputs: SR_hat = observed Sharpe in the ORIGINAL sampling frequency (NOT annualised), T = number of returns, g3 = skewness, g4 = kurtosis (Gaussian = 3), SR* = benchmark Sharpe (default 0), Z = standard normal CDF. Rises with SR_hat, T, positive skew; falls with fat tails. Rule: PSR > 0.95 for 5% significance. Works on any series of per-period (or per-trade) returns.
- Deflated Sharpe ratio, DSR (14.7.3): DSR = PSR with SR* replaced by the expected maximum Sharpe from N independent trials under the null of zero skill: SR* = sqrt(V[SR_n]) * [ (1-g)*Z^-1[1 - 1/N] + g*Z^-1[1 - 1/(N*e)] ], g = 0.5772 (Euler-Mascheroni), e = Euler's number, V[SR_n] = variance of the Sharpe estimates ACROSS the trials, N = number of INDEPENDENT trials. Inputs needed: SR_hat of the selected strategy, T, skew, kurtosis, N, V[SR_n] (all non-annualised, same frequency). SR* grows quickly with N and with the dispersion of trial Sharpes. Then DSR = PSR(SR*) and must exceed 0.95. Exercise (14.x): 100 trials, V = 0.5. Practical notes: N must be effective (independent) trials, so correlated variants (our parameter grids) count as fewer; estimate effective N by clustering trial return series, or be conservative and use the raw count.
- "Third law of backtesting" (Snippet 14.5): every result must be reported with ALL trials used to produce it; otherwise false-discovery probability cannot be assessed.
- Efficiency stats list: annualised SR, information ratio, PSR, DSR.
- Classification scores for meta-labelling (14.8): accuracy, precision, recall, F1 (harmonic mean), negative log-loss; accuracy misleads when classes are imbalanced; F1 undefined in degenerate cases (all-0 predictions etc.).
- Attribution (14.9): decompose P&L by risk class with disjoint categories; Sharpe per class. Mostly for portfolios of bonds/equities.

### Ch 15 - Understanding Strategy Risk (15.1-15.4)  [relevant to FTMO]
- Idea: nearly every strategy has two exits (profit-take, stop-loss), so model each bet as binomial: win +pi+ with prob p ("precision"), lose pi- with prob 1-p. "Strategy risk" = risk the strategy fails to reach its target Sharpe, distinct from portfolio risk.
- Symmetric payout (15.2, +/- pi): annualised SR = (2p-1)/(2*sqrt(p(1-p))) * sqrt(n), n = bets per year; pi cancels. SR is a re-scaled t-value, so many bets with p barely above 0.5 give a high Sharpe (the HFT economics). Example: p=0.55 needs n about 396 bets/year for SR 2. Solving for p: weekly bets (n=52) need p = 0.6336 for SR 2. Sharpe depends on PRECISION, not accuracy (passes are not scored).
- Asymmetric payout (15.3): E[X] = (pi+ - pi-)*p + pi-, V[X] = (pi+ - pi-)^2 * p(1-p); annualised SR = sqrt(n) * ((pi+ - pi-)p + pi-) / ((pi+ - pi-)*sqrt(p(1-p))). Example n=260, pi- = -0.01, pi+ = +0.005, p=0.7 gives SR 1.173; to reach SR 2 needs p = 0.72. Implied precision p* for a target SR* is the root of a quadratic a*p^2 + b*p + c = 0 with a=(n+SR*^2)(pi+-pi-)^2, b=[2n*pi- - SR*^2(pi+-pi-)](pi+-pi-), c=n*pi-^2 (take the root in [0,1]); Snippet 15.3. Snippet 15.4 solves for the implied bet frequency n instead. Higher |pi-| or lower n requires higher precision.
- Probability of strategy failure (15.4): p is unknown/market-determined, so treat it as random. Compute the threshold p_thres where SR = SR* (target). Strategy risk = P[p < p_thres]. Algorithm (15.4.1): from the bet-outcome series estimate pi+ (mean of positive outcomes), pi- (mean of negative), n = bets per year; bootstrap precision: repeat I times, draw n*k outcomes with replacement (k = years investors judge the strategy, e.g. 2), compute fraction positive; fit a KDE on the p's (or normal approximation for large k); strategy risk = integral of the density below p_thres (Snippet 15.5). Author says discard strategies whose risk exceeds the tolerance (e.g. >5%) even if the underlying is low vol; fix by improving pi+, pi-, n or p. Similar in spirit to PSR but lets you vary the parameters under the manager's control.
- Key warning: a tiny drop in p (0.70 to 0.67 in the example) wipes out profit; high-frequency / high-n strategies are intrinsically fragile to small precision changes.

### Ch 16 - Machine Learning Asset Allocation, Hierarchical Risk Parity (16.1-16.8)
- Problem: mean-variance optimisation (Markowitz's critical line algorithm) is unstable (inverts the covariance matrix; condition number explodes with correlated assets - "Markowitz's curse"), concentrates, and underperforms equal weight out of sample. Need N(N+1)/2 IID observations at minimum to estimate a non-singular N x N covariance.
- HRP in three stages: (1) tree clustering: correlation -> distance d = sqrt((1-rho)/2), then Euclidean distance of distance columns, single linkage via scipy; (2) quasi-diagonalisation: reorder the covariance matrix by the dendrogram leaf order so similar assets sit together; (3) recursive bisection: split the ordered list in two, compute each half's variance using inverse-variance weights inside the half, allocate to the two halves in inverse proportion to those variances, recurse down to single assets. No matrix inversion, works on a singular matrix, weights between 0 and 1 summing to 1, long-only as presented.
- Monte Carlo (16.6; 10 assets, 520 days, rebalance every 22 days, 260-day lookback, 10,000 runs, with common/specific shocks): out-of-sample variance CLA 0.1157, IVP 0.0928, HRP 0.0671; HRP has about 72% lower variance than the min-variance optimiser and 38% lower than inverse-variance. Claims also supported by JP Morgan and Raffinot studies. HRP weights are a compromise between CLA concentration and IVP ignoring correlation.
- Uses: allocation across algorithmic strategies / capital allocation to managers / combining ML signals. Exercise 1: align strategy P&Ls to their bet frequency, cluster, compute HRP.
- Relevant to us: when combining several weak edges, equal weight or inverse-variance with correlation-aware clustering (HRP) is a robust choice versus estimating a full optimiser from short noisy samples.

### Ch 17 - Structural Breaks (17.1-17.4)  [regime filters]
- Idea: breaks (mean-reversion giving way to momentum, bubble starts) are where participants make costly mistakes; build features from break tests.
- Two families: CUSUM tests (do cumulative forecast errors depart from white noise) and explosiveness tests (exponential growth/collapse: right-tail unit root tests like SADF; sub/super-martingale tests).
- Brown-Durbin-Evans CUSUM (17.3.1): recursive least-squares residuals standardised; the cumulative sum S_t is N(0, t-k-1) under the null that beta is constant. Caveat: depends on the arbitrary starting point.
- Chu-Stinchcombe-White CUSUM on levels (17.3.2): drops regressors, assumes the expected change is zero, so statistic S_{n,t} = (y_t - y_n) / (sigma_hat * sqrt(t-n)) on log prices (standard form); critical value grows with time: c_alpha[n,t] = sqrt(b_alpha + ln(t-n)) with b_0.05 = 4.6 (Monte Carlo). One-sided test. The reference level y_n is arbitrary, so compute it for a set of backward-shifting windows n in [1,t] and take the supremum. Cheap and usable as a regime/trend-break filter on the incremental feed (uses only data up to t).
- Chow-type Dickey-Fuller (17.4.1): tests for a switch from random walk to explosive at an unknown break date tau*; Andrews' trick: try all tau* in a trimmed interval [tau0, 1-tau0] and take the max statistic. Drawbacks: single break, bubble must run to the end of the sample.
- SADF, supremum augmented Dickey-Fuller (17.4.2): for each end point t, run an ADF regression (delta y = alpha + beta*y_{t-1} + lagged deltas, optional time trend) from every start t0 in [1, t - tau] (tau = minimum window), take the supremum of the ADF t-stat: SADF_t = max over t0 of ADF_{t0,t}. Detects multiple bubble/burst cycles; spikes when prices are bubble-like and falls after bursts. Parameters in Snippet 17.1: minSL (minimum sample length), constant ('nc', 'ct', 'ctt'), lags. Use LOG prices (levels then affect return mean, not volatility, so regressions across very different price levels stay valid). Cost O(T^2) ADF fits (E-mini dollar bars: 356,631 bars -> about 242 PFLOPs for the full series; needs parallelisation, so on our data use a coarser timeframe, bounded window or subsampling).
- Variants: Quantile ADF (central value Q and dispersion of the top ADF values, e.g. q=0.95, v=0.025) and Conditional ADF (mean of ADF stats above the q quantile) are more robust than the raw max (which is outlier-sensitive and depends on sampling).
- Conditions (17.4.2.3): coefficient on lagged log price below 0 = steady state (mean-reverting, half-life), exactly 0 = unit root (martingale), above 0 = explosive.
- Sub/super-martingale tests (17.4.3): fit polynomial (Poly1, Poly2), exponential or power trend on log price over backward-expanding windows, take the maximum absolute t-value (growth and collapse); a penalty exponent phi in [0,1] on window length (t/(T-t0)^phi) tunes the preferred holding period (phi near 0: long trends; near 1: noisier short bubbles).
- Reciprocal prices turn bubbles into bursts (exercise 5); the abs/two-sided versions detect both.

### Ch 18 - Entropy Features (18.1-18.8)
- Concept: entropy of an encoded price/return sequence measures information content or compressibility. Low entropy = redundant, patterned, "compressed" (inefficient) market; high entropy = unpredictable, "decompressed" efficient market. Claims bubbles form in low-entropy markets and the author suggests momentum may work when entropy is low and mean-reversion when high (as an ML feature, not tested in the text).
- Estimators: plug-in (maximum likelihood, word length w, needs n much larger than w); Lempel-Ziv complexity; Kontoyiannis/Gao match-length estimator (average of longest-match lengths L within a window, entropy about log2(n) / average L; window n chosen with n about N - (log2 n)^2, e.g. N=256 -> window about 198). Caveats: asymptotic only, short messages can be repeated, symmetric window ignores final bits (analyse the reversed message if the end matters).
- Encodings (18.5): binary (sign of return), quantile (equal counts per letter, boundaries from the training period), sigma (fixed-step bins of the return range). Binary suits fixed-size price bars; discards information when |r| varies. Need at least about 10 letters on messages of length 100 for an unbiased estimate of Gaussian entropy (about 1.42 for a standard normal); fewer letters underestimate.
- Generalised mean view: entropy = log of the effective number of items; Meucci's entropy-based portfolio concentration uses principal-component risk shares.
- Microstructure entropy (18.8.4): quantise the buy-volume fraction of volume bars, estimate entropy, take its CDF as a predictor of adverse selection. Needs signed volume (we lack it).
- Practical for us: entropy of binary/sigma-encoded M5-D1 returns in rolling windows is computable from price alone; unproven as a filter. Treat as an idea to test with DSR, not an accepted effect.

### Ch 19 - Microstructural Features (19.1-19.7)
- Three generations: price-sequence models (tick rule, Roll, high-low vol, Corwin-Schultz), strategic-trade models (Kyle, Amihud, Hasbrouck lambdas = price impact per unit signed volume), sequential-trade models (PIN, VPIN). Plus extra features: round-size trade frequency, cancellation rates, TWAP footprints, option-implied information, serial correlation of signed order flow. Author notes t-values of the regressions are more informative than the coefficients.
- Useful with OHLC only: 
  - Parkinson high-low volatility: sigma_HL^2 = (1/(4 ln 2)) * mean[(ln(H/L))^2] (k1 = 4 ln 2), more efficient than close-to-close; usable on any bar.
  - Corwin-Schultz spread estimate from two-bar high-low ranges: alpha built from beta (sum of squared 1-bar log ranges) and gamma (squared 2-bar log range); spread S = 2(e^alpha - 1)/(1 + e^alpha), negative alpha set to 0. Estimates effective spread from OHLC, potentially a cross-check of our spread table (not needed where MT5 spreads exist).
  - Roll model: effective spread c from serial covariance of price changes: spread = 2*sqrt(-cov(dp_t, dp_{t-1})) when cov is negative.
- Not usable (needs trade/volume/book data): tick rule, Kyle/Hasbrouck/Amihud lambda (Amihud needs dollar volume), PIN/VPIN, order sizes, cancellations.
- 19.7: defines microstructural information as the model's cross-entropy loss CDF; flash-crash story. Skip.

### Ch 20-22 - HPC (multiprocessing and vectorisation, brute force and quantum computers, CIFT/HPC use cases) - skimmed
- Ch 20: vectorise first, then multiprocess; split work into atoms/molecules; linear partitions vs nested-loop (triangular) partitions for balanced load; mpPandasObj engine with single-thread debug mode and on-the-fly output reduction. Hint for our sweeps: one job per parameter combination, balance heavy and light jobs, keep a single-process debug path.
- Ch 21: dynamic portfolio optimisation with transaction costs reformulated as integer optimisation for quantum annealers (pigeonhole partitions); no practical use here.
- Ch 22: Berkeley Lab CIFT project, flash-crash response, VPIN on HPC, supernova/plasma use cases; no relevance.

## Topic tags

### trend
- SADF / CUSUM / sub-super-martingale t-values are explicitly trend/bubble (explosiveness) detectors; phi parameter selects trend horizon (17.4.3).
- Author suggests momentum bets may work better in low-entropy (patterned) regimes (18.1, untested).

### mean-reversion
- Synthetic OU study: mean-reversion P&L with zero equilibrium is best exploited with small profit-take and wide stop; Sharpe decays quickly with half-life (13.6).
- SADF "steady state" branch = mean-reverting regime with a half-life (17.4.2.3).

### volatility
- Parkinson high-low volatility estimator is better than close-to-close (19.3.3). Daily volatility (EWM) as the unit for barrier distances is in Ch. 3 (not in this part).

### stops-and-exits
- Optimal profit-take/stop-loss depends on the process: wide stop + small target for mean-reverting, near-zero edge on random walk; any optimum on random walk is overfit (Ch. 13).
- Every strategy has implicit stop (margin / pain); model it explicitly as a binomial (Ch. 15).
- Barriers + vertical barrier (max holding period) = triple barrier.

### position-sizing/risk
- Strategy risk: probability that precision falls below the break-even-for-target precision (Ch. 15). Sharpe is very sensitive to p when n is large.
- Drawdown and time-under-water percentiles (95th) as run statistics (14.5.2).
- HRP for combining strategies (Ch. 16).

### testing-and-robustness/overfitting
- Expected max Sharpe of N null trials grows about sqrt(2 ln N); DSR corrects for it (12.5, 14.7.3).
- PSR corrects for short samples, skew, kurtosis (14.7.2). Both should exceed 0.95.
- CPCV: report distribution of Sharpe over many paths (12.4). Backtest is not research; walk-forward alone is one path (12.2).
- Report all trials (14.7.3, "third law").
- Count bets not trades (14.3).
- Use log prices in break tests (17.4.2.1).

### costs/execution
- Implementation-shortfall stats: dollar performance per turnover, return on execution costs (14.6).
- Roll / Corwin-Schultz spread estimators from price (19.3).

### portfolio/diversification
- HRP (16.4); variance of the average of correlated paths/strategies = sigma^2/N*(1+(N-1)rho) (12.5); Markowitz's curse; equal weight beats unstable optimisers out of sample (16.3).

### seasonality/time, patterns, breakout, momentum/oscillators, intraday/sessions, psychology/discipline
- Little content. Intraday TWAP footprints at the first seconds of each minute and hourly open times (19.6.3) are volume-based and not testable here.

## Testable ideas

1. ★ **Deflated Sharpe / PSR gate for every strategy and sweep** - compute on per-trade or daily R series: PSR(SR*=0) = Z[(SR_hat*sqrt(T-1))/sqrt(1 - skew*SR_hat + ((kurt-1)/4)*SR_hat^2)]; DSR with SR* = sqrt(V_trials)*((1-0.5772)*Z^-1(1-1/N) + 0.5772*Z^-1(1-1/(N*e))), N = number of independent configurations tried (cluster correlated variants), V_trials = variance of the non-annualised Sharpe across the trials. Pass if DSR > 0.95. Source: Ch. 14.7.2-14.7.3. Claimed evidence: theory plus the popular published paper. Fit: very good (needs only the R list and trial log); fixes the "24 variants all negative / best of many looks good" problem. Differs from the failed strategies: it is a decision tool, not a strategy; the existing robustness report (halves, share profitable) is complementary.

2. ★ **Strategy-risk / FTMO feasibility from (p, payoff R, n)** - from the trade list estimate pi+ (mean win in R), pi- (mean loss in R), n (trades per year); compute precision needed for a target Sharpe and the bootstrap probability that precision over a k-year window drops below that threshold (draw n*k trades with replacement, KDE or direct count). Map to FTMO: use R-based bet outcomes, also the break-even precision p_BE = |pi-|/(pi+ + |pi-|) (1R stop, 2R target: 33%) plus costs. Source: Ch. 15. Claimed evidence: analytical examples only. Fit: excellent (R based, no extra data); gives a clean "how fragile is the hit rate" number; pairs with FTMO Monte Carlo already built. Different: evaluation tool.

3. ★ **CPCV distribution for parameterised strategies** - N groups (e.g. N=8 or 10 time blocks), k=2, all C(N,k) splits; choose the parameter set on the training groups, evaluate on the held-out groups, stitch into phi = C(N-1,k-1) paths, one Sharpe per path; also compute PBO from the in-sample vs out-of-sample ranks. Purge/embargo by dropping trades that overlap the test block boundaries (trades last minutes to days; embargo about 1-2% of the sample). Source: Ch. 12.4. Evidence: theory only. Fit: good - sample is 2018/2020-2026 intraday, many trades; extends the existing walk-forward and halves tests; respects the 2021-09-14 split if the final holdout is excluded from the groups. Differs: a test method, not a strategy.

4. ★ **Synthetic-data exit calibration (OU/random-walk null)** - fit phi and sigma of the instrument or of the signal's P&L (OLS of deviation on lagged deviation), simulate 100,000 paths with maxHP, and build the Sharpe heat map over (TP, SL) in R or sigma multiples; use it (a) to see whether the optimum is a flat plateau (random walk: no edge in exits) and (b) as a null distribution against which the historical SL/TP grid result is compared (is our best grid cell better than the best cell on synthetic random walks of equal length?). Source: Ch. 13.5. Evidence: simulations in the chapter. Fit: very good for our SL/TP sweeps and consistent with the existing random-price-path Monte Carlo. Differs: examines exits independent of any pattern.

5. **CUSUM / SADF as a regime filter** - compute on log closes of H1 or D1 (or M15 with window cap): Chu-Stinchcombe-White S_{n,t} = (ln P_t - ln P_n)/(sigma*sqrt(t-n)) max over backward windows, flag when above sqrt(4.6 + ln(t-n)); or SADF with minSL about 100 bars, constant 'ct', lags 1-5, log prices. Use the flag (explosive up/down) to switch momentum on, or to switch off mean-reversion strategies; evaluate with DSR. Source: Ch. 17. Evidence: chart on E-mini only; no performance numbers. Fit: OK (only prices; SADF is O(T^2) so cap window or compute on daily/hourly only; swap if holding overnight). Differs from the failed trend strategy by trading only after a statistically significant break rather than any N-day breakout; high risk of being just another trend filter.

6. **Entropy regime feature** - rolling encoded returns (binary or sigma-encoded, quantile with training-period boundaries), plug-in or Kontoyiannis entropy over a 100-250 bar window; test whether low-entropy windows have positive serial correlation / better trend-follow results and high-entropy windows revert. Source: Ch. 18.5, 18.8.1. Evidence: none quantitative. Fit: OK, price only; cheap. Differs: a conditioning variable. Weak prior, test with DSR.

7. **Parkinson high-low volatility and Corwin-Schultz spread as filters** - use sigma_HL to scale stops/targets or to size (vol target), and CS spread as an extra cost filter. Source: Ch. 19.3.3-19.3.4. Fit: good (we have OHLC); small expected effect; useful mainly as a better volatility denominator than close-to-close.

8. **HRP allocation across several weak edges** - cluster the R/day P&L series of the strategies (distance sqrt((1-rho)/2)), quasi-diagonalise, recursive bisection with inverse-variance. Compare with equal weight and inverse variance on a pseudo out-of-sample basis (re-estimate each 22 days from a 260-day lookback). Source: Ch. 16. Evidence: MC variance 0.0671 vs 0.0928 vs 0.1157. Fit: good for the "combine weak edges" focus once there are at least 3-4 strategies; with 2-3 strategies equal weight or inverse variance is nearly the same.

## Warnings / pitfalls
- A single backtest path (walk-forward) hides selection bias; the maximum over N trials is inflated even if all true Sharpes are zero. Without logging N and the dispersion of trial Sharpes, nothing can be claimed.
- Count independent trials, not parameter combinations: correlated variants overstate N (too harsh) while untracked manual iterations understate it (too lax). Include every look: variants, symbols, timeframes, filters.
- Annualised Sharpe in PSR/DSR formulas is wrong: use the per-period (non-annualised) value with matching T, skew, kurtosis; annualising by sqrt(a) assumes IID returns.
- Short samples, negative skew and fat tails inflate Sharpe (PSR corrects); strategies with small wins and rare large losses look better than they are.
- Time-reversal consistency: if a strategy only works forward in time and fails on reversed data, suspect overfitting rather than "historical accuracy" (12.2.1).
- Leakage: purge training trades whose label span overlaps the test period; embargo after the test block; in WF only purge, no embargo (12.2, 12.4).
- Hit-rate fragility: with large n, a few points of precision decide profit (Ch. 15); high-frequency style systems have strategy risk even when portfolio vol is low.
- Optimising profit-take/stop-loss on a random-walk-like instrument just picks noise; flat heat map = no optimum (Ch. 13). Asymmetric payoff trap: small target with a wide stop gives a high hit rate and a high Sharpe until the tail loss arrives.
- Structural-break tests: raw price ADF is invalid across long samples (use logs); SADF max is outlier-driven (use quantile / conditional versions); CUSUM tests depend on the arbitrary reference point; all are expensive (O(T^2)).
- Entropy estimators are asymptotic; small alphabets underestimate entropy; short windows are noisy.
- Mean-variance optimisers are unstable; with few, noisy strategy return series prefer simple (equal weight / inverse variance / HRP).
- Most of Ch. 18-19 relies on tick, volume and order-flow data; our histdata has none (volume column zero). Not testable.
