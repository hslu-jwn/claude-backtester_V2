# Strategy 4: Trend following (Kaufman style)

Requested by the user 2026-10-14: "the trend following strategy in *Trading Systems and Methods*
(Perry Kaufman), pages 152-154, Appendix B pages 329-332", to be tried on different timeframes. The
user asked Claude to answer the open questions itself.

**Source status (updated 2026-10-14, user supplied the 5th edition, 2013):**
- **pp. 152-154** (ch. 4, Charting Systems): *Dunnigan and the Thrust Method*. Swings by higher highs +
  higher lows, Dunnigan's buy patterns and thrust, the One-Way Formula, and Ruggiero's programmable
  "Dunnigan trend" -> signal `dunnigan` below.
- **pp. 329-332** (ch. 8, Trend Systems; the 5th edition has no Appendix B, its appendices are numbered
  1-6): (a) acting on the next open instead of the close gave better prices 75% of the time but lower total
  profit, because fast breakouts that never come back are missed -> we keep entry at the close; (b) a band
  around the trend line gives fewer, more reliable but later signals and a bigger risk per trade ->
  option `sma_band_atr`; (c) the calculation period matters more than the trend method; classic periods
  3, 5, 20-23, 63 and 252 days -> used in the sweep; (d) the simplest trend system: long while the n-day
  change is positive, short while negative -> signal `momentum`; (e) Taylor's MPTDI: moving average with
  a volatility-dependent entry band, a stop fixed at entry, and an opposite signal that exits and reverses
  -> the same position model as below.
- breakout, sma and kama remain Kaufman's standard trend systems chosen by Claude. Details the pages
  leave open were decided by Claude (user's instruction 2026-10-14) and are marked *(Claude)*.

Folder `strategy/trend_following/`, config `TrendFollowingConfig`, registry name `trend_following`.
Indicators here are new and only this strategy uses them, so they live in the strategy folder.

## Idea

Always follow the current trend of one timeframe. A signal in the other direction closes the open
position and opens the reverse one (stop-and-reverse). No target: profits run until the trend turns.
A protective stop at entry defines 1R and limits the loss when the trend breaks sharply.

## Trend signal (⚙️ `signal`, one rule parameterized by `Direction`)

All values use only closed candles of the strategy timeframe. "Previous N" excludes the current candle.

| Signal | Long when | Short when | ⚙️ parameters (default) |
|---|---|---|---|
| `breakout` (default) | close > highest high of the previous N candles | close < lowest low of the previous N candles | `breakout_period` 20 |
| `sma` | close crosses above SMA(N) of closes (previous close ≤ previous SMA, current close > current SMA) | mirrored | `sma_period` 50 |
| `momentum` | close − close N candles ago > 0 | < 0 | `momentum_period` 20 |
| `dunnigan` | the last two candles each made a higher high **and** a higher low than the candle before, and the close is above the last swing top | mirrored | none |
| `kama` | KAMA rises by more than the filter: KAMA − KAMA[1] > f | KAMA − KAMA[1] < −f | `kama_er_period` 10, `kama_fast` 2, `kama_slow` 30, `kama_filter` 0.1 |

- **SMA band** (⚙️ `sma_band_atr`, default 0 = plain cross): with b > 0 the line is SMA + b × ATR for longs
  and SMA − b × ATR for shorts (ATR as for the stop); the cross rule is applied to that line *(Claude:
  ATR instead of MPTDI's fixed point steps)*.
- **Momentum:** the event repeats on every candle while the change keeps its sign (like `breakout`);
  a change of exactly 0 gives no event.
- **Dunnigan swings (p. 152):** in an upswing, a candle whose high **and** low are both below the high and
  low of the upswing's highest candle starts a downswing; the upswing's highest high is a **swing top**
  (mirrored: downswing -> upswing, lowest low = **swing bottom**). Inside and outside candles never change
  the swing. Ruggiero's confirmation "above the high of the current downtrend" is read as: close above the
  most recent swing top *(Claude)*. No event before the first swing top / bottom exists.
- **KAMA:** ER = \|close − close[n]\| / Σ\|close[i] − close[i−1]\| over n candles (0 if the sum is 0);
  SC = (ER·(2/(fast+1) − 2/(slow+1)) + 2/(slow+1))²; KAMA = KAMA[1] + SC·(close − KAMA[1]), seeded
  with the close of candle n. Filter f = `kama_filter` × the standard deviation of the last 20 KAMA
  changes (`kama_filter_period` 20); no signal before 20 changes exist.
- Each candle gives at most one signal **event** (a direction). An event acts only if it differs from
  the open position's direction or there is no position; an event with the trend just keeps the
  position (`breakout` and `kama` repeat while the trend runs, `sma` fires only on the cross).
- No signal until the indicator has its full history (warm-up). The runner's warm-up must cover it.

## Position

- One position per symbol at a time. Entry at the **close of the signal candle** (like strategy 3,
  `close` mode).
- **Reverse:** an opposite signal closes the open position at that candle's close (exit reason
  `signal`) and opens the new one at the same close.
- **Protective stop:** entry ∓ ⚙️ `stop_atr_mult` (default 3.0) × ATR(⚙️ `atr_period` 20) of the
  strategy timeframe at the signal candle (Wilder ATR, `detectors/atr.py`). 1R = this distance. The
  stop does not move (no trailing, no break-even). After a stop-out the strategy is flat; the next
  signal **event** in either direction (also in the stop candle, at its close) opens a new position.
- **No take profit.** No session filter, no daily limit, no news filter.
- Engine: SL inside the candle is checked before the strategy sees the close (as for all strategies);
  a candle that hits the SL and closes with an opposite signal: SL first, then the new entry at the close.

## Timeframes (⚙️ `timeframe`)

15m, 30m, 1h, 4h (default), 1d. Everything (signal, ATR, stop) on that one timeframe; no higher
timeframe. 4h and 1d candles are UTC-aligned.

## Costs

Spread, commission and **swap** (risk-management.md › Costs). Trend trades hold for days, so every
result is reported with and without swap.

## Evaluation ("Appendix B": performance measurement and parameter sensitivity)

Grid tool `python -m backtester.tools.trend_grid`: every signal × timeframe on the 5 symbols, gross
and net, 2020-22 vs 2023-26, plus a small parameter sweep per signal (breakout 20 / 55 / 100, SMA
20 / 50 / 100 / 200, SMA 50 and 200 with band 0.5 / 1.0 ATR, momentum 5 / 20 / 63 / 252, KAMA filter
0.0 / 0.1 / 0.5, dunnigan without parameters) to check that the result is not one lucky
parameter. Reported per variant: trades, win rate, avg R gross / net, sum R, profit factor, max
drawdown in R, avg holding time. A variant counts only if neighbouring parameters and both periods
agree.
