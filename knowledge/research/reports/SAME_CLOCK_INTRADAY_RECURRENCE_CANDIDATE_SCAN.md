# Same-clock intraday return-recurrence candidate scan

Date: 2026-10-29  
Decision: **do not create a single-instrument strategy or diagnostic from the current evidence**.

## Candidate boundary

The screened idea was deliberately distinct from the frozen backlog: use a completed intraday
interval's return to predict the return in the same clock interval on later days. Opening-to-close,
first-to-last-half-hour, gap, final-30-minute, fix, and large-shock rules were excluded because those
families are already represented locally.

## Primary evidence opened

- Steven L. Heston, Robert A. Korajczyk, and Ronnie Sadka, “Intraday Patterns in the Cross-section
  of Stock Returns,” *Journal of Finance* 65(4), 2010, 1369–1407,
  [DOI](https://doi.org/10.1111/j.1540-6261.2010.01573.x),
  [full author PDF opened](https://www.bauer.uh.edu/departments/finance/documents/Heston_Korajczyk_Sadka_paper_UH.pdf).
  The study uses 1,715 NYSE common stocks from January 2001 through December 2005 and 13 half-hour
  intervals per day. Its core estimator is cross-sectional: rank or regress each stock's return
  relative to other stocks, not the time-series return of an index. The next-day, same-half-hour
  winner-minus-loser decile spread averages about 3.01 basis points and remains statistically
  positive at diminishing magnitude for up to 40 trading days. The authors compare that magnitude
  with commissions and twice the quoted half-spread; the paper's practical interpretation is
  institutional execution timing, not a net standalone index strategy.

- Guido Baltussen, Zhi Da, Sten Lammers, and Martin Martens, “Hedging Demand and Market Intraday
  Momentum,” *Journal of Financial Economics* 142 (2021), 377–403,
  [DOI](https://doi.org/10.1016/j.jfineco.2021.04.029),
  [full paper opened](https://www3.nd.edu/~zda/intramom.pdf). The relevant result predicts the last
  half hour using the prior close-to-current-day return across a broad futures universe. It is a
  closing-window anomaly, not same-clock recurrence, and is already represented by the parked
  `US500_FINAL30_CONT` adaptation. It cannot validate a new middle-of-day recurrence rule.

- Carlo Rosa, “Understanding Intraday Momentum Strategies,” *Journal of Futures Markets* 42(12),
  2022, 2218–2234, [DOI/abstract opened](https://doi.org/10.1002/fut.22375). This is contrary evidence
  for the adjacent overnight-to-last-half-hour family: the predictability disappears in its
  out-of-sample period. Its thresholded regime result does not repair the absence of a same-clock,
  single-instrument effect and would add selection.

## Why the published result does not transfer

1. **Cross-section is the mechanism.** The Heston–Korajczyk–Sadka regression explicitly removes the
   market component and predicts which stocks outperform other stocks. A US500, FX, or gold CFD has
   no contemporaneous 1,715-name ranking dimension.
2. **Required data and execution differ.** Replication needs point-in-time constituent membership,
   hundreds of synchronized stocks, bid/ask or midpoint data, corporate-action handling, and a
   long–short portfolio. Supported single-symbol OHLC bars cannot reproduce it.
3. **The economic margin is small.** About 3 bps is explicitly compared with a two-trade spread
   burden. A retail-CFD round trip plus slippage is not shown to leave positive expectancy.
4. **It is not an aggregate time-series result.** Statistical significance over many stocks and
   dates cannot be converted into evidence that an index's positive 13:30–14:00 return predicts its
   own return at 13:30–14:00 tomorrow.
5. **The transferable futures literature found in the bounded search uses openings or closes.**
   Those effects overlap locally exhausted or parked families and do not establish recurrence in
   ordinary middle-of-day intervals.

## Decision

Record the territory as screened and unsupported for the current platform. Do not create a
lookback grid over clock buckets, lag days, instruments, or signs: that would manufacture a new
data-mining surface from a cross-sectional result that does not identify the proposed estimand.

Reconsider only with primary evidence for a **single-instrument time-series** same-clock effect on a
transferable futures/FX market, explicit out-of-sample testing, realistic round-trip costs, and a
predefined non-opening/non-closing interval. Cross-sectional equity evidence alone is insufficient.
