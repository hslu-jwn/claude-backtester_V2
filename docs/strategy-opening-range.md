# Strategy 6: Opening-range breakout

Ideas I-07 / I-08 / I-44 (`knowledge/ideas.md`), ROADMAP 11.10. Rules chosen by Claude from the knowledge
base with the user's go ("use your accumulated knowledge to set them", 2026-10-15); the volume A/B runs on
FX, gold, US30 and US2000 (user, 2026-10-15). Folder `strategy/opening_range/`, config `OpeningRangeConfig`,
registry name `opening_range`. Day trade: every trade closes before the session ends, nothing is held
overnight. Base timeframe **1m**. Bullish described, bearish mirrored (one code path by `Direction`).

Why these choices: Kaufman (p.759-764) found volatility-scaled ORBs mildly positive gross (PF 1.07-1.18)
and fixed-point ORBs mostly negative; Crabel / Kaufman found the break far stronger after narrow-range
days (I-08); Aziz trades it only when the opening range is small against the daily ATR. A close beyond
the level (not a wick) is used because wick-only breaks do not count anywhere in this project
(`confluences.md`), and the engine fills at candle closes.

## Sessions (⚙️ `sessions`, per symbol)

Every time is local wall time in the session's own zone (`zoneinfo`, DST per city).

| Market | Session | Open | Exit (session end) |
|---|---|---|---|
| US indices (NAS100, US500, US30, US2000) | New York cash | 09:30 America/New_York | 15:55 |
| GER40, EU50 | Frankfurt cash | 09:00 Europe/Berlin | 17:25 |
| UK100 | London cash | 08:00 Europe/London | 16:25 |
| JP225 | Tokyo cash | 09:00 Asia/Tokyo | 14:55 |
| FX, XAUUSD, XAGUSD | London open | 08:00 Europe/London | 12:00 Europe/London |
| FX, XAUUSD, XAGUSD | New York open | 09:30 America/New_York | 15:55 America/New_York |

FX and metals trade both of their sessions, each with its own range and its own trade.

## Entry (⚙️ `entry_mode`)

- **`range` (default):** the opening range = high / low of the first ⚙️ `range_minutes` (default **15**)
  minutes of the session (the 1m candles closing in (open, open + range_minutes]). Long signal: the first
  1m candle after the range that **closes above the range high**; short: closes below the range low.
- **`band`:** O = the close of the 1m candle closing at the session open. Long: the first candle that
  closes above O + ⚙️ `band_atr` (default 0.5) × daily ATR; short below O − band_atr × daily ATR.
- **Daily ATR:** Wilder ATR(⚙️ `atr_period`, default 14) of this session's own daily ranges (session high
  - low with the previous session close), the value known before today's session; no trade until it exists.
- **Entry** at the close of the signal candle. Signals only until ⚙️ `entry_window_minutes` (default 120)
  after the open. One trade per session (⚙️ `max_reversals` = 0).

## Stop, target, exit

- **Stop:** the other side of the range (`range`) or the other band (`band`).
- **Target:** ⚙️ `target_r` (default **0 = none**): the trade runs to the session end. Variants 1.0 and 2.0 R.
- **Session end:** a trade still open closes at the close of the 1m candle that closes at the exit time
  (or the first later candle, if that one is missing).
- **Reversal (variant, `max_reversals` = 1):** after a stop-out, a close beyond the other side within
  the entry window opens one trade the other way, stop at the first side.
- SL and TP in one candle: SL first (engine rule).

## Filters (all off by default; each is an A/B variant)

- ⚙️ `max_range_atr` (0 = off; variants 0.15, 0.3): `range` mode only, skip the session when the opening
  range is wider than this × daily ATR (Aziz).
- ⚙️ `narrow_day_filter` (off; variants `nr4`, `inside`): trade only when the previous session was the
  narrowest of the last 4 sessions (NR4) or inside the session before it (Crabel / I-08).
- ⚙️ `min_rel_volume` (0 = off; variant 1.5): the signal candle's tick volume must be at least this × the
  mean tick volume of the same minute after the open over the previous ⚙️ `volume_lookback` (default 20)
  sessions. Only on data with volume (FTMO's MT5 cache; histdata has none).
- The shared cost filter (`CostConfig.max_cost_r`) can be used as in every strategy.

## Data and test (CLAUDE.md › research mode, data split)

- **Development** (before the cut-off 2021-09-14): price-only variants on histdata 2015-2021 (FX, gold,
  silver, indices); the volume A/B on FTMO's MT5 data before the cut-off for FX, XAUUSD (2010-2021), US30
  (2019-2021) and US2000 (2018-2021), the same variant with and without `min_rel_volume`.
- **Test** once on FTMO's MT5 data from 2021-09-14 with the variants chosen in development, real costs
  (`risk-management.md` › Costs), robustness report (halves, costs x 1.5, best trade removed, share of
  profitable variants). Report "no edge" honestly.
