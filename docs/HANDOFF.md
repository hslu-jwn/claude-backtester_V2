# Handoff

Read first in every session; rewritten at the end of every session (CLAUDE.md › Session
protocol). Current state only; history is in git and `docs/archive/ROADMAP-v1.md`.

## Where things are (2026-10-23, 05:00)

- **Repo:** V2 = `X:\Dokumente\Projekte\backtester-claude\backtester-claude_V2`, GitHub
  `hslu-jwn/claude-backtester_V2` (only remote). V1 is read-only, frozen as backup.
- **Branches:** `main` has everything up to V2.4 (v2-review merged 2026-10-23). `v2-setup`,
  `v2-live`, `v2-review` are merged; `wip-a2a3-gemini` is superseded; all can be deleted.
  Start the next phase on a new branch from `main`.
- **Tests:** 3742 passed, 5 skipped, 1 xfailed (~3 min); ruff clean. Golden trade lists
  (`tests/golden/`, 7 strategies, 2023): `python -m backtester.tools.golden --check`.
- **PC quirks:** long runs in a terminal tab must write to a log file (unread output stalls
  the process); `NODE_OPTIONS=--use-system-ca` is set (TLS interception).
- **AI team:** Codex out of quota until ~06:30 (hit at 04:25); Antigravity (Gemini + Claude
  4.6, one weekly quota) empty until ~2026-10-29. Usage in `docs/research-log.md`.
- **Live bot:** not running (stopped 2026-10-21). V2.4 changed its sizing, exits and safety
  (`docs/review/live.md`, `docs/live-trading.md` › Review fixes); start it only on this PC.

## V2.4 done (2026-10-22 / 23, details in `docs/review/`)

- Golden lists; Codex review of all 8 modules: 84 findings. Group A (no result change) fixed:
  validation, working-folder paths (13.17), analytics / risk bugs (walk-forward lookahead,
  portfolio weights, ...), strategy option bugs, UI (replay showed future results, presets lost
  costs, ...), 19 live-bot safety fixes (Opus subagent), runner exit hang.
- Group B (the user's decisions 2026-10-22) fixed with specs: FTMO daily loss on the initial
  balance; passing days played to the end + unfinished attempts shown; adaptive risk from entry
  risk only; **slippage now applied**; BE beyond TP1 keeps the SL; commission on fills; MAE at
  gap exits; strategy 1 zone lifetime + weekend swings; strategy 2 late events; doji tolerance.
  Golden net R 2023 old -> new: opening_range -6.8 -> -35.6, session_zone_sweep -310.7 ->
  -443.8 (+156 trades from the zone lifetime), no_wick -719 -> -1014, ny_index_sweep -23.6 ->
  -31.6, gap_fade -10.9 -> -16.6, trend_following 7.3 -> 6.8, gap_momentum 6.8 -> 6.4.
- Speed: profile in `docs/review/speed.md`; speed 1 + 2 done (profiled dev-period runs:
  opening_range 51.6 -> 37.5 s, ny_index_sweep 328 -> 224 s, session_zone_sweep 103 -> 61 s);
  identical trades.

## Accepted by the user (do not ask again)

- 2026-10-22: V2 setup; team (Codex shell mode, Claude 4.6 lane, split); Phase 3 inventory;
  ROADMAP 5.1-5.7 stay as they are; v2-setup merged into main; all nine B decisions
  (`docs/review/README.md` › B); continue autonomously, questions collected for 7:30.
- 2026-10-23 (answers to the 7:30 questions): slippage always on, no switch, values to be
  measured from the demo bot's fills (ROADMAP V2.4b); merge v2-review into main; live-bot
  defaults of the review fixes accepted (MT5 `None` only "empty" when last_error is success,
  60 s wall-clock exit fallback, restored daily stop closes own positions); V2.5 decisions in
  `docs/design/ui-proposal.md` (dark only, Monte Carlo / prop pass only for the chosen
  variant, Risk tab merged into Backtest, rest chosen by Opus); regime classifier spec
  accepted (`docs/regime-classifier.md`, choices left to Opus).
- Everything accepted in V1 (`docs/archive/ROADMAP-v1.md`, specs in `docs/`).

## Open (needs the user)

1. **UI fixes not visible yet:** the user saw no changes on 2026-10-23. The fixes are
   behavioural, not a new look (the look comes with V2.5): in chart replay, exits / results
   after the cursor stay hidden (overlay and "Trades in view"); loading a preset keeps the costs
   of symbols not shown in the panel. The app must be restarted on `main` to load them
   (`restart_app.bat`). Check again in the next chat; if still nothing, investigate.
2. **AI quotas:** the user checks whether the ChatGPT account is Plus or Pro, and decides
   between accepting Antigravity's small weekly quota and a paid Gemini API key.
3. Old known issues: 4 unformatted test files; research's own DSR per trade vs the trial log's
   daily DSR; chart does not auto-refresh live candles; remote branch `claude/ui-polish`.

## Next step

`Continue.Code`: (1) last V2.4 item: merge the archived grid tools into the research runner
(Codex); (2) V2.4b slippage from the demo fills (needs demo trades; the bot is not running);
(3) V2.5 app redesign per `docs/design/ui-proposal.md`. Then `Continue.Research` for V2.6
(regime classifier first, spec accepted) and V2.7.

## First prompt for the next chat

`Continue.Code`
