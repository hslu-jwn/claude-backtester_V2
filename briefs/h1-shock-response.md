# Brief: strategy 11 `h1_shock` from candidate INTRADAY_H1_SHOCK_RESPONSE v0.1.0

Read `AGENTS.md` first (no lookahead, test first, frozen config, one code path by Direction); its
hard limits apply (no commits, no servers, no `live/`, no `.env`). Model the folder on strategy 10
(`src/backtester/strategy/timed_hold/`, `tests/strategy/timed_hold/`), reuse
`strategy/session_stats.py` (`TimedExit`) and the NYSE calendar loader in
`strategy/timed_hold/day_filter.py` (import it; do not copy the CSV).

## Source of the rules

`research/candidates/INTRADAY_H1_SHOCK_RESPONSE__v0.1.0.json` (sections hypothesis, market, data,
math, entries, exits, risk, experiment) and its record `knowledge/research/records/R-2026-004*.md`.
Quote the JSON rules in the spec; do not reinterpret them.

## Deliverables

1. **Spec draft** `docs/strategy-h1-shock.md` (before code), in the style of
   `docs/strategy-timed-hold.md`: Definitions (local-clock H1 event bars from M1, robust z per
   symbol and local clock hour, cost multiple, trade side by response mode), Rule, Exits, the 18-cell
   grid exactly as `experiment.total_grid_size` / parameters, the primary cell (k = 3.0, h = 1) and
   the rejection criteria from `experiment` (copy them as gates), and an **Assumptions** section
   listing every point you had to decide. Session exclusions (the former blocker), use these
   (decided by Opus 2026-11-09, write them as assumptions):
   - NAS100, US500: New York clock; eligible event bars and holding intervals only inside NYSE
     regular hours 09:30-16:00 on NYSE trading days, excluding 09:30-10:00 (opening) and
     15:30-16:00 (final 30 minutes); skip NYSE full closures and early-close days.
   - XAUUSD, GBPUSD, GBPJPY: London clock; weekdays; exclude 21:00-23:59 London (rollover / daily
     reopen) and the first 2 hours after the Sunday reopen; no other holiday calendar.
   - The robust-z normalization uses only completed event bars before the signal (no lookahead).
2. **Strategy** `src/backtester/strategy/h1_shock/` (config, strategy), registered in
   `strategy/registry.py` as "Strategy 11 · H1 shock response", plus every list that enumerates
   strategies (grep tests and tools for `"timed_hold"` to find them: registry tests, settings-panel
   tests, `tools/golden.py` + `python -m backtester.tools.golden --write --strategy h1_shock`,
   `tools/risk_sweep.py`, `tools/entry_screen.py` STRATEGY_SYMBOLS). If the settings-panel widget
   limit test fails, hide this strategy's research-only fields the way timed_hold's are hidden in
   `ui/settings_panel.py` `_panel_symbol`.
3. **Tests first** `tests/strategy/h1_shock/test_h1_shock.py`: event detection on hand-built
   candles, robust z from past bars only (appending future candles never changes earlier signals),
   both response modes, stop distance, time exit after h hours, each session exclusion, NYSE
   closure skip, one position per symbol, DST for both clocks.
4. **Grid** `research/grids/h1_shock.toml` with all 18 cells, `monkeys = false`,
   `sensitivity = false`, `entry_screen = false`, symbols as in the JSON.

Do NOT run the research grid (Opus reviews the spec first).

## Done =

`python -m pytest tests/strategy tests/tools tests/ui -q` green, `python -m ruff check .` clean.
Report (max 300 words): files, tests, every assumption you added beyond the list above, anything
in the JSON you found ambiguous (quote it).

## Decisions on the questions of the first dispatch (Opus, 2026-11-09; write them as assumptions)

1. **Stale / non-advancing OHLC record:** a run of >= 15 consecutive M1 candles that are flat
   (open = high = low = close) at one unchanged price inside an eligible window. An H1 bar that
   contains such a run is invalid. Single or short runs of identical bars are legitimate.
2. **Expected-M1 schedule = the session rules above** (they replace the missing authoritative CFD
   calendar for entry exclusions, integrity checks and the normalization window W60 alike):
   - NAS100, US500: every minute of 09:30-16:00 New York on NYSE trading days (full closures and
     early-close days are not trading days for this strategy).
   - XAUUSD, GBPUSD, GBPJPY: every minute of Monday-Friday 00:00-21:00 London. The Sunday reopen
     (about 22:00 London) plus 2 hours ends at Monday 00:00 London, so no Sunday minute is eligible;
     21:00-23:59 London is excluded every day.
   - An H1 event bar is **valid** only if it has >= 55 of its 60 expected M1 candles, no run of more
     than 5 consecutive missing minutes, and no stale run (1.). Invalid bars are neither events nor
     part of W60; W60 counts only valid bars.
   - An entered trade whose holding interval later breaks these rules is kept and reported (the
     gate tool's integrity count), not dropped; the JSON's "TEST_FAILED" applies to the experiment
     report, not to the backtest.
