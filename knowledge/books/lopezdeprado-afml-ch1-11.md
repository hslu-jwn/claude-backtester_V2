> Reading notes, own words, made 2026-10-16 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

> Cited as LP, by chapter.section (e.g. LP 3.6); the ebook text has no page numbers.

# Lopez de Prado - Advances in Financial Machine Learning (Wiley 2018), chapters 1-11

Note: the text file has no printed page numbers (ebook extraction). References below are chapter and section numbers (e.g. "3.6"), which are stable. Roughly: Ch1 ~pp.1-18, Ch2 ~19-44, Ch3 ~43-56, Ch4 ~59-76, Ch5 ~75-92, Ch6 ~93-100, Ch7 ~103-111, Ch8 ~113-129, Ch9 ~129-136, Ch10 ~141-149, Ch11 ~151-158 (approximate).

## Overview
- The book is a manual for applying ML to finance. Chapters 1-11 cover data structuring (bars, event sampling), labelling (triple barrier, meta-labelling), non-IID sample weights, fractional differentiation, ensembles, purged cross-validation, feature importance, hyper-parameter tuning, bet sizing, and a warning chapter on backtesting.
- The central message: finance has low signal-to-noise, short samples and overlapping outcomes, so standard ML tooling (k-fold CV, fixed-horizon labels, accuracy scoring) produces false discoveries. Almost everything in the book is a defence against overfitting and information leakage.
- Stance of the author: skeptical of backtests ("a backtest is not an experiment and proves nothing"), strongly in favour of ex-ante research tools (feature importance), industrial team process, and honest accounting of how many trials were run.
- Much of the book needs ML (random forests, bagging). For us the transferable parts are: meta-labelling as a filter on a rule-based signal, triple-barrier outcome definition, event sampling (CUSUM), purging/embargo for any train/test split of overlapping trades, uniqueness weighting of overlapping trades, bet sizing from a probability, and the backtest-overfitting rules (Ch 11).
- Chapters 12-16 (CPCV, synthetic backtests, deflated Sharpe, PBO details) are NOT in this part, but Ch 11 introduces PBO via CSCV.

## Chapter notes

### Ch 1 - Financial ML as a Distinct Subject
- 1.2: the main reason projects fail is the "Sisyphus paradigm": every quant alone builds a whole strategy and settles for either an overfit false positive or crowded factor investing. Fix is the "meta-strategy paradigm": a research factory with specialised stations (data, features, strategy, backtesting, deployment, oversight).
- 1.3.1.3: a strategy must have a theory naming the economic mechanism that makes another agent lose money to us (behavioural bias, asymmetric information, regulatory constraint). Gluing features together is not a theory. "Features may be found by black box but the strategy is developed in white box."
- 1.3.1.4: backtesters must account for the number of trials that led to the strategy; backtest results are NOT fed back to researchers (otherwise they overfit to them).
- 1.3.1.6: strategy life cycle: embargo (data after backtest end) -> paper trading -> graduation with small size -> allocation grows if it performs, decays as edge fades -> decommission. Allocation as a concave function of live evidence.
- 1.3.2.6: overfitting called unethical; "always ask in what way you may be overfitting". Table 1.2 lists pitfalls: research through backtesting, chronological sampling, integer differentiation, fixed-horizon labelling, learning side and size together, non-IID weighting, CV leakage, walk-forward overfitting, backtest overfitting.
- 1.6 FAQ: backtest overfitting is "the most important open problem in mathematical finance"; chance of a false positive rises with every new test on the same data.

### Ch 2 - Financial Data Structures
- 2.2: four data types (fundamental, market, analytics, alternative). Fundamental data must be aligned to its real release date (backfilled and revised values are a common source of fake results).
- 2.3.1: time bars are poor (oversample quiet periods, undersample busy ones; returns are serial-correlated, heteroscedastic, non-normal). Tick, volume and dollar bars sample by activity and give returns closer to IID normal (Mandelbrot/Taylor, Clark, Ane/Geman). Dollar bars are the most stable over years because bar count depends less on price level and share changes.
- 2.3.2: information-driven bars (tick/volume/dollar imbalance bars, runs bars) sample when signed order flow becomes more imbalanced than expected; they need tick-rule signed volume (we do not have it).
- 2.4: "ETF trick" turns a basket/spread/rolled future into a single non-expiring total-return series; roll gaps can be subtracted from prices (forward or backward roll) but rolled prices can go negative, so compute returns on rolled prices over raw prices. Relevant only if we ever use futures; our CFD data has none of this except index CFD rolls inside the broker feed.
- 2.5.2.1 CUSUM filter: event-based sampling. Keep two running sums of up and down deviations (reset to zero when they cross zero), emit an event only when one exceeds a threshold h, then reset. Unlike Bollinger-band touches it does not fire repeatedly while price hovers near a level; a whole run of size h is needed. Used to choose which bars become training samples. Exercise suggests h = daily vol.
- Point: ML works best when trained on relevant "event" bars, not on every bar.

### Ch 3 - Labeling
- 3.2: the usual fixed-horizon label (sign of return over h bars versus a fixed threshold) is bad: fixed threshold ignores volatility changes (most labels end up 0 in quiet periods), and ignores the path, i.e. the stop-loss that would have closed the trade.
- 3.3: use dynamic thresholds from an exponentially weighted std of returns (Snippet 3.1, daily vol from intraday bars with a span of e.g. 100 days).
- 3.4 Triple-barrier method: for each event set an upper barrier (profit-take), a lower barrier (stop-loss), both as multiples of the current volatility estimate, and a vertical barrier (max holding bars). Label is the first barrier touched: +1 upper, -1 lower, vertical -> sign of the return (author's preference) or 0. Path-dependent; the barriers need not be symmetric. Eight on/off combinations; sensible ones are [pt,sl,t1] = [1,1,1], [0,1,1] (exit after N bars unless stopped), [1,1,0].
- 3.5: if we do not know the side, barriers must be symmetric so the label does not depend on side.
- 3.6 Meta-labeling: when a primary model already gives the SIDE (long/short), build a secondary binary model that learns whether to TAKE the bet (1) or pass (0). Labels: 1 if the trade following the primary signal ended in profit by the barrier logic, else 0. Barriers can now be asymmetric (pt vs sl) since side is known.
- 3.7 How to use: tune the primary to high recall (catch most true opportunities, accept low precision), then let the meta-model raise precision by filtering false positives; this raises F1. Four stated benefits: (1) turns a white-box rule/fundamental model into an ML overlay, (2) limits overfitting since ML does not choose side, (3) lets you separate long and short logic, (4) allows sizing (predicted probability -> bet size). Author's claim: meta-labelled systems are "more robust and reliable" than standard labelling (no numeric evidence given).
- 3.8 "Quantamental": any primary signal, even a discretionary human call or a technical rule, can be wrapped; features for the meta-model can include market state (e.g. structural breaks, volatility, serial correlation).
- 3.9: drop labels that are extremely rare; the "neutral" 0 class is unnecessary because low confidence implies neutral.
- Exercises 3.4/3.5 explicitly propose meta-labelling a moving-average-cross trend strategy (ptSl = [1,2], vertical barrier 1 day, random forest with features volatility, serial correlation, MA crosses) and a Bollinger mean-reversion strategy (ptSl=[0,2]); compare accuracy/precision/recall/F1 of primary alone versus filtered.

### Ch 4 - Sample Weights
- 4.2: when each label spans a window of bars and windows overlap (the next event starts before the previous outcome is known), labels are not IID. The effect is like spilled blood samples between tubes: observations share returns.
- 4.3-4.4: count concurrent labels per bar; a label's uniqueness at a bar = 1/(number of labels that use that bar); average uniqueness of a label = mean over its life. Average uniqueness can be computed only on training data (needs the future t1), no leakage because it is never used as a test-time feature.
- 4.5: with K effectively independent outcomes out of I observations, a standard bootstrap oversamples; expected unique draws approx (1-1/e) of K, not I. Consequences: trees in a forest become near-copies, and out-of-bag accuracy is grossly inflated. Fixes: (a) bag with max_samples = average uniqueness, (b) sequential bootstrap: draw one at a time, lowering the probability of items that overlap with those already drawn (probability proportional to the uniqueness the candidate would have given the current draw set). Monte Carlo (numObs=10, numBars=100, maxH=5): median average uniqueness 0.6 for standard bootstrap versus 0.7 for sequential.
- 4.6: weight a sample by the absolute sum of returns attributed to it over its life, each return divided by concurrency, then normalised so weights sum to the number of samples. Does not work with a "neutral" class, another reason to drop it.
- 4.7: time decay: weights decline linearly with cumulative uniqueness (not calendar time); parameter c in (-1,1]: c=1 no decay, 0<c<1 linear decay to a positive floor, c=0 to zero, c<0 oldest fraction erased. Motivation: markets are adaptive.
- 4.8: class weights; default 'balanced' (or 'balanced_subsample' for bagging). For meta-labels where 2/3 are zeros, unbalanced training makes the classifier predict "don't trade" almost always.

### Ch 5 - Fractionally Differentiated Features
- 5.2: returns are stationary but memoryless; prices have memory but are non-stationary. Integer differencing (d=1) removes more memory than needed. Fractional differencing with 0<d<1 keeps memory while passing a stationarity test.
- 5.4-5.5: weights follow a binomial series; they decay slowly for 0<d<1 (so the value depends on a long history). Two implementations: expanding window (causes a negative drift) and Fixed-Width-Window (FFD): drop weights below threshold (e.g. 1e-5) so every point uses the same weight vector, driftless.
- 5.6: find the minimal d that makes ADF reject a unit root. For E-mini S&P futures log prices about d=0.35 gives ADF below the 5% critical value (-2.86) while correlation with the original price series stays 0.995 (returns: correlation 0.03). On 87 liquid futures, stationarity was reached with d<0.6 in all cases.
- Practical recipe (5.7): cumulative sum -> FFD(d) for d in [0,1] -> minimum d with ADF p<5% -> use as a feature. Relevance for us: only as a feature for an ML/filter model. We do not need it for the rule-based strategies.

### Ch 6 - Ensemble Methods
- 6.2: error = bias + variance + noise. Bagging reduces variance; boosting reduces bias but raises overfit risk. In finance (very noisy) bagging is usually preferable.
- 6.3: bagged prediction variance falls with the number of estimators only if their forecasts are weakly correlated; redundant (overlapping) observations make bootstrap samples near-identical, so bagging then does nothing, regardless of N. Rule of thumb: if each label spans 100 bars, sample about 1% per estimator.
- 6.3.2: majority vote improves accuracy only if single-classifier accuracy exceeds chance; bagging cannot rescue poor classifiers.
- 6.4: random forest overfits when observations are redundant; remedies: lower max_features, set min_weight_fraction_leaf about 5% (early stopping) until OOB accuracy converges to k-fold accuracy, or bag decision trees with max_samples = average uniqueness. Do not trust OOB accuracy; use unshuffled stratified k-fold with a small k.
- 6.7: bagging with early-stopped base learners is also a scalability tool.

### Ch 7 - Cross-Validation in Finance
- 7.3: k-fold CV fails because (1) observations are not IID: serially correlated features plus overlapping labels let train information leak into the test fold (an irrelevant feature then looks predictive), and (2) the same test data is reused many times in model development (selection bias).
- 7.4.1 Purging: remove from the training set every observation whose label time span overlaps in time with any test label span (three overlap conditions). 7.4.2 Embargo: additionally drop training observations immediately AFTER each test block, for h bars; h about 1% of the number of bars usually suffices. No embargo needed before the test block (training labels ending before test start contain only past information).
- Diagnostic: if performance keeps improving as the number of folds k rises toward T, the CV is leaking; after proper purging performance stops improving beyond some k.
- Both purging and embargo must be used for every train/test split (hyper-parameter tuning, feature importance, backtesting).
- 7.5: lists scikit-learn bugs (scoring ignores sample weights, class label handling); lesson: read the code you run.
- Exercises: shuffled k-fold gives much higher scores than unshuffled purged CV; the latter is the realistic one. Ex. 5: trying 1000 configurations guarantees some lucky ones; even a train/validation/test split fails if the test set is used to pick among many configurations.

### Ch 8 - Feature Importance
- 8.1: repeating "run ML, backtest, tweak, repeat" on the same data is statistically fraudulent; about 20 iterations suffice to find a "significant" false strategy at the 5% level.
- 8.2: "Marcos' First Law of Backtesting: backtesting is not a research tool, feature importance is." Do feature analysis before any backtest.
- 8.3: MDI (mean decrease impurity; in-sample, tree-only, diluted by substitute features, set max_features=1 to avoid masking); MDA (permutation importance, out-of-sample with purged CV; correlated features can both look unimportant); SFI (single-feature OOS score; no substitution effects but misses joint effects).
- 8.4.2: orthogonalise features with PCA first; if the feature importances computed with labels agree with the PCA ranking computed without labels (weighted Kendall tau; example 0.82), that is evidence the pattern is not pure overfit.
- 8.5: compute importance per instrument and aggregate (parallelised) or stack all instruments in one standardised dataset (preferred by the author: more data, less overfit to one instrument).
- 8.6: synthetic test with 40 features (10 informative, 10 redundant, 20 noise): all three methods mostly separate signal from noise, SFI worst because of joint effects.

### Ch 9 - Hyper-Parameter Tuning
- 9.2-9.3: use grid or randomised search, always with purged k-fold; random search with log-uniform distributions for scale-type parameters (C, gamma) has a fixed compute budget and is not slowed by irrelevant parameters.
- 9.4: scoring: for meta-labelling use F1 (accuracy rewards predicting "no trade" always). Otherwise use negative log-loss instead of accuracy, because log-loss penalises confident wrong calls, and that matches PnL when the bet size depends on confidence. Sample-weighted log-loss approximates a PnL-relevant metric.

### Ch 10 - Bet Sizing
- 10.1: high accuracy with bad sizing still loses money (accuracy on small bets and low accuracy on big bets ruins you).
- 10.2: strategy-independent methods: (a) concurrency: c_t = number of concurrent long bets minus short bets; fit a mixture of two Gaussians to c_t and size by the CDF (the stronger the signal, the lower the chance it gets stronger); (b) budgeting: size = (concurrent long - concurrent short) / max concurrent; (c) meta-labelling probability.
- 10.3: from a predicted probability p of the chosen class (binary case): z = (p - 1/2) / sqrt(p(1-p)), bet size m = 2*Z(z) - 1, with Z the standard normal CDF. So p=0.5 gives size 0, higher p gives size rising toward 1 (a smooth saturating curve). For more than two classes it uses one-vs-rest with a different null. The side comes from the primary model; for meta-labels use the probability of label 1 as the size.
- 10.4: average the sizes of all bets still active (between entry and their barrier) rather than overriding, to reduce turnover.
- 10.5: discretise the size to steps (d such as 0.05-0.2) to avoid jitter trades.
- 10.6: dynamic sizing with a sigmoid or power function of the gap between forecast price and market price, with a break-even limit price. Needs forecast prices; not applicable to our rule-based exits.

### Ch 11 - The Dangers of Backtesting
- 11.2: a backtest is a hypothetical simulation, "not an experiment, proves nothing"; use it as a sanity check on sizing, turnover, cost resilience and scenarios. Seven sins (Deutsche Bank): survivorship bias, look-ahead bias, storytelling, data mining/snooping, ignoring transaction costs, outliers, shorting costs. Additional: unrepresentative sample period, ignoring stop-out/margin limits, ignoring funding costs.
- 11.3: even a flawless backtest is probably wrong because the better a researcher gets, the more tests he has run on the same data, so multiple testing alone produces flukes.
- 11.4: "the purpose of a backtest is to discard bad models, not to improve them." Adjusting the model after seeing backtest results is dangerous. Do not backtest until the model is fully specified; if it fails, start over.
- 11.5 recommendations: (1) develop models for whole asset classes, not one security; an effect appearing in one instrument only is likely false. (2) bag; if bagging hurts performance the strategy fits a few outliers. (3) do not backtest until research is complete. (4) record every backtest so the probability of overfitting can be estimated and the Sharpe ratio deflated by the number of trials. (5) simulate scenarios rather than only the historical path. (6) if a backtest fails, start from scratch, do not reuse it.
- 11.6: walk-forward has a single test path that can be re-run endlessly until a false positive appears; it is also leak-prone when serial dependence is long. PBO via combinatorially symmetric cross-validation (CSCV): build matrix M of PnL series (T periods x N trial configurations); split time into S equal blocks (e.g. S=16 gives 12,780 combinations of S/2 blocks); for each combination choose the best trial in the in-sample half, find its relative rank among all N trials out-of-sample (omega), compute logit = ln(omega/(1-omega)); PBO = fraction of combinations where the logit is below 0, i.e. the in-sample winner ends below the OOS median. Needs synchronous PnL series for all trials, so we must log every parameter variant tried. Observations inside each block keep time order; sampling is done on blocks.

## Topic tags

### trend
- Ch 3 exercise: moving-average-crossing trend strategy meta-labelled with a random forest; only as an example, no numeric result.
- Ch 5: price memory matters; stationarity via fractional differencing preserves trend-like memory for features.

### breakout
- Not covered directly. CUSUM filter (2.5.2.1) is a volatility-scaled "run of size h" detector which is conceptually a breakout/filter-rule trigger (equivalent to the Fama-Blume filter rule) usable as an event definition.

### mean-reversion
- Ch 3 exercise 5: Bollinger-band mean reversion with one-sided barriers [0,2] (stop only) meta-labelled; no results given.

### momentum/oscillators
- Not covered.

### patterns
- Not covered; Ch 1: a pattern needs a theory/mechanism, storytelling after the fact is a named sin (11.2).

### intraday/sessions
- 2.3.1.1: markets are busier at the open than at midday; time bars therefore sample unevenly; volatility-scaled thresholds are needed in labelling (3.2).
- 3.3: volatility estimated intraday but expressed per day (EWM std with span in days).

### seasonality/time
- Ex. 11.4: "September is the only negative month" is given as a data-mining example, not a reason to trade.

### volatility
- 3.3 dynamic thresholds: set barriers from an EWM std of recent returns; our ATR-based stops are the same idea.
- Bars with constant information content have more stable volatility (homoscedastic).

### stops-and-exits
- 3.2/3.4: fixed-horizon labels ignore stops; triple barrier encodes SL, TP and max hold together, first touch wins. Our SL/TP in R plus session-end exit is a triple barrier with the vertical barrier at session close.
- 11.2: ignoring stop-out limits/margin calls is a backtest sin.

### position-sizing/risk
- Ch 10: size from probability (z-score -> normal CDF), average concurrent bets, discretise steps, concurrency-based sizing (budget by max concurrent bets).
- 3.7: poor accuracy on large bets with good accuracy on small bets loses money.
- 1.3.1.6: allocation to a strategy should grow only with live evidence (concave allocation function), and shrink as performance decays.

### testing-and-robustness/overfitting
- Purging and embargo (7.4), uniqueness weights (Ch 4), PBO/CSCV (11.6), count and record all trials (11.5), no research by backtest (8.2, 11.4), multi-instrument models (11.5), bagging as an overfit test, scenario simulation, 20 iterations give one false discovery at 5% (8.1).
- Walk-forward is a single path and can be overfit (11.6).

### costs/execution
- 11.2: transaction costs are hard to simulate; a "flawless" backtest assumes costs far above what anyone would ask and still may be a fluke.
- 2.4.1: ETF trick includes costs per dollar, a bid-ask term, and carry.

### psychology/discipline
- Ch 11: do not research under the influence of a backtest; resist reusing failed backtest results; overfitting is unethical.

### portfolio/diversification
- 1.2: independent silo strategies for diversification; 11.5 a signal that works only on one security is suspect; 8.5 stacked cross-instrument datasets.
- Ch 16 (hierarchical risk parity) is outside this part.

## Testable ideas

1. **Meta-label filter on our existing rule signals (rule-based, no ML)** ★
   - Rule: take every signal of an existing strategy (e.g. strategy 2 NY sweep, 5 gap fade, 6 ORB), compute the triple-barrier outcome in R (win = TP hit, loss = SL hit, time exit = sign of R or by threshold) as a 0/1 meta-label. Then, instead of a random forest, define 3-6 simple pre-registered features measured at the signal bar: ATR percentile / recent realised-vol rank, distance of the signal from the daily range (position in prior-day range), serial correlation sign of last N bars, weekday, minutes since session open, size of the stop in ATR. Test each feature alone (single-feature importance, SFI style) with purged time-blocked splits: bucket by feature quantile, compare mean R per bucket in train blocks versus held-out blocks. Optionally a depth-2 decision tree or logistic regression with strong regularisation.
   - Source: Ch 3.6-3.8, Ch 8 (SFI/MDA), Ch 9.4 (F1 scoring).
   - Author's claim: meta-labelling lifts F1 and is more robust than learning side+size; no numbers.
   - Fit: good for our data, because it keeps the primary rule unchanged and only decides trade/skip, which also makes it a natural test of whether a rule has ANY conditional edge. Risk: if the primary has negative expectancy overall, the filter must find pockets of positive expectancy; with a few hundred trades per symbol this is easily a fluke, so count every feature tried (deflate) and require the same sign in both halves and in the post-2021-09-14 MT5 data.
   - Difference from the 4 failed strategies: not a new entry rule, a conditional layer over them. Strategy 2 already has optional filters (trend, close at 16:15 ET, cost filter) that behave like hand-made meta-labels (-17 R at best): a systematic meta-label study would formalise that.

2. **Triple-barrier outcome re-labelling to audit our trade list** ★
   - Rule: for each signal compute R outcome under a grid of (take-profit multiple, stop multiple, max-hold bars) in ATR units, with first-touch logic and the conservative SL-first rule in one candle. Compare which vertical barrier (time exit) gives the best stability, by halves.
   - Source: Ch 3.4.
   - Claim: path-dependent labels are the realistic outcome; no numbers.
   - Fit: good; we already do SL/TP in R, so this is mostly a consistency check and a systematic way to sweep exits while recording every trial for deflation. Note swap costs make long vertical barriers expensive.
   - Differs: it tests the exit design, not a new entry.

3. **CUSUM event-driven entry triggers** ★
   - Rule: on 5m-1h bars run the symmetric CUSUM filter on returns with threshold h = k x (daily vol estimate), k in a small set (0.5, 1, 1.5); an event fires when the positive (negative) cumulative sum exceeds h, then reset. Trade either continuation (in the event direction) or fade, with ATR-scaled SL/TP and exit at session end. Sample only event bars.
   - Source: 2.5.2.1; relates to filter-rule trading (Fama/Blume).
   - Claim: avoids repeated triggers around a level; no performance claim.
   - Fit: good (price only, intraday, no volume needed). It is basically a volatility-normalised filter rule, so expect results similar to breakout/momentum or mean-reversion families; the value is mainly as a cleaner event definition for other tests.
   - Differs: event spacing is volatility-scaled instead of calendar/session-based; but expected edge is low (prior: filter rules lose after costs).

4. **Probability-to-size mapping for combined/weak signals** ★
   - Rule: if any filter gives a probability p (or a calibrated win-rate estimate from a bucket) that a trade wins, set the risk fraction in R as m = 2*Normal CDF((p-0.5)/sqrt(p(1-p))) - 1 scaled to a maximum risk, discretised to steps of 0.05-0.1, averaging overlapping open signals; compare against flat size on the R series.
   - Source: Ch 10.3-10.5.
   - Claim: sizing from confidence beats flat sizing when probabilities are informative; no numbers.
   - Fit: good and cheap to test in R space (risk/ layer). Only useful if some filter actually gives calibrated probabilities; with p near 0.5 the size is near zero, which is also a useful property for FTMO drawdown limits.
   - Differs: pure risk layer.

5. **Concurrency-aware sizing for multi-symbol / multi-strategy books**
   - Rule: when several strategies/symbols fire at the same time, scale each trade by 1 / (number of concurrent positions) (uniqueness idea) or budget size = concurrent / max concurrent. Use for FTMO daily loss control.
   - Source: Ch 4.3-4.4, 10.2. Fit: good for portfolio-level combination; it does not create edge.

6. **Meta-labelling with event-time "regime" features (vol rank, trend, session)**
   - Rule: same as idea 1 but with features from higher-timeframe states (daily trend direction vs trade direction, vol regime). Source Ch 3.8 (suggests structural breaks, serial correlation). Fit: moderate; those hand features overlap with the trend filter already tried in strategy 2.

7. **Fractionally differentiated price level as a feature**
   - Rule: FFD(d) of log price with minimal d for stationarity (d about 0.3-0.5), used as a mean-reversion / trend-strength feature for a filter. Source Ch 5. Fit: poor-moderate; only worth it inside an ML filter, hard to interpret, easily overfit.

## Warnings / pitfalls
- Standard k-fold CV and shuffled splits leak information with overlapping trade outcomes; use time-ordered blocks, purge overlaps, embargo after test blocks (about 1% of bars).
- Overlapping trades (e.g. several signals open at once, or multi-bar holds) are not independent samples; the effective sample size is lower than the trade count (average uniqueness). Our t-stats and Monte Carlo that treat trades as independent may overstate significance.
- OOB or in-sample accuracy is inflated; judge only on purged out-of-sample data.
- Fixed-horizon or fixed-threshold labels ignore stops and volatility regime; use vol-scaled barriers.
- A neutral/"time exit" class complicates weighting and metrics; a cleaner design is binary win/loss with a probability.
- Accuracy is a bad score for meta-labels when most labels are 0; use F1 or, better for money, a PnL-weighted measure.
- Repeating test-modify-test on the same data finds false positives at roughly one per 20 trials at the 5% level; record every trial, deflate the Sharpe by the trial count, estimate PBO (CSCV) when selecting among variants.
- Walk-forward is a single path and easily re-run until it looks good.
- A backtest is not a research tool: do not tune the strategy on backtest output; research with ex-ante tools (feature importance, theory), backtest once, and restart if it fails.
- A pattern found in one security only is likely false; test on whole classes (all indices, all FX/gold) with the same parameters.
- Look-ahead through data alignment (release dates, revisions) and survivorship; for us the equivalent is the SeriesView rule, which is already enforced.
- Bagging that changes the performance sharply signals a strategy resting on a few outliers.
- A flawless, conservative-cost backtest can still be a fluke once many tests have been run on the same data.
- Need a theory: the strategy must name who loses money to us and why; ex-post stories are a listed sin.
- Meta-labelling limits overfit risk only in the sense that the side is fixed; the secondary model can still overfit its own features, so the same purged validation applies.
- Much of the book assumes tick/volume/order-flow data and large ML infrastructure that we do not have; the transferable value is methodological discipline rather than a ready strategy.
