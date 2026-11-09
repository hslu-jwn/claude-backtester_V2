# Brief: gap-tolerant integrity gate + skip NYSE short days (the user's decision 2026-11-09)

Read `AGENTS.md` first; its hard limits apply (no commits, no servers, no `live/`, no `.env`).
Decision recorded in `docs/HANDOFF.md` › Accepted (2026-11-09, item 6). Background:
`docs/strategy-timed-hold.md` › Results (data diagnosis: US500 histdata omits quiet minutes; holiday
exits slip past the 17:00 New York rollover).

## Part A: integrity gate (`src/backtester/tools/alternating_path_gates.py` `integrity_failures`)

- Today a trade fails when ANY M1 candle closing in (entry, exit] is missing or invalid.
- New rule: a trade fails only if (a) a run of more than `max_gap_minutes` consecutive missing
  minutes lies inside (entry, exit], or (b) the candle closing at the exit time is missing, or
  (c) any present candle is invalid (OHLC rules, unchanged). Default `max_gap_minutes = 5`.
- Keep the function signature compatible (add `max_gap_minutes: int = 5` keyword). Both gate tools
  (`alternating_path_gates.py`, `timed_hold_gates.py`) use it; `timed_hold_gates` reports the
  setting in `gates.json` settings. Update `docs/strategy-alternating-path.md` › Gates and
  `docs/strategy-timed-hold.md` › Gates (gate 7 wording) with "(the user, 2026-11-09)".
- Tests first in the existing gate test files: a 3-minute hole passes, a 6-minute hole fails, a
  missing exit candle fails, an invalid candle fails, scattered single-minute holes pass.

## Part B: `timed_hold` NYSE short days (`src/backtester/strategy/timed_hold/`)

- New config field `skip_nyse_short_days: bool = False` (`config.py`): when true, no entry on a
  date that is an NYSE full closure or early close (`calendars/nyse_holidays.csv`, types `closed` and
  `early_close_13:00`; the loader is in `day_filter.py`). Applies with any `day_filter`.
- The index grids `research/grids/timed_hold_rod*.toml`, `timed_hold_fomc.toml`,
  `timed_hold_tom.toml` set `skip_nyse_short_days = true` in `[base]` (one line each, comment
  "the user 2026-11-09").
- Spec `docs/strategy-timed-hold.md` › Definitions: one bullet for the field.
- Tests first in `tests/strategy/timed_hold/test_timed_hold.py`: a closure date and an early-close
  date give no trade with the flag, and a trade without it; the default is False.
- Do not touch `src/backtester/ui/settings_panel.py` unless the panel widget-limit test fails; if
  it does, add the path `strategy.skip_nyse_short_days` to the existing timed_hold hide list there.

## Done =

`python -m pytest tests/tools tests/strategy tests/ui tests/engine/test_ticks.py -q` green,
`python -m ruff check .` clean. Report files changed and tests.
