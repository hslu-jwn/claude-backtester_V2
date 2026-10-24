# Brief: V2.4d item 9 — prices rounded to the instrument tick in the engine (a setting, then measured)

Context: ROADMAP › V2.4d (9) (accepted by the user 2026-10-23); `docs/review/book-app-requirements.md`
A5; `knowledge/books/pardo-evaluation-optimization.md` ch.6 (tick math). Today the engine
(`engine/backtest.py`, `engine/trade.py`) uses raw float levels (e.g. an SL at 1.234567 on a 5-digit
symbol); only `risk/sizer.py` and `live/` know tick sizes (MT5 `trade_tick_size`,
`results/trading.json` from `tools/mt5_info.py`). Engine code: Opus reviews every line; the
result-changing default is the user's decision after the measurement (same procedure as V2.4d 3
and T-03).

## What to build

1. `SymbolCosts.tick_size: float | None` (None = no rounding) for the symbols in
   `DEFAULT_SYMBOL_COSTS`, from the FTMO values already recorded in the repo (`results/trading.json`
   if present, else `docs/risk-management.md` › Costs tables / `engine/costs.py` comments); list the
   values and their source in the spec. Binance symbols: their exchange tick (or None, say which).
2. `CostConfig.round_to_tick` (bool, default **False** = today exactly). When on, at order fill:
   - market entry: unchanged (a fill at the bid / ask the candle shows is already on a tick);
   - limit entry level, SL, TP1-3: rounded to the tick **in the conservative direction**: SL
     toward the entry (it can only be hit earlier), TP toward the entry (never further than
     planned), a buy limit down / sell limit up (fills no better than planned); the break-even
     level toward the entry as well;
   - R uses the rounded SL distance; a rounding that puts SL or TP on or beyond the entry
     rejects the order like an invalid one today (counted, reason in the run notes).
3. Counter per run: orders whose levels moved by rounding, and the mean move in ticks.
4. Setting in the panel / grid files, spec in `docs/risk-management.md` › Costs.
5. **Measurement** (no default change): `scripts/measure_ticks.py` on the golden setup (7
   strategies, 2023, current defaults) with rounding off / on -> `results/ticks.md` + `.csv`
   (trades, wins, net R, avg R, orders moved, rejected, change). Run it (log file).

## Rules

Spec first, the test-case list at the top of the test file (long / short, SL and TP each side,
limit levels, break-even, a level already on a tick unchanged, rejection when rounding crosses
the entry, `None` tick = no change, off = identical to today), failing tests, then code. With the
default the golden lists stay identical (`python -m backtester.tools.golden --check >
results\golden_v24d9.log 2>&1`). Never edit `src/backtester/live/`.

Done = the tests of what you changed green (`pytest -q tests/engine tests/strategy/test_contract.py
<your new test files> > results\pytest_v24d9.log 2>&1`; Opus runs the full suite), golden identical, `ruff
check .` clean, the measurement table in the report. Report: files changed, test count, decisions
the spec did not settle, open questions.

## Answers given up front (Opus, 2026-10-24)

- Round only the levels the strategy sets (limit entry, SL, TP1-3, break-even level); never a
  market fill, a gap fill at an open or an M1 replay price (those are prices the data showed).
- Tick source order: `results/trading.json` (`trade_tick_size` per FTMO symbol) if present, else
  the cache's digits (10^-digits), else None. Keep the values as a literal table in
  `engine/costs.py` with the date and source in a comment, so the engine never reads
  `results/` at run time.
- A level within 1e-9 of a tick counts as on the tick (float noise is not a move).
- The TP penetration distance (V2.4d 3) is not rounded; it is a threshold, not an order level.
- Break-even level: it sits at the entry plus the cost offset, so that a hit ends at 0R net.
  Round it to the side that keeps a hit at >= 0R net: a long's BE level rounds **up**, a
  short's **down**. (This overrides "toward the entry" in item 2 for the BE level only.)
- Rejected orders (rounding crosses the entry) go through `strategy.on_order_skipped` like the
  cost filter's skips.
