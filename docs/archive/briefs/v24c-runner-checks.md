# Brief V2.4c leftovers: three runner checks (Codex, medium)

Picked by the user 2026-10-28 from `docs/review/backtest-audit.md` › Re-check 2026-10-28:
#2 swept-parameter count, #6 entry screen in the runner, #13 slope of returns + top-10 trades.
Checklist source: `knowledge/topics/testing-and-robustness.md` lines 18, 107, 240-254.

**Test first:** write the tests below, run them red, then implement. Never change an existing
expected value to make a test pass (see "Existing tests"). Only the research runner's
reporting changes: no engine, cost, strategy, default or verdict-threshold change, nothing in
`live/`. Development data only for anything new (never read test-period data for these).

## 1. Swept-parameter count (#2)

- `ResearchConfig.max_free_params: int = 4` (checklist: "at most about 4 free parameters",
  Kaufman p.938), validated >= 1.
- `tools/research_grid.py`: `swept_params(spec) -> list[str]`: sorted distinct setting names
  that take **more than one distinct value** in any family (`spec.grids`, or `spec.grid` when
  there are no families). A setting listed with one value is not free.
- Runner: `research.json` gets `"swept_params": [...]`, `"free_params": n`; when
  `n > max_free_params` add the flag `too_many_parameters` to every variant row of the run
  (it is a property of the grid) and a report line "Free parameters: n (limit 4): names".
  It is a warning flag, never a refusal. Flag label for the UI (`ui/research_model.py`,
  same place as the other flag labels): "more than 4 swept settings".

## 2. Entry screen in the runner (#6)

- New `tools/research_entry_screen.py` modelled on `tools/research_monkeys.py`:
  `calculate(folder, spec, variant_id, start, end, settings, sources) -> dict`: read the chosen
  development variant's trades (`read_trades`), `ScreenTrade.from_trade`, M1 via
  `tools.entry_screen.load_m1`, `bar_minutes` from the strategy's base timeframe (as in
  `tools/entry_screen.py` main), `screen_variant(... settings.engine.costs, EntryScreenConfig() ...)`,
  `judge([screen])`. Return `{variant_id, start, end, bar_minutes, passed, reasons, cells,
  cells_positive, cell_share, bracket_win_rate, random_percentile, trades, skipped, flags}`
  with `flags = ["entry_screen_failed"]` when not passed. JSON-safe values only.
- Spec defaults of `EntryScreenConfig` stay (1,000 runs, seed 42). Measure the time on the
  test fixtures only; if it looks slow, say so in the report, do not lower the runs.
- Runner `finish()`: run it right after the monkeys block, same pattern: only when a chosen
  variant exists and `spec.entry_screen` is true; write `entry_screen.json`, append its flags
  to the chosen row; delete a stale `entry_screen.json` otherwise. Report block (title
  "Entry screen (chosen development variant)") with passed, the reasons and the three numbers.
  If the M1 data for a symbol is missing, record `{"error": ...}` in the JSON and the report
  instead of crashing the run (monkeys' behaviour if it has one; follow it).
- Grid file key `entry_screen = true|false` (default true), validated like `monkeys`.
- UI flag label "entries not better than chance".

## 3. Slope of returns and top-10 trades (#13)

In `tools/research_diagnostics.py` next to `by_year` (chosen development variant and each test
run, same row identity as `by_year`: period, variant ID, test run):
- `returns_slope.csv`: monthly net R by UTC **entry** month (months between the first and last
  trade with no trade count as 0), OLS slope in R per year (`slope_per_month x 12`), its
  standard error, t-stat, n months. Fewer than 6 months -> slope fields empty.
  Flag `declining_returns` on the chosen development row when t <= -2.0 (new
  `ResearchConfig.decay_t: float = -2.0`). UI label "returns falling over time".
- `top_trades.csv`: the 10 best and 10 worst trades by `r_net` (fewer if fewer trades; a trade
  is in both lists only if there are < 20 trades, that is fine): rank, side ("best"/"worst"),
  symbol, direction, entry time, exit time, exit reason, r_net, hold hours. Plus in the report:
  net R, net R without the 10 best, share of net R from the 10 best.
- Report block "Decay and extreme trades" with the slope line and the three numbers.
- Pure helpers in `analytics/` (e.g. `analytics/robustness.py`: `monthly_net(trades)`,
  `returns_slope(monthly)`, `top_trades(trades, n=10)`), tools only wire them.

## Test cases

`tests/tools/test_research_grid.py` / new files as fits:
1. `swept_params`: one value per setting -> []; two settings with 2+ values -> both; a setting
   repeated with the same single value in two families -> not free; union across families.
2. 5 swept settings -> `too_many_parameters` on every row and in research.json; 4 -> no flag.
3. `max_free_params=0` -> ValueError.
`tests/analytics/test_robustness.py` (or a new file):
4. `monthly_net` fills empty months with 0, uses entry month in UTC (a trade entering
   2023-01-31 23:30 UTC belongs to January).
5. `returns_slope` on a perfect line 1, 2, ..., 12 R per month -> slope 12 R/year, t = inf or
   very large (say how infinity is stored: JSON null + "perfect fit"? choose: store `None` for
   SE = 0 and t; test it); constant series -> slope 0; 5 months -> None fields.
6. Declining series with noise (fixed numbers in the test) -> t <= -2 -> flag.
7. `top_trades`: 25 trades -> 10 + 10, sorted best desc / worst asc, ties by entry time;
   3 trades -> 3 best and 3 worst.
8. Net R without the 10 best and the share (net R <= 0 -> share None).
`tests/tools/test_research_entry_screen.py`:
9. With the synthetic fixtures the runner tests already use: `entry_screen.json` written,
   keys present, `passed` bool; `entry_screen = false` -> no file and stale file removed.
10. Failing screen -> `entry_screen_failed` in the chosen row's flags.
11. Missing M1 for a symbol -> error recorded, run finishes.
12. The screen reads nothing after the development end (assert `load_m1` end argument).
13. Grid file `entry_screen = "yes"` -> GridError.

## Existing tests

Runner tests that count calls or compare full output file lists / reports may change. Where a
test counts calls or file lists and the new output is expected, add `entry_screen = false` to
that test's grid **or** add the new file names to the expected list; never change numeric
expectations. List every existing test you touched and why.

## Docs

`docs/research-runner.md`: new subsection "Runner checks (V2.4c, 2026-10-28)" with the three
rules above (thresholds, files, flags, the grid key); add the three files to the Output list.
`docs/review/backtest-audit.md`: rows #2, #6, #13 -> ☑ with the file names.

Done = new tests green; `pytest tests/tools tests/analytics tests/ui -q` green; ruff check +
format clean. Do not commit. Report: files changed, tests added, existing tests touched, the
entry-screen time on the fixture run, open questions.
