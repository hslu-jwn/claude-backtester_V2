# High-throughput strategy funnel

Date: 2026-11-04  
Status: active research operating policy; no holdout authorization and no V2 code change

## Objective

Produce a broad stream of falsifiable, V2-compatible intraday strategy candidates without
misrepresenting parameter variants as independent discoveries or weakening the final holdout.
The first production target is 20 strategy families and 200-400 fully declared development cells.

## Four separate counters

1. **Family:** one economic/event hypothesis, including both predicted directions.
2. **Specification:** one immutable machine-readable handoff and implementation identity.
3. **Cell:** one exact Cartesian parameter combination within a specification.
4. **Result:** one canonical development evaluation returned by V2.

Backlog coverage, literature sources, validator tests, and synthetic fixtures are not strategy
output. Reports must show all four counters and must never summarize cells as independent
strategies.

## Funnel

### A. Capability filter

Fast-lane candidates use only current V2 M1 OHLC symbols, causal aggregation from completed bars,
`SIGNAL_CLOSE` or supported `LIMIT` execution, fixed price-defined stops, R accounting, and a
same-day clock exit. They must not depend on an authoritative holiday calendar, news values,
executed volume, order books, point-in-time constituents, unsupported portfolio accounting, or
the final holdout.

### B. Batched preregistration

Group related triggers behind one uniform entry/exit interface and declare the entire Cartesian
grid. Each batch freezes:

- every trigger and continuation/reversal sign;
- every aggregation horizon and causal warm-up;
- stop, target, and time-exit domains;
- exact symbol universe and session clock;
- a declared baseline and cluster-level pass/reject rules;
- all costs, robustness checks, and multiplicity accounting.

The batch is exploratory breadth, not evidence that every cell has an independent rationale.

### C. Cheap development rejection

V2 evaluates every declared cell on development data only. The default disposition is rejection.
A family cannot advance because one cell is positive. Advancement requires a coherent neighboring
cluster, adequate trades, positive net results after resolved and doubled costs, stability across
symbols and chronological development partitions, and resistance to removal of extreme days.

### D. Promotion

Only a surviving frozen family receives deeper source review, independent skeptical review, and
a smaller confirmatory specification. Development results remain visible and counted. The final
holdout remains unavailable until the user explicitly authorizes the exact promoted version.

## Throughput and token controls

- Default to one active, reusable Terra research sub-agent only when local work is insufficient.
- Keep related follow-ups with the same agent; do not fan out short-lived discovery workers.
- Run focused validation while drafting and the full gate once per completed batch, not after each
  small documentation edit.
- Avoid reopening synthetic-control hardening unless it blocks an immediate batch or protects a
  scientific invariant.
- Persist concise batch manifests and decision tables rather than repeatedly rereading the entire
  research log.

## Initial production sequence

1. Freeze a reusable OHLC event-response grammar and semantic invalid-combination rules.
2. Draft the first 40-100-cell batch using only observed contiguous bars and same-day exits.
3. Obtain V2 compatibility feedback before producing further batches with the same grammar.
4. After compatibility, produce batches until at least 20 families and 200-400 cells are either
   queued, rejected by capability checks, or returned with canonical development results.

## Scientific boundary

This funnel increases falsification throughput, not the probability that any candidate works.
Hundreds of cells create a severe selection problem; they are useful only when all failures remain
recorded and a lucky development cell is not called a discovered strategy.
