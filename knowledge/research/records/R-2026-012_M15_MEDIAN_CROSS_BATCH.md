# R-2026-012 — M15 rolling-median cross response batch

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test whether crossing a causally frozen local price median continues or fades. This is a threshold-
location family, distinct from return magnitude, prior-range breakout, candle geometry, streak, and
trend-pullback paths. No direct source supports it. Rosa (2022) supplies abstract-level contrary
context for adjacent intraday momentum, and I-58 raw-price mean reversion is already adverse/parked.

## Event and eight-cell grid

For `L in {8,16}`, freeze the median of completed closes `t-L ... t-1`; even-L median is the mean
of the two middle sorted values. Up-cross requires `close_{t-1} <= median` and `close_t > median`;
down-cross is the mirror. Prior equality qualifies, current equality does not. `FOLLOW_CROSS`
trades the cross; `FADE_CROSS` trades its negative. Combine two lookbacks, two response modes, and
holds `{30,60}` with a fixed one-ATR stop: exactly eight cells.

All bars `t-L ... t` must be physically adjacent. ATR96 advances over valid observed bars across
routine elapsed gaps and freezes through `t-1`. Use six supported FX pairs and completed London
M15 signals ending 09:00 through 13:45; all exits precede 15:00. Entry is signal close, management
starts next M1, and cell portfolios/failures are isolated.

## Advancement and multiplicity

For each mode, center `L=8/hold=60` has exact neighbors `L=16` and hold 30. Center plus at least one
neighbor must pass normal/doubled costs, both UTC halves, at least three symbols per half, 300 center
trades, common five-date removal, and a wholly positive center interval from 10,000 circular five-
date bootstrap resamples (seed 2026012) on eligible weekdays including zero-trade dates.

The complete declaration ledger has 304 selectable R007-R012 cells, R008's two diagnostics, and all
named legacy trials including I-58/raw-price and intraday-momentum variants. No best-cell/family
rescue, queue, run, or final holdout is authorized.

## Pre-review skeptical boundary

A rolling median is not a stationary fair value, crossings can be bid-ask noise, and repeated
threshold trades invite high costs. Compact preregistration limits search but does not supply edge.
