# Grid merge 3 historical commands

The old gap tool was `src/backtester/tools/gap_momentum_grid.py`:
`python -m backtester.tools.gap_momentum_grid --mode index` (or `--mode fx`).
The archived sweep commands used `python -m backtester.tools.archive.<name>`;
the replacement grid headers also record their earlier, pre-archive default commands.
The `grid_common.py` helpers moved without behavioral changes to `research_helpers.py`.

Reproduction (full development span, default costs, no shocks):

| Variant | Old trades | Runner trades | Old net R | Runner net R |
|---|---:|---:|---:|---:|
| NAS100 range 5m T0 | 1684 | 1684 | -42.229861754748235 | -42.229861754748235 |
| NAS100 range 15m T0 | 1655 | 1655 | -43.70618536410871 | -43.70618536410871 |
| XAUUSD H4 breakout 20 | 156 | 156 | -30.357621392104853 | -30.357621392104853 |
| XAUUSD H4 breakout 55 | 88 | 88 | -59.95273451797779 | -59.95273451797779 |

Entry/exit timestamps and prices, stop, gross/net R and swap all matched per trade.
NAS100 span 2015-01-02..2021-09-13; XAUUSD 2010-01-01..2021-09-13.
Logs: `results/gm3_orb_old.log`, `gm3_orb_new.log`, `gm3_trend_old.log`,
`gm3_trend_new.log`, `gm3_reproduction.log`; runner outputs `results/gm3_check/`.

## Validation and decisions

- Full suite: **3717 passed, 5 skipped, 1 xfailed, 44 warnings** in 202.19 seconds.
  Log: `results/pytest_gm3.log`.
- Targeted research group: **104 passed** in 38.84 seconds (`results/gm3_migrated.log`).
- `ruff check .`, formatting checks on all 16 changed Python files and `git diff --check`: clean.
- Removed-module reference scan: empty outside `docs/archive/` and `results/`.
- Real saved-trade walk-forward smoke: `results/gm3_walk_forward.log`; both NAS100 variants
  resumed, no additional backtest runs, test period unspent.
- Tests were written first and their failures captured in `results/gm3_failing.log`,
  `gm3_grids_failing.log`, `gm3_study_failing.log`, `gm3_helpers_failing.log`.
- Saved sweep oracle covers **278 configurations**: ORB 41 (including optional volume),
  gap fade 36, no wick 24, trend 95, NY sweep 8, NY volume 2, gap momentum 36 per mode.

Implementation choices (documented in `docs/research-runner.md`):

- Walk-forward defaults off; CLI enables anchored unless the grid specifies a mode.
  Rolling window defaults to three years; one prior year is sufficient, as in the existing splitter.
- Annual pick includes all saved development variants, stable file-order ties. Comparison
  uses the overall chosen development variant; it is blank if no variant qualifies.
- Calendar years, including empty/partial years, count as one year. Efficiency is blank
  for no windows or nonpositive mean annual training R.
- SMA bands have their own family to avoid inventing unswept period/band combinations.
  The helper module was renamed rather than discarded because active tools still use it;
  its execution behavior is unchanged.
- Historical briefs were moved verbatim under `docs/archive/briefs/` to preserve provenance
  while removing references to deleted executables from active documentation.
- Historical gap-tool commands in grid headers use PowerShell string concatenation to
  retain the old command while keeping deleted module identifiers in this archive only.

No unresolved trading-rule questions. No roadmap completion box was changed; independent
review and the user's acceptance remain pending under AGENTS.md. No commits or branches.

## Workspace file manifest

Generated from the final working-tree diff; `A` means an added/untracked file, `M` modified,
`D` deleted. The four briefs listed under both D and A were moved verbatim.

- `M` `AGENTS.md`
- `D` `briefs/grid-merge-1.md`
- `M` `briefs/grid-merge-2.md`
- `D` `briefs/grid-merge-3.md`
- `D` `briefs/phase3-dedupe-tests.md`
- `D` `briefs/phase3-dedupe.md`
- `M` `docs/ARCHITECTURE.md`
- `M` `docs/HANDOFF.md`
- `M` `docs/research-runner.md`
- `M` `docs/strategy-gap-fade.md`
- `M` `docs/strategy-gap-momentum.md`
- `M` `docs/strategy-no-wick.md`
- `M` `docs/strategy-ny-indices.md`
- `M` `docs/strategy-opening-range.md`
- `M` `docs/strategy-trend-following.md`
- `D` `src/backtester/tools/archive/README.md`
- `D` `src/backtester/tools/archive/__init__.py`
- `D` `src/backtester/tools/archive/gap_fade_grid.py`
- `D` `src/backtester/tools/archive/gap_fade_walk_forward.py`
- `D` `src/backtester/tools/archive/no_wick_grid.py`
- `D` `src/backtester/tools/archive/orb_grid.py`
- `D` `src/backtester/tools/archive/s2_volume_ab.py`
- `D` `src/backtester/tools/archive/strategy2_sweep_grid.py`
- `D` `src/backtester/tools/archive/trend_grid.py`
- `M` `src/backtester/tools/entry_screen.py`
- `D` `src/backtester/tools/gap_momentum_grid.py`
- `D` `src/backtester/tools/grid_common.py`
- `M` `src/backtester/tools/noise_study.py`
- `M` `src/backtester/tools/open_gap_study.py`
- `M` `src/backtester/tools/orderflow_study.py`
- `M` `src/backtester/tools/research.py`
- `M` `src/backtester/tools/research_diagnostics.py`
- `M` `src/backtester/tools/research_grid.py`
- `M` `src/backtester/tools/risk_sweep.py`
- `M` `src/backtester/tools/strategy2_explore.py`
- `D` `tests/tools/archive/test_gap_fade_grid.py`
- `D` `tests/tools/archive/test_gap_fade_walk_forward.py`
- `D` `tests/tools/archive/test_orb_grid.py`
- `D` `tests/tools/archive/test_s2_volume_ab.py`
- `D` `tests/tools/archive/test_trend_grid.py`
- `D` `tests/tools/test_gap_momentum_grid.py`
- `A` `docs/archive/briefs/grid-merge-1.md`
- `A` `docs/archive/briefs/grid-merge-3.md`
- `A` `docs/archive/briefs/phase3-dedupe-tests.md`
- `A` `docs/archive/briefs/phase3-dedupe.md`
- `A` `docs/archive/grid-merge3-provenance.md`
- `A` `research/grids/gap_fade.toml`
- `A` `research/grids/gap_momentum_fx.toml`
- `A` `research/grids/gap_momentum_index.toml`
- `A` `research/grids/no_wick.toml`
- `A` `research/grids/ny_index_sweep.toml`
- `A` `research/grids/ny_index_volume.toml`
- `A` `research/grids/orb.toml`
- `A` `research/grids/trend_following.toml`
- `A` `src/backtester/tools/gap_bucket_study.py`
- `A` `src/backtester/tools/research_helpers.py`
- `A` `src/backtester/tools/research_walk_forward.py`
- `A` `tests/tools/fixtures/gm3_sweeps.json`
- `A` `tests/tools/test_gap_bucket_study.py`
- `A` `tests/tools/test_research_helpers.py`
- `A` `tests/tools/test_research_sweep_files.py`
- `A` `tests/tools/test_research_walk_forward.py`
