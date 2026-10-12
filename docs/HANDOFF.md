# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

## Last session (2026-10-12): Phase 1 assessment and Phase 2 cleanup of the docs
- Done and accepted by the user: conflict list resolved, docs/ROADMAP/CLAUDE.md corrected,
  project skills in `.claude/skills/`, Strategy Simulator (6.1) and prop-firm field (5.6) added to the ROADMAP,
  cleanup backlog C.1-C.3 added.
- Known and accepted: `/ponytail-audit` not installed.
- Work done by the user's local sessions in parallel (merged 2026-10-12): C.1 Dukascopy removed, C.2 MT5 test skip,
  C.3 strategy registry + template, C.4 layer fixes (`tools/`), 8.6a (strategy popover/settings for both strategies).
- Decisions: strategy 1 is paused; the liquidity sweep is reworked iteratively with the user (code untouched until he says);
  the Simulator ranks by max net R with a minimum trade count and tunes/reports on separate periods;
  the user marks which settings take part in the Simulator; work locally for backtests and chart checks.

## Accepted by the user (do not ask again)
- The ROADMAP order and the cleanup backlog as written.
- Tests first, small commits on the session branch, no PR unless asked.

## Open (needs the user)
- C.1-C.4 and 8.6a are built (ROADMAP: ◐ "waiting for the user's OK"). Ask once at the start: "OK to mark them ☑?" and record the answer.
- Stray empty file `CUsersjusti.claudeclaude-notify-signalsstop` in the repo root (a Windows path glued into a file name, committed by accident):
  propose deleting it and add the pattern to `.gitignore`; delete only after the user says yes.
- Sweep rework: the threshold for "not significant" (percent / ATR / points) is to be agreed before implementing.
- Best-time tag removal and the window settings (ROADMAP 8.3 / 8.4) wait for his go.

## Next step (suggested)
Confirm C.1-C.4 / 8.6a, then 8.6b / 8.6c, or the sweep rework discussion (the user decides). After that 6.1 Strategy Simulator is the next milestone.

## First prompt for the next chat
`Continue.`
