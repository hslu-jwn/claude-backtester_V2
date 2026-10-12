# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

## Last session (2026-10-12): cleanup C.1-C.4 and strategy 2 in the app (8.6a)
- Done and accepted by the user: C.1 Dukascopy removed (`data/cache.py`), C.2 MT5 path test skip, C.3 strategy registry
  + `strategy/_template/` + shared detector settings (`RunSettings.detectors`), C.4 layer fixes (`tools/`, `paths.py`,
  `tests/test_layers.py`, `CsvAdapter` removed, trading symbols = all five), 8.6a (strategy popover lists both strategies;
  settings panel, presets and backtest follow the pick; Trades overlay is strategy 1 only for now).
- Checks: 971 tests pass; ruff clean except RUF007 in `core/series.py` (old, left alone: lookahead-critical file);
  strategy 1 and 2 `trades.csv` byte-identical before/after (short fixed runs on copied cache).
- Decisions: shared detectors = swings, FVG, order block, equilibrium; `confluence_kinds` stays per strategy;
  old preset JSON is migrated on load; presets are listed per strategy ("Default" is in both); `overlay_drawings`,
  `selected_overlays`, `RETCODE_DONE_PARTIAL`, `delete_credentials` stay (tests / documented codes / planned feature).
- Environment (local, not the repo): the user's `.venv` was reinstalled editable from this folder. A stale app server
  from another checkout (OneDrive `...\TradingBot\V1_forex\repo\backtester-claude`) was still listening on port 8050,
  so the user saw the old app: stop it or use `--port 8051`. Strategy 2 needs the NAS100 / US500 cache:
  `python -m backtester.data.histdata data/raw/histdata/` (NAS100 was imported, US500 import not confirmed).

## Accepted by the user (do not ask again)
- The ROADMAP order and the cleanup backlog as written; C.1-C.4 and 8.6a are done.
- Tests first, small commits on the session branch, no PR unless asked.
- Strategy 1 is paused; the liquidity sweep and the best-time tag are reworked by the user (code untouched until he says).
- Not done on purpose: splitting `ui/pages/chart.py` (1,393 lines) and `tools/check.py` (669 lines).

## Open (needs the user)
- Sweep rework: the threshold for "not significant" (percent / ATR / points) is to be agreed before implementing.
- Best-time tag removal and the window settings (ROADMAP 8.3 / 8.4) wait for his go.
- US500 cache: confirm the import ran (`python -m backtester.tools.check NAS100 US500`).

## Next step (suggested)
8.6b (Trades overlay for strategy 2: 3 TPs, route / entry / confluence hover) then 8.6c (AM/PM session view), both visual
steps the user checks locally; or the sweep rework discussion (the user decides). After that 6.1 Strategy Simulator.

## First prompt for the next chat
`Continue.`
