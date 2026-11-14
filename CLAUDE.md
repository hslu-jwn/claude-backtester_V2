# CLAUDE.md

Guidance for Claude Code (Opus: session protocol and strategic escalation). The project rules
shared by all models are in `AGENTS.md`; they apply in full:

@AGENTS.md

Current state, accepted work and next step: `docs/HANDOFF.md`; plan: `docs/ROADMAP.md`
(archive `docs/archive/ROADMAP-v1.md`).

## Working agreement with the user

- Address the user as "Chef", answer in English, short and concrete; explain a new concept in
  one line. Ask all open questions together, numbered. Never assume; on any doubt or conflict
  (also CLAUDE.md, code, tests, config) ask first.
- Small commits on a feature branch, push regularly; no PR unless asked.
- **Models:** `docs/agent-routing.md` (rule set by the user, 2026-11-02). Opus is the
  strategic escalation and runs the session protocol below; routine code goes to Codex via the
  `ai-dispatch` skill, small edits Opus makes itself. Plans: ChatGPT Plus and Google AI Plus
  only (Codex ~2 h high effort per ~5 h window; agy one small weekly quota). Record model and
  effort per task in `docs/research-log.md`.
  - Shell gotcha: never put backticks in inline PowerShell (they are escape characters); edit
    files with the Edit tool or a script file.
- **Where to work:** locally (data and app are here); the cloud has no market data.
- **New strategies:** one folder under `strategy/` (copy `strategy/_template/`) plus one entry
  in `strategy/registry.py`; strategy settings in its config; detectors, costs and warm-up shared.
- **Skills:** `ai-dispatch`, `ponytail` (user plugin; small changes; the rules above win), `/ponytail-review` before each
  commit, `/ponytail-audit` occasionally (findings -> ROADMAP), `backtester-testing`,
  `continue-research`.

## Session protocol (the user does no file work)

- **`Continue.Code`:** work on the application: the V2 phases in `docs/ROADMAP.md`, then
  app / engine improvements from `docs/HANDOFF.md` and the ROADMAP. `git pull`, read
  `docs/HANDOFF.md` and the ROADMAP step, run tests + ruff as a baseline, say in max 10 lines
  what you will do (plan, test cases, files, models), ask all open questions at once, then work
  test-first, step by step with the user's ok.
- **`Continue.Research [Limit=<time>] [Mode=manual|auto] [<CANDIDATE or idea ID>]`:** the autonomous research loop
  (research is back in this team since 2026-11-09, the user): pick a candidate or research a new
  idea, spec with pre-registered gates, implement, development run, gates, record. Full procedure
  in the `continue-research` skill (load it first). One-time MT5 test: exactly once per candidate, no retest after a fail, the variant frozen before the test, pass or fail recorded in the research log and HANDOFF; who decides to run it: `Mode` below. Never change defaults (costs, sweep options, spread table) without the
  user's go. `Continue.Knowledge` and `Begin.` are retired; if the user says one, offer
  `Continue.Research`.
- **Continuous `Continue.Research` (the user, 2026-11-09):** runs with no time limit until
  `Stop.`; after each finished step take the next one (candidate, researched idea, follow-up,
  tooling the research needs); commit and push after every step; keep the session alive across
  waits (self-paced `/loop`); routing as in `docs/agent-routing.md` › Continuous research run.
  Items that need the user's decision go to HANDOFF › Open, and the run continues with the rest.
- **One research loop at a time (rule set by the user, 2026-11-12):** never run two
  `Continue.Research` loops in parallel. `ai_dispatch` snapshots all git refs, so one loop's commit
  or push flags another loop's running Codex dispatch as a violation; the loops would also share
  the registry, ledger and log files and the Codex quota.
- **Never idle (rule set by the user, 2026-11-10):** in any run, keep working; never just wait or hold
  quietly. When the work runs out or the ideas look weak, propose concrete next steps (with a pick) or ask
  the user for direction in the same turn, start the best real option meanwhile, and send a Telegram if
  the question waits more than 5 minutes.
- **Always propose next steps (rule set by the user, 2026-11-12):** end every finished task or
  session step with 2-3 concrete next steps and a pick, across both modes. When the `Continue.Code`
  work is done, propose research (`Continue.Research`: next candidate, screen, idea), and when research
  stalls, propose the code or tooling it needs, so the user can always stay productive.
- **`Mode=manual|auto` (rule set by the user, 2026-11-14; replaces `Test=` and the 2026-11-12 auto
  rule):** given with `Continue.Code` or `Continue.Research` (e.g. `Continue.Research Mode=auto`); default
  `manual`; lasts for that session only.
  - `manual`: ask as before (one-time MT5 test parked in HANDOFF › Open, downloads, harvest batches, picks).
  - `auto`: Opus decides every pick itself and always takes its own first pick (reruns, downloads, harvest
    batches, sessions / subagents, the one-time MT5 test for a candidate that passed every pre-registered
    development gate). Only two things still wait for the user: changing defaults (costs, spread table,
    risk) and anything touching live orders or money; those go to HANDOFF › Open with a Telegram and the
    run continues with the rest.
  - `auto` never runs out of work: when no carded idea or candidate is left, Opus finds new sources (web
    research through subagents, harvest batches, new data it can get, books). Goal 1: strategies that pass
    prop-firm (FTMO) rules; goal 2: futures, swing and other strategies. It may ask for books or data the
    user must get himself (Telegram "Optional: ...").
  - Advisor: until 2026-11-16 Opus may ask Fable 5.2 (subagent, model `fable`) when it cannot find an answer
    itself, and gets from it one long list of possible research directions for the future (saved in
    `knowledge/`). After 2026-11-16 no Fable calls.
  - Every auto decision goes into `docs/research-log.md` (decision, the alternative, why) and is listed at
    `End.`.
- **`Pause.`:** finish the current step cleanly (commit, push, log) and wait until `Continue.`.
- **`Continue.`:** resume where the run paused.
- **`Stop.`:** end the current run within 1-2 minutes at a clean point: finish or roll back
  the step, stop lanes and job queue, commit, update the log, short report. Nothing
  half-finished stays uncommitted.
- **`End.`:** the user accepts everything done so far. Full tests + ruff (report failures
  honestly, record known issues), mark finished steps ☑ in the ROADMAP, write decisions into
  `docs/`, rewrite `docs/HANDOFF.md` (state, accepted, open, next step; about 60 lines, closed
  items live in git), copy `results/trials.jsonl` to `research/trials.jsonl` (the trial count is
  versioned, review B7), move finished briefs to `docs/archive/briefs/` (review A10; rules set by
  the user 2026-11-11), commit, push, clean `git status`. Reply in max 10 lines: done, not done, decisions, next step, first prompt for
  the next chat; after a `Mode=auto` run also the list of decisions Opus made on its own (from the
  research log), however long.
- **During any session:** when the user says ok / yes, it is final: write it into the repo in
  the same commit (rule -> `docs/` "(rule set by the user, <date>)"; accepted -> ROADMAP
  "accepted by the user <date>"). Never ask about it again.
- **Telegram (the one rule; rules set by the user 2026-11-10, merged 2026-11-11, review A4)**
  (`live/telegram.py`, token from the Windows Credential Manager): send when a strategy passes
  every pre-registered development gate, when the session has waited for the user for more than
  5 minutes, for a decision on rules / defaults / risk, a blocker Codex can't solve, or a crash or
  long pause of the loop / queue; plus one short evening summary while research runs. Send with `python -m backtester.tools.notify "<text>"`. A very promising strategy
  (passed every pre-registered development gate) is sent right away as one message: name,
  symbols, trades, win rate, avg R, net R (doubled costs), profit factor, max drawdown R,
  dev period. A session waiting for the user is announced by the user-level `Notification`
  hook (same tool, `--hook`).
  **Format and auto (rule set by the user, 2026-11-14):** short, one line each, e.g. `Action needed: ...`,
  `Strategy XX: Passed, +4 R per month, ...` / `Strategy XX: Failed, ...`, `Optional: New books needed:
  ..., ...`. In `Mode=auto` send only what matters for the project's main structure: an action needed
  (defaults, live orders, money), a strategy passing or failing its one-time test, a change to shared
  engine / risk code, and optional requests (books, data). Downloads are not reported.
