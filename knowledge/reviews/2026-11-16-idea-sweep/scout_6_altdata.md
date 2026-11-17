# Scout 6: free alternative / fundamental data (2026-11-16)

Honest summary: ~10 web searches, 4 pages fetched. Free alt-data signals in the literature are mostly pre-2015, gross of costs, and daily/weekly on single US shares; most have a low prior on FTMO CFDs. Anything marked UNVERIFIED was not confirmed against a primary page. The ledger compact copy had no rows on FINRA short volume, Form 4, Google Trends, Wikipedia, GDELT, prediction markets, weather or net liquidity (grep). Closed neighbours: EIA reports (S12), earnings premium / PEAD (I77, FB123, FB115), auctions / events closed on power.

Power warning for every row: the dev window for FTMO CFDs ends 2021-09-14 and FTMO M1 starts ~2019-20, so a CFD-only screen has ~1.5-2 years of dev. Rows using Alpaca bars (2016+) or histdata (2000s) have more.

---

## 1. FINRA daily short-sale volume ratio, 1-day cross-sectional sort on large caps
- Mechanism: short sellers trade on short-term overreaction and information; high short volume / total volume predicts negative next-day return.
- Venue / symbols: ~46 US large caps + sector ETFs (Alpaca minute bars 2016+); executable as FTMO share CFDs or only as a signal for sizing.
- Horizon: 1 day (decays after 1 day).
- Data: FINRA Reg SHO daily short-sale volume files, FREE, bulk text files by date (page: finra.org > Data > Short Sale Volume; exact URL UNVERIFIED). History ~2009/2010+ (UNVERIFIED start). Published ~6 pm ET the same day, so a next-open entry is point-in-time. Caveat: file covers off-exchange / TRF volume only, not all venues.
- Published effect: Diether, Lee, Werner (RFS 2009): ~1.39 %/month NYSE, 1.41 %/month Nasdaq for a daily long-low / short-high strategy, 2005 data; the working-paper summary says costs wipe it out (secondary source, CXO). A JFE paper on 2010-2015 reports predictability gone beyond a 1-day hold (snippet, UNVERIFIED authors). Zhu (Jan 2024): extreme-low short volume predicts up to 4 months, 2010-2022 (UNVERIFIED details).
- Source: https://ideas.repec.org/a/oup/rfinst/v22y2009i2p575-607.html; quote: "Short sellers ... correctly predict future negative abnormal returns."
- Difference from ledger: ledger has no short-flow row; closest are crypto taker-flow sorts (I-78), which survived. This is the equity analogue of "flow sort" but at 1 day, where share-CFD cost (10-20 bp round trip per ledger FB123 note) is the wall.
- Prior survives costs: 8 %. Better as a filter on a weekly horizon (untested in the literature I found): 10 %.

## 2. SEC EDGAR Form 4 opportunistic insider buys (non-routine)
- Mechanism: insiders with no routine-timing pattern trade on private information; predictive 4-6 months.
- Venue: US large caps (46 CFD shares); horizon: weeks to months (swap cost applies, ~22 bp for 5 nights per ledger FB123).
- Data: EDGAR full-text / daily index and Form 4 XML, FREE (https://www.sec.gov/edgar), history 2003+ electronic, filings dated to the second so point-in-time. Filing delay up to 2 business days; use acceptance timestamp.
- Effect: Cohen, Malloy, Pomorski (JF 2012): opportunistic portfolio 82 bp/month value-weighted abnormal, routine ~0, sample 1986-2007 (search summary of NBER digest; the NBER PDF would not parse, so UNVERIFIED against primary). 1.59 %/month equal-weighted 4-factor (single presentation, UNVERIFIED).
- Source: https://www.nber.org/papers/w16454.pdf ; quote UNVERIFIED (PDF not readable).
- Difference: new data family; ledger has earnings premium and PEAD only.
- Problem: large caps have few opportunistic insider buys; the effect lives in small, local, poorly governed firms. Event count on 46 names is probably < 100 per year; power check likely closes it. Prior: 5 %.

## 3. Futures open interest growth / CFTC COT speculator positioning, weekly-to-monthly
- Mechanism: open interest rises with hedging demand; Hong-Yogo: it predicts commodity, bond and currency returns beyond futures prices.
- Venue: XAUUSD, XAGUSD, USOIL, UKOIL, NATGAS, FX majors, indices (CFD); horizon 1-4 weeks (swap on CFD).
- Data: CFTC COT (legacy / disaggregated / TFF), FREE bulk (https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm); weekly Tuesday positions, published Friday 15:30 ET, so Monday entry is point-in-time. History 1986+ (futures-only), TFF 2006+. Open interest from exchange settlements is not free for all contracts (UNVERIFIED).
- Effect: Hong & Yogo (JFE 2012): one SD rise in commodity market interest raises expected commodity returns by 0.63-0.73 %/month depending on draft, 1965-2008 (UNVERIFIED sample from snippet); "to a lesser degree" currency, bond, stock. CXO summary of net speculator positions: gross Sharpe ~0.55 over 84 futures 1992-2018, FX ~0.47, fixed income negative (secondary source). A farmdoc paper found little Granger evidence (commodities).
- Source: https://econpapers.repec.org/RePEc:eee:jfinec:v:105:y:2012:i:3:p:473-490 ; quote: "open interest could be more informative than futures prices"
- Difference: the brief says COT was "partly considered", but I could not find a COT row in the compact ledger by keyword; check ledger for the exact row before use. Monthly oil carry (I68) was closed on power: same power problem (0.6 %/month vs monthly sd 4-12 %).
- Prior: 6 %. Better as a conditioning filter on a cross-sectional FX or commodity basket than as a driver.

## 4. Google Trends / Wikipedia page-view attention timing
- Mechanism: rising search for finance terms (e.g. "debt") precedes falls; Wikipedia views of company pages precede moves.
- Venue: US30 / US500 / NAS100 and DJIA names; horizon: weekly.
- Data: Google Trends (free but sampled, re-scaled, rolling index: NOT strictly point-in-time, a real defect); Wikimedia pageviews API, FREE, daily from 2015-07 (https://wikimedia.org/api/rest_v1/), point-in-time.
- Effect: Preis, Moat, Stanley (Sci. Rep. 2013): "debt" strategy +326 % vs buy-and-hold 16 % over 2004-02-2011, 98 terms tried, costs excluded, 104 trades/year (fetched). Moat et al. 2013 Wikipedia: up to 141 % vs 3 % over 2007-12 to 2012-04, 30 DJIA company pages (press summary, UNVERIFIED). ElBahrawy et al. (2019) Wikipedia-informed crypto strategy beats baselines out of sample, July 2015-Jan 2019 (UNVERIFIED size).
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC3635219 ; quote: "would have increased the value of a portfolio by 326%"
- Difference: ledger has no attention-data row.
- Heavy snooping (98 terms, best one shown), no t-stats; this regime (2004-2012, crisis) is unlikely to repeat. Prior: 3 %. Use only as a pre-registered single-term check on Wikipedia 2015+.

## 5. GDELT news tone as a daily index / FX signal
- Mechanism: news tone predicts next-day returns, mostly short-lived local effects.
- Venue: index CFDs (country tone vs local index), EURUSD / USDJPY; horizon: 1 day.
- Data: GDELT 2.0 event and GKG files, FREE (https://www.gdeltproject.org/data.html; BigQuery free tier), 15-minute updates from 2015-02; point-in-time by file timestamp. Tone is a crude lexicon measure; GDELT has had outages and processing changes (UNVERIFIED).
- Effect: IMF WP 18/274: news tone "robustly predicts daily returns" in advanced and emerging markets, local effects short-lived (abstract snippet; no effect size retrieved, UNVERIFIED). Zhang (arXiv 2505.16136, 2025): FinBERT on GDELT for EURUSD, USDJPY, 10y Treasury, XGBoost (size UNVERIFIED).
- Source: https://imf.org/-/media/Files/Publications/WP/2018/wp18274.ashx ; quote UNVERIFIED (not fetched).
- Difference: new data family. Cost: daily index CFD round trip is 1-4 bp gross edge scale per ledger pattern, so a daily-tone edge must exceed this. Prior: 4 %.

## 6. Prediction-market probabilities (Kalshi / Polymarket) as event surprises
- Mechanism: contract prices are real-time probabilities for CPI / FOMC / earnings outcomes; the outcome minus the price is the surprise, available intraday and more precisely than consensus.
- Venue: US500, NAS100, USDJPY around releases; BTC around macro prints; horizon: minutes to 1 day.
- Data: Kalshi public API with trade history (FREE read; https://docs.kalshi.com, UNVERIFIED depth), Polymarket public CLOB / subgraph (FREE). History: Kalshi macro markets since ~2022, Polymarket 2020+; short.
- Effect: Fed FEDS 2026-010: Kalshi CPI forecasts improve statistically on Bloomberg consensus, FOMC forecasts at least as accurate as fed funds futures (secondary summaries, UNVERIFIED). HHS study: Polymarket earnings-beat markets incrementally informative for announcement returns, Sep-Nov 2025 only. Bürgi, Deng, Whelan (CEPR 2026): prices are biased (favourite-longshot), takers lose ~32 % (snippet). No paper found testing price-based trading of the underlying asset.
- Source: https://www.federalreserve.gov/econres/feds/files/2026010pap.pdf ; quote UNVERIFIED.
- Difference: ledger closed FOMC / CPI / EIA event families on power (few events, ~8-12 per year). Prediction-market data does not fix the event count. Dev window is also post-2021 (mixes with test). Prior: 2 %. Listed for completeness; close without a look.

## 7. Retail herding (Robintrack) 5-day reversal
- Mechanism: intense retail buying episodes are followed by negative returns.
- Venue: US shares; horizon: 5 days.
- Data: Robintrack holdings counts, FREE archive (historical), but the feed ended in Aug 2020; covers 2018-08 to 2020-08 only (UNVERIFIED start). So no clean dev/test split and not live-updatable.
- Effect: Barber, Huang, Odean, Schwarz (2020): shorting herded stocks for 5 days gave positive market-adjusted returns 63 % of the time, gross (search summary, UNVERIFIED). Welch (JF 2022): crowd portfolio does not underperform; the signal is mostly lagged volume.
- Source: https://www.nber.org/papers/w27866 ; quote UNVERIFIED.
- Prior: 1 %. Closed on data (no forward data). Note only because it is the only free retail-flow history.

## 8. NOAA weather forecast revisions for NATGAS
- Mechanism: revisions in gas-weighted degree days between model runs move prices; the revision is not yet in a 08:00-18:00 daily price (weak assumption).
- Venue: NATGAS CFD (FTMO, ~2019-20+), possibly UKOIL / wheat is out of scope; horizon: 1-3 days.
- Data: NOAA GFS / GEFS archived forecasts, FREE (AWS Open Data / NOMADS), 2015+ for the GFS archive on AWS (UNVERIFIED); heavy (GRIB) but doable. Needs a degree-day conversion by population weights (a build task).
- Effect: no academic paper found with an effect size; only trade press describing the mechanism (NGI). UNVERIFIED. Mu (2007, "Weather, storage, and natural gas price dynamics") is the academic anchor I recall but did not retrieve: UNVERIFIED.
- Source: https://www.naturalgasintel.com/?p=210224 (news, not evidence); quote: not used.
- Difference: ledger has EIA storage report (S12 falsified) and NATGAS carry; weather revisions are a different information source, and are usually priced within the model-run window (futures react within minutes), which implies a gap in a bar-based daily test. Dev window on FTMO NATGAS before 2021-09 is ~1.5 years: power likely fails. Prior: 4 %.

## 9. Net liquidity (H.4.1 + Treasury General Account + reverse repo) weekly changes
- Mechanism: fall in Fed net liquidity drains risk assets.
- Venue: US500 / NAS100 / BTC; horizon: weekly.
- Data: FRED / ALFRED (https://fred.stlouisfed.org, API key free), H.4.1 weekly (Thursday), TGA from Daily Treasury Statement (daily), RRP from NY Fed (daily); point-in-time (these series are not much revised; ALFRED vintages exist).
- Effect: none found in peer review. A blog analysis of H.4.1 data 2003-2026 reports level correlation 0.84 but weekly-change correlation about -0.03 (UNVERIFIED, blog). That is the evidence against it.
- Source: https://eco3min.fr/en/net-liquidity-vs-equities-correlation/ ; quote UNVERIFIED.
- Prior: 2 %.

## 10. Free crypto flow data beyond what the ledger holds: stablecoin supply / exchange flows (weekly)
- Mechanism: stablecoin issuance as fresh buying power; the weekly crypto cross-section is the only family that has survived.
- Venue: BTC/ETH perps; Bybit / Binance weekly horizon.
- Data: DeFiLlama stablecoin API (FREE, https://stablecoins.llama.fi, UNVERIFIED depth, history since ~2017); Coin Metrics community data (FREE tier, daily; UNVERIFIED terms); Glassnode free tier is limited.
- Effect: no formal study found; only media and vendor claims (Cointelegraph, Santiment). UNVERIFIED. Mostly a time-series BTC signal, so ~N=1 asset; MDE large.
- Source: none peer-reviewed.
- Difference: the ledger's survivors are cross-sectional and flow-based; this is time-series, single-asset (weak). A cross-sectional version would need per-token on-chain flow (e.g. exchange netflow per token) which is not free at history depth (UNVERIFIED).
- Prior: 3 %.

---

## Ranking by prior (my pick order)
1. FINRA short-volume ratio, tested as a weekly / multi-day cross-sectional sort on 46 names plus ETFs (8-10 %); needs only a free bulk download and Alpaca bars already owned.
2. COT / open-interest conditioning on FX-commodity baskets (6 %).
3. Form 4 opportunistic buys (5 %; likely closed on power).
4. NATGAS weather revisions (4 %, build cost high).
5. GDELT tone (4 %), Wikipedia (3 %), stablecoin supply (3 %).
6. Close without a look: prediction markets (2 %), net liquidity (2 %), Robintrack (1 %).

Not checked: FRED ALFRED specifics, Treasury auction data (ledger closed auctions), earnings calendar timestamps (ledger closed earnings), shipping / AIS, TIC flows, ECB balance sheet, EIA / USDA reports beyond S12, 13F (45-day lag, so slow and stale), 8-K timing, StockTwits / Reddit archives (Pushshift access restricted; UNVERIFIED).
