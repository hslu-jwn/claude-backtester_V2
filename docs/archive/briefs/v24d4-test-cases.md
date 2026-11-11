# V2.4d item 4 test cases

Spec: docs/risk-management.md > Monte Carlo report.

1. Default stationary bootstrap is seeded/reproducible, correctly shaped, in range;
   zero days and one day; repeats/omissions and drawdown exceeding historic drawdown.
2. Permutation preserves every day, total R, exact seeded orders and historic numbers.
   Pin permutation-specific existing tests explicitly, retain all expected values.
3. Block starts uniform; continuations wrap; inferred restart frequency (corrected for
   accidental adjacent restarts) implies configured geometric mean. Mean 1 is iid.
4. Invalid sampling/block lengths, nonfinite R, dimensions, counts, horizon rejected.
5. Additive maximum drawdown includes initial zero; hand series [2,-3,-2,4,-1] = 5 R;
   constant -1 gives horizon R; positive/zero series gives zero; empty unavailable.
6. Double bootstrap reproducible, monotone in q and bound confidence; risk percent =
   R * risk * 100. Independent reference loop verifies nested sampling/quantiles.
7. Reports contain sampling, block length, source, R and percentage bounds in HTML/JSON.
   MTM daily file preferred; missing file/legacy column falls back; invalid data rejected.
8. Research chosen dev and completed test outputs get bounds and report blocks;
   dev-only/resume preserve once-only test guard. Consumers share sampled orders.
9. Benchmark 200 x 1000 x 126 under a minute; comparison uses golden setup strategies
   4/6/7; full pytest, golden --check and ruff logged. No golden reference changes.

Implementation and tests require independent Opus review; no self-approval.
