---
name: codex-helper
description: Hand a task to Codex (OpenAI Codex CLI) non-interactively - code writing, code review, specs, test-case lists, strategy design from research, or a second opinion before asking the user. Use whenever AGENTS.md › Team assigns work to Codex.
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

- **Codex has no working shell on this PC:** on Windows its sandbox blocks every command,
  reads included (2026-10-22). So **paste what it needs into the brief** (the source file, the
  diff from `git diff`, the spec section) and ask for findings or a unified diff as the answer;
  Opus applies a diff with `git apply`, then tests. It still auto-loads `AGENTS.md`.
- **Read-only by default** (`-s read-only`; the guard also fails the call if any file changed).
  `--write` (`workspace-write`) only helps once commands work.
- **Effort** (CLAUDE.md › Models and subagents): `medium` for normal coding and reviews,
  `high` for specs, strategy design, hard bugs, anything touching no-lookahead / engine / risk.
  After a failed try raise one level (`xhigh`, then `--model gpt-6-astra`) before escalating
  to Opus.
- Long tasks: run with `run_in_background` and wait for the notification.

## Brief (what to put in the prompt)

Files / folder it may touch, the spec section (`docs/...` › heading), the test cases or
acceptance criteria, and "done =" (tests green + ruff). For reviews: the diff range
(`git diff main...<branch>`) and what to check first (lookahead, fills, SL/TP order, costs,
swap, time zones). Codex starts with no chat context.

## Result

- Prints a JSON line: `status` ok / error / limit / violation, `answer` = path of the answer
  file in `results/ai/`. Read that file.
- Exit 3 = **violation** (commit, branch switch, or a protected path such as
  `src/backtester/live/` changed): inspect, revert the offending change, report it.
- Exit 4 = **usage limit**: hand the task to Gemini or Opus (CLAUDE.md › usage limits).
- Then verify: read the diff, run the tests yourself, and only then commit (Opus commits).
