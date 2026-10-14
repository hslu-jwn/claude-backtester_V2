# Chart patterns, bar patterns and price levels

Sources: K = Kaufman *TSM* ch. 3-5, 15, 18; H = Hougaard.

## General verdict
- Patterns come from crowd habits, but most are seen in hindsight. Only rigid, coded rules can be
  tested (K p.113, 147). Common one-bar patterns are frequent and therefore weak alone; combine them
  with filters (K p.113).
- Academic studies cited by Hougaard: hammer/shooting star and most candlestick reversal patterns have
  mean returns indistinguishable from zero. Larry Williams found no clustering of S&P retracements at
  Fibonacci 38.2/61.8 (H).
- With so many retracement levels (25, 33, 38.2, 50, 61.8 …) price touches one by chance; require
  confirmation (slowing momentum, a close) and a 10-15 % tolerance (K p.159-167).
- Lookahead trap: pivots, spikes, islands and V-tops exist only after the following bars; detectors
  must emit on the confirming bar (K p.113, 119, 147). This is our invariant #1.

## Patterns with some evidence or a codeable rule
- **Key reversal + volatility filter:** raw key reversal "strikingly unimpressive"; with true range
  > 1.5 × 20-day average it improved markedly on heating oil (K p.111). → I-12
- **Spike:** high exceeds the prior n highs and both neighbours by k × ATR, k > 0.75 (K p.107).
- **Outside bar closing beyond the prior range:** fade it (see mean reversion) (K p.157-158).
- **Inside / narrow-range bar:** precedes expansion; best known as an ORB filter (K p.762-764). 3-bar
  inside pattern up-inside-up → continuation (gold, silver, crude) (K p.158).
- **Lo-Mamaysky-Wang (US stocks 1962-96):** smoothed-extrema definitions of H&S, double top,
  rectangle etc.; patterns occur far more often than in random data; 9 of 10 had positive 3-day
  returns, 5 significant. Small edge, daily horizon (K p.176-178). → I-23
- **Bulkowski:** best bullish = rectangle top breakout, falling wedge, ascending triangle, double
  bottom; symmetric triangle the most dependable (K p.178-179).
- **DeMark Sequential:** 9-bar setup (close < close 4 bars earlier), 13-bar countdown (close < close
  2 bars earlier); takes 21-39 bars; robustness only across unrelated markets (K p.173-176).
- **Pivot (fractal) breakout:** break of the last confirmed n-bar pivot high/low; Colby's pivot-reverse
  system on 101 years of DJIA was profitable (K p.108, 158).
- **Hougaard's discretionary patterns:** inside-bar break at the open with a double top; equal-size
  second pullback ("harmonic retracement"); big drop off the open → 2-3 bar bounce → new lows. All
  single examples, undefined tolerances. Fibonacci 78.6 % with a tiny stop: ~20 % hit rate, claimed
  positive (no data).

## Levels
- **Round numbers** attract orders (NY Fed study); place orders just beyond them (K p.81, 167).
- **Daily pivots:** P = (H+L+C)/3, R1 = 2P−L, S1 = 2P−H, R2 = P+H−L, S2 = P−H+L (K p.143, 687).
- Support/resistance from trading firms predicted intraday FX pauses for about 5 days (Oster, K p.95).
- Broken resistance becomes support (K p.96).
- **Price objectives:** pattern height from the breakout (−20 % conservative); several partial targets
  (K p.133-139).
- **Value area (Market Profile):** central ~70 % of time-at-price; moves outside the prior value area
  are directional. Buildable from M1 (time replaces volume) (K p.822-830).

## Our context
- Our SMC tools (FVG, OB, BOS, sweeps) are a family of swing/level patterns. The books give no
  evidence for them specifically; strategies 1-3 built on them failed. Treat any new pattern idea with
  the same skepticism and test it mechanically.

## From Volman, Aziz and Coulling
- **Round numbers (V):** 00 and 50 levels (and 20-steps as light guides) act as magnets and barriers;
  EURUSD often moves in 20-pip steps; don't trade a small setup straight into a near round number; a
  round number 10-13 pip beyond a break helps the target. For gold use $5/$10, indices 50/100 points. → I-30
- **Equal highs/lows** need rounding to whole pips (or an ATR tolerance) to be detected (V ch.2).
- **Aziz S/R:** horizontal levels only, from daily wicks/extremes, near the current price; a level is a
  zone; more touches = stronger; enter on an indecision candle at the level, stop on a 5-min close
  beyond, target the next level. Named candle patterns and diagonal trend lines rejected as subjective.
- **Coulling candles:** hammer / shooting star / long-legged doji / hanging man, graded by volume; the
  wick is the first thing to read; repeated wicks at one level (2-3 within a few bars) matter more.
  Price-only proxy: wick length vs ATR, bar range vs average. → I-41
- **Coulling pivots:** 3-bar pivot (middle bar has a higher high *and* higher low than its neighbours,
  or a lower low and lower high); a pivot high followed by a pivot low defines a congestion zone.
- **Triangles / triple tops (C ch.11):** rising triangle (flat ceiling, higher lows) = break up; falling
  = break down; pennant = direction unknown. Single chart examples only.
- See [volume-and-wyckoff.md](volume-and-wyckoff.md) for accumulation/distribution, tests and climaxes.
