# Crypto (BTC/ETH) intraday, time-of-day, funding and event effects: literature notes

Date: 2026-11-09. Scope: published or working-paper evidence on intraday effects in BTC and ETH.
Status labels: OPENED-FULL (full text read, via pdftotext or fetch), OPENED-ABSTRACT (abstract or
repository page only), NOT-OPENED (known only from search snippets or secondary summaries).
No numbers below are invented; "n/r" means the source did not report it or I did not extract it.
Note: all page/table references are to the accepted-manuscript PDFs I read, not the journal pagination.

## Bottom line

1. No peer-reviewed paper I could open documents an after-cost, stop-defined same-day BTC/ETH rule
   that survives 8-10 bp round-trip taker cost plus slippage. Every opened paper either ignores
   costs, or reports break-even costs below Binance taker cost.
2. The best-evidenced facts are about volatility/volume/liquidity timing (Hansen-Kim-Kimbrough:
   spikes at 00:00 and 16:00 UTC, smaller at 08:00 UTC), not signed returns. Those help with
   stop sizing, slippage timing and filter design, not direction.
3. Directional candidates that are testable on our own data, in order: (a) 1h/2h/4h reversal after
   large moves (De Nicola 2021, abstract only), (b) first-to-last-half-hour intraday momentum on a
   futures-defined clock (Shen et al. 2022, gross 3-10 bp, too thin unlevered), (c) 21:00-23:00 UTC
   long (Quantpedia blog, not peer reviewed, no costs). All three need our own out-of-sample test on
   2020-2026 Binance M1 data; none is a result we can quote as profitable.

## Source register

| # | Source | Status | Note |
|---|---|---|---|
| S1 | Shen, Urquhart, Wang (2022), "Bitcoin intraday time-series momentum", Financial Review 57(2), 319-344; accepted manuscript R2 (Reading CentAUR 100181) | OPENED-FULL | Tables 3, 5, 6, 8 read |
| S2 | Wen, Bouri, Xu, Zhao (2022), NAJEF 62, 101733 | OPENED-ABSTRACT (IDEAS/RePEc page; ScienceDirect 403) | No numbers available to me |
| S3 | Bouri, Lau, Saeed, Wang, Zhao (2021), "On the intraday return curves of Bitcoin", IRFA 76, 101784; accepted manuscript (Kent KAR 93919) | OPENED-FULL | Tables 4, A3 read |
| S4 | Hansen, Kim, Kimbrough (2021), "Periodicity in Cryptocurrency Volatility and Liquidity", arXiv 2109.12142v2 | OPENED-FULL (text extracted, sections 5-6 read) | Volatility/volume, not returns |
| S5 | Benigno, Rosa (2023), "The Bitcoin-Macro Disconnect", NY Fed Staff Report 1052 | OPENED-FULL (intro, data, Table 8 area) | Event study 2017-2022 |
| S6 | Ben Omrane, Dabbou, Saadi, Savaser, Sebai (2025), IREF 103 (IDEAS 2025 listing) | OPENED-ABSTRACT | 5-min BTC/ETH 2016-2023 volatility around releases |
| S7 | He, Manela, Ross, von Wachter (2024), "Fundamentals of Perpetual Futures", arXiv 2212.06888v5 | OPENED-ABSTRACT (full text downloaded, searched for predictability only) | Basis arbitrage, not intraday direction |
| S8 | De Nicola (2021), "On the Intraday Behavior of Bitcoin", Ledger 6, 58-80 | OPENED-ABSTRACT (LMU repository page) | 1h/2h/4h negative autocorrelation |
| S9 | Caporale, Plastun (2018/2019), "Price overreactions in the cryptocurrency market", Brunel WP 18-01 | OPENED-FULL | DAILY data 2013-2017, trading robot with costs |
| S10 | Quantpedia, "Are There Seasonal Intraday or Overnight Anomalies in Bitcoin?" (blog) | OPENED-FULL (blog) | Not peer reviewed; no costs |
| S11 | Eross, McGroarty, Urquhart, Wolfe (2019), "The intraday dynamics of bitcoin", RIBAF 49, 71-81 | OPENED-ABSTRACT (via search metadata only) | Volatility/liquidity by hour |
| S12 | Substack summary of a CoinDesk-intraday 2015-2025 macro-announcement paper | NOT-OPENED (underlying paper not identified) | Do not cite |
| S13 | Müller (2024), "Revisiting seasonality in cryptocurrencies" (day-of-week) | NOT-OPENED | Search snippet only |
| S14 | Caporale-Plastun, Aharon-Qadan, Ma-Tanizaki etc. day-of-week papers | NOT-OPENED | Search snippets only |
| S15 | K33, Presto Labs, Brave New Coin funding-rate notes | NOT-OPENED | Industry notes, snippets only |
| S16 | CME Group article on 24/7 crypto; trader blogs on CME-gap fill rates; Ledger note that CME went 24/7 on 2026-05-29 | NOT-OPENED | Claims unverified |
| S17 | Lim (JFDA) and Hyperliquid preprint on the 2025-10-10 cascade | NOT-OPENED (snippets) | Liquidity recovery, not price direction |

## 1. Time-of-day and day-of-week

### 1a. Long 21:00 -> 23:00 UTC (S10, Quantpedia, OPENED-FULL, blog)
- Rule: buy BTC at 21:00 UTC, sell at 23:00 UTC, every day.
- Sample: hourly Gemini data, "9.10.2015 - 3.2.2022" (date format ambiguous).
- Reported: 33% annualised, 20.93% annualised vol, max drawdown -22.45%. Sharpe not reported.
  Costs not discussed. No academic citation; the blog says the strategy had a drawdown in 2022-2023.
- Gross per trade: not reported. Back-of-envelope only: 33%/365 is about 9 bp per day if the
  return were earned uniformly over days, which is about the Binance round-trip cost
  (8-10 bp) before slippage. Treat as my arithmetic, not a source number.
- Trades/year: about 365. Post-publication: the blog's own update notes weakness 2022-2023.
- Data needed: BTC/ETH M1 or H1, UTC clock only. Our Binance data covers it.
- Verdict: unproven; the sizing says costs eat essentially all of it. Note US DST: US equities
  close 20:00/21:00 UTC, so the window is just after the US cash close.

### 1b. Hour-of-day volatility and volume structure (S4, OPENED-FULL)
- Volume and volatility spike at 00:00 UTC and 16:00 UTC, less so at 08:00 UTC, on Coinbase Pro,
  Binance and Uniswap, BTC and ETH, "nearly identical patterns in different calendar years"
  (section 5.2 and Appendix A). Detailed sample 2020-10-01 to 2021-06-01.
- Within the hour: first minute has most volatility, peaks every 15 min, smaller every 5 min,
  strongest at 00h, 04h, 12h, 16h, 20h but not 08h (section 6). Authors tie this to perpetual
  funding (Binance 00/08/16 UTC, BitMEX 04/12/20, FTX hourly) as a conjecture.
- Lowest volatility/volume roughly 5-12 UTC (North American night). Volatility on Monday's first
  hour is particularly high.
- Use: size stops and expect wider spreads/slippage at 00:00 and 16:00 UTC; schedule entries
  away from the first minutes after those times. No return direction is claimed.

### 1c. Day-of-week / weekend
- S13/S14: NOT-OPENED. Search snippets say a Monday effect was found in older samples (to 2018),
  but one 2024 paper reports it does not persist after 2015 and that weekends mostly show lower
  activity, not return anomalies. Treat as dead until opened and tested on our data.
- Weekend CFD note: FTMO CFDs close/gap on weekends, so a Binance weekend edge may not transfer.

## 2. Funding-rate settlement (00:00, 08:00, 16:00 UTC)

- Price drift into/out of funding: I found no peer-reviewed paper that tests signed returns
  around Binance settlement times. S4 documents volatility/volume spikes at 00/16 (and weaker 08),
  only as a microstructure fact.
- Funding level as predictor: S7 (OPENED-ABSTRACT) is about basis/no-arbitrage; its strategy is
  delta-neutral and does not predict spot direction. The funding-level predictor claims are all
  industry notes (K33: negative 30-day funding then 90-day returns positive, six episodes since
  2018, no significance test; Presto: near-zero correlation between funding changes at T and
  price changes at T+1). All NOT-OPENED, snippet only. Horizon is days to months, not same-day.
- What we can test ourselves (data in binance_funding): sign of the last settled funding rate
  and the extreme-funding percentile versus the next 1-8 h return; return in the 30 min before
  and after 00/08/16 UTC. This is a pure hypothesis; no published effect size exists to compare to.

## 3. Intraday momentum and reversal

### 3a. First-half-hour predicts last-half-hour (S1, OPENED-FULL)
- Data: tick data from Bitfinex, Bitstamp, CEX.IO, Coinbase, Kraken aggregated to 1 min, from the
  earliest date to 2020-12-31 (Bitstamp 2011-2012 dropped). 3,375 trading days in the full sample.
- Clock: opening time chosen per exchange at the volume spike (exact UTC per exchange is in the
  paper's Table 1; I did not extract it); close fixed at 5pm EST (22:00 UTC in winter, 21:00 UTC
  in summer), when the CME Bitcoin futures 60 min break begins. First half-hour return =
  price 30 min after open / previous day close - 1. Last half-hour return is the final 30 min before 5pm EST.
- In-sample (Table 3): slope 0.968, Newey-West t 4.38, R2 1.44%; second-to-last half-hour has
  negative slope (anti-persistence); both together R2 2.12%. Out-of-sample R2 for first half-hour only about 1.09%,
  second-to-last 1.40% (section 3.2, Table 3).
- Strategy (Table 5): timing on first half-hour: 7.82% p.a.; on second-to-last: 17.32%; combined:
  16.69%; always-long on the same half-hours 6.54%.
- Gross profit per trade, unlevered (Table 8, full sample, 3,375 days): 2.8 bp, 6.1 bp, and 9.6 bp
  (combined signal; 1,465 trading days). Break-even costs 3, 7, 10 bp. Always-long: 2.0 bp.
- Cost survival: the paper itself concludes the unlevered strategies are NOT profitable at 25 bp
  Bitstamp fees; they work only with 10:1 leverage per its break-even logic. Against Binance taker
  4-5 bp per side (8-10 bp round trip), only the combined signal is at break-even in the full sample,
  so effectively zero net edge. Sample is dominated by 2013-2017 and by exchange-specific clocks.
- Trades/year: up to 365 (combined signal 1,465 days / about 9.25 years, about 160/yr).
- Post-publication status: published 2022, tested only to 2020; no post-2020 replication found.
- Data needed: M1 Binance (we have it) but their clock was spot-exchange volume spikes; for ours,
  use a fixed UTC window and test the sensitivity.

### 3b. Wen, Bouri, Xu, Zhao 2022 (S2, OPENED-ABSTRACT)
- Sample 2013-03-03 to 2020-05-31 high-frequency BTC; ETH, LTC, XRP similar. Both intraday momentum
  and reversal; reversal attributed to overreaction, momentum to late-informed investors; patterns shift
  with large jumps, FOMC release days, liquidity, and COVID. Market timing beats always-long and
  buy-and-hold. No effect sizes obtained; cost treatment unknown. Not usable until the full text is read.

### 3c. Functional-curve timing (S3, OPENED-FULL)
- Bitstamp 5-min data, 2014-11-01 to 2019-08-10 (1,367 days). Forecast cumulative intraday return curve,
  buy at predicted minimum, sell at predicted maximum (long only, no short-selling).
- Table 4: best (FPAR, window 182) 64.70% p.a., vol 58.15%, Sharpe 1.11, max DD -99.25% (log-return basis).
  Gross per trade: n/r. Costs: main results without costs; appendix (Table A3) with 0.03% fee gives
  Sharpe 0.74. Window 365 gives Sharpe 0.83 (without fees); the subsample where both scores are serially correlated shows
  negative returns. Sensitive to the training window. Spread and slippage ignored.
- Verdict: not a stop-defined rule; discard as an implementable candidate.

### 3d. Short-horizon reversal (S8 abstract; S9 full text)
- S8: negative first-order autocorrelation of 1h, 2h, 4h BTC returns; bigger moves, bigger reversals;
  explanation: overreaction and leverage liquidation cascades. Sample, effect size and costs n/r
  (abstract only; full text not available at the repository). A simple strategy was tested retroactively, no numbers.
- S9 (daily data, 2013-04-28 to 2017-12-31): counter-movement strategy after overreaction days is
  not profitable in a trading-robot test with spread/fees; inertia strategy profitable but statistically
  indistinguishable from random. It is daily data and old; only a warning that "statistically
  present" reversal does not equal "profitable after costs".
- Testable here: after a 1h/2h/4h move larger than k x rolling ATR, fade for the next 1-4 h with a
  stop at 1 ATR. Predicted gross unknown; must be tested on 2020-2026 M1.

## 4. US macro releases and CME gap

### 4a. CPI, FOMC (S5 OPENED-FULL, S6 OPENED-ABSTRACT, S12 NOT-OPENED)
- S5: 30-minute windows [t-5, t+25 min], 2017-2022. BTC is "orthogonal" to monetary policy
  (Target/Path/LSAP) and macro news except CPI, where the CPI coefficient is significant in the full
  sample; footnote 6 says that restricted to 2017-2021 the CPI coefficient is no longer significant
  (read from the text excerpt; the table value with asterisks for CPI ex food and energy was shown as -0.04***/-0.02** in a
  results table, I did not map which asset/window). The conclusion is a sign-based reaction to CPI
  surprise is weak and not stable. Mean and surprise-direction effect sizes in bp: n/r by me.
- S6: 5-min BTC/ETH 2016-2023; volatility responds to US monetary policy news in all phases
  (before, during, after), stronger during the pandemic; ETH reacts more than BTC. Direction not claimed.
- S12 (not opened): claims systematic reactions since 2020 and larger ETH reactions. Unverified.
- Use: a straddle-free same-day approach would be a volatility-event trade, not a directional edge.
  CPI at 13:30 UTC (12:30 UTC in US-DST mismatch weeks), FOMC at 18:00/19:00 UTC. Surprise sign needs
  consensus data we may not have (check news_clean contents).
- Cost caution: spread and slippage widen at releases; FTMO CFD slippage (about 5x model) is worst here.

### 4b. CME Sunday gap (S16, NOT-OPENED)
- Only trader blogs (claims 75-98% fill rates, unsourced methods). No academic paper found.
  A search result says CME moved to 24/7 crypto futures on 2026-05-29, which would end the gap
  (unverified; check CME's own notice before any test). Treat as dead until a primary source says otherwise.

## 5. Liquidation cascades and large-move reversal

- No paper opened tests signed returns after cascades. S17 (NOT-OPENED): 2025-10-10 cascade
  studied for liquidity recovery on Hyperliquid, not for a tradable reversal; a single event is not a sample.
- Related evidence: S8 and S9 above. Our binance_flow data (check what columns it holds, for example
  liquidation or taker-flow fields) could define a cascade filter locally; no published benchmark exists.
- Risk: entering against a cascade means wide slippage on CFDs and stop-run risk. Weak candidate for FTMO.

## Status table

| Effect | Best evidence | Gross per trade | Trades/yr | Beats 8-10 bp RT? | Status |
|---|---|---|---|---|---|
| 21-23 UTC long | blog, 2015-2022 | about 9 bp (my arithmetic) | 365 | No (roughly even before slippage) | unproven |
| First-30-min -> last-30-min | S1, to 2020 | 2.8 / 6.1 / 9.6 bp (Table 8) | 160-365 | No (paper says not profitable without leverage) | weak, thin |
| Hour-of-day vol spikes (00/16/08 UTC) | S4 | n/a (no direction) | n/a | n/a | usable as filter |
| Funding-time drift | none | n/a | n/a | n/a | no published effect |
| Funding level predictor | industry notes | n/a | n/a | n/a | not opened, multi-week horizon |
| 1-4 h reversal after big moves | S8 abstract, S9 daily | n/r | n/r | unknown | testable, plausible |
| CPI/FOMC direction | S5, S6 | n/r (30-min betas) | about 20-25 | unknown | mostly disconnected; weak |
| CME gap | blogs | n/a | about 52 | n/a | likely dead (24/7 CME since 2026-05, unverified) |
| Day-of-week | snippets | n/a | n/a | n/a | dead on later samples (unopened) |

## Suggested next steps (not run)
1. Open full text of S2 (Wen et al.) via institutional access; extract the jump-conditional and
   FOMC-day tables.
2. On our Binance BTCUSDT/ETHUSDT M1 data, 2020-2026, test with the fixed development/test split:
   (i) 1-4 h fade after > k ATR moves, (ii) first/last 30 min on a fixed UTC clock, (iii) 21-23 UTC.
   Compare gross bp per trade with 9 bp Binance cost and with the FTMO live-fill cost (5x model slippage).
3. Check CME's own notice on the 24/7 launch before spending time on gap tests.
