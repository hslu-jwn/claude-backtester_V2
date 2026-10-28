# Handoff

Read first in every session; rewritten at the end of every session (CLAUDE.md › Session
protocol). Current state only; history is in git and `docs/archive/ROADMAP-v1.md`.

## Where things are (2026-10-28 morning, after `End.`)

- **Repo:** V2 = `X:\Dokumente\Projekte\backtester-claude\backtester-claude_V2`, GitHub
  `hslu-jwn/claude-backtester_V2`. V1 is read-only.
- **Branches:** work on **`v2-6-research`** (pushed). `main` = merged 2026-10-27 at `da7efb9`;
  everything after (UI, V2.6d, news, V2.6i) is **not merged** yet. Merge to `main` only on the
  user's word.
- **Tests:** ~4960 passed, 7 skipped, 1 xfailed (~9.5 min, fine); ruff clean. Golden lists
  unchanged since 2026-10-27 (news filter is off by default).
- **Data:** 34 FTMO symbols (+ Binance), cache rebuilt 2026-10-26. News calendar at
  `data/news/economic_events.csv` (git-ignored; rebuild with `python -m
  backtester.tools.news_clean ../backtester-news/economic_events_2020_to_2026-10-25.csv`).
- **Demo bot RUNNING** (since 2026-10-27 16:00 UTC, restarted 18:22 UTC, PID 7380/12116):
  `--strategy fill_probe`, 23 symbols, 0.01 % risk, prefix `fp`; log
  `results/live/probe_stdout.log`. Stop: create `results/live/STOP` (`EMERGENCY` closes all).
  Survives the chat, not a reboot. Restart only between :21 and :28. Probe trades whose 20-min
  exit falls into a daily break are retried until the reopen (the user: leave it).
- **LibreHardwareMonitor** (port 8085) feeds the queue's temperature guard; start it after a
  reboot (admin prompt).
- **App:** `restart_app.bat`; dev preview for Claude: `..\.claude\launch.json` (port 8052).
- **PC quirks:** long runs log to a file; .ps1 disabled; no backticks in inline PowerShell.
- **AI team:** ChatGPT Plus (Codex) + Gemini Plus; Antigravity (Gemini / Claude 4.6) empty until
  ~2026-10-29, so Opus reviewed Codex's code. The user: use subagents for heavy work.

## Research department (since 2026-10-27)

Strategy research is a separate team at `../Research_Department/`; strategies arrive as JSON in
`../Shared_Interface/queue/` (contract 0.1.0, accepted by both teams 2026-10-27). We keep
implementation, data, costs, validation, experiments and the one-time test. Process
`docs/research-intake.md`; tool `python -m backtester.tools.intake
validate|claim|recover|reject|progress|result|finish` (V2.6i i1-i7 built and accepted
2026-10-28). Focus: **day trading** (the user). `Continue.Knowledge` is retired;
`Continue.Research` now works on queue submissions. Queue empty so far; the two research
drafts are stopless / monthly (would be `UNSUPPORTED_STRATEGY_TYPE`). We told Research on
2026-10-28 that we are ready for a first R-type day-trading pilot. Gemini guide for them:
`../RESEARCH_TEAM_GEMINI_GUIDE.md`.

## State of the current work

| Item | State |
|---|---|
| V2.4b fill analysis | 1,128 fills NY + Asia (`docs/review/fill-analysis-2026-10-28.md`); median slippage at or below the model, p90 ~3x; **no London fills yet** |
| V2.4e news filter | wired into every run; FTMO restricted-event scope; **off by default** (accepted) |
| V2.6i intake | i1-i7 done; i8 = first real pilot when Research submits |
| Deals export | `scripts/export_deals.py <since> --offset-hours 3` (+2 h from 2026-11-01), read-only |

## Accepted / decided by the user (do not ask again)

- 2026-10-28 (`End.`): everything of the night 2026-10-27/28 incl. Opus's decisions
  (`docs/review/night-2026-10-28.md`): news filter off by default, FTMO scope default, V2.6i
  built before the fill analysis, empty text settings allowed, no one-time test spent.
- 2026-10-28 (midday): do not build the p90 stressed costs yet; the bot keeps running and the
  user comes back to it later. Fill report re-run at 10:35 UTC (1,511 fills, 339 London);
  brief ready in `briefs/v24b-p90-stress.md`, not dispatched.
- 2026-10-28: slippage (V2.4b): keep the model slippage as default; after London fills, the
  measured p90 per symbol becomes the stressed cost level (instead of costs x 1.5).
- 2026-10-27: research department split, decisions D1-D8
  (`docs/review/research-interface-review-2026-10-27.md` › 3), day-trading focus, fill probe
  left as it is, FTMO fees as defaults, news windows High 2 / 2, Medium none.
- Earlier: see git history of this file.

## Open (needs the user)

1. One-time MT5 test of the three pre-registered V2 hypotheses (strategy 4 on GBPJPY; gap fade
   and gap momentum in quiet sideways markets): only on the user's go.
2. Merge `v2-6-research` into `main` (the user's word).
3. Opening-range sessions for AUS200 / HK50 (left out, 2026-10-27).

## Next step

After the London session has traded (from 2026-10-28 ~08:00 local, one more day is best):
`scripts/export_deals.py 2026-10-27T16:00 --offset-hours 3`, then `python -m
backtester.tools.fill_report --since 2026-10-27T16:00 --deals results/fill_report/deals.csv`;
build the accepted V2.4b part (measured p90 per symbol as the stressed cost level in the
robustness report, test-first); stop the bot (`results/live/STOP`, at a minute without probe
positions); 12.5 demo reconciliation. Watch `../Shared_Interface/queue/pending/` for the first
submission (V2.6i i8). Then research (V2.6 lanes + queue) and V2.7 portfolio.

## First prompt for the next chat

`Continue.Code` (re-run the fill report with the London fills, then build the V2.4b p90 stressed
costs; check the shared queue for a first submission)
