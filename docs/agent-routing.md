# Agent routing (rule set by the user, 2026-11-02; replaces the 2026-10-22 team rules)

Goal: the cheapest method that reliably does the task. Escalate on a demonstrated failure, never
by habit. One coordinator at a time; no review chains by default.

## Order of preference

1. **Local tools, zero tokens:** `pytest`, `ruff`, `rg` / `grep`, plain Python scripts, the
   research runner and job queue, `git diff --stat`. Filter logs to the relevant lines first.
2. **Local LLM, zero paid tokens:** `ai_dispatch local` (Ollama qwen3.5 4b / 9b / 27b by
   `--effort low / medium / high`): summarise a filtered log, extract fields from a long text.
   Text only, no tools, no file access; feed it an excerpt (`--brief <file>`), not a whole log.
3. **The active coordinator does it itself** when the task is small (one file, a few lines,
   a question): a brief plus a check costs more than the change.
4. **Delegate** (below) only when the task is bounded and the worker is cheaper or better.
5. **Escalate to Opus** only for the cases under Escalation.

## Coordinator

- **Routine coding sessions:** Codex `gpt-6.1-sol` medium, started directly in this repo
  (`codex`; it reads `AGENTS.md`). It does the work itself; no Opus in the loop.
- **Claude Code session (Opus):** the session protocol in `CLAUDE.md` (`Continue.*`, `Stop.`,
  `End.`, research loop), user decisions, and escalations. It delegates coding to Codex and
  verifies by running the tests, not by a second AI review.

## Workers

| Task | Route | Verified |
|---|---|---|
| Mechanical edits (renames, labels, doc sync, pinning tests) | Codex `--model gpt-reserve` low, or Claude subagent `haiku` | 2026-10-28 |
| Routine code from an exact brief (tools, reports, UI glue) | Codex `gpt-6.1-terra` medium (dispatcher default) | 2026-11-02 |
| Engine / no-lookahead / risk, a new strategy from a spec, hard bugs | Codex `--model gpt-6.1-sol` medium, high only when needed | 2026-10-29 |
| Codex failed twice at sol | Claude subagent `sonnet` (no Astra: OpenAI flagship, no access) | in-session |
| Quick bounded fixes, short text tasks | `ai_dispatch groq` (`openai/gpt-oss-120b`; also `--model qwen/qwen3.8-27b`), free tier | 2026-11-02 |
| Long-text extraction, summaries | `ai_dispatch openrouter` (`nvidia/nemotron-3-ultra-550b-a55b:free`; also `cohere/north-mini-code:free`); only `:free` models accepted | 2026-11-02 |
| Docs / look-ups when the agy quota is out | `ai_dispatch gemini-api` (`gemini-3.8-flash`; also `gemini-flash-lite-latest`), AI Studio free tier | 2026-11-02 |
| Hard logic check, independent second analysis | `ai_dispatch groq` or `gemini-api` (free); DeepSeek direct needs `--allow-paid` and a balance | not enabled |
| Complex debugging that needs the chat context | Claude subagent `sonnet` medium | in-session |
| Docs / method look-ups, short research summaries | `ai_dispatch gemini --effort low/medium` (Flash 3.8) | 2026-11-02 |
| Large log / long text extraction | local tools first, then `ai_dispatch local` | 2026-11-02 |
| Independent second opinion on a high-risk change | `ai_dispatch claude46 --effort medium` (small weekly quota) | 2026-10-29 |

**Hosted APIs** (OpenAI chat format, text only: no tools, no file access). Keys live only in
the Windows Credential Manager (generic credential `<provider>@backtester-ai`, user name
`<provider>`), entered by the user. Probed 2026-11-02 with a one-word prompt:
- groq, openrouter, gemini-api: working; defaults set in `ai_dispatch` (`Provider.model`).
- openrouter free models are often rate-limited upstream (`google/gemma-4-31b-it:free` gave 429):
  exit 4, try another `:free` model, never a paid one. The free list has no DeepSeek model.
- deepseek: key valid, account has no balance (HTTP 402); paid per token, so it also needs
  `--allow-paid`.
- GitHub Models: not enabled; `models.github.ai` answered a plain "OK" to every request, even
  without a token, so no real API response reached this PC.
- Not used: LiteLLM (one stdlib HTTP call covers every provider), Cerebras (no recurring free
  tier).
Free tiers may log or train on prompts: send excerpts of our own code and logs only, never
credentials, `.env`, MT5 / Telegram data or `src/backtester/live/`.

## Continuous research run (rule set by the user, 2026-11-09)

- **Codex first:** all coding (strategies, tools, tests, fixes) goes to Codex via `ai_dispatch`:
  `gpt-6.1-terra` by default, `gpt-6.1-sol` for engine / risk code. Opus reviews by running the
  tests.
- **Literature / web research:** free models first (`ai_dispatch gemini --effort low`,
  `gemini-api`, `openrouter`); Opus opens the sources before relying on them.
- **Sonnet only for small work (rule set by the user, 2026-11-10):** Sonnet sub-agents do small finishes
  and bounded tasks (a spec draft, a check), never heavy builds (engine steps, new strategies), even when
  Codex is at its limit; heavy work waits for the Codex reset.
- **Claude Sonnet sub-agents** only when Codex fails, is rate-limited or at its limit, or as a
  parallel addition while Codex is busy; never to fill a wait. The research log names the model of
  every task. (The user's "use Sonnet" of 2026-11-09 morning applied to that run only.)
- **Opus only coordinates, decides and reviews**; it paces Claude token use so the session limit is
  never hit (small context, filtered logs, short reports; slow down or wait for the reset when
  close). When Codex hits its limit, Opus does work that needs no Codex (research, specs, gates,
  records, reviews by running tests) and resumes coding after the reset (~5 h window). Never fall
  back to a paid model on its own.

## Codex quota and sol reviews (rules set by the user, 2026-11-09)

- **Use 90-100 % of every 5-hour Codex window.** Up to 2 parallel Codex dispatches, each in its own
  lane worktree on independent files (never two writers in one checkout; no commits in a checkout
  while a write dispatch runs there). Keep a backlog so Codex never idles: next research
  candidates, open tool briefs, read-only Codex reviews of risk-adjacent changes. Spare quota goes
  to quality first (sol or higher effort where it helps, tests, reviews). No busywork: if nothing
  useful is left, idle quota is fine.
- **Claude usage is the brake:** Opus still reviews every result by running the tests; if the
  Claude limit gets close, lower the Codex rate instead of skipping reviews.
- **Weekly Codex limit:** when it is out, stop coding, report it in HANDOFF › Open and continue with
  non-Codex work; the user decides on a weekly reset (two left); never reset or buy anything.
- **Codex `gpt-6.1-sol` as a read-only reviewer, selectively:** for changes near costs, fills,
  risk or no-lookahead, and for every new strategy built from a spec (spec vs code, lookahead),
  where tests may not catch a wrong rule; it counts toward the Codex use. Not for UI glue, docs or
  small tools (the tests decide there). Read-only, one round per change: sol reports findings with
  evidence; Opus decides which are real, fixes go through the normal route, Opus verifies by running
  the tests.
- **Opus effort:** the user may run this session at medium effort for long / overnight runs and
  switch to high for decisions. At medium, a high-stakes judgement (ambiguous trading rule, gates /
  pre-registration, one-time test, a bug two workers could not fix) is parked in HANDOFF › Open for a
  high-effort pass instead of being decided.

## Escalation to Opus (strategic only)

Architecture decisions, a trade-off the user must decide, a bug two workers could not fix,
anything that could break no-lookahead, fills, costs or risk in a way tests may not catch.
Opus decides and writes the brief; a worker implements.

## Rules

- **Context:** a brief names the files, the spec section, the tests and "done =". No
  whole-codebase or full-log dumps; Codex starts without chat context.
- **Compact answers:** workers return conclusion, files changed, test result, open questions.
- **Bounded retries:** one retry at the same level, then one level up, then stop and report.
  Max one review round per change.
- **Verification:** the coordinator runs the tests of what changed (full suite once before a
  commit). AI review only for engine / no-lookahead / risk / live-adjacent changes.
- **Fallback discipline:** `ai_dispatch` never switches model on its own. Exit 4 (limit) or a
  local / free failure means: try the next row of the *same* cost level, or pause and report.
  Never move to a paid Claude model just because a free one failed.
- **Security:** the dispatcher strips secret env vars; never send credentials, `.env`, MT5 or
  Telegram data, or `src/backtester/live/` code to an external model. `local` keeps data on
  this PC.
- **Usage:** every dispatch is logged in `results/ai_calls.jsonl`;
  `python -m backtester.tools.ai_dispatch stats` sums calls, minutes and limit hits per model.
  Claude Code usage is visible in the app; no token counts exist for Codex / agy runs, so do not
  estimate savings.
