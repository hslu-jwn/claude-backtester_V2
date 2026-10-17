# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

**Several sessions share this checkout.** Before committing: `git status` / `git pull`, stage only your own files,
never `git add -A` over another session's changes. If another session ends later, it merges its section here.
At this session's end `engine/backtest.py`, `engine/costs.py`, `analytics/metrics.py` had another session's
uncommitted changes (likely 12.8 slippage) — not ours, left alone.

## Last session, strategy / live chat (2026-10-15 .. 17)
- **Working rule (user 2026-10-15):** Opus plans / manages / reviews; coding and testing by subagents (Sonnet for
  code and judgment, Haiku for mechanical work) — CLAUDE.md › Models and subagents.
- **Strategy 5 gap fade** (11.4-11.6): 2020-26 weak positive (+55 R net), out of sample 2018-19 negative -> no edge.
- **Data:** MT5 download tool (26 FTMO symbols, FX / metals M1 from 2010, indices mostly from 2021-09), scripted
  histdata download (21 symbols 2015-2021), Binance BTC / ETH futures 1m + order flow + funding from 2020; all symbols
  registered with FTMO costs. **Data split (user):** develop before **2021-09-14**, test once on MT5 data after it.
- **Costs:** FTMO % commission (metals, crypto), crypto % swap, Binance taker fee + funding, cost breakdown on the
  results page; fixed spread now **scaled with the price level** (11.14).
- **Strategy 6 opening-range breakout** (11.10, rules set by Claude with the user's go): price-only no edge;
  tick-volume filter improves 17/18 variants; out of sample (FTMO 2021-09..2026, US30/US500/NAS100/US2000, band
  0.25 ATR + volume) **+30 R / 301 trades (+0.10 R/trade), but 2024-26 only +2.7 R** -> forward-test candidate.
- **No edge:** volume filter on strategy 2 (11.15); BTC / ETH order flow real but 2-5x below fees (11.16; one
  hypothesis left: BTC 1h cvd_12 momentum, test once after the cut-off).
- **Live (7.1 ☑, 7.2 ◐):** demo test orders clean on the FTMO demo (fills confirmed from deals); risk sizer, daily
  guard (-2 %, FTMO 5 % / 10 % from the initial balance read from the first balance deal = 100k), bot
  `python -m backtester.live.bot` (starts MT5 itself, stop files results/live/STOP / EMERGENCY, paper log),
  `/live` page, Telegram (works, user's test message arrived). Spec `docs/live-trading.md`.

## Accepted by the user (do not ask again)
- Everything above ("End." 2026-10-17): ROADMAP 7.1, 11.5, 11.6, 11.8, 11.9, 11.10, 11.14, 11.15, 11.16 ☑;
  7.2 built, not yet run live.
- Earlier: knowledge chat 2026-10-16 (Phase 12 order, verdict rules, gap fade no edge); FTMO swap defaults; strategy 2
  parked, 1 paused, 3 dropped, 4 parked; tests first, small commits, no PR; spread table stays off by default.

## Open (needs the user)
1. **UI clean-up before the first live day (user 2026-10-17; change nothing before the next session asks):**
   remove the Sweep button from the top bar; Settings: chart settings collapsible and the account-connection part
   better organized; a clear separate button that opens the live-account window with all its options.
2. **First live demo day:** after the UI clean-up, press Start on `/live` (US open 15:30 Swiss time); laptop on and
   awake 15:25-22:00. The user decides how long the forward test runs (an FTMO trial is 14 days).
3. Knowledge chat's open points (12.8 slippage question, books, 11.11 / 11.12 there = stationarity, gap momentum).
- **Known issues:** ruff RUF007 in `core/series.py`; the settings panel shows cost fields only for the 5 strategy
  symbols (others need a symbol dropdown); `.vscode/` and a stray file `C…Usersjusti.claudeclaude-notify-signalsstop`
  (from a notify hook) are untracked in the repo root, not ours; empty folders `data/raw/histdata_2021_year_not_imported/`
  and `data/raw/histdata_2021_skipped/` can be deleted by the user.

## Next step
UI clean-up (open point 1): ask the user's exact wishes, then build test-first via a Sonnet subagent and show it in
the app; then the first live demo day.

## First prompt for the next chat
`Continue.` (UI clean-up, then the demo forward test) — or `Continue.Knowledge` for the research.
