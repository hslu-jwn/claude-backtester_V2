# Roadmap

The order the project is built in. Each step is small enough for one Claude Code session:
build it, test it, show it to the user, commit. **Don't start the next step until the user
has checked the current one.** Step IDs (e.g. `1.2`) are how the user will refer to them.

Status: ☐ open · ◐ in progress · ☑ done (update this file when a step is finished)

---

## Phase 0: Historical data

FTMO's MT5 server only keeps about one month of 5m history, so another source is needed
for backtest history. **Since 2026-10-10 (user's decision) all history comes from
histdata.com** M1 files the user downloads into `data/raw/histdata/<SYMBOL>/` (bid only,
spread a fixed setting). Dukascopy (0.1) didn't work for the user and is no longer used;
its code was removed (C.1). MT5 is used to compare the recent month against FTMO's own feed, and
later for live trading.
Details and pitfalls: `ARCHITECTURE.md › Data sources`.

- ☑ **0.1 Dukascopy downloader + cache (removed 2026-10-12, C.1; history only).**
  `data/dukascopy.py` + command `python -m backtester.data.download`.
  Downloads M1 **bid and ask** candles day by day, saves them to `data/cache/` (Parquet),
  skips days already downloaded (so an interrupted download can resume), waits briefly
  between requests. Symbols: XAUUSD, GBPUSD, GBPJPY. Tests use saved sample files, not the
  network.
- ☑ **0.2 Resampling + cache reader.** Build 5m / 30m / 1h candles from the M1 cache
  (UTC-aligned) and a `CacheAdapter` implementing `DataAdapter` that the chart and
  backtests use. Keep bid candles for the chart and the spread (ask − bid) per candle for
  costs. Drop flat zero-volume minutes first (`ARCHITECTURE.md › Data sources`), so the
  daily break shows as a gap like on TradingView.
  Check: `python -m backtester.tools.show XAUUSD M5 2026-09-02T13:00 2026-09-02T14:00`.
- ⏸ **Postponed, then dropped (2026-10-10): the full Dukascopy download.** Dukascopy was throttling the user's
  connection (HTTP 503 / timeouts on every request). 0.3 waits until the download works
  again; Phase 1 continues with the XAUUSD days already in the cache. Done for the next
  download: the downloader stops the whole run after 3 days in a row fail with
  503/timeouts (clear message, suggests a higher `--delay`), and the default delay is 2 s.
  Download one pair at a time.
- ☑ **0.3 Data check.** Report per symbol: first/last candle, gaps (expected: weekends,
  holidays, daily break around 22:00 UTC for gold), duplicates, broken candles
  (high < low etc.), and a spot check. **The user compares 3 candles at known times with
  TradingView or MT5** (remember MT5 shows server time, usually UTC+2/+3).
  Gold's price scaling is already verified (0.1); **GBPUSD and GBPJPY are not yet**: check
  their point factors here (GBPUSD ≈ 1.2–1.4, GBPJPY ≈ 180–210) and add a real sample
  file test for each, like the XAUUSD one. Only the XAUUSD sample file
  exists in `tests/data/fixtures/` (the GBP ones were removed; a real GBP sample is still open).
  Meanwhile GBPUSD / GBPJPY September 2026 come from histdata.com:
  `python -m backtester.data.histdata data/raw/histdata/` → `data/cache/histdata/`
  (New York standard time, one hour later while Europe is on summer time; verified against
  TradingView, see `ARCHITECTURE.md › histdata.com`).
  Each symbol is read from its own source's cache (`data/sources.py`), no `--cache-dir` needed.
  Done: each pair's median 5m candle range is measured and its doji threshold set
  (`detectors/swings.py › equivalent_doji_body`, spec: confluences.md › Swing high / low);
  `tools.check` prints both.
  Check: `python -m backtester.tools.check XAUUSD GBPUSD GBPJPY`. Gaps are classified by the
  17:00 New York daily close they contain (daily break, weekend, holiday shortened/closed,
  not downloaded, unexpected), so no holiday calendar is needed.
  **Full history (2026-10-09, confirmed by the user).** The user downloaded histdata.com
  for all three symbols: year files 2020-2025 (`DAT_MT_{SYMBOL}_M1_{YYYY}.csv`) and month
  files 2026-01..09. Built: `data/histdata.py` reads year files and zip files too (same
  rules: histdata's clock → UTC (corrected below), bid only, only UTC days fully covered are written;
  periods may not overlap), rows grouped per day in one pass; tests in
  `tests/data/test_histdata.py` (year file, 31 Dec / 1 Jan from two files, zip, overlap).
  Imported (`python -m backtester.data.histdata data/raw/histdata/`, 2 min):

  | | cached days | with minutes | minutes | merged duplicate minutes |
  |---|---|---|---|---|
  | XAUUSD | 2020-01-02 .. 2026-09-30 (2,464) | 2,092 | 2,344,432 | 1,092 |
  | GBPUSD | 2020-01-02 .. 2026-09-30 (2,464) | 2,107 | 2,457,323 | 376 |
  | GBPJPY | 2020-01-02 .. 2026-09-30 (2,464) | 2,106 | 2,458,886 | 615 |

  No month or week is missing; no day in between is uncached. 2020-01-01 and 2026-10-01
  are only partly in the files (not written). Weekdays without any minute: holidays
  (Good Friday, 25 Dec, 1 Jan; gold more of them) and **2026-09-25 (Friday) for all three:
  histdata's September 2026 file has no row for that day** (and the 24th ends early).
  **2023-02-20 .. 2023-07-28: many weekdays have exactly 960 / 900 / 840 minutes**, i.e.
  whole hours missing in histdata's files (gold most, also the GBP pairs; see the data
  check below).
  **Data check over the full history** (`python -m backtester.tools.check XAUUSD GBPUSD
  GBPJPY`, 50 s). Integrity: 0 for every check (no duplicate timestamps after the
  importer's merge, no broken candles, no price <= 0), nothing "not downloaded", bid
  price range per year plausible (gold 1,451-5,597, GBPUSD 1.03-1.42, GBPJPY 124-220).
  Unexpected gaps (no 17:00 New York close inside, >= 5 min), per year:

  | | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
  |---|---|---|---|---|---|---|---|
  | XAUUSD | 3 | 1 | 2 | 549 | 3 | 6 | 3 |
  | GBPUSD | 15 | 41 | 41 | 643 | 51 | 28 | 12 |
  | GBPJPY | 37 | 18 | 26 | 635 | 17 | 23 | 10 |

  (After the time-zone fix below; before it, gold had 13-22 a year outside 2023, the
  false 20:00 break.)

  - **2023-02 .. 2023-07: about 110-140 hours missing per month and symbol**, as holes of
    1-3 whole hours on most weekdays (histdata's files). Backtests over that half year see
    candles missing (e.g. a 30m candle with 0 or 30 minutes); the user decides whether to
    leave it out or get it from another source.
  - **Time zone fixed (user's TradingView check, 2026-10-09).** Gold showed its daily
    break at 20:00-21:00 UTC instead of 21:00-22:00 in exactly the weeks where only the US
    is on summer time (2nd to last Sunday of March; last Sunday of October to 1st Sunday
    of November). The user compared XAUUSD 5m 2026-03-18 14:00 UTC on TradingView (OANDA:
    O 4878.655 H 4887.310 L 4872.340 C 4884.035): it was our 13:00 candle. histdata's clock
    changes on the **European** dates: New York standard time (UTC−5), one hour later
    while Europe is on summer time. `data/histdata.py › histdata_to_utc` now converts that
    way (tests: `test_clock_changes_on_europes_dates`, the TradingView candle included);
    the full history was re-imported. Now gold's break is at 21:00-22:00 UTC in those
    weeks too, the Sunday opens are at 17:00 New York in every week, and the checked
    candle is at 14:00 (4877.875 / 4886.325 / 4871.798 / 4883.825).
  - **The Sunday evening of Europe's change (checked by the user, 2026-10-09).** histdata's
    files skip the hour 19:00-19:59 (their clock) on the March Sunday and repeat it on the
    October Sunday, every year and symbol. The user's TradingView check (GBPUSD 5m, Sunday
    2026-03-29) shows our 22:00-22:55 candles at the same UTC times, so the conversion is
    right: in March histdata simply has no 23:00 UTC hour (TradingView has it) and has
    flat pre-open quotes at 21:00-21:55 that TradingView doesn't show; in October the
    repeated hour is an exact copy (same 60 rows twice), merged by the import with no
    loss. Both are before Tokyo (00:00 UTC then), no change needed.
  - GBPUSD 2026-05-18: 4 h + 3 h + 2 h + 1 h missing. GBPUSD 2024-11-07: four 1-hour gaps.
  - Days: 2026-09-25 (Friday) has no data for any symbol (missing in the file).
  The data check now picks its spot candles over the whole history when it covers more
  than a year (`history_spot_times`: years 2020-2026, US+EU summer, winter and US-only
  summer time weeks at 14:00 UTC; in the US-only weeks also the candle 1 h earlier) and
  prints the unexpected gaps per year. Tests in `tests/data/test_check.py`.
  **Compared by the user on TradingView (M5, bid, UTC):** 2026-03-18 14:00 was the old
  "1 h earlier" row, so those weeks were shifted (fixed above). Values after the fix:

  | UTC | season | XAUUSD O / H / L / C | GBPUSD O / H / L / C | GBPJPY O / H / L / C |
  |---|---|---|---|---|
  | 2020-07-14 14:00 | US+EU summer | 1800.598 / 1802.355 / 1800.058 / 1800.275 | 1.25090 / 1.25114 / 1.25048 / 1.25079 | 134.227 / 134.252 / 134.163 / 134.189 |
  | 2021-03-09 14:00 | winter | 1713.354 / 1715.879 / 1713.204 / 1714.354 | 1.38868 / 1.38926 / 1.38824 / 1.38870 | 151.193 / 151.231 / 151.136 / 151.158 |
  | 2022-03-23 14:00 | US summer / EU winter | 1935.073 / 1936.619 / 1934.828 / 1935.183 | 1.31751 / 1.31798 / 1.31750 / 1.31795 | 159.073 / 159.117 / 159.056 / 159.102 |
  | 2024-07-16 14:00 | US+EU summer | 2442.605 / 2444.795 / 2442.515 / 2444.265 | 1.29536 / 1.29561 / 1.29532 / 1.29558 | 205.488 / 205.552 / 205.482 / 205.521 |
  | 2025-03-05 14:00 | winter | 2899.735 / 2905.085 / 2899.105 / 2904.875 | 1.28221 / 1.28264 / 1.28194 / 1.28257 | 191.072 / 191.083 / 190.884 / 190.904 |
  | 2026-03-18 14:00 | US summer / EU winter | 4877.875 / 4886.325 / 4871.798 / 4883.825 | 1.33257 / 1.33316 / 1.33236 / 1.33309 | 212.527 / 212.574 / 212.482 / 212.573 |
  **Doji thresholds over time** (report only, no rule change; the user decides). The data
  check now prints, over more than a year, per year (per quarter in 2026): the median 5m
  range, the share of 5m candles that are dojis with the configured threshold and what
  the gold rule (1.53% x the median 5m range) would give (`doji_by_period`).

  | | XAUUSD median 5m range | XAUUSD dojis at 0.065 | gold rule would give | GBPUSD median | GBPUSD dojis | GBPJPY median | GBPJPY dojis |
  |---|---|---|---|---|---|---|---|
  | 2020 | 1.297 | 7.3% | 0.0198 | 0.00052 | 1.8% | 0.062 | 3.5% |
  | 2021 | 0.970 | 8.9% | 0.0148 | 0.00039 | 2.8% | 0.048 | 4.4% |
  | 2022 | 1.066 | 8.4% | 0.0163 | 0.00054 | 1.8% | 0.081 | 2.9% |
  | 2023 | 0.910 | 9.7% | 0.0139 | 0.00041 | 2.3% | 0.069 | 3.3% |
  | 2024 | 1.340 | 6.8% | 0.0205 | 0.00031 | 3.1% | 0.072 | 3.1% |
  | 2025 | 2.500 | 3.9% | 0.0382 | 0.00039 | 2.0% | 0.073 | 3.0% |
  | 2026 Q1 | 6.510 | 1.6% | 0.0995 | 0.00043 | 1.8% | 0.073 | 2.9% |
  | 2026 Q2 | 4.780 | 1.9% | 0.0730 | 0.00034 | 2.5% | 0.050 | 4.5% |
  | 2026 Q3 | 4.040 | 2.1% | 0.0617 | 0.00028 | 3.0% | 0.051 | 4.3% |

  Gold's 0.065 is a fixed price amount: with gold's 5m candles 3-7 times smaller in
  2020-2024 than in 2026, it makes 7-10% of the 5m candles dojis then versus about 2%
  now. The GBP pairs' thresholds (a few points, prices on the same scale over the years)
  give 1.8-4.5% in every period.
  **User (2026-10-09): the doji threshold is a detector setting with a changeable number.**
  It is one per symbol (Settings › Detectors › Doji threshold, `detectors.swings.
  doji_max_body`, saved in presets). Backtests already used it; now the chart overlays do
  too (swings, BOS + trend, sweeps, FVG, OB, BPR, session zones: `OverlaySettings.
  doji_max_body` / `swing_config`). The spec defaults are unchanged (gold 0.065).
- ◐ **0.4 MT5 adapter + feed comparison** (user's request 2026-10-09: MT5 connection
  before the strategy trades). `MetaTrader5` is the optional extra `[mt5]` (Windows only);
  everything else (tests, backtests, chart) works without it, unit tests use a fake module.
  - `data/adapters/mt5_adapter.py` (`Mt5Adapter`, a `DataAdapter`): candles via
    `copy_rates_*`, only closed candles (the forming one is dropped), times converted to
    UTC, MT5's spread per candle kept (real, unlike histdata).
  - Server time → UTC: not assumed. Determined from the latest tick vs real UTC and from
    MT5's history against the histdata cache (per week, incl. the DST weeks); the rule is
    documented in `ARCHITECTURE.md › MetaTrader 5`.
  - Symbol mapping: FTMO's names for XAUUSD, GBPUSD, GBPJPY (suffixes possible), their
    specs printed (contract size, digits, tick size / value, volume min / step / max, stops
    level, swap, trade mode); the mapping is a setting.
  - Feed comparison per timeframe over the period MT5 has history for: best time offset,
    average |difference| of O/H/L/C, how often the candle color differs, missing candles on
    either side. FTMO spread per symbol and hour of day (median, 90%) next to the cost
    defaults (3.1). Report only; the user decides about the defaults.
  **Built (2026-10-09), not yet run against FTMO:** the terminal was running but not
  logged in (`Terminal: Authorization failed`), so the results below are still open.
  - `data/adapters/mt5_adapter.py`: `Mt5Adapter`, `ServerClock` (server time = zone time
    + whole-hour shift), `load_mt5` (the only `MetaTrader5` import). Tests:
    `tests/data/test_mt5_adapter.py` (US / EU / fixed clocks incl. the US-only summer time
    weeks, forming candle dropped, spread in price, server-time request window, nothing
    else imports MetaTrader5).
  - `python -m backtester.tools.mt5_info`: symbol names + specs, the clock measured per
    week of MT5's H1 history against the cache (`tools/mt5_compare.py`), saved to
    `results/trading.json` (symbol names; the clock only when one rule predicts every week).
    Method: `ARCHITECTURE.md › MetaTrader 5`. Tests: `tests/data/test_mt5_info.py`.
  - `python -m backtester.tools.feed_compare`: the comparison and spread tables, written to
    `results/feed_compare/<time>/`. Tests: `tests/data/test_feed_compare.py`.
  - Check (after the login is saved in Settings ⚙ → Trading): run `tools.mt5_info`; it
    prints FTMO's names and specs, the offsets per week, the deciding DST weeks and the
    rule. Then `tools.feed_compare`. Open: the rule found (→ ARCHITECTURE), the symbol
    specs, the comparison and spread numbers (→ here, for the user's decision on 3.1).
- ☑ **0.5 Index data: NAS100, US500** (user's request 2026-10-10, for strategy 2; data
  side only, no strategy code). Built:
  - `data/histdata.py`: a folder is searched with its subfolders
    (`data/raw/histdata/<SYMBOL>/`), single files / zips still work; histdata's
    `NSXUSD` / `SPXUSD` are cached as **NAS100** / **US500** (`SYMBOL_NAMES`).
  - Clock: the indices use histdata's forex / gold clock (their 16:15 break moves to
    15:15 on histdata's clock in the US-only summer time weeks, like gold's 17:00 close
    to 16:00), so the existing conversion applies. Candles for the TradingView check
    (M5, chart in UTC; other feeds may be offset in price, the shape and timing must
    match):

    | UTC | season | NAS100 O / H / L / C | US500 O / H / L / C |
    |---|---|---|---|
    | 2026-09-02 13:30 | US+EU summer | 29051.93 / 29055.47 / 28997.29 / 29037.24 | 7641.23 / 7641.74 / 7633.63 / 7640.38 |
    | 2026-01-14 14:30 | winter | 25576.76 / 25624.69 / 25504.63 / 25616.72 | 6933.64 / 6941.35 / 6922.85 / 6940.15 |
    | 2026-03-18 13:30 | US summer / EU winter | 24699.25 / 24729.03 / 24675.29 / 24715.14 | 6692.13 / 6699.50 / 6687.74 / 6696.25 |
    | 2026-03-18 12:30 | ^ 1 h earlier | 24796.03 / 24796.03 / 24715.28 / 24736.08 | 6719.85 / 6719.85 / 6699.64 / 6703.40 |
    | 2022-03-23 13:30 | US summer / EU winter | 14532.38 / 14547.90 / 14494.51 / 14508.16 | 4485.20 / 4489.45 / 4481.24 / 4483.45 |
    | 2026-03-18 20:10 | last candle before the break | 24411.90 / 24418.31 / 24392.74 / 24399.05 | 6616.05 / 6616.40 / 6609.85 / 6611.04 |
    | 2026-03-18 22:00 | first candle after it | 24402.76 / 24405.04 / 24378.75 / 24385.25 | 6618.35 / 6618.94 / 6611.45 / 6614.24 |

    **Checked by the user on TradingView (US500, 2026-10-11):** the clock is right.
    TradingView's feed is a few points higher than histdata, by the same amount on every
    value of a candle; the candle 1 h earlier is clearly different, so no hour shift.
    NAS100 has the same break pattern minute for minute, so it uses the same clock (not
    compared separately).

    | UTC | TradingView O / H / L / C | TradingView − ours |
    |---|---|---|
    | 2026-03-18 12:30 | 6724.23 / 6724.30 / 6704.10 / 6707.85 | +4.38 / +4.45 / +4.46 / +4.45 |
    | 2026-03-18 13:30 | 6700.60 / 6703.85 / 6691.98 / 6696.60 | +8.47 / +4.35 / +4.24 / +0.35 (range 11.87 vs 11.76) |
    | 2026-09-02 12:30 | 7648.50 / 7649.25 / 7645.00 / 7646.00 | +8.37 / +8.38 / +8.14 / +8.39 |
    | 2026-09-02 13:30 | 7649.00 / 7650.00 / 7642.25 / 7648.75 | +7.77 / +8.26 / +8.62 / +8.37 |

  - `tools.check NAS100 US500`: gap rules per symbol (`check.SYMBOL_CONFIGS`, confirmed by
    the user): daily break 16:15-18:00 New York (up to 120 min), weekend Fri 16:15 → Sun
    18:00 NY (up to 51 h: the US DST-change weekend is 50.75 h). Over 2020-01-02 ..
    2026-09-30 (files already in `data/raw/histdata/`, imported into a scratch cache):
    integrity 0, bid range per year plausible (NAS100 6,636-30,797, US500 2,184-7,817),
    unexpected gaps per year NAS100 25 / 2 / 3 / 515 / 50 / 16 / 12, US500 49 / 13 / 6 /
    558 / 54 / 15 / 9 (2020-2026): 2023 = the histdata holes every symbol has; real halts
    among the rest (limit-down nights 2020-03-09/16/18, CME outage 2025-11-28).
  - Doji threshold (gold rule, user's choice: median over the full history): NAS100
    median 5m range 11.57 → **0.1767**, US500 2.51 → **0.0384** (`MEDIAN_M5_RANGE`).
    Dojis per year with it: NAS100 1.1-3.3%, US500 2.4-6.4%.
  - Costs (`engine/costs.py`): fixed spread NAS100 1.0, US500 0.5 (user's estimates until
    FTMO's are measured), commission and swap 0; slippage per fill for every symbol
    (risk-management.md › Costs). Slippage and swap are stored, not yet applied (Phase 5).
  - History: histdata has both indices from 2010. Downloaded and imported (2026-10-11):
    2018-01 .. 2026-09 (cached 2018-01-02 .. 2026-09-30, 3,194 days; NAS100 2,951,165
    minutes, US500 2,847,541). 2018-2019 hold the pre-2020 all-time highs (ATH check) and
    warm-up, so backtests can start 2020-01-01. All raw files moved into
    `data/raw/histdata/<SYMBOL>/` (NAS100 and US500 17 files, the others 15).
  - **Old trading hours until 2018-12-14:** the index files follow the old CME hours, a
    halt 16:15-16:30 and a break 17:00-18:00 New York (from 2018-12-17: 16:15-18:00).
    Expected gaps (user, 2026-10-11): `check.OLD_CME_BREAKS` (`BreakWindow`, dated).
    Unexpected gaps 2018 / 2019 after that: NAS100 18 / 7, US500 1,170 / 580; US500's
    are almost all 5-10 min of no quotes at night (thin feed in those years).
  Check: `python -m backtester.tools.check NAS100 US500`, chart NAS100 / US500 M5.

## Cleanup backlog and status notes (2026-10-12, agreed with the user)

- **Strategy 1 is paused** (user): its ◐ steps stay as they are, its tests stay green.
- **"Done" = the user marks a step done**; a done step can be reopened for rework.
- ☑ **C.1 Remove Dukascopy** (done, accepted by the user 2026-10-12): the cache helpers moved to `data/cache.py` (`COLUMNS`, `cache_path`, `read_cached_day(s)`, `empty_cache_frame`, `write_atomic`, `DEFAULT_CACHE_DIR` = histdata cache, test `tests/data/test_cache.py`); `dukascopy.py`, `download.py`, their test and the `.bi5` fixtures are gone. `CacheAdapter()` without argument now reads the histdata cache (it used to point at the Dukascopy folder). The "day missing" message names `python -m backtester.data.histdata`. Backtests byte-identical (trades.csv, both strategies).
- ☑ **C.2 Windows-only MT5 path test** (done, accepted by the user 2026-10-12): `test_known_servers_from_the_terminal_folders` is skipped off Windows; `test_nothing_else_imports_metatrader5` now passes `PYTHONPATH=src` to its subprocess, so it no longer needs `pip install -e`.
- ☑ **C.3 Strategy registry + template folder** (done, accepted by the user 2026-10-12): `strategy/registry.py` (`StrategySpec`, `REGISTRY`, `make_strategy`, `strategy_name`, `default_config`) replaces the `isinstance` special case in the runner; `run.py --strategy` takes its names; `Strategy` now declares `h4_alignment` / `full_history` (the runner used `getattr`); `strategy/_template/` (config, strategy, README with the steps), tests `tests/strategy/test_registry.py`. Backtests byte-identical. **Shared detectors (2026-10-12, user's yes):** `swings`, `fvg`, `order_block`, `equilibrium` moved out of both strategy configs into `RunSettings.detectors` (`detectors/settings.py` `DetectorSettings`; paths `detectors.fvg.*` etc.); a strategy takes `(symbol, config, detectors)`. Old preset / settings JSON with them under `strategy` is migrated on load (`settings._migrate`). Backtests byte-identical. `confluence_kinds` stays per strategy (different defaults). The settings menu / presets for strategy 2 are 8.6a (done).
- ☑ **C.4 Layer fixes** (done, accepted by the user 2026-10-12): `data/check.py`, `show.py`, `feed_compare.py`, `mt5_info.py`, `mt5_compare.py` moved to `tools/` (commands: `python -m backtester.tools.<name>`); `paths.py` holds `RESULTS_DIR` (live/ no longer imports the runner); strategy 2 names `TradeResult` only under `TYPE_CHECKING`; `tests/test_layers.py` checks every import against the layer order. `CsvAdapter` (unused, untested) deleted. `live.trading_settings.SYMBOLS` is now every backtest symbol (NAS100, US500 added).
- **Cleanup audit (2026-10-12), decided:** `overlay_drawings` (ui/overlays.py) and `selected_overlays` (ui/pages/chart.py) are only called by tests, but those tests are the reference for what the chart page does, so they stay. `RETCODE_DONE_PARTIAL` and `delete_credentials` stay (documented MT5 code, a "forget login" function). Not done: splitting `ui/pages/chart.py` (1,393 lines) and `tools/check.py` (669 lines).
- **Test baseline for the cleanup:** 817 passed, 2 skipped (the `.bi5` fixtures, now removed); end state 921 passed. Golden check: `trades.csv` of strategy 1 (XAUUSD, GBPJPY) and strategy 2 (NAS100 / US500 from copied data) over 2026-04-01..05-15 byte-identical before and after.
- Known, left as is: `strategy.strong_move.atr_mult` is unused and hidden in the settings; the results trade list uses Dash's deprecated `DataTable` (works).

## Phase 1: Chart (no lookahead)

- ☑ **1.1 Dash chart page.** Candlesticks from the cache. Pick symbol, timeframe and date
  range. Approximate timestamps on the x-axis, zoom/pan, no gaps for weekends.
- ☑ **1.2 Replay mode.** A cursor that steps forward candle by candle (buttons + autoplay
  speed). Only candles up to the cursor are drawn, using `SeriesView`, so the chart shows
  exactly what the engine sees. Higher timeframes during replay come from
  `HigherTimeframeClock` only.
  Replay steps on the shown timeframe (M5: 5 minutes per step, H1: one hour) and keeps
  the replay time when switching timeframe, and the visible time span around it (M5 -> M1:
  the same hours with smaller candles; a zoom/pan sets the span and replay steps keep it). Start: click a candle (default: first candle of
  the last day). `engine/replay.py` hands out the views; the 3.1 engine loop reuses it.
- ☑ **1.3 Session lines.** Implement `sessions.py` (DST-aware, tested around the March and
  October/November changes) and draw a vertical line at each session start (Tokyo yellow,
  London blue, NY red), with one "Sessions" switch to show or hide them all.

## Phase 2: Confluences on the chart (visual check)

Every detector gets: tests (incl. the no-lookahead test) → an overlay layer → **user
checks it on the chart** → commit. The chart starts empty: a switch turns the overlays on
and the "Overlay types" checkbox panel (opens like a dropdown) picks which types are shown
(swings, BOS, FVG, OB, breaker, BPR, session zones, … in roadmap order; zone types have
indented sub-entries for their ★ confirmation / ✕ invalidation markers). This "all confluences" mode checks the detectors; the strategy's
session view (3.5) is separate. Overlays draw a small marker on the
**confirming candle**, so the user can see when each pattern became known, and a hover
text with its state (active / tapped / confirmed / invalidated).

- ☑ **2.1** ATR + strong-move filter (no overlay; used by the others).
  Check: `python -m backtester.tools.show XAUUSD M5 2026-09-02T13:00 2026-09-02T14:00 --atr 14`.
- ☑ **2.2** Swing highs / lows. Overlay: ▼ orange at a swing high / ▲ cyan at a swing low on
  the candle with the extreme wick, a thin line at the swing price over the turn candles
  (first turn candle to the confirming candle) ending in a dot on the confirming candle (hover).
  Also adds the Overlays switch and the type dropdown every later detector plugs into.
- ☑ **2.3** Trend label + BOS. `detectors/bos.py`, `detectors/trend.py`, overlay
  "BOS + trend": a red horizontal line at the broken swing's price, from the swing's
  extreme-wick candle to the breaking candle, labeled "BOS", hover dot on the breaking
  candle (first BOS / trend flip; a break with the trend is no BOS). Two badges in the chart's top-left corner show the trend
  at the replay cursor: the **overall trend** (4H by default, `TrendConfig.overall_timeframe`;
  60 days of 4H warm-up history before the chart range, `ChartConfig.overall_trend_warmup_days`)
  and the shown timeframe's trend.
- ☑ **2.4** Zone validation state machine (shared by all zones). `detectors/zone.py`:
  `ZoneBox` (fixed geometry), `ZoneValidator` (tap → confirmed, or invalidated; emits
  `ZoneTransition` events), `ZoneBook` (the zones a detector still checks). No overlay of
  its own; seen through the FVG overlay. Check: `pytest tests/detectors/test_zone.py`.
- ☑ **2.5** FVG. `detectors/fvg.py`, every gap in both directions, strong-move filter on
  candle 2 (switch, default off). Overlay "FVG": a green (bullish) / red (bearish) box from
  candle 1 until it is used: to the candle that confirmed or invalidated it, to the cursor
  while still open (no length limit); invalidated ones fainter. No marker on candle 3
  (user's choice): hovering over the box shows range, candle 2 vs. the strong-move
  threshold, the shown timeframe's trend (with / against) and the state (taps are
  listed there, no marker on the chart); the sub-entries "↳ ★ confirmations" / "↳ ✕ invalidations" under FVG add ★ / ✕
  (every zone overlay gets these sub-entries). Panel switch "FVG strong-move filter".
- ☑ **2.6** Order block, first version. **This is the code in use** (2.12 is on hold, see
  there); kept here as built. `detectors/order_block.py`: at each BOS, the leg into the most
  recent swing of the opposite kind (`confluences.md › Order block`); strong-move filter on
  the move away (switch, default on). Overlay "Order block": yellow box from the leg's
  first candle until confirmed / invalidated, hover over the box (leg, swing, BOS, strong
  candle, state), sub-entries ★ / ✕. Panel switch "OB strong-move filter". Zone drawing
  is shared (`ui/zone_overlay.py`): one color per zone type in both directions (FVG green,
  OB yellow), overlapping boxes stack darker.
- ☑ **2.7** Breaker block. Rules defined by the user on 2026-10-10 (`confluences.md ›
  Breaker block`: the last green run into the swing high a bullish BOS breaks, bearish
  mirrored). Built as part of 8.2 (8.2.3, see there).
- ☑ **2.8** BPR. `detectors/bpr.py`, built on the FVG detector: an older FVG invalidated
  by the move (candles 1–3) that creates an overlapping FVG in the opposite direction
  (`confluences.md › Balanced price range`). Overlay "BPR": purple box (both directions)
  from the older FVG's candle 1 until confirmed / invalidated, hover over the box (both
  FVGs, state), sub-entries ★ / ✕. Follows the "FVG strong-move filter" switch.
- ☑ **2.9** Session zones (30m), incl. support/resistance by price, flips and the kill on the 3rd break (`strategy-session-zones.md › Session zones`, › Zone flips, › Session zones on the chart).
  `strategy/session_zone_sweep/zones.py` (`SessionZoneTracker`; a candle belongs to the session it closes in). Overlay "Session zones": dotted box from the swing to the end of the session the zone is used in (or its kill), colored by that session, filled only there. Session lines now go through the candle the session starts on.
- ☑ **2.10** Multi-timeframe view: show 30m zones on the 5m chart (done with 2.9: shown on M5–M30; the chart loads 30m candles, read only through the replay's clock).
- ☑ **2.11** Liquidity sweep. `detectors/sweep.py` (`confluences.md › Liquidity sweep`):
  the top of the move that took a high confirmed since the last BOS (or the high that BOS broke), turned into a sweep by
  the next bearish BOS (lows mirrored); exists from the BOS candle. Overlay "Liquidity
  sweep": magenta line from the swept high to the sweeping candle, marker on the wick, hover.
- ⏸ **2.12** Order block rework. **On hold** (user, 2026-10-07): built, then reverted because
  the user found the first version (2.6) looked better on the chart; may come back to it.
  The built version is on branch `ob-rework-2.12` (incl. the rule for a red top: then the
  previous green run). The user finds OBs hard to define as fixed rules (which swept high
  counts is intuition: a recent one, not necessarily the last one, sometimes much older).
  Later idea: the user shows a set of example OBs and an algorithm is derived from them.
  Planned as: Rewrite `detectors/order_block.py` on top of 2.11
  (`confluences.md › Order block`): one OB per liquidity sweep; range = same-color leg into
  the sweeping candle, wick to wick; exists from the BOS candle; no strong-move filter
  (remove the switch and `OrderBlockConfig.strong_move*`); only invalidation (close beyond
  the far edge), no tap / confirm. Overlay stays yellow, drawn until invalidated, only the
  ✕ sub-entry.

## Phase 3: Strategy 1 + backtest

- ◐ **3.1 Engine.** Backtest loop over 5m with 30m/1h clocks; trade management in R
  (SL before TP inside one candle, break-even rule at the next session start).
  Costs: the cache has no ask prices now (histdata.com), so the spread is a **fixed setting
  per symbol** (user's FTMO values), plus an optional commission per trade; both can be
  switched off. Longs enter at ask (bid + spread) and exit at bid; shorts mirrored.
  Default costs (estimates, user asked for rough values; FTMO publishes no fixed spreads):
  spread XAUUSD 0.25 (25 cents), GBPUSD 0.00003 (0.3 pip), GBPJPY 0.010 (1.0 pip);
  commission per lot round turn $5 for forex (user's figure), $6 for gold (reported about
  $5.81, scales with the gold price). Commission is a dollar amount per lot, so in R it
  depends on the SL distance: commission_R = commission per lot / (SL distance x value of a
  1.0 price move per lot). Contract specs: XAUUSD 100 oz per lot ($100 per $1 move),
  GBPUSD 100,000 GBP per lot ($10 per pip), GBPJPY 100,000 GBP per lot (pip value in USD
  via USDJPY, use a fixed approximation, setting).
  Reuses `engine/replay.py` for the multi-timeframe stepping.
  Built: `engine/backtest.py` (`run_backtest`, `EngineConfig`), `engine/trade.py`
  (`TradeResult`), `engine/costs.py` (`CostConfig`, `SymbolCosts`), tests in
  `tests/engine/test_backtest.py`. **Provisional assumptions, awaiting the user's check:**
  - 1R = chart (bid) distance entry → initial SL. `r_gross` uses chart prices;
    `r_net = r_gross − spread_R − commission_R`, spread_R = spread / SL distance.
  - SL / TP are triggered by the chart (bid) prices for longs and shorts alike; a short's
    exit fills at ask (level + spread) but is not triggered earlier by the ask.
  - Break-even: decided once, by the close of the first base candle closing at or after
    the first session start after the entry (5m: the candle closing at the start). Close
    beyond the cost-covered break-even level → SL = that level from the next candle on;
    otherwise the original SL stays for good. **Changed by the user (2026-10-07):
    break-even includes the costs** (a hit ends at 0R net, `strategy-session-zones.md ›
    Stop loss`); built with 3.3b (`CostConfig.break_even_offset`).
  - Gap through the SL fills at the candle's open (can be worse than −1R); gap through
    the TP fills at the TP (never better than planned).
  - Still open at the end of the data → closed at the last close (`END_OF_DATA`).
  - GBPJPY commission uses USDJPY ≈ 150 (`USDJPY_APPROX`).
- ◐ **3.2 Setup state machine** (sweep → 30m reaction → 5m BOS → confluence → entry).
  Step 3 uses the confluence BOS (only against the 5m trend); setting
  `SessionZoneSweepConfig.entry_bos_with_trend` (default off) also lets a close above the
  last 5m swing high in a 5m uptrend count (`strategy-session-zones.md › Entry sequence`).
  Built: `strategy/session_zone_sweep/setup.py` (`Setup`, `StructureTracker`),
  `signals.py` (`SetupTracker`: feeds the setups from the 5m / 30m detectors), tests in
  `tests/strategy/session_zone_sweep/test_setup.py` with a hand-built London / New York
  day (`scenario.py`). **Provisional assumptions, awaiting the user's check:**
  - Sweep and reaction are read on closed 30m candles. Sweep = wick into the zone past
    its near edge (touch is no sweep, like a tap). Reaction = green, non-doji 30m close
    above the zone; the sweep candle can be the reaction candle.
  - The 30m candle that sets an undecided zone's role (first close outside) can itself be
    the sweep + reaction.
  - "During that 30m candle or after": the 5m BOS candle closes after the reaction
    candle's open.
  - Confluence: a bullish FVG / OB / BPR that came into existence at or after the BOS
    leg's low (lowest low between the broken swing's wick candle and the BOS candle), not
    yet confirmed or invalidated, confirmed (zone.py validation) by a candle after the
    BOS candle. Taps before step 4 count. Breakers have been a confluence since 8.2.3.
  - FVG trend rule only for FVGs; OBs and BPRs have none.
  - Cancel: only a real opposite 5m BOS cancels (also with `entry_bos_with_trend` on).
  - After an entry the zone's setup restarts at the sweep; only 30m candles closing after
    the entry count. Several setups triggering on the same candle in the same direction
    give one entry (all of them restart). Several confluences confirmed at once: the most
    recently formed one is used.
  - A zone flip by a close of the other color (e.g. a green candle gapping below support)
    is no reaction: the new setup starts at the sweep.
  - `skip_tokyo` ignores the zones active in Tokyo.
- ◐ **3.3 SL / TP** incl. 1h obstacles and the 1.2R minimum.
  Built: `strategy/session_zone_sweep/targets.py` (`ObstacleTracker`, `stop_loss`,
  `take_profit`), `strategy.py` (`SessionZoneSweep`, the `Strategy` the engine runs; keeps
  every signal and its outcome in `decisions`), tests in `test_targets.py`.
  **Provisional assumptions, awaiting the user's check:**
  - ATR = the 5m ATR(14) at the entry close. SL buffer and "just below" an obstacle are
    ATR fractions, both default 0 (`sl_buffer_atr_mult`, `tp_buffer_atr_mult`; spec: TBD).
  - "The resistance zone" = the nearest live session zone with role resistance whose
    bottom is above the entry. Entry inside or above every resistance zone → fallback.
  - Fallback: the nearest obstacle level between 1.2R and 2R; none → 2R.
  - Obstacles: untouched 1h swing highs (no later 1h wick reached them) and never-tapped
    bearish 1h FVGs / OBs, existing at the entry, level = swing price / zone bottom.
    Clustering chains: each level less than 0.2R above the previous one joins its cluster.
    The TP sits below the first level of the first cluster it may not pass.
  - R for TP / minimum R:R is on chart prices (costs not included).
  - A signal whose TP is below 1.2R is dropped and still restarts the setup.
  - Last 1.5h tag: entry close time within 90 minutes of the next session start.
- ◐ **3.3b Trades on the chart** (user's wish, before 3.4). Spec:
  `strategy-session-zones.md › Trades on the chart`. The chart page runs strategy 1 + the
  engine on the shown symbol and range (same `Replay`, with enough warm-up before it) and
  draws overlay "Trades": position boxes (long: green entry→TP, red entry→SL; short
  flipped) from entry to exit, R:R label, hover; sub-entry "↳ trade confluences" (swept
  session zone, 5m BOS, entry confluence, BOS-move low when the SL used it) in the normal
  overlay colors. Replay: boxes appear at the entry close and grow until the exit.
  Also in this step: **break-even with costs** (3.1 change: SL moves to the level where a
  hit is 0R net; "in profit" = the close is beyond that level).
  Built: `ui/trades_overlay.py` (overlay "Trades", sub-entry "↳ trade confluences"),
  `TradeResult.break_even_stop`, `Targets.sl_at_bos_leg`; tests in
  `tests/ui/test_trades_overlay.py`. Choices made while building (check them):
  - The backtest runs over the whole run of consecutive cached days containing the shown
    range (not a fixed warm-up), cached per symbol, so every range and timeframe shows the
    same trades. Only trades entered on the shown range are drawn.
  - On a timeframe other than 5m, a trade is drawn on the chart candle containing its 5m
    entry / exit (on 30m both can be the same candle).
  - The swept session zone is drawn from where it formed to the entry candle, filled from
    its active session's start; the BOS line from the broken swing's wick candle to the
    BOS candle.
- ◐ **3.3c Strategy rework from the user's manual trades** (2026-10-07, XAUUSD 2026-09-14).
  Spec: `strategy-session-zones.md` › Entry sequence (equilibrium entry), › Stop loss (SL
  size), › Take profit (reworked: reversal levels = session zones, untouched 1h highs,
  1h OBs; no 1h FVGs; 4H OBs as hard limit; two TPs 50/50 with break-even after TP1; TP at
  the minimum R when no level is in reach). New settings: `use_equilibrium`,
  `max_sl_atr_mult`, `min_sl_atr_mult`, TP1 share, break-even after TP1. The engine must
  support partial closes (result in R = weighted sum), and the chart boxes show TP1 and TP2.
  Built: equilibrium in `signals.py` (`equilibrium_zone`, `ZoneKind.EQUILIBRIUM`), SL size
  and the new TP in `targets.py` (`UnmitigatedOrderBlocks` for the 4H limit, `Level`,
  `Rejected`; `Decision.rejected` says why a signal gave no trade), partial closes in
  `engine/trade.py` (`PartialExit`, `TradeResult.parts`), TP1 line + per-part hover in
  `ui/trades_overlay.py`; tests in `test_equilibrium.py`, `test_targets.py`,
  `tests/engine/test_backtest.py`, `tests/ui/test_trades_overlay.py`.
  **Provisional assumptions, awaiting the user's check:**
  - Confirmed by the user (2026-10-07): the equilibrium's move ends at the first 5m
    swing high confirmed after the BOS candle (leg = BOS leg's low → the highest wick up
    to the candle confirming that swing, fixed; 2026-10-08); only a **close** below the leg's low invalidates it (confluences.md updated);
    `min_sl_atr_mult` stays off by default.
  - Equilibrium exists from the end swing's confirming candle, whose own wick doesn't tap
    it (zone.py rule). Only the setup whose BOS made the leg may use it. It also follows
    the "most recent confluence wins" rule when several confirm at once.
  - SL size = entry → SL after the buffer; widening comes before the `max_sl_atr_mult`
    check. No ATR yet → no SL size checks.
  - TP levels: a cluster's level is its nearest price; a cluster that starts below
    `min_rr` is passed as a whole. Resistance zones count only with their bottom above
    the entry (entry inside a zone: not a level). TP1 / limit compare the TP price after
    the buffer with `min_rr` / the cap.
  - TP2 = the furthest of the next 1 + `obstacles_passable` levels within the limit.
  - 4H OB "unmitigated" = never tapped, same as 1h; strong-move filter as for 1h OBs.
  - After TP1 the break-even SL counts from the next candle; if the TP1 candle itself
    closes back beyond the break-even level, the rest closes there in that candle.
    TP1 and TP2 in one candle (no SL): both filled; SL and TP1 in one candle: SL.
  - Session-start break-even still applies to the rest if it hasn't moved yet.
  - Chart: equilibrium drawn indigo (display choice); the green box runs to TP2, with a
    dashed TP1 line; R:R label "TP1 R / TP2 R".
- ☐ **3.3d Review mode** (proposed, user to confirm): the app jumps from one setup the
  program found to the next; the user marks take / skip (+ short reason, optional own TP);
  saved to a file. Builds a reference set (agreement % after every rule change) and, later,
  training data for a learned filter.
- ☑ **3.4 Backtest run + results file.** Command to run a backtest; writes the R trade list
  and settings used to `results/<run>/`. **One or several symbols per run** (user, 2026-10-08):
  results per symbol and combined (trades merged in time order). Reports progress (for the
  progress bar in 4.0) and can run in the background so the app stays usable. Also records, per session, the session zones and
  the confluences that were part of a setup (triggered or not, confirmed or not), so the
  session view (3.5) can draw them without re-running the strategy.
  Built: `runner.py` (`run_backtests`, `write_results`, `start_run` / `BackgroundRun`),
  command `python -m backtester.run XAUUSD GBPUSD --start 2026-09-01 --end 2026-09-30`
  (`run.py`; options `--warmup-days`, `--workers`, `--out`, `--cache-dir`), summary in
  `analytics/metrics.py`, per-session record in `strategy/session_zone_sweep/journal.py`
  (fed by `SetupTracker`'s `session_zone_events` / `zone_transitions` / `links`), engine
  progress callback; tests in `tests/test_runner.py`, `tests/analytics/test_metrics.py`,
  `tests/strategy/session_zone_sweep/test_journal.py`. Files: `trades.csv`, `settings.json`,
  `summary.json`, `sessions.json`. Choices made while building (check them):
  - Days are UTC days, both ends included. Uncached days at the start / end of the range
    are left out with a note (the cache starts 2026-09-02); a gap inside is an error.
  - Warm-up: up to 14 cached days before the range (`RunSettings.warmup_days`), only
    consecutive cached days. Trades entered in the warm-up are dropped. The chart (3.3b)
    runs over the whole cached block instead, so the two can differ when the block starts
    more than 14 days before the range.
  - Trades still open at the range's end close at the last close (`END_OF_DATA`); the run
    does not continue past `--end`.
  - Win / loss / break-even by net R (break-even: 0R net). Average R:R = planned R if every
    TP is hit (share-weighted). Max drawdown on cumulative R with trades counted at their
    exit time.
  - "Part of a setup" = a confluence a setup at step 4 (after its 30m reaction and BOS)
    could have used: open, same direction, formed at or after the BOS leg's low (an
    equilibrium only for its own BOS). `setup_confirmed` = a setup took its confirmation
    (an entry signal); `traded` = it became an order. Its record ends when it is
    confirmed, invalidated or its session ends; a setup's reset doesn't end it.
  - A trade belongs to the session whose start < entry close time <= end.
  - Symbols run in separate processes (one per symbol); results are identical to a run in
    one process.
  Fixed (user, 2026-10-08): GBPUSD runs crashed in `equilibrium_zone` (2026-09-04 21:00,
  2026-09-24 23:50): the first 5m swing high after the BOS was below the BOS leg's low
  (weekend / rollover gap), so the leg was upside down. The leg's far end is now the
  move's high: the highest wick from the BOS leg's low up to the candle that confirms the
  end swing (short mirrored); test with the hand-built 2026-09-04 GBPUSD candles.
- ☐ **3.5 Session view.** Click a session line → that session's zones, setup confluences
  and trades (TradingView-style position boxes) are drawn; click outside the chart → off.
  Static by default, with a "replay this session" button.
  Spec: `strategy-session-zones.md › Session inspection view`.
- ☑ **3.6 Results view.** Its own page, opened automatically when a run finishes (user,
  2026-10-08), TradingView look (see 4.0). Stat cards (net R gross / net, number of trades,
  win rate, average R:R, average win / loss, profit factor, expectancy, max drawdown in R),
  equity curve in R over time (gross and net), R distribution, splits by symbol / session /
  long-short / confluence type / TP1-TP2 / tag, run selector (earlier runs). Trade list (click a trade → chart jumps to it and selects its session), win rate,
  expectancy, profit factor, max drawdown in R, equity curve in R, split by symbol /
  session / tag.
  Built (2026-10-08, confirmed by the user 2026-10-09): `ui/pages/results.py` (top bar: ← Chart,
  run selector, symbol filter All / per symbol for every tab; header: run, symbols, days,
  preset, run date; tabs Overview / Performance summary / List of trades),
  `assets/results.js` (equity curve with Lightweight Charts), `assets/results.css`;
  metrics in `analytics/metrics.py` (`summarize` extended, `split` + `SPLITS`,
  `equity_curve`, `r_histogram`, `tp_outcome`), trades.csv read back by
  `analytics/records.py` (`TradeRecord`); new `confluence` column in trades.csv
  (`Order.confluence` → `TradeResult.confluence`) and `created` in summary.json; chart
  focus `/?symbol=…&from=…&to=…&t0=…&t1=…` in `pages/chart.py` + `chart.js` `focus`.
  Tests: `tests/analytics/test_metrics.py`, `tests/ui/test_results_page.py`.
  Check (choices made while building):
  - Every number is computed from trades.csv with `analytics/metrics.py` (so the symbol
    filter and older runs work); summary.json gets the same new metrics for new runs.
  - Expectancy = average net R per trade (so it equals "avg realized R (net)"); average
    win / loss and profit factor on net R; profit factor "—" without a loss.
  - Losing streak: losses in a row by exit time; a break-even ends a streak.
  - **Max drawdown changed (3.4 metric):** trades closing at the same time (same candle)
    now count as one step, as on the equity curve (their order inside a candle is
    unknown). The run 2026-09-02..30 (3 symbols) is unchanged (49.97 R).
  - Equity curve: net (blue area) and gross (dashed grey) on the top pane, net drawdown
    shaded red in a pane below; x = exit time, starts at 0 at the first entry.
  - Performance tab: TradingView-style table All / Long / Short, then the six split
    tables (two per row) and the R histogram (Plotly, net R, 0.25 R bins).
  - TP outcome groups: "TP1 + TP2", "TP1, rest out" (rest at break-even / SL / end of
    data), "TP (one target)", "no TP". Tag groups: "last 1.5h" / "other". Runs written
    before the confluence column take it from the reason text.
  - Trade list: sorted by the arrows in the header (dash DataTable, still built into Dash
    but marked deprecated; no new dependency). Click a row → the chart opens on that
    symbol with the days from entry to exit, Trades overlay + "trade confluences" on,
    scrolled to the trade (60 candles before, 30 after), on the current timeframe. The
    session view (3.5) isn't built, so no session is selected yet.
- ☐ **3.7 Cross-check with the manual backtest.** Run the same XAUUSD period as the
  user's manual R log and compare trade by trade. Every difference is either a code bug or
  an unclear spec rule. Clarify with the user, don't guess.

## Phase 4: Settings menu

**UI layout** (user, 2026-10-08; inspiration: TradingView's top toolbar, screenshot in the
chat). One top bar, left to right: **symbol selector** (top left, dropdown with search),
**timeframe buttons** (1m 5m 30m 1h 4h …), then small clean **icon buttons**, each opening a
popover / dropdown: **chart settings** (overlays switch + types panel, colors), **strategy**
(select the strategy, only strategy 1 for now; its settings, 4.1), **replay** (like
TradingView's replay: play, step, speed, select date), **backtest** (symbols: one or several
at once, date range, settings preset, Run button with progress). Date range: nicer than now,
a calendar popover plus quick ranges (1M, 3M, 6M, YTD, 1Y, all) like TradingView's bottom
bar. Light theme like the screenshot. After a run the results page (3.6) opens.

- ☑ **4.0a Chart engine: TradingView Lightweight Charts** (user, 2026-10-08: the Plotly
  chart is too slow). First measure where the time goes (detectors, strategy run, figure
  building, sending the figure, drawing in the browser). Then, in sub-steps, each checked
  by the user on the chart:
  1. ☑ Overlays output neutral drawing objects (box, line, marker, label, with color and
     hover text) instead of Plotly traces, so the chart library can be swapped.
  2. ☑ Candles, volume-free, session lines, zoom / pan / price axis with Lightweight Charts
     (library file served locally from `ui/assets/`, no CDN), TradingView look.
  3. ☑ Boxes (zones, FVG, OB, BPR, session zones, position boxes) as one custom primitive;
     lines and markers with the library's own tools; all overlays and the hover texts.
  4. ☑ Replay in the browser: the cursor step only adds the next candle and the drawings
     that exist by then, instead of rebuilding the whole figure on the server.
  No lookahead rule unchanged: the browser only ever gets data up to the replay cursor.
  Measured (2026-10-08, XAUUSD M5, 2026-09-21..25 = 1,104 candles, all overlays and
  sub-entries on): detectors 50 ms, Trades (strategy + engine over the whole cached block)
  ~0.9 s, both once per range; full chart: drawing 12 ms, Plotly figure 160 ms, JSON 36 ms,
  1.48 MB sent (0.14 MB gzipped; Dash sends it uncompressed), FVG 409 kB and BPR 205 kB
  the largest. One replay step: ~90 ms on the server (figure 65 ms, of it candles only
  35 ms), 0.8 MB sent per step. Most server time is Plotly building and validating trace
  objects. Drawing in the browser was not measured.
  Step 1 built: `ui/drawing.py` (Box, Line, Marker, Label, Hover, Badge; x = chart candle
  position, y = price, "\n" line breaks), `ui/plotly_render.py` (`to_plotly`, called in
  `build_candle_figure`; lanes for stacked fills and hover points moved there),
  `overlays.overlay_drawings`; tests in `tests/ui/test_plotly_render.py`, the overlay tests
  check the converted traces (`tests/ui/plotly_helpers.py`). Same figure as before for 32
  cases (3 symbols, M5 / M30 / H1, full chart and replay).
  **Parts 2-4 built (2026-10-08, confirmed by the user):** Lightweight Charts 5.2.1
  (`ui/assets/lightweight-charts-5.2.1.standalone.production.js`, Apache 2.0, license in
  `ui/assets/LICENSE-lightweight-charts.txt`, TradingView logo on), `ui/assets/chart.js`
  (chart created once; candles, session lines, legend, trend badges, one primitive for
  boxes / lines / markers / labels, hover tooltip, replay deltas), `ui/chart_data.py`
  (candle, drawing and delta payloads cut at the cursor; drawings redrawn per group of
  events, `OverlayType.group`), `ui/chart_config.py` (config, no Plotly). The Plotly chart
  and `ui/plotly_render.py` are removed; overlay tests check the drawing objects
  (`tests/ui/overlay_helpers.py`), `tests/ui/test_chart_data.py` checks the payloads: no
  candle, drawing, end or time after the cursor in any full payload or delta, and deltas
  (forward, back, jumps) add up to the full payload at every cursor of a scenario day.
  Measured the same way as part 1 (XAUUSD M5 21-25 Sep, all overlays; GBPJPY the same):

  | | before (Plotly) | after |
  |---|---|---|
  | open the week in the browser, chart drawn | ~1.8 s (1.5 MB) | candles 0.14 s, overlays 0.22 s (0.68 MB); new range with cold detectors 0.3 / 0.4 s |
  | one replay step | ~1.0 s, 1.09 MB | click -> applied 25-31 ms, drawn the next frame (<= 16 ms later; 70 ms with two frames waited); 1.6 kB (max 3.2) |
  | server per replay step | ~90 ms (figure) | 1 ms on a week, 3 ms on a month |
  | one month (5,514 candles), all overlays | tab crashed (headless Chrome) | candles 0.21 s, overlays 1.2 s (3.3 MB); zoom / pan at 60 fps (95% of frames <= 17 ms) |

  The first Trades load of a range is the slow part (strategy + engine over the cached
  block, ~1 s): overlays appear after the candles.
  Check (choices made while building, TradingView style):
  - ★ ✕ ▼ ▲ markers are drawn by our primitive at their price (the library's series
    markers only have circle / square / arrows above / below a bar).
  - Markers and labels are hidden while candles are narrower than 3 px (unreadable there,
    and it keeps a fully zoomed-out month smooth).
  - Hover: the nearest hover area or marker within 20 px; a zone shows its text anywhere
    along its middle (Plotly only near the box's ends). Candle OHLC + spread are in the
    legend top-left (TradingView style) instead of a tooltip.
  - Session labels at the bottom of the chart (the legend is top-left); grid off as before.
  - Drawing order inside an overlay: fills, outlines, lines, markers, labels.
  - Outside replay the whole range is shown (as before); time axis labels are the
    library's (UTC).
- ☑ **4.0 Top toolbar** as described above, replacing the current controls (no new
  features: the existing chart settings, overlays and replay move into the popovers;
  the backtest button is wired once 3.4 exists).
  Built (2026-10-08, confirmed by the user): `pages/chart.py` layout (top bar: symbol
  dropdown with search, timeframe buttons, icon buttons with popovers for chart settings,
  strategy, replay on/off and backtest; replay bar floating at the bottom of the chart;
  bottom bar: quick ranges, calendar, messages, UTC), `assets/toolbar.css` (icons as inline
  SVG), `assets/toolbar.js` (popovers close on a click outside or Escape), backtest via
  `runner.start_run` in the background with a progress bar, then `/results/<run id>`
  (`pages/results.py`: summary table, notes, files, raw summary.json; placeholder until
  3.6), page routing in `ui/app.py`; tests in `tests/ui/test_toolbar.py`. No new
  dependency.
  Check (choices made while building):
  - Quick ranges end on the last cached day and stop at a missing day (a range over it
    can't be shown); "All" = the latest run of consecutive cached days.
  - Timeframe buttons only for the timeframes the data layer supports (no D button yet).
  - The backtest starts with the chart's symbol and days; when it finishes the results page
    opens in the same tab ("← Chart" goes back; symbol and timeframe are remembered).
  - Strategy popover: one entry (strategy 1); it doesn't change anything yet (4.1).
  - Escape first closes an open menu or calendar inside a popover, then the popover.

- ☑ **4.1** Settings page generated from the config dataclasses (strategy, detectors,
  session filters, costs), with defaults from the spec.
  Must include (user's wish): the session zone kill rule as its own setting: on/off, and the
  number of breaks that kills a zone (`SessionZoneSweepConfig.zone_kill_breaks`, default 3).
  Also (user's wish): step 3 with the 5m trend on/off (`entry_bos_with_trend`, default off).
  Built (2026-10-08, confirmed by the user 2026-10-09): `backtester/settings.py` (`leaves`: every
  value of `RunSettings` with its path, kind, spec default and help text from its source
  comment; `form_values` / `settings_from_values`, `to_json` / `from_json`,
  `SettingsError` naming the field), `ui/settings_panel.py` (modal: groups Entry,
  Confluences, Stop loss, Take profit, Session zones, Sessions & filters, Detectors, Costs,
  plus Backtest for the warm-up days; per field label, help, input, ↺ reset, a blue dot
  when it differs from the default; "Reset all to defaults"), opened by "Settings…" in the
  strategy popover (`assets/toolbar.js` `data-modal`, styles in `toolbar.css`). New
  setting `SessionZoneSweepConfig.zone_kill` (on/off; spec updated). The Trades overlay
  (`OverlaySettings.strategy`, `OverlayType.strategy_settings`) and the backtest use the
  current settings. Tests: `tests/test_settings.py`, `tests/ui/test_settings_panel.py`,
  `tests/ui/test_trades_overlay.py`, `tests/strategy/session_zone_sweep/test_zones.py`.
  Check (choices made while building):
  - Changes apply at once when valid (no OK / Cancel), kept in the browser (local
    storage), so they survive a reload. An invalid value is shown in the status line and
    not applied (the last valid settings stay in use).
  - Not shown: `strategy.strong_move.atr_mult` (nothing reads it; the strong-move
    multipliers are per FVG / OB) and the engine's session starts (they always follow the
    strategy's session starts, one setting for both).
  - Entry confluence types offer FVG / OB / BPR only (breakers were added in 8.2.3, the
    equilibrium has its own switch); timeframes only those the data layer supports.
  - Help texts are the source comments (some improved); labels are set in
    `settings_panel.py` (new fields fall back to their name).
  - The chart settings popover's FVG / OB strong-move switches stay as they were: they
    only change the FVG / OB / BPR drawing overlays. The strategy's own switches are in
    the panel (Detectors). Unifying them belongs to 4.3.
  - A settings change makes the Trades overlay run again (~1 s per range); the other
    overlays stay cached.
- ☑ **4.2** Save / load named settings presets (JSON in `results/presets/`); every
  backtest run stores the exact settings it used.
  Built (2026-10-09, confirmed by the user): `backtester/presets.py` (one JSON file per
  preset in `results/presets/`: name + settings; `list_presets`, `load_preset`,
  `save_preset`, `rename_preset`, `delete_preset`); preset bar at the top of the settings
  panel (dropdown, Save, Revert, name field, Save as, Rename, Delete) and a "Settings
  preset" dropdown in the backtest popover (`ui/settings_panel.py`); `settings.json` of a
  run gets `preset`; command `python -m backtester.run … --preset NAME`. Tests:
  `tests/test_presets.py`, `tests/ui/test_settings_panel.py`, `tests/test_runner.py`.
  Check (choices made while building):
  - "Default" is not a file: always the spec defaults; it can't be saved over, renamed or
    deleted ("Save as" makes a new preset from it).
  - Picking a preset (in the panel or the backtest popover, they are the same choice)
    loads its settings at once; later changes mark it "(modified)" until "Save"; "Revert"
    loads the saved settings again. Deleting a preset loads Default.
  - A run records "<name>" or "<name> (modified)" when its settings differ from the
    saved preset; the exact settings are always in settings.json.
  - Names: 1-60 letters, digits, spaces, `_ - . ( ) +`; "Tight SL" and "tight sl" are the
    same preset (Windows file names), the first spelling is kept.
  - With `--preset`, `--warmup-days` defaults to the preset's warm-up.
  Fixed on the way: picking an option in a dropdown inside a toolbar popover closed the
  popover (the option leaves the page before the click arrives; `toolbar.js`), and the
  backtest popover showed "Pick one or more symbols…" right after loading the page (Dash
  ran the Run callback with 0 clicks when the page was built).
- ☐ **4.3 UI layout and look review** (at the end of the UI work; the user decides the
  details then). Known wishes so far: the strong-move filter switches (FVG, OB) become a
  dropdown; the overall layout of the controls; chart colors and other visual details.
  Until then the current layout and colors stay as they are.

- ☑ **4.0b Chart improvements** (user, 2026-10-08), TradingView look and behaviour:
  1. **Keep the position when switching timeframe:** the time at the centre of the view
     stays at the centre and the number of visible candles stays the same (5m 2026-09-12
     12:15 in the middle → on 30m the candle containing 12:15 in the middle). Cached days
     needed by the new timeframe (D, W) are loaded automatically. Replay keeps its time
     as now.
  2. **1D and 1W timeframes**, resampled from M1 (bid). Day = 17:00 New York to 17:00
     New York (DST-aware), week = Sunday 17:00 NY open to Friday 17:00 NY close, like
     TradingView for forex / gold; setting (option: UTC midnight). Intraday timeframes
     (incl. 4H, used by the overall trend) unchanged. No session lines on D / W.
  3. **Screenshot button** (top right): PNG of the chart as shown, with a stamp in the
     corner (symbol, timeframe, first → last visible candle in UTC, replay time if on,
     overlays on, preset) and the same data in a Windows-safe file name, e.g.
     `GBPJPY_M5_2026-09-12T0800_2026-09-12T1630_UTC_replay-1215.png`; also copy to
     clipboard. Purpose: the user sends screenshots for trade reviews and the stamp says
     exactly where on the chart they are.
  4. **Go to date / time** (like TradingView's Alt+G): enter a UTC time, the chart loads
     that day if needed and centres on that candle.
  5. **Box zoom** (like Plotly): zoom tool in the toolbar; drag a rectangle → zoom to that
     time and price range; reset zoom / double-click goes back; double-click on the price
     axis = auto-scale again. No clash with picking the replay start or normal panning.
  Built (2026-10-09, confirmed by the user on the chart):
  - **Part 1:** `chart.js` `viewNow` / `showView` (centre time + candle count kept when only
    the timeframe changes, outside replay; price axis back to auto-scale), the browser
    reports its view in the store `chart-viewport`; `pages/chart.py` `dates_for_view`
    (days the new view needs) and the `_timeframe_days` callback; tests in
    `tests/ui/test_timeframe_switch.py`. Check: the needed days are added to the shown
    range plus `ChartConfig.switch_warmup_candles` (100) candles on the left for the
    overlays, within the run of cached days around the centre; when that would exceed
    `max_candles` (e.g. a month on 1m) only the days the view needs are kept. The centre
    lands on the candle containing the centre time (5m 12:15 → the 30m 12:00 candle).
    Also fixed: the selected timeframe button turned purple after a click (Dash 4 style).
  - **Part 2:** `Timeframe.W1`; `data/resample.py` (`DayBoundary`: 17:00 New York, the
    default, or UTC midnight; `candle_close`, `calendar_label`), `CacheAdapter.fetch_frame`
    (`boundary`; D / W read the cached days around the range), D and W buttons, "Daily /
    weekly candles" in the chart settings popover (`ChartConfig.day_boundary`); tests in
    `tests/data/test_resample.py` (DST start week 2026-03-08, DST end week 2026-11-01,
    weekend, UTC option), `tests/data/test_cache_adapter.py`,
    `tests/ui/test_daily_weekly_chart.py`. Check:
    - A D / W candle's `ts` is its close minus 1 / 7 days (so "closed at ts + duration"
      stays exact on DST days); on the chart it is named by its trading day (D) or the
      Monday of its week (W), like TradingView.
    - A D / W candle belongs to the range when it closes in it, and is only shown when
      every UTC day it covers is cached: with the cache starting 2026-09-02, the first D
      candle is 09-03 (09-02's day opened 09-01 21:00) and W shows the weeks of 09-07,
      09-14 and 09-21 (the week of 09-28 closes 10-02, after the cached days).
    - UTC option: days 00:00-24:00 UTC (Sunday evening is its own small candle), weeks
      Sunday 00:00 to Sunday 00:00 UTC.
    - Overlays run on D / W like on other timeframes (session zones stay on 5m-30m).
    - A switch to D / W from a view wider than the D / W candles available shows all of
      them (instead of keeping an empty, huge candle count).
    - D and W can also be chosen for the strategy's timeframe settings (4.1) now.
  - **Part 3:** camera button top right (`shot-save`: saves the PNG at once) and "▾" with
    "Download PNG" / "Copy to clipboard" (`pages/chart.py`, `chart.js` `shot`,
    `shotCanvas`, icon in `toolbar.css`). Check:
    - The picture is the library's `takeScreenshot` (candles, axes, every drawing and the
      session lines are in its canvas) with the legend, the trend badges and the stamp
      drawn on top; the hover tooltip and the crosshair are not in it.
    - Stamp (bottom left, above the time axis) and file name: first and last visible
      candle by their open time (D / W: their day), "replay at" = the replay time (close
      of the cursor candle, as in the replay message), overlays = the ticked types while
      the Overlays switch is on, preset = the current preset, "(modified)" when changed.
      Example: `GBPJPY_M5_2026-09-23T1935_2026-09-24T0530_UTC_replay-0535.png`.
    - Copy works in Chrome / Edge on 127.0.0.1; if the browser refuses, the menu says so.
  - **Part 4:** "Go to" field in the bottom bar, Alt+G focuses it (`pages/chart.py`
    `parse_goto`, `goto_dates`, `_goto`; `chart.js` `goto`; `toolbar.js`); tests in
    `tests/ui/test_goto.py`. Check:
    - Accepts `2026-09-12 12:15`, `2026-09-12T12:15` (the stamp's format), or a day
      (= 00:00), UTC; Enter goes there.
    - A day outside the shown ones: as many days as shown now, centred on it, within the
      run of cached days and the candle limit. The chart centres on the candle containing
      the time, keeps the zoom (or shows 120 candles when more than 500 were visible) and
      puts the crosshair on it, so the legend shows that candle.
    - In replay: only times up to the replay time, and no other days are loaded.
  - **Part 5:** zoom and reset-zoom buttons in the top bar (`chart.js` box zoom,
    `chart.css`). Check:
    - Zoom on: a transparent layer over the chart pane takes the mouse (no panning, no
      candle clicks for the replay start while it is on); drag a rectangle → that time
      and price range (price axis manual), then the tool turns off. Drags under 6 px are
      ignored. Escape turns the tool off.
    - Reset zoom or a double-click on the chart goes back one zoom (several zooms: one
      step each); with none left it shows the whole range with auto-scale. A
      double-click on the price axis auto-scales (the library's own, like TradingView).
    - New candles (symbol, timeframe, days, replay on / off) forget the zoom steps and
      switch the price axis back to auto-scale.
    - In replay a box zoom keeps its price range on the following steps (until a
      double-click / reset), like a manually scaled price axis on TradingView.

## Phase 5: Risk & FTMO simulation

`docs/risk-management.md` (rewritten 2026-10-10): sizer, account simulator, Monte Carlo,
sweep, and the Risk page. Input is an R trade list (a backtest run or the user's manual R
log); nothing here re-runs detection. One strategy per run. The prop-firm field (FTMO
phases, limits, pass probability; `risk-management.md › Prop-firm field`) comes later and
has no step yet.

- ☐ **5.1 RiskConfig + PositionSizer.** `risk/config.py` (`RiskConfig`: starting balance
  100,000, risk per trade 1% of the current balance, per-symbol contract specs: value per
  point, lot step, minimum lot; costs per symbol: spread, commission, swap, slippage),
  `risk/sizer.py` (`PositionSizer`). Lots = risk $ ÷ (SL distance incl. costs × value per
  point), rounded down to the lot step. Several TPs: each part rounded down, the
  **remainder goes to TP1**; too small for all parts (< parts × minimum lot) → **fewer
  TPs** (later TPs dropped, the last remaining one closes the rest); below one minimum lot
  → skipped, "too small". The trade's R is recalculated from the lots actually used per
  part. Spec: `risk-management.md › Account & sizing`, › Costs. Tests: hand-built cases
  for rounding, remainder to TP1, 3 → 2 → 1 TPs, too small.
- ☐ **5.2 AccountSimulator.** `risk/account_sim.py`: replays the R trades in time order,
  candle by candle, no lookahead. Balance (closed trades) and equity incl. floating P/L
  at each candle's worst point; costs (spread, commission, swap per night, slippage on
  entries and SL hits); **personal daily stop** −2% of the day's starting balance, closed
  + floating, day = midnight `Europe/Prague`, no new entries after it; **max open risk** 2%
  (a trade counts full risk until its SL is at break-even, then 0) with **correlation
  groups** (GBPJPY + GBPUSD on, NAS100 + US500 off); **drawdown scaling** (equity ≥ 4%
  below its high → risk × 0.5, back as soon as it is less than 4% below). Skipped trades
  listed with their reason. Output per `risk-management.md › Account simulator`
  (equity / balance curve, return %, max drawdown % and $, longest drawdown, worst day,
  per month, …). Needs the candles between entry and exit (floating P/L), read through
  the cache, not stored in the trade list.
- ☐ **5.3 Monte Carlo.** `risk/monte_carlo.py`: reshuffles the order of **whole trading
  days** (⚙ 1,000 runs, seeded) and runs the AccountSimulator with the same settings on
  each. Output: distribution of max drawdown and final balance (e.g. "95% of runs stay
  below X% drawdown"), a fan of equity curves. Spec: `risk-management.md › Monte Carlo`.
- ☐ **5.4 Risk sweep.** `risk/sweep.py`: grid over risk per trade (e.g. 0.25–1.5%), daily
  stop (1–3%), max open risk, drawdown-scaling threshold and factor; per cell max drawdown,
  return, Monte Carlo 95% drawdown. Spec: `risk-management.md › Risk sweep`.
- ☐ **5.5 Risk page in the UI.** Dash page "Risk" (`risk-management.md › UI page`). Left
  panel: trade source (a backtest run or the manual R log), starting balance, risk, costs
  per symbol, daily stop, max open risk + correlation groups, drawdown scaling, Monte
  Carlo runs. Main panel: equity curve with drawdown below, key numbers, skipped trades
  with reasons, Monte Carlo fan + drawdown distribution, sweep heatmap. Visual step: the
  user checks it in the app.
- ☐ **5.6 Prop-firm field** (user, 2026-10-12, possible addition, after 5.5): presets for several prop firms, not only FTMO (rules editable), so that after a backtest the probability of passing any of them can be estimated (`risk-management.md` › Prop-firm field, `risk/prop_rules.py`). To be specified with the user before building.

## Phase 6: Robustness (before trusting any result)

- ☐ **6.1 Strategy Simulator** (user, 2026-10-12; replaces "parameter sweeps"; must be done before Phase 7). Automatic backtests over many settings of one strategy instead of making every preset by hand. Sub-steps, each test-first:
  1. The user marks which settings take part (per strategy) and gives values or ranges; the settings come from the strategy's config (universal settings the same for all strategies, extra ones per strategy).
  2. A runner builds the grid (random search for big grids), runs the backtests in parallel (reusing `runner.py`) and writes every result to `results/sim/<id>/` (resumable; may take hours).
  3. Ranking by **max net R** (user), with a minimum trade count against lucky settings; other metrics shown next to it.
  4. Overfitting guard (user: yes): tune on one period, report the best settings on a later, untouched period (see 6.2); the number of variants tried is stored (`backtest-evaluation-research` skill).
  5. The best settings are saved as a preset (`results/presets/`) and shown after the run.
  6. Settings of a Simulator result can be loaded on the chart (Trades overlay) to check them visually.
  Open: sweep settings join only after the sweep rework (`confluences.md` › Liquidity sweep).
- ☐ **6.2** In-sample / out-of-sample split: tune settings on one period, judge them only on
  a later period the tuning never saw. Walk-forward later.
- ☑ **6.3** Results per year / per quarter, to see if the edge is stable or one lucky period.
  **Speed with years of data (2026-10-09, confirmed by the user).** Before: a backtest
  slowed down the longer it ran (1 month 4 s, 6 months 48 s; the full history would have
  taken hours). Found by profiling, changed without changing any result:
  - `detectors/zone.py` `ZoneBook`: zones nobody revisits stay open for good and were
    checked on every candle. Now the untapped zones are kept sorted by their near edge and
    a candle only checks those it reaches, plus the tapped ones, in the same order.
  - `strategy/session_zone_sweep/journal.py`: only the confluence records not ended yet
    are looked at per candle (all were); `signals.py`: the equilibria are only filtered
    after a transition (was every candle).
  - `data/cache.py` `read_cached_days` (then in `dukascopy.py`): the day files of a range are read in one go
    (pyarrow dataset), 9x faster than one by one (2,464 files: 7.2 s → 0.8 s).
  - Found on the way: the order of confluences inside a session record in sessions.json
    changed from run to run (same content; FVG and BPR made by the same candle came from
    a set). Now sorted by kind and edges as a tie-break, the same on every run.
  Proof: `tests/test_speed_same_results.py` (the old check-every-zone book against the new
  one on random candles, and strategy 1 + engine over three weeks of seeded random-walk
  candles with both: identical trades and session records); on the real cache, all three
  symbols 2026-06..07: trades.csv byte-identical to before, sessions.json the same content
  (and now identical between runs); candles from the new reader identical to the old
  (5m, 4h, D, XAUUSD and GBPJPY). Now: 6 months 10.6 s, **full history XAUUSD 4 min 41 s**
  (one process; the symbols run in parallel).
  Chart with years cached (`tests/ui/test_long_history.py`):
  - The chart opens on the last month ("1M"), no longer on the whole run of cached days.
  - A range far over the candle limit (estimated from the cached weekdays, > 1.5 x
    `max_candles`, e.g. "All" on 5m ≈ 500,000) is refused at once with the message to pick a
    shorter range or 4h / D; closer to the limit it is read and checked exactly as before.
    4h / D over all 6.7 years: about 5 s on the server (13 s in the browser), no freeze.
  - Trades overlay: runs from the 1st of the month before the shown range's month to a
    week after it (`trades_overlay.run_window`; was the whole run of cached days = 6.7 years
    ≈ 5 min). Every range starting in the same month shows the same trades; ranges in
    different months can differ slightly at their start (setups and levels from before the
    anchor are not known). Ranges longer than 183 days (`ChartConfig.trades_max_days`) show
    a message instead (the strategy runs about 40 s per year of 5m candles).
  **Results per year / quarter (built 2026-10-09, confirmed by the user):**
  `analytics/metrics.py` `by_period` (`by_year`, `by_quarter`: per period the summary of
  all symbols and of each), results page Performance tab "Per year" and (collapsible)
  "Per quarter" tables (trades, win rate, net R, max drawdown in R; all symbols and each
  symbol; one symbol when the filter shows one), `python -m backtester.run` prints the
  per-year table too; trade list virtualized (17,747 rows: 25 s → 1.6 s to open). Tests in
  `tests/analytics/test_metrics.py`, `tests/ui/test_results_page.py`, `tests/test_runner.py`.
  Check: a trade belongs to the period it was entered in (UTC); a period's max drawdown
  counts only its own trades, starting at 0.
  **First full run** (`python -m backtester.run XAUUSD GBPUSD GBPJPY --start 2020-01-01
  --end 2026-09-30 --preset Default`, `results/20261009-084815_XAUUSD-GBPUSD-GBPJPY`;
  2020-01-01 isn't cached): 17,747 trades, win rate 34.5%, **net R −3,022.9 (gross
  −895.1)**, max drawdown 3,027.5 R, profit factor 0.74, average R:R planned 1.76.

  | year | all: trades / win / net R / max DD | XAUUSD | GBPUSD | GBPJPY |
  |---|---|---|---|---|
  | 2020 | 2,718 / 35.7% / −366.2 / 374.3 | 909 / 35.1% / −121.4 / 129.7 | 875 / 35.0% / −104.1 / 108.3 | 934 / 36.9% / −140.7 / 150.6 |
  | 2021 | 2,649 / 35.5% / −433.9 / 435.6 | 844 / 35.8% / −129.5 / 131.3 | 870 / 35.1% / −114.9 / 115.2 | 935 / 35.6% / −189.4 / 193.9 |
  | 2022 | 2,707 / 32.8% / −553.2 / 565.5 | 868 / 33.5% / −180.7 / 193.1 | 888 / 32.5% / −174.9 / 179.5 | 951 / 32.3% / −197.6 / 197.6 |
  | 2023 | 2,400 / 34.8% / −427.8 / 433.6 | 792 / 34.3% / −179.5 / 179.5 | 805 / 34.2% / −131.5 / 142.9 | 803 / 35.9% / −116.8 / 140.8 |
  | 2024 | 2,571 / 35.0% / −444.1 / 451.4 | 826 / 35.5% / −117.9 / 120.9 | 840 / 34.6% / −151.6 / 154.2 | 905 / 35.0% / −174.7 / 183.5 |
  | 2025 | 2,672 / 33.8% / −436.7 / 445.3 | 826 / 34.6% / −92.7 / 92.7 | 858 / 34.8% / −111.6 / 123.5 | 988 / 32.2% / −232.4 / 241.6 |
  | 2026 (to 09-30) | 2,025 / 34.7% / −288.4 / 296.4 | 659 / 34.4% / −35.3 / 45.7 | 685 / 33.3% / −125.6 / 134.9 | 681 / 36.3% / −127.5 / 134.4 |

  Every year and every symbol is negative, also before costs (gross −0.05 R per trade,
  net −0.17 R). Caveats from the data check above: 2023-02..07 has many missing hours;
  gold's doji threshold makes 3-5 times more dojis before 2025.
  **The table is the re-run after the time-zone fix**
  (`results/20261009-135418_XAUUSD-GBPUSD-GBPJPY`, 7.5 min): 17,742 trades, win rate
  34.6%, net R −2,950.4 (gross −825.3), max drawdown 2,955 R, profit factor 0.75. The
  first run (above, before the fix) differs little: the ~3 shifted weeks a year.
- ☑ **6.4 Robustness report** (knowledge base T-01; user, 2026-10-14). **Built 2026-10-14, waiting for the
  user's check.** `analytics/robustness.py` (pure functions on trade lists and grids, config
  `RobustnessConfig`, defaults Kaufman's, accepted by the user): share of profitable variants and
  `robust` at >= 70 %, mean / sample st.dev / mean − 1 sd of net R over a grid, neighbour-smoothed
  series / grid and the plateau variant, Welch's t of the trade R of the halves 2020-22 / 2023-26
  (`|t| >= 2` = they differ), kurtosis of the daily R (days with a closing trade; normal 3, flag > 7),
  net R without the best trade, stressed net R (each trade's cost `r_gross − r_net`, spread +
  commission + swap, × 1.5; swap income not scaled; no re-run), shock days (true range of a daily bar
  > 3.5 × the mean true range of the 10 days before; trades belong to the UTC date they exit on;
  more than half of the shock days with a closing trade profitable = risk understated). Used by
  `python -m backtester.tools.trend_grid`: new `robustness.csv` (variant × symbol group) and `grid.csv`
  (per signal × timeframe family and over all variants), a printed family table, and `--no-shocks`.
  Tests: `tests/analytics/test_robustness.py`, `tests/tools/test_trend_grid.py`. The Strategy
  Simulator (6.1) reuses the functions. Check: `python -m backtester.tools.trend_grid --symbols
  XAUUSD NAS100 --timeframes D1 H4 --signals breakout sma --out results/trend_check2` and look at
  `grid.csv` / the family table.
- ☑ **6.5 R split by time** (knowledge base I-22; user, 2026-10-14). **Built 2026-10-14, waiting for the
  user's check.** `analytics/metrics.py`: four new split keys, listed with the others on the results page
  (Performance tab) and usable in `split` / `by_period`; time groups are listed in time order: **Hour
  (UTC)** of the entry ("08:00 UTC"), **Weekday** ("1 Mon" … "7 Sun", Friday is its own row), **Month
  part** (first 3 / last 3 weekdays of the entry month, no holiday calendar; "mid" otherwise; the first
  part wins where they overlap), **NY window** (New York time of the entry, DST by city: Open 9:30-11:00,
  Midday 11:00-15:00, Close 15:00-16:00, else "Outside cash hours"; the window times are the Aziz
  windows, constants `NY_WINDOWS`). Tests: `tests/analytics/test_time_splits.py`. Check: open a run
  on the results page and look at the four new tables under Performance.
- ☑ **6.6 MT5 history check** (user, 2026-10-14): how many years of M1 with tick volume and spread FTMO's
  MT5 serves. **First check 2026-10-14** (read-only, FTMO-Demo): the terminal's "Max bars in chart" is
  100,000, so only ~3.5 months of M1 come back (2026-07-06 .. 2026-10-14); every bar has tick volume and
  spread. The user raises the limit (MT5 › Tools › Options › Charts › Max bars in chart = Unlimited,
  restart), then check again. Median spreads of those 3.5 months against our fixed `SymbolCosts.spread`
  (+ slippage): XAUUSD 0.42 (0.25 + 0.10), GBPUSD 0.2 pip (0.3 + 0.2), GBPJPY 1.6 pip (1.0 + 0.3),
  US100.cash 1.45 (NAS100 1.0 + 1.0), US500.cash 0.60 (0.5 + 0.25). Spreads are nearly flat over the day
  except the server-midnight bar (17:00 New York rollover: GBPUSD ~6.7 pip, GBPJPY ~21 pip) and slightly
  higher gold spreads in Asia. Changing the defaults is the user's call.
  **Second check 2026-10-15 (after the setting was fixed):** `common.ini` still had `MaxBars=100000` (the
  user's change had not been saved); Claude set it to 2147483647 (backup `common.ini.bak-2026-10-15` next to
  it), closed MT5 gracefully and started it again (user: "do this yourself"). The terminal now reports
  `maxbars` 100,000,000 and serves M1 with tick volume > 0 on every bar and a spread per bar: XAUUSD from
  2015-05 (median spread 22 points), GBPUSD from 2015-11 (6), GBPJPY from 2016-01 (16), US100.cash and
  US500.cash from 2017-12 (145 / 46); the FX and gold requests were capped at 4,000,000 bars, so they may
  reach further back. Not yet exported or compared with the histdata cache; the spread over the years is a
  historical server value and differs from today's (gold median 0.22 over the years against 0.42 in the last
  3.5 months): the spread table (6.7) must be built per year as well as per hour.
- ☑ **6.7 Spread by year and hour of day in the cost model** (user, 2026-10-14). **Built and run 2026-10-15,
  waiting for the user's check; off by default.** `engine/spread_table.py` (`SpreadTable`: spread per symbol,
  New York year and New York clock hour, nearest year with the hour, later year on a tie, None -> fixed
  spread), `CostConfig.spread_table` (None = the fixed `SymbolCosts.spread`; `spread`, `spread_r`,
  `break_even_offset`, `too_expensive` take the time; the engine passes the entry candle's close time, so one
  spread of the entry time is charged for the round trip as before), hidden in the settings menu but kept in
  the settings JSON (`runner.jsonable`, `settings._convert`), `python -m backtester.tools.spread_table`
  (reads the running terminal's M1 history, writes `data/spreads/ftmo_spread_median.json`, `..._p90.json`,
  `coverage.csv`; git-ignored data, 40 KB) and `trend_grid --spread-table PATH`. Tests:
  `tests/engine/test_spread_table.py`, `tests/tools/test_spread_table_tool.py`, `tests/test_settings.py`,
  `tests/tools/test_trend_grid.py`. Not done: a news mark-up (no calendar), exit-time spread for shorts.
  **Result (FTMO demo M1 2015-2026; server clock NY + 7 h, 920 of 948 weeks):**
  - **The spread moved over the years more than over the day.** Median over NY 9-15, price units: XAUUSD
    0.42 (2015) .. 0.15 (2020) .. 0.07 (2021) .. 0.07 (2023) .. 0.16 (2024) .. 0.23 (2025) .. 0.42 (2026), fixed
    model 0.25. NAS100 0.6 (2021-22) .. 0.7-1.45 (2023-26), fixed 1.0 (all hours 1.4-1.6 since 2023). US500 0.28-0.55,
    fixed 0.5. GBPJPY 0.005-0.008 (2020-23) .. 0.012-0.016 (2024-26), fixed 0.010. GBPUSD 2e-5 .. 6e-5
    (2022-26), fixed 3e-5.
  - **Suspicious old years:** GBPUSD 2020-21 has a median of 5 pips at all hours (0.0005) and GBPJPY
    2015-17 and 2019 3.5 pips: probably how the old bars were recorded, not real trading costs. Treat
    values before 2022 with care; the table is better trusted for 2022-26.
  - **Hour of day (2026):** FX flat within about 15 % apart from the rollover hour NY 17 (GBPUSD 6.4 pip,
    GBPJPY 20 pip against 0.2 / 1.4 pip by day); gold 0.40-0.48 all day (0.52 at 18:00); NAS100 1.45 in the
    cash session and 1.6-1.85 outside; US500 0.55-0.60. In 2024 the indices were much tighter in the US
    session (NAS100 0.8 against 2.2 at night). The 90th percentile is 1.0-1.1 x the median for the
    indices, 1.3-1.5 x for gold / GBPJPY, 2 x for GBPUSD.
  - **Effect on a run** (strategy 4 breakout 20, M15, 2023-26, XAUUSD / NAS100 / US500 / GBPJPY, 8,899
    trades, gross unchanged): net R −451 with the fixed spread, −545 with the table (XAUUSD +19, NAS100
    −19, US500 −4, GBPJPY −90).
  - **Decisions for the user:** (1) use the table by default (changes the net R of every strategy), or
    keep it as an option; (2) trust the years before 2022, or start the table in 2022 and use the
    fixed spread before.

## Phase 7: Live trading via MT5 (much later; not before 6.1 is done)

Demo account first, then FTMO. Same strategy code, fed by closed candles only.
`live/` module (execution part) with `order_send`, a kill switch, the FTMO limits from `risk/`
enforced before every order, and a log of every decision. Not before Phases 3–6 show a
stable edge.

User's wishes (2026-10-09), to be specified before building (open questions: MT5 server
name, FTMO symbol names, risk per trade on demo, demo lock / daily stop / emergency stop,
fully automatic vs. signal mode, two TPs as two half positions, notifications):
- **Settings ⚙ → Trading:** platform dropdown (MT5 now, others later), login, password,
  server, "Test connection". Credentials stored only on the user's PC (never in the repo,
  never in results/): Windows Credential Manager via `keyring` (7.1).
- **"Trade live"** starts the bot as its own process (not inside the browser) and opens a
  new tab `/live`; closing the tab doesn't stop the bot, the tab can be reopened any time.
- **Live tab:** connection and account (balance, equity, today's P/L in R and %), FTMO
  limits as bars, open positions, today's signals / setups, live chart with zones,
  confluences and trades, log, Start / Stop and an emergency stop (close all + stop).
- MT5's Python API only works on Windows with the MT5 terminal running: demo on the
  user's PC first; for 24/5 later a Windows VPS near the broker.
- Needs from Phase 5 at least: position sizer (lots from risk % and SL distance) and the
  FTMO daily / max loss limits.

- ☑ **7.1 Account connection + demo test orders** (user's request 2026-10-09).
  - Settings ⚙ → Trading: platform (MT5 now, others later), login, password (masked),
    server (the servers the terminal knows, else typed), optional terminal path, "Save",
    "Test connection" (connected or MT5's error; account name, server, DEMO / REAL,
    currency, balance, equity, leverage, algo trading allowed).
  - Login, password and server only in the app and in the Windows Credential Manager
    (`keyring`); never in the repo, `.env`, results/, logs, error messages or test output.
  - **DEMO LOCK:** every order function refuses unless `account_info().trade_mode` is DEMO.
    No override yet.
  - `python -m backtester.live.test_orders XAUUSD` (and a button in Trading, demo only):
    market buy 2 x min lot with SL / TP (fill vs ask, slippage), modify the SL (break-even
    test), close half (TP1 test), close the rest; the same as a sell. Every request and
    result (retcode) logged, execution times, nothing left open afterwards.
  - Not yet (7.2, after the risk sizer of Phase 5 and the open questions above): strategy
    trading, the Live tab, position sizing from risk %.
  **Built (2026-10-09), not yet run against the demo account** (terminal not logged in):
  - `live/credentials.py` (keyring), `live/trading_settings.py` (`results/trading.json`:
    platform, terminal path, symbol names, server clock), `live/connection.py` (session,
    report, known servers from the terminal's `bases/` folder), `ui/trading_panel.py` (the
    modal, opened from ⚙ Chart settings → Trading → "Account connection…").
  - `live/orders.py`: `require_demo` in every order function, `MAGIC` on every order,
    filling mode fallback, `OrderLog`. `live/test_orders.py`: the scripted test and its
    report; the break-even move right after the entry is expected to be rejected
    ("invalid stops": the SL would be on the wrong side of the price), so the test then
    moves the SL halfway to the entry to test the modify itself.
  - Tests with fakes (`tests/live/`, `tests/ui/test_trading_panel.py`): secrets never in
    trading.json, reports or error texts; every order function refuses REAL / CONTEST /
    no account without sending; the full buy + sell run; filling fallback; market closed;
    an error midway still closes everything; the user's own positions are left alone.
  - Check: Settings ⚙ → Trading → "Account connection…": enter login, password, server,
    Save, Test connection (shows account, DEMO, balance, algo trading). Then "Run demo
    test orders" (or `python -m backtester.live.test_orders XAUUSD`) while the market is
    open; afterwards no position in the terminal's Trade tab, history shows 2 x 3 deals
    per symbol.

- ◐ **7.2 Demo forward test of the ORB candidate** (user 2026-10-17; spec `docs/live-trading.md`): automatic
  demo orders + paper log, 0.25 % risk, daily stop -2 %, emergency stop, the bot starts MT5 itself, minimal
  Live page and Telegram (messages + /status, /stop). Order: 7.1 demo test orders, then sizer + bot loop,
  then Live page and Telegram.
  **7.1 run on the FTMO demo 2026-10-17 (BTCUSD):** first run showed FTMO confirms fills late (deal 0, price
  0.0 in the order result) -> fill confirmation from the deals added; second run clean: fills at the quote
  (0 slippage), SL modify, half and full close ok, nothing left open, median 174 ms. Built 2026-10-17:
  risk sizer, daily guard (-2 %, FTMO 5 % / 10 %), bot loop `python -m backtester.live.bot` (stop files
  results/live/STOP and EMERGENCY), paper log; not yet run live.
  Built 2026-10-17 too: `/live` page, Telegram (messages, /status /stop /emergency; token in the Credential
  Manager; the user's test message arrived), initial balance from the first balance deal, settings panel
  limited to the 5 strategy symbols' cost fields (the page froze with 28 symbols). Accepted by the user 2026-10-17.
  **Done in 7.3 (2026-10-17):** UI clean-up —
  remove the Sweep button from the top bar; Settings: chart settings collapsible, the account connection
  section better organized; a clear separate button that opens the live-account window with all its options.

- ☑ **7.3 UI clean-up before the first live day, step (a)** (user 2026-10-17; spec `docs/live-trading.md` ›
  App layout and Live page; mockups in `docs/ui-mockups/`, inspiration only): one top bar Chart · Backtest ·
  Risk · Live (Live red while the bot runs), app opens on `/live` when the bot runs; Sweep menu into the chart
  settings; chart settings one collapsible block; account connection + Telegram from ⚙ to `/live` › Connection;
  new `/live` page with Start / Pause / Stop / Close all & stop, settings editable only when stopped, account in
  USD, daily stop and FTMO limits, session countdown, heartbeat, setup funnel, positions, recent-trades strip.
  **Built 2026-10-17, accepted by the user 2026-10-17 ("End."):** bot PAUSE file (paused breakouts skipped for
  the day) and status fields paused / risk_percent / strategy / session / setups; `ui/nav.py` top bar,
  `ui/live_model.py` (tested helpers), new `ui/pages/live.py`, Connection on `/live` (`trading_panel` as
  Details), sweep controls in ⚙ Chart settings; Live page times in Swiss time. Fix: `bot.py --daily-stop`
  default (slots dataclass). Polish left: empty trades chart axes, Connection dropdowns light on the dark page.
- ☑ **7.4 Chart page in the new style, step (b)** (user 2026-10-17, after 7.3): side cards (backtest result,
  overlay switches, trades in view), timeframe buttons, range bar (1M / 3M / 6M / YTD / 1Y / All, go to date).
  Decided by the user 2026-10-17: page dark like `/live`, the chart pane itself lighter (light-blue background,
  same candle colours); "Backtest result" card shows the newest run; the overlay switches move from the toolbar
  into the side panel below the Backtest result card (only there); a click on a trade in "Trades in view" jumps
  to it on the chart; the side cards are collapsible (chart full width).
- ☑ **7.5 Update data button** (user 2026-10-17): no download at app start (fast start); a "⟳ Update data"
  button on the chart page fetches in the background, per symbol, everything after its last cached day up to
  yesterday: MT5 cache from the running terminal, Binance for BTC / ETH-USDT, new histdata months once
  published. Decided by the user 2026-10-17: the chart shows MT5 bars after a symbol's last histdata day
  (chart only); backtests keep one feed (data split rule).
  **Built 2026-10-17, accepted by the user 2026-10-17:** `data/update.py` (plan), `tools/update_data.py` (job, CLI
  `--dry-run`), `ui/update_button.py`, chart MT5 fill (`chart_data.chart_adapter`); first real run: 28 updated, 0
  errors. Decided by the user 2026-10-17: the update keeps adding new histdata months for the 5 core symbols;
  histdata caches more than 93 days old are not kept current (MT5 on the chart after them); a trade with exit
  reason `end_of_data` counts as "open" in Trades in view. 7.4 built the same day (`ui/chart_side.py`,
  `chart-page.css`); newest run = newest `YYYYMMDD-HHMMSS` run id. Open polish: "Updated …" text overlaps the
  button on narrow windows; dashed "MT5" marker at the feed switch not drawn; replay bar and ⚙ dialog on the dark
  page not checked visually.

## Phase 8: Strategy 2 (NY Open index sweep)

`docs/strategy-ny-indices.md` (new 2026-10-10), detection rules in `confluences.md`.
NAS100 and US500, AM and PM windows. Strategy logic only in `strategy/ny_index_sweep/`;
detector changes stay shared and must keep strategy 1 working (its tests green, changes
in its results reported).

- ☑ **8.1 Index data: NAS100, US500.** Built as 0.5 (import, clock, data check, doji
  thresholds, cost estimates). Clock confirmed by the user's TradingView check
  (2026-10-11); cached 2018-01-02 .. 2026-09-30, so 2018-2019 give the ATH check and
  warm-up for backtests from 2020-01-01.
- ◐ **8.2 Detector updates** (`confluences.md`, 2026-10-10). One detector per sub-step,
  tests first incl. the no-lookahead test, each checked on the chart:
  1. ◐ **Liquidity sweep rework** (`detectors/sweep.py`, › Liquidity sweep): candidate =
     a wick beyond one of the **last ⚙ N confirmed swings** (default 3; replaces "since
     the last BOS plus the broken one"), level = the furthest taken within N (#N when
     more are taken); ⚙ close beyond the level still counts (default yes); becomes a
     sweep only with a BOS **within ⚙ X candles** (default 10) of the extreme, a new
     extreme restarts the count. Overlay "Liquidity sweep" follows.
     Built (2026-10-10): `detectors/sweep.py` `SweepConfig` (`lookback_swings` 3,
     `bos_within` 10), hover shows "n candles after the top"; tests in
     `tests/detectors/test_sweep.py`. Close setting `close_beyond_counts` (default on; off =
     a candle closing beyond a level doesn't sweep it, user's choice 2026-10-10; a higher
     candle that sweeps nothing drops the candidate).
     Strategy 1 doesn't use this detector (its zone sweep is its own), so its results
     can't change. Check (choices made while building):
     - "Within X candles": BOS candle index − top index ≤ X (the top's own candle = 0).
     - A top with no BOS in time is dropped; a later candle that takes one of the last N
       swings starts a new candidate, even below the old top (it may be the BOS candle
       itself).
     - The detector still pairs a sweep with a BOS on its own timeframe; the AM's sweep on
       1h / 4h with the BOS on the setup TF is strategy 2's job (8.4).
  2. ◐ **Equilibrium rework** (› Equilibrium): leg = swing low (after a sweep: the sweep
     extreme) → the **high wick of the BOS candle**, fixed at the BOS candle (was: up to
     the first swing high after the BOS); tap = wick below 50%, confirm = green close
     back above, invalidate = close below the leg's low. EQ SL rule (beyond the leg's low,
     buffer ⚙ 10% of swing low → deepest wick into the EQ; ⚙ EQ-only toggle: beyond the
     deepest wick). **Changes strategy 1** (`strategy-session-zones.md › Entry sequence`,
     › Stop loss): its tests re-run and the change in its results reported.
     Built (2026-10-10): `detectors/equilibrium.py` (was a stub): `equilibrium_box`,
     `move_start` (moved from strategy 1's `setup.py`), `deepest_wick`,
     `equilibrium_stop_loss`, `EquilibriumConfig` (`sl_buffer` 10%, `sl_at_deepest_wick`
     off) and `EquilibriumDetector` (one EQ per real BOS; leg from the sweep extreme when the
     BOS made a liquidity sweep, else from the start of the BOS move); overlay
     "Equilibrium" (indigo, ★ / ✕ sub-entries). Strategy 1 (`signals.py`) builds its EQ at
     the break candle from its own 5m breaks (the leg start is unchanged: the BOS leg's
     low); `EntrySignal.eq_deepest`; `targets.stop_loss` uses the EQ rule (no ATR buffer,
     no small-confluence rule for an EQ); settings `detectors.equilibrium.*` (before C.3 `strategy.equilibrium.*`) under Stop loss.
     Tests: `tests/detectors/test_equilibrium_detector.py` (incl. no-lookahead),
     `tests/strategy/session_zone_sweep/test_equilibrium.py` (new scenario),
     `tests/ui/test_equilibrium_overlay.py`. The old rule (leg up to the first swing high
     after the BOS, 3.3c) is replaced.
  3. ◐ **Breaker block** = step 2.7 (› Breaker block), built here; 2.7 is marked done
     with it.
     Built (2026-10-10): `detectors/breaker.py` (was a stub): `BreakerDetector` (one per
     real BOS; range = `order_block.find_leg` with the other color: the green run back from
     the broken high's green turn candle, dojis skipped, red ends it), `BreakerBlock`;
     overlay "Breaker block" (orange, ★ / ✕, panel order 2.7). Strategy 1: breakers are now
     a step-4 confluence and in the default `confluence_kinds` (spec: step 4 lists them;
     they were only left out because they weren't built), selectable in the settings, drawn
     orange by "↳ trade confluences". Tests: `tests/detectors/test_breaker.py` (incl.
     no-lookahead), `tests/ui/test_breaker_overlay.py`; strategy 1's EQ tests run without
     breakers, plus a test that the breaker wins a same-candle tie with the EQ (strategy 1's
     rule: the most recently formed, then the one nearest the close).
  Status (2026-10-11): 8.2.1 – 8.2.4 built, the user checks them on the chart later
  (Liquidity sweep, Equilibrium, Breaker block overlays).
  **Rule change after 8.2.1 (user, 2026-10-11, code not updated):** a sweep needs a wick
  beyond the **most extreme of the last N** swings, not one of them (`confluences.md` ›
  Liquidity sweep). To do: `detectors/sweep.py` (`_take`: candidate only when the wick is
  beyond the most extreme of the last N; level = that swing), its tests, strategy 2's
  `_register_sweeps`.
  4. ◐ **Confluence toggles** (› Confluence toggles): OB, breaker, BPR, FVG, EQ each
     on/off per backtest, in the settings (4.1) and presets.
     Strategy 1 (2026-10-10): already had them: "Entry confluence types"
     (`confluence_kinds`: FVG, OB, breaker since 8.2.3, BPR) plus `use_equilibrium` (its
     spec names this switch), both in Settings › Confluences and saved with presets. Added
     `test_each_confluence_type_can_be_switched_off` (`test_setup.py`: switching a type off
     removes its entries, the others stay). Strategy 2 gets the same in its config (8.4).
     On the chart, the Overlay types panel already switches each type on/off.
- ◐ **8.3 4h candles in TradingView alignment + AM/PM window clock.** 4h candles closing
  at 02/06/10/14/18/22 ET (DST-aware), built from 1m, as an option next to the current
  UTC-aligned 4h (strategy 1 keeps its own); 1h on full hours. Window clock (ET, NY DST):
  AM 09:00–11:30 (open 09:30), PM 13:30–16:00 (open 14:00), best-time tags AM
  09:50–10:10, PM 13:50–14:10; all ⚙. Tests around the March and November changes.
  **Changed by the user (2026-10-11):** the best-time tag and its include / exclude toggle
  are replaced by the window settings: start and end per session, default 30 min before
  until 2 h after the open (= the windows above), the whole setup inside, always on
  (`strategy-ny-indices.md` › General). To do (code not updated): drop `best_time` /
  `include_best_time_trades` / `WindowTimes.best_start|best_end` / `is_best_time`, keep
  start / end as the settings (UI with 8.6).
  Built (2026-10-10):
  - `data/resample.py` `H4Alignment` (UTC default, NEW_YORK), `new_york_h4_open`,
    `spans_utc_days`; `CacheAdapter.fetch_frame(h4=…)` reads NY 4h candles like D / W
    (they cross UTC midnight: candles closing in the range, only when every UTC day they
    cover is cached). Chart settings popover: "4h candles" (UTC / New York); the overall-
    trend 4H badge stays UTC (strategy 1). Tests: `tests/data/test_resample.py` (summer,
    winter, March DST week), `tests/data/test_cache_adapter.py`,
    `tests/ui/test_daily_weekly_chart.py`.
  - 1h: UTC full hours are full New York hours too (whole-hour offsets), nothing to build.
  - `strategy/ny_index_sweep/windows.py` (new strategy folder): `WindowConfig` /
    `WindowTimes` (settings), `window_on`, `window_of`, `is_best_time`, `windows_between`.
    Tests: `tests/strategy/ny_index_sweep/test_windows.py`.
  Check (choices made while building):
  - A candle belongs to the window it closes in, start < close <= end (as for sessions):
    the 1m candle closing at 09:00 ET is before the AM window, the one closing at 11:30
    its last.
  - Best time: the entry time (the entry candle's close) within 09:50–10:10 /
    13:50–14:10, both edges included.
  - A NY 4h bucket starting at a time that doesn't exist (02:00 ET on the March DST
    Sunday, markets closed) would move to 03:00; the data has no candles then.
  - Compare on TradingView after importing the indices into the main cache (0.5):
    NAS100 / US500 4h with "4h candles: New York" vs FOREXCOM:NSXUSD / SPXUSD 4h.
- ☑ **8.2.5 Liquidity sweep rework and research (user, 2026-10-12 / 13; accepted at "End.").**
  Built, all **off by default**: equal-high tolerance (`equal_tolerance_atr`, N swings 1-5),
  breakout filter (`two_closes_cancel`, `cancel_closes` 2 / 3, `cancel_wick_first`),
  `bos_before_top`, doji as a share of the candle's range (`SwingConfig.doji_range_share`);
  temporary **Sweep** menu in the chart toolbar; the same options in strategy 2's config
  (Settings › Entry). Tools: `tools/sweep_study.py` (35,000 sweeps, outcome per rule),
  `analytics/sweep_quality.py`, `tools/strategy2_sweep_grid.py`, `tools/strategy2_explore.py`
  (entry time, AM / PM, window size, exit structures). Results (spec: `confluences.md` ›
  Liquidity sweep, `strategy-ny-indices.md` › Backtest options): sweeps are a coin flip after
  the BOS on every rule, with or without the trend; strategy 2 2023-26 base -3.4 R net
  (+42.7 gross), 2020-22 about -50 R in the wide window; the window cut 30 min before to 90
  after (+39 R in 2023-26) and "breakout 2 closes" (+53 R) did **not** hold on 2020-22
  (-21 R, -34 R). No rule change adopted; defaults unchanged. Open: decide the next idea
  (cost filter, new edge sources, the user's own rules; see HANDOFF).
- ◐ **8.4 Strategy 2 setup state machine** (`strategy/ny_index_sweep/`). Bias (AM: 4h
  trend, PM: 15m trend) and the AM route (1h = 4h trend → setup 5m / entry 1m, else 15m
  / 5m) read once before the window and frozen; only trades in the bias direction.
  Funnel: sweep (AM: 1h / 4h, registered at the wick, checked at the HTF close; PM: 15m /
  5m) → real BOS on the setup TF → 3rd confluence in the BOS move (incl. those created by
  that BOS) tapped → entry-TF BOS → entry-TF confluence tapped + confirmed → entry at
  that close (⚙ entry-TF confluence off: enter at the entry-TF BOS close). Ranking only
  when several are hit by the same candle (OB > BB > BPR > FVG > EQ). PM: a 15m BOS from
  the same sweep replaces a running 5m setup. Cancellations (opposite setup-TF BOS; ⚙
  close beyond the swept level before our BOS), back to step 5 on an opposite entry-TF
  BOS, next 3rd confluence when one is invalidated, timeout ⚙ 25 setup-TF candles from
  the original BOS, window end kills untriggered setups, one open trade per setup,
  re-entries, ⚙ max trades per session per index (1). Hand-built scenario tests (an AM
  and a PM day), like strategy 1's `scenario.py`.
  Open questions answered by the user on 2026-10-11 (spec updated): BoS = the most recent
  swing high (a setting "last swing high before the sweep" comes later, not built), tap by
  entry-TF wicks, inside the move by time, timeout, same sweep, no trend = no bias.
  Built (2026-10-11), with 8.5: `strategy/ny_index_sweep/` (`config.py`
  `NyIndexSweepConfig`, `frames.py` detectors per timeframe incl. untouched swings and
  never-tapped zones, `setup.py` the state machine, `strategy.py` `NyIndexSweep`,
  `targets.py`); engine: three TPs (`Order.take_profit_3`, `tp2_share`) and
  `Strategy.on_trade_closed(ref, result)`; trades.csv `take_profit_3`, `tp2_share`;
  runner `make_strategy`, NY 4h and 15m / 1h / 4h from the first cached day for strategy 2
  (`full_history`, ~30 s start-up per symbol); `python -m backtester.run NAS100 US500
  --start … --end … --strategy ny_index_sweep` (spec defaults, no presets; UI in 8.6).
  Tests: `tests/strategy/ny_index_sweep/` (`test_parts.py`; `test_strategy.py`: every
  decision on a 20-day random walk checked against the rules, no lookahead with cut
  histories, entry-TF confluence off), `tests/engine/test_backtest.py` (three TPs, the
  callback), `test_setup_steps.py` (each branch of the state machine on real 1m / 5m
  candles with injected BoS events and zones: funnel, entry-TF confluence off, X-candle
  limit, close-beyond setting, deeper wick, opposite BoS, tap timeout, tap only after the
  BoS, nothing in the move, zones created by the BoS, next 3rd confluence, entry BoS after
  the tap, opposite entry-TF BoS, re-entry after the trade, PM 15m replaces 5m). Choices made while building (check them):
  - Sweeps are seen on closed 1m candles against the sweep-TF swings confirmed before that
    1m candle opened. One setup per route waits for its BoS at a time (a deeper wick moves
    its extreme). AM: 1h and 4h levels together, one setup per wick; the most extreme
    level taken decides the sweep TF (X-candle limit, close-beyond check).
  - 3rd-confluence candidates: confluence-TF zones in the move, setup-TF breaker / OB
    created by the BoS, and the EQ of the leg (on the setup TF). A candidate drops out
    when a candle of its own timeframe closes beyond its far edge.
  - Several tapped / confirmed on one candle, same kind: the one price reaches first.
  - Entry candidates are validated from the candle after the entry-TF BoS (earlier taps
    don't count). An opposite entry-TF BoS: back to step 5.
  - A signal without an order (SL not beyond the entry, no TP, best time excluded) sends
    the setup back to step 5 and doesn't count as a trade; max trades reached ends it.
  - Tags: `am` / `pm`, `route_<setup>_<entry>`, `z3_<kind>`, `entry_<kind>`, `best_time`;
    `confluence` in trades.csv = the 3rd confluence's kind.
  - Strategy 2 switches off strategy 1's break-even at the next session start
    (`Strategy.uses_session_break_even`); break-even only after TP1.
  - Later setting (user, 2026-10-11): BoS against "the last swing high before the sweep".
  **Open after the first run (2026-10-11 / 12), code not updated yet (user: no code
  changes for now):**
  1. Sweep: the most extreme of the last N swings must be taken (8.2.1 note above).
     Example that showed it: NAS100 2026-09-24 AM short "swept" a 4h high at 29,669 with
     price around 30,200.
  2. Windows instead of the best-time tag (8.3 note above); the `best_time` tag and
     `include_best_time_trades` go away.
  3. Strategy 2 settings in the settings panel and presets (windows per session and the
     rest of `NyIndexSweepConfig`), with 8.6.
  Then re-run 8.7.
- ◐ **8.5 Strategy 2 SL / TP** (› Stop Loss, › Take Profit). SL below the 3rd confluence
  + ⚙ 10% of its height; ⚙ narrow-confluence threshold (0 = off) → sweep extreme; EQ SL
  rule (8.2.2). Rejection zones (AM: 1h + 4h, PM: 15m; untouched swing highs,
  unmitigated opposite FVG / OB / BB / BPR; higher TF wins when close; ⚙ 0.2R
  clustering). 3 equal parts: TP1 = near edge of the first zone ≥ ⚙ 1.2R, TP2 / TP3 the
  next zones; break-even incl. costs after TP1. ATH fallback (above the highest high of
  all data before the entry): ⚙ fib extension of the setup-TF BOS leg (1.382 / 1.5 /
  1.618 / 2.0) or fixed R (1.2 / 1.5 / 1.8); zones running out after TP1 / TP2 →
  fallback levels; levels running out → the rest closes at the last TP. Engine: 3
  partial exits.
  Built with 8.4 (`targets.py`). Choices made while building (check them):
  - Narrow-confluence threshold in ATRs (14) of the 3rd confluence's timeframe; then the
    SL goes below the sweep extreme with the same buffer (10% of the 3rd confluence).
  - Rejection levels below 1.2R are dropped before clustering; the rest cluster as in
    strategy 1 (chained, < 0.2R). Levels come from closed 15m / 1h / 4h candles; a high
    is "touched" when a later wick reaches it (>=).
  - Fallback levels must lie beyond the last TP and at or beyond 1.2R; fib from the sweep
    extreme (0) to the setup-TF BoS candle's high (1). Two TPs: a third at TP1, the rest at
    TP2; one TP: all of it.
- ◐ **8.6 Chart: strategy 2 trades + AM/PM session view.** **8.6a done (2026-10-12, user's "3"; accepted by the user 2026-10-12):** the strategy popover lists both strategies (`strategy/registry.py`); picking one switches the settings panel (its own fields and groups, a new "Windows" group for strategy 2; `engine.break_even_at_next_session` is not shown for strategy 2), the presets (one list per strategy, "Default" = that strategy's defaults; a preset file records `strategy.name`) and the backtest button (runs the picked strategy). `RunSettings.strategy` is either config, the JSON carries `strategy.name`, the store `settings-current` carries `strategy`, float lists (`fib_levels`, `fixed_r_levels`) are comma-separated numbers. `strategy.confluence_kinds` has one widget per strategy (different defaults; strategy 1 hides EQUILIBRIUM). The Trades overlay says it is strategy 1 only for now. **Still open: 8.6b** Trades overlay for strategy 2 (3 TPs, route / entry / confluence hover), **8.6c** AM/PM session view and the Sessions button for strategy 2. Check 8.6a: `python -m backtester.ui.app`, strategy popover → Strategy 2: Settings… shows its fields; change a value, save a preset, switch back to Strategy 1 (its preset list has no strategy 2 presets); Run backtest with NAS100 / US500 for a short range.
  Original text: Also: strategy 2 in the
  strategy popover and the settings panel (`NyIndexSweepConfig`: the window start / end per
  session, user 2026-10-11), the backtest button running it, Trades overlay with TP3. Trades overlay for strategy 2
  (3 TPs); the Sessions button shows the AM/PM windows when strategy 2 is chosen (the
  strategy popover gets a second entry); session view: pick one AM or PM session and see
  sweep, BOS, 3rd confluence, entry confluence, SL / TPs. Visual step: the user checks it.
- ◐ **8.7 First backtest on NAS100 / US500 + results.** `python -m backtester.run` with
  strategy 2 on NAS100 + US500 over the cached history; results page split by AM / PM,
  best-time tag, route and confluence type; per-year table reported here.
  **First full run (2026-10-11)**, before the user's check of 8.4 / 8.5 and before the
  rule changes above (sweep: most extreme of the last N; best-time tag replaced by the
  window settings), so it is to be re-run after them: `python -m
  backtester.run NAS100 US500 --start 2020-01-01 --end 2026-09-30 --strategy
  ny_index_sweep` (`results/20261010-224222_NAS100-US500`, ~45 min, workers ~1.8 GB):
  1,658 trades, win rate 37.5%, **net R −61.2 (gross +29.6)**, average R:R planned 2.93,
  max drawdown 79 R. NAS100 866 trades +16.7 R net, US500 792 trades −77.9 R net.

  | year | all: trades / net R | NAS100 | US500 |
  |---|---|---|---|
  | 2020 | 250 / −47.6 | 136 / −10.1 | 114 / −37.5 |
  | 2021 | 251 / −3.9 | 139 / −12.8 | 112 / +8.9 |
  | 2022 | 278 / −6.3 | 136 / +3.2 | 142 / −9.4 |
  | 2023 | 173 / +12.9 | 91 / +13.9 | 82 / −0.9 |
  | 2024 | 246 / −15.8 | 136 / −9.1 | 110 / −6.7 |
  | 2025 | 254 / −0.6 | 130 / +14.2 | 124 / −14.8 |
  | 2026 | 206 / +0.1 | 98 / +17.4 | 108 / −17.4 |

  Splits (net R per trade): AM 428 trades +0.001, PM 1,230 −0.050; route 5m/1m 1,442
  −0.021, 15m/1m (PM) 162 −0.206, 15m/5m (AM) 54 +0.047; 3rd confluence breaker 1,228
  −0.041, OB 214 +0.043, EQ 177 −0.077, FVG 39 −0.168; best time 139 +0.082, other
  1,519 −0.048. Exits: SL 1,034, break-even 283, last TP 341.

## Phase 9: Strategy 3 (no-wick candle in the trend)

Rules set by the user 2026-10-13, spec `strategy-no-wick.md`. Plain 1:1, one folder `strategy/no_wick/`.

- ☑ **9.1 Build and compare** (accepted by the user 2026-10-14, strategy dropped, no variant has an edge). Spec, tests first (`tests/strategy/no_wick/`, limit fills in
  `tests/engine/test_backtest.py`), engine support for limit fills (`Order.limit_fill`, SL first in the
  fill candle), strategy + config, registry entry, `python -m backtester.tools.no_wick_grid`
  (entry timeframe 5m / 15m / 30m / 1h x trend higher / same x entry close / body_end / middle, 2020-22
  against 2023-26). Results recorded here after the user has looked at them.

  **First full grid (2026-10-13, `python -m backtester.tools.no_wick_grid`, 5 symbols, 2020-01-01 to
  2026-09-30, spec defaults: sl_buffer 10%, rr 1, expiry 6, wick share 0).** Every one of the 24 variants
  is negative, gross as well as net, in both halves (2020-22 and 2023-26):

  | timeframe / trend / entry | trades | win % | gross R | net R |
  |---|---|---|---|---|
  | 5m higher close | 116,835 | 47.2 | -4,759 | -37,178 |
  | 15m higher close | 23,795 | 48.5 | -780 | -4,111 |
  | 15m same close | 29,251 | 48.8 | -841 | -4,358 |
  | 30m higher close | 9,260 | 49.4 | -231 | -1,120 |
  | 1h higher close | 3,701 | 49.6 | -61 | -308 |
  | 1h same close | 4,499 | 49.3 | -84 | -343 |
  | 15m higher middle | 20,803 | 45.2 | -1,947 | -5,333 |
  | 15m higher body_end | 14,585 | 33.6 | -4,327 | -21,312 |
  | 1h higher body_end | 2,225 | 34.3 | -722 | -2,684 |

  Reading: the entry itself has no edge (gross about -0.02 to -0.03 R per trade on `close`), and the
  stops are tight, so costs take about 0.1 to 0.14 R per trade on 5m / 15m. Higher timeframes lose
  less per trade only because costs are a smaller share of the stop. `body_end` is by far the worst
  (win rate 33-36%): the limit fills exactly when price comes back through the candle's open, the
  stop is close, and the SL-first rule in the fill candle is conservative. Trend source (higher
  vs same) makes no difference. Full CSVs: `results/no_wick_grid/` (git-ignored).

## Phase 10: Strategy 4 (trend following, Kaufman style)

Requested by the user 2026-10-14 (Kaufman, *Trading Systems and Methods*, pp. 152-154 and Appendix B);
the pages could not be read, so the rules in `strategy-trend-following.md` were chosen by Claude
(user's instruction to answer open questions itself). One folder `strategy/trend_following/`.

- ☑ **10.1 Engine: exit on signal, no take profit.** (10.1-10.4 accepted by the user 2026-10-14 with "End."; swap in the engine and `--swap-file` added in the same session; strategy 4 parked, drop / keep as a filter is his open decision) A strategy can close an open trade at the current
  candle's close (exit reason `signal`); an order may have no TP. Tests first in `tests/engine/`.
- ☑ **10.2 Build strategy 4.** Signals `breakout` / `sma` / `kama`, ATR protective stop, stop-and-reverse,
  timeframes 15m / 30m / 1h / 4h / 1d. Tests first (`tests/strategy/trend_following/`), no-lookahead test,
  registry entry.
- ☑ **10.3 Compare.** `python -m backtester.tools.trend_grid`: signal x timeframe x parameter sweep,
  5 symbols, 2020-22 vs 2023-26, gross / net (swap not modelled). Results recorded here.

  **First full grid (2026-10-14, `python -m backtester.tools.trend_grid`, 5 symbols, 2020-01-01 to
  2026-09-30, stop 3 x ATR(20), swap not modelled).** Net R (sum), with the 2020-22 / 2023-26 halves:

  | variant | trades | win % | avg R net | sum R net | 20-22 | 23-26 |
  |---|---|---|---|---|---|---|
  | 15m / 30m, all signals | 2.8k-113k | 13-32 | -0.04 to +0.02 | mostly negative | mixed | negative |
  | 1h breakout 100 | 1,434 | 23.2 | +0.075 | +107 | +66 | +41 (XAUUSD +115, others ~0) |
  | 4h sma 50 / 100 / 200 | 1.7k-3.6k | 15-20 | +0.015 | +27 to +57 | mixed | small + |
  | 1d breakout 55 / 100 | 84 / 60 | 30 | +0.43 / +0.62 | +36 / +37 | +7 / +2 | +29 / +35 |
  | 1d sma 100 / 200 | 345 / 243 | 21 / 14 | +0.11 / +0.21 | +37 / +51 | +2 / +1 | +35 / +50 |
  | 1d kama 0 / 0.1 / 0.5 | 338-1,137 | 29-33 | +0.01 to +0.03 | +4 to +28 | mixed | mixed |

  Reading: trend following loses on 15m / 30m (costs, chop) and turns slightly positive from 4h up, more
  so with slower settings (the neighbours agree). But the gain sits almost only in 2023-26 and mostly in
  XAUUSD (the 2024-26 gold trend) and the indices; GBPUSD / GBPJPY are flat or negative. 1d has only
  60-250 trades in 6.75 years, too few to trust. Net results on 4h / 1d are optimistic by the missing
  swap. Not yet a robust edge. Full CSVs: `results/trend_grid/` (git-ignored).
- ☑ **10.4 Signals from the book (5th ed. pp. 152-154, 329-332).** `momentum`, `dunnigan` (Ruggiero's
  Dunnigan trend), `sma_band_atr` (MPTDI-style band); sweep with Kaufman's classic periods. Tests first,
  then the grid again.

  **Book-signal grid (2026-10-14, `trend_grid --signals sma momentum dunnigan --sma-periods 50 200`, 5 symbols,
  2020-01-01 to 2026-09-30, swap rates still 0: net = net ex-swap).** Sum R net (2020-22 / 2023-26):

  | variant | trades | avg R net | sum R net | 20-22 | 23-26 | per symbol |
  |---|---|---|---|---|---|---|
  | 1h sma 50 band 1.0 ATR | 4,596 | +0.044 | +201 | +145 | +56 | XAU +78, GJ +65, NAS +93, GU -14, US500 -21 |
  | 30m sma 50 band 1.0 | 9,618 | +0.012 | +118 | +73 | +46 | XAU +193, GU -128 |
  | 1h sma 50 band 0.5 | 6,521 | +0.018 | +116 | +135 | -19 | |
  | 4h momentum 5 | 10,731 | +0.008 | +81 | +62 | +19 | 4 of 5 positive |
  | 1d momentum 252 / sma 200 band | 77-160 | +0.37 to +0.66 | +51 to +59 | ~+2 | ~+50 | too few trades, mostly 2023-26 |
  | dunnigan (all timeframes) | 356-31k | -0.05 to +0.01 | -1,279 to +40 | mixed | mixed | no edge |
  | momentum 15m-1h, sma without band 15m-30m | | negative | | | | costs |

  Reading: the band (book p. 329) helps everywhere: fewer trades, higher average, smaller drawdown. 1h sma 50
  with a 1.0 ATR band is the first variant positive in both halves on 3 of 5 symbols, but its neighbours
  (band 0.5, sma 200) are not positive in 2023-26, so not yet stable. Dunnigan's trend (pp. 152-154) has no
  edge. Swap still to add (MT5 not connected yet). CSVs: `results/trend_grid_book/`.

  **Full grid with FTMO swap (2026-10-14, `trend_grid --swap-file results/ftmo_swap_2026-10-14.json`).** Rates read
  from MT5 2026-10-14 (USD per lot per night; long / short): XAUUSD -61.27 / -4.20, GBPUSD -5.77 / -4.48, GBPJPY
  +2.04 / -13.85 (triple Wednesday), NAS100 -6.91 / +0.34, US500 -1.22 / -0.46 (triple Friday). Today's rates applied
  to 2020-26 (rates near zero in 2020-21, so swap is overstated there). Sum R net with swap | without swap:

  | variant | trades | with swap | without | 20-22 / 23-26 (with swap) |
  |---|---|---|---|---|
  | 1h sma 50 band 1.0 | 4,596 | -13 | +201 | +43 / -57 |
  | 30m sma 50 band 1.0 | 9,618 | -187 | +118 | -72 / -115 |
  | 1h breakout 100 | 1,434 | -71 | +107 | -21 / -49 |
  | 4h momentum 5 | 10,731 | -32 | +81 | +9 / -41 |
  | 4h sma 50 | 3,582 | -57 | +57 | -6 / -52 |
  | 1d sma 200 (plain / band 0.5 / 1.0) | 243 / 115 / 77 | +10 / +10 / +10 | +51 | about -11 / +21 |
  | 1d momentum 252 | 160 | +13 | +59 | -11 / +24 |
  | every other variant | | negative | | |

  Reading: with swap no variant on 15m-4h is positive. Swap costs 0.03-0.2 R per trade, more the longer the hold;
  XAUUSD longs (-$61 / night) eat the gold trend that carried the gross results. Only 1d sma 200 and momentum 252
  stay slightly positive, with 77-243 trades, negative in 2020-22. No robust edge. CSVs: `results/trend_grid_swap/`.

  **Robustness check (2026-10-14, user asked): 1h sma with band on XAUUSD + GBPJPY + NAS100, FTMO swap.**
  SMA 40 / 50 / 60 x band 0.75 / 1.0 / 1.25: all 9 positive with swap together (+13 to +107 R, 2,243-3,573 trades,
  max DD 45-79 R); sma 50 band 1.0 best (+107 R, 2020-22 +69 / 2023-26 +38, max DD 47 R). Per symbol not stable:
  XAUUSD loses in 2020-22 in 7 of 9 and wins in 2023-26 in all 9 (gold trend); GBPJPY wins in 2020-22 in all 9 and
  loses in 2023-26 in 6 of 9; NAS100 mixed. The total is positive because different symbols carry different
  periods, and the 3 symbols were chosen after seeing the results. +107 R over 81 months = about 1.3 R / month
  against a 47 R drawdown. CSVs: `results/trend_check/`.
- ☑ **10.5 Strategy 4 as a trend filter for strategy 2** (user, 2026-10-14: "keep it as a filter"). Built 2026-10-14,
  accepted by the user 2026-10-15 with "End." (with the rollover close and the cost filter); **strategy 2 parked by the
  user 2026-10-15** after these results. `NyIndexSweepConfig.trend_filter` (off by default; spec: strategy-ny-indices.md ›
  Trend filter): signals only in the direction of the last SMA ± band x ATR cross (strategy 4's `sma` signal, shared
  class `SmaBandCross`). Same session: FTMO swap rates of 2026-10-14 made the default costs (user, 2026-10-14).

  **Result (2026-10-14, NAS100 + US500, 2020-01-01 to 2026-09-30, FTMO swap now in net).** Sum R; ex-swap = net
  without swap; halves = net with swap:

  | variant | trades | gross | net ex-swap | net | 20-22 / 23-26 | max DD |
  |---|---|---|---|---|---|---|
  | no filter | 1,662 | +29.2 | -61.6 | -135.4 | -89.9 / -45.5 | 141 |
  | 1h sma 50 band 1.0 | 1,028 | -0.6 | -53.5 | -104.2 | -48.8 / -55.4 | 105 |
  | 1h sma 40 / 60, band 1.0 | 1,044 / 1,018 | +5.4 / +8.8 | -48.7 / -44.8 | -99.2 / -95.5 | | 101 / 97 |
  | 1h sma 50, band 0.5 / 1.5 | 1,059 / 995 | +43.5 / +12.3 | -12.4 / -40.3 | -64.9 / -87.1 | | 69 / 90 |
  | 4h sma 50 band 1.0 | 891 | -20.1 | -67.9 | -112.9 | -39.7 / -73.2 | 114 |
  | 15m sma 50 band 1.0 | 1,097 | +63.1 | +6.4 | -46.4 | -44.6 / -1.8 | 67 |

  Reading: the 1h filter removes about 38% of the trades but not the losing ones: gross per trade falls (+0.018 ->
  0.000 R). Net improves only because fewer trades pay costs. 15m is the best (+6 R ex-swap) but strategy 2's PM
  bias already is the 15m trend, and it is still -46 R with swap; one trade's R varies about +-1.6, so ~1,000 trades
  have a noise of about +-50 R. **No filter variant gives an edge.** New finding: **swap costs strategy 2 -74 R** (654
  of 1,662 trades are held over the 17:00 New York rollover, NAS100 longs -$6.9 / lot / night against stops of a few
  points), more than spread + commission (0.055 R per trade, about -91 R). CSVs and trade lists: `results/s2_trend_filter/`.

  **Cost filter, studied on the trade lists (not built; Phase 11 plans it as I-45):** skipping trades whose spread +
  commission is above X R of the stop. No filter run: X = 0.10 R keeps 1,453 trades, net ex-swap -61.6 -> +1.0
  (20-22 -58.3 -> -14.6, 23-26 -3.4 -> +15.6), net with swap -64.4; X = 0.08 / 0.06 / 0.05: +1.1 / -14.3 / +5.7 ex-swap.
  Not monotonic and inside the noise; it does not turn strategy 2 positive with swap. Re-entries a skipped trade would
  allow are not modelled in this study.

  **Close before the rollover and cost filter in the engine (2026-10-14/15, user: "test" / "build it").** Both built, off
  by default (strategy-ny-indices.md › Close before the rollover; risk-management.md › Cost filter). The rollover close is
  at 16:15 ET because the index feed has no candles 16:15-18:00 ET (a first run at 16:59 closed everything at 18:01 and
  was discarded). Same data and period as above, sum R, halves = net with swap:

  | variant | trades | win % | gross | net ex-swap | net | 20-22 / 23-26 | max DD |
  |---|---|---|---|---|---|---|---|
  | no filter | 1,662 | 37.4 | +29.2 | -61.6 | -135.4 | -89.9 / -45.5 | 141 |
  | close at 16:15 ET | 1,662 | 41.0 | -15.0 | -105.8 | -109.6 | -58.2 / -51.5 | 115 |
  | cost filter 0.10 R | 1,507 | 38.6 | +50.0 | -8.1 | -77.9 | -45.6 / -32.3 | 91 |
  | close 16:15 + cost 0.10 | 1,507 | 42.4 | +11.2 | -47.0 | -49.5 | -20.3 / -29.3 | 59 |
  | 15m trend filter | 1,097 | 39.1 | +63.1 | +6.4 | -46.4 | -44.6 / -1.8 | 67 |
  | close 16:15 + 15m filter | 1,097 | 42.8 | +42.3 | -14.4 | -17.2 | -18.7 / +1.6 | 46 |

  Reading: closing at 16:15 removes almost all swap (-74 -> -4 R) but also 44 R of gross profit from the runners that
  reach TP2 / TP3 overnight: net +26 R. The cost filter (engine, re-entries included) removes 155 trades with tight
  stops that were gross losers too: net +57 R, both halves better. Combined -49.5 R, with the 15m filter -17 R (max DD
  46 R). Each step helps a little and in both halves, but the best combination was picked from 6 runs on the same
  data and is still negative: **no edge yet**. Not run: rollover + cost + 15m together. Defaults unchanged (all off).


## Phase 11: Research studies from the knowledge base (user, 2026-10-14)

6.4, 6.5, 6.6, 6.7, 11.1 and 11.2 are accepted by the user 2026-10-15 ("End."); the open decisions of
6.7 (spread table as default, from which year) stay open. Next by Claude's decision (user: "you can
decide", 2026-10-15): the gap-fade candidate I-39 as a spec and strategy test with the real costs
(11.4 below), then 11.3.

One-off research tools on cached data; they change no setting and no strategy. Ideas and sources:
`knowledge/ideas.md`. Order agreed with the user 2026-10-14: robustness report (6.4) and time split (6.5)
first, then these studies, then day-trade strategies without swap (ORB I-07/I-08, compression break I-33)
with the cost-to-target (I-45) and free-path (I-37) filters.

- ☑ **11.1 Noise / regime study** (I-01). **Built and run 2026-10-14, waiting for the user's check.**
  `analytics/noise.py` (efficiency ratio ER(n) = |close − close n bars ago| / sum of the n bar moves,
  from closed bars only; rank correlation; seeded random-walk reference) and `python -m
  backtester.tools.noise_study` (per symbol × timeframe M15-D1 × n 10 / 20 / 60 × year / half /
  all → `results/noise_study/noise.csv`; with `results/trend_grid/split.csv` also
  `vs_strategy4.csv` and `vs_strategy4_stats.csv`: per symbol × timeframe × half the mean ER next to
  strategy 4's gross R per trade over that timeframe's variants). Tests `tests/analytics/test_noise.py`,
  `tests/tools/test_noise_study.py`. **Result (2020-01-02 .. 2026-09-29, 5 symbols):**
  - **All markets are almost random-walk noisy.** Random-walk reference ER: 0.319 (n 10), 0.227 (n 20),
    0.133 (n 60). ER(20) per symbol on M15 / H1 / H4 / D1: XAUUSD 0.228 / 0.247 / 0.257 / 0.236,
    GBPUSD 0.224 / 0.242 / 0.244 / 0.222, GBPJPY 0.222 / 0.240 / 0.241 / 0.223, NAS100 0.244 / 0.270 /
    0.270 / 0.242, US500 0.240 / 0.263 / 0.261 / 0.243. FX on M15 and GBPUSD / GBPJPY on D1 are at or
    below the random walk; gold and the indices are slightly above, H1-H4 the least noisy timeframes.
  - **Kaufman's "indices are the noisiest" does not hold on this data**: NAS100 / US500 have the highest
    ER here (0.24-0.27); a plausible reason is the strong upward drift 2020-26 (ER counts drift as
    efficiency) and CFD data instead of futures 2000-2012. Not a statement about trend following on
    indices: strategy 4 on indices still failed (ROADMAP 10).
  - **Halves:** ER changed little (first → second half, n 20: XAUUSD H4 0.248 → 0.265, GBPJPY H4 0.248 →
    0.235, GBPUSD D1 0.227 → 0.217, US500 D1 0.236 → 0.248). Noise rose slightly in the FX pairs on
    H4 / D1 and fell in gold and the indices.
  - **Does noise explain strategy 4's halves?** Partly, in direction, not in size. Over 50 symbol ×
    timeframe × half cells the level correlates with gross R per trade (rank correlation +0.39, t 2.9)
    and the change between the halves correlates strongly over 25 pairs (+0.59, t 3.5): where ER rose,
    gross R per trade rose. By tercile of ER: the noisiest third (ER 0.217-0.235, the random-walk level)
    −0.010 R per trade gross, the two less noisy thirds +0.015 R per trade gross, before spread and swap
    (about 0.1 R per trade on the fast timeframes, ROADMAP 10). So noise decides the sign of the raw
    signal but the signal is far too small to pay costs. Caveats: ER and strategy 4 both measure
    trendiness of the same prices (partly circular), cells share trades, few cells.
  - **Consequence:** the ER gate (I-02) can only select the better part of a signal that has no net edge;
    do not expect it to rescue strategy 4. It is a diagnostic and a possible filter for a better base
    signal. **I-02 dropped by the user 2026-10-15.**
- ☑ **11.2 Open / gap / trend-day study on NAS100 / US500** (I-09, I-39). **Built and run 2026-10-15,
  waiting for the user's check.** Plan by Opus, code by Sonnet. `analytics/open_gap.py` (cash days
  09:30-16:00 New York from M1, classified; daily ATR(14); one record per regular day; features known
  at 10:00 / 11:00 are listed in `FEATURE_FIELDS` and tested not to read later bars; summaries per
  half) and `python -m backtester.tools.open_gap_study` (`results/open_gap_study/`: days, exclusions,
  gap_fill, first30, trend_days, extremes, last_hour). `metrics.month_part(date)` was extracted. Tests:
  `tests/analytics/test_open_gap.py`, `test_open_gap_summaries.py`, `tests/tools/test_open_gap_study.py`.
  **Data facts** (from the cache): the index feed has no bars 16:15-18:00 New York; the 16:00-16:14
  bars are not the cash session; holiday CFD sessions end 12:59 (43-45 days), half days 13:14;
  2023-02..07 has many hour-sized holes: 2023-26 loses about 130 of ~880 days (74 data holes, 54 first
  bar missing, NAS100) against about 30 in 2020-22; ~1,450-1,520 regular days per symbol are used.
  **Results** (2020-01 .. 2026-09; "gap" = cash open − previous cash close, the CFD trades overnight):
  - **Gap fill (same day): 60 % NAS100, 58 % US500 (claim 48 %); by day 3: 76 % / 75 % (claim 76 %).**
    It depends on size: <0.1 ATR 90-92 %, 0.1-0.25 74-76 %, 0.25-0.5 48-52 %, 0.5-1 29-31 %, 1+ 10-17 %.
    Against the baseline "the same-size move the other way" (extend: 54 % overall, the random-walk
    level) the excess is small: which level is touched FIRST, the previous close ("fill") or its
    mirror ("extend"): NAS100 44 % vs 37 %, US500 43 % vs 38 % (rest: neither / same bar). Same sign in
    both halves and both symbols; by bucket the edge sits in 0.1-0.25 ATR (54 vs 46, 58 vs 40) and, for
    NAS100, 0.5-1 ATR (30 vs 17); 0.25-0.5 ATR has none.
    As a 1:1 fade (target previous close, stop at the mirror level, exit at the close) this is about
    +0.04-0.05 R per trade before costs (same-bar days counted as losses, days with neither level
    exit at the close: not measured), z about 3 (NAS100) and 2 (US500), the two symbols are not
    independent; cost per trade on a 0.1-0.25 ATR gap is a large share of that. Candidate, not a rule.
  - **First 30 minutes vs the rest of the day: no continuation** (51-55 %, mean rest in that direction
    +0.009 / −0.008 ATR, |t| < 1; 2020-22 55 %, 2023-26 49-51 %).
  - **Trend days (open and close in the opposite 10 % of the range): 7 % of days** (claim 20 %, not
    reproduced with this strict definition; 6-8 % in both halves, Fridays the same, 8-12 % in 2020-22).
    Features at 11:00: gap unfilled lift 0.98-1.06, new extreme 10-11 lift 1.0, close at 11:00 in the
    extreme fifth of the range so far lift 1.3-1.5 (10 % vs 7 %; partly mechanical).
  - **Day high / low: 80-86 % of days have the high or the low in the first 90 minutes** (claim 90 %;
    uniform 23 %, random walk 32 % each): high 38-42 %, low 46-52 %. The last hour has the high on
    25-36 % of days and the low on 17-25 % (random walk 26 %): U-shape, more in 2020-22.
  - **Last hour:** a new high of the day in the last hour is followed by a close at 0.85-0.89 of the
    range (mechanical) and a mean close only +0.02 ATR above the old high; 2020-22 t +2.6..+3.6 (both
    symbols, high and low), 2023-26 t −0.8..+1.4: not stable.
  - **Consequence:** the claims of the books are mostly not reproduced as edges: gap fill is mostly
    the random-walk touch frequency, the first 30 minutes do not continue, trend days are rare and
    hardly predictable at 11:00. The only candidate is the gap fade of 0.1-1 ATR gaps (fill first
    44 vs 37 %): test as a strategy with spread (the candle path and exits decide), ideas I-39.
- ☐ **11.3 Time-of-day drift by session for XAUUSD / GBPUSD / GBPJPY** (I-17).
- ☑ **11.4 Gap fade as a strategy test** (I-39; candidate from 11.2). Spec first (`docs/strategy-gap-fade.md`):
  NAS100 / US500, gap = cash open − previous cash close in daily ATR(14), only gaps of 0.1-1 ATR, entry at
  the cash open, target the previous close, stop at the mirror level (1:1), exit at 16:00 if neither; no
  overnight hold. Test with the spread table (and the fixed spread), robustness report, halves, stressed
  costs; sweep only gap bucket, stop distance and exit time. Expected from 11.2: about +0.04-0.05 R gross
  per trade (fill first 44 vs 37 %), so costs decide; report "no edge" if net is not positive in both halves.

  **Result 2026-10-15** (`tools/gap_fade_grid.py`, 2020-01..2026, NAS100 + US500, 2374 trades): default
  (0.1-1 ATR, stop 1.0, exit 16:00) +112.7 R gross, +55.0 R net with the fixed spread (+58.6 with the spread
  table), +0.023 R/trade, halves +34.6 / +20.4; swap -1.7 R. 27 of 36 variants net positive (75 %), mean - 1 sd
  negative (-8.9); best gap 0.1-1, stop 0.75, exit 12:00: +79.4 R net, halves +57.5 / +21.9, +42.1 with costs x1.5.
  Weak positive, 2023-26 weaker; not yet an edge without out-of-sample confirmation. Accepted by the user 2026-10-15 ("weak positive,
  waiting for out-of-sample"); next 11.5-11.7 (user, 2026-10-15).
- ☑ **11.5 MT5 history download** (user, 2026-10-15): FTMO M1 bars from the running terminal into their own
  cache `data/cache/mt5/` (same Parquet layout as histdata: bid = MT5 bar, ask = bid + the bar's spread, volume =
  tick volume), so every tool can read FTMO data through `SymbolSources`; histdata stays the default. Server
  clock checked for the downloaded years (against histdata where both exist).
- ☑ **11.6 Gap fade out of sample** (user, 2026-10-15): the same 36 variants on FTMO's NAS100 / US500 history
  2017-12..2019-12 (never seen by 11.4), fixed spread and spread table.
  **Result 2026-10-15:** FTMO has only daily index bars before 2021-09 (M1 from 2021-09-14), so the test ran on
  histdata 2018-2019 instead (never seen by 11.4; fixed spread, no spread table for those years): default
  -22.1 R gross, -59.4 R net / 747 trades (-0.080 R/trade); 11.4's best variant (stop 0.75, exit 12:00) -7.3 R
  gross, -54.9 R net; 6 of 36 variants net positive, mean -22.7 R. On FTMO's own feed 2021-09..2026-09 the
  default is +13.9 R net / 1836 trades (+0.008 R/trade, histdata same window +28.7 R). **Out of sample: no edge.**
- ☑ **11.7 Gap fade walk-forward** (user, 2026-10-15): each year, pick the variant that was best on the years
  before and trade it in that year; report the chained out-of-sample net R against the default variant.
  **Result 2026-10-16** (`tools/gap_fade_walk_forward.py`, histdata NAS100 + US500 2018-2026, anchored, max net R on
  the years before, first test year 2019; runtime 125 min): chained out-of-sample **+0.6 R / 1423 trades** against
  the default variant's +22.6 R / 2752 trades (2019-26). Picks jumped between variants (5 different in 8 years);
  test years -12.7, +18.3, +5.7, -13.1, -13.5, -1.1, +15.9, +1.0 R. Monte Carlo report: walk-forward **NO EDGE**
  (all 6 checks fail: t 0.02, random entries 92nd percentile, weaker half -6.3 R, costs x1.5 -19.3 R, random fills
  median -35.7 R); default variant **NO EDGE** (t 0.47, costs x1.5 -16.4 R, random fills median -47.1 R fail; random
  entries 98.7th percentile, halves and without-best pass); FTMO pass at 1 % risk 29 % (walk-forward) / 32 %
  (default). The slippage stress hurts most: gap stops are small, so a few points of slippage are a large share of
  1 R. **Gap fade: no tradeable edge.**
- ☑ **11.8 More markets from MT5** (user, 2026-10-15): about 26 liquid FTMO symbols (FX majors and crosses,
  US / EU / JP indices, metals, energy, BTC / ETH, DXY as reference) with `tools/mt5_download.py`.
- ☑ **11.9 Crypto order flow from Binance** (user, 2026-10-15; the user may trade crypto on Binance directly,
  no prop firm needed): public trade data (aggTrades, aggressor side) of BTCUSDT / ETHUSDT, reduced to 1m bars
  with buy / sell volume, delta and trade count; the raw files are deleted after each month.
- ☑ **11.10 Opening-range breakout** (I-07 / I-08) with the tick-volume A/B (I-44), after 11.8 / 11.9 (user, 2026-10-15).

- ☑ **11.11 Stationarity / half-life diagnostic** (accepted by the user 2026-10-20) (T-11; user, 2026-10-16, after 12.10): ADF, half-life, Hurst,
  variance ratio and lag-correlation grid per symbol, timeframe and half, development years only (before 2021-09-14).
  Decided by the user 2026-10-19: all 21 histdata symbols 2015-01-01..2021-09-13 (GER40 only to 2020-06-12, 13.13),
  halves at the middle of the period; the time-of-day part drops the 2015-2018 US-only-DST weeks (13.12); a finding
  needs Benjamini-Hochberg at 5 % over all cells, the same sign in both halves and >= 2 sibling symbols; a seeded
  random walk is the reference. Built in its own worktree / branch `claude/knowledge-stationarity` (app running).
  Built 2026-10-19 (awaiting the user's check): `python -m backtester.tools.stationarity_study --cache-dir <histdata cache>` ->
  `results/stationarity/` (adf, hurst, vr, lagcorr, time_of_day, findings .csv, summary.txt); code `analytics/stationarity.py`.
  Findings use the robust variants (Spearman lag grid, returns clipped at 5 robust sd for VR and time of day, gap returns zeroed in lag pairs). Files with no cache day (New Year days) are bridged. Sibling rule as built: the symbol plus >= 1 same-sign sibling.
  **Result 2026-10-19:** findings real / shuffled-returns reference (same rule): ADF 0 / 0, VR 188 / 0, lag grid 356 / 0,
  time-of-day mean 88 / 0, time-of-day autocorrelation 516 / 0. (1) **No stationarity:** no symbol / timeframe reverts
  to a level (0 of 105 ADF cells; core 5 p 0.14-0.98; half-lives months to years). (2) Hurst at or below the random
  walk everywhere. (3) **Short-term reversal is real but tiny:** VR < 1 and negative lag-1 correlation on M5-H1 in
  most FX pairs and metals (H1 k=1,h=1: XAGUSD -0.077, GBPUSD -0.042, XAUUSD -0.039, GBPJPY -0.035; both halves); the
  next-hour move after a 1-sd hour is 0.2-0.5 of one spread -> not tradeable; small moves revert, big moves continue
  (raw Pearson positive). Indices: no robust H1 structure. (4) The 20:30-22:00 UTC FX / silver pattern and the M5
  autocorrelation are bid / spread microstructure at the rollover, not an edge. First run's lag-grid "findings" were
  crash hours (March 2020, SNB 2015, Brexit night) and weekend-gap returns; fixed (gap returns zeroed, Spearman,
  winsorized). Conclusion: price-only time-series structure on these symbols is too small for retail costs.
- ☐ **11.12 Gap momentum** (I-46, Chan; user, 2026-10-16, after 11.11): the opposite side of the failed gap fade.

## Phase 12: Backtest realism and Monte Carlo (user, 2026-10-15)

Lessons from HftBacktest, VectorBT, NautilusTrader and prediction-market-backtesting, read 2026-10-15
(`knowledge/topics/backtest-frameworks.md`, ideas T-02..T-07). Each step test-first, off by default where it
changes results, defaults changed only with the user's go.

  **Development result 2026-10-16** (`tools/orb_grid.py`, before the cut-off, fixed spread; `results/orb_dev/`):
  price-only on histdata 2015-2021-09, 18 symbols: 0 of 23 variants net positive; gross small positive
  (+0.01-0.04 R/trade), costs about 0.1 R/trade for 5-30m ranges, less for ATR bands (best: band 0.5-1 ATR,
  -0.005 to -0.014 R/trade). US indices with band 0.25-0.5 ATR slightly positive (+12-24 R, ~+0.01 R/trade)
  but the first half negative. XAGUSD about -1 R/trade: today's fixed spread on 2015 prices (cost-model flaw).
  Volume A/B on FTMO MT5 (FX, XAUUSD 2015-21, US30 2019-21, US2000 2018-21): min_rel_volume 1.5 improves
  17 of 18 variants, mean +0.013 R/trade; best: US indices band 0.25 ATR, no target, with volume: 177 trades,
  +19.7 R net (+0.11 R/trade), halves +0.9 / +18.8, +16.3 with costs x1.5, +14.3 without the best trade.
  Candidate for the test period (small sample, chosen among many variants).
  **Test period (go by the user 2026-10-16):** exactly two variants fixed in advance, band 0.25 ATR and band
  0.5 ATR, no target, min_rel_volume 1.5, on US30 / US2000 / NAS100 / US500, FTMO MT5 data from 2021-09-14,
  real costs, robustness report; nothing tuned afterwards.
  **Test result 2026-10-16** (`results/orb_test/`, spread scaled with the price level): band 0.25 ATR 301
  trades, +35.0 R gross, +30.3 R net (+0.10 R/trade), halves 2021-23 +27.6 / 2024-26 +2.7, costs x1.5 +25,
  best trade removed +23; band 0.5 ATR 263 trades, +12.3 R net (+0.05), halves +12.7 / -0.5. Same with the
  spread table. US30 and US500 carry it, US2000 flat; Welch t about 1.5 (not significant). Out of sample
  positive but fading since 2024: not a confirmed edge. Accepted by the user 2026-10-17 ("End."); next: demo forward test 7.2.
- ☑ **11.14 Spread scaled with the price level** (numbered 11.11 in its commits; user 2026-10-16; built, awaiting the user's check): the fixed spread is today's; in years
  with other prices it is scaled by price / reference price (cost-model fix, mainly for the development years).
- ☑ **11.15 Volume filter on parked strategies with potential** (numbered 11.12 in its commits) (user 2026-10-16: "yes if the strategies
  have potential"): only strategies with positive gross R before costs qualify; decided by Claude per strategy.
  Claude's pick (user "ok", 2026-10-16): strategy 2 only (+29 R gross 2020-26); development on FTMO US30 /
  US2000 before the cut-off (the only indices with tick volume there), A/B on NAS100 / US500 from 2021-09
  (already used by strategy 2, so not fresh). Gap fade and strategies 1, 3, 4: no (nothing before costs).
  **Result 2026-10-16** (`results/s2_volume_ab_mt5/`): development US30 + US2000 2018-21: spec -10.5 R gross /
  -147 R net (739 trades), with volume -6.3 / -18 (119); NAS100 + US500 2021-09..2026: spec +13.6 / -81 (1215),
  with volume -23.5 / -30 (120, -0.25 R/trade). The filter only removes trades: **no edge**; option stays off.
- ☑ **11.16 Order-flow study on BTC / ETH** (numbered 11.13 in its commits) (user "ok", 2026-10-16): Binance futures delta (taker buy - sell)
  and its imbalance vs the next 1m-4h return, against the round-trip fee; development period 2020-01 .. 2021-09-13
  only. Research tool, no rule. Next after it: forward test of the ORB on the FTMO demo (needs Phase 7).
  **Result 2026-10-16** (`results/orderflow_study/`): short-horizon effects are real against a circular-shift
  baseline and stable on both symbols and halves (5m cumulative delta over 4 bars mean-reverts over the next 3
  bars, relative volume), but 0.02-0.05 %, 2-5x below even the maker fee. Effects that beat the fees (BTC 1h
  cvd_12 momentum, 4h CVD divergence) are BTC-only, tail-driven in the 2020-21 bull run and unstable on ETH,
  out of 576 tests. Nothing ready for a spec; one hypothesis to re-test once on post-cut-off data: BTC 1h
  cvd_12, 6-bar horizon.
- ☑ **12.1 Random-entry baseline** (T-02; next step, user 2026-10-15, before the gap fade walk-forward 11.7):
  Monte Carlo of entries. For a run, draw 1,000 seeded sets of random entry times (same symbols, same session
  windows, same trade count and long/short mix), keep the strategy's own stop / target / exit and the real
  costs, and report where the strategy's net R sits (percentile, mean and spread of the random runs) in the
  robustness report. First use: the gap fade (11.4 / 11.7).
  Decided by the user 2026-10-15: gap fade baseline = same gap days, same stop and exit, coin flip between fading
  and following the gap; other strategies = random entry times inside the strategy's own window with its own stop
  and exit; defaults 1,000 runs, seed 42.
- ☐ **12.2 Intrabar order from M1** (T-03): when SL and TP are both inside one candle, read the M1 bars inside it
  to see which came first; only a conflict inside one M1 bar stays SL first (CLAUDE.md allows "unless a lower
  timeframe resolves it"). Option, off by default; report how many trades change.
- ☑ **12.3 Walk-forward splitter** (T-04): rolling and anchored windows as a shared tool for 6.1 / 6.2 and studies;
  11.7 becomes its first user.
- ☐ **12.4 Parameter heat map** (T-05): two parameters, one metric (net R, R per trade), on the results page.
  Visual step.
- ☐ **12.5 Demo reconciliation** (T-06; before Phase 7): demo trades from MT5 next to the engine's trades on the
  same candles (entry, exit, spread, swap, R), every difference explained.
- ☐ **12.6 Stressed fills** (T-07): seeded random slippage on stop / market fills and "touch is not a fill" for
  limits, as an extra column in the robustness report.
  Random slippage built 2026-10-15 (`analytics/random_fills.py`, kind C of the Monte Carlo report); "touch is not a
  fill" for limits still open.
- ☐ **12.8 Engine slippage** (found 2026-10-15, filed by the user's go the same day): `SymbolCosts.slippage`
  (`engine/costs.py`) is defined but the engine never applies it, so every backtest so far ran without slippage
  although `risk-management.md › Slippage` says entries and SL hits get it (TPs none). Apply it in the engine
  (net R only, reported per trade like `spread_r`), decide with the user whether time / signal exits count as
  market fills, and rerun the open studies' headline numbers to show the change.
- ☑ **12.7 Monte Carlo backtester** (user, 2026-10-15): one tool and results page that runs the Monte Carlo kinds
  on a backtest: trade order / day reshuffle (5.3, account drawdown and FTMO pass rate), random entries (12.1),
  random fills (12.6), synthetic price paths. Decided by the user 2026-10-15: **all four kinds, shown in the
  report** (not a separate app page). The report shows a fan of simulated equity curves (like a stock-price Monte
  Carlo chart: many seeded paths from the start balance, best and worst marked), all important numbers (among them
  the probability of passing an FTMO challenge, the gain on a 100k account, the average gain per month in %), and
  ends every test with a clear verdict whether the strategy has an edge. Thresholds and approximations: see the
  spec `risk-management.md › Monte Carlo` once agreed.
  **Built 2026-10-15** (`tools/monte_carlo.py`, `analytics/verdict.py`, `risk/monte_carlo.py`,
  `analytics/random_baseline.py`, `analytics/random_fills.py`, `data/random_walk.py`). First run: gap fade NAS100 +
  US500 2020-01-01..2021-09-13 (development years), 625 trades, +24.4 R net (+0.039 R/trade): **WEAK** (t 1.08 < 2;
  halves check fails by construction, every trade in the first half); random entries 97.5th percentile, costs x1.5
  +14.8 R, without best +23.4 R, random fills median +7.9 R; 1 % risk: gain p50 +24.4 %, 1.19 % per month, max DD p95
  29.2 %, FTMO pass 49.6 % (0.5 %: 74.6 %); random paths no warning. Runtime 37 min (kind D most of it).
  Halves split at the middle of the run's period (user, 2026-10-15); n/a checks count neither way (user, 2026-10-15).
- ☐ **12.9 Portfolio tool** (user, 2026-10-16; goal: combine weak, uncorrelated edges into a significant one):
  correlation of daily R between strategies / variants, a combined Monte Carlo report on one account, and the
  number of variants tried in the verdict (deflated Sharpe, López de Prado) so combining does not produce false
  positives.

- ☑ **12.10 Trial log + deflated Sharpe** (accepted by the user 2026-10-19, "End.") (T-08; research order agreed by the user 2026-10-16: 12.10 -> 11.11 ->
  11.12): every run logged with its trial family; PSR / DSR (López de Prado) on the chosen variant.
  **Built 2026-10-16** (`analytics/deflated_sharpe.py`, `analytics/trial_log.py`, `tools/trials.py`; DSR >= 0.95 is
  verdict check 7, user 2026-10-16). Back-fill (count-only, the old result files have no sd): gap_fade 36, opening_range 41.
- ☐ **12.11 Bayesian report** (T-10): Beta posterior of the win rate and of mean R, A/B of variants, trades needed;
  prior odds 1:50 against an edge (rule set by the user, 2026-10-16).

**Infrastructure order** (agreed by the user 2026-10-16: finish the infrastructure first, then find and combine
edges): 12.8 engine slippage -> 12.2 intrabar order from M1 -> 12.9 portfolio tool -> 6.1 Strategy Simulator; later
5.2 account simulator and 12.5 demo reconciliation (before live). Knowledge on combining edges: the user adds
Carver *Systematic Trading*, López de Prado *Advances in Financial Machine Learning*, Chan *Algorithmic Trading*,
Davey *Building Winning Algorithmic Trading Systems* to `00_Literature/Trading` (books are added only from the text).
Done 2026-10-16: the four books plus Kurt and Kaeppel are in `knowledge/` (Natenberg skipped by the user).

## Phase 13: Whole-software audit 2026-10-19 (findings; nothing fixed yet)

Read-only audit by three agents during the first demo day (user: do not change the app while the demo test runs).
Tests 2262 passed, 1 failed only when run from another folder (13.22); ruff clean except 4 files not formatted (three
are another session's uncommitted reformatting). Each item test-first; fix the live ones after the demo day, one at a
time, with the bot stopped. Claude's ranking; the user decides the order.

**Live bot (could hurt the forward test)**
- ☐ **13.1 Loop safety net:** `bot.py` `run` catches only connection errors; any other exception (tick None in
  `orders.py` market_order / close_volume, `account_info` None, sizer ValueError) ends the bot silently: no Telegram,
  positions keep only their server SL, no 15:55 exit (overnight swap). Log + Telegram + continue.
- ☐ **13.2 EMERGENCY before STOP:** `cycle()` checks the STOP file first; Stop then "Close all & stop" in the same
  minute stops without closing.
- ☐ **13.3 Retry closes until flat:** `_close_all` (emergency, daily stop, FTMO breach) logs `close_failed` once and
  stops / blocks; positions stay open unmanaged.
- ☐ **13.4 Single-instance lock:** `start_bot` only checks the heartbeat; a double click before the first heartbeat
  or a bot stuck in connect backoff (> 120 s) lets a second bot start -> duplicate orders. PID / lock file.
- ☐ **13.5 Lost order result:** a non-DONE / None `order_send` result is treated as rejected; if the server executed
  it, the position is orphaned (no session exit). Look up own positions by comment first.
- ☐ **13.6 Closed-bar check on server time:** `Mt5Adapter.to_candles` uses the PC clock; a PC clock > 2 s ahead lets
  the forming bar in, and it is never refreshed (lookahead / parity).
- ☐ **13.7 Sizing on the live price:** risk uses the signal close, not the ask / bid; SL rounded to digits, not
  tick size; no stops-level check.
- ☐ **13.8 Wall-clock fallback exit:** session exits need a bar at 15:55; on half-days or a feed stall the position
  stays overnight.
- ☐ **13.9 Validate CLI risk** (`--risk 0` / negative crashes, no 2 % / 5 % cap outside the UI); **13.10** entry
  deal `fee` missing from net money on the `_close` path; **13.11** daily-loss guard (`risk/prop_rules.py`) measures
  5 % of the day-start balance, FTMO and the Monte Carlo use 5 % of the initial balance.
- Minor: STOP file during startup deleted silently; restart replay writes noisy "stale signal" skips; Telegram
  `/emergency@botname` not matched; initial balance = first balance deal (a top-up misstates the 10 % limit).

**Data**
- ☐ **13.12 histdata clock 2015-2018:** `histdata_to_utc` assumes "NY standard + Europe DST" for all years; in
  2015-2018 the files follow US DST, so 3-4 weeks a year (mid-March, end Oct / early Nov) are 1 h late. 2019-2026
  correct. Affects the development years of strategy 6 (ORB 2015-2021) and every pre-2019 study. Date-dependent rule.
- ☐ **13.13 GER40 histdata changes instrument on 2020-06-15** (DAX ~11,960 -> Euro Stoxx level ~3,100,
  GRXEUR files 2020-2021). Add a price-continuity check to the importer; drop or relabel those files.
- ☐ **13.14 MT5 cache before 2020:** server clock NY+7 is valid only from 2020 (1 h shifts 2015-2019 in US-only DST
  weeks, most Fridays 2010-2014); sparse days (XAUUSD / XAGUSD 2010-12 ~21 bars, GBPUSD Jan 2019) and 23 empty
  US30 days in 2019 cached as valid.
- ☐ **13.15 One-day holes on 1 January** (XAUUSD / GBPUSD / GBPJPY 2020, NAS100 / US500 2018, 15 symbols 2021) from
  year-by-year imports; re-import neighbouring years together and count both files.
- ☐ **13.16 MT5 downloader swallows errors:** every Mt5Error in the first chunk counts as "before history"; a wrong
  broker name reports "no new days" as success.
- ☐ **13.17 Paths relative to the working folder** (`paths.py`, `data/cache.py`, `binance.py`, `costs.py`, spread
  table, the bot's STOP / PAUSE files): a tool run from another folder sees no data or writes a new `data/cache`
  there. Anchor to the repo root.
- ☐ **13.18 Output folders:** `orb_grid --part` without `--out` lets the parts overwrite each other (also
  `gap_fade_grid`); the Monte Carlo folder name omits `--source` / `--seed` / `--runs`. Update job vs readers on
  Windows (PermissionError, shared `.tmp` name for two jobs).
- Minor: `mt5_download --end` accepts today; Binance day holes not retried; tools crash with tracebacks on bad input
  (`show` end <= start or bad `--tz`, `trials add --count -1`); `spread_table.py` duplicates the MT5 defaults;
  `check.py` loads whole histories into memory; `.gitignore` line with an inline comment does not match the stray
  hook file `C:Usersjusti.claudeclaude-notify-signalsstop`; `.vscode/` and `data/cache/dukascopy/` leftovers;
  `data` extra lacks numpy / requests.

**Engine / analytics**
- ☐ **13.19 no_wick limit fill is lookahead** (strategy 3 orders a limit inside the candle it just saw close and the
  engine fills it in that candle). Strategy 3 is dropped; remove or block the path.
- ☐ **13.20 Kind C random fills never slip time exits** (`signal`, `end_of_data`), the main exits of strategies 5 / 6;
  together with 12.8 (engine slippage still not applied) all net R stays optimistic.
- ☐ **13.21 Parallel runner progress race** (`runner.py` drain with `queue.empty()`): progress can step backwards ->
  the flaky `test_parallel_processes_give_the_same_result`; trades themselves are deterministic.
- ☐ **13.22 `tests/tools/test_s2_volume_ab.py`** fails when pytest runs from another folder (relative path).
- ☐ **13.23 Monte Carlo FTMO pass rate:** unfinished attempts are dropped (slow strategies look better); the pass
  fires at the first exit reaching the target even if a later trade that day breaches.
- Minor: short SL / TP triggered on bid candles (slightly optimistic); EDGE possible with DSR n/a; MC `_one_run`
  divides by a zero balance (unreachable at <= 1.5 %); `risk/account_sim.py`, `config.py`, `sweep.py` still stubs.
- Verified correct (short): demo lock without bypass, no credentials in files / logs / Telegram, sizer rounding,
  Prague day / NY session DST, live signal only on closed bars, live / backtest parity of strategy 6, MTF clock,
  SL-first fills, swap / funding / commission math, gap fade and ORB windows, deflated Sharpe math, cache sanity on
  random days (no duplicates, no broken candles), histdata / MT5 seam within 0.03-0.07 %.
