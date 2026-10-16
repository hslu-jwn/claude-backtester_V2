# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

**Two sessions share this checkout (2026-10-14/15).** Besides this one, a second session works on Phase 6 / 11
(robustness report 6.4, time splits 6.5, noise study 11.1; see their ROADMAP entries and commits). Before committing:
`git status` / `git pull`, stage only your own files, never `git add -A` over the other session's changes. If that
session ends after this one, it may rewrite this file: merge both sections instead of overwriting.

## Last session (2026-10-14/15, strategy 2 costs and filters): swap defaults, trend filter, rollover close, cost filter
- **Swap defaults:** FTMO's MT5 rates of 2026-10-14 are now the default `SymbolCosts` (user, 2026-10-14;
  risk-management.md › Costs). Net results of every strategy now include swap.
- **Strategy 2 trend filter** (user: keep strategy 4 as a filter): `NyIndexSweepConfig.trend_filter`, off by default;
  signals only in the direction of the last SMA ± band x ATR cross (shared class `SmaBandCross` in
  `strategy/trend_following/indicators.py`, strategy 4 uses it too).
- **Close before the rollover** (user: test it): `close_before_rollover`, off by default, closes at **16:15 ET**
  (`rollover_close_minutes` 45) because the histdata index feed has no candles 16:15-18:00 ET. Rollover time constants
  moved to `sessions.py` (layer rule: strategies may not import the engine).
- **Cost filter** (user: build it): `CostConfig.max_cost_r`, off by default; the engine skips an order whose spread +
  commission is above that many R of the stop and calls `Strategy.on_order_skipped` (strategy 2: no trade counted,
  setup stays open; strategy 4: flat). Strategies 1 and 3 have no hook (noted in the spec).
- **Results (ROADMAP 10.5):** strategy 2, 2020-26 with swap: -135 R; best combination close 16:15 + 15m filter -17 R,
  close + cost 0.10 -50 R. Swap was -74 R (654 trades held overnight). No edge -> **strategy 2 parked by the user
  2026-10-15**. CSVs: `results/s2_trend_filter/` (git-ignored).
- 1348 tests pass.

## Last session, knowledge chat (2026-10-15/16): backtest frameworks, Monte Carlo report, gap fade verdict
- **Framework lessons** (HftBacktest, VectorBT, NautilusTrader, prediction-market backtesting; "Kalshi Market" repo
  not found, dropped): `knowledge/topics/backtest-frameworks.md`, checklist lines 14a-c / 21a, ideas T-02..T-07,
  ROADMAP Phase 12.
- **Monte Carlo report** (12.7 ☑, spec `risk-management.md › Monte Carlo report`):
  `python -m backtester.tools.monte_carlo NAS100 US500 --start .. --end .. --strategy gap_fade` ->
  `results/monte_carlo/<..>/report.html` + `summary.json`. Verdict EDGE / WEAK / NO EDGE from 6 checks (t >= 2,
  random entries >= 95th pct, both halves of the run's period, costs x1.5, without best trade, random-fill median);
  fan chart; account numbers at 0.5 / 1 / 1.5 % on 100k; FTMO 2-Step pass probability; kinds A day reshuffle
  (`risk/monte_carlo.py`), B random entries (`analytics/random_baseline.py`, gap fade `mode="follow"`),
  C random fills (`analytics/random_fills.py`), D random price paths (`data/random_walk.py`, slow: ~9 s per path).
- **Walk-forward** (12.3 ☑ `analytics/walk_forward.py`; 11.7 ☑ `tools/gap_fade_walk_forward.py`, 125 min).
- **Gap fade: no edge** (I-39). Walk-forward 2019-26 +0.6 R / 1423 trades, default +22.6 R / 2752; both NO EDGE;
  2020-21 alone WEAK (t 1.08). Random slippage kills it (small stops).
- **Found:** the engine never applies `SymbolCosts.slippage` -> every backtest so far is too optimistic (12.8 filed).
- 1832 tests pass (without the other session's `tests/tools/test_orb_grid.py`); ruff: only the old RUF007.

## Accepted by the user (do not ask again)
- Knowledge chat 2026-10-16 ("End."): everything built, ROADMAP 11.7 / 12.1 / 12.3 / 12.7 ☑; verdict rules (n/a
  checks neutral, halves at mid-period); Monte Carlo all four kinds in the report, risks side by side; gap fade no
  edge; infrastructure first, then find / combine edges (order in ROADMAP Phase 12).
- Strategy chat 2026-10-15: FTMO swap rates as defaults; trend filter code stays (off); strategy 2 parked.
- Earlier: tests first, small commits, no PR; strategy 1 paused, strategy 3 dropped, strategy 4 parked; sweep option
  defaults stay off; temporary Sweep menu stays.

## Open (needs the user)
1. **Books:** the user adds Carver, López de Prado, Chan, Davey to `00_Literature/Trading`; then add them per
   `knowledge/README.md` (focus: combining edges, meta-labelling, deflated Sharpe).
2. **12.8 engine slippage:** do time / signal exits count as market fills (slipped)? Ask before building.
3. Older open points of the knowledge chat: spread table as default (and from which year), volume A/B (I-44),
   11.3 time-of-day drift keep or drop.
4. **Opening-range breakout (11.10, strategy 6)** is another session's work in this checkout (`tools/orb_grid.py`,
   `tests/tools/test_orb_grid.py` uncommitted at this session's end); leave its files alone.
5. **Login:** update the MT5 login in Settings ⚙ → Trading (the user does this; never ask for credentials in chat).
- **Known issues:** ruff RUF007 in `core/series.py`; the FTMO daily-loss check counts an overnight trade only from
  its exit day (spec note); Monte Carlo kind D is slow (37 min for 2 symbols x 20 paths); strategy 2's `decisions`
  list shows cost-filtered orders as taken.

## Next step (suggested)
12.8 engine slippage (spec question 2 first), then 12.2, 12.9, 6.1 (ROADMAP Phase 12 order).

## First prompt for the next chat
`Continue.` (infrastructure, 12.8 next) or `Continue.Knowledge` once the new books are in `00_Literature/Trading`.
