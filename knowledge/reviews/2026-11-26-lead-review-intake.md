# Intake of the two lead-research reviews of 2026-11-21 (Opus, 2026-11-26)

Two outside reviews, read in full at their summaries and synthesis, cross-checked against the ledger:

- **Review A** (lead agent + 14 research agents): `../../../lead-research-2026-11-21/` (next to the repo, kept
  outside at the user's request; 21 files, `FINAL-REPORT.md`, `07-synthesis-and-ranking.md`).
- **Review B** (lead agent + 3 streams): `2026-11-21-lead-research/` in this folder (6 files, `FINAL-REPORT.md`,
  `01-ranked-opportunities.md`). Review A's note that this folder "holds only duplicates" is wrong: the files differ.

Nothing in them is a rule; each item below goes through a card, the M-rules and the gates.

## Corrections found at intake

- A rank 6 (measure Strategy 20 on the top-100 liquid universe) is **already done**: ledger FB017, dev +171.0 bp a
  week (t 3.64), spent test +166.3 (t 3.06), forward-logged. Only its use for the go-live design is new.
- A "close I-127": already PARKED 2026-11-18 (M4); A adds a contrary-evidence source only.
- I-105 flaw (both reviews): confirmed from the card itself (`knowledge/ideas.md` › I-105): the signal uses the
  official open, the entry is market-on-open, so the order needs a price that does not exist yet. No forward row is
  read before 2026-12-03, so a refreeze now is clean.

## Task list (in order; status kept here until done, then ledger / HANDOFF)

| # | Task | Source | Needs | Status |
|---|---|---|---|---|
| R1 | I-105 refreeze: register an executable variant (new card, counted) before 2026-12-03; I-105 (and I-134, which splits it) become report-only | A 03/00, B 01 | signal-free pre-market coverage count (small Alpaca download) | done 2026-11-26: I-143 |
| R2 | Strategy 20 go-live notes in its spec: Binance 50-symbol Reduce-Only rule (sub-accounts < 50 symbols, the top-100 variant holds ~40), BNB fee payment (-10 %), live signal from the exchange API, not the public-data files | A 12/17 | docs only | open |
| R3 | Pre-register a Binance **spot** 2018-01..2019-12 replication of Strategy 20 (same rule, never looked at) as a pool member, before any download | A 17 | card; then the download | open |
| R4 | Strategy 19: split the forward return into funding and price legs; descriptive cross-coin funding-dispersion check by half-year (no returns) | A 11/15 | data on disk | open |
| R5 | I-109 live path: exit before 11 a.m. ET on SIFMA early-close days (order calendar); log the clearing regime dates (cash 2026-12-31, repo 2027-06-30); paper variants 5Y (IEI) and a pre-registered IEF 4 p.m. diagnostic | A 09/15 | IEF M1 download for the diagnostic | open |
| R6 | Execution fill-model study for Strategy 20 on aggTrades, decision rule fixed first (adopt at saving >= 1.5 bp, t >= 2, 2-tick rule, least liquid third) | A 12 | Codex terra; aggTrades download | open |
| R7 | F-01 employee selling after earnings at high stock-comp firms: return-blind audit (EDGAR tags, 8-K timing, breadth, borrow, MDE); card only at pass chance >= 15 % | A 08, B 01 rank 1 | Codex terra, SEC data | open |
| R8 | Return-blind feasibility audits, one each: SEC Rule 201 trigger archives; CRSP fast-track IPO eligibility; non-overnight follow-on offerings (post-2015 census); HLP backstop clusters (>= 50); rights issues (>= 50 executable) | B 01 ranks 2-4, 6, 7 | Codex terra, web | open |
| R9 | Ledger hygiene: HV-T0116-2 "untestable" -> "parked on power"; add the reviews' closed negatives (A 03-05, 16; B 03) as rejected rows so they are not re-proposed; add them to `knowledge/topics/cost-wall.md` §4 | A 07 §4, B 03 | docs only | open |
| R10 | Ledger columns for effect and standard error per row (needed for any pooled verdict or empirical prior) | A 06/10 | tooling | open |
| R11 | Pooled-evidence verdict, frozen flow + carry composite, one forward book for all right-sign streams | A 06/10 | **the user's rule decision** | waits |
| R12 | Swiss tax check of goal-2 derivative streams (ESTV KS 36), SSRN 7601879 PDF (I-109 German / reversal legs), formal stop of FTMO CFD signal research | A §6 | **the user** | waits |

Information only (2026-11-18 decisions stand, not reopened): Databento $125 credit with a spend limit (A, B); HyroTrader
Two-Step for a reduced S20 book (A 13); USDC-M zero-maker perps (A 11 parks it, ~30-50 contracts; B suggests an
overlap count).
