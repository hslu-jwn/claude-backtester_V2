# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

**Several sessions may share this checkout.** Before committing: `git status` / `git pull`, stage only your own files,
never `git add -A` over another session's changes. `claude/knowledge-stationarity` was merged here 2026-10-21 (user)
and its worktree `../backtester-knowledge` removed; knowledge sessions now work on this branch too.
Untracked `.vscode/` and a garbled `C…claude-notify-signalsstop` file in the root are not ours (left alone).

**All branches merged (user, 2026-10-22):** this branch now contains `main` (ponytail-audit skill), `claude/ui-polish`,
`claude/knowledge-stationarity` and `sweep-most-extreme-level` (merged with `-s ours`: its 2026-10-11 rule was later
rebuilt as the `equal_tolerance_atr` option, off by default, so its old code was not taken). `main` was fast-forwarded
to this branch and pushed, so a fresh clone of `main` has everything.

## Moving to another PC (user, 2026-10-22)
Git holds the code, specs, knowledge base and research grids. Not in git, set up by hand on the new PC:
1. `git clone <repo>`, then `python -m venv .venv`, `.venv\Scripts\activate`,
   `pip install -e ".[dev,ui,data,risk,mt5]"` (the old `.venv` is not portable).
2. **Copy the git-ignored folders** from the old PC into the same paths: `data/raw/`, `data/cache/` (histdata, mt5,
   binance*, live) and `results/` (runs, trial log, live logs, `trading.json`). Without them no backtest, study or
   chart works (or re-import: `python -m backtester.data.histdata data/raw/histdata/` and the MT5 download).
3. **MT5:** install the FTMO terminal, log in to the demo, enter login / password / server again in the app's
   Settings ⚙ → Trading (they live in the Windows Credential Manager, not copied). Then `python -m backtester.tools.mt5_info`.
4. Optional: Claude's memory folder `~/.claude/projects/<project-path>/memory/` (2 notes, both also in CLAUDE.md /
   knowledge/README.md).
6. Check: `pytest` (2026-10-22: 3218 passed, 5 skipped, 1 xfailed, ~37 min), `python -m backtester.ui.app`, chart shows US500.
The bot is **not running** (stopped 2026-10-21); start it only on the new PC, never on both.

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

## Knowledge chat 2026-10-21 (this branch): no-wick retest study + merge
- **11.17 ☑ no-wick retest study (I-62, user's idea + Bard FX video summary):** `tools/no_wick_retest_study.py`, limit at
  the no-wick end, 1m fills, 4 trend filters, 9 stops, 8 targets, 4 timeframes, 18 symbols: 0.4 % of 4,608 variants
  positive; a gold H1 cluster failed its one pre-registered MT5 test (-0.02 R/trade). No edge.
- **Merged `claude/knowledge-stationarity`** (user, 2026-10-21): `tools/monte_carlo.py` now has `--run` and `--set` /
  `--cache-dir` / `--spread-table` together; numbering clashes fixed: no-wick study 11.17 / I-62 (11.13 / I-61 =
  large-move study), funded-account loss rate 12.14 (12.12 = entry screening).

## Knowledge chat 2026-10-19..21 (merged from `claude/knowledge-stationarity`)
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
- Knowledge chat 2026-10-21: merge of the knowledge branch; 11.17 no-wick retest study (no edge) and its study
  definitions (stops, targets, filters, cost cap 0.3 R, no overnight holds); renumbering 11.17 / I-62 / 12.14.
- "End." 2026-10-21 (second chat): 7.8 and its rules (`live-trading.md` › Bot data and chart: overlay since the
  current bot start, on by default; the bot updates its 4 symbols itself, the rest in the background); 6.1 + 6.2
  research runner + page and its decisions (single best variant tested once, min 100 development trades, `--retest`
  only explicitly and logged, command line first then page, default sort verdict -> test net R -> dev net R);
  research-speed plan order (1) runner, (2) speed, (3) contract tests, (4) result-bias fixes 12.2, 12.8, 13.20,
  13.12-13.15, 13.23, (5) clean-up 13.17, 13.18, 13.21, 13.22, (6) portfolio tool 12.9; old grid tools archived.
- First chat 2026-10-21 ("End."): 7.6, 7.7, 13.1-13.5 + 13.4b, 5.6 card + button, 12.14 (then 12.12), 5.7 parts 1-2 (parked);
  MT5 preferred day by day; Binance symbols hidden in the UI; funded risk on the initial balance; adaptive risk rules.
- Earlier: knowledge chat 2026-10-19, 2026-10-17 decisions, ROADMAP 7.1-7.5, 11.x studies, FTMO swap defaults,
  cut-off 2021-09-14, strategy 6 = forward-test candidate; strategies 1 paused, 2 / 4 parked, 3 dropped; tests
  first, small commits, no PR.
- Knowledge chat 2026-10-20: 11.11 / 11.12 / 11.13 / 12.9 / 12.12 ☑ with their results; gap momentum rules (ATR stop
  1.0, symbols, sweep, slippage stand-in, close tolerance 10 min); entry screening pass rule incl. 90th percentile and
  item (c) reading; portfolio tool rules (equal weights, IDM off, first components); DSR on daily R; research paused
  until the demo forward test has data.
- Knowledge chat 2026-10-19 ("End."): six books added, 12.10 ☑, research order 12.10 -> 11.11 -> 11.12, Bayesian
  prior odds 1:50 (12.11), DSR as check 7, back-fill, Natenberg skipped; audit findings recorded as Phase 13.

## Open (needs the user)
1. **Restart the bot** from the Live page (it was stopped 2026-10-21 18:49 CH); with 7.8 it then writes its bars.
2. **Research:** 11.11 / 11.12 / 11.13 / 11.17 done, all no edge; research paused by the user (2026-10-20) until
   the demo forward test has data; next options 12.11 Bayesian report, tick 12.13, or new ideas / papers. New ideas
   go through `tools.research` (one grid file each). The user offered to supply papers; suggested topics:
   backtest overfitting / PBO / White's Reality Check / Hansen SPA; intraday momentum and ORB in index futures (Gao
   et al., Zarattini / Aziz); volume as a breakout filter; combining weak edges (vol targeting, meta-labeling);
   retail CFD cost models.
3. **Remaining audit items** 13.6-13.23 for the live bot and data.
- **After the merge (2026-10-21):** `tools/research.py` still computes its own deflated Sharpe on per-trade R while the
  trial log's family Sharpes are now daily (12.13); align it when 12.13 is ticked. `tools/gap_momentum_grid.py` stays
  in `tools/` (imports `tools/archive/trend_grid`); move it to the archive once a gap-momentum grid TOML exists.
- **Known issues / polish:** 4 unformatted test files (tests/engine/test_backtest.py, test_percentage_costs.py,
  test_spread_scaling.py, tests/live/test_connection.py); variant results pages opened from the Research page have
  no prop-firm card / Monte Carlo button (the chosen variant's run has them); research batches lose up to 8 variants'
  work on an interrupt (chunked); the chart does not auto-refresh live candles (reload); an adopted position (13.5)
  misses the entry commission; PID reuse can fool the lock (rare); 13.23 Monte Carlo pass rate; the remote branch
  `origin/claude/ui-polish` (merged) can be deleted.

## Next step
Strategy / app work (`Continue.`): research-speed plan step (4), the result-bias fixes (12.2 intrabar M1 order, 12.8
engine slippage, 13.20 time-exit slippage, 13.12-13.15 data clock / holes, 13.23), then 13.6-13.8 for the live bot.
Research (`Continue.Knowledge`): paused until the demo has data; then 12.11 or new ideas via `tools.research`.

## First prompt for the next chat
`Continue.` on the new PC after the setup above (step 4, result-bias fixes) — or `Continue.Knowledge` for research.
