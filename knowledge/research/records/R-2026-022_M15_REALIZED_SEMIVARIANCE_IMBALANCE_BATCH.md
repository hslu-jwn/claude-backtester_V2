# R-2026-022 — M15 realized-semivariance imbalance transition batch

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test an intrahour signed-variation distribution rather than another M15 close level, magnitude, or
sign-pattern trigger. Liu, Lu, Li and Wang (2023) was opened in full. It uses 5-minute returns from
31 Chinese commodity futures in 2007–2018, aggregates positive and negative realized semivariance
over prior weeks, and tunes a daily 20-day momentum strategy. It reports rolling out-of-sample and
cost checks, but neither its market nor horizon validates a 60-minute FX imbalance response.

## Four-cell design

At each eligible M15 boundary, use 76 consecutive valid M1 closes to form overlapping prior and
current 60-return windows ending 15 minutes apart. For each window, sum squared positive and negative
one-minute log returns and define `Q=(RS+−RS−)/(RS++RS−)`. Trigger only from prior `|Q|<0.50` into
current `Q>=0.50` or `Q<=−0.50`; zero total variation, persistent extremes, and direct extreme sign
flips do not trigger. Trade `{FOLLOW_IMBALANCE, FADE_IMBALANCE}` for `{30,60}` minutes: four cells.

## Distinctness, advancement, and multiplicity

R007 thresholds an unusually large M15 return; R009 uses one-candle wick geometry; R010/R014/R017
use completed-M15 close-sign or displacement paths. R022 instead decomposes all one-minute squared
returns inside a rolling hour by sign and detects a normalized distributional transition. A single
jump can still create overlap, so maximum single-return variance share is mandatory reporting.

Each mode's 60-minute center and 30-minute neighbor must both pass normal/doubled costs, UTC halves,
three positive symbols per half, 300 center trades, common five-date removal, and seed-2026022
circular five-date bootstrap including zero-event weekdays. The proposed ledger has 348 selectable
R007-R022 cells plus diagnostics and all named higher-moment/semivariance trials. No queue, run,
best-cell rescue, or holdout access is authorized.

## Pre-review skeptical boundary

The source transfer is severe, the threshold/window are original, squared returns can be one-jump
dominated, and broker M1 closes can carry microstructure noise. The family is a falsification only.
