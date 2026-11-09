# Authoritative symbol-session calendar gate

Date: 2026-11-03  
Status: research acceptance requirement; price-free and non-operational  
Applies to: R004 expected-M1 integrity predicate, R005 session masks, and future studies that must
distinguish scheduled closure from missing data.

## Required semantic object

An authoritative calendar is not a list inferred from observed bars. Before any experiment OHLC
is read, one immutable declaration must resolve the exact symbol universe and required interval.
It must identify:

- declaration ID/version/hash, generation and resolution times, stage, and required interval;
- authoritative source/provider identity, source version/hash, timezone-database version, and the
  canonical symbol-to-venue/product mapping;
- for every symbol, a versioned schedule and exception-table identity/hash, IANA timezone,
  complete verified interval, recurring weekly open segments, and complete holiday/early-close
  treatment;
- the rule that expected minutes are half-open UTC M1 intervals generated independently of OHLC;
- explicit scheduled-closed categories: weekend, recurring daily break, holiday, and early close;
- DST ambiguity/nonexistence policy and effective-date behavior for schedule revisions; and
- fail-closed behavior for unavailable, ambiguous, uncovered, or identity-drifted dates.

`coverage_complete=true` is a capability assertion that must be supported by the named source and
jointly tested. It cannot be established by the research fixture itself.

## R004 use

For each calendar-open half-open UTC minute, R004 requires exactly one fresh OHLC record. Missing,
duplicate, or stale expected M1 during a position makes the experiment `TEST_FAILED`; scheduled-
closed minutes are not missing and may not be bridged into an H1 bar or holding horizon. If any
symbol-date is uncovered or ambiguous, fail before strategy metrics. No entry may be erased after
the fact because a later data defect was observed.

The calendar identity, timezone database, symbol schedules, and first integrity defect must be
published in the canonical result shape already frozen in `R004_CANONICAL_RESULT_MAP.md`.

## R005 use

R005 additionally needs predetermined local/session and benchmark masks. A calendar declaration
can establish scheduled market openness, but it does not by itself establish whether a benchmark
administrator publishes a fix on a local holiday. Benchmark-publication calendars therefore need
their own identities or explicit linkage; they may not be inferred from price activity.

## Executable research reference

`fixtures/authoritative_session_calendar_declaration.json` is a synthetic, price-free example.
`tools/validate_session_calendar_declaration.py` and focused tests require exact universe and
interval coverage, complete closure categories, source/schedule/exception identity, causal
resolution, fail-closed missingness, and stable post-resolution identity. It does not claim that
V2 has this capability, authorize R004/R005 execution, or modify the Shared Interface.

Declaration chronology is fail-closed: `resolved_at` may equal but cannot precede `generated_at`.
This ordering check is not evidence that a real calendar was resolved before prices; the explicit
pre-OHLC and independent-derivation assertions still require implementation proof.

The consolidated runner additionally joins the calendar fixture to
`fixtures/signal_time_cost_declaration.json` on the shared experiment context: stage, pre-OHLC
resolution, exact interval, and ordered symbol universe. It deliberately does not require the
venue-calendar provider identity to equal any broker cost-component source. Those are independent
provenance objects that an eventual study must resolve and publish separately.

The manifest separately pins the calendar declaration ID/version/hash and supplies it to
`calendar_gate_errors`. Fixture-only tuple drift is therefore rejected, while the synthetic zero
digest remains a placeholder rather than evidence of content integrity or a real calendar source.
