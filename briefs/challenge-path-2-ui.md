# Brief: challenge path simulator, increment 2 (Results page tab)

You work in a lane worktree of the V2 repo. Read `AGENTS.md` first (hard limits: no commits, no
branches, never start the app or any server / long-running process, no credentials, never edit
`src/backtester/live/`). Increment 1 is merged: `risk/challenge_path.py` (`RULE_SETS`, `play_attempt`,
`simulate`) and `tools/challenge_path.py`.

## Spec

`docs/risk-management.md` › "Challenge path simulator and FTMO rule sets": the Results page shows a
run's real trade path through an FTMO account: balance, daily-loss and max-loss lines, a pass / breach
marker, a start-date picker, a risk % input and the rule-set choice.

## Files you may create / change

- new `src/backtester/ui/challenge_path_tab.py` (layout + callbacks, like `ui/prop_firm_card.py`)
- `src/backtester/ui/pages/results.py`: add a tab `("challenge", "Challenge path")` to `TABS`, render it
  in the existing tab callback, call the new module's `register_callbacks` from `register_callbacks`
- new `tests/ui/test_challenge_path_tab.py`

## What to build

- Controls (dark theme classes as the other Results tabs use): rule set dropdown (`RULE_SETS` keys,
  labels "FTMO 2-Step", "FTMO 1-Step", "FTMO Instant", default 2-Step), risk % number input (default 1.0,
  min 0.1, max 5, step 0.1), start-date dropdown (the monthly start dates of the run; default the first).
- Computation is fast (no resampling): compute in the callback with `simulate` on the run's trades
  (`pages.results.read_trades`, the run's start / end from its settings as `tools/challenge_path` does);
  cache per (run, rule set, risk) in memory (`functools.lru_cache` on a pure helper is enough).
- Figure (plotly, same colours as `pages.results`: UP / DOWN / MUTED / ACCENT): x = date, closing balance
  line, the day's worst equity as a faint line, daily-loss floor (step line, DOWN dashed), max-loss
  floor (step line, DOWN solid; it rises for the trailing rule sets), phase target line(s) (UP dashed),
  a marker at the end: "Passed" (UP), "Daily loss" / "Max loss" (DOWN), "Open" (MUTED), "Survived" (MUTED).
- Below the figure: a small summary table for the chosen rule set over all start dates (attempts,
  pass %, daily %, max %, open, median / p90 weekdays to funding) and a one-line note: "News and
  market-break restrictions on funded / Instant accounts are not modelled; fees are not published."
- Empty run / no trades: a muted "No trades in this run" text, no exception.

## Tests (first)

- Layout builds for a hand-made run folder (tmp results dir) and contains the three controls with the
  defaults above; the tab is in `TABS`.
- The figure helper for a passing 2-Step attempt has the balance trace, both floors, the target lines
  and a "Passed" marker; a breached 1-Step attempt ends with "Daily loss" or "Max loss" and its max-loss
  floor trace is non-decreasing.
- Changing the risk input changes the plotted path (higher risk, larger moves); invalid risk (0, empty)
  -> no_update, no exception.
- Empty run -> the "No trades" text.
- The app builds with the new callbacks without duplicate ids (follow `tests/ui/test_nav.py` /
  `test_page_callbacks_register_without_clashes` patterns).

## Done =

New tests pass, the full suite (`python -m pytest -q -p no:cacheprovider -n 8`) green, ruff clean.
Report files changed, test results, open questions. Do not start the app; Opus checks it in the browser.
