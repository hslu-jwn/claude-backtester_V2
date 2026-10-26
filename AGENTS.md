# AGENTS.md

Project rules for every model working in this repository: Claude (Opus), Codex and Gemini
(Antigravity CLI). `CLAUDE.md` and `GEMINI.md` point here. Read this first, every task.

## Team (rule set by the user, 2026-10-22)

- **Opus (Claude)** is the only dispatcher: plans, assigns tasks, checks every result itself
  (reads the diff, runs the tests; a model's "done, tests pass" does not count), merges,
  commits and talks to the user. It writes or reviews code itself only when the others fail or
  the task touches no-lookahead, the engine or risk.
- **Codex** writes all production code (strategies, fixes, speed-ups), specs and test-case
  lists, designs strategies from the research (`knowledge/` entries with sources) and gives a
  second opinion on decisions. Runs in shell mode (edits files, runs pytest / ruff itself).
- **Claude 4.6** (Sonnet 4.6 / Opus 4.6 through the Antigravity CLI, on the Google quota):
  reviews Codex's code, is the second coding lane when Codex is busy or at its limit, and the
  next step in the escalation chain before Opus.
- **Gemini** (3.8 Flash through the Antigravity CLI) does the bulk work that is not production
  code: literature / web / study research, `knowledge/` write-ups, writing tests from a
  test-case list, running tests and sweeps, research-card write-ups.
- Codex never calls the others. When Codex plans work for another model it writes a task brief
  file (`briefs/<name>.md`) and Opus hands it on.
- **Cross-review:** no model approves its own work. Codex writes code -> Claude 4.6 reviews it
  and Gemini tests it; Claude 4.6 writes -> Codex reviews; Gemini writes tests -> Codex
  reviews them. Tests (written first, from the spec) and the implementation come from
  different models where possible; when the other models are out of quota, one model writes
  both (tests first) and Opus reviews the tests and the code.
- **Escalation, code:** Codex (2 tries) -> Claude 4.6 (Sonnet, then Opus 4.6) -> Opus.
  **Research / tests:** Gemini (2 tries) -> Claude 4.6 Sonnet -> Codex -> Opus. Raise effort or
  model one level after a failed try before passing the task on.
- **Hard limits for Codex, Claude 4.6 and Gemini:** never start a server, app preview or any
  process that keeps running after your answer (a preview of the app on 2026-10-24 kept a
  dispatch open for 30 hours); never commit, push or create branches;
  never read, print or ask for credentials (they live only in the Windows Credential
  Manager); never edit `src/backtester/live/` (order and bot code) or `.env`.
  `python -m backtester.tools.ai_dispatch` enforces this after every call (commits, resets,
  branches, pushes, protected paths, any change on a read-only task) and logs every call to
  `results/ai_calls.jsonl`. The CLIs' own sandboxes are not a hard wall (tools are
  auto-approved headless); the guard is.
- **Lanes:** parallel strategy work happens in a git worktree next to V2 (`python -m
  backtester.tools.lanes create <name>`, `tools/lanes.py`, `docs/research-runner.md` › Lanes).
  A lane may change only `src/backtester/strategy/<name>/`, `docs/strategy-<name>.md`,
  `tests/strategy/<name>/` and `research/grids/<name>*.toml` (`lanes check <name>` enforces it);
  shared code and the `strategy/registry.py` entry go through Opus.
- Every answer ends with a short report: what was done, files changed, test results, open
  questions. A trading rule that is unclear is reported, never guessed.

## What this is

A Python backtester and research platform for rule-based trading strategies. It replays
historical M1 candles one at a time (no lookahead), runs the strategies in `strategy/`
(7 so far: session zone sweep, NY index sweep, no-wick, Kaufman trend following, gap fade,
opening-range breakout, gap momentum), simulates trades in **R multiples** with real costs
and swap, and turns them into account results (balance, drawdown, Monte Carlo, FTMO /
prop-firm pass probability). A research runner sweeps variants with a fixed data split
(develop before 2021-09-14, test once on MT5 data after) and a trial log. Results show in a
Dash app with a TradingView Lightweight Charts chart.

Data: MetaTrader 5 (FTMO) M1 history in `data/cache/mt5/` (26 symbols, preferred day by day),
histdata.com M1 files for older years, Binance BTC / ETH futures. Live: a demo-only forward
test bot on the FTMO demo (`live/`). Goal of V2: a library of research-based strategies and a
portfolio of them that balances itself across market regimes.

## Specs are the source of truth

All trading rules live in `docs/`. Code implements them; it does not reinterpret them.

| File | Contents |
|---|---|
| `docs/confluences.md` | Swings, trend, BOS, strong-move filter, zone validation, FVG, OB, breaker, BPR, equilibrium, SMT |
| `docs/strategy-session-zones.md` | Strategy 1: sessions, session zones, entry sequence, SL/TP, backtest options |
| `docs/strategy-ny-indices.md` | Strategy 2: NY Open index sweep (NAS100/US500, AM/PM windows), entry funnel, SL/TP, backtest options |
| `docs/strategy-no-wick.md` | Strategy 3: no-wick candle in the trend (timeframes, trend source, entry modes, SL at swing, 1R), backtest options |
| `docs/strategy-trend-following.md` | Strategy 4: trend following after Kaufman (breakout / SMA + band / momentum / KAMA / Dunnigan, ATR stop, stop-and-reverse, no TP) |
| `docs/strategy-gap-fade.md` | Strategy 5: fade the index cash-open gap (0.1-1 ATR) to the previous close, stop at the mirror level, exit 16:00 (ROADMAP 11.4) |
| `docs/strategy-opening-range.md` | Strategy 6: opening-range breakout (range / ATR band, session-end exit, narrow-range and tick-volume filters) (ROADMAP 11.10) |
| `docs/strategy-gap-momentum.md` | Strategy 7: gap momentum (opening gap beyond the prior range, day trade) |
| `docs/research-runner.md` | Research runner: data split, grids, scorecard, flags, trial log |
| `docs/live-trading.md` | Phase 7.2: demo forward test (automatic demo orders, risk 0.25 %, daily stop, Live page, Telegram) |
| `docs/risk-management.md` | FTMO rules, risk guidelines, `risk/` components, risk UI page |
| `docs/ARCHITECTURE.md` | Layers, data flow, how the engine steps through time, data sources (histdata.com, MT5) |
| `docs/ROADMAP.md` | What to build next and its status; V1 history in `docs/archive/ROADMAP-v1.md` (step IDs like "ROADMAP 11.4" point there) |

**Knowledge base (background, not rules):** `knowledge/` holds what the trading books in
`00_Literature/Trading` teach: `README.md` (index, how to add a book), `topics/` (synthesis per
subject, incl. the backtest checklist in `topics/testing-and-robustness.md`), `ideas.md` (strategy
idea backlog with IDs I-xx / T-xx and status). Use it when designing or judging a strategy. An idea
becomes a rule only when the user picks it and it is written into a `docs/` spec. Update an idea's
status when it is tested.

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
  data/        DataAdapter interface, histdata.com importer, cache (data/cache/histdata/,
               helpers in data/cache.py), MT5 adapter
  detectors/   Swings, trend, BOS, ATR/strong move, FVG, OB, breaker, BPR, equilibrium, zone validation
  sessions.py  Tokyo/London/New York session clock (DST-aware)
  strategy/    Strategy interface, registry.py, one folder per strategy (_template/ to copy)
  engine/      Backtest loop: steps the base timeframe, feeds views, manages trades in R
  risk/        RiskConfig, prop-firm presets, position sizing, account simulator, Monte Carlo, sweeps
  analytics/   Metrics on R trade lists (win rate, expectancy, drawdown in R, …)
  live/        MT5 connection, login in the Windows Credential Manager, demo-locked orders
  tools/       Command-line tools: data check / show / update, research runner, Monte Carlo,
               portfolio, studies, gap_bucket_study, ai_dispatch (grids in research/grids/)
  ui/          Dash app: chart page (Lightweight Charts in ui/assets/, data from chart_data.py),
               backtest results page, Risk & Prop Firm page
tests/         pytest; mirrors src/ structure
data/raw/      histdata.com M1 files, histdata/<SYMBOL>/DAT_MT_*_M1_*.csv|zip (git-ignored)
docs/          Specs (source of truth)
```

## Commands

```bash
python -m venv .venv            # then activate it (.venv\Scripts\activate on Windows)
pip install -e ".[dev,ui,data,risk,mt5]"
pytest                          # all tests
pytest tests/detectors -q       # one area
ruff check . && ruff format .   # lint + format
python -m backtester.ui.app     # start the Dash app (or restart_app.bat)
python -m backtester.tools.show XAUUSD M5 2026-09-02T13:00 2026-09-02T14:00  # print cached candles
python -m backtester.data.histdata data/raw/histdata/  # import histdata files (all pair subfolders) -> cache
python -m backtester.tools.check XAUUSD GBPUSD GBPJPY NAS100 US500  # data check report (gaps, broken candles, spot check)
python -m backtester.run XAUUSD GBPUSD --start 2026-09-01 --end 2026-09-30  # backtest -> results/<run-id>/
python -m backtester.run NAS100 US500 --start 2026-09-01 --end 2026-09-30 --strategy ny_index_sweep  # strategy 2
python -m backtester.tools.research research/grids/orb.toml [--dev-only] [--retest]  # research runner (docs/research-runner.md)
pip install -e ".[mt5]"           # MetaTrader5 + keyring (Windows only, optional)
python -m backtester.tools.mt5_info      # FTMO symbol names + specs, server clock -> results/trading.json
python -m backtester.tools.feed_compare  # FTMO vs histdata cache, FTMO spreads -> results/feed_compare/
python -m backtester.live.test_orders XAUUSD  # scripted test orders, DEMO accounts only
```

## Testing

- **Test first (user's rule, stricter than before):** before new code is written or existing
  code changes, write a test file with the critical cases (edge cases, extreme values, faulty
  data), then work through them one by one. Never weaken a test afterwards to make it pass.
  A feature is done when its tests pass and the user has marked it done (it can be reopened).
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
