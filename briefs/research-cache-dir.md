# Brief: research runner `--cache-dir` (pre-sample checks)

Read `AGENTS.md` first; its hard limits apply (no commits, no servers, no `live/`, no `.env`).

## Goal

Let the research runner read a separate histdata cache folder, so a strategy can be run on an
untouched pre-sample (e.g. `data/cache/histdata_presample/`, EURUSD / GBPUSD 2008-2014) without
touching the main cache or the fixed development / test split. Background and line references:
`knowledge/research/reports/2026-11-09_presample_2008_2014_plan.md` › 3 (read it; it names
`research.py` lines for `parse_args`, `run_research(..., sources=...)`, `--results-dir`).

## Files

- `src/backtester/tools/research.py` (CLI only: `parse_args` / `main`)
- `tests/tools/` - add tests to the existing research CLI test file (find it: grep `parse_args`
  or `--dev-only` in `tests/tools/`), or a new `tests/tools/test_research_cache_dir.py`
- `docs/research-runner.md`: one short paragraph in the CLI / flags section
- Nothing else.

## Behaviour

- New optional flag `--cache-dir PATH`. When given, the runner uses
  `SymbolSources.single(PATH, <the grid's symbols>)` (find `SymbolSources.single` in
  `src/backtester/data/sources.py`; if it does not exist, use the existing constructor the way
  `timed_hold_gates.py` builds sources from `cache_dirs`) instead of `DEFAULT_SOURCES`, passed
  through the existing `sources=` parameter of `run_research`. Without the flag nothing changes.
- A non-existing folder, or a grid symbol without a subfolder there, is a clear `SystemExit`.
- The flag does not change the development / test cutoff logic (a cache ending before 2021-09-14
  simply has no test data; `--dev-only` still works).
- `--cache-dir` must be recorded in the run's saved settings the same way the existing runs record
  `cache_dirs` (check `runner.py`), so `tools/timed_hold_gates.py` finds the right data.

## Tests

1. `parse_args([... "--cache-dir", "x"])` gives the path; default None.
2. With a tmp cache folder holding a symbol subfolder, `main` passes sources pointing at it to
   `run_research` (monkeypatch `run_research` to capture the argument; no real backtest).
3. Missing folder / missing symbol subfolder -> SystemExit with a message naming it.
4. Without the flag, `run_research` gets the default sources (unchanged behaviour).

## Done =

New tests green, `python -m pytest tests/tools -q` green, `python -m ruff check .` clean. Report
files changed, tests, anything unclear.
