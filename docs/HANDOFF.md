# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

**Several sessions share this checkout.** Before committing: `git status` / `git pull`, stage only your own files,
never `git add -A` over another session's changes. If another session ends later, it merges its section here.
At this session's end `engine/backtest.py`, `engine/costs.py`, `analytics/metrics.py` still had another session's
uncommitted changes (likely 12.8 slippage) — not ours, left alone.

## Last session, strategy / live chat (2026-10-17, UI clean-up)
- **ROADMAP 7.3 ☑** (spec `docs/live-trading.md` › App layout and Live page; mockups `docs/ui-mockups/`,
  inspiration only):
  - Top bar Chart · Backtest · Risk · Live on every page. The Live link is red while the bot runs, and the app
    opens on `/live` when the bot runs.
  - ⚙ holds only the chart / backtest settings, as one collapsible block; the Sweep menu moved in there.
  - The account connection (MT5 + Telegram) moved to `/live` › Connection.
  - The new `/live` page has Start / Pause / Stop / Close all & stop; risk %, daily stop and symbols are editable
    only while the bot is stopped. It shows balance / equity in USD, today against the daily stop, the FTMO limits,
    the session countdown, the heartbeat, the setup funnel per symbol, positions, a recent-trades strip
    (Day / Week / All), signals and the log. All times are in Swiss time.
- **Bot:** a `results/live/PAUSE` file means no new entries (open trades still managed; paused breakouts are
  skipped for the day). New status fields: paused, risk_percent, strategy, session, setups. Fix: the
  `--daily-stop` default was broken (slots dataclass).

## Accepted by the user (do not ask again)
- Everything above ("End." 2026-10-17). Decisions: no separate start page; settings only editable when stopped;
  Telegram always on (no switch); Backtest link = newest run; Risk greyed until its page exists; Swiss time on
  the Live page; paused signals skipped for the day; chart restyle is a later step (7.4).
- Earlier: ROADMAP 7.1, 7.2 (built), 11.x studies, FTMO swap defaults, data split cut-off 2021-09-14, strategy 6 =
  forward-test candidate; strategy 1 paused, 2 / 4 parked, 3 dropped; tests first, small commits, no PR.

## Open (needs the user)
1. **First live demo day:** open `/live`, check Connection (test connection), then press Start before the US open
   (15:30 Swiss time); laptop on and awake 15:25-22:00. The user decides how long the forward test runs.
2. **7.4 chart page in the new style** (after the first live days): side cards, timeframe buttons, range bar.
3. Knowledge chat's open points (12.8 slippage question, books, 11.11 / 11.12 = stationarity, gap momentum).
- **Known issues / polish:**
  - The empty trades chart on `/live` shows odd axes (−1..6), and the Connection dropdowns may look light on the
    dark page.
  - ruff RUF007 in `core/series.py`.
  - The settings panel shows cost fields only for the 5 strategy symbols.
  - Untracked `.vscode/` and a stray file `C…Usersjusti.claudeclaude-notify-signalsstop` in the repo root (not
    ours).
  - The empty folders `data/raw/histdata_2021_*` can be deleted by the user.

## Next step
The first live demo day (open point 1): start the app, check the Connection on `/live`, press Start before
15:30 Swiss time and watch the page and Telegram. The first session after it reviews the day's trades against
the paper log.

## First prompt for the next chat
`Continue.` (first demo day / review it) — or `Continue.Knowledge` for the research.
