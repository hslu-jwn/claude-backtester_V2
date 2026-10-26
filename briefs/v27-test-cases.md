# V2.7 test cases (written before implementation)

- Search: two opposite daily series cancel exactly; correlation -1; equal weights;
  leave-one-out of two members equals the remaining single series.
- Hand-calculated drawdown includes initial zero; worst calendar month; drawdown length
  counts observed trading days, including an unrecovered final drawdown; Sharpe uses 252.
- Align only intersecting days, keep joint zeros, report union days dropped and each member's
  dropped days; warn below 250, including zero common days. Flat ratios are undefined/null.
- Reject duplicate identities/dates, nonfinite R, unsorted dates, any date on/after cutoff,
  non-development provenance, pools outside 2..12. Enumerate all 781 sets for twelve members.
- Regimes: separate symbol/day attribution, unknown history explicit, no pooled-symbol vote;
  no use of the day's unfinished D1. Leave-one-out recomputes on the remaining common days.
- Members: only chosen research variants; validate research period, saved run period, daily
  dates and trade timestamps. Never read test.csv or use test flags/results. No backtest.
- Cache: stable identities regardless of pool order; changed daily content invalidates cache.
- Queue: at most ten unique jobs, selected metric/direction determines rank; no --test,
  --retest or backtest. Worker revalidates development provenance before using saved trades.
- CLI: --test needs only set ID; MT5 start fixed at cutoff; same sorted member set refused
  even if order/end changes; reservation made before execution, survives failure/concurrency;
  successful test recorded in trials and stored separately from development results.
- UI: Portfolio navigation/route; development labels, pool/metrics/details, queue panel;
  no test button/results. Callback registration without launching app; empty/broken files.
- Run requested analytics/tools/UI tests only, log to results/pytest_v27.log; ruff touched files.
- Benchmark twelve members (781 sets), target under 30 seconds.

## Review fixes (2026-10-26, before implementation)

- Missing daily CSV: validate development trades first, rebuild with research_series.ensure,
  retain weekdays and both R columns/position, reuse the saved file on the next load.
- Missing trades: member stays ineligible with the pipeline instruction, no raw OS error.
- Invalid development period or holdout trade: refuse before writing a missing daily series.
- Interval callback updates only the Monte Carlo block; selection renders the static detail.
- Search cache invalidates on classifier config/implementation and development D1 data changes;
  identical inputs reuse it and holdout data never enters regime computation.
- Custom results directories share the default trial log and permanent test reservation;
  attempts recorded there, including failed attempts, prevent reruns from another directory.
