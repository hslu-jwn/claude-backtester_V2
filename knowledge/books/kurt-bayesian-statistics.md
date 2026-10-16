> Reading notes, own words, made 2026-10-16 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

> Cited as WK by chapter (no page numbers in the extracted text). Methods M1-M10 below are the notes' own extensions for our R trade lists.

# Notes: Will Kurt, *Bayesian Statistics the Fun Way* (No Starch 2019)

Note on page numbers: the extracted text has no page headers, so references are by chapter (Ch N) and section name. The only page the text itself cites is "page 127" (Ch 13, plotting a PDF in R). Appendix A (R basics) and Appendix B (calculus) are tool tutorials and are only mentioned, not summarised.

## Overview

- A beginner-level, intuition-first introduction to Bayesian statistics in four parts: (I) probability rules and the binomial / beta distributions, (II) conditional probability, Bayes' theorem, prior / likelihood / posterior, (III) parameter estimation (mean, spread, normal, PDF / CDF / quantile, priors, Monte Carlo A/B test), (IV) hypothesis testing with the Bayes factor and posterior odds.
- Stance: probability is a measure of belief, not frequency. Data is the only fixed thing; beliefs must move with it. Priors are not a flaw but a way to encode background knowledge; a prior is "wrong" only if you refuse to let data override it.
- Everything is built from a few rules: negation, product rule, sum rule, Bayes' theorem. Each later tool (beta posterior, A/B test, Bayes factor, parameter estimation by hypothesis grid) is derived from those.
- Practical output is always a probability statement ("P(B better than A) = 0.96", "95% interval 0.67%-0.84%") rather than a significance verdict. The book keeps stressing "how much better" and "how sure", not "significant or not".
- The book contains NO trading content. Its value for us is the machinery for judging a small, noisy trade sample: Beta posterior of win rate, Monte Carlo comparison of two variants, Bayes factor with skeptical prior, "how much data to convince a skeptic".
- Limits of the book (important for us): it treats only binary outcomes (win/loss) properly. It has no treatment of fat tails, autocorrelation, multiple testing, or non-binary payoffs (R multiples). Those need our own extensions (flagged below as "extension").

## Chapter notes

### Ch 1 - Bayesian Thinking and Everyday Reasoning
- Process: observe data D, form hypothesis H, update belief. Notation P(D | H, X) with X = background experience.
- A hypothesis is good when it makes the data likely: P(D | H1) much greater than P(D). Compare hypotheses by the ratio of how well each explains the same data.
- Key warning: P(D | H) ("how well my belief explains the data") is not P(H | D) ("how well the data supports what I believe"). Collecting data to confirm a belief is the wrong direction. Backtest translation: do not search for trades that confirm the idea; ask how well the idea explains all trades.

### Ch 2 - Measuring Uncertainty
- Probability 0..1, P(X) + P(not X) = 1. Probabilities of events by counting outcomes; probabilities of beliefs via betting odds: odds m:n implies p = m/(m+n).
- Converting odds to probability: o = p/(1-p), so p = o/(1+o). Used later for prior odds.

### Ch 3 - The Logic of Uncertainty
- Product rule (independent): P(A,B) = P(A) P(B). Sum rule: P(A or B) = P(A) + P(B) - P(A,B).
- Example "probability of being late" = P(train late) x P(bus late) = 0.03. Backtest translation: probability that k independent sleeves are all losing in a period = product, but only if truly independent (see Ch 6 warning).

### Ch 4 - Creating a Binomial Probability Distribution
- Binomial B(k; n, p) = C(n,k) p^k (1-p)^(n-k). Parameters: k successes, n trials, p success probability.
- Cumulative form pbinom: P(at least one success in n trials) = 1 - (1-p)^n. Gacha example: 100 pulls at p = 0.72% gives about 0.52 chance of at least one hit, even though exactly-one is only 0.35.
- Backtest translation: "probability of a losing streak / of at least m wins in n trades given a true win rate" is a binomial tail (streak runs need a Markov/simulation extension).

### Ch 5 - The Beta Distribution
- Probability vs statistics: probability knows p and asks about data; statistics sees data and asks about p (inference).
- With a wins and b losses observed, the plausibility of every possible p is Beta(alpha = a, beta = b), density proportional to p^(a-1) (1-p)^(b-1). Mean = a/(a+b).
- Probabilities of ranges come from integrating the PDF (R: integrate(dbeta)). Examples: Beta(14,27) gives 0.98 probability that the true rate is below 0.5 (the box loses money). Beta(5,1195): P(rate > 0.005) = 0.29, so a stated decision rule "need more than 0.7 belief" fails.
- Decision pattern used throughout: define the threshold that matters (break-even), compute the posterior probability of being on the good side, compare against a pre-set required confidence (0.7 in the example).

### Ch 6 - Conditional Probability
- P(A | B); revised product rule P(A,B) = P(A) P(B | A). Treating dependent events as independent gives wrong answers (the color-blind male example: 0.04 vs naive 0.02125).
- Bayes' theorem: P(A | B) = P(B | A) P(A) / P(B). Lets us reverse "probability of data given belief" into "probability of belief given data".
- Warning applicable to us: independence is assumed constantly in practice (e.g. treating trades or strategies as independent); check how much dependence changes the result.

### Ch 7 - Bayes' Theorem with LEGO
- Visual derivation of Bayes via areas of stacked bricks. Only value: confirms the theorem as a plain ratio of counts (4 of 6 yellow studs lie over red = 4/6). No method content.

### Ch 8 - The Prior, Likelihood, and Posterior of Bayes' Theorem
- Three parts: posterior P(H | D), likelihood P(D | H), prior P(H); P(D) normalises and is usually unknowable.
- Proportional form: posterior is proportional to prior x likelihood. P(D) cancels when comparing two hypotheses, so compare ratio of (prior x likelihood).
- Robbery example: H1 (robbed) vs H2 (baseball + unlocked door + forgotten laptop) ends at 6,570:1 for H1 mainly because the product of three small priors makes H2 extremely improbable. Lesson: a hypothesis that explains data perfectly (likelihood 1) can still lose heavily if it needs many unlikely conditions. This is an Occam penalty and matters for strategies with many tuned parameters (each added parameter condition multiplies in another unlikely coincidence).
- Sensitivity: because the numbers are explicit, anyone can substitute a different likelihood and see the effect. Use this for a robustness table of prior assumptions.

### Ch 9 - Bayesian Priors and Working with Probability Distributions
- Star Wars example: C-3PO's data (2 successes, 7440 failures) is the likelihood, a "Han is exceptional" belief (20,000 successes, 1 failure) is the prior. Beta posteriors add parameters: Beta(a_post, b_post) = Beta(a_like + a_prior, b_like + b_prior). Result Beta(20002, 7401) about 73% survival.
- Point: statistics that contradicts all other knowledge needs a prior, but the prior must be stated and can be challenged. A prior in beta form is equivalent to "pseudo-observations": Beta(a,b) acts as if a wins and b losses were already seen. Strength of prior = a + b.
- Backtest translation: a prior encoding "random strategies do not work" is a Beta with mean at break-even and a+b large.

### Ch 10 - Introduction to Averaging and Parameter Estimation
- Why the mean works: errors weighted by their probability cancel (expectation = sum of x_i p_i).
- Warning: mean as measurement of one true value is justified; mean as summary of genuinely varying things (heights) is not the same. Ask what you are trying to measure. Backtest translation: mean R of a trade list is a legitimate estimate of the edge only if trades are draws from one stable process (they are not if the regime changes between halves).

### Ch 11 - Measuring the Spread of Our Data
- MAD (mean absolute deviation), variance, standard deviation: all measure spread; standard deviation is the default because it pairs with the mean in the normal distribution. Variance penalises large deviations more.
- Spread of observations signals how uncertain the mean is. (The book does not yet give the standard error sigma/sqrt(n); that is our extension: uncertainty of the mean R shrinks with sqrt(n), not n.)

### Ch 12 - The Normal Distribution
- Normal(mu, sigma) as the honest model when only mean and sd are known. 68 / 95 / 99.7% inside 1 / 2 / 3 sigma.
- "n-sigma event" table: 3 sigma about once per year of daily events, 5 sigma about once per 5 millennia, 6 sigma 1.4 million years. If you see 5+ sigma, assume the normal model is wrong rather than that something miraculous happened.
- Normal vs beta: for bounded rates (0..1) the normal is a poor model; use beta. Do not use a normal when you know more (bounds, skew).
- Backtest translation: a "6-sigma drawdown" or "7-sigma backtest" is evidence of a wrong model or data bug, not of an edge.

### Ch 13 - Tools of Parameter Estimation: PDF, CDF, Quantile Function
- PDF shows shape; CDF gives P(X <= x) so ranges are CDF differences; quantile function (inverse CDF) gives medians and intervals.
- Credible interval ("confidence interval" in the book's wording) = quantiles. Example: Beta(300, 39700) gives 95% interval 0.668% - 0.837% via qbeta(0.025/0.975).
- Prediction: apply the interval to a future batch (100,000 visitors gives 670-840 conversions). Backtest translation: next 100 trades expected wins interval.
- Book distinguishes its Bayesian "interval" from the classical confidence interval (different meaning). For us: the Bayesian one is the statement "95% probability the true win rate lies in here", which is what we actually want.
- Binomial CDF works too: pbinom(3,5,0.5) = 0.8125.

### Ch 14 - Parameter Estimation with Prior Probabilities
- Small data gives absurd posteriors (2 clicks of 5 allows rates up to 80%). A prior from related data (industry mean 2.4% click rate; weak prior Beta(1,41)) restrains that. As data grows (25 of 100, then 86 of 300) the posterior moves toward the data and the prior's influence fades.
- Prior strength = alpha + beta. Beta(5,200) needs more evidence to move than Beta(1,41). Choosing strength is a judgment about how well the reference data describes the current process.
- Priors can come from experts, quantified (e.g. Beta(2,8) vs Beta(200,800)), and different people's priors can be compared; they converge with data.
- No truly "fair" prior: Beta(1,1) says "all rates equally likely", and after 11,000 sunrises it still implies the sun fails to rise within a human lifetime. Beta(0,0) undefined with zero counter-examples. Honest answer with no information and no data: "can't conclude anything".
- Backtest translation: strong skeptical prior for strategy win rates; weak/flat prior only if you truly have no reference class (we do: 5 failed strategies).

### Ch 15 - From Parameter Estimation to Hypothesis Testing: A Bayesian A/B Test
- Two variants, same prior Beta(3,7) (mean 0.3), data A: 36 clicks / 114 not, B: 50 / 100. Posteriors Beta(36+3, 114+7) and Beta(50+3, 100+7).
- Monte Carlo: draw 100,000 samples from each posterior, P(B > A) = fraction of draws with b > a = 0.96. Also look at the ratio b/a: mean about 1.4, 25% chance of 50%+ improvement; "chance B is 20% worse is about the same as chance it is 100% better".
- Author notes that with a flat prior this is roughly like a one-sided p about 0.04 in a classical t-test, but gives a direct probability and an effect-size distribution.
- Exercises (not solved in text): add a skeptical prior that B = A; add a prior that B is near 20%; explore how many samples convince a skeptic when true rates are 0.25 vs 0.30.

### Ch 16 - Introduction to the Bayes Factor and Posterior Odds
- Ratio of posteriors = Bayes factor x prior odds: P(H1|D)/P(H2|D) = [P(D|H1)/P(D|H2)] x [P(H1)/P(H2)]. P(D) cancels.
- Evidence scale (author's guideline, for posterior odds): 1-3 interesting; 3-20 on to something; 20-150 strong; over 150 overwhelming. Use judgment: stakes decide the threshold.
- Example loaded die: 4 sixes in 10 rolls; likelihood ratio about 4 for "p(6)=1/2" vs "p(6)=1/6", but prior odds 1:2 (one loaded die in three) leave posterior odds about 2: not conclusive, roll more.
- Rare disease example: prior odds 1:3,700 overwhelm a likelihood ratio of about 2.2, posterior odds about 1:1,659 against the scary hypothesis. Lesson for us: a rare-hypothesis prior can dominate. For trading, "this particular strategy has a real edge" is a rare hypothesis (base rate of working strategies is low), so the same effect applies.

### Ch 17 - Bayesian Reasoning in The Twilight Zone
- Hypothesis "oracle always right" vs "guessing": likelihood ratio after n correct answers = 2^n.
- Skeptic with prior odds 1/1,000,000 needs n > 21 correct for posterior odds above 2. Reverse-engineering: from the amount of evidence needed to be convinced you can infer someone's prior (Don about 1.17, Pat about 0.0003).
- Method: required evidence = log of (target posterior odds / prior odds). Use to answer "how many trades must a strategy win before I believe it?" given a skeptical prior.

### Ch 18 - When Data Doesn't Convince You
- If two hypotheses explain the data equally well (Bayes factor 1), more data never changes the posterior odds; only the prior can. Example: "friend is psychic" vs "friend uses a loaded die": 90% hit rate fits both identically.
- A hypothesis that assigns probability 1 to any data (unfalsifiable) gains from contradicting evidence. Always ask "what result would make me abandon this?"
- Lesson for us: a good backtest is falsifiable; if every outcome (profit or loss) can be rationalised by the strategy story (regime changed, filter failed), no amount of data will correct us.
- Also: a two-hypothesis test only picks the better of two, not a good one. Always add a plausible third alternative (e.g. "the edge is only costs/slippage artefact", "edge only from one year").

### Ch 19 - From Hypothesis Testing to Parameter Estimation
- Duck game: attendant claims p = 0.5, customer p = 0.05; data 24 prizes in 100. Bayes factors against two bad hypotheses favour the less wrong one (653:1 for 0.5 over 0.05) even though both are poor. Searching a grid (0 to 1 by 0.01) finds the best hypothesis p = 0.24 (Bayes factor of 1.5 million vs 0.5).
- Any prior shape can be applied on the grid (e.g. "rates in 0.2-0.3 are 1000 times less likely"), multiply by the Bayes factors, normalise by the sum, then compute expectation, intervals, and tail probabilities. This is a numerical posterior (grid approximation) and works for non-beta priors.
- Grid-normalised likelihood with flat prior equals Beta(24+1, 76+1): confirms the beta result by a different route.
- Exercise (unsolved in text): compare two games by sampling both posteriors, same method as Ch 15.

### Appendices
- A (R basics: vectors, seq, ifelse, sample) and B (calculus basics) are tutorials; nothing for us beyond translating to numpy/scipy.

## Topic tags

### testing-and-robustness (primary)
- Beta(wins + prior_a, losses + prior_b) is the posterior of a true win rate; prior strength = a + b controls how fast data overrules it (Ch 5, 9, 14).
- Monte Carlo comparison of two posteriors gives P(B > A) and the distribution of the ratio B/A, i.e. "how much better and how sure" (Ch 15). Direct answer to variant A vs B questions (filter on/off, entry mode, timeframe).
- Bayes factor: ratio of likelihoods for two explicit hypotheses; combine with prior odds for posterior odds; the log of required evidence tells how many observations convince a skeptic (Ch 16-17).
- Prior odds must reflect base rates of strategies working. Rare-hypothesis priors can outweigh a respectable-looking likelihood ratio (Ch 16 disease example).
- Posterior is proportional to prior x likelihood; many tuned conditions multiply small probabilities (Ch 8): an Occam penalty relevant to parameter-heavy strategies.
- Sensitivity analysis of the prior (Ch 8, 14, 18): report results under several priors (flat, skeptical, optimistic). If the conclusion flips between them the data is too thin.
- Two-hypothesis tests only rank the two given; add alternative hypotheses (Ch 18). Unfalsifiable hypotheses grow stronger with contradicting data.
- Sigma-events: 5+ sigma means the model is wrong (Ch 12).
- Bayesian interval is a direct probability statement; still ignores autocorrelation and regime shifts, which the book does not cover (extension needed).
- Missing from the book: multiple-comparison correction (testing 24 variants). Bayesian answer (extension): use a shared hierarchical prior or a skeptical prior fitted to the distribution of all variant results; or divide prior odds by the number of variants tried.

### position-sizing/risk
- The book does not cover sizing. Relevant pieces: (a) the Beta posterior of win rate gives a distribution of the Kelly fraction if payoff is fixed (extension: f* = p - (1-p)/b with p drawn from posterior; size to the lower quantile, not the mean), (b) binomial tail probabilities for streaks and for "k losses in n trades", (c) predictive intervals for the number of wins in the next m trades (Ch 13: wins/visitors scaled to future batch).
- Decision threshold pattern (Ch 5): fix break-even beforehand, compute posterior probability of beating it, act only above a stated confidence.
- Warning on independence (Ch 3, 6): daily-loss and total-loss probabilities for FTMO depend on correlation between trades and between sleeves; product-rule shortcuts overstate diversification.

### volatility
- Ch 11-12: sd and normal model; use only when nothing else is known. Large moves in sigma units should prompt model doubt.

### psychology/discipline
- Ch 1, 18: data should change beliefs, not the reverse; ask what evidence would change your mind before looking; non-falsifiable beliefs get reinforced by contrary data.

### portfolio/diversification
- Product rule for joint losses only valid for independent sleeves (Ch 3, 6).

### Not relevant to this book
- trend, breakout, mean-reversion, momentum/oscillators, patterns, intraday/sessions, seasonality/time, stops-and-exits, costs/execution (no content).

## Methods to apply to our backtests

All computations assume trade lists in R (one float per closed trade, after costs). Win means R > 0 (or R above a stated hurdle, e.g. R > 0.1 to net out noise; choose and fix first). Python tools: scipy.stats.beta, numpy.random.beta, scipy.special.

### M1 - Beta posterior of win rate  ★
- Input: wins w, losses l (R > 0 vs R <= 0; scratches by a declared convention). Prior Beta(a0, b0).
- Posterior: Beta(w + a0, l + b0). Mean = (w + a0)/(w + l + a0 + b0). 95% interval: beta.ppf([0.025, 0.975], w + a0, l + b0).
- Question to answer: P(true win rate > break-even p*). For fixed target payoff, p* = 1/(1 + average win R / average loss R) (before costs; after costs use net R). Compute 1 - beta.cdf(p*, ...).
- Predictive: wins in next m trades is beta-binomial; interval from scipy.stats.betabinom(m, a, b). Gives FTMO relevant "losses among next 20 trades".
- Fit in our terms: reports for each strategy variant on the pre-2021-09-14 sample and on the MT5 test sample separately. Cheap, no new data.
- Limit: win rate alone ignores payoff size. Use M5/M6 for expectancy.

### M2 - Skeptical priors that encode our failures  ★
- Reference class: we tested 5 strategies and about 100 variants; all failed. Encode as "true win rate near break-even and strategy-level edge near 0".
- Concrete choice (extension, needs user's go): prior Beta(a0, b0) with mean = p* and strength a0 + b0 = 100 to 200 (equivalent to 100-200 phantom break-even trades). A weaker alternative a0 + b0 = 20. Report the posterior under (flat Beta(1,1), skeptical-weak, skeptical-strong); show whether conclusions flip. Do not pick the prior after seeing results; fix it in the docs first.
- Effect size: with 400 trades observed at 52% vs break-even 50%, a strong skeptical prior leaves posterior mean near 50.6%, a flat prior near 52%. This is the honest statement that small samples cannot prove small edges.

### M3 - Bayesian A/B test of two variants (filter on/off, entry mode A vs B, same signal different timeframe)  ★
- Per Ch 15. For each variant i: posterior Beta(w_i + a0, l_i + b0). Draw N = 100,000 samples each with numpy; P(B > A) = mean(b > a); distribution of b/a or b - a; report median, 5th and 95th percentile of b - a.
- Required both: "probability B better" and "probability B is better by at least a practical margin" (e.g. win rate +2 points), mean(b - a > margin).
- For R-valued results use M5 (expectancy) in place of win rate when payoffs differ between variants.
- Caveat: variants evaluated on overlapping trades (a filter is a subset) are not independent. Compare paired: restrict to common signals and treat the filtered-out trades as the difference set; test the removed trades (are they worse than the kept ones?) rather than kept vs all.
- Multiple variants: do not run M3 on the best-of-24 pair. Either pre-register the pair, or run the version in M7.

### M4 - Bayes factor: edge vs no edge  ★
- H1: win rate = p1 (a specific alternative, e.g. the in-sample estimate shrunk, or a planned design target such as 0.55). H0: win rate = p* (break-even). BF10 = p1^w (1-p1)^l / (p*^w (1-p*)^l). Work with logs to avoid underflow: ln BF = w ln(p1/p*) + l ln((1-p1)/(1-p*)).
- Better H1 (extension): a distribution of plausible edges, e.g. H1: p ~ Beta(a1, b1) with mean above p*; marginal likelihood is a ratio of beta functions: BF10 = [B(w + a1, l + b1)/B(a1, b1)] / [p*^w (1-p*)^l]. Use scipy.special.betaln. This avoids the Ch 19 problem of picking a single p1 that is "too extreme" (a hypothesis that is too wrong beats a worse one without being good).
- Posterior odds = BF10 x prior odds. Prior odds for "this particular strategy has a real, net-of-cost edge": our base rate is about 0 of 5 strategies. A defensible prior is 1:20 to 1:100 (user decision). Interpret with the author's scale (Ch 16: over 20 strong, over 150 overwhelming) but demand the stricter side because multiple tests were done.
- Required sample (Ch 17 method): n such that BF reaches the target. For a fixed true win rate p1 vs p*, expected log BF per trade = p1 ln(p1/p*) + (1-p1) ln((1-p1)/(1-p*)) (this is the KL divergence). Needed n = ln(target posterior odds / prior odds) / that per-trade value. Example (p* = 0.5, p1 = 0.55, target posterior odds 20, prior odds 1/50): ln(1000) = 6.9; per trade about 0.0050; so n about 1,380 trades. With p1 = 0.52: about 8,600 trades. This quantifies why our trade counts (a few hundred) cannot prove small edges.

### M5 - Posterior of mean R per trade (extension beyond the book; same logic as Ch 10-12)
- The book only gives the normal model for a mean with unknown spread; for R multiples use: m = mean(R), s = std(R, ddof=1), n trades; posterior for true mean under a flat prior is Student-t with df = n - 1, location m, scale s/sqrt(n). P(mean R > cost hurdle) = 1 - t.cdf((h - m)/(s/sqrt(n)), n - 1).
- Skeptical prior: Normal(0, tau) with tau about 0.05-0.10 R per trade (an edge of that size is already generous after costs). Posterior mean = m x n/(n + s^2/tau^2) (shrinkage). Show shrinkage factor.
- Caveats: the book says (Ch 12) the normal model is honest only when mean and sd are all you know; trade R is fat-tailed and autocorrelated, so also run a bootstrap of daily blocks. Fit with our existing day-reshuffle Monte Carlo: same statement, different engine.
- Equivalent to our existing t-stat but returns P(edge > hurdle) and shows prior sensitivity.

### M6 - Monte Carlo of the posterior into FTMO outcomes  ★
- Draw p (and for fixed-payoff strategies the payoff) from the posterior (M1 / M5), then simulate the account path under the FTMO rules for each draw. Report pass probability as the average over posterior draws, not for the point estimate. This yields a wider and more honest interval than simulating with the in-sample rate fixed (parameter uncertainty added to path uncertainty).
- Implementation in our terms: for k in range(10_000): p_k ~ Beta; simulate 1 account of T trades with that p_k and the strategy's R distribution (win R, loss R); apply risk/ FTMO rules; record pass/fail/breach. P(pass) = mean. Compare with P(pass) at the plug-in p; the gap measures how much parameter uncertainty matters.
- The same loop with the lower 20th-percentile p gives a defensible go/no-go threshold for demo trading.

### M7 - Multiple variants: shared prior / "winner's curse" correction (extension; the book is silent on this)
- We often have 12-24 variants of one idea. Treat true variant win rates as draws from a common Beta(a, b) (hierarchical prior). Estimate a, b from all variants jointly (method of moments or empirical Bayes using the observed w_i, l_i). Posterior for each variant is Beta(w_i + a, l_i + b): the best variant is shrunk strongly toward the group mean, which removes most of the winner's curse.
- Simple version without any fitting: use the skeptical prior M2 for all variants and report the posterior probability that the best variant beats break-even; when 24 variants were looked at, require a stricter threshold (e.g. posterior probability over 0.95 for the best after shrinkage, or divide prior odds by the number of variants).
- Complements our "share of profitable variants" metric: that metric is a descriptive count; this one adds a probability.

### M8 - Grid posterior with arbitrary priors (Ch 19 method)  ★
- Hypotheses grid: p_i = np.linspace(0.01, 0.99, 99). Likelihood L_i = p_i^w (1 - p_i)^l (work with logs). Prior vector from any belief (e.g. 90% mass near break-even, 10% mass spread on 0.5-0.6). Posterior = prior x L, normalised by sum. Then expectation, intervals, P(p > p*).
- Needed when the prior is not a beta (mixture "no edge with prob 0.9, edge with prob 0.1" is a spike-and-slab prior; posterior mass on the "no edge" spike is the direct answer to "probability this strategy has no edge").
- Cheaper to implement than M4 variants and easy to audit.

### M9 - Required sample size by simulation (the book's exercise, Ch 15 Ex. 3)
- To plan the MT5 validation: for a hypothesised true win rate and a given skeptic's prior, simulate datasets of increasing n (numpy.random.binomial), compute P(B > A) or P(p > p*) each time, and record n at which it exceeds 0.95 in, say, 80% of simulations (Bayesian power). Output a table n vs P(conclude edge).
- Use it before running the single-shot MT5 test: it states in advance how many trades we need and avoids declaring a non-result.

### M10 - Evidence-to-change-mind rule (Ch 17-18)
- Before each test, write in the ROADMAP: the BF / posterior threshold that would count as "edge" and the result that would count as "no edge". After the test, if the answer is "no edge", record it without re-tuning. Makes hypotheses falsifiable.
- Add third hypotheses as controls: "random entries with the same exit logic" (our Monte Carlo random entries already is that). Bayes factor of strategy vs random-entry baseline tests exactly the Ch 18 problem (two explanations that fit equally).

## Warnings / pitfalls

- Priors are subjective; the book says to state them and show how conclusions change. Choose the prior before looking at the result, or the analysis is circular.
- A flat Beta(1,1) prior is not neutral (sunrise example, Ch 14); with few trades it pulls toward 50% and can overstate edge when break-even is not 50%.
- A Bayes factor compares only the two hypotheses given. Both can be bad; the better one still "wins" (Ch 19 duck game, 653:1 for a wrong claim). Pick hypotheses that are plausible, or integrate over a range (M4 beta version).
- Hypotheses that explain the data equally well give BF = 1 and no amount of data helps (Ch 18). In backtests: "edge" vs "luck of this particular year" need data that separate them (different instruments, different years, MT5 sample).
- Unfalsifiable stories get stronger with contradicting data.
- Independence assumption (Ch 3, 6) can badly mislead; trades overlap in time and share market regimes.
- The normal model is only safe when nothing else is known; use beta for rates (Ch 12). Trade R is fat-tailed: sigma-based statements are optimistic.
- The book's win/loss framing ignores payoff asymmetry; a high win rate with small wins and rare large losses can have negative expectancy. Always combine with M5.
- No treatment of multiple testing, autocorrelation, regime shifts or look-ahead. Bayesian methods do not remove the garden-of-forking-paths problem: the number of variants tried must enter the prior (M7).
- The evidence scale (Ch 16) is a guide, not a law; the book says the required odds depend on stakes. For capital at risk (FTMO fees, account loss) use the strict end.
- Examples use idealised sizes; check small-n cases: with fewer than about 30 trades the posterior is almost entirely the prior.
