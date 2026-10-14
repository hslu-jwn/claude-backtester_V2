> Reading notes, own words, made 2026-10-14 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

# Kaufman, "Trading Systems and Methods" 5th ed. - chapters 8-13 (book pp. 309-616)

Notes in my own words. Page numbers are book pages (printed headers). Text lines 13930-28166 of kaufman.txt.

## Overview

This block covers the "signal" chapters of the book: trend systems (8), momentum and oscillators (9), seasonality and calendar patterns (10), cycles (11), volume / open interest / breadth (12), spreads and arbitrage (13). Kaufman's stance is practical and sceptical. He believes trend following works because of fat-tailed price runs and slow-moving fundamentals (interest-rate policy), but says there is "no best system, only trade-offs" (all trend methods give about the same profit factor, they differ in trade count, win rate and risk). He repeatedly warns that the computer should validate an idea with a fundamental reason, not discover one; that fast systems die from costs; that counter-trend (oscillator) trading is much riskier than trend following because the scale of momentum changes with volatility; that seasonal and calendar effects change over time and many have faded; and that spreads/pairs are mean-reverting short-term and need volatility-matched legs. For our project: chapter 8 mostly confirms what strategy 4 found (costs and fast speeds kill trend following; equity indices are noisy and trend badly), and the genuinely new material is the oscillator / mean-reversion section (RSI 2-day, stochastic timing inside a trend, divergence), calendar effects, the Fisher / Hilbert / cycle tools, the "strength oscillator" as a trending-vs-sideways filter, and pairs / ratio spreads (index vs index, ratio stress indicator, carry). Volume chapter is mostly irrelevant (we have no volume); brief note only.

## Chapter notes

### Ch 8 - Trend Systems (pp. 309-368)

Why trends work and fat tail
- Three reasons given: long trends capture slow fundamental moves (rate policy); price runs have a fat tail (more long runs than a coin-flip model, fewer short runs); money flow keeps trends going. Trend following fails when the market is sideways; no technique avoids that (p. 309-311).
- Trade distribution of a simple 40-day MA system on S&P / bonds / euro / crude / gold: long right tail, one trade can offset 30 losses (Fig 8.2, Table 8.1, p. 312). Pure trend systems NEED this tail; adding profit targets or stops removes part of it (p. 320).
- Trends are clearer on lower-frequency data; hourly charts are mostly noise; fast trends show backtest profits but are unstable (p. 313). Interest rates trend best, FX moderately, individual stocks and equity indices poorly (noise). Emerging/new markets can trend strongly at first.

Signal mechanics
- Trendline direction (MA turning up/down) beat price-crosses-MA in the Amazon test: 26-37% fewer trades and better profit factor for periods 20-80; for the 5-day period price cross was less bad (Table 8.2, p. 315). Note: MA-direction signal is mathematically the same as n-day momentum sign (price vs price n days ago) (p. 368).
- Entry delay test, Eurodollar vs S&P: for the smooth market signal on the close is best, delays hurt; for the noisy S&P entering next open/close helped for most periods (Table 8.3, p. 318). Delaying entry after a signal improves the fill about 75% of the time but total profit falls because fast breakouts that never retrace are missed (p. 329).
- Profile of a long-term trend system (NASDAQ 100, 40-day MA, 10 years): only 34.7% winners, avg winner/avg loser 2.22, winners held ~32 bars vs losers ~6.6 bars, 10 consecutive losses possible (Table 8.4, p. 319). Typical: win rate often below 30%, long losing streaks.

Bands and channels (pp. 320-330)
- Band around the trendline cuts false signals: high/low-based bands, Keltner (10-day MA of typical price +- 10-day average range), percentage bands, ATR bands, standard-deviation (Bollinger 20-day, 2 sd) bands, scaled by factor s. Modified Bollinger (double-smoothed centre, alpha 0.15, width factor 2.5) corrects slow band narrowing (p. 325).
- Result with high/low bands: better for noisy S&P (turned 40-day loss into profit), worse for trending Eurodollar. Wider band = fewer signals but later entries and bigger risk per trade; too wide kills the average profit (pp. 321, 328).
- Band rules: reversal always-in-market (close beyond opposite band), or enter on band break and exit at the MA centre (neutral zone; half-size orders; can re-enter same direction) (pp. 326-328). One order per day rule suggested when using intraday penetration.
- Bollinger used mostly mean-reverting: confirm with volume/breadth; low bandwidth predicts high volatility and vice versa (p. 329). Williams combo: Bollinger bands squeezing inside Keltner channel + Chaikin oscillator cross of zero = volatility-breakout entry (p. 330).

Single-trend classic systems (pp. 330-336)
- Calculation period matters more than method (p. 330). Popular periods: 3, 5, 20-23, 63, 252 days; doubling the period (5,10,20,40,80,160) keeps percentage steps equal and avoids over-weighting slow settings.
- Described: momentum system, MPTDI step-weighted MA with volatility-dependent period/band/stop, Volatility System (buy/sell when close moves more than k x ATR(n) vs prior close, k about 3), Keltner 10-day MA rule, TRIX (triple EMA of log price, 6-day, signal 3-day MA), Raschke "First Cross" (enter first pullback in a new trend: fast-slow MA oscillator crosses its own average against the trend, with a rising low / falling high condition) (pp. 331-336).

Comparison of six trend methods (pp. 336-349) - the key result
- Tested: n-day momentum (M), simple MA direction, EMA direction, n-day breakout (NDB), swing breakout (SWG), linear-regression slope (LRS). Futures: Eurodollar, S&P, euro, crude; stocks IBM, BAC, Ford; 20 years to Feb 2011; always-in-market, no stops, close fills, $20/futures trade, $0.01/share; periods 5-160 step 5 (swing 0.25%-4%).
- Eurodollar (smoothest): all profitable, longer periods better, MA best, breakout second, momentum last. S&P: MA best; momentum the only outright loser at 160 days; the MA profit was largely one short held Apr 2007-Oct 2008. IBM: only MA profitable. Stocks lose nearly everywhere; S&P mostly loses, especially at short speeds (Figs 8.12-8.15).
- Profit factors of M/MA/EXP/LRS/NDB are close together and rise with the period; the market matters more than the formula. For S&P, euro, crude profit factors are similar up to ~85 days then diverge (pp. 342-346).
- Risk profiles differ: MA/EXP/M win only ~34% of trades (momentum ~ MA), LRS and EXP ~43%, breakout just under 50%. Breakout has less than half the trades, much larger average profit per trade and larger risk per trade (distance between n-day high and low), and is "investing" more than trading at 100+ days. MA = many small losses + few big wins ("conservation of capital") (pp. 344-349).
- Trades vs profit factor: periods producing more than ~200 trades in 20 years were clearly worse; fast trading margin per trade is too thin (Fig 8.21, p. 347-348). Swing method with percentage swing breaks on markets with quoted-yield prices.
- Robust testing standards he used: same long period for all, same start date regardless of period, speeds from a few trades/year to ~100/year, realistic costs, judge by profit factor / information ratio not net profit (pp. 348-349).
- Verdict: moving average and N-day breakout look best but with opposite profiles; "There is no best system, only trade-offs" (p. 349).

Two and three trends (pp. 350-359)
- Slow trend gives direction, fast one times entries. Three rule sets: MA cross reversal; price above/below both MAs with neutral zone; both slopes agree, exit when they disagree (Fig 8.22).
- Eurodollar 60 vs 20 day, $40 round-turn: 60-day alone avg trade $149 (1.65 PF), 20-day $62, combined (20-day signals only in direction of 60-day) $92 per trade, holding 16 days, in market only half the time (Table 8.7, p. 357). Combined results only a little below the slow trend alone but with half the time exposed.
- Eurobund 1990-2011: 40-day 13.3k, 80-day 55.6k, 40-80 crossover 35k, 20-40-80 crossover 61.2k, PF 2.80, far fewer trades (Table 8.8, p. 359). Author warns that a computer finding a profitable combination of unprofitable parts should not be trusted unless each trend has a purpose (p. 357).
- Other recipes: Donchian 5/20 (close beyond both MAs by 1 ATR; exit on cross back; claims consistent 50-year corn profit, no parameter tuning, vol-sized), Donchian 20/40 breakout (40-day high entry, 20-day low exit = Turtle basis), Golden Cross 50/200 on S&P (66.7% on SPX vs passive -7.8% in 11 years from 1999, vol-scaled to 12%), Woodshedder ROC (5-day ROC below 252-day ROC for 2 days = buy), "stay ahead of the crowd" 8/18 (vs 10/20) MA difference, Appel 3-ROC composite > 4%, 4-9-18 crossover (pp. 352-358).

Choosing speed (pp. 359-363)
- Rule of thumb: mark the swings you want to capture on a chart, take average swing length, use MA of about one-quarter of that. Example IBM 16-day MA: 36 trades, 20 winners, +114 per share over 2 years (Table 8.9, no costs). Calendar-driven participants (funds, hedgers) want a different speed than speculators. A "best" period of 6 months or more means you failed to capture the seasonal move. Accept frequent small losses rather than try to remove them.
- Signal progression: look at whether neighbouring MA lengths (e.g. 1-25) turn in order from short to long; orderly change is reliable, erratic alternation is not. Alternative: average the trend direction of many calculation periods ("consensus") to avoid dependence on one parameter (pp. 363-366).
- Fundamental early exit idea (rate policy changes) and projected-crossover price calculations (price at which MA or two MAs will cross, Lambert's MDI) (pp. 366-368).

### Ch 9 - Momentum and Oscillators (pp. 369-426)

Momentum basics
- Momentum = price now minus price n bars ago (speed). It has less lag than an MA, leads price turns, but is noisy. Use price differences, not percentages, on back-adjusted futures (pp. 370-374). Momentum != volatility. Momentum can also mean price minus its MA (relative strength).
- Zero-line crossing of momentum is essentially the MA turning; add a small band around zero for noise.
- Timing entries inside a trend: short momentum (e.g. 6 days) with a 30-50 day trend gives a pullback entry within about 3 days (p. 376).

Fading extremes (pp. 377-381)
- Draw upper/lower bounds at visual extremes, a % of max, or 2 standard deviations of the momentum (about 5% of values beyond). Entry options: aggressive (touch bound), minor confirmation (first turn after the bound), major confirmation (cross back inside), timing (n days outside). Exits: opposite signal, partial return to centre, zero line (the benchmark), allow overshoot.
- Big problem: the scale of momentum changes with volatility (S&P 20-day momentum band +-30 in 2006 but -150 in 2008). Fixed bands blow up; the aggressive fade entry cannot be given a logical stop. His accidental test with the sign reversed (buying when momentum crosses the upper bound, close-stop) showed small consistent profits: high momentum persists short-term, so aggressive fading is a LOSING rule (p. 380). Declining momentum does not mean price is falling.
- Safer: use the trend as protection (only buy extreme lows while trend is up; if price keeps falling the trend flips and exits you); stop-loss or exit at zero momentum; profit target slightly short of zero to raise win rate or slightly past zero for larger wins (pp. 380-381). "High-momentum trading" (trade with the move for minutes/hours) exists but needs full-time attention.

MACD and divergence index (pp. 382-385)
- MACD: EMA(12)-EMA(26), signal = 9-day EMA of that (also shown 20/40 etc.). Cross of MACD and signal = trend signal, but many whipsaws; filter by requiring MACD to have first reached an extreme (+-2 level in his chart) and then cross, which is curve-fitted to the instrument's scale. Appel prefers 19/39 for NASDAQ.
- Divergence Index: (fast MA 10 - slow MA 40) / (stdev of daily price changes over 40) squared; bands = +-1.0 x stdev of DI over 40. Rules: buy when DI drops below lower band while trend up; sell when above upper band while trend down; exit at DI crossing zero (p. 384) - volatility-adjusted, no fitted scale. Shown on S&P futures only (no stats).

Oscillators, normalised (pp. 385-403)
- RSI (Wilder): 14 periods, bands 30/70. Aan's study: typical RSI(14) tops/bottoms near 72/32; Kaufman says 70/30 too narrow, use roughly 1.5 sd equivalent; longer period + wider confidence bands = fewer, safer trades. Variants: RSI of n-day changes (smoother), CMO (up-sum minus down-sum / total), RSI on MA spread (MACD-RSI, 5-day RSI on 10/40-week MA spread, bands 30/70).
- 2-day RSI (Stokes, MarketSci): RSI computed on 2-day changes. Rule on S&P: buy next close when RSI(2) crosses below 10, short when above 90, exit one day later. Result he quotes: until 1998 RSI extremes meant continuation (trend), after 1998 it became a good mean-reversion signal; longs and shorts both worked 2000-2008. Scale-in version: <20 buy 25%, <15 50%, <10 75%, <5 100% (mirror for shorts) (p. 389-390). Cost sensitive because 1-day holds.
- Stochastic (Lane): %K raw = (close - lowest low n)/(highest high n - lowest low n), %D = 3-day average, "slow" versions smoothed twice. Typical bands 20/80. Best used WITH a trend filter: 60-day MA down + 20-day stochastic crossing above 80 then falling = short entry (Fig 9.16). Lane patterns (hinge, set-up, failure). Warns that delaying entries for timing costs lost opportunities, but delaying exits costs real money.
- StochRSI = stochastic of RSI values.
- Williams: A/D oscillator DRF = ((high-open)+(close-low)) / (2 x (high-low)), range 0-1; bands 80/20 raw or 70/30 after 0.30 exponential smoothing; fix for gaps by using true high/low (include previous close); entries at next open. Williams %R (10-day), Ultimate Oscillator (buying pressure over 7/14/28 with weights 4/2/1; 50% line, 30/70 exits; "failure swing" setups). Ehlers' Relative Vigor Index (close-open over high-low, 4-bar symmetric smoothing, 10-bar sum, signal line).
- Blau: True Strength Index = double EMA of 1-day price change / double EMA of absolute change (e.g. 20/20); smooth with little lag; use n-day differences for extra smoothing (10-20-20) and anticipate turn when slope flattens. Double-smoothed stochastic. TRIX as oscillator. Using the next price as the divisor to stabilise returns.
- Strength oscillator (trending vs sideways): average of daily close changes over n days divided by average high-low range over n days; large = trending, near zero = sideways (p. 408).
- Volume variants (momentum x average volume, money-flow RSI, Herrick Payoff Index with open interest) listed for completeness; volume makes indicators noisier (pp. 408-411).

Velocity / acceleration and hybrids (pp. 412-418)
- First difference of price = velocity, second difference = acceleration; acceleration turns before velocity. Sideways market = both near zero (p. 415-416).
- Hybrids: Wilder's Directional Parabolic (ADX direction filter + parabolic stop), Kestner oscillator: osc = MA10 - MA50; if ADX(14) < 30: sell when osc falling, buy when rising; (always: cover when osc turns) (p. 417). Oscillator as entry timing for a trend: 40-day trend up AND 5-day stochastic < 20 -> buy; exit as soon as trend changes; optional rule forcing entry after n days to avoid missing the trade (p. 418). Cambridge Hook (outside reversal + RSI>60 + volume/OI rising).

Divergence (pp. 418-426)
- Bearish divergence: price makes higher swing high while momentum/MACD makes lower high (bullish mirror). Must be OPPOSITE directions; stronger when divergence is large and starts from an extreme; longer timeframe = bigger reversal. Compare peaks, not noisy points.
- Rules: enter when MACD crosses its signal after the divergence is visible; exit if momentum exceeds the previous peak (divergence void), at the neutral level (50 / 0), at a price objective, or when MACD crosses back; or let it convert to a trend trade. Anticipating the divergence (short as price makes the new high while momentum is still lower than at last peak) is more profitable but riskier; scale in thirds (new high with low momentum; momentum within 15-20% of previous high; MACD cross) (pp. 421-423). Double / triple divergences more reliable.
- Programmable version (TSM Divergence): price swing size (2-5%), strength (min 5% lower indicator at second peak), stochastic length 5-10, exit when %D reaches 50 (or 40/60 variants) or fast %K touches 20. Admits code misses obvious chart divergences; slope divergence (regression slope of price vs momentum since last momentum peak) covers rounded tops. Double-smoothed 20-20-20 momentum slope divergence example NASDAQ 1999.
- Closing comment (p. 426): oscillators are best as timing tools inside a conservative strategy; make the oscillator fast enough to give 1-2 extreme readings within the waiting window (3-period oscillator on daily bars, or 10-period on hourly bars, if willing to wait 2 days) so you buy dips not rallies.

### Ch 10 - Seasonality and Calendar Patterns (pp. 427-484)

- Seasonality = yearly cycle; real for crops, energy demand, some stocks (airlines, retail); needs a physical reason. Financial markets (rates, FX, indices) are doubtful candidates because participants can choose their timing (pp. 483-484). Only commodities (mostly agriculture; copper) showed consistent seasonality in Bernstein's catalogue (p. 473).
- Methods to extract seasonality: monthly averages / medians (median preferred), detrending by regression or first differences (Bernstein), percentage vs yearly average, indexed prices, link relatives and chain relatives, 12-month centred MA method (simplest and good), X-11/X-12-ARIMA, Winters' method, Fourier. Use cash data or unadjusted prices for percentages; back-adjusted futures give wrong percentages and distorted seasonal shapes (pp. 430-451, wheat example Table 10.1).
- Robustness remarks: a few extreme years distort averages (cotton); compare bull vs bear years; patterns change (wheat low moved from June to April in 2001-2010); volatility rises into the seasonal peak, which confirms a true seasonal; use volatility seasonality to size positions (pp. 440-454).
- Corn rule-set (cash): buy end-April if price in lower half of 5-year range, exit end-July; short end-July if in upper 35%, exit end-Oct; "non-seasonal year" short end-Jan if price in upper 35% (pp. 460-464). In practice trade December futures: sell end-Feb exit end-July was consistently profitable 1990-2010, buy end-Jul / exit Oct-Dec inconsistent (Figs 10.21-10.26).
- Stock market calendar effects (pp. 478-483) with the author's evidence: holiday effect (Merrill: day before holidays up 67.9% of the time 1897-1964 vs 50.8% day after; Fosback: buy 2 days before holiday, sell 1 day before, 880% 1928-1975 with 70% winners vs -41% for the rest of the days; later weaker); month-end effect (buy last or second-to-last trading day, exit 4th trading day of next month; confirmed by several authors, weaker after 1975); Hirsch "Nov 1 to Apr 30" six-month rule; January barometer (first 5 days + whole January direction predicts year; works mainly for bull years; Dow 12 years to 2010 only 7 correct, weak); McGinley January rule (S&P first 5 days up -> buy and hold, 32 correct out of 40 since 1942); Freeburg: October has most "ricochet rallies"; September weakest. S&P futures monthly pattern 1982-2010: summer decline, strong Oct-Nov; "sell in May" less reliable recently (Fig 10.29-10.30). Presidential cycle (Ch 11): pre-election year best (~11% Dow, 1912-1992), midterm year worst (2.3%); S&P futures 1983-2010 totals: pre-election 16.4, election 69.5, first year -30, second year 48.3 (Tables 11.1, 11.3).
- Key warning on data mining: academic found 18 straight years of "good coffee crop then good European wheat harvest" after testing hundreds of pairs; failed in year 19 (p. 470). "Computer is used to validate a belief, not to create one." Do not use exact days; seasonality is only reliable at monthly resolution; average into position (p. 484).

### Ch 11 - Cycle Analysis (pp. 485-526)

- Cycles come in agricultural/production, business cycle (8.6 years), Kondratieff 54-year wave (only 3 observations), presidential 4-year cycle, short behavioral cycles. Livestock cycle 9-12 months; Swiss franc cycles 24-52 weeks with up to 40% variance (so not tradeable by fixed period). At least 8 repetitions needed before believing a cycle; detrend and deseasonalise first.
- Detection tools: manual peak spacing (Ehrlich Cycle Finder), subtract MA from price, triangular MACD (long MA = half cycle length, short = half of that; example 20-10, 63-day for quarterly earnings), trigonometric regression (1 or 2 frequencies; copper 8.4 and 10.6/2.6 quarters), Fourier / FFT power spectrum (needs stationarity, 256+ points), Excel Fourier add-in with monthly returns (airline and corn examples reproduce seasonal pattern), Maximum Entropy (Ehlers MESA, short samples), Hilbert Transform (quadrature = 0.0962 p[t] + 0.5769 p[t-2] - 0.5769 p[t-4] - 0.0962 p[t-6]; in-phase = p[t-3]; phase angle sawtooth).
- Ehlers' use: the existence of a short-term cycle means the market is NOT trending (cycles usable ~20% of the time) - a regime detector, not a trading signal itself (p. 515).
- Fisher Transform: scale price within n-period high-low channel to -1..+1 (x = 0.5*2*((P-minL)/(maxH-minL)-0.5) + 0.5*x_prev), then y = 0.5 ln((1+x)/(1-x)); sharp turning points; trigger line like MACD signal; overbought/oversold about +-80 (on ratio charts); best signals just after an extreme not near zero (pp. 518-520). Inverse Fisher of RSI (mom 10, RSI 20, WMA 30) gives bipolar +-1 output.
- Cycle Channel Index (Lambert's CCI): (typical price - SMA) / (0.015 x mean deviation), +-100 bands contain 70-80% of values; N should be at most a quarter of the cycle. Lorca-Susino Short Cycle Indicator (EMA8/EMA20 squared distances vs high/low of 20 bars, intraday 30/60 min S&P, complex multi-condition rules). Hurst phasing (half-span and full-span MA shifted by half their length to project cycle highs/lows and symmetric price targets, 10% error margin) (pp. 521-526).
- No tested P/L numbers given for any cycle trading rule in this chapter; mostly illustrations.

### Ch 12 - Volume, Open Interest, Breadth (pp. 527-564) - brief (we have no volume)

- Futures volume is posted a day late, spreads and rolls are not counted; use total volume across contracts. Tick volume (number of price changes in a bar) is a decent proxy for volume when real volume is missing (pp. 528-529, 560). Our M1 histdata has no usable volume, but tick count or range-based proxies might exist for CFD feeds (MT5 tick_volume) - not in the histdata files.
- Daily volume is erratic (stdev about 38% of the mean); use smoothed volume; high volume mostly predicts high volatility rather than direction. Intraday volume has a W (or U) shape: high at open, dip, bump, high into close; compare each time bucket with its own history, never "rising volume" in absolute terms (pp. 529, 561-562). Opening-bar volume above normal tends to mean a high-volume, higher-volatility day.
- Indicators discussed: OBV with low-volume and small-price-move filters (pp. 563-564), Market Facilitation Index = range / tick volume (volume up + MFI up = potential new trend; volume down + MFI up = false move), integrated forecast model (regression slope forecasts of price, volume, OI, OBV, weights tested), breadth indicators for stocks (advance/decline etc.), filtering low-volume bars from signals.
- Relevant takeaway only: intraday seasonality of activity/volatility (time-of-day) is real and strong; the same pattern shows up in range per time bucket, which we CAN measure from price alone.

### Ch 13 - Spreads and Arbitrage (pp. 565-616)

Concepts
- Spread = long one market, short a related one (pairs, intermarket, calendar). Reduces directional risk if legs correlated: Var(A-B) = VarA + VarB - 2Cov. A spread in practice is often not lower risk if volatility is mismatched (spread behaves like the more volatile leg) or margin/leverage is increased; third factor (FX) adds risk (pp. 571, 604, 615-616).
- Arbitrage types: location, carry (cash and carry limit), product (crush, crack), interest-rate parity (forward FX = spot x (1+i_foreign)/(1+i_domestic)), cross-rate consistency (triangular), program trading index vs futures fair value. Mostly institutional / high-frequency; not available to us.
- Globalisation increased correlations, especially in a crisis (go to 1.0); spreads relationships change structurally (gold/silver ratio 33:1 was "normal" but ranged 20-100 over the decades) (p. 600-601).

Pairs trading (pp. 583-586, 609)
- Selection: correlation 0.5-0.7 (higher gives too little profit versus costs, lower is riskier), better: cointegration (Engle-Granger, Johansen, Phillips-Ouliaris). Trade mean reversion over a few days only; longer holds fight the trend of each leg.
- Method 1: compute 14-day raw stochastic for each leg, enter when the difference exceeds a threshold T (e.g. >50 or <-50), exit when the difference returns to zero.
- Method 2 "stress indicator": take D = Stoch1 - Stoch2, then apply a raw stochastic over the same window to D itself; enter short leg 1 / long leg 2 when stress > 95, reverse below 5; exit at middle. Spreadsheet only, no performance numbers given (HPQ vs SUN illustration).
- Sizing: equalise risk of the legs - invest equal dollars / divide a risk budget by 20-day dollar ATR of each leg (e.g. 1000/ATR$). Extreme price/vol ratios between legs are dangerous (Fig 13.24).
- Mean-reverting vs trending spread: noise dominates short term, trend dominates long term; a pairs trade is a short-term noise bet; a sustained divergence (e.g. S&P vs Russell ratio) is best handled with a trend rule on the ratio (p. 608).
- Volatility of the ratio jumps (S&P/NASDAQ futures ratio showed 3 regimes 2006-2011; mean-reversion levels fixed in 2006-07 would have been catastrophic in 2008); add a low-volatility filter (spread too quiet to pay costs) and use relative-value indicators (stochastic, RSI, Fisher) not fixed ratio levels (p. 610-612).
- Intermarket index spreads: ratio S&P/Dow stayed in about a 6% band in 2002-03 and was traded as short-term mean-reverting; S&P/Russell ratio trended (pp. 581-583). Dow/S&P/NYSE/Russell spreads express macro opinions.
- Ratio as "new market": crude/gold ratio with 40-week MA trend rule, legs vol-adjusted; ratio profits lower than trading legs individually but low vol and correlation 0.42 of weekly P/L to the single-market trend results = diversification; ratio trades more often than the legs' own trend systems (pp. 604-607). Same with XOM/crude and WERN/crude (daily, 40-day MA).
- Market-neutral baskets: rank by indicator, long top basket / short bottom basket, replace names only if they move 2+ places, equal volatility-adjusted exposure, correlation 0.5-0.7; stock noise favours short holding mean reversion (pp. 613-614).

Carry trade (pp. 596-599)
- Money flows to the highest real yield; forward FX prices already discount the rate differential, so the carry trade profit comes from "forward bias": high-yield currencies tend not to depreciate as much as parity implies. Rule: at each month-end rank currencies by 3-month rate differential vs USD, long high-yield/short low-yield, volatility-adjust sizes, rebalance monthly. March 2009 sample: 6 of 7 pairs moved in the carry direction (Table 13.3, Fig 13.12). Risks: periods of violent unwinds (crisis), concentration in the funding currency (USD/JPY/CHF), correlated moves across majors, emerging currencies add return and risk. Kaufman cites bank carry indices as evidence of long-run profit but no hard statistics.

Other
- Calendar-spread dynamics, crack/crush, interest-rate yield curve spreads, TED spread, merger arb, single stock futures: not relevant for our instruments.

## Topic tags

**trend**
- Fat-tailed run lengths are why trend following pays; right tail can offset 30 losses; wins are ~30-35% for MA systems, ~50% for breakouts. All simple methods (momentum, MA, EMA, regression slope, N-day breakout) have similar profit factor, differing in risk profile (Ch 8, pp. 311-349).
- Equity index trending is weak/noisy: S&P mostly loses for MA systems, only a few long slow settings win, one big short in 2007-08 carried the result (pp. 339-341). IBM etc. lose. Matches our strategy 4 result on indices.
- Costs: systems with over ~200 trades in 20 years were worse; 5-day MA loses on everything (pp. 315, 348).
- Stops and profit targets reduce the chance of capturing the tail (p. 320) - relevant to our fixed 3xATR stop.
- Use trendline direction rather than price cross (fewer trades, better PF at 20+ days); use bands on noisy markets (S&P benefited), no band on smooth markets (pp. 315, 321).

**breakout**
- N-day breakout: fewer trades, higher win rate (~50%), big per-trade profit, big risk per trade; Donchian 20/40 (Turtle basis); Volatility System buy/sell if close moves > 3 ATR vs previous close (pp. 333, 343-345, 353).

**mean-reversion**
- RSI(2)-type rules on S&P: buy < 10, sell > 90, hold one day; mean-reversion regime appeared after ~1998 (pp. 389-390).
- Bollinger bands normally used mean-reverting but needs confirmation; momentum fade needs trend filter and volatility-scaled bands; zero-momentum exit; stochastic only with trend (pp. 329, 378-381, 395).
- Pairs / ratio spreads mean-revert in days; hold only a few days; volatility filter (pp. 584-586, 610).

**momentum/oscillators**
- Momentum is leading but noisy; scale is volatility-dependent; fixed bands fail; normalised oscillators (RSI, stochastic, DRF, TSI, Fisher, CCI) fix the scale but not the regime problem. Divergence is the most popular use but hard to program (pp. 377-379, 423-426).
- Aggressive fading of extremes loses; extreme momentum tends to persist short term (p. 380).
- Best role: timing inside a trend (pullback entry) with an oscillator fast enough to fire 1-2 times in the waiting window (pp. 376, 418, 426).

**patterns**
- Cambridge Hook (outside reversal + RSI > 60 + volume/OI), Lane stochastic patterns (hinge, set-up, failure), RSI top/bottom formations, head and shoulders on RSI (pp. 387, 396, 418). No stats given.

**intraday/sessions**
- Intraday activity has a U/W shape through the day with spikes at open and close; compare each time bucket to its own history (pp. 560-562). Short-cycle detection (MESA/Hilbert) intended for intraday bars: presence of a short cycle = sideways market (p. 515).
- Entry timing: next-open or after a small retracement improves price 75% of the time but loses total profit (p. 329).

**seasonality/time**
- Seasonality only credible where physical/behavioral cause exists; monthly resolution only; patterns shift; use median; compare bull/bear years; confirm with seasonal volatility (Ch 10).
- Stock calendar effects: pre-holiday, month-end (buy last day, exit 4th day of new month), Hirsch Nov-Apr, January indicators, presidential cycle; many weakened after the 1970s (pp. 479-484, 492-494).
- Financial markets (FX, rates, indices) are poor seasonal candidates (p. 483).

**volatility**
- Band width, ATR and stdev scaling; Bollinger squeeze precedes expansion; volatility seasonality confirms real seasonals; position size should shrink when seasonal volatility is high; ratio volatility regimes (pp. 322-329, 454, 610).

**stops-and-exits**
- Exit trend trades when trend flips, do not delay exits for timing (p. 395, 418). Divergence trades exit when momentum exceeds the prior peak or reaches neutral. Parabolic stop + ADX in hybrid. Oscillator-based profit target at zero momentum. Hurst target = mirror distance about the trend line.

**position-sizing/risk**
- Size by volatility: investment / (ATR x point value) (p. 354); equalise leg volatility in spreads (p. 586); Golden Cross vol-scaled to 12% annual vol (p. 355); reduce size in seasonally volatile months.

**testing-and-robustness/overfitting**
- Standards listed on p. 348-349 (same period, same start date, speeds from 2-3 to ~100 trades per year, realistic costs, profit factor). Doubling the period (5,10,20,40,80,160) for fair sampling. Do not trust a combination of unprofitable pieces that turns profitable unless each piece has a purpose (p. 357). Fundamental reason first, computer validates (p. 331, 470). Expectation checks ("bridge example") to catch wrong tests (p. 346). Fitted oscillator thresholds are unreliable (p. 384).

**costs/execution**
- $20 per futures trade, $0.01/share used; fast systems unrealistic without costs (p. 337). Entry on signal close vs delayed (p. 316-318). Order tricks like pre-computing the price that will trigger the signal (p. 316). Spread orders cheaper than two legs, legging in adds risk (p. 614).

**psychology/discipline**
- Long losing streaks (10 in a row) are normal for trend systems; most traders dislike holding through giveback; accept frequent small losses instead of trying to remove them (pp. 319-320, 363).

**portfolio/diversification**
- Ratio-spread "new markets" give 0.42 correlation to the same MA applied to legs; correlation rises in crises; carry trade needs a diversified currency basket vol-adjusted (pp. 599, 605, 570).

## Testable ideas

Ranking: ★ = most promising for our data (price only; FX, gold, NAS100, US500; M1 resampled).

1. ★ **RSI(2) / 2-day-change mean reversion on index (and test FX/gold)** - rule: RSI computed on 2-bar changes (Wilder smoothing 14-bar average-off or 2-bar); long when RSI(2) < 10, short when > 90, exit on the next bar close (daily bars) - variants: scale-in 25/50/75/100% at 20/15/10/5; intraday version on 1h/4h bars with exit after 1-3 bars (no overnight swap); filter with trend (price above/below 200-day MA) as option. Source: Ch 9, "The 2-Day RSI" pp. 389-390 (Stokes/MarketSci). Claimed evidence: S&P futures; flipped from trend-following to mean-reverting after 1998; long and short both profitable 2000-2008; he warns it is cost sensitive. Fit: good for US500/NAS100 daily (spread small vs daily range, 1-day hold costs one swap night; FTMO index swap is small); poor for FX unless intraday. Differs from failed ones: counter-trend, very short hold (days or bars) so swap barely matters, no SL/TP structure from SMC, not a trend system. Must check the regime flip claim in halves of our 2018-2026 data.

2. ★ **Trend filter + short-oscillator pullback entry** - rule: slow trend = 40-day (or 1h: 200-bar) MA slope; buy when trend up and 5-period stochastic < 20 (or RSI(2) < 10 or 3-bar momentum at -1 sd band); mirror for shorts; exit when trend flips or when stochastic returns to 50-80 (profit target at momentum zero) - optionally a forced entry after n bars. Source: Ch 9 "Using a Oscillator as Timing for a Trend System" p. 418, p. 376, p. 395, p. 426 (oscillator period chosen so it gives 1-2 extremes in the allowed waiting window); also Raschke First Cross p. 335. Claimed evidence: qualitative only. Fit: good on 15m-4h in FX/gold/indices; hold times can be limited intraday (no swap) or multi-day (swap). Differs from strategy 4: that enters on the trend change and holds with 3 ATR stop; here the entry is a pullback inside an established trend with a quick profit target, many more samples, limited time in trade.

3. ★ **Calendar and time-of-day effects (price-only)** - (a) Month-end: buy US500/NAS100 close of last (or second last) trading day of month, exit close of 4th trading day of next month (Merrill/Fosback/Kaeppel, p. 480). (b) Pre-holiday: buy close of 3rd day before an exchange holiday, sell close of day before the holiday (p. 479-480). (c) Hirsch: long Nov 1 - Apr 30 (p. 480). (d) Turn-of-quarter, September/October monthly bias (p. 483). (e) Intraday hour-of-day drift and range profile per symbol and session (derived from W-shaped activity pattern, pp. 561-562, 529): measure mean return and range per 15-30 min bucket in UTC, then test simple fade/follow of the first N minutes of London and NY, or use the profile as a filter/time stop for any strategy. Source: Ch 10 pp. 478-483, Ch 12 pp. 560-562. Claimed evidence: Fosback 880% 1928-75, month-end and holiday effects still profitable but weaker (Freeburg); Dow monthly pattern 1998-2010 shows Oct and April strength (Fig 10.30). Fit: indices hold multi-day long (swap on longs is a cost for index CFD; check FTMO rates); intraday bucket studies cost-free apart from spread. Different from failed ones: pure time rule, no price pattern; extremely cheap to test. Kaufman warns effects decay and need a fundamental reason (flows, tax, vacation, month-end rebalancing).

4. ★ **NAS100 vs US500 ratio mean reversion (stress indicator)** - rule: ratio r = NAS100/US500 (or log ratio) on 1h or daily bars; 14-bar raw stochastic of each leg's price (or of ratio); D = stochastic(NAS) - stochastic(US500); stress = stochastic of D over the same 14 bars; stress > 95: short NAS100/long US500, stress < 5: reverse; exit when stress mid (50) or D crosses 0; max hold a few days; legs sized by equal 20-bar dollar ATR (or beta-neutral); skip trades when ratio volatility is below a threshold (low-vol filter, p. 610) or has jumped (vol-regime filter). Source: Ch 13, Methods 1-2 pp. 584-585, sizing p. 586, volatility regimes pp. 610-611, index ratio p. 581-583. Claimed evidence: illustration only (stocks); index ratio S&P/Dow stayed inside ~6% in 2002-03. Fit: moderate. Pros: market neutral, uses our two index symbols, intraday exits possible. Cons: correlation between NAS100 and US500 is very high (Kaufman's rule says 0.5-0.7 is workable, much higher leaves too little profit to pay for two spreads), both legs pay spread + commission, swap on both legs partly offsets; ratio trended strongly (tech outperformance 2019-2020, 2023-24) so use a trend filter on the ratio (p. 608). Differs from failed: market-neutral relative value, not directional price pattern or MA trend.

5. ★ **GBPUSD / GBPJPY cross-rate relative value and swap-signed carry** - (a) the third leg USDJPY ~ GBPJPY/GBPUSD; trade the synthetic cross vs actual (triangular consistency, Ch 13 cross-rate matrix pp. 575-576): spread = ln(GBPJPY) - ln(GBPUSD) - ln(USDJPY) is zero by construction on a single broker feed, so only useful against a separate USDJPY series (we do not have USDJPY) - note for the user. (b) Instead: ratio GBPJPY/GBPUSD (= JPY vs USD strength) with the stress-indicator rules of idea 4 and a trend filter; (c) carry: hold direction of positive swap (use the FTMO swap sign/size as the rate-differential proxy, e.g. long GBPJPY earns positive swap), rebalance monthly, size by volatility, with a trend filter or stop when 12-bar drawdown exceeds x ATR (carry unwinds are violent). Source: Ch 13 carry trade pp. 596-599, pairs pp. 583-586. Claimed evidence: one month (March 2009) 6 of 7 currency pairs followed carry direction; long-run bank carry indices cited without numbers. Fit: carry could be the only idea that EARNS swap instead of paying it, test whether FTMO positive swaps on long GBPJPY exceed spread + drawdown costs; risk is unwind crashes (2008, 2020, Aug 2024) that threaten FTMO 5%/10% loss limits. Differs from failed: yields from holding rather than price pattern.

6. **Fisher Transform / stochastic extreme with trigger cross** - rule: channel = n-bar high/low (n = 10-20), x smoothed 0.5 factor, y = 0.5 ln((1+x)/(1-x)); trigger = previous value; sell when Fisher crosses below trigger after being above +80% (in scaled form), buy mirror; exit near zero. Source: Ch 11 pp. 518-520 and Ch 13 p. 612. Claimed evidence: chart examples only. Fit: all timeframes; mean-reversion; low parameter count. Overlaps with idea 1-2 (it is an oscillator); test mainly as a cleaner trigger than raw RSI.

7. **Divergence Index mean-reversion in trend (volatility-normalised)** - rule: DI = (SMA10 - SMA40)/(stdev of 1-bar price changes over 40)^2 (as printed in the book; verify formula scaling), band = +-1 x stdev(DI, 40); buy when DI below lower band while slow trend is up, sell when above upper band while trend down, exit when DI crosses zero. Source: Ch 9 pp. 384-385. Claimed evidence: S&P chart only. Fit: all TFs; self-normalising, so no fixed scale problem. Differs: the scale problem of fixed momentum thresholds is solved by construction.

8. **Strength Oscillator as regime filter** - rule: S = SMA(close - close[1], n) / SMA(high - low, n) (n = 10-20) or with 3-bar change; high |S| = directional, near 0 = sideways; use to switch between trend-following and mean-reversion (idea 1/2) or to skip our failed strategies in the wrong regime. Plus Ehlers idea: if a stable short cycle (Hilbert phase) exists then the market is not trending. Source: Ch 9 p. 408, Ch 11 p. 515, velocity/acceleration both near zero = sideways p. 415. Claimed evidence: none quantified. Fit: cheap filter to test on all prior strategies and on ideas above.

9. **Momentum continuation after a 3-ATR move (Volatility System)** - rule: if close moves more than k x ATR(n) (k = 3, n = 20) from the previous close, enter in the same direction at the next bar open, exit after m bars or on a trailing stop; also test the fade version to confirm it loses. Source: Ch 8 p. 333, Ch 9 p. 380 (accidental reversed-rule test: buying upper-bound momentum with a close-stop gave small consistent profits across futures). Claimed evidence: "small but consistent profits", no numbers. Fit: intraday on indices/gold around news; costs matter (spread vs few-minute edge). Differs: event-bar momentum, very short hold.

10. **Bollinger squeeze breakout (Williams combo)** - rule: Bollinger(20, 2 sd) inside Keltner(20) channel = squeeze; then go in the direction of the first oscillator zero-cross / close outside the band; exit at the MA centre. Source: Ch 8 p. 330 (Williams, Chaikin oscillator requires volume - substitute momentum or MACD histogram). Claimed evidence: none. Fit: 15m-4h, all symbols; volatility-expansion entry which we have not tried. Differs: volatility regime driven, not trend or SMC pattern.

11. **Williams A/D oscillator (DRF) with gap link** - rule: DRF = ((high - open) + (close - low)) / (2 x range), range uses prior close extension (true high/low); 0.30 EMA smoothing; short when smoothed DRF > 0.70, long when < 0.30, enter next open; exit on opposite or after N bars. Source: Ch 9 pp. 397-401. Claimed evidence: soybeans Jan-Mar 2011: raw 9 trades 6 won, smoothed 2 trades both won (tiny sample). Fit: OHLC only; good for daily indices/gold; very small evidence, high chance of noise.

12. **Two-trend filter to cut time in market (halved exposure)** - rule: enter only in the direction of a slow trend (60-day) using signals of a faster trend (20-day); exit when fast flips; otherwise flat. Source: Ch 8 Table 8.7 pp. 350-357 (per trade profit rises from $62 to $92; time in market ~50%), Table 8.8 (20-40-80 crossover PF 2.80 on Eurobund). Claimed evidence as stated. Fit: poor-to-moderate for us: this is essentially a refinement of failed strategy 4; only worth testing if idea 8 shows regime dependence. Different only by the long-only-in-trend pullbacks.

13. **Seasonal volatility sizing** - rule: compute average range/ATR per calendar month (and per weekday / session hour) for each symbol; scale risk down in historically high-vol months/hours and up in calm ones, or skip hours with range below spread x multiple. Source: Ch 10 pp. 453-454 (position sizing from seasonal volatility), Ch 12 pp. 561-562. Fit: good for all symbols, directly tested through R-multiples and cost-to-range ratio; improves cost efficiency of any strategy.

14. **Cycle length -> MA period rule** - rule: set the trend MA = one-quarter of the average swing length measured on a rolling window (not by eye), choose momentum span = half to one cycle. Source: Ch 8 pp. 360-362, Ch 9 p. 376. Evidence: single IBM example (36 trades, 20 winners). Fit: a cheap, non-optimised way of picking parameters; can feed ideas 2 and 12.

Not recommended for us (explain): seasonal agri rules, crush/crack/yield-curve spreads, program trading, merger arb, volume/OI indicators, Kondratieff/presidential/Hurst cycles (too slow or no instrument), classic divergence with visual peak picking (see pitfalls), weather degree-day work.

## Warnings / pitfalls

- Costs: systems that trade more than ~200 times in 20 years had clearly lower PF; 5-day systems lose; results ignoring costs look better than real (pp. 337, 347-348). 1-day-hold RSI(2) systems are "sensitive to costs" - check return per trade against spread, commission and swap (p. 390).
- Regime change: RSI(2) flipped from trend-following to mean-reverting in 1998; Merrill/Fosback holiday and month-end effects faded after market participation grew; wheat seasonal low shifted; January barometer is weak recently; ratio levels (S&P/NASDAQ) shifted by 25%+ after 2008. Reassess in halves of sample.
- Oscillator scale problem: fixed momentum thresholds fail across volatility regimes; aggressive entry at the extreme can not have a logical stop, and extreme momentum tends to continue; always filter by trend or use normalised/self-scaling indicators (pp. 379-380, 384).
- Counter-trend trading is "considerably" riskier than trend following: losses are hard to limit when the market keeps moving (p. 401, 426).
- Fitted thresholds (MACD +-2 lines etc.) are curve-fit and unreliable (p. 384). Divergence is subjective on a chart and hard to code; his own code misses obvious cases (p. 424). Do not trust visual examples; there are no published P/L statistics for divergence, Fisher, CCI, cycle rules.
- Computer-found parameter combinations without a causal reason (the coffee/wheat story, 18 years in a row) fail out of sample; need fundamental logic first (p. 470). Combos of individually unprofitable trends that become profitable should be distrusted (p. 357).
- Removing outlier months/years "to clean the pattern" is manipulation (LTCM comparison, p. 469); a few extreme years can create fake seasonal patterns (cotton, p. 440).
- Do not pick exact days; seasonality only at monthly resolution; average into positions (p. 484).
- Stops and targets reduce the fat-tail capture of trend systems; delayed entry improves price 75% of the time but gives up total profit (pp. 320, 329).
- Spread/pair risks: ratio levels are not stationary; volatility jumps in a crisis; correlations go to 1 in crises; mismatched leg volatility turns the spread into an outright position in the more volatile leg; low volatility ratio may not pay costs; leverage from low margin hides risk; legging in adds risk (pp. 600, 604, 610, 614-616). Pairs that are too correlated (above ~0.7) give too little profit versus costs.
- Carry trade: forward bias profit is steady but with violent drawdowns and funding-currency concentration (USD, JPY, CHF); not "free interest" because the forward already discounts the differential (pp. 597-599).
- Back-adjusted futures cannot be used for percentage or ratio math (can go negative); our CFD/spot data does not have this problem but swap/rollover must be modelled (pp. 322, 374, 430).
- For FTMO: mean-reversion systems can have occasional very large losses (no natural stop); define a hard stop and daily-loss guard before testing any of ideas 1-5.
