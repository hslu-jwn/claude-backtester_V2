# V2.6l: every declared cell in the result envelope (Codex gpt-6.1-terra, medium)

Read `AGENTS.md` first. Rule: ROADMAP V2.6l (Research's review
`../Shared_Interface/feedback/messages/FB_FX_LONDON_FIX_REV_RESULT_REVIEW_20261029T070325Z_RESEARCH.json`,
our answer `FB_FX_LONDON_FIX_REV_20261029T164921Z_83af`): the result envelope must show every
declared cell, not only the chosen one, and `variants_tried` counts declared cells only.
Process doc: `docs/research-intake.md`. Envelope builder: `src/backtester/tools/intake.py`
(the function that builds `envelope = {...}` with `"robustness"` and `"variants_tried"`).

Decided by Opus 2026-11-03 (night run, recorded as assumptions; do not ask): generic manifest
for every submission; the R004-specific map (`robustness.r004`) and the data-integrity check
are **not** part of this step (R004 is an unqueued draft; the integrity check needs an
authoritative CFD session calendar V2 does not have).

## What to build (test-first: tests below first, run red, then code)

1. New module `src/backtester/tools/intake_cells.py`:
   `cell_manifest(folder: Path, costs_of: Callable[[dict], CostConfig] | None = None) -> list[dict]`
   for a research folder (`results/research/<grid>/`): one row per **declared cell** = per row
   of `variants.csv` / folder `variants/<id>/`, sorted by `cell_id`:
   `cell_id`, `parameters` (the `overrides` of `variants/<id>/scorecard.json`), `status`
   (`COMPLETED`, or `FAILED` with `reason` when the folder / `trades.csv` is missing or
   unreadable; a failed cell still gets its row, other numbers null), `trades`,
   `gross_mean_r`, `net_mean_r`, `gross_total_r`, `net_total_r`, `stop_rate` (share of trades
   whose `exit_reason` is `stop_loss`), `half_first_net_r`, `half_second_net_r` (from the cell's
   `scorecard.json`), and `cost_stresses`: `{"factor_1.5": ..., "factor_2.0": ...,
   "fill_p90": ...}` from `analytics.robustness.stressed_net(trades, 1.5 / 2.0)` and
   `stressed_net_p90(trades, load_slippage_p90(), costs)` where `costs` is the cell's own
   `CostConfig` (`settings.from_dict(variants/<id>/settings.json).engine.costs`; fall back to
   `CostConfig()` and say so in the row's `notes`). Read trades with
   `analytics.records.read_trades`. Floats rounded to 6 decimals. No test-period data: the
   cells are development runs; never read `research.json["test"]`.
2. `trial_accounting(folder, info, trial_log_count) -> dict`:
   `{"declared_cells": n, "sensitivity_runs": m, "trial_log_count": count}` (`m` = folders in
   `sensitivity/`, 0 when absent).
3. In the result envelope (`intake.py`): `robustness["cell_manifest"]` and
   `robustness["trial_accounting"]`; if `robustness["sensitivity"]` exists, add
   `"selectable": False` to it (sensitivity runs are not trials of the submission);
   `variants_tried` = `declared_cells` (was the trial-log count). Keep everything else; the
   development-stage redaction rules and `REDACTED` disclosure (robustness `{}`) stay as they
   are. The envelope must still pass `_validate_envelope`.
4. `docs/research-intake.md`: a short "Result envelope: declared cells (V2.6l)" section
   (fields, `variants_tried` rule, sensitivity not selectable) and one line "Data-integrity
   check: not supported until a versioned CFD session calendar (holidays, early closes) exists;
   see ROADMAP V2.6l".

## Tests (`tests/tools/test_intake_cells.py`; reuse the fixtures of
`tests/tools/test_intake_envelopes.py` for the envelope cases)

1. Two declared cells with hand-built `trades.csv`: one row each, sorted, parameters from the
   scorecard overrides, `stop_rate` = 1 / 3 for one stop of three trades, totals and means.
2. `factor_1.5` / `factor_2.0` equal `stressed_net` with those factors; `fill_p90` equals
   `stressed_net_p90` with the cell's costs; a cell without `settings.json` uses `CostConfig()`
   and has the note.
3. A declared cell whose folder is missing: `status` `FAILED`, a reason, numbers null; the
   other cell is unaffected.
4. `trial_accounting`: 2 declared cells, 3 sensitivity folders, trial log count 5.
5. Envelope: `variants_tried == 2` although the trial log counts 5; `cell_manifest` and
   `trial_accounting` present; `sensitivity["selectable"] is False`; schema validation passes;
   a `REDACTED` envelope still has `robustness == {}`.
6. The existing assertions `variants_tried == 1` in `test_intake_envelopes.py` stay valid (one
   declared cell there); if a fixture has no `variants.csv`, `variants_tried` falls back to the
   trial-log count (old behaviour) and `trial_accounting.declared_cells` is null; test that too.

## Limits

Touch only `src/backtester/tools/intake.py`, new `src/backtester/tools/intake_cells.py`,
`tests/tools/test_intake_cells.py`, `docs/research-intake.md` (and
`tests/tools/test_intake_envelopes.py` only if a fixture needs a `variants.csv`; never change an
expected value there). Never write into `../Shared_Interface/` or `results/`, never send
feedback, never start a server, never commit / push / branch.

**Done =** new tests green, `python -m pytest tests/tools -q` green, `ruff check .` and
`ruff format --check` clean. Report: files changed, test results, open questions.
