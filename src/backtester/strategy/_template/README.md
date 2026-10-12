# Adding a strategy

1. **Spec first:** write `docs/strategy-<name>.md` (rules, defaults, backtest options) and
   list it in CLAUDE.md. Ambiguous rule: ask, never guess.
2. **Copy this folder** to `strategy/<name>/` (the folder name is the strategy's name) and
   rename `TemplateConfig` / `TemplateStrategy`.
3. **Config:** every tunable value is a field of the frozen config dataclass with the
   spec's default and a trailing comment (the settings menu takes its help text from it).
4. **Strategy:** `base_timeframe`, `timeframes`, `on_candle(now, views)` returning
   `Order`s in price terms (entry, SL, TP). Optional class attributes (strategy/base.py):
   `uses_session_break_even = False` (no break-even at the next session start),
   `h4_alignment`, `full_history` (timeframes loaded from the first cached day).
   Strategy-only logic stays in this folder; shared detectors come from `detectors/`.
5. **Register:** one `StrategySpec` entry in `strategy/registry.py`.
6. **Tests** in `tests/strategy/<name>/` first: hand-built candle fixtures with the answer
   written in the test, and a no-lookahead test (appending future candles never changes an
   order already given). `tests/strategy/test_registry.py` checks the contract.
7. **Run:** `python -m backtester.run SYMBOL --start ... --end ... --strategy <name>`.

Not done by the registry yet (ROADMAP C.3, open): the settings menu, presets and the chart's
Trades overlay are strategy 1 only.
