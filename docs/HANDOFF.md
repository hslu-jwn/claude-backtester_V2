# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

**Several sessions share this checkout.** Before committing: `git status` / `git pull`, stage only your own files,
never `git add -A` over another session's changes. If another session ends later, it merges its section here.
At this session's end `engine/backtest.py`, `engine/costs.py`, `analytics/metrics.py` still had another session's
uncommitted changes (likely 12.8 slippage) — not ours, left alone.

## Last session, strategy / live chat (2026-10-17 evening: polish, dry run, 7.4, 7.5)
- Live page polish: empty trades chart without axes, dark Connection dropdowns, readable symbol labels; ruff RUF007.
- Dry run: Test connection now uses the terminal's logged-in account when nothing is typed or saved (no login is
  saved in the Credential Manager; the bot does the same). FTMO-Demo, DEMO, algo trading allowed.
- Bot: started without the empty console window (closing that window killed the bot on 2026-10-17);
  "Close all & stop" greyed out while stopped; warm-up history re-fetched until it reaches the last quote
  (`stale_history` warning otherwise; US500 / NAS100 came back a day short at the first start).
- **7.4 ☑** chart page dark, light-blue chart pane, side panel (newest backtest, overlay switches, trades in view,
  collapsible). **7.5 ☑** "⟳ Update data" button (MT5, Binance, new histdata months; background, nothing at app
  start); the chart shows MT5 bars after a symbol's last histdata day, backtests stay on one feed. First real
  update: 28 updated, 0 errors (caches to 2026-10-16).

## Accepted by the user (do not ask again)
- Everything above (2026-10-17). Decisions: histdata months keep being added for the 5 core symbols; histdata
  caches > 93 days old are not kept current; `end_of_data` = "open" in Trades in view; overlays only in the side
  panel; newest run = newest run id; "Close all & stop" disabled while stopped.
- Earlier: ROADMAP 7.1-7.3, 11.x studies, FTMO swap defaults, data split cut-off 2021-09-14, strategy 6 =
  forward-test candidate; strategy 1 paused, 2 / 4 parked, 3 dropped; tests first, small commits, no PR.

## Open (needs the user)
1. **First live demo day, Monday 2026-10-19:** laptop on and awake 15:25-22:00 Swiss time; open
   http://localhost:8050/live (start the app with `python -m backtester.ui.app` if it is not running), check
   Connection › Test connection, press Start before 15:30. Watch the heartbeat, the log (no `stale_history`)
   and Telegram. The user decides how long the forward test runs.
2. Knowledge chat's open points (12.8 slippage question, books, 11.11 / 11.12, gap momentum).
- **Known issues / polish:**
  - "Updated …" status overlaps the Update button on narrow windows; no "MT5" marker at the feed switch yet;
    replay bar and ⚙ dialog on the dark chart page not checked visually.
  - The settings panel shows cost fields only for the 5 strategy symbols.
  - `engine/backtest.py`, `engine/costs.py`, `analytics/metrics.py` hold another session's uncommitted ruff
    reformatting (user: leave them). Untracked `.vscode/`.
  - The empty folders `data/raw/histdata_2021_*` can be deleted by the user.

## Next step
The first live demo day (open point 1). The first session after it reviews the day's trades against the paper log.

## First prompt for the next chat
`Continue.` (first demo day / review it) — or `Continue.Knowledge` for the research.
