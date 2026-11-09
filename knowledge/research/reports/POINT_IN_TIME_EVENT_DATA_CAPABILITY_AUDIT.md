# Point-in-time event-data capability audit

Date: 2026-11-03  
Scope: read-only V2 code/documentation audit; no calendar CSV, market values, or results opened  
Verdict: **V2 supports a hashed retrospective schedule for blackout/descriptive splits, not a
point-in-time macro-surprise dataset. Directional event research remains unsupported.**

## What V2 does support

- A strict 29-column CSV loader validates schedule identity, timestamps, precision, currencies,
  impact labels, source metadata, coverage, and row uniqueness.
- `ScheduleEvent` deliberately excludes actual, forecast, and previous values. Strategies and the
  execution engine receive only schedule objects.
- Calendar bytes are SHA-256 identified; research runs record the hash and refuse silent calendar
  replacement on resume.
- Exact and uncertain schedule rows support entry blackouts and descriptive news/news-free splits.
  Missing/invalid files have explicit behavior.
- The implementation therefore has useful execution-risk controls, even though the delivered real
  calendar remains retrospectively sourced and user acceptance is pending.

## Why it is not point-in-time surprise data

1. V2's own specification says schedules, classifications, revisions, and cancellations are not
   verified historical vintages.
2. Forecast and previous values are parsed from the CSV shape but never exposed. There is no
   consensus snapshot identity, contributor count, forecast dispersion, or timestamp proving what
   was knowable immediately before release.
3. `EventResults` is an unwired accessor for the retrospective `actual` string only. It releases
   that string at `scheduled_at + caller-supplied delay`; it does not use an observed publication
   timestamp.
4. The loader parses `known_at_utc`, `source_retrieved_at_utc`, `source_updated_at_utc`, and
   `point_in_time_verified`, but those fields are not retained in `ScheduleEvent` or
   `EventResults`. A row marked not point-in-time verified can still supply the retrospective
   actual accessor.
5. Revisions are not modeled as versioned observations. There is no first-release value versus
   later revised value, revision timestamp, or causal as-of query.
6. Values remain source strings without unit/scaling, seasonal-adjustment, period-reference,
   transformation, or comparable-series identity. A signed standardized surprise cannot be
   computed faithfully.

These are appropriate safeguards for the current schedule-only design, not defects requiring an
immediate implementation change.

## Minimum future capability

Only if independent evidence first establishes an effect surviving supported M1 entry latency and
event-time costs should research request a separate immutable event-observation snapshot with:

- event/series/release identity, reference period, unit, scaling, adjustment and transformation;
- scheduled time, actual publication time, first-known time, retrieval time, and source/provider;
- pre-release consensus snapshot time, median/mean, dispersion, contributor count and source hash;
- first-release actual, prior value as known pre-release, every revision with its known-at time,
  and an as-of accessor that cannot see later revisions;
- cancellation/reschedule history and historical schedule-vintage identity;
- exact coverage, missingness, corrections, embargo/publication-latency semantics, and stable
  snapshot hash; and
- separation from the blackout calendar, with no strategy access before observed publication plus
  a frozen executable delay.

## Research decision

Do not treat the current news CSV or `EventResults` as authorization for actual-minus-consensus,
revision, or directional announcement strategies. Continue using schedule data only within its
documented blackout/descriptive scope. Do not build a research fixture or ask V2 for an event-data
route yet: the priority matrix correctly requires independent post-latency evidence first.

No V2 edit, strategy draft, queue submission, run, or holdout request follows from this audit.

