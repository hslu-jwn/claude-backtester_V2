# Handoff

Read first in every session; rewritten at the end of every session (CLAUDE.md › Session
protocol). Current state only; history is in git and `docs/archive/ROADMAP-v1.md`.

## Where things are (2026-10-28 morning, after `End.`)

- **Repo:** V2 = `X:\Dokumente\Projekte\backtester-claude\backtester-claude_V2`, GitHub
  `hslu-jwn/claude-backtester_V2`. V1 is read-only.
- **Branches:** work on **`v2-6-research`** (pushed). `main` = merged 2026-10-27 at `da7efb9`;
  everything after (UI, V2.6d, news, V2.6i) is **not merged** yet. Merge to `main` only on the
  user's word.
- **Tests (2026-11-02):** 5070 passed, 7 skipped, 1 xfailed (16 min); ruff clean. Golden lists
  unchanged since 2026-10-27 (news filter is off by default).
- **Data:** 34 FTMO symbols (+ Binance), cache rebuilt 2026-10-26. News calendar at
  `data/news/economic_events.csv` (git-ignored; rebuild with `python -m
  backtester.tools.news_clean ../backtester-news/economic_events_2020_to_2026-10-25.csv`).
- **Demo bot STOPPED** by the user (last log line 2026-10-31 01:00 local): the FTMO demo
  challenge failed at max drawdown. The fill-probe run (`--strategy fill_probe`, 23 symbols,
  0.01 % risk, prefix `fp`) ran 2026-10-27..31; log `results/live/probe_stdout.log`. Its
  `status.json` was never written (R1, fixed 2026-11-02), so the Live page showed "not
  running" throughout. **New account 2026-11-02:** the user opened a new FTMO 14-day trial
  (logged in in MT5) for more fill collection and 12.5 reconciliation; the old account's deals
  are not in it (the bot's own `paper.csv` / `trades.csv` keep every fill). A bot restart is
  the user's call; restart only between :21 and :28. Stop: `results/live/STOP` (`EMERGENCY`
  closes all).
- **Fill report 2026-11-02:** `results/fill_report_2026-11-02/` (5,512 fills 2026-10-27..31,
  23 symbols, 1,502 London; commission only from the 10-27/28 deals file).
- **Finalization (V2.8, plan accepted 2026-11-02):** audit and baselines in
  `docs/review/finalization-audit-2026-11-02.md`; the ~30 s UI start is the chart page
  rendering all 10,397 trades of the newest run (U1).
- **LibreHardwareMonitor** (port 8085) feeds the queue's temperature guard; start it after a
  reboot (admin prompt).
- **App:** `restart_app.bat`; dev preview for Claude: `..\.claude\launch.json` (port 8052).
- **PC quirks:** long runs log to a file; .ps1 disabled; no backticks in inline PowerShell.
- **AI team (session 2026-11-02, accepted by the user):** one routing table,
  `docs/agent-routing.md` (local tools -> free local Ollama -> Codex terra / sol -> Opus only
  for escalation; no cross-review chain). `ai_dispatch` lanes: `local` (Ollama), hosted free
  APIs `groq`, `openrouter` (`:free` only), `gemini-api` (all probed OK), `deepseek` (key OK,
  no balance, needs `--allow-paid`); GitHub Models off (endpoint answers "OK" to everything);
  no Astra (no access). `ai_dispatch stats` sums usage. Keys: Windows Credential Manager,
  `<provider>@backtester-ai`. `Continue.Research` procedure is now the `continue-research`
  skill. Baseline before the change: tag `pre-agent-migration-2026-11-02`.
- **Not checked 2026-11-02:** demo bot and data state above are from 2026-10-28; check before
  relying on them. Open: top up DeepSeek to enable it.

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
| V2.6i intake | i1-i7 done; i8 pilot FX_LONDON_FIX_REV run 2026-10-28: all 9 variants negative, result envelope sent, **rejected by the user 2026-10-29**, moved to `queue/rejected/`, Research told (`docs/research-log.md`) |
| Open questions for Research | 0 (inbox 2026-10-29; replies sent to the result review, the H1-shock preflight and the study-route note) |
| Next builds | V2.6l result envelope per cell + integrity check; V2.6j and V2.6k built 2026-10-29; V2.4c checks #2 #6 #13 built, not accepted |
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

V2.8 in the ROADMAP order: R1 and T1 built; U1 (chart trade list in pages of 100) accepted by
the user 2026-11-02; re-measure the chart start on an idle PC in step (4); next V2.4b p90
(below), 12.5, V2.6l, V2.4e.

Older note (2026-10-28): after the London session has traded (from 2026-10-28 ~08:00 local, one more day is best):
`scripts/export_deals.py 2026-10-27T16:00 --offset-hours 3`, then `python -m
backtester.tools.fill_report --since 2026-10-27T16:00 --deals results/fill_report/deals.csv`;
build the accepted V2.4b part (measured p90 per symbol as the stressed cost level in the
robustness report, test-first); stop the bot (`results/live/STOP`, at a minute without probe
positions); 12.5 demo reconciliation. Watch `../Shared_Interface/queue/pending/` for the first
submission (V2.6i i8). Then research (V2.6 lanes + queue) and V2.7 portfolio.

## First prompt for the next chat

`Continue.Code` (re-run the fill report with the London fills, then build the V2.4b p90 stressed
costs; check the shared queue for a first submission)
