# Phase 3 helper refactor: independent test/review brief

For Opus to dispatch to Gemini (tests) and Claude 4.6 (review). Codex must not dispatch them.
Existing tests and expected values remain unchanged. Before production edits, run the required existing suite as a baseline.

Critical test cases for independent test authorship:
- CSV: every original module name stays importable; first-seen key order across heterogeneous rows; missing cells; quoted commas/newlines; UTF-8; empty rows write exactly a CRLF header.
- Cached day: every original module name stays importable; latest date across unsorted dates and symbols; default sources unchanged; empty symbols or any empty symbol cache still raise ValueError.
- Timestamp: research._now stays callable; UTC ISO string with seconds precision remains unchanged; trial_log.now_iso is the survivor.
- Number: both original _number names stay callable; finite floats/numeric strings/zero/bools preserve float conversion; None, invalid strings, NaN and positive/negative infinity return None; overflow behavior remains unchanged.
- Import each affected tool in a fresh interpreter, especially grid_common and research, to catch import cycles.

Required verification: .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/tools tests/ui tests/analytics tests/test_runner_many.py; .venv/Scripts/python.exe -m ruff check .
Independent approval remains with Opus; Codex execution does not replace cross-review.
