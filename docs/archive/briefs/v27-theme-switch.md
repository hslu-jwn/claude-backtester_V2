# Dark / bright mode switch (user, 2026-10-27)

Colours only. No logic, layout, data or behaviour changes anywhere.

## What the user asked

- A **dark / bright mode switch in the shared top bar, on the right, next to "Update data"**
  (`src/backtester/ui/update_button.py` builds that button; find where the top bar is assembled).
  One small button or toggle, same look as the other top-bar controls; its title explains it.
- **Dark mode = today's look, unchanged**, except the chart candles: **bright green up and bright
  red down**: up `#22c55e`, down `#ef4444`, for body, border and wick alike (today: up body
  `#6f9ceb`, down body / border / wick `#000000`, `ui/chart_config.py` ~line 56).
- **Bright mode = white background**, light panels and dark text, close to how the app looked
  **before the V2.5 dark redesign** (`git show ba05aab~1:<path>` shows the pre-redesign files;
  `ba05aab` introduced `ui/assets/theme.css` with the dark tokens). **Candles in bright mode stay
  exactly as today** (up `#6f9ceb`, down / border / wick `#000000`).
- **Dark is the default.** The choice is remembered per browser (`dcc.Store(storage_type="local")`,
  like `side-collapsed` in `ui/pages/chart.py`) and applies to every page (Chart, Backtest,
  Research, Portfolio, Live).

## How (suggested; keep it small)

- Theme tokens: `ui/assets/theme.css` holds the dark tokens (CSS custom properties). Add a bright
  token set under a root class or attribute (e.g. `html[data-theme="light"]` or a class on the
  app's outer Div) and switch only that class / attribute. Grep the other `ui/assets/*.css`
  files for hard-coded dark colours that bypass the tokens and route them through tokens.
- Chart: `ui/assets/chart.js` creates the Lightweight Charts chart from `cfg` (`chart_config.py`
  -> `chart_settings`). The chart's background, grid, text and candle colours must follow the
  theme, also when switched while a chart is open (`chart.applyOptions` / `series.applyOptions`),
  without reloading data. Python-side colours that use `theme_color(...)` must not freeze the dark
  value into the chart config if the switch is client-side; pass both palettes or resolve in JS.
- Plotly figures (Results / Research / Portfolio pages) if they hard-code a dark template: give
  them the matching light template in bright mode, or at least a readable background.

## Rules

- Test first: write the tests before the code (pytest, `tests/ui/`). At least: the top bar has
  the switch next to Update data; the theme store defaults to dark; both candle palettes have the
  values above; bright mode tokens define a white background; a page build changes nothing else.
  Never weaken an existing test; if one breaks for a reason that is not "colour", stop and report.
- Run only the tests of what you changed (`.venv/Scripts/python.exe -m pytest tests/ui -q -p
  no:cacheprovider`) and `ruff check .` / `ruff format` on changed files.
- Do NOT start the app or any server, do not commit, push or create branches, do not touch
  `src/backtester/live/`, `.env` or credentials. Do not edit `ui/chart_side.py` or the
  `run-trades-*` parts of `ui/pages/chart.py` (just changed by Opus).
- Windows: use the project venv `.venv/Scripts/python.exe`; no PowerShell backticks.
- Report: files changed, what each change does, test results, anything unclear.
