# Rishi K. Narang, *Inside the Black Box*, third edition (Wiley, 2024)

Short: **IBB**. Read 2026-11-18 by Codex.

The book explains the components of quantitative trading systems: alpha, risk, transaction costs, portfolio construction, execution, data, and research. It surveys broad strategy families and the risks of fitting models to historical data. It is primarily a framework for understanding quant trading, rather than a collection of fully specified, measured effects. (IBB, contents; §§3.2, 9.3)

**Citation limitation:** The supplied text does not expose reliable printed page numbers. Its form-feed breaks are present, but ordinary page numbers are absent; counting those breaks would not establish printed pages. I therefore use section references below rather than inventing `IBB p.N` citations. The PDF’s library location was not verified.

## Testable ideas

The book’s descriptions below are **NEW** relative to the supplied list of judged families, but they are incomplete research leads, not executable rules.

- **Equity issuance and buyback supply** (IBB §3.2.2.3): The author says secondary offerings, new issuance, and buybacks can generate signals for the issuing shares. The proposed mechanism is a change in the supply of shares; the book does not specify a trade direction, entry, exit, holding period, or universe. **No size or sample given.** Testing would require point-in-time issuance and buyback event data and daily share prices; venue: real US shares. **NEW.**

- **Bond auction and issuance signals** (IBB §3.2.2.3): The author suggests that new bond issuance and auction data can forecast bond prices. The relevant flow is new supply, but the book gives no exact signal, entry, exit, holding period, or universe. **No size or sample given.** Testing would require historical auction and issuance data plus corresponding bond or Treasury futures prices; venue: exchange futures if a suitable contract and futures cost model are used. **NEW.**

## Method notes

- Record when data became available to the strategy, rather than assuming that an observation was available on the date it describes; asynchronous data can introduce lookahead. (IBB §8.4)
- Separate model fitting from out-of-sample testing. Revising a model in response to its test-period results makes that period part of the development process. (IBB §9.3.4)
- Inspect the equity curve, several drawdowns and their recovery times, rather than relying on average return alone. A historical maximum drawdown depends on the regimes represented in the sample. (IBB §§9.3.2.1, 9.3.2.4)
- Resampling can show different return paths from the observed distribution, but it cannot supply adverse outcomes missing from that distribution. (IBB §9.3.2.4)
- Group forecasts into quantiles and check whether subsequent returns improve with forecast strength; a weak or irregular relationship can expose an unreliable signal. (IBB §9.3.2.5)
- Test delayed entries to measure signal decay, and ensure the simulation cannot capture a price move that occurred before the information was actionable. (IBB §9.3.2.9)
- Evaluate a candidate’s contribution to the existing portfolio, including comparison of the portfolio with and without it. (IBB §9.3.2.8)
- Include commissions and fees, slippage, and market impact when assessing implementation costs. (IBB §5.1)

## Verdict

Neither new lead qualifies for a card under the requested standard: the book identifies a supply-related mechanism, but gives neither a measured effect size nor a complete trading rule for issuance, buybacks, or bond auctions. They would require separate research before a strategy specification can be written.

