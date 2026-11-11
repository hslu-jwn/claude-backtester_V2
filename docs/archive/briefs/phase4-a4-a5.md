# Brief A4 + A5: strategy option bugs and UI fixes (V2.4, group A; trades must not change)

Findings with evidence in `docs/review/strategy.md` and `docs/review/ui.md`. Test first (a
failing test per finding, then the fix). No trading-rule default, no existing test expectation
changes; the golden trade lists (`tests/golden/`, spec defaults) must stay identical. Do NOT
edit `src/backtester/live/`.

## A4: strategy options that are off by default

- strategy #3 (`ny_index_sweep/setup.py`): with `sweep_close_beyond_counts=False`, the HTF
  close-beyond cancellation keeps working after the setup BoS (spec AM step 3).
- strategy #4 (`ny_index_sweep/strategy.py`): the close-before-rollover cutoff is derived from
  each trade's entry date, so missing cutoff-day candles cannot postpone the exit a day.
- strategy #6 (`session_zone_sweep/strategy.py`): equal obstacle and limit timeframes keep
  separate progress for each tracker.

## A5: UI

- ui #1 (`ui/trades_overlay.py`) and ui #2 (`ui/pages/chart.py` "Trades in view"): during
  replay never show an exit, partial exit or result whose time is after the replay cursor;
  clip only the drawing.
- ui #5 (`ui/settings_panel.py`): loading a preset keeps every setting of the preset
  (including costs of symbols not shown in the panel) and overlays only the edited fields;
  `modified` stays correct.
- ui #6 (`ui/pages/results.py`): research-variant ids resolve to the same run folder for the
  prop-firm card and the Monte Carlo button.
- ui #7 (`ui/prop_card_job.py`): changed inputs start a fresh calculation instead of
  "finished without a result".
- ui #9 (`ui/pages/results.py`): run listing skips summaries whose JSON root is not an object.
- ui #10 (`ui/monte_carlo_job.py`): progress keeps the current kind and path count beyond the
  200 retained log lines.
- ui #11 (`ui/backtest_job.py` / `runner.py` progress): progress per symbol never goes
  backwards (audit 13.21).

Done = new tests green; `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests`
green (redirect its output to a file; this PC's terminal stalls unread output); `ruff check .`
clean; new test files formatted. Do not run the golden check (Opus runs it). Report per
finding: test name, files.
