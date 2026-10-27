# Brief V2.6i step 3: feedback / result envelopes, terminal moves, end-to-end test (Codex, medium)

Read first: `docs/research-intake.md`, `../Shared_Interface/INTERFACE_CONTRACT.md` (Results,
Feedback and error handling, Lifecycle), `../Shared_Interface/schemas/result.schema.json` and
`feedback.schema.json`, `src/backtester/tools/intake.py` (steps 1-2), `runner.write_results`,
the research folder files (`info.json`, `summary`, significance / robustness outputs; read
`tools/research.py` to see their names). AGENTS.md rules apply (test first). Changes only in
`tools/intake.py`, `tests/tools/test_intake*.py`, `docs/research-intake.md` (command list).

## Functions in `tools/intake.py`

All writes are atomic (temp file in the same folder + `os.replace`), refuse to overwrite an
existing envelope, and validate against the schema with jsonschema when installed (raise on an
invalid envelope: never write one). Paths inside envelopes are relative to the umbrella with
`/` separators and must resolve inside it. `created_at` UTC ISO.

1. `emit_feedback(umbrella, *, status, issues, subject_file, claim=None, payload=None,
   sha256=None, scope="SUBMISSION", in_reply_to=None, related_experiment_id=None) -> Path`:
   writes `Shared_Interface/feedback/messages/<feedback_id>.json`, feedback_id =
   `FB_<STRATEGY_ID or UNKNOWN>_<YYYYMMDDTHHMMSSZ>_<4 hex>`; producer
   `"V2 backtester team"`; strategy identity from the claim / payload, null when unparseable.
   Issues from step 1 map 1:1 (code, severity, message, field, `requires_revision` = True for
   invalid and unsupported kinds, False for notes).
2. `reject_invalid(umbrella, results) -> list[Path]`: under the claim lock, every pending file
   with an `invalid` ERROR moves to `queue/rejected/` (never deleted; on a name clash append
   `.dup-<n>` before `.json`) and gets one feedback envelope status `REJECTED` with its sha256.
3. `reject_unsupported(umbrella, results, claim) -> Path`: for a claim whose issues contain an
   `unsupported` error: feedback with `UNSUPPORTED_DATA` (if any data issue) else
   `UNSUPPORTED_STRATEGY_TYPE`, then `finish(..., "rejected")`.
4. `progress(umbrella, claim, status)` for `CLAIMED` / `IMPLEMENTING` / `TESTING`: one feedback
   envelope each (issue code `PROGRESS`, INFO, requires_revision False).
5. `next_experiment_id(results, stem, stage) -> str`: `<stem>__<stage>__<n>`, n = 1 + the
   highest n recorded in `results/intake/<stem>/experiments/`, never reused.
6. `emit_result(umbrella, results, claim, *, experiment_id, stage, research_folder,
   requested_costs, warnings=(), errors=(), status="COMPLETED") -> Path`: builds
   `result.schema` from the research folder (`info.json` submission / dataset / code_commit,
   the chosen or best development variant's metrics: net_r, max_drawdown_r, expectancy_r,
   sharpe_daily_r, profit_factor, trades, win_rate, average_win_r / average_loss_r when
   available, everything else null; `variants_tried` = trial count of that research folder;
   `statistical_diagnostics` = DSR / PSR / significance flags found there; `robustness` = the
   robustness results found; `resolved_cost_model` = the engine cost settings recorded in the
   run settings; `accounting_type` R_STOP_DEFINED; `stage_split` constant;
   `holdout_disclosure` = NONE for DEVELOPMENT, REDACTED for FINAL_HOLDOUT unless the caller
   passes FULL). `artifacts` = the research folder's main files and run folders with sha256.
   FINAL_HOLDOUT requires the step-2 authorization file, else raise. Also writes
   `results/intake/<stem>/experiments/<experiment_id>.json` (what was emitted, where).
   Map metric names by reading what the research folder actually contains; if a metric is not
   there, write null, never a guess. List the mapping in `docs/research-intake.md`.
7. `finish(umbrella, results, claim, outcome)` with outcome `completed` / `rejected`: under the
   lock `os.replace` claimed -> terminal folder; record it in `claim.json` (`finished_at`,
   `outcome`).
8. CLI: add `reject`, `progress <stem> <status>`, `finish <stem> completed|rejected`,
   `result <stem> --research-folder <path> --stage DEVELOPMENT [--requested-costs json]`.

## Test cases (first)

feedback for unparseable JSON has null identity, scope SUBMISSION, subject_file relative, and
validates; reject_invalid moves and writes one envelope per file, never deletes, name clash
handled; unsupported claim -> feedback status + file in rejected/; progress envelopes validate;
experiment ids count up and survive a restart; emit_result on a small synthetic research folder
(build one in tmp with the files the real runner writes, or run the research runner on the
existing test fixtures if that is how `tests/tools/test_research*.py` do it) validates against
the schema, has the right sha256s, relative paths, NONE disclosure; FINAL_HOLDOUT without
authorization raises, with it gives REDACTED; overwriting an envelope refused; an artifact path
outside the umbrella refused.

**End-to-end (i7)**, one test: temp umbrella -> write a synthetic valid submission to
`pending/` via `.tmp-x` + rename -> validate -> claim -> progress CLAIMED -> a tiny development
research run on the existing synthetic test cache with a `[submission]` grid -> emit_result ->
finish completed; asserts: queue file in `completed/` byte-identical to what was submitted,
envelope sha256 == that file's sha256, envelope validates, trial lines carry the submission,
nothing written outside tmp. Plus the negative path: an invalid and an unsupported submission
end in `rejected/` with feedback, and no run happens.

## Done =

`pytest tests/tools -q` green, ruff clean, only the files named above changed. Do not commit.
