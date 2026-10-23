# Brief: merge four exact duplicate helpers (Phase 3, behaviour must not change)

Pure refactor. No test's expected value may change; no output, default or trading rule may
change. Keep every existing public name importable (old names delegate to the survivor) so
callers and tests keep working.

1. `write_csv`: survivor `src/backtester/tools/grid_common.py::write_csv`. Replace the identical
   copies in `tools/entry_screen.py`, `tools/archive/no_wick_grid.py`,
   `tools/archive/strategy2_sweep_grid.py` with an import (only where the body is really
   identical: same header order, same empty-output behaviour; if one differs, leave it and say
   why).
2. `last_cached_day`: three identical bodies in `tools/archive/gap_fade_grid.py`,
   `tools/archive/orb_grid.py`, `tools/archive/s2_volume_ab.py`. Move one to
   `tools/grid_common.py`; the three modules import it (keep the name available in each).
   Watch for import cycles (`grid_common` imports `research`).
3. `research._now` duplicates `analytics/trial_log.py::now_iso`: keep `now_iso`, `research`
   uses it (keep `_now` as an alias if tests reference it).
4. `ui/live_model.py::_number` and `ui/trade_focus.py::_number`: identical finite-number
   parsing; keep one (in the module the other already imports from, or a tiny shared helper in
   `ui/`), the other delegates.

Done = `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/tools tests/ui
tests/analytics tests/test_runner_many.py` green and `.venv\Scripts\python.exe -m ruff check .`
clean. Report each merge: files changed, and anything you left alone and why.
