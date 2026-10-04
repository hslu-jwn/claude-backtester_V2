# Architecture

## Layers

Each layer only imports from the layers above it in this list.

1. **core/**: value types (`Candle`, `Timeframe`, `Direction`), `CandleSeries` (engine-private
   full history), `SeriesView` (lookahead-safe window), `HigherTimeframeClock`.
2. **data/**: `DataAdapter` interface. Dukascopy M1 history is downloaded into a local
   cache and resampled; backtests and the chart read the cache (`CacheAdapter`).
   `Mt5Adapter` for comparing with FTMO's feed and for live trading. Returns closed candles
   in UTC, oldest first.
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

## Data sources

### Dukascopy (backtest history)

- Free historical data, M1 candles and ticks, many years back, timestamps in **UTC**,
  separate **bid** and **ask**.
- Raw files are LZMA-compressed binary (`.bi5`). URL paths use **zero-based months**
  (January = `00`). Prices are stored as integers and must be divided by a per-symbol
  point factor (e.g. JPY pairs and gold differ from other FX pairs). Field order in candle
  files may not be OHLC. **Verify factor and field order against a known candle**, never
  assume. A maintained library (Python, or the `dukascopy-node` CLI) may be used instead
  of a hand-written parser if it is simpler; ask the user if it adds a Node dependency.
- Empty files for weekends and holidays are normal.
- Resample M1 → 5m/30m/1h ourselves so every timeframe comes from the same data.
- It is Dukascopy's feed, not FTMO's: small price differences are expected (see 0.4).

### MetaTrader 5 (FTMO feed, live trading)

FTMO's server keeps only about one month of 5m history, so MT5 is used for the feed
comparison (0.4) and for order execution (Phase 7).

- The `MetaTrader5` Python package only works on **Windows**, with the MT5 terminal
  installed, running and logged in. Import it only inside `data/adapters/mt5_adapter.py`
  (and later `execution/`), so everything else, including the tests, runs without it.
  Tests use a fake module.
- **Server time is not UTC.** Bar times from MT5 are in the broker's server time (many
  brokers use UTC+2 in winter / UTC+3 in summer, switching with US DST; verify for the
  user's FTMO server, don't assume). The adapter converts to UTC with a configurable
  server time zone, and Phase 0.3 checks it against a known candle.
- Bar time = candle **open** time (same as `Candle.ts`).
- The newest bar MT5 returns may still be **forming**. The adapter drops any bar whose
  close time is after "now". This matters most for live trading.
- **History depth** is limited by the broker's server and the terminal's "Max bars in chart"
  setting. Report the first available candle instead of failing silently.
- Symbol names can differ by broker (suffixes like `.r`); keep a mapping in config.
- Rates include a per-bar `spread` (in points). Store it in the cache; the engine can use it
  as an approximate cost.
- Never put login, password or server in code or git: read them from `.env` (git-ignored).

## Build order

See `docs/ROADMAP.md`. Phases: 0 historical data (Dukascopy) → 1 chart with replay → 2 confluences on the
chart → 3 strategy 1 + backtest → 4 settings menu → 5 risk & FTMO simulation →
6 robustness → 7 live trading via MT5.
