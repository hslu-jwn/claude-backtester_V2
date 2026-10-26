# Brief: V2.5a — dark theme, page skeleton, top bar (look only, content stays)

Context: ROADMAP › V2.5 (decisions of the user 2026-10-23 in `docs/design/ui-proposal.md`; read
it fully, its tables are the accepted list). Reference look: `docs/design/app-v2.png` (dark
trading terminal: near-black background, thin dividers, a compact row of key numbers above a
large chart, a side panel on the right, tabs below the main area, green / red accents, little
text). No brand names or logos from the picture. This brief is the **foundation**; the pages
follow in V2.5b (Research), V2.5c (Chart, Results), V2.5d (Backtest, Live).

## What to build

1. **Design tokens** in one stylesheet (`ui/assets/theme.css`, loaded first): background,
   panel, raised panel, line, text, muted text, green (profit / up), red (loss / down), amber
   (warning flags only), accent (focus / selected tab); font sizes (12 / 13 / 15 / 20), spacing
   steps (4 / 8 / 12 / 16 / 24), radius 6. Dark only (user decision): remove light rules and
   any light switch. Every existing page uses the tokens (replace hard-coded colours in
   `ui/assets/*.css`, inline styles in `ui/pages/*.py`, `chart_config.py` colours for the
   chart background / grid / text; candle and overlay colours stay).
2. **Shared skeleton helpers** (`ui/layout.py`): `page(strip, main, side=None, tabs=None)`,
   `key_strip(items)` (label + value + optional green/red sign colour + optional tooltip),
   `details(summary, children)` (native `html.Details`, closed by default, styled),
   `info(text)` (small "i" with the text as tooltip), `tabs_below(...)` (dcc.Tabs styled like
   the reference). Pages adopt them in V2.5b-d; in this brief use them only for the top bar.
3. **Top bar** (`ui/nav.py`): `BACKTESTER` as plain text, tabs `Chart | Backtest | Research |
   Live` (Risk tab: merged into Backtest by the user's decision 2026-10-23, so remove the grey
   "Risk" tab and `pages/risk.py` stub; Portfolio comes with V2.7, not now), right side: bot
   status chip (dot + short text, Live tab red while the bot runs, as today), the "Update data"
   button moved here from the chart toolbar (`update_button.py`, its status line as tooltip,
   shown while running), and a settings gear opening the existing MT5 / Telegram connection
   settings (today in Live › Settings fold) — moving the gear is look only; the connection form
   itself stays where V2.5d puts it.
4. Remove "← Chart" links (the top tab does it).

## Answers given up front (Opus, 2026-10-24)

- No new dependencies (no dash-bootstrap, no new fonts from the internet); plain Dash + CSS.
- Keep every element id that callbacks or tests use; restyle, do not rename. If an id must
  change, update its callback and test in the same change and list it.
- Charts (Lightweight Charts in `chart.js`, Plotly figures): background / grid / axis text from
  the tokens; series colours unchanged.
- Never start a server and leave it running (AGENTS.md); for a visual check run the app
  briefly from a test client or render the layouts in tests. Opus does the browser check.

## Rules

Test-case list first: every page layout renders without error (Dash layout functions called in
tests); the top bar has exactly the four tabs and the right-side items; no hard-coded colour
remains in `ui/assets/*.css` outside `theme.css` (a test greps hex colours, allow-list for chart
candle / overlay colours); `details()` is closed by default; ids used by callbacks still exist.
Run only the UI tests (`pytest -q tests/ui > results\pytest_v25a.log 2>&1`); Opus runs the full
suite. Never edit `src/backtester/live/` (UI files under `ui/` are fine).

Done = UI tests green, `ruff check .` clean. Report: files changed, ids changed (if any),
decisions the proposal did not settle, open questions.
