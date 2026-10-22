# Brief A1: validation hardening (V2.4, group A; results must not change)

Findings with evidence: `docs/review/core.md`, `detectors.md`, `engine.md`. Fix ONLY these,
test first (a failing test per finding, then the fix):

- core #1: `SeriesView.window()` must reject a negative `stop` (and keep the existing future
  check); raise the same kind of error the class uses for invalid indices.
- core #2: `Candle` rejects non-finite OHLC.
- core #3: `Candle` rejects naive timestamps (aware ones stay as they are; do not convert
  silently unless the class already normalizes).
- detectors #2: sweep config validation rejects NaN and non-integral counters (keep explicitly
  supported infinite tolerance).
- detectors #3: ATR rejects non-finite input instead of poisoning its state (raise).
- engine #3: generic limit fills require the limit to have been placed before the fill candle
  (pending order known at the previous step); strategies that already do this must behave
  exactly as before.
- engine #4: partial-exit shares must be finite, positive, and leave a positive remainder.
- engine #5: orders with non-finite prices are rejected before level validation.
- engine #10: end-of-data closures call the strategy's `on_trade_closed` like other exits.

Rules: no trading rule, default or existing test expectation changes; raise clear errors
(`ValueError` unless the module already uses a specific type; `LookaheadError` only for real
lookahead). Keep changes minimal.

Done = new tests green; `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests`
green; `ruff check .` clean. Do NOT run the golden check (Opus runs it). Report per finding:
test name, files changed.
