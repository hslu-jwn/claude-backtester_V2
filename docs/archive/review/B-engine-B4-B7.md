# B-engine: B4-B7 implementation report

Implements the decisions in `README.md` section B (rule set by the user, 2026-10-22).
Prepared for independent review; no commit, branch, push or golden rewrite performed.

## Changes per decision

- **B4:** price-scaled adverse slippage on market entries and every non-TP exit,
  including limit-entry stops and gap stops. Limit entries and TP fills remain unslipped.
  Kind C includes signal/time/end-of-data exit draws, weighted per part. Trade results
  and CSV records preserve `limit_fill` so Kind C can exclude limit-entry draws; older
  CSVs without that column retain the market-entry assumption. Spread/commission
  switches do not disable configured slippage; setting symbol slippage to zero does.
- **B5:** only move BE after TP1 when BE lies strictly behind TP1; equality and a BE
  beyond TP1 leave the original stop unchanged, for either direction.
- **B6:** percentage commission uses actual entry and exit fills. Solve BE for the
  remainder's zero net result with fixed/percentage commission and adverse stop
  slippage. The cost filter estimates commission at the actual entry fill, retaining
  chart-entry spread scaling. Entry screening's scalar and vector fill calculations
  follow the same B4/B6 formulas.
- **B7:** gap/open exits include only the open in that candle's excursions, keeping
  prior excursions. Partial TPs retain exposure. SL-first and closed-candle processing
  remain in force, including a TP gap whose candle also reaches the stop.

Specs updated in `docs/ARCHITECTURE.md` (engine costs/excursions) and
`docs/risk-management.md` (costs and Kind C).

## Files changed

- Engine: `src/backtester/engine/backtest.py`, `costs.py`, `trade.py`.
- Analytics: `src/backtester/analytics/entry_screen.py`, `random_fills.py`, `records.py`.
- CSV output: `src/backtester/runner.py`.
- Specs/report: `docs/ARCHITECTURE.md`, `docs/risk-management.md`, this report.
- Tests: `tests/engine/test_user_decisions_b4_b7.py` (new), `test_backtest.py`,
  `test_costs.py`, `test_percentage_costs.py`, `test_signal_exits.py`,
  `test_spread_scaling.py`; `tests/analytics/test_random_fills.py`;
  `tests/strategy/session_zone_sweep/test_targets.py`; `tests/test_runner.py`;
  `tests/ui/test_trades_overlay.py`.

## Existing expectations changed

Each row identifies an existing test, its old and new expected values, and the decision.
Names are unchanged unless the row states a rename. Values are rounded where shown.

| Test | Old → new | Decision |
|---|---|---|
| `tests/analytics/test_random_fills.py::test_time_exit_gets_no_exit_slippage_by_default_but_can_be_configured` (renamed `test_time_exit_gets_exit_slippage_by_default_but_can_be_configured`) | Default signal fill draws **1 → 2**; explicit configured override now tests opt-out **2 → 1** | B4 |
| `tests/engine/test_backtest.py::test_break_even_with_costs_is_0r_net` (renamed `test_gap_through_break_even_with_costs_realizes_gap_loss`) | BE **100.31 → 100.51**; exit chart price **100.31 → 100.50**; net **0 → -0.005R**; gross **0.155 → 0.25R**. The unchanged candle opens at 100.50, below the new BE stop. | B4 |
| `tests/engine/test_backtest.py::test_short_break_even_with_costs_is_mirrored` | BE **99.69 → 99.49**; net still zero | B4 |
| `tests/engine/test_backtest.py::test_long_costs_spread_at_entry_and_commission` | Entry fill **100.25 → 100.35**; TP net **1.876 → 1.836R**; stopped net **-1.124 → -1.204R** | B4 |
| `tests/engine/test_backtest.py::test_short_costs_spread_at_exit` | Entry fill **100 → 99.90**; net **1.876 → 1.836R**; TP exit fill still 95.25 | B4 |
| `tests/engine/test_backtest.py::test_costs_can_be_switched_off_one_by_one` (renamed `test_spread_and_commission_switches_leave_slippage_active`) | Spread off: entry fill **100 → 100.10**, net **1.976 → 1.936R**. Commission off: net **1.90 → 1.86R**. Both off: net **2 → 2 - (0.1 × 100 / 4342.74) / 2.5 R** (scaled slippage remains). | B4 |
| `tests/engine/test_backtest.py::test_two_tps_net_of_costs` | Both TPs: net **1.445 → 1.395R**. BE scenario: stop **100.31 → 100.51**, net **0.5225 → 0.4975R**; remaining half still nets zero | B4 |
| `tests/engine/test_costs.py::test_indices_have_no_commission_so_break_even_is_the_spread[NAS100]` (renamed `test_indices_break_even_is_spread_plus_two_slips_without_commission`) | BE offset **1 → 3** | B4 |
| `tests/engine/test_costs.py::test_indices_have_no_commission_so_break_even_is_the_spread[US500]` (same rename) | BE offset **0.5 → 1** | B4 |
| `tests/engine/test_percentage_costs.py::test_percentage_commission_without_exits_assumes_the_exit_at_the_entry` | BE offset **0.1 → 0.1 / (1 - 0.0005)** = 0.10005002501250625; commission estimate remains 0.05R | B6 |
| `tests/engine/test_signal_exits.py::test_signal_exit_costs_long_bid_short_ask` | Long exit fill **99 → 98.90**, net **-0.625 → -0.725R**. Short exit fill **99.25 → 99.35**, net **0.375 → 0.275R**. | B4 |
| `tests/engine/test_spread_scaling.py::test_break_even_offset_uses_the_scaled_spread` | BE offset **0.0245 → 0.049** (half-scaled spread plus two half-scaled slips) | B4 |
| `tests/strategy/session_zone_sweep/test_targets.py::test_two_tps_order_and_weighted_result` | BE **110 → 110.00506592612038**; spread/commission off still retain two scaled slips | B4 |
| `tests/test_runner.py::test_two_symbols_per_symbol_and_merged_in_time_order` | Per-trade net **1.1912444803883673 → 1.188430008035272R**; combined **2.3824889607767346 → 2.376860016070544R** | B4, B6 |
| `tests/test_runner.py::test_results_folder` | Persisted per-trade net **1.1912444803883673 → 1.188430008035272R**, same updated `NET` constant | B4, B6 |
| `tests/ui/test_trades_overlay.py::test_the_scenario_trade_with_its_chart_positions` | Net **1.1912444803883673 → 1.188430008035272R** (scaled spread/slippage and entry-fill commission) | B4, B6 |
| `tests/ui/test_trades_overlay.py::test_the_settings_panel_settings_reach_the_trades_overlay` | Net with spread/commission off **1.2 → 1.197185596599795R** (entry slippage remains) | B4 |

No existing B5/B7 expected assertions needed changes. New regressions prove those decisions.

## Validation and handoff

- Added `tests/engine/test_user_decisions_b4_b7.py` before production edits. The first
  36 hand-built cases produced **33 failures, 3 passes** against the original code.
  Extended coverage to 66 cases for both directions, equality at TP1, partial exits,
  limit/market entries, percentage plus fixed costs, cost-filter boundaries, entry
  screening, CSV entry-kind round trips, SL-first, and future-prefix stability.
- Focused verification: **410 passed** (9 existing pandas deprecation warnings).
- Full suite: **3606 passed, 5 skipped, 1 xfailed**, 44 existing deprecation warnings,
  199.20 seconds, exit code 0. Output: `results/b-engine-pytest.txt`.
- `ruff check .`: **All checks passed**, exit code 0. Output: `results/b-engine-ruff.txt`.
  `git diff --check` is clean; modified Python files checked/formatted with Ruff.
- `tests/golden/`, `src/backtester/live/`, and `.env` untouched. Opus owns independent
  review, golden regeneration, and final acceptance. No unresolved trading-rule questions.
