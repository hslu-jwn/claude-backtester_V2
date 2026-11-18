# Cartea, Jaimungal and Penalva, *Algorithmic and High-Frequency Trading* (Cambridge University Press 2015)

Short: **AHFT**. Cited by printed page. Read 2026-11-18 by Codex; PDF in the library folder Tier 4.

The book combines electronic-market microstructure, empirical equity-market observations and mathematical models of execution, market making and statistical arbitrage (AHFT pp. 39, 81, 246, 273). Its empirical examples use daily data and detailed NASDAQ order-book messages; many later strategies are model-based rather than demonstrated historical trading systems (AHFT pp. 39–40, 134, 295).

## Testable ideas

None selected. The examined sections do not provide a complete trading rule **and** a stated return effect size suitable for this brief. For example, the order-book imbalance analysis reports a relationship with subsequent price changes but does not state an entry-and-exit rule with a return size in the examined empirical section (AHFT pp. 295–297). The pairs-trading discussion provides model-based rules, but the cited INTC–SMH illustration does not establish a trading return size (AHFT pp. 57–59, 273–274).

## Method notes

- **Separate observation from explanation.** The authors explicitly describe their interpretations of empirical patterns as speculation and limit their descriptive conclusions to the sample studied (AHFT p. 39).

- **Check whether explanatory variables are available at decision time.** The daily-return regression includes same-day SPY return, VIX change, volume and order flow. It describes contemporaneous relationships; those completed-day values cannot be used to predict that same day’s open-to-close return (AHFT pp. 43–44).

- **Reconstruct event data before interpreting it.** NASDAQ order messages record additions, cancellations and executions of standing orders; market orders must be inferred from executions. Cancellation and execution messages may need matching to earlier order IDs to recover price and quantity (AHFT pp. 39–41).

- **Track abnormal sessions explicitly.** Early closes and a market shutdown appear as outliers in intraday volume curves. The authors caution that such observations can disproportionately affect backtests and algorithm design (AHFT pp. 66–67).

- **Treat spread as a cost, measured against a defined reference.** The quoted half-spread is the immediate cost relative to midprice for a small aggressive order; effective half-spread compares the actual execution price with midprice and can differ because of book walking or hidden liquidity (AHFT pp. 71–72).

- **Normalize costs by price and examine their distribution.** In the book’s 2013 sample, median quoted spreads were 419 bp for ISNS, 29.5 bp for FARO, 5.5 bp for MENT and 2.9 bp for AAPL. Dollar spreads alone obscure these differences; the sample is illustrative, not a current cost estimate (AHFT pp. 72–73).

- **Model halts and stale observations deliberately.** The authors note that their spread statistics include messages timestamped during a trading halt. A small effect on a full-year aggregate does not establish that a halt is harmless to an individual strategy (AHFT pp. 73–74).

- **Allow impact to depend on order size.** An order larger than available best-quote depth walks the book and obtains a worse average price; execution simulation should not assume unlimited liquidity at the quoted price (AHFT pp. 81–82).

- **Use event-study benchmarks and examine clustering.** For one AAPL trading day, the authors compare activity in the 10 ms after executions with a benchmark of all 10 ms intervals, and also examine events excluding same-side orders close to a preceding order. They flag their order reconstruction as a simplifying assumption (AHFT pp. 82–83).

- **Distinguish temporary from persistent impact.** The book estimates the association between five-minute net order flow and midprice changes separately from the immediate cost of walking order-book snapshots. Its estimates are model- and sample-dependent; the contemporaneous regression alone does not prove causal permanent impact (AHFT pp. 87–88).

- **Account for tick size and latency.** A fixed cent tick has different basis-point significance at different share prices. In the book’s single-day AAPL example, successive quote changes often reverse, while latency exposes an order to intervening changes even when the eventual quote is unchanged (AHFT pp. 52–53).

- **Do not assume every passive order fills.** The market-making exercises explicitly ask how optimal posting changes when a matching market order fills the agent’s quote with probability below one. A realistic passive-fill assumption matters to simulated profitability (AHFT p. 272).

- **Normalize event rates by exposure time.** For order-book imbalance, the authors calculate market-order arrival rates conditional on each imbalance regime by dividing arrivals by time spent in that regime. Raw event counts alone would confound frequency with time in the state (AHFT pp. 296–297).

- **Treat pairs as risky positions.** Pairs trading relies on a spread reverting to its historical or modeled relationship; the authors explicitly distinguish it from risk-free arbitrage (AHFT p. 273).

## Verdict

No **NEW** idea qualifies for a research card under the requested threshold: the examined examples offer useful microstructure mechanisms and modeling tools, but not a complete, applicable trading rule with a stated return size. Order-book imbalance is especially dependent on detailed quote data and short horizons; its reported predictive relationship is not itself a net trading return (AHFT pp. 295–297). The strongest contribution here is improving cost, execution and event-study design.

