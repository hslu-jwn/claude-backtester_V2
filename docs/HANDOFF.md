# Handoff

Read first in every session; rewritten at the end of every session (CLAUDE.md › Session
protocol). Current state only; history is in git and `docs/archive/ROADMAP-v1.md`.

## Where things are (2026-10-27, End of session)

- **Repo:** V2 = `X:\Dokumente\Projekte\backtester-claude\backtester-claude_V2`, GitHub
  `hslu-jwn/claude-backtester_V2`. V1 is read-only.
- **Branches:** all V2.6 / V2.7 work is on **`v2-6-research`** (pushed, **not merged to
  `main`**). `main` = state of 2026-10-26 `End.`. `docs/v2.4e-economic-calendar` is contained in
  `v2-6-research`. Merge to `main` only on the user's word.
- **Tests:** ~4620 passed, 5 skipped, 1 xfailed (~7.5 min); ruff clean; golden lists (2023)
  identical since the 2026-10-26 default change (`python -m backtester.tools.golden --check`).
- **Data:** cache rebuilt 2026-10-26 (V2.6 step 2: histdata clock, MT5 server clock per date,
  wrong instruments dropped). Backups moved to `..\old\v26b-cache-backups\` (user: move, not delete).
- **Queue:** `python -m backtester.tools.queue status` (from the V2 folder). An end-to-end
  pipeline run of `research/grids/orb_example.toml` was still in its Monte Carlo step at 07:45
  (started 00:56); let it finish or `queue stop` (graceful). LibreHardwareMonitor not installed
  yet (temperature guard shows "no sensor").
- **App:** `restart_app.bat`; new: Portfolio tab, queue panel + pipeline state on the Research
  page, review mode / trade inspection on the Chart page.
- **PC quirks:** long runs in a terminal must log to a file; .ps1 disabled; the dev preview for
  Claude is `X:\Dokumente\Projekte\backtester-claude\.claude\launch.json` (port 8052).
- **AI team:** ChatGPT Plus + Gemini Plus. Codex hit its limit 2026-10-26 18:14-21:14 (Sonnet
  subagents built step 3 meanwhile); Antigravity (Gemini / Claude 4.6) empty until ~2026-10-29.
  The user: no heavy building by Sonnet subagents; delegate mechanical work.
- **Live bot:** not running (stopped 2026-10-21). Step 6 waits for the user.

## Built 2026-10-26 / 27 (details: ROADMAP › V2.6 build order, `docs/review/night-2026-10-27.md`)

| Step | What | State |
|---|---|---|
| 1 | Job queue, temperature guard, file locks | accepted |
| 2 | Data fixes 13.12-13.16, 13.18; cache rebuilt | accepted |
| 3 | Research pipeline, queue panel, lanes | accepted |
| 4 | V2.7 Portfolio tab (search, top-10 Monte Carlo, one-time test CLI) | accepted |
| 5 | Review mode, trade inspection, heat map, strong-move dropdown, 4.3 items | accepted (2026-10-27 `End.`) |
| 6 | Live (demo bot, V2.4b, 12.5) | skipped (user) |
| 7 | V2.4e news calendar on synthetic data, filter default off | accepted (2026-10-27 `End.`) |
| 8 | Full check: Codex review (`docs/review/v26-full-check.md`), fixes 1-6, `--help` on Windows, live job logs | accepted (2026-10-27 `End.`) |
| 9 | More symbols: proposal list `docs/review/symbol-proposal-2026-10-27.md` | **waiting for the user's pick** |

## Accepted by the user (do not ask again)

- 2026-10-22 / 23 / 24: see git history of this file; all V1 decisions; V2.5 UI decisions.
- 2026-10-27 (`End.`): steps 5, 7, 8 of the V2.6 build order accepted.
- 2026-10-26: everything up to V2.5 accepted (`End.`); tick rounding on + median spread table
  default (spread re-checked after demo trading); build and test the whole app first, research
  after; V2.6 build order; queue first, LibreHardwareMonitor guard; pre-registered hypotheses
  (strategy 4 on GBPJPY, gap strategies in quiet sideways markets) tested once later; MT5 server
  clock per date through 2021-09-13, sparse days filled by histdata only before 2021-09-14;
  wrong instruments dropped; app may start the queue runner; one-time MT5 test CLI only; lanes
  next to V2; portfolio: development only, equal weights, own tab, 2-4 members, MC top 10;
  review mode + trade inspection for every strategy, heat map on the card, 4.3 items picked;
  steps 1-4 accepted; Opus may use `../backtester-news/` for V2.4e; night plan (go through the
  steps, skip step 6, step 7 on synthetic data, step 8 fix small / list big, step 9 list only).

## Open (needs the user) — the morning list is `docs/review/night-2026-10-27.md`

1. Steps 5, 7, 8 accepted at `End.` 2026-10-27; first in the next chat: merge `v2-6-research`
   into `main` (the user's word).
2. Decisions listed in the night file: news blackout timing (candle close vs fill time) and
   window sizes; **spread table in the development period** (full check finding 7: 2015-2020
   indices use 2021 values); more symbols (pick from the proposal); pipeline Monte Carlo speed
   (one core, 3+ h for a small grid).
3. Install LibreHardwareMonitor (Options › Remote Web Server, port 8085).
4. News: the regenerated calendar file -> `data/news/economic_events.csv`.
5. Demo bot restart for step 6 (V2.4b slippage, 12.5 reconciliation) — the user's call.
7. Old known issues: research's own DSR per trade vs the trial log's daily DSR; chart does not
   auto-refresh live candles; remote branch `claude/ui-polish`; CLI named-preset restrictions
   differ slightly from the app's.

## Next step

The user's morning check and decisions (list above), then: more symbols (step 9 download),
step 6 when the user restarts the demo bot, the regenerated news file into V2.4e; after that
intensive research (V2.6 lanes + queue) and V2.7 portfolio on real research results.

## First prompt for the next chat

`Continue.Code` (read `docs/review/night-2026-10-27.md` first)
