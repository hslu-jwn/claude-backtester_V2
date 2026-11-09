# Limited research pilot

Date: 2026-10-27  
Research ID: `R-2026-001`  
Outcome: two draft adaptations; no submissions; no profitability claims

## Method

Three independent research territories were inspected, followed by an adversarial quantitative
review. The review required rules, data, timing, costs, controls, multiple-testing accounting, and
rejection gates to be explicit. A schema-valid draft is not automatically implementable; the
current strategy schema still contains free-text semantic fields.

## Draft 1: diversified 12-month ETF absolute momentum, long/cash

Primary evidence comes from Moskowitz, Ooi, and Pedersen's futures/forwards study of time-series
momentum ([JFE article](https://doi.org/10.1016/j.jfineco.2011.11.003),
[paper PDF](https://fairmodel.econ.yale.edu/ec439/mosk.pdf)) and the longer historical study by
Hurst, Ooi, and Pedersen ([AQR/JPM paper](https://images.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/AQR-JPM-Fall-2017.pdf)).
Those papers do not directly validate a seven-ETF long/cash implementation.

Important counterevidence is part of the hypothesis record. Kim, Tse, and Wald report that much
of reported performance can be driven by volatility scaling
([Journal of Financial Markets article](https://doi.org/10.1016/j.finmar.2016.05.003)). Huang,
Li, Wang, and Zhou challenge asset-level and out-of-sample predictability and the conventional
pooled inference ([JFE article](https://doi.org/10.1016/j.jfineco.2019.08.004),
[working paper](https://down.aefweb.net/WorkingPapers/w717.pdf)). Evidence on moving-average ETF
implementations also cautions that tradable-fund results may be weaker than index results
([Journal of Empirical Finance record](https://pure.psu.edu/en/publications/testing-moving-average-trading-strategies-on-etfs/)).

The draft therefore classifies itself as an `ADAPTATION`, fixes the universe, and treats a
possible benefit primarily as a risk/exposure filter. It requires point-in-time total-return
signals, executable next-open prices, corporate actions, cash returns, cross-symbol portfolio
weights, and stopless accounting. Those inputs/capabilities are not established in V2, so the
draft is not ready for implementation or queue submission.

## Draft 2: US500 final-30-minute continuation

Baltussen, Da, Lammers, and Martens document that the same-day return through 30 minutes before
the close predicts the final half-hour return across many futures
([JFE article](https://doi.org/10.1016/j.jfineco.2021.04.029),
[author PDF](https://academicweb.nd.edu/~zda/intramom.pdf)). The authors' headline strategy does
not generally include transaction costs and explicitly warns that frequent rebalancing may make
the result inaccessible to many investors. Gao et al. provide related earlier evidence for the
first/last half-hours in SPY ([JFE article](https://www.sciencedirect.com/science/article/pii/S0304405X18301351)).

The local draft is explicitly a `US500` CFD proxy adaptation, not a replication of futures or
SPY. It forms the signal only from a fully closed M1 candle at the `T-30` boundary, enters at the
next M1 open, and exits at the last regular-session M1 close. This avoids using the signal close
as an assumed fill. It freezes one primary instrument and window, charges two aggressive fills,
and uses adjacent-window and shifted-day controls.

This is closer to V2's candle engine but is still blocked by mandatory stop-loss/R accounting,
normal close-fill semantics, notional sizing, and lack of a verified exchange early-close
calendar for the proxy. The fixed development segment also does not establish the draft's required
five years of US500 history. It remains a priority-10 parked draft rather than an active candidate.

## Parked concept: cross-asset 12-month TSMOM with volatility scaling

The same primary TSMOM literature motivated a cross-asset futures/CFD concept. Skeptical review
found it premature: the universe and tradable contracts, continuous-futures construction, roll
rules, excess returns, collateral yield, FX conversion, contract multipliers, volatility target,
portfolio aggregation, and missing-contract rules all need an immutable contract. Back-adjusted
signals cannot be used naively for executable P&L.

V2's stop-defined R trades and exit-booked portfolio combination are not equivalent to a
stopless, target-notional, daily mark-to-market futures portfolio. This concept should not become
a strategy draft until the data/accounting contract and simulator route are approved.

## Shared rejection principles

- Use V2's protected chronological development/test protocol; do not invent a second holdout.
- Count every asset/window/lookback/filter/parameter tested.
- Reject practical relevance when plausible costs remove the result.
- Reject fragile findings dominated by one asset, a few crisis days, the largest 1% of trades, or
  a single parameter point.
- Compare with predeclared timing and economic controls, not only a zero-return null.
- Treat predictability without net implementability as a research finding, not an edge.
