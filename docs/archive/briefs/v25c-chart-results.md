# Brief: V2.5c — Chart and Results pages in the new skeleton

Context: ROADMAP › V2.5 (decisions of the user 2026-10-23, `docs/design/ui-proposal.md` › Page:
Chart and › Page: Results; read both tables fully, they are the accepted list). V2.5a (ba05aab)
gave the dark tokens and the helpers in `ui/layout.py` (`page`, `key_strip`, `details`,
`info`, `tabs_below`); V2.5b (382612a) the Research cards. Reference look:
`docs/design/app-v2.png`. Look and clarity only: every control and number stays reachable.

## What to build

**Chart page** (`ui/pages/chart.py`, `chart_side.py`, `ui/assets/chart*.css`, `toolbar.*`):
1. Chart header row: symbol dropdown, timeframe buttons, replay / zoom icons, camera menu (as
   today, restyled compactly; "Update data" already moved to the top bar in V2.5a).
2. **Key strip above the chart** from the newest run (today's "Backtest result" card): Net R,
   Win rate, Trades, Max drawdown, "Results →" link; the run id as a tooltip; dashes without a run.
3. **Side panel** right of the chart: "Trades in view" (as today).
4. **Tabs below the chart** (Opus decision of 2026-10-23): `Trades` (the newest run's trades,
   compact rows, click opens the trade on the chart as the side list does), `Overlays` (master
   switch essential; the type switches inside `details()`), `Backtest` (the run form: Symbols,
   Days, Preset, Run, status — moved out of the toolbar popover), `Strategy` (strategy dropdown
   + "Settings…" button opening the existing settings modal). The toolbar popovers for these go.
5. Chart settings popover (gear): Session lines essential; the rest in `details()`; long notes
   -> `info()` tooltips.
6. Strategy settings modal: groups as collapsible sections, first open, rest closed; per-field
   notes -> tooltips. Nothing removed.

**Results page** (`ui/pages/results.py`, `prop_firm_card.py`, `results.css`):
7. Row above the strip: run selector + symbol radio. Header: title + Symbols + Days; Preset,
   Run date, notes in `details()`.
8. **Key strip**: Net R, Trades, Win rate, Profit factor, Max drawdown, Expectancy, Prop pass %
   (middle risk level of the prop card). The other overview cards (Avg R:R planned, Avg realized
   R, Avg win / loss, Longest losing streak, gross values) go into `details()`; their sub-texts
   become tooltips.
9. Equity curve large in the main area; **side panel** = prop-firm card (pass % prominent, full
   table in `details()`, the how-text as `info()`, Monte Carlo button / progress / open report).
10. **Tabs below**: `Trades` (default; essential columns time, symbol, side, R net, exit; the
    rest via a "More columns" toggle), `Performance` (summary table, per year; per quarter and
    the R histogram in `details()`), `Overview details`.
11. Also show, when the run folder has them (V2.4d / profile outputs: `skill_bounds.json`,
    `drawdown_bounds.json`, `profile.json`): a compact "Skill vs trend" line and the best
    condition in the Performance tab; "–" otherwise.

## Answers given up front (Opus, 2026-10-24)

- Keep every id used by callbacks / `chart.js` / tests; when an element moves into a tab, keep
  its id. If an id must change, update its callback, JS and test together and list it.
- The chart canvas must keep its size behaviour (Lightweight Charts resizes with its
  container); tabs below must not shrink the chart below 420 px height at 900 px viewport.
- Replay, trade focus (`/?symbol=…&entry=…`), presets and the backtest job must work exactly as
  before (existing tests).
- No new dependencies. Never start a server and leave it running (AGENTS.md); Opus does the
  browser check.

## Rules

Test-case list first: each page renders; the moved controls exist once (no duplicate ids); key
strip values from a fixture run; tabs present with the right default; `details()` closed by
default; the trade-focus URL still selects symbol / timeframe; the backtest form in the tab
starts a job like the popover did (existing callback tests). Run only the UI tests
(`pytest -q tests/ui > results\pytest_v25c.log 2>&1`); Opus runs the full suite. Never edit
`src/backtester/live/`.

Done = UI tests green, `ruff check .` clean. Report: files changed, ids changed, decisions the
proposal did not settle, open questions.
