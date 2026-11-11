# V2.5c test cases

Write regression tests before implementation; Opus reviews code and browser appearance.

- Chart and Results render with empty data and a fixture run; every ID occurs once.
- Chart has Trades (default), Overlays, Backtest and Strategy tabs; moved controls retain IDs.
- Overlay master remains visible; type switches and chart settings details start closed.
- Chart strip uses newest run net R, win rate, count and drawdown; empty runs show dashes.
- Both trade lists focus the run's symbol/timeframe; existing replay/focus and backtest-job tests remain.
- Results defaults to Trades below a persistent equity chart and prop-firm side panel.
- Results strip respects symbol filter and includes expectancy and middle-risk prop pass.
- Trade columns default to time, symbol, side, net R and exit; More columns restores all.
- Performance preserves summaries/splits/year, folds quarter and histogram, reads optional
  skill/drawdown/profile outputs, and handles missing/malformed files with dashes.
- Strategy groups are collapsible, first visible group open, others closed; all fields remain.
- Chart CSS reserves at least 420px canvas height; Opus checks at a 900px viewport.
- Run only `pytest -q tests/ui > results/pytest_v25c.log 2>&1` and `ruff check .`.

## Implementation handoff

- Existing callback / chart.js IDs retained. `ch-card-result` moved above the chart.
- Removed unused presentation IDs: `tb-strategy`, `pop-strategy`, `tb-backtest`,
  `pop-backtest`, `ch-card-result-fold`. No callback or JS references required changes.
- Added `chart-key-strip`, `chart-tabs`, `chart-tab-{trades,overlays,backtest,strategy}`,
  the `run-trade` pattern ID, `rs-key-strip`, `rs-prop-pass`, `rs-more-columns`.
- Display choice where the proposal is silent: middle-risk **Fixed** pass probability.
  The side card and strip use the same value, with full Fixed/Adaptive table retained.
- Saved prop estimates and diagnostics describe the full run, explicitly labelled; the
  symbol filter updates trade metrics/equity without pretending to recompute those files.
- Chart forms remain mounted while tabs hide their panels, preserving callback inputs,
  presets and form state. Newest-run trade rows include symbol and UTC time.
- Header notes, overlay types, quarter, histogram, overview metrics, full prop table and
  Monte Carlo progress start folded; the first visible strategy group starts open.
- Validation: **620 passed, 1 skipped** (existing DataTable deprecation warnings), log
  `results/pytest_v25c.log`; `ruff check .` and `git diff --check` clean.
- Browser review at a 900px viewport and the full suite remain for Opus. No server started,
  no roadmap completion marked, no commit/branch/push, no protected paths changed.
