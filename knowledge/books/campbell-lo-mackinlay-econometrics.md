# Campbell, Lo and MacKinlay, *The Econometrics of Financial Markets* (Princeton University Press, 1997)

Short: **CLM**. Read 2026-11-18 by Codex; PDF in the library folder Tier 4.

The book surveys econometric methods for financial prices and returns, including return predictability, market microstructure, event studies, asset-pricing models and nonlinear data analysis (CLM pp. 4–5). For this project, its strongest contribution is guidance on designing event studies, assessing statistical power, and identifying apparent effects caused by trading frictions or repeated searches (CLM pp. 101–102, 150–178, 523–524).

## Testable ideas

No idea selected. The reviewed sections did not give a sufficiently specified trading rule **and** a measured return size that met the brief. The earnings-announcement example measures announcement-related abnormal returns, but its classification uses announced earnings versus forecasts and does not establish an executable entry and exit rule (CLM pp. 152–153, 166).

## Method notes

- **Define event timing and sample selection first.** Specify the event, the price window, the universe and exclusions; describe the distribution of events through time and potential selection biases (CLM p. 151).
- **Keep estimation and event windows separate.** The book gives 120 prior days as an example for estimating a daily market model and normally excludes the event window so event returns do not influence the normal-return estimate (CLM p. 152).
- **Abnormal returns need a counterfactual.** The book defines them as actual return minus expected normal return and discusses both a constant-mean model and a market model. Check whether conclusions depend on the model selected (CLM pp. 151, 166).
- **Do not automatically infer causation from an event return.** The standard interpretation assumes the event is exogenous; it can fail when the price change itself triggers the event (CLM pp. 157–158).
- **Account for uncertainty in the normal-return model.** Estimation error adds variance and can induce serial correlation among measured abnormal returns even when the underlying disturbances are independent (CLM pp. 159–160).
- **Handle calendar clustering.** Overlapping event windows can produce cross-security dependence. The book discusses an event-time portfolio approach and a multivariate approach, while noting finite-sample and power limitations of the latter (CLM pp. 166–167).
- **Calculate power for the intended effect and sample.** In the book’s illustrative 5% test, a 0.5% abnormal return with 2% standard deviation and 20 events has power of only 0.20; its calculations depend on the stated distributional assumptions (CLM pp. 168–169, 171–172).
- **Balance window length against event-date certainty.** Shorter windows can improve power when timing is known, but intraday microstructure complicates inference; uncertain dates may require a wider window to avoid missing the event (CLM pp. 175–177).
- **Use nonparametric checks with care.** Sign and rank tests can supplement parametric tests; the sign test’s assumed 50% positive-return probability can fail for skewed abnormal returns (CLM pp. 172–173).
- **Check thin trading and stale prices.** Closing prices can reflect transactions at different times, biasing return moments and market-model betas; the book reports that adjustments were generally smaller for actively traded securities (CLM p. 177).
- **Treat bid–ask bounce as a potential artifact.** Alternating transaction prices at bid and ask can create negative short-run price-change autocorrelation even when the underlying value is unchanged (CLM pp. 101–102).
- **Distinguish quoted from effective spread.** The Roll estimator relies on restrictive assumptions and is undefined in its usual form for positive return autocovariance. The book cautions that many empirical estimates indicated model specification problems (CLM pp. 102, 134–135).
- **Be wary of long horizons relative to the sample.** Standard variance-ratio approximations can perform poorly when the return horizon is a large fraction of the available history, including severely reduced power against some alternatives (CLM pp. 57–58).
- **Count specification searches.** Overfitting can produce strong in-sample results; repeated searches can also produce misleading out-of-sample success. The book recommends disciplined prior specifications, appropriate corrections where available, and limited or weakly correlated out-of-sample evaluations (CLM pp. 523–524).

## Verdict

No **NEW** idea from the reviewed sections merits a strategy card under the requested standard of an executable rule, mechanism and stated return size. The book is valuable as a methods reference: its event-study power examples quantify detectability under explicit assumptions, while its microstructure and data-snooping discussions explain why an apparently significant price effect may not be tradable or robust (CLM pp. 101–102, 168–172, 523–524).

