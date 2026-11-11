# V2.4e: validate the real economic calendar (Codex gpt-6.1-terra, medium)

Read `AGENTS.md` first. Rule: ROADMAP V2.4e ("real-calendar validation pending") and V2.8 step
(3). Spec: `docs/news.md` (loader, cleaning, imputation, FTMO scope). Calendar:
`data/news/economic_events.csv` (cleaned, git-ignored; 9,836 rows). Loader:
`backtester.data.news.load_calendar(NewsConfig)`.

Decided by Opus 2026-11-03 (night run, recorded as assumptions; do not ask): validation is a
read-only report, no filter default changes; anchors only for release times that are fixed and
well established; every other event is checked for internal consistency; deviations are
listed, never auto-corrected.

## What to build (test-first)

New `src/backtester/tools/news_validate.py`,
`python -m backtester.tools.news_validate [--calendar data/news/economic_events.csv] [--out
results/news_validation]`; writes `report.md` and `deviations.csv`, prints the summary. Never
edits the calendar.

1. **Loader:** load through `load_calendar` (the same path every run uses); report the SHA256,
   row counts by impact and precision, and the loader's warning counters.
2. **Anchors** (High, exact rows, `country` US / GB as named; local time in the zone named,
   DST via zoneinfo): `Non-Farm Employment Change` (US) 08:30 America/New_York;
   `CPI m/m`, `CPI y/y`, `Core CPI m/m` (US) 08:30 America/New_York; `FOMC Statement` (US)
   14:00 America/New_York; `Official Bank Rate` (GB) 12:00 Europe/London. Per anchor: rows
   checked, rows matching, the deviating rows (date, UTC time, local time, source provider,
   precision note). Keep the anchor table in one module-level constant with a comment that it
   lists only fixed published schedules. Imputed rows (note contains "release time imputed")
   are counted separately.
3. **Consistency:** for every (`event_name`, `country`) with at least 5 exact rows, the mode
   of the local release time in the country's zone (reuse the country -> zone map of
   `tools/news_clean.py`, do not copy it); rows off the mode by more than 5 minutes go to
   `deviations.csv` with the event's mode and share; the report lists the 20 events with the
   most deviations. Events without a zone mapping are counted as "not checked".
4. **Coverage:** High rows per year and source provider (and the Finance-Calendar year from
   2025-10-24 apart, as `docs/news.md` describes), weekday share, rows still day-only by year.
5. **Summary line:** anchors passed / failed counts, consistency deviation count, day-only
   share of High rows; exit 0 always (it is a report), exit 2 only when the file cannot be
   loaded.

## Tests (`tests/tools/test_news_validate.py`, hand-built CSVs in `tmp_path` through the same
29-column writer the existing news tests use)

1. An NFP row at 13:30 UTC in winter and 12:30 UTC in summer both match 08:30 New York; a
   row at 12:30 UTC in winter is a deviation.
2. FOMC at 19:00 UTC in winter matches 14:00; BoE at 11:00 UTC in summer matches 12:00 London.
3. Imputed rows are counted apart from source-exact rows.
4. Consistency: 6 rows of one event, 5 at 10:00 local, 1 at 10:30 -> one deviation with the
   mode 10:00 and share 5/6; 4 rows -> not checked (below 5).
5. Unknown country -> counted as not checked.
6. Coverage counts by year and provider.
7. Unreadable file -> exit 2 with a clear message.

## Then run it on the real calendar

`python -m backtester.tools.news_validate` and put the summary (anchors, deviations, day-only
share) in your answer. Report only; do not edit the calendar or `news_clean`.

## Limits

New files only (`tools/news_validate.py`, `tests/tools/test_news_validate.py`) plus a
"Real-calendar validation" section in `docs/news.md` (command, checks, the run's summary).
No change to `data/news/`, the loader, the filter, any default, `live/`. Never start a
server, never commit / push / branch.

**Done =** new tests green, `python -m pytest tests/tools tests/data -q` green, ruff check and
format clean, the real run done.
