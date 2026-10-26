# Market regime classifier

**Accepted 2026-10-23** (the user left the three open choices to Opus, rule set by the user
2026-10-23): daily candles for every strategy, efficiency ratio as the trend measure (ADX as
an option), ER 0.30 over 20 closed days, volatility split at the median of the last 2 years.
Build it in V2.6.

Implemented in `analytics/regime.py` (V2.6): incremental closed-D1 labels, ER and ADX.
D1 follows the adapter default: 17:00 America/New_York with DST-aware close times.
ATR uses Wilder smoothing (simple-average seed); volatility rank is the fraction of the
previous lookback observations <= the current ATR/close (ties included, current excluded).
Trend and volatility warm up independently. The profile's stricter best-condition rule
(detrended mean, >=30 trades, positive BCa 90% lower bound) is specified in
`strategy-profile.md` and supersedes the original raw-mean best-regime summary below.

Shared tool in `analytics/regime.py`, used by every strategy's results, research cards and the
portfolio (V2.6 / V2.7). It labels each **trade** with the market regime at its entry, so every
result can be split by regime ("works in trends", "works in quiet sideways markets").

## Sources

- Trend vs noise: Kaufman's **efficiency ratio** ER(n) = |close_t - close_(t-n)| /
  sum |close_i - close_(i-1)|; 0 = pure noise, 1 = straight line; low noise favours trend
  following, high noise mean reversion (Kaufman, *Trading Systems and Methods*, p.10-16,
  781, 868-871, 1070-1072; `knowledge/topics/markets-and-regimes.md`).
- Alternative trend measure: Wilder's **ADX** (Wilder 1978, *New Concepts in Technical Trading
  Systems*), "ADX > 20 = trend" (Kaufman p.1062-1072).
- Volatility: rank the instrument's volatility against **its own** recent history, because the
  same raw level is extreme for one market and normal for another (Kaeppel, *The Option
  Trader's Guide to Probability, Volatility and Timing*, p.64-72: deciles of the last 2 years);
  ATR as the volatility measure (Wilder; Kaufman p.188, 219-220).

## Rule (no lookahead)

- Input: **daily candles of the trade's symbol that closed before the trade's entry time**
  (`HigherTimeframeClock`-style: the last D1 candle with close time <= entry time). Never the
  entry day's own unfinished candle.
- **Trend:** ER over `er_days` closed days. ER >= `er_trend` -> trend, direction by the sign of
  close_t - close_(t-n): `trend_up` / `trend_down`; otherwise `sideways`.
  (Option `trend_method = "adx"`: ADX(`adx_period`) >= `adx_trend` -> trend, direction by
  +DI vs -DI.)
- **Volatility:** ATR(`atr_period`) / close of the last closed day, ranked against the same
  measure over the previous `vol_lookback_days` closed days; rank >= `vol_high_rank` -> `high`,
  else `low`.
- Not enough closed history -> `unknown` (counted separately, never guessed).
- Label per trade: trend part x volatility part, e.g. `trend_up / high`.

## Config (frozen dataclass `RegimeConfig`, proposed defaults)

| Field | Default | Why |
|---|---|---|
| `timeframe` | D1 | regimes are slow; the same for every strategy, comparable across them |
| `trend_method` | "er" | Kaufman's measure; noise is what decides trend vs mean reversion |
| `er_days` | 20 | about one month of trading days |
| `er_trend` | 0.30 | to be checked: indices average ~0.12, so 0.30 marks clear trends |
| `adx_period`, `adx_trend` | 14, 20 | Wilder's period, Kaufman's threshold |
| `atr_period` | 14 | Wilder |
| `vol_lookback_days` | 500 | ~2 years (Kaeppel) |
| `vol_high_rank` | 0.5 | split at the median: half the days high, half low |
| `min_trades_best` | 30 | a regime is named "best" only with at least this many trades |

## Output

- Each trade gets `regime_trend` and `regime_vol`.
- Breakdown per regime (6 cells + unknown): trades, net R, R / trade, win rate; shown on every
  research card and results page. **Best regime** = highest R / trade among cells with at least
  `min_trades_best` trades (none if no cell qualifies).
- Tests: hand-built daily series with an obvious answer (straight line -> trend_up, zigzag ->
  sideways), the no-lookahead test (appending future days never changes a past label; the
  entry day's own candle is never used), DST / weekend days, unknown with short history.

## Decisions (2026-10-23)

1. Daily candles for every strategy.
2. ER is the default trend measure; ADX stays a config option.
3. ER 0.30 over 20 days; volatility split at the median of 2 years (one setting for all
   symbols; per-symbol thresholds only if the user asks later).
