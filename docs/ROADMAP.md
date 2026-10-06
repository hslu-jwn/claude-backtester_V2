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
- ◐ **0.3 Data check.** Report per symbol: first/last candle, gaps (expected: weekends,
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
and a dropdown picks which types are shown (multi-select: swings, BOS, FVG, OB, breaker,
BPR, session zones, …). This "all confluences" mode checks the detectors; the strategy's
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
- ☐ **2.4** Zone validation state machine (shared by all zones)
- ☐ **2.5** FVG
- ☐ **2.6** Order block
- ☐ **2.7** Breaker block
- ☐ **2.8** BPR
- ☐ **2.9** Session zones (30m), incl. flips and the second-break kill
- ☐ **2.10** Multi-timeframe view: show 30m zones on the 5m chart

## Phase 3: Strategy 1 + backtest

- ☐ **3.1 Engine.** Backtest loop over 5m with 30m/1h clocks; trade management in R
  (SL before TP inside one candle, break-even rule at the next session start).
  Spread from MT5 data applied to entries/exits (setting; can be switched off).
- ☐ **3.2 Setup state machine** (sweep → 30m reaction → 5m BOS → confluence → entry).
- ☐ **3.3 SL / TP** incl. 1h obstacles and the 1.2R minimum.
- ☐ **3.4 Backtest run + results file.** Command to run a backtest; writes the R trade list
  and settings used to `results/<run>/`. Also records, per session, the session zones and
  the confluences that were part of a setup (triggered or not, confirmed or not), so the
  session view (3.5) can draw them without re-running the strategy.
- ☐ **3.5 Session view.** Click a session line → that session's zones, setup confluences
  and trades (TradingView-style position boxes) are drawn; click outside the chart → off.
  Static by default, with a "replay this session" button.
  Spec: `strategy-session-zones.md › Session inspection view`.
- ☐ **3.6 Results view.** Trade list (click a trade → chart jumps to it and selects its session), win rate,
  expectancy, profit factor, max drawdown in R, equity curve in R, split by symbol /
  session / tag.
- ☐ **3.7 Cross-check with the manual backtest.** Run the same XAUUSD period as the
  user's manual R log and compare trade by trade. Every difference is either a code bug or
  an unclear spec rule. Clarify with the user, don't guess.

## Phase 4: Settings menu

- ☐ **4.1** Settings page generated from the config dataclasses (strategy, detectors,
  session filters, costs), with defaults from the spec.
- ☐ **4.2** Save / load named settings presets (JSON in `results/presets/`); every
  backtest run stores the exact settings it used.

## Phase 5: Risk & FTMO simulation

`docs/risk-management.md`: sizer, account simulator, Monte Carlo, sweep, and the
Risk & Prop Firm page. Also accepts the user's manual R log as a trade source.

## Phase 6: Robustness (before trusting any result)

- ☐ **6.1** Parameter sweeps over the backtest options.
- ☐ **6.2** In-sample / out-of-sample split: tune settings on one period, judge them only on
  a later period the tuning never saw. Walk-forward later.
- ☐ **6.3** Results per year / per quarter, to see if the edge is stable or one lucky period.

## Phase 7: Live trading via MT5 (much later)

Demo account first, then FTMO. Same strategy code, fed by closed candles only.
`execution/` module with `order_send`, a kill switch, the FTMO limits from `risk/`
enforced before every order, and a log of every decision. Not before Phases 3–6 show a
stable edge.
