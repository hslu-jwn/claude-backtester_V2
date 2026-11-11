# Handoff

Read first in every session; rewritten at the end of every session (CLAUDE.md › Session
protocol). Current state only; history is in git and `docs/archive/ROADMAP-v1.md`.

## Where things are (2026-11-11, `End.` of the 2026-11-10/11 research session, Test=auto)

- **Tested and recorded (research log 2026-11-10):** strategy 12 `energy_report` (EIA oil) falsified;
  strategy 13 `daily_reversal` (Connors E8 / CAP) falsified; hypothesis 15 Turtle Soup (setup TS)
  falsified; C1 crypto trend following inconclusive (primary 23 trades < 40, all 16 cells positive);
  C2 crypto momentum one-time MT5 test **not confirmed** (the user's go; +5.0 R, doubled -18.9 R);
  C3 crypto intraday momentum screened out on costs. Idea harvests: 4 Codex web rounds (48 ideas).
- **Code:** runner D1 UTC-aligned; crypto weekly / isolated-Saturday closures do not cut research
  segments; gates modes for energy_report / daily_reversal; **multi-symbol step 1a** (reference-symbol
  snapshots, `MarketAwareStrategy.on_market_candle`, `ReferenceInput`, golden identical, `0741e6a`;
  design `docs/design/multi-symbol.md`).
- **Pre-registered, not built:** five lead-lag strategies (specs + grids, all open points decided by
  Opus after a skeptic review): 14 `us_close_de_open` (prior 15-20 %, literature 3-7 bp gross vs 2-6 bp
  costs), `oil_cad_leadlag`, `usd_breadth_usdcad`, `gold_silver_leadlag`, `btc_eth_leadlag`; three DRAFT
  pair / basket specs (`wti_brent_spread`, `gold_silver_ratio`, `fx_relative_strength`) that need steps B / C.
- **Pre-sample data added (the user's go):** histdata 2008/09/10-2014 XAUUSD, XAGUSD, USDCAD, USOIL, UKOIL
  in `data/cache/histdata_presample/`; clock check `results/presample_2008_2014/clock_check_metals_cad_oil.md`:
  excluded years XAUUSD 2009, XAGUSD 2009 + 2011, USDCAD 2009, USOIL + UKOIL 2010.
- **Rules set by the user this session:** Telegram on a promising strategy or > 5 min waiting; broad idea
  sources (no academic backing needed); never idle (propose or ask); Sonnet only for small work.
- **Uncommitted, not Opus's:** `src/backtester/tools/notify.py` (hook trace log lines); the user decides.

## Earlier: 2026-11-10 `End.` of the 2026-11-09/10 session

- **Session summary:** research hypotheses 11 (Gotobi USDJPY: development +16.5 R, pre-sample
  2008-2014 +30.9 R, one-time MT5 test **not confirmed**, bootstrap bound -0.012) and 12 (month-end
  post-fix USD: falsified on 2008-2014); two pre-registered calendar x clock screens (FX 792 cells,
  indices 660 cells) with 0 survivors; pre-sample histdata 2008-2014 for 6 FX pairs and 2010-2014
  for 5 indices in `data/cache/histdata_presample/` (the user's go). Code: gate 7 rollover tolerance
  in `tools/timed_hold_gates.py`; 12.5 reconciliation of runs 3 + 4 (all trades explained);
  `tools/reconcile.py` reads `no_history` starts. The live-spread proposal stays unapplied (its spread
  raises were already in; the rest would lower slippage). Tests at `End.`: 5,483 passed, 14 skipped, 4 xfailed (8 min 52 s), ruff clean.
- **Uncommitted, not Opus's:** `src/backtester/tools/notify.py` (hook trace log lines); the user decides.

- **Fill probe run 4 STOPPED** 2026-11-09 08:39 UTC (STOP file, the user's go; closed nothing):
  ran from 2026-11-05 21:21 UTC on the new 14-day trial, final balance 90,159 of 100,000
  (-9.84 %, just above FTMO's 10 % max loss). Log `results/live/probe_stdout_run4.log`. Next:
  fill report + 12.5 reconciliation on runs 3 and 4.
- **12.5 reconciliation of runs 3 + 4 (2026-11-09 night, `results/reconcile_2026-11-09/`, today's
  costs, live-spread proposal not applied):** 2026-11-03 11:21 .. 2026-11-09 08:39 UTC: 3,502 matched,
  15 demo-only (2026-11-04 00:00, bar missing in cache), 621 engine-only, all explained: 606 by the tool
  (daily stop, skips, bot down) and 15 at 2026-11-03 11:30 because the bot had no price history for
  those symbols at its 11:21 start (`no_history` in `probe_stdout_run3.log`; the tool does not read that
  log yet). Exit reason agrees 87-99 % per symbol except NATGAS (52 %); the engine is more conservative
  on matched trades for most symbols (e.g. US500 -38 vs demo -29 R); NATGAS demo -525 vs engine
  -1,111 R (the R-basis gap of 2026-11-03). Baseline: 5,479 passed, ruff clean. No default changed.
- **Research back in this team (the user, 2026-11-09):** the research department is archived in
  `../archive/research-department-2026-11/` (with `Shared_Interface/`); its records, evidence
  checks and registries are in `knowledge/research/`, its 20 unbuilt drafts in
  `research/candidates/` (prioritised README). `Continue.Research` = skill `continue-research`
  (pick a candidate or research an idea, spec with pre-registered gates, build, development run,
  gates). Intake tool removed (archived in `../archive/v2-intake-tool/`). Also archived: V1,
  `old/`, `book-notes-2026-10-23/`; the merged `bt-live` worktree was removed (branch `v2-live`
  kept). Umbrella layout: `../AGENTS.md`, `../archive/README.md`.
- **Continue.Research run 1 (2026-11-09, 11:43-14:30):** strategy 10 `timed_hold`
  (`docs/strategy-timed-hold.md`, registry `timed_hold`, gates `tools/timed_hold_gates.py`),
  7 pre-registered hypotheses / 16 cells from published effects, development only (test period
  untouched). **No family advances.** The one lead: F1a, short EURUSD 07:00-13:00 London
  (Breedon & Ranaldo): +68.9 R / 1,723 trades after the FX ATR fix, p 0.0067, passes costs x2,
  halves, bootstrap and best-date removal; fails breadth (GBPUSD net negative, gross positive) and
  the joint F1 rule (F1b fails). The EURUSD placebo profile has the paper's daily shape with 07:00
  as its extreme; but the edge faded in 2020-21 and 17 trades carry 58 % of it. Every published
  effect tested shows the predicted sign gross (indices, crosses) at +0.01-0.03 R per trade, below
  the 0.04-0.06 R cost: `knowledge/topics/cost-wall.md`. None of the 18 M15 candidates is worth a
  build (triage report). Decisions for the user:
  (1) F1a: download EURUSD / GBPUSD 2008-2014 for an untouched pre-sample check (plan
      `knowledge/research/reports/2026-11-09_presample_2008_2014_plan.md`: separate cache, runner
      `--cache-dir` option about 10 lines, histdata clock check first), and / or the one-time MT5
      test of F1a (2021-09-14 on), or drop it;
  (2) a gap-tolerant integrity gate (> 5 missing minutes) and skipping NYSE closure / early-close
      days in index families (US500 histdata omits many quiet minutes, spec › Results);
  (3) the live-spread proposal (below).
- **Live spreads (2026-11-09, the user):** fill report on runs 3 and 4 (7,019 fills):
  `results/fill_report_2026-11-09/` (`report.md`, `spread_proposal.md`); under-charged spread
  GBPJPY 2.25x, GBPUSD 1.97x, NAS100 1.95x, UK100 1.77x, GER40 1.52x (means; FX medians fit, the
  tail is Asia / rollover hours); BTCUSD slippage 5x. Proposal only in
  `data/spreads/proposal_live_2026-11-09.json`, not wired in: applying it is the user's decision
  (4.6 days, demo account).
- Hypothesis 6 (F2L, momentum on large-move days) also falsified (spec).
- **Tests (2026-11-09, after research run 1):** 5238 passed, 11 skipped, 3 xfailed (8 min 35 s);
  ruff clean. Earlier the same day after the merge: 5159 passed (8 min 7 s; the
  intake tests left with the tool); ruff clean.

## Earlier state (2026-11-03 night run, V2.8)

- **Repo:** V2 = `X:\Dokumente\Projekte\backtester-claude\backtester-claude_V2`, GitHub
  `hslu-jwn/claude-backtester_V2`. V1 is archived (`../archive/`), read-only.
- **Branches:** work on **`v2-6-research`** (pushed). `main` = merged 2026-10-27 at `da7efb9`;
  everything after (UI, V2.6d, news, V2.6i) is **not merged** yet. Merge to `main` only on the
  user's word.
- **Tests (2026-11-03):** 5111 passed, 7 skipped, 1 xfailed (8 min 10 s); ruff clean. Golden
  lists unchanged since 2026-10-27 (news filter is off by default).
- **Data:** 34 FTMO symbols (+ Binance), cache rebuilt 2026-10-26. News calendar at
  `data/news/economic_events.csv` (git-ignored; rebuild with `python -m
  backtester.tools.news_clean ../backtester-news/economic_events_2020_to_2026-10-25.csv`).
- **Demo bot STOPPED** by the user (last log line 2026-10-31 01:00 local): the FTMO demo
  challenge failed at max drawdown. The fill-probe run (`--strategy fill_probe`, 23 symbols,
  0.01 % risk, prefix `fp`) ran 2026-10-27..31; log `results/live/probe_stdout.log`. Its
  `status.json` was never written (R1, fixed 2026-11-02), so the Live page showed "not
  running" throughout. **New account 2026-11-02:** the user opened a new FTMO 14-day trial
  (logged in in MT5) for more fill collection and 12.5 reconciliation; the old account's deals
  are not in it (the bot's own `paper.csv` / `trades.csv` keep every fill). A bot restart is
  the user's call; restart only between :21 and :28. Stop: `results/live/STOP` (`EMERGENCY`
  closes all).
- **Fill report 2026-11-02:** `results/fill_report_2026-11-02/` (5,512 fills 2026-10-27..31,
  23 symbols, 1,502 London; commission only from the 10-27/28 deals file).
- **Finalization (V2.8, plan accepted 2026-11-02):** audit in
  `docs/archive/review/finalization-audit-2026-11-02.md`; night run 2026-11-02/03 in
  `docs/archive/review/night-2026-11-03.md` (phase 3 and 4 done; three questions for the user there).
  Chart usable 2.2-2.6 s (was ~30 s).
- **LibreHardwareMonitor** (port 8085) feeds the queue's temperature guard; start it after a
  reboot (admin prompt).
- **App:** `restart_app.bat`; dev preview for Claude: `..\.claude\launch.json` (port 8052).
- **PC quirks:** long runs log to a file; .ps1 disabled; no backticks in inline PowerShell.
- **AI team (session 2026-11-02, accepted by the user):** one routing table,
  `docs/agent-routing.md` (local tools -> free local Ollama -> Codex terra / sol -> Opus only
  for escalation; no cross-review chain). `ai_dispatch` lanes: `local` (Ollama), hosted free
  APIs `groq`, `openrouter` (`:free` only), `gemini-api` (all probed OK), `deepseek` (key OK,
  no balance, needs `--allow-paid`); GitHub Models off (endpoint answers "OK" to everything);
  no Astra (no access). `ai_dispatch stats` sums usage. Keys: Windows Credential Manager,
  `<provider>@backtester-ai`. `Continue.Research` procedure is now the `continue-research`
  skill. Baseline before the change: tag `pre-agent-migration-2026-11-02`.
- **Open:** top up DeepSeek to enable it (optional).

## Research (one team again since 2026-11-09)

Focus: **day trading** (the user). Backlog: `research/candidates/README.md` (former department's
drafts, highest priority M15_SHOCK_RESPONSE_BATCH) and `knowledge/ideas.md`. Tested and rejected
by the user: FX_LONDON_FIX_REV (2026-10-29), M15_ALTERNATING_PATH_BATCH / R014 (2026-11-06).

## State of the current work

| Item | State |
|---|---|
| V2.4b | built 2026-11-03: measured fill p90 per symbol is the stressed cost level (`analytics/slippage_p90.json`, 5,512 fills) |
| 12.5 | built 2026-11-03: `tools/reconcile.py`, all demo trades matched / explained (`results/reconcile_2026-11-02/`) |
| V2.4e news filter | wired into every run; FTMO restricted-event scope; **off by default** (accepted); real-calendar validation built 2026-11-03 (`tools/news_validate.py`); 1-hour rows fixed by `news_clean` rule 3 (2026-11-03, 665 rows; anchors 5 / 6 pass) |
| V2.6i intake | retired 2026-11-09 (tool archived); i1-i7 done; i8 pilot FX_LONDON_FIX_REV run 2026-10-28: all 9 variants negative, result envelope sent, **rejected by the user 2026-10-29**, moved to `queue/rejected/`, Research told (`docs/research-log.md`) |
| R014 M15_ALTERNATING_PATH_BATCH v0.2.0 | claimed 2026-11-05, strategy 9 `alternating_path` built (`docs/strategy-alternating-path.md`, grid `research/grids/alternating_path.toml`); development run 2026-11-06: all 4 cells negative (-2,585 to -3,925 R), every gate fails except the trade count (`results/research/alternating_path_1ffe705d/gates.json`); envelope published; **rejected by the user 2026-11-06**, moved to `queue/rejected/`, Research told (decision + gate readings) |
| Built, waiting for the user's acceptance | none; V2.6j, V2.6k, V2.6l and V2.4c checks #2 #6 #13 accepted by the user 2026-11-03 |
| Deals export | `scripts/export_deals.py <since> --offset-hours 3` (+2 h from 2026-11-01), read-only |

## Accepted / decided by the user (do not ask again)

- 2026-11-09: research department folded back into this team and archived; intake tool
  removed; V1, old folders and the bt-live worktree archived / removed; fill probe run 4 stopped.
- 2026-11-06: R014 M15_ALTERNATING_PATH_BATCH v0.2.0 rejected after the development stage.
- 2026-11-02: V2.8 finalization plan (audit), U1 chart pager (looked at), V2.4b now, no
  `pytest-xdist`, R1 `live/` status fix, night-run rules (ROADMAP V2.8), 12.5 scope.
- 2026-10-28 (`End.`): everything of the night 2026-10-27/28 incl. Opus's decisions
  (`docs/archive/review/night-2026-10-28.md`): news filter off by default, FTMO scope default, V2.6i
  built before the fill analysis, empty text settings allowed, no one-time test spent.
- 2026-10-28 (midday): do not build the p90 stressed costs yet; the bot keeps running and the
  user comes back to it later. Fill report re-run at 10:35 UTC (1,511 fills, 339 London);
  brief ready in `docs/archive/briefs/v24b-p90-stress.md`, not dispatched.
- 2026-11-09 (the user, Open 9): swap is scaled by price / reference price like spreads (option a;
  no historical rate table).
- 2026-11-09 (the user, Open 10, option a): gate 7 tolerates rollover-hour gaps and gaps up to 6
  minutes for holds crossing the FTMO daily rollover; Gotobi G1 is ready for the one-time test.
- 2026-11-09 (the user): research multi-day holds too, with every fee counted (overnight swap
  incl. the triple-swap day, spread, commission, slippage; FTMO cost model). Day trading is no
  longer the only scope.
- 2026-11-09 (the user, answers to Open 5-7): (5) F1a: yes to the pre-sample check (download
  EURUSD / GBPUSD 2008-2014 into a separate raw root and cache, clock check, `--cache-dir` runner
  option, run F1a there); the one-time MT5 test is NOT part of it (needs its own go). (6) ok:
  gap-tolerant data-integrity gate (fail only on > 5 consecutive missing minutes or a missing exit
  candle) and skipping NYSE full-closure and early-close days in the index families. (7) yes:
  apply the live-spread proposal. Opus's reading of (7), recorded as an assumption: apply the
  proposal's raises (fixed spread of the under-charged symbols, BTCUSD slippage 0.5 -> about 2.5);
  keep the over-charged values as they are (conservative); the session-split table (proposal
  point 3) needs more data and is not applied. Golden lists regenerated with the new costs.
- 2026-10-28: slippage (V2.4b): keep the model slippage as default; after London fills, the
  measured p90 per symbol becomes the stressed cost level (instead of costs x 1.5).
- 2026-10-27: research department split, decisions D1-D8
  (`docs/archive/review/research-interface-review-2026-10-27.md` › 3), day-trading focus, fill probe
  left as it is, FTMO fees as defaults, news windows High 2 / 2, Medium none.
- Earlier: see git history of this file.

## Open (needs the user)

1. One-time MT5 test of the two remaining pre-registered V2 hypotheses (strategy 4 on GBPJPY; gap
   momentum in quiet sideways markets): only on the user's go. Gap fade's test is struck (review B3,
   the user 2026-11-11): V1 11.4 / 11.6 already ran it on 2021-09..2026, so only forward demo data
   could still test it.
2. ☑ `v2-6-research` merged into `main` 2026-11-03 (the user; fast-forward, full suite green).
3. ☑ Opening-range sessions for AUS200 / HK50 added 2026-11-03 (the user: AUS200 10:00-15:55
   Sydney, HK50 09:30-15:55 Hong Kong, held over lunch).
4. ☑ Research's reviewability proposal: moot, the department is archived (2026-11-09).
5. ☑ decided 2026-11-09; pre-sample check done: F1a does NOT pass (EURUSD 2008-2014 +40 R net
   but bootstrap lower bound -0.009). Still open: the one-time MT5 test of F1a (criteria
   pre-registered in the spec), only on the user's go; Opus's view: weak, park it.
6. ☑ done 2026-11-09 (`0c2178c`): gap-tolerant integrity gate, `skip_nyse_short_days` in the index grids.
7. ☑ done 2026-11-09 (`d0bbcd8`): spreads of 17 symbols and BTCUSD slippage raised; golden regenerated.
8. ☑ decided 2026-11-09: multi-day holds are in scope ("yes, but regard the fees"; in progress).
9. ☑ done 2026-11-09 (`df600b4`): swap scaled by price / reference price, golden regenerated.
10. ☑ decided 2026-11-09 (option a, rule in spec › Hypothesis 11): rollover-hour gaps and gaps up to
    6 minutes do not fail gate 7 for holds crossing the daily rollover. **Gotobi G1 (USDJPY long
    03:00 -> 09:55 JST on gotobi days, stop 1.0) passes all seven gates: ready for the one-time
    test** (dev: 413 trades, +16.5 R net, doubled costs +9.7 R, p 0.0035). Criteria pre-registered
    in the spec; the test runs only on your go.
11. ☑ decided 2026-11-09 ("Yes, all four pairs"): AUDUSD, NZDUSD, USDJPY, EURJPY histdata
    2008-2014 downloaded (28 files, `data/raw/histdata_presample/`) for the four-pair H12
    confirmation and a Gotobi pre-sample check (criteria pre-registered in the spec).
12. ☑ decided 2026-11-09 (the user: "Yes, run the test"): Gotobi G1's one-time MT5 test runs once
    on 2021-09-14 to the last cached day, grid `research/grids/timed_hold_gotobi_test.toml` (the frozen
    primary cell only), criteria in spec › Hypothesis 11. Pre-sample: +30.9 R, gate 7 failed on
    histdata gaps (recorded). H12 falsified on 2008-2014.
    **Result: not confirmed** (USDJPY 321 trades, +6.6 R net, +2.5 R doubled, but bootstrap 2.5 %
    -0.012 R; spec › One-time test result). No retest. The 302 integrity flags were a histdata-only scratch
    check; on MT5 the post-2021 rollover break starts at 20:55 UTC, so gate 7's 21:00-23:00 window
    would need 20:55 for future FX holds across the rollover (a gate change: your call, low priority).

- **Strategy 11 `h1_shock` (2026-11-09):** the last drafted candidate that passed the cost screen,
  tested and falsified (all 18 cells net negative). With it, every research candidate is tested or
  triaged out; new work needs new researched ideas (and the user's answer to Open 8, multi-day
  holds).

13. ☑ decided 2026-11-10 (the user: "Yes, test C2"): crypto momentum C2 (BTCUSD momentum 20 / stop 2,
    chosen from C1's cells) gets its one-time MT5 test; criteria in `docs/strategy-trend-following.md` ›
    Hypothesis C2.
    **Result: not confirmed** (test 215 trades +5.0 R, doubled costs incl. swap -18.9 R, second half
    negative, bootstrap -0.114). No retest.

14. **Codex at its weekly limit (2026-11-10 14:54):** heavy work waits for the weekly reset (the user: "We'll
    wait for codex weekly reset tomorrow"). Next Codex job: multi-symbol step 1a (`docs/archive/briefs/multi-symbol-1a.md`),
    then 1b, then the five pre-registered lead-lag strategies (14 `us_close_de_open`, gold->silver, BTC->ETH,
    oil->CAD, USD breadth->USDCAD).

## Next step

In this order (Codex sol for engine work, terra for runs; Sonnet only for small work):
1. **Multi-symbol step 1b** (`docs/design/multi-symbol.md` › Delivery 1b): research grids / CLI with
   reference inputs, bundle coverage, gates support (weighted control, per-symbol overrides).
2. **Build and run the five lead-lag strategies** in prior order (14, oil-CAD, USD breadth, gold-silver,
   BTC-ETH) from their specs; sol review per new strategy; development gates; pre-sample checks on
   2008/10-2014 (excluded years above) before any one-time test; Test mode per the user's command.
3. Steps B / C (pairs, baskets: 13-21 + 7-12 engineering days) only on the user's go; then the three drafts.
Other open items: stressed-cost p90 refresh with runs 3 + 4 (needs the user's go); the user's check of data
fixes 13.12-13.18; gate 7's 20:55 UTC rollover start (low priority); `notify.py`.

## First prompt for the next chat

`Continue.Code` for multi-symbol step 1b, then `Continue.Research` (Test=manual unless the user says
`Test=auto`) to build and run the five pre-registered lead-lag strategies.
