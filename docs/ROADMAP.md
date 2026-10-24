# Roadmap

What to build next and its status. Step IDs (e.g. `V2.4.1`) are how the user refers to them.
Status: ☐ open · ◐ in progress · ☑ done (update this file when a step is finished).

**History:** phases 0-13 of V1, with every decision the user accepted, are archived verbatim in
`docs/archive/ROADMAP-v1.md` (read it there; the IDs below point to it).

---

## Open from V1

Status as written in V1. Note: 5.1-5.7 are still marked open there, but `risk/` (sizer,
account simulator, Monte Carlo, risk sweep, risk page, prop-firm card, adaptive risk) was
built in V1 (V1 status table). **Decision (user, 2026-10-22): 5.1-5.7 stay as they are**
(not completed further, not ticked); the parts in use (Monte Carlo, prop-firm pass
probability, adaptive risk) are checked in the V2.4 review. Phase 13 are
findings of the 2026-10-19 audit, input for the V2.4 review.

- ☐ **3.3d Review mode** (Phase 3)
- ☐ **3.5 Session view** (Phase 3)
- ☐ **3.7 Cross-check with the manual backtest** (Phase 3)
- ☐ **4.3 UI layout and look review** (Phase 4)
- ☐ **5.1 RiskConfig + PositionSizer** (Phase 5)
- ☐ **5.2 AccountSimulator** (Phase 5)
- ☐ **5.3 Monte Carlo** (Phase 5)
- ☐ **5.4 Risk sweep** (Phase 5)
- ☐ **5.5 Risk page in the UI** (Phase 5)
- ☐ **5.6 Prop-firm field** (Phase 5)
- ☐ **5.7 Adaptive risk for prop-firm accounts** (Phase 5)
- ☐ **11.3 Time-of-day drift by session for XAUUSD / GBPUSD / GBPJPY** (Phase 11)
- ☐ **12.2 Intrabar order from M1** (Phase 12)
- ☐ **12.4 Parameter heat map** (Phase 12)
- ☐ **12.5 Demo reconciliation** (Phase 12)
- ☐ **12.6 Stressed fills** (Phase 12)
- ☑ **12.8 Engine slippage** (Phase 12) — fixed in V2.4 (B4), 2026-10-23
- ☐ **12.9 Portfolio tool** (Phase 12)
- ☐ **12.11 Bayesian report** (Phase 12)
- ☐ **12.13 DSR on daily R** (Phase 12)
- ☑ **13.6 Closed-bar check on server time** (Phase 13) — fixed in V2.4 (live #1), 2026-10-23
- ☑ **13.7 Sizing on the live price** (Phase 13) — fixed in V2.4 (live #7), 2026-10-23
- ☑ **13.8 Wall-clock fallback exit** (Phase 13) — fixed in V2.4 (live #8), 2026-10-23
- ☑ **13.9 Validate CLI risk** (Phase 13) — fixed in V2.4 (live #18), 2026-10-23
- ☐ **13.12 histdata clock 2015-2018** (Phase 13)
- ☐ **13.13 GER40 histdata changes instrument on 2020-06-15** (Phase 13)
- ☐ **13.14 MT5 cache before 2020** (Phase 13)
- ☐ **13.15 One-day holes on 1 January** (Phase 13)
- ☐ **13.16 MT5 downloader swallows errors** (Phase 13)
- ☑ **13.17 Paths relative to the working folder** (Phase 13) — fixed in V2.4 (A2), 2026-10-23
- ☐ **13.18 Output folders** (Phase 13)
- ☑ **13.19 no_wick limit fill is lookahead** (Phase 13) — refuted by two V2.4 reviews (pending limits precede the fill candle; now enforced by the engine, A1), 2026-10-23
- ☑ **13.20 Kind C random fills never slip time exits** (Phase 13) — fixed in V2.4 (B4), 2026-10-23
- ☑ **13.21 Parallel runner progress race** (Phase 13) — fixed in V2.4 (A5), 2026-10-23
- ☐ **13.22 `tests/tools/test_s2_volume_ab.py`** (Phase 13)
- ☑ **13.23 Monte Carlo FTMO pass rate** (Phase 13) — fixed in V2.4 (B2), 2026-10-23

## V2 phases (user, 2026-10-22)

- ☑ **V2.1 Set up this PC** (tools, venv, data check, baseline tests).
- ☑ **V2.2 Team setup** (AGENTS.md, Codex / Claude 4.6 / Gemini through `tools/ai_dispatch.py`).
- ☑ **V2.3 Move to V2 and clean up** (inventory accepted by the user 2026-10-22).
- ◐ **V2.4 Full Codex review and speed-up** (2026-10-23: golden lists, review of all 8
  modules (84 findings, `docs/review/`), groups A + B fixed, speed 1 + 2 (partial) done;
  speed 2 complete; grid tools merged into the research runner 2026-10-23 (combined grids,
  grid robustness, shock days, breakdowns, sensitivity, filter twins, walk-forward, old sweeps as
  `research/grids/*.toml`, identical trades on the reproduction check; archive deleted); open:
  the user's check of the UI fixes): golden trade lists of all strategies first; review
  core -> detectors -> engine -> risk -> analytics -> strategies -> ui -> live (correctness,
  then speed, then cleanup); profile a real sweep, optimize with before/after numbers and
  identical golden trade lists. Includes merging the archived grid tools into the research
  runner.
- ☑ **V2.4a Trades of every strategy on the chart** (accepted by the user 2026-10-23) (rule set by the user, 2026-10-23: show
  the trades of any strategy on the chart; the trade itself is enough, confluences only when
  the user asks for a strategy): the "Trades" overlay runs the selected strategy through the
  backtest runner (`ui/trades_overlay.py` `registered_run`); strategy 1 keeps its confluences.
- ☐ **V2.4c Honesty tooling before V2.6** (audit 2026-10-23, `docs/review/backtest-audit.md`;
  audit asked for by the user 2026-10-23): T-10 Bayesian report, T-09 CPCV + PBO, T-19
  effective N, T-14 matched monkeys for every strategy, T-03 / 12.2 intrabar order from M1 (**done: default `engine.intrabar = "m1"`, set by the
  user 2026-10-24; golden net R 2023: session zones -484.9 -> -479.9, no-wick -1036.2 -> -959.7**);
  then measure the spread table's effect on the golden lists (default stays off unless the
  user decides) and a news-day split. The grid merge (V2.4) also takes the runner-level audit
  items: sensitivity around the chosen variant, filter twins, SE of expectancy, time in
  market, expectation haircut.
- ☐ **V2.4d Book requirements** (accepted by the user 2026-10-23; Pardo, Masters, Aronson,
  `docs/review/book-app-requirements.md` with the code check), in this order: (1) keep the daily
  net R series of every variant (trial log / runner); (2) daily returns marked to market (open
  trades valued each day, not booked at exit); (3) take profits and limit entries fill only on
  penetration by a per-symbol distance: built as a setting first, its effect measured on the
  golden lists of all 7 strategies, then the user picks the default (rule set by the user
  2026-10-23); **done: default 0.5 x spread + short TP on the ask (set by the user 2026-10-23;
  golden net R 2023: session zones -443.8 -> -484.9, no-wick -1013.9 -> -1036.2, gap fade
  -16.6 -> -21.1, NY indices -31.6 -> -30.9, the others without TPs unchanged)**; (4) drawdown Monte Carlo as Masters' double bootstrap (kind A only permutes
  the historic days and is optimistic); (5) best-of-N significance in the runner (White's
  Reality Check / Monte Carlo permutation over the variants' daily series); (6) walk-forward
  with month-based windows, walk-forward efficiency and the open-trade boundary rule;
  (7) detrended benchmark and long / short position bias; (8) bootstrap (BCa) bounds of the
  mean and log profit factor; (9) prices rounded to the tick in the engine. Later (V2.6 /
  V2.7): MCPT of the whole optimisation on permuted data (job queue), nested walk-forward
  for the portfolio's member selection.
- ☐ **V2.4b Slippage from the demo fills** (rule set by the user, 2026-10-23): slippage is
  always applied, no on/off switch (most realistic scenario); measure it per symbol from the
  demo bot's fills (fill price vs the order's signal / stop price, `results/live/`) and set the
  `SymbolCosts.slippage` defaults from it; until then the current presets (~half the spread)
  stay.
- ☐ **V2.5 App redesign** (decisions 2026-10-23 in `docs/design/ui-proposal.md`) after `docs/design/app-v2.png`: dark trading-terminal look, essential
  vs "Details" per page (list to the user first), research page as one vertical list of
  cards, Fast mode (headless) vs Visual mode with identical trade lists.
- ☐ **V2.6 Continuous research:** research-based strategies only, job queue (≈8 workers,
  temperature guard, resumable), 3 lanes in worktrees, Monte Carlo, parameter stability,
  regime breakdown (regime classifier in `analytics/`, spec first, user decides), warning flags,
  research cards, `docs/research-log.md`.
- ☐ **V2.7 Portfolio:** combine strategies that balance each other by regime; combined equity,
  correlation of daily R, Monte Carlo prop-firm pass probability, leave-one-out; the user picks.

## V2.5-V2.7 in detail (the user's brief of 2026-10-22, kept here so no chat needs it again)

### V2.5 App redesign (content stays, look and clarity change)
- Restyle the Dash app after `docs/design/app-v2.png` (look only, no brand names or logos):
  dark trading-terminal theme, top navigation tabs, a compact strip of key numbers above a large
  chart, a side panel, tabs below the chart, green / red accents, little text.
- Per page: essential items always visible, the rest behind a collapsible "Details"
  (`docs/design/ui-proposal.md`, decisions of 2026-10-23).
- Research page: one vertical, scrollable list, NO horizontal scrolling; each research run a
  compact card with: strategy + source, idea in one line, period, trades, net R, R/trade, win
  rate, max drawdown, profit factor, out-of-sample result, Monte Carlo drawdown and prop-firm
  pass probability, best market regime, parameter stability, warning flags. Click a card to
  expand the full details.
- Two modes with a switch / CLI flag: Fast mode = headless, no chart, for automated research;
  Visual mode = the app. Both give identical trade lists for the same settings (test).
- Codex reviews the redesign code. Done = tests green and the user looked at it in the browser
  and said ok.

### V2.6 Continuous research
Goal: a library of tested, research-based strategies. Do NOT judge pass / fail; record every
strategy with all metrics; the user decides later.
- Every strategy comes from research (book, paper, study, reputable source), cited in its
  `docs/` spec; Opus checks the source exists before any code. Never invent or data-mine rules
  (e.g. entering at an arbitrary time because it backtests well). Vary only the settings of a
  researched idea (R:R, stop / target method, session windows, timeframes, symbols, filters).
- Safeguards: develop before 2021-09-14, test the best variant ONCE on MT5 data from
  2021-09-14, every variant in the trial log, DSR, robustness report (halves, stressed costs,
  best trade removed), real costs + swap + slippage.
- Every strategy also gets: Monte Carlo (drawdown spread incl. worst 5 %, longest losing
  streak, prop-firm pass probability and typical time to pass), parameter stability (do
  neighbouring settings also work, or only one exact combination?), regime breakdown
  (`docs/regime-classifier.md`).
- Flag suspicious results automatically: win rate > 80 %, < 100 trades, profit from a few
  trades, big gap between development and test, isolated best parameter.
- Pipeline per idea: (1) research -> idea file with sources (Gemini; while its quota is empty:
  Codex / Opus); (2) pick idea, spec in `docs/` + test-case list (Codex); (3) tests, then
  strategy code (per AGENTS.md › Team); (4) review of the diff for lookahead and spec (Codex /
  Claude 4.6 / Opus); (5) sweep, robustness, one-time MT5 test, Monte Carlo, parameter
  stability, regime breakdown, research card: Python job queue (no AI tokens); (6) short
  write-up + warning flags on the card; (7) merge + update `knowledge/ideas.md`, ROADMAP,
  `docs/research-log.md` (Opus).
- Parallel lanes: 3 lanes, each in its own git worktree, each on one idea; a lane touches only
  `strategy/<its_name>/`, its spec and its tests; shared code is read-only (a needed shared
  change goes through Opus); Opus merges the `strategy/registry.py` entry. The trial log
  (`results/trials.jsonl`) gets a file lock so parallel writes are safe.
- Job queue (plain Python, built in V2.6): all sweeps in one queue, about 8 worker processes
  (room for the AI lanes, the app and Windows). Lanes run no heavy backtests themselves.
  Temperature guard: read the CPU temperature; above about 85 °C pause starting new jobs until
  it cools down; Telegram if the queue stops or stays paused. Queue state in files, resumes
  after a restart.
- Opus rhythm: check in every 2-3 hours (scheduled): lanes and queue, assign work, verify and
  merge finished strategies, update the log, Telegram if something is very promising. Keep
  `docs/research-log.md` current after every step.
- Strategy 4 (Kaufman trend following) passed a prop-firm challenge in some tests, but slowly:
  keep it as a portfolio candidate.
- Regime classifier: `analytics/regime.py` per `docs/regime-classifier.md` (accepted
  2026-10-23); every research card and results page shows net R, R/trade and win rate per
  regime and names the best regime.

### V2.7 Portfolio (main goal)
- Combine strategies that balance each other (e.g. trend following + range / mean reversion,
  chosen by their regime breakdown) for a smoother equity curve and a higher prop-firm pass
  probability. Base: `analytics/portfolio.py`; computing in the job queue; Codex helps pick
  the combinations.
- Per candidate set: combined equity curve, correlation matrix of daily R, regime breakdown,
  max drawdown, Monte Carlo prop-firm pass probability, and the same with each strategy
  removed. Present the best combinations; the user decides.
- Telegram only for: a decision on rules / defaults / risk, a blocker Codex can't solve, a
  crash or long pause of the loop / queue, a very promising strategy; plus one short evening
  summary while research runs.
