# R-2026-021 — M15 EURUSD–GBPUSD relative-dislocation pair

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test one preregistered relative-value dislocation. Gatev, Goetzmann, and Rouwenhorst's opened NBER
paper selects U.S. stock pairs on daily data, trades convergence over six-month periods, and finds
material microstructure and cost sensitivity. It does not identify EURUSD–GBPUSD, M15 robust-
standardized returns, or a 30–60-minute response. Both signs are therefore speculative.

## Four-cell design

For each pair, divide its synchronized four-change log return by twice a prior-only 96-return robust
MAD scale. Let `D` be standardized EURUSD minus GBPUSD return. Trigger only when `abs(D)` moves from
strictly below two to at least two. `CONVERGENCE` shorts the outperforming foreign currency and buys
the underperformer; `DIVERGENCE` follows the spread. Both pairs quote USD, so foreign and pair sides
coincide.

Select response `{CONVERGENCE, DIVERGENCE}` and hold `{30, 60}`: exactly four event-level cells.
Every event is an atomic two-leg basket. Each leg risks 0.20% at its own frozen one-ATR stop, at
most 0.40% aggregate. Partial entry and partial-data estimands are forbidden.

## Distinctness, advancement, and multiplicity

R020 ranks six currencies without a magnitude threshold; R021 fixes one pair and tests a normalized
relative-dislocation threshold. Both hold cells must pass total normal/doubled costs, UTC halves,
common five-date removal, and seed-2026021 date bootstrap. The center needs 300 pair events, 600
legs, and positive EURUSD and GBPUSD contributions in each half.

The proposed ledger has 344 selectable R007–R021 cells plus diagnostics and all named pairs,
ratio, rank, and cross-symbol trials. No best leg, cell, or family rescue, queue, run, or holdout is
authorized.

## Pre-review skeptical boundary

No direct evidence establishes that this fixed FX pair is stationary or economically substitutable.
Separate volatility scaling can manufacture apparent dislocations, and two-leg costs can dominate.
