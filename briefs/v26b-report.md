# V2.6 step 2 — implementation handoff

Implementation is ready for Opus's independent review and the user's acceptance.
No ROADMAP checkbox was marked done. No commits, pushes, branches, terminal sessions,
downloads, servers or cache rebuilds were performed. No production cache or raw file was
changed. Tests use temporary caches and fake MT5 sessions. Work was performed alone.

## Clock evidence

- `results/clock_check_histdata.md`: 920 original-cache edge observations across both
  feeds; every sampled 2015–2018 DST-gap GBPUSD Sunday open is one hour late under the
  old conversion. Friday FX/gold closes corroborate the US DST correction. 2019–2021
  FX edges support retaining the existing European-date rule. Normal weeks are unchanged.
- `results/clock_check_mt5.md`: 384 daily price matches and 77 H1 weekly matches against
  corrected histdata, using `mt5_compare.weekly_offsets` without a terminal connection.
  Sampled pre-2020 daily proofs: 2015 60/60, 2016 48/49, 2017 50/50, 2018 50/50,
  2019 35/60. The table and CSV identify unproven sampled dates; these are samples,
  not approval of all unsampled days. Each queued repair proves every affected day.
- No universal pre-2020 MT5 clock was inferred. Missing pre-2015 references mean those
  non-empty MT5 days are excluded. Other pre-2020 days without a clear direct price
  match, including MT5-only symbols without histdata, are excluded too. Empty weekends
  remain closed days. Sparse/empty weekdays are excluded using the configurable
  symbol/year median threshold (default strictly below 50%). Histdata fills absent MT5
  days wherever available; missing MT5-only data stays visibly missing.
- Open finding: XAUUSD's 2020 and March 2021 overlap also has a one-hour residual,
  contrary to a universal NY+7 rule from 2020. Modern clock correction is outside this
  pre-2020 repair; it needs a separate decision. Modern timestamps are unchanged.
- Reproduce the bounded read-only measurements with `python scripts/v26b_clock_evidence.py`
  against original caches. Edge/match passes took approximately 1.6/5.4 seconds; each
  enforces a 540-second bound. Logs: `results/v26b_clock_edges.log`,
  `results/v26b_clock_match.log`; dated CSVs: `results/v26b_clock_edges.csv`,
  `results/v26b_clock_matches.csv`, `results/v26b_clock_weekly.csv`.

## Implementation

- Histdata: date-dependent zoneinfo conversion, explicit transition errors, configurable
  daily-close continuity validation before writes, and removal/exclusion of GER40 UTC
  cache days from 2020-06-15. Adjacent year files already combine correctly in one import;
  the regression checks both halves of January 1. Disconnected periods are not compared
  as consecutive closes. Documented jump exemptions require a date, symbol and reason.
- Offline MT5 repair: per-day price proof, UTC re-bucketing, retained originals,
  per-symbol file locks, staging before active writes and dated per-day decision reports.
  Reruns use retained originals and cannot shift the same inputs twice. Modern density
  filtering can also exclude anomalously sparse modern days; Opus must stop if that
  changes any 2023 golden trade list.
- Downloader: only validated-symbol `RES_E_NOT_FOUND` becomes `Mt5NoHistory`; other
  first-chunk errors fail with nonzero status. Later errors always propagate. Today/future
  end dates and reversed ranges fail before connecting. Binance daily 404 holes retry once.
- Tools: clean show/trials validation, shared MT5 spread defaults, one-year M1 reads in
  check with cross-year gaps and exact full-history M5 median. Outlier thresholds are
  explicitly per year. Monte Carlo default folders include source, seed and runs, also
  for saved runs; explicit output overrides remain unchanged. No `--part` users remain.
- Cache day writes use unique temporary names, atomic replacement and bounded Windows
  sharing retries, following V2.6a's pattern. Repair reuses `filelock.py`.
- Packaging/cleanup: numpy/requests are included in the data extra; ignore comments are
  on separate lines and the named stray hook file is ignored.

## Rebuild handoff — not executed

`scripts/rebuild_cache_v26b.md` has 21 histdata jobs and 26 offline MT5 repair jobs.
Drain and verify stage 1 before adding stage 2. Nine duplicate raw CSV/ZIP periods
matched after newline normalization; the plan selects plain CSVs and imports every
neighbouring year together. Raw files remain untouched. Retain MT5 originals under
`data/cache/mt5/_v26b_original/`; inspect per-day exclusions in `_v26b_reports/`.

Opus runs the rebuild, data check and golden check afterwards. Golden lists were neither
run nor regenerated here. Stop and report any 2023 golden difference.

The named stray hook file, `.vscode/` and `data/cache/dukascopy/` were absent.
**Removed: nothing.**

## Files changed

- `.gitignore`, `pyproject.toml`, `docs/ARCHITECTURE.md`
- `src/backtester/data/adapters/mt5_adapter.py`
- `src/backtester/data/binance.py`, `cache.py`, `histdata.py`, `mt5_download.py`
- New `src/backtester/data/cache_repair.py`
- `src/backtester/tools/check.py`, `monte_carlo.py`, `mt5_download.py`, `show.py`,
  `spread_table.py`, `trials.py`
- New `src/backtester/tools/cache_repair.py`
- `tests/tools/test_monte_carlo_tool.py` (old folder-name expectations updated to the
  explicitly requested source/seed/run suffix, not weakened)
- New `tests/data/test_v26b_data.py`, `tests/tools/test_v26b_tools.py`
- New `briefs/v26b-test-cases.md` (written first), this report,
  `scripts/v26b_clock_evidence.py`, `scripts/rebuild_cache_v26b.md`
- Git-ignored evidence/log artifacts under `results/` listed above and `results/pytest_v26b.log`

## Validation

The initial regression run failed on the expected defects before implementation.
The first full run exposed two obsolete Monte Carlo path assertions and an empty-cache
check edge case; all were resolved against the requested behavior. Subsequent targeted
tests also cover malformed year placement, sparse history, explicit fake MT5 failures,
UTC-midnight preservation and queue command validity. No test expectation was weakened.

Final command: `.venv/Scripts/python.exe -m pytest -q tests/data tests/tools > results/pytest_v26b.log 2>&1`.
Result: **715 passed**, 20 existing pandas deprecation warnings, 144.01 seconds.
The 48 new regressions also passed in the focused run. Ruff and `git diff --check`
passed on the changed files. Independent cross-review, cache rebuild/data check,
golden check and the user's acceptance remain for Opus.
