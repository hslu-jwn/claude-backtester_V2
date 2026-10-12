# Architecture

## Layers

Each layer only imports from the layers above it in this list.

1. **core/**: value types (`Candle`, `Timeframe`, `Direction`), `CandleSeries` (engine-private
   full history), `SeriesView` (lookahead-safe window), `HigherTimeframeClock`.
2. **data/**: `DataAdapter` interface. histdata.com M1 files (downloaded by the user) are
   imported into a local cache and resampled; backtests and the chart read the cache
   (`CacheAdapter`). The Dukascopy downloader is kept but no longer used.
   `Mt5Adapter` for comparing with FTMO's feed and for live trading. Returns closed candles
   in UTC, oldest first.
3. **detectors/**: incremental, timeframe-agnostic pattern detectors. Input: a `SeriesView`.
   Output: events stamped with their confirming candle. Spec: `confluences.md`.
4. **sessions.py**: maps UTC timestamps to Tokyo / London / New York sessions (DST-aware).
5. **strategy/**: combines detectors across timeframes into setups and trade signals in price
   terms (entry, SL, TP). Strategy 1: `session_zone_sweep/` (spec `strategy-session-zones.md`,
   base 5m). Strategy 2: `ny_index_sweep/` (spec `strategy-ny-indices.md`, base 1m, 5m / 15m /
   1h / New York-aligned 4h, AM / PM windows).
6. **engine/**: the backtest loop. Owns the `CandleSeries`, steps time, hands out views,
   opens and closes trades, and records each closed trade with its result in **R**.
7. **analytics/**: statistics on R trade lists.
8. **risk/**: turns an R trade list into account equity under prop-firm rules; Monte Carlo
   and parameter sweeps. Spec: `risk-management.md`.
9. **live/**: platform connection (MT5), the login in the Windows Credential Manager,
   trading settings, demo-locked order functions (Phase 7). Only the MT5 command-line
   tools in `data/` (`mt5_info`, `feed_compare`) read its settings and connect through it.
10. **ui/**: Dash app with a TradingView Lightweight Charts chart in the browser. Reads
   results; never contains trading logic. See "How the chart gets its data" below.

## How a backtest steps through time

```
for each base-timeframe candle i (5m for strategy 1, 1m for strategy 2), oldest first:
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
An order closes in up to three parts (`take_profit`, `take_profit_2`, `take_profit_3` with
`tp1_share` / `tp2_share`; strategy 1 uses two, strategy 2 three), break-even after TP1 if
asked. When a trade has closed, the engine calls `strategy.on_trade_closed(order.ref,
result)` before the next `on_candle` (strategy 2: one open trade per setup, re-entries).
The break-even at the next session start (step 2) is strategy 1's rule: a strategy with
`uses_session_break_even = False` (strategy 2) skips it.

`runner.py` picks the strategy from its config (`make_strategy`: a `NyIndexSweepConfig`
runs strategy 2) and loads every declared timeframe from the cache: the base and lower
timeframes from the warm-up start, the strategy's `full_history` timeframes (strategy 2:
15m, 1h, 4h, for untouched highs and never-tapped zones as TP levels) from the first cached
day, 4h in the strategy's `h4_alignment` (strategy 2: New York, `data/resample.py`
`H4Alignment`; these candles cross UTC midnight and are read like D / W candles).

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
show in one app. **Decision (user, 2026-10-10): all history comes from histdata.com**;
Dukascopy is no longer used (it didn't work for the user) and is no longer the default
anywhere. Its code and cache folder are kept for now. Current mapping: XAUUSD, GBPUSD,
GBPJPY, NAS100, US500 → histdata.com (`DEFAULT_SOURCES`; price decimals per symbol in
`PRICE_DIGITS`).
`--cache-dir` on `data.check` / `data.show` overrides it for a single run.

### Dukascopy (not used since 2026-10-10; code kept)

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

### histdata.com (backtest history, every symbol)

- M1 files in MetaTrader format, per month (`DAT_MT_{SYMBOL}_M1_{YYYYMM}.csv`, the
  current year) or per year (`DAT_MT_{SYMBOL}_M1_{YYYY}.csv`, full past years), plain or
  inside histdata's zip files, put in `data/raw/histdata/<SYMBOL>/` by hand, one subfolder
  per pair (files directly in `data/raw/histdata/` work too; the same period twice is
  refused). History 2020-01 .. 2026-09 since 2026-10-09 (indices 2018-01 .. 2026-09). Imported with
  `python -m backtester.data.histdata data/raw/histdata/` (searches the subfolders; a
  single file, zip or pair folder works too) into `data/cache/histdata/` (same layout and
  columns as the Dukascopy cache, own folder so the sources never mix). `data/sources.py`
  reads every symbol from there.
- **Symbol names:** histdata's index names are cached under ours (`histdata.SYMBOL_NAMES`):
  `NSXUSD` → **NAS100**, `SPXUSD` → **US500**. Forex and gold keep their names. histdata
  offers both indices from 2010 (year files 2010-2025, month files for 2026).
  XAUUSD histdata was compared with the Dukascopy cache on 2026-09-02..07: every M1
  candle identical (same minutes, OHLC within 0.001), so the switch changes nothing for
  those days. Differences to Dukascopy: no ask prices (spread unknown, NaN), and the
  September 2026 files have **no rows for Friday 2026-09-25** (all three pairs).
- Timestamps: **New York standard time (UTC−5), one hour later (UTC−4) while Europe is on
  summer time**, converted to UTC on import (`histdata_to_utc`). Outside the weeks where
  only the US is on summer time this equals New York time with daylight saving, which the
  first check below found; the user's TradingView check of 2026-03-18 14:00 UTC (XAUUSD
  5m, a US-only summer time week) showed the clock follows the **European** dates (see
  ROADMAP 0.3).
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
  and GBPJPY's daily breaks at the 17:00 close. Europe changes at 01:00 UTC on a Sunday,
  when FX is closed: a minute in the skipped or repeated hour stops the import. histdata's
  files skip the hour 23:00 UTC on the March Sunday and repeat (an exact copy) 00:00 UTC on
  the October one; checked against TradingView, the conversion is right (ROADMAP 0.3).
- **Indices (NAS100, US500) use the same clock** (checked 2026-10-10 on the files): their
  daily break starts at 16:15 on histdata's clock and moves to 15:15 in exactly the weeks
  where only the US is on summer time, like gold's 17:00 close moves to 16:00. Converted,
  the break is at **16:15-18:00 New York** in every week (105 min), the weekend **Fri
  16:15 → Sun 18:00 New York**, US holidays close early at 13:00 / 13:15 New York.
  Confirmed by the user's TradingView check of US500 (2026-10-11, ROADMAP 0.5; that feed
  is a few points higher, timing identical). The data check's gap rules for them:
  `check.SYMBOL_CONFIGS` (break up to 120 min, weekend up to 51 h for the US DST-change
  weekend; until 2018-12-14 the old CME hours, halt 16:15-16:30 and break 17:00-18:00
  New York; confirmed by the user).
- Bid only (ask columns empty, candle `spread` NaN): costs use a **fixed spread per
  symbol** (`engine/costs.py`, risk-management.md › Costs). Volume is always 0 in the files and is
  stored as NaN (unknown). Non-trading minutes are **missing**, not flat filler, so the
  flat-zero-volume filter never drops a histdata minute.
- Only UTC days fully inside the imported months are cached (a month runs from midnight of
  the 1st on histdata's clock: 04:00 UTC in European summer time, 05:00 UTC otherwise). Minutes that appear twice (a feed glitch: single-tick rows written
  out of order) are merged in file order: first open, max high, min low, last close.

### MetaTrader 5 (FTMO feed, live trading)

FTMO's server keeps only about one month of 5m history, so MT5 is used for the feed
comparison (ROADMAP 0.4) and for order execution (Phase 7, `live/`).

- The `MetaTrader5` Python package only works on **Windows**, with the MT5 terminal
  installed and running. It is the optional extra `[mt5]` (with `keyring`). It is imported
  only by `data/adapters/mt5_adapter.py` (`load_mt5`); every other module gets the module
  passed in, so the tests, backtests and the chart run without it
  (`test_nothing_else_imports_metatrader5`). Tests use a fake module (`tests/live/fake_mt5.py`).
- **Login:** entered only in the app (Settings ⚙ → Trading → Account connection…) and kept in
  the Windows Credential Manager (`live/credentials.py`, `keyring`, service
  `backtester.trading`). Never in the repo, `.env`, results/, logs, error messages or test
  output: `Credentials` prints as `<hidden>`, MT5 error texts are scrubbed
  (`connection.scrub`), the password is never sent back to the browser. Without a saved
  login the tools attach to the account the running terminal is logged in to.
  Non-secret settings (platform, terminal path, symbol names, server clock) are in
  `results/trading.json` (`live/trading_settings.py`).
- `live/connection.py` `session()` connects, yields the module and always shuts down; one
  lock serializes sessions (the module is process-wide, Dash callbacks run in threads).
  The server dropdown suggests the folders in the terminal's `bases/` (servers it has
  connected to).

**Candles (`Mt5Adapter`, a `DataAdapter`)**

- Bar time = candle **open** time in the broker's **server time**, written as if it were
  UTC. `ServerClock(zone, shift_hours)`: server time = local time in an IANA zone + a
  whole-hour shift (`UTC` + 2: fixed; `America/New_York` + 7: UTC+2 / +3 on the US dates;
  `Europe/London` + 2: UTC+2 / +3 on the European dates). The adapter converts bar times
  with it and asks the terminal for a UTC range in server time (padded by a day).
  Without a measured clock the adapter refuses to start.
- Only **closed** candles: a bar whose UTC close time is after now is dropped.
- Served timeframes: M1, M5, M15, M30, H1 (H4 / D1 bars are cut on the server's day).
- `spread` per candle = MT5's bar spread (points) x the symbol's point, in price units.
  MT5 doesn't document whether it is the bar's lowest, average or last spread.
- **History depth** is the broker's and the terminal's "Max bars in chart";
  `history()` returns everything the terminal has, the reports print the first candle.
- Symbol names can differ by broker (suffixes like `.r`): `TradingSettings.symbols` maps
  ours to the server's.

**Server time → UTC: how the rule is found** (`python -m backtester.data.mt5_info`)

1. Per week of MT5's **H1 history** (server weeks), the whole-hour offset −12..+14 h whose
   shifted bar times meet the histdata cache's H1 candles with the smallest median
   |close difference| (at least half the bars matched; `mt5_compare.weekly_offsets`).
   Also printed: that error as a share of the candle range and how much worse the next
   best offset is (how clear the match is).
2. Every rule (zones `UTC`, `America/New_York`, `Europe/London` x shifts −14..+14 h) is
   scored by the number of weeks it predicts (offset at Wednesday 12:00 UTC);
   `fit_clock`. The weeks where only the US or only Europe is on summer time (2nd Sunday
   of March to the last Sunday of March; last Sunday of October to the 1st Sunday of
   November) decide between US and European dates; they are printed one by one.
3. The rule is saved only if it predicts **every** week and no other rule does.
4. Live check: the newest tick's server time − real UTC must be the rule's offset with a
   tick at most 5 minutes old (only while the market trades).

**Rule found for the FTMO server: not measured yet** (the terminal wasn't logged in on
2026-10-09). It is written here after the first run of `data.mt5_info`.

**Feed comparison** (`python -m backtester.data.feed_compare`, ROADMAP 0.4): per symbol
and timeframe (M1, M5, M30, H1), over the days both MT5's history and the cache have:
best time shift (multiples of the timeframe within ±3 h; 0 when the clock is right),
average |difference| of O/H/L/C (price and % of the median candle range), how often the
color differs / is opposite, candles only one side has. FTMO's spread per UTC hour
(median, 90%) from M1 (else M5) next to the cost defaults. Report in
`results/feed_compare/<time>/`.

**Orders** (`live/orders.py`, ROADMAP 7.1)

- **DEMO LOCK:** every order function checks `account_info().trade_mode` first and raises
  `DemoLockError` (nothing sent) unless it is `ACCOUNT_TRADE_MODE_DEMO`. No override yet.
- Orders carry the magic number `MAGIC`; cleanup only ever closes those, never the user's
  own positions.
- Filling mode: the symbol's allowed ones (FOK, IOC), then RETURN; a request rejected with
  10030 is sent again with the next. Every request and result is logged (`OrderLog`,
  JSON lines, execution time in ms).
- `python -m backtester.live.test_orders XAUUSD` / the button in Trading: the scripted
  test (open 2 x min lot with SL / TP, SL to break-even, close half, close rest; buy and
  sell), log in `results/live/test_orders/`.

## Build order

See `docs/ROADMAP.md`. Phases: 0 historical data (histdata.com) → 1 chart with replay → 2 confluences on the
chart → 3 strategy 1 + backtest → 4 settings menu → 5 risk & FTMO simulation →
6 robustness → 7 live trading via MT5 → 8 strategy 2 (NY Open index sweep).
