# R-2026-019 — M15 synchronized USD breadth-transition basket

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test the lane's first synchronized multi-symbol mechanism. Menkhoff et al. (2012), opened in full,
rank up to 48 currencies using monthly past excess returns and form winner-minus-loser portfolios;
costs materially reduce returns. That does not establish a six-pair M15 common-USD breadth signal,
a simultaneous USD basket, or a 30–60-minute response. This rule is original and speculative.

## Four-cell design

Orient four-change log returns so positive always means USD strength: negate EURUSD, GBPUSD,
AUDUSD, and NZDUSD returns; retain USDCHF and USDCAD signs. Using six synchronized contiguous
M15 streams, trigger USD strength when the positive count moves from below five to at least five,
and weakness analogously. Exact-zero scores count neither sign.

Every event is one atomic six-leg basket. Select `{FOLLOW_BREADTH, FADE_BREADTH}` and hold
`{30, 60}`: exactly four event-level cells. Each leg has its own frozen one-ATR stop and risks
0.08% of the cell's common pre-entry equity, for at most 0.48% aggregate chart-stop risk. Invalid
data, cost, or size on any leg prevents partial entry; a post-entry required-leg defect fails the
whole affected cell.

## Distinctness, advancement, and multiplicity

R007–R018 derive signals per symbol. R019 conditions on contemporaneous agreement across all six
pairs and evaluates one basket event, so it is not a renamed single-series path rule. Both hold
cells for a response mode must pass normal/doubled total costs, UTC halves, common five-date
removal, and seed-2026019 date bootstrap. The center also needs at least 100 basket events, 600
legs, and four positive symbol contributions in each half.

The proposed ledger has 336 selectable R007–R019 cells plus diagnostics and all named currency-
momentum, pair/session, and USD-breadth trials. No best leg, cell, or family rescue, queue, run, or
holdout is authorized.

## Pre-review skeptical boundary

Six pairs share mechanical USD exposure, so agreement may contain little incremental information.
The five-of-six threshold and four-change window are arbitrary, all-leg costs accumulate, and
atomic multi-symbol semantics may be unsupported. The monthly primary result is only a boundary.
