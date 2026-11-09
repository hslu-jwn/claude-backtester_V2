# R004 independent-review packet

Prepared: 2026-11-02T17:26:02Z  
Status: **blocked externally; no independent review has occurred**  
Draft SHA-256: `FF8C351894E02DF22163C475470C399F96D3F075A8801CFF4BACC5B2A9E6EA73`

## Artifact set

Review all three artifacts as one frozen candidate set:

1. `strategies/drafts/INTRADAY_H1_SHOCK_RESPONSE__v0.1.0.json`
2. `research/R-2026-004_INTRADAY_SHOCK_RESPONSE.md`
3. `reports/R004_CANONICAL_RESULT_MAP.md`

The hash above binds only the JSON draft. Before review, recompute it; any mismatch voids this
packet until the changes are reconciled and a new packet/hash is recorded. The research record and
result map are mutable supporting documents until review is complete.

## Blocking external dependency

Do not approve handoff readiness unless V2 canonically confirms both:

- an immutable, version-identified authoritative symbol-session calendar exists for every in-scope
  symbol/date and is resolved before experiment OHLC is read; and
- the exact `robustness.r004` publication map can be serialized in the canonical result envelope.

Research's reply requesting those confirmations is
`FB_INTRADAY_H1_SHOCK_RESPONSE_REPLY_20261102T171227Z_RESEARCH`. Absence of an answer is not implied
approval. The draft remains `DRAFT`, unqueued, and development-only.

V2 answered adversely in `FB_INTRADAY_H1_SHOCK_RESPONSE_20261102T232536Z_ca99`: it has no
authoritative, version-identified CFD symbol-session calendar covering holidays and early closes.
Research acknowledged this in
`FB_INTRADAY_H1_SHOCK_RESPONSE_REPLY_20261103T103714Z_RESEARCH`. The review binding is retained to
detect artifact drift, but its status is `BLOCKED_EXTERNAL`; do not spend an independent review
while the capability gate is known to fail. Queueing the incompatible payload merely to trigger
calendar work is forbidden. A later sourced calendar requires a fresh compatibility check before
this packet may return to `PENDING`.

Research's price-free acceptance shape is now executable in
`AUTHORITATIVE_SYMBOL_SESSION_CALENDAR_GATE.md` and
`fixtures/authoritative_session_calendar_declaration.json`. Passing that synthetic validator does
not satisfy the external dependency; a real declaration for the exact universe and interval must
still be jointly verified before compatibility is rechecked.

## Required independent checks

The reviewer should answer each item `PASS`, `FAIL`, or `BLOCKED`, with a brief reason:

1. **No lookahead:** event return, same-clock median/MAD state, and eligibility use only closed H1
   bars and deterministic information available at signal close.
2. **Calendar causality:** expected M1 intervals cannot be inferred from price-bar presence,
   absence, neighboring observations, or realized returns.
3. **Gap behavior:** a missing, duplicate, or stale expected M1 while a position is open fails the
   experiment; it cannot cancel the historical entry, imply stop survival, or backfill an exit.
4. **Grid accounting:** the only selectable grid is exactly 2 response modes × 3 thresholds × 3
   horizons = 18 cells, with independent state and `variants_tried=18`.
5. **Primary selection:** `k=3,h=1` is the sole primary setting; pooled raw-q sign mechanically
   selects continuation or reversal, while both sign cells remain counted.
6. **No rescue:** secondary cells, symbols, directions, clock hours, halves, common-event samples,
   placebos, and concentration exclusions cannot replace a failed primary.
7. **Raw versus executed response:** direction-normalized raw q and stop-defined executed R remain
   separate through estimation, uncertainty, costs, and canonical publication.
8. **Costs and fills:** signal-time price-unit event floors and resolved execution costs are causal;
   the fixed 6-ATR stop and exit priority do not require an unobservable same-bar path.
9. **Decision completeness:** every submitted rejection criterion maps to an explicit
   `COMPLETED`, `SKIPPED_EARLY_STOP`, `UNSUPPORTED`, or `FAILED` result-map row; omission cannot pass.
10. **Holdout protection:** the artifact requests development only, contains no custom split, and
    supplies no mechanism to inspect or authorize the final holdout.

The reviewer must also challenge sample dependence, correlated index events, March 2020
concentration, clock-hour/news confounding, minimum event counts, doubled costs, and the fact that
direct primary evidence supports conflicting signs.

## Verdict record

An acceptable independent verdict must record:

- reviewer identity or independent agent/task identifier;
- review timestamp in UTC;
- the exact JSON SHA-256 above;
- one status and reason for all ten checks;
- overall verdict `APPROVE_UNCHANGED`, `CHANGES_REQUIRED`, or `BLOCKED_EXTERNAL`; and
- every requested change without editing the candidate artifact during the review.

`APPROVE_UNCHANGED` means scientifically and semantically ready for a later promotion decision; it
does not submit, authorize execution, or authorize holdout access. Any requested change keeps the
draft mutable, requires a new hash, and requires another independent review of the changed set.
