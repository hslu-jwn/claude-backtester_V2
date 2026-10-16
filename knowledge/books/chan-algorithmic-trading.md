> Reading notes, own words, made 2026-10-16 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

> Cited as EC with the print page. Idea numbers C-1 to C-11 in this file are local to the notes; backlog IDs are in ../ideas.md.

# Notes: Ernest P. Chan, *Algorithmic Trading: Winning Strategies and Their Rationale* (Wiley 2013)

Page numbers are the book's printed page numbers. All text is paraphrased. Whole book read (ch 1-8, conclusion); bibliography/index skipped.

## Overview
- Practical, strategy-by-strategy book. Two camps: mean reversion (ch 2-5) and momentum (ch 6-7), plus backtesting pitfalls (ch 1) and risk/Kelly (ch 8).
- Author's stance: prefer simple, linear, near-parameterless models built on a stated economic reason ("understand the inefficiency first, build the strategy second"). Distrust nonlinear / many-parameter models (data-snooping).
- Statistical tests first (ADF, Hurst, variance ratio, half-life, cointegration), then a trivial linear strategy to prove the edge exists without parameter fitting. The tests use every bar, so they have more power than a backtest with few round trips.
- Most examples are stocks/ETFs/futures with MATLAB code; costs are explicitly NOT included in his example backtests, and he often uses in-sample parameters (he says so). Treat his Sharpe numbers as upper bounds.
- Items relevant to us: ch 1 pitfalls and significance testing; ch 2 stationarity/Hurst/half-life tools; ch 3 Bollinger / scaling-in / Kalman; ch 5 FX pairs and rollover; ch 6 correlation-of-returns test for momentum; ch 7 opening-gap momentum on futures and GBPUSD; ch 8 Kelly, Monte Carlo leverage, CPPI, stop-loss logic, risk indicators.
- Overall message: strategies fade (regime shifts, crowding), momentum crashed after 2008, mean reversion thrives on constant volatility, keep leverage conservative (half-Kelly or less), validate by walk-forward / live.

## Chapter notes

### Ch 1 - Backtesting and Automated Execution (pp. 1-38)
- Always re-backtest a published strategy yourself: details (orders at open vs just after open, bid vs ask vs last, 4:00 vs 4:15 close) change profitability. True out-of-sample only starts after the rule is frozen/published (pp. 2-3).
- Look-ahead bias (p. 4): e.g. using the day's high/low to decide an entry the same day. Cure: the same program code for backtest and live, only the data feed differs; feed bars one at a time. (Matches our SeriesView design.)
- Data-snooping (pp. 4-7): too many free parameters. Tweaking a model after seeing out-of-sample data turns that data into in-sample. Remedies: out-of-sample, cross-validation across several subsets, high Sharpe + short drawdown duration (automatically passes sub-sample tests), fewest parameters, prefer linear over nonlinear (any nonlinear model has a linear Taylor approximation; need a reason not to use it). Same Occam argument for assuming Gaussian returns unless strong evidence otherwise. Equal-weight z-score factor models beat fitted weights (Kahneman quote, p. 6). Walk-forward (ideally small real money) is the final test; he expects live Sharpe to be at best about half the backtest Sharpe (p. 7).
- Stock split/dividend adjustment, survivorship bias, primary vs consolidated prices (pp. 8-10): inflate mean-reversion backtests more than momentum (outlier prints from small off-exchange trades revert). Highs/lows from consolidated feeds are exaggerated by small trades.
- FX-specific (p. 11): quotes are venue dependent, spreads vary by venue, so backtest with bid/ask from the venue you trade; trade prices are not available in FX.
- Short-sale constraints, uptick rule (pp. 12-13): stocks only.
- Futures continuous contracts (pp. 13-15): back-adjust by price difference (keeps P&L right, return wrong) vs by ratio (return right, P&L wrong); you cannot have both; spreads need price adjustment, ratios need return adjustment. Use settlement not last-trade price; intermarket spreads need synchronous closes (use intraday bid/ask).
- Statistical significance (pp. 16-22): three null hypotheses. (1) Gaussian null: test stat = daily Sharpe x sqrt(n days); critical values 1.282/1.645/2.326/3.091 for p = 0.10/0.05/0.01/0.001. (2) Monte Carlo of simulated price series with the same first four moments (Pearson system), run strategy 10,000 times, count how often average return >= observed. (3) Lo-style: keep number of longs/shorts and hold period, randomize entry dates over the real price series. Example (TU 12-month momentum): test 1 gave 2.93 (p<0.01), test 2 only 88% (kurtosis of the returns alone helps momentum strategies), test 3 gave p~0. The three tests answer different questions; failing to reject is informative. Hypothesis test gives P(R|H0), not P(H0|R).
- "When not to backtest" (pp. 22-24): high return but low Sharpe (0.3) plus 2-year drawdown; long-only strategy that merely matches buy-and-hold (use information ratio, benchmark properly); survivorship-biased picks; neural nets with ~100 nodes and Sharpe 6; HFT backtests (market-impact "Heisenberg" issue).
- Predictive power rests on stationary statistics (pp. 24-25): regime shifts (decimalization 2001, 2008 crisis volume collapse, Reg NMS 2007, uptick rule) can void old backtests; mean reversion profits dropped when volatility fell/was spiky; momentum had a multi-year bear market after 2008.
- Platform discussion (pp. 25-37): prefer a platform where backtest and live code are the same; latency and colocation are rarely the bottleneck (broker confirmation latency is); MATLAB/R/Python for research; event-driven vs bar-driven. Low relevance for us except the "same code backtest/live" principle.

### Ch 2 - The Basics of Mean Reversion (pp. 39-62)
- Most price series are geometric random walks; returns, not prices, mean-revert around zero. Anti-serial-correlation of returns = mean reversion of prices (tradeable). Few traded assets are stationary, but we can build stationary combinations (cointegration).
- Stationarity does not mean range-bound; it means the variance of log price grows slower than lag tau (variance ~ tau^(2H), H = Hurst exponent; H<0.5 mean reverting, 0.5 random walk, >0.5 trending). (pp. 41-45)
- ADF test (pp. 42-44): regress delta-y(t) on y(t-1) (plus lagged differences, offset, drift assumed 0); test statistic = lambda / SE(lambda), must be more negative than critical value (Dickey-Fuller table; example critical values with offset, n large: -3.458 / -2.871 / -2.594 for 1/5/10%). Lambda must be negative. Start with 0 lag, often 1 lag is needed. Sampling the data more finely (intraday) does not raise significance; it is the span of time that counts. Example: USD.CAD daily, ADF stat -1.84, not stationary.
- Hurst exponent via genhurst (generalised, q=2) and Variance Ratio test (Lo-MacKinlay, tests H = 0.5) (pp. 45-46). USD.CAD: H = 0.49, VR p-value 0.37, cannot reject random walk.
- Half-life (pp. 46-48): from lambda via the Ornstein-Uhlenbeck relation, half-life = -ln(2)/lambda. If lambda >= 0, do not even try mean reversion. Very small |lambda| means long half-life and few round trips. Half-life is a natural time scale: set look-back to a small multiple of it instead of optimising. USD.CAD half-life about 115 days (daily bars). Half-life is a better predictor of strategy Sharpe than the strict ADF significance level; profitable trading works at much less than 90% certainty.
- Linear mean-reversion strategy (pp. 48-50): position size (number of units) = minus z-score of price vs moving average/std with look-back = half-life. Parameterless, uses no stop, needs unlimited capital, not practical but proves the edge. Positive P&L on USD.CAD even though not stationary, but with large drawdown and in-sample half-life (look-ahead).
- Why run tests at all: they use every bar and are independent of specific entry/exit rules, so more power than a trade backtest.
- Cointegration (pp. 50-59): CADF = regress one series on another for the hedge ratio, then ADF on the residual (order dependent; try both, pick the more negative statistic). Johansen test handles >2 series, order independent, gives rank r (number of independent stationary portfolios) via trace and eigen statistics (critical values at 90/95/99%) and eigenvectors = hedge ratios; first eigenvector has the shortest half-life. Example EWA/EWC CADF -3.64 (5% crit -3.36); EWA-EWC-IGE triplet half-life 23 days, linear strategy APR 12.6%, Sharpe 1.4 (no costs).
- Pros/cons (pp. 60-62): fundamental story for each pair, many time scales (short horizons give many trades and high Sharpe). Con: consistency breeds over-leverage (LTCM); rare loss is catastrophic; stops are hard to place logically (see ch 8).

### Ch 3 - Implementing Mean Reversion Strategies (pp. 63-85)
- Lets real implementation not require true stationarity: short-term / "seasonal" mean reversion (only in certain periods of the day) can be traded and closed before the next equilibrium shift. A stationary series with a 10-year half-life is useless.
- Spread definition (pp. 64-70): price spread (fixed number of shares), log-price spread (fixed capital weights, needs daily rebalancing), or ratio. Ratio is natural for FX crosses (EURGBP = EURUSD/GBPUSD) and robust when the pair is not truly cointegrated; for genuinely cointegrated pairs an adaptive-hedge price spread was better (GLD/USO: spread APR 10.9% Sharpe 0.59, log 9%/0.5, ratio negative).
- Bollinger-band version (pp. 70-72): enter when z-score beyond entryZscore (author example 1), exit at exitZscore (0, or opposite band); look-back = half-life or optimised; one unit at a time so capital is easy to manage. GLD/USO: APR 17.8%, Sharpe 0.96 vs 0.59 for the linear version.
- Scaling-in (pp. 72-74): Schoenberg-Corwin proof that entering at two or more bands is never optimal in-sample versus a single all-in entry when the probability of going deeper is constant; but with time-varying volatility, scaling-in may give better out-of-sample Sharpe.
- Kalman filter (pp. 74-84): dynamic regression where hedge ratio and intercept are the hidden state (random walk state, noise parameter delta ~ 0.0001, measurement variance 0.001). The prediction error is the z-score numerator and sqrt(Q) the dynamic band. EWA/EWC: APR 26.2%, Sharpe 2.4 (in-sample tuned). Also a one-variable version as a market-maker's mean-price estimator (gain depends on trade size).
- Data errors (pp. 84-85): bad ticks inflate mean-reversion backtests (a fake spike looks like a reversal) but deflate momentum; spread strategies are very sensitive to small errors. Clean data matters more for mean reversion.

### Ch 4 - Mean Reversion of Stocks and ETFs (pp. 87-106)
- Stock pairs are rarely cointegrated out of sample; ETF pairs/triplets hold up better (EWA/EWC, RTH/XLP, GLD/GDX). GLD/GDX lost cointegration after July 2008 when oil peaked; adding USO restored it (a worked example of hypothesis -> test -> fix, p. 91-92).
- Intraday buy-on-gap (stocks, pp. 93-96): buy stocks that gap down more than 1 std (90-day close-to-close return std) from prior low to open, but only if the open is above the 20-day MA (momentum filter on a reversion trade: small drops revert, big drops carry news); buy the 10 weakest; exit at the close. APR 8.7%, Sharpe 1.5 (2006-12), faded after 2009. Mirror short version also shown. Message: daily bars show no mean reversion, but certain periods (open to close) do.
- Index arbitrage with a subset of component stocks; cross-sectional linear long/short mean-reversion (Khandani-Lo weights, Sharpe 1.3 close-to-close; open-to-close version Sharpe 4.7 before costs). Not applicable to our single-instrument data.
- Warns that open prices used for signals cannot be traded at (signal noise), and primary-exchange fills are worse than consolidated.

### Ch 5 - Mean Reversion of Currencies and Futures (pp. 107-131)
- FX: commodity currencies (AUD, CAD, NOK, ZAR) are natural cointegration candidates; FX is 24h so stops work, high leverage, no short constraints (p. 108). Cross rates synthesised (AUD.ZAR = USD.ZAR/USD.AUD), P&L lands in two currencies.
- For cointegration tests, pairs must be quoted with the same quote currency so a one-point move has the same value (use AUDUSD and CADUSD=1/USDCAD, not USDCAD) (pp. 109-110). Example 5.1: Johansen hedge ratio on a rolling 250-day window, 20-day z-score, AUDUSD vs CADUSD: APR 11%, Sharpe 1.6 (2009-12, no costs). The same idea on the ready-made cross AUDCAD (fixed 1:1) gave APR 6.2%, Sharpe 0.54: the unequal hedge ratio mattered.
- Rollover interest (pp. 113-115): excess return of a cross held past 17:00 New York = log price change + log(1+i_base) - log(1+i_quote); triple rollover on the day before the weekend settles (T+2; T+1 for USDCAD/USDMXN so Thursday). For AUDCAD the interest averaged about 5% a year but changed APR only 6.7% -> 6.2%.
- Futures: total return = spot return + roll return; contango = negative roll, backwardation = positive. Roll returns can exceed spot returns (corn -12.8% vs +2.8%; VX about -50% per year). Mean reversion of spot does not give mean reversion of the futures price (author lost >$100k on this). Calendar spreads trade only the roll return; CL 12-month log calendar spread stationary, half-life 36 days, APR 8.3% Sharpe 1.3 (rolled 10 days before expiry, 61-day holds). Intermarket spreads (crack spread, CL-BZ) failed ADF. VX vs ES stationary portfolio (regime-split at mid-2008) APR 12.3%, Sharpe 1.4.
- Little of the futures material applies to us (CFD index/gold have no term structure in our data), but note: only run cointegration inside one regime, and instruments must have a common unit of point value.

### Ch 6 - Interday Momentum Strategies (pp. 133-154)
- Four causes of momentum: persistence of roll-return sign (futures), slow diffusion of news, forced fund flows, HFT manipulation.
- Test for time-series momentum (pp. 134-137): correlation (and p-value) between the past return over a look-back and the future return over a holding period, using non-overlapping pairs (step by max(lookback, hold)); scan a grid of look-backs and holds {1,5,10,25,60,120,250}; also correlation of signs; plus Hurst + variance ratio. TU example: Hurst 0.44 and VR not significant, yet correlations at (250, 25) = 0.27, p=0.02: momentum and reversion can coexist at different horizons, which Hurst alone cannot show.
- Simple rule (Moskowitz-Yao-Pedersen): go long/short by sign of the past 12-month return, hold 1 month; to smooth timing, open a 1/25 slice every day (staggered tranches). Results (Table 6.2): BR 100/10 Sharpe 1.09, HG 40/40 Sharpe 1.05, TU 250/25 Sharpe 1.04 (APR 1.7% on notional, can lever). Replacing the lagged return by the lagged roll return (threshold 3% annual) lifts TU Sharpe to 2.1.
- Other entry signals: N-day high, price vs (E)MA, Bollinger upper band, Alexander filter (x% reversal). Combining a momentum rule with a mean-reversion filter (CL: long if price below 30 days ago but above 40 days ago) improved results (APR 12%, Sharpe 1.1).
- Cross-sectional futures/stock momentum (12-month rank, hold 1 month): worked until 2007 then lost about -33% / -30% a year in 2008-09 ("momentum crashes", Daniel-Moskowitz). S&P DTI index (EMA trend on 24 futures): Sharpe 1.3 over 1988-2010 but -26% drawdown since end 2008.
- Pros/cons (pp. 150-154): momentum has fewer independent signals (long horizons) so lower Sharpe; momentum horizon shrinks as more people trade it (PEAD went from days to hours); long crash recoveries (1929: 30 years). Advantages: natural stop (exit when momentum flips), unlimited upside / limited downside, thrives on fat tails (random series with TU's kurtosis reproduced the strategy return 12% of the time), diversifies against mean-reversion books.

### Ch 7 - Intraday Momentum Strategies (pp. 155-168)
- Extra cause: stop-order triggering -> breakout strategies.
- Opening gap momentum (pp. 155-157): buy if today's open is above yesterday's HIGH by entryZscore x std of daily close-to-close returns (90-day, entryZscore = 0.1, i.e. a very small threshold); sell short if open below yesterday's LOW by the same; exit at the close (in the code the return is open-to-close). FSTX (Eurostoxx 50 future): APR 13%, Sharpe 1.4, 2004-12. Same rule on GBPUSD with "close" = 17:00 ET and "open" = 05:00 ET (London open): APR 7.2%, Sharpe 1.3, 2007-12 (no costs stated). Rationale: stops cluster and cascade after a long gap (overnight/weekend), plus overnight news.
- PEAD (stocks, pp. 158-162): trade the open after an after-hours earnings release in the direction of the gap if |gap| >= 0.5 std, exit at the close; overnight holding was negative on average. Drift horizon has shrunk to intraday. Other event drifts (M&A, index changes) also compressed. Macro news (FOMC, CPI) on EURUSD showed no significant momentum in the author's test; older research found 10 minutes of UK-data momentum in GBPUSD (pre-1999).
- Leveraged ETF end-of-day rebalancing (pp. 163-164): last 15 min momentum in the direction of the day's move when the move exceeds 2% (APR 15%, Sharpe 1.8 on DRN). Mostly an equity-index phenomenon; fed by leveraged ETF AUM.
- HFT (pp. 164-168): order-book imbalance, ticking, momentum ignition, stop hunting around support/resistance and round numbers (Osler's FX research: levels breached tend to continue), order flow as predictor (Lyons). Needs tick/Level-2 data we do not have.

### Ch 8 - Risk Management (pp. 169-186)
- Goal: maximise long-run compounded growth; fear of losses itself is not the objective. Core rule: keep leverage constant (so scale down after losses, up after gains; Example 8.1 on p. 171). This "selling into losses" is blamed for contagion (Aug 2007 quant meltdown).
- Kelly (pp. 172-173): Gaussian optimal leverage f = m / s^2 (mean excess return over variance of excess returns). Over-estimating edge or under-estimating variance causes ruin; under-leveraging only costs growth. Use half-Kelly or treat Kelly as an upper bound; for several strategies F = C^-1 M (inverse covariance times mean excess returns). When a broker cap Fmax is below total Kelly leverage, uniformly scaling is NOT growth-optimal; Example 8.2: with two uncorrelated strategies (Sharpe-ish 1.15 vs 1.7) and a cap of 2, putting everything on the better strategy gave growth 0.96 vs 0.82 for proportional scaling.
- Non-Gaussian: sample returns from a Pearson-system distribution with the strategy's four moments (100k draws), maximise g(f) = mean log(1+fR); example Kelly 18.4, simulated optimum 19, and historical-return optimum 18.4. Leverage above 1/|worst bar return| gives total ruin (30.2 in the example). Simulated drawdowns are far worse than historical: unconstrained f gave max drawdown -0.999; half Kelly still -0.96; had to cut leverage by factor 7 to get -0.5 on simulated returns (only 1.5x on historical returns). Suggest a compromise between the two estimates.
- CPPI (pp. 180-182): to cap drawdown at -D, trade only a sub-account of size D x equity with leverage f (Kelly) on that sub-account; the rest sits in cash; when equity reaches a new high-water mark, reset the sub-account to D of total equity; on losses do not top up. Long-run growth rate close to using leverage f*D on the whole account (0.002484 vs 0.002525 per day, D = 0.5), but the drawdown is bounded by D (the alternative can still draw down 0.9 with half Kelly). Apply per single strategy, not a multi-strategy book (winners would subsidise losers). Weakness: cannot protect against gaps.
- Stop loss (pp. 182-184): useless over closed-market gaps and in liquidity vacuums (flash crash stub quotes). Mean-reversion strategies: stops contradict the entry logic and lower backtest performance (survivorship bias), but protect against regime change into trending; set the stop wider than the worst backtest intraday drawdown so it never triggers in sample. Momentum strategies: the flipped signal is the stop.
- Leading risk indicators (pp. 184-186): VIX > 35 is bad for the FSTX gap strategy (return 13% -> 2.6%, Sharpe 1.4 -> 0.16) but good for buy-on-gap stocks; TED spread, HYG, MXN, ONN/OFF; the sign of the effect is strategy specific; few crisis events means high data-snooping risk.

### Conclusion (pp. 187-189)
- Process is scientific: hypothesis -> quantitative model -> test on new data -> look for the reason when it fails (GLD/GDX/oil). Judgment is still needed because the statistics are non-stationary. Author's experience: model that survived past stress needs no extra deleveraging before a crisis, start conservative; apply Kelly per strategy so a failing strategy withers quickly, rather than across the whole book.

## Topic tags

**trend**
- Time-series momentum is detected with the lagged correlation grid (p. 134-137), the Hurst exponent (>0.5) and variance ratio (p. 45, 134).
- Trend rules listed: sign of 12-month return, N-day high, price vs EMA/MA, upper Bollinger band, up-day count, Alexander filter (p. 139-140). Futures momentum is largely roll-return persistence, which does not exist in our spot/CFD data.
- Momentum crashed 2008-09 and for years after (pp. 151-152): relevant to why our strategy 4 was not stable.

**breakout**
- Opening gap breakout: open beyond prior day's high/low by 0.1 daily-return-std, trade the open-to-close (p. 156). Explanation: clustered stop orders after long closed periods cascade (p. 157). Stop hunting at support/resistance and round numbers (Osler, p. 167).

**mean-reversion**
- Test with ADF, Hurst, variance ratio; size look-back from the half-life; linear z-score scaling or Bollinger band; Kalman for adaptive mean/ratio. Short-term / time-of-day reversion exists even when daily bars show a random walk (p. 96). Pair/spread signals must use equal point values. Mean reversion needs a stop only to guard against regime change (p. 183).

**momentum/oscillators**
- Momentum filter on a reversion trade (price above 20-day MA before buying a gap-down, p. 93-94) and reversion filter on momentum (CL 30/40-day, p. 140) both improved results.

**patterns**
- No chart patterns. Only stop-cluster logic and round-number levels (p. 167).

**intraday/sessions**
- GBPUSD gap rule with day defined as 05:00 ET (London open) to 17:00 ET (p. 157). FX is 24h, week gap Fri 17:00 to Sun 17:00 ET is the natural gap (p. 157). Rollover at 17:00 ET, triple day by settlement convention (pp. 113-114). End-of-day leveraged-ETF rebalancing momentum in the last 15 min (p. 163-164). News drift horizons have shrunk to minutes/hours; macro releases on EURUSD showed none (p. 163).

**seasonality/time**
- "Seasonal mean reversion" = reversion only in particular parts of the day (p. 63, 96). Calendar-month seasonality in commodity spreads mentioned but not pursued (p. 126).

**volatility**
- Thresholds expressed in std of 90-day daily returns (gap strategies). Mean reversion thrives on high but constant volatility; falling volume/volatility after 2008 hurt it (p. 24). Regimes: ES vs VX changed relationship mid-2008, so tests/regressions must be run within a regime (p. 129). VIX>35 as a go/no-go filter, direction depends on strategy (p. 184).

**stops-and-exits**
- Time-based exits for momentum (hold N days, 25-day tranches), signal-flip as stop; mean-reversion stops only beyond worst historical excursion; stop loss and CPPI cannot beat gaps (pp. 153, 182-184).

**position-sizing/risk**
- Kelly f = m/s^2, half-Kelly, Kelly as upper bound; Monte Carlo growth maximisation with Pearson moments; leverage cap breaks proportional scaling (Example 8.2); drawdown constraint solved by CPPI sub-account of size D; keep leverage constant; per-strategy Kelly rather than portfolio Kelly (pp. 170-189).

**testing-and-robustness/overfitting**
- Three p-value constructions; cross-validation; simplicity; walk-forward live; forget backtests with low Sharpe and long drawdown; expect live Sharpe about half of backtest; run tests inside one regime; true OOS starts at publication (pp. 2-24).

**costs/execution**
- His example strategies exclude costs (stated repeatedly, pp. 49, 63, 88, 120); open-price signals are not tradable at the open (signal noise, p. 95); FX needs bid/ask from the traded venue (p. 11); rollover interest matters only for multi-day holds (p. 114); NBBO sizes are tiny, intraday spread trades need substantial cost assumptions (p. 90).

**psychology/discipline**
- Over-confidence from steady mean-reversion profits leads to over-leverage (p. 61); do not override a model manually (preface); better to start underleveraged; fund-level deleveraging into losses is contagious (p. 172).

**portfolio/diversification**
- Momentum + mean reversion books diversify each other (p. 154); apply Kelly separately to each strategy and let failing ones wither (p. 188); multi-strategy CPPI is flawed (p. 182).

## Testable ideas

All ideas below use only price data and can be run on our M1-derived bars. IDs are suggestions for the idea backlog (prefix C- for Chan).

1. ★ **Stationarity / Hurst / half-life scan per symbol and timeframe (diagnostic, not a strategy)** (C-1)
   - Rule: for each of XAUUSD, GBPUSD, GBPJPY, NAS100, US500, and each timeframe (M5, M15, H1, H4, D1) and each year/half-sample: compute (a) ADF statistic and lambda on log price with 1 lag, (b) generalised Hurst H(q=2) over lags (e.g. 2..100 bars) and the variance-ratio statistic at several q, (c) half-life = -ln2/lambda, (d) lag-correlation grid between past-k-bar and future-h-bar returns using non-overlapping pairs (k,h in {1,5,10,25,60,120,250} bars). Report per half (2020-22 vs 2023-26) to check stability.
   - Source: ch 2 (pp. 41-48), ch 6 (pp. 134-137). Author's claim: tests use every bar, have far more power than a trade backtest; they tell which regime/horizon (mean reversion vs momentum) exists before any rules are written. Practical note: half-life > a few hundred bars means no strategy; H<0.5 at short horizons and H>0.5 at long ones is the typical pattern he describes.
   - Fit: good, cheap, no new data. Use returns at the closing bar only (no lookahead; estimate on past window only if used for decisions). Does not by itself prove tradeability after spread/swap. Differs from all four failed strategies: it is a measurement that picks the horizon instead of guessing a rule. Also reveals whether the failed trend-following horizons (15m-1d) had any momentum at all.
2. ★ **Time-of-day return profile and intraday autocorrelation by session** (C-2)
   - Rule: bucket returns by hour/half-hour of day (UTC converted from New York/London) per symbol; compute mean return, std and lag-1..lag-k autocorrelation of bar returns inside each bucket, per half-sample. Candidate rules appear only where autocorrelation is robustly negative (reversion window) or positive (continuation window).
   - Source: ch 3 (seasonal mean reversion, p. 63), ch 4 (p. 96 "price series that do not exhibit mean reversion with daily bars can exhibit strong mean reversion during specific periods"). Evidence: buy-on-gap profits only in open-to-close window.
   - Fit: good; swap-free if intraday. Differs from failed ones: not a pattern/zone, a time-conditioned statistic.
3. ★ **Linear z-score scaling, parameterless, half-life look-back, on one symbol** (C-3)
   - Rule: position (in risk units, capped e.g. at +/-3 units) = -(price - MA(L)) / std(L), L = half-life from item 1 re-estimated only on past data (rolling window, e.g. 250 daily bars); rebalance each bar or day. Variant: Bollinger band (entry z=1, exit z=0) with the same L; single-unit positions.
   - Source: ch 2 (pp. 48-50, 59-60), ch 3 (pp. 70-72). Author results: USD.CAD positive but big drawdown; GLD/USO Sharpe 0.59 (linear) vs 0.96 (Bollinger), costs excluded.
   - Fit: poor-to-medium for single FX/gold/index (they are near random walks on D1; indices trend upward); more suited as a test of whether H<0.5 windows exist (use item 1 as a gate). Swap kills multi-day holds, so run on M15-H4 with intraday flat. Differs from failed ones: purely reversion, no sweeps/zones/SL ATR rule.
4. ★ **GBPUSD / FX opening gap momentum (London open, day defined by 17:00 ET close to 05:00 ET open)** (C-4)
   - Rule: define "close" = last M1 bar at 17:00 New York (prior day), "open" = first bar at 05:00 New York (07:00 or 08:00 CET depending on DST handled by zoneinfo). Long if open > prior-day high of the 17:00-17:00 window by 0.1 x std of 90-day daily close-to-close returns; short if open < prior low by the same margin; exit at the end of the London session or fixed hours later (author exits at day close); no overnight (no swap). Parameters: entryZscore 0.1 (try 0..0.5), std look-back 90.
   - Source: ch 7 (pp. 155-157). Claim: FSTX APR 13%, Sharpe 1.4 (2004-12); GBPUSD APR 7.2%, Sharpe 1.3 (2007-12); no costs mentioned. Rationale: stop clustering across the long closed gap.
   - Fit: moderate. FX gaps on a 24h market are small (weekend gap is the only real one) so the signal count is low; need spread check. The indices (NAS100/US500) have a genuine overnight gap; the same rule can be tested there as the opposite of our failed gap-fade (strategy 5 faded 0.1-1 ATR gaps, so this tests the opposite direction: momentum from the open instead of fading to previous close). Test with the robustness report, halves, stressed costs. Also compare against the gap-fade result: if fade has no edge, continuation might or might not.
5. ★ **Opening-gap continuation vs fade, conditional on gap size and prior volatility** (C-5)
   - Rule: for indices and XAUUSD, split gaps (open vs previous close/high/low) into buckets of size in units of 90-day daily std; measure mean open-to-close return per bucket and per sign. Chan's approach is the continuation side for gaps beyond prior range; his stock buy-on-gap is the reversion side for moderate gaps with an MA filter (price above 20-day MA).
   - Source: ch 4 (pp. 93-96) and ch 7 (pp. 155-157). Claim: reversal on small gaps with trend filter, continuation on gaps beyond the prior day's range.
   - Fit: good; uses the existing open/gap study infrastructure (ROADMAP 11.2). Differs from failed strategy 5 by (a) conditioning on whether the gap exceeds prior high/low and (b) adding a trend (MA) filter, and by testing both directions.
6. **VIX-like volatility regime filter using our own realised volatility** (C-6)
   - Rule: compute realised volatility (e.g. 20-day std of daily returns, or ATR percentile) on the past window and test whether a strategy's profit differs when the regime is high vs low; skip trades when above a threshold chosen on the sample years only.
   - Source: ch 8 (pp. 184-186) claim: VIX>35 turned a Sharpe 1.4 gap strategy into 0.16 but helped another. Direction is strategy specific.
   - Fit: good as a meta-filter (no external data). Differs: it is a filter for any primary signal, in line with the meta-labelling focus.
7. **Kelly / half-Kelly sizing and CPPI sub-account for FTMO** (C-7)
   - Rule: from the R trade list compute f = mean(R)/var(R) per trade-day return series; use quarter to half of that as risk per trade. CPPI: with FTMO max loss 10% treat D = 0.10 (or a stricter internal buffer like 0.06-0.08 so daily 5% limit is not hit) of equity as the trading sub-account; risk per trade = f x sub-account equity; reset sub-account to D x equity only when total equity prints a new high; never top up after losses.
   - Source: ch 8 (pp. 172-182). Claim: growth rate about the same as fixed f*D leverage, but drawdown bounded by D by construction; simulated unconstrained Kelly had -99.9% drawdown and needed a seven-fold cut.
   - Fit: directly relevant to FTMO. Not a strategy; goes into `risk/` and Monte Carlo. Note CPPI cannot stop gap losses, which exist in indices (and weekend gaps in FX/gold); FTMO daily-loss reset at midnight Prague is separate. Differs from failed ones: sizing layer.
8. **Staggered tranche holding (1/N of capital per day, hold N days)** (C-8)
   - Rule: decision each day, invest 1/N of capital for N days instead of one monthly decision; reduces timing luck and gives smoother equity.
   - Source: ch 6 (p. 138, Example 6.1). Claim: TU Sharpe about 1.0.
   - Fit: poor for us as originally stated (multi-day hold means swap), but the principle (overlapping tranches) is useful for any slow signal and for Monte Carlo realism.
9. **Correlation-grid-driven momentum on daily indices/gold (time-series momentum, 12-1 months)** (C-9)
   - Rule: long if the 250-day return is positive, short if negative, hold 25 days (tranches). Gate by the lag-correlation grid p-value (item 1) per symbol and half-sample.
   - Source: ch 6 (pp. 137-140). Claim: Sharpe about 1 on three futures, crashed after 2008.
   - Fit: poor (overnight swap, sparse signals, and strategy 4 already tested slower trend rules and failed). Only worth running as part of the grid in item 1.
10. **Mean-reversion pair on FX: AUDUSD vs CADUSD style** (C-10)
    - Rule: use only instruments we trade. Within our set the only pair with a known shared driver is GBPUSD vs GBPJPY (JPY leg: GBPJPY/GBPUSD = USDJPY, so a cointegration test on log GBPUSD and log GBPJPY is really a test on USDJPY being stationary, which it is not). A genuinely testable but data-limited variant: XAUUSD vs a USD proxy (GBPUSD) via Johansen with rolling 250-day window, 20-day z-score, Bollinger entry 1, exit 0.
    - Source: ch 5 (Example 5.1, pp. 108-112). Claim: AUDUSD/CADUSD APR 11% Sharpe 1.6; the fixed-ratio cross only 0.54.
    - Fit: poor with the five given symbols (no commodity-currency pair, and the pair must have the same quote currency); mark as untestable unless we import AUDUSD, USDCAD etc. from histdata. If imported, use same-quote-currency series, rollover cost from swap table. Differs: relative value, not directional.
11. **Stop-loss placement rule for any reversion strategy: wider than the worst in-sample excursion** (C-11)
    - Rule: set the hard stop at a multiple (e.g. 1.2-1.5x) of the worst adverse excursion observed in the development sample; check it never triggers on development years; evaluate on the test years.
    - Source: ch 8 (pp. 182-184).
    - Fit: a design rule; for FTMO it doubles as a per-trade loss cap relative to the 5% daily limit.

## Warnings / pitfalls
- Backtest pitfalls list (ch 1): look-ahead (using same-day high/low), data-snooping (many parameters, nonlinear models, tweaking after seeing OOS), survivorship bias, bad adjustment for splits/rolls, consolidated vs primary prices (inflates reversion), venue-dependent FX quotes, short-sale constraints, wrong continuous-contract adjustment, last-trade vs settlement price, asynchronous closes in spreads, regime shifts, ignoring costs, bad ticks (inflate reversion), benchmark not chosen (long-only vs buy-and-hold).
- A published or in-sample "OOS" is not OOS if you re-tuned after seeing it. Real OOS = frozen rule + new data; best = walk-forward live with small money; expect about half the backtest Sharpe.
- Hypothesis testing does not give the probability the strategy is real; different nulls give very different p-values (88% vs 100% for the same strategy, p. 19-21); a random series with fat tails alone can make momentum strategies look good (12% of runs matched).
- Mean reversion: dangerous consistency, over-leverage, rare catastrophic loss, regime change into a trend; stops hurt the backtest but are insurance; spread strategies are very sensitive to data errors; cointegration found in-sample often disappears out of sample (stock pairs; GLD/GDX broke in 2008).
- Momentum: low Sharpe at long horizons, post-crisis "crashes" lasting years, horizons shrink as the effect gets known (PEAD), data errors less harmful.
- Futures: roll return can dominate; spot mean reversion does not transfer to futures.
- FX: pairs need same quote currency for hedge ratios; rollover interest and triple-day conventions; a P&L in two currencies needs converting.
- Kelly: very sensitive to over-estimated mean/under-estimated variance; Gaussian Kelly can mean ruin with fat tails; simulated drawdowns are much deeper than historical; leverage cap makes proportional scaling suboptimal; CPPI and stops do not protect against gaps; applying the same deleveraging rule by many funds can cause contagion.
- Author's own examples exclude costs and use in-sample parameters; quoted Sharpe ratios (1-4) are optimistic ceilings, not expectations.
