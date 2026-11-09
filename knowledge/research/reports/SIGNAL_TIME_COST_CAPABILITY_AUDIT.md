# Signal-time cost capability audit

Date: 2026-11-03  
Scope: read-only V2 implementation/documentation audit; no market data or result values read  
Verdict: **V2 has substantial cost mechanics, but no canonical declaration proves historically
reconstructed signal-time cost coverage. Current costs can be used only under their explicitly
declared model/stress assumptions.**

## Why this matters

Costs are not a predictive input, but they are scientifically consequential. They can reject a
fill through a cost limit, change the selected variant through net-R ranking, and decide whether a
research candidate survives a feasibility gate. A cost value measured after the evaluated date
therefore cannot be described as a causal historical observation merely because it is not a
trading signal.

Two valid but different modes must be kept separate:

1. **Historical reconstruction:** only cost information whose source and effective interval cover
   the simulated timestamp is used. Missing coverage fails or marks the observation unsupported.
2. **Predeclared conservative stress:** a later/current estimate may be applied to older periods
   if its provenance and transformation are frozen before outcomes. It is a scenario assumption,
   not a historical signal-time estimate, and must not silently become the primary reconstructed
   cost series.

## Read-only findings

### Spread

- `engine/ftmo_spread_median.json` stores year/New-York-hour medians for five symbols. XAUUSD,
  GBPUSD, and GBPJPY cover 2015-2026; NAS100 and US500 begin in 2021. Other symbols use fixed
  spreads.
- `SpreadTable.spread_at` uses the nearest available year, including a later year. V2 explicitly
  documents that NAS100/US500 development dates in 2015-2020 use 2021 values and that the full
  2021 measurement crosses the fixed development/test cutoff.
- A missing symbol/hour silently falls back to a price-scaled fixed spread. The applied numeric
  settings are serializable, but the run does not expose a structured per-fill provenance flag
  distinguishing measured cell, nearest-year substitution, and fixed fallback.
- The shipped table has a free-text note but no declaration ID/version, generated timestamp,
  content digest, effective interval, per-cell observation counts, or missing-spread share. The
  measurement tool writes `coverage.csv`, but that evidence is not part of the shipped table.
- Fixed spreads/reference prices mix short recent measurement windows and explicit estimates.
  This is documented, but it is not a complete historical-coverage claim.

### Slippage, commissions, and financing

- Default slippage is commonly a rough fraction of spread. The separate p90 fill file has a
  global collection interval, sample count, and value per symbol, but no immutable model identity,
  account/feed identity, order-side/type buckets, time-of-day coverage, or applicability interval.
- Unmeasured p90 symbols use a 1.5x total-cost factor. That is a useful stress rule, not measured
  slippage for the missing symbol.
- Commission assumptions are substantially documented, but some instrument classifications and
  values remain assumptions. Current commission schedules are applied historically.
- Current swap rates are applied to every year; V2 documents that this overstates some earlier
  periods. Day-flat research normally avoids swap, but the provenance distinction remains needed
  in the generic cost contract.

### Result traceability

`settings.json` can preserve resolved numeric engine costs and the embedded spread table. That is
valuable reproducibility evidence. It does not by itself prove source identity, point-in-time
availability, coverage, or which fallback supplied a particular simulated endpoint. V2.6l also
allows missing settings to substitute `CostConfig()` and records the substitution in notes; the
separate reviewability audit already classifies this as fail-open for a canonical result.

## Minimum declaration gate

Before research calls a cost input authoritative or signal-time, resolve an immutable declaration
before OHLC/outcome access. It must state:

- declaration identity/version/hash, generation time, stage, required interval, and mode;
- exact symbol universe and required components;
- source identity/version/hash, broker/feed/account class, unit, side, timestamp semantics, and
  applicable order/fill type for every component;
- measured/effective interval, coverage completeness, sample-count or schedule support, unknown
  encoding, and explicit missingness behavior;
- every substitution/transformation, including nearest-year use, price scaling, fixed fallback,
  and stress factor;
- whether the value is reconstructed evidence or a conservative scenario assumption; and
- a fail-closed rule: no undeclared default, zero-for-unknown, or post-resolution identity drift.

Primary historical reconstruction requires full required-interval coverage and `fallback=NONE`.
A conservative-stress declaration may use later estimates, but it must be labeled
`CONSERVATIVE_STRESS`, remain separate from primary reconstructed metrics, and never establish
that historical executable costs were observed.

## Consequences for current research

- R-2026-005 remains blocked. Its frozen endpoint-cost accounting is executable, but the present
  V2 mappings do not prove historical endpoint-cost coverage for all five pairs.
- Cost feasibility screens may use explicitly predeclared stress assumptions, but their records
  must say so. They may not be cited as reconstructed signal-time costs.
- No rerun, queue submission, holdout access, V2 change, or profitability conclusion follows from
  this audit.

## Executable research reference

`fixtures/signal_time_cost_declaration.json` is an outcome-free synthetic historical-
reconstruction declaration. `tools/validate_cost_declaration.py` and six focused tests require
complete symbol/component coverage, immutable source identity, exact effective intervals,
fail-closed missingness, no fallback, mode-consistent evidence labels, and stable post-resolution
identity. It is a research acceptance reference only, not evidence that V2 currently satisfies the
gate.

The validator also requires `resolved_at >= generated_at`. This rejects impossible declaration
chronology but does not prove that resolution preceded OHLC access; the separate
`resolved_before_ohlc: true` assertion remains mandatory and requires external implementation
evidence for a real study.

## Calendar integration boundary

The consolidated research-control runner now joins this declaration to
`fixtures/authoritative_session_calendar_declaration.json` on the shared experiment context only:
development stage, resolution before OHLC, exact required interval, and ordered canonical symbol
universe. `tools/validate_research_controls.py` rejects drift in any of those fields.

Cost-component source identities are intentionally not equated to the calendar's authoritative
source. Spreads, fills, and commissions are broker/feed/account evidence; scheduled-open minutes
are venue/product/calendar evidence. Treating those providers or hashes as one identity would be a
false provenance claim. Any future executable bundle still must name both declarations
independently.

The manifest also pins the declaration ID/version/hash tuple and passes it to `cost_gate_errors`,
so post-resolution tuple drift fails the consolidated gate. Because the fixture uses an all-zero
synthetic digest, this is a review anchor only—not proof of file content or external cost data.
