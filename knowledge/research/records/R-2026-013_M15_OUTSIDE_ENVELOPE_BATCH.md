# R-2026-013 — M15 outside-envelope close response batch

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test a strict two-bar range-expansion event: completed bar `t` exceeds both prior high and low and
closes beyond one prior extreme. Follow that close or fade it. This envelope relation differs from
R009's one-candle wick geometry and R008's multi-bar compression breakout, though all overlapping
trials remain in one ledger.

The frozen backlog cites Kaufman pages 111 and 157-158 for outside-bar/key-reversal context without
identifying the edition. Wiley verifies current sixth-edition metadata only; cited pages were not
opened and no direct cost-aware M15 FX evidence was inspected. The rule is speculative.

## Event and eight-cell grid

Require strict `high_t>high_{t-1}` and `low_t<low_{t-1}`. Direction is +1 only when
`close_t>high_{t-1}`, -1 only when `close_t<low_{t-1}`; wick-only outside bars, equality, and closes
inside the prior envelope are no event. Require current high-low range / frozen `ATR96_{t-1}` at
least `{1.0,1.5}`. Combine threshold, `{FOLLOW_CLOSE,FADE_CLOSE}`, and hold `{30,60}` with a fixed
one-ATR stop: exactly eight cells.

Event bars must be physically adjacent. Use six supported FX pairs, signal closes ending 09:00
through 13:45 London, signal-close entry, next-M1 stop eligibility, executable costs and isolated
cell state. All exits precede 15:00; post-entry defects fail only affected cells.

## Advancement and multiplicity

For each mode center threshold 1.0/hold 60 has exact neighbors threshold 1.5 and hold 30. Center
plus at least one neighbor must pass normal/doubled costs, UTC halves, three positive symbols per
half, 200 trades, common five-date removal, and seed-2026013 circular five-date bootstrap over
eligible weekdays including zeros.

The ledger contains all 312 selectable R007-R013 cells, R008's diagnostics, and named legacy trials
including I-12 and related R008/R009 patterns. No best-cell/family rescue, queue, run, or holdout.

## Pre-review skeptical boundary

Outside bars can be pure volatility noise, the close filter may enter after repricing, and overlap
with prior geometry/breakout searches is substantial. Compactness limits but does not cure this.
