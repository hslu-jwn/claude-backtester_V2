# Statistics and Bayes

How much a trade list can prove, in numbers. Sources: WK = Kurt *Bayesian Statistics the Fun Way* (by
chapter; "M1-M10" are the methods the reading notes translated to our R lists, an extension of the
book), LP = López de Prado (chapter.section), RC = Carver, EC = Chan, K = Kaufman. Tools in
[../ideas.md](../ideas.md): T-08 (trial log + DSR), T-10 (Bayesian report), T-19 (effective N). The
checklist that uses them is in [testing-and-robustness.md](testing-and-robustness.md).

## The core problem: small edges need huge samples
- Realistic Sharpe is low: 0.3-0.5 per instrument and rule set, about 1.0 as an absolute ceiling for a
  very diversified book (RC p.52, epilogue). Years needed on average to pass a 2-sigma test that SR > 0, true
  SR 0.2 / 0.3 / 0.5 / 1.0 / 2.0: 45 / 37 / 20 / 6 / 1.4 years (RC Table 5, p.71). Negative-skew rules need
  about 3 more years at SR 1.0.
- Ranking two rules is harder: a Sharpe gap of 0.25 between rules correlated 0.5 needs about 40 years
  (RC Table 6, p.73). Ranking rules by backtest Sharpe is mostly noise; pool instruments instead (two
  rules with single-instrument SR 0.05 and 0.30 need ~45 years to separate, ~11 years when run over a
  portfolio, RC ch.3).
- In trades: a win rate of 55 % against a 50 % break-even needs about 1,400 trades for posterior odds of 20
  against a skeptical prior of 1:50, and 52 % needs about 8,600 (WK ch.17, notes M4). Our runs have a few
  hundred trades: they cannot prove a small edge, only reject a bad one.
- Sample error of a rate is about 1/sqrt(N) (K p.28); the 20-trade check of Douglas is an alarm for gross
  failure, not a test.

## Beta posterior of the win rate (WK ch.5, 9, 13, 14; M1)
- With w wins and l losses and a prior Beta(a0, b0), the true win rate has the posterior Beta(w + a0,
  l + b0); mean (w + a0)/(w + l + a0 + b0); 95 % interval from the 2.5 / 97.5 % quantiles. "Win" is
  declared first (R > 0, or R above a hurdle); scratches by a stated convention.
- The question that matters: P(true win rate > break-even p*). Break-even for average win W and average loss
  L (net R): p* = L / (W + L). Decide the threshold and the required confidence before looking (WK ch.5).
- Prior strength = a0 + b0 (phantom trades). Flat Beta(1,1) is not neutral: with few trades it pulls to
  50 % and overstates edge when break-even is not 50 % (WK ch.14). Use three priors and show that the
  verdict does not flip: flat, weak skeptical, strong skeptical. Skeptical = mean at p*, strength 20 (weak) or
  100-200 (strong) because 0 of our 5 strategies worked (M2; the choice needs the user's go and is fixed
  in `docs/` before the test). With 400 trades at 52 % vs 50 %, the strong prior leaves the posterior mean
  near 50.6 %.
- Predicted wins in the next m trades follow a beta-binomial (WK ch.13), usable for "losses among the
  next 20 trades" in FTMO planning.
- Win rate ignores payoff size: a high win rate with rare large losses can have negative expectancy. Pair it
  with the mean-R posterior (M5): Student-t with n-1 degrees of freedom, location mean R, scale
  s/sqrt(n); P(mean R > cost hurdle). A skeptical Normal(0, tau) prior with tau 0.05-0.10 R shrinks the mean
  by n/(n + s²/tau²). Trade R is fat-tailed and autocorrelated: also run the day-block bootstrap.
- Below about 30 trades the posterior is almost only the prior (WK ch.14).

## A/B test of two variants (WK ch.15; M3)
- Draw 100,000 samples from each posterior; P(B > A) = share of draws with b > a; look at the distribution
  of b - a or b / a ("how much better and how sure"), and P(b - a > practical margin, e.g. 2 points).
- A filter produces a subset of the unfiltered trades, so the two lists are not independent: compare the
  kept trades against the removed ones (are the removed trades worse?), paired on common signals.
- Do not run it on the best pair of 24 variants: pre-register the pair or use the shared prior below.

## Bayes factor and required evidence (WK ch.16-18; M4)
- Posterior odds = Bayes factor × prior odds. For win rate: ln BF = w ln(p1/p*) + l ln((1-p1)/(1-p*)).
  A better H1 is a distribution (p ~ Beta(a1, b1)): BF = [B(w + a1, l + b1)/B(a1, b1)] / [p*^w (1-p*)^l], so
  one extreme p1 does not win by default (WK ch.19: the better of two bad hypotheses still "wins").
- Prior odds for "this strategy has a real net edge" are low: our base rate is 0 of 5, a defensible prior
  is 1:20 to 1:100 (user decision). Scale: 3-20 interesting, 20-150 strong, > 150 overwhelming (WK ch.16);
  stakes decide, demand the strict end for FTMO money.
- Needed trades = ln(target posterior odds / prior odds) / KL per trade, KL = p1 ln(p1/p*) + (1-p1)
  ln((1-p1)/(1-p*)). Gives the 1,400 and 8,600 above.
- Two hypotheses that explain the data equally well keep BF = 1 forever (WK ch.18): "edge" vs "luck of
  this year" needs different instruments, years or the MT5 sample. Add third hypotheses (costs artefact,
  one-year effect, random entries with the same exits: the Bayes factor against the random-entry baseline
  is the T-02 question).
- Unfalsifiable stories gain from contradicting data. Write before each test which result counts as "no
  edge" (M10).
- Grid posterior (WK ch.19; M8): hypotheses p = 0.01..0.99, prior vector of any shape (for example 90 % mass
  at break-even and 10 % on 0.5-0.6), posterior = prior × likelihood, normalised. The mass on the "no
  edge" spike is the direct answer to "probability this has no edge".
- Bayesian power before the single MT5 test (M9): simulate datasets of growing n for a hypothesised win
  rate and the skeptic's prior; the n where P(conclude edge) > 0.95 in 80 % of runs says in advance how many
  trades are needed.

## Multiple testing: the number of trials
- Every extra test on the same data raises the odds of a fluke: about 20 tries give one "significant" false
  strategy at 5 % (LP 8.1). Zero-skill rules, one year of data, accepted at SR 0.5: 1 rule tested accepts
  <1, 10 rules 3, 100 rules 30 (RC Table 3). Sharpe cut-off for 5 % false acceptance over 100 rules and
  5 years: 1.5, over 30 years 0.7 (RC Table 4); a realistic single-instrument SR of 0.3 can never pass it.
- Expected maximum Sharpe of N independent null trials grows like sqrt(2 ln N) (LP 12.5, 14.7.3). The best
  of 24 variants is therefore expected to look good by luck alone.
- **PSR** (LP 14.7.2, standard form): PSR(SR*) = Z[(SR_hat - SR*) sqrt(T-1) / sqrt(1 - g3 SR_hat + ((g4-1)/4)
  SR_hat²)] with SR_hat the **non-annualised** Sharpe of the per-trade (or per-day) R series, T the number
  of returns, g3 skewness, g4 kurtosis (normal = 3), Z the normal CDF. Pass above 0.95. Rises with SR and T,
  falls with negative skew and fat tails.
- **DSR** (LP 14.7.3): PSR with SR* = sqrt(V) [(1-g) Z⁻¹(1 - 1/N) + g Z⁻¹(1 - 1/(N e))], g = 0.5772, V =
  variance of the Sharpe estimates across the trials, N = **independent** trials. Needs the trial log
  ("third law": report every result with all trials behind it). Correlated grid cells count as fewer
  trials (cluster the return series); untracked manual iterations count as more. When unsure use the raw
  count.
- Shared prior (M7): treat the true win rates of the variants as draws from one Beta(a, b) fitted to all
  variants (empirical Bayes); the best variant then shrinks toward the group mean and the winner's curse
  disappears. Simple version: skeptical prior for all, stricter threshold (posterior > 0.95 for the best)
  or prior odds divided by the number of variants.
- **Max-of-N sampling distribution** (DA p.255-330): the statistic of a data-mined winner is the maximum of N means, biased upward;
  its p-value comes from the distribution of that maximum (White's bootstrap with common day indices, or the permutation max), not
  from the single-rule distribution. Bias grows roughly with log N and shrinks with more observations (artificial rules, best of
  1,024: about 84 % a year with 10 months of data, under 12 % with 1,000). Same family as the sqrt(2 ln N) rule above, but taken
  from the actual return series.
- **Markowitz-Xu shrinkage:** H' = R_mean + B (H - R_mean), the best variant's return pulled toward the average of all tested
  variants, B in [0, 1] from within-/between-variance, N and the observation count; a rough guide, sometimes badly wrong
  (DA p.255-330). Compare the empirical-Bayes shared prior above.
- The Bayesian answer does not remove the garden of forking paths; the variants tried must enter the
  prior (WK notes). Davey's 70 %-of-grid heuristic (KD p.106) is descriptive and complementary.

## Effective sample size
- Overlapping trades (several signals open, multi-bar holds) are not independent: label uniqueness at a bar
  is 1/(number of labels using it), average uniqueness is the mean over the trade's life (LP 4.3-4.4).
  Count bets (consecutive same-side positions) not trades (LP 14.3). Our t-statistics and Monte Carlo that
  treat trades as independent may overstate significance. → T-19
- Product-rule shortcuts for joint losses are valid only for independent trades or sleeves; check how much
  dependence changes the answer (WK ch.3, 6).

## Null hypotheses and the normal model
- Three nulls for "is the average return real" (EC p.16-22): (1) Gaussian, test statistic = daily Sharpe ×
  sqrt(days), critical values 1.645 at 5 %, 2.326 at 1 %; (2) Monte Carlo of price series with the same first
  four moments (in the TU example only 88 % because kurtosis alone helps momentum); (3) random entry dates with
  the same number of longs / shorts and holding time (our T-02). They answer different questions; a hypothesis
  test gives P(result | H0), not P(H0 | result).
- A 5-sigma or 7-sigma backtest or drawdown means a wrong model or a bug (WK ch.12; the Dow fell more than 4
  sigma about 30 times in 1914-2014, RC ch.1). Use the Beta for rates, not the normal (WK ch.12).
- Expect the live Sharpe at best about half the backtest (EC p.7); Carver's pessimism factors are 65-75 %
  (RC Table 14, ch.4).
## Bootstrap, permutation and bounds (Masters, Aronson, Pardo)
- Use log returns: +10 % then the move back is -9.1 %, so percent returns make a flat system look profitable (TM ch.1). Win rate
  means nothing without the win/loss sizes: target 1 and stop 9 on a random walk wins 90 % with E = 0 (TM ch.1).
- Standard error = SD/sqrt(N); plan with mean - SE; 30 trades is the floor (RP ch.6). **Lower bound of the mean:** LB = mean - t ×
  SD/sqrt(n); H0 "no skill" is rejected exactly when LB > 0 (n=100, mean 8, SD 5, p .95 → 7.17). A t-test survives skew but one wild
  outlier ruins it: look at the histogram (TM ch.6).
- Statistical is not practical significance: with thousands of days tiny returns become significant; show the effect size (R a
  year, net) next to p. Fix alpha in advance (0.05 significant, 0.01 very); a p-value is not P(system is worthless) and cannot rank
  systems, because it depends on sample length (TM ch.6; DA p.217-253, 389-440).
- **Bootstrap:** percentile, pivot (least reliable), BCa (bias and acceleration corrected); sample size = original, B >= 10,000
  for serious work. **Bootstrap log(PF), not PF or Sharpe:** with 50 returns the PF lower bound is useless and the upper bound is
  violated 4× too often; fewer than about 100 returns is unreliable for ratios (TM ch.6). Single rule: zero-centre the rule's daily
  returns and resample (DA p.217-253).
- **Permutation p** = (k+1)/(m+1), k = permuted runs at least as good, m >= 100, usually 1,000+; every permutation must be a plausible
  outcome under the null (TM ch.7). For one rule: keep its +1/-1 positions in order against shuffled detrended market changes
  (DA p.217-253). Best-of-N and training-process versions: [testing-and-robustness.md](testing-and-robustness.md).
- **Order-statistic bounds on grouped returns** (monthly / quarterly, for monitoring): lower bound = m-th smallest of n OOS returns,
  m = n·p (conservative) or (n+1)·p; needs >= 100 returns. The bound itself is uncertain: P(m-th smallest > q-quantile) =
  1 - I_q(m, n-m+1) (incomplete beta); n=200, p .1 → with probability .999 the true failure rate is <= 18 %. Add an upper bound
  that about 40 % of periods should reach; too few reaching it signals decay (TM ch.6).
- **Double-bootstrap drawdown bound:** outer loop resamples the whole OOS set; inner loop (about 10,000) draws N-bar sequences from
  it and takes the DD quantile at DD_conf (0.90-0.999); the Bound_conf percentile (0.6-0.9) of the outer quantiles is the bound. A
  plain bootstrap treats the OOS sample as the truth and underestimates catastrophic DD by more than 10× on short samples (63
  returns, p .001: 13.65×), about 2× on moderate ones, and is fine only with ~2,500 returns and modest p (TM ch.6). **Disagreement:**
  Davey's plain resample of the walk-forward trades (KD ch.7, 14) is of this anti-conservative kind; Masters' double bootstrap
  is the correction. Measure DD in log-equity units; the bound holds for one stated period, not "ever".

See also: [testing-and-robustness.md](testing-and-robustness.md), [combining-edges.md](combining-edges.md),
[position-sizing-and-risk.md](position-sizing-and-risk.md).
