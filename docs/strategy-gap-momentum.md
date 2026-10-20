# Strategy 7: Gap momentum (opening gap beyond the prior range)

Research candidate I-46 (Chan, *Algorithmic Trading* ch.7 pp. 155-157; ROADMAP 11.12). **Draft 2026-10-20:
the points marked ❓ wait for the user's decision; nothing is built before they are answered.**
Folder `strategy/gap_momentum/`, config `GapMomentumConfig`, registry name `gap_momentum`. Day trade: flat
before the 17:00 New York rollover (no swap).

Why: strategy 5 faded index gaps to the previous close and has no edge (ROADMAP 11.4-11.7). Chan trades the other
side, but only for gaps that open **beyond the prior day's high or low**: stop orders cluster beyond the prior
extreme and cascade after the closed period. His results are gross of costs (Euro Stoxx 50 future Sharpe 1.4,
2004-12; GBPUSD Sharpe 1.3, 2007-12). "No edge" is the expected honest outcome if net R is not positive in both
halves.

## Definitions

All times New York (`America/New_York`, DST via `zoneinfo`); base timeframe **1m**.

- **Session** (two modes, ⚙️ `mode`):
  - `index` (default): cash session 09:30-16:00 ET. Open price = close of the 1m candle closing at 09:30;
    session high / low / close = of the 1m candles 09:30-16:00 of the previous regular day (as strategy 5).
  - `fx` (Chan's GBPUSD variant): day 05:00-17:00 ET (London open to the New York close). Open price = close of
    the 1m candle closing at 05:00; prior high / low / close = of the previous day's 05:00-17:00 candles.
- **Volatility:** sd of the last ⚙️ `vol_days` (default **90**, Chan) daily close-to-close log returns of the
    sessions above, known before today's open. No trade until `vol_days` returns exist.
- **Regular day:** as strategy 5 (a previous session without its closing candle gives no trade).

## Rule (bullish described, bearish mirrored: one code path by `Direction`)

- **Long** if open > prior high × (1 + ⚙️ `entry_z` × sd), default `entry_z` **0.1** (Chan); **short** if
  open < prior low × (1 − `entry_z` × sd). Otherwise no trade. One trade per day.
- **Entry:** at the open price (the close of the 09:30 / 05:00 candle).
- **Stop:** ❓ Chan uses none (open-to-close). Our trades need a stop for R. Options:
  (a) ⚙️ `stop_atr` × daily ATR(14) from the entry (wide, close to Chan's no-stop; default 1.0);
  (b) the prior high (long) / prior low (short): the breakout failed when price is back inside the range
  (tight; costs are large in R);
  (c) the previous close (the gap is filled).
- **Target:** none (Chan). ⚙️ `target_r` = 0 means none.
- **Time exit:** ⚙️ `exit_time`, default **15:59 ET** (`index`) / **16:59 ET** (`fx`): at the close of the 1m
  candle closing at that time (signal exit); missing candle -> first later candle, as strategy 5.
- SL and TP inside one candle: SL first (engine rule).

## Backtest options

- Symbols ❓: development (histdata, before 2021-09-14): NAS100, US500 (`index`); GBPUSD, EURUSD, XAUUSD (`fx`).
  Test once on FTMO MT5 data from 2021-09-14 with the variants fixed in advance (+ US30, US2000 for `index`).
- Costs: fixed spread **and** the spread table (off by default), swap as usual (should be 0), slippage per
  ROADMAP 12.8 once built.
- Monte Carlo report (verdict with all 7 checks, family `gap_momentum`), robustness report, halves at the middle of
  the period.
- Sweep **only**: `entry_z` (0, 0.1, 0.25, 0.5), the stop option / `stop_atr` (0.5, 1, 2), `exit_time` (11:00, 12:00,
  15:59). Every variant goes into the trial log.
- Study part (I-09 / C-5): next to the strategy, open-to-close return per gap bucket (gap in sd units, beyond /
  inside the prior range, up / down), both directions, so continuation and fade are compared on the same days.
