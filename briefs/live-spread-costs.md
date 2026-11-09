# Brief: raise default spreads / BTCUSD slippage from the live fills (the user's decision 2026-11-09)

Read `AGENTS.md` first; its hard limits apply (no commits, no servers, no `live/`, no `.env`).
This is a **default change the user approved on 2026-11-09** (HANDOFF › Accepted: "apply the
live-spread proposal"; Opus's reading recorded there: raises only).

## Source

`data/spreads/proposal_live_2026-11-09.json` (git-ignored, on this PC) and
`knowledge/research/reports/2026-11-09_live_spread_proposal.md`. Per symbol: `current_fixed_spread`,
`proposed_fixed_spread`, `current_slippage`, `proposed_slippage`, at the symbol's `reference_price`.

## Change (`src/backtester/engine/costs.py`, `_BASE_SYMBOL_COSTS` / the slippage table there)

1. Fixed spread: set `proposed_fixed_spread` (rounded to 2 significant digits, at reference price,
   same units as today) for every symbol whose `proposed_fixed_spread / current_fixed_spread >= 1.05`:
   AUDUSD, EURAUD, EURJPY, GBPJPY, GBPUSD, GER40, JP225, NAS100, UK100, US30, US500, USDCAD,
   USDJPY, XAUUSD, ETHUSD, UKOIL, USOIL (check each ratio in the JSON; skip any below 1.05).
   Every other symbol keeps its spread (no lowering).
2. Slippage: BTCUSD `proposed_slippage` (about 2.5, 2 significant digits). No other slippage changes.
3. A short comment at the changed table: "live fills 2026-11-03..09 (fill probe runs 3+4), raises
   only; the user 2026-11-09; knowledge/research/reports/2026-11-09_live_spread_proposal.md".
4. The spread table (`data/spreads/*.json`) and `CostConfig` switches stay as they are.

## Consequences to handle

- Tests that pin today's cost values (grep `tests/` for the old numbers, e.g. `0.00003` for GBPUSD,
  `1.53` GER40, `1.45` UK100, `0.25` XAUUSD, NAS100 `1.0`, BTCUSD slippage `0.5`): update the expected
  values to the new defaults ONLY where a test pins the default table itself; tests that build their
  own `CostConfig` stay unchanged. Never change a test's logic.
- `docs/risk-management.md` (or wherever the cost table is documented; grep "spread" there): update
  the listed values and add the rule line "(rule set by the user, 2026-11-09)".
- Golden lists: regenerate with `python -m backtester.tools.golden --write` (all strategies; it takes
  a few minutes) because default costs changed; report the trade-count changes per strategy (counts
  should be unchanged or nearly; R values change).

## Done =

`python -m pytest -q` (full suite) green, `python -m ruff check .` clean, golden regenerated.
Report: the old -> new value per symbol, tests updated (file:line), golden changes.
