# Handoff

Read first in every session; rewritten at the end of every session (CLAUDE.md › Session
protocol). Current state only; history is in git and `docs/archive/ROADMAP-v1.md`.

## Where things are

- **Repo:** V2 = `X:\Dokumente\Projekte\backtester-claude\backtester-claude_V2`, GitHub
  `hslu-jwn/claude-backtester_V2` (only remote). V1 (`backtester-claude_V1`, GitHub
  `hslu-jwn/backtester-claude`) is read-only, frozen as backup.
- **Branch:** `main` has V2.1-V2.3 (merged 2026-10-22); V2.4 work on `v2-review`.
- **PC:** i9-10900K, 64 GB; Python 3.13 venv in `.venv`; tests ~3 min (3246 passed).
  `NODE_OPTIONS=--use-system-ca` is set (this PC intercepts TLS; npm / Codex need it).
- **AI team:** Codex CLI (ChatGPT login), Antigravity CLI `agy` (Google login; Gemini 3.8
  Flash + Claude Sonnet / Opus 4.6), all through `tools/ai_dispatch.py` (AGENTS.md › Team).
- **Data:** `data/` and `results/` copied from the old PC and checked 2026-10-22 (MT5 to
  2026-10-19, no missing days); obsolete `data/cache/dukascopy` deleted.
- **Live bot:** not running (stopped 2026-10-21); start it only on this PC, from the Live page.

## Accepted by the user (do not ask again)

- 2026-10-22: V2 setup (V2.1); team setup with Codex in shell mode (`--approve-for-me`),
  Claude 4.6 lane via agy, new split (Codex writes production code, Claude 4.6 reviews,
  Gemini research + tests); Phase 3 inventory (keep all 7 strategies incl. gap momentum,
  delete `tools/sweep_study.py` and unused data folders, merge exact duplicate helpers,
  archive ROADMAP V1 verbatim, rewrite CLAUDE.md / HANDOFF / README); graphify dropped;
  ROADMAP 5.1-5.7 stay as they are (not completed further); v2-setup merged into `main`.
- Everything accepted in V1 stays accepted: see "accepted by the user" / "rule set by the user"
  in `docs/archive/ROADMAP-v1.md` and the specs in `docs/`.

## Open (needs the user)

1. **Restart the bot** from the Live page when wanted (it writes its bars with 7.8).
2. Known issues: 4 unformatted test files (`tests/engine/test_backtest.py`,
   `test_percentage_costs.py`, `test_spread_scaling.py`, `tests/live/test_connection.py`);
   research's own DSR is per trade while the trial log is daily (align when 12.13 is ticked);
   results pages opened from the Research page lack the prop-firm card; research batches lose
   up to 8 variants on an interrupt; the chart does not auto-refresh live candles; an adopted
   position (13.5) misses the entry commission; remote branch `origin/claude/ui-polish` can go.
3. Audit findings 13.6-13.23 (open list in `docs/ROADMAP.md`) feed the V2.4 review; 13.19
   (no-wick limit fill is lookahead) first.

## Next step

**V2.4** (`Continue.Code`): golden trade lists of all 7 strategies on a fixed period, then the
Codex review module by module (core -> detectors -> engine -> risk -> analytics -> strategies
-> ui -> live) and the speed-up with a profiled real sweep. Opus on **high** for this phase.

## First prompt for the next chat

`Continue.Code`
