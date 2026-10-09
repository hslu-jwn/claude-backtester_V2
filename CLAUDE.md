# CLAUDE.md

Guidance for Claude Code working in this repository. Read this first, every session.

## What this is

A Python backtester for rule-based price-action trading strategies (session zones, FVGs,
order blocks, BOS, liquidity sweeps). It replays historical candles one at a time, detects
patterns with hard-coded rules, simulates trades in **R multiples**, and turns them into
account results for an **FTMO $100k challenge**. Results are shown in a Dash web app with a
TradingView Lightweight Charts chart. History comes from Dukascopy; MetaTrader 5 (FTMO) for feed comparison and later live trading.

## Specs are the source of truth

All trading rules live in `docs/`. Code implements them; it does not reinterpret them.

| File | Contents |
|---|---|
| `docs/confluences.md` | Swings, trend, BOS, strong-move filter, zone validation, FVG, OB, breaker, BPR, equilibrium, SMT |
| `docs/strategy-session-zones.md` | Strategy 1: sessions, session zones, entry sequence, SL/TP, backtest options |
| `docs/risk-management.md` | FTMO rules, risk guidelines, `risk/` components, risk UI page |
| `docs/ARCHITECTURE.md` | Layers, data flow, how the engine steps through time, data sources (Dukascopy, MT5) |
| `docs/ROADMAP.md` | Phases and numbered steps; what to build next and its status |

- If a rule is **ambiguous or contradicts another rule, stop and ask** the user. Never guess
  a trading rule. Quote the spec line you are unsure about.
- If the user changes a rule, update the spec in `docs/` in the same commit as the code.
- Reference the spec section in docstrings (e.g. `Spec: confluences.md › Order block`).

## Invariant #1: no lookahead, ever

Nothing (any timeframe, detector, strategy, trade engine, risk simulator, chart replay) may
use information from a candle that has not closed at the current simulated time.

- Detectors and strategies only ever receive a `SeriesView` (`core/series.py`). Never pass
  a `CandleSeries`, list, DataFrame or index into the full history to them.
- Higher timeframes are read only through `HigherTimeframeClock.view_at(now)` (`core/mtf.py`),
  where `now` is the **close time** of the current base candle.
- A pattern exists only from the candle that **confirms** it. Every event carries the index
  and close time of its confirming candle, and nothing may act on it earlier.
- Detectors are **incremental**: `update(view)` is called once per closed candle, in order.
  They must not re-scan and rewrite the past.
- Trade fills, SL/TP hits and floating P/L use only the current candle's OHLC. If SL and TP
  are both inside one candle, assume **SL hit first** (conservative) unless a lower timeframe
  resolves it.
- `LookaheadError` is a bug. Never catch it to make something work.

Every detector needs a test proving this (see Testing).

## Other design rules

- **Bullish is described, bearish is mirrored.** Implement one code path parameterized by
  `Direction`, never two copy-pasted versions.
- **Strategy logic stays in its strategy folder.** Detectors, sessions, engine, risk and
  the chart are shared by every strategy. Anything only one strategy needs (e.g. "only
  FVGs after a session sweep") lives in `strategy/<name>/`, never in a shared layer, so a
  new strategy can be added later as another folder and compared with the existing ones.
- **Timeframe-agnostic tools.** Detectors don't know which timeframe they run on; the
  strategy decides (strategy 1: 30m zones, 5m entries, 1h TP obstacles).
- **No magic numbers.** Every tunable value (ATR multiplier, buffers, R caps, obstacle count,
  …) lives in a frozen config dataclass with the spec's default, so backtests can sweep it.
- **Strategies output trades in R only.** Money, lots, FTMO rules and Monte Carlo belong to
  `risk/` and run on the R trade list, so risk settings can be tested without re-running
  detection.
- **Time:** store and compute in UTC. Convert only at the edges with `zoneinfo`: session
  starts in `America/New_York` (each session following its own city's DST, per spec), FTMO
  daily reset at midnight `Europe/Prague` (CE(S)T). Never hard-code UTC offsets.
- Data sources implement `DataAdapter` (`data/adapters/base.py`); nothing else may know where
  candles came from.
- Keep `core/`, `detectors/`, `strategy/`, `engine/` and `risk/` free of Plotly/Dash imports.
  The UI imports from them, never the other way round.

## Layout

```
src/backtester/
  core/        Candle, Timeframe, Direction, CandleSeries/SeriesView, multi-timeframe clock
  data/        DataAdapter interface, Dukascopy downloader, cache (data/cache/), MT5 adapter
  detectors/   Swings, trend, BOS, ATR/strong move, FVG, OB, breaker, BPR, equilibrium, zone validation
  sessions.py  Tokyo/London/New York session clock (DST-aware)
  strategy/    Strategy interface + session_zone_sweep/ (strategy 1)
  engine/      Backtest loop: steps the base timeframe, feeds views, manages trades in R
  risk/        RiskConfig, prop-firm presets, position sizing, account simulator, Monte Carlo, sweeps
  analytics/   Metrics on R trade lists (win rate, expectancy, drawdown in R, …)
  live/        MT5 connection, login in the Windows Credential Manager, demo-locked orders
  ui/          Dash app: chart page (Lightweight Charts in ui/assets/, data from chart_data.py),
               backtest results page, Risk & Prop Firm page
tests/         pytest; mirrors src/ structure
data/raw/      Local CSV candles, <SYMBOL>_<TF>.csv (git-ignored)
docs/          Specs (source of truth)
```

## Commands

```bash
python -m venv .venv            # then activate it (.venv\Scripts\activate on Windows)
pip install -e ".[dev,ui,data]"
pytest                          # all tests
pytest tests/detectors -q       # one area
ruff check . && ruff format .   # lint + format
python -m backtester.ui.app     # start the Dash app (once implemented)
python -m backtester.data.show XAUUSD M5 2026-09-02T13:00 2026-09-02T14:00  # print cached candles
python -m backtester.data.check XAUUSD GBPUSD GBPJPY  # data check report (gaps, broken candles, spot check)
python -m backtester.run XAUUSD GBPUSD --start 2026-09-01 --end 2026-09-30  # backtest -> results/<run-id>/
pip install -e ".[mt5]"           # MetaTrader5 + keyring (Windows only, optional)
python -m backtester.data.mt5_info      # FTMO symbol names + specs, server clock -> results/trading.json
python -m backtester.data.feed_compare  # FTMO vs histdata cache, FTMO spreads -> results/feed_compare/
python -m backtester.live.test_orders XAUUSD  # scripted test orders, DEMO accounts only
```

## Testing

- Write the test before or with the code. A feature is done when its tests pass.
- Use small **hand-built candle fixtures** (`tests/conftest.py` → `make_candles`) where the
  correct answer is obvious and written in the test, e.g. "the swing high is confirmed at
  candle 4 with price 1.2050".
- Cover the edge cases the spec names: dojis skipped, wick-only breaks not counting,
  opposite-color candle ending an OB leg, swing confirmed by the next session's first candle, …
- **No-lookahead test for every detector:** run it incrementally over a series and assert
  that (a) no event is emitted before its confirming candle and (b) appending future candles
  never changes events already emitted.
- Never "fix" a failing test by changing its expected value without checking the spec and,
  if unclear, asking the user.

## Workflow

- Work in small steps: one detector or component per change, tests green, then commit.
- The user names steps by their ID in `docs/ROADMAP.md` (e.g. "do 1.2"). Do only that step,
  then stop and tell the user how to check it (which command, what to look at on the chart).
  Mark the step ☑ in ROADMAP.md in the same commit once the user has confirmed it.
- Visual steps (chart, overlays) are only done when the user has looked at them. Start the
  app for them and say what they should see.
- Commit messages: short imperative summary (`Add FVG detector with validation tests`).
- Never commit market data, `.env`, MT5 login/password/server or backtest outputs.
- MT5 login, password and server live only in the Windows Credential Manager (entered in
  Settings ⚙ → Trading). Never put them in code, `.env`, results/, logs, error messages or
  test output, and never ask the user for them in the chat.
- Every order function refuses unless the account is DEMO (`live/orders.py`
  `require_demo`). Never add an override without the user's explicit decision.
- When done with a step, summarize what was built, what is still a stub, and any spec
  questions that came up.
