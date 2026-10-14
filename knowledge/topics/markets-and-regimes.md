# Markets, noise and regimes

Which kind of strategy fits which market and when. Sources: K = Kaufman *TSM*, H = Hougaard.

## Noise decides the style
- **Efficiency ratio** ER(n) = |close_t − close_(t−n)| / Σ|close_i − close_(i−1)|. 0 = pure noise,
  1 = straight line. It measures noise, not volatility (K p.10-14, 781, 868-871, 1070-1072).
- Low noise (high ER) → trend following works; high noise → mean reversion fits (K p.14, 870).
- Kaufman's test (2000-2012, futures, gross): the lower a market's noise, the higher the profit factor of
  a 40-day MA trend system. Short rates trend best, then bonds, USD crosses, energy, metals.
  **Equity indices are the noisiest and worst for trend** (S&P ER ≈ 0.12, PF ≈ 1.16) (K p.13-16, 1070).
- Noise rises as markets mature and get more participants; trend periods must get longer over time
  (K p.14-16, 870, 990).
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
- Low-volatility entry filter improved a 40-day MA system in 5 of 5 markets (incl. $15/side costs)
  (K p.861-866); best thresholds differed by market → test one fixed setting.
- After a shock, volatility always rises, then decays; prices often partly reverse over days
  (K p.132, 992-1000).

See also: [trend-following.md](trend-following.md), [mean-reversion-and-oscillators.md](mean-reversion-and-oscillators.md),
ideas I-01, I-02 in [../ideas.md](../ideas.md).
