# R-2026-018 — M15 RSI extreme-entry response batch

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test a bounded-oscillator state transition. The frozen backlog cites unspecified-edition Kaufman
pages 389–390 for short-horizon RSI context; those pages were not opened, and Wiley metadata only
identifies the current book. No inspected source establishes this RSI(14) M15 FX rule or net edge.

## Four-cell design

Compute causal Wilder RSI(14) on observed completed M15 close changes with explicit zero-gain/loss
conventions. An upper event requires prior RSI `<70` and current RSI `>=70`; a lower event requires
prior RSI `>30` and current RSI `<=30`. Event bars must be physically adjacent. Same-side extreme
persistence cannot repeatedly fire, while a direct move from one extreme into the opposite extreme
qualifies as the other side's entry under those exact Booleans. Trade `{FOLLOW_EXTREME, FADE_EXTREME}` for `{30, 60}` minutes:
exactly four cells. Use the common frozen prior one-ATR stop, fills, costs, state, and defect rules.

## Distinctness, advancement, and multiplicity

R018 is a bounded recursive oscillator-state entry, not R007's return magnitude, R010's strict
close streak, or R017's displacement/path-length ratio. Each mode's 60-minute center and 30-minute
neighbor must both pass normal/doubled costs, UTC halves, three positive symbols per half, 300
center trades, common five-date removal, and seed-2026018 circular five-date bootstrap including
zero-trade weekdays.

The proposed breadth ledger has 332 selectable R007-R018 cells plus diagnostics and all named RSI,
oscillator, streak, and exhaustion trials. No best-cell rescue, queue, run, or holdout is authorized.

## Pre-review skeptical boundary

RSI extremes can persist in trends, threshold entry may be late, observed-sequence gaps influence
state, and threshold/horizon selection plus correlated symbols lower the prior.
