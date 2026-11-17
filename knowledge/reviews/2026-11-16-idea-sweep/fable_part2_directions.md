# Final directions: scouts ranked against the survival model, with cards

Claude Fable 5.2, advisory, 2026-11-16, part 2 of 2 (last session). Builds on
`fable_part1_postmortem.md` in the same folder. Read-only on the repo.

Read: all 8 scout files in full. The scouts worked from search snippets; their effect sizes are UNVERIFIED and
I use them only for sign and rough size. Research analysis, not a recommendation to trade or buy; venue and money
decisions are the user's.

**What I verified myself today (web):**

| Fact | Result | Source |
|---|---|---|
| FINRA daily short-sale volume files | Free, plain HTTP, no key. `CNMSshvolYYYYMMDD.txt` (consolidated) exists from 2018-08-01 (HTTP 200) and not for 2016-01-04 (403). Per-facility files go back further: `FNSQshvol20120103.txt` 200 (200 KB), `FNYXshvol20150105.txt` 200. Fields: `Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market`. Posted by 18:00 ET on the trade date. Off-exchange (TRF / ADF) volume only | https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files ; files under https://cdn.finra.org/equity/regsho/daily/ |
| Alpaca daily bars vs auction prints | Daily and minute bars are "aggregated from trades"; official open / close condition codes do **not** set the daily open / close. A separate "Historical auctions" endpoint exists (SIP). Free plan: SIP history with the last 15 minutes withheld | https://docs.alpaca.markets/us/docs/market-data-faq ; https://docs.alpaca.markets/us/reference/stockauctions-1 |
| Alpaca delisted names | **Not confirmed.** The FAQ says "make sure the asset is active"; a forum thread says there is no historical-assets endpoint. Survivorship stays an open risk until tested on the live API | https://forum.alpaca.markets/t/delisted-tickers/18227 |
| Hyperliquid history | L2 book and `asset_ctxs/[date].csv.lz4` in `s3://hyperliquid-archive` (**requester pays**: needs an AWS account, transfer is billed); fills in `s3://hl-mainnet-node-data/node_fills_by_block` (older: `node_fills`, `node_trades`). No date range stated, "data may be missing", no candles in S3. Field list of `asset_ctxs` not shown | https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data |
| OKX / Bybit public trade archives | **Not verified** (search returned only third-party vendors). The research log's finding stands: OKX keeps ~100 days of taker volume, Bybit trade files are too large | n/a |

## 1. One ranked table (data sets first, then ideas)

Columns: c = round-trip cost / instrument sd over the hold (must be below ~0.02); breadth = names per bet;
name-periods = names x development periods (need ~5,000+ effective); NP = non-price data. Priors = chance to pass
its own development and test gates. Rows 1-10 get a card in section 2.

| Rank | Direction (origin) | c | Breadth | Name-periods (dev) | NP | Venue | Data status | Prior | Decision |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Strategy 20 regime / tail audit and selection haircut (part 1; scout 7 B1) | n/a | n/a | n/a | n/a | n/a | owned | certain to inform | **Card 0** |
| 2 | Wide funding-carry sort on unseen perps (part 1 B; scout 3 #3 "basis sort" folds in at weekly speed) | ~0.006 | ~40 a leg | ~200 x 186 weeks | yes | Binance / Bybit perps | owned (`data/cache/binance_wide`) | 20 % | **Card 1** |
| 3 | Alpaca wide universe + auction prints + delisted audit (part 1 D, data set) | n/a | 1,000+ | 1,000 x 1,430 days | no | real shares | free, account exists; delisted names unconfirmed | certain to decide cards 3-4 | **Card 2** |
| 4 | FINRA short-volume ratio, weekly sort, wide universe (part 1 E; scout 6 #1) | ~0.01 | 100 a leg | 1,000 x 297 weeks | **yes** | real shares | free, verified 2012+ | 8 % | **Card 3** |
| 5 | Overnight -> intraday reversal on the wide universe, I-96's rule (part 1 D; scout 1 #2, 4 D2 source) | ~0.025 (borderline) | 100 a leg | 1,000 x 1,430 days | no | real shares | after card 2 | 8 % | **Card 4** |
| 6 | Pre-registered equal-risk book of the crypto streams, forward only (part 1 section 4.3; scout 7 B2) | ~0.006 | as the streams | forward | yes | Bybit / Binance | owned | n/a (no look) | **Card 5** |
| 7 | Hyperliquid: free funding + daily prices by API, fills by S3 (part 1 A; scout 4 D4, scout 8 #8) | ~0.006 | ~100-150 | ~150 x ~130 weeks | **yes** | Hyperliquid / Bybit | API free; S3 requester-pays (user's AWS) | 25 % that it replicates | **Card 6** |
| 8 | Leveraged single-stock ETF close rebalance (part 1 F; scout 1 #1 "extra", scout 8 #3) | 0.02-0.03 real share; 0.1+ CFD | ~15 names | ~300 date clusters | **yes** (forced, computable) | real shares | Alpaca bars free; fund assets from SEC N-PORT (free, monthly) | 10 % | **Card 7** |
| 9 | Retail positioning collector (part 1 G; scout 5 #9) | n/a | 30+ symbols | forward only | **yes** | FTMO CFDs later | free live snapshots, no history | 5 % to matter | **Card 8** |
| 10 | Wikipedia page-view attention sort on the wide share universe (scout 6 #4, turned cross-sectional) | ~0.01 | 100 a leg | 1,000 x 297 weeks | **yes** | real shares | free API from 2015-07 (scout; not verified by me) | 5 % | **Card 9** |
| 11 | Open-interest / positioning sorts (FB-006, FB-008, part 1 C) | ~0.006 | ~50 a leg | 250 x 104 weeks | yes | perps | free, 2021-12+ | 7 % | parked: pass chance below 15 %; revisit only inside card 5 at a 26-week addition date |
| 12 | End-of-day cross-sectional reversal, last 30 min (scout 8 #1) | **~0.06** (30-min sd ~40 bp vs ~2.5 bp) | 100 a leg | huge | no | real shares | after card 2 | 5 % | not carded: fails P1 by the rule; overnight-hold variant is card 4's cell |
| 13 | Crypto session-split sort, realised-skewness sort (scout 4 D2, D3) | ~0.006 weekly | ~50 | ok | no | perps | owned 1 h | 4-5 % | parked: price-only, no published crypto size, family `crypto_xs_factors` already at 7 looks (I-79 MAX killed) |
| 14 | Form 4 insider buys on a wide universe (scout 6 #2) | ~0.01 | events | ok on small caps | yes | real shares | EDGAR free, wants a contact e-mail in the client string | 5 % | long-range row |
| 15 | Volatility-managed overlay on the survivors (scout 7 A1 / B5) | n/a | n/a | n/a | n/a | n/a | owned | n/a | not a look: a variant shaped on spent data; only as a pre-set sizing rule inside card 5 |
| 16 | Commodity cross-section carry / basis-momentum, ETF trend sleeve, VIX curve, GSCI roll (scout 2 #3, #4, #8; scout 7 A2; scout 4 D7) | fine on futures | 20+ | monthly, decades | partly | futures / ETFs, own capital | mostly paid; EIA and Cboe strips free | 10 % | long-range rows; not this week |

**Duplicates and closures, one line each (no card, no look):**

| Scout item | Closed because |
|---|---|
| S1 #1 index leveraged-ETF last-30 conditioned; S8 #3 see-saw; S7 A4 | H02 / H06 measured it: 0.5-1.3 bp gross, no rise on large-move days; index flow is small against futures volume. Single-stock version is card 7 |
| S1 #2 overnight ETF premium; S7 A3 European-open drift | I-87 / I-87b: swap >= premium; ~1.2 bp a night against the spread |
| S1 #4 dealer gamma / 0DTE | I-86 (opposite sign, t -1.97); intraday gamma data is paid |
| S1 #6 noise-area momentum | I-85 killed (t 0.37); `orb` family closed |
| S1 #3 closing imbalance feed; S1 #5 ETF price vs NAV; S1 #8 retail internalisation; S8 #2 VIX products; S8 #7 overnight venue | needs paid data |
| S1 #7 and S8 #9 Russell reconstitution; S2 #5 corn; S2 #6 crack / crush; S2 #7 index roll; S5 #6 interventions; S3 #4 delivery futures; S3 #9 stablecoins | 1-12 events a year: closed on power (part 1 P2) |
| S2 #1 natural-gas storage day | already rejected 2026-11-02 (`NATURAL_GAS_ANNOUNCEMENT_DAY_CANDIDATE_SCAN.md`): the authors' own 2014-18 subsample shows nothing; FTMO NATGAS also has no development data |
| S2 #2 Treasury month-end extension; S8 #4 threshold rebalancing | no bond instrument owned; monthly events, turn-of-month family already at 3 looks (H04, H09, I-67) |
| S2 #9, S5 #10, S6 #3 COT positioning | I-74: tradeable part ~11 bp per 20 days, below swap + spreads; 10 CFD proxies are ~6 independent bets (fails P2, P5) |
| S2 #10 FTMO CFD roll mis-sizing | a platform gap, not a market edge; firm can change it and may ban it (part 1 list "would not do") |
| S3 #1 quarter-hour imbalance | 6 majors, 4-12 h holds: c ~0.04-0.08, breadth 6; I-82 shows flow at daily speed pays less than its cost |
| S3 #2 perp-spot basis reversion | two legs at taker fees; I-98's cousin (turnover ate the funding) |
| S3 #5 DeFi liquidations; S8 #8 liquidation / ADL cascades | I-76 family; ~7 cascades in 3 years; the data, not the idea, lives on in card 6 |
| S3 #6 Deribit expiry hour; S3 #7, S8 #5, S8 #6 ETF window / hours; S3 #8 weekend | one or two instruments, calendar-style (SC1 / SC2: 0 of 1,452), c ~0.08 on BTC at 1 h |
| S4 D1 factor timing of own sorts | ~270 weeks of one series: no power, and a look at spent data |
| S4 D5 same-weekday cross-section on perps | daily turnover: 20 bp against ~15 bp gross (I-82) |
| S4 D6, S5 #2, #4, #5 FX carry / momentum, gated or intraday | 7 independent currencies, no flow data, no swap history; P03 closed by arithmetic (part 1); H07 covers the intraday form |
| S5 #1 Tokyo / ECB fixes; S5 #3 month-end signed; S5 #7 gold fix; S5 #8 option cuts | fix family closed (S08, HV-T0045, H12): 2.5 bp gross against the same cost; gold fix reformed 2015; no strike archive |
| S6 #4 Google Trends; S6 #5 GDELT; S6 #6 prediction markets; S6 #8 weather; S6 #9 net liquidity; S6 #10 stablecoin supply | one index or one commodity per date (fails P2), or not point-in-time, or 8-12 events a year |
| S6 #7 Robintrack | feed ended 2020-08: no test period, not updatable |
| S7 A5 crypto jump -> index CFDs | lead-lag family closed (L14-L18); minutes-scale against 1-3 bp spread |
| S7 B3 / B4 weighting and challenge optimisation | done (pass map, prop mechanics, S20 package); with 1.5 streams equal risk is enough |

What the scouts confirm: eight independent sweeps found **no new price idea** that clears c on the FTMO venue, and
the only items that survive the model are data sets (short-sale volume, wide share bars, on-chain fills, page views).

## 2. Cards (ready for the continue-research loop)

Common to all cards unless stated: rule fixed and committed before any data; gates on per-date net means;
t >= 3.0; doubled-cost check; "without the 2 best periods"; halves both > 0. The extra gates of section 3 are
written in as *proposed* lines and apply only if the user accepts them. Hours are rough.

### Card 0. Strategy 20 regime and tail audit (no new look at any signal)
- **Question:** how much of the forward expectation survives regime and tails, and are Strategies 19 and 20
  independent at slow frequency?
- **Inputs:** the frozen weekly net lists of Strategy 20, top-100, Strategy 19 (development and test), nothing else.
- **Outputs (all descriptive, no gate, no variant):** (a) per-calendar-year net and t for each stream side by side;
  (b) correlation of non-overlapping 26-week sums; (c) the joint worst 10 % of weeks; (d) median week and t on
  +-50 % winsorised member returns; (e) deflated Sharpe with the trial counts of `family_budget.py`; (f) the closed
  form "pass ~83 % at volatility ~9 % x Sharpe, time ~1.65 / Sharpe^2 years" against `risk.monte_carlo` on a
  synthetic stream at Sharpe 0.7 / 1.0 / 1.3 / 2.0.
- **Why first:** it sets the shrink factors and sizing for card 5 and the user's prop decision, and costs nothing.
- **Script / effort:** one screen script on existing CSVs, ~2 h, Opus inline. **Data to fetch:** none.

### Card 1. Wide funding-carry sort on unseen perps (family `crypto_carry_xs`, third and last look)
- **Hypothesis:** perps with the highest trailing funding underperform those with the lowest over the next week,
  net of funding and cost, on names never used for I-73 / I-73R.
- **Mechanism (who is forced):** leveraged longs pay funding to hold; when it is extreme they are the marginal
  holders and are liquidated or give up first (BIS WP 1087 mechanism, opened by Opus earlier).
- **Universe:** all Binance USDT perps incl. delisted, **minus the 37 symbols of I-73 and I-73R**, eligible by
  Strategy 20's liquidity rule; weeks with fewer than 40 eligible names are skipped.
- **Signal:** mean funding rate over the trailing 7 days (21 settlements), known at Monday 00:00 UTC.
- **Trade:** short the top quintile, long the bottom, equal weight, hold 1 week; P&L = price + funding received / paid.
- **Cost:** 20 bp a week per unit side (as I-78); doubled = 40.
- **Periods:** development 2020-05..2023-12; test 2024-01..2026-10 once (4th use of that period: threshold 3.3 if
  the alpha-spending proposal is accepted, else 3.0).
- **Power line:** c ~0.006. Long-short weekly sd assumed 475-620 bp (Strategy 20's): MDE at t 3 on 186 weeks =
  105-136 bp. Evidence so far: +112 to +138 (17 perps), +63 (20 perps). Expected t 1.4-3.0; pass chance ~20 %.
- **Kills:** net <= 0; t < 3.0; a half <= 0; net <= 0 at 40 bp; net <= 0 without the 2 best weeks; price part
  < -20 bp (I-73's own kill). *Proposed:* +-50 % capped version keeps the sign and >= half the mean; no half below
  25 % of the mean. **Report, not a gate:** weekly correlation with Strategy 20 (above 0.5 = same stream).
- **Verdict wording:** t 1.5-2.9 with all other kills passed = UNPROVEN-POSITIVE (shelf), not falsified. Either way
  the family is closed after this look.
- **Script / effort:** copy `research/screens/2026-11-14_i78_crypto_wide_factors_screen.py`, swap the sort variable,
  add the exclusion list; ~1.5 h (one Codex terra call or Opus inline). **Data to fetch:** none
  (`data/cache/binance_wide/funding`, `klines_1d`).

### Card 2. Alpaca wide-universe audit and download (data card, signal-free)
- **Questions, in this order, stop at the first "no":** (1) does the bars endpoint return history for names that
  were delisted 2016-2021 (try 20 known ones from the SEC / exchange delisting lists; the assets list with
  `status=inactive` if it exists: UNVERIFIED); (2) does the free plan serve the "Historical auctions" endpoint
  (official open and close prints); (3) how many names have a trailing-60-day median dollar volume above
  USD 20 million per month 2016-2021.
- **Universe rule to freeze here (before any return is looked at):** each month, the top 1,000 US common stocks by
  trailing-60-day median dollar volume, price > USD 5, point-in-time; ETFs excluded.
- **Download:** daily bars 2015-07.. for the union (~2,500 names), and `30Min` bars for the same (13 bars a day,
  ~46 million bars, ~4,600 requests: about an hour inside the rate limit); auctions if served.
- **If (1) fails:** survivorship bias in a reversal test favours buying losers that later vanish. Cards 3-4 then
  run only on the names alive at each date *as far as Alpaca shows them*, are labelled "survivorship not
  controlled", and can at most end as UNPROVEN.
- **Script / effort:** extend `src/backtester/data/alpaca.py` with `timeframe` and a symbol-file argument (test
  first) + one audit script; ~3 h Codex terra, download in the background. **Data source:** the user's existing
  Alpaca account (keys in the Credential Manager; never printed).

### Card 3. FINRA short-volume ratio, weekly cross-sectional sort (new family `share_flow`)
- **Hypothesis:** the abnormal off-exchange short-volume ratio of a stock predicts its next-week return relative
  to other stocks.
- **Mechanism:** two readings, opposite signs. (a) Short sellers are informed (Diether, Lee, Werner 2009: high
  short volume -> lower returns). (b) Off-exchange short volume is mostly wholesalers selling short to fill retail
  **buy** orders, so a high ratio marks retail buying (the reading behind DIX, already on disk). The sign is the
  test: **two cells, |t| >= 3.3.**
- **Universe:** card 2's top-1,000 rule.
- **Signal:** SVR = sum ShortVolume / sum TotalVolume over the last 5 trading days, minus the stock's own mean
  SVR of the previous 60 days. Files: per-facility `FNSQ` + `FNYX` + `FNQC` (+ ADF) summed before 2018-08-01,
  `CNMS` after; a known break, so the 60-day baseline is not allowed to span 2018-08-01.
- **Trade:** Friday's file is public at 18:00 ET. Enter at Monday's close, exit next Monday's close; long the
  lowest decile, short the highest (the mirror is the second cell); equal weight.
- **Cost model (assumption to record):** 2 bp per fill (close-auction or last-minute fills in liquid names) +
  1 bp slippage + 0.6 bp a week borrow on the short side = ~7 bp a week per unit side at full turnover; doubled = 14.
- **Periods:** development 2016-01..2021-09-13 (~297 weeks); test 2021-09-14..now, once.
- **Power line:** c ~0.01. Decile long-short weekly sd guessed 100-150 bp: MDE at t 3.3 = 19-29 bp a week.
  Published ~32 bp a week in 2005 data (UNVERIFIED), halved 16: expected t 1.8-2.8; pass chance ~8 %.
- **Kills:** |t| < 3.3; net <= 0; a half (2016-18 / 2019-21) with the other sign; doubled costs <= 0; without the
  2 best weeks <= 0. *Proposed:* no half below 25 % of the mean.
- **Venue note:** real shares only (a long-short share account is the user's decision). On the 46 FTMO share CFDs
  c is ~0.05: not a goal-1 idea.
- **Script / effort:** downloader for ~1,430 x 4 small text files (~1.5 GB, plain HTTP, no key, be polite: one
  request at a time) + screen; ~4 h Codex. **Fetch first:** https://cdn.finra.org/equity/regsho/daily/ files
  2015-10..now; daily bars from card 2.

### Card 4. Overnight -> intraday reversal on the wide universe (I-96's rule, new cell: real-share cost)
- **Hypothesis:** stocks with the highest market-relative return from yesterday's close to 10:00 underperform
  those with the lowest from 10:00 to the close.
- **Mechanism:** attention buying at the open (retail, overnight clientele) is supplied by intermediaries who are
  paid by the intraday reversal (Berkman et al. 2012; Lou, Polk, Skouras 2019: UNVERIFIED sizes). Not forced.
- **Evidence in the ledger:** I-96 on 33 large-cap CFDs: gross +10.1 bp a day, gross t 4.44, killed by 16 bp cost;
  gross faded to negative 2019-21. The fade is the main reason for the low prior.
- **Universe:** card 2's rule. **Signal:** (10:00 price / previous close - 1) minus SPY's, from the 30-minute bars.
- **Trade:** at 10:00 short the top decile, long the bottom, exit at the close; flat overnight (no borrow overnight,
  no financing).
- **Cost model:** 1.5 bp half-spread + 1 bp slippage at 10:00, 1 bp at the close = ~3.5 bp per name, ~7 bp a day
  per long-short unit; doubled = 14. (Assumption: liquid names; measure real spreads on a sample of Alpaca quotes
  before the screen if the quotes endpoint is free.)
- **Periods:** development 2016-01..2021-09-13 (~1,430 days); test 2021-09-14.., once.
- **Power line:** c ~0.025 (6-hour name sd ~120-130 bp): borderline by the rule. Long-short daily sd guessed
  40-60 bp: MDE at t 3 = 3-5 bp a day net, i.e. 10-12 bp gross needed. Pass chance ~8 %.
- **Kills:** net <= 0; t < 3.0; halves 2016-18 / 2019-21 not both > 0 (*proposed:* neither below 25 % of the
  mean: this is the gate the fade must clear); doubled costs <= 0; without the 2 best days <= 0.
- **Script / effort:** adapt `2026-11-15_i96_overnight_reversal_screen.py`; ~2 h. **Fetch first:** card 2.
- **Rule question for the user:** the `shares` family on CFDs has two kills (I-96, I-99 if confirmed) and "Wave 3
  closed". This card and card 3 are a different cost cell (c 0.01-0.025 against 0.13). They run only if the user
  accepts real shares as a research venue and a new family label.

### Card 5. One pre-registered crypto book, forward only (no data look)
- **Content:** inclusion rule, weights and sizing written now, before any joint statistic beyond what the spec
  already shows. Streams: Strategy 20 top-100 tranches (PASSED) and Strategy 19 (UNPROVEN-POSITIVE); card 1 joins
  only if it ends PASSED or UNPROVEN and its correlation with Strategy 20 is below 0.5.
- **Weights:** equal risk from development volatility; means shrunk (PASSED x 0.65, UNPROVEN x 0.4) for sizing;
  account volatility set from card 0's table for the user's chosen pass chance. Optional pre-set sizing rule
  (scout 7 A1): none. A volatility overlay would be a variant fitted on spent data.
- **Judged:** once, on the forward log, with the O'Brien-Fleming boundary already registered (FB-254); additions
  only on fixed dates every 26 weeks; kill as in the strategy specs.
- **Effort:** a spec section + one extra forward file (book = weighted sum of existing forward files); ~2 h Opus.

### Card 6. Hyperliquid: carry and flow replication on a venue with public fills
- **Step A (signal-free audit, free):** from the public API (`info` endpoint: `fundingHistory`, `candleSnapshot`
  with daily candles; no key) count perps and weeks of history; confirm what `asset_ctxs` holds once any S3 file is
  seen. From the docs: fills are in `s3://hl-mainnet-node-data/`, requester pays.
- **Step B (free, only if card 1 is not FALSIFIED):** card 1's frozen rule on Hyperliquid's own funding and daily
  prices, all listed perps, from the first week with 40+ names. A replication: kill at t < 2.0 or net <= 0.
  Power: ~130 weeks, sd ~475-620: t 2 needs ~83-109 bp a week.
- **Step C (needs the user: an AWS account and a few USD of transfer, exact size unknown):** rebuild the 7-day net
  taker flow from fills and run Strategy 20's frozen rule on Hyperliquid's flow and prices. This is the independent
  signal replication the research log found impossible on OKX / Bybit. Kill at t < 2.0.
- **Value:** raises or lowers the confidence in the one survivor before money is committed; no new strategy.
- **Effort:** A 1 h Opus; B 2 h; C 4-6 h Codex after the user's go.

### Card 7. Leveraged single-stock ETF rebalance into the close (new family `letf_single`)
- **Hypothesis:** on days when the required rebalance of 2x / -2x single-stock funds is large against the stock's
  closing volume, the stock continues in the day's direction from 15:30 to the close.
- **Mechanism (who is forced):** the funds must trade L x (L - 1) x assets x day return near the close; the amount
  is known at 15:30. The index version exists and is tiny (H02 / H06) because index funds are small against
  futures volume; single names have a far higher flow-to-volume ratio (UNVERIFIED: to be measured in step 1).
- **Step 1 (signal-free audit):** list the single-stock leveraged funds per underlying; monthly net assets from
  SEC N-PORT filings (free; EDGAR asks automated clients for contact details in the client string: the user decides
  what to send), carried forward daily by the fund's own return; ratio = required flow / dollar volume of the
  stock's 15:30-16:00 bar (Alpaca 30-minute bars). **Go only if at least 300 name-days have a ratio >= 5 %** in the
  development window; otherwise close on size without a look at returns.
- **Trade:** at 15:30, if ratio >= 5 %: follow sign(day return) to the close. Control (reported): same days'
  move size on names without leveraged funds.
- **Cost:** real shares ~2.5 bp per trade; FTMO share CFDs 8-16 bp (so goal 1 only if the effect is >= ~30 bp).
- **Periods (own split, needs the user's go because the mechanism starts after 2021-09):** development from the
  first fund launch to 2024-12-31, test 2025-01-01.., once.
- **Power line:** c ~0.02-0.03. Last-30-minute sd on such days ~90 bp (guess), ~300 date clusters: MDE ~16 bp.
  Pass chance ~10 %.
- **Kills:** net <= 0; t < 3.0 (date clusters); halves not both > 0; doubled costs <= 0; without 2 best days <= 0;
  effect not larger at ratio >= 10 % than at 5-10 % (dose check: a forced flow must scale).
- **Effort:** step 1 ~4 h (the N-PORT pull is the work), screen ~2 h.

### Card 8. Retail positioning collector (FB-284), start now
- **What:** one scheduled daily snapshot of public retail long / short ratios for FX majors, gold and indices,
  appended to a CSV with fetch time. No signal, no look.
- **Why now:** it is the only non-price data that exists for the FTMO symbols, it has no history, and every week
  not stored is lost. A first power line is possible after ~2 years.
- **Needs the user:** which source (terms of use differ; some need an account) and a scheduled task. ~2 h.

### Card 9. Wikipedia page-view attention sort on the wide share universe (new family `share_attention`)
- **Hypothesis:** stocks with abnormal attention this week underperform next week (attention buying is reversed;
  Da, Engelberg, Gao 2011 on search volume: UNVERIFIED, and their sign is up for 2 weeks then reversal, so the
  sign is again the test: two cells, |t| >= 3.3).
- **Signal:** this week's page views of the company's article / mean of the previous 8 weeks (Wikimedia REST API,
  daily from 2015-07, free, point-in-time: scout's claim, not verified by me). Needs a ticker -> article map
  frozen before the look.
- **Universe, trade, cost, periods, kills:** as card 3. **Power:** as card 3; pass chance ~5 %.
- **Run only after cards 2-3:** same harness, one more sort variable. ~3 h incl. the mapping.

## 3. Method changes (proposals only; each line can be accepted or rejected on its own)

| # | Proposal | Exact wording | Effect on existing rows |
|---|---|---|---|
| M1 | Third verdict | Verdicts are FALSIFIED (net <= 0, or the predicted sign is wrong, or gross < cost with the gross 95 % interval below cost), UNPROVEN-POSITIVE (net > 0 at normal costs, same sign in every independent sample, 1.5 <= t < 3.0) and PASSED. | I-71, Gotobi G1, I-76 (at 10 bp), I-84, I-98, I-73 become UNPROVEN-POSITIVE; nothing becomes PASSED |
| M2 | Family closure | Only FALSIFIED rows count toward "two falsifications close a family". | no family reopens for new variants; the wording of closed families changes |
| M3 | Shelf | Every UNPROVEN-POSITIVE row with a tradable venue gets a frozen forward paper log with the FB-254 boundary. No retest on old data. | forward logs for Gotobi G1 and I-71; I-73 has one |
| M4 | Power rule | A card states c = round-trip cost / instrument sd over the hold, and effective name-periods. c > 0.03: closed without a look. Otherwise the card states the pass chance at the family's realised median effect (or the halved published one); below 15 %: PARKED, not closed. | replaces "halved guess vs MDE" for ideas without a published size; the 9 crypto rows closed on 2026-11-15 become PARKED |
| M5 | No unregistered pass statistic | A statistic can pass a gate only if the card named it before the data. | I-73 and I-83 relabelled "test t < 3.0: not confirmed alone; pooled evidence only" |
| M6 | Tail gate (cross-sectional books) | With member returns capped at +-50 % per period the net keeps its sign and at least half its mean. Reported next to it: median period, t on the capped series. | Strategy 20 passes (+78 to +97 of +145-147) |
| M7 | Regime gate | No calendar half below 25 % of the full-period mean. | Strategy 20's development fails it (+327 / +2); it stays alive on its passed test but is sized on the shrunk mean, and the fail is written in the spec |
| M8 | Alpha spending on a test period | Threshold t 3.0 for the 1st-3rd one-time test on a period, 3.3 for the 4th, 3.5 from the 5th. Diagnostics on a spent period are never evidence for a new variant. | crypto 2024+ has 3 uses: card 1 would need 3.3 |
| M9 | Two-sided cards | If the sign is not fixed by a published mechanism, both signs are cells and the threshold is 3.3. | cards 3 and 9 |
| M10 | Shrunk reporting | Every PASSED row is reported with a forward estimate = measured mean x 0.65 (x 0.4 for UNPROVEN) until its forward log has 52 weeks. | Strategy 20: +92 "fair" -> ~+60 to +90 planning range |
| M11 | Signal stop | K = 10 is reached: no new signal screens on the 34 FTMO CFDs until a new venue fact or a new non-price data set for them exists. | goal-1 work = shelf logs and card 8 only |
| M12 | Harvest target | Scouts and harvest batches search for data sets (free, 100+ names, non-price, 3+ years), not strategies. | idea-harvest task templates |
| M13 | Venue scope | Real US shares (long-short, own account or a share prop firm) are a research venue under goal 2, with their own family labels and cost model. | enables cards 2-4, 7, 9 |

## 4. First-week plan

Budget: ~2 h of Codex high effort per 5 h window; Opus coordinates, writes cards and runs small scripts inline.
One research loop at a time; no commits while a write dispatch runs.

| Day | Opus (inline) | Codex window | Needs the user |
|---|---|---|---|
| 1 | Card 0 (audit). Pre-register cards 1 and 5. Put section 3 into HANDOFF > Open as a line-by-line list | Card 1 screen (terra, ~1.5 h) | accept / reject M1-M13; real shares as a venue (M13) |
| 2 | Card 1 verdict, ledger, family closed. Card 5 spec + forward file. Card 6 step A (API audit) | Card 2: downloader extension + audit script (test first), start the background download | pick the source for card 8; AWS account yes / no for card 6 step C |
| 3 | Card 2 audit result: freeze the universe rule; pre-register card 3 (both signs) | Card 3: FINRA downloader + screen | none |
| 4 | Card 3 verdict. Pre-register card 4. Card 6 step B if card 1 was not falsified | Card 4 screen | none |
| 5 | Card 4 verdict. Card 7 step 1 design (fund list, N-PORT pull) | Card 7 step 1 audit | the split for card 7; what contact string EDGAR may get |
| 6-7 | Card 7 go / no-go on flow size; card 9 mapping if cards 3-4 left the harness in place; week report with all verdicts and the shelf | Card 7 screen or card 9 | Strategy 20 prop decision stays open; card 0's numbers go into that package |

Order logic: owned data first (cards 0, 1, 5), then the one download that unlocks four cards (card 2), then
non-price before price (card 3 before 4). If card 2 shows no delisted names, cards 3-4 still run but can end at
most UNPROVEN. If the user rejects M13, days 2-7 shrink to cards 6 and 8 and the long-range list starts early.
Expected yield of the week, honestly: about 0.4 new PASSED streams (20 % + 8 % + 8 % + 10 % + 5 %, not independent),
a firm answer on whether carry is a second stream, and a decision-grade picture of Strategy 20.

## 5. Long-range directions (after this week)

| # | Direction | Why it follows from the model | First step |
|---|---|---|---|
| 1 | Let the forward logs decide | The only clean test left for Strategy 20 and the book is time; power by week 104 is 20-34 % | Monthly update from 2026-12-02; never change a frozen book after a good or bad run |
| 2 | Independent flow replication whenever fills become cheap | The survivor rests on one exchange's taker field | Card 6 step C; re-check OKX / Bybit archives once a year |
| 3 | Wide US shares, weekly horizon, more free non-price sorts | c ~0.01 and 1,000 names; the scarce input is data nobody sorts | SEC fails-to-deliver (twice monthly), short interest (twice monthly), Form 4 buys in small and mid caps, each as one two-sided card |
| 4 | Mid-cap segment of the share universe (ranks 500-2,000) | P4: large caps are worked by funds; I-96 faded there | Rerun any card that ends UNPROVEN on ranks 1,001-2,000 as its one pre-registered second cell |
| 5 | Open-interest and positioning sorts on perps | Same data type as the survivor; today underpowered (104 weeks) | Re-card in 2027 when 250+ weeks exist; until then PARKED |
| 6 | Turnover control for Strategy 20 (rank buffer) | I-82: the daily and weekly gross are the same edge per day, so cost is the lever | Frozen forward variant only; never fitted on spent data |
| 7 | Hyperliquid positions by address | The purest "who must trade" data: liquidation prices are known in advance | After card 6: signal-free count of liquidatable notional near price per coin-day |
| 8 | Leveraged single-stock products as they grow | A forced flow that scales with assets and is new each year | Repeat card 7's flow-size audit yearly even if it is a no-go now |
| 9 | Exchange futures: trend + carry + commodity basis-momentum | Documented over decades; c fine; needs 20+ markets and own capital, not a prop account (Sharpe ~0.5 means ~7 years to pass) | One bought daily data set, then Carver's fixed rule set once; the user's money decision |
| 10 | Free curve data that exists today | EIA energy strips (1980s+), Cboe VIX futures per contract: enough for a term-structure study, not for a portfolio | Data audit only, when item 9 is decided |
| 11 | Retail positioning on FTMO symbols | The only non-price data for goal 1 | Card 8 now; first power line in late 2028 |
| 12 | Crypto prop terms watch | The binding risks are rule changes and payout practice, not the edge | Re-read both firms' rules before any fee and every quarter |
| 13 | The combination as the product | A prop pass is a Sharpe target (~1.65 / Sharpe^2 years); only independent streams move it | Add a stream to the book only at 26-week dates and only PASSED or UNPROVEN ones |
| 14 | Keep the ledger as the asset | 189 rows are a calibrated prior: IC 0.03-0.07 for real effects, zero for patterns | Add c, name-periods and the three-verdict label as columns; refit the shrink factors yearly |
| 15 | What not to reopen | Price or clock signals on the 34 CFDs, crypto faster than ~3 days, single-instrument timing with macro or sentiment series, events rarer than weekly | A new idea in these cells needs a new data set or a new venue fact first |

## 6. Not verified

- Scout effect sizes and quotes (snippets); all published sizes I quote from memory.
- Alpaca: delisted-name coverage, free access to the auctions endpoint, an inactive-assets listing, quote history.
- Hyperliquid: depth of fills history, `asset_ctxs` fields, the API's candle depth, actual S3 transfer cost.
- OKX / Bybit official trade archives; Wikimedia API depth; SEC N-PORT coverage of the leveraged funds; first
  launch date of single-stock leveraged funds.
- FINRA: I confirmed file existence for five dates and the field layout, not completeness across facilities or the
  true first date (earlier than 2012-01 is possible).
- Every sd, cost and pass chance in the cards is a guess to be replaced by the card's own signal-free power line
  before the look. I-99's result is still not in the repo.
