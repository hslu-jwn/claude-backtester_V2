# R-2026-015 — M15 round-number single-cross response batch

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test whether a completed M15 close that moves strictly across exactly one fixed 50-pip price-grid
level continues or fades over the next 30 or 60 minutes. The grid is an original, deliberately
compact operationalization. Wiley metadata confirms the current Kaufman book identity, while the
frozen backlog cites pages 81, 143, and 167 of an unspecified edition for round-number or pivot
context. Those pages were not opened and no inspected source establishes this FX rule or its
profitability.

## Four-cell design

For EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCHF, and USDCAD, define one pip as exact decimal `0.0001`
and the grid as every exact multiple of `0.0050`. The physically adjacent M15 closes at `t-1` and
`t` must both be off-grid and have exactly one grid level strictly between them. Zero moves,
endpoint touches, and moves crossing zero or multiple levels are not events.

The only selectable parameters are response `{FOLLOW_CROSS, FADE_CROSS}` and hold `{30, 60}`:
exactly four cells. Use the frozen prior ATR96 as a one-ATR stop. Signal closes end from 09:00
through 13:45 Europe/London subject to the selected exit being due no later than 15:00. Entry is
at the completed signal close, stop eligibility starts on the next M1 candle, all executable costs
apply, and portfolios and data failures remain isolated by cell.

## Advancement and multiplicity

For each response mode, the 60-minute hold is the center and 30 minutes is its only neighbor. Both
must pass normal and individually doubled costs, UTC halves, at least three positive symbols per
half, 300 center trades, common five-date removal, and a seed-2026015 circular five-date bootstrap
over eligible weekdays including zeros.

The breadth ledger contains 320 selectable R007-R015 cells, the two R008 diagnostics, and every
named round-number, pivot, or crossing trial including I-30. No isolated best-cell or best-family
rescue, queue submission, experiment run, or holdout access is authorized.

## Pre-review skeptical boundary

Round-number salience may be absent, the 50-pip spacing may be arbitrary across pairs and regimes,
and apparent crosses may be spread or volatility effects. Exact-decimal arithmetic and the strict
single-level definition prevent implementation ambiguity but do not supply evidence or prior.
