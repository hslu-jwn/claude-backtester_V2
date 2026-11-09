# Brief: scale the per-lot swap by price (the user's decision 2026-11-09, HANDOFF › Open 9 (a))

Read `AGENTS.md` first; its hard limits apply (no commits, no servers, no `live/`, no `.env`). This is
a **cost default change approved by the user on 2026-11-09** ("a").

## Why

`src/backtester/engine/costs.py` `CostConfig.swap_r_nights` charges `nights * swap_*_per_lot` money
per lot (2026 FTMO values at 2026 prices). Real financing is a rate times the notional, so at the
lower index / FX price levels of 2015-2021 the fixed money amount overstates the swap in percent terms
(US500: about 4-5 bp per night instead of about 1.6 bp). Spreads already scale with
`price / reference_price` (rule of 2026-10-16, `spread_price_scaling`); swap gets the same rule.

## Change

- In `swap_r_nights` (and therefore `swap_r`): when `entry > 0`, the symbol has a `reference_price`,
  and the new switch `CostConfig.swap_price_scaling: bool = True` is on, multiply the per-lot money
  part (`usd`) by `entry / reference_price`. The percentage part (`swap_*_pct_year`) is already
  notional-based: unchanged. No `entry` or no reference price: unchanged (today's behaviour).
- Check every caller of `swap_r` / `swap_r_nights` (grep `src/`) passes the entry price; where one
  does not and could, pass it (report each place). Do not touch `src/backtester/live/`.
- Credits (positive swap) scale the same way.
- `docs/risk-management.md` › Costs (swap): one paragraph with "(rule set by the user, 2026-11-09)".

## Tests (write first, in `tests/engine/test_costs.py` or next to the existing swap tests)

1. Entry at half the reference price -> half the per-lot swap in money (R accordingly).
2. `swap_price_scaling=False` -> today's value.
3. No reference price, or `entry = 0` -> today's value.
4. Percentage swap unchanged.
Existing tests that pin swap R at the default config with an entry price different from the reference:
update only their expected numbers (never their logic) and list them.

## Golden lists

Regenerate `python -m backtester.tools.golden --write` (all strategies) and report the trade-count
changes (should be none; R values with swap change).

## Done =

Full suite `python -m pytest -q` green, `python -m ruff check .` clean, golden regenerated. Report the
changed callers, tests updated (file:line), golden changes.
