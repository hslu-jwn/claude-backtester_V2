---
name: gemini-helper
description: Hand a task to Gemini (Antigravity CLI, agy) non-interactively - literature / web / study research, knowledge/ write-ups, simple pre-planned code, writing and running tests, research-card summaries. Use whenever AGENTS.md › Team assigns bulk work to Gemini.
---

# gemini-helper

Gemini runs through the Antigravity CLI (`agy`; Gemini CLI no longer serves personal
accounts). Opus is the only dispatcher and checks every result itself.

## Call

```bash
.venv/Scripts/python -m backtester.tools.ai_dispatch gemini --effort <low|medium|high> \
    [--write] [--cwd <repo or worktree>] --label <short-name> \
    (--prompt "<task>" | --brief briefs/<name>.md)
```

- Effort picks the model: `low` / `medium` / `high` -> `gemini-3.8-flash-<effort>` (no Pro
  model on this account; `high` stands in for Pro).
  - `medium`: literature and web research, summaries, card write-ups.
  - `high`: simple pre-planned code, writing and running tests, hard papers / books.
- Always runs with `--sandbox` (terminal restrictions). `--write` adds
  `--dangerously-skip-permissions` so it can edit files and run pytest unattended; use it only
  in a lane worktree or with a clean working tree, so the guard sees exactly its changes.
- Code tasks need a brief planned by Codex or Opus (files, spec section, test cases, done =
  tests green + ruff). Research tasks: topic, sources wanted (books, papers, studies with
  links), output file in `knowledge/`.
- Parallel research: several calls with `run_in_background`, one topic each, different
  `--label`s.

## Result

Same as codex-helper: JSON line with `status` and `answer` file in `results/ai/`; exit 3 =
violation (revert and report), exit 4 = usage limit (hand to Codex, then Opus). Escalation:
2 tries at Gemini (second one with higher effort) -> Codex. Then review: Gemini's code is
reviewed by Codex, and Opus runs the tests before any commit.
