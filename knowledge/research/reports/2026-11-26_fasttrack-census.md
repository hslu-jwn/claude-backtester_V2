# CRSP fast-track IPO census (return-blind), 2026-11-26 (Sonnet worker)

Only first-day closes were read, and only as an eligibility input; no later IPO price, return, index or fund flow was read or computed. Script: `research/screens/2026-11-26_fasttrack_census.py` (`download | census`); caches and outputs in `data/cache/fasttrack/` (`census.csv`, `census_eligible.csv`, `census_by_year.csv`, `census.txt`).

## 1. Ground truth: none found
Searched (web search, anonymous): CRSP / Morningstar index-change notices, Vanguard / Schwab / Invesco / BNY Mellon / Morningstar commentary, Murray and Sammon (RAPS 16(2), 2025). Result:
- No public per-IPO list of fast-track additions with dates. Morningstar index-change notices sit on a JS-only site (not readable); commentary pages name only single cases (2026) and rule text.
- Murray and Sammon: SSRN version and data appendix not located; the one nasdaq.com article that may discuss it timed out on fetch. No replication file confirmed.
- Rule facts from secondary sources (UNVERIFIED, conflicting in detail): inclusion at the 5th trading day after listing, seasoning 20 trading days otherwise, 10 % float minimum until April 2026, then 10 % FSO or about $3.3 bn float-adjusted cap (Schwab / Morningstar snippets).
- Not tried: monthly N-PORT holdings of VTI (SEC EDGAR) as an indirect ground truth. Month-end snapshots would show "held", but not fast-track versus normal inclusion. Worth a later look, not done here.
=> Step 4 (agreement table) cannot be done. Counts below are PREDICTED, not confirmed.

## 2. Method
- IPO list: Nasdaq IPO calendar API (`api.nasdaq.com/api/ipo/calendar?date=YYYY-MM`, priced deals, 2017-03 .. 2025-12): 3,164 deals (SPACs, ADRs, funds included). 106/106 months fetched. Pricing date taken as the Nasdaq "priced" date.
- CIK: name match (normalised) between the Nasdaq company and a 424B4/424B1 in the SEC quarterly form index (SEC `form.gz`, 2017Q1..2026Q1) within +-4 days: 2,303 matched, 861 unmatched (mostly later renamed companies, plus SPAC/ADR names; unmatched share by year 36 % in 2017, 11 % in 2025).
- Exclusions: SIC 6770 / 6726 / 6189 (blank-check, closed-end funds), name containing "acquisition" or "merger", business address not in a US state or PR (proxy for "primarily US" and ADRs). REITs kept (not excluded by anything I could verify).
- First-day close: first row of `data/cache/alpaca_1d/<SYM>.csv`, taken only when it falls 0-7 days after the pricing date. Rejected when close / offer price is outside 0.1-10 (Alpaca closes are split-adjusted, cover shares are not; 141 deals, mostly micro-cap reverse splits).
- Shares: dei cover-page shares outstanding of the first 10-Q/10-K filed after pricing (SEC companyfacts, distinct class values of that filing summed). Missing for 173 deals (direct listings, no XBRL cover tag).
- Float proxy: shares offered / shares outstanding >= 10 % (offer includes secondary shares; ignores greenshoe, lockups and non-IPO free float; true CRSP free float is unknown).
- Breakpoint proxy (UNVERIFIED): $2.4 bn at 2024-12-31 (R8 search snippet), scaled by the SPY close relative to 2024-12-31 (market level, not an IPO price). History not found. Sensitivity lines at flat $1.5 bn and $3 bn.
- Predicted fast-track = eligible row with market cap at first close >= breakpoint and float proxy >= 10 %.

## 3. Counts per year (predicted)
| year | priced deals | operating US, usable | predicted size+float | size only | size only at flat $1.5 bn | at flat $3 bn |
|---|---|---|---|---|---|---|
| 2017 (Mar-Dec) | 193 | 82 | 16 | 20 | 12 | 3 |
| 2018 | 258 | 107 | 29 | 32 | 29 | 13 |
| 2019 | 232 | 90 | 22 | 26 | 22 | 12 |
| 2020 | 477 | 121 | 34 | 38 | 32 | 17 |
| 2021 | 1,044 | 237 | 44 | 63 | 71 | 47 |
| 2022 | 187 | 33 | 3 | 3 | 3 | 2 |
| 2023 | 162 | 32 | 4 | 7 | 8 | 3 |
| 2024 | 239 | 67 | 9 | 10 | 12 | 6 |
| 2025 | 372 | 78 | 5 | 8 | 13 | 6 |

Total predicted 166 (2017-03..2025-12). "Usable" = US operating deals with a close and shares; a further 173 + 63 + 141 deals fell out for missing shares / close / split-adjusted close, and 861 had no CIK (so the table is a LOWER bound).
- Scale check: the paper's 262 additions for 2017-03..2022-12 against my 148 for the same window (56 %). The gap is plausibly the unmatched CIKs, missing shares, split-rejected closes and a conservative float proxy, but cannot be attributed without ground truth. Events a year: about 30-45 in 2018-2021 (the hot-IPO years), 3-9 a year in 2022-2025 (market for IPOs shut; 2025 also thin because of 34 deals without close or shares). Rough, UNVERIFIED planning figure: 20-45 a year in a normal year, about 10 in a weak one; averaged over 2017-2025 about 18 predicted a year (about 30 after scaling for the 56 % coverage).

## 4. Top-1,000 (`alpaca_meta` + `alpaca_meta_fwd`)
- By T+4: **0 of 166.** The universe is the top 1,000 by trailing dollar volume, so a new IPO cannot be a member in its IPO month or the next. Of the 166 predicted events, 72 ever enter it, the earliest after 3 months (13 after 4), the rest up to 42 months later; 94 never do. Ever-members by year: 2017: 8, 2018: 16, 2019: 13, 2020: 16, 2021: 11, 2022: 1, 2023: 2, 2024: 4, 2025: 1.
- Consequence: this universe cannot define the tradable set for this event. A card would need its own point-in-time liquidity rule from the IPO's first days' volume (allowed as an input, not read here) or a different execution basis.
- April 2026 float rule change: adds an absolute-float test (about $3.3 bn float-adjusted), so the 10 % float condition above is a 2017-2025 rule only; any 2026 sample needs the new rule (UNVERIFIED text).

## 5. Incidents and caveats
- No bot-protection page was met on the Nasdaq calendar or SEC. The Nasdaq stage was slow (backoff 0.5 / 5 / 30 s, no bypass was needed). One run hit my own 590 s timeout and was resumed from the cache; only one downloader ran at a time. SEC rate at most 8 requests a second, four threads.
- Breakpoint history, float definition, security-type filters and the buffer rules are not verified; the proxy could be off by tens of percent, which moves the predicted count (flat $1.5 bn vs $3 bn: 2021 71 vs 47, 2019 22 vs 12).
- Share-class and dual-class cover sums, direct listings, SPAC-merger "IPOs" (not in the priced list) and tickers reused by an older company are handled only coarsely.

## 6. Verdict: PARK on data
No ground truth, the breakpoint history is unknown, coverage against the paper's total is only 56 %, and the existing top-1,000 universe is empty at T+4. A frozen card is not justified until (a) an event list or the N-PORT route gives a reproduction check, or (b) the breakpoint history is found. If the user wants to go on: N-PORT check first (anonymous SEC data), then a card with its own IPO-day liquidity rule.

## 7. N-PORT check (2026-11-27)
Script `research/screens/2026-11-27_fasttrack_nport.py` (`list | identify | download | names | check`); cache `data/cache/fasttrack/nport/`. Return-blind: only name, title, CUSIP / ISIN, share balance, country and asset class of holdings were extracted (value, price and percent tags never parsed; raw XML not stored).

**Source.** SEC EDGAR, registrant Vanguard Index Funds (CIK 36405), series S000002848 = Vanguard Total Stock Market Index Fund (tracks CRSP US Total Market). Its NPORT-P filings list 28 reports, **quarter-end months only, 2019-09-30 .. 2026-06-30** (the other two months of a quarter are non-public). Filing lag about 60 days. So the data resolves "held at quarter end", not "held at T+4" or "added in week X".

**What the quarter-end grid can and cannot separate.** CRSP also adds non-fast-tracked IPOs at the quarterly reconstitution (assumed implemented after the close of the 3rd Friday of Mar / Jun / Sep / Dec; UNVERIFIED). An IPO listed before that date and held at quarter end is held under either route (not diagnostic). Only IPOs listed **after** the 3rd Friday of the quarter-end month, with T+4 (4 business days, holidays ignored) on or before the quarter end, are diagnostic: held at that quarter end means fast-track (or another non-reconstitution add), not held means regular. That is a window of about 5-8 trading days a quarter, so only 19 of 461 IPOs qualify.

**Sample and matching.** 461 IPOs from `census.csv` with a usable close and shares (why empty), 2019-03 .. 2025-12; 119 predicted eligible, 342 predicted not. The census has no CUSIP, so matching is by normalised company name (legal suffixes and share-class words dropped) against holding name or title, equity holdings only, plus the SEC former names of the CIK. Matches: 417 current name, 1 former name, 43 never found. No ticker or CUSIP step (holdings carry no ticker; the census no CUSIP), so false matches (same name, other company) and misses (renamed company, different spelling) are possible; sanity: 95.8 % of predicted-eligible and 88.9 % of predicted-not IPOs are found in some snapshot.

**Confusion table (diagnostic window, n = 19; actual = held at the first quarter end).**

| | held (fast-track-like) | not held (regular) | total |
|---|---|---|---|
| predicted eligible | 5 | 0 | 5 |
| predicted not eligible | 13 | 1 | 14 |

By year (n): 2020: 3 (all held, all predicted not), 2021: 14 (9 held predicted not, 4 held predicted eligible, 1 not held), 2022: 1 (held, predicted not), 2024: 1 (held, predicted eligible). Precision 5/5 = 100 %, **recall 5/18 = 28 %**. Sensitivity: widening the window to start 7 days before the assumed reconstitution gives n = 56 (predicted eligible 19 held / 1 not; predicted not eligible 27 held / 9 not; that window may include reconstitution adds); starting 7 days later leaves n = 0. Non-diagnostic IPOs (listed before the reconstitution): held at the next quarter end 103 of 114 predicted eligible (90 %), 211 of 328 predicted not (64 %).

**Misses (13 of 18 held IPOs were predicted not eligible).** The held ones include small caps by our proxy: Brilliant Earth (market cap about $164 m), Laird Superfood ($347 m), Thorne ($397 m), AN2 ($299 m), plus larger ones our rule rejected only on the float proxy (Vizio $3.5 bn, ACV $5.3 bn, Remitly $8.0 bn, EngageSmart $5.5 bn). The single not-held case is Miromatrix ($306 m, held first at 2021-12-31). So either CRSP fast-tracks (nearly) every IPO of the total-market universe, micro caps included, or the size breakpoint is far below the proxy and the 10 % float test is wrong; with this data the two cannot be told apart. The fast-track set is wider than our predicted set, so the census count (166, about 18 a year) is a lower bound.

**Verdict: PARK.** Recall 28 % (< 70 %) on 19 resolvable cases; precision is 100 % but on only 5. The public size-plus-float rule does not reproduce fast-track. A bigger observation: Vanguard Total Stock Market holds almost every sizeable US IPO within days. A card would need the real rule first (e.g. predict "all IPOs above a low size" and check on a larger window); the quarter-end grid is too coarse for more than about 4-5 diagnostic cases a year.

**Assumptions.** (1) Reconstitution date = 3rd Friday of Mar / Jun / Sep / Dec, T+4 = 4 business days, no holiday calendar. (2) Held at a quarter end after such a listing is taken as fast-track (the fund could in principle also hold it for other reasons, e.g. buying in the IPO, which index funds rarely do). (3) "Actual" is the fund's holding, a proxy for the CRSP index membership (sampling, cash flows). (4) Name matching as above, no CUSIP. (5) Predicted not-eligible = all 342 usable not-predicted IPOs, not a sample. (6) The 19-case window is thin; the verdict rests mostly on the 13 of 14 held among predicted-not.
**Incidents.** None: no bot-protection page, SEC rate at most 8 requests a second, one downloader, no process left running.
