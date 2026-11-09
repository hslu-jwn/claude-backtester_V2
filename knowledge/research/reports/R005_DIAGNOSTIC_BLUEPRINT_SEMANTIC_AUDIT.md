# R005 diagnostic-blueprint semantic audit

Date: 2026-11-02  
Outcome: **scientifically bounded but not implementation-ready; keep research-local**.

## What is already frozen

The question, five-pair universe, quote normalization, ten pair-by-session cells, IANA sessions,
opening/fix/rollover/overlap masks, next-17:00-New-York date anchor, complete-five-pair primary
composition, two co-primary tests, concentration checks, and no-holdout rule are explicit. The
synthetic calendar audit shows the masks do not make the estimand structurally empty.

## Blocking semantic decisions

1. **Canonical return unit.** Raw cells are log returns, but “resolved-cost net” is not defined in
   one unit. Joint review must choose and document a causal conversion from entry/exit price-unit
   costs into the same dimensionless log- or simple-return unit for both direct and inverted USD
   quotes. `net_r` is inapplicable and cannot be used as a shortcut.
2. **Daily aggregation order.** The primary observation must be constructed deterministically
   before uncertainty is calculated. Joint review must freeze whether pair-day net is the sum of
   its direction-normalized block gross returns minus every block round trip, followed by an equal
   average across the five complete pairs. Averaging blocks first would overweight days and pairs
   with different fix-induced block counts and is not equivalent.
3. **Uncertainty input.** “Date-clustered” is ambiguous after collapsing to one complete-five-pair
   value per date. The result must name the exact daily series, estimator, finite-sample correction,
   and interval method. Pair/block rows are reporting splits, not independent observations.
4. **Calendar authority.** IANA conversion and price-free masks do not by themselves establish that
   a minute was expected to trade. The study needs the same pre-OHLC, immutable, version-identified
   symbol-session calendar principle frozen for R004, plus an explicit policy for local holidays
   that are currently acknowledged as contamination.
5. **Cost timestamp and endpoint.** A scheduled diagnostic block has no predictive signal. The
   study request must distinguish observed midpoint endpoint returns from a hypothetical executable
   endpoint-cost probe and state which completed M1/H1 timestamps supply each price. It must not
   imply that an H1 open was known only after that hour closed or label the probe an executed trade.
6. **Canonical table transport.** Embedded cells versus checksummed canonical tables remains an
   interface decision. Whichever route is chosen must preserve all ten cells, daily coverage and
   exclusion counts, the two co-primary series, requested/resolved costs, and every decision check
   without requiring access to V2-local artifacts.
7. **Terminal semantics.** Unsupported universe/calendar/cost capability, data-integrity failure,
   incomplete required outputs, and a completed unfavorable study need distinct statuses. A partial
   result cannot be interpreted as a favorable diagnostic.

## Recommended joint-review sequence

First publish the generic unit/aggregation/calendar/status semantics, then serialize the R005
example, then run a price-free synthetic conformance fixture. Only after that fixture reproduces
the frozen retained-bucket distributions and all required cells should either team consider a real
development study. A favorable diagnostic would still require a new immutable strategy hypothesis;
it cannot authorize trading or final-holdout access.

This audit does not propose a Shared Interface edit and does not authorize a queue payload.

## Resolution update â€” 2026-11-03

`R005_STATISTICAL_ACCOUNTING_RESOLUTION.md` now freezes blockers 1, 2, 3, and 5 on the research
side: exact M1 endpoint observations, raw-pair and USD/local log-return signs, adverse effective
fills and doubled costs, sum-then-equal-weight daily aggregation, complete-five-pair composition,
and a synchronized five-day moving-block bootstrap with Holm control across the two co-primary
sessions. These are no longer open choices for a future adapter.

Blockers 4, 6, and 7 remain external/joint: authoritative session calendar, canonical table
transport, and terminal statuses. The all-five capability declaration is separately specified in
`R005_DATA_CAPABILITY_DECLARATION_AUDIT.md`. The research accounting reference now passes its
price-free fixture, but a future adapter must reproduce it jointly. R005 remains research-local and
unexecuted.
