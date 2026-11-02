---
name: continue-research
description: Procedure for the user's Continue.Research command - the autonomous test loop on research-department submissions (intake, specs, sweeps, one-time MT5 test, result envelopes). Load when the user says Continue.Research.
---

# Continue.Research (moved from CLAUDE.md, 2026-11-02)

- **`Continue.Research [Limit=<time>] [<STRATEGY_ID>]`:** the autonomous test loop on research
department submissions (V2.6 / V2.7; job queue, lanes, research log built in V2.6; intake per
`docs/research-intake.md`). **Blocked until ROADMAP V2.6i passes**: until then it may work
only on V2.6i itself or on the three pre-registered V2 hypotheses (ROADMAP V2.6).
- Start: read `../Shared_Interface/INTERFACE_CONTRACT.md`, list `queue/pending/` and our open
  claims in `results/intake/`.
- First call in a chat: ask ALL open questions at once, numbered (limit, topic, anything
  unclear in the log or specs) and wait. Then run autonomously (Telegram only for urgent
  ones). Later calls in the same chat reuse the answers.
- `Limit=60min` / `2h` / `3d`: write start time and deadline into `docs/research-log.md`,
  check the clock after every step; at the deadline finish the current step cleanly
  (commit, log) and stop. No limit = until "Stop." or the resources run out.
- STRATEGY_ID given: work only on that submission. Otherwise the highest-`priority`
  submission in `queue/pending/`, then our open claims. No submission -> report and stop;
  never invent an idea to fill the time.
- Rules: every strategy comes from a validated, claimed submission; its sources and
  evidence are the research department's responsibility (Opus does not re-research them,
  but returns feedback on anything that looks wrong). Every rule maps to the submission;
  anything unclear: Opus decides by its own judgment, writes it into the spec's
  "Assumptions" section, tells Research in an `ASSUMPTION_MADE` feedback message and builds
  anyway; `NEEDS_CLARIFICATION` only when no reasonable reading exists. Specs need no user
  approval in the loop; the one-time MT5 test still does (rule set by the user, 2026-10-28;
  `docs/research-intake.md` › Assumptions and replies). One parameter set pooled across all
  markets by default; per-market parameters with re-optimisation only as a walk-forward
  variant of a promising strategy (rule set by the user, 2026-10-23). Vary only the parameters
  the submission marks tunable, within its ranges. Do not judge pass / fail: record every
  strategy with all metrics and the submission's rejection criteria computed; the user decides.
  Every experiment ends in a result envelope (or a feedback envelope) in `../Shared_Interface/feedback/`.
  The one-time MT5 test of a submission needs the user's explicit go.
  Develop before 2021-09-14, test the best variant once on MT5 data from 2021-09-14 (rule set
  by the user, 2026-10-15); every variant in the trial log; DSR, robustness report, real
  costs + swap, Monte Carlo, parameter stability, regime breakdown, warning flags. Prefer no
  overnight holds (swap). Never change defaults (costs, sweep options, spread table) without
  the user's go.
- End of run: short report (tested, results, research cards added, envelopes written,
  feedback sent); a very promising strategy first, and on Telegram.
