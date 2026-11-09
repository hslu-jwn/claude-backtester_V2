# Research log

Running log of the research loop (V2.6 / V2.7) and of the model / effort used per task, so a
run resumes after a restart or a usage limit. Newest first. Every AI call is also logged by
the dispatcher in `results/ai_calls.jsonl` (model, effort, seconds, status).

## 2026-11-09: continuous Continue.Research (routing back to Codex first, the user)

- **Hypothesis 11 Gotobi USDJPY (evening):** idea scan Gemini Flash low (free; month-end fix, OPEX,
  gap fade, quarter-end already covered or built; Gotobi new); Opus opened arXiv:2301.13204 via a
  fetch agent (Gemini's NBER Gotobi citation is a Tokyo-fixing paper without Gotobi results). JP
  holiday calendar from the Cabinet Office CSV. Build: Codex gpt-6.1-terra medium (`day_filter =
  "gotobi"`); review: gpt-6.1-sol medium, read-only, no defects. Dev run: G1 passes gates 1-6
  (USDJPY +16.5 R, p 0.0035), fails gate 7 on rollover-hour gaps (23 trades) -> HANDOFF › Open 10;
  G2 falsified. Gap listing: a scratchpad script calling `integrity_failures` per trade.
- **Gotobi one-time test (the user's go):** frozen one-cell grid `timed_hold_gotobi_test.toml`
  (dev reproduced +32.0 R); test 2021-09-14..2026-11-08 USDJPY +6.6 R, criterion 2 (bootstrap) fails:
  not confirmed, no retest. H12 falsified on 2008-2014; Gotobi pre-sample +30.9 R (gate 7 fail).
- **Idea scans 2-3 (Gemini Flash low, free):** fixings / flows: quarter-end USD funding is a
  forward-basis effect (not spot), gold / ECB fixes dead per the scan; the W pattern of Krohn, Mueller,
  Whelan (JF 2024, confirmed via the Bank of Canada summary) -> Codex screen -> hypothesis 12. Scheduled
  flows: LETF end-of-day = the falsified F2L family; index rebalance days about 28 events (too few);
  Nikkei SQ and post-NFP drift unsourced (bp claims of 25-55 look inflated): screened out.
- **Routing note (the user, 2026-11-09 evening):** Claude tokens run out as fast as Codex and Codex
  can be reset, so more work goes to Codex (screens, runs, diagnostics, not only code).
- **User decisions:** pre-sample check of F1a (yes), gap-tolerant integrity gate + NYSE short-day
  skip (ok), live-spread raises (yes); see HANDOFF › Accepted.
- **Tooling (Codex gpt-6.1-terra, medium):** `tools/time_of_day_profile.py` (screen hourly drift
  vs costs, dev only); research runner `--cache-dir`; histdata clock rule US DST through 2018
  (Opus measured the 2008-2014 clock on NFP / FOMC release spikes: one hour off in every
  US-summer / Europe-winter week under the old rule).
- **Screen (Opus, profile tool):** hourly profiles of six USD pairs (London clock, 2015-2021): the
  USD strengthens in the European morning in every pair, but a 07:00-13:00 hold sums to only
  1.2-1.9 bp per day on USDJPY / AUDUSD / NZDUSD / USDCAD / USDCHF vs 1.0-1.8 bp cost; only EURUSD
  (-2.9 bp vs 0.8 bp) clears. No new family built (screen, not a hypothesis).
- **F1a pre-sample 2008-2014** (pre-registered `27b3fcb`): EURUSD +40.4 R net, +0.023 R per trade,
  doubled costs +10.8, both halves positive, bootstrap lower bound -0.009 -> **fails criterion 3**;
  5 of 7 years positive. Spec › F1a pre-sample check.
- **Live-spread raises applied** (the user's yes; Codex gpt-6.1-sol medium): fixed spreads raised
  for 17 symbols (e.g. GBPUSD 0.3 -> 0.59 pip, GBPJPY 1.0 -> 2.3, NAS100 1.0 -> 1.9, UK100 1.45 ->
  2.6, GER40 1.53 -> 2.3, XAUUSD 0.25 -> 0.41, US500 0.5 -> 0.61), BTCUSD slippage 0.5 -> 2.5;
  nothing lowered; spread table untouched. Golden lists regenerated (one count 2,511 -> 2,516);
  full suite 5,289 passed. Earlier research results used the old (lower) costs: index and GBP
  results above are, if anything, too kind.
- **Strategy 11 `h1_shock`** (candidate INTRADAY_H1_SHOCK_RESPONSE, unblocked by the NYSE calendar
  and Opus's session / data-validity decisions): spec draft + build by Codex sol (it stopped three
  times on undefined data rules; each decided by Opus and recorded); read-only sol review (no
  material finding); gates tool by Codex terra. Development run: all 18 cells net negative
  (-0.001 to -0.022 R per trade), primary response q indistinguishable from zero. Falsified.
- **Gap scan** (Gemini Flash low, free; `results/ai/20261109-160127_gemini_gap-scan.md`, leads
  only): intraday time-series momentum (Li, Sakkas & Urquhart 2022) = the F2 family already tested;
  pre-release macro drift (Kurov et al., JFQA 2019) runs with the coming surprise, not tradable
  without it; VPIN / order-flow rules need volume data we lack; one USDJPY session rule attributed to
  Frömmel & Lampaert looks unreliable (not opened). Nothing new worth a build: the same-day idea space
  is exhausted at our costs; the next direction waits on HANDOFF › Open 8 (multi-day holds).
- **Multi-day scope** (the user: "yes, but regard the fees"). Free-model scan (Gemini low; leads
  only). **Hypothesis 9 F4M** (turn of the month close to close, pre-registered `915b43c`, multi-day
  support by Codex sol `cb954f8`): falsified, TOM is no better than a mid-month control week in
  US500 / NAS100 / UK100 / GER40 / JP225 (spec). Found: the engine's swap is not price-scaled, so it
  overstates 2015-2021 index financing about 3x (HANDOFF › Open 9).
- **Hypothesis 10 (I-03 RSI(2) index mean reversion,** Kaufman; RSI signal by Codex sol, flat-RSI fix
  by Codex terra): falsified, primary US500 -3.9 R net over 309 trades, no cell advances. Overnight
  drift and FX carry screened out on fees (spec). Multi-day idea space with published support at our
  fees is now thin; next candidates need new research.
- Models: Codex terra x3 (all ok, no violations; one false-positive risk avoided after Opus learned
  not to commit during a dispatch); Opus coordination, clock check, screen, review. No Sonnet.

## 2026-11-09: Continue.Research run 1 (11:43 to 13:59 CET, the user)

- Limit 13:59 CET; the user asked for quality research with Sonnet sub-agents (more than usual).
- Plan: (1) cost-in-R table per symbol and stop size; (2) triage of the 18 M15 candidates against
  it; (3) literature on effects with published, post-publication evidence whose gross edge per
  trade can exceed our costs (macro-announcement days, FX time-of-day, index intraday momentum,
  calendar effects); (4) best idea -> spec with pre-registered gates -> build -> `--dev-only` run.
- **Literature (Sonnet sub-agents, sources marked opened / abstract):** reports in
  `knowledge/research/reports/2026-11-09_*.md` (macro announcements, FX / gold time of day, index
  intraday momentum, calendar effects, commodity / EU / Asia intraday, cost-in-R table, M15
  triage). Kept: Breedon & Ranaldo FX sessions, Baltussen et al. last-30-minute momentum,
  Lucca & Moench pre-FOMC (falsification only), turn of month. Dead: pre-holiday, day of week,
  macro-day long, pre-ECB, gold sessions, overnight drift. M15 candidates: none worth a build.
- **Cost table:** 0.2 R per trade at a 1-ATR M15 stop, 0.02-0.04 R at a 0.5 daily-ATR stop
  (indices, majors). Only session-sized holds leave room for a published few-bp effect.
- **Strategy 10 `timed_hold`** (`docs/strategy-timed-hold.md`): fixed-time hold, ATR stop, day
  filters (FOMC, turn of month, pre-holiday) from published calendars, `with_day` direction.
  Pre-registered in `6e4569c` (families, gates) and `4b8819a` (F2 European legs) before any run;
  skeptic review by a sub-agent applied before the run (disjoint baselines, F1 joint rule,
  p-values vs 0.01). Built by a Sonnet sub-agent (51 tests), gates tool by a second one
  (`tools/timed_hold_gates.py`), both checked by Opus (code read, targeted suite 916 passed).
- **Results (12 cells, 5 hypotheses, development only, test period untouched):** no family
  advances. F1a EURUSD short 07:00-13:00 London +72.5 R net / 1,723 trades (+0.042 R, p 0.008,
  passes costs x2, halves, bootstrap, best dates) but GBPUSD -25.8 net and F1b (USD-hours long)
  fails, so F1 is not supported by its pre-registered joint rule. F2 last-30-minute momentum:
  positive gross in all 5 indices (+10 to +36 R) but net negative (costs 0.04-0.05 R vs about
  +0.01-0.03 R gross per trade). F3 FOMC mornings -0.27 R per trade vs other days (falsified,
  opposite of the 1994-2011 drift). F4 turn of month: no effect. Table: spec › Results.
- **Hypothesis 6 F2L** (pre-registered `fdb450c` after the F2 results, counted as new): F2 only on
  days with |move| >= 0.5 daily ATR. Falsified: US500 -0.035 R per trade net, gross +0.008 R;
  NAS100 / UK100 negative, GER40 +6.6 net (fails costs x2). 6 hypotheses, 15 cells in total.
- **Hypothesis 7 F1X** (pre-registered `e2d8744`): short EURJPY / EURAUD / GBPJPY / GBPAUD in
  European hours. Gross positive on all four (+25 to +42 R), net negative on all four (costs
  0.04-0.06 R vs +0.02 R gross per trade). 7 hypotheses, 16 cells in total. The mechanism shows
  up gross everywhere; it clears costs only on EURUSD.
- **Follow-ups (spec › Run 1 follow-ups):** a code review found the FX daily ATR about 8 % too
  small (Fridays irregular, Sunday stubs counted); fixed (`atr_skip_weekend`, tolerance 180) and
  the FX families rerun: no verdict changes (F1a EURUSD +68.9 R, p 0.0067). EURUSD placebo
  profile (6-hour long holds from every London hour): a smooth Breedon-Ranaldo shape, 07:00 the
  extreme. F1a dissection: 6 of 7 years positive but faded in 2020-21, top 1 % of trades = 58 %
  of net. More literature: EURUSD-specific effects (nothing better than Breedon-Ranaldo), crypto
  intraday (nothing that beats costs; leads: fade after large 1-4 h moves, first-to-last
  30-minute momentum as a filter), commodity / EU / Asia intraday; synthesis
  `knowledge/topics/cost-wall.md`; pre-sample 2008-2014 data plan
  (`knowledge/research/reports/2026-11-09_presample_2008_2014_plan.md`, needs the user's go).
- **Live spreads** (the user's request, Sonnet sub-agent): `results/fill_report_2026-11-09/`
  (7,019 fills of runs 3+4, 23 symbols, about 4.6 days): FX medians match the model; means 1.4-2x
  from Asia / rollover bars (NY hour 18 about 5x). Under-charged spread: GBPJPY 2.25x, GBPUSD
  1.97x, NAS100 1.95x, UK100 1.77x, GER40 1.52x; slippage under-charged only on BTCUSD (5x).
  Proposal only, `data/spreads/proposal_live_2026-11-09.json` (not wired in). For this run: the
  F1a EURUSD lead is not flattered by the cost model (EURUSD spread median 0, slippage 0.81x of
  the model); UK100 / NAS100 / GER40 were under-charged, so F2's net results are if anything
  too kind.
- **Data finding:** US500 histdata 2015-2021 omits many quiet minutes (2017 worst); the strict
  integrity gate over-flags; holiday / early-close days exit after the rollover (spec › Results).
- **Process:** the runner's matched monkeys took 30+ minutes per family; the grids now switch
  monkeys / sensitivity / entry screen off (diagnostics only). US30 dropped (cache from 2019-02).
- Models: Opus (coordination, spec, review, gates edits); Sonnet sub-agents x15 (literature x6,
  cost table, triage, calendars, implementation, gates tool, paper check, skeptic review, data
  gaps, live-spread measurement). No Codex / Gemini.

## 2026-11-09: research back in this team

- The user folded the research department back into V2 and asked for everything not needed to be
  archived. Department + shared interface in `../archive/research-department-2026-11/` (its last
  session state, `ACTIVE` since 2026-11-06, frozen as is); 21 research records, 75 reports and the
  registries copied to `knowledge/research/`; 20 unbuilt drafts to `research/candidates/`
  (R014 v0.1.0 dropped as superseded). Intake tool removed (`../archive/v2-intake-tool/`).
- Unanswered at the merge (now moot): the 17 R007-R024 compatibility preflights, the fast-lane
  bulk question, the reviewability proposal. The fast-lane idea (one shared harness for the M15
  batches) stays worth considering when the first candidate is built.
- `Continue.Research` rewritten (skill `continue-research`): candidate or researched idea ->
  spec with pre-registered gates -> build -> development run -> gates -> record. Opus inline,
  no dispatch.

## 2026-11-06: R014 development run and gates

- `results/research/alternating_path_1ffe705d` (2015-01-02..2021-09-13, 6 FX pairs, `--dev-only`,
  test period untouched). Net R: FOLLOW/30 -3,925 (17,673 trades), FOLLOW/60 -3,866 (16,626),
  FADE/30 -2,882 (15,160), FADE/60 -2,585 (14,042). Gross: FOLLOW -162 / -308, FADE +317 / +389
  (about +0.025 R per trade, costs about 0.2 R per trade at a 1-ATR M15 stop).
- Gates (`tools/alternating_path_gates.py`, `gates.json`): both modes fail every gate except the
  300-trade minimum; no symbol positive in any half; bootstrap lower bounds about -1.7 to -2.5 R
  per day; 111-170 trades per cell touch a missing / invalid M1 candle.
- Envelope `Shared_Interface/feedback/results/M15_ALTERNATING_PATH_BATCH__v0.2.0__DEVELOPMENT__1.json`
  (status COMPLETED). Gates tool by Opus inline (no dispatch); no one-time test.
- **Rejected by the user 2026-11-06**: moved to `queue/rejected/`; Research told the decision and
  the gate readings (`ASSUMPTION_MADE`, see `docs/strategy-alternating-path.md` › Gates).

## 2026-11-05: M15_ALTERNATING_PATH_BATCH v0.2.0 (R014) implemented as strategy 9

- Validated and claimed (sha256 `d09d44b9...`), status IMPLEMENTING; five `ASSUMPTION_MADE`
  points sent (M15 buckets, ATR seed, data-integrity handling, R-only sizing, gates after the
  run); spec `docs/strategy-alternating-path.md` › Assumptions. Brief
  `briefs/r014-alternating-path.md`.
- Codex gpt-6.1-sol medium, 1 call: config, strategy, 75 tests, spec, 4-cell grid. Opus: runner
  config union, panel (fixed fields hidden, widget limit), tool symbol tables, golden list
  (2,511 trades, 2023). Full suite 5,225 passed; golden 9/9 identical.
- Not done: the development run of the 4 cells and the submission's gates (UTC halves,
  doubled cost components, five-best-date removal, block bootstrap, M1 data-integrity count);
  no envelope yet. Research's 17 R007-R023 preflights and the fast-lane bulk question are
  unanswered.

## 2026-11-02: finalization audit and V2.8 R1

Opus (Claude Code, high effort) did the read-only audit (`docs/review/finalization-audit-2026-11-02.md`)
and R1 itself (`live/` is Opus-only; 3 tests, about 25 lines). T1 (a test fixture) by Opus.
U1 by Codex gpt-6.1-terra medium (`briefs/v28-u1-trade-pager.md`): first call hit the usage
limit (reset 21:36, the user chose to wait), second call done in ~5 min, inside the brief's
files, tests green on Opus's run; no fix round.

Night run 2026-11-02/03 (V2.8 step 3): V2.4b, 12.5, V2.6l, V2.4e each by Codex gpt-6.1-terra
medium in one call (V2.4b first went to gpt-6.1-sol, "model at capacity" after one partial test
file, then terra per the routing's same-cost rule); Opus checked each by running the tests and
comparing with recorded numbers; one Opus fix round on 12.5 (direction check, stop tolerance).
Feedback to Research 2026-11-03: `FB_INTRADAY_H1_SHOCK_RESPONSE_20261102T232536Z_ca99` (no
authoritative CFD session calendar, so the R004 integrity predicate is unsupported for all five
symbols; `robustness.r004` deferred until R004 is queued; V2.6l cell manifest available) and
`FB_UNKNOWN_20261102T232536Z_1ebf` (reviewability proposal received, review after V2.8).
2026-11-03 morning: stop inside the spread refused (the user's answer to night question 1) by
Opus inline (about 10 lines + 6 tests; routing: small edit); golden no_wick re-written (31 sells
fewer), the other 8 identical. Calendar rule 3 (1-hour shift, the user's answer to night
question 2) by Opus inline (about 30 lines + 9 tests; routing: small edit).

## 2026-10-28: first research pilot FX_LONDON_FIX_REV v1.0.0 (V2.6i i8)

Claimed 13:25 UTC, strategy 8 `london_fix` (Codex gpt-6.1-sol medium, Opus review), 9 variants
on development data 2015 - 2021-09-13, six USD pairs, 10,397 trades each. **All 9 negative**
(best v0007 stop 5 ATR / 180 min: -1,043 R, -0.10 R per trade). Pooled gross +181 R, 4 of 6
pairs with the predicted gross sign: the postfix drift exists, costs (~1,220 R) eat it, as
the source paper says for liquidity demanders. Criteria (`results/intake/<stem>/criteria.json`):
1 met, 2 not met, 3-5 met, 6 not run (monkeys skipped by the user: > 5.5 h CPU, cannot change
the outcome). Result envelope `FX_LONDON_FIX_REV__v1.0.0__DEVELOPMENT__1` sent; the user decides
pass / fail; no holdout. **Rejected by the user 2026-10-29** (moved to `queue/rejected/`, bytes unchanged, REJECTED message `FB_FX_LONDON_FIX_REV_20261029T170636Z_097b`). Research confirmed 3 assumptions within minutes; the swap / 23:55
assumption is open. Codex models: gpt-6.1-sol (pilot), gpt-6.1-sol (V2.4c checks; terra would
have done).

## Model usage, night 2026-10-27/28

| Tool / model | Effort | Calls | Minutes | Used for | Worth it? |
|---|---|---|---|---|---|
| Codex gpt-6.1-sol | medium | 4 | ~40 | V2.6i steps 1-3 (intake validator / claim, submission metadata + test gate, envelopes + end-to-end) and a ponytail cleanup | yes; all four green on the first try, no stop; Opus review found 4 real issues (results-folder leak in ordering, crash-remnant duplicate, schema-message crash, test-period evidence in development envelopes) |
| Opus (this app) | medium | - | - | news calendar wiring, FTMO restricted-news scope, deals export, fill analysis, reviews | small glue cheaper than a brief; Claude 4.6 (agy) quota still empty |

## 2026-10-27: research department split

From now on this log records only the backtester side (experiments, intake, model usage).
Research findings, sources and hypotheses live in `../Research_Department/knowledge_base/`.
Reviewed their contract 0.1.0 (`docs/review/research-interface-review-2026-10-27.md`, Opus
medium, no code changed); both pilot drafts are not runnable in V2 today (stopless /
notional, adjusted ETF data). Intake = ROADMAP V2.6i.

## Model usage, V2.1-V2.4 (2026-10-22 / 23)

| Tool / model | Effort | Calls | Minutes | Used for | Worth it? |
|---|---|---|---|---|---|
| Codex gpt-6.1-sol | high | 16 | 165 | module reviews (8), A1, B-risk, B-engine, B-strategy, speed 1-2 | yes: found 84 real issues with evidence; implementations needed few corrections |
| Codex gpt-6.1-sol | medium | 9 | 44 | inventory, dedupe, golden tool, A2/A3 finish, A4/A5 | yes for well-specified batches |
| Gemini 3.8 Flash | high | 4 | 25 | two reviews (good), one write task (quota ran out half-way) | reviews yes; bulk writing burns the weekly quota |
| Claude Opus 4.6 (agy) | high | 3 | 4 | one review | the 4 subagents it started emptied the weekly quota |
| Claude subagents (this app) | Opus high / Sonnet medium | 2 | - | live-bot fixes (19 findings, 45 tests), UI proposal draft | yes; live code is Opus-only |

| Codex gpt-6.1-sol | medium | 3 | 50 | grid merge 1-3 (2026-10-23) | yes: exact reproduction; Opus fixed a slow shock-day read (31 s -> 2 s), a misleading haircut on losses, legacy test fixtures |
| Claude subagent (this app) | Sonnet | 1 | 4 | merge of the Pardo / Masters / Aronson notes into knowledge/topics | yes for knowledge merges |
| Opus (this app) | medium | - | - | V2.4a trades overlay for every strategy, backtest audit, book-claim check | small UI change cheaper than a brief |
| Codex gpt-6.1-sol | medium / high | 11 | ~330 | V2.4d 1-5, V2.4c T-10 / T-14 / T-03 (2026-10-23 evening); 5 short stops with a rule question, all good questions | yes; hit the limit at 21:10 after ~5 h of work since the morning reset, the last task (T-03) was already complete |

| Codex gpt-6.1-sol | medium | 3 | 23 | V2.6a job queue: read-only pass by mistake (found 6 shared-file collisions), build, fix round (2026-10-26) | yes; Sonnet subagent review found 5 real defects (one Windows replace race, reproduced by Opus); Haiku subagent pinned 14 tests for the new defaults |

| Codex gpt-6.1-sol | medium | 2 | 43 | V2.6b data fixes + server-clock revision (2026-10-26) | yes; Sonnet subagents: wrong-instrument table, sparse-day fix; the continuity check found DXY = Dow Jones and EU50 = IBEX in histdata; Opus caught the holiday-day drop via the golden check |

| Codex gpt-6.1-sol | medium | 2 | 21 | V2.7 portfolio page + fix round (2026-10-26) | yes; Sonnet subagents built V2.6 step 3 while Codex was at its limit (18:14-21:14) and reviewed V2.7 (no blocking defect) |

| Codex gpt-6.1-sol | medium | 9 | ~120 | night 2026-10-26/27: step 5 (+2 fix rounds, 4.3 items), V2.4e news (2 rounds), full check review + fixes | yes; the full-check review found 6 real defects (one review no-peek leak); its 'violation' flag came from Opus editing files during the read-only review, not from Codex. Codex failed twice on the chart stats strip (wrong brief by Opus), Opus fixed it |

Limits seen: Codex hit its limit twice (about 20:50 and 04:25; reset after ~4.5 h);
Antigravity (Gemini + Claude 4.6, one shared weekly quota) is empty until about 2026-10-29.

## Strategy profiles, development period, spec defaults (2026-10-25)

`python -m backtester.tools.strategy_profile --strategy <name>` for all 7 strategies (current
defaults incl. TP penetration 0.5 + ask, intrabar M1), results in `results/profiles/`. Best cells
by **detrended** R per trade (>= 30 trades); "lower90" = BCa 90 % lower bound. These are
descriptive cells picked after the fact, **not** a significance test (many cells were looked at).

| Strategy | Trades | Net R | Best cells (detrended R/trade, lower90) |
|---|---|---|---|
| 1 Session zones | 20,167 | -4,556 | London session -0.12 (-0.14); everything negative |
| 2 NY index sweep | 1,381 | -328 | sideways / high vol -0.08 (-0.17); all negative |
| 3 No-wick | 42,448 | -11,498 | London -0.18 (-0.19); all negative |
| 4 Trend following | 1,027 | -182 | **GBPJPY +0.16 (+0.02, 200 trades, the only positive lower bound)**; sideways / low vol raw +14.9 R but detrended -0.03 |
| 5 Gap fade | 2,420 | -83 | sideways / low vol +0.05 (-0.01, 406 trades); trend_up / low +0.02 |
| 6 Opening range | 3,318 | -199 | trend_up / low -0.01; sideways / high -0.01: near zero, no edge |
| 7 Gap momentum | 975 | -12 | sideways / high vol +0.03 (-0.01, 285 trades) |

Reading (Opus): no strategy has a robust edge in any condition. Candidates worth a researched
follow-up, not a conclusion: strategy 4 on GBPJPY (the only positive lower bound; check it as a
pre-registered hypothesis on the MT5 test period, it was found by looking at 30+ cells), and the
quiet sideways regime for the two gap strategies (5 and 7 both best there, in line with mean
reversion working in noise, Kaufman). For combining (V2.7): 4 trend-following and 5 / 7 gap
strategies prefer opposite regimes, which is the kind of pair the portfolio looks for.

## Research runs

(none yet; V2.6 starts after the regime classifier spec is accepted)
