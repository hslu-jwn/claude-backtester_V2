# Brief: R10 backfill of the ledger effect columns (lead review intake 2026-11-26, R10)

Worker: Claude Sonnet subagent. Coordinator: Opus (checks, commits). Read first: `AGENTS.md`, `docs/research-runner.md`
› Ledger (the "Effect columns" bullet defines every column and allowed value), and
`../lead-research-2026-11-21/10-wave2-stacking-and-pooling.md` › "C. Empirical-Bayes prior per family type" (why).

## Task
Fill the 7 columns `est, se, est_unit, est_basis, est_sample, type, dup_group` of `research/ledger.csv`. This is
bookkeeping from records already written; **never run a screen, read market data or compute a new result**.

1. `type` (a-f) for every non-harvest row (ids not starting with `HV-`). Leave HV rows blank.
2. `est` / `se` for every row with a data look (stage screened, dev_tested, tested, falsified, specced, method rows with
   a measured result, and parked / rejected / closed rows whose verdict quotes a measured number). Rules:
   - One value per row: the **first development look** (or the pre-sample if that was the first look); never the test
     value when a development value exists. Prefer **gross**; use net only when no gross is recorded (`est_basis`).
   - Oriented to the predicted sign: right sign = positive.
   - `se`: as recorded; else est / t when a t is recorded (|t| > 0.05); else leave est and se blank (do not invent).
     A threshold (e.g. "t >= 3.3", "gate 1.5 bp") is not a result.
   - Units: keep the record's own unit (bp per trade / week / month-end, R per trade, ...) in `est_unit`.
3. Rows closed **before any look** on power (M4 / pass chance / expected t): `est_sample` = expected, est = the
   pre-registered expected (halved) effect and se as the card states, only if both are on the card; else blank.
4. `dup_group`: one short label shared by near-duplicate rows (same signal / data, e.g. I-78 / I-83 / I-84 / FB-017
   one group; I-109 / I-110 one group). Blank for a unique row.

Sources to read: the row's own `verdict`, `gross_r`, `net_r`, `notes`, `spec` columns; the card in `knowledge/ideas.md`;
the spec in `docs/`; `docs/research-log.md`; reports in `knowledge/research/reports/`.

## Output
- `research/ledger.csv`: change **only** those 7 columns (the coordinator checks every other cell against git HEAD).
  Write with Python `csv` (DictWriter, `lineterminator="\n"`), keep the column order and row order.
- `research/ledger_effects_sources.csv` (new): `id,field_source,note` — for every row you filled, where the est / se came
  from (file + heading or ledger column) and any conversion (e.g. "se = est / t 2.4").
- Then run `.venv/Scripts/python.exe research/screens/ledger_effects.py list` (must end "ok").

## Allowed / forbidden
Only the two files above. Never commit, push or branch; never start long-running processes; never edit
`src/backtester/live/`, `.env`, `src/backtester/tools/notify.py`; no credentials; no downloads; no package installs.

## Done =
`ledger_effects.py check` ok, `pytest tests/tools/test_ledger_effects.py` green. Report: rows filled per type, rows with
est / se by est_sample and basis, dup groups, every judgment call (assumptions), and rows you could not fill and why.
