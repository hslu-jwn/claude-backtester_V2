# A2 + A3 implementation handoff

Codex worked alone on the inherited, unreviewed working tree. No commits, branches, pushes,
protected-path edits, strategy-rule changes, default trading-setting changes or golden replay.
Existing test expectations were preserved. This is an implementation handoff, not independent
approval or user acceptance under AGENTS.md.

## Per finding

Test paths below are relative to `tests/`; implementation paths are relative to `src/backtester/`.
“Prior” means the model that left the unfinished working tree; its identity was not supplied.

| Finding | Work and author | Regression test | Implementation files |
|---|---|---|---|
| A2: engine #7, risk #11, analytics #7, UI #8, other data/results defaults | Prior cache/funding anchoring kept; Codex simplified root constants, added remaining defaults and consumer coverage | `test_paths.py`: `test_paths_independent_of_working_directory`, `test_consumer_defaults_are_anchored`, `test_home_override_before_import_reaches_consumers`, `test_explicit_trial_path_stays_relative`, `test_dispatch_cli_default_is_anchored_explicit_is_relative` | `paths.py`, `data/cache.py`, `data/binance.py`, `engine/costs.py`, `tools/histdata_download.py`, `tools/spread_table.py`, `tools/ai_dispatch.py`; existing imports in `analytics/trial_log.py`, `risk/prop_card.py` and UI inherit the shared root |
| Analytics #1 | New: Codex | `analytics/test_a2_a3_regressions.py::test_training_excludes_exits_at_or_after_test_start` | `analytics/walk_forward.py` |
| Analytics #2 | New: Codex; fixed and adaptive replay both preserve weights | `analytics/test_a2_a3_regressions.py::test_portfolio_weights_reach_day_exposure`, `test_weighted_real_trade_keeps_risk_weight_and_partial_exits` | `analytics/portfolio.py`, `analytics/records.py`, `engine/trade.py`, `risk/monte_carlo.py` |
| Analytics #3 | New: Codex; real PartialExit objects and CSV dictionaries covered | `analytics/test_a2_a3_regressions.py::test_random_fill_stop_slippage_is_weighted_per_part`, `test_weighted_real_trade_keeps_risk_weight_and_partial_exits` | `analytics/random_fills.py` |
| Analytics #4 | New: Codex; exact close, tolerance boundary, outside tolerance, next session and end of input | `analytics/test_a2_a3_regressions.py::test_gap_bucket_last_close_tolerance` | `analytics/gap_buckets.py` |
| Analytics #5 | New: Codex; missing pre-entry candle and no candle by deadline | `analytics/test_a2_a3_regressions.py::test_entry_hit_deadline_uses_trade_timestamp`, `test_entry_hit_does_not_use_a_candle_after_deadline` | `analytics/entry_screen.py` |
| Analytics #6 | New: Codex; shared feature buckets for tables, spreads, halves and noise baselines | `analytics/test_a2_a3_regressions.py::test_orderflow_common_buckets_with_missing_targets`, `test_orderflow_noise_uses_same_extreme_buckets` | `analytics/orderflow.py` |
| Analytics #8 | New: Codex; non-object JSON roots warn and skip, following valid record retained | `analytics/test_a2_a3_regressions.py::test_trial_reader_warns_for_non_object_root` | `analytics/trial_log.py` |
| Analytics #9 | New: Codex; missing sibling p-value shown as n/a | `analytics/test_a2_a3_regressions.py::test_stationarity_missing_sibling_p_value` | `analytics/stationarity.py` |
| Analytics #10 | New: Codex; empty-series correlation and IDM documented | `analytics/test_a2_a3_regressions.py::test_empty_daily_series_have_finite_correlation_and_idm` | `analytics/portfolio.py`; `docs/risk-management.md` |
| Risk #3 | Prior validation kept; Codex expanded finite-config tests and preserved live caller error wording | `risk/test_prop_rules.py::test_guard_rejects_non_finite_inputs`, `test_all_guard_config_numbers_must_be_finite`, `test_nonfinite_daily_stop_keeps_caller_error_description` | `risk/prop_rules.py` |
| Risk #8 | Prior fix and test kept; Codex documented statistical convention | `risk/test_monte_carlo.py::test_post_ruin_statistics_no_nan_or_zero_division` | `risk/monte_carlo.py`; `docs/risk-management.md` |
| Risk #9 | Prior tests kept; new implementation and invalid-volume cases by Codex | `risk/test_sizer.py::test_bad_spec_raises`, `test_capped_volume_rounded_down_to_step`, `test_invalid_volume_spec_is_rejected` | `risk/sizer.py` |
| Risk #10 | New: Codex; both timestamps checked even when the period contains no weekdays | `analytics/test_a2_a3_regressions.py::test_risk_days_reject_naive_timestamps_even_without_weekdays` | `risk/monte_carlo.py` |

## Definitions and compatibility

- A daily/monthly return starting at a non-positive balance is 0%; reaching zero from a
  positive balance is -100%. The compounded account stays ruined. Documented in the risk spec.
- Empty/constant components have off-diagonal correlation 0 and diagonal 1. Empty rolling
  windows are omitted. IDM uses the existing formula and cap: sqrt(N) for N empty components.
- `BACKTESTER_HOME` is set before importing consumer modules. Explicit CLI paths stay relative
  to the current folder. Historical walk-forward inputs without `exit_time` keep their existing
  entry-only contract; actual closed trade records must exit strictly before the test window.
- Reserved findings risk #1/#2/#4/#5/#6/#7 and analytics #11 were left unchanged, including
  the future-R exposure approximation, pass-day policy and default time-exit slippage policy.
- Protected live modules already import shared paths (`bot.py`, `test_orders.py`,
  `trading_settings.py`); no additional live-path edit was identified or made. The live-caller
  validation regression is fixed in `risk/prop_rules.py`.

## Validation and acceptance blocker

Failing regression runs were saved before new fixes (`results/a2-a3-before.log`,
`a2-paths-before.log`, `a2-a3-extra-before.log`, `a3-extra-before.log`,
`a3-deadline-before.log`). The inherited tests only added assertions; no baseline expectation
was replaced. The original path test's monkeypatch is necessary to undo the suite's autouse
trial-log isolation for its read-only default-path assertion.

Affected analytics/risk/path/live-caller run: **678 passed** before the final extra deadline case.
Final focused run: **209 passed**. Repository `ruff check .`: clean. New test files formatted.

The first full run had **3,429 passed, 26 failed, 5 skipped, 1 xfailed**. The live-caller error
wording failure was subsequently fixed and verified. The other **25 failures explicitly require
relative default cache paths** in `tests/data/test_cache.py` and `tests/data/test_sources.py`.
These conflict with A2's absolute default paths. They are preserved as instructed; Codex asked
whether only those path expectations may be updated. No compatibility/equality workaround was
introduced into production code to hide this conflict.

Final full-suite result: **3,463 passed, 25 failed, 5 skipped, 1 xfailed** in 196.03 seconds;
output redirected to `results/a2-a3-full-final.log`. Every remaining failure is one of the
relative-path assertions above. Final repository lint and `git diff --check` pass. An AST
comparison against HEAD confirms the original bodies and decorators of all **59 existing test
functions/classes** in modified test files are preserved in order, with additions only.
The brief's green-full-suite acceptance condition remains blocked unless the path-test conflict
is resolved. No unclear trading rule was encountered.
