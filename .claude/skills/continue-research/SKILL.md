---
name: continue-research
description: Procedure for the user's Continue.Research command - the autonomous research loop (pick or research a strategy idea, spec with pre-registered gates, implement, development run, gates, record; Mode=manual (default) / Mode=auto: CLAUDE.md). Load when the user says Continue.Research.
---

# Continue.Research (research back in this team since 2026-11-09, the user)

`Continue.Research [Limit=<time>] [Mode=manual|auto] [<CANDIDATE or idea ID>]` runs the whole research loop in this
repo. The former research department (2026-10-27 to 2026-11-06) is archived; its records are in
`knowledge/research/`, its unbuilt drafts in `research/candidates/`. There is no queue, no JSON
envelope and no feedback file any more: decisions go into the spec and `docs/research-log.md`.

## Start

- Read `docs/HANDOFF.md`, the last entry of `docs/research-log.md`, `research/candidates/README.md`,
  the top of `knowledge/ideas.md` and `knowledge/topics/cost-wall.md` (what every test so far says
  about gross edge vs costs; read it before proposing anything).
- First call in a chat: ask ALL open questions at once, numbered (limit, topic, anything unclear);
  meanwhile start the work they do not block (never idle) and Telegram after 5 minutes of waiting
  (CLAUDE.md › Telegram). Then run autonomously; an unclear point is decided by Opus and recorded
  as an assumption (AGENTS.md › Specs, per mode). Later calls in the same chat reuse the answers.
- `Limit=60min` / `2h` / `3d`: write start time and deadline into `docs/research-log.md`, check the
  clock after every step; at the deadline finish the current step cleanly (commit, log) and stop.
  No limit = until `Stop.` or the resources run out.

## Pick the work

1. ID given: only that candidate / idea.
2. Otherwise the highest-priority open candidate in `research/candidates/README.md` that V2 can
   run (blocked / parked rows skipped).
3. No runnable candidate: research a new idea (below). Never fill time with an unfounded idea.
4. Nothing worth building: never idle or schedule quiet holds (the user, 2026-11-10). Propose the next
   steps (with a pick) or ask the user for direction, start the best real option (tooling the research
   needs, a new idea source), and Telegram the question if it waits more than 5 minutes.

## Research a new idea (when needed)

- Day trading and multi-day holds (multi-day in scope since 2026-11-09, the user: count every fee,
  overnight swap incl. the triple-swap day); V2's M1 symbols and supported
  execution only; stop-defined, results in R.
- **Idea sources (rule set by the user, 2026-11-10):** search broadly on the internet (forums,
  practitioner blogs, trading books, videos, papers); an idea need not be scientifically backed to be
  tested (label it SPECULATIVE / PRACTITIONER), but every test keeps the pre-registered gates. When the
  backlog is empty, look for new ideas online. Codex may do web research too (not overdone).
- Cheapest route first (`docs/agent-routing.md`): local search of `knowledge/`, then a free model
  for literature / web look-ups (`ai_dispatch gemini --effort low`, `gemini-api`, `openrouter`).
  A model's citation is only a lead: Opus opens the source before relying on it.
- **Filter by mechanism and size (review tips, the user 2026-11-11):** prefer a counterparty that
  must trade (rebalancing, hedging, settlement, index rules) and an effect stated in bp per event;
  halve a published effect before the cost check (post-publication decay). Every harvest or
  literature prompt starts with the "stop proposing" list of `knowledge/topics/cost-wall.md` §4.
- Write a card in `knowledge/ideas.md`: mechanism, falsifiable prediction, sources actually read,
  label (PUBLISHED finding / ADAPTATION / ORIGINAL / SPECULATIVE), expected gross edge per trade.
- **Screen first, before any spec or build (hard step, review A2, the user 2026-11-11):** a fixed
  clock window or a daily-bar rule gets a small pandas / `tools/time_of_day_profile.py` screen of
  gross bp per trade vs the cost from the cost table, on development data only; only survivors get a
  spec. Every screen is counted. Otherwise estimate gross R per trade against our costs at that stop
  size (R014: about 0.2 R per trade at a 1-ATR M15 stop); an idea far below the cost stays a card.
- **Required size:** before a build, check with the Monte Carlo / prop tools what edge per trade the
  FTMO goal needs at the expected trade count; an idea that cannot reach it is not built.
- **Skeptic pass** (Opus itself, or one free model on a brief): leakage, selection bias, costs,
  sample size, multiple testing, alternative explanations. Record the answers on the card.

## Build and run

- Spec `docs/strategy-<name>.md` before any code: rules (quoted from the candidate JSON when there
  is one), an "Assumptions" section for every point Opus decided, the grid in
  `research/grids/<name>.toml` with every cell counted, and the **rejection criteria fixed before
  the run** (gates: costs doubled, halves, symbol breadth, best-date removal, bootstrap lower bound,
  minimum trades, data integrity; see `docs/strategy-alternating-path.md` › Gates and
  `tools/alternating_path_gates.py` as the pattern). New strategies put their gates in a `[gates]` table of the grid
  and run `python -m backtester.tools.gates <research folder> [--controls 200]` (`docs/research-runner.md` ›
  Gates table); no new gates tool per strategy. Specs need no user approval in the loop.
- **Power line in every spec (review tip 1):** the minimum detectable edge at the planned sample
  (trade sd from a pilot or a similar family). If the one-time test is underpowered, pre-register a
  combined estimate (pre-sample + development + test) or a forward demo instead of a pass / fail gate.
- **Stop rules (review tip 5, the user 2026-11-11):** one Codex window per hypothesis; stop at the
  first failed gate; no rescue variants (a changed rule is a new, counted hypothesis); a family is
  closed after two falsifications; a lead expires after one failed independent check (closed, not
  parked).
- **Pipeline controls (review tip 2):** after any change to a gates tool, run a planted drift
  (positive control, must pass about as often as the power says) and shuffled days (negative
  control, at most 5 % passes) through it once (`tools/gates.py --controls N` does both on the control cells).
- Implement: new strategy folder via Codex `gpt-6.1-sol` medium on a brief
  (`briefs/<name>.md`); registry, panel, golden lists and tool tables by Opus; full suite green.
- Vary only the parameters the spec marks tunable, within its ranges; one parameter set pooled
  across markets (rule set by the user, 2026-10-23). Development only:
  `python -m backtester.tools.research research/grids/<name>.toml` (development only, before
  2021-09-14; the one-time test needs `--test`, review B2, 2026-11-11).
- Compute the gates on the development run and report every cell with all metrics. Pass / fail is
  read mechanically from the pre-registered gates (that is what `Mode=auto` acts on); anything beyond
  them (a retest, a rule change, a rescue) is the user's decision in `manual`, Opus's first pick in `auto`
  (recorded as an auto decision). Failed and rejected strategies stay
  recorded.
- **One-time MT5 test:** exactly once per candidate, no retest after a fail, the variant frozen before the
  test (runner `--test`), pass or fail recorded in the research log and HANDOFF. `Mode=manual` (default):
  a candidate that passes all pre-registered development gates is parked in HANDOFF › Open as "ready for
  the one-time test". `Mode=auto`: the loop runs it itself. Both: never change defaults (costs, sweep
  options, spread table) without the user's go. `Mode=auto` in full (never out of work, Fable advisor until
  2026-11-16, Telegram format, auto-decision log): CLAUDE.md › `Mode=manual|auto`.

## Record

- `docs/research-log.md`: what was tested, cells, net / gross R, gates, model and effort per task.
- Candidate row / idea card status (built, rejected by the user <date>, ...); `docs/HANDOFF.md`.
- **Count every look (review tip 4):** screens, cells and one-time tests all go into the committed
  ledger `research/ledger.csv` (one row per idea or hypothesis, the user 2026-11-11); one family-level
  threshold covers all hypotheses together.
- Count families, specs and cells honestly; a parameter cell is not a new hypothesis, and a failed
  family is not re-proposed under a new name.
- End of run: short report (tested, results, gates, decisions needed); a very promising strategy
  first, and on Telegram (format and command: CLAUDE.md › Telegram), sent as soon as it passes
  its gates, not only at the end of the run.
