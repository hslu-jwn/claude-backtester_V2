# Research log

Running log of the research loop (V2.6 / V2.7) and of the model / effort used per task, so a
run resumes after a restart or a usage limit. Newest first. Every AI call is also logged by
the dispatcher in `results/ai_calls.jsonl` (model, effort, seconds, status).

## 2026-11-14: Continue.Research Mode=auto (no limit), start

- Start 18:00. HANDOFF: free-data idea space looks exhausted; no runnable candidate (all M15 drafts triaged out).
- **Auto decision 1:** ask Fable 5.2 (subagent, model `fable`) now for the one long list of research directions
  (CLAUDE.md › Mode=auto, Advisor, allowed until 2026-11-16) -> `knowledge/reviews/2026-11-14-fable-research-directions.md`.
  Alternative: a harvest batch first. Why: the advisor window closes in two days and the list should steer the
  next harvests and screens.
- **Auto decision 2:** Binance positioning data (data.binance.vision `futures/um/daily/metrics`: 5-min open interest,
  top-trader and account long/short ratios, taker ratio) probed, **not downloaded**: BTCUSDT starts 2020-09-01, every
  other perp (ETH, BNB, LTC, DOGE, ZRX checked) only 2021-12-01, after the development cut (2021-09-14). A
  cross-sectional positioning idea would have no development data; BTC alone has ~54 weeks. Alternative: download
  all 37 and pre-register a test-only run. Why not: no development screen possible, one look at test data burns it.
- **Auto decision 3:** the two one-time MT5 tests in HANDOFF › Open 1 are **not run**. Neither passed pre-registered
  development gates (both are post-hoc best cells of the 2026-10-25 profiles), and both test periods look spent like
  gap fade's (review B3): V1 ran strategy 4 on GBPJPY M15 2023-26 (`docs/archive/ROADMAP-v1.md` line 1061); gap
  momentum ran on MT5 2021-26 (I-46, ROADMAP 11.12). Alternative: run them as the user pre-registered on 2026-10-26.
  Why not: a test on seen data proves nothing; striking them is the user's call (HANDOFF › Open).

## 2026-11-14: I-75 weekly crypto cross-sectional reversal KILLED (the user: "Yes, screen it")

- Card and kills committed before data (68f9726), script frozen (5267451), power line before the run (59b3cd5: t 3
  needed ~290 bp/week). Opus, local screen reusing I-73's helpers.
- Result: 81 weeks, net -146.8 bp/week, t -1.05, both halves negative (-177 / -117): KILLED on net <= 0. Large
  liquid perps show no reversal (the paper's effect is small-coin driven); the sign is momentum. Correlation with
  I-73's weeks +0.25. Model: Opus only.

## 2026-11-14: harvest batch 13 (crypto reversal / order flow, policy days, OPEC, gold macro days): nothing verified (the user: "New cells, terra high")

- Codex `gpt-6.1-terra` `--search` (high for ACAD, low for AGG / nonsense), 8 tasks T0089-T0096, 2 parallel, no guard
  alarms. 7 ideas, 0 verified: DeFi liquidation recovery and order-flow imbalance (untestable), FTSE after rate
  cuts and gold news lag (unverified: quote not on the page; terra high 2 of 7 here, 2 of 19 over batches 12-13),
  OPEC unchanged production (no rule, no size; parked), weekly crypto cross-sectional reversal (PDF 403 for the
  script and web-fetch; abstract read: 8.69 %/week loser-minus-winner, t 9.60, 200 coins 2015-2019, strongest in
  small / illiquid coins). Canaries: known answer PASSED, nonsense empty.
- Lead for the user: the crypto reversal is testable on the 37 cached perps (large / liquid only, so expect far
  less); it overlaps I-73's price part. Not carded: only the abstract was readable.

## 2026-11-14: harvest batch 12: batch 10-11 academic cells rerun on terra high: nothing new (the user: "Yes, rerun them")

- Codex `gpt-6.1-terra` high `--search`, 11 tasks T0078-T0088 (the 9 ACAD / CB cells of batches 10-11 with the same
  queries; vol targeting filed under IDX-US.SWING.FLOW; two canaries), 2 parallel, no guard alarms, 0 % unverified.
  12 ideas: the same ones terra medium found plus two new, both unusable (yen intervention aftereffect: untestable;
  gold ETP flows: needs ETP flow data, source unfetchable); I-74 found again (dedup: ledger URL).
- Canaries: known answer PASSED (Lustig et al., verified), nonsense empty. Reading: terra medium's misses were the
  named-paper canary, not the content cells; these cells are exhausted for our data. Model: Opus + Codex terra high.

## 2026-11-14: canary check: worker effort, not the query (the user: "Canary check first")

- Same sharp known-answer query (T0073's) on stronger settings: terra high (T0075) and sol medium (T0077) both found
  Lustig, Roussanov & Verdelhan "Common Risk Factors in Currency Markets" (quote verified by `harvest check`);
  terra medium had missed it in batches 10 and 11. Nonsense cell on sol medium (T0076): empty (pass).
- Routing (`docs/agent-routing.md`): ACAD / CB harvest tasks now on terra high; one run per setting, so watch the
  canary every batch. Batches 10-11's ACAD cells may have missed sources (rerun only on the user's go).

## 2026-11-14: harvest batch 11 (volatility state, open auctions, gold reversal): nothing to screen (the user: "1")

- Codex `gpt-6.1-terra` `--search`, 8 tasks T0067-T0074 (medium for ACAD, low for AGG / BROKER / BLOG), 2 parallel,
  no guard alarms. 10 ideas, 1 verified: Kang-Rouwenhorst-Tang hedger position-change reversal (score 6; Opus read
  the paper: +43 bp / 20 days, t 4.16, 1994-2012, half before the report is public) -> card I-74, below cost on our
  venue and needs COT data: not screened. The rest: implied-vol / variance-premium ideas (needs VIX / OVX / option
  data or unfetchable), two untestable; the open-auction cell found nothing.
- Canaries: nonsense empty (pass); known answer FAILED again (an ECB paper with the Lustig et al. portfolio design,
  but neither Koijen nor Lustig named): second failure in a row, worker recall on named papers is weak.
  Unverified rate terra medium --search 10.7 %, low 16.7 %.

## 2026-11-14: fsync fix; harvest batch 10 (forced flows): nothing to screen (the user: "1")

- `data/cache.write_atomic` now fsyncs before the rename (test-first; full suite 5,963 passed; ~8 ms per day file):
  the hard restart had left 52 Binance files with broken footers.
- Harvest batch 10, Codex `gpt-6.1-terra` `--search` (medium for ACAD / CB, low for BLOG), 8 tasks T0059-T0066
  (oil settlement window, gold delivery / roll / ETF flows, Japanese investor flows in yen crosses, reserve and
  intervention FX flows, vol-targeting rebalancing; two canaries), 2 parallel, no guard alarms. 4 ideas, 0 kept:
  crude order-imbalance impact (untestable: tick order flow, no rule), Swiss intervention (untestable), gold
  delivery-month premium (+0.36 %/month front vs second contract, 1979-2019: a futures term-structure effect, not
  tradeable on the gold CFD; no paid futures data; parked unfetchable), canary paper unverified.
- Canaries: nonsense empty (pass); known answer FAILED (a different G10 carry paper, quote not on the page;
  Koijen / Lustig not found). Unverified rate terra medium --search 15 % (stays below 20 %).
- `harvest check` needs the Avast web-shield CA here (`NODE_EXTRA_CA_CERTS`): certifi + that file as
  `REQUESTS_CA_BUNDLE` (scratchpad copy); the first run without it parked everything as unfetchable (reverted).

## 2026-11-14: I-73R replication on 20 unseen perps FAILED (the user: "Yes, replicate I-73")

- Universe and gates pre-registered before the download (ba253bc), script frozen (0a5a1f3), power line before the
  run (b9f3fa9: t 2 needed 85 bp/week, expected t ~2.6). Download 20 perps (~7 GB); the session's hard restart
  left 52 damaged parquet files (SXP 2023-04, price + flow; `write_atomic` has no fsync): deleted, re-downloaded,
  full scan of all 37 perps clean.
- Result: net +63.4 bp/week, t 1.05, halves -18.9 / +145.7, without 2 best +14.8: FAILED on t and halves. Funding
  part +48.5 holds, price part +35 vs +103 on the original 17. 37-symbol union +59.6, t 1.11. Model: Opus only.

## 2026-11-14: resumed (the user: "Continue."); HV-T0020-3 closed as untestable

- Funding-extreme fade on single coins, power check on 17 perps (signal-free, development): 920 episodes but only
  122 separate 72 h clusters; 72 h sd 1,132 bp -> t 3 needs ~300 bp per episode vs 59 bp halved claim. Closed,
  not screened; the cross-sectional version (I-73) covers the mechanism. Model: Opus only.

## 2026-11-14: paused (the user: "Pause.", "finish everything first")

- Clean point: strategy 19 tool built and committed (2bfc8b1), full suite 5,962 passed, ruff clean. Resume with:
  forward log from about 2026-12-02 (HANDOFF › Open 4), then the next Binance idea or HANDOFF › Open.

## 2026-11-14: Strategy 19 research tool built (the user: "Yes, all three")

- Codex `gpt-6.1-sol` medium (brief `briefs/crypto_carry.md`, ~25 min, guard ok): `strategy/crypto_carry/book.py`,
  `tools/crypto_carry.py`, 15 tests. It stopped correctly on a spec conflict: ties are common (default 0.01 %
  rate) and A5 "ties by symbol name" was not what the screen did (universe order, stable sort); name order gives
  development +124 / test +110 bp, t 2.92. Opus fixed A5 to the frozen tested behaviour (the spec's own rule).
- Opus fixes: `--update` only the last 3 months (was from 2019-09: hundreds of failing requests per run); a
  delisted symbol no longer stalls the forward log, measured against the newest funding print (a first fix
  against the Monday would have let a lagging feed write zero-signal weeks into the log; caught by its test);
  layer rule (strategy must not import engine: cost as config, pinned by a test); an old test fake broken by
  the klines commit 2303ecf (`test_v26b_data`, signature only).
- Golden: development and test identical to the screen. Monte Carlo of the test weeks at 1 % risk per R: median
  +34 % over 5.1 years, max drawdown median 4.6 % / p95 8.1 % (optimistic: resamples the observed edge).

## 2026-11-14: I-73 one-time test PASSED (the user: "Yes, run I-73 test")

- Gates pre-registered before any test data (30c10b1), script frozen (fc59ab7), development re-run identical
  (+138.0 bp, t 1.30). One assumption fixed before the test: signal = funding accrued in the last 7 days (XTZUSDT
  settles every 4 h / 1 h from 2025-07-20; identical ranking for 8 h symbols).
- Test 2021-09-20 .. 2026-10-19, 266 weeks: net +112 bp/week, t 2.93, pooled t 3.08, halves +105 / +119, without
  2 best +95, doubled costs +92, PF 1.72, max drawdown -3,967 bp, worst week -3,159 bp. All five gates pass.
- Data check: EOS prices end 2025-05-21 while its funding file continues (constant placeholder); ranking only
  symbols with an entry bar gives +110 bp, t 2.98. Model: Opus only. Telegram sent.

## 2026-11-13: Continue.Research on Binance futures (Test=manual, no limit): cost check; I-72 KILLED

- Project moved; memory notes copied to the new project key (7 files), no old paths in the settings.
- Cost model check (HANDOFF › Next step 2): `engine/costs.py` charges BTCUSDT / ETHUSDT taker 0.05 % per side
  (10 bp round trip) plus funding every 8 h from `binance_funding`, longs pay a positive rate: matches Binance's
  published regular-user USD-M fees (maker 0.02 %, taker 0.05 %). No spread or slippage is modelled (Binance
  data is last-trade M1, bid = ask); screens report net at 12 bp as a stress diagnostic. 2020-21 taker was
  0.04 %, so 0.05 % is conservative for the development period.
- I-72 funding-settlement drift (card and kills committed before data, 1559dbf; Opus, local pandas screen):
  1,758 symbol-events, PRE gross -0.3 bp, POST +2.3 bp vs 10 bp cost; no-settlement hours look the same.
  KILLED, family `funding_settlement` closed. Model: Opus only (no dispatch).
- Power check, funding-extreme fade (parked HV-T0020-3): 46 BTC / 55 ETH 72 h episodes in development vs
  ~1,300 needed at the halved claim. Binance on two symbols: intraday effects are below 10 bp (crypto intraday
  report: 3-10 bp), multi-day effects are underpowered in 20 months. Asked the user for more symbols (breadth).
- The user: "Yes, 15 perps". Opus built `binance_download --klines` test-first (4 tests; 1m klines + taker-buy
  volume, same cache format) and downloaded BCH, XRP, EOS, LTC, TRX, ETC, LINK, XLM, ADA, BNB, XTZ, XMR, NEO, DASH,
  ATOM 2020-01/02 .. 2026-11 (5.4 GB, ~70 min; EOS delisted: 530 days missing after it).
- I-73 cross-sectional funding carry (source: BIS WP 1087 "Crypto carry", read in full; card and kills 
  committed before the new data was read, b586776; power line before the screen, 5c04fec): 82 weeks, net
  +138 bp/week, t 1.30 -> KILLED on t < 3.0 (t 3 needed ~300 bp/week). Price part +106 bp has the paper's
  sign; all of it in 2021 (halves +2 / +274). Model: Opus only; web-fetch subagent for the paper (failed to
  read the PDF; Opus used pdftotext locally).

## 2026-11-13: research paused (the user: "first pause, I'll restructure the folder location")

- Decisions by the user: no paid futures data for now; Binance futures (cached data) is the viable next
  direction. Paused at a clean point (no lane, queue or dispatch running).

## 2026-11-13: harvest batch 9 (forums, Reddit, GitHub, podcasts, books): nothing to screen (the user: "search for more ideas")

- Codex `gpt-6.1-terra` medium `--search`, 8 tasks (T0051-T0058; first use of FORUM, REDDIT, GIT, AV, BOOK sources;
  two canaries), no guard alarms. 6 ideas, 0 verified, 12.5 % unverified. Canaries: nonsense empty (pass);
  carry known answer = Koijen et al. "Carry" itself (pass). Nothing to screen: two ES order-flow setups need
  order-book / delta data (authors: unprofitable / little left after fees), post-opex reversal (opex family
  killed, I-70), Binance funding capture (not on FTMO CFDs), a discretionary NFP read. GitHub and books: none.
- Checker bug fixed test-first: a quote matched only fuzzily made the seller check scan the whole page (the
  canary paper was rejected as `sells_course` on bond "coupon"); now only the text around the matched window,
  and never on papers / central-bank sources. No earlier rejection was affected.
- Opus checked the own backlog meanwhile: the open I-xx ideas are bar-pattern / indicator rules (cost-wall stop
  list) or closed families (month-end, local hours, carry under swap).

## 2026-11-13: harvest batch 8 (central bank / exchange sources): nothing to screen (the user: "Run batch 8")

- Codex `gpt-6.1-terra` medium `--search`, 8 tasks (T0043-T0050: DAX expiry settlement, US closing auction /
  settlement, ECB 14:15 fix, LBMA gold auction, oil index roll, BOJ ETF buying; two canaries), 17-41 s each,
  no guard alarms (answers saved after all calls). 3 ideas, 0 verified. Canaries: nonsense empty (pass);
  carry known answer found a carry paper citing Koijen et al. and Lustig et al. (pass).
- HV-T0045-1 ECB-fix dollar reversal (Bank of Canada SWP 2021-48): parked unfetchable (robots; a manual fetch
  got only the archive interstitial). Same USD-demand-around-fixings mechanism as the falsified `london_fix`
  family (cost wall stop list); recorded there, not screened. HV-T0048-1 BOJ ETF afternoon effect: the forced
  buyer is gone (purchases scaled down 2021, stopped 2024), untradeable now. HV-T0049-1: the canary.

## 2026-11-13: harvest pipeline fixed (the user: "Yes, fix pipeline")

- Opus, test-first (`tests/tools/test_harvest.py`, 8 new cases). On a closer look the quote matcher was right:
  the two fetched misses of batch 7 (arXiv abstract, Whaley OCR PDF) are paraphrases, not on the page. Real
  defects fixed: (1) a page the script may not or cannot read (robots.txt, 401 / 403 / 429, login wall, no
  answer) is now parked `unfetchable`, not the worker's `unverified_source` (a 404 still is); (2) `check`
  appends to `checked.jsonl` instead of overwriting it; (3) skill: known-answer canary from an open family
  (`ACAD.FX-MAJ.SWING.CARRY`, Koijen et al. / Lustig et al.), answers saved only after parallel calls end.
- Batches 6-7 rechecked: HV-T0033-1, HV-T0036-1, HV-T0038-1 -> parked unfetchable (academia.edu, ResearchGate);
  none worth a manual read (day-of-week family closed; single-stock auctions; needs option positioning
  data). Real unverified rate: terra low 1 of 5 (20 %), terra medium 2 of 7 (29 %) on ACAD; the routing
  note stands (medium for ACAD, watch the rate).

## 2026-11-13: harvest batch 7 (index flows, terra medium): nothing verified (the user: "Yes, run batch 7")

- Codex `gpt-6.1-terra` medium `--search`, 8 tasks (T0035-T0042: the four ACAD tasks of batch 6 again, DAX
  expiry auction, US expiry opening; two canaries), 10-82 s each: 7 ideas, 0 verified (4 unverified_source,
  3 untestable). Nothing to card: quarterly-expiry opening reversal (Whaley; 4 events a year, closed family
  `calendar_clock` "triple witching", pre-2000 evidence); DAX expiry opening reversal (1996, settlement has
  moved to the 13:00 intraday auction); the rest need option / order-book data or state no price rule.
- **Pipeline defects found (for Continue.Code):** (1) the known-answer canary "local hours" can never pass:
  the prompt tells the worker to skip closed families and `fx_hours` (Breedon & Ranaldo) is closed since
  2026-11-11; batch 6's "canary failed" is this, not the worker's recall. (2) `harvest check` marks blocked
  hosts as unverified_source (ResearchGate 403, academia.edu robots) and misses quotes on fetched pages
  (arXiv abstract, a PDF); 4 of 7 here. The 40 % rule on batch 6's terra low stands on its own numbers but
  is confounded by (2). (3) Opus's driver still wrote answer files mid-run (guard exit 3 on 5 calls, answers
  valid); fixed in the scratch driver.

## 2026-11-13: harvest batch 6 (index flows) + I-71 UK100 review-auction short: KILLED (the user: "Yes, run batch 6")

- Codex `gpt-6.1-terra` low `--search`, 8 tasks (T0027-T0034, 2 parallel, 17-44 s each): 5 ideas, 1 verified.
  Canaries: nonsense cell empty (pass); known-answer cell "local hours" FAILED (Breedon & Ranaldo not found).
  Unverified rate 40 % (2 of 5) on ACAD sources -> terra low taken off academic searches (rule: > 20 %);
  batches 3-5 used terra medium. Exit 3 on five calls was Opus's driver writing answer files while the
  other call ran (guard: read-only task changed); the answers are valid. `harvest check` overwrites
  `checked.jsonl`: restored from git and batch 6 appended.
- HV-T0031-1 (score 5 -> 6: the worker's "costs_ignored" flag was wrong, the source states net of costs).
  Opus read the source (KruegerAlgorithms, sells an MQL5 tool): card I-71, rule and kills committed before
  data (2365c6d). Screen (Opus, local): 83 event days, gross +11.7 bp, net +9.0 bp, **t 2.16 < 3.0: KILLED**;
  pre-sample +12.5 (n 34) / dev +6.5 (n 49), other weekdays +0.0 bp. Sign replicates out of sample, power
  too low (~160 events needed). Family `index_review_auction` closed.

## 2026-11-13: Continue.Research (Test=manual, no limit): cost wall refresh; placeholder spreads fixed

- No runnable candidate, no carded idea (HANDOFF › Open 4); a harvest batch needs the user's OK (asked).
  Meanwhile (Opus, local): dev-period cost at a 0.5 daily-ATR stop with today's costs (cost-wall §3).
- Found while doing it: the MT5 history 2020-21 of EURUSD, AUDUSD, USDCAD, USDCHF, USDJPY, EURJPY, EURGBP has
  a constant 50-point spread on 23-88 % of the bars; the table extended today carried it (EURUSD 2020: 5 pips
  every hour). Dropped those years (test-first); 2020 -> 2019, 2021 -> 2022 values. GBPUSD's same cells in the
  original table: question for the user. Golden lists (2023) unaffected.

## 2026-11-13: spread table extended, option A (the user: "A: full table")

- Opus, test-first (`tests/engine/test_spread_table.py`, `test_spread_table_factor.py`; step-9 test updated to
  the new rule). 27 symbols merged into `engine/ftmo_spread_median.json` and `data/spreads/` (median + p90),
  without AUS200 2019-21, DXY 2024, BTCUSD / ETHUSD; factors GER40 1.07, UK100 1.09, UKOIL 1.09, US30 1.10,
  USDCAD 1.09, USOIL 1.08. Spec `risk-management.md` › Costs.
- Golden (2023 net R): london_fix -273.4 -> -373.7; alternating_path -491.1 -> -483.4 (2,516 -> 2,512 trades);
  opening_range -36.6 -> -27.8; daily_reversal 3.9 unchanged (to 0.1 R). No verdict changes. Full suite
  5,926 passed; golden 13 / 13; ruff clean.

## 2026-11-13: hourly spread table for the other symbols, proposal (the user: "Hourly fixed spreads")

- Opus, local scripts (`scripts/cache_spread_table.py`, cache ask - bid; GBPUSD / XAUUSD rebuilt from the
  cache match the packaged table within one tick). 29 symbols, median by New York year and hour.
  Hour 17 is 9-20x the fixed spread for FX; London / New York hours of the FX majors 0.5-0.7x (the
  2026-11-09 raises used the all-hours live mean); FX 2015 2-8x. Feed artifacts excluded (AUS200
  2019-21, BTCUSD / ETHUSD, DXY 2024).
- Impact (net R, today -> table): london_fix 2023 -273.4 -> -368.5 (its time exit at 17:05 New York pays the
  rollover spread on shorts), 2016 -191.7 -> -326.7; alternating_path 2016 -514.4 -> -746.6, 2023 -491.1 ->
  -482.9; opening_range 2023 -36.6 -> -27.5. Variants B (never below fixed) and C (hour 17 only) in
  `docs/spread-table-extension.md`. No default changed; waiting for the user.

## 2026-11-13: GBPJPY 1.09 / GBPUSD 1.38 (the user: "Yes, 1.09 / 1.38")

- Opus, test-first: `LIVE_TABLE_FACTOR` = ratio of means over all fill probe entries at the bar-close
  lookup (`fill_spread_time`), one factor for every hour. Spec `risk-management.md` › Costs.
- Golden (2023 net R): no_wick -1276.8 -> -1293.9; session_zone_sweep -478.3 -> -494.6; alternating_path
  -490.7 -> -491.1; london_fix -273.3 -> -273.4; h1_shock / trend_following below 0.1 R. No verdict
  changes. Full suite 5,915 passed; golden 13 / 13; ruff clean.

## 2026-11-13: rollover fixes a + b + c applied (the user: "Yes, a + b + c")

- Opus, test-first (`tests/engine/test_fill_spread_time.py`, factor and gate 7 cases). (a) `fill_spread_time`
  (1 µs before the fill instant) at every fill / signal spread lookup: engine entry, cost filter,
  break-even offset, limit penetration, two-leg entries, entry screens, a strategy's signal cost, fill
  report. (b) GBPJPY `LIVE_TABLE_FACTOR` 1.40 -> 1.06. (c) gate 7 window 16:55-18:00 New York (zoneinfo).
  Specs: `risk-management.md` › Costs, `strategy-timed-hold.md` › Gate 7 decision.
- Open question for the user: with the new lookup, the live-ratio method gives GBPJPY 1.09 (not 1.06)
  and GBPUSD 1.38 (not 1.33); 1.06 / 1.33 kept as approved.
- Golden lists rewritten (2023 net R old -> new): session_zone_sweep -513.5 -> -478.3 (2,961 -> 2,962
  trades; GBPJPY factor); no_wick -1277.7 -> -1276.8 (4,166 -> 4,164); h1_shock 0.5 -> 0.7; ny_index_sweep
  -32.1, trend_following 14.4, opening_range -36.6 change below 0.1 R. No verdict changes (all falsified
  or closed). Full suite 5,916 passed; golden 13 / 13 identical after the write; ruff clean.

## 2026-11-13: rollover-hour spread measured (Continue.Code; the user picked "1")

- Opus, local scripts only. The under-charge of "NY hour 18" is one instant, not an hour: live probe
  entries at 18:00 NY were 12.8x the table (44 fills), at 18:30 1.5x, at 19:00 1.5x. The MT5 cache
  shows why: the wide rollover spread runs 17:05-17:59 NY (GBPUSD ~20x the day median, the table's
  hour 17 already charges ~16x) and drops back within the 18:00 minute. An order sent at 18:00:0x
  still pays the hour-17 spread (buys at 18:00 paid 16.6x the table; GBPUSD 0.00119 vs table h18
  0.00005, h17 0.00064).
- The engine looks the entry spread up at the signal bar's close (`now` = 18:00:00 -> hour 18). For the
  8 table-symbol buys at 18:00, the previous hour's value fits (paid / model median 1.09 vs 10.3); at
  every other :00 both lookups fit equally (|log| 0.62 vs 0.66, n = 271). `scripts/rollover_spread_check.py`.
- Reach: golden lists 20 of ~14,000 trades enter at 18:00 NY sharp (no_wick 17, session_zone_sweep 3;
  both falsified). The 18 symbols without a table pay a flat fixed spread at every hour, hour 17
  included (EURUSD buys at 18:00 paid ~5 pips vs 0.2 fixed).
- Gate 7: `rollover_integrity_failures` tolerates gaps 21:00-22:59 UTC (fixed hours); the FTMO break is
  16:55-17:05 NY (20:55 UTC in US summer, 21:55 in winter), so summer gaps from 20:55 fail.
- Proposals for the user (no default changed): (a) entry spread = value of the bar that just closed;
  (b) then GBPJPY's live factor 1.40 -> 1.06 (its hour-18 share is gone); (c) gate 7 window 16:55-18:00
  NY via zoneinfo. HANDOFF › Open 3 / 5.

## 2026-11-13: challenge path simulator (Continue.Code; the user: "do all")

- FTMO rules verified on ftmo.com (web-fetch subagent, pages dated 2026-10/11): 2-Step 10 % / 5 %, 5 % daily,
  10 % static, 4 days; 1-Step 10 %, 3 % daily, 10 % end-of-day trailing, best day <= 50 %; Instant no target,
  3 % daily, 10 % intraday trailing, best day <= 30 %, 90 % split. Fees and the 1- / 2-Step split are not on
  the pages: inputs. Spec `risk-management.md` › Challenge path simulator (assumptions listed there).
- Core + CLI: Codex `gpt-6.1-sol` medium, write, lane `challenge_path` (brief
  `briefs/challenge-path-1-core.md`). Opus review found one rule error: attempts inherited trades entered
  before their start; fixed (entry date >= start) with a test. Smoke run on the F1a EURUSD development run
  (1 % risk, 80 monthly starts): 2-Step pass 36 %, 1-Step 34 %, Instant max-loss breach 55 % (closed lead;
  numbers only show the tool works).
- Results tab "Challenge path": Codex `gpt-6.1-terra` medium, lane `challenge_ui` (brief
  `briefs/challenge-path-2-ui.md`). Opus browser check (dev port 8052, F1a EURUSD run): added a "Phase 1 passed"
  marker (the Verification reset looked like a crash; phase results now carry their day) and 1-decimal
  numbers; 1-Step floor trails 90,000 -> 99,072, never falls. Full suite 5,905 passed, golden 13 / 13.

## 2026-11-13: GBPUSD live spread factor 1.33 (Continue.Code; the user: "do all")

- Opus: the 2.18x live mean / table ratio (fill probe runs 3 + 4, 309 fills) is one hour: NY 18 (reopen
  after the rollover) 10.25x; all other hours 1.33x, London + NY hours 1.12x. `LIVE_TABLE_FACTOR` GBPUSD
  1.33 (test-first, `tests/engine/test_spread_table_factor.py`); GBPJPY 1.40 kept (1.06 without hour 18;
  costs are never lowered without the user's go). Spec `risk-management.md` › Costs.
- Golden lists rewritten for the six GBPUSD strategies (2023 net R old -> new): session_zone_sweep -503.9 ->
  -513.5; no_wick -1224.7 -> -1277.7 (4,170 -> 4,166 trades: the stop-in-spread refusal); london_fix
  -272.0 -> -273.3; alternating_path -488.3 -> -490.7; h1_shock 0.6 -> 0.5; trend_following 14.4 unchanged.
  All falsified families; no verdict changes. Check: 13 / 13 identical after the write.

## 2026-11-12: data fixes accepted; MT5 GBPUSD 2019 quarantined (Continue.Code; the user: "Accept, fix GBPUSD")

- Opus (no dispatch): read-only check `scripts/data_fix_check.py` -> `docs/data-fix-check.md`; 13.12-13.18
  accepted by the user. New finding: MT5 GBPUSD 2019-02..09 5-10 pips off its own GBPJPY / USDJPY cross
  and histdata (normal days 0.1-0.4 pips). Fix test-first (`tests/data/test_cross_quarantine.py`, 6 tests):
  `cache_repair --cross-check`, 149 days moved to `data/cache/mt5/_quarantine/GBPUSD/`, histdata fills them.
- Not a gate look; no closed family is re-run. Every earlier development result that read GBPUSD 2019
  (strategy 1, London fix, R014, F1a / F1b) used the bad days; F1a's joint-rule failure on GBPUSD
  (-25.8 R) is among them, but F1a is closed by its pre-sample check (2026-11-11).

## 2026-11-12: Continue.Research Test=auto (the user): no candidate eligible; I-68 closed on power

- Start: no runnable candidate (README: all M15 drafts triaged out), no open carded idea with a mechanism
  except I-68 (parked, needs an EIA download) and T-20 (cost tooling; no cell near cost is still open,
  and using it on a closed cell would be a rescue). Test=auto had nothing to act on: no candidate has
  passed every development gate.
- I-68 power check (Opus, no dispatch; `research/screens/2026-11-12_i68_power_check.py`, volatility only,
  no edge look, no download): USOIL monthly sd 12.5 % (130 months, 2010-11..2021-09). Halved published
  carry ~0.7 % per month needs ~2,700 months for t 3; EIA 1986-2021 gives expected t ~1.2. **Closed on
  power** (ledger I68); the download is not needed.
- Consequence: HANDOFF Open 4 (direction) is the only way forward for research; the loop stops here.

## 2026-11-12: cost-frame diagnostic (the user: "Rethink the cost frame"; not a gate look)

- Same pairs screen, three cost frames (diagnostic only, verdicts unchanged):
  FTMO as modelled (credits off): P01 net -124.2 bp, P02 -14.1; FTMO with swap credits: P01 -53.1, P02
  -14.1; no swap (futures-like): P01 **+194.0 bp per trade (t 1.27, 18 trades, halves +63 / +324)**, P02
  +12.0 (t 0.22). P01's round trip is only ~15 bp; ~318 bp per trade is swap on two oil legs over ~17 days.
- Other ideas of the day are not cost-bound: I-51 gross Sharpe already negative, I-67 / I-70 killed on t,
  L15 / L17 spread-bound intraday. So a cost-frame change alone unlocks nothing that passes t >= 3; the
  only lead it would create is P01 under futures costs, which still needs more sample (pre-sample
  2010-2014 USOIL / UKOIL exists) and a venue decision (FTMO CFDs pay swap; futures do not).

## 2026-11-12: pre-build screen of pair drafts P01 / P02: both KILLED (auto mode)

- Opus (no dispatch): `research/screens/2026-11-12_pairs_screen.py`, committed before the run (22b792f).
  Primary cells, development only, stops not simulated, equal notional, both legs' round trip + swap.
- P01 USOIL / UKOIL: 18 trades, hold 17.5 d, gross +209.3 bp, net -124.2 bp (t -0.78), halves -279.5 /
  +31.2. P02 XAUUSD / XAGUSD: 22 trades, gross +20.4 bp, net -14.1 bp (t -0.26). **Both killed.** Oil
  shows a gross edge that two legs' swap over weeks eats (~333 bp per trade); both are underpowered anyway.
- Consequence: two-leg 2b (research / risk integration) deferred until a pair idea clears a screen.

## 2026-11-12: two-leg trades, increment 2a-3 group runner and result files

- Codex `gpt-6.1-sol` medium, write, worktree `two_leg3` (brief `briefs/two-leg-2a3-runner.md`), 578 s:
  `group_runner.py` (bounded loading, warm-up discarded, one `trades.csv` row per group in the legacy
  schema and cost signs, `group_legs.csv`, `rejected.csv`, `unresolved.json`, `settings.json`), 14 tests.
  Opus: checked the row mapping against `components()`; classified `group_runner` as app level in
  `tests/test_layers.py`. Full suite 5,852 passed, golden 13 / 13 identical.
- Next (2b): a first pair strategy needs a spec (P01 WTI / Brent or P02 gold / silver drafts) with its
  rules for entry eligibility, exits after a stop, missing marks, then research integration and risk.

## 2026-11-12: two-leg trades, increment 2a-2 paired M1 engine

- Codex `gpt-6.1-sol` medium, write, worktree `two_leg2` (brief `briefs/two-leg-2a2-paired-engine.md`),
  568 s: `engine/group_backtest.py`, `GroupStrategy`, 24 engine tests (cross-symbol lookahead, future
  append, atomic next-open entry, expiry, peer exit at next open, residual / stale marks, costed example).
  Opus review: clock causality checked line by line (entry only at the next minute's open, peer exits at
  the next candle's open). Full suite 5,837 passed, golden 13 / 13 identical, legacy files untouched.

## 2026-11-12: two-leg trades, increment 2a-1 (the user: "Yes, build two-leg")

- Codex `gpt-6.1-sol` medium, write, worktree `two_leg` (brief `briefs/two-leg-2a1-group-model.md`), 400 s:
  `strategy/group.py`, `engine/group_trade.py`, 47 tests. Opus review found one real error, caused by the
  brief: P/L valued as `q*(exit*v_exit - entry*v_entry)` books a conversion gain on the whole notional;
  fixed to `q*(exit - entry)*v_exit` (CFD cashflow = price P/L at exit), test corrected, decision in
  `docs/design/multi-symbol.md` › B. Full suite 5,804 passed, golden 13 / 13 identical.

## 2026-11-12: A3 one gates tool (auto mode, "your pick")

- Codex `gpt-6.1-sol` medium, write, worktree `a3_gates` (brief `briefs/a3-gates-tool.md`; two worker
  questions answered in the brief first: always-on gates, the controls' sd), 743 s:
  `tools/gates.py` (`[gates]` table in the grid, `--controls N`), circular block bootstrap moved to
  `analytics/bootstrap.py` (old names re-exported, outputs pinned), `[gates]` excluded from the research id.
- Opus review: the generic tool on the real strategy 14 run gives the same verdicts, gates, net R, halves,
  bootstrap and control numbers as `us_close_de_open_gates.py` (0 differences; only the missing-US500
  diagnostic is tool-specific). Full suite 5,755 passed, golden 13 / 13 identical, ruff clean.

## 2026-11-12: harvest batch 5 (intraday events, >= 20 bp per event): nothing new (auto mode)

- Codex `gpt-6.1-terra` medium `--search`, 6 calls (11-38 s). Both canaries pass again. CPI / NFP index
  drift, ECB EURUSD, gold after US data: 0 ideas each; BOJ / DAX: 1 (pre-ECB DAX drift, on the cost-wall
  stop list, not re-tested). Ledger HV-T0021-1 (canary duplicate), HV-T0026-1.
- Day total: 5 batches, 26 tasks, 13 ideas, 0 alive. Every looked-at idea of the day killed or rejected;
  cost-wall page updated (no live leads).

## 2026-11-12: harvest batch 4 (practitioner sources) + I-70 opex week: KILLED (auto mode)

- Codex `gpt-6.1-terra` medium `--search`, 6 calls (12-47 s), queries limited to CFD-tradable ideas.
  Both canaries pass for the first time: T0015 Quantpedia option-expiration week found, T0016 nonsense
  words empty. T0017 gold flows 0; T0018 expiration weeks 2 (1 verified); T0019 Nikkei ex-dividend 1
  (untestable); T0020 bitcoin funding extremes 3 (2 verified, 1 merged). Scores 3-4 (< 6).
- Opus picked I-70 (opex week on US500; funding fades deferred: funding data only from 2020, crypto
  swaps heavy). Rule + kills committed in d3c8161 before data; pre-sample 2010-2014 + development
  2015-2021-08. Result: 129 weeks, gross +8.7 bp, net -3.8 bp (t -0.19); pre-sample +4.8 / development
  -9.1 bp; all other weeks gross +31.1 bp. **Killed** on all three criteria: the published effect is gone
  out of its sample.

## 2026-11-12: H13f frozen CAP on pre-sample + development: KILLED (auto mode, the user)

- Opus 5.5 (no dispatch): grid `research/grids/daily_reversal_cap_presample.toml` (committed a3471b8 before
  the run; CAP, 2R, hold 5), `--cache-dir data/cache/histdata_presample --dev-only`: 2010-2014, 5 indices,
  18 trades +1.72 R. Pooled with development CAP / 2R (32 trades +5.1 R): 50 trades, net +6.82 R,
  doubled +6.22, mean +0.136 R, bootstrap lower -0.087, March 2020 -1.02 R.
- **Killed** (< 80 trades, bootstrap bound <= 0). Third look in daily_reversal (E8, TS falsified, now
  CAP killed): family closed, also in `research/harvest/known_families.csv`.

## 2026-11-12: harvest batch 3 + I-69 screen: KILLED (the user: "Codex is reset")

- Codex `gpt-6.1-terra` medium `--search`, 5 calls (17-36 s), queries limited to CFD-tradable ideas:
  T0010 known-answer canary now finds the option-expiration-week effect (Scribd copy, 403 for the
  checker); T0011 nonsense canary returned an IG Bollinger page (canary too plausible: needs a better
  nonsense cell); T0012 BOJ ETF / JP225 dividend flows 0 ideas; T0013 single-leg oil roll 0;
  T0014 bitcoin futures expiration week 1 (quote verified, filtered as untestable: no explicit entry).
  Unverified rate terra medium 1 / 3.
- Opus carded I-69 (rule + kills committed in c487e2b before any data): long BTCUSD Monday 00:00 to
  Friday 15:00 UTC in CME expiry weeks, 2018-01 to 2021-08. Result: 41 weeks, gross -60 bp, net -100 bp
  per week (t -0.72), 46 % positive; other weeks +95 bp gross. **Killed.** The paper's sample is our
  development period, so this is a failed replication of its in-sample claim.

## 2026-11-12: web-access probe + harvest pilot 2 (the user: "Web probe + harvest")

- Probe (Opus, direct one-line `codex --search exec`, terra low, 12 s): found and quoted the Breedon &
  Ranaldo canary. Cause of the empty pilot 1: `ai_dispatch` never passed `--search`. Fixed test-first:
  `ai_dispatch --search` (Codex only, refused for write tasks: web pages are untrusted input), 35aea66.
- Pilot 2 (Codex `gpt-6.1-terra` low `--search`, 5 calls, 21-31 s each): T0005 known-answer canary
  (option-expiration week, Stivers & Sun) MISSED, it returned another option-expiry paper; T0006 nonsense
  canary correctly empty; T0007 Goldman roll WTI spread, T0008 crypto funding-time spreads, T0009 dealer
  gamma: one idea each. T0003 / T0004 skipped (families now closed: turn_of_month, london_fix).
- `harvest check`: 4 of 4 `unverified_source`. Three sources are PDFs, which the checker reads as raw
  bytes (tool bug, not bad citations); ResearchGate refuses bots. Terra NOT taken off academic sources on
  this batch (the 20 % rule would be applied to a tool bug). None of the four is runnable on our data
  anyway (options, futures spreads, no rule, options gamma). Ledger rows HV-T0005-1 .. HV-T0009-1.
- Known families: trend and turn_of_month marked falsified (now in the prompt's skip list).
- Follow-up (the user: "YES, but wait for codex reset"): `harvest check` reads PDFs (`pypdf` in the data
  extra, test-first with a compressed test PDF). The other cause of the 4/4 unverified: in this sandbox
  Python's `requests` failed every fetch with an SSL error (proxy CA only in `NODE_EXTRA_CA_CERTS`); with a
  combined CA bundle (skill note) the recheck gives T0007 verified (not runnable: futures spread),
  T0005 untestable (options), T0008 404, T0009 403. Unverified rate 2 / 4: one true bad citation (T0008).
  Next batch (terra medium, CFD-tradable filter in the queries) waits for the Codex reset.

## 2026-11-12: I-51 diversified daily trend portfolio screen: KILLED (the user: "1")

- Opus 5.5 (this session, no dispatch): `research/screens/2026-11-12_i51_trend_portfolio_screen.py`, one
  volatility-scaled portfolio over 35 cached symbols (28-33 active), 12-month sign, monthly rebalance,
  cost table spread + swap (credits off), development only: 67 months 2016-02 to 2021-08. Kills from the
  card (review D3), fixed before the run.
- Net -33.5 bp per month, Sharpe -1.03 (halves -1.01 / -1.03): **killed** (Sharpe < 0.4, net <= 0).
  Diagnostic after the verdict (not a gate): gross Sharpe -0.13; totals gross -290 bp, swap -1924 bp,
  spread -32 bp. Trend had no edge here before costs, and FTMO swaps alone would sink a real one.
- Trend family: second falsification after strategy 4 (S04), family closed.

## 2026-11-12: I-67 month-end rebalancing screen: KILLED (the user: "your choice")

- Opus 5.5 (this session, no dispatch): `research/screens/2026-11-12_i67_month_end_screen.py`, US500
  development D1 closes (last M1 close <= 16:00 NY), 2015-01 to 2021-08. Signed T-3..T-1 return opposite
  to the sign of T-8..T-4; kill criteria from the card, fixed before the run.
- 80 months (37 long, 43 short): signed gross +19.9 bp (t 0.95); halves split at the 2017-09-05 T+2 shift
  +38.1 / +7.8 bp; net +14.2 bp. **Killed on t < 2** (mean and halves pass). Underpowered at 80 months.
- Assumption (Opus): the F4 turn-of-month family already had two falsifications (F4, F4M); this third look
  was taken because review D2 (accepted by the user 2026-11-11) asked for exactly this cheap test. The
  family is now closed: no further turn-of-month variants, no rescue on more data without the user's go.

## 2026-11-12: pre-build screen of lead-lag L15-L18: all four stay cards (the user: "your pick")

- Opus 5.5 (this session, no dispatch): `research/screens/2026-11-12_leadlag_screen.py`, development data
  only (2015-01-02 / ETH 2018-01-10 to 2021-09-13), the primary cell of each spec, timed hold without the
  stop, one position at a time, cost table round trip + swap. Rule fixed before the run: survive only if
  mean net bp > 0 and the signal beats its direction-weighted all-days control (signal dates removed).
- L15 oil -> USDCAD: 387 trades, gross +1.20 bp vs cost 1.67 bp, net -0.47 bp (t -0.18), vs control +1.21.
  L16 USD breadth -> USDCAD: 656, gross -0.94, net -2.58 (t -1.40), vs control -0.93.
  L17 gold -> silver: 515, gross +3.68 vs cost 15.46, net -11.77 (t -2.68), vs control +3.69.
  L18 BTC -> ETH: 624, gross -19.59 vs cost 13.10, net -32.68 (t -2.28), vs control -18.49.
- None built (4 looks counted in the ledger). With strategy 14 falsified, nothing in the lead-lag family
  is left to build; the family stays at 1 falsification (screens are not builds).

## 2026-11-12: strategy 14 `us_close_de_open` development run: FALSIFIED (Continue.; the user's go)

- Opus 5.5 (this session, no dispatch): both grids `--dev-only --workers 4` (GER40 16 cells,
  `results/research/us_close_de_open_f2c04bdb`; UK100 16 cells, `us_close_de_open_uk_a79a37c4`), 2015-01-02
  to 2021-09-13, then `tools/us_close_de_open_gates.py` (integrity on). Test not spent.
- **Primary (0.10 %, 0.5 ATR, exit 09:30):** 598 trades, gross +8.8 R, net -4.6 R (doubled -16.6), mean
  -0.008 R, bootstrap lower 2.5 % -0.041, p 0.66; halves -8.1 / +3.5; vs the date-filtered control +0.019 R
  (lower -0.020); long -8.5 R / short +3.9 R; DST-mismatch weeks 47 trades -4.7 R. UK100 primary 768 trades,
  net -39.1 R (gross +9.8). Verdict falsified; all 8 S cells falsified (best: 0.20 / 0.5 / 10:00, 308 trades,
  net +12.2, bootstrap lower -0.027, effect lower -0.009, first half -3.2). Controls C: all negative net.
  One GER40 integrity failure (2020-04-14), 46 days with a missing US500 signal candle.
- Cost wall again: gross +0.015 R per trade against about 0.022 R cost per trade.
- **Pipeline controls** (review tip 2, first run for this tool; scratch script on the primary's control
  trades, 200 draws each): negative (fake signal cells from control days) 0 % pass of all falsification
  checks; positive (planted +0.049 R = MDE at 80 % power) effect gate 69.5 %, mean gate 94.5 %, bootstrap
  vs zero 30 % (controls are net negative after costs). Tool behaves as designed.
- Family `lead_lag`: falsification 1 of 2 (closed after two).

## 2026-11-11: strategy 14 gates tool (Continue.Code; the user's go on U5-U6)

- Codex `gpt-6.1-terra` medium, write, worktree `s14_gates` (brief `briefs/us-close-de-open-gates.md`):
  `tools/us_close_de_open_gates.py` + 8 tests. Opus: review, BOM fix, runner saves reference cache dirs
  in settings.json (the tool reads US500 through them). No run.

## 2026-11-11: strategy 14 `us_close_de_open` built (Continue.Code; the user's go on U1-U4)

- Codex `gpt-6.1-sol` medium, write, lane `us_close_de_open` (brief `briefs/us-close-de-open-build.md`):
  strategy, 67 tests, GER40 + UK100 grids. Opus: review (spec vs code, lookahead), registry entry,
  merge. No backtest or research run; gates tool next (U4).

## 2026-11-11: multi-symbol step 1b (Continue.Code; the user's go on Opus's picks)

- Opus 5.5 (this session, no dispatch; small change): strategy-declared references, research pieces
  cut at required-reference gaps, manifest with reference files, blocked-decision counts; test-first
  (6 new tests). No research run.

## 2026-11-11: review follow-up (Fable review + framework; the user's go on Opus's picks)

- Opus (this session): verified review A-C (verdicts in the review file), B2 / B3 / B5 / B9 / B1 / B8,
  ledger backfill, known families, docs. Codex `gpt-6.1-terra` medium: `tools/harvest.py` (290 s;
  Opus fixed the fuzzy quote check, redirects, a BOM).
- **Harvest pilot stopped after 3 attempts:** the known-answer canary T0001 (Breedon & Ranaldo, local
  hours) came back empty at terra low (24 s), medium (27 s) and medium write mode (15 s); the nonsense
  canary T0002 was correctly empty. Cause not proven: the canary's own family (`fx_hours`, closed) is
  in the prompt's skip list, and 15-27 s is too short for any search, so this dispatch path likely
  has no web access. T0003 / T0004 not run. Next: a one-line web-access probe, a canary outside the
  skip list. No ideas recorded from the pilot.

## 2026-11-10: continuous Continue.Research Test=auto (the user)

- Answers: continuous until `Stop.`; research generally (any source on the internet, ideas need not be
  scientifically backed; find new ones online when the backlog is empty); pre-sample check before the
  MT5 test whenever older data exists; routing as before (Codex for screens, runs, code and some web
  research; free models for literature); Telegram for a promising strategy or > 5 min waiting.
- **Idea harvests (Codex web research, medium):** 24 ideas (`knowledge/research/reports/2026-11-10_idea_harvest_*.md`);
  multi-leg / basket ideas not runnable, RSI2-like pullbacks already falsified, crypto funding too short.
- **Strategy 12 `energy_report`** (EIA oil report, follow / fade; Codex sol build + terra integration, sol
  review: 3 defects fixed): falsified on development, all 8 report cells negative (primary -7.5 R, 322 trades).
- **Strategy 13 `daily_reversal`** (Connors E8 / capitulation, 6 indices; US30 dropped before any result):
  falsified, primary E8 2R -35.0 R (335 trades); CAP +5 to +7 R on only 32 trades (min 80).
- Next: Kaufman trend following on BTCUSD / ETHUSD (never run on crypto; FTMO crypto swap -30 %/year).
- **C1 crypto trend following (strategy 4, BTCUSD / ETHUSD):** two data fixes on the way (runner D1 UTC,
  crypto Saturday closures; segments 102 -> 18); primary 23 trades < 40: inconclusive; all 16 cells positive,
  momentum-20 lead parked (HANDOFF › Open 13).
- **C3 crypto intraday momentum: screened out on costs.** Shen, Urquhart, Wang (Reading, 2021) report 2.8 bp
  gross per trade (break-even about 3 bp) vs FTMO crypto commission 6.5 bp per round trip; Wen et al. 2022
  tables not accessible. Not built.
- **Idea harvest round 2** (Codex web, 12 ideas). **Hypothesis 15 Turtle Soup** (failed 20-day extreme,
  daily, 7 symbols; setup TS of strategy 13, Codex sol): falsified, primary 38 trades -9.2 R.
- **C2 crypto momentum one-time test (the user's go):** BTCUSD momentum 20 / stop 2, test 2021-09-14..2026-11-08:
  215 trades +5.0 R, doubled costs incl. swap -18.9 R, halves +12.7 / -7.8: not confirmed.
- **Codex at its weekly limit (14:54):** heavy work waits for the reset (the user); Sonnet only for small work.
  Done meanwhile: strategy 14 spec (Sonnet, small), four lead-lag specs (Gemini, free), multi-symbol design.
- **Pre-sample data (the user's go "download the data"):** histdata XAUUSD, XAGUSD (from 2009), USDCAD (2008),
  WTIUSD / BCOUSD = USOIL / UKOIL (from 2010) to 2014: 29 files, imported into `data/cache/histdata_presample/`
  (effective starts: gold 2009-03, silver 2009-05, oil 2010-11). Per-year clock check still to do (Codex).
- **Free research while Codex is out (Gemini Flash medium):** pair / basket draft specs (WTI-Brent, gold-silver
  ratio, FX relative strength); skeptic review of the five lead-lag specs (priors: S14 15-20 %, oil-CAD 5-8 %,
  USD breadth 4-6 %, gold-silver < 2 %, BTC-ETH < 1 %), all open points decided by Opus; literature for S14:
  3-7 bp gross per trade expected vs 2-6 bp GER40 costs (cost wall risk).
- **2026-11-11:** Codex reset; multi-symbol step 1a built (Codex sol, 1,417 s; golden identical); pre-sample
  clock check (Codex terra): excluded XAUUSD 2009, XAGUSD 2009 + 2011, USDCAD 2009, USOIL + UKOIL 2010.
  `End.` on the user's word (full suite: 5733 passed, 14 skipped, 4 xfailed, 45 warnings; ruff clean); the rest is in HANDOFF › Next step.
- Test=auto: a candidate passing every pre-registered development gate (and its pre-sample check)
  gets its one-time MT5 test in this run, once, frozen.

## 2026-11-09: continuous Continue.Research (routing back to Codex first, the user)

- **Hypothesis 11 Gotobi USDJPY (evening):** idea scan Gemini Flash low (free; month-end fix, OPEX,
  gap fade, quarter-end already covered or built; Gotobi new); Opus opened arXiv:2301.13204 via a
  fetch agent (Gemini's NBER Gotobi citation is a Tokyo-fixing paper without Gotobi results). JP
  holiday calendar from the Cabinet Office CSV. Build: Codex gpt-6.1-terra medium (`day_filter =
  "gotobi"`); review: gpt-6.1-sol medium, read-only, no defects. Dev run: G1 passes gates 1-6
  (USDJPY +16.5 R, p 0.0035), fails gate 7 on rollover-hour gaps (23 trades) -> HANDOFF › Open 10;
  G2 falsified. Gap listing: a scratchpad script calling `integrity_failures` per trade.
- **Index screen (the user's go "Yes, download indices"):** histdata SPXUSD, NSXUSD, GRXEUR, UKXGBP,
  JPXJPY 2010-2014 downloaded (25 files, `data/raw/histdata_presample/`); two-stage screen pre-registered
  in `docs/archive/briefs/index-clock-screen.md` (660 cells), run by Codex.
  **Result: 0 survivors of 660** on 2010-11..2014 (index files start November 2010; no clock year
  excluded); nothing confirmed. Report `knowledge/research/reports/2026-11-09_index_clock_screen.md`.
- **Calendar x clock screen (Codex terra, pre-registered `d1334e1`, definitions fixed before the run):**
  792 cells on 2008-2014, **0 survivors** (largest |t| about 3, the size expected from noise across 792
  cells; threshold 4.0). Nothing goes to confirmation; 2015-2021 and the test period stay unused.
  Report `knowledge/research/reports/2026-11-09_calendar_clock_screen.md`.
- **Idea scan 4 (Gemini low):** nothing buildable (Breedon-Ranaldo = F1; dividend repatriation needs a
  dividend calendar; Toshin / life-insurer / holiday-asymmetry / DST unsourced). Next: pre-registered
  two-stage calendar x clock screen (`docs/archive/briefs/calendar-clock-screen.md`, 792 cells, discover 2008-2014,
  confirm 2015-2021, test period unspent), run by Codex.
- **Gotobi one-time test (the user's go):** frozen one-cell grid `timed_hold_gotobi_test.toml`
  (dev reproduced +32.0 R); test 2021-09-14..2026-11-08 USDJPY +6.6 R, criterion 2 (bootstrap) fails:
  not confirmed, no retest. H12 falsified on 2008-2014; Gotobi pre-sample +30.9 R (gate 7 fail).
- **Idea scans 2-3 (Gemini Flash low, free):** fixings / flows: quarter-end USD funding is a
  forward-basis effect (not spot), gold / ECB fixes dead per the scan; the W pattern of Krohn, Mueller,
  Whelan (JF 2024, confirmed via the Bank of Canada summary) -> Codex screen -> hypothesis 12. Scheduled
  flows: LETF end-of-day = the falsified F2L family; index rebalance days about 28 events (too few);
  Nikkei SQ and post-NFP drift unsourced (bp claims of 25-55 look inflated): screened out.
- **Routing note (the user, 2026-11-09 evening):** Claude tokens run out as fast as Codex and Codex
  can be reset, so more work goes to Codex (screens, runs, diagnostics, not only code).
- **User decisions:** pre-sample check of F1a (yes), gap-tolerant integrity gate + NYSE short-day
  skip (ok), live-spread raises (yes); see HANDOFF › Accepted.
- **Tooling (Codex gpt-6.1-terra, medium):** `tools/time_of_day_profile.py` (screen hourly drift
  vs costs, dev only); research runner `--cache-dir`; histdata clock rule US DST through 2018
  (Opus measured the 2008-2014 clock on NFP / FOMC release spikes: one hour off in every
  US-summer / Europe-winter week under the old rule).
- **Screen (Opus, profile tool):** hourly profiles of six USD pairs (London clock, 2015-2021): the
  USD strengthens in the European morning in every pair, but a 07:00-13:00 hold sums to only
  1.2-1.9 bp per day on USDJPY / AUDUSD / NZDUSD / USDCAD / USDCHF vs 1.0-1.8 bp cost; only EURUSD
  (-2.9 bp vs 0.8 bp) clears. No new family built (screen, not a hypothesis).
- **F1a pre-sample 2008-2014** (pre-registered `27b3fcb`): EURUSD +40.4 R net, +0.023 R per trade,
  doubled costs +10.8, both halves positive, bootstrap lower bound -0.009 -> **fails criterion 3**;
  5 of 7 years positive. Spec › F1a pre-sample check.
- **Live-spread raises applied** (the user's yes; Codex gpt-6.1-sol medium): fixed spreads raised
  for 17 symbols (e.g. GBPUSD 0.3 -> 0.59 pip, GBPJPY 1.0 -> 2.3, NAS100 1.0 -> 1.9, UK100 1.45 ->
  2.6, GER40 1.53 -> 2.3, XAUUSD 0.25 -> 0.41, US500 0.5 -> 0.61), BTCUSD slippage 0.5 -> 2.5;
  nothing lowered; spread table untouched. Golden lists regenerated (one count 2,511 -> 2,516);
  full suite 5,289 passed. Earlier research results used the old (lower) costs: index and GBP
  results above are, if anything, too kind.
- **Strategy 11 `h1_shock`** (candidate INTRADAY_H1_SHOCK_RESPONSE, unblocked by the NYSE calendar
  and Opus's session / data-validity decisions): spec draft + build by Codex sol (it stopped three
  times on undefined data rules; each decided by Opus and recorded); read-only sol review (no
  material finding); gates tool by Codex terra. Development run: all 18 cells net negative
  (-0.001 to -0.022 R per trade), primary response q indistinguishable from zero. Falsified.
- **Gap scan** (Gemini Flash low, free; `results/ai/20261109-160127_gemini_gap-scan.md`, leads
  only): intraday time-series momentum (Li, Sakkas & Urquhart 2022) = the F2 family already tested;
  pre-release macro drift (Kurov et al., JFQA 2019) runs with the coming surprise, not tradable
  without it; VPIN / order-flow rules need volume data we lack; one USDJPY session rule attributed to
  Frömmel & Lampaert looks unreliable (not opened). Nothing new worth a build: the same-day idea space
  is exhausted at our costs; the next direction waits on HANDOFF › Open 8 (multi-day holds).
- **Multi-day scope** (the user: "yes, but regard the fees"). Free-model scan (Gemini low; leads
  only). **Hypothesis 9 F4M** (turn of the month close to close, pre-registered `915b43c`, multi-day
  support by Codex sol `cb954f8`): falsified, TOM is no better than a mid-month control week in
  US500 / NAS100 / UK100 / GER40 / JP225 (spec). Found: the engine's swap is not price-scaled, so it
  overstates 2015-2021 index financing about 3x (HANDOFF › Open 9).
- **Hypothesis 10 (I-03 RSI(2) index mean reversion,** Kaufman; RSI signal by Codex sol, flat-RSI fix
  by Codex terra): falsified, primary US500 -3.9 R net over 309 trades, no cell advances. Overnight
  drift and FX carry screened out on fees (spec). Multi-day idea space with published support at our
  fees is now thin; next candidates need new research.
- Models: Codex terra x3 (all ok, no violations; one false-positive risk avoided after Opus learned
  not to commit during a dispatch); Opus coordination, clock check, screen, review. No Sonnet.

## 2026-11-09: Continue.Research run 1 (11:43 to 13:59 CET, the user)

- Limit 13:59 CET; the user asked for quality research with Sonnet sub-agents (more than usual).
- Plan: (1) cost-in-R table per symbol and stop size; (2) triage of the 18 M15 candidates against
  it; (3) literature on effects with published, post-publication evidence whose gross edge per
  trade can exceed our costs (macro-announcement days, FX time-of-day, index intraday momentum,
  calendar effects); (4) best idea -> spec with pre-registered gates -> build -> `--dev-only` run.
- **Literature (Sonnet sub-agents, sources marked opened / abstract):** reports in
  `knowledge/research/reports/2026-11-09_*.md` (macro announcements, FX / gold time of day, index
  intraday momentum, calendar effects, commodity / EU / Asia intraday, cost-in-R table, M15
  triage). Kept: Breedon & Ranaldo FX sessions, Baltussen et al. last-30-minute momentum,
  Lucca & Moench pre-FOMC (falsification only), turn of month. Dead: pre-holiday, day of week,
  macro-day long, pre-ECB, gold sessions, overnight drift. M15 candidates: none worth a build.
- **Cost table:** 0.2 R per trade at a 1-ATR M15 stop, 0.02-0.04 R at a 0.5 daily-ATR stop
  (indices, majors). Only session-sized holds leave room for a published few-bp effect.
- **Strategy 10 `timed_hold`** (`docs/strategy-timed-hold.md`): fixed-time hold, ATR stop, day
  filters (FOMC, turn of month, pre-holiday) from published calendars, `with_day` direction.
  Pre-registered in `6e4569c` (families, gates) and `4b8819a` (F2 European legs) before any run;
  skeptic review by a sub-agent applied before the run (disjoint baselines, F1 joint rule,
  p-values vs 0.01). Built by a Sonnet sub-agent (51 tests), gates tool by a second one
  (`tools/timed_hold_gates.py`), both checked by Opus (code read, targeted suite 916 passed).
- **Results (12 cells, 5 hypotheses, development only, test period untouched):** no family
  advances. F1a EURUSD short 07:00-13:00 London +72.5 R net / 1,723 trades (+0.042 R, p 0.008,
  passes costs x2, halves, bootstrap, best dates) but GBPUSD -25.8 net and F1b (USD-hours long)
  fails, so F1 is not supported by its pre-registered joint rule. F2 last-30-minute momentum:
  positive gross in all 5 indices (+10 to +36 R) but net negative (costs 0.04-0.05 R vs about
  +0.01-0.03 R gross per trade). F3 FOMC mornings -0.27 R per trade vs other days (falsified,
  opposite of the 1994-2011 drift). F4 turn of month: no effect. Table: spec › Results.
- **Hypothesis 6 F2L** (pre-registered `fdb450c` after the F2 results, counted as new): F2 only on
  days with |move| >= 0.5 daily ATR. Falsified: US500 -0.035 R per trade net, gross +0.008 R;
  NAS100 / UK100 negative, GER40 +6.6 net (fails costs x2). 6 hypotheses, 15 cells in total.
- **Hypothesis 7 F1X** (pre-registered `e2d8744`): short EURJPY / EURAUD / GBPJPY / GBPAUD in
  European hours. Gross positive on all four (+25 to +42 R), net negative on all four (costs
  0.04-0.06 R vs +0.02 R gross per trade). 7 hypotheses, 16 cells in total. The mechanism shows
  up gross everywhere; it clears costs only on EURUSD.
- **Follow-ups (spec › Run 1 follow-ups):** a code review found the FX daily ATR about 8 % too
  small (Fridays irregular, Sunday stubs counted); fixed (`atr_skip_weekend`, tolerance 180) and
  the FX families rerun: no verdict changes (F1a EURUSD +68.9 R, p 0.0067). EURUSD placebo
  profile (6-hour long holds from every London hour): a smooth Breedon-Ranaldo shape, 07:00 the
  extreme. F1a dissection: 6 of 7 years positive but faded in 2020-21, top 1 % of trades = 58 %
  of net. More literature: EURUSD-specific effects (nothing better than Breedon-Ranaldo), crypto
  intraday (nothing that beats costs; leads: fade after large 1-4 h moves, first-to-last
  30-minute momentum as a filter), commodity / EU / Asia intraday; synthesis
  `knowledge/topics/cost-wall.md`; pre-sample 2008-2014 data plan
  (`knowledge/research/reports/2026-11-09_presample_2008_2014_plan.md`, needs the user's go).
- **Live spreads** (the user's request, Sonnet sub-agent): `results/fill_report_2026-11-09/`
  (7,019 fills of runs 3+4, 23 symbols, about 4.6 days): FX medians match the model; means 1.4-2x
  from Asia / rollover bars (NY hour 18 about 5x). Under-charged spread: GBPJPY 2.25x, GBPUSD
  1.97x, NAS100 1.95x, UK100 1.77x, GER40 1.52x; slippage under-charged only on BTCUSD (5x).
  Proposal only, `data/spreads/proposal_live_2026-11-09.json` (not wired in). For this run: the
  F1a EURUSD lead is not flattered by the cost model (EURUSD spread median 0, slippage 0.81x of
  the model); UK100 / NAS100 / GER40 were under-charged, so F2's net results are if anything
  too kind.
- **Data finding:** US500 histdata 2015-2021 omits many quiet minutes (2017 worst); the strict
  integrity gate over-flags; holiday / early-close days exit after the rollover (spec › Results).
- **Process:** the runner's matched monkeys took 30+ minutes per family; the grids now switch
  monkeys / sensitivity / entry screen off (diagnostics only). US30 dropped (cache from 2019-02).
- Models: Opus (coordination, spec, review, gates edits); Sonnet sub-agents x15 (literature x6,
  cost table, triage, calendars, implementation, gates tool, paper check, skeptic review, data
  gaps, live-spread measurement). No Codex / Gemini.

## 2026-11-09: research back in this team

- The user folded the research department back into V2 and asked for everything not needed to be
  archived. Department + shared interface in `../archive/research-department-2026-11/` (its last
  session state, `ACTIVE` since 2026-11-06, frozen as is); 21 research records, 75 reports and the
  registries copied to `knowledge/research/`; 20 unbuilt drafts to `research/candidates/`
  (R014 v0.1.0 dropped as superseded). Intake tool removed (`../archive/v2-intake-tool/`).
- Unanswered at the merge (now moot): the 17 R007-R024 compatibility preflights, the fast-lane
  bulk question, the reviewability proposal. The fast-lane idea (one shared harness for the M15
  batches) stays worth considering when the first candidate is built.
- `Continue.Research` rewritten (skill `continue-research`): candidate or researched idea ->
  spec with pre-registered gates -> build -> development run -> gates -> record. Opus inline,
  no dispatch.

## 2026-11-06: R014 development run and gates

- `results/research/alternating_path_1ffe705d` (2015-01-02..2021-09-13, 6 FX pairs, `--dev-only`,
  test period untouched). Net R: FOLLOW/30 -3,925 (17,673 trades), FOLLOW/60 -3,866 (16,626),
  FADE/30 -2,882 (15,160), FADE/60 -2,585 (14,042). Gross: FOLLOW -162 / -308, FADE +317 / +389
  (about +0.025 R per trade, costs about 0.2 R per trade at a 1-ATR M15 stop).
- Gates (`tools/alternating_path_gates.py`, `gates.json`): both modes fail every gate except the
  300-trade minimum; no symbol positive in any half; bootstrap lower bounds about -1.7 to -2.5 R
  per day; 111-170 trades per cell touch a missing / invalid M1 candle.
- Envelope `Shared_Interface/feedback/results/M15_ALTERNATING_PATH_BATCH__v0.2.0__DEVELOPMENT__1.json`
  (status COMPLETED). Gates tool by Opus inline (no dispatch); no one-time test.
- **Rejected by the user 2026-11-06**: moved to `queue/rejected/`; Research told the decision and
  the gate readings (`ASSUMPTION_MADE`, see `docs/strategy-alternating-path.md` › Gates).

## 2026-11-05: M15_ALTERNATING_PATH_BATCH v0.2.0 (R014) implemented as strategy 9

- Validated and claimed (sha256 `d09d44b9...`), status IMPLEMENTING; five `ASSUMPTION_MADE`
  points sent (M15 buckets, ATR seed, data-integrity handling, R-only sizing, gates after the
  run); spec `docs/strategy-alternating-path.md` › Assumptions. Brief
  `docs/archive/briefs/r014-alternating-path.md`.
- Codex gpt-6.1-sol medium, 1 call: config, strategy, 75 tests, spec, 4-cell grid. Opus: runner
  config union, panel (fixed fields hidden, widget limit), tool symbol tables, golden list
  (2,511 trades, 2023). Full suite 5,225 passed; golden 9/9 identical.
- Not done: the development run of the 4 cells and the submission's gates (UTC halves,
  doubled cost components, five-best-date removal, block bootstrap, M1 data-integrity count);
  no envelope yet. Research's 17 R007-R023 preflights and the fast-lane bulk question are
  unanswered.

## 2026-11-02: finalization audit and V2.8 R1

Opus (Claude Code, high effort) did the read-only audit (`docs/archive/review/finalization-audit-2026-11-02.md`)
and R1 itself (`live/` is Opus-only; 3 tests, about 25 lines). T1 (a test fixture) by Opus.
U1 by Codex gpt-6.1-terra medium (`docs/archive/briefs/v28-u1-trade-pager.md`): first call hit the usage
limit (reset 21:36, the user chose to wait), second call done in ~5 min, inside the brief's
files, tests green on Opus's run; no fix round.

Night run 2026-11-02/03 (V2.8 step 3): V2.4b, 12.5, V2.6l, V2.4e each by Codex gpt-6.1-terra
medium in one call (V2.4b first went to gpt-6.1-sol, "model at capacity" after one partial test
file, then terra per the routing's same-cost rule); Opus checked each by running the tests and
comparing with recorded numbers; one Opus fix round on 12.5 (direction check, stop tolerance).
Feedback to Research 2026-11-03: `FB_INTRADAY_H1_SHOCK_RESPONSE_20261102T232536Z_ca99` (no
authoritative CFD session calendar, so the R004 integrity predicate is unsupported for all five
symbols; `robustness.r004` deferred until R004 is queued; V2.6l cell manifest available) and
`FB_UNKNOWN_20261102T232536Z_1ebf` (reviewability proposal received, review after V2.8).
2026-11-03 morning: stop inside the spread refused (the user's answer to night question 1) by
Opus inline (about 10 lines + 6 tests; routing: small edit); golden no_wick re-written (31 sells
fewer), the other 8 identical. Calendar rule 3 (1-hour shift, the user's answer to night
question 2) by Opus inline (about 30 lines + 9 tests; routing: small edit).

## 2026-10-28: first research pilot FX_LONDON_FIX_REV v1.0.0 (V2.6i i8)

Claimed 13:25 UTC, strategy 8 `london_fix` (Codex gpt-6.1-sol medium, Opus review), 9 variants
on development data 2015 - 2021-09-13, six USD pairs, 10,397 trades each. **All 9 negative**
(best v0007 stop 5 ATR / 180 min: -1,043 R, -0.10 R per trade). Pooled gross +181 R, 4 of 6
pairs with the predicted gross sign: the postfix drift exists, costs (~1,220 R) eat it, as
the source paper says for liquidity demanders. Criteria (`results/intake/<stem>/criteria.json`):
1 met, 2 not met, 3-5 met, 6 not run (monkeys skipped by the user: > 5.5 h CPU, cannot change
the outcome). Result envelope `FX_LONDON_FIX_REV__v1.0.0__DEVELOPMENT__1` sent; the user decides
pass / fail; no holdout. **Rejected by the user 2026-10-29** (moved to `queue/rejected/`, bytes unchanged, REJECTED message `FB_FX_LONDON_FIX_REV_20261029T170636Z_097b`). Research confirmed 3 assumptions within minutes; the swap / 23:55
assumption is open. Codex models: gpt-6.1-sol (pilot), gpt-6.1-sol (V2.4c checks; terra would
have done).

## Model usage, night 2026-10-27/28

| Tool / model | Effort | Calls | Minutes | Used for | Worth it? |
|---|---|---|---|---|---|
| Codex gpt-6.1-sol | medium | 4 | ~40 | V2.6i steps 1-3 (intake validator / claim, submission metadata + test gate, envelopes + end-to-end) and a ponytail cleanup | yes; all four green on the first try, no stop; Opus review found 4 real issues (results-folder leak in ordering, crash-remnant duplicate, schema-message crash, test-period evidence in development envelopes) |
| Opus (this app) | medium | - | - | news calendar wiring, FTMO restricted-news scope, deals export, fill analysis, reviews | small glue cheaper than a brief; Claude 4.6 (agy) quota still empty |

## 2026-10-27: research department split

From now on this log records only the backtester side (experiments, intake, model usage).
Research findings, sources and hypotheses live in `../Research_Department/knowledge_base/`.
Reviewed their contract 0.1.0 (`docs/archive/review/research-interface-review-2026-10-27.md`, Opus
medium, no code changed); both pilot drafts are not runnable in V2 today (stopless /
notional, adjusted ETF data). Intake = ROADMAP V2.6i.

## Model usage, V2.1-V2.4 (2026-10-22 / 23)

| Tool / model | Effort | Calls | Minutes | Used for | Worth it? |
|---|---|---|---|---|---|
| Codex gpt-6.1-sol | high | 16 | 165 | module reviews (8), A1, B-risk, B-engine, B-strategy, speed 1-2 | yes: found 84 real issues with evidence; implementations needed few corrections |
| Codex gpt-6.1-sol | medium | 9 | 44 | inventory, dedupe, golden tool, A2/A3 finish, A4/A5 | yes for well-specified batches |
| Gemini 3.8 Flash | high | 4 | 25 | two reviews (good), one write task (quota ran out half-way) | reviews yes; bulk writing burns the weekly quota |
| Claude Opus 4.6 (agy) | high | 3 | 4 | one review | the 4 subagents it started emptied the weekly quota |
| Claude subagents (this app) | Opus high / Sonnet medium | 2 | - | live-bot fixes (19 findings, 45 tests), UI proposal draft | yes; live code is Opus-only |

| Codex gpt-6.1-sol | medium | 3 | 50 | grid merge 1-3 (2026-10-23) | yes: exact reproduction; Opus fixed a slow shock-day read (31 s -> 2 s), a misleading haircut on losses, legacy test fixtures |
| Claude subagent (this app) | Sonnet | 1 | 4 | merge of the Pardo / Masters / Aronson notes into knowledge/topics | yes for knowledge merges |
| Opus (this app) | medium | - | - | V2.4a trades overlay for every strategy, backtest audit, book-claim check | small UI change cheaper than a brief |
| Codex gpt-6.1-sol | medium / high | 11 | ~330 | V2.4d 1-5, V2.4c T-10 / T-14 / T-03 (2026-10-23 evening); 5 short stops with a rule question, all good questions | yes; hit the limit at 21:10 after ~5 h of work since the morning reset, the last task (T-03) was already complete |

| Codex gpt-6.1-sol | medium | 3 | 23 | V2.6a job queue: read-only pass by mistake (found 6 shared-file collisions), build, fix round (2026-10-26) | yes; Sonnet subagent review found 5 real defects (one Windows replace race, reproduced by Opus); Haiku subagent pinned 14 tests for the new defaults |

| Codex gpt-6.1-sol | medium | 2 | 43 | V2.6b data fixes + server-clock revision (2026-10-26) | yes; Sonnet subagents: wrong-instrument table, sparse-day fix; the continuity check found DXY = Dow Jones and EU50 = IBEX in histdata; Opus caught the holiday-day drop via the golden check |

| Codex gpt-6.1-sol | medium | 2 | 21 | V2.7 portfolio page + fix round (2026-10-26) | yes; Sonnet subagents built V2.6 step 3 while Codex was at its limit (18:14-21:14) and reviewed V2.7 (no blocking defect) |

| Codex gpt-6.1-sol | medium | 9 | ~120 | night 2026-10-26/27: step 5 (+2 fix rounds, 4.3 items), V2.4e news (2 rounds), full check review + fixes | yes; the full-check review found 6 real defects (one review no-peek leak); its 'violation' flag came from Opus editing files during the read-only review, not from Codex. Codex failed twice on the chart stats strip (wrong brief by Opus), Opus fixed it |

Limits seen: Codex hit its limit twice (about 20:50 and 04:25; reset after ~4.5 h);
Antigravity (Gemini + Claude 4.6, one shared weekly quota) is empty until about 2026-10-29.

## Strategy profiles, development period, spec defaults (2026-10-25)

`python -m backtester.tools.strategy_profile --strategy <name>` for all 7 strategies (current
defaults incl. TP penetration 0.5 + ask, intrabar M1), results in `results/profiles/`. Best cells
by **detrended** R per trade (>= 30 trades); "lower90" = BCa 90 % lower bound. These are
descriptive cells picked after the fact, **not** a significance test (many cells were looked at).

| Strategy | Trades | Net R | Best cells (detrended R/trade, lower90) |
|---|---|---|---|
| 1 Session zones | 20,167 | -4,556 | London session -0.12 (-0.14); everything negative |
| 2 NY index sweep | 1,381 | -328 | sideways / high vol -0.08 (-0.17); all negative |
| 3 No-wick | 42,448 | -11,498 | London -0.18 (-0.19); all negative |
| 4 Trend following | 1,027 | -182 | **GBPJPY +0.16 (+0.02, 200 trades, the only positive lower bound)**; sideways / low vol raw +14.9 R but detrended -0.03 |
| 5 Gap fade | 2,420 | -83 | sideways / low vol +0.05 (-0.01, 406 trades); trend_up / low +0.02 |
| 6 Opening range | 3,318 | -199 | trend_up / low -0.01; sideways / high -0.01: near zero, no edge |
| 7 Gap momentum | 975 | -12 | sideways / high vol +0.03 (-0.01, 285 trades) |

Reading (Opus): no strategy has a robust edge in any condition. Candidates worth a researched
follow-up, not a conclusion: strategy 4 on GBPJPY (the only positive lower bound; check it as a
pre-registered hypothesis on the MT5 test period, it was found by looking at 30+ cells), and the
quiet sideways regime for the two gap strategies (5 and 7 both best there, in line with mean
reversion working in noise, Kaufman). For combining (V2.7): 4 trend-following and 5 / 7 gap
strategies prefer opposite regimes, which is the kind of pair the portfolio looks for.

## Research runs

(none yet; V2.6 starts after the regime classifier spec is accepted)
