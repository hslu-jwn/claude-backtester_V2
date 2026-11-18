# Ralph Vince, *The Mathematics of Money Management: Risk Analysis Techniques for Traders* (John Wiley & Sons, 1992)

Short: **MMM**. References use printed pages (`MMM p.N`). Read 2026-11-18 by Codex; PDF in the library folder Tier 4.

The book studies position sizing and portfolio allocation for trading systems, especially fixed-fractional sizing and the author’s “optimal f.” It moves from empirical trade sequences to fitted return distributions, portfolio correlations, and risk controls. Its examples are largely hypothetical or sizing exercises, rather than measured market effects. Several statistical and optimization claims need care before use in research. (MMM p.9, p.49, p.73, p.88)

## Testable ideas

None identified that combine a market entry and exit rule with a stated empirical effect size. The numerical examples examined concern hypothetical wagers, trade-distribution fitting, or portfolio sizing; they do not establish a tradable market effect in basis points per event or day. (MMM p.29–30, p.54, p.88)

## Method notes

- **Test dependence in more than one way.** A runs test examines the sequence of wins and losses; serial correlation examines the relationship between trade outcomes. A lack of dependence in signs does not establish independence of outcome sizes. (MMM p.10–12)
- **Check apparent dependence out of sample.** The author suggests splitting data and checking whether a relationship found in one segment also appears in another. Changing rules to exploit an in-sample pattern risks fitting noise and then sizing too aggressively. (MMM p.12)
- **Keep models parsimonious.** The book recommends minimizing adjustable parameters and extra qualifications, and looking for behavior that persists across markets. This is a useful robustness principle, though simplicity alone does not prove future profitability. (MMM p.13)
- **Estimate expectancy after costs before sizing.** Position sizing cannot turn a negative-expectancy standalone system into a positive-expectancy one; commissions and slippage matter when estimating the edge. Portfolio interactions are a separate question. (MMM p.13)
- **Separate arithmetic returns from compounded growth.** With reinvestment, dispersion affects geometric growth, so average trade profit alone does not describe the growth of an account. (MMM p.14–17)
- **Treat historical optimal f as a fitted estimate.** The empirical calculation finds the fraction that would have maximized geometric growth on the observed trades; that is not knowledge of the future distribution. (MMM p.16, p.60)
- **Stress the largest loss.** The book notes the sensitivity of sizing to the largest observed losing trade. A historical maximum loss is not a reliable bound on future losses. (MMM p.30)
- **Compare growth and drawdown at the same risk level.** A higher geometric mean by itself does not establish a lower drawdown. Fractional sizing changes both growth and risk, so comparisons should specify the fraction used. (MMM p.30)
- **Distinguish a growth-rate calculation from a first-passage estimate.** The book uses `ln(goal)/ln(geometric mean)` as an expected number of trades to a target; that calculation should not be treated as a validated expected time to first reach the target under variable returns. (MMM p.29–30)
- **Test distribution and tail assumptions.** In the book’s 232-trade example, changing distribution bounds produces materially different optimal sizing estimates. The result illustrates model sensitivity, not evidence that either estimate is correct. (MMM p.54)
- **Use goodness-of-fit tests cautiously.** The book describes the Kolmogorov–Smirnov distance between empirical and theoretical cumulative distributions. Its statement that a high test result gives the probability that the theoretical distribution generated the data is not a valid interpretation of a p-value. (MMM p.49)
- **Preserve tail information when binning.** Replacing trade outcomes with bin midpoints can materially distort sizing, particularly if a large loss shares a wide bin with smaller losses. (MMM p.60)
- **Consider sample size and assumptions together.** The book’s binomial illustration highlights how many observations may be needed to distinguish a small win-rate edge; it assumes independent trials, two outcome categories and a constant success probability. Win rate alone also does not establish profit when payoff sizes differ. (MMM p.100–101)
- **Model simultaneous exposures and margin.** Portfolio sizing depends on combinations of positions, not just each system in isolation; margin can constrain an otherwise theoretical allocation. (MMM p.28, p.95)
- **Do not infer safety from sparse overlap.** The book observes that two related markets can show little measured strategy-return correlation simply because their trades have not coincided; future simultaneous exposure can be different. Its proposed manual correlation adjustment is a judgment to stress-test, not an observed fact. (MMM p.96)

## Verdict

There are **no NEW market-effect cards** from the material examined: the book provides useful sizing and testing questions, but the examples reviewed do not supply both a forced-trading mechanism and an empirical effect size. Its strongest contribution to this project is as a checklist for dependence, overfitting, tail sensitivity, compounding, and portfolio constraints; its optimal-f prescriptions and statistical interpretations should not be adopted uncritically. (MMM p.12–13, p.49, p.54, p.96)

