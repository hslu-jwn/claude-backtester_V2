# McNeil, Frey and Embrechts, *Quantitative Risk Management: Concepts, Techniques and Tools*, revised edition (Princeton University Press, 2015)

Short: **QRM**. Cite by printed page (`QRM p.N`). Read 2026-11-18 by Codex; PDF in the library folder Tier 4.

The book presents statistical methods for measuring and managing financial risk. It covers the empirical properties of returns, time-series and extreme-value models, dependence, risk aggregation, and applications to market and credit risk. Its market-risk chapter develops historical simulation and evaluates risk forecasts against realized losses (QRM pp.79–80, 135, 299, 342–43, 351–52).

## Testable ideas

None. This is a methods note; no trading-rule idea is proposed.

## Method notes

- **Model volatility and extremes as time-varying.** Returns may have little serial correlation while absolute or squared returns are serially correlated; volatility varies and extreme returns cluster. Independent trade or return resampling can therefore miss an important feature of loss sequences (QRM pp.79–80).
- **Use drawdown alongside one-period loss measures.** The book describes maximum drawdown as a peak-to-bottom loss over a period. For a prop-firm simulation, this motivates tracking the account path in addition to a one-day loss distribution; the specific firm’s breach rules must still be implemented separately (QRM p.78).
- **Distinguish VaR from the severity of tail losses.** VaR is a loss-distribution quantile; expected shortfall addresses losses in the tail beyond that quantile. Reporting both gives more information than a breach threshold alone (QRM pp.64, 69, 354).
- **Historical simulation applies past risk-factor changes to the current portfolio.** It preserves the historical joint scenarios without explicitly estimating a multivariate dependence model, but its basic form is unconditional and needs sufficient relevant, synchronized history, including extreme observations (QRM pp.342–43).
- **Consider conditional risk forecasts.** Dynamic historical simulation combines historical scenarios with volatility forecasts to reflect changing risk. Such forecasts need out-of-sample evaluation rather than an assumption that a more complex model is better (QRM pp.343–44, 351–52).
- **Do not assume square-root-of-time scaling always works.** The book derives it under independent, identically distributed Gaussian risk-factor changes and a linear loss model, then notes that those assumptions generally do not fit empirical data. Simulating paths is an alternative for multi-period loss estimates (QRM pp.350–51).
- **Evaluate forecasts using only information available when made.** Compare each risk estimate made at time *t* with the subsequently realized loss, repeating the comparison out of sample (QRM pp.351–53).
- **Check both VaR breach frequency and timing.** Under the book’s continuous-distribution and correct-conditional-forecast assumptions, violations have the specified probability and are independent. A plausible total breach count alone can miss clustered violations (QRM pp.352–53).
- **Treat overlapping forecast horizons carefully.** Overlapping multi-period losses produce dependent violation indicators, complicating formal tests. Non-overlapping observations avoid that issue but leave fewer observations (QRM p.354).
- **Check breach magnitude as well as count.** The book describes an expected-shortfall backtest based on residuals for VaR violations, with a t-test or bootstrap under the stated model assumptions (QRM pp.354–55).
- **Score forecasts according to the quantity forecast.** The book uses squared error for conditional means and a quantile-consistent score for VaR; these provide a basis for comparing competing forecasts out of sample (QRM pp.355–57).
- **Evaluate the predictive distribution as well as individual tail measures.** Under the book’s assumptions, probability integral transforms of realized losses using correctly specified conditional distributions should behave as independent uniform observations; the book suggests checking both their distribution and dependence (QRM pp.363–64).

## Verdict

No **NEW** trading idea is proposed: the selected material supplies risk-measurement and forecast-evaluation methods, rather than a forced-flow mechanism with a stated return size worth a strategy card. The most directly useful material for the project is path-based drawdown measurement, conditional loss forecasting, and out-of-sample checks of breach frequency, clustering and severity (QRM pp.78, 343–44, 351–55).

