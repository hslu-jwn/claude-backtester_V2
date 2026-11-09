# Index intraday momentum and related day-level effects: literature notes (2026-11-09)

Scope: can a day trade on index CFDs (US500, NAS100, US30, GER40, UK100, JP225), stop-defined, results in R, use the published intraday return predictability? Cost assumption: US500 round trip about 0.5-1 point = 1-2 bp.

Source status: OPENED-FULL = full text downloaded and read via pdftotext (key sections, not every page). OPENED-ABSTRACT = abstract or summary page only. NOT-OPENED = known only from search snippets. "Derived" = my arithmetic, not a paper number. Table numbers refer to the opened version.

## 0. Bottom line

- The signal in the literature is NOT first-30-minute continuation over the rest of the day. It predicts the LAST 30 minutes from (a) previous close to first 30 min (Gao, r1 includes overnight) or (b) previous close to 30 min before close (Baltussen, rROD). I-09 ("no first-30-minute continuation", price-only, 2018-2026) tested a different target, so it does not contradict either paper.
- Gross edge per trade is about 2.5-4 bp on average, a trade every day, against a half-hour move with a standard deviation of about 40 bp. With a 1-2 bp cost this is a thin edge (net about 0 to +0.05 R, derived). It is a late-session, short-hold trade, and stops barely fit inside a 30-minute window.
- Post-2018 evidence: one non-peer-reviewed SPX test (2022-2026) finds nothing unconditional. Zarattini et al. (2024) is a different, all-day breakout rule and is not a replication.
- Overnight/intraday "tug of war" (Lou, Polk, Skouras) and end-of-day reversal are cross-sectional stock effects. They do not give a single-index day-trade rule.

## 1. Gao, Han, Li, Zhou (2018 JFE 129(2), 394-414), "Market intraday momentum"

Status: OPENED-FULL (working-paper version "Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return", pdf from c.mql5.com; the published JFE version was not opened, so published numbers may differ). Abstract page of the JFE version: OPENED-ABSTRACT via RePEc.

- Sample: SPY (S&P 500 ETF), 1 Feb 1993 - 31 Dec 2013, half-hour returns from TAQ. Also 10 other ETFs and two international index futures (FTSE-type FT, XX).
- Signal definition: r1 = first half-hour return measured FROM THE PREVIOUS DAY'S CLOSE (p0,t = p13,t-1). So overnight gap + first 30 min. Target r13 = last half-hour return (15:30-16:00).
- Predictive regression (Table 1): slope 6.94 (x100), significant at 1%, R2 = 1.6%. Adding the 12th half-hour: in-sample R2 2.6%.
- Out-of-sample R2: 1.2% (r1 only), 1.8% (r1 + r12). Certainty-equivalent gains about 6.35% and 6.44% p.a. (risk aversion 5).
- Timing strategy using sign of r1 (Table 4): 6.67% p.a., sd 6.19%, Sharpe 1.08, skew 0.90, versus Always Long in last half hour -1.11% p.a. (Sharpe -0.18) and Buy&Hold 6.04% p.a. (Sharpe 0.29). Trades every day, so the signal appears on 100% of days.
- Conditioning: stronger on high-volatility days, high-volume days, recession days, and macro-release days (Sharpe 2.10 in recessions vs 0.66 expansions).
- Costs (Section 5.2, Table 10): costs taken as the TAQ half spread at 15:30 (no spread at the closing auction). After July 2001: 4.46% p.a. net, 2.47 points lower than gross. From 2005 (proportional spread about 1.2 bp): 6.52% net vs 7.96% gross; combined (r1,r12) rule 4.74% net vs 5.50% gross. Commissions ignored (footnote 12).
- Futures check (Table 13): FT futures r1 only: in-sample R2 1.90%, OOS R2 1.87%, average return 1.84% p.a., Sharpe 0.43.
- Per-trade, derived: 6.67% / 252 = about 2.6 bp per day gross; 7.96% / 252 = about 3.2 bp (2005+). Std of the daily trade = 6.19% / sqrt(252) = about 39 bp. Net 2005+: 6.52% / 252 = about 2.6 bp.

## 2. Baltussen, Da, Lammers, Martens (2021 JFE 142(1), 377-403), "Hedging demand and market intraday momentum"

Status: OPENED-FULL (published JFE version, pdf from academicweb.nd.edu/~zda/intramom.pdf).

- Sample: 60+ futures (equity, bond, commodity, currency), Dec 1974 - May 2020. Equity: ES from 1982-04, DAX (DA) from 1997-01, FTSE 100 (FT) from 1998-07, Nikkei 225 SGX (EN) from 1997-04 (Appendix table).
- Signal: rROD = return from previous market close to 30 minutes before close (includes overnight). Gao's rONFH is the first-half-hour variant. Target: last 30 minutes (rLH).
- Pooled equity regression (Table 2, Panel A): rONFH slope 4.86 (t 6.52), R2 1.49%, R2OOS -1.71%. rROD slope 4.18 (t 7.29), R2 2.45% (pooled adjusted), R2OOS 2.88%. rM and rSLH also significant, so the whole day carries information, not just the opening.
- Single-market (Appendix Table B1 / table with ES etc., slopes x100, R2 %, R2OOS %): rROD slope / R2 / R2OOS: ES 6.18 / 3.41 / 2.29; NQ 6.36 / 4.10 / 3.76; YM 5.02 / 2.20 / 2.18; DAX 3.42 / 2.13 / 0.42; FTSE 100 (FT) 4.28 / 3.09 / 2.03; Nikkei SGX (EN) 2.70 / 1.30 / 1.20; Euro Stoxx (SW) 1.98 / 0.80 / 0.37. For ES, rONFH alone has R2OOS -1.68%, so Gao's predictor fails out of sample on ES while rROD works. Weak or absent: IB 0.93 (t 1.45), XP 1.05 (t 1.73), PT 2.12.
- Subsamples (Table 5): effect present in both 1974-1999 and 2000-2020; equity rROD slope appears to fall from 5.96 (1974-99) to about 3.98 (2000-20) (pdf layout garbled, treat as approximate). The paper says results are "similar" in both halves.
- Timing strategy, equity index futures, 1/N portfolio (Table 6): rONFH avg 4.21% p.a., sd 3.95%, SR 1.07, success rate 0.55; rROD avg 6.86%, sd 3.96%, SR 1.73, success 0.55; (rONFH and rROD agree, no trade otherwise): 5.47%, SR 1.60, success 0.61. Always Long last half hour: 0.44%, SR 0.11. Derived: 6.86% / 252 = about 2.7 bp per day gross for an equal-weight basket; the single-market sd is higher than the basket's.
- Costs: the paper states it does NOT model transaction costs (p. 386); only says a one-tick assumption still leaves a positive net Sharpe in S&P 500 futures, with no number. So "SR 1.73" is gross.
- Gamma channel: the effect is stronger when S&P net gamma exposure is negative (Table 7/8); leveraged-ETF rebalancing demand adds explanatory power (Table 9). Predictive power reverts over the next days (Table 11).
- Session caveat (Table 12, extraction approximate): in the S&P 500 cash index with 16:00 close, rROD slope about 5.98, R2 about 3.28%. In the futures panel (16:15 close) the later segment shows no significant predictability. The authors argue hedging happens before the cash close. A CFD that tracks the futures after 16:00 ET or has a 16:15 close should test the exact 15:30-16:00 ET window, not the CFD session close.
- Per-trade, derived: ES slope 0.0618 x typical |rROD| of about 0.5-1.0% gives a conditional last-half-hour edge of about 3-6 bp, more on big days. Predictable R2 is only 3.4%, so most of the half-hour variance (sd about 35-45 bp) is noise.

## 3. Replications, decay, failures (2018-2025)

| Item | Status | Finding |
|---|---|---|
| Firmtape blog "Is intraday momentum still alive? ... 1,085 SPX sessions of the 0DTE era" (dev.to) | OPENED-ABSTRACT (WebFetch summary; vendor blog, not peer reviewed; methodology not independently checked) | SPX 2022-04-14 to 2026-08-20: rROD slope on last 30 min +0.006 +/- 0.009 (t 0.6), each year |t| <= 1.0 with alternating sign (2022 +0.009, 2023 +0.002, 2024 -0.016, 2025 +0.016, 2026 -0.012). Conditional on a self-built short-gamma proxy: +0.055 (t 3.1) on about 15% of sessions, author calls it "not worth a position". Slope units unclear (not x100 of Baltussen). Weak evidence, but it is the only direct recent test found. |
| Zarattini, Aziz, Barbon (2024, SFI RP 24-97), "Beat the Market" | OPENED-FULL (pdf from alexandria.unisg.ch) | Different rule: 14-day time-of-day "noise area" breakout from the open plus overnight gap, entries on 30-min checks, VWAP trailing stop, exit at close. SPY 2007-05 to 2024-04, IB commission $0.0035/share + $0.001 slippage. Unlevered, 100% size, stop at opposite band: 6.2% p.a., vol 10.9%, SR 0.61, 5,494 trades. Current band + VWAP stop: 9.7% p.a., vol 7.7%, SR about 1.24, 7,668 trades. Volatility-targeted with leverage capped at 4x: 19.6% p.a., vol 14.3%, SR 1.33, MDD 25%, win rate (daily) about 43%. Backtest authors are practitioners, in-sample parameters, SPY not CFD. The headline needs leverage. It is not an independent test of Gao/Baltussen. |
| Liu and Tse (2017) | NOT-OPENED (secondary: hull-repository snippet) | Reported: for S&P 500 ETF and 12 international index futures the first half-hour return did not predict the last half hour, but the overnight return did. Needs verification. If true it matches I-09 (first 30 min alone is weak) and supports an overnight-gap rule. |
| Elaut, Frömmel, Lampaert (2018, J Fin Markets 37, 35-51) | OPENED-ABSTRACT (RePEc) | RUB/USD MICEX 2005-2014 only. Momentum attributed to liquidity providers avoiding overnight inventory. Not an index paper; no decay evidence. |
| Zhang, Ma, Zhu (2019, Econ Modelling 76, 319-329) | NOT-OPENED (RePEc/search snippets) | Chinese stocks: first and/or 7th half-hour predict the last half hour. China only. |
| Li, Shen, Wang, Zhang (2020 FRL 35), Chinese stock index futures | NOT-OPENED (title only) | Findings not seen. |
| EFMA 2024 "Interday Cross-Sectional Momentum" | NOT-OPENED (server 503; only a search snippet said the US last-half-hour effect weakened about 75% out of sample and is not significant in Europe or Canada) | Treat as unverified. |
| Aalto thesis "Intraday momentum in futures markets" (20 indices/bonds/FX, 2008-2024) | NOT-OPENED (403; search snippet only) | Snippet: effect still present, concentrated in last 10 minutes, many strategies may not survive costs. Unverified. |
| Julin (Orebro MSc thesis 2024) | OPENED-ABSTRACT (pdf abstract) | OMXS30 and 5 stocks, only Mar 2023 - Feb 2024: weak predictability, "not sufficiently strong to support consistent trading strategies". One year only. |

Net status: no peer-reviewed decay study found. No published test on 2019-2024 US500/NAS100 with costs that I could open. Treat the effect as: alive in the Baltussen sample through May 2020 (the authors say the last four months of that sample, Feb-May 2020, were strong), unproven since, and the only recent test is a vendor blog showing zero unconditional slope.

## 4. Related effects

- Lou, Polk, Skouras (2019 JFE 134(1), 192-213), "A tug of war": OPENED-ABSTRACT (search result + LSE page). Cross-sectional stocks: momentum profits accrue overnight, short-term reversal/size etc. intraday, offsetting. Not an index timing rule. A newer working paper by the same authors (LSE FMG DP961, July 2026; OPENED-FULL abstract/intro only) says smoothed past overnight market returns negatively forecast quarterly (not daily) close-to-close market returns, and smoothed intraday returns positively forecast overnight. Quarterly horizon, so useless for a day trade. A claimed daily-level "day destroys the night" index reversal was only a search-result paraphrase and was not seen in the paper text: NOT verified at daily frequency.
- Bogousslavsky (2021 JFE 141(1), 172-194), "The cross-section of intraday and overnight returns": OPENED-ABSTRACT (search snippets only). Stock anomaly returns are weak at the end of the day because arbitrageurs cut positions before the close. Cross-sectional, no index rule.
- End-of-day reversal: the paper I opened is Baltussen, Da, Soebhag (April 2025), "End-of-Day Reversal" (OPENED-FULL pdf, intro read). It is cross-sectional: ROD3 (overnight + first half-hour + middle) negatively predicts individual stocks' last-half-hour returns, long-short 3.78-6.86 bp per day (9.5-17.3% p.a.), t-stat above 10 in sorts. The authors state it is distinct from and opposite to market-level intraday momentum. It needs a stock portfolio, not index CFDs. (The "Bogousslavsky 2021 end-of-day reversal" label in the task is a different paper; Bogousslavsky 2016 is about infrequent rebalancing.)
- Cheng and Madhavan (2009, J Investment Management 7(4), 43-62), leveraged ETF rebalancing: NOT-OPENED (search only). Reported: daily re-leveraging amplifies close volatility. A Fed note (Tuzun 2013, FEDS 2013-48; NOT-OPENED) is quoted as estimating about $1.04bn of rebalancing demand per 1% index move on $20.14bn of leveraged-ETF NAV at 15 Dec 2011, a 2011 figure. Baltussen et al. Table 9 uses this channel: effect is real but modest in R2.
- Opening-gap reversal/fill on indices: no peer-reviewed study found. Only vendor stats (roughly 60-70% full-gap fill on ES, no method, no sample size) and a caution that small gaps fill mostly by arithmetic. Dead until we test it ourselves on I-09's data.

## 5. Edge per trade versus cost and stop

Setting: US500 daily ATR about 1.2% = about 120 bp. Stop 0.25-0.5 ATR = 30-60 bp. Last-half-hour sd about 35-45 bp (derived from Gao sd 6.19% / sqrt(252) = 39 bp). Cost 1-2 bp round trip.

| Rule | Gross bp per trade (derived from paper annual returns / 252) | Share of days with signal | Net after 1-2 bp | In R with a 30 bp stop (derived) |
|---|---|---|---|---|
| Gao r1 (prev close to 10:00) sign -> last 30 min | about 2.6-3.2 bp (6.67%, 7.96% 2005+) | 100% | about 0.6-2.2 bp (Gao's own 2005+ net is 6.52% = about 2.6 bp at spread 1.2 bp) | gross +0.09 R, net +0.02 to +0.07 R |
| Baltussen rROD (prev close to 15:30) sign -> last 30 min, equity basket | about 2.7 bp (6.86%, SR 1.73 gross) | 100% | about 0.7-1.7 bp | gross +0.09 R, net +0.02 to +0.06 R |
| Baltussen rROD with rONFH agreeing (both signs equal) | 5.47% / (252 x 0.61 days?) not given; treat as 2.2 bp per calendar day, but trades only on days when both agree (share not reported, success 0.61) | below 100% (not reported) | not reported | not computable |
| Baltussen rROD on big |rROD| days only (conditioning on gamma/volatility) | not reported; slope 4-6 x 0.01 x |rROD| suggests 5-10 bp when |rROD| is 1-2% | maybe 20-30% of days (my guess, unverified) | not reported | worth testing |
| Zarattini noise-area breakout | 5.5 bp per calendar day for the levered portfolio (9.7% p.a. unlevered after IB costs on SPY = about 3.8 bp per day) | 5,494-7,668 trades over about 4,300 days | costs already in (SPY, not CFD) | stop is VWAP/band, not fixed R |
| Cross-sectional rules (end-of-day reversal, tug of war) | 3.8-6.9 bp per day for a stock portfolio | not applicable | not applicable | not applicable to index CFDs |

Reading the table: the signal is a probability tilt (success rate about 53-55%, 61% when both predictors agree), not a large move. A fixed 30-60 bp stop is wider than the expected move, so the stop will mostly be a catastrophe stop and the exit will be the close. Costs eat 30-70% of the gross edge. A 0.5-point spread on a 5,500-index US500 is 0.9 bp; 1 point is 1.8 bp.

## 6. Does I-09 conflict with the literature?

No, because the objects differ.
- I-09: first-30-minute return continues over the rest of the day (price only, NAS100 and US500, 2018-2026). Gao and Baltussen do not claim this; Baltussen's own Table 2 shows rONFH alone has R2OOS -1.71% for the pooled equity group and -1.68% for ES, i.e. the first-half-hour predictor is the weak one.
- Gao/Baltussen: previous close -> first 30 min or -> 15:30 predicts only the 15:30-16:00 return. The overnight gap is part of the predictor.
- Liu and Tse (NOT-OPENED) are said to find that overnight, not first 30 min, carries the signal, which would also be consistent with I-09.

## 7. Candidate rules to test (not yet tested here; nothing below is claimed profitable)

1. Baltussen rROD rule on US500/NAS100/US30/GER40/UK100: signal = sign of (price at T-30min minus previous cash close); enter at T-30min at the cash close of the underlying; exit at close (or T-5min); catastrophe stop 0.25-0.5 ATR. Test in two variants: all days, and only days where |rROD| exceeds its 14-day or 60-day mean (volatility/gamma proxy). Evidence: published through May 2020 with R2OOS 2-4% on ES/NQ/YM, 0.4-2% on DAX/FTSE, 1.2% Nikkei; recent decay unproven. Check session times of each CFD: US 15:30-16:00 ET (not the futures 16:15 close), DAX futures 17:00-17:30 CET.
2. Agreement filter: trade only when sign(rONFH) = sign(rROD) = sign(overnight gap). Baltussen Table 6 shows success 0.61 vs 0.55 and SR 1.60 vs 1.73 (lower SR, fewer trades), so it raises hit rate but cuts days. Evidence status: published, small gain, no cost line.
3. Negative control: the Firmtape result (zero unconditional slope 2022-2026) is the null to beat. Run the identical regression on our data split by year 2019-2026 and report slope, t, and net R. If 2022+ is flat, drop rules 1 and 2.
4. Zarattini noise-area breakout is a separate hypothesis (all-day breakout, VWAP trailing stop). Unlevered Sharpe 0.61-1.24 on SPY, 17 years, practitioner paper; only worth a test if framed as trend-day breakout, not as a replication of Gao.

## 8. Dead or not usable for these CFDs

- Gao first-half-hour rule on ES-like data out-of-sample (Baltussen: R2OOS -1.7%); use rROD instead.
- Cross-sectional end-of-day reversal and Lou-Polk-Skouras tug of war (stock portfolios; quarterly index horizon).
- Opening-gap fade/fill as an academic edge: no evidence found, only vendor claims.
- Currency/FX intraday momentum (Elaut) and Chinese or OMXS30 single-market evidence: not our markets.
- Any claim that the Baltussen Sharpe of 1.73 is net of costs: it is gross.

## 9. Gaps in this review

- JFE published Gao version, Liu and Tse, Zhang/Ma/Zhu, Li et al., EFMA 2024, Aalto thesis, Cheng and Madhavan, Tuzun, Bogousslavsky 2021 full text, and Lou-Polk-Skouras 2019 full text were not opened.
- Per-trade bp and R-values are my arithmetic from annualised returns and sds; none of the papers reports average bp per trade or days-with-signal for CFD-style rules.
- Table cell values from Baltussen were read from pdftotext layout and a few cells (subsample R2, Table 12 panel split) are garbled; the numbers marked approximate should be checked in the PDF before use.
