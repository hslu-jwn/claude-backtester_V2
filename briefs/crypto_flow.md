# Brief: Strategy 20 crypto taker-flow sort, research tool (Codex gpt-6.1-sol medium)

Read first: `AGENTS.md`, `docs/strategy-crypto_flow.md` (the spec; "Rule (frozen)", "Risk unit" and "Build" are the
source of truth), the reference implementation that produced the tested numbers,
`research/screens/2026-11-14_i78_crypto_wide_factors_screen.py` (functions `load`, `week_rows`, `spread`, `test`;
do not edit it), and the downloader `research/screens/2026-11-14_binance_wide_download.py` (do not edit it). The
pattern to copy is Strategy 19: `src/backtester/strategy/crypto_carry/book.py`, `src/backtester/tools/crypto_carry.py`,
`tests/strategy/crypto_carry/test_book.py`, `tests/tools/test_crypto_carry.py`.

## What to build

A research tool that turns the frozen weekly rule into one observation per week. No engine strategy, no registry
entry, no UI.

1. `src/backtester/data/binance_wide.py` (data layer, the only place that knows the file layout):
   - `ROOTS = (Path("data/cache/binance_wide"), Path("data/cache/binance_wide_test"))`.
   - `read_klines(symbol, roots) -> DataFrame` indexed by UTC day (normalized open_time), columns open, close,
     volume, quote_volume, taker_buy_volume; the roots' rows concatenated, duplicate days dropped (keep first),
     sorted. `read_funding(symbol, roots) -> pd.Series` of rates indexed by calc_time floored to the minute
     (an empty Series with a DatetimeIndex when there is no file). `symbols(roots)` = sorted union of CSV stems.
   - `update(roots[-1], end_month, fetch=...)`: for every USDT perp listed under
     `data/futures/um/monthly/klines/` on data.binance.vision (S3 listing with pagination, as in the downloader;
     skip names with "_" and non-USDT), fetch the complete months after the last month already in that symbol's
     CSV in the newest root (or from 2024-01 for a symbol not there yet), for both `klines/<SYM>/1d/` and
     `fundingRate/<SYM>/`, append and rewrite the CSV atomically (`.tmp` then replace). Header detection as in the
     downloader (old files have no header). Network goes through an injectable `fetch` so tests never touch it.
2. `src/backtester/strategy/crypto_flow/__init__.py` and `book.py`: pure functions (no file access, no engine import):
   - frozen dataclass `CryptoFlowConfig` with the spec values: min_bars 60, volume_window 30, min_quote_volume 5e6,
     min_eligible 20, signal_days 7, quantile 5, cost_bp 20.0 (= 2 legs x 2 sides x 5 bp), r_bp 600.0.
   - `eligible_signals(klines: Mapping[str, DataFrame], monday, config) -> dict[str, float]`: the spec's
     eligibility and flow signal (rule 1-2), exactly as `week_rows` in the screen.
   - `pick_legs(signals, config) -> (longs, shorts) | None`: sort by (flow, symbol), n = floor(len / 5);
     long the n highest, short the n lowest; fewer than `min_eligible` eligible symbols (counted before the
     signal NaN drop, as the screen does) -> None.
   - `week_result(monday, longs, shorts, klines, funding, config)`: entry = open of the Monday bar, exit = close of
     the next Sunday bar or the last close in the week; funding in (Monday 00:00, next Monday 00:00) exclusive;
     price_bp, funding_bp, cost_bp, net_bp, r_gross = (price_bp + funding_bp) / r_bp, r_net = net_bp / r_bp; plus
     per-member leg rows. Docstrings cite `Spec: strategy-crypto_flow.md › Rule (frozen)`.
3. `src/backtester/tools/crypto_flow.py` CLI:
   `python -m backtester.tools.crypto_flow [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--out DIR] [--update] [--forward]`
   - Weeks: every Monday with Monday >= start and Sunday exit <= end. Default end: the last Sunday for which the
     newest daily bar of any symbol and the newest funding print of any symbol both reach the exit (complete
     monthly files); never a future week.
   - `--out` (default `results/crypto_flow/<UTC timestamp>/`): `trades.csv` (one row per week: `entry_time`,
     `exit_time` (ISO UTC, exit = Sunday 23:59), `r_gross`, `r_net`, `price_bp`, `funding_bp`, `cost_bp`,
     `net_bp`, `n_long`, `n_short`, `n_eligible`) and `legs.csv` (week, symbol, side, signal, price_bp,
     funding_bp, exit_day). Print weeks, mean net bp, t, sd, worst week, max drawdown in R (like crypto_carry).
   - `--update`: calls `binance_wide.update` first (network; never called by tests).
   - `--forward`: weeks from Monday 2026-11-16 (`FORWARD_START`) to the last complete week, appended to
     `research/forward/crypto_flow.csv` with the same append-only checks as `crypto_carry.append_forward` (reuse it
     if its column handling allows, otherwise copy the logic): rows already in the file are never rewritten; a
     recomputed existing week that differs by more than 1e-9 stops with an error naming the week.

## Tests first (`tests/strategy/crypto_flow/test_book.py`, `tests/tools/test_crypto_flow.py`, `tests/data/test_binance_wide.py`)

Hand-built fixtures (tiny DataFrames / tmp CSV roots); answers written in the test:
1. eligibility: 59 bars before the Monday -> not eligible, 60 -> eligible; median quote volume over the last 30 bars
   below 5e6 -> not eligible; no Monday bar -> not eligible; a missing bar among the last 7 -> no signal; a zero
   7-day volume -> no signal.
2. signal: exact flow value for a hand-built 7-day block; bars on or after the Monday never enter the signal.
3. pick_legs: 25 symbols -> 5 / 5; a tie broken by symbol name; 19 eligible -> None.
4. week_result: exact price / funding / net / r numbers for a small week; funding at Monday 00:00 and next Monday
   00:00 not counted, Monday 08:00 and Sunday 16:00 counted; a long pays a positive rate; a member whose bars stop
   on Thursday exits at Thursday's close.
5. no-lookahead: computing the weeks, then appending later bars and funding, never changes an emitted week; a
   change to a bar on or after a Monday never changes that Monday's signals or legs.
6. data layer: two roots concatenate, duplicate days keep the first root; header and no-header CSVs both read;
   `update` with a fake fetch appends only the missing complete months and rewrites atomically.
7. forward log: append-only; a changed existing week raises.
8. golden (skip with a clear reason if `data/cache/binance_wide` or `data/cache/binance_wide_test` is missing):
   development 2020-01-01 .. 2023-12-31 gives 186 weeks (first Monday 2020-05-25), mean net 145.0 bp (abs diff
   < 0.05), t 3.24 (abs diff < 0.005); test 2024-01-01 .. 2026-10-25 gives 147 weeks, mean net 147.2 bp (abs diff
   < 0.05), t 3.76 (abs diff < 0.005): the screen's numbers.

## Rules

- Hard limits (AGENTS.md): no commits, branches, pushes; no server or long-running process; no credentials; never
  edit `src/backtester/live/` or `.env`; tests write only to `tmp_path`; no network in tests.
- No lookahead (AGENTS.md › Invariant #1). Times in UTC. Layer rule: `strategy/` must not import `engine/` or
  `data/` (pass data in).
- Unclear rule: stop and report it with the spec line; do not guess.
- Done = the new tests pass, `python -m pytest -q -p no:cacheprovider -n 8 tests/strategy tests/tools/test_crypto_flow.py tests/data`
  green, `ruff check src tests` clean. Report: files changed, test results, the golden numbers you got.
