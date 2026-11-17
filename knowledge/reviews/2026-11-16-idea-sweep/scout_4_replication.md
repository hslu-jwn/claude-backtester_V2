# Scout 4: replication / meta-research literature -> testable directions (2026-11-16)

Evidence quality note: web search returned summaries, I fetched full text only for the Quantpedia study. Quotes marked (S) come from search-result summaries or abstracts, not from the paper text; treat as UNVERIFIED verbatim. Effect sizes are from abstracts. No direction below was tested.

## What survives (5 lines)
1. Decay is the rule, not death: McLean-Pontiff (97 stock predictors) ~26 % lower out of sample, ~58 % lower after publication; Quantpedia (355 strategies) mean Sharpe -33 %, median -44 %. Plan on halving every published effect (our MDE rule already does).
2. Decay is larger where arbitrage is cheap (Bartram-Djuranovik-Garratt, currencies: bigger decline for "larger in-sample profits and lower arbitrage costs" (S)). Survivors sit where trading is costly, capacity small, idiosyncratic risk high: that is exactly crypto perps and our three passes.
3. Cross-sectional sorts on flow / funding / positioning at weekly frequency in crypto are the best match to our history; size, volume and illiquidity crypto anomalies come from micro-caps (Fieberg-Liedtke-Zaremba 2024 (S)) and fail liquid-only; crypto momentum is tradable mostly via shorts at high cost (same paper), consistent with our C2 / I-97 kills.
4. Time-series trend and carry in futures have the best century-long evidence (Hurst-Ooi-Pedersen; Koijen et al. carry Sharpe ~0.7 within asset classes (S)) but need futures prices and roll data (PAID) and our 35-symbol CFD trend run already failed (I51, gross Sharpe -0.13); not a CFD direction.
5. Intraday effects are real but tiny (Gao et al. first-half-hour predicts last-half-hour R2 ~1.6 % (S); Heston-Korajczyk-Sadka same-half-hour continuation for 40 days (S)); only the multi-name, low-turnover versions can beat 1-4 bp cost walls, and only if applied to names with big spreads in absolute terms, which kills them in net terms. Overnight/intraday split (Lou-Polk-Skouras) is a cross-sectional stock effect.

## Directions (ranked by my prior)

### D1. Cross-sectional factor momentum / timing across our own passed crypto sorts
- Mechanism: factor returns autocorrelate (Fieberg-Liedtke-Metko-Zaremba 2023: factor-level autocorrelation "not widespread", mostly size and volatility (S)); here we test only whether S20 / I-73 / I-83 weekly returns predict their own next-4-week returns, to scale exposure.
- Venue + symbols: Binance USDT perps (all, incl. delisted), Bybit check. Horizon: weekly signals, monthly scaling. Trades: no new trades, it is a sizing overlay on existing books.
- Data: OWNED (the strategies' own weekly return series, 266+ test weeks). 
- Effect: no published number for these factors; the paper is cross-sectional on 34 anomalies, 3,900 coins, 2014-2022 (S). Decay unknown.
- Source: https://econpapers.repec.org/RePEc:taf:quantf:v:23:y:2023:i:12:p:1853-1869  Quote (S): "factor-level autocorrelation is not widespread"
- Differs from ledger: I-97 / FB-009 are coin-level momentum (killed); this is factor-level timing of already-passed sorts, no row covers it. FB-254 is monitoring only.
- Power warning: only ~270 test weeks, MDE large; likely closes on power. Prior survives: 5 %.

### D2. Session-split cross-sectional sort on crypto (Lou-Polk-Skouras on 24 h assets)
- Mechanism: a stock's overnight vs intraday return components persist with opposite-signed cross-period reversal; "profits are either earned entirely overnight ... or entirely intraday" for 14 strategies (S). Crypto has no close, so define sessions (e.g. 00-08 / 08-16 / 16-24 UTC, or Asia / EU / US) and sort by the past-week return of one session component.
- Venue + symbols: Binance USDT perps, top-100 liquid first. Horizon: weekly sort, 1 week hold (same cost structure as S20).
- Data: OWNED (1h klines).
- Effect: JFE 2019, US stocks 1993-2013 (UNVERIFIED sample); monthly spreads of several % per year; no crypto version found. Decay: authors argue the pattern should limit clienteles.
- Source: https://researchonline.lse.ac.uk/id/eprint/87481  Quote (S): "profits are either earned entirely overnight"
- Differs from ledger: I-96 / FB-113 are share-CFD gap reversals (killed); I-82 daily taker flow sort killed; none splits crypto returns by session. Correlation with S20 unknown (risk: same tail coins).
- Prior survives costs: 8 %.

### D3. Realized-skewness / realized-moment weekly sort on crypto perps (Amaya et al.)
- Mechanism: intraday realized skewness (not total-period) predicts next week: long lowest decile, short highest; lottery / skew preference.
- Venue + symbols: Binance USDT perps, 1h bars (5-minute bars for the closer replica). Horizon: weekly.
- Data: OWNED (1h; 1m klines also downloadable free).
- Effect: US stocks, +19 bp/week, t 3.70 (published JFE 2015; 2013 working paper +24 bp, t 3.65) (S); sample ~1993-2008 per CXO summary; post-publication decay UNVERIFIED; CXO notes weekly trading frictions would eliminate most stock profit. Crypto bp-per-week scale is 5-8x larger, so our 20 bp cost matters less.
- Source: https://econpapers.repec.org/RePEc:eee:jfinec:v:118:y:2015:i:1:p:135-167  Quote (S): "average return of 19 basis points the following week"
- Differs from ledger: I-79 (MAX) killed t 0.70 and I-80 volume shock killed; realized skewness is a separate construct but correlated with MAX, so expect overlap. No ledger row uses intraday realized moments.
- Prior survives costs: 7 %.

### D4. Independent-venue replication of the passed sorts (OKX / Hyperliquid / Bitget perps)
- Mechanism: no new mechanism; tests whether S20 (taker-flow) and I-73 (funding carry) survive on a venue not used in development; the literature stresses replication on fresh samples (Jensen-Kelly-Pedersen: 55.6 % US replication, higher globally (S)).
- Venue + symbols: OKX perps (history from ~2019-20 UNVERIFIED), Hyperliquid (history since 2023 only). Horizon: weekly.
- Data: FREE public APIs (funding, candles; taker-flow availability per venue UNVERIFIED); not owned yet.
- Effect: n/a (our own factor); the S20BY check already showed Bybit +145.5 bp/week, t 2.93 on largely the same coins, so independence is partial.
- Source: https://nber.org/system/files/working_papers/w28432/w28432.pdf  Quote (S): "replication rate"... (no short verbatim confirmed) UNVERIFIED
- Differs from ledger: S20BY is same coins with Bybit prices; this adds coins and venues that Binance does not list. Value is portfolio-level confidence for the HyroTrader decision, not a new strategy.
- Prior it survives: 25 % (but low incremental research value).

### D5. Same-calendar-period seasonality in crypto weekly cross-section (Keloharju-Linnainmaa-Nyberg / Heston-Sadka)
- Mechanism: a coin's return in the same weekday / same week of month / same hour one period ago predicts the same period now (common factor loadings, size and industry-like), "strategy based on same-calendar month returns earns 13 % per year" in US stocks 1963-2011 (S); also found in commodities, indices and at daily frequency (S).
- Venue + symbols: Binance USDT perps; version A same-weekday (lags 1-8 weeks), version B same hour-of-day lag 1 day (HKS 2010: half-hour continuation lasts 40 days (S)). Horizon: daily hold for A, 1 h for B (B hits cost wall; pick A).
- Data: OWNED.
- Effect: anomaly meta-strategy 1.88 %/month, t 6.43 for 15 stock anomalies (S, in-sample). Crypto: UNVERIFIED; Quantpedia says hour-of-day BTC effect (21-23 UTC) not net of cost, academic work on 15 m observations finds no persistent pattern (S).
- Source: https://www.nber.org/papers/w20815.pdf  Quote (S): "average return of 13% per year"
- Differs from ledger: SC1 / SC2 and the turn-of-month / weekday rows are time-series calendar screens on CFDs (killed); this is a cross-sectional own-history signal on perps, untested.
- Daily turnover: cost 20 bp round trip vs a likely 5-15 bp gross: prior survives costs: 4 %.

### D6. FX carry from the MT5 swap table, cross-sectionally, with swap earned not paid
- Mechanism: Koijen-Moskowitz-Pedersen-Vrugt carry across assets; for FX CFD the signed swap is the carry. The ledger killed carry for CFDs "because swap eats the premium" but that applies to the wrong-side leg; long the high-yield, short the low-yield pair earns net-positive swap on both legs if broker markup is below the rate gap.
- Venue + symbols: FTMO FX pairs (AUDJPY, NZDJPY, CADJPY, CHFJPY, USDJPY ...) where the rate spread is largest. Horizon: monthly. Trades: few (12 rebalances x ~6 pairs), so it fails the 300-trades rule; needs a big edge.
- Data: OWNED for prices; swap history by date is PARTIAL (mt5_info gives current swaps only; a historic swap series is not owned: UNVERIFIED).
- Effect: Sharpe ~0.7 gross within asset classes, 1.1 diversified, 1972-2012 monthly (S). Currency anomaly profits "decrease substantially after the publication" (Bartram et al., S).
- Source: https://econpapers.repec.org/RePEc:eee:jfinec:v:127:y:2018:i:2:p:197-225  Quote (S): "gross Sharpe ratio of about 0.7"
- Differs from ledger: HV-T0049 / T0057 / T0103 (carry) are flagged needs_data / untestable and never screened; I-87 (overnight premium) and I-68 (oil carry) are different assets. Likely closes on power, 2008-2021 has only ~160 monthly points.
- Prior survives costs: 5 %.

### D7. Futures-roll / curve carry via spot-vs-futures gap (Goal 2) - only if futures data is bought
- Mechanism: carry and roll yield in commodity and index futures; Quantpedia, Koijen et al. place it among the most replicated cross-asset effects.
- Venue + symbols: CME/ICE futures (ES, NQ, CL, GC, 6E ...). Horizon: monthly.
- Data: PAID (continuous futures with roll dates); the CFD proxy fails (oil carry closed on power I-68).
- Effect: see D6; Hurst-Ooi-Pedersen trend net Sharpe quoted ~0.4 (CXO) vs 0.77 (AQR table) over 1880-2013 (sources conflict).
- Source: https://www.TrendFollowing.com/whitepaper/Century_Evidence_Trend_Following.pdf  Quote: none verified.
- Differs from ledger: I51 (trend on CFDs, killed), I-68 (oil carry closed on power). A futures-priced version is a separate question the venue rule allows.
- Prior survives costs: 10 %, but needs money for data, so a user decision.

## Explicit non-recommendations (to save the loop time)
- Intraday momentum (Gao et al.): overlaps H02 / F2 (falsified after costs), C3 (screened out), I-85 / I-86 (killed). Index CFD cost walls remain.
- Volatility-managed overlays: Cederburg et al. (JFE 2020) find real-time versions underperform out of sample (S); not a signal, at most a risk-sizing test.
- Crypto size / volume / illiquidity and momentum sorts: micro-cap or short-leg driven per Fieberg et al.; overlap I-80, I-97, FB-012.
- Realized skewness on US large caps: ~19-24 bp/week gross before costs (CXO says frictions remove it); weaker than D3's crypto variant.
- Chen-Zimmermann Open Source Asset Pricing: monthly stock characteristics; replication "nearly 100 %" and post-publication decay "remain positive" (S), no short-horizon or futures subset found. Not directly usable.

## Sources actually opened or returned
- https://nber.org/system/files/working_papers/w28432/w28432.pdf (Jensen-Kelly-Pedersen)
- https://papers.ssrn.com/abstract=3604626 (Chen-Zimmermann)
- https://quantpedia.com/in-sample-vs-out-of-sample-analysis-of-trading-strategies/ (opened; quote "investment strategies typically remain profitable after publication")
- https://repec.cepr.org/repec/cpr/ceprdp/DP15653.pdf (Bartram et al., currency anomalies)
- https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414 (Gao et al.)
- https://econpapers.repec.org/RePEc:eee:jfinec:v:134:y:2019:i:1:p:192-213 (Lou-Polk-Skouras)
- https://econpapers.repec.org/RePEc:bla:jfinan:v:65:y:2010:i:4:p:1369-1407 (Heston-Korajczyk-Sadka)
- https://econpapers.repec.org/RePEc:eee:jfinec:v:106:y:2012:i:3:p:660-684 (Menkhoff et al. currency momentum; spread up to 10 % a year, partly transaction costs)
- https://econpapers.repec.org/RePEc:cup:jfinqa... CTREND JFQA PDF returned HTTP 404 on fetch, claims about CTREND UNVERIFIED
- https://econpapers.repec.org/RePEc:oup:rfinst:v:29:y:2016:i:1:p:5-68 (Harvey-Liu-Zhu, t > 3.0 bar, which our gates already meet)
