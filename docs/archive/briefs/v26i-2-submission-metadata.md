# Brief V2.6i step 2: submission identity in research runs (Codex, medium)

Read first: `docs/research-intake.md`, `docs/research-runner.md` (grid file format, trial log,
one-time test), `src/backtester/tools/research_grid.py` (`load_grid`, `GridSpec`, `TOP_LEVEL`),
`src/backtester/tools/research.py` (where `info` is built and written, where trials are appended,
the `--test` / `--retest` path), `src/backtester/analytics/trial_log.py` (`TrialRecord`, `key`),
`src/backtester/tools/intake.py` (step 1). AGENTS.md rules apply (test first). No change to
engine, strategies, live, data adapters or trading semantics: a grid without `[submission]`
must behave exactly as today (same files, same trial lines, same results).

## 1. Grid file: optional `[submission]` table

```toml
[submission]
strategy_id = "US500_FINAL30_CONT"
specification_version = "0.2.0"
submission_sha256 = "<64 lowercase hex>"
experiment_id = "US500_FINAL30_CONT__v0.2.0__DEVELOPMENT__1"
```

`load_grid` validates: exactly these four keys; `strategy_id` matches
`^[A-Z][A-Z0-9_]{2,63}$`; version `^[0-9]+\.[0-9]+\.[0-9]+$`; sha256 `^[a-f0-9]{64}$`;
experiment_id == `<strategy_id>__v<version>__DEVELOPMENT__<n>` with n >= 1 (the grid only ever
names the development experiment; the test experiment ID is derived, see 3). Any problem ->
`GridError` naming the key. Add `submission: dict | None = None` to `GridSpec` and
`"submission"` to `TOP_LEVEL`.

## 2. Where the identity is recorded

- `info.json` of the research folder: `info["submission"] = spec.submission` (key only when
  present).
- Every `TrialRecord` written for that grid: new optional field `submission: dict | None = None`
  (last field, default None, **not** part of `key`, omitted from the JSON line when None so old
  lines and grids without a submission are byte-identical).
- `info["dataset"]`: for a grid with `[submission]` only, `{"dataset_id": "v2-cache",
  "version": <sha256>, "symbols": [...], "start", "end", "source_summary"}` where version is
  the sha256 of the sorted lines `<symbol>\t<relative cache file path>\t<size>` of every cache
  file the run's symbols resolve to through `DEFAULT_SOURCES` (look at how `data/sources.py`
  and `data/cache.py` locate day files; sizes, not contents, so it stays fast), and
  source_summary names the cache dirs. Put the function in `tools/intake.py` as
  `dataset_version(symbols, start, end, sources) -> dict`.
- `info["code_commit"]` = `git rev-parse HEAD` of the repo (short is fine) for every run, and
  `info["code_dirty"]` = True when `git status --porcelain` is non-empty (catch any git error ->
  None). Existing runs without the keys must still load everywhere (UI, pipeline, portfolio).

## 3. One-time test gate for submissions

The research runner runs the one-time test automatically after development unless
`--dev-only` (see `run_research` around the `test_info` / `retest` logic). For a grid with
`[submission]`, the test part (first test and `--retest`) runs only if the file below exists;
otherwise the development part runs as usual, the test is skipped exactly as with `--dev-only`,
and the log / `report.md` say one line: "test skipped: no user authorization for <stem>".
Required file:
`results/intake/<strategy_id>__v<version>/test_authorization.json` exists and contains
`{"authorized_by": "user", "quote": <non-empty text>, "authorized_at": <ISO time>,
"experiment_id": <the development experiment_id of this grid>}`. Opus writes that file only
after the user's explicit go in chat, quoting the user's words; no code path writes it. The test
run records `info["submission"]` with `experiment_id` replaced by
`<strategy_id>__v<version>__FINAL_HOLDOUT__1` (`__2` for a retest, counting existing ones in the
trial log or info). Grids without `[submission]` keep today's behaviour exactly.

## Test cases (first)

grid without `[submission]` loads to `submission=None` and produces identical trial lines
(compare the JSON of a TrialRecord with and without the new field: no `submission` key when
None); each bad key / pattern / extra key / wrong experiment_id -> GridError naming it; good
table -> GridSpec.submission; TrialRecord.key unchanged by `submission`; `dataset_version` is
deterministic, changes when a cache file's size changes, and lists only the run's symbols;
test gate: no file -> development runs, test skipped (no test trial line, test status stays
not_run, the skip line in the log); file with authorized_by != "user" or empty quote or another
experiment_id -> skipped the same way; `--retest` without the file -> skipped; valid file ->
test runs (stub the actual test run as the existing
research tests do); a grid without `[submission]` is never gated. Use the existing research
test fixtures (look at `tests/tools/test_research*.py`) and tmp folders; never write the real
`results/`.

## Done =

New and existing research / trial-log / grid tests green (`pytest tests/tools tests/analytics
-q`), `ruff check . && ruff format --check .` clean, files changed only:
`tools/research_grid.py`, `tools/research.py`, `analytics/trial_log.py`, `tools/intake.py`,
their tests, `docs/research-runner.md` (a short `[submission]` section). Do not commit. Report
files changed, tests, open questions.
