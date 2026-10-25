# Handoff

Read first in every session; rewritten at the end of every session (CLAUDE.md › Session
protocol). Current state only; history is in git and `docs/archive/ROADMAP-v1.md`.

## Where things are (2026-10-25, 21:00)

- **Repo:** V2 = `X:\Dokumente\Projekte\backtester-claude\backtester-claude_V2`, GitHub
  `hslu-jwn/claude-backtester_V2`. V1 is read-only.
- **Branches:** `main` has everything up to V2.4a (trades of every strategy on the chart).
  **All work since then is on `v2-grid-merge` (pushed, not merged)**: grid merge, V2.4c, V2.4d,
  regime classifier + strategy profile, V2.5a-d. Merge it into `main` at the next `End.` (or when
  the user accepts). `v2-chart-trades` is merged.
- **Tests:** 4146 passed, 5 skipped, 1 xfailed (~5 min); ruff clean. Golden trade lists
  (`tests/golden/`, 2023) rewritten twice with the user's default decisions (TP penetration,
  intrabar M1): `python -m backtester.tools.golden --check`.
- **App:** dark redesign V2.5a-d is in; restart with `restart_app.bat` to see it.
- **PC quirks:** long runs in a terminal tab must write to a log file; PowerShell scripts (.ps1)
  are disabled (join commands with ` ; `); AI dispatch waiters must detect hangs (a Codex app
  preview kept a dispatch open for 30 h on 2026-10-24; AGENTS.md now forbids lingering processes).
- **AI team:** ChatGPT Plus + Gemini Plus only. Codex medium by default, high for engine / risk;
  briefs carry the likely rule answers; Codex runs only its own tests, Opus the full suite
  (CLAUDE.md › Models › speed rules). Usage in `docs/research-log.md`.
- **Live bot:** not running (stopped 2026-10-21). V2.4b (slippage from demo fills) needs it.

## Done since 2026-10-23 (details: ROADMAP, `docs/review/`, `docs/research-log.md`)

- Backtest audit (`docs/review/backtest-audit.md`) and the three new books merged into
  `knowledge/` (Pardo, Masters, Aronson; checklist 33-38; `docs/review/book-app-requirements.md`).
- Research runner: combined grids, grid robustness, shock days, breakdowns, sensitivity, filter
  twins, month walk-forward with WFE, daily series per variant (marked to market), Reality Check,
  PBO, effective N, Bayesian view, matched monkeys, skill vs trend (detrended), BCa bounds, log
  PF, double-bootstrap drawdown, profile block. Old grid tools deleted (reproduced exactly).
- Engine (defaults set by the user): TP / limit fill on 0.5 x spread penetration + short TP on
  the ask; same-candle SL / TP resolved from M1. Tick rounding built, **off** (decision open).
- Regime classifier + strategy profile; all 7 strategies profiled (no robust edge anywhere;
  candidates: strategy 4 on GBPJPY, the gap strategies in quiet sideways markets).

## Accepted by the user (do not ask again)

- 2026-10-22 / 23: see git history of this file; all V1 decisions; V2.5 UI decisions
  (`docs/design/ui-proposal.md`); regime spec; slippage always on (V2.4b).
- 2026-10-23: trades of every strategy on the chart (V2.4a); ChatGPT Plus + Gemini Plus, work
  placed by limits; audit before the grid merge; V2.4d in the proposed order; one pooled
  parameter set across markets; TP penetration default 0.5 x spread + short TP on the ask.
- 2026-10-24: intrabar default M1; speed rules for the AI team; the breakdown shows where each
  strategy performs best (raw and detrended) as input for combining strategies (V2.7);
  continue autonomously.

## Open (needs the user)

1. **Tick rounding default** (`results/ticks.md`; effect tiny; Opus recommends on).
2. **Spread table default** (`results/spread_table.md`; the measured FTMO median spread raises
   costs at the index open by 25-90 %; Opus recommends the median table as default for
   realism).
3. **V2.5 look:** restart the app and say ok or what to change.
4. **News:** the user gathers news data for the news-day split (V2.4c).
5. Demo bot restart for V2.4b (slippage, demo vs engine reconciliation) — the user's call.
6. Old known issues: research's own DSR per trade vs the trial log's daily DSR; chart does not
   auto-refresh live candles; remote branch `claude/ui-polish`.

## Next step

After the user's answers: V2.6 continuous research (job queue, lanes, research-based ideas
from `knowledge/ideas.md`), starting with the profile candidates as pre-registered hypotheses;
then V2.7 portfolio (combine strategies by regime).

## First prompt for the next chat

`Continue.Code`
