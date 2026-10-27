# Test tool: Fill probe (not a strategy)

**TEST TOOL, never research or trade it for profit.** Rule set by the user, 2026-10-27 (ROADMAP V2.6d step 1).
Folder `strategy/fill_probe/`, config `FillProbeConfig`. Deliberately **not** in
`strategy/registry.py` (no research tool, grid, golden list or ranking may pick it up); only the
demo bot runs it: `python -m backtester.live.bot --strategy fill_probe` (`live/bot.py`
`BOT_STRATEGIES`; default symbols `FILL_PROBE_SYMBOLS`, risk 0.01 % per trade, comment prefix
`fp`).

Purpose: the FTMO demo bot runs it to produce many varied fills (long and short, different minutes and
spreads) so slippage, spreads and commissions can be measured. Profit does not matter. It is not from
research and has no edge claim; its backtest results must not enter trial logs, portfolios or rankings.

## Rule (one code path by `Direction`)

Base timeframe 1m, warm-up 1 day. At every closed 1m candle (`now` = its close time):

- **Entry only if** the last candle of the view closes exactly at `now` (the market is open), `now.minute %
  interval_minutes == 0` (default 30), and no trade of this instance is open or pending (freed on
  `on_trade_closed` and `on_order_skipped`).
- **Direction** alternates per instance: long, short, long, ... on every order sent, also if it is skipped.
- **ATR:** Wilder ATR(`atr_period` 14) of the 1m candles (true range with the previous close). No order until
  it exists and is > 0.
- **Entry** = the current close. **Stop** = entry -/+ `stop_atr` (3.0) x ATR. **Take profit** = entry +/-
  `target_r` (1.0) x (entry - stop) distance; `target_r` 0 = no take profit.
- **Time exit:** `exits()` returns the open trade once `now - entry time >= max_hold_minutes` (20).
- `Order.confluence = "probe"`, reason `fill probe long #3`.

## Settings (`FillProbeConfig`)

| Field | Default |
|---|---|
| `interval_minutes` | 30 |
| `atr_period` | 14 |
| `stop_atr` | 3.0 |
| `target_r` | 1.0 |
| `max_hold_minutes` | 20 |
