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

Grid tool `python -m backtester.tools.research research/grids/trend_following.toml --dev-only`: every signal × timeframe on the 5 symbols, gross
and net on development data with scorecard halves, plus a small parameter sweep per signal (breakout 20 / 55 / 100, SMA
20 / 50 / 100 / 200, SMA 50 and 200 with band 0.5 / 1.0 ATR, momentum 5 / 20 / 63 / 252, KAMA filter
0.0 / 0.1 / 0.5, dunnigan without parameters) to check that the result is not one lucky
parameter. Reported per variant: trades, win rate, avg R gross / net, sum R, profit factor, max
drawdown in R, avg holding time. A variant counts only if neighbouring parameters and both periods
agree.

## Hypothesis C1: crypto trend following (pre-registered 2026-11-10, before any run)

**Hypothesis and sources.** Persistent crypto price movements may allow daily trend signals to
capture multi-week moves after costs, although reversals and financing can erase the edge. Liu and
Tsyvinski, [Risks and Returns of Cryptocurrency](https://www.nber.org/papers/w24877) (Review of
Financial Studies, 2021), report time-series momentum; Liu, Tsyvinski and Wu,
[Common Risk Factors in Cryptocurrency](https://doi.org/10.1111/jofi.13119) (Journal of Finance,
2022), document a cross-sectional momentum factor. These results motivate this test; they do not
establish profitability for this stop-and-reverse strategy or FTMO costs.

**Data and costs.** Use the default cache, BTCUSD primary (MT5 history from 2017), ETHUSD breadth
(from 2018), through 2021-09-13 inclusive; verify actual coverage. D1 candles are UTC-aligned.
At reference prices the configured spreads are about 1.0 BTCUSD and 0.66 ETHUSD, small relative to
daily ranges; commission is 3.25 bp per side. Swap is enabled: -30% per year on both sides,
approximately 8 bp per charged night, with triple charge Friday. Report results with and without
swap as required above; all gates below use swap-inclusive net R.

**Fixed grid.** `research/grids/trend_following_crypto.toml` has eight cells: signal breakout or
momentum, its corresponding period 20 or 55, and fixed protective stop 2 or 4 times ATR(20).
All other settings use the strategy defaults. The primary is BTCUSD breakout 20 with 4 ATR stop;
ETHUSD is breadth. Monkeys, sensitivity and entry screen are off. No cell is substituted for the
primary based on results.

**Gates fixed before running.** Evaluate the primary on BTCUSD unless otherwise stated:

- Sum net R > 0 at normal costs and with every cost doubled, including swap.
- Sum net R > 0 in each half of the BTCUSD development period; split at the UTC midpoint of the
  runner's development interval and assign trades by exit time (midpoint belongs to the first half).
- ETHUSD sum net R > 0 at normal costs: breadth 1 of 1, with correlated markets.
- Sum net R > 0 after removing the five highest individual net-R trades at normal costs.
- Circular block bootstrap of entry-time-ordered net R per trade: 2.5% quantile of the mean > 0,
  blocks of 5 trades, 10,000 resamples, seed 2026110.
- At least 40 BTCUSD trades. Report long and short separately, including their counts and net R,
  in view of the 2017 and 2020-21 bull runs.
- Check data integrity, including missing exit candles, for the primary and breadth trades.

The eight cells are multiple tests and C1 also adds one hypothesis to the program's cumulative
hypothesis count; report that count and the eight cells alongside any selection or significance
claim. The gates are development checks, not a substitute for the separately authorized one-time
holdout test.

**Tooling for a future run.** Development command (do not run as part of preregistration):
`python -m backtester.tools.research research/grids/trend_following_crypto.toml --dev-only`.
Afterward, `python -m backtester.tools.timed_hold_gates results/research/<folder> --primary-symbol BTCUSD --min-trades 40 --min-breadth 1`
reports normal net R, exit-time halves, breadth, count, directions and the specified trade bootstrap
per symbol. Its overall `advances` is not C1's decision: its doubled costs omit swap, it removes the
best five entry dates rather than individual trades, and its rollover-tolerant integrity check is
different from the requested missing-exit-candle check. Compute doubled swap-inclusive costs and
five-best-trade removal separately; audit missing exit candles for both symbols (the
`daily_integrity_failures` helper checks exits and observed OHLC but also flags invalid OHLC).
Verify the runner's recorded period covers the intended BTCUSD history, and use the primary cell,
not the automatically selected cell. No existing CLI computes all C1 gates as specified.

**C1 amendment (Opus, 2026-11-10, before any result):** the first development run stopped at load time
("Replay needs at least one candle"): ETHUSD has no candles in 2017, while the joint period starts at
BTCUSD's first day (2017-04-06). The grid is split, nothing else changes: `trend_following_crypto.toml`
(BTCUSD, primary) and `trend_following_crypto_eth.toml` (ETHUSD, breadth; its development period starts at
its first cached day in 2018). Same 8 cells each.

**C1 result (2026-11-10, development; `results/research/trend_following_crypto_*` latest runs after the D1 and
Saturday-closure data fixes, `b53d70c` and the following commit):** primary BTCUSD breakout 20 / stop 4 ATR:
**14 trades, +4.8 R: fails the minimum of 40 trades -> not enough evidence (neither pass nor falsified).**
All 16 cells (8 per coin) are net positive: BTCUSD breakout 20/2 +9.0 R (15), 55/2 +2.0 (5), 55/4 +2.3 (3);
momentum 20/2 +14.7 R (74), 20/4 +8.0 (70), 55/2 +3.8 (25), 55/4 +2.5 (21); ETHUSD +1.3 to +6.5 R per cell
(3-50 trades). Robustness cells cannot replace the primary. Trades stay few because the cache is still cut
into 102 (BTCUSD) / 98 (ETHUSD) segments (2018 and 2021 have partial Saturday files; indicators restart per
segment). The cuts are investigated before any follow-up hypothesis.

**C1 result after the isolated-Saturday rule (2026-11-10; segments BTCUSD 102 -> 18, ETHUSD 98 -> 15;
`results/crypto_isolated_saturday_20261110/summary.json`):** primary BTCUSD breakout 20 / stop 4: **23
trades, +3.6 R: still below the minimum of 40 -> not enough evidence; C1 is closed as inconclusive (no MT5
test).** All 16 cells net positive again: BTCUSD breakout 20/2 +8.2 (25), 55/2 +3.6 (9), 55/4 +2.6 (7);
momentum 20/2 +14.3 R (117), 20/4 +7.5 (113), 55/2 +4.0 (54), 55/4 +3.7 (48); ETHUSD +0.7 to +8.9 R per cell.
The momentum-20 cells are a lead chosen after seeing the data (parked for the user, HANDOFF › Open), not a pass.

## Hypothesis C2: crypto momentum (pre-registered 2026-11-10; the user's go for its one-time test: "Yes, test C2")

Chosen **after** seeing C1's development cells (BTCUSD momentum 20 / stop 2 ATR: 117 trades, +14.3 R,
+0.1225 R per trade; ETHUSD +4.8 R): the development result is selection-biased and proves nothing; the
one-time MT5 test is the only confirmation. Frozen: `research/grids/trend_following_crypto_c2_test.toml`
(D1, momentum 20, stop 2 ATR, swap on, BTCUSD), nothing re-tuned, test 2021-09-14 to the last cached day.
**Confirmed** only if all hold on the test period: (1) BTCUSD net R > 0 at normal costs and with every cost
doubled, swap included (computed per trade as gross minus twice all costs); (2) bootstrap 2.5 % quantile of
mean net R per trade > 0 (blocks of 5, 10,000 resamples, seed 2026110); (3) net R > 0 in both halves of the
test period; (4) mean net R per trade >= half the development value (0.061 R); (5) at least 40 trades.
Anything else is "not confirmed", recorded either way; no retest. ETHUSD is not tested (kept unspent).

**C2 one-time test result (2026-11-10; `results/research/trend_following_crypto_c2_test_52370dda/`, run
`results/20261110-134534_BTCUSD/`): NOT CONFIRMED.** Development reproduced (117 trades, +14.3 R). Test
2021-09-14..2026-11-08, BTCUSD: 215 trades, net +5.0 R (+0.023 R per trade, p 0.39). Criteria: (1) normal
+5.0 R but doubled costs incl. swap -18.9 R: **fail**; (2) bootstrap 2.5 % -0.114: **fail**; (3) halves
+12.7 / -7.8: **fail**; (4) mean 0.023 < 0.061: **fail**; (5) 215 trades: pass. Years 2021-2026: +1.9,
-5.4, +13.2, +0.6, -9.5, +4.1. The C1 development edge was mostly the 2017-2021 crypto trend regime plus
selection. No retest.
