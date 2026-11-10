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
- **`Continue.Research [Limit=<time>] [Test=manual|auto] [<CANDIDATE or idea ID>]`:** the autonomous research loop
  (research is back in this team since 2026-11-09, the user): pick a candidate or research a new
  idea, spec with pre-registered gates, implement, development run, gates, record. Full procedure
  in the `continue-research` skill (load it first). **One-time MT5 test mode (rule set by the user, 2026-11-09):** default `Test=manual`: a
  candidate that passes all pre-registered development gates is parked in HANDOFF › Open as
  "ready for the one-time test" and the loop moves on. `Test=auto`, given with the command (e.g.
  `Continue.Research Test=auto`): the loop runs the one-time test itself, only for a candidate that
  passed every pre-registered development gate. Both modes: exactly once per candidate, no retest
  after a fail, the variant is frozen before the test, pass or fail recorded in the research log
  and HANDOFF. Auto lasts for that run only; the next session is manual unless the user says
  `Test=auto` again. Never change defaults (costs, sweep options, spread table) without the
  user's go. `Continue.Knowledge` and `Begin.` are retired; if the user says one, offer
  `Continue.Research`.
- **Continuous `Continue.Research` (the user, 2026-11-09):** runs with no time limit until
  `Stop.`; after each finished step take the next one (candidate, researched idea, follow-up,
  tooling the research needs); commit and push after every step; keep the session alive across
  waits (self-paced `/loop`); routing as in `docs/agent-routing.md` › Continuous research run.
  Items that need the user's decision go to HANDOFF › Open, and the run continues with the rest.
- **`Pause.`:** finish the current step cleanly (commit, push, log) and wait until `Continue.`.
- **`Continue.`:** resume where the run paused.
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
- **Telegram default (rule set by the user, 2026-11-10):** send a message when a promising strategy
  is found (passed its pre-registered gates) or when the session has been waiting for the user for
  more than 5 minutes; this replaces "no Telegram" from earlier runs.
- **Telegram** (`live/telegram.py`, token from the Windows Credential Manager) only for: a
  decision on rules / defaults / risk, a blocker Codex can't solve, a crash or long pause of
  the loop / queue, a very promising strategy; plus one short evening summary while research
  runs. Send with `python -m backtester.tools.notify "<text>"`. A very promising strategy
  (passed every pre-registered development gate) is sent right away as one message: name,
  symbols, trades, win rate, avg R, net R (doubled costs), profit factor, max drawdown R,
  dev period. A session waiting for the user is announced by the user-level `Notification`
  hook (same tool, `--hook`).
