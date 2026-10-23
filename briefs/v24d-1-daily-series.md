# Brief: V2.4d items 1 + 2 — daily series of every variant, marked to market

Context: ROADMAP › V2.4d (accepted by the user 2026-10-23), `docs/review/book-app-requirements.md`
B1 and E1 (Masters ch.5-6, Aronson ch.6). Today `analytics/daily.py` books a whole trade on its
exit day, and the trial log (`analytics/trial_log.py`, `results/trials.jsonl`) keeps only summary
statistics per variant. The best-of-N tests, PBO and effective N (next briefs) need the full daily
series of every variant.

## What to build

1. **Marked-to-market daily net R** (`analytics/daily.py`, new function next to `daily_net_r`;
   do not change `daily_net_r` itself or its callers yet):
   - Days as today: weekdays of the period, cut at midnight `Europe/Prague`, empty days 0.
   - A trade open across a day cut is valued at that cut: unrealized R =
     direction x (mark - entry fill) / stop distance, where mark = the close of the last M1
     candle that closed at or before the cut. Candles are bid prices: a long is marked at that
     close (the price it could sell at), a short at close + the trade's spread (the price it
     could buy back at), as the engine's exits do (`engine/costs.py`). Each day gets the
     change of value since the previous cut; the exit day gets the rest, so **the days of a
     trade sum to its `r_net` exactly** (test with a tolerance of 1e-9).
   - Costs: entry spread and entry commission on the entry day (they are known then), swap on
     the day whose cut follows the rollover it is charged at (`swap_r` spread over its nights;
     if the night count is not recoverable from the trade, on the exit day and say so in the
     spec), exit costs on the exit day. Funding like swap.
   - Prices come from the cached M1 candles through `SymbolSources` (one read per symbol and
     run of consecutive cached days, as `tools/research_diagnostics.load_shocks` does). The
     function takes trades + sources; a pure core takes trades + a mapping
     (symbol, cut) -> mark so tests need no cache.
   - Also return per day the **position**: the sum over open trades of direction x 1 for the
     time the trade was open that day (share of the day, so 0.5 = long half the day), for the
     detrended benchmark later (V2.4d item 7).
2. **Daily series of every variant kept** (E1):
   - The research runner writes `variants/<id>/daily.csv` (date, net_r_exit_booked,
     net_r_mtm, position) for every development variant, every sensitivity neighbour and every
     test run, resumable like the scorecard (an existing finished variant without the file gets
     it from its saved trades on the next run, without re-running the backtest).
   - `TrialRecord` gets an optional `series` field: the path of that file relative to the
     results folder (None on old lines and on tools that keep no series). `run.py`,
     `tools/entry_screen.py`, `tools/monte_carlo.py` and `tools/portfolio.py` keep working
     unchanged (series None) unless adding it is trivial.
   - A reader `trial_log.read_series(record, results_dir)` -> (dates, values) for one series
     kind, and `series_matrix(records, kind)` -> dates x variants aligned on the union of dates
     (missing days 0), for the next briefs.
3. The daily statistics already in the trial log (`day_mean`, `day_sharpe`, ...) and the DSR
   stay on the exit-booked series for now (no result change in this brief); the spec says so.

## Rules

Spec first (`docs/risk-management.md` › Trial log and deflated Sharpe, and
`docs/research-runner.md` › Output), then the test-case list at the top of the new test file,
failing tests, then code. Hand-built trades and marks in tests: at least a long and a short over
three day cuts with a weekend, a trade inside one day, a gap across the cut, swap nights, two
symbols, a trade exiting exactly at a cut. No lookahead: a mark at a cut uses only candles closed
by the cut. No change to any trade, scorecard, ranking or golden list. Never edit
`src/backtester/live/`. Long runs to log files.

Done = full suite green (`pytest -q > results\pytest_v24d1.log 2>&1`), `ruff check .` and
`ruff format --check` on changed files clean. Report: files changed, test count, decisions the
spec did not settle, open questions.

## Answer from Opus (your question of 15:38)

Book the trade's whole `commission_r` on its entry day, for every commission model
(conservative; the trade's days still sum to `r_net` exactly). No cost settings needed; the same
rule for old runs. Write this rule into the spec. Swap: when the night count is not recoverable,
spread `swap_r` evenly over the day cuts the trade was open across (no cut: the exit day).
Go ahead with the brief.
