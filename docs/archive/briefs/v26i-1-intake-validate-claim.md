# Brief V2.6i step 1: intake validator, claim and recovery (Codex, medium)

Read first: `docs/research-intake.md` (whole), `../Shared_Interface/INTERFACE_CONTRACT.md`
(Submission and claim protocol, Strategy requirements), the three schemas in
`../Shared_Interface/schemas/`, `src/backtester/filelock.py`. AGENTS.md rules apply (test first).

## What to build

New module `src/backtester/tools/intake.py` (no engine, strategy, live or data change), tests in
`tests/tools/test_intake.py`, and one optional extra in `pyproject.toml`:
`intake = ["jsonschema>=4.18"]` (decided by the user, D3). jsonschema is installed in `.venv`
already. Schema-conformance tests use `pytest.importorskip("jsonschema")`; every other check
works without it.

Everything takes an `umbrella: Path` argument (default: the parent of the V2 repo root, i.e.
`backtester.paths` HOME's parent; check `backtester/paths.py` for the right anchor) and a
`results: Path` (default `<HOME>/results`). Tests build a temporary umbrella with
`Shared_Interface/{queue/{pending,claimed,completed,rejected},schemas,documentation}` and copy
the real schema files and `documentation/V2_SYMBOLS.json` from `../Shared_Interface/` at test
time (skip the module if that folder is missing). Never commit copies of the schemas.

### Issue type

`Issue(code: str, severity: "ERROR" | "WARNING" | "INFO", message: str, field: str | None,
kind: "invalid" | "unsupported" | "note")`. `field` is a JSON Pointer (e.g. `/risk/accounting_type`).
Messages never contain absolute paths outside the umbrella or environment details.

### `validate_file(path, umbrella) -> tuple[dict | None, list[Issue]]`

In this order; stop at the first `invalid` problem that makes later checks meaningless:

1. Containment: resolved path must be inside `umbrella/Shared_Interface/queue/`; symlinks and
   non-regular files -> `UNSAFE_PATH`. Size > 1 MiB -> `FILE_TOO_LARGE`. Name must match
   `^[A-Z][A-Z0-9_]{2,63}__v[0-9]+\.[0-9]+\.[0-9]+\.json$` -> else `BAD_FILENAME`.
2. Bytes -> UTF-8 (BOM allowed) -> `json.loads` with no hooks; failure -> `INVALID_JSON`;
   top level not an object -> `INVALID_JSON`.
3. `schema_version`: major must be 0 and minor 1 (`0.1.x`) -> else
   `UNSUPPORTED_SCHEMA_VERSION`.
4. JSON Schema (`strategy.schema.json`, Draft 2020-12 with format checking): every error ->
   `SCHEMA_INVALID` with its pointer (skip this step with one INFO `SCHEMA_NOT_CHECKED` if
   jsonschema is missing).
5. Semantic checks (all `invalid` unless noted), mirroring
   `../Research_Department/tools/validate_contract.py` `validate_strategy_semantics` and
   `parameter_domain_size` (read them; do not import them):
   - file name == `<strategy_id>__v<specification_version>.json` -> `FILENAME_MISMATCH`;
   - `status == "SUBMITTED"` and `submitted_at` a UTC timestamp -> `NOT_SUBMITTED`;
   - parameter domains: FIXED not tunable and no values/range fields; VALUES / RANGE tunable;
     VALUES non-empty and contains the baseline; RANGE has min/max/step, step > 0, max >= min,
     (max-min)/step an integer within 1e-9, baseline on the grid -> `PARAMETER_DOMAIN_INVALID`;
   - `experiment.total_grid_size` == product of tunable domain sizes -> `GRID_SIZE_MISMATCH`;
   - capability (kind `unsupported`): `market.v2_compatibility != SUPPORTED` or a universe
     symbol not in `V2_SYMBOLS.json` -> `UNSUPPORTED_DATA`; `risk.accounting_type !=
     R_STOP_DEFINED`, `exits.stop_loss` null, or `entries.execution_timing == NEXT_BAR_OPEN`
     -> `UNSUPPORTED_STRATEGY_TYPE`;
   - `market.holding_period == OVERNIGHT` -> WARNING `OVERNIGHT_LOW_PRIORITY` (kind `note`).
6. Duplicate identity: the same file name already in `claimed/`, `completed/` or `rejected/`,
   or a folder `results/intake/<stem>/` -> `DUPLICATE_IDENTITY` (invalid).

### `pending(umbrella) -> list[Path]`

Files in `queue/pending/` excluding dot-files (`.tmp-*`, `.claim.lock`) and `README.md`, sorted
by (-priority, submitted_at, name) for valid files; unreadable ones last by name.

### `claim(umbrella, results, worker, now=None) -> Claim | None`

Under `backtester.filelock` on `queue/.claim.lock`: take the first pending file with no
`invalid` ERROR; `os.replace` it to `claimed/`; then write
`results/intake/<stem>/claim.json` atomically (temp file + `os.replace`):
`{"file", "strategy_id", "specification_version", "sha256" (lowercase hex of the exact bytes),
"worker", "claimed_at" (UTC ISO), "issues": [...]}`. Return `Claim(path, sha256, payload,
issues)`; unsupported issues stay in `issues` (step 2 turns them into feedback). Invalid
pending files are never moved here (step 2 rejects them with feedback). The submitted bytes are
never modified. None when nothing is claimable.

### `recover(umbrella, results, now=None, max_age=timedelta(hours=1)) -> list[Path]`

Under the same lock: a file in `claimed/` with no `results/intake/<stem>/claim.json` and an
mtime older than `max_age` goes back to `pending/` (`os.replace`); returns the moved paths.

### CLI

`python -m backtester.tools.intake validate|claim|recover [--root UMBRELLA] [--worker NAME]`;
`validate` prints one line per pending file (`ok`, or the codes) and exits 1 if any invalid.
`claim` prints the claimed file and its sha256 or "nothing to claim". No file writes from
`validate`.

## Test cases (write first, then the code)

valid fixture claims and writes claim.json with the right sha256; bytes in `claimed/` identical
to the input; dot-file and `.tmp-x.json` ignored; partial JSON -> INVALID_JSON and not claimed;
schema-invalid (missing `risk`) -> SCHEMA_INVALID with pointer; wrong file name / identity ->
FILENAME_MISMATCH; schema_version `1.0.0` -> UNSUPPORTED_SCHEMA_VERSION; status DRAFT ->
NOT_SUBMITTED; bad RANGE and grid size mismatch; unknown symbol -> UNSUPPORTED_DATA but still
claimable; UNIT_NOTIONAL and NEXT_BAR_OPEN -> UNSUPPORTED_STRATEGY_TYPE; symlink or `..` path
-> UNSAFE_PATH (skip the symlink case if the OS refuses to create one); duplicate in
`completed/` -> DUPLICATE_IDENTITY; priority order (two valid files, higher priority claimed
first); two-worker race: two processes (multiprocessing, spawn) claim concurrently from one
pending file -> exactly one Claim, the other None; crash after the move but before claim.json
(simulate by moving manually) -> `recover` with an old mtime puts it back, with a fresh mtime
leaves it; a claimed file with claim.json is never recovered; `validate` CLI writes nothing.

Build the valid fixture as a Python dict in the test (based on the schema), not by reading the
research drafts.

## Done =

`pytest tests/tools/test_intake.py -q` green, `ruff check . && ruff format --check .` clean,
no change outside `src/backtester/tools/intake.py`, `tests/tools/test_intake.py`,
`pyproject.toml`. Report files changed, test results, open questions. Do not commit.

Likely questions, answered: periods / data are not checked here (step 2); no feedback envelopes
yet (step 2); `results/intake/` is git-ignored already (results/); Windows: `os.replace` is the
atomic move; the lock is `backtester.filelock` (read its API).
