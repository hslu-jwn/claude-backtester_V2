# Marcos Lopez de Prado, *Causal Factor Investing: Can Factor Investing Become Scientific?* (Cambridge Elements 2023, open access)

Short: **CF**. Cite by printed page: `CF p.45`. Read 2026-11-18 by one Sonnet agent (`knowledge/reading-brief.md`), PDF in
`X:\Daten\03_Bibliothek\Trading\Tier 4`. Methods only, no trading rule.

Pages cited are the printed book pages. Pages 73-80 are references only.

## Overview

- A short methods essay, not a strategy book. Its claim is that nearly all factor-investing papers make causal claims
  (a regression with Y on X implies "X causes Y") but only test association, and never state a causal graph or a mechanism.
- The author separates two kinds of spurious finding. Type-A: noise mistaken for signal (p-hacking, backtest overfitting,
  selection under multiple testing). Type-B: a real association that is not causal (missing confounder, controlling for a
  collider or mediator, specification-searching). Type-B can happen with a single trial and gets worse with more data.
- Only a falsifiable mechanism ("X causes Y through M") lets other people attack the claim with new data and
  experiments instead of only re-running the backtest.
- Evidence ladder (p. 50): randomized trial > natural experiment > simulated intervention with a causal graph >
  observational / backtest > case study > expert opinion. A backtest is rank 4: it cannot prove or disprove a mechanism.
- The author shows with 5,000-sample Monte Carlo runs that standard regressions give significant false positives under
  fork, collider and confounded-mediator structures, and that the wrong model can have higher R-squared.
- Stance: sharply critical of academic factor investing. Offers no new trading rule. Value for us is purely methodological.

## Chapter notes

### Ch 1 - Introduction (pp. 1-2)
- Factor research is called phenomenological: it catalogues associations, never says why. The author wants "causal factor investing".
- Six contributions: causal content of factor models, type-A vs type-B taxonomy, an evidence hierarchy, Monte Carlo
  demos, an alternative reading of time-varying risk premia (under-controlling), and actions for authors.

### Ch 2 - Association vs Causation (pp. 3-5)
- Association: P(Y|X) differs from P(Y). Causation needs an intervention: P(Y | do(X=x)) > P(Y). Conditioning is not setting.
- Causal graph (DAG): the do-operation deletes all arrows into X. This is the meaning of "ceteris paribus".
- Confounder (Z causes both X and Y) creates a noncausal association (ice cream and drownings, with weather as Z).
- Five conclusions: causality is beyond statistics; causation implies association but not the reverse; causality is
  directional; it is sequential; ceteris paribus can only be understood from the graph.

### Ch 3 - The Three Steps of Scientific Discovery (pp. 6-13)
- Step 1 phenomenological (observe an association, induction). Step 2 theoretical (propose a falsifiable causal
  mechanism, abduction). Step 3 falsification (other researchers deduce implications and try to break them).
- Example mechanism (PIN theory, p. 8): order-flow imbalance -> market impact -> mid-price change -> market-maker losses
  -> wider spread -> less liquidity -> more volatility. Each link is a measurable, separately testable variable.
- Three falsification strategies (p. 9): show P(Y|do(X)) = P(Y); show a causal prediction from the mechanism fails;
  show an association the mechanism implies does not exist (no do-operation needed).
- Falsifying by "risky forecasts": predict an outcome under an intervention not yet seen. This is out-of-sample by design.
- Parsimonious theories preferred (fewer controls, easier to falsify). Complex maths or peer review does not make a claim scientific.
- Hypothesis testing logic: fail to reject H0 never proves H0. Causal claims need an experiment; associational ones do not.

### Ch 4 - Causal Inference (pp. 14-24)
- Observed difference E[Y|X=x1] - E[Y|X=x0] = ATT + self-selection bias (SSB). Randomization sets SSB to 0 (eq. 3-6).
- Interventional studies: controlled experiment, RCT (random assignment; Monte Carlo over subsamples gives uncertainty).
- Natural experiments (Nature randomizes): regression discontinuity (units just above vs just below a threshold),
  crossover (each unit is its own control; needs wash-out against carry-over), difference-in-differences (needs equal
  pre-trends; check by computing pre-treatment changes). Case-control, cohort and synthetic control are not true natural experiments.
- Simulated interventions: observational data plus an assumed graph. They cannot prove the graph, only contradict it.
- Causal discovery (p. 19-20): constraint-based (PC, FCI), score-based (GES), functional causal models (direction from
  noise independence). ML tools (MDA, Shapley) can find relevant variables first, then discovery proposes arrows.
- Do-calculus (pp. 20-24): path blocking rules. A path through a collider is blocked unless you condition on it or its
  descendants; conditioning on a non-collider blocks the path. d-separation = conditional independence.
- Backdoor criterion: adjustment set S blocks all backdoor paths and contains no descendants of X (eq. 8).
- Front-door criterion: use a mediator when the confounder is latent (eq. 9). Instrumental variable W: affects X,
  affects Y only through X, no backdoor to Y; effect = slope(Y on W) / slope(X on W).

### Ch 5 - Causality in Econometrics (pp. 25-30)
- Regressing Y on X vs X on Y gives inconsistent slopes, so least squares is directional, i.e. causal, not a statement
  about the joint distribution. Only Deming (orthogonal) regression is symmetric.
- Beta is unbiased only if the error is exogenous. Textbooks define exogeneity by construction (empty, associational);
  the explicit version needs the model to be correct, which needs a causal graph.
- Stepwise and general-to-simple specification searches are selection bias under multiple testing.
- Granger causality is only sequential association: a rooster crow "Granger-causes" dawn; a common confounder fakes
  it; lag selection is multiple testing; it is linear only. Useful at most for the direction between two unconfounded variables.

### Ch 6 - Causality in Factor Investing (pp. 31-51)
- 6.1 Causal content (pp. 32-34): choice of OLS, p-values on beta, and one portfolio per factor (long the exposure, not
  the residual) all show the authors treat beta as a causal effect to be monetized.
- 6.2 Omitted mediation analysis (pp. 34-38): standard economic rationales (risk of bankruptcy, q-theory, ...) are
  "not even wrong": no declared graph, no ideal experiment, no estimation plan. Hypothetical example (not a claim of
  accuracy): value gap (HML) -> order-flow imbalance (OI) -> price convergence (PC), with momentum (MOM) as confounder
  and bid-ask spread (BAS) as collider that must NOT be controlled; structural equations 13-15. Proposed tests per link:
  e.g. link 1 via a natural experiment on random timing of fundamental-data updates across stocks (updated vs not yet updated).
- 6.3 Causal denial (pp. 38-39): a causal claim must come with (i) a graph, (ii) a falsifiable mechanism, (iii)
  evidence for both. A mechanism lets the community falsify without relying on backtests, even if the author p-hacked.
- 6.4 Spurious factors (pp. 40-49): Bloomberg-GSAM US multi-factor index since 2007: Sharpe 0.29, t = 1.16, mean 1.13 %
  per year, before costs, borrow and fees; negative against 6-month T-bills. A Sharpe of 0.29 needs over 31 years of daily
  data to reach 95 % significance (Bailey and Lopez de Prado 2012).
  - Type-A (pp. 41-43): leading cause is selection bias under multiple testing; falls with sample size; fixable by
    multiple-testing corrections (Hochberg, deflated Sharpe, White, Romano-Wolf, FDR). With no serial correlation a type-A
    factor has zero expected return before costs. Many researcher degrees of freedom: window, frequency, quantiles,
    controls, universe, outlier rules, dates. A backtest is not an experiment; replication on other sectors / countries /
    periods does not prove causality (same noncausal association or same fluke can appear).
  - Type-B (pp. 43-49): can happen with one trial, gets stronger with more data, cannot be fixed by multiple-testing
    adjustment; it needs a causal theory.
  - Under-controlling (p. 44-46): true Y = bX + cZ + u. If Z also drives X, the estimate of b has bias equal to
    (c*d)/(1+d^2) (d = effect of Z on X). Needs both c and d nonzero. Consequence: apparent time-varying risk premium
    when the X-Z covariance drifts, while the true effects stay constant. Parsimonious explanation for factor decay.
  - Over-controlling (p. 46-47): controlling for a collider opens a backdoor path (Berkson); controlling for a mediator
    removes part of the effect. Black-box funds go from profits to losses because of this. Textbooks wrongly call extra regressors harmless.
  - Specification-searching (pp. 47-49): picking models by R-squared mixes causal discovery with adjustment.
    The right model is the one that debiases one coefficient, not the one that predicts best. A different problem from p-hacking.
  - Temporal properties (p. 49): two independent nonstationary or strongly autocorrelated stationary series look associated
    regardless of sample size (spurious regression). Unit-root tests fix residuals, not causal specification.
- 6.5 Hierarchy of evidence (pp. 49-51, Figure 12): see Overview. "Out-of-sample" is not an evidence type: it helps
  against type-A only, not type-B (a stock-bond correlation seen out of sample is still not a causal link). Absence of
  the implied association does falsify causation (modus tollens): no association, no cause.

### Ch 7 - Monte Carlo Experiments (pp. 52-63)
- 7.1 Fork (Z -> X, Z -> Y; 5,000 normal draws): regressing Y on X alone gives a significant beta although X has no
  effect; adding Z removes it. Code in Appendix B.1.
- 7.2 Collider (X -> Z <- Y, X and Y independent): Cov(X,Y) = 0, but conditioning on Z gives Cov(X,Y|Z) = -1/3 (proof in
  A.2). Regressing Y on X and Z gives a significant X. The wrong model also has higher R-squared.
- 7.3 Chain with confounded mediator (X -> Z -> Y, W -> Z, W -> Y): controlling for Z gives a significant but misleading
  X effect ("mediation fallacy", Simpson-type). Correct model Y on X alone: adjusted R-squared 0.144 vs 0.784 for the wrong
  one; F-stat 840.8 vs 9,069. So R-squared-driven selection picks the wrong model.
- 7.4 Fama-French / Carhart critique: no trial count reported, specs justified by explanatory power, macro confounders
  (business cycle, inflation, yield-curve slope) omitted, momentum-value interaction, no mechanism; plus a plausible
  collider (book-to-market is caused by both size and returns), which could make the size factor a false discovery.
  Controlling for momentum swaps confounder bias for multicollinearity; backdoor adjustment is better than adding a regressor.
  The burden of proof for the graph lies with the claimant. Note this is an argument, not a measured result.

### Ch 8 - Conclusions (pp. 64-68)
- Why theory matters: curbs type-A (fewer choices), allows correct risk/performance attribution, enables counterfactual
  stress tests.
- Eight benefits of a causal factor (p. 67-68): efficiency, interpretability, transparency, reproducibility,
  adaptability (robust to changes outside the causal path), extrapolation (survives black swans, e.g. PIN-based liquidity
  strategies in the 2010 flash crash), surveillance (watch the mechanism weaken before a statistical break test fires; basis
  for factor timing and sizing), improvability.
- Industry incentives (Harvey 2022): associational studies are cheaper to produce, so they dominate.

### Appendix (pp. 69-72)
- A.1 proof of the bias formula; A.2 proof of the collider covariance -1/3; B.1-B.3 short Python snippets
  (numpy + statsmodels, seed 0, n = 5,000) for fork, collider, confounded mediator. Easy to reuse as unit tests.

## Topic tags

- testing-and-robustness/overfitting (the core of the book)
  - A backtest is associational evidence only; it cannot prove a mechanism (p. 42-43).
  - Always report and correct for the number of trials (deflated Sharpe, Hochberg, White, Romano-Wolf, FDR);
    medicine logs all trials by law (p. 42).
  - Replication on other assets or periods does not show causality (p. 43).
  - Sharpe 0.29 needs 31+ years of daily data for significance: small effects need very long samples (p. 41).
  - Do not choose models by R-squared; a correct model can have much lower fit (pp. 47-48, 60).
  - Spurious regression with persistent series (p. 49).
- portfolio/diversification
  - Factors are combined for diversification, not for a joint prediction (p. 33).
  - Multi-factor index Sharpe 0.29 over 15 years, before costs (p. 40).
- costs/execution
  - The factor index return of 1.13 % per year is before costs, impact, borrow and fees; negative vs T-bills (p. 40).
- seasonality/time
  - Time-varying risk premia can be an artefact of drifting covariance between intended and unintended exposure (p. 45).
  - Regression-discontinuity and diff-in-diff designs use timing/threshold rules (pp. 17-18).
- position-sizing/risk
  - Causal mechanism monitoring could drive dynamic sizing and factor timing (p. 68).
- psychology/discipline
  - Industry incentives push toward associational, cheap studies (pp. 66-67).
- Trend, breakout, mean-reversion, momentum/oscillators, patterns, intraday/sessions, volatility, stops-and-exits:
  not covered (momentum and value appear only as examples of confounded factors).

## Testable ideas

The book gives no tradable rule. Everything below is a market-structure test it motivates, or a method change.

### Strategy-type ideas

**Natural experiment on a forced flow: index-event timing (RDD)** - Pick an event where a counterparty must trade by a
mechanical threshold (index inclusion cut-off by market cap rank, Russell-type reconstitution, ETF creation). Compare
returns of units just above vs just below the threshold over a fixed window (RDD, p. 17). Use the threshold as the
assignment variable; no free parameters except bandwidth, which is pre-registered. - Ch 4.2 (p. 17), Ch 6.2 (p. 37, link-1
natural experiment idea). - Author claims none for this; it is a design pattern. - Fit: daily US shares (Alpaca, 2015+)
fit if the cut-off dates and rank data are available (rank is not in our data; market cap would need a proxy); long
horizons avoid the intraday cost wall; short stock borrow cost is an issue for the below-threshold leg (use long-only
contrast against a matched benchmark). - Differs: the identification is the threshold, not a price pattern.

**Difference-in-differences on a scheduled flow: Treasury month-end extension** - Treated unit: 10-year Treasury futures
in the last 3 days of the month; control: a similar asset not subject to index extension (e.g. 2-year, or the same
bond in non-month-end windows of the same calendar day-count). Effect = (month-end window return minus normal window)
for treated minus the same for control. Check pre-trends in earlier windows (p. 18). - Ch 4.2. - No author claim. -
Fit: good; FRED yields plus Yahoo 10y futures exist; no swap issue on futures; tests that the effect is the extension
flow and not a general calendar effect. - Differs from failed strategies: no price-pattern entry; mechanism and control group are named.

**Crossover test for the crypto taker-flow sort** - Strategy 20: the flow signal is "treated" in some weeks and its
influence is "removed" (signal shuffled or lagged) in matched weeks for the same coin; compare each coin to itself
(crossover design, p. 17). Needs a wash-out gap between periods. - Ch 4.2. - No author claim. - Fit: good (weekly,
perps, funding costs known). - Differs: removes coin-level confounders by self-control.

**Negative-control / placebo implication check** - From the mechanism ("index funds must buy at month end") deduce
an association that must be absent elsewhere (e.g. no effect when fund flows are known to be zero, or on assets that
are not in the index). Show the effect disappears. This is falsification strategy 3 (p. 9) and the modus tollens
rule (p. 51). - Ch 3.3, 6.5. - Fit: good, cheap, uses data we already hold. ★

**Order-flow imbalance mechanism chain** (PIN-style, p. 8) - With Binance taker-flow data test the chain link by link:
taker imbalance -> next-bar return (impact) -> funding / basis change -> later reversal. Pre-register one test per link.
- Ch 3.2. - Author claims the mechanism is a valid example; no numbers. - Fit: good on crypto perps (we have taker flow,
prices, funding); no L2 book so spread links cannot be tested. - Differs: tests the mechanism before any trading rule.

### Method ideas (how our tests should change; C = causal, not the sweep's M rules)

★ **C1. Causal graph card per hypothesis** - Before any data look, write the DAG (treatment X, outcome Y, confounders,
mediators, colliders) and the mechanism M with one measurable check per link, next to the pre-registered gates. Gate:
a strategy spec without a graph and without a stated "adjustment set" is not allowed to reach the one-time test.
Applies: Ch 6.3 (p. 39), Ch 3.2.

★ **C2. Control list rule: no collider or mediator controls** - In every regression or risk-adjusted test (market beta,
vol, size, momentum controls) check whether each control is caused by X or by both X and Y. Examples for us: controlling for
volatility or for same-period returns when the signal itself drives volatility; controlling for "traded volume" when
volume is caused by both flow and return. Reject controls chosen only because they raise R-squared. Adjustment set is
chosen from the graph (backdoor criterion, p. 22). Applies: Ch 6.4.2.2-3, 7.2-7.3.

★ **C3. Simulation unit tests for our own estimators** - Use the three 5,000-sample generators (fork, collider,
confounded mediator, pp. 53-60, code B.1-B.3) as regression tests of our scorecard/test code: our tooling must report
"no effect" with the correct specification and must not flag significance only after adding the wrong control.
Extend with the opposite case (a true effect we must recover). Cheap and deterministic with a seed.

★ **C4. Two spuriosity checks in the verdict language** - Add to the three verdicts: type-A check (trial-count
adjusted t, deflated Sharpe, ledger) and a separate type-B check (graph declared, confounders listed with their proxies
tested, collider controls absent). "Passed" needs both. Type-B cannot be fixed by raising the t threshold, and it gets
more likely as the sample grows, so a large-sample pass does not reduce the type-B burden (p. 43).

**C5. Power / required-sample reasoning** - Use the book's example: Sharpe 0.29 daily needs 31+ years for 95 %.
Add to the power check a "years to significance" line (Bailey and Lopez de Prado 2012 formula, not given in this book)
and refuse ideas whose annual Sharpe under shrinkage would need more history than we have. Applies: p. 41.

**C6. Hierarchy-of-evidence label on every result** - Tag each result: natural experiment (flow with a threshold or a
random timing), simulated intervention (graph + adjustment), or observational backtest. Weight priority toward the first
two; treat observational as unproven-positive at best. Applies: Fig. 12, p. 50.

**C7. Mechanism-surveillance gate** - For passed streams (crypto taker-flow sort, month-end extension) define a
live monitor of the mechanism variable itself (e.g. index-fund AUM growth, flow size) rather than only a drawdown stop;
decay of the mechanism is detectable before the P&L break (p. 67-68). Needs data on the flow; for Treasury month-end
this could be duration of the benchmark index or fund assets if free data exist.

**C8. Spurious-regression guard** - For any regression of levels on levels (yields, VIX, COT positions, funding),
test stationarity and use changes or returns; compare with a persistent-series null (random walk pairs) so we know the
spurious t-stat level for our own series (pp. 49). Add to the testing checklist.

**C9. Do not use Granger tests as evidence of mechanism** - If used at all, only to choose the direction between two
unconfounded series (p. 28-29). Never as a gate. Includes COT-vs-price lead-lag claims.

**C10. Placebo and negative-control tests as a standard gate** - For each mechanism, list the implied absence (assets
or dates where the counterparty is not forced) and test that the effect is gone. Applies: p. 9, 51.

**C11. Replication on other markets is not causal evidence** - Do not count "works on another asset class" as
causal support; count it only as protection against type-A. Applies: p. 43.

## Warnings / pitfalls

- Backtest outcome is one more associational claim; it proves neither mechanism nor causality (pp. 42-43, 64).
- Reporting only the best of many specs (window, frequency, quantiles, universe, dates, outlier rules) is p-hacking;
  trials must be logged and corrected (p. 41-42).
- Adding every available control is not safe: colliders and mediators bias the estimate and can flip the sign (pp. 46-47,
  55-60). Textbook advice that irrelevant regressors are harmless is wrong in causal terms.
- Choosing a model by R-squared or F-stat favored the wrong, biased model in the experiments (adjusted R-squared 0.784
  vs 0.144 for the correct one, p. 60).
- Time-varying premia and "factor decay" may come from a missing confounder whose covariance with the factor changes,
  not from real change in the premium (p. 45). Black-box strategies can switch from profit to loss without any warning (p. 47).
- Out-of-sample helps against type-A only; it is not evidence of causality (p. 51).
- Nonstationary or highly persistent series produce spurious associations at any sample size (p. 49).
- Granger causality is not causality; it fails under common confounders and is multiple-testing prone (pp. 28-29).
- Multicollinearity can amplify bias when the specification is wrong (p. 48, note 34).
- Weak evidence level: factor index Sharpe 0.29, t 1.16, before costs, over 15 years (p. 40). Small edges need decades.
- Limits of the book itself: no method here proves a mechanism from observational data; simulated interventions assume the
  graph is right and can only refute a graph, not confirm it (p. 19). The hypothetical HML-OI-PC graph is illustrative, not
  tested. The critique of Fama-French is an argument by structural possibility, not an empirical re-estimation.
