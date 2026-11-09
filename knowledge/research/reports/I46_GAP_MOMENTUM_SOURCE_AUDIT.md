# I-46 gap-momentum source audit

Date: 2026-10-29  
Decision: **reject the cited evidence for momentum; do not create a strategy draft**.

## Question

Does Ernest Chan's published FSTX/GBPUSD result support buying an open above the prior high and
shorting an open below the prior low, then exiting at the same-day close?

## Source inspected

- Ernest P. Chan, *Algorithmic Trading: Winning Strategies and Their Rationale*, Wiley, 2013,
  Chapter 7, “Opening Gap Strategy,” pp. 156–157,
  [full-book PDF page/text](https://asset.quant-wiki.com/pdf/Algorithmic%20Trading_%20Winning%20Strategies%20and%20Their%20Rationale-Wiley%20%282013%29.pdf),
  [author's companion directory](https://epchan.com/book2/). **Relevant full book text and printed
  code opened; companion directory listing opened.** The prose calls the rule momentum and reports
  FSTX APR 13%/Sharpe 1.4 for July 2004–May 2012 and GBPUSD APR 7.2%/Sharpe 1.3 for July
  2007–February 2012, gross of costs.

- A public independent reproduction tracker for the same example,
  [FSTX/GBPUSD sign audit](https://github.com/l3a0/quantitative-trading/issues/365).
  **Issue and reported reproduction opened; underlying proprietary data were not independently
  rerun here.** It reports that the source bytes reproduce the positive FSTX headline only with the
  fade sign; reversing the return sign to match the momentum prose produces approximately the
  opposite APR and Sharpe. This corroborates the error visible directly in the printed code.

## Critical sign inconsistency

The published code is, in relevant part:

```text
longs  = open > prior_high * (1 + threshold * volatility)
shorts = open < prior_low  * (1 - threshold * volatility)
positions(longs)  =  1
positions(shorts) = -1
ret = positions * (open - close) / open
```

For an up-gap `position = +1`. If price continues upward so that `close > open`, `(open-close)` is
negative. The code loses on continuation and profits when the up-gap fades. The same inversion holds
for down-gaps. The return expression is therefore a **gap-fade** payoff despite the momentum prose.

This is not a cosmetic naming issue. It reverses the hypothesis. The published FSTX equity curve and
headline statistics cannot be attributed to momentum unless the original result is reproduced from
authoritative data with a corrected `(close-open)/open` payoff. The GBPUSD paragraph provides no
separate code, so its sign is also unresolved.

## Additional limitations

1. The source says the rule worked best after testing a number of futures, but does not count the
   searched markets or adjust the reported best result for selection.
2. Results are gross; gap-open spreads, slippage, commissions, futures rolls, and FX clock-specific
   costs are omitted.
3. FSTX and GBPUSD use materially different session definitions. The FX “gap” from 17:00 to 05:00
   ET spans an actively traded OTC interval, not a market closure.
4. A single 0.1-volatility threshold and 90-day estimator are reported without an untouched holdout
   or modern replication.
5. Opening/gap strategies are outside the current preferred research territory and overlap the
   locally failed gap-fade/opening families.

## Decision

Reject I-46's claimed momentum evidence. Do not reinterpret the positive source result as support
for both signs and do not run local data merely to decide which sign wins.

Reconsider only if an independent, cost-aware replication fixes the payoff direction before testing,
uses authoritative session/roll semantics, counts the market/threshold search, and confirms the
momentum sign out of sample across transferable instruments. Until then, the source result belongs
to the gap-fade evidence set and cannot reopen that failed family.
