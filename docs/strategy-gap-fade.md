# Strategy 5: Gap fade (index cash open)

Research candidate I-39 from the open / gap study (ROADMAP 11.2, 11.4). Rule set by the user,
2026-10-15: entry **at the open** (no opening-range wait), test it as a strategy with real costs.
Folder `strategy/gap_fade/`, config `GapFadeConfig`, registry name `gap_fade`. Symbols NAS100, US500.
Day trade: nothing is held overnight on regular days (no swap).

Why: in 11.2, gaps of 0.1-1 daily ATR touched the previous cash close before the mirror level
44 vs 37 % (NAS100) and 43 vs 38 % (US500), same sign in both halves. Before costs that is about
+0.04-0.05 R per trade, so costs decide. "No edge" is the expected honest outcome if net R is not
positive in both halves.

## Definitions (same as the 11.2 study, `analytics/open_gap.py`)

All times New York (`America/New_York`, DST via `zoneinfo`); base timeframe **1m**.

- **Cash open price:** the close of the 1m candle that closes at **09:30 ET** (the last price before
  the cash open; known at 09:30, no lookahead).
- **Previous cash close:** the close of the 1m candle that closes at ⚙️ `cash_close` (default **16:00 ET**)
  on the previous trading day.
- **Gap** = cash open price − previous cash close. Gap up > 0, gap down < 0.
- **Daily ATR:** Wilder ATR(⚙️ `atr_period`, default 14) over the cash sessions (09:30-16:00) of the
  previous regular days, built from the 1m candles; the value known before today's open. No trade
  until the ATR has `atr_period` days.
- **Regular day:** a cash session with a candle closing at 16:00 ET. A day whose previous cash
  session had no 16:00 candle (half day, holiday CFD session, data hole) gives no trade.

## Rule (bullish described, bearish mirrored: one code path by `Direction`)

- **Filter:** ⚙️ `min_gap_atr` (default 0.1) ≤ |gap| / ATR < ⚙️ `max_gap_atr` (default 1.0). Other days: no trade.
- **Direction:** fade the gap. Gap down → **long**; gap up → **short**.
- **Entry:** at the cash open price (the close of the 09:30 candle), one trade per day at most.
- **Target:** the previous cash close (the gap is filled).
- **Stop:** the mirror level, entry − ⚙️ `stop_gap_mult` × |gap| for a long (default 1.0 = 1:1 in price).
  R is measured from the entry to the stop as usual; spread and commission come from the engine's
  cost model.
- **Time exit:** a trade still open at ⚙️ `exit_time` (default 16:00 ET) closes at the close of the
  1m candle that closes at that time (signal exit, `Strategy.exits`). If that candle is missing
  (half day, data hole), the trade closes at the close of the first later candle the feed has
  (the evening session on a half day; rare, kept in the results, may carry swap).
- SL and TP inside one candle: SL first (engine rule).

## Backtest options

- Run with the fixed spread **and** with the spread table (`CostConfig.spread_table`, off by default;
  the spread table stays off by default, user 2026-10-15), swap as usual.
- Robustness report (ROADMAP 6.4): halves 2020-22 / 2023-26, share of profitable variants, stressed
  costs, best trade removed.
- Sweep **only**: gap bucket (`min_gap_atr` / `max_gap_atr`, e.g. 0.1-0.25, 0.25-0.5, 0.5-1, 0.1-1),
  `stop_gap_mult` (e.g. 0.75, 1.0, 1.5), `exit_time` (e.g. 11:00, 12:00, 16:00).
- `mode` = `fade` (default) or `follow`: follow takes the other direction (gap up -> long) with the same stop and
  target distances, same days, filter and time exit. Research only, used by the random-entry baseline
  (ROADMAP 12.1, user 2026-10-15); default fade.

Research runner commands (development only):

- `python -m backtester.tools.research research/grids/gap_fade.toml --dev-only`
