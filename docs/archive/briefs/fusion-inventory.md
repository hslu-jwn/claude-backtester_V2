# Brief: fusion inventory (read records, write one file)

Model: Codex `gpt-6.1-terra` medium. Write task. You may create ONE file:
`knowledge/topics/fusion-inventory.md`. Touch nothing else. No commits, no servers, no credentials,
no market-data reads beyond listing folders (this is an inventory of what we already MEASURED, not a new look).

## Goal

A table of every component (signal, condition, stream, data set) we already have, with what it measured,
so combinations ("fusions") can be proposed from it. Facts only, copied from the records; no new numbers.

## Sources (read all)

1. `research/ledger.csv` (one row per idea / hypothesis; columns id, stage, family, name, mechanism, period,
   trades, gross_r, cost_r, net_r, verdict, notes ...).
2. `knowledge/ideas.md` (cards I-xx / T-xx; status lines: PARKED, CLOSED, KILLED, ALIVE, SHELF ...).
3. `research/screens/` (73 scripts; read the module docstring / header comment of each, and any result
   numbers quoted in `docs/research-log.md` for it).
4. `docs/research-log.md` (newest first) for the numbers of live streams and screens.
5. Live streams: `docs/strategy-crypto_flow.md` (Strategy 20), the Strategy 19 carry spec
   (`docs/strategy-*carry*.md`, find it), card I-109 (Treasury month-end) and the shelf in `docs/HANDOFF.md`
   (I-100, I-84, I-98, H11, I-71, I-105, I-109).
6. `knowledge/topics/cost-wall.md` §1 (older strategies 1-14 table).
7. Data: `ls data/cache/` subfolders. For each, find in the docs / screens what it holds (source, symbols or
   names, period, frequency). Do NOT open large data files; a folder listing and file counts are enough.

## Output: `knowledge/topics/fusion-inventory.md`

Header: purpose, date 2026-11-19, "facts copied from records, no new data look", source key.

Section 1 "Alive and near-live streams": Strategy 19, Strategy 20, I-109, each shelf item. Columns:
id | what | venue / symbols | dev period | gross edge (unit as recorded: bp/week, bp/event, R/trade) | t | test result |
regime notes (halves, years, conditions) | status.

Section 2 "Components with a measured positive gross edge" (killed or parked, but gross > 0 somewhere):
same columns plus "cost" and "why killed". Include F1a, F2 (all indices), F1X, R014 FADE, London fix, gap fade,
ORB test, I-73, I-83, every ledger row with gross_r > 0 or a positive bp gross, and every screen result with a
positive gross.

Section 3 "Measured zero / negative components" (one line each: id, what, gross, t, verdict). Compact.

Section 4 "Conditions / regime variables we can compute" (VIX level, volatility regime classifier, trend /
sideways regime from strategy profiles, news / FOMC calendar, funding, taker flow, month-end, weekend
month-ends, ...): name, where computed (file), period available, used by which test so far.

Section 5 "Data sets in data/cache/": folder | source | contents | period | frequency | used by.

Section 6 "Gaps": items whose numbers you could not find (say where you looked). Never invent a number;
write "n/a (not recorded)".

Rules: every number gets its source in brackets (ledger id, log date, spec file). Plain English, short lines.
Keep it under about 400 lines. Done = the file exists and every row has a source.

Final answer: the row counts per section and the list of gaps.
