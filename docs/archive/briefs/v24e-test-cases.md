# V2.4e synthetic test cases (written before tests and production changes)

Only generated CSVs under pytest temporary directories; never open the delivered CSV.

1. Explicit 29-column schema: addendum's ordered header, UTF-8 BOM and quoted commas.
   Reject missing/extra/duplicate/reordered headers and malformed row widths.
2. UTC: Z and explicit offsets normalize identically across local timezones and DST dates;
   naive or malformed timestamps fail; blank timestamps stay None.
3. Validation: nonempty unique event_id and dedupe_key, High/Medium only, exact minute/second
   timestamp required, range needs ordered window ends; invalid precision fails.
4. Quality checks: suspicious exact time_label 00:00:00/23:59:59 and UTC weekends produce
   counted warnings, configurable errors; High counts per source/year and source transitions
   recorded, composition-change warnings/errors. Simultaneous distinct events retained.
5. File missing: report no calendar, disable filtering/split. SHA256 equals synthetic bytes
   and is persisted with run diagnostics and trial metadata.
6. Instrument relevance: EURUSD excludes unrelated currencies; currency takes precedence
   over country, country is fallback, GLOBAL opt-in per instrument; map major FX/index/metal/
   crypto instruments in configurable settings. Unknown instruments do not match.
7. Schedule objects contain no actual/forecast/previous; separate results accessor yields
   source strings only at release+delay, never a microsecond earlier; no release => no actual.
8. Blackout default off preserves complete synthetic trade results and skip callbacks.
   Enabled windows use inclusive [release-before, release+after] boundaries; one microsecond
   outside allowed. High and Medium windows independent, nonnegative finite settings.
9. Nonexact date/range/unknown: block-day conservative policy or skip with counted warning;
   no fabricated exact release; range covers represented UTC dates; simultaneous event IDs
   retained. Flag-only records events without skipping; block entries reuses skip callback.
10. Engine acceptance integration: inside order skipped once, outside order accepted; off
    and missing-calendar trades equal baseline. Existing golden files never rewritten.
11. Split: UTC entry-day and entry-minute classification for relevant High events, Medium
    excluded, nonexact rows day-only (uncertain minute explicitly separate); trades before
    2020-01-02 always no-calendar, never news-free. Out-of-coverage trades also no-calendar.
12. Per-variant summaries: counts and net R reconcile to input in day and minute dimensions;
    source periods kept separate when configured, missing file disables reporting; hash and
    coverage composition included. Cached diagnostics must not silently reuse another hash.
13. Run only pytest -q tests/data tests/tools tests/engine, logging results/pytest_v24e.log;
    ruff only touched Python files. No real calendar or market-data runner invocation.

Addendum: loader tests build CSVs with all 29 supplied columns. Runner tests persist splits
for every variant and test/retest, hash in settings/trials, no-calendar and source buckets,
resume rejection on hash changes, and missing-file behavior. Use results/pytest_v24e2.log.
This list does not authorize guessed trading rules or claim user acceptance.
