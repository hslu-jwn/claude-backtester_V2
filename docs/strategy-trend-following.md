# Strategy 4: Trend following (Kaufman style)

Requested by the user 2026-10-14: "the trend following strategy in *Trading Systems and Methods*
(Perry Kaufman), pages 152-154, Appendix B pages 329-332", to be tried on different timeframes. The
user asked Claude to answer the open questions itself.

**Source status (updated 2026-10-14):** the user later supplied the 5th edition (2013). There,
pages 152-154 are **not** trend vs mean reversion: they are chapter 4 (Charting Systems), *Dunnigan
and the Thrust Method*: swing direction from higher highs + higher lows, Dunnigan's buy patterns and
thrust, the One-Way Formula, and Ruggiero's programmable "Dunnigan trend" (uptrend = two consecutive
candles with both a higher high and a higher low, confirmed by price moving above the high of the
current downtrend; mirrored). The 5th edition has no Appendix B (its appendices are numbered 1-6) and
pages 329-332 could not be read before the file was gone. The rules below remain Kaufman's standard
trend systems chosen by Claude; a `dunnigan` signal is a possible addition (ask the user).

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
| `kama` | KAMA rises by more than the filter: KAMA − KAMA[1] > f | KAMA − KAMA[1] < −f | `kama_er_period` 10, `kama_fast` 2, `kama_slow` 30, `kama_filter` 0.1 |

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

Spread and commission as for every strategy. **Swap is not modelled yet** (`swap_*_per_lot` = 0
until filled from MT5). Trend trades hold for days, so net results on 4h / 1d are optimistic by the
swap; this is noted with every result.

## Evaluation ("Appendix B": performance measurement and parameter sensitivity)

Grid tool `python -m backtester.tools.trend_grid`: every signal × timeframe on the 5 symbols, gross
and net, 2020-22 vs 2023-26, plus a small parameter sweep per signal (breakout 20 / 55 / 100, SMA
20 / 50 / 100 / 200, KAMA filter 0.0 / 0.1 / 0.5) to check that the result is not one lucky
parameter. Reported per variant: trades, win rate, avg R gross / net, sum R, profit factor, max
drawdown in R, avg holding time. A variant counts only if neighbouring parameters and both periods
agree.
