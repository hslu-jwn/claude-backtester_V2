---
name: idea-harvest
description: Online idea harvest for the research loop - plan small search tasks, let a web-capable cheap worker return ideas as JSON with URL and verbatim quote, verify and filter them with local scripts (tools/harvest.py), and record every idea in research/ledger.csv. Load when the user asks for an idea harvest or when continue-research runs out of carded ideas and the user has approved a harvest batch.
---

# idea-harvest (design: `knowledge/reviews/2026-11-11-fable-research-framework.md`; the user, 2026-11-11)

Feeds `continue-research`: it finds and filters ideas; it never builds, screens or tests them.
Every idea, kept or not, ends as a row in the one ledger `research/ledger.csv`.

## Needs the user's OK first

A batch (its size and the Codex share), any new data download or purchase, a new source type with
terms-of-use risk, reviving a parked idea. Never run a harvest batch on your own initiative.

## Steps

1. **Plan:** `python -m backtester.tools.harvest plan <KEY> ...` (key `SOURCE.MARKET.HORIZON.MECHANISM`,
   framework §2) writes task rows to `research/harvest/tasks.csv`. Every batch carries two canaries:
   one cell with a known answer and one nonsense cell that must come back empty. The known answer
   must come from a family that is **open** in `known_families.csv` (the prompt tells the worker to skip
   every closed family): since 2026-11-13 `ACAD.FX-MAJ.SWING.CARRY` "currency carry trade returns":
   Koijen, Moskowitz, Pedersen & Vrugt "Carry" or Lustig, Roussanov & Verdelhan must appear. ("local
   hours" / Breedon & Ranaldo can no longer pass: `fx_hours` is closed.) Replace the canary when its
   family closes.
2. **Search (worker):** one task per call, read-only:
   `ai_dispatch codex --search --effort low --label harvest-<task_id> --prompt "<harvest prompt TASK_ID>"`
   (`--search` is required: without it `codex exec` has no web access, probe 2026-11-12)
   (model per `docs/agent-routing.md`; at most 2 in parallel; a limit means pause, never a paid
   fallback). Save the JSON answer as `research/harvest/raw/<task_id>.jsonl` **only after every running
   call has ended**: the dispatcher's guard flags any repo change during a read-only call (2026-11-13,
   batches 6-7: false exit 3); commit the planned tasks before dispatching. Text-only free models
   (Ollama, groq, openrouter, gemini-api) may only translate or fill the schema from page text the
   script fetched; they are never asked for sources.
3. **Check:** `harvest check raw/<task_id>.jsonl --model <worker>` fetches every URL itself
   (robots.txt, one request per second per site, public pages only), finds the quote on the page,
   and applies the schema / seller / testable / data / mechanism / hindsight filters. PDFs are read
   as text (`pypdf`, data extra). Inside a Claude Code sandbox every fetch fails with an SSL error
   (its proxy CA is only in `NODE_EXTRA_CA_CERTS`): set `REQUESTS_CA_BUNDLE` to certifi's bundle plus
   that file (scratchpad copy) for the check command; never disable certificate checks. On this PC Avast's
   web shield does the same (its CA is the `NODE_EXTRA_CA_CERTS` file, 2026-11-14): same fix; if every
   source comes back `unfetchable`, suspect this first and revert the appended `checked.jsonl` rows. Ideas without
   a stated mechanism are **parked**, not dropped (the user, 2026-11-11). A page the script may not or
   cannot read (robots.txt, 401 / 403 / 429, login wall, no answer) is parked as `unfetchable`, not
   counted against the worker (a 404 still is); Opus may read it only if it is public without a login.
   `check` appends to `checked.jsonl` (it accumulates every batch).
4. **Dedup and score:** `harvest dedup`, `harvest score` (against `research/harvest/known_families.csv`
   and the ledger; the score ranks attention only, it says nothing about profit).
5. **Report and record:** `harvest report --write-ledger`; the counts per stage go at the top of the
   batch report. A model with more than 20 % `unverified_source` on a source type is taken off it.
6. **Opus reads the top 10 only** (score >= 6): opens every source itself, writes an idea card in
   `knowledge/ideas.md` with the kill criterion in its ledger row **before** any data is looked at,
   then hands the best (at most 5 per batch, picked before any result) to `continue-research`
   (screen first, then spec).

## Rules

- Public pages only, no login, no paywall bypass; store the URL and a quote of at most 300
  characters; never send repository content, account data or credentials to any site or model.
- Multiple testing: every idea and every look is a ledger row; the pass threshold rises with the
  number of screened ideas in a family (|t| >= 3.0 up to 10, 3.5 up to 50, 4.0 above).
- A harvested idea is a lead, never a finding. Nothing is called profitable before its one-time test.
