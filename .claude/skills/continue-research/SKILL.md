---
name: continue-research
description: Procedure for the user's Continue.Research command - the autonomous research loop (pick or research a strategy idea, spec with pre-registered gates, implement, development run, gates, record; one-time MT5 test per Test=manual (default) / Test=auto). Load when the user says Continue.Research.
---

# Continue.Research (research back in this team since 2026-11-09, the user)

`Continue.Research [Limit=<time>] [<CANDIDATE or idea ID>]` runs the whole research loop in this
repo. The former research department (2026-10-27 to 2026-11-06) is archived; its records are in
`knowledge/research/`, its unbuilt drafts in `research/candidates/`. There is no queue, no JSON
envelope and no feedback file any more: decisions go into the spec and `docs/research-log.md`.

## Start

- Read `docs/HANDOFF.md`, the last entry of `docs/research-log.md`, `research/candidates/README.md`,
  the top of `knowledge/ideas.md` and `knowledge/topics/cost-wall.md` (what every test so far says
  about gross edge vs costs; read it before proposing anything).
- First call in a chat: ask ALL open questions at once, numbered (limit, topic, anything unclear)
  and wait. Then run autonomously (Telegram only for urgent items, CLAUDE.md). Later calls in the
  same chat reuse the answers.
- `Limit=60min` / `2h` / `3d`: write start time and deadline into `docs/research-log.md`, check the
  clock after every step; at the deadline finish the current step cleanly (commit, log) and stop.
  No limit = until `Stop.` or the resources run out.

## Pick the work

1. ID given: only that candidate / idea.
2. Otherwise the highest-priority open candidate in `research/candidates/README.md` that V2 can
   run (blocked / parked rows skipped).
3. No runnable candidate: research a new idea (below). Never fill time with an unfounded idea.

## Research a new idea (when needed)

- Day trading first (open and close the same session, the user); V2's M1 symbols and supported
  execution only; stop-defined, results in R.
- Cheapest route first (`docs/agent-routing.md`): local search of `knowledge/`, then a free model
  for literature / web look-ups (`ai_dispatch gemini --effort low`, `gemini-api`, `openrouter`).
  A model's citation is only a lead: Opus opens the source before relying on it.
- Write a card in `knowledge/ideas.md`: mechanism, falsifiable prediction, sources actually read,
  label (PUBLISHED finding / ADAPTATION / ORIGINAL / SPECULATIVE), expected gross edge per trade.
- **Cost pre-check:** estimate gross R per trade against our costs at that stop size (R014: about
  0.2 R per trade at a 1-ATR M15 stop). An idea whose plausible gross edge is far below the cost
  stays a card; do not build it.
- **Skeptic pass** (Opus itself, or one free model on a brief): leakage, selection bias, costs,
  sample size, multiple testing, alternative explanations. Record the answers on the card.

## Build and run

- Spec `docs/strategy-<name>.md` before any code: rules (quoted from the candidate JSON when there
  is one), an "Assumptions" section for every point Opus decided, the grid in
  `research/grids/<name>.toml` with every cell counted, and the **rejection criteria fixed before
  the run** (gates: costs doubled, halves, symbol breadth, best-date removal, bootstrap lower bound,
  minimum trades, data integrity; see `docs/strategy-alternating-path.md` › Gates and
  `tools/alternating_path_gates.py` as the pattern). Specs need no user approval in the loop.
- Implement: new strategy folder via Codex `gpt-6.1-sol` medium on a brief
  (`briefs/<name>.md`); registry, panel, golden lists and tool tables by Opus; full suite green.
- Vary only the parameters the spec marks tunable, within its ranges; one parameter set pooled
  across markets (rule set by the user, 2026-10-23). Development only:
  `python -m backtester.tools.research research/grids/<name>.toml --dev-only` (before 2021-09-14).
- Compute the gates on the development run. Do not judge pass / fail: report every cell with all
  metrics and the gates; the user decides. Failed and rejected strategies stay recorded.
- **One-time MT5 test mode (rule set by the user, 2026-11-09):** default `Test=manual`: a
  candidate that passes all pre-registered development gates is parked in HANDOFF › Open as
  "ready for the one-time test" and the loop moves on. `Test=auto`, given with the command (e.g.
  `Continue.Research Test=auto`): the loop runs the one-time test itself, only for a candidate that
  passed every pre-registered development gate. Both modes: exactly once per candidate, no retest
  after a fail, the variant is frozen before the test, pass or fail recorded in the research log
  and HANDOFF. Auto lasts for that run only; the next session is manual unless the user says
  `Test=auto` again. Never change defaults (costs, sweep options, spread table) without the
  user's go.

## Record

- `docs/research-log.md`: what was tested, cells, net / gross R, gates, model and effort per task.
- Candidate row / idea card status (built, rejected by the user <date>, ...); `docs/HANDOFF.md`.
- Count families, specs and cells honestly; a parameter cell is not a new hypothesis, and a failed
  family is not re-proposed under a new name.
- End of run: short report (tested, results, gates, decisions needed); a very promising strategy
  first, and on Telegram (format and command: CLAUDE.md › Telegram), sent as soon as it passes
  its gates, not only at the end of the run.
