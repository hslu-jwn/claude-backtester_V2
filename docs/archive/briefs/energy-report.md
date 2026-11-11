# Brief: strategy 12 `energy_report` (oil around the weekly EIA petroleum report): spec + code, no run

You work in the lane worktree `bt-lane-energy_report` (branch `lane/energy_report`). Read `AGENTS.md`
first; hard limits apply (no commits, no servers, no `live/`, no `.env`). A lane may change only
`src/backtester/strategy/energy_report/`, `docs/strategy-energy_report.md`, `tests/strategy/energy_report/`,
`research/grids/energy_report*.toml` (`python -m backtester.tools.lanes check energy_report`). The registry
entry is done by the coordinator: list what it needs. Do NOT run the grid (pre-registration first).

## Idea (sources: `knowledge/research/reports/2026-11-10_idea_harvest_broad.md` ideas 1, 4, 9)

Weekly EIA Weekly Petroleum Status Report, normally Wednesday 10:30 America/New_York. Indriawan et al.
(2021, SSRN 3822093, abstract only): intraday predictability in crude oil from the report window to the
session close. Rousse and Sevi (SSRN 2874907, abstract only): partial reversal after the announcement.
Label PUBLISHED lead, SPECULATIVE rules.

## Rules to specify (write `docs/strategy-energy_report.md`, copy `strategy/_template/`)

- Symbols USOIL (primary), UKOIL (breadth). Data 2015-2021 histdata (`data/cache/histdata/`); note the
  documented 2020 oil jumps.
- Report day: Wednesday; a week with a US federal / NYSE holiday on Monday-Wednesday is skipped (the
  release shifts; the real schedule is not in the repo). Record as an assumption.
- Reaction R = log(close at 10:45 / close at 10:29) NY time, scaled by the daily ATR (14, finished
  regular D1 bars, 17:00 NY days, weekend stubs excluded).
- Families: F (follow): |R| >= k x ATR -> trade in R's direction at the 10:45 close, exit at the candle
  closing 14:30 NY. V (fade): |R| >= k -> trade against R, exit 13:00 NY. Stop `stop_atr` x ATR from entry.
  Cells: k {0.15, 0.30} x stop_atr {0.5, 1.0} per family = 8 cells per symbol. Primary: F, k 0.15, stop 1.0.
  Control: the same rules on non-report Wednesdays (gate 3, disjoint).
- Gates (fixed before any run, pattern `tools/timed_hold_gates.py` / `docs/strategy-timed-hold.md` ›
  Gates): net R > 0 normal and doubled costs; both halves; report days minus disjoint control bootstrap
  2.5 % > 0; breadth UKOIL net > 0; best 5 dates removed > 0; min 150 trades; gate 7 integrity with the
  rollover tolerance. Family-wise level reported.
- Trades never cross the rollover (exit before 17:00 NY): no swap.

## Code

Strategy folder, config dataclass with these fields (defaults = primary cell), tests first (report-day
calendar incl. holiday weeks, reaction threshold, follow / fade direction, exits, stop, no lookahead:
appending future candles never changes earlier orders), grid `research/grids/energy_report.toml`
(diagnostics off like the timed_hold grids). If an existing gates tool fits with a flag, say how; else
note what the coordinator must add. `python -m pytest tests/strategy/energy_report -q` green, ruff clean.
Report files, the registry line needed, and every assumption.

## Decisions by Opus (2026-11-10, after Codex's questions, before any code or run; record as assumptions)

1. Reaction threshold in price units: |close(10:45) - close(10:29)| >= k x ATR (ATR in price units); the
   direction is the sign of that difference.
2. Control (gate 3): the same clock rules on Tuesdays and Thursdays (non-report days; skip a day with a
   NYSE full closure), disjoint from the report Wednesdays. Implement as a config switch
   (`days = "report"` / `"control"`), with the grid running both.
