# I-30 round-number level evidence check

Date: 2026-10-29  
Decision: **retain as a diagnostic event annotation only; do not create a directional strategy,
filter, or target/skip rule**.

## Question

Does independent evidence support I-30's proposal to trade breakouts or fades at round numbers, or
to improve another setup by skipping/targeting trades according to a nearby round number?

This check separates a documented market microstructure effect from a profitable rule observable
with OHLC bars. Daily pivot levels are a different construction and were not treated as validated by
round-number evidence.

## Primary evidence inspected

- Carol L. Osler, “Support for Resistance: Technical Analysis and Intraday Exchange Rates,”
  *Federal Reserve Bank of New York Economic Policy Review* 6(2), 2000, 53–68,
  [full paper](https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf).
  **Full paper opened.** It tests support/resistance levels published by six FX firms from January
  1996 through March 1998 against one-minute indicative quotes for USD/DEM, USD/JPY, and GBP/USD,
  during 09:00–16:00 New York. Actual levels predicted 15- or 30-minute trend interruptions better
  than 10,000 sets of arbitrary levels. This establishes conditional price behavior around
  professional, time-varying levels—not a profitable round-number trading rule. The study does not
  deduct trading costs or report an executable strategy return.

- Carol L. Osler, “Currency Orders and Exchange Rate Dynamics: An Explanation for the Predictive
  Success of Technical Analysis,” *Journal of Finance* 58(5), 2003, 1791–1819,
  [DOI](https://doi.org/10.1111/1540-6261.00588),
  [full working paper](https://fraser.stlouisfed.org/docs/publications/frbnysr/frbny_sr125.pdf).
  **Full working paper opened; publisher abstract opened.** The data contain almost 9,700
  stop-loss and take-profit orders at one large dealing bank from 1 September 1999 through
  11 April 2000 for USD/JPY, GBP/USD, and EUR/USD. Requested execution rates cluster at round
  numbers, but order types have different placement patterns: take-profit orders provide negative
  feedback while stop-loss orders provide positive feedback. The paper explains how both a bounce
  at a level and momentum after a breach can arise. It explicitly says that it does not evaluate
  whether the documented patterns create risk-adjusted profits.

- Carol L. Osler, “Stop-Loss Orders and Price Cascades in Currency Markets,” *Journal of
  International Money and Finance* 24(2), 2005, 219–241,
  [DOI](https://doi.org/10.1016/j.jimonfin.2004.12.002),
  [full working paper](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr150.pdf).
  **Full working paper opened; publisher abstract opened.** Minute quotes for USD/DEM, USD/JPY,
  and GBP/USD during New York hours from January 1996 through April 1998 show unusually rapid
  moves when prices reach regions where stop-loss orders are known to cluster. Responses around
  stop-loss clusters are larger and longer-lived than responses around take-profit clusters; most
  significance lasts hours, not days. The identification is indirect—order-book clustering from a
  different sample locates likely order regions—and the paper studies price dynamics, not net
  trading performance.

## What transfers and what does not

The evidence supports one narrow statement: **round-number proximity can mark an FX
microstructure event.** It does not determine the trade side from OHLC alone.

1. A level can produce either reversal or continuation. Take-profit liquidity can interrupt a
   trend; stop-loss execution can amplify it. A bar touching or crossing a round number does not
   reveal which latent order type dominates.
2. The empirical level definitions are not I-30's universal constants. The papers use currency-
   specific quotation conventions and professional levels; they do not validate gold increments
   of 10/50, index increments of 100/500, or daily pivots.
3. Predicting a bounce frequency or faster price movement is not a strategy P&L. Spread, slippage,
   gap risk during a cascade, entry timing, stop placement, and false touches remain unresolved.
4. “Skip if the level is inside the target” and “vacuum if it lies beyond the break” are opposite,
   flexible overlays. Applying either after seeing another setup's results would add an uncounted
   interaction search and could cosmetically rescue a failed signal.
5. The studies use old institutional FX samples, one dealer's conditional orders, and indicative
   minute quotes. Market structure, decimal conventions, electronic execution, and V2's broker
   feed reduce direct transportability.
6. A price cascade can worsen execution exactly when continuation looks strongest. OHLC bars
   cannot reconstruct the skipped quotes or order-book depth needed to price that risk.

## Decision and admissible future use

Keep I-30 out of the strategy queue. A future preregistered study may use **distance to the nearest
predefined round number as a descriptive event label** for an independently valid signal, provided
the increment is frozen per instrument before development results, every interaction is counted,
and the unconditional strategy verdict cannot be reversed by the subgroup.

Do not use round-number proximity to choose breakout versus fade, suppress trades, alter targets,
or reopen a failed family. Reconsider a directional use only if new independent evidence provides
the same instrument/quotation convention, an OHLC-observable causal rule, realistic net costs and
slippage, an out-of-sample test, and a small frozen rule surface. No qualifying study was found in
this bounded check.
