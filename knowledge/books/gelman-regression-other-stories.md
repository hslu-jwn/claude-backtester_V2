# Gelman, Hill and Vehtari, *Regression and Other Stories* (Cambridge University Press, 2020)

Short: **ROS**. Cite by printed page (`ROS p.N`). Read 2026-11-18 by Codex; PDF in the library folder Tier 4.

The book explains regression as a tool for description, prediction and causal inference. It covers uncertainty, simulation, model building and diagnostics, then moves to study design and causal inference. Its examples show how noisy estimates, selection and model assumptions can mislead. For trading research, its strongest contribution is to evaluating purported effects rather than proposing trading rules. (ROS pp. 49, 81, 153, 291, 383)

## Testable ideas

None: the selected sections provide statistical methods, not a trading rule with a market mechanism and measured trading effect.

## Method notes

- **Estimate magnitude and uncertainty together.** An interval can show whether the data are consistent with economically meaningful gains or losses; failure to reject zero does not establish that an effect is negligible. For trading, compare the interval with costs as well as zero. (ROS p.58)
- **Expect selection to exaggerate noisy winners.** Selecting estimates because they pass a significance threshold favors large observed effects. The authors distinguish errors of sign from exaggeration of magnitude; both can be severe when signal is small relative to noise. (ROS pp.59, 62)
- **Design around plausible effects, not a hoped-for significant result.** Before a study, examine likely estimation error and sign or magnitude errors over plausible effect sizes. The book’s illustrative low-power example shows why an apparently significant result can be misleading. (ROS pp.291–292)
- **Use fake-data simulation to check the research procedure.** Generate data with known parameters, fit the intended model repeatedly, and check whether estimates and uncertainty intervals behave as expected. For trading, make the simulated data reflect the features relevant to the proposed test. (ROS p.161)
- **Consider regularization when data are sparse.** Weakly informative priors can constrain implausible estimates; their scale and assumptions need justification. The book also discusses partial pooling of coefficients as an alternative to choosing a small subset solely by predictive score. (ROS pp.123–124, 180)
- **Separate uncertainty about the average from uncertainty about a new outcome.** A future trade or event varies around the conditional mean, even if the mean is estimated precisely. Use a predictive distribution when assessing individual future outcomes. (ROS p.115)
- **Check whether the data match the question.** Outcome measurement, relevant predictors and generalization to the intended population matter. In trading, this means checking whether the sampled instruments, period and measured returns represent the intended application. (ROS pp.153–154)
- **Inspect residuals and simulated replications.** Residual plots can reveal systematic misfit; compare replicated datasets from the fitted model with observed data to find features the model fails to reproduce. (ROS pp.161–163)
- **Validate in the direction of intended use.** In-sample prediction is optimistic. The authors identify leave-future-out validation as useful for time series; for trading, train on the past and evaluate on later observations. (ROS p.172)
- **Treat model selection itself as uncertain.** The highest cross-validation score need not be the best final choice; the authors discuss model averaging, differences between sample and target population, and regularized model expansion. (ROS p.180)
- **Distinguish association from causation.** An observational causal interpretation requires assumptions about assignment conditional on measured confounders; the book stresses that one cannot prove from the data that all relevant confounders were measured. (ROS pp.388–389)
- **Avoid casually adjusting causal regressions for post-treatment variables.** They can change the interpretation of the treatment coefficient, even if they improve prediction. Define the causal question and the timing of variables first. (ROS pp.180, 374)
- **Beware regression to the mean in before-and-after comparisons.** An extreme observation can be followed by a less extreme one without the intervention causing the change. This matters when evaluating rules selected after exceptional returns. (ROS p.87)

## Verdict

No **NEW** trading idea with a market mechanism and stated size emerged from the selected sections, so none merits a strategy card. The book is useful instead as a methods reference for noisy effect estimates, selection bias, simulation, validation and causal claims.

