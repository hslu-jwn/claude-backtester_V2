# Handoff

Read first in every session; rewritten at the end of every session (CLAUDE.md › Session
protocol). Current state only; history is in git and `docs/archive/ROADMAP-v1.md`.

## Where things are (2026-10-27 evening, `Continue.Code` session; not an `End.`)

- **Repo:** V2 = `X:\Dokumente\Projekte\backtester-claude\backtester-claude_V2`, GitHub
  `hslu-jwn/claude-backtester_V2`. V1 is read-only.
- **Branches:** work on **`v2-6-research`** (pushed). `main` = merged 2026-10-27 at `da7efb9`
  (step 9 and the file-lock fix); everything after (UI, V2.6d) is **not merged** yet. Merge to
  `main` only on the user's word.
- **Tests:** ~4800 passed, 5 skipped, 1 xfailed (~8.5 min, fine: the user 2026-10-27); ruff
  clean. Golden lists re-written 2026-10-27 for the FTMO conversion adjustment (only strategy 1's
  GBPJPY trades changed, -7.97 R; all files gained the `conversion_r` column).
- **Data:** 34 FTMO symbols (+ Binance), cache rebuilt 2026-10-26; the eight step-9 symbols with
  full MT5 history and clock repair. News calendar cleaned + imputed at
  `data/news/economic_events.csv` (git-ignored; rebuild with `python -m
  backtester.tools.news_clean ../backtester-news/economic_events_2020_to_2026-10-25.csv`).
- **Demo bot RUNNING** (since 2026-10-27 16:00 UTC): `--strategy fill_probe`, 23 symbols, 0.01 %
  risk, comment prefix `fp`; logs `results/live/probe_stdout.log` and `results/live/<date>/`.
  Stop: create `results/live/STOP` (or `EMERGENCY` to close all). Started detached from a
  PowerShell (`Start-Process`); it survives this chat but not a reboot. Restarted 2026-10-27
  18:22 UTC on the fixed probe (direction by half-hour slot, `exit_at`; PID 7380) at a minute
  without open positions; the first run's log is `results/live/probe_stdout_run1.log`.
  Restart rule: only between :21 and :28 (no probe position open).
- **LibreHardwareMonitor** installed (winget), web server on 8085, the queue's temperature guard
  reads the CPU. Not started with Windows: after a reboot start it (admin prompt).
- **App:** `restart_app.bat`; dark / bright switch in the top bar (dark default); chart trade
  list sortable by pair and minimisable; live candles refresh on today's chart of a bot symbol.
- **PC quirks:** long runs log to a file; .ps1 disabled; dev preview for Claude:
  `X:\Dokumente\Projekte\backtester-claude\.claude\launch.json` (port 8052).
- **AI team:** ChatGPT Plus + Gemini Plus; Antigravity (Gemini / Claude 4.6) empty until
  ~2026-10-29. The user: use subagents for the heavy work (2026-10-27).

## New: research department (the user, 2026-10-27)

Strategy research (literature, ideas, hypotheses, specs) is now done by a separate team at
`../Research_Department/`; it hands strategies over as JSON through `../Shared_Interface/`. We keep
implementation, data, costs, validation, experiments and the one-time test. Process:
`docs/research-intake.md`; review of their contract, our requests and decisions D1-D8:
`docs/review/research-interface-review-2026-10-27.md`; our answer to them:
`../BACKTESTER_TEAM_RESPONSE.md`. `Continue.Knowledge` is retired; `Continue.Research` is blocked
until ROADMAP V2.6i (intake adapter) passes. Nothing built yet; the interface is a proposal.

## V2.6d before research (ROADMAP) — state

| Step | What | State |
|---|---|---|
| 1 | Fill-collection demo bot (`strategy/fill_probe`, not in the research registry; `live/bot.py --strategy`) | running; first report `results/fill_report/` |
| 2 | FTMO fees: per-symbol page read (`docs/review/ftmo-fees-2026-10-27.md`); NATGAS / DXY 0.0007 % per side; 0.7 % currency conversion adjustment (`conversion_r`) | done; demo deals confirm every traded symbol's commission |
| 3 | News: calendar cleaned (lost times -> day-only on the local date), 2,468 times imputed from siblings, windows High 2 / 2 min, Medium none (impact without window ignored) | done; **filter still off by default** |
| 4 | LibreHardwareMonitor + guard (fixed: urllib's `Connection: close` stalled it) | done |
| 5 | Known issues: daily DSR everywhere (old research folders re-run dev variants), live candle refresh, CLI presets = app, tests isolated from the local news file, `claude/ui-polish` already gone | done |
| — | V2.4b fill report `tools/fill_report.py` (slippage / spread / commission vs the model) | built; first run 136 fills (NY session only) |

First fill numbers (2026-10-27, n small): entries slip about 1x the model's slippage at the
median, 4x at p90; stop-loss exits mostly better than the model; BTCUSD far above (median 6.4 vs
0.5). Commissions match the model for every traded symbol (NATGAS rounds to $0 on tiny lots).

## Accepted / decided by the user (do not ask again)

- 2026-10-27: step 9 accepted, `main` merged; night-file decisions (news at candle close,
  spread-table cost exception, light pipeline Monte Carlo); trade list sort / minimise; dark /
  bright mode (+ Plotly); V2.6d plan; FTMO fees as defaults ("research all the fees and
  implement them"); news windows High 2 / 2, Medium none, day-only High times imputed; ~8 min
  full suite is fine; use subagents for heavy work.
- 2026-10-27: the fill probe stays as it is although it opens trades whose 20-min time exit
  falls into a symbol's daily break (closes rejected with `10018 market closed`, retried until
  the reopen); only enough fills for spread / slippage matter. In the fill report, treat these
  delayed time exits as outliers, not as normal exit slippage.
- Earlier: see git history of this file.

## Open (needs the user)

1. News filter on by default? (changes every backtest from 2020; golden lists re-written).
   The switch did nothing outside tests until 2026-10-27 (calendar never reached the engine;
   now wired, `news.execution_calendar`). Since 2026-10-27 the filter blocks only FTMO's
   restricted events (`docs/news.md` › FTMO restricted events; `events="impact"` = the old
   all-High scope). Golden setups 2023 (`scripts/measure_news_filter.py`): FTMO scope blocks 4
   trades in strategy 1 and 4 in strategy 3, none elsewhere (-1.2 / -1.8 R); the old all-High
   scope blocked 1-5 % (`results/news_filter_impact.md`). Opus's call for the night (the user:
   "use your own best judgement"): **leave it off by default**, because FTMO exempts the
   Challenge and Verification phases and the effect is tiny; switch it on for funded-account
   runs. The user may overrule.
2. NATGAS: done; oil / DXY: oil 0 confirmed by the deals, DXY not traded by the probe.
3. Merge `v2-6-research` into `main` (the user's word).
4. Opening-range sessions for AUS200 / HK50 (left out, 2026-10-27).
5. Research interface: contract 0.1.0 accepted by both teams 2026-10-27; next is V2.6i after
   the fill analysis (`docs/research-intake.md`).

## Night 2026-10-27/28 (Opus alone, the user's "use your own best judgement")

Summary and Opus's decisions: `docs/review/night-2026-10-28.md` (news filter wired + FTMO scope,
V2.6i intake built, deals export, cleanup). Fill analysis on 1,128 fills (NY + Asia, no London
yet): `docs/review/fill-analysis-2026-10-28.md` (proposal: keep model slippage, use measured p90
as the stressed level after London fills). All six probe positions stuck in the daily break
closed at their reopen (UKOIL last, 00:05 UTC). Bot still running.

## Next step

Let the bot collect 1-3 days of fills (Asia / London sessions too), then: export the deals
(`fill_report.deals_to_csv` via a read-only MT5 session, server offset +3 h until 2026-11-01,
then +2 h), run `python -m backtester.tools.fill_report --since 2026-10-27T16:00 --deals ...`,
and set per-symbol slippage (V2.4b) from the medians / p90 with the user; stop the bot; 12.5
reconciliation. Then research (V2.6 lanes + queue) and V2.7 portfolio. Codex review of the
2026-10-27 work (`results/ai/20261027-173807_codex_v26d-review.md`): all 7 findings fixed
(`5bb1b7d`).

## First prompt for the next chat

`Continue.Code` (read `results/fill_report/report.md` first; re-run the fill report on the new
fills; run the news off / on comparison as a script file and show the user)
