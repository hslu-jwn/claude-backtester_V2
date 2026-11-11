# Brief: `day_filter = "gotobi"` in strategy 10 `timed_hold` (hypothesis 11)

Read `AGENTS.md` first (no lookahead, test first, frozen config); hard limits apply (no commits, no
servers, no `live/`, no `.env`). Spec: `docs/strategy-timed-hold.md` › Hypothesis 11 (read it; the
"Gotobi day" bullet is the rule).

## Files

- `src/backtester/strategy/timed_hold/` (config.py validation, day_filter.py), its tests (tests first),
  `docs/strategy-timed-hold.md` › Definitions › Qualifying day: one bullet for `gotobi`.
- Calendar exists: `src/backtester/strategy/timed_hold/calendars/jp_holidays.csv` (date,type,source_url).
  Load it only when `day_filter == "gotobi"` (like the other files). Do not edit it.
- Grid exists: `research/grids/timed_hold_gotobi.toml`; it must load and expand (check with the runner's
  grid loader in a test or a dry parse); do not run it. Do not change shared code.

## Rule

`qualifies(day)` for `gotobi` (day = the entry candle's local date in `zone`, here Asia/Tokyo): True when
`day` is the gotobi day of a target date 5, 10, 15, 20, 25 or the month's last calendar day. Gotobi day =
the target date if it is a Tokyo business day, else the nearest earlier Tokyo business day (may fall in
the previous month for the 5th, e.g. after New Year). Tokyo business day = Monday-Friday, not in
jp_holidays.csv, not Dec 31 / Jan 2 / Jan 3. Independent of `trading_days` (NYSE calendar not used).

## Tests (first)

Hand-checked dates: a plain weekday 10th; a Saturday 25th -> Friday 24th; a Sunday 5th -> Friday 3rd; a
holiday target (e.g. 2019-05-05 Sunday and the Golden Week 2019 run -> 2019-04-26 Friday); Jan 5 when
Jan 2-4 are around a weekend; month-end on the 31st Saturday -> Friday 30th; 2020-02-29 (leap, Saturday)
-> 2020-02-28; a non-gotobi weekday is False; Dec 31 never qualifies. A strategy-level test: on a
hand-built USDJPY M1 series in Asia/Tokyo, a 03:00 -> 09:55 long fires only on gotobi days; no lookahead
(appending future candles never changes earlier orders); existing tests unchanged. Also report what the
strategy does when the entry candle is missing (e.g. Monday 03:00 JST = Sunday 18:00 UTC): expected no
trade that day.

## Done =

`python -m pytest tests/strategy tests/tools tests/ui tests/engine/test_ticks.py -q` green (settings-panel
widget limit: hide new paths like timed_hold's others if needed), `python -m ruff check .` clean. Report
files, tests, anything unclear (quote the spec line).
