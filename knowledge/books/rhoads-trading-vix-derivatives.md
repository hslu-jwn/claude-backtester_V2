# Russell Rhoads, *Trading VIX Derivatives* (Wiley 2011)

Short: **RH**. Cite by chapter (the extraction has no page numbers). Read 2026-11-18 by one Sonnet agent; PDF in the
library folder Tier 2. VIX index, VIX futures (term structure, SOQ settlement on expiry Wednesday), VIX options and
ETNs (daily roll from the 1st to the 2nd month). Opus's reading against our ledger: the ETN roll and the curve-slope
trades are the spent family `vix_basis` (I-113 killed, I-114 short leg falsified at its one-time test); "VIX
backwardation predicts S&P 500 returns" is parked as HV-T0067-1 / HV-T0083-1; the ETN footprint needs AUM history
we lack. No new card.


Page numbers do not appear in the extracted text; items are cited as RH Ch N / section name (RH p.? = not recoverable).

### Overview
- Practitioner primer from the CBOE Options Institute, written Nov 2010. First half: what VIX, VIX futures (VX), VIX options, weekly futures options, ETNs (VXX, VXZ, XXV, VQT) and alternative vol indexes are. Second half: uses (indicator, hedging, speculating, calendar/vertical/condor spreads).
- Data window used by the author is tiny: VIX futures 2007 to Oct 2010 (about 46 monthly pairs, about 4 years, dominated by 2008). He says so himself; every "system" is demonstration level, no costs, no significance tests.
- Stance: educational and descriptive. Most claims are a few hundred observations or fewer, in-sample, with the index in points (S&P points), not R.
- Most useful content for us: exact contract mechanics (expiry, AM settlement SOQ, curve shape, roll), the persistent premium of futures over spot, how VXX rolls mechanically (sells cheap front, buys dear second month), the front-vs-index and curve-slope "indicators", and the calendar-spread pattern (long back, short front).
- Nothing in the book covers ETN daily rebalancing flows to hedgers in depth (the ETN issuer hedge flow is only implied by "daily restructuring", Ch 6, Ch 11). No intraday data, no order flow.

### Chapter notes

### Ch 1 - Understanding Implied Volatility
- Implied vol is set by net option order flow (buying lifts it). Put-call parity keeps put and call IV together. Earnings example: weekly options before an earnings date show IV doubling into the event (Amazon, 155% annualized on 1-day option = about 9.8% 1-day move; realised open move -11.8%).
- Rule of thumb: daily move = IV / sqrt(252) (traders use /16); 30-day move = VIX / sqrt(12).
- Fit: background only.

### Ch 2 - About the VIX Index
- VIX = 30-day implied vol from SPX options (new method since 2003, Whaley idea 1993); uses midquotes of OTM puts and calls of the two expirations with at least 8 days left, weighted to exactly 30 days. Time to expiry measured to 8:30 CT on SPX expiry Friday.
- Inverse relation stock/VIX explained by put demand in sell-offs.
- Siblings: VXD, VXN, VXO (S&P 100), RVX, QQQ vol; futures on VXD/VXN/RVX traded briefly 2005-2010 and were delisted.

### Ch 3 - VIX Futures (core chapter for us)
- Launched 26 Mar 2004; contract size changed in 2007 (value divided by 10). Multiplier 1,000 USD per point, tick 0.05 (50 USD). Mini-VIX (VM) 100 USD per point, three months listed. Up to 8-9 monthly expiries. Hours 7:20-15:15 CT, i.e. the future trades 70 minutes before SPX options open, priced on anticipation.
- Expiry rule: the Wednesday 30 days before the NEXT month's standard option expiry (third Friday). Last trading day is Tuesday; settlement Wednesday morning (RH Ch 3 "Contract specifications"; Ch 11 Table 11.1 lists 2011 dates: some months expire in option-expiry week, four months a week after).
- Settlement = AM SOQ, calculated from OPENING prices of SPX options on Wednesday (published as VRO), not the Tuesday close. Therefore overnight S&P moves feed straight into settlement.
- Settlement gap evidence (Tables 3.2-3.5, 2007-Sep 2010): Tuesday close vs Wednesday SOQ differences of up to about +/-8-10% in ordinary times (Jul 2007 +8%, Oct 2007 -8.5%, Aug 2009 +10%) and extremes: Oct 2008 index 53.11 / future 52.80 -> SOQ 63.04 (+18/+19%); Jan 2009 index 56.65 / future 57.90 -> SOQ 49.88 (-12/-14%). Jan 2009: 100% of the final day's range was above the settlement. Author's advice: close before expiry if you want certainty.
- No arbitrage link between VIX future and spot (no replicable basket), so the future trades at premium or discount to spot. Futures were at a premium to spot on a majority of days 2007-2010 (Table 3.6), except 2008 (mostly discount, even 4th month). Same for further months vs front (Table 3.7).
- Curve typically upward sloping then flattening; inverted when VIX spikes (Figs 3.7, 12.1-12.4).
- Author's convention for tests: roll to the next contract on the Friday before expiry (avoids the expiry-week SOQ risk). Data: CFE site gives O/H/L/C/Settle/Volume/OI per contract.
- Fit for us: we already own Cboe VIX futures; expiry calendar and SOQ-gap are checkable on our data (Tuesday close of the expiring contract vs the Wednesday final settlement). The SOQ gap vs overnight ES move is mechanical.

### Ch 4 - VIX Options
- Launched 24 Feb 2006; multiplier 100; cash settled, European, same AM SOQ expiry as the futures. Fair underlying for options is the same-expiry future, not spot (put with strike 20 offered at 1.00 with spot 18 and future 23.85 is fair).
- Open interest peaks at far OTM calls (e.g. Dec 2010: strikes 30, 40, 27.5 above ATM 21): institutions buy VIX calls as crash insurance. Peak OI 3.5m contracts May 2010; VIX options about 25% of CBOE index option volume.
- Binary VIX options (BVZ, from 2008): pay 100 if settle above strike; their price is a market probability.
- Option settlement surprise tables (Oct 2008 calls/puts) show how SOQ gap moves option value.

### Ch 5 - Weekly options on VIX futures
- Introduced late 2010; are options on the nearest-following VIX futures, American, settle in futures position, settle on Friday close. Underlying future depends on whether the Friday is before or after the monthly expiry.
- Strategy: protective call (long weekly call) against a short VIX future. Table 5.3: on the 10 worst S&P days since 2004 VIX rose more than the S&P fell on 9/10; front future more than S&P fell on 9/10; across the 100 worst days VIX up less in only 12.
- "VIX takes the stairs down and a rocket up".

### Ch 6 - Volatility ETNs (core for roll flows)
- ETN = unsecured debt of issuer (credit risk; no basket). VXX launched 29 Jan 2009 (S&P 500 VIX Short-Term Futures Index: constant roughly 30-day maturity mix of first and second month futures, weights shifted DAILY). VXZ (20 Feb 2009): months 4-7, balanced. XXV (Aug 2010): inverse of the VXX index. VQT (Barclays VEQTOR): 10-40% VIX futures exposure, rest S&P 500 TR, 2% five-day loss stop to cash. VIXS: London ETF equivalent. VXX options from May 2010; VXX volume peaked at 40m shares/day in May 2010.
- Mechanism stated by author: to keep a 30-day average maturity VXX sells the near future (cheaper) and buys the next (dearer) every day, so roll cost in contango drags; with contango on 7 Sep 2010: Sep 24.45, Oct 28.60, Nov 29.60 versus spot 23.80. Result: VXX about -85/-88% vs VIX -52/-60% from inception to Oct 2010; VXZ about -25/-31%.
- Corr of daily changes S&P vs VXX/VXZ about -0.80; the S&P and VXX moved the same way on only about 16% of days.
- Implicit flow: since the daily roll of a large long-vol ETN is a predictable, mechanical sale of front / purchase of second month, it is a "must-trade" counterparty. The book does not size it or test it.

### Ch 7 - Alternate vol and strategy indexes
- VXV (93-day IV): VXV above VIX about 83% of days 2004-2010; below VIX on about 50% of days in 2008; ratio VXV/VIX under 1 = near-term stress (a term-structure proxy from spot indexes).
- VPD (sell front VIX future monthly; size so a 25-point rally costs 25% of capital) and VPN (same with 25-strike call hedge): both fell about 50% (VPD) / 40% (VPN) Sep-Dec 2008 after steady gains; VPD closely tracks the S&P (short vol is a hidden long equity beta). VTY (short 3-month variance, 25% capital). Implied Correlation Index (index IV vs single stock IVs).
- Warning: carry from selling the premium is steady with catastrophic tail.

### Ch 8 - Vol indexes on other assets
- GVZ (gold, from GLD options), OVX (oil, USO options), EVZ (euro, FXE), OIV/GVX/SIV/CIV (CME). Correlation of GVZ with gold price only 0.09, OVX uncorrelated with oil, EVZ mildly inverse to EUR/USD. CME vol futures CVF, GVF listed late 2010. CME realised-vol futures on six FX pairs planned using the 2:00 pm CT fix (30-second VWAP).
- Fit: GVZ/OVX/EVZ are free Cboe series, could be features for our gold/oil/EURUSD CFDs; no mechanism for edge claimed.

### Ch 9 - The VIX as a stock market indicator
- S&P/VIX 10 worst days table 9.1, VIX up more than S&P down on 9 of 10; on 500 worst days VIX out-ran the S&P loss more than 90% of the time.
- VIX filter on S&P moving average systems 1990-2010: long above MA and VIX below its MA: 20-day MA 95.65 -> 140.22 points, 50-day 331.83 -> 370.66, 200-day 847.73 -> 626.10 (worse). Buy and hold 880 points beat all. Buy S&P after a -1% day, hold one day: 921 points, adding "VIX up at least 3% that day" 1,060 points. No costs.
- Futures as indicator (2007+): on the 10 worst S&P days since 2007 the front future rose more than the S&P fell on 9 of 10. 20 Nov 2008: index +8.9% but front future only +5.3% against S&P -6.7%, and the S&P rose over 15% in the next four days (a divergence "panic" signal, n=1).
- Modified (constant-maturity) VIX future = days-weighted average of the front two (FMD/TD x FMC + BMD/TD x BMC; example 23 and 58 days, 29.00 and 31.10 -> 30.50). Compare it to spot VIX: futures at discount to spot = panic/oversold. Long S&P only when future below index: about 5%/yr, with a 5% buffer about 6%/yr (2007-2010, tiny sample, includes 2008).
- GLD/VIX ratio (monthly chart): buy S&P when ratio crosses up through 2.75, sell/short when it crosses down through 6.25, hold 15 days. 2005-2010: 32 signals, +736 S&P points (415 long, 321 short), longs 15 of 19 winners (79%), shorts 8 of 13 (61%).
- VIX option put-call ratio: if ratio under 0.33 (3x more calls) go short S&P for 3 days close-to-close; long when ratio above 1.00 (with at least 75,000 contracts volume) for 3 days; combined about +1,400 S&P points over 46 months, win rate about 50%, big losers; the author flags weak validity.

### Ch 10 - Hedging with VIX derivatives
- OTM VIX calls as disaster insurance; the VIX call open interest skew proves heavy institutional hedging demand. Average VIX move on S&P days down 2.5% or more: VIX index +15%, front future only +9% (down 5% days: +17.5% and +11%). So future beta to S&P is lower than spot beta (about 0.6 of the index).
- Cost comparison: hedge $500k with SPX ATM puts about 1% for one day versus about 60-90 VIX Jan 20 calls; collar example with VIX options.
- Constant front-month long VIX futures hedge is costly because the future gravitates to spot; using two months (constant maturity) is smoother. 90% S&P + 10% constant-maturity VIX futures beat S&P over 2007-2010 ($10,139 vs $8,867 per $10,000), but outperformed only in 2007-2008. Szado (UMass, J. Alt. Inv.): Aug-Dec 2008 fully diversified portfolio -19.68%; add 1% OTM VIX calls -> +17.70%; 3% -> +97.18%. Conclusion: protection in crashes, drag in the long run.

### Ch 11 - Speculating with VIX derivatives
- Futures trade checklist: expiry day (Wednesday), index vs future gap, curve. 17 Oct 2008 case: VIX 70.33, Nov future 46.85; short future after VIX fell to 59.89 still lost because the future rose to 54.50 (front future below spot in a panic does not converge from above).
- Short the second month rather than the front when the front is at discount and the second at premium (2-3 Nov 2010 example: Dec future fell 1.40 vs Nov 1.20 vs index 1.01).
- Put on VIX when futures premium is high: long put profits even if spot VIX is unchanged ("negative time value" because the future converges down to spot). Breakeven for Jan 25 put = 21.10, versus spot 19.50.
- VXX behaviour (Feb 2009-Oct 2010, 441 days): moves the same direction as VIX on 83% of days; VIX up days: VXX up 76%, VIX down days: VXX down 88%; five-day: VXX up with VIX only 69% (VXZ about 80%), VXX down with VIX 92%; intraday (open-to-close) match 76%/83%; overnight match about 77% (VXZ 69%). Author: VXX is poor for long holds, so it is the better vehicle for a long-term short volatility view; VXX lost 88% while VIX lost 55% (Jan 2009-Oct 2010).

### Ch 12 - Calendar spreads with VIX futures (testable)
- Curve examples: 8 Jan 2010 normal (index 18.13, Jan 19.90, Feb 22.55, ... Aug 24.90, flattening); 30 Oct 2009 flat/backwardated after a stock dip (index 30.69, all futures 27.7-28.4; Nov 2009 settled 22.54); 8 Oct 2008 inverted (index 57.53, Oct 45.56, Nov 35.39, Dec 31.21, ... May 27.60).
- Convergence: the front future approaches spot over the last two weeks; the curve is steepest at the front and flattens beyond month 4.
- Rule tested over Mar 2007-Oct 2010: sell the nearer contract, buy the next (first pair short Feb 2007 / long Mar 2007 ... last short Sep 2010 / long Oct 2010), enter on the Friday before expiry of each month and exit on the Friday before expiry of the NEXT month (so a roughly one-month hold of a spread that sits at months 4/5 at entry per Fig 12.7: the examples use the pair a few months out, e.g. entered 14 May 2010 and exited 10 Sep 2010, spread widened 4.0 points).
  Result, 46 trades: 36 winners (78%), avg +0.76 point (about 760 USD), best +4.00, worst -15.87 (short Oct 2008 / long Nov 2008), total +35.0 points. Net of nothing (no commissions, settlement prices).
- Filter: only when spot VIX is below the future that is shorted (normal contango): 33 trades, 76% win, avg +0.95, worst -9.15, total +31.45.
- Stops (closing-price) of 2-5 points improved totals; a 4-point stop with 4-point target on the filtered version smoothed the 2008 drawdown. Optional exit: when spot goes above the front future the premise is dead. Hedge with OTM VIX calls.
- Two worked trades: short Apr / long May 2010 (net +700 USD); short May / long Jun 2010 (-250, flash crash would have cost -1,650 on the spread but -9,900 on a naked short).
- Calendar spread risk: in a spike the front contract explodes relative to the second (Oct 22, 2008: Oct settled 63.04 against Nov at 46.50).

### Ch 13 - Calendar spreads with VIX options
- Same thesis through options: buy the near put, sell the far put (long Nov put/short Dec put) so a spike does not destroy the position; worst case -0.85 against -11.35 for futures in Nov 2008. Calendar call spreads (short Nov call, long Jan call) and diagonals shown; theoretical 2008 scenarios lose 16-43 points.
- Takeaway: cost of the "normal curve persists" bet is a fat left tail, hedge with options.

### Ch 14 - Options + futures calendars
- 10 mini-option contracts per future; option-equivalent future price = strike + call bid (short call replacing short future earned extra 0.60 time value in the Sep 2010 example). Long put + long future cuts spike risk but lowers payoff.
- Table 14.10 shows Oct 2008 settlement 63.04 vs Nov at open 46.50.

### Ch 15 - Vertical spreads with VIX options (not read in detail; skimmed)
- Bull call spread example: 20/27.50 calls cost 2.90 for 4.60 profit (vs 4.40 for a naked 20 call) when futures premium makes long calls expensive. Spread choice depends on the future not the index.

### Ch 16 - Iron condors and butterflies (skimmed)
- With future 28.55 vs spot 22.00 (Sep 2010) an iron condor on 20/22.5/25/27.5 pays 1.50 credit for 1.00 risk because spot sits in the profit zone while the pricing underlying (future) sits in the loss zone; iron butterfly built the same way (22.54 spot, 30.15 Jan future). The edge idea is: options priced off the future but settled at spot-based SOQ are cheap or rich when the basis is large.
- Needs VIX options data: we do not have them.

### Topic tags
- trend: VIX moving-average filter on S&P 20/50-day improves a long-only MA system, 200-day does not (Ch 9). Weak.
- breakout: nothing.
- mean-reversion: VIX spike = short-term oversold; buy S&P after a -1% day with VIX +3%: 921 -> 1,060 points one-day hold (Ch 9, no costs). Future below spot = panic = buy S&P (about 5%/yr). Convergence of future to spot in the last two weeks is the mechanical mean-reversion (Ch 3, 11, 12).
- momentum/oscillators: GLD/VIX ratio crossing 2.75/6.25 (15-day hold); VXV/VIX ratio under 1 as stress (Ch 7, 9).
- patterns: none.
- intraday/sessions: VIX futures trade 70 min before SPX options open; SOQ uses the 8:30 CT opening prints; VXX intraday follows VIX 76-83%.
- seasonality/time: expiry Wednesday calendar, Friday-before-expiry roll, author notes only 4 years of data so no seasonality tested; 2008 treated as outlier.
- volatility: the core topic; VIX = 30-day IV; futures premium to spot; term structure normal/inverted; 2008 inversions.
- stops-and-exits: spread stops 2-5 points and targets 4 points help (Ch 12); close before expiry to avoid SOQ gap; weekly calls as stop-loss hedge.
- position-sizing/risk: VPD sizing so that a +25 point rally costs 25% of capital (about 0.34% historical frequency); 3% OTM calls in a portfolio gave +97% in crash; naked short VIX futures lose 10 points in a flash crash.
- testing-and-robustness/overfitting: the author's own caveats: 4 years, one crisis, no costs, system parameters picked by inspection (2.75/6.25 ratio levels, 0.33 put-call level), not recommendations.
- costs/execution: VXX decay from the roll; hedging bid-ask on SPX puts about 0.9% per day (1,350 vs 1,125 sale), VIX options bid-ask; no cost modeling in tests.
- psychology/discipline: "think of the spread as one trade", not mentioned further.
- portfolio/diversification: 10% constant-maturity VIX futures + 90% S&P; Szado study; VPD/VPN behave like leveraged long equity.

### Testable ideas

**1. SOQ settlement gap vs overnight index move** - Rule: for each VX expiry Wednesday, measure final settlement minus Tuesday close of the expiring contract and regress on the overnight (Tuesday 16:00 ET to Wednesday 09:30 ET) move in S&P/NAS100 futures or the FTMO US500 CFD. Not a trade, a measurement; then test: hold the expiring contract at Tuesday close and the S&P index overnight as a hedge, or only trade when overnight move is large. - RH Ch 3 (Tables 3.2-3.5), Ch 4 - author shows gaps of -14% to +19%, up to +/-10% in normal times - Fit: good for the data audit (we have the contracts and the US500 CFD), poor as a standalone edge: tradability requires holding futures to expiry (futures venue), the gap is symmetric unless hedged by the observable overnight index move, which the market already prices at the Tuesday close only partly. Differs from I-113/I-114 (basis from spot): this is the expiry-day jump, not carry. Unproven-positive at best; power: only about 12 expiries per year. Parked.

**2. Constant-maturity VIX future versus spot as equity signal (futures below spot = buy index)** - Rule: build the days-weighted front-two future; when it is below spot VIX (optionally 5% buffer) be long US500/NAS100 CFD next day (or hold); otherwise flat. Or use the sign of (CM future - spot) as a regime filter for other strategies. - RH Ch 9 Table 9.7-9.8 - author: about +5%/yr, +6% with buffer, 2007-2010 only - Fit: good data fit (VIX futures contracts, FTMO index CFDs, overnight swap on the long). Basically a term-structure slope (backwardation = stress = subsequent equity rebound). Differs from I-113 (future-spot basis harvest in VIX futures) and I-114 (short leg) because here the VIX curve is a signal for an equity index, not the traded asset. Highest value in the 2008-type regime, tiny n; use 2004-2025 and test the n of distinct stress episodes. ★

**3. VXX-style constant-maturity roll as a forced flow (front sell / second buy) and its footprint in VX futures** - Rule: the ETN index sells 1/N of the front and buys the second every day; compute the size relative to open interest (we know ETN AUM only from outside; need external data) and test whether daily changes in the front-second spread correlate with the known roll schedule (more selling near month end of the roll window). Trade: long second-month / short front spread in the days of heavy roll in contango, i.e. pre-position as the counterparty-free-rider (it is what the book's calendar strategy does implicitly). - RH Ch 6 (mechanism), Ch 11 (VXX -88% vs VIX -55%) - author claims only the performance gap, no flow test - Fit: partial: we have VX contracts, not ETN AUM or shares outstanding (would need free data from issuer); no CFD instrument. Mechanism-based "must trade" counterparty = in our focus, but the VXX flow was most relevant 2009-2018, and we cannot size it without AUM. Differs from the failed VIX basis: tests the daily roll-window pattern of the spread, not basis level. Needs a power check on spread data (about 15 years x 12 rolls).

**4. Calendar spread: short month-4 / long month-5 and hold until month 1/2 (author's normal-curve rule)** - Rule: when spot VIX is below the future to be shorted (the filter), sell the contract currently in month 4 and buy month 5; exit on the Friday before the short leg expires; 2-4 point stop on closes, 4-point target. - RH Ch 12 (Tables 12.8-12.14) - author: 46 trades, 78% win, avg +0.76 point, total +35 points; filtered 33 trades, 76%, avg +0.95; worst -15.87 (Oct/Nov 2008) - Fit: data fit good (contracts 1-8 needed, we have Cboe VIX futures); cost low in points (a few ticks plus exchange fees); no swap. Differs from killed I-113/I-114: those were front-leg basis harvesting (short leg falsified); this is a month-4/month-5 spread, partly beta-neutral to level, but exposed to the same inverted-curve regime and the same underlying risk premium; likely to share the same fate (roll-down is the risk premium paid for tail). Note the entry dates in the book are "Friday before the month-1 expiry", which makes the pair month-4/5 and holds about 3 months. A power check first: only 4 years in the book, our data allow roughly 2005-2025 (about 240 trades). Moderate priority: may be just I-114 in another form (check correlation of spread P&L with I-114 trade stream before testing). ★

**5. Weekly VIX options: skipped.** Options data not available.

**6. VIX/VXV (3-month vs 1-month IV) ratio as regime filter** - Rule: ratio VXV/VIX below 1 (inversion) = stress; use as a filter that switches off long-risk strategies (or switches on the long side after reversion above 1). 83% of days above 1 in 2004-2010; below 1 about 50% of days in 2008. - RH Ch 7 - author: descriptive only - Fit: we have VIX futures; VXV (now VIX3M) is a free Cboe index series (not in our data list; would need download); alternatively use the VX month-2 / month-1 slope which we do own. Differs from failed ideas: regime filter, not a stand-alone trade. Candidate input to the portfolio regime layer. ★

**7. Panic-divergence signal: front future rises less than S&P falls** - Rule: on a day with S&P down at least 2.5% where the front/constant-maturity VX rises less than the S&P loss (author: about 10% of such days), go long index for 4 days. - RH Ch 9 Table 9.6 and Fig 9.2 - author: 20 Nov 2008 only, followed by +15% S&P in four days - Fit: n is tiny (about 10% of about 50-100 bearish days), cost wall not an issue for a rare long. Overfit risk very high; fat-tail power check says insufficient. Mark as report-only.

**8. VIX put-call ratio / VIX call volume extreme (short S&P for 3 days)** - needs CBOE VIX option volume; not in our data. Author's win rate about 50%; reject unless data gets free.

**9. GLD/VIX ratio (2.75 up-cross buy, 6.25 down-cross sell, 15-day hold)** - RH Ch 9 - 32 signals, 79% long wins - Fit: thresholds selected by inspection on 2005-2010; GLD is a share (Alpaca daily) and VIX we have; we trade XAUUSD CFD. Pure data-mined; treat as a negative control for our multiple-testing ledger rather than a candidate.

**10. Expiry-calendar feature (VX expiry Wednesday and Friday-before-roll dates) as event dummies** - Test whether index CFD returns/volatility around VX expiry Wednesday morning differ (SOQ calculation affects SPX option opening prints, may create opening volatility in the cash index at 09:30 ET on that day). - RH Ch 3 - no claim - Fit: US500/NAS100 CFD M1 data allows an open-auction test on about 12 days/yr (over 15 yr = 180 events), low power. Differs from our failed intraday session rules: tied to a mechanical settlement process. Low priority, cheap to run.

Top picks: ★ 2 (curve slope as index signal), ★ 4 (month-4/5 spread, after correlation check against I-114), ★ 6 (VIX/VXV or VX2/VX1 regime filter), ★ 3 (ETN roll window, needs outside AUM data). Idea 1 as a measurement/feature, not a strategy.

### Warnings / pitfalls
- Sample is 2007-2010 only; 2008 dominates every table. Author flags results as demonstration; no costs, commissions or slippage in any system.
- Calendar spread and short-vol strategies show steady gains and then one catastrophic spike (Oct/Nov 2008: -15.87 spread points, VPD -50%, VPN -40%). A 25-point limit or an OTM call hedge changes the profile but costs carry.
- The future does not converge from above when spot is far above the future (17 Oct 2008): "being right about spot" can still lose on the future.
- AM settlement: closing the position the day before expiry removes the SOQ gap risk; holding is a coin flip around the overnight index move.
- Thin-volume days distort VIX put-call ratio (min 75,000 contracts filter). Ratios and thresholds (2.75/6.25, 0.33) are picked after looking at the chart.
- ETNs carry issuer credit risk and tracking error from the daily roll (VXX -88% vs VIX -55% over the first 21 months, partly the 2009 crash starting level); direction match falls with holding period.
- Using spot VIX as the underlying for VIX options or as the "truth" for futures P&L is wrong; the proper underlying is the same-expiry future.
- Everything in the book that uses S&P "points" is not risk-adjusted and not R-based; recompute in R with our costs before any conclusion.
