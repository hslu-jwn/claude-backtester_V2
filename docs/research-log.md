# Research log

Running log of the research loop (V2.6 / V2.7) and of the model / effort used per task, so a
run resumes after a restart or a usage limit. Newest first. Every AI call is also logged by
the dispatcher in `results/ai_calls.jsonl` (model, effort, seconds, status).

## 2026-10-28: first research pilot FX_LONDON_FIX_REV v1.0.0 (V2.6i i8)

Claimed 13:25 UTC, strategy 8 `london_fix` (Codex gpt-6.1-sol medium, Opus review), 9 variants
on development data 2015 - 2021-09-13, six USD pairs, 10,397 trades each. **All 9 negative**
(best v0007 stop 5 ATR / 180 min: -1,043 R, -0.10 R per trade). Pooled gross +181 R, 4 of 6
pairs with the predicted gross sign: the postfix drift exists, costs (~1,220 R) eat it, as
the source paper says for liquidity demanders. Criteria (`results/intake/<stem>/criteria.json`):
1 met, 2 not met, 3-5 met, 6 not run (monkeys skipped by the user: > 5.5 h CPU, cannot change
the outcome). Result envelope `FX_LONDON_FIX_REV__v1.0.0__DEVELOPMENT__1` sent; the user decides
pass / fail; no holdout. Research confirmed 3 assumptions within minutes; the swap / 23:55
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
