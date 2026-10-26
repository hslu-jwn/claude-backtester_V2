# V2.6 step 5 test cases

Tests precede implementation; callbacks are exercised without starting an app.

- Review: append labels and round trip UTC keys, optional TP and reason; last label wins across settings hashes; reject invalid labels, non-finite TP and reasons over 200 characters.
- Agreement: four labelled setups, remove one take and one skip; expect two agreements of four, with separate counts and settings history.
- Review transport: truncate at entry close before encoding candles; reveal permits later candles; overlays, replay steps and order payloads must obey the same ceiling; empty runs and navigation bounds are safe.
- Inspection: select exactly the clicked trade, preserving recorded notes, entry, SL, all TPs and exit; no other trade drawings; clear and replay from a configurable 50-candle lead-in; preserve session inspection.
- Heat map: three varied parameters fix the third to the chosen variant; missing combinations remain None; development metrics only; chosen variant marked; invalid/equal axes and fewer than two varied parameters are handled.
- Dropdown: off/FVG/OB/both map exactly to the four legacy boolean combinations; old settings keys and callback IDs survive.
- Layout and callback registration smoke checks, without a server, plus existing tests/ui regression suite.

## Implementation handoff

Changed files:
- `briefs/v26e-test-cases.md`
- `tests/ui/test_v26e.py`
- `src/backtester/ui/review.py`
- `src/backtester/ui/review_callbacks.py`
- `src/backtester/ui/parameter_heatmap.py`
- `src/backtester/ui/strong_move.py`
- `src/backtester/ui/pages/chart.py`
- `src/backtester/ui/pages/research.py`
- `src/backtester/ui/research_model.py`
- `src/backtester/ui/settings_panel.py`
- `src/backtester/ui/trade_focus.py`
- `src/backtester/ui/assets/chart.js`
- `docs/strategy-session-zones.md`

IDs added:
- `chart-review`, `chart-inspect`
- `review-period`, `review-run`, `review-leave`, `review-previous`, `review-next`,
  `review-unlabelled`, `review-reveal`, `review-current`, `review-reason`, `review-tp`,
  `review-take`, `review-skip`, `review-status`, `review-agreement`, `review-history`
- `inspection-panel`, `inspection-replay`, `inspection-lead`, `inspection-reason`
- `st-strong-move`
- Pattern IDs `{type: heatmap-data|heatmap-x|heatmap-y|heatmap-metric|heatmap-figure, index: <card source>}`

IDs removed or renamed: none. `chart-filters` retains its ID; its visible control is now
a dropdown with scalar values `off`, `fvg`, `ob`, `both`. Server mapping also accepts legacy
checklist lists. The two original settings fields retain their IDs and are hidden; settings
JSON, presets and grid keys retain their boolean values.

Review history is stored separately as `results/review/<strategy>-history.jsonl`; label data
remains exactly `results/review/<strategy>.jsonl`. History percentages are observations at
evaluation time, with counts and UTC time. Existing chart candle limits still apply when
revealing a very long trade; the chart can request a higher timeframe.

Validation: UI-only pytest output is in `results/pytest_v26e.log`; ruff checks and formatting
are limited to the touched Python files. No server, preview, commit, push or branch was created.
Final run: **700 passed, 1 skipped**, 22 existing Dash deprecation warnings, 36.73 seconds.
Ruff: all checks passed; all 10 touched Python files pass the formatting check. `git diff --check`
also passed. The workspace virtualenv's `pytest.exe` was used because pytest is not on PATH.
Opus cross-review and the user's visual acceptance remain pending; ROADMAP is not marked done.
No trading-rule questions arose.
