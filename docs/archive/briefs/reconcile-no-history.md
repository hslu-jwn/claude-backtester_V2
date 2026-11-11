# Brief: `tools/reconcile.py` explains engine-only trades caused by "no_history" at bot start (ROADMAP 12.5)

Read `AGENTS.md` first; hard limits apply (no commits, no servers, never edit `src/backtester/live/` or
`.env`, never print credentials). The user asked for this (2026-11-10). Test first; never weaken a test.

## Why

Reconciliation of runs 3 + 4 (`results/reconcile_2026-11-09/`) left 15 engine-only trades "unexplained"
at 2026-11-03 11:30 UTC; the cause (found by reading `results/live/probe_stdout_run3.log`, UTF-16): at
the 11:21 start the bot logged `no_history` for those 15 symbols, so it never traded them then. Brief
`briefs/reconcile-1103-1130.md` and its answer `results/ai/20261109-224422_codex_reconcile_1130.md` have
the details.

## Change

- Read the bot's probe stdout logs in `--live-dir` (`probe_stdout*.log`; detect UTF-16 / UTF-8). The lines
  carry only a time of day: find each run's start date from evidence already in the live dir (e.g. the
  per-date folders / paper or trade records of the first orders after the start); if a start date cannot
  be established, skip that log and say so in the report (never guess a date).
- Rule: an engine-only trade of symbol S whose signal time lies after a bot start at which S was logged as
  `no_history`, and before the bot's first trade, paper fill or later non-`no_history` evaluation of S
  after that start, gets the explanation "no price history at bot start". Existing explanations take
  precedence; nothing else changes.
- Report section: per run start, the symbols with no_history.

## Tests (first, `tests/tools/test_reconcile.py` or next to the existing ones)

Hand-built live dir: a UTF-16 log with a start line and no_history for one symbol -> its engine-only
trade at the next signal is explained, another symbol's is not; a trade after the symbol's first fill
is not explained by this rule; a log whose date cannot be established is skipped and reported; existing
tests unchanged.

## Done =

`python -m pytest tests/tools -q` green, `python -m ruff check .` clean; rerun `python -m
backtester.tools.reconcile --since 2026-11-03T11:21:00+00:00 --until 2026-11-09T08:39:00+00:00 --out
results/reconcile_2026-11-09` and report the counts (expected: 0 unexplained). Report files and tests.
