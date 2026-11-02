---
name: ai-dispatch
description: Hand one bounded task to Codex, Gemini / Claude 4.6 (agy) or the free local Ollama model through backtester.tools.ai_dispatch, or show AI usage stats. Use when docs/agent-routing.md routes a task to a worker instead of doing it in this session.
---

# ai-dispatch

Pick the route in `docs/agent-routing.md` first. If the task is small enough to do here, or a
local tool (pytest, ruff, rg, a script) does it, do not dispatch.

## Call

```bash
.venv/Scripts/python -m backtester.tools.ai_dispatch <codex|gemini|claude46|local> \
    --effort <low|medium|high|xhigh> [--model <id>] [--write] [--cwd <worktree>] \
    --label <short-name> (--prompt "<task>" | --brief <file>)
.venv/Scripts/python -m backtester.tools.ai_dispatch stats
```

- **codex**: default `gpt-6.1-terra`; `--model gpt-6.1-sol` for engine / no-lookahead / risk /
  new strategies / hard bugs; `gpt-reserve` for mechanical edits. No Astra (no access).
  Shell mode: edits files and runs pytest / ruff itself.
- **groq / openrouter / gemini-api / deepseek**: hosted chat APIs, text only, key from the
  Credential Manager; each has a verified default model. OpenRouter accepts only `:free` models; deepseek direct needs `--allow-paid`.
  Use only rows marked verified in the routing doc.
- **gemini**: Flash 3.8 by effort; docs, look-ups, short summaries. **claude46**: Sonnet 4.6
  (low / medium) or Opus 4.6 (high); only for a second opinion on a high-risk change.
  Both share one small weekly agy quota.
- **local**: Ollama on this PC, zero paid tokens, text in / text out, no tools. Give it a
  filtered excerpt with `--brief`, never a whole log.
- Write tasks need a clean tree or a lane worktree so the guard sees only the worker's changes.
  Long tasks: `run_in_background`, wait for the notification.

## Brief

Files it may touch, the spec section, test cases or acceptance criteria, "done =" (tests green
+ ruff), and the likely rule questions with answers. The worker has no chat context.

## Result

JSON line: `status` ok / error / limit / violation, `answer` = file in `results/ai/`.
- Exit 3 = violation (commit, branch, protected path, change on a read-only task): inspect,
  revert, report.
- Exit 4 = limit: no automatic switch. Use the next route of the same cost level or pause and
  report; never fall to a paid Claude model because a free one failed.
- Verify by running the tests of what changed; read the diff. No second AI review unless the
  change is engine / no-lookahead / risk.
