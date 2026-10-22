# Brief A2 + A3: paths, analytics and risk fixes (V2.4, group A; trades must not change)

Findings with evidence in `docs/review/<module>.md`. Test first (a failing test per finding,
then the fix). No trading rule, default or existing test expectation changes. Do NOT edit
`src/backtester/live/` (if a live module needs a change, list it in your report).

## A2: paths independent of the working folder (audit 13.17)

engine #7, risk #11, analytics #7, ui #8: anchor the default `results/` and `data/` folders to
the project root in ONE place (`src/backtester/paths.py`; e.g. the repo root found from the
package location, overridable by an environment variable `BACKTESTER_HOME` for tests) and make
`costs.FUNDING_DIR`, `trial_log.default_path`, `prop_card` / UI `RESULTS_DIR` and the other
relative defaults use it. Relative paths that the user passes explicitly on a command line keep
working as before (relative to the current folder). Test: run the defaults from another current
folder (`monkeypatch.chdir(tmp_path)`) and get the same absolute paths.

## A3: analytics and risk

- analytics #1: walk-forward training may only use trades whose exit is before the test window
  starts.
- analytics #2: portfolio scaling carries component risk weights into the Monte Carlo day
  events / exposure.
- analytics #3: random fills apply stop slippage per exit part, weighted by its share.
- analytics #4: gap-bucket records finalize at the last session close within the configured
  close tolerance.
- analytics #5: entry-screen hit-rate deadlines from `trade.entry_time`.
- analytics #6: orderflow tables, spreads and halves use the same bucket codes.
- analytics #8: trial-log reader skips (with a warning) lines whose JSON root is not an object.
- analytics #9: stationarity findings format a missing sibling p-value.
- analytics #10: empty daily series give no NaN correlations / IDM (define them; document).
- risk #3: guard rejects non-finite configuration and account inputs.
- risk #8: post-ruin statistics: no NaN / ZeroDivisionError (define the values; document).
- risk #9: sizer validates volume step / min / max and rounds a capped volume down to a valid
  step before the minimum check.
- risk #10: reject naive timestamps in the risk day mapping.

Not in this batch (decided separately): risk #1, #2, #4, #5, #6, #7, analytics #11.

Done = new tests green; `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests`
green; `ruff check .` clean; new test files `ruff format`ted. Do not run the golden check.
Report per finding: test name, files; plus anything in `live/` that still needs a change.
