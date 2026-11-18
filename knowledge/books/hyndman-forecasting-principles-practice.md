# Hyndman and Athanasopoulos, *Forecasting: Principles and Practice*, second edition (publisher not stated in supplied text, 2018)

Short: **FPP**. Read 18 November 2026 by Codex; library tier: 4.

The supplied text is an online second-edition copy, last updated 5 September 2018. It has no identifiable printed page numbers, so the references below use its section numbers rather than invented page citations. The book introduces time-series forecasting, from simple benchmarks and diagnostics to model selection, prediction intervals and practical data problems. Its examples use R. (FPP, Preface)

## Testable ideas

None. This is a forecasting-methods book; the sections reviewed do not establish a trading mechanism and a return size per event or day.

## Method notes

- **Separate fitting from evaluation.** Assess forecasts on observations not used to fit the model; a close training fit can coexist with poor forecasts. The book says the test period should ideally be at least as long as the maximum forecast horizon. (FPP §3.4)
- **Use rolling forecast origins.** At each origin, train only on earlier observations and score the subsequent forecast. Evaluate the horizon relevant to the intended use, including multi-step horizons. (FPP §3.4)
- **Distinguish residuals from forecast errors.** The book defines residuals on the training set, generally for one-step forecasts; test-set forecast errors can cover multiple steps. They answer different evaluation questions. (FPP §3.4)
- **Choose the error metric deliberately.** MAE targets the conditional median and RMSE the conditional mean. Neither is a direct measure of trading profitability or loss-limit breaches. (FPP §3.4; trading application is an inference)
- **Treat percentage errors cautiously near zero.** MAPE is undefined at zero and unstable near zero; the book also advises against sMAPE. Scaled errors offer a comparison against a naïve training-set benchmark. (FPP §3.4)
- **Inspect residual behaviour.** Check mean, autocorrelation, variance and distribution. Normality and constant variance make conventional interval calculations easier, but are not necessary conditions for useful point forecasts. (FPP §3.3)
- **Test interval coverage out of sample.** The book reports that nominal 95% ETS prediction intervals provided only **71%–87%** coverage in the cited study. It identifies innovation, parameter, model-selection and changing-process uncertainty as distinct sources. This is a warning for tail-risk modelling, not a calibrated prop-firm breach estimate. (FPP §11.4)
- **Match resampling to dependence.** Residual bootstrapping assumes uncorrelated forecast errors and that future errors resemble past errors. For autocorrelated remainders, the book describes a block bootstrap using contiguous sections. (FPP §§3.5, 11.4)
- **Investigate extreme observations before replacing them.** An outlier may be an error or a genuine unusual event carrying information about the process. Removing genuine extremes can be especially consequential when evaluating losses. (FPP §12.9; loss application is an inference)

## Verdict

No new trading idea warrants a card from the sections reviewed: the book supplies forecasting and evaluation methods, not a stated trading effect with a counterparty mechanism and return size. Its most useful contribution here is the warning that apparent forecast accuracy and nominal prediction intervals can understate out-of-sample uncertainty. It does not provide a specific drawdown or prop-firm loss-limit method in the sections reviewed.

