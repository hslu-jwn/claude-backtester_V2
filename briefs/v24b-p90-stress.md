# Brief V2.4b: measured fill p90 as the stressed cost level (Codex, medium)

Decided by the user 2026-10-28 (`docs/review/fill-analysis-2026-10-28.md`, ROADMAP V2.4b): the
model slippage stays the default; the **stressed cost level** of the robustness report becomes
the **measured p90 slippage per symbol** from the demo fills instead of the flat "costs x 1.5".
Fill report with London fills: `results/fill_report/report.md` (1,511 fills, 23 symbols).

**Test first:** write the tests (cases below) before the code, run them red, then implement.
Never change an existing expected value to make it pass; see item 6.

## 1. The p90 table (data file + writer)

- `src/backtester/tools/fill_report.py`: new option `--write-p90 PATH`. Writes JSON
  `{"source": "fill_report", "since": <ISO>, "until": <ISO of the last fill>, "min_fills": N,
  "symbols": {SYM: {"p90": float, "n": int}}}` from the existing by-symbol table
  (`suggest_p90`, already clipped at >= 0, price units, market fills only). Only symbols with
  `n >= --p90-min-fills` (default 30) go in. Sorted keys, stable output.
- Generate the committed default with the real data (I already ran the export):
  `python -m backtester.tools.fill_report --since 2026-10-27T16:00 --deals results/fill_report/deals.csv --write-p90 src/backtester/analytics/slippage_p90.json`
  (NATGAS, n = 17, stays out). Ship the file as package data like
  `engine/ftmo_spread_median.json` (check `pyproject.toml`).

## 2. `analytics/robustness.py`

- `load_slippage_p90(path=None) -> dict[str, float]` (default: the package file).
- `stressed_net_p90(trades, p90, costs: CostConfig | None = None, fallback_factor=1.5) -> float`:
  per trade
  - symbol in `p90`: `r_net - sum(extra_r)` where for every **market fill** (the entry unless
    `limit_fill`; each exit part whose reason is stop_loss / break_even / signal / end_of_data,
    weighted by its share; take profits get nothing) the extra is
    `max(0, p90[sym] - costs.slippage(sym, trade.entry)) / |entry - initial_stop|`.
    Reuse `random_fills.max_slippage_r(trade, extra, RandomFillsConfig(factor=1.0))` and its
    fill rules; do not copy them.
  - symbol not in `p90`: the old per-trade rule `stressed_net`'s formula with `fallback_factor`.
  - stressed is never above `r_net` (extra clipped at 0).
- `RobustnessConfig`: new `cost_stress_mode: str = "p90"` (`"p90"` | `"factor"`, validated);
  `cost_stress` (1.5) stays as the factor mode and the fallback for unmeasured symbols.
- `trade_robustness`: `net_r_stressed` follows the mode; new keys `cost_stress_mode` and
  `stressed_unmeasured_symbols` (sorted list of traded symbols that used the fallback; empty in
  factor mode -> list of all traded symbols? no: in factor mode leave it `[]`).
- Module docstring: describe the new rule.

## 3. `analytics/scorecard.py`

Same mode switch (`cost_stress_mode` in its config, default "p90", from `RobustnessConfig`),
`net_r_stressed` follows it. Flag text `FLAG_STRESSED` label: "not profitable with stressed
costs".

## 4. Callers and labels

- Find every caller of `trade_robustness`, `stressed_net`, `scorecard` (tools/monte_carlo.py,
  tools/research.py, ...). Where the run's own `CostConfig` is available, pass it (the model
  slippage must be the one the run used); otherwise the default `CostConfig()`.
- Labels: `ui/pages/research.py` "Costs x1.5 net R" -> "Stressed costs net R";
  `ui/research_model.py` flag label "costs x1.5" -> "stressed costs";
  `tools/monte_carlo.py` report line: in p90 mode "Stressed costs (fill p90), net R" plus the
  fallback note "x1.5 for: SYM, ..." when the list is non-empty; in factor mode keep
  "Costs x 1.5, net R"; `analytics/verdict.py` check text "Net R positive with stressed costs".
- Do not touch the engine, `engine/costs.py`, `live/`, or any default other than the stress.

## 5. Test cases (tests/analytics/test_robustness_p90.py, plus fill_report tests)

1. Long market entry, stop-loss exit, risk 10, model slip 1, p90 3 -> 2 market fills x 0.2 R
   = r_net - 0.4.
2. Take-profit exit: only the entry pays (r_net - 0.2).
3. `limit_fill=True` with a TP exit: unchanged r_net.
4. Partial exits: TP part 0.5 + stop-loss part 0.5 -> entry + 0.5 x one exit.
5. p90 below the model slippage -> unchanged r_net (never better than the base).
6. Symbol not in the table -> exactly `stressed_net([t], 1.5)`.
7. Mixed list: sum of 1 + 6.
8. Zero stop distance -> ValueError (as `max_slippage_r`).
9. `RobustnessConfig(cost_stress_mode="x")` -> ValueError; factor mode gives the old numbers.
10. `trade_robustness` reports `cost_stress_mode` and the unmeasured symbols list.
11. Short trade mirrors case 1 (same R result).
12. `TradeRecord`-style objects (exit_reason as string, parts as dicts) work.
13. fill_report `--write-p90`: min-fills filter, JSON shape, symbols sorted, p90 values equal
    the report's `suggest_p90`.
14. `load_slippage_p90()` reads the packaged file; it has GER40, XAUUSD; not NATGAS.

## 6. Existing tests

Tests that pin `net_r_stressed` / the x1.5 behaviour through the default config: make them
pass `cost_stress_mode="factor"` explicitly (they test the factor formula); do **not** edit
their expected numbers. List every such test in the report. Golden trade lists must not change
(this only affects the robustness/scorecard columns).

Done = new tests green, `pytest tests/analytics tests/tools tests/ui -q` green, ruff check +
format clean. Do not commit. Report: files changed, tests added, tests switched to factor mode,
the generated JSON's symbol count.
