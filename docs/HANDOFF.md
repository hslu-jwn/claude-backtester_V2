# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

**Several sessions share this checkout.** Before committing: `git status` / `git pull`, stage only your own files,
never `git add -A` over another session's changes. A knowledge session works in its own worktree
`../backtester-knowledge` on `claude/knowledge-stationarity` (11.11); it merges its own section here when it ends.
Untracked `.vscode/` and a garbled `C…claude-notify-signalsstop` file in the root are not ours (left alone).

## Last session, strategy / app chat (2026-10-19..21, "End.")
Worked in a temporary worktree + dev app on :8051 (removed at the end), merged into this branch step by step.
- **Data rule (user 2026-10-19):** MT5 preferred day by day, histdata for older days, for backtests, tools and the
  chart (`data/sources.py` `preferred_dirs`; `docs/ARCHITECTURE.md`). FX research before 2021 now reads MT5 too.
- **Doji thresholds for all 23 symbols** (median 5m range, full history, `confluences.md`); Binance BTCUSDT /
  ETHUSDT hidden from the UI symbol lists (research only).
- **Chart page (7.6 ☑):** 42 s -> 3 s first load (cause: the 213-field settings dialog's wildcard callbacks),
  candles load on scroll, bottom fields removed except "Go to", overlays in ⚙ Settings (Chart Settings / Chart
  Overlays, closed by default), loading bar, update status as a popover, side-panel toggle on a right-edge strip,
  click a trade (results page, side panel, live page) -> chart on the strategy's timeframe with only the order
  (entry / SL / TP); every strategy's run trades drawn from the saved trade list.
- **Backtest page `/backtest`:** large two-phase bar (loading data / running), ETA, Cancel (also while loading,
  nothing saved), list of previous runs when idle / after Cancel; unsupported / data-less / unmapped symbols are left
  out with a note; results header shows the run's strategy; run-id path check fixed.
- **Live page (7.7 ☑):** every card folds; open by default Open positions, Closed trades (own Day / Week / All),
  Today's signals; setup funnel no longer ticks "Entered" on skipped setups (the bot had correctly skipped by volume
  on 10-19 / 10-20; no orders were sent).
- **Live bot fixes 13.1-13.5 + 13.4b (accepted, first demo check pending):** loop safety net, emergency before stop,
  retry closes until flat, single-instance lock (`results/live/bot.lock`), bot started via a launcher (an app
  restart no longer kills it — checked live 2026-10-20 23:14), adoption of orders with a lost result. The new bot
  runs on the FTMO demo since 2026-10-20 22:47 CH.
- **Prop-firm card + Full Monte Carlo button (5.6 / 12.7):** card on every results page (FTMO 2-Step, fixed vs
  adaptive, pass probability, fails, avg / median days, funded lost; cached `results/<run>/prop_firm.json`); button
  runs `tools.monte_carlo --run <id>` in the background, report served at `/monte-carlo/<id>/report.html`, written
  to the trial log. **12.12 ☑:** funded account risks on the initial balance, profits paid out daily (user rule).
- **Adaptive risk (5.7, parked):** spec `risk-management.md` › Adaptive risk (linear room scaling, floor 0.25, daily
  budget 3 %); sweep tool `tools/risk_sweep.py`, result `results/risk_sweep/2026-10-21/`: only strategy 6 has an
  edge; adaptive 1.5 % / floor 0.1 / budget 2.5 % passes 84 % on the MT5 test period vs 16 % fixed, but ~411 days on
  average. User: park it until a strategy with a good edge exists; goal = pass within ~3 months without more risk.
- Tests 2610 passed, 1 skipped; `ruff check` clean; `ruff format --check`: 4 test files unformatted (not touched
  this session: tests/engine/test_backtest.py, test_percentage_costs.py, test_spread_scaling.py,
  tests/live/test_connection.py).

## Accepted by the user (do not ask again)
- Everything above ("End." 2026-10-21): 7.6, 7.7, 13.1-13.5 + 13.4b, 5.6 card + button, 12.12, 5.7 parts 1-2
  (defaults unchanged, parked). Decisions: MT5 preferred day by day; Binance symbols hidden in the UI; trade focus
  opens the strategy's base timeframe; card data limits 100 trades / 120 days; button reports go into the trial log;
  funded account risk on the initial balance; adaptive risk rules (linear, floor 0.25, never above base, daily budget
  (a) 3 %, challenge + funded, FTMO limits); no daily-cap "N losses" rule; BTCUSD stays out of strategy 6 (no
  session).
- Earlier: knowledge chat 2026-10-19 (six books, 12.10, research order 12.10 -> 11.11 -> 11.12, DSR check 7, audit as
  Phase 13), 2026-10-17 decisions, ROADMAP 7.1-7.5, 11.x studies, FTMO swap defaults, cut-off 2021-09-14, strategy 6
  = forward-test candidate; strategies 1 paused, 2 / 4 parked, 3 dropped; tests first, small commits, no PR.

## Open (needs the user)
1. **Demo forward test** of strategy 6 runs (new bot since 2026-10-20 22:47). Watch the Live page / Telegram; first
   trades will show in Closed trades with "Chart →". First live check of 13.1-13.5 happens with the first real
   events (an error, a stop, a close).
2. **Research:** 11.11 stationarity / half-life study (T-11) is running in the knowledge session, then 11.12 gap
   momentum (I-46).
3. **Remaining audit items** 13.6-13.23 (live clock, live-price sizing, wall-clock fallback exit, data clock issues,
   …); the user decides the order.
- **Known issues / polish:** 4 unformatted test files (above); an adopted position (13.5) misses the entry commission
  in its net R; PID reuse can fool the lock (rare); Monte Carlo kind A pass rate counts finished attempts only (13.23,
  matters for 5.7 later); strategy 6 sweep samples are small (177 / 302 trades); the remote branch
  `origin/claude/ui-polish` (merged) can be deleted.

## Next step
Research for an edge (`Continue.Knowledge`, 11.11 then 11.12) while the demo forward test runs. Strategy / app work
(`Continue.`): review the demo's first trades, then audit items 13.6-13.8 for the live bot.

## First prompt for the next chat
`Continue.Knowledge` (research) — or `Continue.` for the demo review / live fixes.
