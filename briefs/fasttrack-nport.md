# Brief: fast-track census, indirect ground truth from Vanguard Total Stock Market N-PORT holdings (return-blind)

Worker: Claude Sonnet subagent. Coordinator: Opus. Read first: `AGENTS.md`, `briefs/fasttrack-census.md` (same rules),
`knowledge/research/reports/2026-11-26_fasttrack-census.md` (the predicted list in `data/cache/fasttrack/census.csv` /
`census_eligible.csv`).

## Question
Does the Vanguard Total Stock Market Index Fund (tracks CRSP US Total Market; VTI share class) hold each predicted
fast-track IPO in the first N-PORT filing after the IPO, and do IPOs we predicted NOT eligible stay out until a later
quarterly reconstitution? That separates fast-track adds (held within weeks) from ordinary quarterly adds.

## Steps
1. Find the fund's CIK / series on SEC EDGAR and list its NPORT-P filings (public since 2019; monthly holdings, filed
   quarterly with a 60-day lag; the first two months of each quarter may be non-public). Note what months are public.
   If only quarter-end holdings are public, say what that resolves and what not.
2. For each IPO in the census (predicted eligible and a sample of predicted not eligible, both 2019-03 .. 2025-12):
   first holdings report date after the IPO in which the fund holds it (match by CUSIP if the census has it, else
   name / ticker; record the match method). Read only identifiers, share counts and the report date; **never read or
   use the value / price columns** (return-blind).
3. Classify: held at the first report whose date is <= IPO + ~35 days -> "fast-track-like"; first held only after the
   next quarterly reconstitution -> "regular". Confusion table vs our prediction, by year; list misses with reasons.
4. Verdict: does the public rule reproduce fast-track (precision / recall)? GO to a frozen card only if recall >= 70 %
   and precision >= 70 % on resolvable cases; else PARK.

## Allowed / forbidden
- May create: `research/screens/2026-11-27_fasttrack_nport.py`, files under `data/cache/fasttrack/nport/`, and append a
  section "N-PORT check (2026-11-27)" to `knowledge/research/reports/2026-11-26_fasttrack-census.md`. Nothing else.
- SEC User-Agent exactly as `research/screens/2026-11-26_r7_f01_stage_a.py` builds it (keyring), never printed; at most
  8 requests a second; one downloader; no bot-protection bypass; no commits / pushes / branches; no credentials; no
  package installs; no long-running process left behind. ruff check + format on your script only.

## Done =
Report section with sources, months resolvable, match method, confusion table, verdict, and every assumption.
