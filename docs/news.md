# Economic calendar (V2.4e)

Status: synthetic implementation, including the 29-column CSV-format addendum, loader
validation, research split and hash persistence. The delivered CSV has not been opened,
copied, or used for results. Real-calendar verification and user acceptance remain pending.

## Schedule and results

`data/news.py` defines frozen schedule events and calendars containing no `actual`, `forecast`,
or `previous` fields or result objects. The separate `EventResults` accessor returns actual
source strings only when `now >= release + delay`; no release means no result. Negative delays
and naive simulation timestamps fail. The accessor is not wired into any strategy.

The source is retrospective: schedules, classifications, revisions and cancellations are not
verified historical vintages. Forecasts and previous values must remain unavailable to
strategies until a versioned source exists.

## Configuration and instrument relevance

`EngineConfig.news` contains `NewsConfig`. These settings remain available to JSON/grids
but have no UI widgets. The filter defaults to `enabled=False`. Window defaults (rule set by the user, 2026-10-27): High 2 minutes before and 2 minutes after the
release (`ImpactWindow(2.0, 2.0)`), Medium no window (`ImpactWindow(0.0, 0.0)`). An impact whose
window is 0 / 0 is not filtered at all: neither its exact releases nor its day-only rows block
anything (so Medium never blocks; High day-only rows left after imputation block their day).
`enabled` stays False; the user decides separately when to switch it on.
The configured path is `data/news/economic_events.csv`, relative to the project root.
The research runner loads each configured calendar once per invocation for descriptive
reporting, independently of the blackout switch. The engine accepts an explicitly supplied
schedule through its `calendar` keyword argument. Every run through `runner.run_backtests`
(CLI, app, research runner, job queue) and the chart's trade overlay passes
`news.execution_calendar(config)`: None while `enabled` is False (no file read), otherwise the
configured CSV, loaded once per process and file version (wired 2026-10-27; before that the
switch had no effect outside tests). A missing schedule disables filtering. An absent configured
file reports "no calendar" and disables the research split; an invalid existing file fails.

Currencies and fallback countries are configurable per instrument. A nonblank currency takes
precedence over country; country is considered only when currency is blank. Codes are trimmed
and matched without case sensitivity. `GLOBAL` requires explicit per-instrument opt-in and is
off for every default instrument. CSV `currency=ALL,country=GLOBAL` uses the same opt-in.
An unknown instrument matches no events. Defaults cover major
FX pairs, XAUUSD/XAGUSD, NAS100, US500, US30, US2000, GER40 and BTCUSD/ETHUSD.

## Windows

The pure `blocked(t, instrument, calendar, config)` function uses inclusive exact-time bounds:

`release - before_minutes <= t <= release + after_minutes`.

One microsecond outside either bound is allowed. High and Medium windows are configured
independently; negative and nonfinite durations fail. Simultaneous events are all retained.
`matching_events` returns the schedule events causing a window match.

The conservative `block_day` policy covers the UTC date of a date/unknown event. Range records
cover all UTC dates touched by both window ends, inclusive. This is a day-block policy, not an
invented exact release. The alternative `skip` policy excludes uncertain records; counted
warnings are emitted by the loader. Blank timestamps must never become
midnight releases.

At the engine's order acceptance step, `block_entries` calls the existing
`strategy.on_order_skipped(ref, now)` hook once and increments `Backtest.news_blocked`.
`flag_only` records `(acceptance_time, event_ids)` in `Backtest.news_flags` and preserves trades.
The engine uses its existing acceptance timestamp (base-candle close) for both market orders
and reported limit fills; it does not infer an intrabar release or fill timestamp. This does
not change existing fill semantics. Existing positions and exits are unaffected. The blackout
window is checked at that candle close, not at an intrabar M1 fill time (rule set by the user,
2026-10-27). Windows are inclusive at both ends; the sizes per impact are the defaults above.

## Research split

`tools/news_diagnostics.py::news_split` is a pure reporter wired into the research runner.
It reports trade counts and net R per instrument, source period, day/minute dimension and bucket.
Classification uses UTC entry time. Exact High events mark their release minute and day;
Medium events do not enter the split. Nonexact High events mark days; minutes on those days
are `uncertain` unless an exact release occurs in the entry minute. Blackout windows and the
filter's enabled setting do not affect this descriptive split.

Trades before 2020-01-02, or outside the supplied calendar's explicit coverage, belong to
`no_calendar`, never `news_free`. With no schedule, the report is disabled. Covered trades
use `news`, `news_free`, or (minute dimension only) `uncertain`.

`separate_source_periods=True` separates configured UTC coverage boundaries. The initial
boundary is 2025-10-24, identified by the handoff as a coverage-universe change. The comma-
separated `source_boundaries` setting can change those dates. Period labels have an inclusive
lower bound and exclusive upper bound. Disabling period separation pools covered trades.
Every output row carries the calendar SHA256. Each variant and test/retest folder stores
`news.json` (calendar metadata and split rows); `settings.json` stores `calendar_sha256`.
The research folder's `news.csv` combines every development variant and saved test/retest,
with period, variant and test-run identifiers. `research.json` and `report.md` record calendar
versions and High counts per source/year. Trial settings include `calendar_sha256` when a
calendar exists; absent calendars preserve the existing trial identity and count. Run settings
record a null hash when absent. No actual, forecast or previous values enter these outputs.

Calendar manifests are checked before resuming. A changed hash, a newly present/missing
calendar, or a calendar attached to an older unversioned research folder requires a new grid
name. Saved results are never silently relabelled using another calendar version.

## CSV validation

`load_calendar(NewsConfig)` reads the addendum's explicit ordered 29-column schema as UTF-8
with an optional BOM. CSV quoting supports commas and embedded quotes. Blank lines are ignored;
missing, duplicate, reordered or additional columns and incorrect row widths fail.

- Parse timezone-aware timestamps to UTC; preserve blank timestamps. Reject malformed or
  naive values, invalid impacts/precision, duplicate/nonempty event IDs and dedupe keys,
  exact rows without parseable releases, and ranges without ordered window ends.
- Parse both date columns and all UTC timestamp columns, including provenance timestamps.
  Validate impact rank against impact and the boolean point-in-time marker. Nonexact rows
  retain blank release timestamps. Exact UTC dates must agree with the release date.
- Keep retrospective result strings separate from the schedule interface. The explicit
  `EventResults.from_csv` accessor is not called by the runner or strategies.
- Return the SHA256 of the same bytes that were parsed; load once per run.
- Emit counted warnings (or errors under `quality_errors`) for exact rows labelled
  `00:00:00`/`23:59:59`, UTC weekends, and source-boundary composition changes. Record High
  counts per source/year. Source composition warnings compare providers present before/after
  configured boundary dates. Emit counted warnings when uncertain rows are explicitly skipped.
- Coverage is the envelope of represented dates/window ends in the loaded file, with the
  research start additionally capped at 2020-01-02. A blank UTC date uses the supplied local
  date for the existing conservative day policy; it never creates a release timestamp.
  UTC-weekend checks use explicit UTC dates/timestamps, not inferred local-date conversions.

## Verification

Tests live in `tests/data/news/test_schedule.py`, `tests/engine/test_news.py` and
`tests/tools/test_news_diagnostics.py`, `tests/data/news/test_loader.py` and
`tests/tools/test_research_news.py`; the prior test-case list is
`briefs/v24e-test-cases.md`. They use hand-built schedules and CSVs generated by tests.
Existing golden files are
not regenerated. Run `pytest -q tests/data tests/tools tests/engine` and capture output in
`results/pytest_v24e2.log`. Real-calendar validation and user acceptance remain outstanding.

## Cleaning

`python -m backtester.tools.news_clean SOURCE.csv [--out data/news/economic_events.csv]` writes a
cleaned copy and never modifies the source. Rule set by the user, 2026-10-27: rows with
`time_precision` second/minute and `time_label` 00:00:00 or 23:59:59 lost their real release time
in the source (the source clock is Asia/Tehran, so 00:00 is 20:30/19:30 UTC of the previous day).
They become day-only rows on the local date: precision `date`, blank timestamp and time label,
`scheduled_date_utc` = `scheduled_date_local`, and a note appended to `point_in_time_note`; the
`block_day` policy then treats them as day events. Weekend rows are kept (after the rule most move
to their real weekday; the rest are real weekend releases, harmless because no market trades then).
All other rows are copied unchanged (columns, order, values, BOM, line ending). The tool prints
rows in/out, rows changed by impact and the loader's quality counters on the output.

Imputation (rule set by the user, 2026-10-27): a day-only row produced by the rule above gets the
usual release time of the same event. Siblings are the exact, non-suspicious rows of the whole file
with the same `event_name`, `currency` and `country` (schedules are known in advance, so using
later occurrences is no lookahead). Their release times are converted to wall-clock time in the
event's home zone (country -> IANA zone: US America/New_York, EU/DE Europe/Berlin, GB
Europe/London, JP Asia/Tokyo, AU Australia/Sydney, NZ Pacific/Auckland, CA America/Toronto, CH
Europe/Zurich, CN Asia/Shanghai, KR Asia/Seoul, MY Asia/Kuala_Lumpur, IN Asia/Kolkata, SE
Europe/Stockholm, NO Europe/Oslo; other countries, e.g. GLOBAL: no imputation). The mode of the
local times is used if there are at least 3 siblings and the mode covers at least 60 % of them
(`ImputeConfig`); otherwise the row stays day-only. The imputed row keeps its own local date, gets
that local time converted to UTC with zoneinfo (DST-correct), `scheduled_date_utc` = its UTC date,
precision `minute`, `time_label` = the local time (HH:MM), and the note gets "; release time imputed
2026-10-27 from N of M occurrences (HH:MM zone)". Applies to High and Medium rows alike. The tool
also prints imputed rows and rows left day-only, each by impact.
