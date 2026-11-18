# Marcos M. López de Prado, *Machine Learning for Asset Managers* (Cambridge University Press, 2020)

Short: **MLAM**. Read 2026-11-18 by Codex; PDF in the library folder Tier 4.

The book presents machine learning as a set of tools for developing and testing financial theories. It covers financial labels, feature importance, clustering, portfolio allocation, and the effects of repeated testing. Its central argument is that a backtest needs a testable explanation of the economic mechanism behind an edge (MLAM p.2). Much of its numerical evidence concerns controlled simulations of statistical methods rather than measured trading returns.

## Testable ideas

No concrete trading rule with a stated, generalizable effect size was identified in the relevant chapters. The book describes an order-flow response around the 2010 flash crash, but it does not give an exact, reproducible entry and exit rule or a strategy return suitable for a research card (MLAM pp.2–3).

## Method notes

- **Start with a mechanism.** Formulate a testable explanation for who supplies the edge, including cases in which the effect should be absent. The author regards a historical backtest as evidence, not a theory (MLAM p.2).
- **Separate training-set and test-set overfitting.** Repeatedly adjusting a strategy after inspecting its test performance selects for favorable noise. Track the research trials behind a selected result, not just the final run (MLAM pp.8–9).
- **Treat synthetic tests as conditional evidence.** Resampling and Monte Carlo produce alternative paths, but conclusions depend on whether the sampled or estimated process represents the relevant market behavior (MLAM p.9).
- **Match labels to the decision.** Predicting a fixed-horizon return and predicting which price barrier is reached first are different tasks; a feature useful for one need not predict the other (MLAM pp.65–67).
- **Account for the path of a trade.** The triple-barrier label records the first of profit target, loss limit, or maximum holding period. It captures information that a return measured only at a fixed horizon misses (MLAM pp.66–67).
- **Separate direction from size.** Meta-labeling trains a secondary model on the outcomes of a primary model, with the aim of filtering false positives or informing size. The book’s sizing formula assumes symmetric payoffs and additional distributional assumptions; it is not automatically valid for asymmetric trading outcomes (MLAM pp.69–70).
- **Do not equate a p-value with effect size or the probability that a hypothesis is true.** Its interpretation depends on the specified statistical model; repeated in-sample testing and correlated explanatory variables add further problems (MLAM pp.75–76).
- **Measure feature importance out of sample.** Mean-decrease accuracy compares cross-validated performance before and after a feature is shuffled. Correlated features can substitute for one another and make each appear less important (MLAM pp.81–82).
- **Inspect related features as groups.** Clustered feature importance evaluates groups of similar features together to reduce substitution effects; it remains a tool for investigating a mechanism, not proof of causation (MLAM pp.84–85, 90).
- **Check portfolio stability and turnover.** Mean-variance allocations can be unstable when covariance matrices are poorly conditioned; small changes in observations may produce different weights and transaction costs (MLAM pp.92, 103).
- **Consider clustered allocation as a robustness comparison.** Nested clustered optimization first allocates within clusters and then across them. The book reports lower allocation estimation error in its experiments, but recommends evaluating methods for the inputs at hand (MLAM pp.98–100, 103–104).
- **Correct for selection among trials.** The book’s false-strategy theorem models the expected maximum Sharpe across independent Gaussian trial estimates; its result depends on both the number of trials and their dispersion. Those assumptions matter when applying it to correlated strategy variants (MLAM pp.108–109).
- **Estimate multiplicity carefully.** The deflated Sharpe approach incorporates sample length, skewness, kurtosis, and a multiple-testing adjustment. The book proposes clustering trial returns to estimate an effective number of independent trials; that estimate is itself model-dependent (MLAM pp.113–114).
- **Plan for power as well as false positives.** A stricter familywise error threshold can make a real but weak strategy harder to detect. The book’s power calculations depend on the assumed Sharpe, sample length, return moments, and test structure (MLAM pp.119–120).
- **Preserve dependence in resampling where appropriate.** The appendix distinguishes resampling from model-based Monte Carlo and describes block bootstrap as a way to retain serial dependence within sampled blocks (MLAM p.125).

## Verdict

No **NEW** trading idea from the reviewed sections has both a reproducible rule and a stated effect size sufficient for a card. The strongest value for this project is methodological: recording the full trial history, testing selection bias and power, matching labels to actual trade outcomes, and checking allocation stability. The book’s simulation results support investigation of those methods; they do not establish a venue-specific trading edge.

