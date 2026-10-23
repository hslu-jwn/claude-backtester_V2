# David Aronson, *Evidence-Based Technical Analysis* (Wiley 2007)

Short: **DA**. Cite by book page: `DA p.27`.
Source PDF: `X:\Dokumente\Archiv\Trading\Evidence-Based_Technical_Analysis_-_David_Aronson.pdf`.
Notes written 2026-10-23, in our own words. Focus: methods the **application** should get. The
psychology and philosophy chapters (2, 3, 7) are summarized only briefly.

## Overview
- Part I argues that technical analysis must become a science: only objective (programmable)
  rules, tested with statistical inference that accounts for **data-mining bias**. Part II is a case
  study: 6,402 rules on the S&P 500 (1980-2005), evaluated with White's Reality Check and Masters'
  Monte Carlo permutation test. **None was significant.**
- The key ideas for us: a no-skill benchmark (detrending); the statistic of a data-mined winner is
  the *maximum* of N means, so it needs its own sampling distribution; the five factors that set the
  size of the bias; WRC and MCP for best-of-N; keep every tested rule's daily series.
- His statistic is the mean daily return on detrended data, with entry at the next open, gross of
  costs.

## Chapter notes

### Ch 1 - Objective rules and their evaluation (pp.15-31)
- **Objective = programmable** into unambiguous positions (long/short/neutral). Everything else is
  subjective and cannot be tested.
- A rule maps input series to a position series (+1/−1/0; the size can vary). A signal = a change
  in the output.
- Thresholds: fixed for stationary series (oscillators), variable (MA, zig-zag) for trending ones.
  Detrend inputs (ratio to an MA, differences) to use fixed thresholds. Two thresholds → flip-flop
  logic (MA bands: +1 on an upper cross, −1 on a lower cross, hold in between).
- **Inverse rules:** test the opposite of every traditional rule too.
- **Benchmark = a rule with no predictive power** (a random signal, like a placebo).
- **Position bias × market trend:** a no-skill rule earns ER = [p(long) − p(short)] × average daily
  change. S&P 1976-2004 (+0.035 %/day): random 90 % long → 7.31 %/yr; 60 % long → 1.78 %/yr.
  A rule whose short condition is hard to meet gets a long bias and looks good in a bull market.
- **Fix:** subtract the return of a random rule with the same bias, or more simply **detrend the
  market returns** (subtract the average daily log return over the test period from each day's log
  return) *for computing rule returns only*; signals still use real prices. A no-skill rule then
  has an expected return of 0 whatever its bias (proof in the appendix, p.475ff).
- Use log returns. **No look-ahead:** a rule that needs the close cannot fill at that close. His
  return = position at close of day 0 × [log(open day+2 / open day+1) − ALR]. Lagged or revised
  data must be lagged to its real release time.
- Costs: needed for real trading; he leaves them out because his aim is to detect information
  (costs would hide fast-reversing rules).

### Ch 2-3 - Illusory validity; the scientific method (skimmed, pp.33-163)
- Biases: overconfidence, a good story, confirmation bias, illusory correlation (counting hits,
  ignoring misses), hindsight, representativeness: **random-walk charts show convincing "trends
  and patterns"**.
- The hypothetico-deductive method: confirmation cannot prove a claim (affirming the consequent);
  contradiction can refute it. H0 = the rule has no predictive power. Example of turning a
  subjective pattern (head and shoulders) into exact rules.

### Ch 4 - Statistical analysis (pp.165-216)
- The sampling distribution of the performance statistic of a useless rule is the benchmark; the
  p-value is the area at or above the observed value. It is about the evidence, not about the truth
  of H0.
- Standard error = SD/√n; the CLT makes the mean nearly normal (ratios can be very non-normal).
  He prefers computer-intensive distributions (bootstrap, permutation) to the normal assumption.

### Ch 5 - Hypothesis tests and confidence intervals (pp.217-253)
- A test needs: the hypothesis, a test statistic (the mean daily return on detrended data) and its
  sampling distribution under H0. Thresholds: 0.10 possibly, 0.05 significant, 0.01 very, 0.001
  highly significant; set before the test. A type I error (trading a useless rule) is worse than a
  type II error (missing a good one).
- **Bootstrap test (single rule):** zero-centre the rule's daily returns (subtract their mean),
  resample n with replacement (same n), take the mean; 5,000 times; p = share ≥ the observed mean.
- **Monte Carlo permutation test (single rule, Masters):** keep the rule's +1/−1 series in order,
  pair it with **shuffled** detrended next-day market changes (without replacement) → a "noise
  rule"; 5,000 times; p = share ≥ observed. The bootstrap needs only the rule's returns; MCP needs
  the position series and the market changes. They agree well on detrended data.
- Example TT-4-91 (91-day channel breakout on Dow Transports, trading the S&P 500, 1980-2005,
  6,800 days): +4.84 %/yr detrended, p ≈ 0.069 with both methods; 80 % CI +0.62 % to +9.06 %.
  That counts only if it was the only rule tested.
- **Estimation:** the sample mean is the best estimator; bootstrap percentile CI (drop the top and
  bottom (100−CI)/2 % of the resampled means). MCP gives no CI (it tests information, not a
  parameter). A test and a CI can disagree if the sampling distribution is skewed (not an issue for
  the mean with large n, which is why he uses the mean).

### Ch 6 - Data-mining bias (pp.255-330)  ← the core chapter
- **Data-mining bias** = the expected gap between the observed result of the best rule and its true
  expected result. Anecdotes: a "literate" monkey chosen from a million; baseball "patterns proving
  God"; Bible codes (criteria set after the fact; the same "codes" appear in *Moby Dick*); a double
  lottery winner (1 in 17 trillion beforehand, about 1 in 30 after searching all players); the
  Bangladesh-butter vs S&P correlation of 0.70 from hundreds of UN series.
- **Why OOS results fall:** not regime change at exactly the wrong moment, not crowding, but
  randomness plus picking the best. The "decline" is the winner returning to its true level, which
  may be zero.
- Data mining is a multiple-comparison procedure (problem, candidates, figure of merit). Search
  types: parameter optimization (narrowest), rule search (different rule forms), rule induction
  (variable complexity: GA, NN, trees).
- **Data mining still pays:** with enough observations, the best observed rule *is* the most likely
  best future rule (White). Observed performance is a valid **selection** criterion but a biased
  **estimate** of the winner's future.
- Single rule: the statistic is a mean, which is unbiased. Best of N: the statistic is the
  **maximum of N means** and needs that distribution. Example: 50 useless rules, best +37 %; vs a
  single-rule distribution p < 0.05 (wrong); vs the max-of-50 distribution (centred at +33 %)
  p > 0.45.
- **Five factors that set the size of the bias:**
  1. Number of rules tested (more → bigger; roughly linear in log N).
  2. Number of observations behind the statistic (more → smaller; possibly the most important).
  3. Correlation between the rules' returns (higher → smaller, but the bias stays high until the
     correlation is near 1).
  4. Positive outliers / heavy tails (more → bigger; fixed profit targets reduce them).
  5. Spread of true merit between rules (similar merit → bigger; one clearly superior rule →
     smaller).
- **Experiments with artificial rules** (absolute S&P monthly returns, 1928-2003, signs from a
  roulette with p(gain)): all rules with ER 0, 24 months: bias best-of-2 +8.5 %/yr, of 10 +22 %,
  of 50 +33 %, of 400 +48 %. Best of 1,024: about 84 % with 10 months, under 12 % with 1,000
  months. With about 600 or more observations, best-of-10 and best-of-100 have almost the same
  bias.
- Rare good rules among many useless ones (average ER +1.4 %/yr): with 2 months per rule, mining
  is no better than a random pick (bias over 200 %/yr for best-of-256); with 100 months the bias is
  about 18 %; with 1,000 months under 3 %, and the best of 256 really is good (+10 %). The bias
  levels off after about 30 rules (100-month case). With a correlation of 0.9 between rules, the
  best of 256 is no better than a random rule.
- **Remedies:**
  - **OOS testing:** one late block, checkerboard blocks, or **walk-forward folds** (test segments
    must not overlap → independent OOS estimates → variance and CI). Limits: the OOS loses its
    virginity after one use, it takes data away from mining, and the split is arbitrary.
  - **Markowitz/Xu shrinkage:** H' = R̄ + B(H − R̄): shrink the best rule's return toward the mean
    of all tested rules; B ∈ [0,1] from the within-rule and between-rule variances, the number of
    rules and the number of observations. A rough guide only; sometimes badly wrong.
  - **White's Reality Check (bootstrap, best-of-N):** zero-centre every rule's daily returns; per
    replication draw n day indices with replacement (**the same indices for all rules**, which
    keeps the correlation), compute each rule's mean on those days, keep the **maximum**; ≥ 500
    replications; p = share of maxima ≥ the best observed mean. Gives CIs.
  - **MCP for best-of-N:** per replication, one permutation of the detrended market changes applied
    to **all** rules' position series; take the maximum mean; ≥ 500 replications; p = share ≥ the
    observed best. No zero-centring needed; no CIs.
  - Power: rules far worse than the benchmark with a huge variance (e.g. inverse rules) reduce
    power (Hansen); Masters found both tests reasonably robust for typical TA mining. The
    **Romano-Wolf stepwise** version raises power and gives **joint CIs** for all rules.
  - Both need **the full daily series of every rule ever tested**: "few data miners save this
    valuable information".

### Ch 7 - Theories of nonrandom price motion (skimmed, pp.331-385)
- A significant backtest without a theory is an isolated, possibly lucky fact; a theory makes
  persistence more believable.
- Profits as **risk premiums**, which last longer than inefficiencies that get arbitraged away:
  the hedging-risk transfer premium for trend followers in futures (MLM index: 12-month MA on 25
  commodities); a liquidity premium for buying from distressed sellers (stocks: a 2-week sharp
  drop on falling volume tends to bounce the next week); price discovery. Trend following works
  worse in stocks than in futures. Behavioural explanations: under-reaction (conservatism,
  anchoring) → trends; over-reaction → reversals.
- Trend followers lose on 50-65 % of signals; drawdowns of up to 30 % are normal.

### Ch 8 - Case study design (pp.389-440)
- 6,402 binary long/short rules on the S&P 500, 1980-11 to 2005-07, mostly driven by **other
  series** (transports, breadth, OBV, yields, spreads). About half are inverse rules.
- **Data-snooping bias** (using rules others found, with an unknown number of trials, e.g. Zweig's
  double 9:1 with three free parameters) is worse than data-mining bias. He avoided published
  rules.
- H0 for WRC: every rule's ER ≤ 0; for MCP: positions randomly paired with next-day changes.
  Alpha 0.05, set in advance. Statistical significance is not practical significance (with more
  than 6,000 days, tiny returns become significant).
- Operators: channel breakout (n-bar max/min excluding the current bar; 11 lookbacks spaced by
  ×1.5: 3, 5, 8, 12, 18, 27, 41, 61, 91, 137, 205); MA (SMA lag (n−1)/2, linear-weighted lag
  (n−1)/3; a 4-day LWMA smooths indicators before threshold rules to cut whipsaws); channel
  normalization (CN = stochastic, 0-100).
- Rule families: trend (858), extremes and transitions (12 crossing-event types × 39 series ×
  2 thresholds × 3 lookbacks = 2,808), divergence (double channel normalization, so thresholds are
  comparable across pairs; 2,736). Parameter values were not optimized. The **naming code encodes
  family-type-series-threshold-lookback**, e.g. E-4-30-20-60: a good template for a trial log.

### Ch 9 - Results and the future of TA (pp.441-475)
- **No rule significant.** The best (E-12-28-10-30, +10.25 %/yr) had WRC p 0.816; the
  distribution of the best of 6,402 useless rules is centred at about +11 %; p < 0.05 would have
  needed more than 15 %. A naive single-rule test gave p 0.0005, and about 320 rules (5 % = pure
  chance) would have looked significant.
- Top-100 table: mean return, naive bootstrap and MCP p (meaningless), adjusted significance by
  three methods, 80 % joint CIs (e.g. −5.8 % to +20.7 %).
- Done right: a no-skill benchmark, detrending, no look-ahead, data-mining correction, no snooping.
- Limits: no complex rules (Hsu & Kuan, 39,832 rules 1990-2002: only 8 % were complex but they made
  82 % of the 229 significant rules; nothing significant on the Dow or S&P, some on NASDAQ and
  Russell 2000, so less mature markets look more predictable); only always-in reversal rules
  (long/flat or tri-state would fit "occasionally inefficient" markets better); one market.
- Combining rules: equal or optimized weights; **voting** (majority within a family → one unit);
  **fractional position** ((n_long − n_short)/n); a **learning rule** (switch to the family's best
  recent rule). Leave inverse rules out of votes. There is no data-mining-robust test for complex
  rules, so use **three segments: train (parameters) / test (choose complexity: add complexity
  until the test result falls) / validation (untouched)**, which can be walked forward.
- Future: humans design indicators and targets (feature design is the key), computers mine;
  statistical models beat experts (Meehl; Grove-Meehl, 136 studies). The curse of dimensionality:
  the data needed grows exponentially with the number of indicators.

## For the application (what to build)
| Item | Source |
|---|---|
| **Detrended-return benchmark:** rule returns computed on market returns minus their mean over the test period (signals on real prices); report raw and detrended side by side; or subtract the same-bias random benchmark [p(L) − p(S)] × average change | ch.1, appendix |
| Report long/short position bias (time long vs short) for every run | ch.1 |
| Single-run significance: bootstrap (zero-centred) and MCP (position series vs shuffled detrended changes), p and percentile CI | ch.5 |
| **Best-of-N significance on a sweep / the trial log:** White's Reality Check (same bootstrap indices for all rules) and MCP-max (the same permutation for all rules); Romano-Wolf stepwise version and joint CIs as a later step | ch.6, 9 |
| **Store the full daily return series and position series of every variant tested** (the trial log must keep them, not just summaries) | ch.6 |
| Data-mining bias diagnostics: number of variants, number of observations, average correlation between variant returns (effective N), outlier share | ch.6 |
| Markowitz/Xu shrinkage of the best variant toward the average variant (rough guide) | ch.6 |
| Inverse-rule switch for any binary rule (but count it as extra trials) | ch.1, 8 |
| Naming / ID scheme encoding family-type-input-parameters for the trial log | ch.8 |
| Train / test / validation (three segments) when complexity or filters are added; can be walked forward | ch.9 |
| Statistical vs practical significance: show the effect size (R per year, net) next to p | ch.8 |
| Execution convention: decide on bar close, fill at the next bar open (already our rule; keep it) | ch.1 |

## Testable ideas (not now)
Aronson's own 6,402 rules found nothing on the S&P 500. Families that could later be applied to
our symbols: channel-breakout trend rules on *related* series (e.g. NAS100 rules driven by US500,
GBPJPY by GBPUSD); channel-normalized extreme/transition flip-flop rules; divergence rules with
double channel normalization; voting or fractional-position combinations within a family. Note
Hsu & Kuan: no significant rules on the S&P 500 or Dow.

## Warnings / pitfalls
- All returns are gross of costs and on daily S&P data before 2006.
- The bias experiments use monthly returns and independent artificial rules; real numbers differ,
  but the directions (more variants → more bias, more data → less) hold.
- Inverse rules double the trial count and reduce test power.
- Data snooping (trying rules from books or forums) cannot be corrected afterwards: count such rules
  as trials anyway.
