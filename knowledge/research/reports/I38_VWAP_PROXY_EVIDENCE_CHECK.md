# I-38 session-mean “VWAP proxy” evidence check

Date: 2026-10-29  
Decision: **park; do not create a research family or strategy draft**.

## Question and exact local rule

I-38 proposes an index day trade after the New York open: anchor the cumulative mean of typical
price at 09:30; after 15 minutes, buy a pullback that holds above the mean or short a failed test
from below; place a close/buffer stop through the mean and target a prior-day level or 2R. The
backlog calls this a “VWAP proxy” and suggests a later true-tick-volume VWAP comparison.

The bounded search asked whether primary evidence treats the prevailing VWAP or an unweighted
session mean as a causal fair-value level that predicts a cost-surviving bounce/rejection in the
same instrument. Evidence that VWAP is an execution benchmark was not treated as trading-alpha
evidence.

## Evidence inspected

### What VWAP research actually establishes

- Daniel Mitchell, Jedrzej Białkowski, and Stathis Tompaidis, “Volume-weighted average price
  tracking: A theoretical and empirical study,” *IISE Transactions* 52(8), 2020, 864–889,
  [DOI](https://doi.org/10.1080/24725854.2019.1699523). The accessible working-paper record and
  abstract were opened; the delivery PDF was blocked. The study treats VWAP as an **execution
  quality benchmark for a pre-existing large order** and optimizes how to track it under volume,
  impact, and transaction-cost dynamics. It does not infer that price must revert to VWAP or test
  I-38's directional entry.

- Hao Zhou, Petko S. Kalev, and Alex Frino, “Algorithmic trading in turbulent markets,”
  *Pacific-Basin Finance Journal* 62, 2020, 101358,
  [DOI](https://doi.org/10.1016/j.pacfin.2020.101358). **Full paper opened.** Using flagged
  algorithmic and human trades in 384 Australian stocks around the 2008–2009 crisis, the authors
  find algorithmic execution is more sensitive to the prevailing VWAP and creates less price
  pressure. This identifies execution behavior and liquidity smoothing, not positive return from
  buying every hold above VWAP or selling every rejection below it. The sample is equities,
  actual transactions, and market-wide turbulent days; it does not transfer to index-CFD OHLC.

The VWAP execution literature therefore gives I-38 a plausible reason why institutional orders
cluster around a benchmark, but no directional prediction. An execution algorithm approaches VWAP
because a parent order already determines its side; its behavior cannot be reversed into a
standalone side-selection rule without additional evidence.

### Adjacent cost-aware intraday evidence

- Guglielmo Maria Caporale, Luis Gil-Alana, Alex Plastun, and Inna Makarenko, “Intraday Anomalies
  and Market Efficiency: A Trading Robot Analysis,” *Computational Economics* 47, 2016, 275–295,
  [DOI](https://doi.org/10.1007/s10614-015-9484-9). **Full paper opened.** It implements first-45-
  minute and last-15-minute equity trades with spread-aware fills across US and Russian stocks.
  The strategies are unprofitable across normal, crisis, and post-crisis subsamples. This is not a
  VWAP test, but it is adverse to promoting a visual opening-session regularity before net trading
  evidence exists.

- A 2026 SSRN manuscript titled “Momentum Exhaustion and Fair Value Reversion: An ADX-conditioned
  VWAP Strategy in FX Markets” was found, but its own abstract says formal backtesting and
  performance attribution are left to future work. The abstract page was opened; the PDF was
  blocked. It is a proposal, not evidence, and its many filters do not validate I-38.

No peer-reviewed or otherwise independently credible study was found that tests the same
session-mean hold/rejection entry with realistic costs and transferable instruments.

## Specification and identification defects

1. **The proxy is not VWAP.** A cumulative mean of M5 typical prices weights bars equally. True
   VWAP weights transaction prices by executed volume. Relabeling a time-weighted OHLC statistic
   does not import evidence about institutional VWAP execution.
2. **Available volume is not equivalent to exchange volume.** Histdata has no volume; MT5 tick
   volume is a quote/activity proxy on a broker feed. A true-VWAP claim would require validation
   against executed market volume, not merely an A/B with a different proxy.
3. **“Hold” and “failed test” are under-specified.** Close distance, buffer, approach direction,
   number of confirmation bars, slope, and permissible recrossings create a large discretionary
   search surface.
4. **Targets mix hypotheses.** Prior close, prior high/low, and 2R represent different gap,
   breakout, and fixed-payoff mechanisms. They cannot be interchangeable exits in one primary
   test.
5. **Opening overlap is already adverse locally.** The frozen backlog records no robust net edge
   for the opening-range family and no edge for the previous-close gap fade. A session-mean filter
   cannot reopen those failed families without independent evidence.
6. **Endogeneity defeats the “fair value” label.** The prevailing VWAP or cumulative mean moves as
   the same day's prices arrive. Being above or below it is a path statistic, not proof of
   mispricing or an external anchor.
7. **Costs are central.** Pullback/rejection signals can trade frequently near a noisy boundary.
   The closest cost-aware intraday anomaly and FX technical-rule evidence is adverse.

## Decision and reopening condition

Keep I-38 parked and do not add it as a filter to a failed opening/gap rule. Do not call the OHLC
session mean VWAP.

Reconsider only after independent evidence provides all of the following before V2 data access:

- an exact causal definition of the benchmark and hold/rejection event;
- a justified source of executed volume or an honestly named time-weighted alternative;
- one fixed target mechanism and stop, with a day-flat cutoff;
- cost-aware out-of-sample results on a transferable index or index future;
- a comparison against the same entry times with the benchmark condition removed; and
- evidence of incremental prediction beyond opening direction, gap state, and time of day.

No qualifying study was found in this bounded check.

