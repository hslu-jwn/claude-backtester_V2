# Mean reversion and oscillators

Sources: K = Kaufman *TSM* ch. 3-4, 9, 11, 13-14, 16, 18, 22; H = Hougaard; EC = Chan ch.2-5, 8; KD = Davey ch.18; JK = Kaeppel.

## Where it fits
- High-noise markets and short timeframes favour mean reversion (K p.14, 870). Equity indices are the
  noisiest, so they are the natural candidate.
- Mean reversion profile: many small wins, few large losses, needs loose stops; > 60 % winners is the
  norm (K p.1012-1017). You cannot have small losses **and** a high hit rate **and** many trades.
- Mean-reversion entries pay about **half the slippage** of trend entries (limit orders, K p.742).
- Kaufman: counter-trend trading is "considerably" riskier; losses are hard to cap when the market
  keeps going (K p.401, 426). Hougaard rejects fading for retail traders entirely.
- **For FTMO:** always add a hard stop and a daily-loss guard; mean reversion without a stop can hit
  the 5 % daily limit in one trade.

## The oscillator scale problem (K p.377-384)
- Momentum's scale changes with volatility (S&P 20-day momentum ±30 in 2006, −150 in 2008). Fixed
  bands blow up. **Aggressively fading an extreme loses**; extreme momentum tends to persist short term.
- Fixes: normalised oscillators (RSI, stochastic, Fisher, CCI, Divergence Index), a trend filter
  (only buy oversold while the trend is up, so a falling market flips the trend and exits you), exit at
  zero momentum.
- Fitted thresholds (e.g. MACD ±2) are curve-fit (K p.384). Visual divergence is subjective and hard
  to code; Kaufman's own divergence code misses obvious cases (K p.424).

## Concrete rules in the books
- **RSI(2):** long when RSI(2) < 10, short > 90, exit next day; scale-in variant 25/50/75/100 % at
  20/15/10/5. On S&P extremes meant continuation before ~1998 and mean reversion after; both sides
  worked 2000-2008 (K p.389-390). Cost sensitive. → I-03
- **Oscillator as timing inside a trend:** 40-day trend up and 5-day stochastic < 20 → buy; exit when
  the trend flips; optional forced entry after n bars. The oscillator must be fast enough to fire 1-2
  times in the waiting window (K p.376, 418, 426; Elder Triple Screen p.835-838). → I-05
- **Nofri congestion reversal:** inside a range (top = high followed by 2 lower closes, bottom = low
  followed by 2 higher closes), after two closes in one direction take the opposite side at the close,
  exit next close; pause 10 bars after a large move, 2 bars after a false breakout; no stop in the
  original (K p.155-157). → I-13
- **Fade an outside bar that closes beyond the prior range:** the original trend rule died in the
  mid-1980s, the reversed rule "works much better"; stop beyond the bar, exit after ~3 bars; filter
  range > 1.5 × ATR(20) (K p.157-158, 111). → I-12
- **Intraday volatility-shock fade:** bar range ≥ 3 × average (or ≥ 2 × the same time-of-day bar's
  average) and close in the extreme 20 % → enter against it next bar, no stop for 2 bars, then stop
  beyond the extreme, exit at the close (K p.775-777). Daily version: TR / lagged ATR(60) > 2-3 →
  fade for 3-10 days; S&P up-shocks were followed by ~40-point declines over 10 days, down-shocks no
  edge (K p.626-634). → I-16
- **Gap fades:** stock gaps > 1-2 % faded to the close (Reverre); S&P "Intraday High-Low" fade of
  ≥ 0.5 % gaps with stop-and-reverse at the day extreme, +$32/trade gross on 1,600 trades
  (K p.707, 772). See [intraday-sessions-gaps-calendar.md](intraday-sessions-gaps-calendar.md).
- **Midday support/resistance** on S&P: +$268/trade on 8,404 trades 2000-2011, gross, no tuning
  (K p.754). → I-11
- **Gustafson:** long after 4 lower closes, exit after 5 higher closes or 8 days; S&P 76-78 %
  winners (long-only, bull market) (K p.1010). → I-19
- **Davey's two-closes baseline:** after 2 down closes buy at the next open (2 up closes: short), ATR stop 0.5-1.25 × ATR(14), used only to
  demo the monkey test (KD App. A). → I-19, I-03
- **Divergence Index:** (MA10 − MA40) / stdev(changes, 40)², bands ±1 stdev; buy below the lower band
  in an uptrend, exit at zero (K p.384). Self-normalising.
- **Pairs / ratio:** stress indicator = stochastic of (Stoch(A) − Stoch(B)); enter > 95 / < 5, exit at
  the middle; hold a few days; legs sized by equal ATR; correlation 0.5-0.7 is workable (K p.583-586).
  Ratio levels are not stationary (S&P/Nasdaq had 3 regimes in 2006-2011); use a volatility filter and
  a trend rule on the ratio when it trends (K p.608-612). → I-20
- Daily pivots (P, R1, S1, R2, S2) and Chande-Kroll / Jackson zones: fade toward P; no published stats
  (K p.143, 687, 805-808).

## Practitioner warnings
- Retail FX clients win 61-62 % of trades but lose overall: avg win ~43 pips vs avg loss ~78-83 pips
  (H, 43 M-trade study). Win rate alone means nothing.
- Hougaard's own statistics: 39 % winners, 13 % breakeven, still profitable through asymmetry.

## From Aziz and Volman
- **Exhaustion reversal (Aziz):** 5 or more consecutive 5-min candles one way, 5-min RSI > 90 (< 10),
  at a daily level, then an indecision or opposite candle; enter on the first candle making a new
  high (bottom) / new low (top); stop at the extreme; target the session mean, 9/20 EMA or the next
  level; exit if it goes flat. RSI 90 on M5 is rare on index CFDs; thresholds need calibration. → I-40
- **Session mean (VWAP proxy, Aziz):** above it buyers control, below sellers; long on a held
  pullback to it, short on a rejection from below; stop on a 5-min close through it. Without volume use
  the session-anchored mean of typical price; MT5 tick volume later. → I-38
- **IRB boomerang (Volman ch.12):** inside a range at least ~20 pip wide, a small block at a barrier is
  traded away from the barrier; needs ~10 pip of free path.
- **Spikes without buildup** tend to retrace fully to their origin (V ch.15). Fits I-16.

## Statistics first, then a trivial rule (Chan)
Sources: EC ch.2-5, 8. Tools: T-11; ideas I-47, I-48, I-58, I-59.
- Procedure: test the series (ADF, Hurst, variance ratio, half-life; see [markets-and-regimes.md](markets-and-regimes.md)), then trade a
  parameterless linear rule to prove the edge exists: position = −(price − MA(L))/std(L) with L = half-life. It needs unlimited capital
  and no stop, so it is a proof of edge, not a system (EC p.48-50). Bollinger version: enter at |z| > 1, exit at 0, one unit at a
  time; on GLD/USO it beat the linear version (Sharpe 0.96 vs 0.59, gross) (EC p.70-72).
- Short-term or **time-of-day mean reversion** exists even when daily bars show a random walk (EC p.63, 96); a stationary series with a
  10-year half-life is useless. Enter only in the window where the reversion exists and be flat before the next shift.
- **Buy-on-gap (stocks, EC p.93-96):** buy stocks that gap down by more than 1 sd (90-day close-to-close) below the prior low but whose open is
  above the 20-day MA; exit at the close; Sharpe 1.5 in 2006-12, faded after 2009. A momentum filter on a reversion trade: small drops revert,
  big ones carry news. Mirror and the **opposite** gap-momentum rule are in [intraday-sessions-gaps-calendar.md](intraday-sessions-gaps-calendar.md).
- Scaling in at several bands is never optimal in-sample versus all-in at a constant probability of going deeper (Schoenberg-Corwin), but with
  time-varying volatility it can win out of sample (EC p.72-74). Kalman-filter hedge ratios helped on pairs (EWA/EWC Sharpe 2.4, in-sample) but
  need a cointegrated pair; our five symbols give none (GBPUSD / GBPJPY is really a USDJPY test).
- Dangers: steady profits breed over-leverage (LTCM), rare catastrophic loss, regime change into a trend, spread strategies are very sensitive
  to bad ticks (a fake spike looks like a reversal); a stop hurts the backtest but is insurance, set it wider than the worst in-sample
  excursion (EC p.61, 84, 183). Momentum books and reversion books diversify each other.
- Mean reversion does not carry from spot to futures (roll return) and needs equal point values in a pair (same quote currency)
  (EC p.57, 109).

## Davey's euro reversal systems (futures, 2009-2013)
Source: KD ch.18-19, App. B-C. Ideas I-47, I-48. Walk-forward, Monte Carlo and incubation; 76-85 % of optimisations profitable.
- **Night (105-min bars, 18:00-07:00 ET, new trades until 01:00):** long limit at SMA(High, Nb) − ATRmult × ATR(NATR), short mirror
  (Nb 9-19, NATR 73-93, ATRmult 2.55-3.15); one trade a day, the order nearest price; target TRmult × true range (0.51-0.71), stop ≤ ~34
  ticks incl. costs, all flat at session end. Monte Carlo return/DD 2.0, P(profit year) 85 %; first 15 weeks live flat.
- **Day (60-min bars, 07:00-15:00 ET):** if High ≥ highest high of 3-5 bars and Close < Close 70-80 bars ago, sell-short limit at High +
  2-11 pips (wait for one more thrust); mirror for longs; one trade a day, stop 225-425 $, no target, exit 15:00. Return/DD 5.45 but only
  ~20 of 614 days above $1,000: without them barely profitable, so every signal must be taken.
- Cautions: limit fills need penetration; stop and target in one bar; both are fades of range extremes, close in spirit to sweeps and
  the gap fade that failed for us; his 4-year sample is short.

## Kaeppel's timing sketch (options book, no statistics)
- Wilder RSI pullback against an MA trend as entry, exit after 7 days or at the opposite extreme of a second oscillator; ADX/DMI above 75
  = overbought, expect a pause until it falls below 50 (JK p.101-105). One chart each; low priority (close to I-05). Measure instead the
  forward-return hit rate after a signal for several horizons and compare with the unconditional rate (JK p.100; T-13).
