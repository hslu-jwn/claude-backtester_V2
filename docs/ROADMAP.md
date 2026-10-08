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
    swing high confirmed after the BOS candle (leg = BOS leg's low → that swing's price,
    fixed); only a **close** below the leg's low invalidates it (confluences.md updated);
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
- ☐ **3.4 Backtest run + results file.** Command to run a backtest; writes the R trade list
  and settings used to `results/<run>/`. **One or several symbols per run** (user, 2026-10-08):
  results per symbol and combined (trades merged in time order). Reports progress (for the
  progress bar in 4.0) and can run in the background so the app stays usable. Also records, per session, the session zones and
  the confluences that were part of a setup (triggered or not, confirmed or not), so the
  session view (3.5) can draw them without re-running the strategy.
- ☐ **3.5 Session view.** Click a session line → that session's zones, setup confluences
  and trades (TradingView-style position boxes) are drawn; click outside the chart → off.
  Static by default, with a "replay this session" button.
  Spec: `strategy-session-zones.md › Session inspection view`.
- ☐ **3.6 Results view.** Its own page, opened automatically when a run finishes (user,
  2026-10-08), TradingView look (see 4.0). Stat cards (net R gross / net, number of trades,
  win rate, average R:R, average win / loss, profit factor, expectancy, max drawdown in R),
  equity curve in R over time (gross and net), R distribution, splits by symbol / session /
  long-short / confluence type / TP1-TP2 / tag, run selector (earlier runs). Trade list (click a trade → chart jumps to it and selects its session), win rate,
  expectancy, profit factor, max drawdown in R, equity curve in R, split by symbol /
  session / tag.
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

- ☐ **4.0 Top toolbar** as described above, replacing the current controls (no new
  features: the existing chart settings, overlays and replay move into the popovers;
  the backtest button is wired once 3.4 exists).

- ☐ **4.1** Settings page generated from the config dataclasses (strategy, detectors,
  session filters, costs), with defaults from the spec.
  Must include (user's wish): the session zone kill rule as its own setting: on/off, and the
  number of breaks that kills a zone (`SessionZoneSweepConfig.zone_kill_breaks`, default 3).
  Also (user's wish): step 3 with the 5m trend on/off (`entry_bos_with_trend`, default off).
- ☐ **4.2** Save / load named settings presets (JSON in `results/presets/`); every
  backtest run stores the exact settings it used.
- ☐ **4.3 UI layout and look review** (at the end of the UI work; the user decides the
  details then). Known wishes so far: the strong-move filter switches (FVG, OB) become a
  dropdown; the overall layout of the controls; chart colors and other visual details.
  Until then the current layout and colors stay as they are.

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
