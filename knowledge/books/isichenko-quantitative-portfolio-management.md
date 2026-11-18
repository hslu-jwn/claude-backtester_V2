# Michael Isichenko, *Quantitative Portfolio Management: The Art and Science of Statistical Arbitrage* (Wiley, 2021)

Short: **QPM**. Cite by printed page (`QPM p.N`). Read 2026-11-18 by Codex; PDF in the library folder Tier 3.

The book describes an institutional quantitative equity process, from point-in-time data and return forecasts through forecast combination, risk, trading costs, portfolio construction and simulation (QPM pp. 7–8, 129, 155, 172, 185, 226). Its emphasis is on combining weak forecasts and implementing them realistically, rather than publishing complete trading systems (QPM pp. 19, 227–229). The author characterizes typical return predictability as approximately 1 bp per day against roughly 2% stock volatility; this is a broad characterization, not the measured return of a particular rule or sample (QPM p.8).

## Testable ideas

The book gives incomplete rules for the following ideas. Missing entries, exits and holding periods are stated as such rather than supplied.

- **Dividend ex-date flows — NEW** (QPM p.15): Some participants may trade predictably before or after the ex-date because of tax or regulatory considerations. The book gives no direction, entry, exit, holding period, effect size or sample. Data needed: point-in-time ex-dates and dividend terms, daily stock prices and a historical stock universe; venue: real US shares. The proposed counterparty and timing are worth investigating, but the book does not establish a measured edge.

- **Crowded portfolio liquidation — NEW** (QPM pp. 166–168): Forced sales or short covering can move stocks held by similar market-neutral portfolios; the author describes unusually strong performance after extreme dislocations. No actionable trigger, security-selection rule, entry, exit or holding period is given. The cited 8.7% August 2007 loss is one fund’s reported monthly loss, not a tradable event return; otherwise **no effect size or systematic sample is given**. Data needed: historical long-short factor exposures or holdings, stock prices and a point-in-time liquidation trigger; venue: real US shares.

- **Post-announcement merger risk arbitrage — NEW** (QPM pp. 14–15): Model the probability of a merger completing and trade the affected target and acquirer accordingly. The claimed mechanism is the acquisition offer and the possibility that the deal fails. The book gives no precise entry, hedge ratio, exit or holding period. It states a typical offer premium of **20–30%** of the target’s pre-merger price, but this is not the post-announcement strategy return; no strategy effect size or sample is given. Data needed: point-in-time deal announcements and terms, completion outcomes and daily prices; venue: real US shares.

- **Holdings and potential fund liquidation — NEW** (QPM pp. 15–16): Public quarterly Form 13F holdings may contain information because funds have reasons to hold securities and may later need to liquidate them. The book gives no trade direction, entry, exit, holding period, effect size or sample; its figures for aggregate hedge-fund ownership and volume are not returns. Data needed: filing timestamps, historical holdings and daily prices; venue: real US shares. The filing delay and the absence of a defined forced-sale trigger limit the idea as stated.

- **Exposed short positions and squeezes — NEW** (QPM pp. 16, 168–169): Covering by short sellers can amplify price increases, particularly in illiquid shares. The book supplies no predictive entry rule or exit and expresses doubt that such moves can be forecast quantitatively. It reports January 2021 gains of **1,780% for GameStop and 560% for AMC**—two selected episodes, not an estimated strategy return. Data needed: point-in-time short interest, liquidity and daily prices; venue: real US shares.

- **Market-residual daily reversal — MAPS TO: daily reversal** (QPM pp. 20–21): Estimate a stock’s market beta, calculate its market-residual daily return and forecast the next day’s residual in the opposite direction. The author attributes the effect to herding and says this basic forecast is too weak to be practical. No execution times, effect size or sample are given. Data needed: point-in-time daily returns for a broad historical equity universe; venue: real US shares.

## Method notes

- Timestamp data by when it became available, and check whether vendors have revised historical records; apparently historical data can contain lookahead (QPM p.10).
- Include historical listings and delistings in the security universe to avoid survival bias (QPM pp. 11–12).
- Treat a portfolio’s own past market impact as a possible source of overly optimistic simulated forecast performance (QPM p.10).
- Compare simulated trading with actual production using the same point-in-time inputs, portfolio size and constraints; recalibrate costs as they change (QPM p.228).
- Model probabilistic fills carefully: a simulated limit order is not necessarily executed simply because its price was reached (QPM p.228).
- Limit repeated forecast tuning on the same historical data; the author regards forecast fitting and combination as especially vulnerable to overfitting (QPM p.229).
- Account for liquidity when sizing positions, including the cost of exiting under stress; shorts can have asymmetric losses (QPM pp. 168–169).
- Expect correlations among crowded alphas to rise during liquidation events, weakening normal diversification assumptions (QPM p.168).
- Run paper trading alongside production to check system changes and detect execution-model or cost deviations (QPM pp. 231–232).

## Verdict

None of the **NEW** ideas has both a sufficiently specified mechanism and a stated, tradable effect size that makes it ready for a research card. Dividend ex-date flows and crowded liquidation are the closest mechanism leads, but the book supplies neither a measurable rule nor an event return for either (QPM pp. 15, 166–168). The merger premium and squeeze examples are observed price moves, not strategy returns after an actionable entry (QPM pp. 14–15, 169). They would need separate source research before becoming candidates.

