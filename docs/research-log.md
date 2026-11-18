# Research log

Running log of the research loop (V2.6 / V2.7) and of the model / effort used per task, so a
run resumes after a restart or a usage limit. Newest first. Every AI call is also logged by
the dispatcher in `results/ai_calls.jsonl` (model, effort, seconds, status).

## 2026-11-18: T-25 stress scenarios built (the user: "Build T-25 stress test")

- `risk/stress.py` (Opus, test-first, 10 tests): shock day = the worst historical day x a multiple, placed at a random
  position (or k days in a row) in every sampled order; `stress_ftmo` reports the FTMO 2-Step summary for the baseline
  and the defaults (1.5x, 2x worst day, worst day 5 in a row). `ftmo_by_risk` now takes the day-position count from the
  order length (identical for every existing caller). Spec risk-management.md › Stress scenarios. Opt-in, no default
  changes. Not wired into the prop card / UI and not run on a stream: no FTMO stream exists now (goal 1 paused, M11).
- Full suite 6,027 passed, 14 skipped, 4 xfailed (-n 8, 7 min); ruff clean.

## 2026-11-18: T-23 tail concentration audit, Strategy 20 and I-109 (the user: "Yes, run T-23")

- Opus, local script, no model call. Flags fixed in the script docstring before the run.
- largest observation's share of sum r^4 / mean without the 5 largest gains / without the 5 largest losses:
  Strategy 20 development (186 weeks) 0.45 (one week +3,254 bp: CONCENTRATED) / +84 bp (t 2.32) / +179 (t 4.14);
  Strategy 20 test (147 weeks) 0.24 / +103 (t 2.95) / +179 (t 4.75); I-109 development (380 months) 0.16 / +15.1 (t 3.80)
  / +21.3 (t 5.27); I-109 test (61 months) 0.20 / +7.8 (t 0.80) / +37.3 (t 3.33). No stream FRAGILE (all stay > 0 without
  their 5 best periods); every largest observation is a gain (right-skewed, not short tail risk). Weak spot: I-109's test
  mean leans on a few months (2021-22); its forward log carries the weight. Strategy 20's development leans on one week,
  its test does not.

## 2026-11-18: book read: Taleb, Statistical Consequences of Fat Tails (the user: "Read fat-tails, you can use codex again")

- Model and effort: Codex gpt-6.1-terra medium, read-only, 4 parts in 2 parallel pairs (`ai_dispatch --label
  book-ft1..4`, about 3 minutes each, status ok, repo unchanged); 14,400 words of notes. Ch.13-21 skipped (off topic).
- Filed: `knowledge/books/taleb-fat-tails.md`, README row FT, `topics/testing-and-robustness.md` › Fat tails, ideas
  T-23 (tail concentration audit of every stream), T-24 (fat-tail power check), T-25 (stress Monte Carlo beyond the
  worst seen day). No trading rule for our data.

## 2026-11-18: T-21 causal check per card made a rule (the user: "Yes, make it a rule")

- Written to `docs/research-runner.md` › Causal check per card, the continue-research skill, HANDOFF, card T-21.
  New cards only; existing verdicts unchanged.

## 2026-11-18: book read: López de Prado, Causal Factor Investing (the user: "Yes, read it"; "use sonnet")

- Three free books downloaded to `X:\Daten\03_Bibliothek\Trading\Tier 4` (Regression and Other Stories, Statistical
  Consequences of Fat Tails, Causal Factor Investing); CASI's free PDF is gone, 151 Trading Strategies is retracted by
  Springer and SSRN blocks scripts.
- A Codex dispatch (terra medium, read-only) was started and stopped at once on the user's word ("use sonnet"); nothing
  ran on, repo unchanged. One Sonnet agent read the book with the updated reading brief (3,455 words of notes).
- Filed: `knowledge/books/lopezdeprado-causal-factor-investing.md`, README row CF, `topics/testing-and-robustness.md` ›
  Causal checks, ideas T-21 (causal graph and type-B check per card; method proposal for the user) and T-22
  (simulation tests for our estimators). No trading rule in the book.

## 2026-11-18: no paid futures data; book list for the user (the user: "too risky ... make a small text file ... with books")

- Databento dropped for now (real card needed, could exceed the free credit; the user may revisit). HANDOFF updated.
- Book list `knowledge/books-wanted.md` (72 books in 4 tiers, plus free primary sources), copied to the user's Desktop
  as "Trading books to get.txt" (the user's permission). Titles and years checked by one Sonnet web subagent (partly
  from memory; unconfirmed items marked). Books go to `X:\Daten\03_Bibliothek\Trading`; read per `knowledge/README.md`
  › Adding a new book when the user says they are in.

## 2026-11-18: futures data-set scout started (the user: "Futures data hunt"; M12)

- One Sonnet web subagent (read-only): free non-price futures data (COT variants, CIT / index investment, volume and
  open interest, inventories, report calendars, index roll schedules, ETF futures holdings) and free per-contract
  daily futures prices; plus published effect sizes. Opus then applies M4 (c and pass chance) before any download.
- Result (`knowledge/reviews/2026-11-18-futures-data-scout.md`): the one new usable set is CFTC COT (free, 1986+,
  weekly). No free per-contract futures prices (Yahoo serves no expired contracts, tested by Opus; CME history paid).
  M4 before any data: I-118 hedging-pressure premium PARKED (t ~1.4-1.7 at the halved size), I-74 hedger reversal
  re-checked on futures PARKED (needs ~45 bp per 20 days vs ~11), I-119 USO roll not a new look (inside I-115's
  window, falsified). Nothing downloaded. Free futures research is limited to continuous fronts and the energy strips.

## 2026-11-18: Strategy 20 prop firm not pursued (the user: "Not worth it")

- Rerun of `research/screens/2026-11-15_s20_prop_intraday_tranches.py` at the M10 edge (+60 bp a week; daily_hl and
  hourly_close marks, 7 tranches): 10 % per side 93 % pass in ~4 years, 15 % 85 % in ~2.5 years, 25 % 71 % in ~1.3
  years (hourly close); wick bound 15 % at 15 %. HyroTrader official pages read by a web-fetch subagent (Opus 5.5):
  daily loss on start-of-day equity incl. floating P/L, bots allowed for own strategies, terms §10.2(i) on opposing
  correlated positions may bar the long-short book. Package updated (5ee1766). Strategy 20 stays forward-only.

## 2026-11-18: Fable methods M2, M4-M12 accepted (the user: "Yes, as recommended")

- Written to `docs/research-runner.md` › Method rules; pointers in the continue-research and idea-harvest skills.
  M7 applies to new cards only; M8 changed by Opus (each card keeps its own test gate, +0.3 at the 4th and +0.5 from
  the 5th use of a test period) because the wording "t 3.0 for every one-time test" would fail I-109-sized tests.
- Ledger: I73 and I83 verdicts get the M5 note. M4's relabel of rows closed on power is not done blind (the ledger has
  8 such rows from 2026-11-15, Fable said 9 crypto rows); each gets c and a pass chance when its family comes up.
- HANDOFF Open 3 / 4 shortened (K = 10 pause is M11, test-period counting is M8).

## 2026-11-18: I-109 venue decided: CME Micro 10-Year Yield futures, small (the user: "Micro futures, small")

- Options shown: ZN, micro 10-year yield futures, IEF (or a UCITS twin), paper only. The user picked micro futures
  at small size (1-3 contracts). Contract (CME / CFTC filing via web search): $1,000 x yield index = $10 per bp,
  cash-settled on the BrokerTec 3 p.m. ET fix, monthly, two months listed, last trade 3 p.m. ET on the month's last
  business day, so the window is held in the next-month contract.
- Risk per micro from DGS10 windows (yield change, close of the 4th-last to the last trade date; no excess
  adjustment; $3 cost assumed): development 1990-2021 380 months gross $23.7, net $20.7, sd $96, win 59 %, worst
  -$280, a losing year 22 % (bootstrap); test 2021-26 61 months gross $19.0, net $16.0, sd $90, win 54 %, worst
  -$140, a losing year 27 %. Not checked: liquidity / spread, the exact tick, the broker's fees.
- Open for the user (HANDOFF Open 1): broker, loss per month-end, manual orders or a broker connection.

## 2026-11-18: data-set scout result; I-116 parked, I-117 closed on power (auto)

- Scout (Sonnet subagent, ~3 min, 30 tool calls): 10 free data sets, catalogued in
  `knowledge/reviews/2026-11-18-data-scout.md` (NY Fed dealer positions / SOMA / repo, Treasury auctions / buybacks /
  DTS, SEC 13F, FINRA short interest and margin, DefiLlama stablecoins). Not found free: ETF shares-outstanding
  history, index-rebalance announcement history.
- I-116 dealer inventory (Mixon & Tuzun read in full): only a same-week effect, no next-week size -> PARKED.
  I-117 13F best ideas: halved ~2 % a year vs ~9-11 % needed -> CLOSED on power. Neither data set was downloaded.
- Opus inline; no Codex call.

## 2026-11-18: data-set scout started; optional book request (auto)

- Auto decision 54: one web subagent (Sonnet) scouts free non-price data sets (flows / positioning, 3+ years, 20+
  instruments or one liquid market), excluding everything owned. Alternative: harvest batch 19 for strategies.
  Why: batch 18 kept nothing and seven batches gave one card; Fable's M12 (search for data, not strategies) is a
  search choice, not a rule change (the rule M12 itself still waits for the user).
- Telegram "Optional: New books needed": Ilmanen *Expected Returns*, Pedersen *Efficient Inefficiency*, Burghardt
  *The Treasury Bond Basis* (the library has no book on forced flows or futures premia).

## 2026-11-18: I-109 venue diagnostic on 10-year Treasury futures; lint of the new screens (auto)

- Yahoo ZN=F continuous daily closes 2000-09 .. 2026-11 -> data/cache/yahoo_futures. ZN excess per month-end: dev
  +19.2 bp (t 4.63), test months +20.6 (t 2.36); corr 0.96-0.97 with the registered DGS10 statistic; ~0.8x its size;
  no roll-month artefact. ~$230 gross per contract per month-end. Recorded on the I-109 card; HANDOFF Open 1 has it.
- Auto decision 53: run this diagnostic. Alternative: another harvest batch or a 4th `rates_month_end` look (AGG /
  LQD). Why: HANDOFF next step 2 names it, it informs the user's open venue decision, and it spends no test.
- Ruff on the three new screens (pairwise, explicit check, unused names); outputs unchanged. Opus inline.

## 2026-11-18: harvest batch 18 (Treasury futures roll / delivery, SOMA / buybacks / repo, Fed and BIS notes, sector-ETF capping, target-date funds, leveraged bond ETFs): nothing kept (auto)

- 7 Codex `gpt-6.1-terra` `--search` calls (5 content cells, high effort; low for BLOG and the nonsense canary);
  canaries ok (carry found, nonsense empty); 5 ideas, 0 kept by the filters. Opus read the two nearest to owned data:
  target-date-fund rebalancing (Parker, Schoar & Sun; needs fund-of-fund ownership chains) and ETF rebalancing
  pressure (needs daily ETF holdings, paid): both stay untestable.
- Auto decision 52: run batch 18 (7 calls). Alternative: no batch, go straight to data work. Why: no carded idea was
  left; the auto rule asks for new sources first. Yield since batch 12: one card (I-109) in seven batches; the
  harvest is close to exhausted for our free data.

## 2026-11-18: I-115 GSCI roll front-running PASSED development, FALSIFIED at its one-time test (auto run continues)

- Source read in full (Mou 2010, CFTC study; PDF text via the zlib script). Data: EIA daily futures strips, contracts
  1-3, CL / HO / RB / NG (HTML tables, parsed with regex) -> data/cache/eia_strips (to 2021-09-13) and
  data/cache/eia_strips_test (fetched after the test rule, 421f094). EIA stopped the series in 2024-04.
- Card before data (522df40); contract mapping by delivery month (HO / RB / NG expire at month-end), checked at every
  2000-2021 expiry; power before the run (sd 175 bp, t 3 needs ~33 bp net). Development 245 months: net +26.1 bp
  (t 3.37), every gate passed; but halves +51.9 / +2.5 and the pre-index placebo NG +135 bp.
- One-time test 2021-10 .. 2024-03 (30 months, power-sized gates): net -21.5 bp (t -1.13) -> FALSIFIED. Telegram sent.
- Auto decision 50: run the one-time test although the post-publication half was ~0. Alternative: close without
  spending the test. Why: Mode=auto runs the test for a candidate that passed every development gate; the gates are
  read mechanically, and the EIA test window is unused.
- Auto decision 51: no further `index_roll` look. Alternative: grains / metals roll windows. Why: EIA strips were
  the only free curve data and end in 2024; other commodities need paid per-contract data; post-2010 edge ~0.
- Model: Opus inline. Ledger I115; HV-T0007 is now answered by I115.

## 2026-11-18: I-113 VIX futures basis KILLED; I-114 short leg FALSIFIED at its one-time check (the user: "Continue.Research Mode = auto")

- Source read in full by Opus (EFMA 2013 PDF, text pulled with a zlib script: no PDF tools installed): Simon &
  Campasano, VIX futures basis. New free data (curl): Cboe CFE VX settlements 2005-2027 (archive + per-contract files;
  archives for 2018 stop on 2018-02-23, so settlement dates come from Cboe's file names), Cboe VIX history, Yahoo
  ^GSPC -> data/cache/vix (development) and data/cache/vix_test (fetched only after the I-114 card was committed).
- I-113: card before data (1c9a4cd), power before the run (83d82c7; sd $2,673, t 3 needs ~$430). 359 trades
  2007-2021: net +$383 per contract, t 2.19 -> KILLED (t only); post-publication half +$148; paper window reproduced.
- I-114 (short leg, card 9428854 before test data): 95 trades 2021-09 .. 2026-11, net -$30 (t -0.22) -> FALSIFIED.
  Calendar fix during the test (Cboe VIX file has holiday rows from 2022): -$23 before, -$30 after. Telegram sent.
- Auto decision 47: test the short leg once on unseen data (I-114). Alternative: close with I-113. Why: it is the
  leg the mechanism (ETP roll in contango) predicts and post-publication it still had t 2.42; the lead rule allows
  one independent check, recorded as selected after the fact.
- Auto decision 48: close family `vix_basis`. Alternative: keep it open for a hedged or VIX-level-conditioned rule.
  Why: gross ~+$30 per trade in 2021-26, one kill and one falsification; any variant would be shaped on spent data.
- Auto decision 49 (start of run): pick the VIX basis (Fable row 16, scout 2 #8) as the next goal-2 look.
  Alternative: futures continuous data for an I-109 diagnostic (HANDOFF next step 2). Why: the only futures idea with
  free per-contract data, a forced counterparty and a published per-trade size far above costs; I-109's test is spent.
- Model: Opus inline; two web-fetch subagents (SSRN 403; PDF bytes unreadable to them). Ledger I113, I114.

## 2026-11-18: End. of the Mode=auto session 2026-11-16/17 (the user: "End.")

- Full suite 6,016 passed, 14 skipped, 4 xfailed (pytest -n 8, 7 min 52 s); ruff clean. No ROADMAP step closed;
  research/trials.jsonl already equal to results/trials.jsonl; no briefs to archive. HANDOFF rewritten.
- Session: one strategy passed its one-time test (I-109 Treasury month-end), I-110 not confirmed, I-100..I-108 and
  I-111 / I-112 killed or not testable; shelf logger with seven rows; monthly forward task scheduled. Auto decisions
  19-46 (this log) listed in the End report.

## 2026-11-17: I-112 international month-end bonds KILLED (the user: "Keep researching")

- New free data (public, curl): ECB AAA euro curve 10-year (2004+), Bank of England nominal spot curve (1979+, xlsx
  read with the standard library, no new dependency), MOF JGB yields (1974+) -> data/cache/intl_yields. FRED's ICE
  corporate indices are only 3 years long (no corporate card).
- Card before data (e79b3ca), power before the run (8fa7a32; se 2.7). Pooled 380 months: net +2.5 bp, t 1.00 ->
  KILLED (t, halves, breadth); euro +8.0 (t 2.08), UK +8.6 (t 2.34), Japan -4.8 (t -1.98). No rescue. Ledger I112.
  Opus inline.

## 2026-11-17: I-111 threshold rebalancing on US500 KILLED (the user: "Reopen rebalancing")

- Decision by the user: threshold rebalancing is its own family `rebalancing_threshold`; the calendar month-end
  signal stays closed (HANDOFF Accepted, known_families). Opus read NBER w33554 for the signal (eq. 2, bands 0-2.5 %).
- Card before data (496b4eb), power before the run (fbf861f; se 0.58 bp a day). US500 cash closes + FRED DGS10,
  2010-11 .. 2021-09 (inside the paper's sample): gross +1.88 bp a day, net +1.44, t 1.37 -> KILLED (t < 3.0); net
  without the 2020 crash -0.08. Ledger I111. No Telegram (a screen, not a one-time test). Opus inline.

## 2026-11-17: harvest batch 17 (forced flows: rates, Nikkei dividends, gold / oil expiry, vol targeting): nothing kept (the user: "Another idea search")

- 8 Codex `gpt-6.1-terra` `--search` calls (6 content cells, high effort; canaries ok: carry found, nonsense
  empty), 7 ideas, 0 kept by the filters. Opus read them: MBS duration -> Treasury returns (monthly; needs MBS index
  duration), dividend payment pressure abroad and gold delivery-month return (data), WTI penultimate-day pressure
  (FTMO's USOIL CFD rolls before expiry; no futures data), all parked / rejected as filed. Threshold rebalancing
  (NBER w33554, -17 bp next day on S&P futures; already ledger HV-T0037-1) is testable on US500 + FRED.
- Auto decision 46: do not test threshold rebalancing. Alternative: card it as a new family. Why: same buyer
  (fixed-weight funds) and same market (US500) as I-67 in the closed `turn_of_month` family; only the trigger differs.
  The line drawn in auto decision 44 (new market and new buyer = new family) keeps it closed. A user decision could
  reopen it.
- Harvest yield since batch 12: one card (I-109, from batch 16) in six batches. Opus inline.

## 2026-11-17: I-110 long-bond month-end NOT CONFIRMED at its one-time test (the user: "Long-bond card")

- Card before data (1bb20f0) incl. the test rule; power before the run (e77f128; se 7.4). Dev DGS20 1993-10 .. 2021-08:
  net +29.4 bp per month-end, t 4.32, every gate passed (1.57x the 10-year size, same edge per unit of risk).
  One-time test 2021-10 .. 2026-10: net +23.0, t 1.33 < 1.5, TLT +21.6 (t 1.20) -> NOT CONFIRMED (not FALSIFIED);
  no retest. The long end did not out-earn the 10-year in 2022-26 at ~1.6x the risk; I-109 stays the family's row.
  Telegram sent. Ledger I110. Opus inline.

## 2026-11-17: I-109 forward logs built (the user: "Yes, build it")

- Shelf logger: `rows_i109` + `rates_update` (FRED re-download, IEF daily into data/cache/alpaca_1d_rates_fwd);
  logs `shelf_i109` (registered DGS10 statistic) and `shelf_i109_ief` (tradable IEF window) from the 2026-11
  month-end, complete months only. Canaries reproduce dev (381, +18.4, t 4.42) and test (IEF 61, +23.2); all other
  canaries still pass; `log` appends 0 rows today. Monthly task description updated (its prompt already runs the
  shelf). Found on the way: the dev run counted the partial month 2021-09; without it t 4.39 (no change). Opus inline.

## 2026-11-17: harvest batch 16 (rates, US share flows); I-109 Treasury month-end PASSED its one-time test (the user: "New idea search")

- Harvest tool: market codes RATES and SHARE-US (test first); batch 15 rows closed in tasks.csv. Batch 16: 8 Codex
  `gpt-6.1-terra` `--search` calls (6 content cells, high for ACAD / AGG, low for BLOG; canaries ok: carry found,
  nonsense empty), 9 ideas, 0 kept by the mechanical filters. Opus read the sources: Treasury auction cycle (Lou, Yan
  & Zhang 2013) rejected on an out-of-sample study (ohlcv.io 2026-10-22: gone after 2010 once month-end days are
  removed); pre-refunding drift (Wang & Zhao 2025) parked: its sample covers our development window, and 4 events a
  year give no forward power; ETF-flow reversal and dividend pressure need data we lack. The same study's month-end
  Treasury rally became card I-109.
- I-109 (new family `rates_month_end`): card before data (585b997), power before the run (f3880db; se 4.5). Dev
  1990-2021 on FRED DGS10: net +18.4 bp per month-end, t 4.42, every gate passed. Integrity check (CMT curve switch
  risk): IEF real closes over 69 months +22.1 bp, corr 0.99. Test rule fixed before test data (29e5f32), test
  2021-10 .. 2026-10: net +24.9, t 2.14, IEF +23.2 -> PASSED (M1). Telegram sent. HANDOFF Open 8. Opus inline.
- Auto decision 44: Treasury month-end is a new family, not the closed `turn_of_month`. Alternative: count it as
  `turn_of_month` (closed, no look). Why: different market and forced buyer (Treasury index duration extension, not
  equity cash / rebalancing flows).
- Auto decision 45: run the one-time test myself with gates sized to 61 months (net > 0, t >= 1.5, doubled > 0, IEF
  > 0), not t 3.0 alone (~34 bp needed). Alternative: forward log only. Why: Mode=auto runs the test for a
  candidate that passed every development gate; the skill asks for a power-sized test rule.

## 2026-11-17: I-108 mid-cap insider purchases FALSIFIED; family share_insider closed (the user: "Insider card on mid-caps")

- Card pre-registered before data (0972ed9): I-106's rule on ranks 1,001-2,000 (universe builder now takes a rank
  range; `universe_1001_2000.csv`). Cost by the card's signal-free rule: Abdi-Ranaldo half-spread median 10.9 bp ->
  13.9 bp per stock fill, 29.7 bp per event. Power before the run (a5a8cbb): NW se 54.9 bp, t 3 needs 165 bp net.
  Result: 2,848 events, gross -8.9 bp, net -38.6, NW t -0.24, halves +36 / -110 -> KILLED, M1 FALSIFIED. Bigger buys
  worse (-70); sales mirror negative. Second falsification: family `share_insider` closed. Ledger I108. Opus inline.
- Auto decision 43: run the one look although the power is low (pass chance < 5 %). Alternative: record as
  underpowered without a look. Why: the look is cheap and an M1 verdict settles the family either way.

## 2026-11-17: I-107 fails-to-deliver KILLED; short interest not testable on development

- SEC fails files 2016-01 .. 2021-08 (136; three folders on sec.gov, links read from the page); power before the run
  (se 6.8). Result: cell A net -44 (FALSIFIED), cell B net +18, t 0.92, gain only in 2020-21 -> KILLED. Ledger I107.
- Short interest card dropped before any look: FINRA's free exchange-listed short interest starts 2021-06 (no
  development data); a note in I-107's card, no ledger row (nothing was looked at).

## 2026-11-17: I-106 insider purchases FALSIFIED (the user: "Continue with the new share cards")

- SEC insider datasets 2016Q1-2021Q3 (user's contact string); 2,812 officer / director purchase events >= USD 25 k in
  the top 1,000; power before the run (NW se 29.8 bp). Result: gross -38.2 bp per event over 20 days vs SPY, NW t
  -1.46, second half -120 -> KILLED, M1 FALSIFIED. Mirror (sales) also negative. Ledger I106. Opus inline.
- Auto decision 42: insider card first among the new share cards (strongest literature, free point-in-time data).
  Alternative: short interest or fails-to-deliver first. Why: a published sign (one-sided, t 3.0) and no data gaps.

## 2026-11-17: monthly forward-log task scheduled (the user: "Yes, schedule it")

- Claude scheduled task `monthly-forward-logs`, 3rd of each month 09:00 local, first run 2026-12-03 (prompt in
  C:/Users/justi/.claude/scheduled-tasks/monthly-forward-logs/SKILL.md): MT5 update, Strategy 19 / 20 forward logs,
  shelf update / log / status, FB-254 and card 5 checks, commit + push of research/forward/*.csv, Telegram.

## 2026-11-17: shelf logger built (the user: "Yes, build them")

- `research/screens/2026-11-17_shelf_forward.py` (canary / update / log / status) for I-100, I-84, I-98, H11, I-71,
  I-105; all six canaries reproduce the registered results. New shared code (tests first): `tools/forward_log.py`
  (append-only, 4 tests), `binance_wide.update_spot` + shared month-append helper (1 test), `_fetch` on stdlib TLS
  with the system store (the venv's certifi bundle failed Binance's chain; verification on).
- Found: H11 net differs from its registered value by -1.27 R over 413 dev trades with identical gross: the swap and
  spread tables changed after 2026-11-09; forward uses today's costs. Alpaca's daily open is not the official open
  (median 3.4 bp off): I-105 forward uses the official auction prints.
- Auto decision 40: I-105 forward on official auction prints. Alternative: the daily open as in the diagnostic.
  Why: the frozen rule says official open; the daily open is not tradable as such.
- Auto decision 41: H11 / I-71 canaries on trade counts and gross. Alternative: freeze the old cost tables. Why:
  defaults are not changed without the user; forward rows use the project's current costs.

## 2026-11-17: M1 and M3 accepted (the user: "Yes, M1 and M3"); shelf set up

- Rules in docs/research-runner.md › Verdicts and shelf. Ledger relabelled (verdict prefix "M1 (2026-11-17)"):
  UNPROVEN-POSITIVE H11 Gotobi G1, I71, I73 (Strategy 19), I84, I98, I100; FALSIFIED I76 (net -4.7 at its own 20 bp
  cost; Fable's list had it UNPROVEN at 10 bp). Only the 7 verdict cells changed (checked).
- I-105 registered forward only: I-102's 09:30-open diagnostic as a frozen daily rule (power 30 % by day 520).
- Auto decision 38: register I-105 forward-only. Alternative: leave the diagnostic unused. Why: forward data spends
  nothing and is the only clean evidence; it is a new row (no rescue of I-102's verdict).
- Auto decision 39: apply M1's "normal cost" as each card's pre-registered cost (I76 -> FALSIFIED). Alternative:
  Fable's 10 bp reading. Why: the card fixed 20 bp before data.
- Next: one shelf logger for the forward logs to build (I-100, I-84, I-98, H11, I71, I-105); Strategy 19 has one.

## 2026-11-17: I-104 (card 9, Wikipedia attention) KILLED; the sweep's runnable cards are done

- Mapping from Wikidata (89 % of member-months), 1,514 articles' daily views (user's contact string); power before
  the run (sd 77, se 4.6). Result: gross -2.5 bp/week (t -0.27), both cells KILLED. Ledger I104. Opus inline.
- Sweep status: card 0 done, 1 KILLED, 2 done (universe), 3 KILLED, 4 KILLED, 5 registered (forward), 6 A done
  (B closed on data, C needs AWS), 7 KILLED, 8 needs the user's source pick, 9 KILLED. Five new looks on the wide
  universe and crypto today, none near a pass; the 09:30-open reversal diagnostic is the only positive sign (parked).

## 2026-11-17: I-102 (card 4, overnight -> 10:00 reversal, real-share cost) KILLED

- 10:00 prices from one narrow request a day (A7, 1,373 days); power before the run (random-decile sd 22, se 0.58).
  Result: gross +2.55 bp/day (t 1.04), net -4.45, halves +1.3 / -10.3, fade to -10 by 2021 -> KILLED. Ledger I102.
- Diagnostic: the 09:30-open timing earns +12.9 bp/day gross (t 3.94, every year positive); at 7 bp ~+5.9 net, t ~1.8.
- Auto decision 37: do not test the open-timing variant. Alternative: register it as I-104 and spend the test period.
  Why: it is a rescue of a killed cell found on seen development data, its development net t ~1.8 is below the bar,
  and the stop rules forbid rescue variants; parked in HANDOFF › Open for the user (M1 / M3 shelf).

## 2026-11-17: I-103 (card 7, leveraged single-stock ETF rebalance) KILLED

- Step 1 (signal-free size audit, SEC N-PORT with the user's contact string): 352 funds, 280 with reports; GO with
  338 name-days where the required flow is >= 5 % of the 15:30-16:00 dollar volume (326 in 2024; COIN, TSLA, NVDA,
  MSTR). A NaN in the fund sum was fixed before any return (first count 5).
- Step 2: gross +6.4 bp, t 0.80, halves -1.2 / +8.6 -> KILLED; same-size movers without funds +3.2 bp (control).
  Ledger I103. Opus inline.
- Auto decision 36: halves split at the median event date (A3), not calendar halves. Alternative: calendar halves
  (12 events in the first). Why: chosen from event counts before any return.

## 2026-11-17: contact string accepted (the user: "Use my e-mail")

- EDGAR and Wikimedia get the user's e-mail in the User-Agent; stored only in the Credential Manager
  (`backtester-contact` / `email`), never in the repo (docs/share-universe.md › Contact string). Unblocks cards 7, 9.

## 2026-11-17: card 7 split accepted (the user: "Yes, card 7 split as proposed")

- Card 7 (leveraged single-stock ETF rebalance into the close): development from the first fund launch to 2024-12-31,
  test 2025-01-01 .., once (docs/share-universe.md › Splits). Step 1 still needs the EDGAR contact string (N-PORT).

## 2026-11-17: card 4 data path (share-universe A6 -> A7)

- 30-min bars for 2,418 names would have taken ~14 h: Alpaca builds every timeframe from minute bars and pages by
  10,000 underlying minutes (~3 weeks a symbol), so 1-hour bars are no faster. Card 4 needs two prices a day; they come
  from one multi-symbol 1-min request per day and 500 names (09:57-10:03 ET), ~3 requests a day, before any intraday
  data was read. Downloader gained an `end` date (test first). Full suite 6006 passed, ruff clean.
- Auto decision 35: narrow per-day minute requests instead of full intraday history. Alternative: 14 h of 30-min bars
  (all intraday cards later). Why: same trades for card 4, ~1 h; full history only if a later card needs it.

## 2026-11-17: card 2 universe built; I-101 (card 3, FINRA short volume) KILLED

- Card 2: `docs/share-universe.md` frozen before any return (5163736); downloader batch mode (tests first, 9 pass);
  FINRA monthly symbol lists (curl: FINRA's CDN refuses Python's default client) + Alpaca daily bars of 23,756
  candidates (1.8 GB); universe 2016-04 .. 2026-12, 1,000 names a month, 2,418 symbols, ~220 (2016) .. ~120 (2021)
  delisted members a month caught through FINRA. 30-min bars for the union downloading (card 4).
- I-101: pre-registered (5ebefb7), FINRA development files complete, power before the run (sd 72, se 4.4). Result:
  gross +0.8 bp/week (t 0.16), deciles flat; both cells KILLED (A t -2.55, B t -2.88). Ledger I101. Opus inline.
- Auto decision 32 (A4, A5 of the universe): exclude 13 delisted ETPs / non-common symbols found by reading all 532
  no-asset members; start 2016-04 (Alpaca history). Alternative: keep them / a fund master file. Why: before any
  return; hand review of 532 names is complete for this build.
- Auto decision 33: I-101 cost 13 bp a week on the long-short unit (both legs: 2 fills x 3 bp + 0.6 borrow).
  Alternative: the card's literal "7 ... doubled 14". Why: the card's own arithmetic gives ~7 per side; the
  conservative reading. Moot: gross was +0.8.
- Auto decision 34: two-sided cards at |t| 3.3 (M9 wording) without waiting for M9. Alternative: 3.0. Why: stricter.

## 2026-11-17: M13 accepted (the user: "Yes, accept M13")

- Real US shares are a research venue under goal 2 (AGENTS.md › Venues, rule set by the user 2026-11-17). Unlocks
  cards 2-4, 7, 9. M1-M12 still open. Next: card 2 (universe rule, downloader extension, download).

## 2026-11-17: card 2 questions 1-2 (Alpaca coverage, signal-free)

- 20 of 20 names delisted 2016-2021 have full daily SIP history to their last day (prices match deal terms); the
  free plan serves `/v2/stocks/auctions` (official open / close prints) from 2016; `/v2/assets?status=inactive`
  (19,149 symbols) misses pre-2018 delistings (LNKD, YHOO). Question 3 (universe counts) waits on M13.
  `knowledge/reviews/2026-11-16-idea-sweep/card2_alpaca_audit.md`. Opus inline.
- Auto decision 31: run card 2's signal-free questions 1-2 before the user's M13 answer. Alternative: wait. Why: no
  venue commitment and no return look; the answers inform the M13 decision (survivorship was its main risk).

## 2026-11-17: card 6 step A (Hyperliquid audit) and the card 0 (f) fix

- Card 6 A, signal-free (`research/screens/2026-11-17_card6a_hyperliquid_audit.py`, public API, no key): 235 perps,
  56 delisted (all still with candles), funding from 2023-05; Strategy 20's liquidity rule gives >= 20 names on 105
  Mondays (2024-03..), >= 40 on 4. Step B closed on data; step C power: t 2 needs ~93-128 bp/week over ~105 weeks.
  Notes `knowledge/reviews/2026-11-16-idea-sweep/card6a_hyperliquid_audit.md`. Opus inline.
- Card 0 (f): the script subtracted unfinished attempts twice (`ftmo_by_risk` `attempts` is finished-only); rerun:
  simulator pass 80-84 % (full size) / 97-99 % (half) vs closed form 83 / 98 %: the closed form holds.

## 2026-11-17: card 5 pre-registered (crypto book S20 top-100 + S19, forward only)

- Spec section `docs/strategy-crypto_flow.md` › Crypto book; script `research/screens/2026-11-17_card5_crypto_book.py`
  (book = 0.5 / 0.5 of the two r_net, paired by Monday; FB-254 boundary; self-check). No data look. Power: book +0.093
  R/week, sd 0.655, P(confirmed by 104 w) 29 % vs 20 / 17 % single. Sizing left to the user (Open 1). Opus inline.
- Auto decision 29: the book uses the Monday top-100 log, not the mean of the seven weekday tranches. Alternative:
  tranches (card 5's wording). Why: FB-254 is registered on the Monday book; tranches start on different days and
  would need their own pairing rule.
- Auto decision 30: equal risk through each stream's existing R (its development sd, rounded: 600 / 1,000 bp) instead
  of new weights. Alternative: re-estimate the development sds. Why: no new number fitted; the R units are frozen.

## 2026-11-17: handoff taken over; I-100 (Fable card 1) wide funding carry KILLED on t; carry family closed

- The side session (idea sweep + card 0) handed its work to this loop; committed as 1e132ec. The user confirmed: "No, take it over" (2026-11-17). Loop resumed in
  `Mode=auto` on the sweep's first-week plan.
- I-100 (card 1): pre-registered in 502f6ee / A2 before the run, power line before the run (153 weeks, sd 522, t 3
  needs 127 bp). Result: net +107.1 bp/week, t 2.45 -> KILLED on t only (halves +152 / +63, 40 bp +87, without 2 best
  +86, price +67.6); capped +-50 % keeps 0.75; 2022 -11; corr with Strategy 20 +0.27. UNPROVEN-POSITIVE under the
  proposed M1. Family `crypto_carry_xs` closed (third look). Ledger I100. Opus inline, ~1 h, no Codex call.
- Auto decision 26: take over the side session's cards in this loop (one-loop rule) and start with card 1 (owned data,
  ~1 h) over card 2 (Alpaca wide download; needs M13, the user's decision) and card 5 (a spec, no data). Alternative:
  wait for the user's M1-M13 answers. Why: card 1 and card 5 do not depend on any M decision.
- Auto decision 27: development gate t 3.0 (current rules); M8's 3.3 applies only to a later test look and is decided
  then. Alternative: 3.3 now. Why: M8 is about test-period reuse; development was never spent on funding-price sorts.
- Auto decision 28 (A2): universe exactly as Strategy 20 (index and 1000x contracts kept). Alternative: I-73R's
  index-contract exclusion. Why: the card says "eligible by Strategy 20's rule".

## 2026-11-17: card 0 (Strategy 20 regime / tail audit; the user: "Yes, card 0")

- Fable 5.2 wrote and ran `research/screens/2026-11-16_card0_s20_audit.py`, then hit its usage limit; the Fable window
  (CLAUDE.md › Advisor, until 2026-11-16) is now closed, so Opus wrote `knowledge/reviews/2026-11-16-idea-sweep/
  card0_s20_audit.md` from the raw output. S20 without 2020: +100 bp/week, t 3.38; 2022 -32. S19 vs S20 corr
  -0.05..+0.21, opposite years, joint worst weeks at chance; capped tails keep 53-67 % of the mean; DSR fails only
  against the whole ledger on development. Section (f) pass % is buggy (>100 %); years-to-pass usable.

## 2026-11-16: idea sweep: 8 web scouts + Fable post-mortem and directions (the user: "run it here")

- Last Fable day (CLAUDE.md › Advisor). Opus wrote a context pack; 8 Sonnet scouts (shares / ETFs, futures, crypto,
  replication literature, FX, free alternative data, cross-asset + portfolio, 2024-26 papers) swept the web in
  parallel (~2-3 min each, search snippets only, effect sizes UNVERIFIED). Fable 5.2 (subagent, model `fable`) wrote
  part 1 (post-mortem, ~9 min) and part 2 (ranking + cards, ~15 min). All in `knowledge/reviews/2026-11-16-idea-sweep/`.
- Fable's model: profit needs IC (0.03-0.07 for every real effect here) > c = round-trip cost / sd over the hold;
  proof needs IC x sqrt(name-periods) >= 3. Crypto weekly sorts c ~0.006; FTMO CFD cells c 0.03-0.13. One independent
  survivor (Strategy 20); I-83 / FB-017 are the same bet, I-73 passed only on a pooled t. Goal-1 FTMO edge in 3 more
  months: 3-5 %. Suggested weight 10 % goal 1, 50 % crypto, 30 % wide US shares, 10 % method.
- Scouts: no new price idea clears c on FTMO; ~60 items closed one line each (duplicates, c, power). What survives
  are data sets: FINRA daily short volume (Fable verified free, no key, 2018-08+ consolidated, 2012+ per facility),
  wide Alpaca shares (delisted coverage unconfirmed), Hyperliquid (S3 requester-pays), Wikipedia views.
- Cards 0-9 (Strategy 20 regime / tail audit; wide funding carry on ~200 unseen perps; Alpaca wide-universe audit;
  FINRA short-volume sort; I-96 rule on real shares; pre-registered crypto book forward; Hyperliquid replication;
  leveraged single-stock ETF close flow; retail positioning collector; Wikipedia attention sort). Expected yield of
  the week ~0.4 new passed streams. Method proposals M1-M13 and venue M13 -> HANDOFF › Open 7 (rules: the user's).
- Note: Fable wrote before seeing I-99's result (killed today); cards 3, 4, 7, 9 are on real shares (M13), not CFDs.

## 2026-11-17: Alpaca download complete; ledger hygiene

- `data/cache/alpaca`: 61 symbols (15 ETFs, 46 FTMO shares) 2016-01..2026-11, 5.0 GB; empty months only before a
  listing (ARM, PLTR, ZM, XLC, SPCX) and SNOW's reused-ticker gap 2017-08..2020-08. Alpaca history starts 2016-01.
- `research/ledger.csv`: three rows (HV-T0020-3, HV-T0072-1, HV-T0094-1) had unquoted commas in the notes (24 / 21 /
  23 fields); the notes are now one quoted field, no text changed; pandas reads all 190 rows again.
- Loop stopped: waiting for the user's pick (real-broker shares, paid futures data, or End.).

## 2026-11-16: I-99 shock reversal killed; SHARES family closed (auto)

- One look on Alpaca M1, 2,662 events: gross -2.0 bp, net -9.5, t -2.47, halves both negative, mirror negative too.
  Second SHARES falsification after I-96: family closed (no rescue variants). Opus inline (screen), no dispatch.
- Downloader fix: requests end 16 min before now (free plan returned HTTP 403 for the current month); 6 tests.

## 2026-11-16: loop restarted by the user on the share family (Alpaca M1); I-99 pre-registered (auto)

- **Auto decision 24:** first M1 share look = I-99 (FB-121 single-name shock reversal vs flat QQQ, 33 cheap FTMO names,
  dev 2016-01..2021-09-13; card commit aff8c2c, script e028b6e, both before any data). Alternatives: FB-115 earnings
  momentum (needs earnings dates: EDGAR asks automated clients for a contact e-mail, not sent; and ~750 dev events,
  MDE ~33 bp vs a halved 10-20 bp), FB-118 / FB-119 / FB-122 (halved guess below the ~10 bp L/S cost), FB-120 (meme
  names, wide spreads, few events). Why: the only row with a halved gross above cost and a power line near reach.
- **Auto decision 25:** download reordered: development months (2015-12..2021-09) of QQQ + the 33 names first, the
  rest (ETFs, test period, other names) afterwards. Why: halves the wait for the screen; nothing else needs them yet.

## 2026-11-16: Alpaca share minute-bar downloader (the user: "Get Alpaca data")

- `data/alpaca.py` + 5 tests (paging, month cache, resume, missing key): free Basic plan, SIP history with the
  latest 15 minutes withheld, 1Min, split-adjusted, per symbol-month CSV in `data/cache/alpaca` (ignored). Waits for
  the user's account and key (HANDOFF Open 5). Opus inline, no dispatch (small tool).
- Keys stored by the user; smoke test SPY 2016-01: 16,336 bars, 20 days, close ~194 (matches). Full download
  started: 15 ETFs + 46 FTMO shares, 2016-01 to now, two background processes.

## 2026-11-16: research loop paused: free-data frontier reached (auto)

- **Auto decision 23:** stop the self-paced loop and ask the user for direction instead of running priority 4-5 rows
  (all below power or cost by their own guesses). Alternative: keep screening them. Why: no row can reach t 3; the
  remaining value needs the user's money decisions (HyroTrader challenge, Bybit pilot), rules (K = 10 pause,
  test-period uses), or new data (free Alpaca minute bars for shares, paid futures data). Telegram "Optional" sent.

## 2026-11-16: Bybit venue check on the development period; cross-venue flow not feasible (auto)

- `--dev`: 111 weeks (~2021-11..2023, Bybit-listed coins only): Bybit prices + funding +40.6 bp a week (t 1.12) vs
  Binance prices on the same coins +44.8 (t 1.23). Venue transfer holds in both periods; this window is the weak
  2022-23 stretch already seen in the development halves.
- Independent signal replication (another venue's taker flow) is out of reach on free data: OKX keeps ~100 days of
  taker volume; Bybit public trade files are 15-110 MB a coin a day (hundreds of GB). Recorded, not pursued.

## 2026-11-16: Strategy 20 on Bybit prices and funding: the edge transfers (auto; the user: "continue researching")

- **Auto decision 22:** with the signal backlog below power / cost, validate the one edge on its trading venue (the
  gap named in the Bybit-universe diagnostic). Alternative: the code audit. Why: the user asked to keep researching;
  this bears on the prop decision.
- Bybit public v5 daily klines + funding history for every Binance perp listed on Bybit (cache data/cache/bybit;
  two script fixes: pandas floor, pagination stop). Top-100 book: Bybit +145.5 bp a week, t 2.93 vs Binance prices
  on the same coins +137.9, t 2.80. Spec and decision package updated. Model: Opus.

## 2026-11-16: Strategy 20 funded-phase sizing (FB-265) (auto; the user: "Versuch es noch einmal")

- Loop resumed after an interrupted tick (nothing lost: e57b998 was the last commit).
- One funded year, payouts every 4 weeks: 15 % per side 1 % breach / 8.5 % of balance paid (hourly close), 32 % /
  7.0 % on the wick bound; 20 % 7 % / 11.4 %; 25 % 16 % / 14.3 %; 10 % safe on both marks (5.7 %).
- **Auto decision 21:** keep 15 % per side for the funded phase in the decision package; 20 % only after the first 13
  live weeks. Alternative: 20-25 % (more payout, wick-exposed). Model: Opus.

## 2026-11-15: checkpoint suite (auto)

- Full suite `-n 8`: 5,993 passed, 14 skipped, 4 xfailed, 1 failed (`tests/jobs/test_review_fixes.py::
  test_cancel_real_child_and_grandchild`, real child processes; passes 3 of 3 serially, one run 12 s instead of 0.6 s:
  timing-sensitive under parallel load, untouched code). ruff clean. Known flaky, not fixed (job-queue code, outside
  this research run).

## 2026-11-15: weekday-tranche forward logs for Strategy 20 (auto)

- **Auto decision 20:** skip Fable item 9 (short-leg tail cap: a weighting shaped by spent data; the 15 % sizing does
  not need it) and wire the recommended execution into the forward log instead. Alternative: run item 9 as a
  diagnostic. Why: forward evidence should match what a prop account would trade.
- `crypto_flow --anchor mon..sun` (`anchored_weeks`: relabel k days, shift times back; calendar end respected), own
  forward file per anchor; test-first (Monday = plain book, Tuesday = hand-shifted book, forward paths, bad anchor) +
  golden reproducing FB-022's Tuesday anchor (+113.8, t 2.59). Model: Opus.

## 2026-11-15: hourly prop check and Strategy 20 decision package (auto)

- 1 h klines for all book members (12,248 monthly files). Hourly-close marks = daily close marks (86 % pass at 25 % per
  side with tranches); hourly wick bound 28 % at 25 %, 44 % at 15 %, 99 % at 10 % (~2.9 years). Addendum 4.
- **Auto decision 19:** recommend 15 % notional per side, tranched, HyroTrader Two-Step, first 13 weeks as the live
  fill test (`knowledge/research/reports/2026-11-15_s20_prop_decision.md`). Alternative: 25 % (faster, wick-exposed).
  Why: Bybit's multi-exchange mark price should smooth wicks, but that is unverified. The purchase stays the user's.

## 2026-11-15: swap-free CFD prop census; I-87 stays closed on power (auto)

- Fable item 6 (web-fetch subagent): only FundedNext publishes swap-free accounts for all challenges (+10 % price);
  FTMO publishes nothing on it. I-87 overnight premium on a swap-free account: MDE ~4.4 bp a night vs halved premium
  ~1.4-2 -> closed on power (ledger I87b). `knowledge/research/reports/2026-11-15_swap_free_census.md`. Model: Opus.

## 2026-11-15: Strategy 20 prop simulation with intraday bound and weekday tranches (auto)

- Fable items 2-3. Top-100 book at +92, HyroTrader Two-Step: close marks 74 % (Monday) / 85 % (7 tranches) at 25 % per
  side; worst-case intraday bound 4 % / 2 %. The daily 5 % equity rule is the binding risk; the bound is too harsh
  (all extremes at once). Addendum 3 in the prop-fit report; HANDOFF Open 1 now says: no challenge before an hourly check.
- **Auto decision 18:** download 1 h klines for the book's members (data.binance.vision, public) to settle it.
  Alternative: report the bound and stop. Why: it decides the user's money question. Model: Opus.

## 2026-11-15: Fable advisor call 3; Strategy 20 turnover ~55 % -> fair expectation ~+92 bp a week (auto)

- **Auto decision 16:** last Fable call (window ends 2026-11-16) after three empty harvests. Alternative: harvest
  batch 16. Why: the harvest yield is zero; a ranked view of what is left is worth more.
  `knowledge/reviews/2026-11-15-fable-call3.md`: pause FTMO goal-1 signal research (K = 10), stop harvests; value is
  in making Strategy 20 cheaper, safer, verified. Model: Fable 5.2 subagent (read-only, ~2.8 min).
- Item 1 done: one-way turnover 53 % / 58 % a side a week; netted cost ~22 bp a week at ~10 bp a fill -> fair
  expectation ~+92 (the earlier +74 assumed full turnover). Spec and HANDOFF corrected.
- **Auto decision 17:** follow Fable's pick (items 2-3: intraday-mark prop simulation and weekday tranches), then the
  prop decision package; no more FTMO signal screens or harvests this run unless a new venue fact appears.
  Alternative: keep screening priority 4-5 rows. Why: every remaining row sits below the MDE or the cost.

## 2026-11-15: harvest batch 15 (forced flows: crypto index / fund / reward selling, oil index roll, delistings): nothing kept (auto)

- **Auto decision 15:** harvest batch 15, 6 tasks T0105-T0110 (4 mechanism-first cells + canaries T0109 known answer,
  T0110 nonsense), Codex `gpt-6.1-terra` `--search`, high for ACAD, low for BLOG, 2 parallel. Alternative: a last
  Fable advisor call first. Why: the carded backlog was spent; mechanism-first cells no batch had searched.
- 6 calls ok (~40 s each), no guard alarms. 5 ideas, 0 kept: airdrop / fork parent-coin drift (unfetchable page),
  heating-oil index-roll spread and Binance delisting reaction (untestable), delisting short grid (needs announcement
  dates; FB-041), carry canary (passed, parked needs_data). Nonsense canary empty. Top score already rejected
  (HV-T0072-1). Batches 13-15: 0 kept. Model: Codex terra (search), Opus checks.

## 2026-11-15: crypto backlog sweep: 9 rows closed on power / arithmetic (auto)

- **Auto decision 14:** close the remaining priority <= 3 crypto rows without a look where the halved guess sits below
  the MDE (~105 bp a week for a weekly sort on 186 weeks; ~141 on the metrics years) or the cost: FB-012, 013, 006,
  008, 021, 025, 032, 043, 023 (reasons in the ledger). Alternative: screen FB-012 / FB-013 in one batch. Why: a look
  that cannot reach t 3 at the published / guessed size only spends family budget.
- The Fable crypto backlog is now done apart from priority 4-5 rows and FB-002 (composite, forward-only by its card).
  Next source: a mechanism-first idea harvest (counterparties that must trade). Model: Opus.

## 2026-11-15: I-98 spot-hedged funding carry KILLED (auto)

- **Auto decision 13:** FB-035 next (highest prior of the untested crypto rows, data on disk), as a new family
  `crypto_basis` (hedged; not I-73's price bet). Alternative: prop-mechanics rows (FB-258 / FB-265). Why: a new edge
  for goal 2 is worth more than refining a prop decision the user has not made.
- Gross +45.2 bp a week (funding +46.5), turnover cost 33.3, net +12.0, t 1.84; 2022-23 negative. KILLED; no
  low-turnover rescue. Model: Opus.

## 2026-11-15: crypto prop firms' published rules applied to Strategy 20 (auto)

- **Auto decision 12:** read HyroTrader / CFT public rule pages (web-fetch subagent, Sonnet-class) and rerun the
  prop simulation with them. Alternative: leave the questions for the user to ask the firms. Why: public pages answer
  most of them; contacting a firm stays the user's step.
- Hyro: the 5 % low-cap cap is aggregate (low cap = < 100 M USD cap or 0.5-5 M volume or new); 40 % best-day rule;
  static daily 5 %. CFT: static 10 % / daily 5 %, reverse-trading rule to confirm, $10k daily profit cap.
- Top-100 book (low-cap proxy) at the fair +74 bp a week: 67 % pass at 25 % per side (median 357 days), 38 % at 50 %.
  Addendum 2 in `knowledge/research/reports/2026-11-15_s20_prop_fit.md`. Model: Opus + web-fetch subagent.

## 2026-11-15: FB-254 sequential forward boundaries pre-registered (auto)

- **Auto decision 11:** O'Brien-Fleming group-sequential boundary (8 looks every 13 weeks, one-sided 2.5 %, c 2.071)
  plus an early kill at z <= -2, for Strategy 20, its top-100 variant and Strategy 19; the specs' 52-week kills stay.
  Alternative: an SPRT. Why: the backlog row names O'Brien-Fleming; fixed look dates suit a monthly-updated log.
- Power by week 104 at the fair expectations: Strategy 20 34 %, top 100 20 %, Strategy 19 17 %. Forward logs mainly
  catch breaks; a fast confirmation can only come from live / prop results. Model: Opus.

## 2026-11-15: FB-273 maker-fill model: keep taker; measured taker cost ~10 bp a fill (auto)

- **Auto decision 10:** FB-273 on Monday-only aggTrades (104 daily files, 361 MB, ignored cache) instead of 3 full
  months. Alternative: full months. Why: Strategy 20 trades only at Monday 00:00.
- Maker-first 12.0 bp vs taker 9.9 bp a fill (saving -2.1, t -0.44; fills 93 %, misses ~151 bp): keep taker. Taker
  ~2x the backtest's 5 bp a fill -> fair forward expectation ~+74 bp a week. HANDOFF Open 1 note. Model: Opus.

## 2026-11-15: FB-263 futures re-cost closed by arithmetic (auto)

- Would CME futures costs (~0.5-1.7 bp a round trip; FTMO US500 ~2.4, NAS100 ~1.7, US30 ~0.55) rescue the killed
  intraday index rows? No: even at zero cost the best (I-85) has gross t ~1.9; none reaches 3.
  `knowledge/research/reports/2026-11-15_fb263_futures_recost.md`. Model: Opus.
- Goal-1 tally (HANDOFF Open 4 proposal, not adopted): falsified FTMO signal screens since Wave 2: I-85, I-86, I-88,
  I-89, I-90, I-91, I-92, I-93, I-94 (descriptive), I-96 = 10, no pass.

## 2026-11-15: FB-020 Strategy 20 legs against BTC (auto, diagnostic)

- Long leg - BTC: development +141.6 bp a week (t 2.27), test +5.6; BTC - short leg: development -0.6, test +137.7
  (t 2.21). The edge switched legs between periods; a long-only book (prop-firm friendlier) is not supported. FB-020
  closed (ledger). Model: Opus.

## 2026-11-15: I-97 crypto 3-week momentum KILLED; crypto momentum rows closed (auto)

- **Auto decision 8:** run FB-010 as a normal pre-registered development screen (HANDOFF Open 3 proposes exactly that),
  not as a test-only run. Alternative: leave it for the user. Why: Mode=auto; not a default or money; 3-week momentum
  on this universe was not seen. Published size checked first (LTW 2022: 4.1 % a week): passes the power line.
- I-97: net +40.1 bp a week, t 0.68, halves +201 / -87, deciles flat, corr 0.47 with Strategy 20. KILLED.
- **Auto decision 9:** FB-009 / FB-011 / FB-220 closed without a look (second falsification of crypto momentum after C2).
  Alternative: screen FB-009 (time-series form). Why: two-falsification rule. Model: Opus.

## 2026-11-15: FB-022 Strategy 20 rebalance-day check: robust, Monday the luckiest anchor (auto, diagnostic)

- **Auto decision 7:** FB-022 (prior 80, cheap) before new signals. Criteria committed before the run.
- All 7 weekday anchors positive in both periods (development +85..+153, test +46..+147 bp a week); other-six mean +123
  / +85 vs Monday +145 / +147: robust. Fair forward expectation = all-anchor mean (~+94 test, ~+126 development).
  Spec section added. Model: Opus.

## 2026-11-15: Wave 3: I-96 overnight -> intraday reversal on share CFDs KILLED; Wave 3 closed (auto)

- **Auto decision 5:** unblock Wave 3 with free daily data (Yahoo chart API, development range only) and today's FTMO
  share spreads read from MT5 M1 (`research/screens/2026-11-15_share_spreads.py`; 33 names at <= 10 bp, the cheapest
  ~2.3-5 bp at the open / close). Alternative: wait for the user's free-tier minute account (HANDOFF Open 5). Why: the
  priority-1 share row only needs daily bars for its screen.
- I-96 (FB-112): 2,944 days, gross +10.1 bp a day (gross t 4.44), cost 16.1, net -6.0, t -2.64; halves +1.2 / -13.6;
  fading to negative 2019-21. KILLED; family `shares` one falsification.
- **Auto decision 6:** close FB-113 / FB-114 (same mechanism; the extreme decile earns about one leg's cost), FB-115
  (power without outside M1), FB-123 / FB-124 (cost + financing) without a look. Alternative: screen FB-113 as a second
  look. Why: a changed rule on a mechanism whose gross is below cost would be a rescue. Model: Opus.

## 2026-11-15: I-95 closed by arithmetic; FB-017 liquid Strategy 20 frozen and wired into the forward log (auto)

- I-95 (Strategy 20 on FTMO's 30 crypto CFDs, a goal-1 bridge): swap -30 %/yr on both sides = ~115 bp a week for the
  long-short book vs a ~50-60 bp liquid edge: closed, no data look.
- **Auto decision 4:** freeze FB-017 (top 100 by 30-bar median quote volume, HyroTrader's low-cap cap) and run it as a
  diagnostic on the spent periods, then add it to the forward log. Alternative: forward only, no diagnostic. Why: the
  user's prop-firm decision needs to know whether the edge survives without small caps; no N other than 100 was run.
- Diagnostic: development +171.0 bp a week, t 3.64 (full +145.0); test (spent) +166.3, t 3.06 (full +147.2). The edge
  does not depend on the small perps. `CryptoFlowConfig.top_volume`, `crypto_flow --liquid [--forward]` (own log),
  test-first (cut, ties, NaN-signal symbols, future invariance, CLI path) + goldens for both periods. Model: Opus.

## 2026-11-15: Strategy 20 on the Bybit universe (auto, diagnostic)

- **Auto decision 3:** check whether Strategy 20's book exists on Bybit (venue of both candidate crypto prop firms, HANDOFF
  Open 1) before the maker-fill model. Alternative: FB-273 maker fills first. Why: it bears directly on the open money
  decision and costs minutes.
- Public Bybit instrument list (821 USDT perps; 678 of Binance's 923 perps are listed, each counted from its Bybit launch
  day): frozen book on the spent test period +132.8 bp a week, t 3.37 (full +147.2, t 3.76); 191 vs 238 eligible a week;
  79 % of the full book's legs are Bybit coins. Diagnostic only (Bybit-delisted coins missing, Binance prices / funding).
  Addendum in `knowledge/research/reports/2026-11-15_s20_prop_fit.md`. Model: Opus.

## 2026-11-15: Continue.Research Mode=auto (no limit), start; Wave 5 closed on power (auto)

- Baseline: 5,986 passed, 14 skipped, 4 xfailed (`-n 8`), ruff clean. Family budget: 64 looks, 4.5 expected false passes
  (calendar clocks 3.9 of them).
- **Auto decision 1:** Wave 5 first (HANDOFF next step 2), power lines before any look. Alternative: the deferred Binance
  items (maker-fill model, liquid-only Strategy 20). Why: Wave 5 rows are cheap to close or open, signal-free.
- `research/screens/2026-11-15_wave5_power_lines.py` (counts and rms only, no direction applied): FB-186 macro releases
  (calendar only from 2020: 72 release times) MDE 10.1 bp vs halved guess 2.5-7.5; FB-190 central banks MDE 30.3; FB-215
  auction pooled MDE 6.8 vs 3; FB-040 unlocks MDE 283 vs 100-200; FB-028 / FB-029 funding extremes date-clustered MDE
  123 / 81 vs 25-60 / 25-75. All closed before any look (ledger FB186 ... FB029, stage rejected, not looks).
- **Auto decision 2:** FB-066 AUDNZD closed although its optimistic line (67.6 bp) sits inside the halved guess (40-75):
  only 36 entries in 11 years (~3 a year), so it fails the required size (FTMO ~300 trades a year) and adds nothing as
  one of K streams. Alternative: screen it (one look). Model: Opus.

## 2026-11-15: End. (the user: "Yes, End.")

- Full suite 5,986 passed, 14 skipped, 4 xfailed (`-n 8`); ruff clean (src, tests, research/screens). HANDOFF rewritten,
  ROADMAP line added (V2.10, accepted 2026-11-15), brief `crypto_flow.md` archived, `research/trials.jsonl` unchanged
  (no runner trials this session). Uncommitted, not Opus's: `src/backtester/tools/notify.py`.
- Auto decisions of the session (details in the entries above): (1) Fable directions call; (2) Binance metrics not
  downloaded; (3) parked MT5 tests not run; (4) pass map first, then I-76; (5) no I-76 rescue; (6) Fable row 12 skipped
  (required size); (7) I-77 literature first, not screened; (8) harvest batch 14; (9) I-78 one-time test; (10) I-81
  screened despite weak power; (11) Wave 1 order and deferrals (FB-005 / 007 / 273); (12) I-83 one-time test, no
  separate build; (13) Wave 2 start (noise band + gamma; overnight closed by arithmetic); (14) SMT before rotation;
  (15) FB-055 / 095 not run, FB-059 parked, FB-244 later; (16) ICT event rules before the null model.

## 2026-11-15: Wave 4: ICT level-touch null model (the user: "Null model")

- I-94 (descriptive, one look for `ict_levels`): FVG first touches return +0.38 bp in 60 minutes vs -0.26 bp for a
  shifted null zone (difference +0.2, t 0.86); equal highs / lows are exceeded less often than single levels at the same
  distance (-1.4 points, t -4.78). No concept above its null; the remaining ICT backlog rows are closed by this pass.
  Fixed before data: the null zone stays on the real zone's side of price. Model: Opus.

## 2026-11-15: Wave 4: ICT event rules I-91 / I-92 / I-93 KILLED (the user: "Wave 4 (ICT test)", auto)

- **Auto decision 16:** run the three concrete ICT rules (PDH / PDL raid, power of three, CRT) with timed exits on 8
  cheap symbols pooled before the level-touch null model (FVG, equal highs). Edge case fixed before data: a CRT candle
  that takes both prior extremes is skipped.
- I-91 net -1.5 bp (t -0.87), I-92 -2.6 (t -1.59), I-93 -0.8 (t -0.87); controls no worse. All KILLED; family
  `ict_levels` now 7 looks. Observation only: the raid fade is positive on the three US indices (post-hoc). Model: Opus.

## 2026-11-15: Wave 2 part 3: I-89 / I-90 intraday index rotation KILLED; Wave 2 paused (auto)

- I-89 follow the morning NAS100-vs-US500 move: net -3.1 bp a day, t -4.19 (gross +1.3 vs two-leg cost 4.4). I-90 fade an
  extreme morning: net -13.3, t -3.02 (gross -8.9: extremes continue). Both KILLED; family closed. **Auto decision 15:**
  FB-055 (same fade mechanism) and FB-095 (continuous SMT, after I-88) not run; FB-059 (four-index agreement) parked
  because the I-88 diagnostic already showed its result shape (a test would not be blind); FB-244 signal stacking
  left for later (its components are all below cost; prior 8 %). Wave 2 tally: 6 looks (I-85, I-86, I-88, I-89, I-90)
  + I-87 by arithmetic: no FTMO stream. Model: Opus.

## 2026-11-15: Wave 2 part 2: I-88 SMT divergence KILLED (auto)

- **Auto decision 14:** SMT next (the user's explicit interest; FB-078..080 in one screen) before the two-leg rotation
  tool. I-88 NAS100 / US500: 1,490 trades, net -0.26 bp, t -0.17; every split within +-2 bp gross; US triad the same.
  KILLED; family `smt` one falsification. Diagnostic seen: confirmed breakouts (both legs) continue (+4.1 bp, t 2.33),
  noted on FB-059. Model: Opus.

## 2026-11-15: Wave 2 part 1: I-85 / I-86 noise-band momentum KILLED; I-87 overnight below cost (auto)

- **Auto decision 13:** Wave 2 starts with FB-199 / FB-201 (published setup + gamma split, one screen) and closes
  FB-107 / FB-108 by arithmetic (swap 2.4-2.9 bp a night ~ the 2.8 bp published premium). Alternative: the two-leg
  rotation tool first. Why: one script, the gamma file was just unlocked, and it is the last look of the `orb` family.
- I-85: net +0.3 bp a day, t 0.37 (gross +3.0 vs cost 1.7 a trade); I-86 negative-gamma days: -10.8 bp a day, t -1.97,
  opposite sign. Both KILLED; family `orb` closed. DIX / GEX cached in `data/cache/squeezemetrics/`. Model: Opus.

## 2026-11-15: Wave 1 done: I-84 spot-minus-perp flow KILLED (auto)

- Spot daily klines for 243 perps (development months, `data/cache/binance_wide_spot`). I-84: net +70.5 bp a week,
  t 1.76 -> KILLED; adds nothing beyond perp flow (corr 0.58 with Strategy 20). Wave 1 tally: I-82 killed, I-83 passed
  (twin of Strategy 20), I-84 killed; prop-firm table and Strategy 20 prop simulation done; FB-005 / 007 / 273 deferred.
  Family `crypto_xs_factors` now 6 looks (threshold stays 3.0 to 10). Model: Opus.

## 2026-11-15: Strategy 20 against crypto prop-firm rules (auto)

- `knowledge/research/reports/2026-11-15_s20_prop_fit.md`: daily-marked weekly book (paths reproduce the screen's
  weekly net), 2-Step 10 + 5 %, 5 % / 4 % daily, 10 % static: 25 % notional per side passes 90-100 % in every scenario
  (test, development, test with 70 bp a week slippage) in ~10-16 months; 50 % per side 60-90 % in ~4-6 months.
  Optimistic (resampled weeks, end-of-day marks, low-cap cap not applied). HANDOFF Open 12 (the firm and fee are the
  user's money decision); Telegram sent. Model: Opus.

## 2026-11-15: Wave 1: I-82 killed, I-83 absorption PASSED its one-time test; crypto prop firms (auto)

- Shared tool (0ba5965) reproduces I-78 (canary). I-82 daily flow KILLED (-4.2 bp a day, t -0.74). I-83 absorption
  (flow residual on the 7-day return) passed all development gates (+145.4, t 3.57) -> **auto decision 12:** one-time
  test (gates pre-registered fc7d57c, test mode 6d8e072): PASSED (+101.6 bp a week, t 2.85, pooled 4.56). Correlation
  with Strategy 20 0.83: evidence that the flow edge is not just momentum; no separate build (alternative: build it
  as Strategy 21; why not: nearly the same book). Placebo diagnostic corrected to gross. Telegram sent.
- Prop-firm rule table (`knowledge/research/reports/2026-11-15_prop_firm_rules.md`, Sonnet web subagent): HyroTrader and
  Crypto Fund Trader (Bybit, 550-700+ perps, weekend holds, no stop required, own bots allowed) could host Strategy 20;
  Bitfunded cannot (no bots, 5 positions). Signing up / fees: the user's decision.

## 2026-11-15: Wave 1 started (the user: "Yes, Wave 1", then "Mode = auto")

- Mode=auto for the rest of this session (the user). **Auto decision 11:** Wave 1 order: crypto prop-firm rule table
  (Sonnet web subagent, background), then I-82 / I-83 / I-84 (FB-001 / 003 / 004) through one shared screen tool with
  the I-78 canary; FB-005 / FB-007 deferred (metrics only from 2021-12: ~104 development weeks, t 3 needs ~200 bp a
  week), FB-273 deferred (aggTrades, GBs), FB-274 done in the realism check, FB-017 (liquid-only Strategy 20) noted
  as a forward-log variant for the user. Cards + kills before data.

## 2026-11-15: Wave 0 of the idea universe (the user: "1")

- `knowledge/research/reports/2026-11-15_wave0.md`: MT5 census of 166 symbols (shares: FTMO history before 2021-09
  for AAPL / MSFT only, so a share screen needs outside data; carry on FTMO negligible, max +0.45 bp a night on FX /
  indices); family budget (52 looks, ~0.5 expected false passes outside the calendar cells vs 2 passes); Binance
  coverage (spot klines from 2017-18, premium index 2020-01, metrics alts 2021-12); DIX / GEX daily from 2011
  (use next day). No signal look. Model: Opus.

## 2026-11-15: Fable advisor call 2: idea universe (the user's request)

- The user: call Fable once more for a few hundred out-of-the-box ideas and a framework to work through them one
  after the other (hedge-fund strategy classes, two-instrument / SMT ideas, ICT and social-media concepts, order
  flow, books, data sources, venues; focus prop firms, other strategies welcome; ~22 % of the weekly limit available).
- Fable 5.2 subagent started in the background; writes only `research/idea_backlog/2026-11-15-fable-ideas.csv`
  (300+ rows with mechanism, data, expected size, cost cell, prop fit, ledger overlap, first screen, prior) and
  `knowledge/reviews/2026-11-15-fable-idea-universe.md` (framework, work order, hedge-fund map, pair / SMT and ICT
  sections, data / books lists, top 30). Allowed until 2026-11-16 (CLAUDE.md › Advisor).
- Result (~23 min): 335 ideas (FB-001..335) in 22 families (210 strategy, 20 filter, 34 method, 26 data, 14 prop,
  31 reading); priority 1: 42, 2: 51, 5: 99 (listed for the record, overlap falsified families or fail cost / power);
  ~100 worth a look in ~40 screens; six waves, nine shared screen scripts, a look budget per family. No web page
  opened: every source is UNVERIFIED. Owner decisions added to HANDOFF › Open 10-11 (test-use counting rule,
  account / scheduled collector). Committed fe0f831.

## 2026-11-15: prop mechanics, sizing policy and concurrent streams (the user: "Prop mechanics")

- `knowledge/research/reports/2026-11-15_prop_mechanics.md` (house simulator, synthetic trades, open attempts count
  as not passed): the house adaptive risk gains only ~0-3 points over fixed risk at equal time (below the 5-point
  keep threshold); K uncorrelated streams divide the time to pass by ~K at the same pass chance (+0.03 R at 0.5 %:
  16.7 -> 5.8 months with 3 streams, ~45 %); correlation 0.3 costs a few points; K x risk must stay <= ~3 %
  (5 streams at 1 % fail 100 % on the daily loss). Fable's closed form was too optimistic (64 % vs ~47 %). Model: Opus.

## 2026-11-15: Strategies 19 + 20 combined (Fable row 13; diagnostic)

- Same 147 test weeks (2024-01-01 .. 2026-10-19; each tool's own output, aligned by Monday): correlation of weekly
  net **0.06**. S19 +143.9 bp a week (t 2.51, Sharpe 1.49 a year, max DD -3,967), S20 +147.2 (t 3.76, Sharpe 2.24,
  max DD -1,455); equal-risk mix +151.3 (t 4.30, Sharpe 2.56, max DD -2,330). Caveats: S19 failed its replication
  on unseen perps (forward log only), both are Binance weekly books, the period is spent. Supports logging both
  forward side by side. Model: Opus.

## 2026-11-15: I-81 new-listing drift KILLED (auto; the user: "Keep researching")

- Fable row 19 on the crypto split. Card + kills before data (6886954), script frozen (84a5482), power line
  (1c18c02: t 3 needs ~536 bp per event; **auto decision 10:** screen anyway, one counted look in a new family;
  alternative: close as underpowered like HV-T0020-3).
- Result: 234 events, net +611.5 bp per event, t 1.16 (median +1,948: most listings fall against BTC; squeezes in
  the tail); halves +538 / +682; doubled costs +592. KILLED on t. Model: Opus.

## 2026-11-15: Strategy 20 realism check (the user: "Yes, realism check")

- Diagnostics on spent data, no gate: break-even extra slippage ~37 bp per side per member (test); with tiered
  slippage (< 20 M USDT 25 bp, 20-100 M 10 bp, > 100 M 3 bp a side; assumptions) net +77 bp a week (t 1.98) in the
  test, +93 in development; 56 % of test members trade < 20 M USDT a day. The most liquid half alone earns +163 bp
  (t 3.15; a post-hoc variant, not adopted). Capacity irrelevant at retail size. Model: Opus.

## 2026-11-15: Strategy 20 crypto taker-flow sort: research tool built (the user: "Yes, build it")

- Spec `docs/strategy-crypto_flow.md` (R = 600 bp, the development weekly sd; forward log from 2026-11-16; kill
  after 52 weeks at net <= 0 or drawdown worse than -2,200 bp). Codex `gpt-6.1-sol` medium, brief
  `briefs/crypto_flow.md`: call 1 (36 s) stopped on three conflicts between the spec and the tested screen
  (delisting funding, eligibility count, update files): spec aligned with the screen; call 2 (~13 min, guard ok)
  built the data layer, rule module, CLI and 18 tests. Opus verified: golden identical (186 weeks +145.0 / t 3.24;
  147 weeks +147.2 / t 3.76), CLI reproduces the test, full suite 5,986 passed, ruff clean.

## 2026-11-14: I-78 one-time test PASSED (auto decision 9)

- Test months downloaded (911 perps with 2024+ data; AWE / MBOX refetched after connection resets). First `--test`
  call crashed before any result (a perp without a funding file: empty fallback series had no datetime index);
  fixed and committed (d1f79cd) before the run. Dev re-run identical (+145.0, t 3.24).
- Result: 147 weeks, net +147.2 bp a week, t 3.76, pooled t 4.81, halves +120 / +174, without 2 best +127, 40 bp
  +127, PF 2.30, max drawdown -1,455 bp: all six gates PASS. Diagnostics: tail-driven (pump capture in small perps);
  clipped at +-30 % a week both periods keep ~+56-58 bp (t ~1.9 each). Model: Opus. Telegram sent.

## 2026-11-14: crypto split adopted (the user: "Yes, adopt split"); I-78 flow passes development gates (auto)

- Rule in `docs/research-runner.md` › Periods (0ba1c42). Wide universe: 923 USDT perps listed, 265 with data before
  2024 (`research/screens/2026-11-14_binance_wide_download.py`, daily klines + funding, delisted included).
- Cards + kills before data (709a87c), script frozen (d73dfed), power line (d6ccfa4: 186 weeks, |t| 3 needs ~106 bp).
- Result: **I-78 weekly taker-flow imbalance PASSED all five development gates** (+145.0 bp/week, t 3.24; halves
  +327 / +1.7; 40 bp +125; without 2 best +117; correlation 0.56 with a 1-week past-return sort). I-79 MAX and
  I-80 volume shock KILLED. Model: Opus.
- **Auto decision 9:** run the I-78 one-time test (Mode=auto: passed every pre-registered development gate); gates
  pre-registered before any test data (eba2631), test mode added (2941156), dev re-run identical. Alternative:
  park it for the user. Why: auto rule. Expectation: weak (2022-23 half ~0).
- **State at the usage limit:** test-month download (2024-01..2026-10 -> `data/cache/binance_wide_test`) was started
  in the background; if incomplete, rerun the same command (cached symbols are skipped, files are atomic). Then:
  `.venv/Scripts/python.exe -W ignore research/screens/2026-11-14_i78_crypto_wide_factors_screen.py --test`, record
  pass / fail in the card, ledger, this log and HANDOFF, Telegram the result. Downloader needs
  `REQUESTS_CA_BUNDLE` = certifi + Avast CA and `PYTHONIOENCODING=utf-8`.

## 2026-11-14: harvest batch 14 (share CFDs, crypto intraday flows, closing auctions) (auto)

- **Auto decision 8:** harvest batch 14, 8 tasks T0097-T0104 (6 content cells aimed at the new required size:
  daily-or-faster effects >= ~3 bp gross on cheap CFDs, FTMO share CFDs or crypto majors; canaries T0103 known
  answer, T0104 nonsense), Codex `gpt-6.1-terra` `--search`, high for ACAD, low for BLOG, 2 parallel. Alternative:
  pause signal research until the user answers HANDOFF Open 7-9. Why: auto mode never idles; the venue facts
  (share and crypto CFDs) opened cells no earlier batch searched.
- Telegram sent: "Action needed" for HANDOFF Open 7-9.
- Result: 8 calls ok (12-68 s each), no guard alarms. 10 ideas, 0 kept: 6 parked needs_data (cross-sectional
  end-of-day reversal in US stocks, Da et al. EOD paper, 3.6-6.2 bp a day long-short across all stocks: on ~59 share
  CFDs with a spread per leg it is far below cost; overnight-return sorting, monthly; LTW 3-week crypto momentum =
  HANDOFF Open 5; two funding-settlement ideas = I-72, closed), 3 unfetchable (bitcoin turn-of-candle 0.58 bp a
  minute: below cost anyway; large-coin momentum; Euro Stoxx auction flow), 1 rejected untestable. Canaries: known
  answer PASSED (Lustig et al.), nonsense empty. Unverified rate 0 %. Model: Codex terra high / low + Opus.

## 2026-11-14: I-77 earnings-announcement premium on share CFDs: carded, not screened (auto)

- **Auto decision 7:** check the literature before any share-CFD data work. Sonnet web subagent: ~21 bp in the 3-day
  window to 2004, large firms smaller, a 2020 paper reports the US premium gone (not opened, 403). Halved ~10 bp vs
  ~8-10 bp cost (spread + two nights of swap): not screened. FTMO MT5 share history: MSFT M1 from 2010, NVDA from
  2020-11. Alternative: download share CFD history and screen. Why not: expected net <= 0 before any data.

## 2026-11-14: FTMO venue facts (Fable row 8, partial)

- `knowledge/research/reports/2026-11-14_ftmo_venue_facts.md`: rules re-read (no time limit; 1-Step consistency
  50 % from 2026-10-12; 80 % reward after 2-Step); the MT5 server lists 166 symbols incl. 59 share CFDs and 30
  crypto CFDs (swap -30 %/yr); weekend spreads 0.2-35 bp on the alts we cache, so Binance ideas could run on FTMO
  only for the ~6 cheapest coins at ~7-11 bp. Read-only MT5 calls; an aborted first read left the 30 crypto CFDs
  visible in Market Watch (harmless). Model: Opus + web-fetch subagent.

## 2026-11-14: ideas triage (Fable row 24); free futures data (row 33): Stooq gated; books asked

- `knowledge/ideas.md` overview: 48 "open" rows re-labelled: 29 closed by the cost-wall §4 stop list (family named),
  17 parked as management layers (only on a stream with a net edge), I-03 tested (ledger H10), I-52 done in effect.
  Tooling rows T-xx stay open (T-16 partly answered by the pass map). No data, Opus.
- Row 33: Stooq's free futures CSV sits behind a JavaScript proof-of-work bot check (not bypassed); EIA has energy
  contracts 1-4 only. No free contract-level diversified futures source found: goal-2 futures stay blocked on data.
- Telegram "Optional: New books needed" (Fable row 43): Carver *Advanced Futures Trading Strategies*, Pedersen
  *Efficiently Inefficient*, Harris *Trading and Exchanges*, Ilmanen *Expected Returns*, Bouchaud et al. *Trades,
  Quotes and Prices* (none in `knowledge/books/`).

## 2026-11-14: power budget map (Fable row 5); row 12 skipped (auto)

- **Auto decision 6:** Fable row 12 (index-review auction pooled over six indices) not screened: ~48 events a year
  at ~6 bp halved is far below the pass map's ~300 trades a year at +0.05 R, and it would be the family's last
  look. Alternative: power line, then screen. Why not: it cannot become a goal-1 stream even if it passed.
- Power budget map (`knowledge/research/reports/2026-11-14_power_budget_map.md`, 33 symbols, signal-free): daily
  events at 1-6 h holds can show 1-6 bp at t 3; weekly 8-40 bp, monthly 17-80 bp. With the pass map: a goal-1
  stream needs ~2.5-5 bp gross per daily event on the cheapest symbols. Model: Opus.
- Note: Fable row 9 (taker-flow imbalance) overlaps V1 ROADMAP 11.16 (BTC / ETH order-flow study, 2026-10-16:
  effects real but 2-5 bp, below fees; not in the ledger), so it is not a fresh lead.

## 2026-11-14: I-76 liquidation-cascade reversal KILLED (auto)

- Power line before the run (086072b): 5,132 clusters, t 3 needs ~11 bp. Result: net +5.3 bp per cluster, t 2.50,
  2020 +0.0 / 2021 +14.8, doubled costs -4.7: KILLED on t and doubled costs. Control without the flow condition
  -1.9 bp; long side +14.4 bp gross, short -6.9; BTC + ETH -14.7 (t -3.19). Model: Opus only (local screen).
- **Auto decision 5:** no rescue (long-only / alt-only would be post-hoc). Alternative: pre-register a long-only
  variant for the test period. Why not: chosen after seeing the split, and it has passed no development gate.
- Added HANDOFF › Open 7-9 (strike the spent MT5 tests; crypto split, Fable row 7; signal-research stop rule, row 20).

## 2026-11-14: FTMO challenge pass map (Fable row 1); I-76 carded

- Fable 5.2 list in (`knowledge/reviews/2026-11-14-fable-research-directions.md`, 43 rows, ~10 min, Opus checked
  the top rows). **Auto decision 4:** take row 1 (pass map) first, then row 10 (I-76) as the next screen.
  Alternative: row 9 taker-flow imbalance. Why: row 1 sets the required size for every goal-1 idea; row 10 has a
  forced counterparty (liquidations), row 9 has neither a mechanism nor a published size.
- Pass map (`knowledge/research/reports/2026-11-14_challenge_pass_map.md`, house simulator, synthetic iid trades):
  zero edge passes ~30 %; +0.05 R net 64 % in ~340 trades at 0.5 % risk; 2 % risk with 4 trades a day fails 97 %
  on the daily loss. FTMO rules re-read (web-fetch subagent): no time limit, targets 10 / 5 %, 5 % daily, 10 %
  static, 4 days; 1-Step 3 % daily, EOD trailing, consistency 50 % for orders from 2026-10-12. Model: Opus.
- I-76 card and kills committed before data (1e5953e), script frozen (95abf49).

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
