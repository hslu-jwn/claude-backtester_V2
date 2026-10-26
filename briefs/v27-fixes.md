# Brief: V2.7 portfolio fixes (Opus, 2026-10-26)

Your V2.7 work (`briefs/v27-portfolio.md`) was reviewed (Sonnet) and checked in the browser by
Opus. Fix these, test-first, same rules as the V2.7 brief. Run only your tests
(`pytest -q tests/analytics/test_portfolio_search.py tests/tools/test_portfolio*.py tests/ui > results\pytest_v27_fix.log 2>&1`) + ruff.

1. **Grids without daily series give an empty pool (browser).** `orb_example_ccd88137` (run
   before V2.4d) has no `variants/v0000/daily.csv`; the page shows "0 eligible members" and a raw
   `[Errno 2] No such file ...` line. Fix: when `daily.csv` is missing, build the member's daily
   series from its development trade list exactly as `research_series.ensure` would (same
   function and definition: weekdays, exit-booked and marked-to-market columns, the same
   development period); write it with that function (it is resumable and locked) so the next
   load reads it, and keep every existing development-only guard. If the trades are missing too,
   the member is listed as not eligible with a plain sentence ("Run this grid's pipeline first:
   Research › Queue a grid"), never a raw exception text. Tests for both.
2. **Detail panel resets every 5 s** (`ui/pages/portfolio.py` ~333-347): `_detail` also fires
   on `pf-refresh`, so open `details`, table sort and graph zoom reset. Only the Monte Carlo /
   job block may refresh on the interval (separate callback / output); the rest renders on
   selection only. Test: an interval tick does not touch the detail panel's other outputs.
3. **Search cache misses classifier changes** (`portfolio_candidates.py` ~141-145): add the
   regime classifier's config / version and the D1 data stamp (e.g. the last cached D1 day per
   member symbol) to the cache key, so a changed classifier or new D1 data recomputes. Test.
4. **`--test` bypass via `--results-dir`** (`portfolio_candidates.py` ~302-312, `run_test`): the
   one-time rule must hold for the default trial log regardless of `--results-dir`: for `--test`
   always check and record in the default `results/` trial log and reservation (or refuse
   `--results-dir` together with `--test`; pick one, document it in `docs/portfolio.md`). Test.

Report: files changed, test results, which option you chose for 4.
