# Scout 5: FX and metals structural flows (2026-11-16)

Honest summary: the FX flow literature is real but its effects are 2-5 bp per event, which is the same size as the FTMO
cost wall that already killed S08, H12, H11, SC1. The best use of these ideas is as low-turnover or conditioned
variants, not new intraday timing. Most priors are low. Search was web-snippet based; quotes come from fetched PDF text
unless marked.

## 1. Tokyo + ECB fix reversal (the two fixes S08 did not cover)
- Mechanism: dealers pre-hedge unconditional USD demand at benchmark fixes, then unwind. Intermediaries are forced by
  inventory risk. USD up pre-fix, down post-fix.
- Venue/symbols: FTMO CFDs, USD majors (EURUSD GBPUSD AUDUSD NZDUSD USDJPY USDCHF USDCAD).
- Horizon: 30-120 min windows, 1 trade per fix per day.
- Data: OWNED (M1, FTMO + histdata 1999+; pre-2021 = development).
- Effect: dollar portfolio about 2.5 bp pre-fix appreciation and about 2.5 bp post-fix depreciation per day per fix;
  annualised 4-5% per window; t 4.5-11.7; G9, 1999-2019.
- Source: https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf (J. Finance 2024, 79(1), 541-578).
  Quote: "appreciation of the U.S. dollar pre-fix and a depreciation post-fix"
- Difference from ledger: S08 only tested London 4pm on 6 USD pairs (net -0.10). Tokyo (09:55 JST) and ECB (14:15 CET)
  windows and the 3-window basket are untested. Yen is the one pair that does not reverse after London.
- Prior it survives costs: 4%. 2.5 bp gross per window against about 1 bp spread each way plus commission on a 6-pair
  basket; S08 already failed on the same mechanism.

## 2. Intraday-only carry (hold the carry portfolio in daytime, flat overnight)
- Mechanism: not forced flow, but the same authors find risk-premium accrues only intraday. Practical angle: flat
  overnight means no CFD swap and no rollover markup; the premium is earned as price move.
- Venue/symbols: AUDJPY NZDJPY CADJPY EURJPY GBPJPY vs CHFJPY / USDCHF legs, or high-yield vs low-yield pair basket.
- Horizon: intraday, 1 round trip per day per leg.
- Data: OWNED.
- Effect: carry returns "almost exclusively earned during the day"; close-to-close long-foreign portfolio under 1%/yr,
  intraday leg almost 5%/yr (G10; paper versions disagree on the session split: US hours vs European hours).
  Sample about 1999-2019 (version-dependent).
- Source: https://jbs.cam.ac.uk/wp-content/uploads/2024/11/uncovered-interest-parity-in-high-frequency.pdf
  Quote: "excess returns overnight are virtually zero"
  (second source: https://acfr.aut.ac.nz/__data/assets/pdf_file/0007/190753/Krohn_Mueller_Whelan_Jun2018_FXPremiaAroundTheClock.pdf)
- Difference: ledger carry rows are multi-day holds killed by swap; this is the swap-free intraday version.
  Related to H07 (European-hours cross shorts, negative after costs) so partly tested in spirit.
- Prior: 5%. About 5%/yr gross is about 2 bp per day on a basket; cost per daily round trip about equal.

## 3. Month-end equity-hedge flow, pre-fix, relative-equity-signed (Melvin-Prins)
- Mechanism: international equity managers rebalance FX hedges once a month at the last London fix; the amount is
  mechanically proportional to relative equity return since the last adjustment. Forced, calendar-fixed.
- Venue/symbols: USD pairs plus JP225 / US500 / GER40 / UK100 as the signal series (owned). Pre-fix window on the
  second-to-last to last day of the month.
- Horizon: about 1 day per month, 12 events a year per pair, 10 pairs.
- Data: OWNED (index CFDs M1 as the equity proxy; no MSCI needed).
- Effect: sign and significance confirmed, size UNVERIFIED (not found in the extracted text). Sample 2004-2012,
  10 majors.
- Source: https://www.ecb.europa.eu/events/pdf/conferences/131216/Third_FX_Workshop_MELVIN_PRINS_Equity%20hedging%20and%20exchange%20rates%20Nov%202013.pdf
  Quote: "Equity market appreciation over the month predicts currency depreciation before the end-of-month fix"
  (also Hau-Rey, https://www.nber.org/papers/w14165)
- Difference: H12 tested only an unconditional post-fix USD rise (falsified on 2008-14). This is signed by relative
  equity return and is pre-fix, pooled across 10 pairs. I-67 (month-end rebalancing, US500) is the equity side.
- Prior: 4%. Power is the issue: roughly 100 months in development; pool pairs and check MDE first; likely closes on
  power. Note practitioner claims (SocGen, RBC) say it is hard to monetise except right around the fix.

## 4. Weekly cross-sectional FX momentum / carry on CFDs with the swap as an explicit cost
- Mechanism: slow capital, limits to arbitrage; carry-crash risk compensation. Not a forced flow, but the best-
  documented FX anomalies and the weekly horizon fits the "survivors are weekly cross-sectional" pattern.
- Venue/symbols: about 20 owned FX pairs, rank on past 1-3 month return (momentum) or on swap points (carry), hold a
  week; long top / short bottom terciles, USD-neutral.
- Horizon: weekly, 52 rebalances per year.
- Data: OWNED (swap table from FTMO spec; mt5_info).
- Effect: winner-minus-loser spread up to 10% p.a. (about 80 bp per week gross at best); partly explained by
  transaction costs; sample 1976-2010, 48 currencies (sample window UNVERIFIED in my fetch).
- Source: https://www.bis.org/publ/work366.pdf (JFE 2012).
  Quote: "very effective limits to arbitrage which prevent momentum returns"
- Difference: P03 fx_relative_strength is an UNTESTED draft; HV carry rows are "needs_data". This is the weekly
  cross-section with a swap-aware cost, which is the shape of the crypto survivors. Not the single-pair S04 trend test.
- Prior: 8%. Publication decay after 2010 is large; 20 pairs with common USD legs give little breadth; CFD swap
  markup on both legs. Cheap to screen.

## 5. Carry gated by volatility / equity-stress regime (crash filter)
- Mechanism: carry earns a premium but crashes when global FX or equity vol jumps; leveraged carry traders must
  de-lever (funding constraints), forcing JPY / CHF buying.
- Venue/symbols: long AUDJPY NZDJPY CADJPY (and GBPJPY) vs short low-yield; gate on realised vol of the basket,
  VIX (free, daily) or our own DXY / US500 realised vol (owned).
- Horizon: weekly; flat in stress regimes.
- Data: OWNED plus FREE (VIX daily CBOE).
- Effect: carry loses in weeks when VIX rises; global FX vol proxy explains more than 90% of cross-sectional carry
  excess returns across 5 portfolios (Menkhoff et al. JF 2012; sample 1989-2009, 48 countries per abstract, UNVERIFIED
  in my fetch).
- Sources: https://causalclaims.trfetzer.com/paper/DP8291.html ; https://www.nber.org/papers/w14473.pdf
  (quote not verified from source text, UNVERIFIED wording; no verbatim quote taken).
- Difference: filters rather than a new signal; the ledger carry rows are ungated. Overlaps idea 4, so run as a
  variant of one screen, not separately.
- Prior: 6%.

## 6. JPY / CHF central-bank intervention aftermath
- Mechanism: the MoF / SNB must buy or sell; official data (MoF monthly disclosure, SNB) is FREE but delayed 1-3
  months, so it can only label history, not trade live. Live trigger would have to be a price pattern (a sharp
  spike retraced).
- Venue/symbols: USDJPY, EURJPY, GBPJPY, USDCHF, EURCHF not owned for the floor era (EURCHF absent from the list).
- Horizon: intraday to 5 days.
- Data: MoF data FREE; prices OWNED.
- Effect: success when coordinated and above 1 bn USD (Fatum-Hutchison, NBER w9648); the practitioner note says
  spikes retrace within 5 minutes; no tradable effect size found.
- Source: https://www.nber.org/papers/w9648.pdf (no quote taken; UNVERIFIED size).
- Difference: ledger HV rows (Swiss intervention, Yen intervention aftereffect) are "untestable"; the ledger marks
  event-studies with few events as closed on power. About 20 episodes since 2003 for JPY.
- Prior: 2%. Very likely closes on power before any look. Listed for completeness only.

## 7. Gold / silver London PM fix drift (regime-limited)
- Mechanism: a fix is a consensus process among dealers; reported pre-fix drop and post-fix recovery. Silver: 10-12
  bp downward bias around the fix (the working paper that reports it has no verified cite in my results), gold PM
  fix dip documented in Caminschi-Heaney (J. Futures Markets 2014, 34(11), 1003-1039; size UNVERIFIED).
- Venue/symbols: XAUUSD XAGUSD M1 (owned; histdata back to about 2009).
- Horizon: 15-60 min around 10:00 and 15:00 London.
- Effect: bp-level, sample before the 2015 reform (LBMA Gold Price auction replaced the fix); dip likely vanished.
- Source: https://econpapers.repec.org/RePEc:wly:jfutmk:v:34:y:2014:i:11:p:1003-1039 ; critique
  https://www.lbma.org.uk/alchemist/issue-73/has-there-been-a-decade-of-london-pm-gold-fixing-manipulation
  (no verbatim quote taken).
- Difference: ledger has gold-silver ratio and lead-lag rows (killed), nothing on the fix itself.
- Prior: 2%. Cannot be tested out-of-sample post-reform in a meaningful way; the pre-2015 development window is
  the only place it exists, and the one-time test period would show nothing.

## 8. FX option expiry pinning at the 10am NY cut
- Mechanism: dealers delta-hedge near large strikes, pinning spot toward the strike before the cut; release after.
- Venue/symbols: EURUSD, USDJPY, GBPUSD, AUDUSD.
- Horizon: 08:00-10:00 NY (pin), 10:00-11:00 (release).
- Data: strike lists are only in daily commentary (investinglive / ForexLive, Newsquawk): scraping, history unclear.
  Price data OWNED. Tag: FREE but patchy.
- Effect: none published. I found no academic study; only desk commentary. UNVERIFIED that the effect exists.
- Source: https://www.newsquawk.com/headlines/notable-fx-option-expiries-for-todays-ny-cut-26th-october-2026 (desk
  commentary).
- Difference: ledger has US500 opex week (killed) and DAX expiry reversals (untestable); nothing on FX expiries.
- Prior: 2%. No evidence, the strike archive is the blocker.

## 9. Contrarian retail-flow / broker sentiment
- Mechanism: retail longs / shorts are crowded, trade against news, lose; the opposite side is paid.
- Venue/symbols: majors; data from broker sentiment feeds (OANDA, IG, Myfxbook).
- Data: FREE only as live snapshots; historical series not obviously available. Tag: NOT OWNED, history UNVERIFIED.
- Effect: Nolte and Nolte (OANDA order flow) report predictive value for price changes; Kaourma et al. 2025 report
  retail trades against news surprises; no peer-reviewed SSI test found.
- Sources: https://eprints.lancs.ac.uk/71649/1/_paper.pdf ; https://clok.uclan.ac.uk/55052
- Difference: nothing like it in the ledger.
- Prior: 3%. Cannot build a development history without a data purchase; would be forward-only.

## 10. COT speculative positioning at weekly horizon
- Mechanism: extreme speculator positioning mean-reverts (forced liquidation).
- Venue/symbols: 6-7 currency futures positions mapped onto the CFD pairs; gold.
- Horizon: weekly.
- Data: FREE (CFTC, weekly, back to 1986; Tuesday data released Friday: lag handled in the screen).
- Effect: speculative-pressure strategy 2.5%/yr gross currency excess return, Sharpe 0.47 gross (CXO summary of an
  84-future study; the underlying paper is UNVERIFIED).
- Source: https://cxoadvisory.com/equity-premium/net-speculators-position-as-futures-return-predictor
- Difference: ledger has no COT row among the extracted matches (checked FX / gold keywords only).
- Prior: 3%. Gross Sharpe 0.47 is below what t >= 3 needs on 20 years of weekly data (about 1000 weeks, expected
  t around 2).

## Dropped (for the record)
- Triangular / cross-rate deviations on CFD quotes: the literature finds deviations vanish after spreads
  (Reynolds-Soegner-Wagner 2020, IHS WP 17: "do not find evidence for substantial deviations"); FTMO crosses are
  broker-derived. Prior under 2%, not worth a card.
- Treasury auction / FOMC FX effects: few events, already closed on power by ledger (FB190 style).
- Quarter-end CIP basis: needs forwards, not tradable on CFD.

## Pick
If one thing is screened: idea 4 (weekly cross-sectional FX momentum + carry with explicit swap cost, with idea 5 as
its vol gate). It is the only one that matches the horizon of the three survivors and does not live on a 2-3 bp
intraday edge. Idea 1 (Tokyo/ECB fixes) is the cheapest second screen because the M1 data and code are in place,
but expect it to fail like S08.
