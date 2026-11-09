# R-2026-020 — M15 FX relative-strength rank basket

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test a synchronized cross-sectional winner-minus-loser estimand. Menkhoff et al. (2012) form
monthly portfolios across up to 48 currencies and find momentum that is materially reduced by
costs. The opened paper does not support four-change M15 formation, a six-major universe, four-leg
CFD execution, or 30–60-minute persistence. The reverse response is an explicit falsification.

## Four-cell design

Orient each four-change log return as the foreign currency versus USD, rank all six synchronized
pairs, and select the top two and bottom two. Boundary ties suppress the event. `FOLLOW_RANK` is
long the two strongest foreign currencies and short the two weakest; `REVERSE_RANK` inverts both
sleeves. Quote orientation mechanically maps foreign-currency sides to pair sides.

Select response `{FOLLOW_RANK, REVERSE_RANK}` and hold `{30, 60}`: exactly four event-level cells.
Every event is an atomic four-leg basket. Each selected leg risks 0.10% of common cell equity at a
frozen one-ATR stop, at most 0.40% aggregate. Partial entry or partial-data estimands are forbidden.

## Distinctness, advancement, and multiplicity

R019 measures a common USD consensus and puts all six pairs in the same dollar direction. R020
removes the common component by trading relative ranks with two long and two short foreign-currency
sleeves. Both hold cells must pass total normal/doubled costs, UTC halves, common five-date removal,
and seed-2026020 date bootstrap. The center needs 300 basket events, 1,200 legs, and positive top
and bottom sleeve contributions in each half.

The proposed ledger has 340 selectable R007–R020 cells plus diagnostics and all named cross-
sectional FX momentum/rank trials. No best currency, cell, or family rescue, queue, run, or holdout
is authorized.

## Pre-review skeptical boundary

The six-currency cross-section is tiny, ranks may be unstable, four-leg costs accumulate, and
monthly evidence may not transfer intraday. Atomic ranking and sleeve results may be unsupported.
