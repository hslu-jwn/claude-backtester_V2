# R-2026-010 — M15 directional close-streak response batch

Status: speculative high-throughput development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test whether a physically contiguous run of strict same-direction M15 close changes continues or
reverses over the next 30-120 minutes. This is a multi-bar path family: unlike R007 it does not
condition on one extreme return, unlike R008 it does not break a prior range, and unlike R009 it
does not use wick/body geometry.

The frozen backlog cites Kaufman page 1010 for an asymmetric four-down-close long rule. The edition
behind that page is unspecified; Wiley verifies current sixth-edition metadata only. The cited page
and no direct cost-aware M15 FX study were opened. The local symmetric rule is an original low-prior
falsification, not a claimed adaptation with established profitability.

## Frozen event and 72-cell grid

Use six supported pairs: `EURUSD`, `GBPUSD`, `AUDUSD`, `NZDUSD`, `USDCHF`, and `USDCAD`. For
`N in {3,5,7}`, an up streak requires every one of the N close changes from `t-N+1` through `t` to
be strictly positive; a down streak requires all to be strictly negative. Equality breaks both.
Every bar `t-N ... t` must be physically adjacent at 15-minute spacing.

Require absolute net displacement `abs(close_t-close_{t-N})/ATR96_{t-1}` to be at least
`d in {0.5,1.0}`. `CONTINUATION` trades the streak direction; `EXHAUSTION` trades its negative.
Combine response mode with holds `{30,60,120}` minutes and fixed chart stops `{1,2}*ATR96_{t-1}`.
The exact grid is `3*2*2*3*2 = 72` selectable cells.

Signals are completed London-aligned M15 closes ending 09:00 through 12:45 and all exits are due
by 15:00. ATR uses valid observed bars and the previous observed close across routine elapsed gaps,
but a gap inside the event window suppresses the event.

## Timing, costs, state, and defects

The signal enters at the final M1 chart/bid close of completed bar `t`; its earlier path cannot
trigger the new stop. Stop evaluation begins next M1. V2 applies resolved or frozen-fallback spread,
commission, slippage, executable trigger side, and adverse-gap fills. Stop precedes time exit on a
valid due bar. Any missing, duplicate, invalid, or non-finite M1 interval in
`(entry_time,due_exit_time]` fails only affected cells and must be serialized.

Every cell owns isolated equity, positions, exposure, overlap decisions, and failure state. Within
one cell, same-timestamp symbol entries use one pre-entry equity snapshot and risk 0.25% each.

## Advancement and multiplicity

For each response mode the center is `N=5`, `d=0.5`, hold 60, stop 1. Its six exact one-axis
neighbors are `N=3`, `N=7`, `d=1.0`, hold 30, hold 120, and stop 2. The center and at least two
neighbors must pass normal and doubled costs, both UTC-midpoint development halves, at least three
positive symbols in each half, 300 pooled center trades, and common removal of the center's five
best London dates. Ties sort by ascending date.

Use eligible London weekdays including zero-trade dates and 10,000 circular five-date block-
bootstrap resamples with seed 2026010. The center's normal-cost interval must be wholly positive.
Multiplicity is not isolated by family label. The contemporaneous ledger contains all 288
selectable cells across R007-R010, R008's two non-selectable diagnostics, and every identifiable
legacy trial named by those records: R004/I-61, I-32/I-33/opening-breakout, I-12/I-40/wick/no-wick/
outside-bar/key-reversal, and I-19/consecutive-close/streak/exhaustion/serial-dependence. Any cross-
batch comparison or promotion uses this complete ledger because R010 displacement can overlap R007
events. Incomplete history prohibits a confirmatory claim. No best-cell or best-family rescue,
queue action, run, or final holdout is authorized.

## Pre-review skeptical boundary

Strict streaks can arise from random sign clustering; displacement selection can overlap R007's
large-move family; and the response may be exhausted before signal-close entry. The design is useful
only as a cheap, fully retained test of path shape beyond one-bar magnitude.
