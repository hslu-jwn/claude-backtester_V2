# R-2026-011 — M15 trend-plus-pullback response batch

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test a distinct two-stage path: an ATR-material eight-change move followed immediately by one or
two strict opposite close changes. `RESUMPTION` trades the prior move; `FAILURE` trades the pullback.
This differs from R010's uninterrupted streak because the reversal leg is mandatory and the trend
leg itself need not contain same-sign changes.

The frozen backlog cites Kaufman pages 418, 835, and 950 for pullback-with-trend context, without
identifying the edition. Wiley verifies current sixth-edition metadata only; the cited pages were
not opened and no direct cost-aware M15 FX evidence was inspected. The symmetric mechanical rule
is original/speculative and low-prior.

## Event and compact eight-cell grid

For `P in {1,2}`, define prior trend direction as the sign of
`close_{t-P}-close_{t-P-8}` and require absolute displacement of at least frozen
`ATR96_{t-1}`. Then require each of the P close changes through completed signal bar `t` to be
strictly opposite the trend; equality invalidates the event. Every bar `t-P-8 ... t` must be
physically adjacent.

Combine `P={1,2}`, response `{RESUMPTION,FAILURE}`, and hold `{30,60}` minutes with a fixed one-ATR
chart stop: exactly eight selectable cells. Use six supported FX pairs and completed London M15
signals ending 09:00 through 13:45; every exit precedes 15:00.

ATR advances over valid observed bars using the previous observed close across routine gaps and is
frozen through `t-1`. Entry is the final M1 chart/bid close of `t`; stop management begins next M1.
V2 applies executable spread, commission, slippage, trigger side, and adverse-gap logic. Post-entry
data defects fail only affected isolated-cell portfolios.

## Advancement and multiplicity

For each response mode, center `P=1/hold=60` has exact neighbors `P=2` and hold 30. The center and
at least one neighbor must pass normal/doubled costs, both UTC halves, at least three positive
symbols per half, 200 center trades, common five-date removal, and a wholly positive center interval
from 10,000 circular five-date bootstrap resamples (seed 2026011) over eligible weekdays including
zero-trade dates.

The contemporaneous declaration ledger now contains 296 selectable R007-R011 cells, R008's two
diagnostics, and all named legacy trials including I-05 pullback variants. Any cross-batch selection
uses the complete ledger. No best-cell/family rescue, queue, run, or final holdout is authorized.

## Pre-review skeptical boundary

The prior move is a retrospective label, one/two opposite bars may be noise, and the pattern can
overlap R007/R010 observations. Compactness limits parameter search; it does not create evidence.
