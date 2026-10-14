# Mean reversion and oscillators

Sources: K = Kaufman *TSM* ch. 3-4, 9, 11, 13-14, 16, 18, 22; H = Hougaard.

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
