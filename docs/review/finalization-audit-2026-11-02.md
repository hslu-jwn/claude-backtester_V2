# Finalization audit (2026-11-02)

Read-only audit by Opus on `v2-6-research` at `32eba99`; plan accepted by the user 2026-11-02
(ROADMAP V2.8). Measurements with file writes blocked (scratch scripts outside the repo).

## Baselines

**UI** (in-app browser, warm OS cache, server on this PC):

| Stage | Result |
|---|---|
| `import backtester.ui.app` | 1.5 s |
| `create_app()` (builds every page for `validation_layout`) | 2.2 s |
| Chart page `page.children` | 1.6-1.8 s server, **6.4 MB**, 43,488 components (10,671 buttons) |
| Chart page in the browser | 19 s download, not drawn after 200 s (the user sees ~30 s in Chrome) |
| Same, newest-run trade list stubbed | canvas 2.2 s, usable 2.5 s, 289 KB |
| Results page, 10,397-trade run | 0.48 s build, 2.6 MB, usable ~1.9 s |
| Research page | 0.9 s build, 1.3 MB, then the cards again in `rr-cards` (1.15 MB) |

Cause: `ui/pages/chart.py` `newest_trade_rows` renders every trade of the newest saved run into
the chart page; since the London-fix pilot (2026-10-28) that run has 10,397 trades, each a
pattern-matching button watched by an `ALL` click callback.

**Backtests** (`run_backtests`, workers=1, 2019-01-01..2021-09-13, defaults; cProfile in brackets,
V2.4 speed-2 report after the slash): opening_range US500+NAS100 14.8 s (38.5 / 37.5 s),
session_zone_sweep XAUUSD 26.3 s (69.0 / 61.0 s), ny_index_sweep NAS100 94.2 s (243 / 224 s).
No regression; time spread over detectors and views, candle loading 20-35 % of short runs. No
backend change planned.

**Golden lists:** `tools.golden --check` 9/9 identical (2 min 18 s). Ruff clean. Suite: 16 min
on 2026-11-02 (9.5 min on 2026-10-28; ~8 min accepted 2026-10-27).

## Confirmed issues

1. **R1 bot status:** `live/status.py` `build_status` used opening-range-only parts
   (`strategy.sessions`, `setup_state`); `Bot.publish` suppressed every exception, so the
   fill-probe run 2026-10-27..31 never wrote `results/live/status.json` (last heartbeat
   2026-10-21): nav and Live page showed "Bot not running", Telegram `/status` was stale.
   The bot itself was stopped by the user (FTMO demo challenge failed at max drawdown).
2. **U1 chart trade list:** see the cause above.
3. **Docs drift:** HANDOFF said the bot was running; ROADMAP showed V2.6j / V2.6k open though
   built 2026-10-29; the `bt-live` worktree (`v2-live`) is 159 commits behind with no own commits.

Not issues (settled or covered): the 84 V2.4 review findings and full-check findings 1-6 are
fixed; full-check finding 7 decided by the user (option a); 5.1-5.7 stay; 3.7 / 12.11 / 12.13
dropped.

## Side effect of the audit

Opening `/results/20261028-135046_...` let the app's prop-firm card job (a subprocess) write
`prop_firm.json` into that run folder: a git-ignored, regenerable cache (seed 42). Nothing else
changed.
