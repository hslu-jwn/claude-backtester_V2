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
9. **ui/**: Dash app with a TradingView Lightweight Charts chart in the browser. Reads
   results; never contains trading logic. See "How the chart gets its data" below.

## How a backtest steps through time

```
for each base-timeframe candle i (5m for strategy 1), oldest first:
    now   = close time of candle i
    v5    = series_5m.view(i)
    v30   = clock_30m.view_at(now)     # only fully closed 30m candles
    v1h   = clock_1h.view_at(now)
    1. update open trades with candle i (SL first if SL and TP share a candle)
    2. break-even check for trades whose next session start is now reached
    3. strategy.on_candle(now, {M5: v5, M30: v30, H1: v1h}) -> new orders
       (the strategy updates its own detectors for each timeframe whose newest
       candle just closed)
    4. engine fills orders at candle i's close (spec: "enter at that close")
```

`engine/backtest.py` (`run_backtest`) implements this loop on top of `Replay`; trades are
`engine/trade.py` (`TradeResult`: gross and net R), costs `engine/costs.py` (`CostConfig`).

`engine/replay.py` (`Replay`) gives the views for a cursor (`v5` and, via the clocks, `v30`/`v1h`).
The chart replay (ROADMAP 1.2) draws from it, so it shows exactly what the engine sees.

A higher-timeframe detector is updated only when a new candle of that timeframe has
closed, so it is called exactly once per candle, as on its own chart.

## How the chart gets its data

The chart page (ROADMAP 4.0a) draws with TradingView Lightweight Charts in the browser
(`ui/assets/chart.js`, the chart object is created once). The server never builds a
figure; it sends data, always cut at a **cursor** (the last candle, or the replay cursor),
so the browser never receives anything that isn't known at that candle (Invariant #1):

```
cache -> Replay (candles of the range + 30m / overall clocks)
      -> detectors / strategy per overlay, once per range and setting (events, cached)
      -> overlay draw(events confirmed by the cursor) -> drawing objects (ui/drawing.py)
      -> ui/chart_data.py -> JSON stores -> chart.js
```

- `chart-base`: candles 0..cursor as columns (UTC seconds, OHLC, spread) and session lines.
- `chart-ovl`: the drawings of the overlay types the browser asked for (`chart-need`),
  with every sub-entry; the browser shows / hides types and sub-entries itself.
- `chart-delta` (replay): from the browser's cursor (`chart-view`) to the next one: new
  candles (or how many to drop), drawings added / removed (ids = hash of the JSON), badges.
  A drawing that runs to the cursor is sent "live" (end = the latest candle), so a step only
  sends what changed. Per step the server draws again only the groups of events
  (`OverlayType.group`, e.g. a zone with its transitions) that got an event on the new
  candle or were live.

## Data flow

```
DataAdapter -> CandleSeries -> engine loop -> detectors -> strategy -> trades (R)
                                                                        |
                         analytics (win rate, expectancy, DD in R) <----+
                         risk (sizing, FTMO sim, Monte Carlo, sweep) <--+
                         ui (Lightweight Charts chart with zones + position boxes,
                             results page, risk page)
```

R trade lists are saved (e.g. as CSV/Parquet in `results/`) so `risk/` can be rerun with
different settings, or fed the manual R log, without repeating detection.

## Data sources

Every source has its own cache folder (`data/cache/dukascopy/`, `data/cache/histdata/`,
same layout and columns). `data/sources.py` (`SymbolSources`) maps each symbol to the
folder it is read from; the app, `data.check` and `data.show` all use it, so all symbols
show in one app. Current mapping: XAUUSD, GBPUSD and GBPJPY → histdata.com (Dukascopy downloads paused).
`--cache-dir` on `data.check` / `data.show` overrides it for a single run.

### Dukascopy (backtest history)

- Free historical data, M1 candles and ticks, many years back, timestamps in **UTC**,
  separate **bid** and **ask**.
- Raw files are LZMA-compressed binary (`.bi5`). URL paths use **zero-based months**
  (January = `00`). Prices are stored as integers and must be divided by a per-symbol
  point factor (e.g. JPY pairs and gold differ from other FX pairs). Field order in candle
  files may not be OHLC. **Verify factor and field order against a known candle**, never
  assume. A maintained library (Python, or the `dukascopy-node` CLI) may be used instead
  of a hand-written parser if it is simpler; ask the user if it adds a Node dependency.
- Daily M1 files contain **every minute of the day, weekends included**. Minutes without
  trading are filled with flat candles (O = H = L = C, volume 0): gold's daily break
  (21:00–21:59 UTC in summer), the weekend (Fri 21:00 → Sun 22:00 UTC in summer, so
  Saturday is entirely flat) and holidays. Missing or empty files can still occur. The cache keeps them raw. **When resampling, these flat zero-volume minutes
  are dropped, so the charts and backtests show the break as a gap, like TradingView.**
  A higher-timeframe candle with no remaining minutes does not exist.
- Resample M1 → 5m/30m/1h ourselves so every timeframe comes from the same data.
  Candles are bucketed by UTC-floored open time and built from **bid** prices. A partly
  filled bucket (e.g. the hour the break starts) keeps its regular open and close time.
  Each candle's `spread` is the **mean of the per-minute close spreads** (ask − bid) over
  its remaining minutes. D1 is not built (a UTC day is not the trading day).
- `CacheAdapter` (`data/adapters/cache_adapter.py`) raises an error for any requested day
  that was never downloaded, so gaps in the cache are never silent. A day Dukascopy had no
  data for is cached as empty and simply has no candles.
- The server answers **HTTP 503** when it is busy or throttling; the downloader retries with
  a growing wait, and a rerun picks up any day that still failed. After 3 days in a row
  fail with 503s / timeouts (`DukascopyConfig.max_unavailable_days_in_row`), the whole run
  stops and suggests a larger `--delay` (default 2 s per request). **HTTP 429** means the IP
  is blocked: the run stops at once.
- It is Dukascopy's feed, not FTMO's: small price differences are expected (see 0.4).

### histdata.com (XAUUSD, GBPUSD, GBPJPY while Dukascopy downloads are paused)

- Monthly M1 files in MetaTrader format, `DAT_MT_{SYMBOL}_M1_{YYYYMM}.csv`, put in
  `data/raw/histdata/` by hand. Imported with `python -m backtester.data.histdata data/raw/histdata/`
  into `data/cache/histdata/` (same layout and columns as the Dukascopy cache, own folder
  so the sources never mix). `data/sources.py` reads all three symbols from there.
  XAUUSD histdata was compared with the Dukascopy cache on 2026-09-02..07: every M1
  candle identical (same minutes, OHLC within 0.001), so the switch changes nothing for
  those days. Differences to Dukascopy: no ask prices (spread unknown, NaN), and the
  September 2026 files have **no rows for Friday 2026-09-25** (all three pairs).
- Timestamps: **New York local time with daylight saving** (`America/New_York`: UTC−4 in
  summer, UTC−5 in winter), converted to UTC on import.
  **This contradicts HistData's FAQ**, which says the files are "EST without daylight
  saving" (fixed UTC−5). Read as fixed UTC−5, the September 2026 files put the weekend at
  Fri 22:00 → Sun 22:00 UTC and the rollover at 22:00 UTC, one hour after the 17:00 New York
  close. Two GBPUSD M5 candles were compared with TradingView (chart in UTC):

  | Candle (UTC) | histdata read as New York time (UTC−4) | Read as fixed UTC−5 | TradingView |
  |---|---|---|---|
  | 2026-09-30 07:00 | O 1.32544 · H 1.32626 · L 1.32527 · C 1.32583 | O 1.32447 · H 1.32583 · L 1.32439 · C 1.32566 | matches New York time on all four values |
  | 2026-09-30 13:30 | O 1.32924 · H 1.32949 · L 1.32913 · C 1.32926 | O 1.3288 · H 1.33109 · L 1.32869 · C 1.3303 | O ≈ 1.3292 · H 1.3295 · L 1.3291 · C 1.3293: matches New York time |

  Both candles and the gap positions (below) decide it for New York time.

  After the switch, the data check finds the weekends at Fri 17:00 → Sun 17:00 New York
  and GBPJPY's daily breaks at the 17:00 close. US clocks change on a Sunday at 02:00, when
  FX is closed: a minute in the skipped or repeated local hour stops the import.
  Re-check a winter month against TradingView when one is imported.
- Bid only (ask columns empty, candle `spread` NaN). Volume is always 0 in the files and is
  stored as NaN (unknown). Non-trading minutes are **missing**, not flat filler, so the
  flat-zero-volume filter never drops a histdata minute.
- Only UTC days fully inside the imported months are cached (a month runs from New York
  midnight of the 1st: 04:00 UTC in summer, 05:00 UTC in winter). Minutes that appear twice (a feed glitch: single-tick rows written
  out of order) are merged in file order: first open, max high, min low, last close.

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
