# Euan Sinclair, *Volatility Trading*, 2nd ed. (Wiley 2013)

Short: **VT**. Cite by printed page (`VT p.150`). Read 2026-11-18 by 2 Sonnet agents; PDF in the library folder Tier 2.
Index-option volatility trading: forecasting realised volatility, the variance risk premium (who buys options and
why), sizing (Kelly for vol trades), trade evaluation (Lo's Sharpe standard error, K-ratio). We hold no option prices.
Opus's reading against our ledger: short-volatility trades on VIX futures (regime-gated or not) are the spent
`vix_basis` family (I-113 / I-114); the variance premium conditioned on the VIX level (large below VIX 20, negative
above 50, VT table 4.3) is the same short-vol exposure. New, not carded: a VIX-futures ramp into scheduled events
(FOMC, payrolls, CPI) and the fall after; no published size for VX futures found, ~20 events a year on 2013+ data:
low power, a candidate only with a source. Method notes kept: Lo's serial-correlation-adjusted Sharpe standard
error and overlap corrections. No new card.

# Part 1: lines 1-7700 (forecasting, the variance premium by VIX level, events; to inside ch.8)


Scope warning: lines 1-7700 end inside Ch 8 (Kelly). The big variance-premium chapter (Ch 11, p. 213+), VIX futures (Ch 12) and leveraged ETFs (Ch 13) are NOT in this part (they start at text line 11403). Only the short variance-premium section of Ch 4 (pp. 62-65) is covered here. Cite as VT p.<page>.

### Overview
- Practitioner book (option market maker view): trade the spread between realized and implied volatility, hedged. Core claim: profit of a hedged option is proportional to (implied - realized) variance; drift is hedged away, size of moves is not (VT p. 5-7).
- Author's stance: models are thinking frameworks, not truth. BSM is "the language", used to translate fast option prices into slow implied vol. Pragmatic, data-driven; explicitly says edge + variance + size are the three things that matter.
- Volatility is far more predictable than direction (clustering, mean reversion, long memory), but even a correct vol forecast does not guarantee profit (path dependence, hedging noise, VT p. 117-129).
- Implied vol is on average above later realized vol (variance premium), caused by insurance demand, unmodeled tail events, and dealer spread protection. Sinclair warns: the premium alone is not a reason to sell options (insurers earn from investing the float, option sellers on margin do not) and one must de-bias forecasts by the usual spread (VT p. 62-65).
- Large parts (Ch 1, 6, 7, 8) are option mechanics (delta hedging, bands, Kelly) with low direct use for us (no option prices). Ch 2-5 hold the transferable material: vol estimators, stylized facts, vol-forecast methods, and event/calendar behavior of implied vol.

### Chapter notes

### Ch 1 - Option Pricing (pp. 1-12)
- Informal BSM derivation: delta-hedged long option P/L per step = 0.5 * gamma * (dS)^2 + theta + financing; with E[(dS)^2] = sigma^2 S^2 dt. Expected P/L ~ 0.5 * gamma * S^2 * (realized var - implied var) (VT p. 4-7). Equivalent: vega * (realized vol - implied vol).
- Drift drops out; only the size of moves matters. Holds for any finite-variance distribution.
- Assumptions listed (no costs, constant vol, continuous paths, shortable, constant rate). The ones that fail most: constant vol, continuity (jumps cannot be hedged), costs. Rule: never estimate tail risk inside the same model that priced the trade (VT p. 11).
- Mean in variance estimate should be set to zero (noise reduction) (VT p. 15).

### Ch 2 - Volatility Measurement (pp. 13-33)
- Sample-vol facts: s from N returns is biased low (Jensen); bias factor b(N): N=5 0.84, N=20 0.92, N=50 0.96, N=100 0.985 (Table 2.1). Std error of vol ~ sigma/sqrt(2N): N=30 gives about 13% relative error (0.0386 on 0.30 true vol); the common 30-day vol can be off by ~25% at 95% confidence (VT p. 17-19).
- Annualization shortcut: average absolute daily return ~ 0.0499 * annual vol (VT p. 19-20); annual vol ~ 20 * average |daily return|, not 16 * 1%.
- Range estimators: Parkinson (about 5x efficient vs close-close on pure GBM), Garman-Klass (up to 8x), Rogers-Satchell (allows drift), Yang-Zhang (allows opening jumps, up to 14x, but falls to close-close efficiency when gaps dominate). All are biased low under discrete sampling (Parkinson/true var 0.55 at N=5, 0.92 at N=200; GK 0.38 to 0.85) (Tables 2.3-2.4).
- With realistic data (jumps, drift) the efficiency edge shrinks; on real S&P data estimators correlate 0.91-0.999 (Brandt-Kinlay, Table 2.5). Conclusion: no single best estimator; compare them (a Parkinson vol far above close-close vol means big intraday ranges).
- First-exit-time vol estimator (barrier/corridor): sigma ~ delta / sqrt(E[tau]) with small-n bias correction (x0.8 for n=1, 0.95 n=5); about 1.7x more efficient than close-close at equal data use (Merrill 2011).
- Overnight handling: share of variance in the trading day ~85% for US stocks, ~90% for indices, 60-70% for ADRs. Method: estimate intraday vol from high-frequency returns and divide by that share (VT p. 31).
- Intraday vol pattern: peaks at open, quiet midday, small bump into close (also in FX, bonds, indices). Day-of-week effect small (slightly lower Friday, higher Monday). Use 15-30 min sampling to avoid microstructure noise (VT p. 29-32). Low-frequency vol predicts high-frequency vol better than the reverse (Corsi 2009).

### Ch 3 - Stylized Facts (pp. 35-47)
- List: vol clusters, mean-reverts, long memory; fat tails with aftershocks; negative return/vol correlation (asymmetric, strongest in equity indices, mostly absent in FX); vol and volume strongly positively related; vol roughly log-normal (right tail maybe power law).
- Autocorrelation of squared and absolute S&P returns (1950-2011) is significantly positive and decays slowly; autocorrelation of returns is about zero (VT p. 37-39). Absolute returns more autocorrelated than squared.
- Clustering stronger in developed than emerging markets, stronger in bear markets but decays faster in panics.
- Mean reversion in VIX: annualized vol of VIX from daily returns 0.96, weekly 0.84, monthly 0.59 (1990-2011), a variance-ratio signature. The long-run mean itself shifts (VIX regimes 2000-03 vs 2004-06) (VT p. 39-40).
- Fat tails: S&P 500 daily log returns 1950-2011 excess kurtosis 21.3; 24 days below -5%, 17 above +5%; worst -20.47% (1987). Excess kurtosis table: Gold 5.1, WTI 2.1, Nasdaq 9.9, DAX 4.5, FTSE 7.9, Silver 5.1, Hang Seng 32.7 (VT p. 41-42).
- Kurtosis concentrated overnight: Dow 30 overnight 17.3 vs intraday 9.9; many single stocks overnight kurtosis 13-130 (Merck 132, Travelers 609) vs intraday 3-13. Exceptions: oil majors (news arrives in-session) (Table 3.2).
- Leverage effect: SPY 2000-2011 average negative day 1.007% vs positive 0.889% (13% larger); QQQ 12% larger; held in 21 of 24 years. First exit times are shorter for down moves (Jensen et al. 2003). Applies to assets with positive expected return, not to currencies generally.
- Volume vs vol: SPY 2011 corr(volume, daily range) 0.85, corr(volume, |return|) 0.68. Adding lagged volume weakens the asymmetric vol response (Gallant-Rossi-Tauchen).
- Regime split: S&P 500 1990-2011 median 30-day vol 21.6% when below its 200-day MA vs 12.1% above (VT p. 45-46). Robust to vol estimator and MA length.

### Ch 4 - Volatility Forecasting (pp. 49-65)
- Why vol is forecastable while price is not: Fama's efficiency conditions (no costs, perfect info, agreement on price implications) fail much more in the option market (costs, insider flow, slow agreement: IV takes weeks to adjust to some news) (VT p. 49-51).
- Moving-window forecast has a drop-off problem (an old jump leaves the window abruptly). EWMA: sigma_t^2 = lambda * sigma_{t-1}^2 + (1-lambda) r^2, lambda 0.90-0.99. Sinclair calls exponential decay of a one-off event a "stupid solution": better to decide whether the event is an outlier and exclude it (earnings jump) (VT p. 52).
- GARCH(1,1): sigma_t^2 = omega + alpha r^2 + beta sigma_{t-1}^2, forecast reverts exponentially to long-run V at rate (alpha+beta); MSFT example alpha 0.053, beta 0.884. Fit by maximum likelihood needs >= 1,000 points, daily data (intraday seasonality breaks it), variance targeting helps because the likelihood is flat. Weaknesses: parameters unstable on refit, no humped term structures, 330 variants tested by Hansen-Lunde with no clear winner. Sinclair doubts the extra precision of a point forecast is worth the effort (VT p. 53-58).
- Volatility cones (Burghardt-Lane): distribution of realized vol by horizon (20/40/60/120/240 days). MSFT 20-day vol ranged 6.2% to 46.5%, median 15.9%. Rolling (overlapping) windows need a variance adjustment m = (h/n)... factor (Hodges-Tompkins 2002), about 1.06 on variance (1.03 on vol) for 60-day windows from 1,006 points (VT p. 59). Prefer comparing implied vol to the historical vol distribution rather than to a GARCH point forecast.
- Context rule: compare edge to the index spread (e.g., stock IV 39 vs RV 26 vs SPX IV 24 vs RV 18: stock edge is not much better than index).
- Fundamentals (Sridharan 2012): market underestimates vol for firms with high R&D, high cash-flow vol, earnings management; overestimates for large firms, high ROA, high leverage (bond market already prices leverage risk). Better for relative vol and longer horizons.
- Variance premium (VT p. 62-65): causes = insurance risk premium; never-seen events; dealers bias quotes up. Bakshi-Madan: spread positive when risk aversion is high and the physical distribution has negative skew and fat tails; approximate spread ~ -(gamma/2)*skew*sigma^3... + (gamma^2/6)*(kurt-3)*sigma^4 (their eq 4.18). SPY/EEM example implied risk aversion 6.4.
- Table 4.3 (VIX vs subsequent realized, Jan 1990 - May 2012): average % spread by VIX level: VIX<20 27.75% (3,102 days); 20-30 19.78% (1,925); 30-40 13.73% (407); 40-50 9.26% (111); >50 -11.52% (56 days). Spread shrinks as VIX rises and flips negative above 50. Contradicts the pure risk-aversion model (VT p. 63-64).
- Average implied-realized gap for S&P: VIX minus rolling 30-day close-close vol averaged about 3.09 vol points in the sample shown (2006-07); VIX almost always above it. Trade only what is unusual relative to this normal premium.

### Ch 5 - Implied Volatility Dynamics (pp. 67-91)
- PCA of smile changes: parallel level shift explains 65-80% of variation, tilt 5-15%, curvature ~5% (Alexander 2001). Level of ATM vol matters most.
- VIX (1990-2007) regimes: quiet 10-20, volatile 20-40; vol of VIX rises with level; more large moves up than down; locally mean-reverting.
- Mean reversion definitions: informal (circular), formal (negative autocorrelation of returns), trader's (profitable with fade rules). VIX return autocorrelation: daily -0.04, weekly -0.21, monthly -0.12. A Bollinger rule (sell 2 sd above EWMA, buy 2 sd below, exit next close) won 62.2% of trades, average win 1.05 vs loss 0.93 VIX points since 1990; Sinclair stresses spot VIX cannot be traded, so it is not a system (VT p. 72-74).
- Earnings ramp and crush: front-month IV almost always rises into earnings and drops after (AAPL example). Long straddle 10 days before earnings, sold the day before announcement, 73 large caps, Q1 2005-Q3 2010, 2-cent spread: 43% winners, win/loss 1.70, skew 5.4, kurtosis 76.6 (positive, fat-tailed). Profit rises strongly with analyst-forecast dispersion (4th quartile 48 vs 3 for lowest, Table 5.1); no clean pattern for PE, size, yield, analyst count (VT p. 75-77).
- Short straddle the day before earnings, covered the day after: 64% winners, win/loss 0.69, skew -2.1, kurtosis 12.2; also better with high dispersion (VT p. 78-79).
- Same pattern for other scheduled news: rates vol before big economic releases, commodity vol before inventory/crop reports. Carr Futures (Panos 1997): delta-neutral straddle bought Monday close of unemployment-report week, sold Thursday close, Jan 1994-Dec 1996, gained about 9 option ticks (6.53%) (VT p. 79).
- Implied event jump from the front two expiries: forward vol sigma12 = sqrt((s2^2*T2 - s1^2*T1)/(T2-T1)); event variance = T1*(s1^2 - sigma12^2); expected |move| = sqrt(2/pi) * event vol (VT p. 79-80).
- Smile causes: customers long puts (portfolio insurance) and short calls (overwriting), takeover premium in upside strikes, dealers short puts / long calls must hedge dynamically (sell when market falls, so skew is partly self-fulfilling), index implied correlation rises in selloffs, real skew/kurtosis of returns (VT p. 82-84). Smile shape in delta space scaled by ATM vol is very stable over time and across expiries (Table 5.3).
- Sticky strike vs sticky delta: each describes some market states (Derman: sticky strike in ranges, sticky delta in trends); both permit arbitrage in theory.
- Corrado-Su: implied skewness and kurtosis extractable by fitting the Gram-Charlier price formula; sampling variance of skew about 6/N, of kurtosis about 24/N (VT p. 85); estimates are noisy.
- Term structure overreaction (Stein 1989): back-month IV reacts more to front-month IV changes than a rational model allows; empirical persistence constant about 0.95 vs rational about 0.85. Example: long-run vol 15, front 25: rational back-month 23.5, market 24.5. Sinclair argues it is probably psychological (dealers watch the front) and exploitable more now than in 1989 (VT p. 90-91).

### Ch 6 - Hedging (pp. 93-115)
- Hedging costs matter: shorting 1,000 vega ATM 1 year, IV 50 vs RV 40, spread 0.1: expected profit 10,000 in frictionless BSM shrinks to 9,791 (weekly hedging), 9,220 (daily), 8,830 (twice daily), 7,952 (five times daily) (Table 6.1).
- Utility-based bands (Hodges-Neuberger; Whalley-Wilmott: band width ~ (3 * cost * gamma^2 ... /(2 * risk aversion))^(1/3); Zakamouline approximation). Short-gamma bands narrower than long-gamma ones; wider bands when spread is wide, tighter when vol is high.
- Leland: effective vol for hedging cost sigma*sqrt(1 +- sqrt(8/pi) * k/(sigma*sqrt(dt))); example: fair vol 10%, 1% spread, daily rehedge needs about 15.9% implied to break even (VT p. 101).
- Market impact: Gatheral/Merrill model, impact ~ Y * sqrt(order size), and sigma_t^2 = Y^2 * mu_t (variance per unit time proportional to volume per unit time), so Y = sigma/sqrt(volume rate) (VT p. 111-112). Useful as a simple cost model per underlying.
- Aggregation: hedge residual index risk instead of every single name; normalize deltas/gamma by beta; vol beta ~ beta (VT p. 113-115).
- Jumps cannot be dynamically hedged: buy wings when short ATM, diversify, size to limit loss, do not base worst case on history (VT p. 109).

### Ch 7 - Distribution of Hedged Option Positions (pp. 117-129)
- Even with correct vol, hedged P/L has a wide spread: stdev of P/L is about vega * sqrt(pi/(4N))-type (Kamal-Derman) in the number N of hedges, falls as N^(-1/2). Daily hedged example sd about 2,600 on 1,000 vega vs 5,700 weekly (Table 7.1). Correct realized-vol call does not guarantee profit; one-jump examples show timing changes P/L.
- Hedging at implied vol gives smooth deterministic P/L increments but wide final dispersion; hedging at realized gives noisy interim marks (others mark against you) but tight final result (VT p. 125-129). Err high with hedging vol to cut variance. OTM options have far larger P/L variance than ATM.
- Path dependency: P/L accrues where gamma is, so ending near the strike matters; trending markets hurt long gamma hedgers, range-bound markets hurt short gamma (Table 7.3).

### Ch 8 - Money Management, first part (pp. 131-138)
- Same 55%-win coin game, same trades: 5% of bankroll per bet ended at 5,207 vs 620 for flat 5 dollars; sizing alone dominates outcomes. Martingale-type systems trade win frequency for tail loss (skew), no change in expectation.
- Kelly: f = (p*w - q*l)/(w*l); example 55% even-money gives f = 0.10; 45% win rate with 2:1 payoff gives f = 0.175. Betting more than 2x Kelly turns growth negative; betting more than Kelly is worse than betting less; full-Kelly swings are uncomfortable.

### Topic tags

### trend
- Vol-level regime: S&P below its 200-day MA has median 30-day vol 21.6%, above 12.1% (VT p. 45-46); vol is the thing that trends/clusters, price does not.
- Trending markets hurt long-gamma hedgers (hedge buy high, sell low) (VT p. 124).

### breakout
- Nothing directly. The range estimators (Parkinson, YZ) say ranges contain more vol information than closes (VT p. 20-28).

### mean-reversion
- VIX returns have negative autocorrelation (daily -0.04, weekly -0.21, monthly -0.12); VIX Bollinger fade won 62% of trades on spot (untradable) (VT p. 72-74).
- Variance ratio of VIX: 0.96 daily, 0.84 weekly, 0.59 monthly annualized vol (VT p. 39).
- Back-month IV overreacts to front-month moves (Stein) (VT p. 90-91).
- Variance premium shrinks as VIX rises, negative above 50 (VT p. 64).

### momentum/oscillators
- Not covered. Clustering of vol (positive autocorrelation of |returns|) is the vol analogue of momentum; today's vol is the best forecast of tomorrow's (VT p. 38-39).

### patterns
- None. Smile/skew shape stability is a pattern of the surface, not price (VT p. 84).

### intraday/sessions
- U-shaped (open peak, midday trough, mild close resurgence) intraday vol pattern in stocks, FX, bonds, indices (VT p. 31-32).
- Overnight share of variance: stocks ~15%, indices ~10%, ADRs 30-40%; most kurtosis is overnight in stocks (VT p. 31, 42-43).

### seasonality/time
- Scheduled-event ramp and crush of implied vol (earnings, NFP, inventory, crop reports); NFP-week straddle Mon-Thu +6.5% 1994-96 (VT p. 75-80).
- Slight Monday-high, Friday-low vol (small) (VT p. 30).

### volatility
- Everything. Key quantitative facts: sampling error of vol sigma/sqrt(2N); vol approx log-normal; leverage effect 12-13% bigger down moves; corr(volume, range) 0.85 (VT p. 17-45).
- Implied minus realized spread: S&P average roughly +3 vol points (VIX vs 30-day RV); 27.75% relative premium when VIX<20 down to -11.5% above 50 (VT p. 64).

### stops-and-exits
- Not covered. Hedging-band logic (hedge only when delta leaves a band; long positions let deltas run, short positions hedge defensively) is the analogue (VT p. 100).

### position-sizing/risk
- Kelly derivation, f = (pw - ql)/(wl); more than 2x Kelly has negative growth; sizing choice dominates the equity curve in the same-edge coin game (VT p. 131-138).
- Do not judge tail risk with the model that priced the trade; size short-vol so a jump cannot ruin (VT p. 11, 109).

### testing-and-robustness/overfitting
- Sampling error of every estimate: vol SE ~ sigma/sqrt(2N), skew SE ~ sqrt(6/N), kurtosis SE ~ sqrt(24/N) (VT p. 17-18, 85). A 30-day vol can be 25% off.
- Overlapping windows bias variance estimates; correction factor from Hodges-Tompkins (VT p. 59).
- GARCH parameters unstable across refits, flat likelihood, 330 variants, no winner = warning against fitting vol models (VT p. 56-58).
- Correct forecast does not equal profit: hedged P/L dispersion ~ N^(-1/2) (VT p. 122).
- Straddle backtests: results depend on spread assumption (2 cents) and are fat-tailed (kurtosis 76.6 long, 12.2 short) (VT p. 76-78).
- Nonlinear relationships (P/L vs analyst dispersion) are missed by correlation; use quartile sorts (VT p. 77).

### costs/execution
- Hedging cost eats edge: 20% of the modeled profit at 5x daily hedging in the example (Table 6.1); Leland adjusted vol; square-root market impact (VT p. 94, 101, 111-112).
- Range-based estimators and 15-30 minute sampling to avoid bid-ask noise (VT p. 29-30).

### psychology/discipline
- Sizing by feel is "a terrible idea" (VT p. 133). Be selective: wait for clear, measurable edge (VT p. 65).

### portfolio/diversification
- Aggregate option deltas/gamma via beta to index to save hedging costs; keep per-underlying bands as backstop (VT p. 113-115).
- Index vol = component vols + correlation; implied correlation rises in selloffs (VT p. 83-84).

### Testable ideas
We have no option prices, so every idea below is tested on VIX futures, index CFDs / US500, daily US shares and ETFs, EIA futures, or Treasury futures. Ideas that need option data are listed at the end as not testable.

1. ★ **VIX futures: scheduled-event ramp (NFP / FOMC / CPI weeks)** - Rule: go long front-month (or 1st/2nd) VIX future at the close N trading days before a scheduled macro release (NFP = first Friday computable from calendar; FOMC dates from public list; Sinclair's analogue: Monday close of NFP week, exit Thursday close, VT p. 79); exit the close before the release. Control: same-length windows in non-event weeks. Reverse (short after release) tests the crush leg. Parameters: entry offset 1-10 days (author default Mon->Thu = 3 days), exit before event. Source: Ch 5 pp. 75-80. Claimed evidence: +6.53% straddle return 1994-96 (old, option based). Fit: good for cost (a few futures round trips per year per event), mechanism is "dealers/hedgers buy vol ahead of known risk". Caveat: VIX is 30-day so one event moves it little, and futures roll-down against spot drifts negative (we know basis kills longs). Differs from our killed VIX basis (I-113/I-114): it conditions on calendar events, not on contango/backwardation.
2. ★ **Variance-premium regime filter from VIX level** - Rule: compute proxy premium = VIX (or front future) minus subsequent 21-day realized vol of US500 CFD; bucket by VIX level (<20, 20-30, 30-40, 40-50, >50 as in Table 4.3, VT p. 64). Only statement to test: premium (and the sign of short/long return) as function of level. Author claim: 27.75% / 19.78% / 13.73% / 9.26% / -11.52%. Fit: pure measurement on our VIX futures plus US500; the >50 bucket has only 56 days (one episode, 2008 and 2020), so power check mandatory. Differs from I-114: this asks if the long leg only works at extreme VIX, and uses a level interaction rather than basis. Low expected trade count, report as measurement first.
3. ★ **Stein overreaction on VIX futures term structure** - Rule: when front-month VIX future (M1) moves by x on a day or week, regress the move in M3/M4 on it; trade the M4-M1 (or M3-M1) spread against excess back-month reaction (back-month beta above the roughly 0.85 rational value; empirically 0.95, VT p. 90). Entry when back-month move over the last week exceeds beta*front-move by a threshold; exit after N days. Source: Ch 5 pp. 90-91. Claimed evidence: persistent over 20+ years (Stein 1989, Sinclair 2013). Fit: needs multiple VIX futures months with clean history (check what Cboe data we hold). Cost: two legs. Differs from basis (spot vs future): here relative value within the curve, driven by dealer attention on the front.
4. ★ **Vol-state regime + sizing: 200-day MA and realized-vol forecast** - Rule: classify US500/index CFDs into above/below 200-day MA; use median 30-day vol split (21.6% below vs 12.1% above, VT p. 45) to set risk per trade or to scale position size by forecast vol (EWMA lambda 0.94 or 20-day close-close, with Hodges-Tompkins overlap correction). Test: does inverse-vol sizing improve Sharpe/drawdown of our existing passed streams (Strategy 20 crypto flow sort, Treasury month-end)? Fit: good, no new data, no extra cost, mechanism = vol is forecastable, return is not. Differs: this is sizing/risk overlay, not a signal; can reuse the shrunk-forecast habit.
5. ★ **Honest-testing toolkit from this book** - Use as method checks, not trades: (a) vol SE ~ sigma/sqrt(2N), skew SE ~ sqrt(6/N), kurtosis SE ~ sqrt(24/N) for the power check before any vol/tail claim (VT p. 17-18, 85); (b) Hodges-Tompkins overlap factor when using rolling windows (VT p. 59); (c) compare estimators (close-close vs Parkinson vs Yang-Zhang) on our M1 CFDs for session-vol forecasts; (d) report straddle-style fat-tail stats (skew/kurtosis) with every vol-sensitive result. Fit: excellent for the multiple-testing/power framework; can feed T-24 (fat-tail power check).
6. **VIX futures weekly mean reversion (fade large weekly moves)** - Rule: when weekly change in the front VIX future exceeds +/-2 sd of its EWMA-based z-score, fade for 1-5 days. Evidence: VIX weekly autocorrelation -0.21, daily -0.04, monthly -0.12; spot Bollinger fade won 62% (avg win 1.05 vs loss 0.93 VIX points) (VT p. 72-74). Fit: futures move less than spot (roll toward spot), so signal may weaken; costs low. Overlap with I-113/I-114 families: conditioned on shocks, not basis. Check carefully that mean reversion in spot is not simply the futures curve flattening.
7. **Variance premium by volume/skew state (Bakshi-Madan)** - Rule: regress realized-minus-VIX spread on trailing realized skewness and kurtosis of US500 daily returns (and, if available, risk-aversion proxy); trade VIX futures only when model-predicted premium is unusually high/low. Evidence: model fits across indices (SPY risk aversion 6.4, EEM predicted IV 0.221 vs 0.225 actual) but fails at high VIX (VT p. 62-64). Fit: poor to moderate (noisy moments, short samples); differs from basis; likely falsified.
8. **Overnight-vs-intraday tail split for index CFDs and US shares** - Rule: measure overnight (close-open) vs intraday (open-close) excess kurtosis and variance share per instrument (benchmarks: stocks ~85% intraday variance, indices ~90%; overnight kurtosis 17.3 vs intraday 9.9 for Dow 30, VT p. 31, 42). Use for risk model: stop placement, gap risk, swap-holding decisions, and a vol-forecast adjustment. Fit: good as risk input; as a trade it is just gap behavior (our gap fade/momentum failed).
9. **Leverage-effect conditional vol (asymmetric GARCH/EWMA)** - Rule: forecast next-day vol with a down-day-weighted EWMA (GJR/EGARCH style) vs symmetric; test whether asymmetric forecast beats symmetric for sizing in indices and US shares, and whether it fails in FX (author says effect absent in currencies, VT p. 43). Fit: good, uses daily data; supports idea 4. Not a signal for direction.
10. **Volume-conditioned vol forecast** - Rule: add lagged volume (daily share volume from Alpaca) as a regressor for next-day |return|; check whether it removes the asymmetric response (Gallant-Rossi-Tauchen). Fit: moderate, needs daily volume (we have Alpaca). Output is a forecast, not an alpha; low trade impact.
11. **Vol-of-event: realized earnings-day jump vs prior vol (shares)** - Rule: for US shares, estimate the size of the largest overnight gaps relative to trailing 20-day vol (Sinclair's earnings jump). Without an earnings calendar this is only descriptive; with known report dates, test if stocks with high analyst dispersion have larger jumps (author finds dispersion drives profit, VT p. 77). Fit: poor (no analyst data, no calendar).
12. **EIA crude/gas front-month realized vol before inventory report (Wed)** - Rule: realized-vol or move size around the weekly EIA report vs other days; trade long straddle proxy is impossible, so only vol forecast/sizing around the report. Fit: poor to moderate; no option prices; mostly informational. Author notes oil majors' overnight kurtosis is low because oil news arrives in session (VT p. 43).

Not testable on our data (need option quotes or open interest): earnings straddle backtests, strike skew, Corrado-Su moments, dispersion trading, dealer gamma/expiry pinning, Stein test on equity options, forward-vol event jump extraction (needs two IV terms).

### Warnings / pitfalls
- A correct vol forecast does not guarantee profit; hedged P/L is path dependent and dispersion falls only as N^(-1/2) (VT p. 117-122).
- "Cheap/rich" implied vol is seldom a reason by itself; check the catalyst; do not sell vol simply because a premium exists (VT p. 13-14, 64).
- Selling vol: part of the premium pays for events that have never happened; do not size from the worst past event (VT p. 109). Long-vol edges (earnings straddle) show kurtosis 76.6, so results are driven by a few outliers (VT p. 76).
- Short-vol results that rely on today's two-cent spreads are not historical performance (VT p. 76).
- Vol-measurement pitfalls: 30-day windows have 25% error; unadjusted dividends create fake vol (3% ex-div drop looks like 48% annualized); N-1 vs N variance conventions; Jensen bias in taking sqrt (VT p. 14-19).
- Range estimators are biased low under discrete sampling; their efficiency claims assume driftless GBM (VT p. 21-22).
- GARCH: unstable parameters, flat likelihood, intraday seasonality breaks it, no model wins (VT p. 56-58).
- Overlapping windows inflate apparent precision (VT p. 59).
- Market makers get run over by vol cones because they are already short when vol hits highs (VT p. 61).
- Edge in volatility trading has been shrinking: Sinclair says the profits of equity vol long-short portfolios declined over 2008-2013 (VT p. xiii).
- Betting more than Kelly gives lower return and higher variance; martingale doubling trades frequency for skew (VT p. 133-137).
- Smile/vol-surface analytics are seductive but level of vol is "many times more changeable" and more important (VT p. 69-70).

# Part 2: lines 7701-15377 (variance premium, VIX, sizing, evaluation)


### Overview
This part starts inside Ch 8 (Money Management: Kelly sizing and alternatives, p.138 on) and runs through Ch 9 (Trade Evaluation), Ch 10 (Psychology), Ch 11 (Generating Returns through Volatility: the variance premium), Ch 12 (The VIX), Ch 13 (Leveraged ETFs), Ch 14 (Life Cycle of a Trade), Ch 15 (Conclusion), Resources, then the reference list (nothing useful after p.259). The author is a practitioner-sceptic: edge must be understood before it is traded, sizing matters as much as signal, small samples and fat tails fool everyone, and performance statistics (Sharpe, etc.) are noisy. The only market-structure chapter that bears on us is Ch 11-12: the variance premium exists mainly for INDEX options (not single stocks), is a mix of skew and correlation premia, and is best harvested when implied vol is low or falling. Ch 12 (VIX basis, VXX/VXZ) overlaps with our spent VIX tests. Important limit: nearly everything in Ch 11-14 needs option prices, which we do not have. What transfers to us is mostly method (Kelly with parameter uncertainty, honest Sharpe error, persistence tests, pre-set benchmarks) and VIX-futures term-structure ideas.

### Chapter notes

### Ch 8 (second half) - Money Management (pp. 138-162)
- Kelly general form: choose bet fraction f maximizing expected log growth; for small edge f = excess return / variance of the payoff (VT p.138, Eq 8.14). Works for any payoff distribution, not only binary bets. Use return over the risk-free rate.
- Growth rate is symmetric around full Kelly: 2x Kelly gives zero growth, so over-betting is far worse than under-betting by the same ratio; err toward smaller (p.139).
- Full Kelly: one-third chance of the bankroll halving before it doubles. Fraction of Kelly vs. P(double before halving): 1.0 -> 0.667, 0.8 -> 0.739, 0.6 -> 0.834, 0.4 -> 0.941, 0.2 -> 0.998 (Table 8.1, p.139). Smaller fraction costs time to reach goals.
- Fractional Kelly has no utility-theory basis; it is a "poor man's Bayesian" shrinkage (half Kelly = average of own edge estimate and zero edge) (p.139).
- Time for Kelly to dominate is huge: Browne example (15% return, 30% vol, 7% cash): 157 years to beat cash by 10% with 95% confidence, 10,286 years to beat all-stock (p.143). Bankroll PDF is highly skewed; the median path trails the mean.
- Parameter mis-estimation (pp.143-146): with a uniform prior, estimated win probability is (w+1)/(N+2), not w/N; naive Kelly is biased too high. Example 6 wins in 10: std of p 0.137, ~27% posterior chance the game is actually losing; std of Kelly fraction 0.274 at N=10 and 0.097 at N=100 (p=0.6). Key point: SD of the Kelly estimate dominates the small bias.
- "What is the bankroll?" (p.147): not the margin posted; it is the loss you can take before the strategy is abandoned; can scale Kelly multiplier by total wealth.
- Oscar's system / negative progressions (pp.148-149): any progression only reshapes the P&L distribution (frequent small wins, rare disaster); cannot create edge. Simulated craps: 66 disasters in 280,000 trials, avg loss 13,000 units.
- Browne dynamic sizing (pp.150-153): fraction that maximizes probability of hitting a wealth goal by a deadline = delta hedge of a digital call; very aggressive early (leverage 1.8, 3x Kelly) and dialed down as goal nears. Beats Kelly in time-to-dominate (e.g. 14-900 years vs 10,000) but has bankruptcy probability. Relevant for prop-firm style profit targets with fixed deadline and drawdown limits (FTMO challenge).
- Proebsting's paradox (p.153-155): with changing odds, Kelly can overbet unless you mark open positions to market; resolution by Aaron Brown: size on marked-to-market wealth.
- Mean-reverting asset sizing (Ornstein-Uhlenbeck, pp.155-162): log-optimal position = -(wealth x deviation in SD units) / 2; max position at 1.4 SD (sqrt 2); beyond that, add less because losses shrink the bankroll; result independent of reversion speed. Fat tails (logistic, excess kurtosis 9) hurt badly. Toy result: best single entry level for a normal i.i.d. spread is about 0.75 SD (maximize 2TS(1-N(S))). Simulated on VIX with a Bollinger rule: peak near 0.75 SD, left side (too-wide) tails off faster so err toward trading slightly less often.
- Warning: adding to a loser is only right if the mean has not changed; InterOil example: no-news 35% crash with volume 10x normal -> do not sell more vol (p.159). Regime check before scaling in.
- Summary rules: when more edge trade bigger, when more variance/uncertainty trade smaller; set sizing before trading; arbitrary price-based stops are a poor idea in mean-reverting trades.

### Ch 9 - Trade Evaluation (pp. 163-185)
- Keep detailed records per underlying: daily P&L gross and net, winner/loser day %, avg win/loss day, max win/loss, cumulative P&L, max drawdown size and duration (p.166). Review monthly; set three benchmarks (success, respectable, failure) before trading starts (pp.165, 178).
- Sharpe ratio weaknesses (pp.171-173): estimation error. Lo (2002): variance of measured SR is about (1/T)(1 + SR^2/2) per period; simulated GBM drift 0.2/vol 0.3 over 100 days: average measured SR 0.5 vs true 0.66 and standard deviation of the estimate 1.61 - the error is as large as the number. Small-sample bias about S/2T.
- Peso problem: selling far OTM options gives double-digit Sharpe until the loss event; any history-based risk measure misses unseen tails.
- Alternatives (pp.174-177): Sortino (downside deviation), Calmar (excess return / max drawdown; rule of thumb x% return needs x% drawdown), Sterling, Omega (needs full distribution, not robust to extremes), K ratio (t-stat of slope of log cumulative return; handles order of returns; two equity curves with identical returns and Sharpe 5.28 can look totally different). No single magic statistic: use several.
- Scalability can matter more than Sharpe (p.177). Traders game whatever is rewarded; separate risk oversight.
- Setting goals by simulation (pp.178-180): a Sharpe-4 process still shows a lost quarter in a few of 20 simulated paths; fix review dates and stop-levels in advance; do not cut size just because of recent results; a manager halving size after two losing days when 20% of days lose is noise-chasing (p.180).
- Persistence tests (pp.180-183): relative persistence via cross-product ratio on above/below-median split into two sub-periods, z = ln(CPR)/sqrt(1/GG+1/BB+1/GB+1/BG); example CPR 1.23, z 0.32 = nothing. Absolute persistence via Hurst exponent (rescaled range; h = ln(R/S)/ln(N/2) quick estimate; applies to log returns of the P&L stream; biased above 0.7 and below 0.4).
- Higher-level evaluation (p.183): do not work on weak areas (trading is not golf); push what works; edge decays as others enter - causes: source of edge gone (tick size change), execution ability, counterparty changed (retail flow vs professionals). Ask "if I started today, would I pick this product?"
- Break results by sector and long/short volatility, record overridden signals too (p.170).

### Ch 10 - Psychology (pp. 187-212)
- Argues psychology matters less than edge; biases useful as a source of mispricing hypotheses. Behavioural explanation must name the specific bias to be testable ("overconfidence + representativeness" vs "fear and greed") (p.188).
- Biases covered: self-attribution, overconfidence (analysts' 90% intervals contain truth only 64% of time, money managers 50%, p.195), availability (Google earnings moves table: average abs next-day move 7.7%, max 15.4%, straddle priced 16% off the latest 9.6% move), short-term thinking (long-vol positions lose most days), loss aversion (suggested as the main reason for the implied vol premium, p.201), conservatism/representativeness (conservatism -> momentum, post-earnings drift; representativeness -> reversal; Wu-Massey: "misreaction"), confirmation bias (define falsifying criteria before a backtest; be flexible when searching, dogmatic when testing, p.206), hindsight bias (state falsifiable forecasts), anchoring (George-Hwang 52-week high predicts returns; Driessen-Lin-Van Hemert: implied vol falls on approach to 52-week highs/lows by 0.9/0.4 vol points, rises by about 1.1-1.2 points after a break, t = 3.9 to 12.9, p.208), narrative fallacy, prospect theory (maps to a fractional-Kelly equivalent).
- Streak maths (p.202): with 55% winning days, an 8-day winning streak appears in about 31% of 100-day samples - do not read it as regime change. Formula given for P(no run of length j in N trials).
- Summary rules: do not trade too often or too big; avoid trades where you must be exactly right; admit being wrong; set buy/sell levels before looking at the market's implied vol.

### Ch 11 - Generating Returns through Volatility: the Variance Premium (pp. 213-223)
- Alpha vs beta (p.213): the index variance premium is beta (a paid risk), not alpha; do not pay alpha fees for it.
- Evidence (p.214): Coval-Shumway 2001: selling equity-index straddles gave about 3% per week, Sharpe 1.2. Hodges et al.: buying S&P 500 and FTSE 100 calls unprofitable 1985-2002. Broadie-Chernov-Johannes 2009: put buying unprofitable even including 1987.
- Author's QQQ test Jan 2000-Apr 2010, second-month options, delta hedged weekly, strategy margin, $100k start: 10-delta strangle Sharpe 1.32, DD 20.6%; 20-delta Sharpe 1.21, DD 34.2%; 30-delta Sharpe 1.14, DD 32.9%; ATM straddle Sharpe 1.14, DD 32.7% (Figs 11.2-11.5). Robust across strikes; drawdowns too large for a levered firm or fund.
- Filters (pp.217-218): sell the 20-delta strangle only when VIX < 35: Sharpe 1.30, smoother, avoids 2008. Sell only when VIX below its EWMA (decay 0.95): Sharpe 1.68, DD 10.3%, but author warns it is much less robust (curve-fit risk; gains mostly from pre-2004; after 2004 both filters about double equity).
- Single stocks (Table 11.1, 2002-2010, 30-delta strangles on Dow components): mixed - some strongly negative (AA, GE, JPM, MRK), several positive (JNJ Sharpe 1.12, WMT 1.12, UTX 1.26); no persistent premium: "the variance premium is largely an index effect" (p.219).
- Sources of the index premium: (1) correlation premium - index options rich vs component options; dispersion trade (short index vol, long component vol) has similar Sharpe but loses when correlations spike (p.219); (2) skewness premium - index skew steeper than stock skew; selling 30-delta risk reversal on QQQ: Sharpe 0.69, annualized 22%, DD 26.9% (Fig 11.8); Kozhan et al. 2011: about half of the excess return from selling OTM puts comes from the return-volatility correlation (realized skew), 1996-2009 S&P 500 (p.220).
- Why the premium exists (pp.220-222): arguments FOR sellers: sellers provide crash insurance, negative skew and kurtosis demand compensation, short vol loses when equities lose; Carr-Wu 2009: stocks with higher variance betas have higher variance premia (variance is a priced factor). Arguments AGAINST: stockholders sell covered calls for yield price-insensitively (depresses call prices); agency-driven preference for negative skew. Net: evidence says sellers have the edge. Buyers: OTM put buyers over-estimate crashes; OTM call buyers are lottery seekers (Ni 2009; Hodges et al.: long-call returns get worse the further OTM). Peso-problem alternative explanation (rare bad events missing in sample). Loss aversion (investors like capped-loss options) is offered as main behavioural reason (p.201, Low 2004).
- Summary (p.222): index implied vol generally exceeds realized; capture by selling straddles/strangles; best when overall vol is low; premium is skew plus correlation; absent in single equities.

### Ch 12 - The VIX (pp. 223-230)
- Model-free implied variance from a strip of OTM options (Carr-Madan, Britten-Jones-Neuberger); VIX is the discrete sum version interpolated to constant 30 days (p.224). Taking sqrt of variance adds Jensen upward bias. Cash VIX is not tradable (needs continuous rebalancing); VIX futures (since March 2004) have no cash-and-carry bound, so prices are model dependent (p.225).
- Simon-Campasano (2012) VIX-basis predictor (p.226): 2006-2011 VIX mean 23.7 (low 9.9, high 81.1); front two futures averaged 23.8 and 24.4; front-month basis mean +0.66, deciles -1.40 / +2.01. Curve is downward sloping 22% of the time even when VIX < 20 and upward 46% of the time when VIX in 40-50: the "usual" shape is not universal.
  - Rule: if front future above cash and expected daily convergence > 0.1 VIX points, short a future; if below cash and convergence > 0.1, buy; hold 5 days. Table 12.1: mean P&L shorts $656 (53 winners / 29 losers), longs $1,040 (22 / 20). Most profit is the realized roll (futures converge to cash at the expected rate). Hedged with S&P futures (regression of VIX returns on index returns, also scaled by time to expiry): shorts $539 (55/27), longs $908 (27/15) - hedge lowered mean but raised hit rate, especially longs.
- Volatility ETNs (pp.227-228): VXX = rolling 30-day front-month VIX futures (daily roll of 1/30), VXZ = 4th-7th month. Contango decays VXX; example June 1, 2011 front 17.9, second 19.5, daily roll loss 0.05. VXX vol is 1.5-2x lower than VIX, VXZ 3-4x lower, correlation to VIX above 90%.
- IVTS = VIX / VXV (3-month implied vol index), above 1 = backwardation (futures expected to rally). Donninger (2011) dynamic VXX/VXZ portfolio weighted by IVTS level (Table 12.3: IVTS <= 0.91: VXX -0.60 / VXZ +0.40; 0.91-0.97: -0.32/+0.68; 0.97-1.05: -0.25/+0.75; > 1.05: -0.10/+0.90): Aug 2010-Aug 2012 99% annualized, DD 12%, Sharpe 2.62 vs short VXX Sharpe 1.5 with a bad drawdown (VXX 20.11 -> 56.84, Jul-Oct 2011). Very short, in-sample, author does not discuss costs or borrow.
- Other: calendar put spreads on VIX in contango 2009-2011: 15.2% annualized, Sharpe 1.2, DD 18%. VIX options variance premium averaged 3.26% in Oct 2006-Nov 2010 (Barnea-Hogan 2012, synthetic variance swaps).

### Ch 13 - Leveraged ETFs (pp. 231-238)
- Volatility drag: (1+x)(1-x) = 1 - x^2. A daily-rebalanced L-times ETF follows L0 (S/S0)^L exp(-0.5 L(L-1) sigma^2 t) (Eq 13.6). The "decay to zero" myth is false: for trending or low vol periods (TLT vs UBT 2011-12: +37.9% vs +82.1%, 6.3% over-performance) the leveraged ETF outperforms. FXI vs FXP Oct-Nov 2008: FXI +9.0%, FXP (-2x) -49.2% at 146% realized vol.
- Kelly link: critical leverage = return / variance; FXI critical leverage 0.04 in that period, so 2x was hopeless (p.234).
- Long leveraged ETF / short reference product (beta-neutral pair) is a perpetual short realized variance / long straddle-like position: needs steady persistent moves, loses to choppy vol (Eq 13.9; breakevens Eq 13.10). Options on leveraged ETFs = compound power options on the reference; implied vol of L should be about L times the vol at "most likely strike" S0 k* (pp. 235-237). Market vols close to theory (SSO, July 2012).

### Ch 14 - Life Cycle of a Trade (pp. 239-248)
- Worked example: short AAPL July vol before iPhone launch, June 25 2007: implied 41 vs forecast 29 (blend of Yang-Zhang 31.1, C2C 28.3, Parkinson 27.2, GK 29.9, RS 27.4, GARCH 36.1, high-frequency 21.0). Exit after 7 days at 29 implied; +$18,390 on avg haircut $76,805 (23.9%). Held to expiry: realized 30.1 vs sold 41.6, expected $21,850 but ended $6,718 due to one big gap in short-gamma region. Lesson: catalyst-dated trades let you exit early (event-driven implied-vol bid before a hyped event, sold before the event). No P&L stops; exit when edge is gone.

### Ch 15 - Conclusion and Resources (pp. 249-259)
- Process: one goal, edge you can name, sizing consistent with goal, records. Execution ability, concentration and product selection are as important as knowledge ("better to be in the sloppiest pit than the best-known complex product"). Reference list follows, nothing to extract.

### Topic tags
- trend: no. Only note: conservatism -> underreaction -> momentum/PEAD; sector persistence (Chan et al.) (p.201).
- breakout: no. 52-week high anchoring (George-Hwang) predicts returns (p.208).
- mean-reversion: Optimal sizing in OU process: position proportional to deviation, max at sqrt(2) SD; best single entry about 0.75 SD for iid normal; fat tails and shifting mean break it (pp.155-162). VIX is mean-reverting but upward-skewed, so use asymmetric bands. VIX basis convergence is the tradable mean reversion (p.226).
- momentum/oscillators: none besides the behavioural remarks above.
- patterns: none; the author calls the "Hindenburg Omen" hilariously overfit (p.209 note).
- intraday/sessions: none.
- seasonality/time: event-run-up in implied vol before scheduled catalysts (earnings, product launches); implied vol falls into holidays (p.245); variance premium bigger when vol is low. Option expiry timing (author sets a monthly review the Monday after expiry, p.164).
- volatility: index variance premium exists, single-stock premium does not (pp.213-219); premium proportionally larger when implied vol is low; sell only when VIX below ~35 or below its EWMA; correlation and skew premia; VIX futures curve is not always in contango; volatility clustering plus mean reversion are the sources of vol predictability (p.249).
- stops-and-exits: no arbitrary price stops for mean-reverting vol trades; exit when the reason for the trade is gone or edge is realized; early exit after edge realized beats holding to expiry (pp.159, 247).
- position-sizing/risk: Kelly f = mu/sigma^2; full Kelly = 1/3 chance of halving before doubling; use Bayesian win-rate (w+1)/(N+2); fractional Kelly 0.2-0.5 for uncertain edges; Browne goal-based sizing (prop-firm target + deadline); Proebsting: size on marked-to-market equity; sizing on bankroll = abandonment loss; scale fixed costs; do not change size on recent results (pp.138-162, 179-180).
- testing-and-robustness/overfitting: Sharpe SE ~ sqrt((1+SR^2/2)/T) (Lo); K ratio; cross-product ratio persistence test; Hurst exponent on P&L; define falsifiable outcomes first; benchmarks before trading; filter-based improvements (VIX EWMA filter) flagged as curve-fit; peso problem; sample-size neglect; small-sample 8-win streak happens 31% of 100-day samples (pp.171-183, 202, 217).
- costs/execution: hedge costs add up, costs hide in "small" tickets; track gross vs net daily P&L; fixed costs make arbitrary size cuts harmful (pp.166, 199).
- psychology/discipline: ten biases listed; loss aversion as the likely source of the variance premium; use a partner; keep a journal (pp.187-212).
- portfolio/diversification: correlation premium/dispersion; do not diversify by working on weak strategies - concentrate on what works (p.183); overconfidence leads to undiversified books.

### Testable ideas
(Our data has NO option prices. Ideas are therefore proxies using VIX futures, VIX index level, index CFDs, daily US shares/ETFs.)

★ **Variance-premium harvest proxy: short-vol exposure sized by VIX level/trend, on VIX futures (long-flat roll-down)** - Rule: when VIX futures front curve is in contango AND VIX below a level (author's 35) AND VIX below its EWMA (decay 0.95), hold short front VIX future (or short roll) for the 5-day window; flat otherwise. Size by Kelly-style mu/sigma^2 with shrinkage ((w+1)/(N+2) for win rate; half or fifth Kelly). - Source: Ch 11 pp.217-218, Ch 12 p.226 - Author's claim: Sharpe 1.30 (VIX<35) and 1.68 (below EWMA) for option selling on QQQ; basis trade Table 12.1 profit per trade $656 short. - Fit: GOOD data fit (Cboe VIX futures available); but I-113 (basis) killed and I-114 short leg falsified, so this is only worth doing as a regime-gated re-test: it differs by adding the level and EWMA filters and the Kelly sizing, not a new basis entry. Treat as high prior of failure; run the power check first. Differs from failed families: not price-pattern; it is a risk-premium stream.

★ **Index-vs-stock variance premium via realized vs VIX forecast error** - Rule: daily, compute VIX^2/252 (implied variance forecast for next month, scaled) minus subsequent 21-day realized variance of S&P 500 CFD (US500 M1 sum of squared returns); regress (or sort) forward return of "short vol" exposure (e.g. short VIX futures roll or short-volatility-sensitive overlay) on the spread in the previous month. Test whether premium is bigger when VIX low (author's claim p.217). - Source: Ch 11, Fig 11.1, p.214, p.217 - Claim: premium proportionally larger when implied vol is low. - Fit: GOOD (VIX futures history + US500 M1 candles for realized variance). Gives a pre-registered conditional-expectation test usable as a gate for any short-vol sleeve; also yields a forecast of the premium without option prices. Differs: tests the premise (premium level and its conditioning), not a price pattern.

★ **VIX-futures calendar/curve-slope predictor of VIX move using IVTS proxy** - Rule: IVTS = VIX / 3-month vol (we have no VXV; proxy with VIX / (second-month VIX future) or front-to-second futures ratio); thresholds from Donninger: <=0.91, 0.91-0.97, 0.97-1.05, >1.05. Map to long/short mix of front vs back VIX-future exposure (short front, long back as a beta-hedged spread) rebalanced daily. - Source: Ch 12, Table 12.3, pp.228-229 - Claim: 99% annualized, Sharpe 2.62 (2010-2012, very short, in-sample). - Fit: PARTIAL: needs per-contract VIX futures (we have Cboe VIX futures); spread ETN costs approximated by roll plus bid/ask. Differs from killed basis tests: uses the slope of the curve (term structure) in a spread (front vs second) rather than basis to spot; risk is that the same information as I-113. Low prior; Sharpe claimed on 2 years is not reliable (power check will say so).

★ **Month-/event-calendar implied-vol run-up proxy: long short-dated VIX exposure ahead of known macro events** - Rule: for scheduled event days (FOMC, CPI, NFP dates) go long VIX front future (or long straddle proxy via VIX futures) 2 days before and exit the close before the event; test vs random pre-weekend days. - Source: Ch 10 p.198, Ch 14 pp.239-248 (implied vol bids before hyped catalysts and drops after) - Claim: catalyst-timed short-vol sale realized 23.9% on haircut in 7 days (single stock) - the mirror image of the run-up. - Fit: GOOD for VIX futures plus a public event calendar (Fed schedule public; CPI/NFP dates known). Differs: event-time rather than price pattern, but need to check overlap with the spent FX fix and month-end tests (not the same instrument). Needs a power check: about 8 FOMC per year only, so low power; pool with CPI/NFP.

**Short-leveraged-ETF drag harvest (long L, short S pair) or its mirror in choppy regimes** - Rule: hold short 2x or 3x leveraged ETF vs long 1x reference (beta-neutral by ratio L), rebalanced weekly; gate: ON when trailing realized vol (e.g. 21-day) is high AND persistence (variance ratio) is low (choppy). - Source: Ch 13 pp.233-235 - Claim: theory (exp(-L(L-1)sigma^2 t/2)); no backtest. - Fit: POOR to uncertain: Alpaca daily bars of leveraged ETFs exist maybe, but borrow cost on leveraged ETFs and hard-to-borrow fees are large and not in our cost model; also pair is long straddle-like (loses in trending); shorting needs margin. Low priority. Differs: structural payoff effect, not price pattern. Document as "needs borrow data".

**Kelly-with-uncertainty sizing overlay for the existing accepted streams** - Rule: for Strategy 20 (crypto taker-flow sort) and Treasury month-end: compute f = (mu-rf)/sigma^2 using shrunk mu (half of posterior mean, or Bayesian (w+1)/(N+2) for win rate) and an SE band; trade at 0.2-0.5 of that, and compute the Browne goal-sizing alternative for FTMO profit target and time limit. - Source: Ch 8 pp.138-153 - Claim: 0.4 Kelly -> 94% chance of doubling before halving. - Fit: GOOD (sizing/risk layer runs on R trade lists). Differs: not a signal. Use for Monte Carlo of FTMO pass probability with sizing as variable.

**Persistence/robustness toolkit as tests** - Rule: add to the research runner (a) Lo (2002) standard error of the Sharpe ratio for every reported Sharpe, (b) K ratio (t of slope of log equity) as a smoothness metric next to Calmar, (c) cross-product ratio persistence test across two sub-periods for sleeves/symbols, (d) Hurst exponent of the strategy P&L stream, (e) "8-win streak" style run-length probability. - Source: Ch 9 pp.171-183 - Claim: Sharpe estimates are as noisy as the value. - Fit: GOOD, no new data; fits the "honest testing" focus. Not a strategy.

**52-week-high anchoring effect on implied vol / returns (shares)** - Rule: for US shares, rank daily by distance to 52-week high; long near-high, short far-from-high (George-Hwang) with monthly rebalance, market-neutral; test with real share costs (Alpaca). - Source: Ch 10 p.208 - Claim: 52-week high has significant power to predict returns (George-Hwang 2004), t-stats of implied-vol response up to 12.9 (Driessen et al.). - Fit: MEDIUM: daily bars of ~23,700 shares available; monthly turnover low so costs manageable; shorting borrow fees needed. Differs: not a breakout-on-price signal because ranking is relative cross-section with monthly holding; but is a momentum-family idea; possible overlap with known momentum results (spent?). Check ledger first.

**Index variance premium by sector/asset class on CFDs (realized variance vs ex-ante forecast)** - Rule: for each CFD index (US500, NAS100, GER40, etc.) compare previous-month realized vol with the VIX-like proxies (VIX for US) and measure the forward return of a short-straddle-like payoff approximated by sign of (VIX-implied variance - forecast realized variance) times forward index absolute return. Mostly diagnostic. - Source: Ch 11 - Fit: POOR: no option prices for non-US indices; only descriptive.

### Warnings / pitfalls
- Full Kelly is far too aggressive when edge is estimated; the SD of the estimated Kelly fraction is as large as the fraction itself at N around 10-30; use fractions 0.2-0.5, Bayesian shrinkage, and never lever an edge you have only observed once (pp.139, 143-146).
- Over-betting by 2x Kelly gives zero growth; losing probability grows quickly (p.139).
- Sharpe ratio estimates have huge sampling error; sorting strategies by Sharpe over short periods is mostly noise (p.172, SE of 1.61 on a 100-day sample).
- Peso problem: short-vol and far-OTM strategies show smooth Sharpe until the tail event; historical risk statistics understate tail risk (p.172, 222).
- Filters that improve a short-vol backtest (VIX below EWMA) may just fit one regime; author warns about curve fitting, edge from pre-2004 only (p.218).
- The variance premium is beta for a risk (crash/correlation), not free alpha; it disappears in single stocks; dispersion trades lose when correlations spike (p.219).
- VIX futures curve is not always contango (downward sloping 22% of the time with VIX < 20); the basis predictor has few observations (about 100 trades) and overlapping 5-day holds (p.226) - cf. our I-113/I-114 failures.
- VIX ETN backtests (Donninger) cover two years in one regime; no cost, borrow or slippage; treat as a hypothesis, not evidence (p.229).
- Scaling in on mean-reverting positions is only correct if the mean has not shifted; size by log-optimal rule, not martingale doubling; check for fundamental regime change (pp.158-159).
- Edge decays as others find it; counterparties change; record gross vs net by period to see decay early (p.184).
- Do not cut size after recent results; do not mix a tested system with ad hoc override decisions (pp.179-180).
- Behavioural story is not evidence: name the exact bias, derive a testable consequence, and still demand backtest plus mechanism (pp.188, 210).
