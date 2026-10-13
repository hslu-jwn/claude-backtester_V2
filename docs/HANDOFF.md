# Handoff

Read first in every session, rewritten by Claude at the end of every session (see CLAUDE.md ›
Session protocol). The user does no file work. Newest state only; history is in git and the ROADMAP.

## Branch
`claude/happy-johnson-l6dmz2` (the session's branch; use the one the session prompt names if different)

## Last session (2026-10-13): liquidity sweep rework and research
- **Tools:** `restart_app.bat` (project folder; kills port 8050 and starts the app from `.venv`; fixed for the
  German Windows `netstat` and the venv's activate script); `python -m backtester.tools.sweep_study`
  (sweep outcome per rule, ~35,000 sweeps, with / against the 4h trend, NY windows, per year);
  `tools/strategy2_sweep_grid.py` (full strategy-2 runs per sweep rule); `tools/strategy2_explore.py`
  (entry time, AM / PM, window size, 9 exit structures; `collect` per symbol and variant, then `report`);
  `analytics/sweep_quality.py`.
- **Built, all off by default (nothing changed for backtests):** sweep detector options `equal_tolerance_atr`,
  `lookback_swings`, `two_closes_cancel` + `cancel_closes` (2 / 3) + `cancel_wick_first`, `bos_before_top`;
  doji as a share of the candle's own range (`SwingConfig.doji_range_share`, Settings › Detectors); the same sweep
  options in strategy 2's config (Settings › Entry); a temporary **Sweep** menu in the chart toolbar.
- **Results (spec: `confluences.md` › Liquidity sweep, `strategy-ny-indices.md` › Backtest options; ROADMAP 8.2.5):**
  after a sweep + BOS price is a coin flip on every rule and symbol, with or without the 4h / 15m trend;
  strategy 2 (NAS100 + US500) 2023-26: base 879 trades −3.4 R net (+42.7 gross); every sweep, window and exit
  variant is inside the ±45 R noise; the best-looking ones (window 30 min before to 90 after +39 R, breakout 2
  closes +53 R) were **negative on 2020-22** (−21 R, −34 R). No rule adopted. Costs are 0.055-0.075 R per trade.
- **Why no sweep appeared on a 4h scene (NAS100 2026-06-09 12:00):** the BOS rule "only against the trend" made
  the close below the swing low a with-trend break; the user accepted it. The user's doji complaint was the fixed
  price threshold being tuned to 5m (now the range-share option).
- Checks: 1030 tests pass; ruff clean except the old RUF007 in `core/series.py`.

## Accepted by the user (do not ask again)
- The ROADMAP order and the cleanup backlog; C.1-C.4 and 8.6a done.
- Tests first, small commits on the session branch, no PR unless asked.
- Strategy 1 is paused. A BOS in a downtrend with the trend is no BOS, so a sweep without a BOS is no sweep.
- The with-trend sweep scene on 4h (no sweep) is fine; defaults of all new options stay off.
- "End." accepted everything built in this session as it is (options off, research tools in `tools/`).

## Open (needs the user)
- **Next idea**, the user chooses: (1) cost-aware filter (skip entries where spread + commission is a large share
  of the stop), (2) new edge sources tested with the study framework (session open range breakout, previous
  day / week high-low sweeps, regime filters), (3) the user's own discretionary rules turned into tests one by one.
  My recommendation: 1 and 2 in parallel.
- Whether to keep the temporary Sweep menu on the chart or remove it (defaults unchanged either way).
- Doji share: the user said "doji needs rework"; the option exists (0.10 suggested) but is off. He has not set it.
- Parked: structure cut ("highs before the last bearish BOS no longer have to be taken"), until a real case shows
  an old very high high blocking a sweep.
- ROADMAP 8.3 / 8.4 window settings and best-time tag removal still wait for his go; 8.6b / 8.6c / 6.1 as before.

## Next step (suggested)
Ask which of the three ideas above to start with; run it with `sweep_study` / `strategy2_explore` style tests and
check any finding on data not used to find it (2020-22 vs 2023-26) before trusting it.

## First prompt for the next chat
`Continue.`
