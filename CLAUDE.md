# CLAUDE.md

Guidance for Claude Code (Opus, the orchestrator). The project rules shared by all models are
in `AGENTS.md`; they apply in full:

@AGENTS.md

## Status (V2, 2026-10-22)

| Part | Status |
|---|---|
| Strategies | 7 built. 1 session zone sweep: paused (negative). 2 NY index sweep: parked. 3 no-wick: dropped. 4 Kaufman trend following: parked, but **portfolio candidate** (passed a prop-firm challenge in some tests, slowly). 5 gap fade: no edge. 6 opening-range breakout: demo forward-test candidate (tick-volume filter, fading since 2024). 7 gap momentum: no edge (gold version positive, not significant). |
| Research | runner `tools/research.py` (data split 2021-09-14, one MT5 test of the best variant, DSR, flags, trial log), Research page, entry screening, Monte Carlo, portfolio tool; price-only research found no significant edge so far |
| Costs | FTMO spreads / fees / swap of 2026-10-14 are the defaults; spread table off by default |
| Data | MT5 cache 26 symbols to 2026-10-19 (preferred day by day), histdata 2015-2021, Binance BTC / ETH |
| Live | demo forward test of strategy 6 on the FTMO demo; bot **not running** (stopped 2026-10-21) |
| V2 | V2.1-V2.3 done; V2.4 review + speed-up done except the grid-tool merge (`docs/review/`); next V2.4b slippage from demo fills, V2.5 redesign, V2.6 research (`docs/ROADMAP.md`) |

Details per step: `docs/ROADMAP.md` and its archive `docs/archive/ROADMAP-v1.md`.

## Working agreement with the user

- Address the user as "Chef", answer in English, short and concrete; explain a new concept in
  one line. Ask all open questions together, numbered. Never assume; on any doubt or conflict
  (also CLAUDE.md, code, tests, config) ask first, after asking Codex.
- Small commits on a feature branch, push regularly; no PR unless asked.
- **Models (rule set by the user, 2026-10-22; roles in `AGENTS.md` › Team):** Opus dispatches
  Codex, Claude 4.6 and Gemini with the skills `codex-helper` / `gemini-helper`
  (`python -m backtester.tools.ai_dispatch codex|claude46|gemini`) and checks every result
  itself (diff + tests). Cheapest model and lowest effort that does the task well; one level
  up after a failed try:

  | Task | Model / effort |
  |---|---|
  | Orchestrating, check-ins, merges, routine checks | Opus medium |
  | Phase 4 review, specs, strategy design, regime classifier, hard bugs, no-lookahead / engine / risk | Opus high + Codex high |
  | All production code, specs, test-case lists | Codex medium |
  | Review of Codex's code; second coding lane | Claude 4.6 (`claude46` medium = Sonnet, high = Opus 4.6) |
  | Writing tests from a test-case list, running tests | Gemini high |
  | Literature, web research, summaries, card write-ups | Gemini medium (high for hard papers / books) |
  | Claude subagents: mechanical edits, searches, commands | Haiku, low |
  | Claude subagents: code / tests, debugging, backtests needing judgment | Sonnet, medium (high for hard bugs) |
  | Claude subagents: only if Sonnet failed or critical | Opus, high |

  - Gemini = 3.8 Flash (no Pro model on this account; `agy models`). Claude 4.6 has a small
    **weekly** quota (Opus 4.6 ran out after one review with subagents on 2026-10-22): use it
    for short reviews; models work alone (no subagents).
  - **Plans (the user, 2026-10-23): ChatGPT Plus and Google AI (Gemini) Plus, nothing more.**
    Work is placed by the limits seen (`docs/research-log.md` › Model usage): Codex Plus
    lasts ~2 h of high effort per ~5 h window -> Codex medium by default, high only for
    engine / no-lookahead / risk, one brief at a time, the brief small and exact. Antigravity
    (Gemini + Claude 4.6) is one small weekly quota -> only short reviews or one research
    summary per week, never bulk writing. Small UI / glue changes (well under an hour of
    Codex): Opus writes them directly (a brief + review costs more than the change). Bulk =
    plain Python (job queue, sweeps), no AI tokens.
  - **Usage limits:** dispatch exit 4 = limit; the others take over; two out -> pause the loop
    and resume later. Save Claude and Codex tokens; plain Python does the bulk.
  - Record model and effort per task in `docs/research-log.md` (the dispatcher logs every call
    in `results/ai_calls.jsonl`). Tell the user when a phase would clearly benefit from Opus high.
  - Shell gotcha: never put backticks in inline PowerShell (they are escape characters); edit
    files with the Edit tool or a script file.
- **Where to work:** locally (data and app are here); the cloud has no market data.
- **New strategies:** one folder under `strategy/` (copy `strategy/_template/`) plus one entry
  in `strategy/registry.py`; strategy settings in its config; detectors, costs and warm-up shared.
- **Skills:** `ponytail` (small changes; the rules above win), `/ponytail-review` before each
  commit, `/ponytail-audit` occasionally (findings -> ROADMAP), `backtester-testing`,
  `backtest-evaluation-research`.

## Session protocol (the user does no file work)

- **`Continue.Code`:** work on the application: the V2 phases in `docs/ROADMAP.md`, then
  app / engine improvements from `docs/HANDOFF.md` and the ROADMAP. `git pull`, read
  `docs/HANDOFF.md` and the ROADMAP step, run tests + ruff as a baseline, say in max 10 lines
  what you will do (plan, test cases, files, models), ask all open questions at once, then work
  test-first, step by step with the user's ok.
- **`Continue.Knowledge`:** gather knowledge only, no strategy code. Gemini reads literature,
  websites and studies; results go into `knowledge/` (topics, `ideas.md` with sources and
  status; new books: `knowledge/README.md`).
- **`Continue.Research [Limit=<time>] [<topic>]`:** the autonomous research loop (V2.6 / V2.7;
  the job queue, lanes and research log are built in V2.6).
  - First call in a chat: ask ALL open questions at once, numbered (limit, topic, anything
    unclear in the log or specs) and wait. Then run autonomously (Codex answers questions;
    Telegram only for urgent ones). Later calls in the same chat reuse the answers.
  - `Limit=60min` / `2h` / `3d`: write start time and deadline into `docs/research-log.md`,
    check the clock after every step; at the deadline finish the current step cleanly
    (commit, log) and stop. No limit = until "Stop." or the resources run out.
  - Topic given: research only that. Otherwise the next open idea from
    `docs/research-log.md` / `knowledge/ideas.md`.
  - Rules: every strategy comes from research (book, paper, study) cited in its `docs/` spec;
    Opus checks the source exists before any code. One parameter set pooled across all
    markets by default; per-market parameters with re-optimisation only as a walk-forward
    variant of a promising strategy (rule set by the user, 2026-10-23). Vary only the settings of a researched
    idea. Do not judge pass / fail: record every strategy with all metrics; the user decides.
    Develop before 2021-09-14, test the best variant once on MT5 data from 2021-09-14 (rule set
    by the user, 2026-10-15); every variant in the trial log; DSR, robustness report, real
    costs + swap, Monte Carlo, parameter stability, regime breakdown, warning flags. Prefer no
    overnight holds (swap). Never change defaults (costs, sweep options, spread table) without
    the user's go.
  - End of run: short report (tested, results, research cards added); a very promising
    strategy first, and on Telegram.
- **`Stop.`:** end the current run within 1-2 minutes at a clean point: finish or roll back
  the step, stop lanes and job queue, commit, update the log, short report. Nothing
  half-finished stays uncommitted.
- **`End.`:** the user accepts everything done so far. Full tests + ruff (report failures
  honestly, record known issues), mark finished steps ☑ in the ROADMAP, write decisions into
  `docs/`, rewrite `docs/HANDOFF.md` (state, accepted, open, next step), commit, push, clean
  `git status`. Reply in max 10 lines: done, not done, decisions, next step, first prompt for
  the next chat.
- **During any session:** when the user says ok / yes, it is final: write it into the repo in
  the same commit (rule -> `docs/` "(rule set by the user, <date>)"; accepted -> ROADMAP
  "accepted by the user <date>"). Never ask about it again.
- **Telegram** (`live/telegram.py`, token from the Windows Credential Manager) only for: a
  decision on rules / defaults / risk, a blocker Codex can't solve, a crash or long pause of
  the loop / queue, a very promising strategy; plus one short evening summary while research
  runs.
