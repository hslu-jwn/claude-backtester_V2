# CLAUDE.md

Guidance for Claude Code. The project rules shared by all models are in `AGENTS.md`; they apply
in full:

@AGENTS.md

## Claude Code tools in this project

The project skills are in `.claude/skills/`:
`ponytail`, `ponytail-review`, `ponytail-audit`, `backtester-testing`, `backtest-evaluation-research` (needs web
access; the user may supply the research). They help; they never override the rules above.
graphify is no longer used (user, 2026-10-22).

### ponytail

- **ponytail** (`/ponytail`) keeps changes small, but these rules win when they conflict:
  every tunable value still goes in a config dataclass with the spec default (no magic
  numbers), every detector still gets its no-lookahead test, and bullish/bearish stays one
  code path.
- **Before each commit:** run `/ponytail-review` on the change and fix the "Must fix" items.
- **Occasionally:** `/ponytail-audit` (in `.claude/skills/` since the 2026-10-22 merge of main) for a whole-repo report. It only reports; turn its
  findings into ROADMAP steps rather than fixing them all at once.

## Status (2026-10-21, end of session 2)

| Part | Status |
|---|---|
| Data (histdata.com, 5 symbols, 2018/2020-2026), chart, replay, overlays, settings, presets, results page | built, checked by the user |
| Strategy 1 (session zone sweep) | built, **paused** by the user; full run 2020-2026 negative (ROADMAP 6.3) |
| Strategy 2 (NY Open index sweep) | built, **parked** by the user 2026-10-15; 2020-26 −135 R net with FTMO swap (+29 gross); trend filter, close at 16:15 ET and cost filter (all off by default) improve it to −17 R at best, inside the noise (ROADMAP 8.2.5, 10.5) |
| Strategy 3 (no-wick candle in the trend) | built 2026-10-13; all 24 variants (5m-1h, higher / same trend, close / body_end / middle) negative gross and net 2020-26 (ROADMAP 9.1); dropped by the user |
| Liquidity sweep rules | reworked with the user 2026-10-12/13: options built (tolerance, 2/3 closes, wick+close, BoS before top, doji share), off by default, temporary Sweep menu on the chart; no rule adopted (study: no rule changes sweep quality); do not change defaults without his go |
| Strategy 4 (trend following, Kaufman) | built 2026-10-14 (ROADMAP 10); with FTMO swap no variant is robust; **parked**; its SMA-band cross is strategy 2's optional trend filter (`SmaBandCross`) |
| Costs | swap in the engine (17:00 New York rollover, triple day, net R only); **FTMO rates of 2026-10-14 are the defaults** (user, 2026-10-14); cost filter `CostConfig.max_cost_r` (spread + commission in R of the stop, off by default) |
| Knowledge base + research tools (2026-10-14/15) | `knowledge/` from 6 books (topics, 45 ideas, trigger `Continue.Knowledge`); robustness report 6.4, time splits 6.5, MT5 history 6.6, spread table 6.7 (off by default), noise study 11.1, open / gap study 11.2 built and accepted 2026-10-15; no edge found yet; one candidate: gap fade of 0.1-1 ATR gaps (I-39 / ROADMAP 11.4) |
| Strategy 5 (gap fade, 2026-10-15) | built; 2020-26 weak positive, failed out of sample (2018-19 negative) and walk-forward: **no edge** (ROADMAP 11.4-11.7) |
| Strategy 6 (opening-range breakout, 2026-10-15/16) | built; price-only no edge; with tick-volume filter on US indices +30 R out of sample 2021-09..2026 (+0.10 R/trade) but fading since 2024; **demo forward test candidate** (ROADMAP 11.10, 7.2) |
| Data 2026-10-16 | 26 FTMO symbols in `data/cache/mt5/` (FX / metals from 2010), histdata 2015-2021 for 21 symbols, Binance BTC / ETH futures 1m + order flow + funding from 2020; data split cut-off 2021-09-14; spread scaled with price; FTMO % fees, Binance fees + funding |
| Live (Phase 7, 2026-10-21) | demo forward test of strategy 6 on the FTMO demo; first trade 2026-10-21 US500 short, SL -1.0 R; bot stopped by the user 18:49 CH (restart from the Live page); safety fixes 13.1-13.5 + 13.4b; 7.8: bot writes its symbols' bars (finished days -> MT5 cache, today -> `data/cache/live/`, chart only), starts the cache update at start, "Bot trades" chart overlay; next: 13.6-13.8 |
| Research tooling (2026-10-21) | one runner for every strategy: `python -m backtester.tools.research research/grids/<name>.toml` (spec `docs/research-runner.md`: develop before 2021-09-14, best variant tested once on MT5 data, scorecard + flags, trial log); Research page `/research`; ~6x faster (candles loaded once per worker); contract tests for every registered strategy; old per-strategy grid tools in `tools/archive/` |
| Risk / FTMO (Phase 5) | sizer and daily guard (7.2); Monte Carlo report (12.7) + "Full Monte Carlo" button; prop-firm card on every results page (5.6, FTMO 2-Step, fixed vs adaptive); adaptive risk (5.7) built and swept, **parked** until a strategy has a good edge |
| Strategy Simulator (6.1) | planned, before any MT5/prop-firm work (Phase 7) |
| MT5 | connection, download, demo test orders run on the FTMO demo 2026-10-17; **MT5 data preferred day by day** over histdata for backtests, tools and the chart (user, 2026-10-19) |

## Working agreement with the user

- Address the user as "Chef", answer in English, short and concrete; explain a new concept in
  one line. Ask all open questions together, numbered. Never assume; on any doubt or conflict
  (also for CLAUDE.md, code, tests, config) ask before changing anything.
- Small commits on the session's feature branch; no PR unless asked.
- **Models and subagents (rule set by the user, 2026-10-22; roles in `AGENTS.md` › Team):**
  Opus orchestrates and dispatches Codex, Claude 4.6 and Gemini through the project skills
  `codex-helper` and `gemini-helper` (`python -m backtester.tools.ai_dispatch
  codex|claude46|gemini`). Before asking the user
  anything, ask Codex. Pick the cheapest model and lowest effort that does the task well;
  escalate one level after a failed try:

  | Task | Model / effort |
  |---|---|
  | Orchestrating, check-ins, merges, routine checks | Opus medium |
  | Code review (phase 4), specs, strategy design, regime classifier, hard bugs, anything touching no-lookahead / engine / risk | Opus high + Codex high |
  | Normal coding (all production code), specs, test-case lists | Codex medium |
  | Review of Codex's code; second coding lane; first escalation step | Claude 4.6: `claude46` medium = Sonnet 4.6, high = Opus 4.6 |
  | Writing tests from a test-case list, running tests | Gemini high (`gemini-3.8-flash-high`) |
  | Reading literature, web research, summaries, card write-ups | Gemini medium (high for hard papers / books) |
  | Claude subagents: mechanical edits, searches, running commands | Haiku, low effort |
  | Claude subagents: writing code / tests, debugging, backtests needing judgment | Sonnet, medium (high for hard bugs) |
  | Claude subagents: only if Sonnet failed or the task is critical | Opus, high |

  Antigravity offers no Gemini Pro model on this account (2026-10-22; `agy models`); Flash high
  stands in for "Pro". Claude 4.6 and Gemini share the Google quota. Opus's own
  level is set by the user in the app: tell the user when a phase would clearly benefit from high.
  **Usage limits:** dispatch exit 4 = limit hit; the other tools take over its tasks; if two
  are out, pause the loop and resume later. Save Claude and Codex tokens: short high-value
  steps; Gemini and plain Python do the bulk. Record model and effort per task in
  `docs/research-log.md` (the dispatcher also logs them in `results/ai_calls.jsonl`).
  Claude subagents get a complete brief (files, spec section, test cases, done = tests green +
  ruff). Trivial edits and git commands stay in the main session.
- **Where to work:** the cloud has no market data (git-ignored) and no browser view of the
  app, so backtests and chart checks happen locally; docs and test-only work can run in the cloud.
- **New strategies** must be one new folder under `strategy/` (copy `strategy/_template/`, its README has the steps)
  plus one entry in `strategy/registry.py` (ROADMAP C.3); strategy-specific settings live in
  its config; swings / FVG / OB / equilibrium (`RunSettings.detectors`), costs and warm-up
  are shared.

## Session protocol (user does no file work)

- **Start** (user says "Continue." or names a task): `git pull`, read `docs/HANDOFF.md`, this file and
  the ROADMAP entry of the task, run the tests as a baseline, then say in max 10 lines what you will do
  (plan, test cases, files, models) and ask all open questions at once. Then work test-first.
- **Start, research mode** (user writes `Continue.Knowledge`): continue the research from the
  knowledge base to find a tradeable edge; separate from `Continue.` (which follows the strategy
  work's next step in `docs/HANDOFF.md`).
  - First: `git pull`, read `docs/HANDOFF.md` (knowledge-base chat section and its Open list),
    `knowledge/README.md`, `knowledge/ideas.md` (status column), `knowledge/topics/testing-and-robustness.md`
    (checklist) and the ROADMAP entries of 6.4-6.7 and Phase 11; run the tests as a baseline.
  - Then say in max 10 lines which idea / study comes next and why (best open candidate by evidence:
    an idea that already survived a study beats a new one), test cases, files, models; ask all open
    questions together, numbered.
  - Rules: one idea at a time; test first; the idea's rule goes into a `docs/` spec before any strategy
    code; every test with the robustness report (halves 2020-22 / 2023-26, share of profitable variants,
    stressed costs, best trade removed) and the real cost model (spread table from `tools/spread_table.py`
    where available, swap); report "no edge" honestly and record it in `knowledge/ideas.md` and the
    ROADMAP; never change defaults (costs, sweep options, spread table) without the user's go; prefer
    no overnight holds (swap).
  - Data split (rule set by the user, 2026-10-15): histdata years are the sample (development) years;
    the real test runs on the period FTMO's MT5 history records (`data/cache/mt5/`, ROADMAP 11.5).
    One cut-off for all symbols: **2021-09-14** (first M1 day of FTMO's indices; user confirmed 2026-10-15):
    develop on data before it, test each idea once on MT5 data from it on. 2021-26 was already used by
    the studies and strategies 1-5, so it is fresh only for new ideas.
  - Models: as in Working agreement › Models and subagents (Opus plans, subagents code / test /
    read with Sonnet or Haiku). New books: follow the process in `knowledge/README.md`.
  - End: same End protocol as below, plus update the idea statuses in `knowledge/ideas.md`.
- **During:** when the user says ok / fine / yes, it is final: write it into the repo in the same
  commit (rule -> `docs/` with "(rule set by the user, <date>)"; accepted issue -> ROADMAP line
  "accepted by the user <date>"; postponed/declined -> likewise). Never ask about it again.
- **End** (user says "End." / "Finish." / ends the chat): the user accepts everything done so far.
  Do all of it yourself: full tests + ruff (report failures honestly, record them as known issues),
  mark the finished steps ☑ in the ROADMAP, write all decisions and accepted points into `docs/`,
  rewrite `docs/HANDOFF.md` (last session, accepted, open, next step), commit, push, make sure
  `git status` is clean. In the cloud, unpushed work is lost.
- **Reply at the end** (max 10 lines): done, not done, recorded decisions, next step, how to check,
  and the exact first prompt for the next chat (normally just `Continue.`).
