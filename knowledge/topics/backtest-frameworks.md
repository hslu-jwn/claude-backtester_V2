# Backtest frameworks: what open-source engines teach

What four open-source projects do to make backtests realistic and research honest, and what of it fits
our engine (candles, R multiples, FTMO CFDs). Read from their READMEs and docs on 2026-10-15; nothing
here is a rule (rules live in `docs/`). Tooling ideas T-02..T-07 in [../ideas.md](../ideas.md),
ROADMAP Phase 12.

## Sources
| Project | What it is | Licence |
|---|---|---|
| [HftBacktest](https://github.com/nkaz001/hftbacktest) | Tick / order-book backtester for high-frequency trading and market making (Numba, Rust) | MIT |
| [VectorBT](https://github.com/polakowo/vectorbt) | Vectorized research library: thousands of parameter combinations at once (NumPy, Numba) | Apache 2.0 + Commons Clause (no selling products built on it); many tools only in PRO |
| [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) ([backtest docs](https://nautilustrader.io/docs/latest/concepts/backtesting/)) | Event-driven engine, Rust core, Python strategies; same code in backtest and live | LGPL-3.0 |
| [prediction-market-backtesting](https://github.com/evan-kolberg/prediction-market-backtesting) | NautilusTrader extension for prediction markets (Polymarket runnable; Kalshi only fee plumbing, waits for L2 history) | – |

## Lessons

### 1. Reproduce live before optimising (HftBacktest, prediction-market-backtesting)
A backtest should be neither too pessimistic nor too optimistic. Check it first: run it over a period you
traded live and confirm it gives the same fills, costs and result. Only then tune or judge overfitting.
The prediction-market project replays its real account ledger and documents why an exact match fails
(fees, rebates, queue). **For us:** before Phase 7, put demo trades next to the engine's trades on the same
candles (entry, exit, spread, swap, R) and explain every difference (T-06, ROADMAP 12.5).

### 2. Random-entry baseline (VectorBT `from_random_signals`)
Generate many random entry sets (e.g. 1,000, seeded) with the same number of trades, same direction mix,
same stop / target logic and same costs, and compare the strategy with that distribution. A real edge
sits in the top few percent; a result inside the cloud is luck or the exit logic. Cheaper and more direct
than a t-test because it keeps the real costs, hours and volatility. **For us:** a percentile of net R
against random entries in the robustness report (T-02, ROADMAP 12.1).

### 3. Order of high and low inside a candle (NautilusTrader bar execution)
From a bar alone the engine does not know whether the high or the low came first. Nautilus converts each
bar into open → high/low → close and can choose the order adaptively (the extreme nearer the open first).
Our engine assumes SL first when SL and TP are both inside the candle (conservative, CLAUDE.md), which
biases results down for tight stops on 5m-1h. We have M1 data, so the order can be read from the M1 bars
inside the candle, and only a same-M1 conflict stays SL first (T-03, ROADMAP 12.2).

### 4. Fill models with a seed (NautilusTrader `FillModel`, HftBacktest latency / queue)
Nautilus: probability that a limit order fills when price touches it, probability of one tick of
slippage, random seed so runs repeat. HftBacktest: separate feed and order latency, queue position for
resting orders. **For us:** queue and order-book models do not apply (no book in histdata, 5m-1h
candles), but a seeded random slippage on stop and market fills and a "touch is not a fill" option for
limits are a cheap stress test (T-07, ROADMAP 12.6).

### 5. Parameter surfaces as a picture (VectorBT `heatmap`)
Plot a metric over two parameters; a broad plateau is trustworthy, a lone spike is curve fitting. Our
checklist already asks for this (item 7); the robustness report (6.4) checks the plateau on a family but
does not draw it (T-05, ROADMAP 12.4).

### 6. Walk-forward splits (VectorBT splitters)
Rolling or anchored windows: choose on the window, trade the next one, chain the out-of-sample pieces.
Stronger than one split in halves. 11.7 does it by hand for the gap fade; a shared splitter serves 6.1 /
6.2 and every later idea (T-04, ROADMAP 12.3).

### 7. Same code in backtest and live (NautilusTrader)
One strategy class runs in both; differences come only from the venue adapter, which the docs list
(timing, reconciliation, external activity). Our `Strategy` interface plus the MT5 adapter go the same
way; keep it that way in Phase 7.

### 8. Gated path to money (Kalshi bot projects)
Backtest → paper / demo → small live → scale up, each step gated by evidence. Matches 6.1 → demo → Phase 7.
Prediction markets score forecasts with the Brier score; not relevant to our symbols.

## Monte Carlo: the four kinds (user wants a Monte Carlo backtester, 2026-10-15)
"Monte Carlo" means randomising one input many times (seeded) and looking at the spread of results.
What to randomise decides what it answers:

| Kind | Randomises | Answers | Where |
|---|---|---|---|
| A. Trade order | order of whole trading days (or blocks) of the real R list | how deep can the drawdown get with this edge, which risk % is safe, FTMO pass rate | ROADMAP 5.3 (spec `risk-management.md › Monte Carlo`) |
| B. Entries | entry times, keeping trade count, exits and costs | is there an edge at all (vs luck) | T-02 / 12.1 |
| C. Execution | slippage, fills, spread draws | how fragile is the result to worse fills | T-07 / 12.6 |
| D. Price paths | synthetic candles (random walk, block bootstrap of real returns) | does the strategy profit on data with no pattern (it should not) | seeded random walks exist in tests and 11.1 |

A and B are the most useful; together they are the "Monte Carlo backtester" (ROADMAP 12.7).

See also: [testing-and-robustness.md](testing-and-robustness.md), [costs-and-execution.md](costs-and-execution.md).
