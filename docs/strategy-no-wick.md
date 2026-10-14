# Strategy 3: No-wick candle in the trend

Rules set by the user, 2026-10-13. A deliberately simple strategy to test against strategies 1 and 2.
Folder `strategy/no_wick/`, config `NoWickConfig`, registry name `no_wick`. Detector rules
(swings, BOS, trend, doji) are in `confluences.md`; nothing is redefined here.

## Rule

- **Uptrend:** a **green** candle with **no lower wick** (low = open) is a long signal.
- **Downtrend:** a **red** candle with **no upper wick** (high = open) is a short signal.
- A candle of the other colour, a candle with a wick on that side, and a candle without range
  (high = low) are no signal. No trend yet (no BOS on the trend timeframe) = no trade.
- **No wick** = the wick is at most ⚙️ `max_wick_share` (default 0.0) of the candle's range.
- Entries are one rule parameterized by `Direction` (bullish described, bearish mirrored).

## Trend (⚙️ `trend_source`)

- **`higher` (default):** the trend of the next higher timeframe: 5m → 15m, 15m → 1h, 30m → 4h,
  1h → 4h. Read without lookahead: only candles closed at the current candle's close count.
- **`same`:** the trend of the entry timeframe itself.
- Trend = direction of the last BOS (`confluences.md › Trend`). 4h candles are UTC-aligned.

## Entry timeframe (⚙️ `timeframe`)

5m, 15m (default), 30m or 1h. 1m is not used. The signal candle, the swings and the stop all
belong to this timeframe.

## Entry (⚙️ `entry_mode`, three variants to compare)

| Mode | Entry price |
|---|---|
| `close` (default) | the close of the signal candle, filled at once |
| `body_end` | the open of the signal candle, i.e. the body end on the no-wick side (long: the candle's low when the wick share is 0; short: its high), limit order |
| `middle` | (high + low) / 2 of the signal candle, limit order |

Limit orders (`body_end`, `middle`) are placed at the close of the signal candle and fill when a
later candle trades back to the level (long: low ≤ level; short: high ≥ level), at the level. A candle that gaps past the level (its whole range beyond it) fills at its open; if that open is also beyond the stop, the order is dropped.
They expire after ⚙️ `order_expiry_candles` (default 6) candles of the entry timeframe if not
filled. Stop and target are fixed at the signal; R is measured from the entry price.

## SL / TP

- **SL:** beyond the **last confirmed swing** of the entry timeframe on the stop side (long: the
  last swing low; short: the last swing high), plus a buffer of ⚙️ `sl_buffer` (default 10%, as in
  strategies 1 and 2) of the distance entry → swing. The swing counts if the candle that
  confirms it has closed, which can be the signal candle itself.
- A swing that is not beyond the entry price (long: swing low ≥ entry; short: swing high ≤ entry)
  or no swing yet = no trade.
- **TP:** ⚙️ `rr` (default 1.0) × the risk from the entry price. No break-even move, no partials.

## Positions

No limit: every signal is its own trade, trades overlap, a pending limit order does not block
the next signal. No filters yet (any time, any candle size). Costs are the shared engine costs.

## Engine rule for limit fills (conservative)

The fill candle's own order of events is unknown. If its extreme on the stop side reaches the
SL, the trade is a loss at the SL (SL first). A TP inside the fill candle is **not** counted;
the trade is managed from the next candle. The recorded entry time is the close of the fill candle.

## Backtest options

Entry timeframe, trend source, entry mode, wick share, SL buffer, rr, order expiry. Compared
with `tools/no_wick_grid.py` (all variants, per year, 2020-22 vs 2023-26).
