# Brief: `tools/harvest.py` (idea-harvest pipeline, plain code)

Design: `knowledge/reviews/2026-11-11-fable-research-framework.md` sections 2-4 (read them). You
write code and tests only. Do not run any network call, do not commit, do not touch `.env`,
`src/backtester/live/` or any other existing file except the two listed below.

## Files

- New: `src/backtester/tools/harvest.py` (target about 300 lines, stdlib + `requests`, which is
  already installed; no new dependency).
- New: `tests/tools/test_harvest.py` and fixtures under `tests/tools/harvest_fixtures/`
  (saved HTML pages, a small raw JSONL). **No network in tests:** inject the fetcher.
- Inputs it reads: `research/harvest/known_families.csv` (columns `family, keywords` (`;`-separated),
  `verdict, ledger_ids, note`), `research/ledger.csv` (header in that file; `source` and `notes`
  may hold URLs).

## Command line (`python -m backtester.tools.harvest <cmd>`; all paths overridable for tests)

1. `plan KEY [KEY ...] [--tasks research/harvest/tasks.csv]`: append one row per task key
   `SOURCE.MARKET.HORIZON.MECHANISM` (framework §2 value lists; an optional language prefix like
   `JA-BLOG`; `*` allowed for MARKET / HORIZON / MECHANISM; anything else: exit 2 with the reason).
   Columns: `task_id, key, queries, status, worker, run_date, n_raw, n_verified, n_kept`;
   `task_id` = `T` + 4-digit running number; `queries` = 3 queries joined by ` | `, built from one
   small template table per SOURCE (use the framework's example queries) filled with market and
   mechanism words; `status = open`. A key already present with status open / running is refused.
   No priority learning (later).
2. `prompt TASK_ID`: print the worker prompt of framework §3 with `{task_id}`, sources, market,
   horizon, mechanism, the 3 queries and `{known_families}` = the `family` names of
   `known_families.csv` whose verdict is not `open`, comma-separated.
3. `check RAW.jsonl [--out research/harvest/checked.jsonl]`: one JSON object per line as in §3.
   Per idea: (1) schema (all fields, enums, quote <= 300 chars) -> else `rejected:schema`;
   (2) fetch `source_url` (timeout 20 s, max one request per second per host, respect robots.txt via
   `urllib.robotparser`, User-Agent `backtester-harvest/0.1`); HTTP != 200 or a login / paywall page
   (words: "sign in to continue", "subscribe to read", "log in to view") -> `rejected:unverified_source`;
   (3) quote check: lower-case, collapse whitespace, strip HTML tags; pass if the quote is a substring,
   or the best `difflib.SequenceMatcher` ratio of the quote against same-length windows of the
   page text is >= 0.9 -> else `rejected:unverified_source`; (4) seller words near the claim
   (course, enroll, signals group, discount code, affiliate, coupon) -> `rejected:sells_course`;
   (5) testable: rules.entry and rules.exit stated (not "not stated") and no
   discretion / feel / context / experience word -> else `rejected:untestable`;
   (6) market maps to one of our symbols (small dict: S&P / SPX / ES -> US500, Nasdaq / NQ -> NAS100,
   Dow -> US30, DAX -> GER40, FTSE -> UK100, Nikkei -> JP225, gold -> XAUUSD, silver -> XAGUSD,
   WTI / crude -> USOIL, Brent -> UKOIL, bitcoin -> BTCUSD, ether -> ETHUSD, the FX pair codes)
   -> else `parked:needs_data`; (7) mechanism "not stated" -> `parked:no_mechanism`;
   (8) hindsight words ("would have", "turned $", "never loses") or a stated win rate > 90 % ->
   `rejected:hindsight`. Otherwise `verified`. Write each idea with `status`, `reason`, the task id
   and the model name (`--model`, recorded for the per-model unverified rate).
4. `dedup [--checked ...]`: among `verified` ideas: (a) URL already in the ledger -> `merged`;
   (b) keyword of a known family found in name + claim + rules (case-insensitive) -> family set;
   verdict falsified / closed / tested / screened_out -> `rejected:known_family`, otherwise kept with
   `family`; (c) two new ideas with the same market and horizon and token Jaccard of entry + exit
   >= 0.6 -> merged, `seen_count + 1` on the first.
5. `score`: framework §4 score table (mechanism words: rebalanc / hedg / settlement / index
   inclusion / expiry / fixing -> 3; carry / liquidity provision / risk premium -> 2; else 1;
   source_type paper / central_bank -> 2, book / blog with a claimed_result -> 1, else 0; rules
   entry + exit + stop stated 2, one missing 1; cost headroom: unknown 1 (no cost lookup yet);
   seen on 2+ domains +1; red flags -1 each, at most -3). Clamp 0..10.
6. `report [--ledger research/ledger.csv] [--write-ledger]`: print counts per status and reason,
   per task key, the unverified rate per model, and the top 10 by score (score >= 6). With
   `--write-ledger`, append one ledger row per new idea (id `HV-<task>-<n>`, stage harvested /
   verified / parked / rejected, reason in `verdict`, URL in `source`), never rewriting existing rows.

## Tests (write first, then the code)

Quote found exactly, found with whitespace / case / tag noise, a paraphrase below 0.9 rejected; a
login page rejected; robots.txt disallow -> not fetched, rejected; schema errors; untestable
discretion rule; known-family rejection (e.g. "Turtle Soup") and a kept open family (turn of month);
the Jaccard merge; the score on two hand-scored ideas; `plan` refuses a bad key and a duplicate open
key; `report --write-ledger` appends and does not duplicate on a second call.

Done = `pytest tests/tools/test_harvest.py` and `ruff check` on the new files green; answer with
the files changed, the test result and open questions only.
