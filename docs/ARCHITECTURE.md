# Architecture

## Layers

Each layer only imports from the layers above it in this list.

1. **core/**: value types (`Candle`, `Timeframe`, `Direction`), `CandleSeries` (engine-private
   full history), `SeriesView` (lookahead-safe window), `HigherTimeframeClock`.
2. **data/**: `DataAdapter` interface. `CsvAdapter` now; an exchange API and MetaTrader 5
   (FTMO) adapter later. Returns closed candles in UTC, oldest first.
3. **detectors/**: incremental, timeframe-agnostic pattern detectors. Input: a `SeriesView`.
   Output: events stamped with their confirming candle. Spec: `confluences.md`.
4. **sessions.py**: maps UTC timestamps to Tokyo / London / New York sessions (DST-aware).
5. **strategy/**: combines detectors across timeframes into setups and trade signals in price
   terms (entry, SL, TP). Strategy 1: `session_zone_sweep/`. Spec: `strategy-session-zones.md`.
6. **engine/**: the backtest loop. Owns the `CandleSeries`, steps time, hands out views,
   opens and closes trades, and records each closed trade with its result in **R**.
7. **analytics/**: statistics on R trade lists.
8. **risk/**: turns an R trade list into account equity under prop-firm rules; Monte Carlo
   and parameter sweeps. Spec: `risk-management.md`.
9. **ui/**: Dash + Plotly. Reads results; never contains trading logic.

## How a backtest steps through time

```
for each base-timeframe candle i (5m for strategy 1), oldest first:
    now   = close time of candle i
    v5    = series_5m.view(i)
    v30   = clock_30m.view_at(now)     # only fully closed 30m candles
    v1h   = clock_1h.view_at(now)
    1. update open trades with candle i (SL first if SL and TP share a candle)
    2. detectors.update(...) for each timeframe whose newest candle just closed
    3. strategy.on_candle(now, v5, v30, v1h, detector state) -> new orders
    4. engine fills orders at candle i's close (spec: "enter at that close")
```

A higher-timeframe detector is updated only when a new candle of that timeframe has
closed, so it is called exactly once per candle, as on its own chart.

## Data flow

```
DataAdapter -> CandleSeries -> engine loop -> detectors -> strategy -> trades (R)
                                                                        |
                         analytics (win rate, expectancy, DD in R) <----+
                         risk (sizing, FTMO sim, Monte Carlo, sweep) <--+
                         ui (chart with zones + position boxes, risk page)
```

R trade lists are saved (e.g. as CSV/Parquet in `results/`) so `risk/` can be rerun with
different settings, or fed the manual R log, without repeating detection.

## Build order

Each step ends with green tests and a commit.

1. Test helpers (`make_candles` fixture) and tests for the existing core
2. ATR + strong-move filter
3. Swing high/low detector
4. Trend + BOS
5. Zone validation state machine (tap / confirmed / invalidated), shared by all zones
6. FVG, then order block, then breaker, then BPR
7. Session clock (DST-aware) and session zones on 30m
8. Engine loop with multi-timeframe stepping and trade management in R
9. Strategy 1 entry sequence, SL, TP with obstacles
10. Chart page: candles, session lines, zones, confluences, position boxes
11. Analytics, then `risk/` and the Risk & Prop Firm page
12. Data adapter for a real data source; later MT5 / live trading
