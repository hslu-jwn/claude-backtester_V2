# Brief V2.6j: async questions to Research (Codex gpt-6.1-terra, medium)

Decided by the user 2026-10-28 and accepted by Research
(`../Shared_Interface/feedback/messages/FB_CONTRACT_REPLY_20261028T134149Z_RESEARCH.json`).
Rules: `docs/research-intake.md` › Assumptions and replies (read it first). Code in
`src/backtester/tools/intake.py` (+ a small helper module if it grows, e.g.
`tools/intake_inbox.py`). **Test first.** The shared folder is written only through the
existing `emit_feedback` / `_publish` paths (schema-validated); never edit or delete a message.
No change to the schemas or the contract file.

Real examples to use as fixtures (copy their content into test files; do not read the live
folder in tests): our `FB_FX_LONDON_FIX_REV_20261028T133244Z_00ab.json` (3 ASSUMPTION_MADE),
Research's reply `FB_FX_LONDON_FIX_REV_REPLY_20261028T134149Z_RESEARCH.json` (3 CONFIRMED,
`in_reply_to` = 00ab), our `..._134544Z_1abf.json` (2 ASSUMPTION_MADE, unanswered).

## 1. `intake inbox`

`python -m backtester.tools.intake inbox [--json]`: reads every `*.json` in
`Shared_Interface/feedback/messages/` (skip README, dotfiles, unreadable / invalid files with a
warning line) and prints:
- **Open questions of ours**: messages with `producer` "V2 backtester team" that contain an
  `ASSUMPTION_MADE` or `NEEDS_CLARIFICATION` issue and that no message has `in_reply_to` for;
  per message: feedback_id, strategy_id + version, kind (assumption / blocking), number of
  points, fields, age in days (from `created_at`, `now` injectable).
- **New replies for us**: messages not produced by us whose `in_reply_to` is one of our ids
  and which are not yet recorded as processed; per issue: code (CONFIRMED / CORRECTED / other),
  field, message. Plus messages from Research with no `in_reply_to` (new contract notes).
- A summary line exactly: `Open questions for Research: <n> (oldest <d> days)` (or
  `Open questions for Research: 0`).
- Processed replies: `intake inbox --ack <feedback_id>` records the id in
  `results/intake/inbox_processed.json` (git-ignored results folder; atomic write as elsewhere)
  so it is listed once. `--json` prints the same as one JSON object.

Pure functions (`open_questions(messages)`, `new_replies(messages, processed)`,
`summary_line(open, now)`) carry the logic; the CLI only reads files and prints.

## 2. `intake assume`

`python -m backtester.tools.intake assume <stem> --status IMPLEMENTING|TESTING --file points.json`
where `points.json` is a list of `{"field": "/json/pointer", "message": "..."}`; publishes one
feedback message with one `ASSUMPTION_MADE` / `WARNING` issue per point
(`requires_revision` false) through `emit_feedback`. Validate: non-empty list, every field a
JSON Pointer that resolves inside the claimed submission (reuse `_pointer` or resolve against
`claim.payload`), message length >= 3. Prints the published path.

## 3. Parked submissions (`NEEDS_CLARIFICATION`)

`python -m backtester.tools.intake park <stem> --file points.json`: publishes a
`NEEDS_CLARIFICATION` message (status NEEDS_CLARIFICATION, issues code `NEEDS_CLARIFICATION`,
severity `ERROR`, `requires_revision` true) and records `{"parked": true, "feedback_id": ...,
"parked_at": ...}` in the claim's `results/intake/<stem>/claim.json` (keep the other keys).
The file stays in `claimed/`. `intake parked` lists parked claims; a parked claim is
**unparked** automatically by `inbox` when `pending/` holds a higher specification version of
the same strategy_id (print it; do not claim it, the loop does that). `recover` must never
move a parked claim back to pending (it has a claim record already; add a test that proves it).

## 4. Result envelope: open assumptions

`emit_result` (and the `result` CLI) appends one warning per still-open assumption message of
that submission: `Open assumption (unanswered): <feedback_id>: <fields>`, and one per
answered one: `Assumption <feedback_id>: CONFIRMED|CORRECTED by <reply id>`. Uses the
functions of item 1.

## Test cases

1. Our 00ab + Research's reply -> 00ab not open; 1abf open; summary
   `Open questions for Research: 1 (oldest 0 days)` with `now` = its created_at; with now + 3
   days -> `(oldest 3 days)`.
2. A reply referring to an unknown id -> listed under replies with "unknown reference".
3. Messages without ASSUMPTION / CLARIFICATION (progress CLAIMED, results) never count open.
4. An invalid JSON file in the folder -> warning line, the rest still listed.
5. `--ack` -> the reply is not listed again; ack of an unknown id -> error exit 2.
6. `assume`: two points -> one message, two issues, schema-valid; a field pointer not in the
   submission -> error, nothing published; empty list -> error.
7. `park`: message published, claim.json gets `parked`, file still in claimed/; `recover`
   leaves it; a higher version in pending -> inbox prints "unpark"; the same or lower version
   -> nothing.
8. `emit_result` warnings list the open and the answered assumptions as specified.
9. `--json` output parses and has keys `open`, `replies`, `summary`.

## Docs

`docs/research-intake.md` › Intake commands: `inbox`, `assume`, `park`, `parked`; replace
"(ours: `intake inbox`, planned)" with the real command. `CLAUDE.md` is Opus's to edit (do not).

Done = new tests green; `pytest tests/tools -q -k intake` green; ruff check + format clean.
Report: files changed, tests, open questions. Do not commit.
