# R-2026-014 — M15 alternating-close path response batch

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test a fixed choppy-path event rather than another level or magnitude trigger. Four strict nonzero
M15 close changes across bars `t-4 ... t` must alternate sign. If summed absolute changes are at
least frozen `ATR96_{t-1}`, follow the last change or fade it. No direct source supports this rule;
Rosa (2022) is only contrary adjacent intraday-momentum context.

## Four-cell design

The event definition, one-ATR activity threshold, and one-ATR stop are fixed. Select only response
`{FOLLOW_LAST,FADE_LAST}` and hold `{30,60}`: exactly four cells. Any zero change or gap inside
`t-4 ... t` suppresses the event. ATR remains observed-sequence across routine elapsed gaps.

Use six supported FX pairs and London M15 signal closes ending 09:00 through 13:45. Entry is the
completed signal close, stop eligibility begins next M1, all executable costs apply, exits precede
15:00, and portfolios/failures are isolated by cell.

## Advancement and multiplicity

For each mode, hold 60 is the center and hold 30 its only neighbor; both must pass normal/doubled
costs, UTC halves, three positive symbols per half, 300 center trades, common five-date removal,
and seed-2026014 circular five-date bootstrap over eligible weekdays including zeros.

The breadth ledger contains 316 selectable R007-R014 cells, R008 diagnostics, and all named
serial-dependence/alternation/choppiness trials. No best-cell/family rescue, queue, run, or holdout.

## Pre-review skeptical boundary

Alternation may be random/bid-ask noise, the activity filter may merely select volatility, and the
last sign may carry no information. Four cells keep the falsification narrow; they do not add prior.
