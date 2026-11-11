# Brief: multi-symbol step 1a "bounded observations" (design `docs/design/multi-symbol.md` › A and Delivery 1a)

Read `AGENTS.md` (no-lookahead invariant, SeriesView, layers) and the design; hard limits apply (no commits,
no servers, no `live/`, no `.env`). Test first; never weaken a test.

Build increment 1a exactly as the design describes: the opt-in market-aware strategy capability
(`on_market_candle` or the design's name), the shared-time snapshot provider for reference symbols
(closed candles only up to `now`, readiness / freshness reported, missing candles handled as designed),
the opt-in hook in `engine/backtest.py`, and the runner wiring for an explicit reference-symbol list. No new
trading strategy (a tiny test-only strategy in tests is fine).

Acceptance:
- A no-lookahead test across symbols: appending future candles to any reference series never changes
  earlier orders; a reference candle is visible only after its close.
- DST / different sessions / missing reference candles covered by tests.
- Every existing strategy bit-identical: golden lists unchanged (`tests/golden`), full suite green
  (`python -m pytest -q`, about 9 minutes), ruff clean.
- `docs/ARCHITECTURE.md`: a short section on reference symbols.
Report files, tests, the API a strategy uses, and anything the design left open that you had to decide
(choose the conservative option, list it).
