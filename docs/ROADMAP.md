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
- ☑ **V2.4 Full Codex review and speed-up** (accepted by the user 2026-10-26) (2026-10-23: golden lists, review of all 8
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
- ◐ **V2.4c Honesty tooling before V2.6** (done parts accepted by the user 2026-10-26) (2026-10-23 / 24: T-10, T-09 PBO, T-19, T-14, T-03
  done; spread table measured 2026-10-25 (`results/spread_table.md`, median table: costs per
  trade +25 to +90 % at the index open, no-wick nearly x2; **default: the median table, set by
  the user 2026-10-26; re-evaluated after a period of demo trading (V2.4b)**); news-day split
  moved to V2.4e, 2026-10-26) (audit 2026-10-23, `docs/review/backtest-audit.md`;
  audit asked for by the user 2026-10-23): T-10 Bayesian report, T-09 CPCV + PBO, T-19
  effective N, T-14 matched monkeys for every strategy, T-03 / 12.2 intrabar order from M1 (**done: default `engine.intrabar = "m1"`, set by the
  user 2026-10-24; golden net R 2023: session zones -484.9 -> -479.9, no-wick -1036.2 -> -959.7**);
  then measure the spread table's effect on the golden lists (default stays off unless the
  user decides) and a news-day split. The grid merge (V2.4) also takes the runner-level audit
  items: sensitivity around the chosen variant, filter twins, SE of expectancy, time in
  market, expectation haircut.
- ☑ **V2.4d Book requirements** (accepted by the user 2026-10-26; the tick-rounding default
  stays off until the user decides) (2026-10-23 / 24: items 1-9 done; open: the user's choice of
  the tick-rounding default, measured in `results/ticks.md`, built off) (accepted by the user 2026-10-23; Pardo, Masters, Aronson,
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
- ◐ **V2.4e Economic calendar: news-day split + blackout filter** (synthetic build plus CSV-format addendum: loader validation, per-variant research split and settings/trial SHA256 persistence built; real-calendar validation pending;
  `docs/news.md`; not accepted; decisions by the user, 2026-10-26) — the news part of V2.4c and audit item "News" (`docs/review/backtest-audit.md`).
  Data: `../backtester-news/` (`economic_events_2020_to_2026-10-25.csv`, 9,836 High / Medium
  events 2020-01-02 .. 2026-10-23, `implementation_instructions.md`, `coverage_report.md`,
  `source_manifest.csv`). **Blocked: the data needs fixing first** (Opus check 2026-10-26,
  `../backtester-news/verification_2026-10-26.md`; the user regenerates the file, the CSV is
  never edited here): 2,873 Forex Factory rows (1,620 High, incl. every NFP, most US CPI,
  FOMC, BoE) have a lost time stored as midnight Tehran and labelled exact (e.g. NFP
  2020-01-10 13:30Z sits at 2020-01-09 20:30Z); 258 all-day rows labelled exact; summer
  2023-2025 rows 1 h early (wrong +04:30 offset); Finance Calendar year (2025-10-24 on) has
  only 163 High, 305 bill auctions as Medium and almost no AUD / CAD / NZD / CHF; its raw file
  is missing. Then, per the instructions:
  (1) read-only loader with explicit schema, UTC parsing, blank timestamps kept blank,
  validation (unique `event_id` / `dedupe_key`, impact High / Medium, exact rows parse), CSV
  sha256 logged with every run (trial log); copy the CSV into `data/news/` unchanged;
  (2) instrument -> currencies mapping in config (XAUUSD, GBPUSD, GBPJPY, NAS100, US500,
  GER40, BTC / ETH; `GLOBAL` per instrument explicitly);
  (3) schedule and result behind separate interfaces: strategies never see `actual`,
  `forecast`, `previous` (not point-in-time); `actual` only from release + delay if ever needed;
  (4) **news-day split** in the research runner like the shock-day check: results with /
  without High-impact minutes (and days) per strategy; only from 2020-01-02 (user: 2020+
  only), earlier trades reported apart as "no calendar", never counted as news-free; the
  Finance Calendar year reported apart while its coverage differs;
  (5) **blackout filter** as a strategy / runner setting, default off: windows before / after
  per impact, policy (block entries / flag only), date / range / unknown rows by a separate
  conservative policy (block the day or skip with a warning), simultaneous events kept;
  effect measured on the golden lists, then the user decides any default;
  (6) the tests from the instructions (timezone of the PC, DST, inclusive / exclusive
  boundary, no `actual` one tick early, blank timestamps, date / range policy, two events at
  one time, duplicate keys fail, EURUSD gets no foreign currencies, hash recorded).
  Not in scope: the live bot (needs a live calendar source), 2015-2019 (raw Forex Factory
  cache goes back to 2007 if wanted later). **Rule set by the user, 2026-10-26:** Opus may
  use `../backtester-news/` and implement V2.4e in the repo once it is due (no extra ask).
- ☐ **V2.4b Slippage from the demo fills** (rule set by the user, 2026-10-23): slippage is
  always applied, no on/off switch (most realistic scenario); measure it per symbol from the
  demo bot's fills (fill price vs the order's signal / stop price, `results/live/`) and set the
  `SymbolCosts.slippage` defaults from it; until then the current presets (~half the spread)
  stay.
- ☑ **V2.5 App redesign** (accepted by the user 2026-10-26) (2026-10-25: V2.5a-d done: dark theme, top bar, Research cards,
  Chart / Results / Backtest / Live in the new skeleton, browser-checked by Opus; open: the
  user's look and ok) (decisions 2026-10-23 in `docs/design/ui-proposal.md`) after `docs/design/app-v2.png`: dark trading-terminal look, essential
  vs "Details" per page (list to the user first), research page as one vertical list of
  cards, Fast mode (headless) vs Visual mode with identical trade lists.
- ◐ **V2.6 Continuous research:** (2026-10-25: regime classifier and strategy profile built,
  all 7 strategies profiled, `docs/research-log.md`) research-based strategies only, job queue (≈8 workers,
  temperature guard, resumable), 3 lanes in worktrees, Monte Carlo, parameter stability,
  regime breakdown (regime classifier in `analytics/`, spec first, user decides), warning flags,
  research cards, `docs/research-log.md`.
  **Order (rule set by the user, 2026-10-26): first build the whole app, then check / test it;
  intensive research starts only when everything works.** In V2.6 that means the job queue
  first (plain Python, resumable, ~8 workers, file lock on the trial log, temperature guard
  reading LibreHardwareMonitor's sensor, which the user installs; pause new jobs above
  ~85 °C), then lanes and research cards. Pre-registered hypotheses (written now, tested once
  on MT5 data only when the pipeline is ready, user 2026-10-26): strategy 4 trend following
  on GBPJPY; gap fade (5) and gap momentum (7) in quiet sideways markets.
  **Build order accepted by the user 2026-10-26:** (1) ☑ job queue + temperature guard +
  trial-log lock (`briefs/v26a-job-queue.md`; built 2026-10-26: `python -m backtester.tools.queue`,
  `docs/research-runner.md` › Job queue; accepted by the user 2026-10-26; open: LibreHardwareMonitor install); (2) ☑ data fixes 13.12-13.16, 13.18 (built 2026-10-26, cache rebuilt through the queue, 100 jobs; `briefs/v26b-report.md`, `results/clock_check_*.md`; histdata clock 2015-2018, MT5 server clock per date through 2021-09-13 (2010-2014 dropped: no reference), wrong instruments dropped (GER40 from 2020-06-15, DXY = Dow Jones until 2018-12-14, EU50 = IBEX from 2018-12-17), oil jumps 2020 documented, sparse days filled by histdata only up to 2021-09-13 (user 2026-10-26); golden lists identical; open: the user's check; `tools/check.py` still reports unexpected gaps (~450 / year 2015-2020) and MT5 bid-without-ask rows -> look at them in step 8); (3) ☑ research cards through the queue + lanes in worktrees (built 2026-10-26 by Sonnet subagents while Codex was at its limit: `tools/research_pipeline.py`, queue panel on the Research page, `tools/lanes.py`; `briefs/v26c-cards-lanes.md`; accepted by the user 2026-10-26); (4) ☑ V2.7 portfolio page (built 2026-10-26: Portfolio tab, 2-4 member search on development data, equal weights, top-10 Monte Carlo through the queue, `--test` once per set CLI only; `docs/portfolio.md`, `briefs/v27-portfolio.md`; accepted by the user 2026-10-26; a real search needs >= 2 research grids); (5) ◐ UI: 3.3d review mode (every strategy), 3.5 as trade inspection (every strategy), 12.4 heat map on the research card, 4.3 Opus list -> the user picks (decisions 2026-10-26, `briefs/v26e-ui-items.md`; built 2026-10-27, 4.3 items chosen by the user: Live stale status, empty card tiles folded, candles before trades; the chart strip keeps showing the newest saved run; open: the user's check); (6) live: demo bot restart (the user's call), V2.4b, 12.5; (7) V2.4e news when the
  data is regenerated; (8) ◐ full check of the whole app (night 2026-10-27: Codex review of all V2.6 / V2.7 code, `docs/review/v26-full-check.md`, findings 1-6 fixed with tests, 7 for the user; CLI smoke test, 4 crashing `--help` fixed; end-to-end pipeline run of `orb_example` through the queue; open: the user's check, `docs/review/night-2026-10-27.md`); (9) ◐ possibly more symbols / pairs before research, for more options (proposal list `docs/review/symbol-proposal-2026-10-27.md`, the user picks; the user,
  2026-10-26: which ones and from which source decided then; download + data check + costs
  per symbol); then intensive research. **Night 2026-10-26/27 (the user's decisions):** go through the steps without an ok in between (each built, reviewed, tested, committed on v2-6-research as 'built, not accepted'; the user reviews in the morning); step 6 skipped (the demo bot is the user's call); step 7 built on synthetic data only (the regenerated news file is plugged in later); step 8 fixes small bugs with tests and lists everything touching rules, defaults or the look; step 9 only a proposal list; no heavy building by Sonnet subagents; one Telegram summary in the morning. Dropped as covered by V2.4c / V2.4d (Opus proposal, user
  2026-10-26): 3.7, 12.11, 12.13.
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
  Visual mode = the app. ☑ Identical trade lists for the same settings (`tests/test_fast_visual_identical.py`, 2026-10-25).
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
- **Where a strategy performs best** (the user, 2026-10-24): the breakdown is not only a
  warning; it is the input for combining strategies. Per strategy and per condition (market
  regime, symbol / market class, session, volatility, long vs short) the card shows the raw and
  the **detrended** result (skill vs trend, V2.4d 7), the bounds (V2.4d 8) and the trade count,
  so the strongest *skill* condition of each strategy is visible; V2.7 picks members and their
  active conditions from it (a strategy may trade only in its best regime).

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
