# Roadmap

What to build next and its status. Step IDs (e.g. `V2.4.1`) are how the user refers to them.
Status: ☐ open · ◐ in progress · ☑ done (update this file when a step is finished).

**History:** phases 0-13 of V1, with every decision the user accepted, are archived verbatim in
`docs/archive/ROADMAP-v1.md` (read it there; the IDs below point to it).

---

## Open from V1

Status as written in V1. Note: 5.1-5.7 are still marked open there, but `risk/` (sizer,
account simulator, Monte Carlo, risk sweep, risk page, prop-firm card, adaptive risk) was
built in V1 (V1 status table). **Decision (user, 2026-10-22): 5.1-5.7 stay as they are**
(not completed further, not ticked); the parts in use (Monte Carlo, prop-firm pass
probability, adaptive risk) are checked in the V2.4 review. Phase 13 are
findings of the 2026-10-19 audit, input for the V2.4 review.

- ☐ **3.3d Review mode** (Phase 3)
- ☐ **3.5 Session view** (Phase 3)
- ☐ **3.7 Cross-check with the manual backtest** (Phase 3)
- ☐ **4.3 UI layout and look review** (Phase 4)
- ☐ **5.1 RiskConfig + PositionSizer** (Phase 5)
- ☐ **5.2 AccountSimulator** (Phase 5)
- ☐ **5.3 Monte Carlo** (Phase 5)
- ☐ **5.4 Risk sweep** (Phase 5)
- ☐ **5.5 Risk page in the UI** (Phase 5)
- ☐ **5.6 Prop-firm field** (Phase 5)
- ☐ **5.7 Adaptive risk for prop-firm accounts** (Phase 5)
- ☐ **11.3 Time-of-day drift by session for XAUUSD / GBPUSD / GBPJPY** (Phase 11)
- ☐ **12.2 Intrabar order from M1** (Phase 12)
- ☐ **12.4 Parameter heat map** (Phase 12)
- ☐ **12.5 Demo reconciliation** (Phase 12)
- ☐ **12.6 Stressed fills** (Phase 12)
- ☑ **12.8 Engine slippage** (Phase 12) — fixed in V2.4 (B4), 2026-10-23
- ☐ **12.9 Portfolio tool** (Phase 12)
- ☐ **12.11 Bayesian report** (Phase 12)
- ☐ **12.13 DSR on daily R** (Phase 12)
- ☑ **13.6 Closed-bar check on server time** (Phase 13) — fixed in V2.4 (live #1), 2026-10-23
- ☑ **13.7 Sizing on the live price** (Phase 13) — fixed in V2.4 (live #7), 2026-10-23
- ☑ **13.8 Wall-clock fallback exit** (Phase 13) — fixed in V2.4 (live #8), 2026-10-23
- ☑ **13.9 Validate CLI risk** (Phase 13) — fixed in V2.4 (live #18), 2026-10-23
- ☐ **13.12 histdata clock 2015-2018** (Phase 13)
- ☐ **13.13 GER40 histdata changes instrument on 2020-06-15** (Phase 13)
- ☐ **13.14 MT5 cache before 2020** (Phase 13)
- ☐ **13.15 One-day holes on 1 January** (Phase 13)
- ☐ **13.16 MT5 downloader swallows errors** (Phase 13)
- ☑ **13.17 Paths relative to the working folder** (Phase 13) — fixed in V2.4 (A2), 2026-10-23
- ☐ **13.18 Output folders** (Phase 13)
- ☑ **13.19 no_wick limit fill is lookahead** (Phase 13) — refuted by two V2.4 reviews (pending limits precede the fill candle; now enforced by the engine, A1), 2026-10-23
- ☑ **13.20 Kind C random fills never slip time exits** (Phase 13) — fixed in V2.4 (B4), 2026-10-23
- ☑ **13.21 Parallel runner progress race** (Phase 13) — fixed in V2.4 (A5), 2026-10-23
- ☐ **13.22 `tests/tools/test_s2_volume_ab.py`** (Phase 13)
- ☑ **13.23 Monte Carlo FTMO pass rate** (Phase 13) — fixed in V2.4 (B2), 2026-10-23

## V2 phases (user, 2026-10-22)

- ☑ **V2.1 Set up this PC** (tools, venv, data check, baseline tests).
- ☑ **V2.2 Team setup** (AGENTS.md, Codex / Claude 4.6 / Gemini through `tools/ai_dispatch.py`).
- ☑ **V2.3 Move to V2 and clean up** (inventory accepted by the user 2026-10-22).
- ◐ **V2.4 Full Codex review and speed-up** (2026-10-23: golden lists, review of all 8
  modules (84 findings, `docs/review/`), groups A + B fixed, speed 1 + 2 (partial) done;
  open: rest of speed 2, the archived grid tools merge, the user's visual check of the UI
  fixes): golden trade lists of all strategies first; review
  core -> detectors -> engine -> risk -> analytics -> strategies -> ui -> live (correctness,
  then speed, then cleanup); profile a real sweep, optimize with before/after numbers and
  identical golden trade lists. Includes merging the archived grid tools into the research
  runner.
- ☐ **V2.4b Slippage from the demo fills** (rule set by the user, 2026-10-23): slippage is
  always applied, no on/off switch (most realistic scenario); measure it per symbol from the
  demo bot's fills (fill price vs the order's signal / stop price, `results/live/`) and set the
  `SymbolCosts.slippage` defaults from it; until then the current presets (~half the spread)
  stay.
- ☐ **V2.5 App redesign** (decisions 2026-10-23 in `docs/design/ui-proposal.md`) after `docs/design/app-v2.png`: dark trading-terminal look, essential
  vs "Details" per page (list to the user first), research page as one vertical list of
  cards, Fast mode (headless) vs Visual mode with identical trade lists.
- ☐ **V2.6 Continuous research:** research-based strategies only, job queue (≈8 workers,
  temperature guard, resumable), 3 lanes in worktrees, Monte Carlo, parameter stability,
  regime breakdown (regime classifier in `analytics/`, spec first, user decides), warning flags,
  research cards, `docs/research-log.md`.
- ☐ **V2.7 Portfolio:** combine strategies that balance each other by regime; combined equity,
  correlation of daily R, Monte Carlo prop-firm pass probability, leave-one-out; the user picks.
