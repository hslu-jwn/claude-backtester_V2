# Brief: V2.5 — Fast mode (headless) and Visual mode give identical trade lists (a test)

Context: ROADMAP › V2.5 ("Two modes with a switch / CLI flag: Fast mode = headless, no chart,
for automated research; Visual mode = the app. Both give identical trade lists for the same
settings (test)"). Fast mode exists: `python -m backtester.run ...` and the research runner;
Visual mode = the app's backtest job (`ui/backtest_job.py`, started from the Chart page's
Backtest tab, writing a normal run folder).

## What to build

1. A test (`tests/test_fast_visual_identical.py`) that runs the same settings (a small
   hand-built cached data set or the existing test fixtures; two strategies, one with TPs and
   one without) once through the CLI entry (`backtester.run` main / `run_backtests` +
   `write_results`) and once through the app's backtest job code path (the function the job
   calls, without starting Dash or a server), and asserts the two `trades.csv` files are
   identical row by row (same columns, same values) and the summaries match.
2. If the two paths differ in any setting they pass (e.g. workers, warm-up, preset handling),
   report it; fix only if it is a plain wiring difference, otherwise stop and ask.
3. ROADMAP: tick the "identical trade lists" part when green (one line in V2.5's entry).

## Rules

Never start a server or leave a process running. Run only the new test and the tests of what you
change (`pytest -q tests/test_fast_visual_identical.py tests/ui/test_backtest_job*.py >
results\pytest_fastvisual.log 2>&1`). Never edit `src/backtester/live/`.

Done = test green, `ruff check .` clean. Report: files changed, any difference found.
