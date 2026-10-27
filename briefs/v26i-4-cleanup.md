# Brief V2.6i step 4: simplification round (Codex, medium)

Ponytail review (Opus, 2026-10-28) of the V2.6i code. Behaviour must not change; every existing
test stays green unchanged except where a test reads the removed duplicate file (then point it
at `research.json`).

1. `tools/research.py` `_code_version`: one small `git(*args)` helper instead of two
   near-identical `subprocess.run` blocks.
2. `tools/research.py` `_run_research_locked`: stop writing `folder / "info.json"` (a copy of
   `research.json`) for submission grids; `tools/intake.py` `emit_result` reads
   `research.json` of the research folder instead. Run folders' own `info.json`
   (`_daily_series`) stay.
3. `analytics/trial_log.py` `append`: do not re-apply `_SUBMISSION` (make_record already sets
   it); keep only dropping the key when it is None. Check every TrialRecord writer used inside
   `submission_identity(...)` goes through `make_record`; if one does not, keep the re-apply and
   say why in the report.
4. `tools/intake.py` `emit_result`: `_test_authorized` takes the identity dict (change its
   signature in `tools/research.py` and its callers) instead of a `SimpleNamespace` GridSpec.
5. `tools/intake.py` `emit_result`: derive the metric key list from the result schema's
   `metrics.properties` (read the schema file; it exists whenever envelopes are written)
   instead of the hand-written 15-name tuple.

Done = `pytest tests/tools tests/analytics -q` green, ruff clean, only these files changed:
`tools/research.py`, `tools/intake.py`, `analytics/trial_log.py`, and tests only where item 2
requires. Do not commit. Report net lines removed.
