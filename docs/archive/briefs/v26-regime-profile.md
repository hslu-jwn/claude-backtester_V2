# Brief: regime classifier + "where does a strategy perform best" profile

Context: `docs/regime-classifier.md` (accepted by the user 2026-10-23: build `analytics/regime.py`
exactly as specified there); ROADMAP › V2.6 "Where a strategy performs best" (the user,
2026-10-24: the breakdown is the input for combining strategies, V2.7). Builds on V2.4d:
detrended R per trade (`analytics/detrend.py`), BCa / t bounds (`analytics/bounds.py`),
effective trades (`analytics/effective_n.py`). Pure analytics + one tool + runner wiring.

## What to build

1. **`analytics/regime.py`** exactly per `docs/regime-classifier.md` (rule, config, no
   lookahead, `unknown`), labelling each trade with `regime_trend` (trend_up / trend_down /
   sideways / unknown) and `regime_vol` (high / low / unknown) from the **closed** D1 candles of
   its symbol before its entry. D1 through the symbol's adapter (one read per symbol), the
   UTC-aligned or New York day as `docs/regime-classifier.md` / the data layer define D1 today;
   say which.
2. **`analytics/profile.py`**: for one trade list, a table per **condition**:
   - regime trend x vol (6 cells + unknown), regime trend alone, regime vol alone;
   - symbol and market class (`analytics/market_classes.py`);
   - entry session (Tokyo / London / New York / other, by entry time with `sessions.py`);
   - direction (long / short);
   - weekday of entry.
   Per cell: trades, effective trades, win rate, net R, R per trade, **detrended** net R and R
   per trade, the BCa 90 % lower bound of R per trade (None below 10 trades), max DD in R.
   **Best condition** per dimension = highest detrended R per trade among cells with at least
   `min_trades_best` (30) trades **and** a positive 90 % lower bound; else "none" (state why).
   Also a short list "strongest skill cells" over all dimensions (top 5 by the lower bound).
3. **Tool** `python -m backtester.tools.strategy_profile --strategy <name> [--symbols ...]
   [--start --end] [--set KEY=VALUE]`: runs the strategy (runner, current defaults) on the
   **development period** by default (test period refused without `--allow-test-period`, like
   `tools/entry_screen.py`), writes `results/profiles/<strategy>_<time>/profile.json`,
   `profile.md` (one table per dimension, best condition in bold, the strongest-cells list),
   and one trial-log line (family `<strategy>-profile`). `--all` profiles all 7 registered
   strategies with their default symbols (sequentially; `--workers` for the runner).
4. **Research runner**: the chosen variant's report gets the profile block (development, and
   test once run) + `profile.json`; research cards later read it (V2.5 / V2.6).

## Answers given up front (Opus, 2026-10-24)

- Trades in the warm-up or with `unknown` regime stay in the other dimensions; the regime
  tables show `unknown` as its own row.
- A trade's session = the session that contains its entry time; overlaps (London / New York):
  the later-opened session; outside all sessions -> `other`.
- Detrended per cell uses the per-trade `detrended_r` from `analytics/detrend.py` (drift of the
  whole profiled period per symbol), not a per-cell drift.
- "Best" never picks a cell with fewer than 30 trades, whatever its result.
- Nothing here changes trades, selection, the trial log semantics, the DSR or golden lists.

## Rules

Spec first (`docs/regime-classifier.md` gets an "Implemented" note; a new short
`docs/strategy-profile.md` for the profile), the test-case list at the top of each new test file,
failing tests, then code. Tests: the regime spec's own list (straight line -> trend_up, zigzag ->
sideways, no lookahead: appending future days never changes a past label, entry day's own
candle never used, weekend / DST, short history -> unknown); profile cells sum to the total;
best-cell rule (min trades, positive lower bound, else none); session assignment at the
boundaries. Run only the tests of what you changed (`pytest -q <your test files>
tests/tools/test_research*.py > results\pytest_regime.log 2>&1`); Opus runs the full suite.
Never edit `src/backtester/live/`.

Done = your tests green, `ruff check .` clean, and one real run:
`python -m backtester.tools.strategy_profile --strategy trend_following --symbols XAUUSD >
results\profile_check.log 2>&1` with its regime table and best conditions in the report. Report:
files changed, test count, decisions the spec did not settle, open questions.
