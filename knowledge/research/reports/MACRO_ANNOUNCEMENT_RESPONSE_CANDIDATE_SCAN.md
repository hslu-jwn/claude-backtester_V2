# Scheduled macro-announcement response candidate scan

Date: 2026-10-29  
Decision: **no strategy candidate; directional surprise data and sub-minute execution are essential,
and an OHLC-only post-release rule aliases the existing shock-response family**.

## Candidate boundary

The screened event was a scheduled macroeconomic release affecting FX, gold, or equity-index
futures. A valid candidate would need a causal direction available after the release, a holding
window long enough for M1 execution, realistic release-time costs, and a complete point-in-time
calendar. Pure pre-announcement drift and opening/closing effects were outside scope.

## Primary sources

- Torben G. Andersen, Tim Bollerslev, Francis X. Diebold, and Clara Vega, “Micro Effects of Macro
  Announcements: Real-Time Price Discovery in Foreign Exchange,” *American Economic Review* 93(1),
  2003, 38–62, [DOI/record opened](https://doi.org/10.1257/000282803321455151),
  [full author PDF opened](https://public.econ.duke.edu/~boller/Published_Papers/aer_03.pdf).
  Six years of real-time quotes, announcement realizations, and expectations for five USD exchange
  rates show conditional-mean jumps tied to the **surprise** (actual minus expected), with fast mean
  adjustment. The public release time alone does not identify direction.

- Louis H. Ederington and Jae Ha Lee, “The Short-Run Dynamics of the Price Adjustment to New
  Information,” *Journal of Financial and Quantitative Analysis* 30(1), 1995, 117–134,
  [abstract opened](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/shortrun-dynamics-of-the-price-adjustment-to-new-information/00BEB6F23889807615ADA3EC3050994E).
  Using tick and 10-second interest-rate/FX futures returns, price changes begin within ten seconds
  and are basically complete within 40 seconds. Any overreaction is corrected in the second or
  third minute. This is a microstructure-scale adjustment, not established M1 post-event drift.

- Alex Frino and Amelia Hill, “Intraday Futures Market Behaviour around Major Scheduled
  Macroeconomic Announcements: Australian Evidence,” *Journal of Banking & Finance* 25(7), 2001,
  1319–1337, [DOI/abstract opened](https://doi.org/10.1016/S0378-4266(00)00132-1).
  Most information adjustment occurs within 240 seconds. Quoted spreads widen before the release
  and remain abnormally wide immediately afterward, directly worsening attainable event fills.

- Grigori Erenburg, Alexander Kurov, and Dennis J. Lasser, “Trading around Macroeconomic
  Announcements: Are All Traders Created Equal?,” *Journal of Financial Intermediation* 15(4), 2006,
  470–493, [DOI/abstract opened](https://doi.org/10.1016/j.jfi.2005.07.003). Regular and E-mini S&P
  500 futures show a large activity surge after ten price-relevant announcement types. The reported
  profitable behavior belongs to exchange locals in the first 20 seconds, while off-exchange
  traders lose over the same window. It does not validate delayed retail-CFD entry.

## Blocking and alias analysis

1. **A calendar is not a directional signal.** It identifies time and likely volatility. The primary
   papers require point-in-time expectations and realizations, including release revisions and exact
   timestamps, to define the signed surprise.
2. **The exploitable window is faster than the platform abstraction.** A signal formed after a full
   M1 candle observes most or all documented mean adjustment. Assuming a fill at the release or
   inside that candle would be lookahead and ignore unknown path/order.
3. **Release-time costs are state dependent.** Spread widening, slippage, quote withdrawal, and
   gaps make ordinary bar-close cost assumptions optimistic precisely when the event occurs.
4. **Price-only sign selection is not new.** “Trade in the direction of the first release-minute
   return” is another large-return continuation cell; “fade it” is the opposite R-2026-004 cell.
   Announcement filtering adds an event-definition trial but no independent post-M1 evidence.
5. **The published profitability is access-specific.** First-20-second profits for exchange locals
   versus losses for off-exchange traders argue against transfer to a retail CFD, not for it.
6. **Pre-announcement drift is a different exposure.** It requires holding before unknown news,
   often across overnight hours, and cannot be used to claim a causal post-release rule.

## Decision

Do not draft, queue, or add an announcement filter to R-2026-004. Reconsider only if the shared
data contract first supports an immutable point-in-time calendar plus actual/consensus/revision
fields, auditable release timestamps, and event-time bid/ask or executable costs—and independent
evidence establishes post-signal drift after the platform's causal entry latency. Until then, the
territory is a data/microstructure research dependency rather than an OHLC edge.
