# Fast-lane implementation readiness

Date: 2026-11-05  
Scope: R007–R022 compatibility-preflight specifications only  
Authority: research prioritization; not V2 implementation approval, queue submission, or run request

## Outcome

The research lane contains 16 independently reviewed specifications and 348 selectable development
cells. A read-only check of V2's authoritative intake documentation confirms V2.6i i1–i7, including
the synthetic end-to-end test, are built and accepted; the contract is operational and a real pilot
has completed. The immediate bottleneck was therefore Research retaining every new specification at
compatibility preflight instead of publishing one reviewed payload to the canonical pending queue.

The coding department should not build 16 bespoke runners. A small common harness plus feature
plugins can unlock the lane in tiers while preserving each immutable research definition.
`FAST_LANE_SPEC_MANIFEST.json` is the machine-readable index of exact artifact paths, review-bound
SHA-256 values, preflight IDs, priorities, tier assignments and cell counts.
The manifest audit recomputed every tunable `VALUES` Cartesian product: all 16 declared grid sizes
match their specifications exactly and sum to 348; every artifact hash, review binding and preflight
reference also resolves.

## Shared harness

Every R007–R022 specification needs the following common behavior:

1. causal Europe/London M1-to-M15 boundaries and supported `SIGNAL_CLOSE` entry;
2. observed-sequence Wilder ATR96 frozen through `t-1`;
3. signal-time spread, commission and slippage, then next-M1 stop management;
4. isolated cell equity, positions, overlap decisions, exposure and failure state;
5. same-timestamp sizing from one cell pre-entry equity snapshot;
6. exact due-time exit, stop-before-time priority and affected-cell defect handling;
7. all-cell result publication with normal/doubled costs, symbol and UTC-half rows, five-date
   removal, zero-filled weekday bootstrap, counts, warnings and the complete trial ledger.

One conformance implementation of these semantics should be reused. A reply must identify any item
that cannot be represented rather than silently adapting a strategy.

## Capability tiers

| Tier | Added capability | Specifications unlocked | Cells | Suggested proof |
| --- | --- | --- | ---: | --- |
| 0 | V2.6i shared-interface lifecycle and synthetic end-to-end result | **Passed and accepted** | 0 | V2 docs and canonical contract |
| 1 | Common single-symbol M15 harness plus deterministic feature plugin | R007–R018 | 332 | R014 first: four cells and minimal alternating-path state |
| 2 | Six-stream synchronization and atomic basket state | R019 | 4 | Five-of-six USD breadth transition |
| 3 | Deterministic cross-sectional rank, selection ties and sleeve results | R020 | 4 | Four-leg top-two/bottom-two basket |
| 4 | Robust rolling scale and atomic pair/leg attribution | R021 | 4 | EURUSD–GBPUSD pair |
| 5 | Consecutive M1 close buffer and rolling signed-square sums | R022 | 4 | 76-close semivariance conformance |
| **Total** |  | **16 specifications** | **348** |  |

Tier 1 still contains feature-specific work—compression blocks, candle geometry, streaks, rolling
median/envelope, exact decimal grids, prior-session state, efficiency and RSI—but those features do
not justify separate fill, accounting or result engines. R014 is the smallest proof because it has
four cells, no cross-symbol atomicity, no decimal/session reference, and no recursive oscillator.
Passing it would validate plumbing only; it would not authorize results for the other immutable specs.
R014 v0.2.0 was therefore selected and atomically published as the first queue submission, with the
348-cell contemporaneous multiplicity ledger replacing v0.1.0's earlier 316-cell snapshot. Its
research archive and canonical pending bytes share SHA-256
`d09d44b96cde33f45b718803eb385cc9a9fd908641d06148ea47de61acff31c5`.

## Required reply shape

V2 should answer the bulk request once with:

- confirmation that the documented passed Tier 0 remains current;
- support status for each of the seven common-harness semantics;
- the first tier it can implement without reinterpretation;
- exact unsupported fields or output sizes for each later tier;
- whether one result envelope can retain all 348 selectable cells, two R008 diagnostics and named
  legacy trials without truncation, best-cell selection or loss of failed/skipped cells.

Queue publication authorizes intake and implementation mapping only. It does not authorize Research
to execute an experiment, inspect V2 results outside canonical envelopes, or access the holdout.
