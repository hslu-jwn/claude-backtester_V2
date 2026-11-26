# Brief: CRSP fast-track IPO census (return-blind; R8 follow-up, lead review intake 2026-11-26)

Worker: Claude Sonnet subagent. Coordinator: Opus (checks outputs, commits). Read first: `AGENTS.md`,
`knowledge/research/reports/2026-11-26_r8-feasibility.md` › 2, and the format of
`knowledge/research/reports/2026-11-26_rule201-census.md` (the report you write follows it).

## Question
Can public, free data reproduce **which US IPOs CRSP adds to its US Total Market index by Fast-Track** (inclusion at
the 5th trading day's close, T+4), 2017-03 .. 2025-12, well enough to trade the inclusion? Also count the events a
year, which is the power input for a later card. This is a feasibility census, not a test.

## Hard rule: return-blind
- Never compute or print a price return, a price path, or any price after the IPO's first-day close. The only price
  you may read per IPO is the **first-day close** (eligibility input). No T+1..T+4 prices, no post-inclusion prices,
  no index or fund flows. If a source table carries later prices, drop those columns unread.
- Volume and shares outstanding are allowed (eligibility inputs).

## Steps
1. **Ground truth (which IPOs CRSP actually fast-tracked, with dates):** look for anonymous public sources, for
   example CRSP / Morningstar index-change announcements or press releases, Vanguard (CRSP-tracking funds) or
   ETF holdings files that show additions, academic replication files (Murray and Sammon, RAPS 16(2), 2025, or its
   SSRN version / data appendix), or news lists. Record each source's URL, coverage and quality. If no ground truth
   exists, say so and stop at step 3 (counts only).
2. **IPO list:** US operating-company IPOs 2017-03 .. 2025-12 (exclude SPACs, units, ADRs, closed-end funds, REITs if
   the rule excludes them; note what you did). Free sources: SEC EDGAR (424B4 filings; full-text search or the
   daily / quarterly form index), the Nasdaq IPO calendar, Wikipedia lists as a cross-check. EDGAR needs a
   User-Agent: build it exactly as `research/screens/2026-11-26_r7_f01_stage_a.py` does (keyring
   `backtester-contact` / `email`), and never print or write the address. At most 10 requests a second to SEC.
3. **Eligibility from public data:** first-day close x shares outstanding at the IPO (prospectus, or the cover of
   the 424B4) against the CRSP small-cap / mid-cap breakpoint rule as the R8 report describes it (the breakpoint
   history is UNVERIFIED; find what you can, record the source; if missing, use a documented proxy and say so).
   First-day close: `data/cache/alpaca_1d/<SYMBOL>.csv` if present (read only the IPO date row), else another free
   source, the first-day row only.
4. **Agreement (only if step 1 gave ground truth):** confusion table (predicted vs actual fast-track), per year;
   list the misses with the likely reason (float, security type, breakpoint, non-US).
5. **Counts and power input:** fast-track events per year (ground truth if any, else predicted); how many are in
   our tradable top-1,000 (`data/cache/alpaca_meta` + `alpaca_meta_fwd`) by T+4; note the April 2026 float rule change.

## Allowed / forbidden
- May create: `research/screens/2026-11-26_fasttrack_census.py` (`download | census`), files under
  `data/cache/fasttrack/`, and the report `knowledge/research/reports/2026-11-26_fasttrack-census.md`. Nothing else.
- Never commit, push, branch; never start a server or a long-running process; never edit `src/backtester/live/`,
  `.env`, `src/backtester/tools/notify.py`; never read or print credentials (the keyring email only through the
  pattern above, never printed). No package installs. Anonymous HTTP only; if a site serves a bot-protection /
  CAPTCHA page, do not bypass it: back off, slow down, or drop the source and say so. Run only one downloader.
- Use `.venv/Scripts/python.exe`; run `ruff check` and `ruff format` on your script only.

## Done =
The report (sources, method, assumptions, agreement table or "no ground truth", events a year, top-1,000 share, a
verdict GO to a frozen card / PARK on data with a one-line reason), the script runs, ruff clean. End your answer with:
what you did, files, counts, any incident, and every assumption you made.
