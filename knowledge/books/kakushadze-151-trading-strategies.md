# Kakushadze and Serur, *151 Trading Strategies* (Palgrave Macmillan, 2018)

Short: **K151**. Read 2026-11-18 by Codex; PDF in the library folder Tier 1.

The book catalogs trading strategies across stocks, options, ETFs, fixed income, commodities, currencies and other assets. It generally describes portfolio construction and cites literature rather than reporting measured returns. Many entries are payoff structures or hedges, rather than evidence of an exploitable effect. The ideas below are outside the project’s judged list, but none has both a stated effect size and a sufficiently specified mechanism for a research card.

## Testable ideas

- **Leveraged ETF pair decay** (K151 p.91): Short a leveraged ETF and its equally leveraged inverse on the same index; invest the proceeds in, for example, a Treasury ETF. The book does not specify entry thresholds, rebalancing or exit. Its proposed mechanism is the funds’ daily leverage reset and resulting long-term decay; it warns that a large short-term gain in either leg can hurt the pair. **No size or empirical sample given.** Data: adjusted daily prices, distributions, borrow availability and rates, and financing costs. Venue: real US shares/ETFs. **NEW.**

- **Merger arbitrage** (K151 p.56): After an announced cash acquisition, buy the target; for a stock acquisition, buy the target and short the acquirer in the announced exchange ratio. The book illustrates the payoff if the deal closes and the loss risk if it fails, but gives no systematic entry threshold or exit rule. The proposed opportunity is the gap between target price and deal consideration, exposed to deal completion risk. **No measured effect size or empirical sample given**; the $3 spread is a hypothetical example. Data: point-in-time deal announcements, terms and outcomes, daily prices, borrow and financing costs. Venue: real US shares. **NEW.**

- **Earnings surprise portfolios** (K151 pp.43–44): Rank stocks by standardized unexpected earnings: latest quarterly EPS minus EPS four quarters earlier, divided by the standard deviation of unexpected earnings over the last eight quarters. Buy the top decile and short the bottom decile, dollar-neutral; the book says the typical holding period is six months. It describes earnings momentum but does not establish a compelled counterparty. **No size or empirical sample given.** Data: point-in-time EPS announcements and histories, daily share prices and shorting costs. Venue: real US shares. **NEW.**

- **Same-index ETF arbitrage** (K151 p.125): Buy the cheaper ETF and short the dearer ETF tracking the same index when the executable bid/ask relationship crosses a preset threshold; liquidate as the discrepancy closes. The example threshold is **1.002**, a trading parameter rather than a measured profit. The book says opportunities are ephemeral and require fast execution. **No effect size or empirical sample given.** Data: synchronized ETF bid/ask quotes and executable fills; daily or ordinary M1 bars cannot establish the stated spread. Venue: real US ETFs. **NEW.**

- **Commodity futures skewness** (K151 p.157): Rank commodity futures by historical return skewness, buy the bottom quintile and sell the top quintile in a zero-cost portfolio. The book does not specify the lookback, holding period or a compelled trading counterparty. It cites Fernandez-Perez et al. (2018), but gives **no effect size or sample**. Data: contract-level futures histories, rolls and futures trading costs. Venue: exchange futures. **NEW.**

## Method notes

- A dollar-neutral stock portfolio can be constructed by matching long and short dollar investments; neutrality alone does not establish a profitable signal (K151 pp.43–44).
- Leveraged ETF pairs can suffer substantial short-term losses even when the proposed thesis concerns long-term decay (K151 p.91).
- Apparent index cash-and-carry opportunities must exceed transaction costs; slippage and execution speed can eliminate them (K151 p.122).
- ETF arbitrage should be assessed using executable bid and ask prices, not just observed last prices (K151 p.125).
- The book warns that a healthy-minus-distressed stock portfolio can develop a significantly negative market beta after downturns and lose heavily in a rebound (K151 p.221).

## Verdict

**None of the NEW ideas meets the requested mechanism-plus-stated-size standard for a card on this book alone.** Leveraged ETF resetting supplies the clearest forced-flow mechanism, but the book gives no return size or sample and leaves the trade’s exit unspecified. Merger arbitrage has a concrete deal-linked spread, but its numerical example is hypothetical. Earnings surprise and commodity skewness lack a compelled-counterparty explanation here, while same-index ETF arbitrage requires quote-level execution data and has no reported effect size (K151 pp.43–44, 56, 91, 125, 157).

Read-only report: scanned the contents and strategy catalog and examined the relevant candidate sections. **Files changed:** none. **Tests:** not run; no code changed. **Open question:** none.