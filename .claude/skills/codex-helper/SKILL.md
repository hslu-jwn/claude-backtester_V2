---
name: codex-helper
description: Hand a task to Codex (OpenAI Codex CLI) non-interactively - production code, specs, test-case lists, strategy design from research, code review, or a second opinion before asking the user. Use whenever AGENTS.md › Team assigns work to Codex.
---

# codex-helper

Opus is the only dispatcher (AGENTS.md › Team). This skill runs one Codex task and returns its
answer file; Opus then checks the result itself (diff + tests), never trusting "done".

## Call

```bash
.venv/Scripts/python -m backtester.tools.ai_dispatch codex --effort <low|medium|high|xhigh> \
    [--write] [--model gpt-6-astra] [--cwd <repo or worktree>] --label <short-name> \
    (--prompt "<task>" | --brief briefs/<name>.md)
```

- **Shell mode** (approved by the user, 2026-10-22): Codex runs with `--approve-for-me`
  (workspace-write sandbox, an automatic reviewer approves each command), so it reads files,
  edits and runs pytest / ruff itself. Without `--write` the guard fails the call if any file
  changed. It auto-loads `AGENTS.md`.
- **Effort** (CLAUDE.md › Models and subagents): `medium` for normal coding and reviews,
  `high` for specs, strategy design, hard bugs, anything touching no-lookahead / engine / risk.
  After a failed try raise one level (`xhigh`, then `--model gpt-6-astra`), then escalate to
  `claude46`.
- Write tasks: a clean working tree or a lane worktree (`--cwd`), so the guard sees exactly
  Codex's changes. Long tasks: `run_in_background`, wait for the notification.

## Brief

Files / folder it may touch, the spec section (`docs/...` › heading), the test cases or
acceptance criteria, and "done =" (tests green + ruff). For reviews: the diff range
(`git diff main...<branch>`) and what to check first (lookahead, fills, SL/TP order, costs,
swap, time zones). Codex starts with no chat context.

## Result

- Prints a JSON line: `status` ok / error / limit / violation, `answer` = path of the answer
  file in `results/ai/`. Read that file.
- Exit 3 = **violation** (commit, reset, branch, push, protected path such as
  `src/backtester/live/`, or a change on a read-only task): inspect, revert, report it.
- Exit 4 = **usage limit**: hand the task to `claude46` (CLAUDE.md › usage limits).
- Then: Claude 4.6 reviews the diff, Opus runs the tests itself, and only then commits.
