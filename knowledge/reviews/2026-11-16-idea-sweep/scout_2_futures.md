# Scout 2: exchange futures structure (2026-11-16)

Scope: ~20 min web scan, standard-mode search snippets only (no full-paper reads). Effect sizes not seen in a snippet are marked UNVERIFIED. Ledger rows already covering this domain: P01 (WTI-Brent spread, killed on swap), I68 (oil carry, closed on power), I69 (BTC CME expiry week, killed), FB263 (futures re-cost of intraday index rows, closed), HV-T0007/0029/0037/0106 (Goldman roll / roll-spread / heating oil roll, "verified, not runnable" or untestable), HV-T0067/0083 (VIX backwardation, unfetchable). Nothing in the ledger tests a futures-curve strategy on real futures prices.

Common blocker: every direction below needs per-contract or at least 2-contract futures history. We own none (only CFD proxies, which carry swap and no curve). Free data is therefore the gate (see table at the end).

## Directions

### 1. Natural gas EIA-storage announcement-day premium (and pre-announcement drift)
- Mechanism: weekly EIA Thursday 10:30 ET report; hedgers/market makers demand compensation for event risk, informed pre-positioning starts ~90 min before release.
- Venue/symbols: NYMEX NG (Henry Hub); FTMO proxy NATGAS (owned, M1 from ~2019-20).
- Horizon: intraday to 1 day, ~52 events/yr.
- Data: NATGAS M1 OWNED (proxy, CFD spread/swap apply); NG futures daily FREE via EIA (front 4 contracts, see table).
- Published effect: "more than 50% of the annual return is earned on these days" (Prokopczuk, Wese Simen, Wichmann, Energy Journal 42(2), 2021); abstract also says a simple strategy is profitable after costs (size UNVERIFIED). Surprise sensitivity: 1% inventory surprise ~ -1% price (Gay, Simkins, Turac 2009). Pre-announcement drift from 9:00 ET (Kurov et al.).
- Source: https://centaur.reading.ac.uk/90003/1/NG_paper_final_round.pdf ; quote: "more than 50% of the annual return" (secondary summary of the search result, UNVERIFIED verbatim in the PDF). Drift: https://clsbluesky.law.columbia.edu/2016/09/15/what-drives-informed-trading-before-public-releases/
- Vs ledger: the ledger closed EIA (oil) on power, a few events. NG storage is 52/yr x 15+ years = ~800 events, so power is not the problem. Different from all closed event rows.
- Capacity: small (NG intraday, one product); funds trade around it but the premium is a risk-bearing payment, not an arb. Gross may exceed the NATGAS spread; swap is irrelevant for intraday holds.
- Prior survives costs: 20%.

### 2. Treasury month-end index extension (futures drift into month end)
- Mechanism: Bloomberg US Aggregate (and Treasury) indices extend duration at month end by adding new issues; index trackers must buy duration just before month end, temporary price pressure.
- Venue/symbols: CBOT ZN/ZB/ZF/UB (US futures); no FTMO bond CFD in our list (not available as proxy).
- Horizon: last 3-5 trading days of month, 12 events/yr x 30 yrs.
- Data: ZN daily continuous PAID/FREE-partial (see table; Yahoo ZN=F UNVERIFIED depth); needs no per-contract data if the roll is handled.
- Published effect: Hartley and Schwarz, "Predictable End-of-Month Treasury Returns" (1990-2018), spillover to Treasury futures and swaps; size UNVERIFIED in snippets. Practitioner extension table (US Agg +0.08 yrs) at itcmarkets.com.
- Source: https://www.fedinprint.org/item/fedawp/13394/original ; quote: "The end-of-month effect is persistent over our sample period"
- Vs ledger: closed rows are FOMC/auctions (few events) and CFD turn-of-month on equities (I think killed on t<3). This is bonds, 360 monthly events, index-rule driven.
- Capacity: large and well known to rates desks; expected gross a few bp per month in yield terms, ZN costs ~0.2 bp so costs are not the wall, signal-to-noise is (monthly sd of ZN is large vs effect, power likely bad: 360 obs, t 3 needs ~ 0.16 sd/event).
- Prior: 8%.

### 3. Goldman / S&P GSCI roll-window front-running (roll days 5-9 business day)
- Mechanism: ~$100bn+ of index-linked money must sell nearby and buy next contract on fixed business days 5-9; front-runners (Mou) sell nearby / buy deferred ahead and unwind on roll days; calendar-spread pressure in CL, NG, HO, RB, grains, metals.
- Venue: NYMEX/CBOT/COMEX calendar spreads (front vs second); CFD proxy none (CFDs roll with their own rule; USOIL/UKOIL/NATGAS spread is not tradable on FTMO).
- Horizon: 5 days a month, 12/yr per commodity x ~20 commodities.
- Data: front and second contract settlements: PAID for most commodities; FREE for energy via EIA contracts 1-4 (CL, HO, RBOB 2005+, NG).
- Published effect: Mou (2010): investors forwent "3.6% annual return" through price impact of the roll; spreads profit pre-roll. Counter-evidence: Marechal (2021) "A tale of two premiums revisited" finds no significant systematic roll-day effect; Dubois and Marechal working paper reports sign varying by sub-period (1999-2003 vs 2004-2010).
- Source: https://papers.ssrn.com/abstract=1716841 ; quote: "forwent 3.6% annual return" (abstract wording, paraphrased from search result; UNVERIFIED verbatim).
- Vs ledger: HV-T0007 "Goldman Roll Spread Pressure" is "verified, not runnable" (no data). This proposes the EIA free contract strip as the data fix.
- Capacity: the effect was arbitraged post-2010 (Mou implies spreads were taken), later null. Funds with low costs did take it. Prior low.
- Prior: 7%.

### 4. Cross-sectional commodity carry / basis-momentum (term-structure sort)
- Mechanism: backwardated commodities earn a convenience-yield/hedging premium; basis-momentum captures hedger funding / inventory pressure.
- Venue: ~20 liquid commodity futures (CME, ICE, COMEX); CFD proxy only for XAU, XAG, USOIL, UKOIL, NATGAS (5 names, too few for a cross-section).
- Horizon: monthly rebalance.
- Data: PAID for the full universe (Stevens/Quandl SCF gone, see table); FREE: EIA energy 4 contracts, CFTC irrelevant.
- Published effect: basis-momentum Sharpe 0.55-0.85 (Boons and Porras Prado, J. Finance 74(1), 2019, from 1959); carry SR ~0.6 and momentum 0.72 in a curve-momentum paper's own sample (snippet only).
- Source: https://ideas.repec.org/a/bla/jfinan/v74y2019i1p239-279.html ; quote: UNVERIFIED (no verbatim line retrieved).
- Vs ledger: I68 oil carry was closed on power for ONE commodity (monthly sd 12.5%). A cross-section across ~20 commodities is a different test and mirrors what survived in crypto (XS weekly flow sorts).
- Capacity: well-known factor, Sharpe decayed post-2010; costs 0.2 bp are not the issue, the data is. Cannot trade on FTMO. Goal-2 only.
- Prior: 12% (data hard, edge decayed).

### 5. Seasonal grains: corn new-crop weather premium (June-July)
- Mechanism: weather risk premium hedgers pay before pollination; Dec corn seasonal high into June/July then harvest decline.
- Venue: CBOT ZC Dec (no FTMO grain CFD in the owned list).
- Horizon: ~6-8 weeks, 1 trade/yr per crop (too few events: power problem).
- Data: daily Dec corn: Yahoo ZC=F rolled series / PAID per-contract; FREE USDA none for prices.
- Published effect: farmdoc: new-crop corn average seasonal peak "about 12% above the harvest-time price in early June" (all-year average, since 2000; gross, no costs); new-crop soybeans only ~4% (July peak vs Nov 1), i.e. nothing exploitable.
- Source: https://farmdocdaily.illinois.edu/2021/06/the-absence-of-a-weather-risk-premium-in-new-crop-soybean-futures-prices.html ; quote: "small, but economically significant weather risk premium in new-crop corn" (paraphrase from search result).
- Vs ledger: seasonality rows killed on t < 3. This one has a physical reason but ~25 independent years: t 3 needs a huge Sharpe. Probably closed on power.
- Prior: 5%.

### 6. Seasonal processing spreads (crack/crush) and calendar spreads
- Mechanism: refiner and crusher margins follow physical demand seasons (gasoline summer, heating oil winter, soy crush); hedgers lock margins.
- Venue: NYMEX CL/HO/RB (3-2-1 crack), CBOT ZS/ZM/ZL (crush). FTMO proxy: none (no HO/RB/product CFDs).
- Horizon: weeks to months, few trades/yr.
- Data: EIA free contract 1 for CL/HO/RBOB (RBOB 2005+) enough for a 3-2-1 crack. Grains PAID.
- Published effect: Cole, Kastens, Hampel and Gow (1999): seasonal buy-and-hold on four processing spreads "generally did not" beat zero; only cattle crush significant. Girma and Paulson reported significant profits in petroleum crack spreads (sample UNVERIFIED). A Czech 2016 thesis: calendar-spread seasonality failed out of sample.
- Source: https://ageconsearch.umn.edu/record/285759/files/confp14-99.pdf (UNVERIFIED which of the cited works the file is); quote none verbatim.
- Vs ledger: P01 (WTI-Brent) killed on swap + sign; this is a futures-native spread with no swap, but evidence is mostly negative.
- Prior: 5%.

### 7. Equity index futures quarterly roll mispricing (ES, NQ, FDAX, Mini-TOPIX)
- Mechanism: ~2-3 weeks before IMM expiry, institutions roll via calendar spreads; the spread can trade away from fair value (S&P/TSX 60 roll traded at average discount of "over 80bps" in H20/M20 per Montreal Exchange; selling pressure).
- Venue: CME ES/NQ, Eurex FESX/FDAX, Montreal SXF.
- Horizon: 4 events/yr (mostly dead: power), per index. The position is a calendar spread, so market-neutral.
- Data: needs two contracts: PAID. CME rolls free only as daily current.
- Published effect: UNVERIFIED size for ES (only the SXF 80 bp discount at the exchange doc and a Sydney finding that mispricing spikes before rollover).
- Source: https://www.m-x.ca/f_publications_en/sxf_h20_m20_roll_update_en.pdf ; quote: "over 80bps" (discount to fair value, Mar20/Jun20 SXF)
- Vs ledger: FB263 re-costed intraday index; this is a basis/roll trade, not price pattern. Not in ledger.
- Capacity: explicitly the arbitrage desks' business (basis, sec-lending), spread already tight on ES; SXF is thin (maybe still wide but retail cannot size it and is not on FTMO).
- Prior: 3%.

### 8. VIX futures term structure (short front when contango, flat/long on backwardation)
- Mechanism: VIX futures roll down to spot in contango, paid as insurance premium by hedgers; backwardation signals stress.
- Venue: CFE VX (continuous), ETPs VXX/SVXY are not futures but proxy; FTMO has no VIX CFD in the owned list.
- Horizon: daily to weekly signal.
- Data: Cboe per-contract CSV (OHLC, FREE) via cboe.com historical data, from 2004; settlement archive free.
- Published effect: strategy of shorting in contango reported 69% annualised unhedged, late 2006 - Apr 2014 including simulated pre-inception data (one study, gross); roll-down is the largest negative contributor to long VIX returns (U Minn thesis).
- Source: https://arxiv.org/pdf/2103.02016 (Trading Signals in VIX Futures) ; quote: UNVERIFIED. Data: https://www.cboe.com/us/futures/market_statistics/historical_data/
- Vs ledger: HV-T0067/T0083 (VIX backwardation and S&P) "unfetchable": data never seen. Cboe free CSVs fix the data. Also covered by: SqueezeMetrics DIX/GEX owned.
- Capacity: crowded since 2012-2018, left-tail blow-up (Feb 2018); realistic edge is gone or volatility-targeted only; t >= 3 on the tail-heavy series unlikely.
- Prior: 8%.

### 9. CFTC COT hedging pressure / speculator positioning as a time-series signal
- Mechanism: hedgers pay a premium to speculators; extreme net commercial positions in a commodity forecast returns.
- Venue: any futures with CFTC reports; CFD proxy: XAUUSD, XAGUSD, USOIL, NATGAS, FX (Euro, Yen via EURUSD, USDJPY), US500/NAS100.
- Horizon: weekly (Tuesday data, Friday release). Test: trade Monday open after Friday release.
- Data: CFTC historical compressed files FREE (legacy back to 1986; disaggregated from 2006); price proxies OWNED (M1 CFDs).
- Published effect: Bessembinder 1992 positive; Rouwenhorst and Tang review 1986-2010: "minimal" premiums; Lehecka 2013 (2006-11) no lead-lag. Mixed. Weekly positions predict return when hedgers face funding constraints (NBER conf paper).
- Source: https://www.cxoadvisory.com/?p=21053 ; quote: UNVERIFIED
- Vs ledger: the crypto positioning row FB-006 was closed on power for 104 weeks; COT gives 15-35 years x ~25 markets, so power is fine. Not in ledger as COT.
- Capacity: public data since 1986, weak result, but with a swap-free horizon (weekly hold of the CFD costs swap, cost wall again: check weekly CFD swap on XAU/oil).
- Prior: 7%.

### 10. Basis futures vs CFD/spot (FTMO CFD roll-date dislocation)
- Mechanism: FTMO index/oil CFDs mimic front futures and roll on a broker schedule; around the broker's own roll, CFD price jumps by the calendar spread and CFD "swap" may be adjusted to compensate. If the swap adjustment is mis-sized relative to the real spread, there is a deterministic edge on one side.
- Venue: FTMO USOIL, UKOIL, NATGAS, US500/NAS100/US30, GER40 vs CME/ICE/Eurex futures.
- Horizon: a few days around each roll; ~12 (oil/gas) or 4 (indices) per year per symbol.
- Data: CFD M1 OWNED; spread table OWNED; futures counterpart: EIA contracts 1-2 FREE for oil/gas; index futures PAID (but index fair value can be computed with owned index data).
- Published effect: none (no paper); this is a data-observation idea. Verify with feed_compare tool (exists in repo). UNVERIFIED that it exists.
- Source: none. Related: https://www.cmegroup.com/trading/equity-index/fairvaluefaq.html
- Vs ledger: not covered. Combines the oil-carry finding (I68 closed on power: the swap IS the carry) with owned data.
- Capacity: broker-specific, tiny; FTMO could change rules/roll dates at any time (and ToS risk on arbitrage-like trading in prop firms: ask the user).
- Prior: 10% (high variance, because nobody has measured it).

## Free daily futures data: what you really get

| Source | What it gives | Limits (verified/not) |
|---|---|---|
| EIA (eia.gov/dnav pet_pri_fut, ng_pri_fut) | Daily NYMEX settlement for Contract 1-4: crude (from 1983), heating oil (1980), RBOB (2005+), Henry Hub NG (Contracts 1-4) | Floor close 2:30 pm ET, not settlement; petroleum table notes no data after Apr 5, 2024 in cached copy (UNVERIFIED current); rolling "contract N", not individual expiries; energy only |
| Cboe VIX futures (cboe.com/us/futures/market_statistics/historical_data) | Per-contract CSV: trade date, contract month, OHLC; last row = final settlement; VX and VXT | OHLC not settlement price; no volume/OI confirmed; VIX only; from 2004 (UNVERIFIED start) |
| CFTC COT historical compressed (cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed) | Weekly positions: legacy from 1986 (mid-month/month-end only before 1992-09), disaggregated from 2006 | Positions, not prices; Tuesday data released Friday |
| Yahoo Finance futures tickers (e.g. CL=F, ZN=F, GC=F) | Daily continuous front series | UNVERIFIED depth and roll rule; not seen in this scan; unadjusted rolled series (jumps at roll) |
| Stooq (cl.f etc.) | Possibly daily continuous | UNVERIFIED: search found nothing; test manually |
| Nasdaq Data Link CHRIS / SCF (ex-Quandl) | Was continuous contracts | Community post says Nasdaq-owned Quandl lost its futures providers; CHRIS status UNVERIFIED, likely dead |
| QuantConnect (cloud) | Daily futures history free in their cloud | Locked to their platform, minute/tick limited (per search summary) |
| MarketParquet | ~130 continuous ratio-adjusted OHLCV; recent daily free | Full history is paid |
| TurtleTrader archive | Daily CSV 1970s onward, most US futures | Static archive, not updated; quality UNVERIFIED |
| FirstRate Data | free samples exist (UNVERIFIED); VX etc. paid | not checked |
| Investing.com | Free CSV of futures (per search summary) | Continuous, roll rule unknown |
| CME DataMine / Portara / CSI / Databento | per-contract history | PAID (Portara free tier unavailable) |

Reading: free data gives (a) energy curve strips back to 1980s (EIA), (b) a complete VIX curve (Cboe), (c) COT positions. No free per-contract series for grains, metals, rates or index futures. So directions 1, 3 (energy only), 6 (crack), 8, 9 and 10 can be started with free data; 2, 4, 5, 7 need paid or UNVERIFIED rolled continuous data.

## Pick order if the user wants one
1. COT weekly signal (9): free, long history, power fine, CFD proxies owned. 2. NG storage-day drift (1) on owned NATGAS plus EIA curve. 3. FTMO CFD roll basis audit (10): cheap look, uses owned data. VIX curve (8) is a data-fix for the unfetchable ledger rows but the edge is probably crowded.
