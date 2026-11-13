# Roadmap V2: finished steps

Done (☑) and retired (☒) steps moved verbatim from `docs/ROADMAP.md` on 2026-11-12 (V2.10 review
follow-up). IDs are unchanged; open and in-progress steps stay in `docs/ROADMAP.md`.

## Open from V1

- ☑ **3.3d Review mode** (Phase 3) — every strategy, V2.6 step (5), accepted by the user 2026-10-27
- ☑ **3.5 Session view** (Phase 3) — built as trade inspection, every strategy, V2.6 step (5), accepted by the user 2026-10-27
- ☑ **4.3 UI layout and look review** (Phase 4) — Opus list, the user picked, V2.6 step (5), accepted by the user 2026-10-27
- ☑ **12.2 Intrabar order from M1** (Phase 12) — V2.4c T-03, default `engine.intrabar = "m1"` set by the user 2026-10-24
- ☑ **12.4 Parameter heat map** (Phase 12) — on the research card, V2.6 step (5), accepted by the user 2026-10-27
- ☑ **12.5 Demo reconciliation** (Phase 12) — V2.8, `tools/reconcile.py`, 2026-11-03; runs 3 + 4 reconciled 2026-11-09 (`results/reconcile_2026-11-09/`, all explained)
- ☑ **12.6 Stressed fills** (Phase 12) — V2.4b measured fill p90 as the stressed cost level, 2026-11-03
- ☑ **12.8 Engine slippage** (Phase 12) — fixed in V2.4 (B4), 2026-10-23
- ☑ **12.9 Portfolio tool** (Phase 12) — V2.7 portfolio page, accepted by the user 2026-10-26
- ☑ **12.11 Bayesian report** (Phase 12) — V2.4c T-10, accepted by the user 2026-10-26
- ☑ **12.13 DSR on daily R** (Phase 12) — V2.6d step (5), daily DSR everywhere, 2026-10-27
- ☑ **13.6 Closed-bar check on server time** (Phase 13) — fixed in V2.4 (live #1), 2026-10-23
- ☑ **13.7 Sizing on the live price** (Phase 13) — fixed in V2.4 (live #7), 2026-10-23
- ☑ **13.8 Wall-clock fallback exit** (Phase 13) — fixed in V2.4 (live #8), 2026-10-23
- ☑ **13.9 Validate CLI risk** (Phase 13) — fixed in V2.4 (live #18), 2026-10-23
- ☑ **13.17 Paths relative to the working folder** (Phase 13) — fixed in V2.4 (A2), 2026-10-23
- ☑ **13.19 no_wick limit fill is lookahead** (Phase 13) — refuted by two V2.4 reviews (pending limits precede the fill candle; now enforced by the engine, A1), 2026-10-23
- ☑ **13.20 Kind C random fills never slip time exits** (Phase 13) — fixed in V2.4 (B4), 2026-10-23
- ☑ **13.21 Parallel runner progress race** (Phase 13) — fixed in V2.4 (A5), 2026-10-23
- ☑ **13.22 `tests/tools/test_s2_volume_ab.py`** (Phase 13) — file removed in `8310d47` (strategy contract tests)
- ☑ **13.23 Monte Carlo FTMO pass rate** (Phase 13) — fixed in V2.4 (B2), 2026-10-23
- ☑ **13.12 histdata clock 2015-2018** (Phase 13) — V2.6 step (2), built 2026-10-26; accepted by the user 2026-11-12 (`docs/data-fix-check.md`)
- ☑ **13.13 GER40 histdata changes instrument on 2020-06-15** (Phase 13) — V2.6 step (2), built 2026-10-26; accepted by the user 2026-11-12 (`docs/data-fix-check.md`)
- ☑ **13.14 MT5 cache before 2020** (Phase 13) — V2.6 step (2), built 2026-10-26; accepted by the user 2026-11-12 (`docs/data-fix-check.md`)
- ☑ **13.15 One-day holes on 1 January** (Phase 13) — V2.6 step (2), built 2026-10-26; accepted by the user 2026-11-12 (`docs/data-fix-check.md`)
- ☑ **13.16 MT5 downloader swallows errors** (Phase 13) — V2.6 step (2), built 2026-10-26; accepted by the user 2026-11-12 (`docs/data-fix-check.md`)
- ☑ **13.18 Output folders** (Phase 13) — V2.6 step (2), built 2026-10-26; accepted by the user 2026-11-12 (`docs/data-fix-check.md`)

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
- ☑ **V2.4c Honesty tooling before V2.6** (done parts accepted by the user 2026-10-26; checks #2 #6 #13 accepted by the user 2026-11-03) (2026-10-23 / 24: T-10, T-09 PBO, T-19, T-14, T-03
  done; spread table measured 2026-10-25 (`results/spread_table.md`, median table: costs per
  trade +25 to +90 % at the index open, no-wick nearly x2; **default: the median table, set by
  the user 2026-10-26; re-evaluated after a period of demo trading (V2.4b)**); news-day split
  moved to V2.4e, 2026-10-26) (audit 2026-10-23, `docs/archive/review/backtest-audit.md`;
  audit asked for by the user 2026-10-23): T-10 Bayesian report, T-09 CPCV + PBO, T-19
  effective N, T-14 matched monkeys for every strategy, T-03 / 12.2 intrabar order from M1 (**done: default `engine.intrabar = "m1"`, set by the
  user 2026-10-24; golden net R 2023: session zones -484.9 -> -479.9, no-wick -1036.2 -> -959.7**);
  then measure the spread table's effect on the golden lists (default stays off unless the
  user decides) and a news-day split. The grid merge (V2.4) also takes the runner-level audit
  items: sensitivity around the chosen variant, filter twins, SE of expectancy, time in
  market, expectation haircut. **Re-check 2026-10-28:** all of these are built (grid merge 2,
  4d9be45; spread table default bd5a125; news split in V2.4e); what is left of the audit is
  listed in `docs/archive/review/backtest-audit.md` › Re-check 2026-10-28 (mostly T-16 / T-17 and
  partial checks), each needs the user's pick. **Picked by the user 2026-10-28, built the same
  day (Codex medium, Opus review; accepted by the user 2026-11-03):** #2 swept-setting count (flag
  `too_many_parameters` above 4), #6 entry screen of the chosen development variant in the
  runner (`entry_screen.json`, flag `entry_screen_failed`), #13 monthly returns slope
  (`returns_slope.csv`, flag `declining_returns` at t <= -2) and top-10 trades
  (`top_trades.csv`); brief `docs/archive/briefs/v24c-runner-checks.md`.
- ☑ **V2.4d Book requirements** (accepted by the user 2026-10-26; the tick-rounding default
  stays off until the user decides) (2026-10-23 / 24: items 1-9 done; open: the user's choice of
  the tick-rounding default, measured in `results/ticks.md`, built off) (accepted by the user 2026-10-23; Pardo, Masters, Aronson,
  `docs/archive/review/book-app-requirements.md` with the code check), in this order: (1) keep the daily
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
- ☑ **V2.5 App redesign** (accepted by the user 2026-10-26) (2026-10-25: V2.5a-d done: dark theme, top bar, Research cards,
  Chart / Results / Backtest / Live in the new skeleton, browser-checked by Opus; open: the
  user's look and ok) (decisions 2026-10-23 in `docs/design/ui-proposal.md`) after `docs/design/app-v2.png`: dark trading-terminal look, essential
  vs "Details" per page (list to the user first), research page as one vertical list of
  cards, Fast mode (headless) vs Visual mode with identical trade lists.
- ☒ **V2.6i Research-department intake — retired 2026-11-09 (the user: research back in this team; `tools/intake.py`, its tests and `docs/research-intake.md` moved to `../archive/v2-intake-tool/`, `dataset_version` moved to `tools/research.py`; second submission R014 rejected by the user 2026-11-06). History: (the user, 2026-10-27; i1-i7 built 2026-10-28 night, accepted by the user 2026-10-28: `tools/intake.py` validate / claim / recover / reject / progress / result / finish, `[submission]` grids with dataset fingerprint, commit and test authorization gate, briefs `briefs/v26i-*.md`; i8 = first real pilot FX_LONDON_FIX_REV v1.0.0, run 2026-10-28, rejected by the user 2026-10-29):** strategy ideas now come from
  `../Research_Department/` through `../Shared_Interface/` (process: `docs/research-intake.md`;
  review and decisions D1-D8: `docs/archive/review/research-interface-review-2026-10-27.md`). Test-first
  steps, no engine change: (i1) contract frozen with the agreed edits + fixtures; (i2)
  `tools/intake.py validate`; (i3) atomic claim, lease, crash recovery (`backtester.filelock`,
  `results/intake/`); (i4) submission mapping section in each strategy spec; (i5) strategy /
  experiment / dataset / commit / stage metadata in `settings.json` and the trial log; (i6)
  result and feedback envelope emitters, test-stage run refused without the user's go; (i7)
  synthetic end-to-end fixture; (i8) first real R-type pilot, development stage only. Decisions
  D1-D8 by the user 2026-10-27 (two stages, built after the V2.6d step-1 fill analysis,
  `jsonschema` as optional extra, stopless / portfolio and next-bar-open rejected for now with a
  future-support list, old idea backlog to research, test only on the user's go, queue files
  kept). Contract 0.1.0 accepted by both teams 2026-10-27 (research applied all requested
  edits), so i1 is down to the fixtures.
- ☑ **V2.6j Automatic research loop (the user, 2026-10-28; built 2026-10-29, accepted by the user 2026-11-03):** assumptions instead of waiting,
  async questions to Research (`docs/research-intake.md` › Assumptions and replies); build
  `intake inbox` (open questions of ours, unprocessed replies, age in days), `intake assume`
  (ASSUMPTION_MADE message from a list), parked claims for `NEEDS_CLARIFICATION`, the open
  count in the loop report / HANDOFF, open assumptions listed in the result envelope. Codex
  brief after the pilot (V2.6i i8). Research accepted the workflow 2026-10-28
  (`FB_CONTRACT_REPLY_20261028T134149Z_RESEARCH`). **Built 2026-10-29** (Codex
  gpt-6.1-terra, Opus review): `intake inbox [--json] [--ack]`, `assume`, `park`, `parked`,
  automatic unpark on a higher version, open / answered assumptions in every result envelope.
- ☑ **V2.6l Result envelope for research review (accepted by the user 2026-11-03; Research's review 2026-10-29,
  `FB_FX_LONDON_FIX_REV_RESULT_REVIEW_20261029T070325Z_RESEARCH`; our answer
  `FB_FX_LONDON_FIX_REV_20261029T164921Z_83af`):** embed every declared cell in `robustness`
  (cell ID, parameters, trades, net / gross R, halves, x2 and x1.5 stresses labelled, stop
  share, criteria inputs); `variants_tried` = declared cells only, sensitivity runs reported
  apart. Plus for INTRADAY_H1_SHOCK_RESPONSE (draft, preflight answered
  `FB_INTRADAY_H1_SHOCK_RESPONSE_20261029T164921Z_e881`): a run-level data-integrity check
  that fails the experiment as TEST_FAILED on a missing M1 bar inside trading hours while a
  position is open (definition proposed to Research), day-clustered uncertainty, raw
  forward-response series next to executed R. Codex gpt-6.1-terra.
- ☑ **V2.6k Fast loop (built 2026-10-29 in `80499b0`, accepted by the user 2026-11-03) (the user, 2026-10-28; pilot: 9 variants + sensitivity 3 min, monkeys
  > 5.5 h single-core on 10,397 trades):** (1) fail fast: stage 1 = backtests, scorecard,
  halves, cost stresses and the submission's cheap rejection criteria; monkeys and entry screen
  only for a variant that survives stage 1; (2) monkeys / entry screen parallel over processes
  (like `run_backtests`), a cheaper pre-screen, the spec's 1,000 runs for a real candidate;
  (3) the submission's rejection criteria computed by the runner (today a script,
  `results/intake/<stem>/criteria.json`). Codex `gpt-6.1-terra`, test-first.

## V2.7 Portfolio (sub-steps; the step itself is open)

- ☑ **Challenge path simulator + FTMO rule sets (the user, 2026-11-02; built 2026-11-13 on the user's "do all":
  core + CLI `tools/challenge_path.py` (`cd6b79a`), Results tab; rules verified on ftmo.com 2026-11-13,
  spec `risk-management.md` › Challenge path simulator; accepted by the user 2026-11-13):**
  (a) replay a run's trades in time order at a fixed risk % on e.g. a $100k account through
  the existing `risk/prop_rules.py` (same rules as Monte Carlo and the live guard); on the
  Results page plot balance, daily-loss and max-loss lines and a pass / breach marker, with a
  start-date picker and a risk % input; run from many start dates (e.g. monthly) to show the
  spread. A new, smaller item, not a reopening of 5.2 (`risk/account_sim.py` stays a stub;
  5.1-5.7 stay as they are, the user 2026-10-22). (b) FTMO 1-Step and Instant rule sets next
  to the existing 2-Step config, built from FTMO's current published rules (verified online
  at build time, not from memory); compare a candidate's trades across all three: pass
  probability, time to funding, breach risk, cost per funded account (a slow, low-drawdown
  strategy may suit a no-target account, but trailing drawdown / consistency rules can hurt
  it). Build when a strategy survives research (none has an edge yet, so paths would only
  show breaches).
