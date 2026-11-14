# Roadmap

What to build next and its status. Step IDs (e.g. `V2.4.1`) are how the user refers to them.
Status: ☐ open · ◐ in progress · ☑ done (update this file when a step is finished).

**History:** phases 0-13 of V1, with every decision the user accepted, are archived verbatim in
`docs/archive/ROADMAP-v1.md` (read it there; the IDs below point to it). Finished V2 steps (☑ / ☒)
move verbatim to `docs/archive/ROADMAP-v2-done.md` (first move 2026-11-12).

---

## Open from V1

Status as written in V1. Note: 5.1-5.7 are still marked open there, but `risk/` (sizer,
account simulator, Monte Carlo, risk sweep, risk page, prop-firm card, adaptive risk) was
built in V1 (V1 status table). **Decision (user, 2026-10-22): 5.1-5.7 stay as they are**
(not completed further, not ticked); the parts in use (Monte Carlo, prop-firm pass
probability, adaptive risk) are checked in the V2.4 review. Phase 13 are
findings of the 2026-10-19 audit, input for the V2.4 review. Items done later in V2 point to
where (updated 2026-11-03).

- ☐ **3.7 Cross-check with the manual backtest** (Phase 3) — moved (the user, 2026-11-03): checks the
  code against a strategy's written rules, so it is done for a strategy once it survives research,
  before its MT5 test or live run (a week of its trades against the user's manual picks). Data / chart
  check instead now: `docs/archive/review/tradingview-check-2026-11-03.md`
- ☐ **5.1 RiskConfig + PositionSizer** (Phase 5)
- ☐ **5.2 AccountSimulator** (Phase 5)
- ☐ **5.3 Monte Carlo** (Phase 5)
- ☐ **5.4 Risk sweep** (Phase 5)
- ☐ **5.5 Risk page in the UI** (Phase 5)
- ☐ **5.6 Prop-firm field** (Phase 5)
- ☐ **5.7 Adaptive risk for prop-firm accounts** (Phase 5)
- ☐ **11.3 Time-of-day drift by session for XAUUSD / GBPUSD / GBPJPY** (Phase 11)

## V2 phases (user, 2026-10-22)

- ◐ **V2.4e Economic calendar: news-day split + blackout filter** (2026-10-28, accepted by the user: calendar wired into every run, scope = FTMO restricted events by default (`events="impact"` = all High), filter off by default (`docs/news.md`); synthetic build plus CSV-format addendum: loader validation, per-variant research split and settings/trial SHA256 persistence built; real-calendar validation pending;
  `docs/news.md`; not accepted; decisions by the user, 2026-10-26) — the news part of V2.4c and audit item "News" (`docs/archive/review/backtest-audit.md`).
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
  **Later, open (the user, 2026-10-28; no live news API for now):** (a) a refresh tool that
  pulls new events into the calendar CSV through the same cleaning (`tools/news_clean`), run by
  hand or weekly, so research has a current calendar; (b) only when a strategy with the news
  rule goes to the demo bot: the bot reads that refreshed calendar at start and once a day (same
  blackout logic as the backtest; touches `live/`, needs the user's go). A streaming API only if
  unscheduled events ever matter. Source still to pick (FTMO's restricted list is what counts).
  Not in scope: the live bot (needs a live calendar source), 2015-2019 (raw Forex Factory
  cache goes back to 2007 if wanted later). **Rule set by the user, 2026-10-26:** Opus may
  use `../backtester-news/` and implement V2.4e in the repo once it is due (no extra ask).
- ◐ **V2.4b Slippage from the demo fills** (rule set by the user, 2026-10-23; **decided by the user 2026-10-28** after `docs/archive/review/fill-analysis-2026-10-28.md`: keep the current model slippage as the default (the measured median is at or below it), and once London fills are in use the measured p90 per symbol as the stressed cost level of the robustness report instead of the flat costs x 1.5; open: London fills, then build it): slippage is
  always applied, no on/off switch (most realistic scenario); measure it per symbol from the
  demo bot's fills (fill price vs the order's signal / stop price, `results/live/`) and set the
  `SymbolCosts.slippage` defaults from it; until then the current presets (~half the spread)
  stay.
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
  trial-log lock (`docs/archive/briefs/v26a-job-queue.md`; built 2026-10-26: `python -m backtester.tools.queue`,
  `docs/research-runner.md` › Job queue; accepted by the user 2026-10-26; open: LibreHardwareMonitor install); (2) ☑ data fixes 13.12-13.16, 13.18 (accepted by the user 2026-11-12, plus the GBPUSD 2019 cross-price quarantine; built 2026-10-26, cache rebuilt through the queue, 100 jobs; `docs/archive/briefs/v26b-report.md`, `results/clock_check_*.md`; histdata clock 2015-2018, MT5 server clock per date through 2021-09-13 (2010-2014 dropped: no reference), wrong instruments dropped (GER40 from 2020-06-15, DXY = Dow Jones until 2018-12-14, EU50 = IBEX from 2018-12-17), oil jumps 2020 documented, sparse days filled by histdata only up to 2021-09-13 (user 2026-10-26); golden lists identical; `tools/check.py` still reports unexpected gaps (~450 / year 2015-2020) and MT5 bid-without-ask rows -> look at them in step 8); (3) ☑ research cards through the queue + lanes in worktrees (built 2026-10-26 by Sonnet subagents while Codex was at its limit: `tools/research_pipeline.py`, queue panel on the Research page, `tools/lanes.py`; `docs/archive/briefs/v26c-cards-lanes.md`; accepted by the user 2026-10-26); (4) ☑ V2.7 portfolio page (built 2026-10-26: Portfolio tab, 2-4 member search on development data, equal weights, top-10 Monte Carlo through the queue, `--test` once per set CLI only; `docs/portfolio.md`, `docs/archive/briefs/v27-portfolio.md`; accepted by the user 2026-10-26; a real search needs >= 2 research grids); (5) ☑ UI: 3.3d review mode (every strategy), 3.5 as trade inspection (every strategy), 12.4 heat map on the research card, 4.3 Opus list -> the user picks (decisions 2026-10-26, `docs/archive/briefs/v26e-ui-items.md`; built 2026-10-27, 4.3 items chosen by the user: Live stale status, empty card tiles folded, candles before trades; the chart strip keeps showing the newest saved run; accepted by the user 2026-10-27); (6) live: demo bot restart (the user's call), V2.4b, 12.5; (7) V2.4e news when the
  data is regenerated; (8) ☑ full check of the whole app (night 2026-10-27: Codex review of all V2.6 / V2.7 code, `docs/archive/review/v26-full-check.md`, findings 1-6 fixed with tests, 7 for the user; CLI smoke test, 4 crashing `--help` fixed; end-to-end pipeline run of `orb_example` through the queue; accepted by the user 2026-10-27; open decisions in `docs/archive/review/night-2026-10-27.md`); (9) ☑ more symbols / pairs before research (eight added, full history, accepted by the user 2026-10-27), for more options (proposal list `docs/review/symbol-proposal-2026-10-27.md`; picked by the user 2026-10-27: AUDJPY, CADJPY, NZDJPY, CHFJPY, EURAUD, GBPAUD, AUS200, HK50, after `tools.mt5_info` confirms FTMO's names; decided by the user 2026-10-27 (Opus's picks): no opening-range sessions for AUS200 / HK50 yet (added by the user 2026-11-03: AUS200 10:00-15:55 Sydney, HK50 09:30-15:55 Hong Kong), HK50 quote_to_usd 1 / 7.80 and no news mapping, market class 'AU/HK indices', FX commission $5 (confirmed by FTMO's published rate), doji threshold fields in the settings panel only for the strategy symbols (like the cost fields); state in `docs/review/symbol-proposal-2026-10-27.md`; the user,
  2026-10-26: which ones and from which source decided then; download + data check + costs
  per symbol); then intensive research. **Night 2026-10-26/27 (the user's decisions):** go through the steps without an ok in between (each built, reviewed, tested, committed on v2-6-research as 'built, not accepted'; the user reviews in the morning); step 6 skipped (the demo bot is the user's call); step 7 built on synthetic data only (the regenerated news file is plugged in later); step 8 fixes small bugs with tests and lists everything touching rules, defaults or the look; step 9 only a proposal list; no heavy building by Sonnet subagents; one Telegram summary in the morning. Dropped as covered by V2.4c / V2.4d (Opus proposal, user
  2026-10-26): 3.7, 12.11, 12.13.
- ◐ **V2.6d Before research (the user, 2026-10-27; in this order, research starts after it):** (state 2026-10-27 evening: (1) bot running since 16:00 UTC, analysis after 1-3 days; (2) ☑ fees implemented (NATGAS / DXY, 0.7 % conversion), golden lists re-written; (3) ☑ calendar cleaned and lost release times imputed (`tools/news_clean`), windows High 2 / 2 min, Medium none (the user, 2026-10-27), filter still off by default (the user's call); (4) ☑ LibreHardwareMonitor installed, guard reads the CPU (not started with Windows: start it after a reboot); (5) ☑ daily DSR everywhere, live candles refresh, CLI presets, `claude/ui-polish` already gone)
  (1) **Fill-collection demo run:** a strategy `fill_probe` that only produces many fills (frequent
  market entries, alternating direction, ATR stop / target and a time exit; profit does not matter)
  on many FTMO symbols at minimal risk, 1-3 days on the FTMO demo; the bot gets `--strategy`.
  Output (`paper.csv`, `trades.csv`, deals): slippage per symbol / session / order type (V2.4b),
  spread at the fill, FTMO's real commission per symbol from the deals; then 12.5 reconciliation.
  (2) **FTMO fees:** every symbol's commission (and other fees) researched online and checked
  against the demo deals; implemented as the defaults (the user's go, 2026-10-27: "research all
  the fees from FTMO and implement them"), golden lists re-written with a note.
  (3) **News filter on real data:** clean the calendar (suspicious "exact" midnight / 23:59:59
  times -> day-only, weekend rows dropped), install it at `data/news/economic_events.csv`, run
  the split and the filter on real data, propose window sizes (the user decides), finish V2.4e.
  (4) **LibreHardwareMonitor** installed (winget), its web server on port 8085, the queue's
  temperature guard reading it.
  (5) **Older known issues:** one DSR definition (research's per trade vs the trial log's daily),
  live candles auto-refresh on the chart, remote branch `claude/ui-polish` (delete only on the
  user's word), CLI named-preset restrictions equal to the app's.
  A full suite of ~8 min is fine (the user, 2026-10-27; replaces the < 5 min target).
- ◐ **V2.8 Finalization (plan accepted by the user 2026-11-02; audit
  `docs/archive/review/finalization-audit-2026-11-02.md`):** finish, speed up and stabilize the app, no
  rebuild. In this order: (1) R1 bot `status.json` for every bot strategy, a failed status
  printed once instead of hidden (`live/`, written by Opus, go by the user 2026-11-02);
  (2) U1 chart Trades tab: the newest run's trades in pages of 100 (Time / Pair sort on the
  server, pager, click-to-focus and Minimize unchanged; picked by the user 2026-11-02),
  done = chart payload < 500 KB and usable < 4 s with the 10,397-trade run, the user looked at
  it; U2 (optional) Research cards built once; T1 the slowest tests sped up without weakening
  them, no `pytest-xdist` (the user, 2026-11-02), target ~8 min; (3) V2.4b p90 stressed costs
  now (the user, 2026-11-02: London fills exist; re-run the fill report first), then 12.5
  reconciliation, V2.6l, V2.4e real-calendar validation; (4) full suite + ruff, golden check,
  fast / visual identical, timed browser pass of every page (Chart < 4 s, others < 3 s), intake
  end-to-end test. Before / after numbers with the same scripts; merge to `main` only on the
  user's word.
  **State 2026-11-02 evening:** R1 built (`4fb5fe9`); T1 built (`417e0ab`, Monte Carlo tool
  tests 5.5 min -> 43 s); U1 built by Codex terra, checked by Opus (787 UI tests green), **accepted
  by the user 2026-11-02 after looking at it**: chart page response 6.4 MB -> 290 KB, list 100 rows
  "1-100 of 10,397"; with a game running on the PC the chart was usable at 6-7 s and a page
  step took ~3 s in the browser (server 30-50 ms), so the < 4 s target is re-measured on an
  idle PC in step (4).
  **Night run 2026-11-02/03 (rule set by the user, 2026-11-02):** step (3) in order, then step
  (4); test-first, small commits, push regularly; on a Codex limit wait for the reset and do
  Codex-free steps meanwhile (or another route of `docs/agent-routing.md` at the same cost,
  never a paid fallback); new questions are decided by Opus as recorded assumptions; no MT5
  one-time test, no default changes (costs, spread table, sweep options), no live trading, no
  merge to `main`; clean stop ~10:00 with a short morning report (what the user does not
  object to counts as accepted once checked). 12.5 scope (the user): the fill-probe trades
  2026-10-27..31 trade by trade against the engine on the same M1 bars.
  **V2.4b built 2026-11-02 night** (Codex gpt-6.1-terra after gpt-6.1-sol was at capacity;
  brief `docs/archive/briefs/v24b-p90-stress.md`): `analytics/slippage_p90.json` (23 symbols, 5,512 fills),
  `net_r_stressed` = measured p90 on market fills (`cost_stress_mode = "p90"`, the user's
  2026-10-28 decision), x1.5 only for unmeasured symbols or in `factor` mode; golden lists
  identical.
  **12.5 built 2026-11-03 night** (Codex gpt-6.1-terra, brief `docs/archive/briefs/v28-12-5-reconcile.md`;
  Opus added the direction check and a 1 % R stop tolerance): `python -m
  backtester.tools.reconcile`, run in `results/reconcile_2026-11-02/`. All 2,756 demo trades
  matched an engine trade; 598 engine-only, all explained (450 daily stop, the rest skips /
  bot not running); 0 unexplained. Engine more conservative: matched net R demo -750 vs
  engine -964 without NATGAS (median 0.07 R per trade, exit reason agrees 90 %). Findings for
  the user (no default changed): (a) 110 trades of 2026-10-27 16:00-18:00 UTC have the opposite
  direction in the demo: explained, the bot ran the old counter-based direction rule until its
  18:22 UTC restart (`5bb1b7d`); all 172 later trades of that day match; (b) NATGAS: demo -452 R vs engine -977 R
  because the engine accepts a stop inside the spread (e.g. a 0.002 stop with the 0.06 spread
  = -54 R on one trade). **Decided 2026-11-03 (the user: "Yes, refuse
  them"):** the engine refuses a sell whose SL is not above the ask (`CostConfig.refuse_stop_in_spread`,
  default on; risk-management.md › Costs), the broker's rule; golden: strategy 3 loses 31 of
  4,202 trades (-157 R), the other 8 lists identical. Correction (Opus, 2026-11-03): the -54 R
  NATGAS example was a buy, which the broker accepts (its SL is below the bid) and the demo also
  filled, so it is not refused; its gap is the R basis (risk 0.002 on the bar close vs the demo's
  fill). Re-run `results/reconcile_2026-11-03/`: engine-only 598 -> 526 (74 sells gone, 66 of them
  NATGAS, -1,404 R: sells the demo never filled); 2 USOIL sells at 23:30 UTC now demo-only, the
  demo's spread at that minute was below the engine's hourly median, so the engine sees the SL
  inside its spread. Buys with a tight SL stay filled (the user, 2026-11-03: "Keep broker rule
  only"; cost filter stays off).
  **Short stop on ask (the user, 2026-11-03):** a short's SL triggers when the ask reaches it
  and fills at the SL, as the broker (`CostConfig.short_sl_on_ask`, default on; risk-management.md
  › Costs); golden lists re-written, counts unchanged, net R no_wick -30.7, the others -0.5..+5.2.
  Still open from the spread model: the exit uses the entry spread; the hourly median instead
  of the per-bar MT5 spread.
  **JP225 exit (the user, 2026-11-03):** TSE moved its close from 15:00 to 15:30 on 2024-11-05
  (JPX); the opening-range exit is 14:55 until 2024-11-04 and 15:25 from then on
  (`SessionSpec.late_exit_from` / `late_exit_time`); development data unchanged.
  **V2.6l built 2026-11-03 night** (Codex gpt-6.1-terra, brief `docs/archive/briefs/v26l-cell-manifest.md`):
  the result envelope carries `robustness.cell_manifest` (every declared cell: parameters,
  trades, gross / net mean and total R, stop rate, halves, cost stresses x1.5 / x2 / fill p90)
  and `robustness.trial_accounting`; `variants_tried` = declared cells (pilot: 9, not the 17
  trial-log runs); sensitivity marked not selectable. Checked by Opus against the pilot's
  numbers (identical). Assumptions (Opus, 2026-11-03): the R004-specific map
  (`robustness.r004`) waits until R004 is queued; the data-integrity check is not built:
  Research's reply `FB_INTRADAY_H1_SHOCK_RESPONSE_REPLY_20261102T171227Z_RESEARCH` requires an
  authoritative versioned CFD session calendar (holidays, early closes), which V2 does not
  have; Research is told so (`FB_INTRADAY_H1_SHOCK_RESPONSE_20261102T232536Z_ca99`; the
  reviewability proposal acknowledged in `FB_UNKNOWN_20261102T232536Z_1ebf`, review after V2.8).
  **2026-11-03 (the user):** calendar 1-hour rows: "yes" -> `news_clean` rule 3 built (docs/news.md
  › Cleaning; 665 rows moved; anchors 5 / 6 pass, were 3 / 6); Research's reviewability proposal:
  review it only when the user says so.
  **V2.4e real-calendar validation built 2026-11-03 night** (Codex gpt-6.1-terra, brief
  `docs/archive/briefs/v24e-real-calendar-validation.md`): `python -m backtester.tools.news_validate` ->
  `results/news_validation/`. Anchors: NFP 69/69, US CPI m/m 63/63, FOMC statement 47/47 at
  their published times; US CPI y/y 2 and Core CPI m/m 9 rows, BoE 1 row (11:02 UTC) off.
  **Finding for the user:** 386 High data releases (CPI, PMIs, claims, employment; 2023: 181,
  2024: 186) are exactly 1 h off their event's usual time, the source's known DST defect that
  the cleaning does not repair; with 2 / 2 min windows the filter and the news split miss them
  in 2023-24. 311 of 4,652 High rows (6.7 %) stay day-only. Question: add a `news_clean` rule
  that moves an exact row exactly +-60 min off its event's mode onto the mode?
  **Step (4) 2026-11-03 night, browser on the idle PC** (newest run 10,397 trades, warm): the
  chart was usable at 4.5-4.9 s because the browser spent ~2 s on the 100 trade rows before it
  asked for the candles; the list's first fill now waits for the candles (`chart-base` with
  candles), later redraws keep it: chart usable **2.2-2.6 s** (target < 4 s met), the list
  follows at ~4 s, a page step ~2.3 s. Same look; Opus, test-first. Seen once in ~10 loads:
  a request ended in `ERR_CONNECTION_RESET` and the page stayed on "Updating..." (Dash does
  not retry; dev server; cause not found, a reload fixes it). **Measurement note:** the
  in-app browser pane needs ~19 s for any response above ~1 MB (curl: the same 2.3 MB Results
  response in 0.5 s), so pane timings of large pages are not representative; the hangs may be
  the pane too. Other pages in the pane: Portfolio 1.1 s, Live 0.9 s, Backtest instant.
  **U2 built 2026-11-03 night** (Opus, test-first): the Research layout no longer builds the
  cards the refresh callback builds again on load; layout 1.29 MB -> 144 KB, cards shown at
  1.35 s in the pane (was 9.4 s there).
  **T1 2026-11-03 night** (Opus, test-first): `settings` caches each dataclass's type hints
  (`get_type_hints` ran 25,639 times in one runner test); research-runner variant settings
  8.9 s -> 3.4 s there. **Full suite 5,111 passed in 8 min 10 s** (15 min 39 s before V2.8;
  target ~8 min met); golden lists identical.
- ◐ **V2.9 Multi-symbol strategies** (2026-11-10/11, design `docs/design/multi-symbol.md`, Codex sol): ☑ 1a
  reference-symbol snapshots / market-aware strategies (`0741e6a`, golden identical); ☑ 1b research
  integration (strategy-declared references, research pieces cut at reference gaps, manifest, blocked
  counts; Opus's picks accepted by the user 2026-11-11: references in the strategy config, not a grid
  table / CLI flag; per-decision journal deferred; Opus builds it, not Codex; `5b33a5f`, done per the
  user 2026-11-11); strategy 14 `us_close_de_open` built on it (Codex sol, Opus review) and its gates
  tool (Codex terra); development run 2026-11-12: falsified (ledger L14); ◐ B two-leg trades (accepted by the user 2026-11-12, "Yes, build two-leg"; increments: ☑ 2a-1 group model + group R arithmetic (`056adda`), ☑ 2a-2 paired M1 engine (`6aced59`), ☑ 2a-3 runner / artifacts (`7e8a89d`; one trades.csv row per group), ☐ 2b research / risk (deferred 2026-11-12: P01 / P02 failed the pre-build screen, no pair strategy to serve yet), ☐ 2c account protection only on the user's go); ◐ C baskets (only on the user's go; go given 2026-11-14 for the crypto carry research tool only, "Yes, all three": `docs/strategy-crypto_carry.md` › Build plan).
- ◐ **V2.10 Review follow-up** (Fable review + harvest framework, `knowledge/reviews/2026-11-11-*`; Opus's
  picks accepted by the user 2026-11-11): ☑ B2 test opt-in, ☑ B3 gap fade test struck, ☑ B5 / B9 / B1 / B8
  cost fixes (numbers `knowledge/research/reports/2026-11-11_cost_fixes_old_vs_new.md`), ☑ A1 ledger
  `research/ledger.csv`, ☑ A4 / A7 / A8 / A10 / B7 rules, ☑ archive moves and stub removal, ☑ ideas D1-D5,
  ☑ `tools/harvest.py` + skill `idea-harvest`; ☑ harvest pilot (2026-11-12: web access fixed with `--search`; batches 3-9 run 2026-11-12/13, pipeline fixes 2026-11-13: blocked pages parked `unfetchable`, `check` appends, seller check near the quote, canary from an open family; accepted by the user 2026-11-13 at End), ☐ B4
  dividends (question to FTMO in `docs/ftmo-dividend-question.md`), ☑ A3 one gates tool (`tools/gates.py` + `[gates]` table, `--controls`; one block bootstrap; 2026-11-12, `7771f8e`), ☐ A9 results out of the specs (deferred 2026-11-12: result blocks in `strategy-timed-hold.md` interleave user rules and pre-registered criteria, so no mechanical move; low value while its families are closed), ☑ shrink
  the slowest tests (2026-11-12: gates controls 50 -> ~23 s by vectorized bootstrap means, same draws and pinned
  values; planted monkeys 39 -> 4 s serial; the 8-process file-lock race stays), ☑ finished ROADMAP steps to the archive (`docs/archive/ROADMAP-v2-done.md`, 2026-11-12).
- ☐ **V2.7 Portfolio:** combine strategies that balance each other by regime; combined equity,
  correlation of daily R, Monte Carlo prop-firm pass probability, leave-one-out; the user picks.
  - ☑ **Challenge path simulator + FTMO rule sets** — accepted by the user 2026-11-13 (Results tab "Challenge path",
    `tools/challenge_path.py`; full entry in `docs/archive/ROADMAP-v2-done.md`).

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
- **Changed 2026-11-09 (the user):** research is back in this team (`Continue.Research`, skill
  `continue-research`); new strategies come from `research/candidates/` (drafts of the former
  research department, 2026-10-27 to 2026-11-06, archived in `../archive/`) or a researched
  idea in `knowledge/ideas.md`. The safeguards, Monte Carlo, stability, regime, flags, lanes and
  job queue below still apply.
- Every strategy comes from research (book, paper, study, reputable source), cited in its
  `docs/` spec. Never invent or data-mine rules
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
- Pipeline per idea (until 2026-10-27; now `docs/research-intake.md`): (1) research -> idea file with sources (Gemini; while its quota is empty:
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
