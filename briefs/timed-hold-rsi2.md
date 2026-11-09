# Brief: RSI(2) signal in strategy 10 `timed_hold` (hypothesis 10, I-03)

Read `AGENTS.md` first (no lookahead, test first, frozen config); hard limits apply (no commits, no
servers, no `live/`, no `.env`). Spec: `docs/strategy-timed-hold.md` › Hypothesis 10 (read it).

## Files

- `src/backtester/strategy/timed_hold/` (config.py, strategy.py), its tests (tests first),
  `docs/strategy-timed-hold.md` › Definitions (bullets for the new fields), new grid
  `research/grids/timed_hold_rsi2.toml`. If the settings-panel widget limit fails, hide the new
  research-only paths in `ui/settings_panel.py` `_panel_symbol` like timed_hold's others.
- Do not change shared code (`session_stats.py` etc.).

## New config fields (defaults = today's behaviour)

- `direction = "rsi"` (new value): long when RSI < `rsi_long_below`, short when RSI > `rsi_short_above`
  (0 / 100 or a disabled side: `rsi_short_above = 0` means no shorts), no trade otherwise.
- `rsi_period: int = 2`, `rsi_long_below: float = 10.0`, `rsi_short_above: float = 90.0`.
- `sma_filter_days: int = 0`: > 0 = longs only when the signal close > the simple mean of the last
  `sma_filter_days` daily closes INCLUDING the signal close; shorts only when below (symmetric).
- The daily closes = the ATR-session closes (`atr_zone` / `atr_open` / `atr_close`, regular sessions
  only, as `SessionStats.prev_close`), plus the entry candle's close as today's close: the signal is
  taken at the entry candle (entry_time = atr_close, e.g. 16:00 New York), so today's close is known.
  RSI = Wilder RSI(`rsi_period`) on those closes; no trade until enough closes exist (and the SMA has
  its days). Keep a bounded deque of closes in the strategy (no shared-code change).

## Grid `research/grids/timed_hold_rsi2.toml` (8 cells; `monkeys/sensitivity/entry_screen = false`,
min_trades 100)

`[base]`: US500, NAS100; zone / atr_zone America/New_York; entry_time = exit_time = 16:00; atr
09:30-16:00; `trading_days = "nyse"`; `skip_nyse_short_days = true`; `direction = "rsi"`;
`stop_atr = 2.0`; `day_filter = "all"`. Use `[[grids]]` families:
- `K` (Kaufman): `rsi_short_above = 90`, `sma_filter_days = 0`; grid `rsi_long_below = [10, 5]` with the
  short threshold mirrored (10 -> 90, 5 -> 95: two families K10 / K5 if a grid cannot pair them) and
  `hold_days = [1, 3]`.
- `C` (Connors-style long only): `rsi_short_above = 0` (no shorts), `sma_filter_days = 200`; same
  `rsi_long_below` / `hold_days` cells.
Primary cell: K, 10 / 90, hold 1. State the family / cell names in a comment. Do not run the grid.

## Tests (first)

RSI(2) value on a hand-built close series (compare with a hand calculation), long / short / none by
threshold, the SMA filter including the signal close, no trade before enough closes, the entry
candle close used as today's close (and no candle after it), shorts disabled, hold_days exit with
the RSI signal, no lookahead (appending future candles never changes earlier orders), existing tests
unchanged.

## Done =

`python -m pytest tests/strategy tests/tools tests/ui tests/engine/test_ticks.py -q` green,
`python -m ruff check .` clean. Report files, tests, anything unclear (quote the spec line).
