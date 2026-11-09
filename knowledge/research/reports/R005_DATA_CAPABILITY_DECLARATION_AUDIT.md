# R005 data-capability declaration audit

Date: 2026-11-02  
Outcome: **all five symbols appear in V2's code-level mappings, but no canonical, versioned
declaration proves that the frozen R005 study can be accepted**.

This is a read-only audit of V2 documentation and source declarations. Research did not inspect
market-data values, execute a study, edit V2, or infer capability from observed prices.

## Frozen intake gate

R005 requires `EURUSD`, `GBPUSD`, `AUDUSD`, `USDCHF`, and `USDJPY` together. The primary daily
series is complete-case across all five. One missing symbol, required field, authoritative session
calendar, causal cost series, or development-period segment parks the study. An available-pair
subset may be reported only as the already-declared sensitivity; it cannot replace the primary.

## What V2 currently establishes

- `src/backtester/data/sources.py` maps all five symbols, gives their quote precision, prefers an
  MT5 day where present, and otherwise uses the main histdata cache. `available_symbols()` is
  derived from mutable local cache contents, not from a published capability contract.
- `src/backtester/engine/costs.py` contains cost entries for all five. A configured cost entry
  proves an implementation path, not historical endpoint coverage or fitness for R005's
  dimensionless-return accounting.
- `docs/ARCHITECTURE.md` documents UTC M1 storage, mixed preferred sources, clock-conversion
  periods, bid-only histdata bars, unknown histdata spread/volume, and absent rather than filled
  non-trading minutes. It also records particular gaps and clock qualifications.
- `docs/review/symbol-proposal-2026-10-27.md` lists all five in the then-current MT5 universe and
  reports broad cache/download work. This is dated implementation evidence, not an immutable
  per-study snapshot.
- The fixed development boundary is documented as strictly before 2021-09-14. None of the above
  files gives one versioned row per symbol proving the exact usable interval and required-field
  coverage on the data snapshot that a future diagnostic would resolve.

The evidence is therefore encouraging but insufficient for intake. Scattered code constants,
dated prose, and git-ignored cache contents can disagree or change independently.

## Minimum canonical declaration

A future declaration should be immutable, versioned, checksummed, and resolved before study code
reads OHLC. It should contain one row per symbol with at least:

| Field group | Required content | Why R005 needs it |
|---|---|---|
| Identity | canonical symbol, broker/source aliases, instrument type, base/quote currencies | prevents silent instrument or quote substitution |
| Snapshot | declaration ID/version, generated UTC, data-snapshot ID/hash, producer | makes the capability decision reproducible |
| Coverage | first/last usable UTC minute, development-only usable interval, known empty days, partial days | proves all five cover the same frozen development estimand |
| Bars | cadence, UTC open-time convention, OHLC side, uniqueness rule, completed-bar rule | freezes causal H1 aggregation from M1 |
| Clock | source clock rule/version and verified date ranges | prevents historical DST conversion drift |
| Session calendar | authoritative symbol-session calendar ID/version and expected-minute rule | distinguishes closures from unexpected missing bars without using OHLC |
| Missingness | duplicate/out-of-order policy, expected-minute gaps by class, failure thresholds | forbids partial success or implicit filler bars |
| Market fields | bid/ask/spread/volume availability and exact unknown-value semantics | stops unknown spread or activity from masquerading as zero |
| Costs | cost-model ID/version, endpoint semantics, unit, historical coverage, fallback policy | permits the frozen gross/net/doubled-cost tables in one declared unit |
| Readiness | `SUPPORTED`, `PARTIAL`, `UNSUPPORTED`, or `FAILED`, with machine-readable reasons | prevents an available subset from being promoted silently |

Top-level fields should also state the fixed split, common required interval, required field set,
and whether all requested symbols passed. `PARTIAL` is not acceptance for an all-symbol gate.

## Price-free acceptance fixture

Before real data access, a synthetic declaration should prove these cases:

1. all five rows supported with identical required development coverage -> accept capability;
2. one symbol absent or only partly covered -> park the study;
3. OHLC present but calendar, clock version, or endpoint cost coverage absent -> park;
4. unknown spread encoded as zero -> reject the declaration;
5. one source changes at a dated seam -> accept only when both segments and the seam policy are
   explicit and the required interval remains covered;
6. an available-pair subset -> retain sensitivity eligibility but keep the primary unsupported;
7. declaration or data-snapshot identity changes after resolution -> fail rather than refresh it
   during the run.

## Decision

Do not hand off R005 on the strength of existing V2 mappings. First obtain a canonical capability
declaration meeting the fields and synthetic cases above, then resolve the remaining unit,
aggregation, uncertainty, calendar, endpoint, table-transport, and terminal-status decisions in
`R005_DIAGNOSTIC_BLUEPRINT_SEMANTIC_AUDIT.md`. Capability establishes testability only; it does not
establish a residual session effect, a trading strategy, or holdout authorization.

This audit proposes no Shared Interface schema or V2 implementation change.

## Research-side fixture status

`fixtures/r005_data_capability_declaration.json` implements the all-five supported case using
synthetic identities and no market values. `tools/validate_capability_declaration.py` validates
the declaration structure and a separate requested-symbol gate. Focused tests prove that a partial
or missing pair parks the primary gate, incomplete coverage/calendar/cost intervals fail, unknown
spread cannot be encoded as zero, and a resolved declaration identity cannot drift. The fixture is
an acceptance aid only and does not claim that V2 currently meets the capability.

Update 2026-11-03: `SIGNAL_TIME_COST_CAPABILITY_AUDIT.md` separates historically reconstructed
endpoint costs from later/current conservative stress assumptions. R005's primary cost gate needs
the former for all five symbols and the complete required interval, with no nearest-year or fixed
default fallback. The synthetic generic cost-declaration fixture passes; this is not a claim that
V2's present mappings do.

The consolidated control manifest now pins the capability tuple as declaration ID, version, and
snapshot SHA-256 and supplies it to `capability_gate_errors`. A tuple change in the fixture alone
therefore fails the common entry point. The synthetic zero digest is only a declared placeholder;
this anchor does not establish content hashing, market-data immutability, or real capability.
