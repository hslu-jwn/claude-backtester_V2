# Brief: two-leg trades, increment 2a-1 — group model and group R arithmetic, test-first

Read `AGENTS.md` first; hard limits apply (no commits, no branches, no servers, no `live/`, no `.env`).
You work in the worktree `bt-lane-two_leg`. No backtest or research run. Accepted by the user
2026-11-12 ("Yes, build two-leg"). Spec: `docs/design/multi-symbol.md` › B (read all of section B and
"Tests and compatibility acceptance" items 5-6). If a rule is unclear and not answered below, choose the
reading closest to the design text, write it in the module docstring as an assumption and list it in your
report; stop only if two design sentences contradict each other.

## Scope of this increment (pure model and arithmetic, NO engine)

No change to any existing file except `docs/ARCHITECTURE.md` (one short paragraph). The legacy single-leg
path (`engine/backtest.py`, `engine/trade.py`, `strategy/base.py` `Order` / `TradeResult`) stays untouched;
golden runs must stay identical by construction. The M1 paired engine (synchronized entry, per-leg stops,
exit after a leg stop, residual exposure) is the NEXT increment, not this one.

New files (only these):
- `src/backtester/strategy/group.py`: the order-side model.
- `src/backtester/engine/group_trade.py`: leg cost helpers and group R.
- `tests/strategy/test_group.py`, `tests/engine/test_group_trade.py`.

## Model (`strategy/group.py`), frozen dataclasses

- `GroupLeg`: `symbol`, `direction` (`Direction`), `quantity` (scale-free relative quantity q_i > 0),
  `stop_distance` (initial price stop d_i > 0, price units), optional `take_profit_distance`.
- `EntryPolicy` / `ExitPolicy` enums with only the values the design names and the next increment needs:
  entry `NEXT_OPEN_ALL_OR_NONE` (predeclared synchronized next-open intent; reject the whole group if one
  leg cannot fill), exit `ALL_LEGS_NEXT_OPEN_AFTER_STOP` (a leg stop closes that leg; the other legs exit
  at their next executable open, never at an inferred intraminute price).
- `GroupOrder`: `group_id` (str), `legs` (tuple, ordered, >= 2, distinct symbols), `intent_time` (UTC
  close time of the signal candle), `entry_policy`, `exit_policy`, `expiry_minutes` (> 0), `reason`, `tags`.
  Validation in `__post_init__`: >= 2 legs, distinct symbols, finite positive quantity / stop distance,
  UTC-aware `intent_time`; raise `ValueError` with a clear message.

## Arithmetic (`engine/group_trade.py`)

- `group_basis(legs, values) -> (D, weights)`: `values[i]` = v_i(0), the causal value of one price unit
  per unit quantity at entry (money per price unit, > 0, finite). `D = sum(q_i * v_i * d_i)`,
  `w_i = q_i * v_i * d_i / D`. Reject nonfinite / zero / negative inputs (`ValueError`).
- `LegFill`: per leg the executed facts the engine will supply: `entry_fill`, `exit_fill` (fill prices,
  spread and slippage already inside them), `entry_time`, `exit_time` (UTC), `exit_reason`, and the
  per-cash-flow valuation: `entry_value`, `exit_value` (money per price unit at those timestamps; equal when
  valuation is constant), plus `chart_entry`, `chart_exit` (bid prices for gross).
- `leg_costs(cfg: CostConfig, leg, fill) -> dict` in PRICE units per unit quantity, signed (negative =
  cost): `commission` (via `cfg.commission_price`), `swap` (nights via `costs.rollover_nights` over the
  leg's ACTUAL holding interval, amount via `cfg.swap_r_nights(symbol, direction, risk=1.0, nights,
  entry)`, so credits follow the config's `swap_credit` default), `funding` (only if `cfg` has a funding
  series for the symbol, via `cfg.funding_r` with risk 1.0, else 0), `spread_diagnostic` (`cfg.spread`, for
  reporting ONLY: the spread is already inside the fills and must never be charged twice).
- `group_result(order, fills, cfg, values) -> GroupResult`: per leg normalized money
  `gross_i = sign_i * (chart_exit - chart_entry) * q_i * value` and
  `net_i = sign_i * (exit_fill - entry_fill) * q_i * value + (commission + swap + funding) * q_i * value`,
  each cash flow valued with its own timestamp's value (entry leg of the move at `entry_value`, the change
  to exit at `exit_value`: use `q_i * (exit_fill * exit_value - entry_fill * entry_value)` style so a
  conversion change is causal and explicit; document the formula). Then
  `R_group_gross = sum(gross_i) / D`, `R_group_net = sum(net_i) / D` with D and weights FROZEN from entry.
  `GroupResult` holds: `group_id`, legs, `D`, `weights`, per-leg normalized attribution (`gross_r`,
  `net_r`, cost parts in R), `r_gross`, `r_net`, `exit_reasons`, `residual` (bool, False here), and a
  `reconcile()` check that the leg attributions sum to the group totals (abs tol 1e-12).

## Tests first (hand-built numbers, written before the code)

1. Design example: stop budgets 2 and 1 (e.g. q=1, v=1, d=2 and d=1) -> weights 2/3, 1/3; leg returns +1 R
   and -1 R (in each leg's own stop units) -> group gross +1/3 R exactly.
2. Both legs hit their initial stops at their stop prices, no costs -> group gross exactly -1 R.
3. A leg exit not at its stop -> the group loss is not forced to -1 R (assert the exact value).
4. Validation: NaN, zero, negative quantity / stop / value -> `ValueError`; one leg -> `ValueError`; duplicate
   symbol -> `ValueError`; naive `intent_time` -> `ValueError`.
5. Costs: commission and swap reduce net only; `spread_diagnostic` never changes `r_net` (fills fixed,
   change the spread in a custom `CostConfig` -> `r_net` unchanged); a long leg with swap credit off pays 0
   credit; a Wednesday-crossing hold counts the triple night (use real `CostConfig` symbols, e.g. XAUUSD /
   XAGUSD or USOIL / UKOIL).
6. Conversion change: same prices, `exit_value` != `entry_value` -> the exact hand-computed net R.
7. Reconciliation: leg attributions sum to the totals; weights sum to 1; D and weights do not change when
   the exit values change.
8. Legacy untouched: importing the new modules does not change `strategy.base.Order` / `TradeResult`
   fields (assert their field names equal a literal tuple taken from the current code).

## Done =

`python -m pytest -q -p no:cacheprovider -n 8 tests/strategy/test_group.py tests/engine/test_group_trade.py
tests/engine tests/strategy` green and `python -m ruff check src tests` clean (run from the worktree with
`..\backtester-claude_V2\.venv\Scripts\python.exe`). Docstrings cite `Spec: design/multi-symbol.md › B`.
Report: files, test results, every assumption you made, open questions for the engine increment.
