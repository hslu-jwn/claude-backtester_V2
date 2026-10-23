# A4 + A5 implementation handoff

Implemented all 11 requested findings. Eighteen parameterized regression cases failed
before implementation and pass with the fixes. Existing test expectations and trading
defaults were not changed. No golden checker was run; golden files are untouched.

Paths in the source column are relative to `src/backtester/`.

A4 tests: `tests/strategy/ny_index_sweep/test_a4_options.py`.
A5 tests: `tests/ui/test_a5_regressions.py`, except UI #11 in
`tests/test_a5_progress.py`.

| Finding | Regression test | Changed source files |
|---|---|---|
| Strategy #3 | `test_htf_close_beyond_cancels_after_setup_bos` (BOS, TAPPED, ENTRY, IN_TRADE) | `strategy/ny_index_sweep/setup.py` |
| Strategy #4 | `test_rollover_cutoff_survives_missing_entry_day_candles` (summer/winter) | `strategy/ny_index_sweep/strategy.py` |
| Strategy #6 | `test_equal_timeframes_feed_both_trackers_once` | `strategy/session_zone_sweep/strategy.py` |
| UI #1 | `test_replay_range_end_hides_future_exit_and_partial` | `ui/trades_overlay.py` |
| UI #2 | `test_trades_in_view_callback_observes_replay` | `ui/pages/chart.py` |
| UI #5 | `test_preset_preserves_hidden_costs_and_modified_state` | `ui/settings_panel.py` |
| UI #6 | `test_research_variant_card_and_monte_carlo_resolve_same_folder` | `ui/pages/results.py`, `ui/run_paths.py` (new shared resolver), `ui/prop_firm_card.py`, `ui/monte_carlo_job.py` |
| UI #7 | `test_changed_card_inputs_start_fresh_job` | `ui/prop_card_job.py` |
| UI #9 | `test_run_listing_skips_non_object_summary` (array, null, number, string) | `ui/pages/results.py` |
| UI #10 | `test_monte_carlo_progress_survives_log_retention` | `ui/monte_carlo_job.py`, `ui/process_job.py` |
| UI #11 | `test_delayed_symbol_progress_never_goes_backwards` | `runner.py` |

Validation:

- `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests`: **3508 passed,
  5 skipped, 1 xfailed**, 44 warnings; final output: `results/a4_a5_full_tests.log`.
- `ruff check .`: clean.
- New test files: `ruff format --check` clean.
- `git diff --check`: clean.
- Pre-fix regression evidence: `results/a4_a5_before.log`.

Review still pending: Opus cross-review and golden trade-list comparison, plus browser
review. In replay the overlay must withhold future exits/results and the Trades in view
card displays a replay notice. The app was not started and browser rendering was not
exercised. No trading-rule questions remain.

No commits, pushes, branches, or edits to `src/backtester/live/` or `.env`.
