# Calendar and event effects as day-trade candidates (research notes, 2026-11-09)

Scope: post-2010 / post-publication evidence for one-session, stop-defined index/FX/gold CFD day trades. Costs assumed 1-2 bp round trip on US index CFDs, a few bp elsewhere.
Status tags: OPENED-FULL = full text read (via pdftotext of the downloaded PDF); OPENED-ABSTRACT = abstract/landing page or search snippet only; NOT-OPENED = known only from secondary summaries. No number below is invented; "my arithmetic" marks derived numbers. Numbers cited by table/page where the text layer allowed it.

## 0. Bottom line

1. No calendar effect found has a verified, post-2010, after-cost, OPEN-TO-CLOSE (single-session) result on index CFDs. Every well-documented effect is either close-to-close daily data (so the overnight/intraday split is unknown), multi-day, overnight, or decayed.
2. Most promising to TEST on our own data (hypotheses, not proven rules): (a) turn-of-month/T-3 reversal days, (b) last-30-minute intraday momentum conditioned on the day's move, (c) first-hour-of-Europe "overnight drift" window for GER40/UK100 (only as a 1-hour trade; the paper itself shows it dies after bid-ask costs).
3. Dead for large-cap indices: pre-holiday, Monday/day-of-week, pre-FOMC drift (post-2015), generic option-expiration-week long/short.
4. Gross per-trade edges in the literature are 2-7 bp/day (intraday momentum, overnight drift). With 1-2 bp costs and a stop-defined R-framework (stop widening costs R), these are marginal. The only effect with a large per-event size is the multi-day turn-of-month window (about 48 bp abnormal over T-3..T+3), which is not a day trade.

## 1. Turn-of-the-month (TOM)

### Sources
- Etula, Rinne, Suominen, Vaittinen, "Dash for Cash", RFS 33(1) 2020, 75-111; Feb 2019 working paper version: OPENED-FULL (pdftotext). Published version at academic.oup.com: NOT-OPENED.
- McConnell and Xu, "Equity returns at the turn of the month", FAJ 64(2) 2008, 49-64: OPENED-ABSTRACT (CFA Institute / RePEc landing text via search; Quantpedia summary of its Table 3 opened).
- Lakonishok and Smidt 1988 (RFS 1): NOT-OPENED (cited via Ko and Yang and Quantpedia; DJIA 1897-1986).
- Quantpedia "Turn of the month in equity indexes": OPENED-FULL (secondary source).

### Facts (with location)
- McConnell and Xu (via Quantpedia summary of their Table 3 panel A.1, large-cap): mean daily return 0.15% on days -1..+3 vs 0.01% on other days, t=7.81, CRSP 1926-2005; abstract: value-weighted 0.15%/day, equal-weighted 0.22%/day over the four-day window, other 16 days near zero. Effect in 31 of 35 countries (CFA Institute abstract). Window = last trading day of month plus first 3 of next (T-1... naming differs: "days -1 to +3" = last day through 3rd day).
- Dash for Cash (text p.3-4, p.11-12): average CRSP-VW return since the 1995 adoption of 3-day settlement: -17 bp over T-8..T-4, +77 bp over T-3..T+3. Abnormal (minus sample average daily return): -37 bp for T-8..T-4, +25 bp for T-3..T-1, +48 bp for T-3..T+3. Correlation of T-8..T-4 with T-3..T-1 returns: -0.54 (p.4). 22-23 international equity markets: reversals significant in 20 of 23 (p.4, Tables 1-2). Last decade (2003-2013): cumulative excess return in positive-reversal windows 103%, 73% of total market excess return (p.4).
- Mechanism: month-end cash needs (pensions, dividends) -> institutions sell stocks T-8..T-4 (selling must occur at least 4 business days before month end under T+3 settlement) -> price-pressure reversal T-3..T-1, then new-money buying T..T+3. Settlement moved to T+2 in the US in September 2017 (footnote 16, p.10), so the pressure date shifts by one day; the authors do not test the post-2017 shift.
- Intraday: footnote 25 (p.16): S&P 500 hourly returns show an intraday reversal on T-3 itself: correlation of morning and afternoon returns -0.23, significant at 5%, 11:00 cutoff. This is the only open-to-close-relevant datum found for TOM. It suggests: on T-3, fade the morning move into the close. Untested as a trade.
- Hedge funds with low margin (managed futures, global macro) increase equity beta on T-3 (Table 11), i.e. liquidity providers arrive in the morning of T-3, a capacity limit on the arbitrage.

### Intraday vs overnight
Unknown for TOM. All primary TOM papers above use daily close-to-close. I found no peer-reviewed open-to-close decomposition of TOM on index futures. General background: S&P futures since 2004 earned 4.6%/yr close-to-open vs 4.2%/yr open-to-close (Boyarchenko, Larsen, Whelan, Table IX(a)), so roughly half of the equity premium is overnight; a TOM effect could be mostly overnight. Must be measured on our data (US500/GER40/UK100/JP225 cash-session open-to-close vs close-to-open on T-3..T+3).

### Recent evidence / decay
- Post-2010: no peer-reviewed post-2010 US out-of-sample TOM study found. Giovanis (20 indices, effect in 19/20, claims robustness excluding 2010-2013): OPENED-ABSTRACT via Quantpedia summary, not verified. Nordic thesis 2012-2022 still positive; Malaysia conference paper: absent in recent years; informal blog: Finnish and DAX performance deteriorated after 2008 (low quality, NOT-OPENED). Treat as "published 1988/2008, partially robust internationally, post-2010 US/EU size unverified".
- Transaction costs: Quantpedia lists as "Not reported". A CXO-summarised study: SPY TOM close-to-open only strategy earned 0.0% net CAGR at 0.06% friction per round trip, with 8 round trips a month (NOT-OPENED, secondary; showing that daily-switching versions are cost-fragile, while a single contiguous holding window is not).

### Candidate rules (to test)
| Rule | Entry/exit | Gross | Trades/yr | Status | Overnight? | Skeptic |
|---|---|---|---|---|---|---|
| TOM-A: long index CFD on the 4-day TOM window | buy at cash open of last trading day (T) or T-1 close, hold to T+3 close (multi-day, NOT a day trade) | about 0.15%/day x 4 = 60 bp (VW, 1926-2005, McConnell-Xu); 48 bp abnormal T-3..T+3 (Dash for Cash, 1995-2013) | 12 | published + one international and mechanism replication; post-2010 size unverified | probably mixed | Violates one-session rule. Gross 48-60 bp versus 1-2 bp cost is fine, but mean edge is small relative to 4-day index vol (about 1.5-2%). Buy-and-hold beta, not alpha. |
| TOM-B (day-trade version): long at cash open on each of T-3, T-2, T-1, T, T+1..T+3, exit at close | open-to-close | unknown; if the 7-day abnormal 48 bp were all intraday it would be about 7 bp/day | about 84 | untested hypothesis | unknown | May be mostly overnight. Must measure. |
| TOM-C: fade the T-3 morning move, trade 11:00 to close | enter 11:00 ET (17:00 CET), exit cash close, direction = opposite of open-to-11:00 return | correlation -0.23 only; no bp figure in the paper | 12 | single footnote, unreported test, NOT replicated | no (intraday) | Only 12 trades a year, impossible to validate statistically in our split; T+2 settlement since 2017 shifts the date to T-2. |

## 2. Pre-holiday effect

### Sources
- Ko and Yang, "The Pre-Holiday Premium of Ariel (1990) Has Largely Become a Small-Firm Effect Out of Sample", Critical Finance Review: OPENED-FULL (11-page PDF, Table 1-2).
- Ariel 1990 (JF): NOT-OPENED, via Ko and Yang Table 1 (their replication numbers).

### Facts (Table 1, Table 2, p.3-5)
- Replication 1963-1982 (160 pre-holidays): CRSP EW 0.49% vs 0.06% non-pre-holiday; VW 0.37% vs 0.03%; t-stat of difference 9.12 (EW) and 7.03 (VW).
- Extension 1983-2019 (296 pre-holidays): EW 0.37% vs 0.07%; VW 0.14% vs 0.04%; t-stats 6.76 (EW) and 1.92 (VW). Fraction of positive pre-holiday days for VW 59% (no longer significant).
- VW pre-holiday premium after 1990: t=1.19; after 1995: t=1.23. DJIA t=0.64 and S&P 500 t=0.93 for 1983-2019 (p.4, untabulated). Table 2: significance of the VW premium disappears after controlling for weekend and turn-of-year dummies.
- Small-firm (EW minus VW) pre-holiday differential remains 0.07% (t=2.32) in 1983-2019: consistent with limits to arbitrage, not tradable via large-cap index CFDs.
- Close-to-close only; open-to-close split NOT reported. Futures versions (Fabozzi, Ma, Briley 1994; Dzhabarov and Ziemba 2010): NOT-OPENED.

### Verdict
DEAD for US500/US30/NAS100 as an edge (S&P 500 and DJIA premium statistically zero post-1983). Authors explicitly tie it to McLean and Pontiff decay. About 8-9 pre-holidays a year anyway, and holiday-eve sessions have thin volume and early closes. Not worth testing except as a cheap sanity check.

## 3. Options expiration, triple witching, month-end rebalancing, Monday effect

### Option expiration
- Garcia-Ares and Muravyev, "Option returns: a tale of the expiration rollover day" (June 2025 working paper), via Bogousslavsky's CBOE 2025 discussion slides and a quant blog: OPENED-ABSTRACT only. Finding concerns OPTION returns (delta-hedged calls about -0.43% from day before expiry through two days after), not underlying index returns. Not an index day-trade signal.
- Broker blog (Yahoo Finance): SPX average -0.29% in triple-witching weeks since 2021, expiration Friday average -0.36% (descriptive, no tests, small sample, not peer-reviewed). Treat as noise.
- E-mini intraday spike around third-Friday open (Brunel working paper, search snippet): NOT-OPENED. Quantpedia "option expiration week effect": NOT-OPENED. Stoll and Whaley and Ni, Pearson, Poteshman: NOT-OPENED.
- Verdict: no verified index-level day-trade rule; mechanisms (pin risk, gamma, rollover) are real for options, but index-level return effect is unproven post-2010. Candidate only for a volatility/range filter (expiry Fridays) not a direction signal.

### Month-end rebalancing and FX fix
- Melvin and Prins, "Equity hedging and exchange rates at the London 4 p.m. fix", J. Financial Markets 22 (2015) 50-72: OPENED-ABSTRACT (search results). Equity appreciation over the month predicts USD-selling/currency moves into the month-end fix, partly reverting next day. Return magnitudes not read. NOT verified after costs. Practitioner pages (pulse.bot etc.) are not evidence.
- Candidate (hypothesis): on the last trading day, fade/follow major FX in the hours before 16:00 London depending on the sign of the month's MSCI/S&P return. Need own test on EURUSD, GBPUSD, USDJPY with 1-3 bp spreads.

### Monday / day-of-week
- Sproule and Gosselin, MPRA 117001 (Apr 2023): OPENED-FULL. Finds no day-of-week effects in the S&P 500, 2013-2023 (OLS with Newey-West); cites Rubinstein: Monday effect disappeared after 1987. Working paper, not peer-reviewed.
- Panait 2025 (Proceedings of the International Conference on Business Excellence): OPENED-ABSTRACT; Monday still weaker but narrowing, 2000-2024.
- Verdict: DEAD as a stand-alone rule.

### Pre-FOMC drift and FOMC cycle (event-calendar effect)
- Lucca and Moench, "The Pre-FOMC Announcement Drift", J. Finance 2015: OPENED-FULL (Oct 2012 NY Fed working paper). S&P 500 +49 bp in the 24 h before scheduled FOMC announcements, Sept 1994-Mar 2011, 131 meetings (p.1, p.7), t>4.5, annualized Sharpe 1.14 (p.8), 80%+ of the equity premium. Mostly 24 h (overnight + morning).
- Cieslak, Morse, Vissing-Jorgensen, "Stock returns over the FOMC cycle", J. Finance 2019: OPENED-FULL (Oct 2015 draft). Equity premium earned in even weeks of the FOMC cycle; +13.6 bp/day (week 0) and +10 bp/day (weeks 2,4,6) vs odd weeks (Table, p.5 text), 1994-. Needs re-testing post-2015; no costs.
- Kurov, Wolfe, Gilbert, "The disappearing pre-FOMC announcement drift", Finance Research Letters 40 (2021): OPENED-ABSTRACT (RePEc). Drift appeared first with press-conference announcements and "essentially disappeared after 2015", sample through Dec 2019.
- Verdict: DEAD as originally specified after 2015 (post-publication decay in the textbook McLean-Pontiff sense). FOMC day itself remains a known high-volatility event; not a drift signal.

### Review-level evidence on decay
- McLean and Pontiff, "Does academic research destroy stock return predictability?", J. Finance 2016: OPENED-ABSTRACT (search summaries). Returns about 26% lower out-of-sample and 58% lower post-publication (97 predictors). They study cross-sectional characteristics, not index calendar effects.
- Hou, Xue, Zhang, "Replicating anomalies", RFS 2020: OPENED-ABSTRACT (search summaries). 65% of 452 anomalies fail t>1.96, 82% fail t>2.78 with NYSE breakpoints and value weights; microcaps drive results. Does NOT cover calendar effects (confirmed: none of the results mention them). Applied by analogy only: value-weighted large-cap versions of calendar effects (pre-holiday, Monday) have behaved exactly that way in Ko and Yang.
- Schwert 2003 (Handbook): cited in Ko and Yang, NOT-OPENED. Its conclusion (anomalies fade post-publication) is consistent with the day-of-week and pre-holiday evidence.

## 4. Intraday shocks, reversals and momentum on index futures

### Intraday momentum, last half hour (best-documented intraday index rule)
- Gao, Han, Li, Zhou, "Market intraday momentum", JFE 129(2) 2018, 394-414; Dec 2015 working paper OPENED-FULL. SPY 1993-2013: first half-hour return predicts last half-hour return, in-sample R2 1.6% (first only), 2.6% with the 12th half-hour, OOS R2 1.2% (1.8% with both). Timing strategy (sign of r1, trade last 30 min): 6.67%/yr, std 6.19%, Sharpe 1.08 (p.1-2); gross, "significant after transaction costs" asserted not quantified in the intro. Also holds in FTSE 100 and EuroStoxx 50 futures (2003-2015), NOT in currency or commodity futures (p.2, section 5.6).
- My arithmetic: 6.67%/yr over roughly 250 trades is about 2.7 bp gross per trade; against 1-2 bp round trip this leaves roughly 0.5-1.5 bp. Edge increases with volatility days, recession days, macro-release days.
- Baltussen, Da, Lammers, Martens, "Hedging demand and market intraday momentum", JFE 142(1) 2021, 377-403: OPENED-FULL (PDF). 60+ futures, Dec 1974-May 2020; return from the prior close to 30 minutes before close predicts the last-30-minute return; Table 6 panel A (equity index futures): annualized gross returns of the three timing strategies in the 4.2-6.9% range with Sharpe ratios 1.07-1.73 (text layer of the table is interleaved, so which row is which is NOT verified). Authors state they do not include costs; positive net Sharpe at one tick cost in S&P futures (p.386). Mechanism: gamma hedging by option dealers and leveraged-ETF rebalancing; predictability reverses over following days. Effect negative/zero in the last four months studied (Feb-May 2020) per their text, i.e. regime-sensitive.
- Zarattini, Aziz, Barbon, "Beat the Market: intraday momentum strategy for SPY", Swiss Finance Institute RP 24-97 (2024/2025): OPENED-ABSTRACT only (search summaries; PDF fetch returned only a cover page). Claimed 2007-2024 net 19.6%/yr, Sharpe 1.33, with "assumed trading frictions"; noise-area breakout, VWAP trailing exit. Not peer-reviewed, unreplicated, parameters tuned in-sample. Treat as a lead for rule shape (opening range plus VWAP stop), not as evidence.
- Chinese CSI 300 futures (2025, last-three-hour reversal): OPENED-ABSTRACT; not relevant to our instruments.
- Fung, Mok, Lam (2000) and Grant, Wolf, Yu (2005) opening-gap reversals in S&P futures: OPENED-ABSTRACT; 1987-2002 data; "modest after costs". Too old to count post-2010.

Candidate rule INTRA-1 (last-30-minute momentum): at 30 min before the cash close, go long if return since previous close > 0 (or both first-half-hour and rest-of-day agree), short otherwise; exit at close. Stop: tight (e.g. 0.3-0.5 x average 30-min range). Gross 2-3 bp/trade, about 250 trades/yr, fully intraday, published 2018/2021, post-publication check only to 2020, costs 1-2 bp. Skeptic: the stop eats most of a 2-3 bp edge; per-trade R would be small and the strategy depends on the close auction/MOC flows that CFDs may not replicate (CFD price follows futures, so fine in practice but the cash-index close differs from futures close).

### Overnight drift and opening reversal
- Boyarchenko, Larsen, Whelan, "The overnight drift", NY Fed Staff Report 917 (rev. Aug 2022): OPENED-FULL. ES futures 2004-2020: 02:00-03:00 ET (start of European trading) averages 3.7%/yr = 1.48 bp/day (abstract, t=7.13 in the table); overnight (close-to-open) 4.6%/yr vs open-to-close 4.2%/yr (Table IX(a)). Long ES 02:00-03:00: Sharpe 1.1 gross, -0.5 after bid-ask spreads (p.7); 01:30-03:30 window: 1.3 gross, 0.3 net. The strategy conditional on negative prior-day signed order flow ("buy the dip", BtD, trades half the days) keeps net Sharpe 1.1 (Table IX(b), p.28-29), because it pays the spread only half the time. Opening hour (09:30-10:30 ET) shows negative average returns (opening reversal), per the Liberty Street summary of the same research (NOT-OPENED page).
- Implication: the 1.48 bp/day gross is below our 1-2 bp cost: DEAD unconditional; the order-flow-conditioned version cannot be built without signed-volume data. For GER40/UK100 CFDs the 02:00-03:00 ET window equals 08:00-09:00 CET (cash open) so any signal there is open-to-first-hour, a session effect; untested.
- Note CFD spreads outside the cash session are wider than during it.

### FX intraday seasonality
- Breedon and Ranaldo, "Intraday patterns in FX returns and order flow", SNB WP 2010-4 (published J. Money, Credit and Banking 2013): OPENED-FULL (working paper). Currencies depreciate during their home trading hours (EUR weak in European hours, USD weak in US hours), 1997-2007, six crosses. Table 2: simple open-to-close strategy including bid-ask costs is profitable only for EUR/USD (Sharpe 1.3 for the short in the European morning; 0.9 for the long in the US afternoon); not profitable for other pairs after costs. Sample ends 2007, before the post-2008 FX market structure (EBS, fix reforms). Post-2010 replication: NOT found.
- Candidate INTRA-FX (hypothesis): EURUSD short 07:00-12:00 London, long 13:00-17:00 London (rough hours). Gross size not extracted by me; Sharpe only. Skeptic: sample ends 2007; unreplicated.

## 5. Other 2015-2025 intraday predictability that survives costs OOS

Nothing with a clean OOS-after-cost result for our instrument set was found beyond items already listed. Summary of what was found:
- Survives with caveats: last-30-min momentum (Gao et al.; Baltussen et al.), gross edge about 2-3 bp/trade; "positive net Sharpe at one tick" (Baltussen).
- Fails after costs: unconditional overnight drift (Boyarchenko et al.), FX time-of-day except EUR/USD (Breedon-Ranaldo).
- Disappeared post-publication: pre-FOMC drift after 2015 (Kurov et al.), pre-holiday in large caps (Ko and Yang), Monday effect.
- Unverified (NOT-OPENED): Intraday time-series momentum in VIX futures (J. Banking & Finance 148, 2023, RePEc listing only); Delta-hedging demand and intraday momentum, China (Physica A 2022, listing only).

## 6. Proposed test order for the research loop

1. Decompose open-to-close vs close-to-open returns for TOM windows (T-3..T+3 using actual last trading day of month; check T-2 after Sept 2017) on US500, NAS100, US30, GER40, UK100, JP225, development period only. Ask: is the TOM premium intraday at all?
2. INTRA-1 last-30-minute continuation on the same indices, with a realistic stop and CFD costs; report in R and bp; compare to long-only/always-long benchmark; check the 2020+ period separately from the dev split.
3. T-3 morning fade (TOM-C); only 12 events a year, so use as a conditional filter on INTRA-1, not as a stand-alone strategy.
4. Month-end FX fix drift (needs 5-minute FX).
Everything else in this report: do not build.

## 7. Source status table

| Source | Status |
|---|---|
| Etula et al. 2019 WP (Aalto PDF) | OPENED-FULL |
| Ko and Yang (CFR) | OPENED-FULL |
| Gao et al. 2015 WP | OPENED-FULL |
| Baltussen et al. JFE 2021 | OPENED-FULL (table 6 layout garbled) |
| Boyarchenko et al. NY Fed SR917 | OPENED-FULL |
| Lucca and Moench 2012 WP | OPENED-FULL |
| Cieslak et al. 2015 WP | OPENED-FULL |
| Breedon and Ranaldo 2010 | OPENED-FULL |
| Sproule and Gosselin MPRA 117001 | OPENED-FULL (only abstract and lit review used) |
| Quantpedia TOM page | OPENED-FULL (secondary) |
| McConnell and Xu 2008 | OPENED-ABSTRACT |
| Kurov, Wolfe, Gilbert 2021 | OPENED-ABSTRACT |
| McLean and Pontiff 2016; Hou, Xue, Zhang 2020 | OPENED-ABSTRACT (search summaries) |
| Garcia-Ares and Muravyev 2025 | OPENED-ABSTRACT |
| Melvin and Prins 2015 | OPENED-ABSTRACT |
| Zarattini, Aziz, Barbon 2024 | OPENED-ABSTRACT |
| Lakonishok and Smidt 1988; Ariel 1990; Schwert 2003; Stoll and Whaley; Fabozzi et al.; Dzhabarov and Ziemba; Giovanis; Fung et al.; Grant et al. | NOT-OPENED |
