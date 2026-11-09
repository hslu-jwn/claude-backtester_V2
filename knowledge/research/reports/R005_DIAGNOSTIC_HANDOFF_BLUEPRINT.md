# R-2026-005 diagnostic handoff blueprint

Date: 2026-10-28  
Status: research-owned mapping proposal; non-operational under Shared Interface 0.1.0.

## Purpose

This blueprint maps R-2026-005 into a future diagnostic-study route without inventing an entry
strategy, stop, position size, or R accounting. It is not a queue payload, does not change the
joint contract. The first real strategy pilot is now terminal, but the blueprint cannot be
submitted unless both departments approve an additive study interface.

Update 2026-11-03: the first pilot is terminal, so the sequencing condition is satisfied. The
approval condition is not: joint review is scheduled without a verdict, and no additive study
interface exists. This blueprint therefore remains non-operational and unqueued.

## Proposed immutable study request

| Field group | R-2026-005 value |
|---|---|
| Identity | `study_id=FX_RESIDUAL_SESSION_DRIFT`, immutable specification version, submission hash, `research_id=R-2026-005` |
| Stage | Development only under the fixed V2 split; final holdout forbidden |
| Study type | Direction-normalized return-panel diagnostic with hypothetical endpoint-cost accounting |
| Universe | Required source-matched set: `EURUSD`, `GBPUSD`, `AUDUSD`, `USDCHF`, `USDJPY`; future intake must confirm all five are supported or park the study; no silent substitution or post-result selection |
| Input | Causal UTC M1 OHLC; exactly 60 unique valid bars per retained H1 interval |
| Quote normalization | USD per unit of local currency; negate `USDCHF` and `USDJPY` log returns |
| Sessions | Five fixed local IANA sessions and one 08:00--16:00 `America/New_York` comparison session |
| Calendar transforms | Frozen open/close, overlap, rollover, DST-date, weekend, Tokyo/ECB/London fix masks and next-17:00-New-York date anchor |
| Diagnostic cells | Exactly 10 pair-by-session cells; local and US aggregates reported separately |
| Primary estimands | Complete-five-pair daily local aggregate and complete-five-pair daily US aggregate |
| Cost probe | One complete resolved-cost round trip per contiguous eligible block; gross, net, and doubled-cost net; never label this a trade strategy |
| Gates | Separately for each of two counted co-primary sessions: both halves, four-of-five breadth, two-sided date-clustered 95% raw-return interval excluding zero in the predicted direction, doubled-cost direction-normalized net interval wholly positive, and pooled sign retained after fixed concentration checks; neither co-primary rescues the other |

The canonical request must carry the full rule text or stable machine-readable equivalents. An
adapter may not replace IANA calendars with fixed UTC offsets, bridge excluded blocks, change the
quote sign, use available-pair composition as primary, or promote one favorable cell.

## Required canonical result

The future result must expose enough structured data to reproduce the verdict without opening V2
department files:

- submission hash, implementation version, code commit, dataset identity, fixed split, and
  terminal status;
- all 10 cells with day counts, H1 bucket counts, block counts, gross return, resolved-cost net,
  doubled-cost net, positive-day fraction, and both fixed-half values;
- both complete-five-pair primary daily aggregates and clearly labeled available-pair
  sensitivities;
- daily exclusion counts by reason and observed retained-bucket distributions, checked against
  the price-free calendar expectations;
- date-clustered uncertainty, yearly values, leave-one-date worst retained sign, and the result
  after removing the single precomputed set of five largest absolute pooled gross dates;
- requested and resolved endpoint-cost models, including proof that every disjoint block paid a
  new round trip;
- machine-readable pass/fail for every predeclared gate, plus warnings and errors.

The result must adjudicate the local and USD co-primary effects separately and identify both in the
two-test multiplicity count. An available-pair sensitivity cannot satisfy a primary gate.

`net_r`, stop frequency, win/loss R, drawdown R, profit target, and position sizing are not
applicable and must not be fabricated. A favorable diagnostic is still not a selected strategy.

## Failure and ambiguity handling

- A malformed or unsupported calendar/quote/cost rule parks or rejects the study; V2 does not make
  a convenient assumption that changes the estimand.
- A count mismatch against the synthetic calendar ranges is an implementation warning or failure
  unless a logged data-quality/calendar exclusion explains it.
- Missing prices produce explicit coverage loss. They may not silently alter the complete-pair
  primary composition.
- If any required universe symbol or historical field is unsupported, the study is unsupported or
  parked rather than executed on a smaller convenient universe.
- If any primary gate is unavailable, the result is incomplete rather than favorable.
- Any later executable rule requires a new research record and immutable strategy specification,
  counts all 10 study cells in its multiplicity history, and still needs user authorization before
  a one-time holdout.

## Joint-review decisions needed later

1. Whether studies use separate queue/result directories or a typed envelope in existing paths.
2. Whether a study result may have multiple co-primary estimands (local and US) or needs linked
   child results.
3. The structured units for log return, price-unit cost, and direction-normalized block net.
4. Whether cell tables are embedded or referenced by checksummed canonical artifacts.
5. Terminal statuses for partial data coverage versus implementation failure.

Until those decisions are jointly accepted, R-2026-005 remains research-local.

Update 2026-11-02: `R005_DIAGNOSTIC_BLUEPRINT_SEMANTIC_AUDIT.md` identifies additional blocking
definitions for return/cost units, aggregation order, uncertainty input, authoritative calendars,
endpoint timestamps, table transport, and terminal statuses. The blueprint must not be treated as
implementation-ready until those decisions are jointly frozen and pass a price-free conformance
fixture.

Update 2026-11-03: `R005_STATISTICAL_ACCOUNTING_RESOLUTION.md` freezes the research-owned return,
endpoint-cost, daily-aggregation, and uncertainty semantics. They may no longer be chosen by an
adapter. Authoritative calendar/capability, canonical transport, terminal statuses, and the
future adapter's reproduction of the price-free conformance fixture remain blocking.

Research's price-free accounting reference now exists in
`fixtures/r005_price_free_accounting.json` with eleven focused tests. This removes uncertainty about
the requested formulas; it does not satisfy future adapter conformance, calendar/capability, or
interface transport/status requirements.

The companion synthetic result envelope in `fixtures/r005_diagnostic_result_envelope.json` now
freezes the minimum canonical acceptance shape: ten addressable cells, two co-primary rows,
complete five-pair identity, semantic-version links, explicit cost and exclusion provenance,
decision checks, a non-primary available-pair sensitivity, separate run/scientific states, and no
holdout. `tools/validate_diagnostic_fixture.py` and eight focused tests reject incomplete or
reinterpreted variants. The fixture contains no observed outcome and does not create an
operational interface.

Update 2026-11-04: the consolidated runner now joins this result fixture to
`fixtures/r005_data_capability_declaration.json`. Declaration ID/version, snapshot hash, ordered
five-pair universe, calendar identity, and endpoint-cost identity must match across both fixtures.
This closed a synthetic calendar-name drift that independent validators did not detect. It is an
internal coherence check only, not proof of a real calendar, costs, data capability, adapter, or
study result. The same consolidated join now includes the accounting fixture's frozen accounting
and uncertainty identities, including its explicit bootstrap parameter declaration.

Diagnostic numeric fields are finite-only. Cell metrics, confidence-interval endpoints, and
probabilities reject `NaN` and either infinity at payload validation, and the file entry point
rejects their non-standard JSON tokens before validation. Null or non-finite values cannot silently
stand in for a completed diagnostic measurement or evade an ordered/range check.
