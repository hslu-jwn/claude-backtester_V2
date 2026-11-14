# Brief: Strategy 19 crypto funding carry, research tool (Codex gpt-6.1-sol medium)

Read first: `AGENTS.md`, `docs/strategy-crypto_carry.md` (the spec; its "Rule (frozen)" and "Risk unit"
sections are the source of truth), and the screen that produced the tested numbers:
`research/screens/2026-11-13_i73_crypto_carry_xs_screen.py` (reference implementation; do not edit it).

## What to build

A research tool that turns the frozen weekly rule into one observation per week. No engine strategy, no
registry entry, no UI.

1. `src/backtester/strategy/crypto_carry/__init__.py` and `book.py`: pure functions (no file access):
   - `signal(funding: FundingSeries, monday) -> float | None`: sum of rates with calc time in
     (monday - 7 days, monday]; None if the symbol has < 30 days of funding history before monday or < 21
     rates at or before monday (eligibility, spec › Universe).
   - `pick_legs(signals: dict[str, float], n_leg=4) -> (longs, shorts)`: sort by (signal, symbol name);
     longs = 4 lowest, shorts = 4 highest; fewer than 8 eligible symbols -> None.
   - `week_result(...)`: price return per leg from the close of the M1 bar opening at Monday 00:00 to the
     close of the bar opening Sunday 23:58 (= ending 23:59); funding per leg = sum of rates settled in
     (Monday 00:01, Sunday 23:59] (a short receives a positive rate, a long pays it); a member without its
     entry or exit bar is dropped from its leg, the leg keeps the others; if a whole leg is empty the week is
     skipped (report it). price_bp = mean(long returns) - mean(short returns) in bp; funding_bp = mean(short
     funding) - mean(long funding) in bp; cost_bp = 2 x 2 x `BINANCE_TAKER_FEE` x 1e4 (= 20); net_bp =
     price_bp + funding_bp - cost_bp; r_gross = (price_bp + funding_bp) / 1000, r_net = net_bp / 1000
     (constant `R_BP = 1000.0`, spec › Risk unit).
   - Frozen config as a frozen dataclass `CryptoCarryConfig` with the spec values (n_leg 4, lookback 7 days,
     min history 30 days, min rates 21, R_BP 1000, the 17 symbols in the spec's order). Docstrings cite
     `Spec: strategy-crypto_carry.md › Rule (frozen)`.
2. `src/backtester/tools/crypto_carry.py` CLI:
   `python -m backtester.tools.crypto_carry [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--out DIR] [--update] [--forward]`
   - Prices via `SymbolSources.single(BINANCE_CACHE_DIR, symbols)` (`data/sources.py`) and
     `tools/entry_screen.load_m1`; funding via `engine/costs.load_funding(FUNDING_DIR / f"{sym}.csv")`.
     Do NOT add the 15 symbols to `data/sources.py`, `data/update.py` or `engine/costs.py` tables.
   - Weeks: every Monday with Monday >= start and Sunday exit <= end (end default: the last Sunday whose
     funding is complete for all eligible symbols, i.e. every symbol's funding file reaches its exit).
   - `--out` (default `results/crypto_carry/<UTC timestamp>/`): `trades.csv` (one row per week:
     `entry_time`, `exit_time` (ISO UTC), `r_gross`, `r_net`, `price_bp`, `funding_bp`, `cost_bp`,
     `net_bp`, `longs`, `shorts` (space-separated symbols), `n_long`, `n_short`) and `legs.csv` (week,
     symbol, side, signal, price_bp, funding_bp, dropped). Print weeks, mean net bp, t, sd, worst week, max
     drawdown in R.
   - `--update`: before computing, `data.binance.download_symbol(sym, start_month, this_month, kind="klines")`
     for the 17 symbols (resumable; network). Never called by tests.
   - `--forward`: weeks from Monday 2026-11-16 (`FORWARD_START`, spec › Decisions 3) to the last complete
     week, appended to `research/forward/crypto_carry.csv` (same columns as trades.csv). Append-only: rows
     already in the file are never rewritten; if a recomputed existing week differs from the file by more
     than 1e-9, stop with an error naming the week (data changed under the log).

## Tests first (`tests/strategy/crypto_carry/test_book.py`, `tests/tools/test_crypto_carry.py`)

Hand-built fixtures (tiny FundingSeries via `engine/costs.funding_from_rows`, tiny price frames or a tmp
cache written with `data/cache.write_atomic` + `cache_path`); answers written in the test:
1. signal window: the Monday 00:00 rate is included, the rate at Monday - 7 d 00:00 excluded; a 4 h symbol
   sums every print in the 7 days; < 30 days history or < 21 rates -> None.
2. pick_legs: correct 4 / 4 with 9 symbols; a tie broken by symbol name; 7 eligible -> None.
3. week_result: exact price / funding / cost / net / r numbers for a 9-symbol week; settlement at Monday
   00:00 and next Monday 00:00 not counted, Monday 08:00 and Sunday 16:00 counted; a short receives a
   positive rate; a missing exit bar drops that member only; an empty leg skips the week.
4. no-lookahead: computing the weeks, then appending later funding rows and later price days, never changes
   an already emitted week; a funding row after Monday 00:00 never changes that Monday's signal.
5. forward log: append-only; a changed existing week raises.
6. golden (skip with a clear reason if `data/cache/binance/XTZUSDT` is missing): development 2020-02-17 ..
   2021-09-12 gives 82 weeks, mean net 138.0 bp (abs diff < 0.05); test 2021-09-20 .. 2026-10-25 gives 266
   weeks, mean net 112.0 bp, t 2.93 (abs diff < 0.005) - the screen's numbers.

## Rules

- Hard limits (AGENTS.md): no commits, branches, pushes; no server or long-running process; no credentials;
  never edit `src/backtester/live/` or `.env`; tests write only to `tmp_path`.
- No lookahead (AGENTS.md › Invariant #1). Times in UTC.
- Unclear rule: stop and report it with the spec line, do not guess.
- Done = the new tests pass, `python -m pytest -q -p no:cacheprovider -n 8 tests/strategy tests/tools/test_crypto_carry.py tests/data`
  green, `ruff check src tests` clean. Report: files changed, test results, the golden numbers you got.
