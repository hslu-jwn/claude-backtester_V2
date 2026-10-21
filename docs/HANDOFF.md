# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

**Several sessions share this checkout.** Before committing: `git status` / `git pull`, stage only your own files,
never `git add -A` over another session's changes. A knowledge session works in its own worktree
`../backtester-knowledge` on `claude/knowledge-stationarity` (11.11); it merges its own section here when it ends.
Untracked `.vscode/` and a garbled `C…claude-notify-signalsstop` file in the root are not ours (left alone).

## Last session, strategy / app chat (2026-10-21, second chat, "End.")
- **7.8 Bot positions always on the chart (☑):** the chart showed "not in the cache" for today's US500 short (the
  cache ends yesterday). Now the bot writes its 4 symbols' finished days into the MT5 cache (from its warm-up history,
  never overwrites, empty files for no-data days) and today's bars into `data/cache/live/` each minute; at start it
  launches `tools.update_data` detached for the other symbols (log `results/live/update_stdout.log`). Only the chart
  reads `live/` (`CHART_SOURCES`; backtests / tools keep `DEFAULT_SOURCES`). "Bot trades" overlay (since the current
  bot start, on by default for bot symbols). No TP on strategy 6 orders is correct (`target_r` = 0, session-end exit).
  Fixed in passing: the cache day-list memo and the live-file stamp missed fast rewrites on Windows (flaky tests).
- **Live:** first demo trade 2026-10-21 US500 short 14:06 UTC, SL hit 16:40 UTC (-1.0 R); the bot was stopped with
  "Close all & stop" 16:49 UTC and is **not running**. It needs the 7.8 code: restart from the Live page.
- **Research tooling (6.1 + 6.2 ☑, spec `docs/research-runner.md`):** `python -m backtester.tools.research
  research/grids/<name>.toml [--dev-only] [--retest] [--workers N]` for any registered strategy: TOML grid checked
  against the config, development run (first cached day..2021-09-13), only the best variant (net R, >= 100 trades)
  tested once on 2021-09-14..last day, deflated Sharpe with N = variants, verdict, flags, trial log, run folders +
  preset. Research page `/research` (all research variants + plain runs, sortable, flags, row -> results page).
  Speed: candles loaded once per worker, variant chunks in a process pool (11.4 min -> ~1.5 min, identical trades).
  Contract tests for every registered strategy (`tests/strategy/test_contract.py`). The runner reproduces `orb_grid`
  and `gap_fade_grid` exactly (`research/grids/check_*.toml`); the 7 per-strategy grid tools are archived in
  `tools/archive/` (shared helpers `tools/grid_common.py`). 13.19 not reproduced by the contract test (noted).
- Dev app config `backtester-app-dev` (port 8052) added to `.claude/launch.json`.

## Accepted by the user (do not ask again)
- "End." 2026-10-21 (second chat): 7.8 and its rules (`live-trading.md` › Bot data and chart: overlay since the
  current bot start, on by default; the bot updates its 4 symbols itself, the rest in the background); 6.1 + 6.2
  research runner + page and its decisions (single best variant tested once, min 100 development trades, `--retest`
  only explicitly and logged, command line first then page, default sort verdict -> test net R -> dev net R);
  research-speed plan order (1) runner, (2) speed, (3) contract tests, (4) result-bias fixes 12.2, 12.8, 13.20,
  13.12-13.15, 13.23, (5) clean-up 13.17, 13.18, 13.21, 13.22, (6) portfolio tool 12.9; old grid tools archived.
- First chat 2026-10-21 ("End."): 7.6, 7.7, 13.1-13.5 + 13.4b, 5.6 card + button, 12.12, 5.7 parts 1-2 (parked);
  MT5 preferred day by day; Binance symbols hidden in the UI; funded risk on the initial balance; adaptive risk rules.
- Earlier: knowledge chat 2026-10-19, 2026-10-17 decisions, ROADMAP 7.1-7.5, 11.x studies, FTMO swap defaults,
  cut-off 2021-09-14, strategy 6 = forward-test candidate; strategies 1 paused, 2 / 4 parked, 3 dropped; tests
  first, small commits, no PR.

## Open (needs the user)
1. **Restart the bot** from the Live page (it was stopped 2026-10-21 18:49 CH); with 7.8 it then writes its bars.
2. **Research:** 11.11 stationarity study (T-11) in the knowledge session, then 11.12 gap momentum (I-46). New ideas
   now go through `tools.research` (one grid file each). The user offered to supply papers; suggested topics:
   backtest overfitting / PBO / White's Reality Check / Hansen SPA; intraday momentum and ORB in index futures (Gao
   et al., Zarattini / Aziz); volume as a breakout filter; combining weak edges (vol targeting, meta-labeling);
   retail CFD cost models.
3. **Remaining audit items** 13.6-13.23 for the live bot and data.
- **Known issues / polish:** 4 unformatted test files (tests/engine/test_backtest.py, test_percentage_costs.py,
  test_spread_scaling.py, tests/live/test_connection.py); variant results pages opened from the Research page have
  no prop-firm card / Monte Carlo button (the chosen variant's run has them); research batches lose up to 8 variants'
  work on an interrupt (chunked); the chart does not auto-refresh live candles (reload); an adopted position (13.5)
  misses the entry commission; PID reuse can fool the lock (rare); 13.23 Monte Carlo pass rate; the remote branch
  `origin/claude/ui-polish` (merged) can be deleted.

## Next step
Strategy / app work (`Continue.`): research-speed plan step (4), the result-bias fixes (12.2 intrabar M1 order, 12.8
engine slippage, 13.20 time-exit slippage, 13.12-13.15 data clock / holes, 13.23), then 13.6-13.8 for the live bot.
Research (`Continue.Knowledge`): 11.11 then 11.12, using `tools.research`.

## First prompt for the next chat
`Continue.` (step 4, result-bias fixes) — or `Continue.Knowledge` for research.
