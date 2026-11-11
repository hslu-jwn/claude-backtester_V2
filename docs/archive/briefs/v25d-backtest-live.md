# Brief: V2.5d — Backtest and Live pages in the new skeleton, text cuts

Context: ROADMAP › V2.5 (decisions of the user 2026-10-23, `docs/design/ui-proposal.md` › Page:
Backtest, › Page: Live, › Text cuts; read them fully). V2.5a-c (ba05aab, 382612a, 29a36ab) gave
the tokens, `ui/layout.py` helpers, the Research cards and the Chart / Results pages. This
brief finishes the redesign. Look and clarity only.

## What to build

**Backtest page** (`ui/pages/backtest.py`, `backtest.css`):
1. Running job: status chip (running / done / failed / cancelled), one muted line with strategy,
   symbols, days, preset; progress bar large; Elapsed and Time left in the key strip; detail
   line (candles done of total) muted under the bar; message only on error; Cancel button at
   the strip's right.
2. List view: compact rows (Date, Strategy, Symbols, Trades, Net R green / red; Days (UTC) in a
   "More columns" toggle), header one line, toast "Cancelled".
3. The prop-firm / risk content that the user merged into Backtest (2026-10-23) stays on the
   Results page (V2.5c side panel); here only a link "Risk & prop firm: open a run's results".

**Live page** (`ui/pages/live.py`, `live_model.py`, `trading_panel.py`, `live.css`; **never**
`src/backtester/live/`):
4. Key strip: state chip + strategy + symbols / session window + countdown, Balance, Equity,
   Today (%, money, R, daily-stop bar), FTMO limits (bars), Heartbeat + MT5 connected; buttons
   Start, Pause / Resume, Stop, Close all & stop (red, its confirm dialog kept) at the right.
5. Main: the Recent trades chart (range picker kept, click opens the trade; hint -> `info()`).
6. Side panel: Setup in progress (per-symbol funnel, compact).
7. Tabs below: Open positions (default), Closed trades, Signals & skips, Event log, Settings
   (risk %, daily stop %, symbols; note -> tooltip).
8. Connection (MT5 account, Telegram, demo test orders, test connection): opened by the top-bar
   gear (V2.5a); all helper notes -> tooltips; Telegram and Demo test orders each a `details()`.
9. **Text cuts** across the app per the proposal's list (Monte Carlo how-text, settings notes,
   live connection notes, hints): one-line muted text or `info()` tooltip; no information is
   deleted, only moved into tooltips.

## Answers given up front (Opus, 2026-10-24)

- Every button keeps its callback and confirm; the bot's control flow is untouched (only
  layout files under `ui/`). Credentials fields keep their current behaviour (never shown again
  after saving, stored only in the Windows Credential Manager); do not read, print or log them.
- Keep ids used by callbacks and tests; list any change with its callback / test update.
- No new dependencies; never start a server or the bot and leave it running (AGENTS.md).

## Rules

Test-case list first: both pages render (running, done, failed, cancelled, empty list; live with
no status file, running, paused, error); buttons and the confirm exist once; tabs with the right
default; every former helper note is still present (as a tooltip `title`); no element from the
proposal's tables is missing. Run only the UI tests (`pytest -q tests/ui >
results\pytest_v25d.log 2>&1`); Opus runs the full suite.

Done = UI tests green, `ruff check .` clean. Report: files changed, ids changed, decisions the
proposal did not settle, open questions.
