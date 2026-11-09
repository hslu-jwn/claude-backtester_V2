# FX / gold time-of-day research notes (2026-11-09)

Scope: intraday session / time-of-day patterns in spot FX and gold as possible CFD day trades. All pip conversions assume EURUSD ~1.10 (1 bp = 1.1 pip). Annualised -> per day uses 260 trading days. Nothing here is a backtest result of ours.

## Source status

| Source | Status |
|---|---|
| Breedon & Ranaldo, SNB WP 2011-04 (pre-print of JMCB 2013, 45(5), 953-965) | OPENED-FULL (PDF text, pdftotext). Final JMCB text NOT-OPENED (paywall). |
| Mueller, Tahbaz-Salehi, Vedolin 2017 JF 72(3) 1213-1252 (LSE accepted version) | OPENED-FULL (text extracted, key tables read via search of text; not every table) |
| Krohn, Mueller, Whelan "FX fixings and returns around the clock" (Bank of Canada SWP 2021-48; JF 2024, 79(1), 541-578) | OPENED-FULL (working paper version; final JF numbers may differ) |
| Ranaldo 2009 JBF 33(12) 2199-2206 | OPENED-ABSTRACT (search snippets of SNB WP 2007-03 abstract); numbers only via Breedon-Ranaldo's description |
| Cornett, Schwarz, Szakmary 1995 | NOT-OPENED (only as described in B&R: daily/overall returns no pattern, intraday local-currency depreciation) |
| Caminschi & Heaney 2014 JFM 34(11) 1003-1039 | OPENED-ABSTRACT (search summaries only) |
| Donati & Jung 2019 CBS MSc thesis "Gold Price Dynamics Around the Clock" | OPENED-ABSTRACT (landing page; not peer reviewed; no sample or effect sizes visible) |
| Karnaukh "Dollar ahead of FOMC target rate changes"; Borisenko & Pozdeev | NOT-OPENED (search snippets only) |
| Iwatsubo, Watkins, Xu 2018 J Commodity Markets (gold futures Tokyo vs NY) | NOT-OPENED (microstructure, not a returns rule) |

No post-2013 independent replication of Breedon-Ranaldo using 2010-2024 data was found in two searches. Absence of evidence only; treat as "unreplicated", not "failed".

## 1. Breedon & Ranaldo (SNB WP 2011-04 / JMCB 2013)

- Data: EBS firm bid/offer + order flow, hourly, Jan 1997 - early Jun 2007; EUR/USD, USD/JPY, GBP/USD, EUR/JPY, USD/CHF, AUD/USD. EBS covers ~50% of EUR/USD, USD/JPY turnover, <5% of GBP/USD, AUD/USD. Market-maker data Jan 2005 - May 2007. (p.4-5)
- Sessions in New York time (Table 1): US 08-16 local, Europe 07-15 local (NY +5h), Japan 08-15 local, Australia 10-16 local. Authors state results are not sensitive to the exact hours. Sessions are defined by futures hours, not fitted; but they are fixed ex ante.
- Effect (Table 2, mid-quote session returns, ANNUALISED log returns): EUR/USD EUR session about -0.084 (GARCH -0.095), USD session about +0.100 (GARCH +0.111) for the pair EUR/USD; other rows similar magnitude (|0.03|-0.13). The pdftotext table layout is scrambled, so row-to-pair mapping beyond EUR/USD is uncertain. Unit "annualised" not stated as percent; reading 0.084 as 8.4% per year gives about 3.2 bp per day per session = about 3.5 pips on EURUSD. UNVERIFIED unit reading.
- Share positive EUR session 0.44 (**), USD session 0.56 per EUR/USD rows (as extracted).
- Trading rule (p.10): short base currency in its own session, long in counter-currency's session, open-to-close / open-to-open, using EBS bid/ask. Final column of Table 2 ("trading return", values 0.06/0.07 for EUR/USD, negative for all other pairs, -0.05 to -0.51). Text: "most of these simple time-of-day trading strategies are not profitable when trading costs are included"; EUR/USD the only exception, Sharpe 1.3 (morning short) and 0.9 (afternoon long). Costs are interdealer EBS quotes at normal size, tighter than retail.
- Stability (Fig 2): the EUR-session minus USD-session gap is stable by year 1999-2007, only 2004 wrong sign.
- Bank holiday remark (fn 6): USD appreciated vs EUR/DM over US July 4 on 15 of last 20 occasions (anecdote, not tested).
- Mechanism: domestic agents are net buyers of foreign currency in own hours (order flow), inventory/liquidity.
- Skeptic points: sample ends 2007, pre-crisis, pre-HFT-dominance, pre-ECN/retail spreads; pairs other than EUR/USD unprofitable even for dealers; session cut-offs overlap (EU/US overlap handled by "opening-to-opening"); no out-of-sample after 2007 found; strategy is round-trip twice a day (two legs).
- UTC mapping (approximate, winter, US standard): Europe session 07-15 CET-ish "local" = NY 02:00-10:00 -> UTC about 07:00-15:00; US session 08-16 NY -> UTC 13:00-21:00; overlap handled by opening-to-opening, so short EUR 07:00-13:00 UTC and long EUR 13:00-21:00 UTC roughly. Exact UTC conversions were NOT given in the paper; this mapping is my inference, to be fixed before any test.
- Events/year: ~260 days, two trades/day.
- Gross vs our cost: about 3 pips per leg gross (unit uncertain) vs 0.1-0.3 pip + commission on EURUSD: cost 5-15% of gross if the unit reading holds. On crosses unprofitable even for dealers.

## 2. Ranaldo 2009; Cornett et al. 1995; later work

- Ranaldo (JBF 2009, OPENED-ABSTRACT): indicative quotes, hourly, 24h; same pairs as Cornett plus DEM/EUR-JPY, 1993-2005; domestic currency depreciates in own working hours; "statistically and economically highly significant", persists over many years after calendar controls. Explanation: domestic-currency bias plus market segmentation (WP) / liquidity-inventory (journal). Indicative quotes overstate profitability (B&R use firm EBS quotes for this reason).
- Cornett et al. 1995: per B&R only; overall daily returns show no pattern.
- Post-2013: Krohn-Mueller-Whelan (below) is the only recent paper with 1999-2019 data and shows the dollar "W" pattern; it is a related but different decomposition (fix-centred). It does not replicate B&R's session rule directly. No paper found testing B&R sessions on 2010-2024.
- Our implication: B&R session rule is a testable cheap hypothesis, but the evidence ends in 2007 and the honest status is "published, unreplicated after 2007".

## 3. FOMC / central bank announcements

Mueller, Tahbaz-Salehi, Vedolin (JF 2017), 10 currencies vs USD, tick data 1 Jan 1994 - 2013 (text l.112, l.460):
- Strategy: short USD, long foreign, equal-weighted portfolios by interest-rate differential. Daily excess returns on scheduled FOMC days vs other days: low-rate portfolio pf1 5.19 bp vs -0.51 bp; high-rate pf3 14.47 bp vs 1.73 bp (diff 12.74 bp); dollar portfolio announcement-day-minus-other pre-announcement window 7.89 bp (t=2.02) and post-announcement window (14:15-16:00 NY) +2.39 bp (t=2.32); pf3 additional 12.72 bp = 9.48 bp pre (16:00 prior day to 14:15 NY) + 3.24 bp post (Table IV). AUD: 17.28 vs 1.16 bp, diff 16.12 bp (t=2.51). JPY and NOK differences not significant. Easing regimes 18-24 bp.
- Paper says Sharpe up to 0.8 after transaction costs (l.184) for the carry/high-rate version.
- Mapping to retail: 8 scheduled FOMC days/year. Dollar-portfolio effect ~8-10 bp over 22 hours pre-window = ~9-11 pips EURUSD-equivalent but across a 22-hour hold, not a day trade, and mostly carry-dependent (high-rate currencies, i.e. AUD/NZD, not EUR/GBP/JPY). Per year: 8 events x ~8 bp = 64 bp gross on the dollar portfolio. Volatility on announcement days is large relative to stop, so R is small and noisy. Sample ends 2013; 2009-2015 near-zero rates may have weakened the carry dependence; Borisenko & Pozdeev (NOT-OPENED) report Karnaukh's pre-FOMC dollar drift averages to zero in some specifications.
- Status: peer-reviewed, risk-premium explanation; candidate for a very low-frequency event rule; not a day trade in the strict sense (pre-window starts previous 16:00 NY). Do not call it profitable.

## 4. Gold

- Caminschi & Heaney (JFM 2014, OPENED-ABSTRACT): PM fix (15:00 London) causes price moves in COMEX GC futures and GLD around the fixing; information leaks before fix publication. The London fix was replaced by the LBMA Gold Price (IBA) in March 2015; the original microstructure is gone. Rebuttal in LBMA Alchemist (Fertig).
- Gold session pattern: only an unreviewed MSc thesis (Donati & Jung 2019, CBS) reports gold rising in Eastern hours and falling in Western hours, Sharpe up to 1.61 before costs, "underperform after" costs (as paraphrased on the landing page). No sample, no effect sizes visible. A Kobe/RIETI discussion paper (Iwatsubo et al.) is about futures microstructure and lists London weekday returns > Tokyo; not a tradable rule.
- No peer-reviewed gold session-return rule with effect size and post-2015 data was found.
- Status for XAUUSD: lead only. If we test it ourselves treat as exploratory; gold cost 0.2-0.3 USD vs typical hourly range several USD is cheap, but there is no published effect size to anchor expectations.

## 5. London fix (WM/R 4pm) - brief

Krohn-Mueller-Whelan: USD appreciates into the ECB fix (and Tokyo fix) and depreciates after the London fix; reversal portfolios. Our FX_LONDON_FIX_REV was already rejected; the paper itself finds returns shrinking (see below) and mostly negative after full cost. No further action.

## 6. Krohn, Mueller, Whelan: fix reversals / "W" shape (relevant, new)

Sample Jan 1999 - Dec 2019 (June 2006 - for order flow), G10 vs USD, Refinitiv RTH indicative quotes (WP SWP 2021-48; JF 2024 numbers may differ).
- W-shape: USD appreciates after NY close into the Tokyo fix (about 19:55-20:55 ET), depreciates after; appreciates into ECB fix (14:15 CET), depreciates after, appreciates again into London fix (see l.480-556, l.1156).
- Size: reversal about 6.5% annualised each side of the Tokyo fix for 1999-2014, about 5.0% p.a. around the European fixes; daily swings "a few basis points" (about 2.5-4 bp/day reversal, l.1096-1097); "around 2 bp" for the G9 long portfolio (preliminary version). 6.5% p.a. / 260 = 2.5 bp = 2.75 pips EURUSD per leg.
- Strategy (gross, EUR): long USD pre-Tokyo (17:00-20:55 ET), short USD after (20:55-02:00 ET); long USD 02:00-08:15 ET (pre-ECB), short USD 11:00-17:00 ET. Gross annualised 10.44% EUR, 7.94% GBP, 12.0% JPY around Tokyo (l.1169) = about 4 bp/day EUR = 4.4 pips, two legs.
- After full RTH bid-ask: negative for most windows. With 50% of the spread: EUR 2.65%, GBP 0.51%, JPY 2.73% (Tokyo); 8.64% pre-ECB, 5.46% post-London (l.1180-1183) = up to about 3 bp/day, i.e. about 3 pips, with 2 round trips per day. Sharpe 0.12-1.03 at 50% spread.
- Decay: Tokyo reversal about 5% or below since 2013, first negative year 2018; Europe fix about 10% p.a. after the crisis but below 5% in the last two sample years. Authors cite trader anecdotes of arbitrage capital. Pre-ECB-fix and post-London pieces held up better.
- UTC (winter, ET = UTC-5; DST shifts one hour, trade follows the local-time fix): Tokyo leg 22:00-01:55 UTC (long USD) then short USD to 07:00; pre-ECB long 07:00-13:15 UTC; post-London short USD from 16:00 UTC to 22:00. These legs are mostly outside the 07:00-17:00 UTC range of a daytime-only bot except the ECB/London legs.
- Events/year: ~260 per leg.
- Skeptic points: indicative RTH quotes with inflated spreads; sample overlap with B&R mechanism (same dollar-demand segmentation); decay documented by authors themselves; two round trips per day; the full-cost result is negative, retail CFD costs 0.1-0.3 pip are a small fraction of the "50% spread" assumption only if real executable spreads at those hours are that tight (night spreads in Asia are wider for retail).

## Compare gross effect to cost

| Rule | Gross per trade | EURUSD pips | Cost (ours) | Status |
|---|---|---|---|---|
| B&R EUR-session short / US-session long | ~3 bp/leg (unit unverified) | ~3.5 | 0.1-0.3 pip + comm. | published 1997-2007 only, EUR/USD only profitable even for dealers |
| KMW pre-ECB-fix long USD to ~08:15 ET, post-London short USD | up to ~3 bp/day net of 50% spread (full-cost negative) | ~3 | same | JF 2024, decaying after 2013 |
| MTV pre-FOMC short USD vs high-rate currencies | ~8-14 bp per event, 8 events/yr | ~9-15 on AUD-type | same | JF 2017, sample to 2013, not a day trade |
| Gold Asian-up / West-down | unknown | n/a | 0.2-0.3 USD | thesis only |

R conversion (assumption, not computed): stop 15-20 pips -> 3 pips gross is about 0.15-0.2R per trade before cost; 0.3 pip cost eats about 0.015-0.02R. Edge is small but not eaten by cost if the effect still exists; the key risk is that it no longer exists after 2013.

## Verdict
- Most testable: (a) B&R session sign on EURUSD (UTC ~07:00-13:00 short EUR, 13:00-21:00 long EUR, then fix exact UTC mapping with DST); (b) KMW European legs (long USD pre-ECB fix, short USD post-London fix; test 2014-2024 hold-out); (c) FOMC dollar window as event rule on AUDUSD/NZD (low n).
- Dead or weak: Tokyo-fix reversal (decayed), London 4pm rev (our rejection), non-EURUSD B&R pairs, gold session rule (no peer-reviewed evidence), Caminschi-Heaney fix effect (fix abolished 2015).
- Everything above is gross, from papers; none is evidence for our spreads or for 2014-2025 data.
