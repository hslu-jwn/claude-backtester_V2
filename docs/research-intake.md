# Research intake: how V2 takes strategies from the research department

Process spec (the user, 2026-10-27). **Status: the interface is a proposal, not operational.**
Until ROADMAP V2.6i passes its synthetic end-to-end test, no real submission is claimed or built.
Review of the contract: `docs/review/research-interface-review-2026-10-27.md`.

## Who owns what

| Research department (`../Research_Department/`) | Backtester team (this repo) |
|---|---|
| Literature, papers, studies, community sources | Implementation, data, costs, engine, risk, live |
| Hypotheses, mechanism, falsifiable predictions | `docs/strategy-<name>.md` spec written from the submission |
| Complete JSON strategy specification, its versions | Mapping submission -> config / code / tests |
| Research priority (`priority` field) | Experiments, statistical validation, trial log, DSR |
| Reads result / feedback envelopes | The one-time test (holdout) and its authorisation |

The backtester team no longer does literature research or invents strategy ideas. `knowledge/`
is frozen background (see `knowledge/README.md`); new ideas arrive only through the queue.
Our evaluation methodology (`knowledge/topics/testing-and-robustness.md`,
`statistics-and-bayes.md`, `costs-and-execution.md`, `backtest-frameworks.md`) stays ours.

## Paths (all canonical, never copy them into V2)

- Submissions: `../Shared_Interface/queue/pending/<STRATEGY_ID>__v<x.y.z>.json`
- Claimed / terminal: `../Shared_Interface/queue/{claimed,completed,rejected}/`
- Our answers: `../Shared_Interface/feedback/results/` (result envelopes) and
  `feedback/messages/` (feedback envelopes)
- Schemas: `../Shared_Interface/schemas/`; contract: `../Shared_Interface/INTERFACE_CONTRACT.md`
- Our claim / mapping records: `results/intake/<STRATEGY_ID>__v<x.y.z>/` (git-ignored)

The strategy queue is **not** the compute-job queue (`results/queue`). A submission becomes a
compute job only after it is a reviewed V2 strategy.

## Pipeline per submission (replaces the old "idea -> spec" pipeline)

1. **Intake** (Opus): pick the highest-`priority` file in `pending/`; validate (name =
   identity, schema, status `SUBMITTED`, no duplicate); claim it atomically. A failure gives a
   feedback envelope, nothing runs.
2. **Compatibility check** (Opus, Codex second opinion): data available for the universe and
   period? stop-defined R trade? fill timing representable? Otherwise feedback
   `UNSUPPORTED_DATA` / `UNSUPPORTED_STRATEGY_TYPE`. Never approximate (no invented far stop,
   no changed sizing, no swapped fill timing).
3. **Clarify**: any rule that needs judgment -> feedback `NEEDS_CLARIFICATION` quoting the field
   (JSON Pointer). Research answers with a new specification version; we never guess.
4. **Spec** (Codex): `docs/strategy-<name>.md` from the submission, with a "Submission"
   section: strategy_id, version, sha256 of the submitted bytes, and a mapping table of every
   parameter and rule to a config field / code location / test. The user approves the spec.
5. **Tests, code, review**: as AGENTS.md › Team and › Testing (test-first, lane, no-lookahead
   review).
6. **Development experiment**: grid from the submission's tunable parameters and ranges only
   (adding a variant = feedback, not a silent extension); everything in the trial log; DSR,
   robustness, Monte Carlo, parameter stability, regime breakdown, flags; job queue.
7. **Result envelope** (development stage): metrics, the submission's rejection criteria
   computed (we report them; the user decides), references to `results/<run-id>/` and
   `results/research/<id>/`.
8. **One-time test** after 2021-09-14: only with the user's explicit go per strategy. Its
   envelope discloses only what the agreed holdout policy allows.
9. **Close**: move the queue file to `completed/` or `rejected/` (never deleted), update
   `docs/research-log.md`, ROADMAP, HANDOFF.

## Decided (the user, 2026-10-27)

Two stages only (develop before 2021-09-14, test once after); the adapter is built after the
V2.6d step-1 fill analysis; `jsonschema` as optional extra `[intake]`; stopless / notional /
target-weight / portfolio strategies and `NEXT_BAR_OPEN` fills are rejected for now
(`UNSUPPORTED_STRATEGY_TYPE`; future options in the review › section 6); the one-time test only
on the user's go; queue files kept forever. Details: review › section 3.

## Rules that stay

No lookahead; fixed split (develop before 2021-09-14, test once on MT5 after); one parameter
set pooled across markets by default; never change defaults (costs, sweep options, spread
table) without the user; V2 costs are the ones applied, the submission's requested costs are
recorded next to them; do not judge pass / fail, the user decides.
