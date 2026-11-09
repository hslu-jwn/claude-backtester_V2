# Brief: multi-day holds in strategy 10 `timed_hold` (hypothesis 9, F4M)

Read `AGENTS.md` first (no lookahead, test first, frozen config); its hard limits apply (no
commits, no servers, no `live/`, no `.env`). Spec: `docs/strategy-timed-hold.md` › Hypothesis 9
(read it) and › Definitions / Rule.

## Files

- `src/backtester/strategy/timed_hold/` (config.py, strategy.py, day_filter.py)
- `tests/strategy/timed_hold/test_timed_hold.py` (tests first)
- `docs/strategy-timed-hold.md` › Definitions: bullets for the new fields
- New grids `research/grids/timed_hold_tom_multi.toml` (US500, NAS100: TOM + control) and
  `research/grids/timed_hold_tom_multi_world.toml`-style breadth grids as listed below
- Do NOT change `strategy/session_stats.py` (`TimedExit` is shared with strategies 5 and 7): keep the
  multi-day exit logic inside `timed_hold`.

## New config fields (defaults keep today's behaviour exactly)

- `hold_days: int = 0`: 0 = today's same-day rule (exit_time must be after entry_time). > 0: the trade
  exits at the close of the candle closing at `exit_time` on the trading day that is `hold_days`
  trading days after the entry day (or the first later candle if that one is missing); then
  `exit_time <= entry_time` is allowed.
- `trading_days: str = "weekdays"`: "weekdays" (Monday-Friday) or "nyse" (Monday-Friday minus NYSE
  full closures from `calendars/nyse_holidays.csv`; early closes ARE trading days). Used for
  `hold_days` counting and for `month_day`.
- New `day_filter` value `"month_day"` with `month_day: int = 0`: negative = counted from the month's
  end (-1 = last trading day, -4 = 4th-to-last), positive = from its start (1 = first trading day,
  8 = 8th). `month_day` must be non-zero when `day_filter == "month_day"`.
- One position at a time: no new entry while a multi-day trade is open (state per instance).
- The daily ATR (stop) is unchanged: the finished-sessions ATR at the entry.

## Grids (all `monkeys = false`, `sensitivity = false`, `entry_screen = false`, min_trades 60)

`[base]` common: `direction = "long"`, `day_filter = "month_day"`, `hold_days = 6`,
`[grid] stop_atr = [2.0, 3.0]` and `month_day = [-4, 8]` (TOM and control; 4 cells per grid).
- `timed_hold_tom_multi.toml`: US500, NAS100; zone / atr_zone America/New_York, entry_time = exit_time
  = 16:00, atr 09:30-16:00, `trading_days = "nyse"`.
- `timed_hold_tom_multi_uk.toml`: UK100; Europe/London, 16:30, atr 08:00-16:30, weekdays.
- `timed_hold_tom_multi_de.toml`: GER40; Europe/Berlin, 17:30, atr 09:00-17:30, weekdays.
- `timed_hold_tom_multi_jp.toml`: JP225; Asia/Tokyo, 15:00, atr 09:00-15:00, weekdays.
Check each symbol's cache covers 2015 (GER40 ends 2020-06; that is fine). Do not run the grids.

## Tests (write first)

`hold_days` = 1 and 6 exit on the right day / time (incl. a weekend and an NYSE holiday inside the
hold with "nyse"; a missing exit candle -> first later candle); `hold_days = 0` unchanged (all existing
tests green); `month_day` -4 / -1 / 1 / 8 pick the right dates incl. a month whose last day is a
holiday or weekend; no second entry while a trade is open; config validation of the new fields; no
lookahead (appending future candles never changes earlier orders).

## Done =

`python -m pytest tests/strategy tests/tools tests/ui tests/engine/test_ticks.py -q` green (if the
settings-panel widget limit fails, add the new research-only paths to timed_hold's hide list in
`ui/settings_panel.py` `_panel_symbol`), `python -m ruff check .` clean. Report files, tests, and
anything unclear (quote the spec line).
