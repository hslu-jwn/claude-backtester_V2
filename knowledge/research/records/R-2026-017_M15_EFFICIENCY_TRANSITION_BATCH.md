# R-2026-017 — M15 directional-efficiency transition response batch

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test a path-structure transition rather than another magnitude, level, or sign-pattern trigger.
The frozen backlog cites Kaufman pages 10–14 and 1070–1072 for efficiency-ratio context, but the
edition is unspecified and the pages were not opened. Wiley metadata identifies the current book
only. The fixed eight-change `0.75` rising-edge rule is original and has no profitability prior.

## Four-cell design

Across ten physically adjacent completed M15 bars, compute prior and current eight-change efficiency
ratios: absolute net close change divided by summed absolute close changes. Trigger only when the
prior ratio is below `0.75`, the current ratio is at least `0.75`, and the current net path is
nonzero. This rising edge prevents repeated signals during one persistent efficient path. Trade
`{FOLLOW_PATH, FADE_PATH}` for `{30, 60}` minutes: exactly four cells, with a frozen prior one-ATR
stop and the common cost, fill, state, and defect rules.

## Distinctness, advancement, and multiplicity

R010 requires strict same-sign streaks, R014 strict alternation, R011 a trend-plus-pullback path,
and R007 a one-bar magnitude shock. R017 instead measures the ratio of net displacement to total
path length and triggers only its regime entry. Correlation is expected and recorded, but Boolean
event sets are not renamings.

Each response mode's 60-minute center and 30-minute neighbor must both pass normal/doubled costs,
UTC halves, three positive symbols per half, 300 center trades, common five-date removal, and
seed-2026017 circular five-date bootstrap including zero-trade weekdays. The proposed breadth
ledger has 328 selectable R007-R017 cells plus diagnostics and named efficiency/path trials. No
best-cell rescue, queue, run, or holdout is authorized.

## Pre-review skeptical boundary

Efficiency is descriptive and may simply identify a move after it happened. The arbitrary window
and threshold, correlated symbols, event clustering, and bid/ask costs all lower the prior.
