# Archived per-strategy grid tools

Archived 2026-10-21, replaced by `python -m backtester.tools.research <grid.toml>` (ROADMAP 6.1 + 6.2;
reproduction check on strategy 6 and strategy 5: `research/grids/check_orb.toml`, `check_gap_fade.toml`).

Still runnable as `python -m backtester.tools.archive.<name>`: `orb_grid`, `gap_fade_grid`,
`gap_fade_walk_forward`, `no_wick_grid`, `trend_grid`, `strategy2_sweep_grid`, `s2_volume_ab`.
Their tests are in `tests/tools/archive/`. Shared helpers live in `tools/grid_common.py`.
