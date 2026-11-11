# R007 independent review packet

Date: 2026-11-05  
Reviewer: reusable quantitative-skeptic research sub-agent (`gpt-5.6-terra`, medium)  
Artifact: `strategies/drafts/M15_SHOCK_RESPONSE_BATCH__v0.1.0.json`  
Bound SHA-256: `1f78947d609e81057bbfa33e92256a49216a94fdf6bc91265b0aa5c70e2c9af1`

## Verdict

Suitable for a V2 compatibility preflight. It is not queue-ready until V2 confirms faithful
implementation and result transport. No run or final holdout is authorized.

## Review history

The first pass found under-specified timestamp, entry/stop, gap, multiplicity, session-calendar,
simultaneous-sizing, and result semantics. The draft was restricted from the five mixed instruments
to six previously exercised FX pairs and a London daytime window. It now freezes:

- interval-start M1 timestamps and London wall-clock M15 membership;
- 98-observed-bar causal warm-up, with elapsed gaps represented in scale/ATR history but physical
  adjacency required for the actual event pair;
- signal-close entry with no entry-candle stop lookback;
- bid-chart stops, executable fill costs, adverse gaps, and stop-before-time priority;
- inclusive `(entry_time,due_exit_time]` data-defect failure per affected cell;
- exact mode centers, four-cell adjacency, UTC development halves, five-date removal, and a
  seeded circular block bootstrap;
- component-wise doubled costs and independent simultaneous per-symbol sizing.

The final pass found no remaining research-spec blocker. A later cross-batch review caught that a
strict consecutive-bar warm-up would be inert across routine FX daily breaks. The corrected draft
uses prior observed closes across elapsed gaps for causal scale and ATR history, separately defines
the physically adjacent `event_return_t`, and cannot trade a gap return. The reviewer approved the
correction. It retains the adverse I-61/R004 prior, counts all 48 cells, and prohibits best-cell
rescue. The original V2 questions were sent in
`FB_R007_COMPATIBILITY_PREFLIGHT_20261104T213030Z_RESEARCH`; a canonical correction addendum records
the revised warm-up semantics without authorizing a run.

## Scientific boundary

This is a speculative development screen inside an already adverse shock-response family. Passing
compatibility would establish implementability only. A positive isolated cell would not establish
an edge, reverse the earlier family verdict, or authorize the final holdout.
