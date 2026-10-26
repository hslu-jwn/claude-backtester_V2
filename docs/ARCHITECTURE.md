# Architecture

## Layers

Each layer only imports from the layers above it in this list (`tests/test_layers.py` checks it
on the imports; `paths.py` and `cli.py` are util modules that import nothing). Outside the
layers is the app level: `runner.py`, `run.py`, `presets.py`, `settings.py`, `ui/` and the
command-line tools in `tools/` (data check / show, MT5 info, feed comparison). They may import
any layer; no layer imports them. A strategy names `engine.trade.TradeResult` only as a type
hint (`TYPE_CHECKING`).

1. **core/**: value types (`Candle`, `Timeframe`, `Direction`), `CandleSeries` (engine-private
   full history), `SeriesView` (lookahead-safe window), `HigherTimeframeClock`.
2. **data/**: `DataAdapter` interface. histdata.com M1 files (downloaded by the user) are
   imported into a local cache and resampled; backtests and the chart read the cache
   (`CacheAdapter`, parquet reader and writer helpers in `data/cache.py`).
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
   tools in `tools/` (`mt5_info`, `feed_compare`) read its settings and connect through it.
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

### Intrabar resolution (V2.4c T-03, user 2026-10-23)

`EngineConfig.intrabar = "m1"` is the default (rule set by the user 2026-10-24 after the measurement in
`results/intrabar.md`); `"sl_first"` preserves the earlier execution exactly. Without an
`intrabar_source` (direct engine calls) an ambiguous candle falls back to SL first and is counted.
The optional `"m1"` setting resolves only ambiguous base candles after they have closed:
the current stop and an outstanding TP both reached, or TP1 reached with break-even
after TP1 enabled and its eligible BE level reached, or a limit-fill candle reaching
an outstanding TP. TP reach uses the entry-fixed spread, `tp_penetration` and
`short_tp_on_ask`, including for partial targets. A 1m base never requests intrabar data.

The engine receives an optional `intrabar_source(symbol, start, end)` callable. The
runner supplies it from that symbol's adapter with a bounded UTC-day cache; it never
loads the entire M1 history. Only M1 candles wholly inside `[base.ts, base.close)` may
be replayed, oldest first, at that base close. Strategies still run once per base close;
callbacks and orders cannot act earlier. Missing minutes (including partial coverage,
duplicates or unordered timestamps) cause whole-candle fallback before any mutation.
No source also falls back. No candle outside the closed interval is replayed.

Replay uses the existing stop/TP levels, costs and partial shares. Stops gap to the M1
open, TPs fill at their levels. SL wins if stop and TP share one M1 candle. After TP1,
an eligible break-even stop applies from M1 candle k+1; never infer a same-M1 BE exit
from candle k's close. In the M1 candle that fills a pending limit only SL counts;
TPs count from the next M1 candle (both clarifications confirmed by Opus). Before
the limit fills, extremes and TP hits do not count. Entry penetration uses the placed
limit and the candidate trade's fixed spread. Default mode keeps today's close-based
same-base-candle BE rule and ignores all TPs on the base limit-fill candle.

A replayed limit's `entry_time` is the close of the M1 candle that fills it, so no exit
can precede entry (Opus clarification, 2026-10-23 21:02). `entry_candle` remains the base
candle's open time. The order decision and all strategy callbacks stay at the base
candle's close; recording the M1 entry time does not advance strategy execution.

An exit's time/candle are the resolving M1 candle's close/open. Excursions use only
replayed minutes while exposed, with the existing open-gap excursion rule. Other
candles retain base OHLC execution. Per-run summary counters `intrabar_ambiguous`,
`intrabar_tp_first`, `intrabar_sl_first`, `intrabar_fallbacks` count trade/candle
assessments (two positions on one candle count twice), excluding warm-up entries.
Ambiguity is counted in both modes; resolution/fallback counts apply only in M1 mode.
First exit during a replay determines TP-first/SL-first (BE counts as a stop). A limit
replay with no exit increments only ambiguity. The trade CSV `intrabar` is empty
without a resolution, otherwise `tp_first`, `sl_first`, or `fallback`; fallback takes
precedence across repeated assessments, otherwise the first resolution is retained.
`scripts/measure_intrabar.py` compares both modes on all seven 2023 golden setups,
checkpoints `results/intrabar.csv` and `.md`, and does not change the default.

### Engine costs (rule set by the user, 2026-10-22)

- Slippage is always applied, there is no switch to turn it off (most realistic scenario);
  its per-symbol values are to be measured from the demo bot's fills (rule set by the user,
  2026-10-23; ROADMAP V2.4b).

- **B4:** `SymbolCosts.slippage` worsens each market entry, stop fill (including a gap
  stop), and time / signal / end-of-data exit. Limit entries and TP fills have no
  slippage. Scale the configured slippage by the chart entry / reference price under
  `CostConfig.spread_price_scaling`, independently of the spread switch and spread table;
  keep that entry-scaled amount for the trade's exits, like the fixed spread. An unset
  reference price or disabled scaling uses the configured amount. Gross R and order
  levels remain chart prices; net R uses the adverse fills and costs. Kind C random fills
  also draws extra slippage for time / signal / end-of-data exit parts. Trade results and
  CSV records preserve `limit_fill` so Kind C skips limit-entry draws; older records
  without that field retain the market-entry assumption.
- **B5:** after TP1, move the remaining stop to break-even only if that level lies
  strictly behind TP1 (long: BE < TP1; short: BE > TP1). At equality or beyond TP1,
  keep the original SL; never manufacture an exit at an unreachable BE level.
- **B6:** percentage entry commission uses the actual entry fill, including spread and
  entry slippage. Percentage exit commission uses each part's exit fill. Solve the
  break-even stop so the remaining portion alone nets zero after spread, entry/stop
  slippage, and fixed plus percentage commission. With direction `s` (+1 long, -1 short),
  entry fill `E`, round-turn fixed commission in price units `F`, and per-side rate `p`,
  the exit fill `X` solves `s * (X - E) = F + p * (E + X)`. Convert that fill back to the
  chart stop by removing short-side spread and reversing adverse stop slippage. Prior
  TP profits do not subsidise the remaining portion. Swap/funding are excluded from the
  BE level; a gap through that stop may still produce a loss.

### Engine excursions (rule set by the user, 2026-10-22)

**B7:** an exit at the candle open counts MAE/MFE only through that open, retaining
excursions from earlier candles. Ignore the exit candle's later high/low. This includes
stop gaps and a final TP reached at the open (the TP still fills at its planned limit).
A partial TP leaves exposure, so continue tracking that candle for the remaining
portion. SL-first still applies whenever SL and TP share a candle; all decisions use
only the current closed candle and previously known order levels.

`runner.py` picks the strategy from its config (`strategy/registry.py`: `make_strategy` looks
the config class up in the registry, `StrategySpec` per strategy; a new strategy is one folder,
started from `strategy/_template/`, plus one registry entry). `RunSettings` holds the shared
detector settings (`detectors`: swings, FVG, order block, equilibrium), the engine and the
warm-up; a strategy config holds only that strategy's own settings. The runner loads every declared timeframe from the cache: the base and lower
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

Every source has its own cache folder (`data/cache/histdata/`, same layout and columns,
`data/cache.py`). `data/sources.py` (`SymbolSources`) maps each symbol to the folder it is
read from; the app, `tools.check` and `tools.show` all use it, so all symbols show in one app.
**Decision (user, 2026-10-10): all history comes from histdata.com.** Dukascopy didn't work
for the user and its downloader was removed (ROADMAP C.1, 2026-10-12). Current mapping:
XAUUSD, GBPUSD, GBPJPY, NAS100, US500 → histdata.com (`DEFAULT_SOURCES`; price decimals per
symbol in `PRICE_DIGITS`).
`--cache-dir` on `tools.check` / `tools.show` overrides it for a single run.

**MT5 preferred, day by day (rule set by the user, 2026-10-19):** "We always prefer MT5 if we
have it, but it doesn't go far enough into the past." For every histdata symbol
`SymbolSources` has a preferred folder (`data/cache/mt5/`): a UTC day that exists in the MT5
cache is read from MT5, a day only in the histdata cache from histdata (`PreferredCacheAdapter`;
`cached_days` is the union). It applies to backtests, tools and the chart alike (the chart-only
fill after the last histdata day was removed). Binance and MT5-only symbols are unchanged.
MT5 index prices differ slightly from histdata's, so a small jump at the seam between the two
feeds is expected (the chart marks the first MT5 day after the last histdata-only day).
Research tools that name `MT5_CACHE_DIR` / `DEFAULT_CACHE_DIR` explicitly keep that one feed.

### histdata.com (backtest history, every symbol)

- **V2.6b clock periods (offline audit, 2026-10-26):**

  | Local file dates | Clock rule | Evidence / action |
  |---|---|---|
  | 2015-01-01 through 2018-12-31 | `America/New_York` including US DST | Every sampled US/EU gap-week GBPUSD Sunday open and Friday close is 18:00 NY under the old conversion; the US rule restores 17:00. Gold closes corroborate it. |
  | 2019 onward | NY standard time plus `Europe/London` DST | 2019 gap-week FX opens/closes are already 17:00 NY; 2020/2021 checks agree. Existing later-year conversion retained. |
  | Before 2015 | Existing European-date rule retained, unverified here | No histdata cache/reference available in this audit; no new clock rule inferred. |

  `histdata_to_utc` uses `zoneinfo` for these periods and rejects ambiguous/nonexistent
  wall-clock minutes. Measurements precede implementation: `results/clock_check_histdata.md`,
  dated edges and price matches in `results/v26b_clock_*.csv`; reproduce with
  `python scripts/v26b_clock_evidence.py` against the original caches. Its two measurement
  passes are bounded to 540 seconds each (observed approximately 2 and 6 seconds).
  The European-clock description below applies from 2019, not to 2015–2018.
- **V2.6b import validation:** `ImportConfig.max_day_close_jump` defaults to 0.25.
  An unexplained daily-close jump above it stops that symbol before writes and names
  the file/date; weekends alone do not explain an instrument substitution. Documented
  exemptions are explicit `(symbol, UTC date, reason)` entries in `explained_jumps`.
  GER40/GRXEUR is excluded from **UTC 2020-06-15 onward**, including existing cached
  days, because it becomes Euro Stoxx rather than DAX. Raw files are retained.
  Import all adjacent yearly/monthly periods together to complete the UTC January 1
  day from both files; `scripts/rebuild_cache_v26b.md` supplies one queue job per symbol.

- M1 files in MetaTrader format, per month (`DAT_MT_{SYMBOL}_M1_{YYYYMM}.csv`, the
  current year) or per year (`DAT_MT_{SYMBOL}_M1_{YYYY}.csv`, full past years), plain or
  inside histdata's zip files, put in `data/raw/histdata/<SYMBOL>/` by hand, one subfolder
  per pair (files directly in `data/raw/histdata/` work too; the same period twice is
  refused). History 2020-01 .. 2026-09 since 2026-10-09 (indices 2018-01 .. 2026-09). Imported with
  `python -m backtester.data.histdata data/raw/histdata/` (searches the subfolders; a
  single file, zip or pair folder works too) into `data/cache/histdata/` (same layout and
  columns, own folder). `data/sources.py`
  reads every symbol from there.
- **Symbol names:** histdata's index names are cached under ours (`histdata.SYMBOL_NAMES`):
  `NSXUSD` → **NAS100**, `SPXUSD` → **US500**. Forex and gold keep their names. histdata
  offers both indices from 2010 (year files 2010-2025, month files for 2026).
  XAUUSD histdata was compared with the (since removed) Dukascopy cache on 2026-09-02..07: every M1
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

- **V2.6b historical cache repair (addendum A-C):** one FTMO server clock applies to
  every symbol. `data/cache_repair.py` builds one per-date server clock table from the
  start of the cache through **2021-09-13 inclusive**. Reference symbols with corrected
  histdata prove residual shifts against the original NY+7-converted cache, using M1
  close errors for candidates −1, 0, +1 hours. Every decisive reference must agree.
  That date's residual then applies to every MT5 symbol, including MT5-only symbols.
  Disagreement marks a date ambiguous (all symbol readings are retained); no decisive
  reference marks it unproven. Both exclude the date for all symbols, without averaging.
  From **2021-09-14**, retain the plain `America/New_York + 7 h` conversion unchanged.
  `QualityConfig` requires at least 100 matched bars and 50% coverage, a best median
  error at most 50% of reference median M1 range, and runner-up error at least twice the
  best plus 25% of that range. Flat/short/ambiguous references cannot prove a clock.
  Only proved days survive; bars are regrouped across UTC midnight after correction.
  Pre-2015 dates without reference evidence are excluded. A sparse reference cannot prove
  a date. Empty development days also require a proven server date; there is no invented
  Friday offset for 2010–2014. Missing MT5 days fall back to histdata where available.
  Per-symbol/year weekday bar counts strictly below
  `QualityConfig.min_weekday_share` (0.5) times the median weekday count, and empty
  weekdays, are missing; this density check applies in all years. Removing active day
  files makes `PreferredCacheAdapter` fall back to histdata; MT5 remains preferred on
  every retained day. Direct MT5-only requests report missing data when no replacement exists.
  Run `tools.cache_repair --prove-clock --clock-table PATH` **after** corrected histdata
  is rebuilt, then `tools.cache_repair SYMBOL --clock-table PATH` for each symbol.
  The frozen JSON table records per-date status, residual hours and all decisive readings,
  together with the quality settings. Reuse it for all symbols; do not measure repaired data.
  It locks per symbol with `filelock.py`, retains affected original files under
  `_v26b_original/`, stages measurements before active writes, and writes each day's
  proof/exclusion to `_v26b_reports/SYMBOL.json`. Reruns always start from originals.
  See `results/clock_check_mt5.md` for per-year proven/ambiguous/no-reference dates,
  per-symbol/year kept/dropped counts, disagreeing readings and test-period samples.
  `scripts/v26b2_clock_evidence.py` reproduces the bounded read-only original-cache audit;
  it corrects the proven old histdata DST-gap conversion in memory only. Its evidence
  table is separate from the post-histdata-rebuild table used by the repair jobs.
  The 2023 golden check is run by Opus after rebuild, never regenerated to accept a change.
- **Downloader errors:** only `Mt5NoHistory` (`RES_E_NOT_FOUND` after symbol validation)
  may be skipped before the first dense history day. Other first-chunk errors fail the
  command. `--end` must be before today UTC. Binance daily 404 holes are retried once;
  a second 404 is reported missing and remains eligible next run.
- **Offline checks and output:** `tools.check` reads one M1 year at a time through the
  preferred sources, carries cross-year gaps, and computes outlier limits per year
  (labelled explicitly); its full-history M5 median remains exact. Monte Carlo default
  output folders include source, seed and run count, also for saved runs. No `--part`
  tools remain. Day-cache writes reuse the queue's unique-temp/atomic-replace pattern
  and bounded Windows sharing retries; symbol repair reuses its independent file lock.

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

**Server time → UTC: how the rule is found** (`python -m backtester.tools.mt5_info`)

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
2026-10-09). It is written here after the first run of `tools.mt5_info`.

**Feed comparison** (`python -m backtester.tools.feed_compare`, ROADMAP 0.4): per symbol
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

### Updating the caches (ROADMAP 7.5)

Nothing is downloaded at app start. `python -m backtester.tools.update_data [--dry-run]` (or the
chart page's "Update data" button, `update_data.start_background()` / `state()`) fetches, per
symbol, everything after the last cached UTC day up to yesterday (`data/update.py` plans, the
tool executes; a failing symbol is reported and does not stop the others):

- **MT5 cache**: every symbol with a folder in `data/cache/mt5/`, from the running terminal in
  one session. The download starts `mt5_overlap_days` (7) before the first missing day, because
  `download_symbol` skips the first day with real bars of its range as partial. Weekend days
  are cached as empty files, so a Monday after a cached Sunday has nothing to do.
- **Binance cache**: BTCUSDT / ETHUSDT (monthly zip, else daily zips; days before today only).
- **histdata cache**: whole months after the last cached month, only months that are over;
  download page form + import. Symbols whose histdata cache is more than 93 days behind (a
  closed archive, e.g. EURUSD to 2021-12) are skipped.
- A symbol with no cached day is skipped ("no cache, use the full download tool"): an update
  never downloads a whole history.

**Chart fill (chart only):** for a symbol whose source is the histdata cache, the chart reads
the MT5 cache days after the last histdata day (`ui/chart_data.py` `FeedFillAdapter`,
`chart_adapter`, `chart_cached_days`; the payload field `feed_switch` is the first MT5 day).
`SymbolSources` and with it every backtest, tool and trades overlay keep reading one feed
(data split rule, ROADMAP 7.5).

## Build order

See `docs/ROADMAP.md`. Phases: 0 historical data (histdata.com) → 1 chart with replay → 2 confluences on the
chart → 3 strategy 1 + backtest → 4 settings menu → 5 risk & FTMO simulation →
6 robustness → 7 live trading via MT5 → 8 strategy 2 (NY Open index sweep).

## Research tools (V2.4 grid merge)

`tools/research.py` executes registered strategy grids from `research/grids/`.
For example: `python -m backtester.tools.research research/grids/orb.toml --dev-only`.
Combined families, robustness, shock days, filter twins and sensitivity use shared
analytics. Optional `--walk-forward` reads the saved development variant trades;
it never executes another backtest or reads the untouched test period.
`tools/research_helpers.py` supplies CSV and segmented-run helpers used by studies
and risk sweeps. `python -m backtester.tools.gap_bucket_study --mode index` (or
`--mode fx`) produces gap-bucket analytics independently of strategy backtests.
Previous per-strategy sweep executables were removed after four identical
old/new development results; migration evidence is in `results/gm3_*.log`.
