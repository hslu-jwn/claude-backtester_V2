# Scout 3: crypto mechanisms beyond weekly cross-sectional factors (2026-11-16)

Method: about 14 web searches/fetches, mostly abstracts and search snippets; full papers NOT opened, so most effect sizes are
UNVERIFIED (abstracts give none). Quotes are verbatim from fetched pages/snippets. Ledger overlap checked against
ledger_compact.txt (I69 CME expiry week killed, I72 funding settlement killed, I76 liquidation reversal killed, I98 spot-hedged
carry killed, FB040 unlocks closed on power, HV-T0089 DeFi liquidation wave "untestable", Fable rows 40/41 ETF flows, stablecoin).

## Directions (ranked by my prior)

### 1. Quarter-hour opening order imbalance on Binance perps (periodic algo trading)
- Mechanism: algos fire at 1/5/15-minute marks; opening-bar order flow is serially dependent and its imbalance carries into hours.
- Venue/symbols: Binance USDT-M perps, paper uses six contracts (symbols not stated). Horizon: 4-12 h.
- Data: OWNED (klines, aggTrades, taker flow). Effect: no bp number found (abstract only), sample UNVERIFIED.
- Source: https://arxiv.org/abs/2607.09426 (Kim and Hansen) - "Opening returns are predictable out of sample"
- Differs from ledger: I72 tested funding-settlement hours only; this is every :00/:15/:30/:45 mark, intraday not weekly.
- Prior survives costs: 12 %. Risk: 4-12 h holds on perps at taker fees; needs maker execution or low-cost large caps. Capacity: modest.

### 2. Perp-spot basis mean reversion (time-series, per symbol)
- Mechanism: perps are not guaranteed to converge; funding is slow, so arbitrageurs (capital-limited) close the gap; deviation shrinks over time.
- Venue: Binance perp vs spot, top 20-50 symbols. Horizon: hours to days.
- Data: OWNED (spot + perp klines, funding). Effect: paper reports "high Sharpe ratios", numbers not on abstract page; UNVERIFIED sample.
- Source: https://arxiv.org/abs/2212.06888 (He, Manela, Ross, von Wachter) - "high Sharpe ratios"
  (the page also says returns are driven mostly by price convergence, funding less - from search summary, UNVERIFIED).
- Differs: I98 was funding-carry on spot-hedged book (turnover killed it). This trades convergence of the price gap, directional
  one-leg or delta-neutral; the edge is price, not funding. Needs two legs: cost wall is the main danger.
- Prior: 12 %. Capacity: large on majors, but the published arbitrage is likely institutional-only after costs.

### 3. Cross-sectional basis sort (daily horizon)
- Mechanism: high basis = leverage demand/crowded longs; sort predicts returns at daily horizon (Cao, Luo, Cheng, Dong, Edinburgh).
- Venue: Binance perps, 50-200 symbols. Data: OWNED. Effect: UNVERIFIED (third-party summary: "predictive power is concentrated at daily horizons"; paper not seen).
- Source: https://tradingstrategy.ai/docs/learn/carry-trade.html (summary of paper; title "Anatomy of Cryptocurrency Perpetual Futures Returns")
- Differs: I-73 sorts on funding weekly; basis (price gap) is a related but different signal, daily rather than weekly.
  Risk: high correlation with I-73/Strategy 20 (basis and funding co-move). Check correlation first.
- Prior: 10 %. Daily rebalance doubles cost drag vs weekly.

### 4. Quarterly/delivery futures vs perp drawdown dynamics
- Mechanism: per Gornall, Rinaldi, Xiao (preliminary), perp drawdowns mean-revert quickly while quarterly-futures drawdowns persist and overshoot spot.
- Venue: Binance COIN-M / USDT-M delivery futures BTC, ETH (klines on data.binance.vision - availability UNVERIFIED). Horizon: days.
- Data: FREE if delivery klines exist. Effect: none quantified (search summary only, UNVERIFIED).
- Source: search result summary, no direct URL fetched. Quote: none.
- Differs: ledger has no delivery-futures row; I69 was CME expiry week (killed). Forced flows: quarterly roll and basis arbitrageurs unwinding at expiry.
- Prior: 7 %. Few instruments (BTC/ETH), event count small near expiry (about 4 a year), so power is probably the killer.

### 5. DeFi lending liquidations (Aave/Compound) as forced selling of ETH and alt collateral
- Mechanism: health-factor breaches force collateral sales; paper finds temporary and permanent impact, oracle-linked cascades.
- Venue: ETH, WBTC, LINK, CRV etc. on Binance perps. Horizon: minutes to a day.
- Data: FREE but heavy (The Graph / Dune queries, event logs); owned data covers only the price side. Effect: no bp (abstract only).
- Source: https://www.bis.org/publ/work1062.htm (Lehar and Parlour, Dec 2022) - "temporary and permanent price impact of collateral asset sales in DeFi"
- Also Qin et al. https://arxiv.org/pdf/2106.06389v2.pdf: 3 % price variations can make over 10m USD liquidatable on Compound (search snippet).
- Differs: I76 used perp liquidation clusters (killed t 2.50); HV-T0089 was marked untestable (no data). This one is a *predictive* signal:
  distance of price to the next large liquidatable collateral cluster. Needs a build for the data pipeline (cost: days).
- Prior: 6 %. Capacity: small; events are rare and recent post-2023 DeFi liquidation volume is much lower. Likely closed on power.

### 6. Deribit weekly/monthly expiry hour (08:00 UTC) and max-pain pinning
- Mechanism: dealer hedging and settlement-hour activity; 2025 SSRN reports options activity clustering 08:00-09:00 GMT.
- Venue: BTC/ETH perps around Friday 08:00 UTC; about 52 weekly events a year, 300+ over six years (enough for power only for large effects).
- Data: price side OWNED; open interest by strike / max-pain is PAID (Tardis: only first-of-month CSV free, Deribit since 2019-03-30).
- Source: https://docs.tardis.dev/historical-data-details/deribit - "options_chain" is listed for Deribit (free only on the first day of each month).
- Effect: only secondhand "clear expiration effect in volume, volatility, and returns" (2023 paper, UNVERIFIED, no authors).
  News commentary: "max pain has a mixed record as an actual predictor". Realized-volatility effect more likely than a directional one.
- Differs: I69/I70 were expiry-WEEK drift (killed). This is the settlement hour and uses price only: could be screened on owned data
  (Friday 07:00-09:00 UTC return and range vs other Fridays) without any options data.
- Prior: 5 % directional; volatility-only edge is not tradable on CFDs.

### 7. ETF creation/redemption window (3-4 pm New York) and Coinbase premium
- Mechanism: APs buy or sell spot to match daily net creations; issuers use benchmark prices near the 4 pm fix; Kaiko: "increased activity between 3pm and 4pm New York time".
- Venue: BTC/ETH; BTCUSD / ETHUSD CFDs are owned (FTMO), Binance 1h owned. Horizon: 1 hour, daily.
- Data: flows from Farside are FREE (daily only, 2024+): only about 700 days, so only large effects are detectable (Fable row 40: detectable from about 28 bp).
- Source: https://www.kaiko.com/resources/btc-etfs-impact-on-spot-market-structure (quote above, from search snippet).
- Evidence is mixed: FalconX says flows have "short-term predictive power", Kaiko says the daily relation "remains weak" (both snippets, UNVERIFIED).
  Coinbase premium: only industry commentary; the one SSRN study found Binance leads Coinbase in price discovery, so premium is weak as signal.
- Differs: row 40 tested next-day only; hour-of-day 15-16 ET drift on owned hourly data is a free screen. Calendar-style, so past calendar kills warn.
- Prior: 4 %.

### 8. Weekend / Sunday thin-liquidity reversal
- Mechanism: weekend liquidity falls (Kaiko: weekend trade volume at lows, spreads wider on Coinbase), so liquidations overshoot; Monday rebound.
- Venue: BTC, ETH, majors; horizon: Sunday to Monday. Data: OWNED. Effect: Santiment (2017+): Monday +0.69 %, Saturday +0.5 % average log return (snippet; not peer reviewed).
  Researcher blog says Sunday effect is small. Post-ETF weekends 9.07 points less volatile (Volmex).
- Source: https://research.kaiko.com/insights/where-did-weekend-crypto-traders-go
- Differs: weekday seasonality was killed on CFDs; crypto weekend is a different liquidity regime but effect is likely decayed since ETFs.
- Prior: 4 %. Quick to screen on owned data, so cost of testing is low.

### 9. Stablecoin mint/burn and depegs
- Mechanism: Tether issuance (alleged price support) and USDC depeg flows. Griffin and Shams report significant negative end-of-month abnormal return of 6 % in strong-issuance months (2017 data; snippet).
- Source: https://papers.ssrn.com/abstract=3195066 (Journal of Finance 2020). Contested; data end Nov 2018.
- Data: on-chain supply FREE but needs a pipeline; few events. Fable row 41 already says decayed. Prior: 3 %. Close on power.

### 10. Token unlocks, miner selling, CME gap, exchange flows: not pursued
- Unlocks: FB040 closed on power. CME gap: Fable list says no data and gap-fill dead. Exchange inflow/outflow (CryptoQuant/Glassnode): daily series are PAID.
  Miner selling: daily, slow, few independent events. All prior below 3 %.

## Crypto prop firms (for Goal 1)
- HyroTrader (Bybit perps; also Cleo platform): rules from https://proptradingvibes.com/blog/hyrotrader-prohibited-strategies
  (third-party review, not the official page; UNVERIFIED against HyroTrader's own rules): no minimum or maximum holding time,
  must trade at least once every 30 days; "Martingale and cross-account hedging are prohibited."
  Daily loss static from start-of-day equity, reset 00:00 UTC: Core 3 %, One-Step 4 %, Two-Step 5 %, Instant 3 %.
  Max loss from initial balance: Core 5 %, One-Step 8 %, Two-Step 10 %, Instant 5 %. Funded: total margin 25 % of balance, notional 2x balance.
  Instant: one closed trade losing more than 2 % warns, second ends the account.
- News: reviews mostly say news-only trading is banned but holding through news is allowed (conflicting sources). Weekend/overnight holding permitted.
  Bots: sources conflict (one says EAs allowed on Bybit via API, not on Cleo; another says third-party bots barred during the challenge, custom bots allowed).
  Check with HyroTrader support before relying on automation. See https://fundedtrading.com/propfirm/hyrotrader/ for the review set.
- Crypto Fund Trader: only appears in a comparison URL (velotrade); rules NOT verified here.
- Fit: Strategy 20 style weekly holds and 4-12 h holds (Direction 1) are allowed on holding time; daily loss uses floating P&L plus fees, so tail days matter.

## Pick
1. Direction 1 (quarter-hour imbalance): cheapest to screen on owned data, no overlap with the ledger, has an out-of-sample claim.
2. Direction 6 price-only screen (Friday 08:00 UTC hour) and Direction 8 as one-afternoon calendar screens, only if power clears.
3. Directions 2/3 only after a correlation check against I-73 and Strategy 20.
Unverified overall: effect sizes in all papers except Griffin and Shams; check full texts before pre-registering.
