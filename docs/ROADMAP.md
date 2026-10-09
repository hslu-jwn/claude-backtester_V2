# Roadmap

The order the project is built in. Each step is small enough for one Claude Code session:
build it, test it, show it to the user, commit. **Don't start the next step until the user
has checked the current one.** Step IDs (e.g. `1.2`) are how the user will refer to them.

Status: ☐ open · ◐ in progress · ☑ done (update this file when a step is finished)

---

## Phase 0: Historical data

FTMO's MT5 server only keeps about one month of 5m history, so **Dukascopy** is the source
for backtest history (free, years of M1 data, UTC, bid and ask). MT5 is used to compare the
recent month against FTMO's own feed, and later for live trading.
Details and pitfalls: `ARCHITECTURE.md › Data sources`.

- ☑ **0.1 Dukascopy downloader + cache.** `data/dukascopy.py` + command
  `python -m backtester.data.download XAUUSD 2020-01-01 2026-10-01`.
  Downloads M1 **bid and ask** candles day by day, saves them to `data/cache/` (Parquet),
  skips days already downloaded (so an interrupted download can resume), waits briefly
  between requests. Symbols: XAUUSD, GBPUSD, GBPJPY. Tests use saved sample files, not the
  network.
- ☑ **0.2 Resampling + cache reader.** Build 5m / 30m / 1h candles from the M1 cache
  (UTC-aligned) and a `CacheAdapter` implementing `DataAdapter` that the chart and
  backtests use. Keep bid candles for the chart and the spread (ask − bid) per candle for
  costs. Drop flat zero-volume minutes first (`ARCHITECTURE.md › Data sources`), so the
  daily break shows as a gap like on TradingView.
  Check: `python -m backtester.data.show XAUUSD M5 2026-09-02T13:00 2026-09-02T14:00`.
- ⏸ **Postponed: the full download.** Dukascopy is currently throttling the user's
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
  file test for each, like the XAUUSD one. The current GBP sample files in
  `tests/data/fixtures/` are Dukascopy "TooManyRequests" replies, not data: download them again.
  Meanwhile GBPUSD / GBPJPY September 2026 come from histdata.com:
  `python -m backtester.data.histdata data/raw/histdata/` → `data/cache/histdata/`
  (New York time with DST, verified against TradingView; see `ARCHITECTURE.md › histdata.com`).
  Each symbol is read from its own source's cache (`data/sources.py`), no `--cache-dir` needed.
  Done: each pair's median 5m candle range is measured and its doji threshold set
  (`detectors/swings.py › equivalent_doji_body`, spec: confluences.md › Swing high / low);
  `data.check` prints both.
  Check: `python -m backtester.data.check XAUUSD GBPUSD GBPJPY`. Gaps are classified by the
  17:00 New York daily close they contain (daily break, weekend, holiday shortened/closed,
  not downloaded, unexpected), so no holiday calendar is needed.
  **Full history (2026-10-09, confirmed by the user).** The user downloaded histdata.com
  for all three symbols: year files 2020-2025 (`DAT_MT_{SYMBOL}_M1_{YYYY}.csv`) and month
  files 2026-01..09. Built: `data/histdata.py` reads year files and zip files too (same
  rules: New York time with DST → UTC, bid only, only UTC days fully covered are written;
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
  **Data check over the full history** (`python -m backtester.data.check XAUUSD GBPUSD
  GBPJPY`, 50 s). Integrity: 0 for every check (no duplicate timestamps after the
  importer's merge, no broken candles, no price <= 0), nothing "not downloaded", bid
  price range per year plausible (gold 1,451-5,597, GBPUSD 1.03-1.42, GBPJPY 124-220).
  Unexpected gaps (no 17:00 New York close inside, >= 5 min), per year:

  | | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
  |---|---|---|---|---|---|---|---|
  | XAUUSD | 19 | 13 | 14 | 557 | 18 | 22 | 14 |
  | GBPUSD | 17 | 41 | 41 | 642 | 51 | 28 | 12 |
  | GBPJPY | 42 | 21 | 28 | 636 | 17 | 24 | 11 |

  - **2023-02 .. 2023-07: about 110-140 hours missing per month and symbol**, as holes of
    1-3 whole hours on most weekdays (histdata's files). Backtests over that half year see
    candles missing (e.g. a 30m candle with 0 or 30 minutes); the user decides whether to
    leave it out or get it from another source.
  - **Gold, every year, in the weeks where only the US is on summer time** (2nd Sunday of
    March to the last Sunday of March; last Sunday of October to the 1st Sunday of
    November): a 60-minute gap at **20:00-21:00 UTC** every weekday. Gold's daily break is
    17:00-18:00 New York = 21:00-22:00 UTC in US summer time. A break one hour early, only
    in exactly those weeks, means the files' clock there is one hour off from New York
    time, as if histdata changed its clock on the European dates; then every UTC time we
    computed in those ~3 weeks a year is **1 hour too early**. Not changed (the user checks
    the candles below first). The GBP pairs have no such break to show it.
  - Every symbol: a 60-minute gap on the Sunday of the EU clock change at 23:00 UTC.
  - GBPUSD 2026-05-18: 4 h + 3 h + 2 h + 1 h missing. GBPUSD 2024-11-07: four 1-hour gaps.
  - Days: 2026-09-25 (Friday) has no data for any symbol (missing in the file).
  The data check now picks its spot candles over the whole history when it covers more
  than a year (`history_spot_times`: years 2020-2026, US+EU summer, winter and US-only
  summer time weeks at 14:00 UTC; in the US-only weeks also the candle 1 h earlier) and
  prints the unexpected gaps per year. Tests in `tests/data/test_check.py`.
  **For the user to compare with TradingView (M5, bid, UTC):** if TradingView's candle at
  the UTC time equals our row, the time zone is right; if in the "US summer / EU winter"
  weeks it equals the "1 h earlier" row instead, those weeks are shifted by one hour.

  | UTC | season | XAUUSD O / H / L / C | GBPUSD O / H / L / C | GBPJPY O / H / L / C |
  |---|---|---|---|---|
  | 2020-07-14 14:00 | US+EU summer | 1800.598 / 1802.355 / 1800.058 / 1800.275 | 1.25090 / 1.25114 / 1.25048 / 1.25079 | 134.227 / 134.252 / 134.163 / 134.189 |
  | 2021-03-09 14:00 | winter | 1713.354 / 1715.879 / 1713.204 / 1714.354 | 1.38868 / 1.38926 / 1.38824 / 1.38870 | 151.193 / 151.231 / 151.136 / 151.158 |
  | 2022-03-23 14:00 | US summer / EU winter | 1931.743 / 1932.428 / 1930.538 / 1930.828 | 1.31950 / 1.32059 / 1.31950 / 1.32051 | 159.623 / 159.740 / 159.594 / 159.724 |
  | 2022-03-23 13:00 | (1 h earlier) | 1935.073 / 1936.619 / 1934.828 / 1935.183 | 1.31751 / 1.31798 / 1.31750 / 1.31795 | 159.073 / 159.117 / 159.056 / 159.102 |
  | 2024-07-16 14:00 | US+EU summer | 2442.605 / 2444.795 / 2442.515 / 2444.265 | 1.29536 / 1.29561 / 1.29532 / 1.29558 | 205.488 / 205.552 / 205.482 / 205.521 |
  | 2025-03-05 14:00 | winter | 2899.735 / 2905.085 / 2899.105 / 2904.875 | 1.28221 / 1.28264 / 1.28194 / 1.28257 | 191.072 / 191.083 / 190.884 / 190.904 |
  | 2026-03-18 14:00 | US summer / EU winter | 4869.495 / 4875.225 / 4865.475 / 4869.175 | 1.33260 / 1.33338 / 1.33258 / 1.33309 | 212.445 / 212.539 / 212.444 / 212.504 |
  | 2026-03-18 13:00 | (1 h earlier) | 4877.875 / 4886.325 / 4871.798 / 4883.825 | 1.33257 / 1.33316 / 1.33236 / 1.33309 | 212.527 / 212.574 / 212.482 / 212.573 |
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
- ☐ **0.4 MT5 adapter + feed comparison** (can wait until after Phase 2).
  `data/adapters/mt5_adapter.py` (server time → UTC, drop the forming candle, symbol
  mapping, unit-tested with a fake `MetaTrader5` module). Compare the last month of
  Dukascopy vs FTMO candles: average difference of highs/lows/closes, how often candle color
  differs. Tells us how far Dukascopy backtests can be trusted for FTMO.

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
  Check: `python -m backtester.data.show XAUUSD M5 2026-09-02T13:00 2026-09-02T14:00 --atr 14`.
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
- ☐ **2.7** Breaker block. ⏸ Postponed until the user clarifies breakers ("once it's
  relevant", `confluences.md › Breaker block`). Build after 2.12.
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
    BOS candle. Taps before step 4 count. Breakers are left out (not built, 2.7).
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
  - Entry confluence types offer FVG / OB / BPR only (breakers aren't built, the
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

`docs/risk-management.md`: sizer, account simulator, Monte Carlo, sweep, and the
Risk & Prop Firm page. Also accepts the user's manual R log as a trade source.

## Phase 6: Robustness (before trusting any result)

- ☐ **6.1** Parameter sweeps over the backtest options.
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
  - `data/dukascopy.py` `read_cached_days`: the day files of a range are read in one go
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
  | 2020 | 2,716 / 35.6% / −381.5 / 389.6 | 901 / 35.3% / −119.7 / 128.1 | 871 / 34.7% / −116.3 / 120.5 | 944 / 36.8% / −145.6 / 155.4 |
  | 2021 | 2,655 / 35.1% / −460.1 / 461.8 | 850 / 35.4% / −141.9 / 143.6 | 865 / 34.5% / −125.1 / 125.4 | 940 / 35.5% / −193.1 / 198.7 |
  | 2022 | 2,726 / 32.9% / −549.2 / 561.4 | 872 / 34.2% / −165.6 / 178.0 | 891 / 32.2% / −183.3 / 187.5 | 963 / 32.5% / −200.3 / 200.3 |
  | 2023 | 2,397 / 34.5% / −448.0 / 453.8 | 789 / 34.3% / −182.6 / 182.6 | 800 / 33.6% / −140.3 / 151.6 | 808 / 35.4% / −125.2 / 145.4 |
  | 2024 | 2,553 / 35.2% / −428.8 / 436.1 | 821 / 36.3% / −101.3 / 104.3 | 838 / 34.2% / −158.0 / 160.6 | 894 / 35.1% / −169.5 / 178.3 |
  | 2025 | 2,680 / 34.0% / −445.7 / 454.3 | 833 / 34.5% / −99.2 / 99.2 | 872 / 35.2% / −116.0 / 127.9 | 975 / 32.5% / −230.5 / 239.7 |
  | 2026 (to 09-30) | 2,020 / 34.4% / −309.6 / 317.7 | 663 / 34.1% / −46.9 / 57.4 | 682 / 33.7% / −117.4 / 126.6 | 675 / 35.3% / −145.3 / 152.2 |

  Every year and every symbol is negative, also before costs (gross −0.05 R per trade,
  net −0.17 R). Caveats from the data check above: 2023-02..07 has many missing hours
  and, if the time-zone question is answered "shifted", about 3 weeks a year ran with
  sessions an hour off. Gold's doji threshold makes 3-5 times more dojis before 2025.

## Phase 7: Live trading via MT5 (much later)

Demo account first, then FTMO. Same strategy code, fed by closed candles only.
`execution/` module with `order_send`, a kill switch, the FTMO limits from `risk/`
enforced before every order, and a log of every decision. Not before Phases 3–6 show a
stable edge.

User's wishes (2026-10-09), to be specified before building (open questions: MT5 server
name, FTMO symbol names, risk per trade on demo, demo lock / daily stop / emergency stop,
fully automatic vs. signal mode, two TPs as two half positions, notifications):
- **Settings ⚙ → Trading:** platform dropdown (MT5 now, others later), login, password,
  server, "Test connection". Credentials stored only on the user's PC (never in the repo,
  never in results/), e.g. Windows Credential Manager via `keyring` or the git-ignored `.env`.
- **"Trade live"** starts the bot as its own process (not inside the browser) and opens a
  new tab `/live`; closing the tab doesn't stop the bot, the tab can be reopened any time.
- **Live tab:** connection and account (balance, equity, today's P/L in R and %), FTMO
  limits as bars, open positions, today's signals / setups, live chart with zones,
  confluences and trades, log, Start / Stop and an emergency stop (close all + stop).
- MT5's Python API only works on Windows with the MT5 terminal running: demo on the
  user's PC first; for 24/5 later a Windows VPS near the broker.
- Needs from Phase 5 at least: position sizer (lots from risk % and SL distance) and the
  FTMO daily / max loss limits.
