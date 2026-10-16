# Markets, noise and regimes

Which kind of strategy fits which market and when. Sources: K = Kaufman *TSM*, H = Hougaard, EC = Chan, LP = López de Prado,
RC = Carver, JK = Kaeppel.

## Noise decides the style
- **Efficiency ratio** ER(n) = |close_t − close_(t−n)| / Σ|close_i − close_(i−1)|. 0 = pure noise,
  1 = straight line. It measures noise, not volatility (K p.10-14, 781, 868-871, 1070-1072).
- Low noise (high ER) → trend following works; high noise → mean reversion fits (K p.14, 870).
- Kaufman's test (2000-2012, futures, gross): the lower a market's noise, the higher the profit factor of
  a 40-day MA trend system. Short rates trend best, then bonds, USD crosses, energy, metals.
  **Equity indices are the noisiest and worst for trend** (S&P ER ≈ 0.12, PF ≈ 1.16) (K p.13-16, 1070).
- Noise rises as markets mature and get more participants; trend periods must get longer over time
  (K p.14-16, 870, 990). Carver agrees: most markets do not trend at short horizons, so faster trend rules usually do worse
  (RC ch.12); momentum horizons shrink as more people trade them (EC p.151).
- Alternatives to ER: price density, fractal dimension (K p.10-14), the strength oscillator
  SMA(close change)/SMA(high−low) (K p.408), "a stable short cycle exists = no trend" (Ehlers, K p.515),
  r² of a regression > 0.25 (K p.1062-1072), ADX > 20.

## What this means for our symbols
- **NAS100 / US500:** expect trend following to struggle (noisiest class); mean reversion and
  intraday structure (open, gaps, time of day) are the natural candidates. Strategy 4's failure on
  indices fits the books.
- **XAUUSD / GBPUSD / GBPJPY:** FX and metals sit in the middle; trend can work on slow timeframes but
  swap and long flat spells hurt (strategy 4 result).
- Daily direction of an index is close to a coin flip: Dow closes up on 50.4 % of days over 30 years
  despite a 10× rise (H "Everyone is a chart expert"). A higher-timeframe trend says little about the
  next 5-minute bar.
- NAS100 and US500 are highly correlated, so they are poor as a pair trade (K wants 0.5-0.7) but
  good as each other's out-of-sample check.

## Regime change and decay
- Chan adds: regime shifts (decimalization 2001, 2008 volume collapse, Reg NMS 2007) voided old backtests; momentum had a
  multi-year bear market after 2008 (momentum "crashes" of about −30 % a year in 2008-09); mean reversion thrives on constant volatility
  and suffered when volatility fell or turned spiky; regressions and cointegration must be run **inside one regime** (EC p.24-25,
  129, 151).
- Every fixed rule set is a snapshot of a changing market; edges decay as people exploit them
  (D ch.11, K p.748). Examples from K: outside-day trend rule stopped working in the mid-1980s and the
  reversed (fade) rule then worked (p.158); RSI(2) flipped from trend to mean reversion around 1998
  (p.389); ORB was dominant in the 1990s and faded after 2000 (p.760); fast Turtle 20/10 breakout died
  after the early 1980s while 55/20 survived (p.232); S&P first-bar continuation reversed in the
  2009-11 bull (p.694); calendar effects weakened after the 1970s (p.480).
- **Consequence for us:** always test in halves (2020-22 vs 2023-26) and per symbol; a rule that works
  in one half only is not an edge (this is how strategy 4 failed).
- Regimes defined after the fact are not tradable (K p.694). A regime filter must be computed from
  closed bars only (our invariant #1) and its threshold pre-declared.

## Volatility regimes
- Volatility clusters and changes the meaning of any fixed point size; make every threshold
  ATR- or %-based (K p.188, 219-220, 764).
- Kaeppel ranks volatility by decile of the instrument's own last 2 years (rank 1 = cheap, 10 = rich) because the same raw level can
  be extreme for one instrument and normal for another; also 20-day HV against its 500-day average with ±1.5 sd bands (JK p.64-72).
  The book assumes mean reversion of volatility without statistics. → I-49
- Quiet-market measures for a coming move: short / long volatility ratio (6-day / 100-day), ADX, days since the last N-day high or
  low (JK p.103-105). → I-32
- A volatility switch can reverse sign by strategy: VIX > 35 cut Chan's gap-momentum Sharpe from 1.4 to 0.16 but helped his buy-on-gap
  (EC p.184-186). Few crisis events make such filters easy to snoop.
- Low-volatility entry filter improved a 40-day MA system in 5 of 5 markets (incl. $15/side costs)
  (K p.861-866); best thresholds differed by market → test one fixed setting.
- After a shock, volatility always rises, then decays; prices often partly reverse over days
  (K p.132, 992-1000).

See also: [trend-following.md](trend-following.md), [mean-reversion-and-oscillators.md](mean-reversion-and-oscillators.md),
ideas I-01, I-02 in [../ideas.md](../ideas.md).

## Measuring what the market does (Chan, López de Prado)
Sources: EC ch.2, 6 (p.41-48, 134-137), LP ch.17-18, 13. Tool: T-11 in [../ideas.md](../ideas.md).
- Most price series are geometric random walks; returns mean-revert around zero, prices usually do not. Stationarity means the variance
  of log price grows slower than the lag: variance ~ lag^(2H), **Hurst exponent H** < 0.5 mean-reverting, 0.5 random walk, > 0.5
  trending; the Lo-MacKinlay **variance ratio** tests H = 0.5.
- **ADF test:** regress the change of log price on the lagged level (plus lagged changes); the statistic lambda/SE must be more negative
  than the critical value (about −2.87 at 5 % with offset, large n) and lambda must be negative. Finer sampling does not raise
  significance, the span of time does.
- **Half-life** = −ln 2 / lambda (Ornstein-Uhlenbeck); lambda ≥ 0 means do not try mean reversion; a half-life of hundreds of bars
  leaves no strategy. It is the natural time scale: set the look-back to a small multiple of the half-life instead of optimising. It
  predicts strategy Sharpe better than the strict ADF level; USD/CAD (daily) had H 0.49, VR p 0.37, half-life ~115 days: a random walk.
- **Momentum vs reversion can coexist at different horizons**, which Hurst alone misses: correlate the past k-bar return with the next
  h-bar return on non-overlapping pairs over a grid k, h ∈ {1, 5, 10, 25, 60, 120, 250} (Chan found 0.27, p = 0.02 at (250, 25) on a
  future with H = 0.44). Short horizons typically revert, long ones trend.
- These tests use every bar and are independent of entry/exit rules, so they have more power than a backtest with few round trips;
  report them per half-year sample to check stability.
- **Structural breaks** (LP 17): Chu-Stinchcombe-White CUSUM on log prices, S = (ln P_t − ln P_n)/(sigma·sqrt(t − n)) maximised over backward
  windows, critical value sqrt(4.6 + ln(t − n)) (standard form, one-sided); SADF (supremum of ADF over all start points; explosive when
  positive, mean-reverting when the lagged-level coefficient is negative) on **log** prices; the max is outlier-driven, so prefer the
  quantile / conditional versions; cost is O(T²), so use H1 / D1 or a capped window. Likely just another trend filter. → I-56
- **Entropy** of encoded returns (binary sign, quantile or sigma letters; plug-in or match-length estimator over 100-250 bars): low
  entropy = patterned, claimed to favour momentum, high = efficient. Unproven; at least ~10 letters on length 100 needed for an unbiased
  estimate. → I-56
- Parkinson high-low volatility sigma² = mean[(ln H/L)²]/(4 ln 2) is more efficient than close-to-close and works on any bar (LP 19.3).
- Random-walk reference for barriers: a driftless walk hits the target before the stop with probability S/(S + T) (stop S, target T in
  sigma units); a win rate at 1R : 2R not above 33 % means no edge before costs. Probability of touching a level before time h is about
  twice that of finishing beyond it (reflection principle; JK p.91-95 for the finish-beyond tables). Null reference, not a forecast: real
  returns have fat tails and volatility clusters.
