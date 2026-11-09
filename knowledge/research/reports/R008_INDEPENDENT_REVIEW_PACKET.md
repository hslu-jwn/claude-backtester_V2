# R008 independent review packet

Date: 2026-11-05  
Reviewer: reusable quantitative-skeptic research sub-agent (`gpt-5.6-terra`, medium)  
Artifact: `strategies/drafts/M15_COMPRESSION_BREAK_BATCH__v0.1.0.json`  
Bound SHA-256: `b7886bc04718bd6bd392771d2e7e9007194dee1f0b93bc9710182c10f08cd2bb`

## Verdict

Suitable for a V2 compatibility preflight. It is not queue-ready until V2 confirms faithful
implementation and result transport. No run or final holdout is authorized.

## Review history

The first pass required exact per-cell portfolio isolation, diagnostic-row isolation, ATR seeding,
even-length median, data-defect, bootstrap, and result-row semantics. The completed draft freezes:

- six supported FX pairs and 72 selectable compression-break response cells;
- 98 observed valid M15 bars for causal ATR state, with daily/weekend gaps represented through the
  previous observed close;
- physical 15-minute contiguity across the entire `t-L ... t` event window, so a gap cannot create
  a compression block or breakout;
- signal-close entry, next-M1 stop eligibility, executable fill costs, and stop-before-time priority;
- independent position, overlap, equity, and failure state for every cell;
- two isolated non-selectable plain-break diagnostics;
- exact centers, one-axis neighbors, development halves, five-date removal, doubled costs, and a
  seeded circular five-date block bootstrap over zero-filled eligible weekdays.

The final cross-batch pass approved the observed-sequence indicator history and contiguous-event
rule as causal, reproducible, and non-inert. No research-spec blocker remains.

## Scientific boundary

This is a speculative development falsification inside the adverse-prior I-32/I-33 and opening-
breakout family. The 72 cells and two diagnostic rows are correlated, not independent hypotheses.
Compatibility does not establish profitability, reverse a prior family verdict, authorize a run,
or permit final-holdout access. No best-cell rescue is allowed.
