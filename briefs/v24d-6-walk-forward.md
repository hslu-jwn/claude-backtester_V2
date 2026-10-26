# Brief: V2.4d item 6 — walk-forward with month-based windows, efficiency per window, open-trade boundary

Context: ROADMAP › V2.4d (6) (accepted by the user 2026-10-23); `docs/review/book-app-requirements.md`
D1-D4; `knowledge/books/pardo-evaluation-optimization.md` (ch.11: walk-forward analysis, WFE,
window lengths), `knowledge/books/masters-testing-tuning.md` (ch.5: open trades at the IS / OOS
boundary, unbounded lookback); `knowledge/topics/testing-and-robustness.md` › In-sample /
out-of-sample. Today `analytics/walk_forward.py` works in whole calendar years (anchored or
rolling, pick = max net R) and `tools/research_walk_forward.py` (grid merge 3) reports a WFE
on yearly windows from the saved development trades.

## What to build

1. `analytics/walk_forward.py`: windows in **months** — `train_months` (default 24), `test_months`
   (default 6), `step_months` (default = test_months), anchored or rolling; the yearly mode is
   the special case 12 / 12 and keeps its old numbers exactly (tests). Windows over the
   development period only (the test period stays untouched).
2. **Open-trade boundary rule** (Masters ch.5, Pardo ch.11): a trade belongs to the window it was
   **entered** in; for picking, a train window only counts trades that **exited** before the train
   window's end (no outcome from the future enters a pick); trades entered in a test window and
   exiting after it stay in that test window (the strategy really held them). Say so in the spec.
3. **Per-window table** (`walk_forward.csv`): window, train period, test period, picked variant,
   train net R per month, test net R per month, WFE of the window (test per month / train per
   month; n/a when train <= 0), trades, max DD in the test window. Summary: chained OOS scorecard
   (the existing scorecard on the concatenated test trades), overall WFE = mean OOS R per month /
   mean IS R per month of the picks, the share of windows with a positive test result, and how
   often the pick changed (parameter stability).
4. **Window study** (Pardo ch.11, D3): grid option `walk_forward_study = true` runs the analysis
   for train_months in (12, 24, 36) x test_months in (3, 6, 12) on the saved trades (cheap, no
   backtests) and writes `walk_forward_study.csv` (overall WFE, chained net R per month, share of
   positive windows) — it shows whether the result depends on the window choice.
5. Grid options `walk_forward = "anchored" | "rolling"` stay; new `train_months`, `test_months`,
   `step_months`. Report block updated.

## Rules

Spec first (`docs/research-runner.md` › Walk-forward), test-case list at the top of the test
file, failing tests, then code. Tests: yearly mode identical to today; a trade exiting after the
train end is excluded from that pick; a test-window trade exiting later stays in it; rolling vs
anchored windows; step shorter than test is refused or documented (overlapping test windows would
double count: refuse); too short a period -> no windows with a reason; WFE n/a on a non-positive
train. Selection of the chosen variant, the test run, trial log, DSR unchanged. Never edit
`src/backtester/live/`.

Done = the tests of what you changed green (`pytest -q tests/analytics/test_walk_forward*.py
tests/tools/test_research*.py > results\pytest_v24d6.log 2>&1`; Opus runs the full suite), `ruff check .` clean;
one real run of the runner on a small trend-following grid (2-3 variants, XAUUSD, dev-only,
`walk_forward = "anchored"`, `walk_forward_study = true`, results to `results\v24d6_check`) with the
tables in the report. Report: files changed, test count, decisions the spec did not settle, open
questions.

## Answers given up front (Opus, 2026-10-24)

- A window with no trade of a variant: that variant's train net R is 0 (it can still be picked
  only if all are <= 0; ties go to the first variant as today).
- Months are calendar months (UTC); a window starts on the 1st; the first window starts at the
  first full month of the development period; a partial last test window is kept and its
  per-month numbers use its real length.
- The chosen variant (from the normal selection) is reported next to the walk-forward picks per
  window, as today.
- WFE in R per month; when the train result is <= 0 the window's WFE is n/a and it is left out
  of the overall WFE (say so).
- Nothing in this brief changes selection, the test run, the trial log or the DSR.
