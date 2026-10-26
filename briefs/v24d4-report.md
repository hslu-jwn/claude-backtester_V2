# V2.4d item 4 implementation report

Implemented stationary day bootstrap as the kind A default, retaining exact seeded
permutation orders on request. One order matrix drives account statistics, fan paths,
FTMO challenge/funded phases, adaptive risk, prop cards and risk sweeps; an integration
test verifies the shared results. Whole Days retain their trades and intraday ordering.

Added pure, vectorized Masters-style double-bootstrap bounds on additive daily R:
200 outer histories, 1,000 inner paths, horizon 126 trading days, mean block length 5,
seed 42. JSON and reports show each drawdown quantile's median, 90% and 95% upper bounds
in R and percent balance for all configured risk levels. The Monte Carlo tool uses saved
MTM daily R when available; otherwise saved/calculated exit-booked daily R. Research
writes bounds beside the chosen variant, its published development run and completed
test runs, and adds report blocks without starting an unspent test.

Added and executed `scripts/measure_bootstrap.py` sequentially on the golden setup for
strategies 4, 6 and 7. Complete measured tables follow below. The default
200 x 1000 x 126 bounds calculations took **0.828 / 0.713 / 0.707 seconds** respectively.

## Validation

- Spec, test-case list and failing tests preceded implementation. Additional validation
  edge cases were likewise demonstrated failing before their fixes. Existing numerical
  permutation regression assertions retain every expected value and explicitly select
  `sampling="permutation"`.
- `.venv/Scripts/pytest.exe -q > results/pytest_v24d4.log 2>&1`:
  **3,827 passed, 5 skipped, 1 xfailed, 44 warnings**, 323.64 seconds, exit 0.
- `.venv/Scripts/python.exe -m backtester.tools.golden --check --workers 1
  > results/golden_v24d4.log 2>&1`: all seven reference lists identical, **9,002 trades**,
  exit 0. Golden references were not edited. One worker honors the no-parallel-work request.
- `.venv/Scripts/ruff.exe check . > results/ruff_v24d4.log 2>&1`: all checks passed.
- `.venv/Scripts/python.exe scripts/measure_bootstrap.py
  > results/measure_bootstrap.log 2>&1`: exit 0; writes `results/bootstrap_compare.md`,
  `results/bootstrap_compare.json` and per-strategy daily series / bounds / Monte Carlo JSON
  under `results/bootstrap_compare/`.

## Implementation choices where the brief did not prescribe details

- Quantiles use numpy's linear interpolation; drawdown includes the initial zero equity
  peak. Empty daily input is explicitly unavailable.
- Saved daily series must cover the complete ordered weekday calendar. Malformed headers,
  missing dates/values and nonfinite values raise errors; they never silently fall back.
  Legacy files with a valid exit-booked column remain supported.
- Bounds are recomputed on research resume, avoiding a stale cache after changes to the
  daily series. Only selected development and completed test runs get bounds.
- Existing historic trade-list descriptive statistics and FTMO attempt definitions are
  retained. FTMO pass/breach rates condition on finished attempts; the comparison also
  includes the unfinished share. With no finished attempts, the existing MC pass field
  is 0 and the comparison's breach field is n/a; neither establishes a probability.
- Added the repository root to pytest's configured import path. The requested `pytest -q`
  launcher otherwise failed collection of root-relative helpers (including an existing test),
  whereas `python -m pytest` worked.

## Files changed

Specification and handoff:

- `docs/risk-management.md`
- `docs/research-runner.md`
- `briefs/v24d4-test-cases.md`
- `briefs/v24d4-report.md`

Implementation and measurement:

- `src/backtester/risk/bootstrap.py` (new)
- `src/backtester/risk/drawdown_bounds.py` (new)
- `src/backtester/risk/monte_carlo.py`
- `src/backtester/tools/drawdown_report.py` (new)
- `src/backtester/tools/monte_carlo.py`
- `src/backtester/tools/research.py`
- `scripts/measure_bootstrap.py` (new)

Tests and test configuration:

- `pyproject.toml`
- `tests/risk/test_bootstrap.py` (new)
- `tests/risk/test_drawdown_bounds.py` (new)
- `tests/risk/test_monte_carlo.py`
- `tests/risk/test_adaptive_risk.py`
- `tests/tools/test_drawdown_report.py` (new)
- `tests/tools/test_measure_bootstrap.py` (new)
- `tests/tools/test_research_bounds.py` (new)
- `tests/tools/test_monte_carlo_tool.py`

## Open questions and review status

No unresolved trading-rule questions and no new stubs. Opus must independently review
every risk-code line and rerun the checks; this report is not self-approval. The roadmap
checkbox is unchanged pending user confirmation. No commits, pushes, branches, protected
live-code changes or credential access were performed.

## Measured comparison

# Bootstrap comparison (V2.4d item 4)

Golden setup, 2023-01-01..2023-12-31, seed=42, runs=1000, block_days=5, DD alert=10%. Whole-day account replay compounds risk; bounds use additive daily MTM R.

FTMO pass/breach probabilities condition on finished attempts (both phases). Unfinished share is shown separately, as in the existing report. This comparison changes no further defaults. Bootstrap need not increase every statistic.

| Strategy | Sampling | Risk | Median DD % | P95 DD % | P(DD > alert) | FTMO pass | FTMO breach | Unfinished |
|---|---|---|---|---|---|---|---|---|
| trend_following | permutation | 0.5% | 7.383 | 10.930 | 10.7% | 6.1% | 93.9% | 95.3% |
| trend_following | permutation | 1% | 14.358 | 20.768 | 93.4% | 32.1% | 67.9% | 37.4% |
| trend_following | permutation | 1.5% | 20.923 | 29.688 | 100.0% | 8.3% | 91.7% | 15.6% |
| trend_following | block_bootstrap | 0.5% | 8.004 | 15.174 | 29.9% | 47.1% | 52.9% | 68.6% |
| trend_following | block_bootstrap | 1% | 15.513 | 28.178 | 87.0% | 33.2% | 66.8% | 30.8% |
| trend_following | block_bootstrap | 1.5% | 22.501 | 39.428 | 99.2% | 10.7% | 89.3% | 13.7% |
| opening_range | permutation | 0.5% | 34.209 | 45.215 | 100.0% | 16.9% | 83.1% | 11.9% |
| opening_range | permutation | 1% | 57.890 | 70.711 | 100.0% | 12.6% | 87.4% | 3.3% |
| opening_range | permutation | 1.5% | 73.616 | 84.635 | 100.0% | 0.0% | 100.0% | 0.0% |
| opening_range | block_bootstrap | 0.5% | 33.376 | 52.301 | 100.0% | 16.0% | 84.0% | 12.9% |
| opening_range | block_bootstrap | 1% | 56.789 | 78.150 | 100.0% | 10.9% | 89.1% | 3.5% |
| opening_range | block_bootstrap | 1.5% | 72.677 | 90.379 | 100.0% | 0.0% | 100.0% | 0.0% |
| gap_momentum | permutation | 0.5% | 1.627 | 2.573 | 0.0% | 0.0% | n/a | 100.0% |
| gap_momentum | permutation | 1% | 3.236 | 5.094 | 0.0% | 0.0% | n/a | 100.0% |
| gap_momentum | permutation | 1.5% | 4.825 | 7.562 | 0.4% | 89.7% | 10.3% | 96.1% |
| gap_momentum | block_bootstrap | 0.5% | 1.954 | 3.944 | 0.0% | 0.0% | n/a | 100.0% |
| gap_momentum | block_bootstrap | 1% | 3.892 | 7.760 | 1.5% | 90.8% | 9.2% | 88.2% |
| gap_momentum | block_bootstrap | 1.5% | 5.804 | 11.449 | 8.8% | 83.4% | 16.6% | 63.5% |

## Double-bootstrap trend_following

marked_to_market; 260 historic days; horizon 126 days; outer=200, inner=1000, block_days=5, seed=42. Fixed-fraction bounds (no compounding).

| DD quantile | Units | Median | 90% upper | 95% upper |
|---|---|---|---|---|
| 50% | R | 13.946 | 20.639 | 23.440 |
| 50% | % balance at 0.5% risk | 6.973 | 10.319 | 11.720 |
| 50% | % balance at 1% risk | 13.946 | 20.639 | 23.440 |
| 50% | % balance at 1.5% risk | 20.919 | 30.958 | 35.161 |
| 90% | R | 24.502 | 34.652 | 38.942 |
| 90% | % balance at 0.5% risk | 12.251 | 17.326 | 19.471 |
| 90% | % balance at 1% risk | 24.502 | 34.652 | 38.942 |
| 90% | % balance at 1.5% risk | 36.753 | 51.978 | 58.413 |
| 95% | R | 28.350 | 40.129 | 44.080 |
| 95% | % balance at 0.5% risk | 14.175 | 20.065 | 22.040 |
| 95% | % balance at 1% risk | 28.350 | 40.129 | 44.080 |
| 95% | % balance at 1.5% risk | 42.525 | 60.194 | 66.120 |
| 99% | R | 36.463 | 48.087 | 51.851 |
| 99% | % balance at 0.5% risk | 18.232 | 24.043 | 25.925 |
| 99% | % balance at 1% risk | 36.463 | 48.087 | 51.851 |
| 99% | % balance at 1.5% risk | 54.695 | 72.130 | 77.776 |

Bounds runtime: 0.828s.

## Double-bootstrap opening_range

marked_to_market; 260 historic days; horizon 126 days; outer=200, inner=1000, block_days=5, seed=42. Fixed-fraction bounds (no compounding).

| DD quantile | Units | Median | 90% upper | 95% upper |
|---|---|---|---|---|
| 50% | R | 49.088 | 69.732 | 72.585 |
| 50% | % balance at 0.5% risk | 24.544 | 34.866 | 36.292 |
| 50% | % balance at 1% risk | 49.088 | 69.732 | 72.585 |
| 50% | % balance at 1.5% risk | 73.632 | 104.598 | 108.877 |
| 90% | R | 83.965 | 108.980 | 114.720 |
| 90% | % balance at 0.5% risk | 41.982 | 54.490 | 57.360 |
| 90% | % balance at 1% risk | 83.965 | 108.980 | 114.720 |
| 90% | % balance at 1.5% risk | 125.947 | 163.470 | 172.079 |
| 95% | R | 94.471 | 120.938 | 127.353 |
| 95% | % balance at 0.5% risk | 47.236 | 60.469 | 63.677 |
| 95% | % balance at 1% risk | 94.471 | 120.938 | 127.353 |
| 95% | % balance at 1.5% risk | 141.707 | 181.407 | 191.030 |
| 99% | R | 115.319 | 143.301 | 152.413 |
| 99% | % balance at 0.5% risk | 57.659 | 71.651 | 76.206 |
| 99% | % balance at 1% risk | 115.319 | 143.301 | 152.413 |
| 99% | % balance at 1.5% risk | 172.978 | 214.952 | 228.619 |

Bounds runtime: 0.713s.

## Double-bootstrap gap_momentum

marked_to_market; 260 historic days; horizon 126 days; outer=200, inner=1000, block_days=5, seed=42. Fixed-fraction bounds (no compounding).

| DD quantile | Units | Median | 90% upper | 95% upper |
|---|---|---|---|---|
| 50% | R | 2.675 | 3.725 | 4.051 |
| 50% | % balance at 0.5% risk | 1.338 | 1.863 | 2.026 |
| 50% | % balance at 1% risk | 2.675 | 3.725 | 4.051 |
| 50% | % balance at 1.5% risk | 4.013 | 5.588 | 6.077 |
| 90% | R | 4.886 | 6.831 | 7.415 |
| 90% | % balance at 0.5% risk | 2.443 | 3.415 | 3.708 |
| 90% | % balance at 1% risk | 4.886 | 6.831 | 7.415 |
| 90% | % balance at 1.5% risk | 7.330 | 10.246 | 11.123 |
| 95% | R | 5.743 | 8.024 | 8.731 |
| 95% | % balance at 0.5% risk | 2.871 | 4.012 | 4.365 |
| 95% | % balance at 1% risk | 5.743 | 8.024 | 8.731 |
| 95% | % balance at 1.5% risk | 8.614 | 12.036 | 13.096 |
| 99% | R | 7.382 | 10.103 | 11.070 |
| 99% | % balance at 0.5% risk | 3.691 | 5.051 | 5.535 |
| 99% | % balance at 1% risk | 7.382 | 10.103 | 11.070 |
| 99% | % balance at 1.5% risk | 11.073 | 15.154 | 16.605 |

Bounds runtime: 0.707s.
