---
name: gemini-helper
description: Hand a task to the Antigravity CLI (agy) non-interactively - as Gemini 3.8 Flash for research, knowledge/ write-ups, writing and running tests, research cards; or as Claude 4.6 (Sonnet / Opus) for reviewing Codex's code and as the second coding lane. Use whenever AGENTS.md › Team assigns work to Gemini or Claude 4.6.
---

# gemini-helper (Antigravity CLI: Gemini and Claude 4.6)

Gemini CLI no longer serves personal accounts; both lanes run through `agy` on the Google AI
Pro quota. Opus is the only dispatcher and checks every result itself.

## Call

```bash
.venv/Scripts/python -m backtester.tools.ai_dispatch <gemini|claude46> --effort <low|medium|high> \
    [--write] [--cwd <repo or worktree>] --label <short-name> \
    (--prompt "<task>" | --brief briefs/<name>.md)
```

- **gemini**: effort picks `gemini-3.8-flash-<effort>` (no Pro model on this account).
  `medium` for research, summaries, card write-ups; `high` for writing / running tests and
  hard papers or books.
- **claude46**: `low` / `medium` = Claude Sonnet 4.6, `high` = Claude Opus 4.6 (thinking).
  Use for reviews of Codex's code (read-only) and as the coding lane after Codex.
- agy runs tools inside `--sandbox` with auto-approve (headless mode denies every tool
  otherwise) and answers as JSON; the dispatcher unpacks it. The sandbox is not a hard wall:
  the guard after the call is (any change on a read-only task, commits, branches, pushes,
  protected paths -> exit 3). Write tasks only in a clean tree or a lane worktree.
- Code tasks need a brief from Codex or Opus (files, spec section, test cases, done = tests
  green + ruff). Research tasks: topic, sources wanted (books, papers, studies with links),
  output file in `knowledge/`. Parallel research: several calls in the background, one topic
  each, different `--label`s.

## Result

JSON line with `status`, `note` (e.g. `denied: command`) and the `answer` file in
`results/ai/`; exit 3 = violation (revert and report), exit 4 = usage limit (Gemini and
Claude 4.6 share the Google quota: hand to Codex, then Opus). Gemini's tests and Claude 4.6's
code are reviewed by Codex; Opus runs the tests before any commit.
