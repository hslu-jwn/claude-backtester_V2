# Research log

Running log of the research loop (V2.6 / V2.7) and of the model / effort used per task, so a
run resumes after a restart or a usage limit. Newest first. Every AI call is also logged by
the dispatcher in `results/ai_calls.jsonl` (model, effort, seconds, status).

## Model usage, V2.1-V2.4 (2026-10-22 / 23)

| Tool / model | Effort | Calls | Minutes | Used for | Worth it? |
|---|---|---|---|---|---|
| Codex gpt-6.1-sol | high | 16 | 165 | module reviews (8), A1, B-risk, B-engine, B-strategy, speed 1-2 | yes: found 84 real issues with evidence; implementations needed few corrections |
| Codex gpt-6.1-sol | medium | 9 | 44 | inventory, dedupe, golden tool, A2/A3 finish, A4/A5 | yes for well-specified batches |
| Gemini 3.8 Flash | high | 4 | 25 | two reviews (good), one write task (quota ran out half-way) | reviews yes; bulk writing burns the weekly quota |
| Claude Opus 4.6 (agy) | high | 3 | 4 | one review | the 4 subagents it started emptied the weekly quota |
| Claude subagents (this app) | Opus high / Sonnet medium | 2 | - | live-bot fixes (19 findings, 45 tests), UI proposal draft | yes; live code is Opus-only |

Limits seen: Codex hit its limit twice (about 20:50 and 04:25; reset after ~4.5 h);
Antigravity (Gemini + Claude 4.6, one shared weekly quota) is empty until about 2026-10-29.

## Research runs

(none yet; V2.6 starts after the regime classifier spec is accepted)
