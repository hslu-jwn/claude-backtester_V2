# Brief: V2.6 step 5 fixes after review (Opus, 2026-10-26)

Your step 5 work (`briefs/v26e-ui-items.md`) was reviewed (Sonnet): no-peek holds on every path.
Fix these, test-first, same rules as that brief. Run only your tests
(`pytest -q tests/ui > results\pytest_v26e_fix.log 2>&1`) + ruff.

1. **Label without seeing the trade** (`review_callbacks.py` ~253-285, `transition`): Take /
   Skip with no active review state (before "Run review"), or in the same call that rebuilds the
   state after a settings / symbol change, saves a label for trade 0 the user never saw. Take /
   Skip must be ignored (with a short message) unless an existing state matches the current
   strategy, settings hash and symbol and its current trade is the one on screen. Tests for both
   cases.
2. **Label file not process-safe** (`review.py` ~22, 66-84): use `backtester.filelock.file_lock`
   (lock in `results/.locks/`, as the trial log does) for labels and history; writes atomic
   (whole line); a partial or corrupt line is skipped with a warning in the panel instead of
   breaking every review action. Test with several processes appending (as
   `tests/analytics/test_queue_writers.py` does) and with a corrupt line.
3. **Agreement can trigger huge runs** (`review_callbacks.py` ~223-236, `evaluate`): agreement
   is computed only for labels inside the current review's symbol and period (say so next to
   the number: "n of N labels in this view"); labels elsewhere are counted, not re-run. Catch
   any run error and show it as a message, never a traceback.
4. **History file name collision** (`review.py` ~161): store the history under
   `results/review/_history/<strategy>.jsonl` (strategy names cannot start with `_`); read the
   old location once if present and move it.
5. Minor: the document-wide click handler in `chart.js` (~714-720) should only clear the focus
   when a focus is set (no callback on every click).

Report: files changed, test results.
