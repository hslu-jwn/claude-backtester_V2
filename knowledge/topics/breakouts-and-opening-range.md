# Breakouts and the opening range

Sources: K = Kaufman *TSM* ch. 3, 5, 15-16, 20; H = Hougaard; EC = Chan ch.7; RC = Carver; KD = Davey; JK = Kaeppel; LP = López de Prado.

## Daily / multi-day breakouts
- N-day breakout (Donchian, Turtles): see [trend-following.md](trend-following.md). Reliable but large
  initial risk (= the lookback range) and few trades (~2.7 per year at 20-80 days, K p.1045).
- Failed breakout = a bar that pokes through but **closes** back inside; it confirms the range
  (K p.96). Bull/bear traps: reverse promptly (K p.146).
- Most big profits come from breakouts that never pull back; waiting for a better entry misses them
  (K p.98, 329). Delayed entry improves the fill ~75 % of the time but lowers total profit.
- A triangle narrower than normal noise is not a real compression; its "breakout" just restores
  normal volatility (K p.118).
- **Volatility breakout:** close moves more than k × ATR (k ≈ 3) from the previous close → follow
  (K p.333, 860). Kaufman's accidental reversed test: buying an upper-band momentum break gave small,
  consistent profits, i.e. extreme momentum persists short term (K p.380). → I-15

## Opening range breakout (ORB), K ch.16 p.759-770
- Rule: buy when price exceeds the session open by X, short when it falls X below; exit at the close.
  All day trades, so **no swap**.
- Crabel (1990): 49-76 % winners depending on market; better after an inside day (bonds 60 % → 76 %).
- Kaufman's update (5-min data to 2011, **no costs**): crude oil profitable at all breakout sizes but
  small per trade; small breakouts give hundreds of trades at $5-25 each (costs would kill them).
  S&P fixed-point ORB was mostly **negative**, except after inside days. Gold and bonds: "too small".
- **Volatility-scaled ORB:** X = k × ATR(n) with k 1.0-2.0. Same shape, adapts over time; crude PF
  1.07-1.18 on 480-740 trades (gross). → I-07
- **Inside / narrow-range day filter:** cuts trades by ~90 % but profit per trade 10× and PF 1.5-3.2
  in crude (60-90 trades). Raschke NR4: after the narrowest of 4 days, stop entries beyond its
  high/low, reverse on same-day failure, exit end of day 2 if not profitable (K p.762). → I-08
- **Volatility contraction filter:** only trade if 6-day volatility < 100-day volatility (Crabel; halves
  the trade count) (K p.764).
- **First-hour breakout** (McNutt): range = first 60 min; target = average daily range projected from
  the first-hour low/high (K p.764-766). **Momentum Pinball** (Raschke/Connors): previous day's 3-day
  RSI of 1-day ROC < 30 → buy stop above first-hour high, stop at first-hour low; e-mini S&P
  2000-2011 +$703/contract on 1,734 trades, gross (K p.766).
- **Fisher ORB:** require price to *stay* beyond the level for half the OR duration; exit if not
  profitable within one OR duration (K p.766-770).
- **Afternoon breakout:** a break of the morning range after midday is treated as a directional
  change (K p.749, 754, 770). → I-11

## Hougaard's opening practice (indices, 10-min chart)
- Wait for the first 10-min bar to complete. Example short: gap day, bar 1 makes a double top with a
  prior high, bar 2 is an inside bar, bar 3 closes below bar 2's low → sell, stop above the day high,
  breakeven after profit, no target (H "Everyone is a chart expert"). One example only. → I-10
- Gap-up days: continuation more likely than a fill (claim). Last hour: never short a new high of the
  day; on Friday / month-end trend days buy new highs late (claim). → I-09

## Our context
- Strategy 2 (NY open sweep on NAS100/US500) was a *fade* of the opening extreme, not a breakout.
  The plain volatility-scaled ORB and its inside-day / low-vol filters have not been tested.
- Spread is the main cost; use k ≥ 1 so the stop distance is many spreads wide.
- Session opens must come from `sessions.py` (DST-aware). Index CFDs trade almost 24 h; the "open"
  is the cash open 09:30 New York.

## Compression breakouts (Volman, Coulling)
Sources: V = Volman *Forex Price Action Scalping* (chapter), C = Coulling *Volume Price Analysis* (chapter).
- **Block / range break (V ch.10-13):** a tight box with several equal highs (or lows) on the break side;
  enter 1 pip beyond the barrier. The claimed quality factor is **pre-breakout tension**: 2-6 tiny bars
  hugging the barrier and price squeezed between the 20 EMA and the barrier, the EMA "pushing the bars
  out of the box". Trade only the side of the underlying pressure (higher lows inside the box = long). → I-33
- **Two traps (V ch.11):** *false break* = price runs straight from the other barrier and breaks at once,
  no buildup → skip; *tease* = a poke from the middle or from the EMA without a squeeze → skip. If a
  break gets no follow-through within 1-2 bars it is likely to fail (V ch.12).
- **Second chance (ARB, V ch.13):** after a break, a small cluster on or around the broken barrier, or a
  pullback into the barrier zone, gives a re-entry; stop behind the last arch of the range. → I-42
- **Coulling (C ch.7-8):** congestion zone from 3-bar pivots; a breakout counts only with a clean
  *close* beyond the zone; the broken ceiling becomes the floor (retest entry); stop on the far side.
  Wyckoff's "cause and effect": a longer congestion gives a longer move afterwards. → I-33, I-34, I-42
- Volman: ranges outnumber trends about 4 to 1 (his estimate); Coulling: ~70 % sideways; Kaufman: ~80 %.
- None of these books gives statistics; all evidence is hand-picked charts.

## ORB in Aziz (US stocks, *How to Day Trade for a Living*)
- Opening range = first 5 min (he now prefers 15 or 30); trade the first break after the range closes;
  **only if the range is much smaller than the daily ATR** (skip when the range is close to the ATR);
  stop at a VWAP close; target = next daily level, else exit on the first opposite 5-min extreme.
  Mid/large caps only; on the indices this means event days. → I-07 (adds the range/ATR filter)

## Stop cascades, event triggers and compression state (Chan, Carver, Kaeppel, López de Prado)
- **Why breakouts work (Chan):** stop orders sitting beyond a prior extreme trigger together; the effect is strongest after a long closed
  period (overnight, weekend). Stop hunting around support / resistance and round numbers: levels breached in FX tend to continue (Osler,
  EC p.157, 167). Needs order-flow data for a direct test; the gap version is testable from candles (I-46).
- **One family is enough (Carver):** breakouts, MA crossovers and oscillators capture the same trend behaviour; pick speeds, not families
  (RC ch.7). Davey's own contest system was a 48-bar highest-close breakout with RSI(30) > 50 (short mirror), fixed or ATR stop, waits of
  5 bars after a loss and 20 after a win, daily bars, ~9 futures; 40-75 % drawdowns and one trade made 95 % of a year's profit; a countertrend
  breakout variant failed walk-forward (KD p.24-28, 118-121). → I-54
- **Compression state (Kaeppel):** a long narrow range tends to precede a larger move; measure it by the short / long volatility ratio (6-day /
  100-day), ADX, and days since the last N-day high or low; then trade the break in both directions with an OCO stop pair (JK p.103-105,
  183). No statistics given; the trigger is a volatility state, not a fixed N-day high or a session start. → I-32
- **CUSUM filter (LP 2.5.2.1):** keep running up and down sums of deviations (reset at zero), fire an event only when one exceeds a
  threshold h (about one daily sd), then reset. A volatility-normalised filter rule (Fama-Blume) that does not fire repeatedly while price
  hovers at a level; used as event definition for continuation or fade. Prior: filter rules lose after costs. → I-55
