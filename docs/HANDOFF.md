# Handoff

Read first in every session; rewritten at the end of every session (CLAUDE.md › Session
protocol). Current state only; history is in git and `docs/archive/ROADMAP-v1.md`.

## Where things are (2026-10-23, 05:00)

- **Repo:** V2 = `X:\Dokumente\Projekte\backtester-claude\backtester-claude_V2`, GitHub
  `hslu-jwn/claude-backtester_V2` (only remote). V1 is read-only, frozen as backup.
- **Branches:** `main` = V2.1-V2.3. **`v2-review`** = V2.4 work (pushed), not merged yet.
  `v2-setup`, `v2-live` (merged into v2-review), `wip-a2a3-gemini` (superseded) can go.
- **Tests:** 3721 passed, 5 skipped, 1 xfailed (~3 min); ruff clean. Golden trade lists
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
- Everything accepted in V1 (`docs/archive/ROADMAP-v1.md`, specs in `docs/`).

## Open: questions for the user (7:30)

1. **Slippage size.** The cost presets carried slippage (~half the spread, marked "rough" in
   `engine/costs.py`) that the engine never applied; now it does (B4), and it costs e.g.
   opening_range -0.028 R per trade in 2023. Keep these values, set them from data (e.g. the
   demo bot's fills vs signal prices), or lower them? Add a slippage on/off switch in the
   settings panel like spread / commission (today it can't be switched off)?
2. **Merge `v2-review` into `main`** now (all green), or after your visual check?
3. **Visual check** of the UI fixes when convenient: replay no longer shows future exits /
   results ("Trades in view"); presets keep costs of hidden symbols.
4. **Live bot decisions by the fix (safe side, check them):** an MT5 answer `None` counts as
   "nothing found" only when `last_error()` says success; the wall-clock session exit fires
   60 s after the planned exit if no bar came; restoring a same-day daily stop after a restart
   also closes own positions again.
5. **Phase 5 (redesign):** the list of essential vs "Details" per page is in
   `docs/design/ui-proposal.md` (please look); its 6 questions: dark only or a light switch;
   who writes the one-line idea per research card; regime / parameter stability now or "-"
   first; Monte Carlo + prop pass for the chosen variant only (proposed) or all; the grey
   Risk tab (keep / hide / merge into Backtest); Backtest + Strategy as tabs below the chart
   (proposed) or popovers.
6. **Regime classifier (V2.6) spec draft** `docs/regime-classifier.md` (Kaufman efficiency
   ratio, Wilder ADX / ATR, Kaeppel volatility rank): daily candles for all strategies?
   ER (proposed) or ADX? thresholds ER 0.30 / 20 days, volatility split at the 2-year median,
   or per-symbol thresholds?
7. **AI quotas:** Antigravity's weekly quota is far too small for "Gemini does the bulk"
   (one 13-min task emptied it). Options: accept (plain Python + Codex do the bulk), or a
   paid Gemini API key for the Gemini CLI. Codex said "Upgrade to Pro" at its limit: is the
   ChatGPT account Plus or Pro?
8. Old known issues stay: 4 unformatted test files; research's own DSR per trade vs the trial
   log's daily DSR; chart does not auto-refresh live candles; remote branch `claude/ui-polish`.

## Next step

Last V2.4 item: merge the archived grid tools into the research runner (Codex). Then V2.5
(after question 5) and V2.6 (after question 6).

## First prompt for the next chat

`Continue.Code`
