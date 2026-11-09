# EUR/USD intraday and session effects beyond Breedon-Ranaldo (2026-11-09)

Scope: published intraday or session-level effects in EUR/USD that could be a stop-defined same-day trade.
Already covered and not repeated: Breedon & Ranaldo 2013, Krohn/Mueller/Whelan 2024, Mueller/Tahbaz-Salehi/Vedolin 2017 (FOMC), London 4pm fix reversal.

Status tags: OPENED-FULL = text read via pdftotext; OPENED-ABSTRACT = abstract or catalogue page only; NOT-OPENED = known only from search snippets or memory.
No effect size below is invented. Where a number is missing, the entry says so.

## Verdict

Nothing found beats the Breedon-Ranaldo session rule. No paper offers a published, post-2010, net-of-cost, M1-plus-calendar-only rule on EUR/USD.

- Best remaining candidates are weak and unproven on our data: a Monday/Friday day-of-week filter on the BR rule (OPENED-ABSTRACT only) and last-30-minute intraday momentum (stat. weak for FX).
- The event-driven effects (ECB, NFP/CPI) need surprise values (actual minus consensus). Our calendar's actual/forecast values are not point-in-time verified, so they are not testable honestly.
- Month-end hedging is too small to trade.

## 1. ECB decision days and press conferences

### Conrad & Lamla (2007), "The High-Frequency Response of the EUR-US Dollar Exchange Rate to ECB Monetary Policy Announcements" - OPENED-FULL (working paper, KOF/ETH, Sept 2007)
- Sample: 89 ECB meeting days, 01/1999-10/2006. 5-minute EUR/USD. Events (CET): press release 13:45, press conference introductory statement 14:30, then Q&A.
- Result for direction: on announcement days "no significant effects in the mean" for the time-of-day dummies; only variance dummies are significant at 13:50 and 14:45 (not 14:35). Pre-release dummy at 13:45 insignificant (their lines ~848-858).
- Direction depends on surprises: a surprise in the rate decision moves EUR/USD right after the release; a negative surprise needs about 20 minutes to become significant (their line ~931). Communication about future inflation matters during the statement.
- No tradeable drift rule, no bp-per-trade, no costs. Pre-2007 sample, pre-ZLB. Post-publication: not applicable (event study).
- Needs: M1 + calendar is NOT enough. Needs rate-decision surprise (OIS/consensus).
- Verdict: dead for us (unconditional mean is zero; conditional needs surprise data).

### Valentin, "The Post-ECB Announcement Drift" - OPENED-ABSTRACT (AEA 2023 program page, search summary; PDF at acfr.aut.ac.nz returned HTTP 403)
- Equities and euro-area government bonds only: drift continues up to 20 days in the direction of the intraday reaction during the press conference, not the press release. No FX result found.
- Verdict: no EUR/USD evidence. Multi-day anyway. Dead for a same-day trade.

### Fanta (2025), ECB communication outside meeting days, EUR/USD 1-minute, 2008-2016, 1,868 statements - OPENED-ABSTRACT (IDEAS page for wp2025_23)
- Cumulative abnormal returns "within a few basis points by t=+20" (minutes); no lasting directional move; scattered significant minutes; dovish statements give a brief volatility drop.
- Verdict: dead (a few bp, no drift, no rule).

### Gaps
- No academic pre-ECB-meeting drift study for EUR/USD found (search only; NOT-OPENED anything). Pre-FOMC dollar drift exists (Karnaukh; Mueller et al.) but FOMC is out of scope here.

## 2. US macro releases (NFP, CPI)

### Evans & Lyons (2005), "Do Currency Markets Absorb News Quickly?" JIMF 24(2), 197-217 - OPENED-FULL (NBER WP 11041 text)
- Daily data, USD/EUR (synthetic DM-based pre-1999), Citibank customer order flow, 11 Apr 1993 - 30 Jun 1999, 30 US and 13 German scheduled announcements.
- NFP: a +1 s.d. non-farm employment surprise gives a 24 bp appreciation of the dollar on the announcement day (Table 2, their text ~line 397).
- Follow-through: end-user order flow reacts for days; the cumulative return response over the following 4 days is significant only with negative sign, i.e. partial reversal of the initial impact (Table 5; e.g. unemployment claims: euro depreciated about 17% of the initial impact on following days).
- Edge: multi-day partial reversal, in-sample, daily, needs the surprise s.d. No cost analysis. Sample is 1993-1999.
- Needs: surprise values. Not same-day.
- Verdict: dead for our purpose (daily, pre-euro, requires point-in-time surprises).

### Andersen, Bollerslev, Diebold, Vega (2003, AER), Chaboud et al. (2014, "Rise of the Machines"), Faust/Rogers/Wang/Wright (2007) - NOT-OPENED
- Known only from titles/snippets in search. Cited consensus: price jump within seconds/minutes, volume and volatility 15+ seconds later (Fed IFDP 903 snippet). No continuation/reversal rule with net-of-cost P&L found.

### Other items seen
- "Sign switch effect of macroeconomic news in FX markets" (Bilkent; US news 2005-2012, 10-min response): the reaction sign flips during Jul 2008 - Jan 2009. NOT-OPENED. Supports instability of any news-direction rule.
- Master thesis (Jandejsek, MODUL): 237 NFP events 2000-2020, impact magnitude declining 2017-2020. NOT-OPENED (snippet). Weak source.
- Broker education pieces (forex.com, FXEmpire): NFP "V-shaped reversal" 10-120 min. Marketing, no tests. Do not use.
- Robotwealth 2020 blog: EUR/USD pre-NFP drift in the direction of a bullish release, single informal backtest. NOT-OPENED.

Verdict: the only quantified, post-announcement result requires the surprise sign. Without verified point-in-time actual/forecast this cannot be tested honestly. Dead as a calendar-only rule. A possible unsigned variant (fade or follow the first 5-minute return after NFP at 13:30 UTC) has no published support found.

## 3. Weekend/Monday, Friday, month-end

### Popovic & Djurovic (2014), Applied Economics 46(32), 3968-3979 - OPENED-ABSTRACT (IDEAS)
- Hourly EUR/USD, 1 Jan 2004 - 11 Jan 2014, Swiss FX market quotes. ANOVA, t-tests, Tukey HSD for day, hour, day-by-hour.
- Best pair: Fridays, sell USD / buy EUR at 00:00, sell EUR / buy USD at 03:00 same day (clock timezone not stated in the abstract; Swiss time presumably). No return numbers in the abstract.
- Concerns: 3-hour holding in the quietest hours (spread widest relative to range), data-mined cell from a day x hour grid, no cost treatment visible. Full text NOT-OPENED.
- Needs only M1 + date. Testable cheaply, but treat as data-mining until a holdout confirms it.
- Verdict: do not trade; at most one logged hypothesis with a pre-registered test on 2015-2021 vs 2022+.

### Ahmed et al. (2021), 15 currencies, hourly E-GARCH day dummies - NOT-OPENED (search snippet)
- Currencies depreciate Monday and Wednesday, appreciate Friday. Direction convention vs USD unclear from snippet. No sizes.

### Seasonax (practitioner, daily): EUR/USD 2000-Feb 2018, Monday weak, Friday strong - NOT-OPENED, not peer-reviewed. Do not rely on it.

### Melvin & Prins (2015), "Equity hedging and exchange rates at the London 4pm fix", J. Financial Markets 22, 50-72 - OPENED-FULL (ECB FX workshop version, Nov 2013)
- Rule implied: on the last London trading day of the month, from 15:00 to 16:00 London, trade against the sign of the relative country equity return over the month through day T-1 (equity up -> currency down).
- Sample: 5-minute TWAP, 28 Apr 2004 - 31 Dec 2012, 10 G10 currencies, panel regression (eq. 4): r_FX = -0.0142 x r_EQ, R2 = 0.03 (F = 25.52). Implied: 10% relative equity appreciation -> 14 bp currency depreciation in that hour. The authors themselves call it small. A typical 1-3% relative move gives roughly 1.5-4 bp (arithmetic from their coefficient, not quoted).
- Month-end NBFI flows: about 0.5 bn EUR per 1% equity move; 5% -> about 2.5 bn EUR at the fix (Table 3 text).
- Partial reversal the day after the fix.
- Trades/year: 12 at most, and the sign needs EZ minus US monthly equity return (daily index data, not in M1).
- Size vs our cost: even 4 bp (about 0.4 pip) vs spread plus slippage of about 0.5-1 pip means negative after cost. Also the 4pm fix leg is close to the already rejected fix reversal.
- Verdict: dead (size, 12 trades/year, needs equity data). Note for later: 2004-2012 sample, no post-publication test found.

## 4. Intraday momentum / reversal

### Baltussen, Da, Lammers, Martens (2021), "Hedging demand and market intraday momentum", JFE 142(1), 377-403 - OPENED-FULL (full PDF, academicweb.nd.edu)
- Rule: sign of rest-of-day return (open to 30 min before close) predicts the last-half-hour return. Strategy: long last half hour if rROD > 0, else short.
- Currency futures: 8 US-listed contracts (including Euro FX; table shows contracts, but the pooled panel is 1/N across the 8), sample Dec 1974 - May 2020; "open"/"close" for FX futures set from volume spikes at 08:21 and 15:00 ET (settlement at 15:00 ET).
- Evidence for currencies is the weakest asset class: rONFH has slightly higher t-value and R2 than rROD; rROD and rONFH coefficients positive but insignificant in the opposite-sign split (Table 3 discussion); only about 40-50% of the individual currency contracts have positive significant out-of-sample R2 (Table B4 discussion).
- Table 6 Panel D: currency timing-strategy Sharpe ratios roughly 0.4-1.0 for rONFH / rROD variants (portfolio of 8, gross, annualised; individual EUR numbers NOT read from tables because the text extraction was garbled).
- Last-half-hour reversal the next day is not significant in currency futures.
- Time scale: last 30 minutes before 15:00 ET (about 14:30-15:00 ET, 19:30-20:00 London). That window is 30 minutes long; average absolute size per trade not extracted. A stop of 0.5 daily ATR is far wider than the move, so R per trade would be tiny and the cost of 0.02 R per round trip would likely dominate.
- Mechanism: gamma hedging by option dealers and leveraged ETFs. No FX evidence for that channel (they lack FX LETF data).
- Post-publication: no replication in FX found.
- Needs only M1 (execution at known clock times).
- Verdict: weak, thin, probably cost-limited. Not a priority.

### Elaut, Frömmel, Lampaert (2018), "Intraday momentum in FX markets: disentangling informed trading from liquidity provision", J. Financial Markets 37, 35-51 - OPENED-ABSTRACT (EconPapers/IDEAS summaries; PDF fetch returned 403/invalid)
- Per the summaries, the first-half-hour return predicts the last-half-hour return in the RUB/USD market (MICEX trading hours, 2005-2014 in the Lampaert thesis). Stronger in crises; attributed to liquidity providers' overnight inventory aversion.
- Not EUR/USD and not a 24-hour market; Baltussen et al. note the same difficulty for FX futures.
- Verdict: not transferable to EUR/USD.

## 5. Replications of Breedon-Ranaldo (2015-2025)

- No true replication of the local-hours depreciation pattern for 2015-2025 was found in search (OPENED-ABSTRACT level only; no paper tested EUR/USD after 2013).
- Krohn/Mueller/Whelan (2024) cite it as established and show fix reversals (already covered).
- A 2024 crypto paper (Springer, Review of Quantitative Finance and Accounting, "tea time") cites Ranaldo (2009) for FX local-hours patterns and finds time-of-day structure in crypto; NOT-OPENED, not FX.
- Secondary summary says the pattern is not profitable for most pairs after spread; the SNB working-paper abstract says EUR/USD is profitable (hourly data 1997-May 2007). Our own result (+0.042 R/trade net, 2015-2021, EUR/USD) is the only post-2010 test available.
- The next honest step is an out-of-sample test of the BR rule on 2022-2025 data and on 2008-2014 (pre-sample plan already exists in knowledge/research/reports/2026-11-09_presample_2008_2014_plan.md).

## Summary table

| Effect | Source | Status | Gross size | Trades/yr | Needs beyond M1 + calendar | Verdict |
|---|---|---|---|---|---|---|
| ECB decision day direction | Conrad-Lamla 2007 | OPENED-FULL | mean not significant | ~8 | rate surprise | dead |
| Post-ECB press conf drift | Valentin | OPENED-ABSTRACT | equities/bonds only, no FX | ~8 | surprise/ reaction | dead (no FX) |
| ECB non-meeting comms | Fanta 2025 | OPENED-ABSTRACT | few bp by +20 min | n/a | text coding | dead |
| NFP/CPI follow-through | Evans-Lyons 2005 | OPENED-FULL | 24 bp per 1 s.d. NFP surprise, partial reversal over 4 days | 12 (NFP) | verified surprise | dead (daily, 1993-99) |
| Month-end fix hedging | Melvin-Prins 2015 | OPENED-FULL | 14 bp per 10% rel. equity move, 1 hour | <=12 | monthly equity returns | dead |
| Last-30-min momentum | Baltussen et al. 2021 | OPENED-FULL | currencies weakest asset class | ~250 | none | thin, probably cost-limited |
| Friday 00:00-03:00 | Popovic-Djurovic 2014 | OPENED-ABSTRACT | not stated | ~50 | none | data-mined, hold for holdout |
| Day-of-week (Mon weak / Fri strong) | Ahmed 2021 / Seasonax | NOT-OPENED | not stated | ~50 | none | unverified |
| BR replication post-2013 | none found | - | - | - | - | no independent confirmation |

## Open issues
- Papers not opened: Andersen et al. 2003, Chaboud et al. 2014, Faust et al. 2007, Elaut et al. 2018, Valentin full text, Ahmed 2021, sign-switch paper.
- Baltussen Table 6/B4 EUR-specific rows were not read because the extraction was garbled; re-extract with another tool before citing any number for EUR.
- Everything event-based hinges on a point-in-time surprise source (e.g. Bloomberg/Reuters consensus snapshot); our calendar lacks it.
