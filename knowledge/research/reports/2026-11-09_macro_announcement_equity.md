# Equity index returns around scheduled macro announcements (day-trade view)

Date: 2026-11-09. Scope: US500 / NAS100 / US30 / GER40 CFD, open and close in one session, stop-defined, results in R.
Source status tags: OPENED-FULL (full text read, tables checked), OPENED-ABSTRACT (abstract/landing page or partial text only), NOT-OPENED (lead from a search summary only).
ATR conversion: 1.2% daily ATR = 120 bp, so 1 bp = 0.0083 ATR. A "1R" stop of, say, 0.5 ATR = 60 bp; gross bp / 60 = R before costs.

## Source ledger

| Id | Source | Status | Notes |
|---|---|---|---|
| LM | Lucca & Moench, JF 70(1) 2015, 329-371. Read the Oct-2012 NBER/NY Fed draft (conference.nber.org/conf_papers/f64395) | OPENED-FULL (working-paper draft; published JF text not read, numbers match later citations) | Tables 3, 4, 5, 7, 8, 10 |
| KV | Knox & Vissing-Jorgensen, FEDS 2026-023 (Aug 2025 draft), federalreserve.gov/econres/feds/files/2026023pap.pdf | OPENED-FULL (survey with own tables 4 and 5) | Only source here with 2011-2023 numbers |
| CMV | Cieslak, Morse, Vissing-Jorgensen, JF 74(5) 2019. Read the Oct-2015 draft (stern.nyu.edu) | OPENED-FULL (draft; sections 1-2, strategies) | |
| SW13 | Savor & Wilson, JFQA 48(2) 2013, "How much do investors care..." | NOT-OPENED (only via SW 2013 "Tale of Two Days" draft, wharton.upenn.edu, which restates the numbers) | Draft is OPENED-FULL |
| KSSW | Kurov, Sancetta, Strasser, Wolfe, ECB WP 1901 (2016), later JFQA 2019 | OPENED-FULL (ECB WP) | Directional pre-release drift, not a calendar drift |
| KWG | Kurov, Wolfe, Gilbert, Finance Research Letters 40 (2021), "The Disappearing Pre-FOMC Announcement Drift" | OPENED-ABSTRACT (abstract + intro text via PMC/distantreader; tables not seen) | Table values for bp not read |
| BGM | Boguth, Gregoire, Martineau, JFQA 54(6) 2019 | OPENED-ABSTRACT (Cambridge landing page); findings otherwise via KV and KWG text | |
| LM18 | Lucca & Moench, Liberty Street Economics 2018-11-16 "More Recent Evidence" | OPENED-ABSTRACT (fedinprint) | Claims drift continues only with press conference |
| BDR | Ben Dor & Rosa 2019 | NOT-OPENED (cited in KWG text I read): no drift Apr 2011 - Dec 2017 | |
| IO25 | Ignatieva & Ohashi, Applied Economics 57(17) 2025 | OPENED-ABSTRACT | Press-conference meetings only; sample not visible |
| Zhu | BIS WP 1079 (2023) | OPENED-ABSTRACT | Volume/liquidity explains ~1/3 of drift |
| Brusa-Savor-Wilson | Review of Finance 24(2) 2020, "One central bank to rule them all" | OPENED-ABSTRACT; finding re non-US banks quoted from KV text (OPENED-FULL) | |
| ECB-tone | JFQA 2024 "Does central bank tone move asset prices" (Euro Stoxx 50 around ECB, 13:45 CET) | NOT-OPENED (fetch of PDF failed; search summary only) | Reversal claim unverified |
| Quantpedia pre-ECB | quantpedia.com blog | OPENED-FULL but a blog, no bp/t-stats given | Not evidence-grade |
| QuantSeeker | quantseeker.com SPY pre-FOMC blog | OPENED-FULL but a blog | Not evidence-grade |

## 1. Pre-FOMC announcement drift (LM)

- Claim: S&P 500 average excess return of 49 bp in the 24 h before scheduled FOMC announcements, t > 4.5 (Huber-White), N = 131 meetings, Sept 1994 - March 2011 (LM Table 3 col 1; text p.6). KV Table 4 col 1 gives 0.49, t = 4.61.
- Window: 2:00 pm ET day -1 to 2:00 pm ET announcement day (announcement 2:15 pm; strategy sells ~15 min before). LM p.7.
- Annualised: 3.89% per year in the window vs 0.89% on all other days; more than 80% of the equity premium; Sharpe 1.14 (LM p.7, Table 3). Close-to-close FOMC-day differential only ~33 bp, Sharpe 0.84.
- Return from 2 pm to close on announcement day: about zero (LM Table 3 col 3). Sd of the 24 h return 1.2%, same as other days (LM Table 4), so about 0.4 sd per event.
- Pre-1994 (1970-1993, N = 236, announcement assumed day after): ~5 bp, insignificant, Sharpe 0.2 (LM p.7-8). KV cites a ~20 bp effect 1980-1993 and none 1960-1979.
- Intraday shape (LM Figure 1, text p.5): small rise in the afternoon before, sharp rise the morning of the FOMC day, index ~50 bp above prior-day open right before 2:15 pm, flat after the announcement and next day. The split between overnight and FOMC-morning is NOT given numerically in the text I read.
- E-mini futures: 54 bp (SPY 55 bp), t > 5, shorter samples (LM p.12, Table 10).
- International: DAX, FTSE, CAC, IBEX, SMI close-to-close FOMC-day dummy 29 bp (SMI) to 53 bp (CAC), all highly significant; Sharpe of an FOMC-only strategy 0.75-1.07. European closes precede 2:15 pm ET, so these are pure pre-announcement returns (LM Table 7, p.15). Nikkei no effect.
- Other US releases (claims, GDP advance, ISM, IP, housing starts, personal income): only ISM shows an announcement-day return, 23 bp; no significant pre-announcement returns (LM Table 8, p.10-11). CPI, NFP not in the nine releases.
- Data-mining check: authors compute the max t over ten announcement types by bootstrap; 4.48 exceeds the simulated distribution (LM section 4.1). Still one selected calendar anomaly in one sample.

## 2. Post-publication status of the pre-FOMC drift

Facts I verified:
- April 2011 - Dec 2023, 2pm-2pm S&P 500 window: coefficient 0.16 (i.e. 16 bp), t = 1.50, vs 49 bp t = 4.61 in the LM sample (KV Table 4 col 1 vs col 5; the PDF table text is garbled, column mapping read from the 2-col extraction; check the printed table before citing). Insignificant.
- KV text: since March 2011 the drift is "20 bp per meeting overnight" (night before the FOMC day), i.e. the effect moved to the overnight session. GFC outlier: ~180 bp per meeting over 15 meetings Mar 2008 - Dec 2009.
- BGM: April 2011 - Sept 2017, higher pre-FOMC return only at meetings with a press conference (KV text, OPENED-FULL; BGM itself abstract only). The press-conference framing is a rationalisation after the fact for a small N (~4 PC meetings per year).
- KWG (abstract + intro): extend LM to Dec 2019. Drift first present at press-conference meetings after 2011, then "essentially disappeared after 2015" in both PC and non-PC meetings. Their window starts at the previous day's stock market open (E-mini, open day -1 to 15 min before announcement). Pre/post zero-lower-bound lift-off (Dec 2015): post-ZLB indicator negative at 5%, post-liftoff mean drift not significant; mean VIX 17.7 pre vs 14.7 post. Attributed to reduced uncertainty; explicitly says it is not explained by McLean-Pontiff publication decay because drift persisted after the LM sample ended. bp values by period not seen.
- Ben Dor & Rosa (cited in KWG): no drift April 2011 - Dec 2017 (NOT-OPENED).
- LM18 (abstract): continued large excess returns, only for PC meetings. Contradicts KWG for 2016+ (different sample end/window).
- 2016-2021 summary: flat to weak. 2022-2025: no clean academic estimate found. KV covers to Dec 2023 and the 16 bp / t = 1.5 number is the pooled 2011-2023 value, so any 2020-2023 revival is at most inside that pooled number. QuantSeeker (blog, SPY close-to-close, to Dec 2024): "flat" 2016-2019, "regained momentum" 2020-2024, no numbers; a commenter lists SPY Fed-day returns 2021 -0.9%, 2022 +3.3%, 2023 +4.4%, 2024 -0.3% (unverified, annual sums). A CME note (June 2022, NOT-OPENED) said no drift in H1 2022. Treat 2022-2025 as unresolved, not as revived.
- Mechanism work: Zhu (BIS 2023) volume/liquidity explains ~1/3; Hu-Pan-Wang-Zhu (cited in KWG) uncertainty-resolution; Laarits, Ai-Bansal (risk premium models). Knox et al. option-implied FOMC-day equity premium is only ~1-2 bp higher (Aug 2016 - Dec 2023), far below the realised 49 bp, which suggests the original drift was mostly good news luck (KV section 5.4-5.5).
- Reversal: KV states post-FOMC returns reverse about 60% over a four-day window (Knox & Vissing-Jorgensen working result as summarised by search; NOT-OPENED in detail). Lee & Wang (RAPS 2025) say post-FOMC currency returns offset ~65% of pre-drift, mostly 12-24 h after (currencies, NOT-OPENED). These affect hold-through designs, not the pre-2:15 pm exit.

## 3. Announcement-day equity premium (SW13 and follow-ups)

- SW13 (via SW 2013 draft, OPENED-FULL, p.3): 1958-2009, announcement days (CPI or PPI, employment situation, FOMC from 1978) average excess return 11.4 bp vs 1.1 bp on other days; over 60% of the equity premium on 13% of days; volatility only ~4% higher. SW draft also quotes a 10.68 vs 0.93 bp version in a later NBER paper (search summary, NOT-OPENED).
- Differential ~10 bp = 0.08 ATR per announcement day, close-to-close, unconditional long. Not tradable as a day trade after spread/slippage and a stop. Roughly 60 days per year.
- Skeptic points: Ernst, Gilbert, Hrdlicka (2019) argue ex post selection of announcement types and no control for day of month bias SW; FOMC days still significant (KV text, OPENED-FULL). LM point out the SW result is driven by the FOMC pre-drift in the post-1994 data. CPI and NFP: no evidence of a pre-announcement return in LM Table 8 style tests (they were not in LM's nine). KSSW (2008-2014 E-mini, second data) finds a directional drift in the 30 minutes before several releases, correct sign only; the 7 strong announcements and their names were not extracted by me. Needs the surprise sign, so it is not a calendar rule. KSSW estimate ~USD 20m/yr total profits in the E-mini, i.e. scale is small and may be gone now.
- 2010s and later: no replication of SW with post-2009 data found. Unresolved.

## 4. ECB and other central banks

- Brusa, Savor, Wilson (RoF 2020; finding quoted in KV, OPENED-FULL): 1998-2016, no abnormal excess stock returns around non-US central bank meetings (euro area, UK, Japan, 8 others), even for German stocks around Bundesbank 1973-1998. Only Fed meetings show it, even for non-US stocks. Direct evidence against a pre-ECB drift.
- Quantpedia (blog, OPENED-FULL): in-house backtest of buying DAX/Euro Stoxx 50 at the D-2 close and selling at the D-1 close before the ECB press-conference day D0, samples from 1998 (DAX); no bp, t-stats or OOS split disclosed. Not evidence.
- JFQA 2024 tone paper (search summary only, NOT-OPENED): Euro Stoxx 50 pre-announcement drift before the 13:45 CET rate decision, fully reversed within 24 h. Needs opening before use; magnitude unknown.
- Valentin (post-ECB-announcement drift, in the direction of the announcement-time shock): NOT-OPENED. Its logic is a post-news continuation rule, which is a different candidate.
- Verdict: no verified, sized pre-ECB day-trade drift. Treat as unproven.

## 5. Intraday shape on FOMC days and the FOMC cycle

- LM Figure 1 and Table 3: price flat from 2 pm to close on FOMC day on average; the whole effect is before the statement. Volatility is below normal before the announcement and spikes at 2:00/2:15 pm (LM Figure 6; KV Figure 2, 5-min sd).
- Post-announcement: average announcement-window move is zero in the LM sample; surprises average out. Evidence of a reversal after the announcement (Knox et al. ~60% in four days; Lee-Wang for FX) means holding through 2:15 pm is a coin flip with fat tails, not a drift trade.
- CMV (Oct 2015 draft, OPENED-FULL): 1994-2013, ~160 meetings. Weekly (5-day) average excess return week 0 (day -1 to 3) 0.57%, week 2 0.30%, week 4 0.42%, week 6 0.61%; odd weeks about 0, -0.17%, -0.17%, -0.12%. Regression: +13.6 bp per day in week 0 and +10 bp per day in weeks 2, 4, 6 vs odd weeks, both significant at 1% (Table 1 col 1). Strategy "out of the market in odd weeks": Sharpe 0.8 vs 0.4 buy-and-hold (Table 3). Robust to three sub-periods (1994-2000, 2001-2007, 2008-2013) and in foreign stocks; authors say it held in 2014-2016 after the first draft.
- Replication status: KV (OPENED-FULL) 1994-2016: even-week days ~12 bp higher than odd-week days (Table 5 col 1; 11.48 bp, t-stat significant at 1% by the table stars). 2017-2021: statistically significant opposite cycle, even-week returns lower (S&P 500 excess about -12 bp, one-star; Table 5 col 5). The authors read it as news-worse-than-expected, not as data mining. A pooled 1994-2021 estimate would be near zero. No 2022-2025 test found. Vissing-Jorgensen (2020/2021) links the even-week returns to days with Fed official interactions (search summary, NOT-OPENED).
- Day-trade relevance: the cycle is a multi-day regime filter (go long only in even FOMC weeks), not an intraday rule. Its sign flipped out of sample.

## Candidate rules

All gross returns are before spread, slippage, and financing. US500 daily ATR taken as 1.2% = 120 bp. Events/yr: 8 scheduled FOMC meetings, ~12 ECB decisions.

### Rule A. FOMC-day morning drift (day-trade version of LM)
- Mechanism: pre-announcement fall in uncertainty and volume/liquidity effect, rising prices until the statement (LM; Zhu; KWG explanation).
- Entry: long at the US cash open 09:30 ET on FOMC announcement day (2:15 pm, or 2:00 pm since 2013 era; check the actual statement time per meeting). Exit: 13:45 ET (15 min before). Stop at e.g. 0.5 ATR below entry.
- Published evidence: only the full 24 h number exists (49 bp, 1994-2011). The 09:30 to 13:45 share is not in the text I read; from LM Figure 1 it is a large part but unquantified. Do not assume more than half. Plausible published-sample gross ~20-35 bp (0.17-0.29 ATR); this is my inference, flagged as such.
- Out-of-sample: 2011-2023 24 h figure 16 bp (t = 1.5, KV Table 4); the drift moved to overnight (20 bp per meeting). KWG: gone after 2015. So the intraday morning version has weak or no OOS support. Expected post-2015 gross: roughly 0-10 bp.
- Events/yr: 8. Small N: in 10 years N = 80; per-event sd of the 24 h window ~120 bp (LM Table 4), so se of the mean ~120/sqrt(80) = 13 bp; an effect of 15 bp is undetectable.
- Skeptics: published and decayed (KWG); good-news luck explanation (KV 5.5); option-implied premium only 1-2 bp.
- Verdict: testable but low prior. Treat as a falsification test on our own CFD data, not a trade.

### Rule B. Overnight lead-in (day -1 to FOMC open)
- The 20 bp per meeting overnight drift since March 2011 (KV, text only) is not a day trade (overnight). A day-trade proxy: buy at 15:00-15:50 ET day -1 (within a CFD session), exit at the day -1 close. LM Figure 1: "rises slightly" in that afternoon. Effect tiny. Not worth testing alone.

### Rule C. Fade or hold nothing through the statement
- Evidence says 2 pm to close mean ~0 (LM Table 3 col 3) with big variance. No edge for either direction. Only usable as an exit rule (flat before the statement) for A.

### Rule D. GER40 close-to-close before FOMC
- LM Table 7: DAX FOMC-day close-to-close dummy 29-53 bp across European indices, 1994-2011 (exact DAX value not extracted; range from p.15). A GER40 day-trade version: long at 09:00 CET on FOMC day to 17:30 CET close (before 20:00 CET statement), ~8 per year. The European close is before the statement, so it is pure pre-drift. OOS status unknown; US evidence says decay, so expect decay here too. Candidate for a cheap test with the same event list.

### Rule E. ECB-day
- No verified effect (Brusa-Savor-Wilson found none for non-US banks, 1998-2016). Not a candidate except as a null test.

### Rule F. FOMC even-week long-only filter
- 1994-2016: +10 to 13 bp per day on even-week days. 2017-2021 opposite sign. Not a day-trade entry. Use at most as a regime flag, with a pre-registered expectation of zero edge.

### Announcement-day premium (SW)
- ~10 bp/day, 60 days/yr. After costs of a CFD day trade roughly nil; a pure long on 60 days is also mostly just beta. Not worth a rule.

## What is dead or weak

- Generic announcement-day long (CPI/PPI/NFP/FOMC): small, unreplicated post-2009, dominated by FOMC.
- Pre-FOMC 24 h drift as published: gone post-2015 (KWG), insignificant 2011-2023 pooled (16 bp, t = 1.5).
- Pre-ECB drift: no peer-reviewed support for a durable long edge.
- Even-week FOMC cycle: sign flipped 2017-2021.
- Hold-through the statement: no edge.

## Cheapest next step

One falsification run on our own data: event list of 8 FOMC dates per year with actual statement time (2:00 vs 2:15 pm, 2:00 pm from 2013, 2:00/2:30 pm press conference era) for US500/NAS100/US30, and GER40 for rule D. Pre-register A: long 09:30 ET to 15 min before the statement; report gross bp, hit rate, mean R with a 0.5 ATR stop, split 2012-2015 / 2016-2019 / 2020-2025. Expect: ~0 after 2015. If the pooled mean is < 10 bp, retire the family. I did not do this test.

## Gaps

- LM published JF text, KWG tables (bp by period), BGM full text, SW13 JFQA text, the JFQA 2024 ECB paper and Brusa-Savor-Wilson full text were not opened.
- No 2022-2025 academic estimate for the pre-FOMC drift; no post-2009 SW update; no 2022+ FOMC-cycle test.
- FOMC statement times changed (2:15 pm to 2:00 pm from 2013 per KV; confirm against the actual calendar before any backtest).
