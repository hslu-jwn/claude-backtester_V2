# Brief: research runs of `trend_following` on D1 fail with "Replay needs at least one candle"

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). Test first; never
weaken a test. Preserve no-lookahead (`AGENTS.md` › Invariant #1).

Repro: `python -m backtester.tools.research research/grids/trend_following_crypto.toml --dev-only` (BTCUSD,
`timeframe = "D1"`, 8 cells) fails in `engine/backtest.py` line 146 -> `engine/replay.py` line 38: the base
timeframe D1 has zero candles in a job (`runner.py` `_run_job` -> `run_backtest`). Same for
`trend_following_crypto_eth.toml`. BTCUSD has MT5 M1 from 2017-04.

Find the root cause (e.g. the runner splits the period into chunks shorter than one D1 bar, D1 aggregation
of 24/7 crypto, the warm-up, or the strategy's timeframe not supported by the runner) and fix it once in
the shared code with a test (a hand-built multi-day M1 series run through the runner path on D1). If D1 is
genuinely unsupported for research runs, say so and propose the smallest fix. Do not change the grids or
the spec. Then run both grids above with `--dev-only` and report the per-cell lines. `python -m pytest
tests/engine tests/tools tests/strategy/trend_following -q` green (or the matching paths), ruff clean.
Report root cause, files, tests, run output.
