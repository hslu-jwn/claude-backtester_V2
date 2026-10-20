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

## Last session, knowledge chat (2026-10-16..19): six books, deflated Sharpe, whole-software audit
- **Books:** López de Prado (AFML), Carver (*Systematic Trading*), Chan (*Algorithmic Trading*), Davey (*Building
  Winning Algo Systems*), Kurt (*Bayesian Statistics*), Kaeppel (options; the "Natenberg" PDF is really Kaeppel,
  Natenberg skipped by the user) in `knowledge/`; new topics `combining-edges.md`, `statistics-and-bayes.md`; ideas
  T-08..T-19, I-46..I-60. Research order agreed: 12.10 -> 11.11 stationarity study -> 11.12 gap momentum (I-46).
- **12.10 ☑ trial log + deflated Sharpe:** `results/trials.jsonl` written by `run.py`, the Monte Carlo tool and
  `gap_fade_grid` (`--family`, default the strategy); `python -m backtester.tools.trials list|add`; DSR >= 0.95 =
  verdict check 7 (user 2026-10-16); back-fill count-only gap_fade 36, opening_range 41.
- **Audit 2026-10-19 (read-only, demo day running):** findings in ROADMAP **Phase 13** (13.1-13.23), nothing fixed.
  Most urgent for the forward test: 13.1 bot dies silently on an unexpected error, 13.2 EMERGENCY loses to STOP,
  13.3 closes not retried, 13.4 no single-instance lock, 13.5 orphan position on a lost order result. Data: 13.12
  histdata 2015-2018 are 1 h late in US-only DST weeks (ORB development years), 13.13 GER40 histdata is Euro Stoxx
  from 2020-06-15.
- Tests 2262 passed, 1 failed only when run from another folder (13.22). ruff check clean; `ruff format --check`:
  4 files (3 are the other session's uncommitted reformatting).
- A read-only audit scan may still be running (python PIDs 4680 / 18528, a script in Claude's scratchpad); stopping
  it was blocked while the bot runs. Harmless; it ends by itself or with a reboot.

## Last session, knowledge chat (2026-10-19..21, branch `claude/knowledge-stationarity`, own worktree `../backtester-knowledge`)
Worked in its own worktree because the app ran the demo test and another session edits the app. **Not merged into the
app branch yet**: merge after the demo phase, together with the app session (likely conflict: `engine/costs.py`,
small helper `swap_r_nights`; `risk/monte_carlo.py` imports from the new `analytics/daily.py`; `ui/settings_panel.py`
one line). Data was read from the main checkout's caches via `--cache-dir` (13.17: paths are cwd-relative).
- **11.11 ☑ stationarity study:** no stationarity anywhere; the H1 reversal is real but 0.2-0.5 of a spread.
- **11.12 ☑ gap momentum (strategy 7, `docs/strategy-gap-momentum.md`):** indices and GBPUSD / EURUSD no edge; XAUUSD
  London-open version positive on MT5 2021-26 (+17.8 R, 347 trades) but NO EDGE (t 1.0). Closing-candle tolerance
  10 min (FTMO gold ends 16:55 ET).
- **12.12 ☑ entry screening battery** (`tools/entry_screen.py`): strategies 1-7 all FAIL; only the gap strategies'
  entries carry (tiny) information.
- **11.13 ☑ large-move momentum (I-61):** no robust edge; continuation carried by the top 1 % events.
- **12.9 ☑ portfolio tool** (`tools/portfolio.py`): ORB + gold gap momentum + gap fade on MT5 2021-26, uncorrelated,
  +19.1 R, FTMO pass 79 % at 0.5 % risk, verdict NO EDGE (t 1.2, random entries 93 %, DSR 0.03 with N 306).
- **12.13 (built, waiting for the user's tick) DSR on daily R:** shared `analytics/daily.py`; trial-log lines carry
  daily statistics; reruns: gold DSR 0.83 -> 0.48, portfolio ~0 -> 0.03, no verdict changed. V uses 1/n until 2+
  lines per family have daily stats.
- Tests on the branch 2564 passed, 1 known cwd failure (13.22); ruff clean.
- **Research paused (user, 2026-10-20):** price-only research found nothing significant across 7 strategies and 4
  studies; the next real input is the ORB demo forward test. Resume with 12.11 Bayesian report or new data / ideas.
- Leftover processes the user may end in Task Manager: entry-screen runs PIDs 31704 / 31824, 37156 / 25084,
  38920 / 21316, 26812 / 1720.

## Accepted by the user (do not ask again)
- Knowledge chat 2026-10-20: 11.11 / 11.12 / 11.13 / 12.9 / 12.12 ☑ with their results; gap momentum rules (ATR stop
  1.0, symbols, sweep, slippage stand-in, close tolerance 10 min); entry screening pass rule incl. 90th percentile and
  item (c) reading; portfolio tool rules (equal weights, IDM off, first components); DSR on daily R; research paused
  until the demo forward test has data.
- Knowledge chat 2026-10-19 ("End."): six books added, 12.10 ☑, research order 12.10 -> 11.11 -> 11.12, Bayesian
  prior odds 1:50 (12.11), DSR as check 7, back-fill, Natenberg skipped; audit findings recorded as Phase 13.
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
2. **Audit Phase 13:** which items to fix and in which order (Claude suggests 13.1-13.5 first, with the bot
   stopped, after the demo day). 12.8 slippage question (time / signal exits as market fills?) still open.
3. Knowledge chat: tick 12.13; merge `claude/knowledge-stationarity` after the demo phase; research paused.
- **Known issues / polish:**
  - "Updated …" status overlaps the Update button on narrow windows; no "MT5" marker at the feed switch yet;
    replay bar and ⚙ dialog on the dark chart page not checked visually.
  - The settings panel shows cost fields only for the 5 strategy symbols.
  - `engine/backtest.py`, `engine/costs.py`, `analytics/metrics.py` hold another session's uncommitted ruff
    reformatting (user: leave them). Untracked `.vscode/`.
  - The empty folders `data/raw/histdata_2021_*` can be deleted by the user.

## Next step
The first live demo day (open point 1). The first session after it reviews the day's trades against the paper log,
then the live fixes 13.1-13.5 (bot stopped). Research: 11.11.

## First prompt for the next chat
`Continue.` (first demo day / review it) — or `Continue.Knowledge` for the research.
