# Brief: golden trade lists (Phase 4 / ROADMAP V2.4, step 1)

Goal: a fixed reference of every strategy's exact trades, so every later refactor or speed-up
can prove it changed nothing. No trading rule, default or existing test changes.

## Build `src/backtester/tools/golden.py` (+ tests first in `tests/tools/test_golden.py`)

- A frozen config dataclass `GoldenConfig` with the reference period
  **2023-01-01 .. 2023-12-31** (UTC days, inclusive, as `run.py` takes them), the folder
  `tests/golden/`, and one entry per registered strategy (`strategy/registry.py`): its
  registry name and symbols. Symbols: the ones its `docs/strategy-*.md` spec names (1: XAUUSD
  GBPUSD GBPJPY; 2: NAS100 US500; 5: NAS100 US500; 6: US30 US2000 NAS100 US500; 7: XAUUSD;
  3 and 4: read their specs; if a spec names no symbols, use XAUUSD GBPUSD NAS100 US500 and say
  so in your report). A test asserts every registered strategy has an entry.
- Settings: exactly what `python -m backtester.run --strategy <name>` uses with no preset
  (`RunSettings` default with `strategy=default_config(name)`, default warm-up, default engine /
  costs), `DEFAULT_SOURCES`, `workers` from the CLI (default: the runner's default).
- `python -m backtester.tools.golden --write [--strategy NAME ...]`: runs and writes
  `tests/golden/<name>.jsonl`, one JSON object per trade in the runner's trade order, with
  every field of the trade record (`TradeResult`; enums by name, datetimes ISO UTC, floats
  with `repr` precision so equality is exact; nested objects flattened or as dicts). Plus
  `tests/golden/manifest.json`: period, symbols, trade count per strategy, git commit, date.
- `python -m backtester.tools.golden --check [--strategy NAME ...]`: runs again and compares
  with the stored files; prints per strategy `identical` or the first differing trade (index,
  field, old, new) and the count difference; exit 1 if anything differs.
- Unit tests (no market data): serialization round trip of a hand-built trade record
  (exact floats, enums, times), the comparison reports the first differing field, missing /
  extra trades are reported, registry coverage. Keep it small; reuse existing helpers
  (`runner.run_backtests`, `registry.default_config`, `trial_log`/`runner` JSON helpers if they
  fit) instead of new copies.

## Then run it

`--write` for all strategies (the data is in `data/cache/`), then `--check` once to prove it
is deterministic. Report: trade count per strategy, runtime per strategy, the check result.

Done = new tests green, `ruff check .` clean, golden files written, check identical. Do not
commit.
