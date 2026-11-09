# R005 statistical and accounting resolution

Date: 2026-11-03  
Status: research semantics frozen before market-data access; **not implementation authorization**.

This resolves the research-owned unit, endpoint, aggregation, and uncertainty ambiguities identified
in `R005_DIAGNOSTIC_BLUEPRINT_SEMANTIC_AUDIT.md`. It does not resolve the authoritative calendar,
canonical transport, capability, or terminal-status interface blockers.

## 1. Block endpoints and gross return

An eligible contiguous block is the half-open physical interval `[t0, t1)` remaining after every
predeclared mask. It contains complete M1 bars only.

- Entry observation: raw pair bid open of the M1 bar opening at `t0`.
- Exit observation: raw pair bid close of the M1 bar ending at `t1`.
- Both are scheduled endpoint observations, not predictive signals. The opening value is usable at
  the first tick at `t0`; the closing value is usable only at `t1`.
- A mask between two eligible intervals creates two blocks and two round trips. No price bridge is
  permitted across an excluded interval.
- A pair/session/day observation exists only when at least one eligible block exists. A measured
  zero return is valid; absence of every eligible block is missing, not zero.

For raw pair price `P`, define quote-normalization sign `q=+1` for `EURUSD`, `GBPUSD`, and
`AUDUSD`, and `q=-1` for `USDCHF` and `USDJPY`. The source-matched economic return for a block is:

`r_usd_local = q * ln(P_exit / P_entry)`.

The published predicted direction is negative for the local session and positive for the US
session. Direction-normalized gross return multiplies `r_usd_local` by `-1` for a local-session
block and `+1` for a US-session block.

## 2. Endpoint-cost probe

The cost result is a hypothetical executable-endpoint probe, never a simulated strategy trade.
V2 must resolve separate adverse entry and exit adjustments in the raw pair's price units using
only information available at each endpoint. Spread, commission, and slippage may be combined only
after every component has a named model identity/version, unit, timestamp rule, and historical
coverage. Fixed-per-lot commission must be converted causally to price per base unit; inverse USD
quotes require the contemporaneous endpoint conversion. Missing provenance is not zero cost.

Let `s_pair` be the raw-pair position direction that implements the published prediction:

| Pair quote | Local-session prediction | US-session prediction |
|---|---:|---:|
| local currency per USD (`USDCHF`, `USDJPY`) | `+1` long raw pair | `-1` short raw pair |
| USD per local currency (`EURUSD`, `GBPUSD`, `AUDUSD`) | `-1` short raw pair | `+1` long raw pair |

For raw entry/exit observations `P0`, `P1` and non-negative adverse adjustments `c0`, `c1`:

- long raw pair: `E=P0+c0`, `X=P1-c1`, `r_net=ln(X/E)`;
- short raw pair: `E=P0-c0`, `X=P1+c1`, `r_net=ln(E/X)`.

Any non-positive effective fill is a data/model failure. Direction-normalized net is the formula
above because the raw position direction already encodes the predicted economic sign. Doubled-cost
net repeats the calculation with `2*c0` and `2*c1`; it does not simply subtract twice an ex-post
average cost. Financing is zero because every block is interior-session and day-flat; if an
implementation finds a block crossing its authoritative financing boundary, the block definition
or calendar is wrong and the study fails.

If a required endpoint cost is unavailable, gross results may be retained as incomplete evidence,
but neither net co-primary gate may pass and the study disposition is `INCOMPLETE`. No latest-cost,
zero-cost, or neighboring-hour fallback is allowed.

## 3. Pair-day and pooled aggregation

For each pair, session type, and next-17:00-New-York trading-day label:

1. sum all gross block log returns to form the pair-day raw return;
2. sum all direction-normalized gross, resolved-cost net, and doubled-cost net block returns
   separately; and
3. retain block count and every paid endpoint pair.

Do not average blocks: fix masks create different block counts, and averaging would overweight a
short fragment relative to the rest of its session. For each session type, the primary daily value
exists only on a date with all five pair-day values and is their unweighted arithmetic mean. Pair
weights are exactly 20%; a missing pair makes that date absent from the complete-case primary.
The available-pair daily mean is sensitivity-only and must record its composition.

All means, intervals, halves, yearly summaries, and concentration checks operate on these daily
series—not on blocks presented as independent observations.

## 4. Frozen uncertainty procedure

Inference uses a synchronized moving-block bootstrap over ordered trading-day labels:

- statistic: arithmetic mean of the relevant daily series;
- resamples: 10,000;
- block length: five consecutive observed trading-day labels;
- construction: circular blocks, concatenated and truncated to the original daily sample length;
- seed: `2026005`;
- synchronization: use the same sampled date-block indices across all pair cells, both session
  types, and raw/net series so cross-pair and cross-estimand dependence is retained;
- interval: two-sided percentile 95% interval;
- two-sided p-value: twice the smaller bootstrap tail probability around zero, capped at one.

Report the exact sample size, number of distinct dates per resample, block length, seed, and
percentile endpoints. Fewer than 100 complete-five-pair dates makes both co-primary inference rows
`INCOMPLETE`; no asymptotic or unclustered fallback is allowed.

Each session co-primary is an intersection-union gate: its raw predicted-sign test and its
doubled-cost positive-net test must both pass, so its session-level p-value is the larger of those
two p-values. Apply Holm's step-down procedure at family-wise alpha 0.05 across the local-session
and US-session co-primary p-values. The existing 95% intervals remain reported and must have the
required sign; Holm-adjusted rejection is an additional gate. One session cannot lend significance
to or rescue the other.

Fixed-half and pair-breadth gates use point estimates as already declared; they do not create ten
additional selectable hypotheses. All ten pair/session cells and both co-primary outcomes remain
reported regardless of sign.

## 5. Remaining blockers

Before any real development study, joint review must still supply:

1. a sourced, immutable, versioned symbol-session calendar resolved before OHLC;
2. an all-five canonical data/cost capability declaration satisfying
   `R005_DATA_CAPABILITY_DECLARATION_AUDIT.md`;
3. a typed diagnostic-study and result route with canonical cell/daily-summary transport;
4. distinct terminal states for unsupported capability, data failure, incomplete output, and a
   completed unfavorable diagnostic; and
5. a price-free conformance fixture implementing these formulas and the frozen calendar masks.

No strategy draft, queue payload, market-data computation, profitability claim, or holdout request
is authorized by this resolution.

## Research reference fixture

`fixtures/r005_price_free_accounting.json` and `tools/r005_reference.py` now implement the
price-free accounting reference. Eleven focused tests verify direct/inverse quote orientation,
effective-fill rather than linearized doubled costs, summation across mask-split blocks,
equal-weight all-five composition, the 100-date inference floor, and deterministic moving-block
resampling. All known price, cost, block, pair, bootstrap, and percentile inputs must also be finite;
`NaN`, infinity, booleans, and nonnumeric values fail before arithmetic. Together with the existing
synthetic calendar-mask audit, this proves the research
semantics internally. A future V2/interface implementation must still reproduce both references in
its own joint conformance test; the research fixture is not an implementation approval.

Finite inputs are not sufficient by themselves: every computed cost, effective fill, return,
pair-day total, complete-five mean, bootstrap mean, and percentile interpolation must also remain
finite. The reference uses log differences rather than price ratios where possible and fails
closed when extreme finite values overflow an arithmetic boundary.

The orientation fixture is coverage-closed: it must contain exactly one uniquely identified
`DIRECT_LOCAL`, `DIRECT_US`, `INVERSE_LOCAL`, and `INVERSE_US` case. Each ID is derived from the
row's pair orientation and session, so deleting, duplicating, adding, or relabeling a case fails
even if expected values in the remaining rows still agree.

The separate `fixtures/r005_diagnostic_result_envelope.json` carries these frozen identities into
a synthetic canonical-output example. Its validator requires exact universe/cell accounting,
co-primary inference rows, exclusions, cost provenance, decision checks, and distinct execution
and scientific dispositions. It is deliberately outcome-free and cannot satisfy the remaining
calendar, capability, transport, or implementation gates.

Update 2026-11-04: the accounting fixture now carries the exact identity
`R005_STATISTICAL_ACCOUNTING_RESOLUTION_2026-11-03`, uncertainty identity
`MOVING_BLOCK_5D_10000_SEED_2026005`, and the 10,000-resample/five-day-block/seed-2026005 procedure.
The reference validator enforces those fields and the consolidated runner requires both identities
to match the diagnostic-result fixture. This binds research semantics only; it does not establish
real data, calendar, costs, transport, or adapter conformance.
