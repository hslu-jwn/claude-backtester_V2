# Strategy 8: London-fix USD reversal

Registry/folder: `london_fix`. Implements the claimed research submission below on
completed M1 candles. This is an implementation/spec handover for review, not a
research result or approval of profitability. No experiment or holdout is run here.

## Submission

- strategy_id: `FX_LONDON_FIX_REV`
- specification_version: `1.0.0`
- submission_sha256: `8ec6b914e7669cc28b3eeb1008271dae8df264453934d6ce5c099b3d70ae6263`
- Canonical source: `../Shared_Interface/queue/claimed/FX_LONDON_FIX_REV__v1.0.0.json`
  (read-only; digest verified against the submitted bytes).
- Research ID: `R-2026-003`. The source's literature and hypothesis are provenance,
  not additional trading filters. No local copy of the submission or shared schema.

The following quotations are from that submission.

## Entries

`entries.execution_details`:

> Fill at the close of [16:02,16:03), applying V2 costs; never substitute next-bar-open

Use `zoneinfo.ZoneInfo("Europe/London")` to convert the UTC close time to London.
On Monday through Friday, exactly at 16:03:00 London, the just-completed candle
must be the M1 interval [16:02,16:03). Its close is the market order's chart entry
(`SIGNAL_CLOSE`, `Order.limit_fill=False`). In winter this is 16:03 UTC; in summer
15:03 UTC. No later bar substitutes for a missing signal candle.

Fixed quote-convention side map (`math.definitions.side_s`):

> +1 for EURUSD,GBPUSD,AUDUSD,NZDUSD; -1 for USDCHF,USDCAD

Long EURUSD, GBPUSD, AUDUSD and NZDUSD; short USDCHF and USDCAD. All other
symbols, including USDJPY, produce no orders. There is one shared entry/stop code
path parameterized by `Direction` and numeric side.

`entries.restrictions`:

> At most one entry per symbol per Europe/London calendar day

> Skip missing, duplicate, stale, or out-of-order M1 bars

> Skip non-positive, non-finite, or incomplete ATR

> No entry if that symbol already has an open position

> Never enter USDJPY because the primary source identifies yen as the exception

Each strategy instance belongs to one symbol. An emitted order consumes that day's
entry opportunity, including when execution subsequently skips it. An active order
reference blocks entries until the engine's close/skip callback clears it. Queueing
a time exit alone does not clear the open-position guard. Duplicate or out-of-order
timestamps are rejected by the existing `CandleSeries` boundary before strategy
execution; stale/mismatched callbacks and repeated closes produce no order. Missing
bars are not synthesized. Every weekday with the signal bar is eligible, with no
holiday-calendar filter.

## ATR and stop

`math.definitions.atr60_t`:

> WilderATR_60 of true_range_i=max(high_i-low_i,abs(high_i-close_{i-1}),abs(low_i-close_{i-1})) on completed M1 bars

Feed the existing incremental `detectors.atr.Atr` once per completed M1 candle,
including the signal candle, on all available bars (not only entry-window bars).
The shared definition uses high-low for the first observation without a previous
close. Seed with the arithmetic mean of the first 60 true ranges; subsequently
`ATR_t = (59 * ATR_previous + TR_t) / 60`. Fewer than 60 observations, a nonfinite
ATR or ATR <= 0 means no order. OHLC finiteness/consistency is also enforced by
the existing `Candle` boundary. No future data or full-history container reaches
the strategy.

`exits.stop_loss`:

> Long: entry_price-stop_distance_s_t; short: entry_price+stop_distance_s_t; fixed at entry under V2 adverse fill rules

Distance = `stop_atr_multiplier * ATR`. The strategy freezes that stop at entry:
no trailing, widening, resizing, take profit or signal-derived reversal.
`uses_session_break_even=False` disables the engine's optional session break-even.
The existing engine retains tick rounding, fills and adverse gap-stop handling.

## Time exit and force close

`exits.time_exit`:

> Close on the first completed M1 bar ending at entry_time plus holding_minutes

`exits.end_of_session`:

> Force close by 23:55 Europe/London on the entry day

The UTC deadline is the earlier of entry UTC + `holding_minutes` and 23:55 London
on the entry date converted to UTC. At the first candle close >= that deadline,
`LondonFix.exits()` returns the active `Order.ref`. The existing engine closes at
that candle's close with `ExitReason.SIGNAL`. Default holding 360 minutes exits
at 22:03 London; holding 60 exits at 17:03 London. A settings override at 23:00
with holding 360 exits at 23:55 London.

The engine processes the current candle's stop before `on_candle` and `exits`.
Thus a stop and deadline in the same candle use the existing adverse M1 rule;
gaps beyond a stop use the existing worse executable price. There is no TP.

**Data availability limitation:** as in gap fade/opening range, a missing deadline
bar exits on the first available later completed bar. A literal guaranteed fill
by 23:55 cannot be provided if there is no bar at that deadline; a gap extending
overnight can therefore produce a later exit. No price/bar is invented and the
engine is unchanged. End-of-data uses the engine's `END_OF_DATA` close. This
limitation must be reviewed before running the pilot on incomplete session data.

## Configuration

`LondonFixConfig` is a frozen dataclass. Defaults are the submission's baselines;
`force_close_london` is the submission's session deadline.

| Field | Default | Meaning / allowed pilot grid |
|---|---|---|
| `entry_time_london` | `"16:03"` | Exact London M1 close; fixed in pilot |
| `atr_period` | `60` | Submission parameter `atr_period_m1`; fixed in pilot |
| `stop_atr_multiplier` | `4.0` | Positive finite distance multiplier; grid 3, 4, 5 |
| `holding_minutes` | `360` | Positive integer elapsed minutes; grid 60, 180, 360 |
| `force_close_london` | `"23:55"` | London same-day deadline; fixed in pilot |
| `side_map` | `(1., 1., 1., 1., -1., -1.)` | Fixed tuple in `SYMBOLS` order: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCHF, USDCAD |

The numeric tuple represents the immutable symbol-side map and uses the existing
V2 float-tuple settings serialization. Its contents cannot be overridden. Clock
settings must be HH:MM minute boundaries; entry must precede force close.

## Assumptions (decided by Opus, 2026-10-28)

1. Month-end is the last weekday (Monday-Friday) of the calendar month, using the
   London entry date. Add the trade tag `month_end` only on that date. This is
   reporting metadata, never an entry filter. Examples: 2019-05-31 and 2019-08-30.
2. Doubled-cost stress (2x spread, commission, slippage) is a reported number only,
   calculated later from the trades. Nothing is built for it in this step.
3. There is no London-fix holiday calendar: every weekday with the signal candle
   trades. The source edge case "Weekday with bars but no published fix is flagged
   as holiday contamination" cannot be identified automatically without that
   calendar; record the contamination limitation in subsequent reporting.

## Backtest options and research handover

Use `--strategy london_fix` with the six declared symbols. The shared run settings
control costs, warm-up, news/execution restrictions and source selection; no cost
defaults or execution mechanics are changed. The strategy outputs stop-defined R
trades. Equity sizing and portfolio risk belong to the existing risk/account layer,
not to this strategy or its grid. `math.parameters.risk_fraction_equity` baseline
0.0025 requests 0.25% initial equity risk, one position per symbol, at most six
positions / 1.50% aggregate initial stop risk, subject to V2 leverage limits. Those
account-level settings are a later portfolio evaluation responsibility, not enforced
by these single-symbol R backtests.

**Cost discrepancy to report:** `experiment.costs[2]` says:

> No swap because every position closes on the entry day

V2 charges swap when a position crosses 17:00 America/New_York, rather than London
midnight. A 360-minute hold from 16:03 London can cross that rollover. The task
requires unchanged resolved V2 costs; this implementation neither disables nor
overrides swap. The requested no-swap premise is not guaranteed and needs explicit
disclosure in the later experiment envelope.

`research/grids/london_fix.toml` contains exactly 9 combinations, the baseline,
all six symbols, default `min_trades=100` and the four-field submission identity.
Experiment ID `FX_LONDON_FIX_REV__v1.0.0__DEVELOPMENT__1` names the intended first
development experiment; adding the grid does not allocate, publish or execute it.
Do not run the holdout (from 2021-09-14) without later explicit user authorization.

Subsequent evaluation must retain the source's minimum 500 eligible weekdays per
symbol, all nine variants and registered prior trials, pooled daily inference
(correlated symbols), per-symbol gross signs, chronological development halves,
month-end split, doubled costs, stop frequency, removing five best days and matched
random-time benchmarks. Record the source's rejection criteria; the user decides
acceptance. None of these research diagnostics is an additional trading rule or
an experiment executed by this implementation task.

## Submission mapping

Paths below are relative to `src/backtester/` unless prefixed `tests/` or `research/`.
Test names refer to `tests/strategy/london_fix/test_london_fix.py` unless stated.
Deferred rows describe explicitly unimplemented reporting/account responsibilities.

| JSON field / rule | Config / code location | Test / verification |
|---|---|---|
| `market.universe`, fixed `math.definitions.side_s` | `london_fix/config.py: SYMBOLS, SIDE_MAP, side_map`; `LondonFix.on_candle`; `tools/entry_screen.py: STRATEGY_SYMBOLS` | `test_side_map_and_frozen_stop`, `test_unsupported_symbol`, `test_defaults_fixed_map_and_registry` |
| `market.base_timeframe`, `data.required_fields`, half-open M1 intervals | `LondonFix.base_timeframe/timeframes`; `core/models.py: Candle`; exact close check in `on_candle` | `test_exact_signal_close_and_dst`, `test_bad_timestamps_rejected_and_stale_call_skipped` |
| `market.timezone`, `data.preprocessing[0]`, DST edge case | `LondonFix._tz`, `now.astimezone` | `test_exact_signal_close_and_dst` (winter, summer, both transition Mondays) |
| `math.parameters.entry_time_london`, `entries.signal_time` | `LondonFixConfig.entry_time_london`, `LondonFix._entry_time` | `test_exact_signal_close_and_dst`, `test_force_close` |
| `entries.long_condition`, `short_condition`, weekday restriction | `LondonFix.on_candle` side / weekday / exact-time / ATR guards | `test_side_map_and_frozen_stop`, `test_weekend`, `test_incomplete_or_zero_atr` |
| `entries.execution_timing`, `execution_details`, `order_type` | market `Order`, close entry, no `limit_fill` | `test_exact_signal_close_and_dst`, `test_side_map_and_frozen_stop`; contract `test_trades_enter_at_the_close_of_their_candle` |
| `math.parameters.atr_period_m1`, `math.definitions.atr60_t`, preprocessing Wilder ATR | `LondonFixConfig.atr_period`, shared `detectors/atr.py: Atr` | `test_wilder_includes_signal_candle`, `test_side_map_and_frozen_stop` |
| Incomplete / zero / negative / nonfinite ATR restriction | `LondonFix.on_candle` ATR validity guard | `test_incomplete_or_zero_atr`, `test_invalid_atr_skips` |
| `math.parameters.stop_atr_multiplier`, `math.definitions.stop_distance_s_t`, `exits.stop_loss` | config multiplier; one signed stop expression in `on_candle`; no updates | `test_side_map_and_frozen_stop`, `test_wilder_includes_signal_candle` |
| `exits.profit_target=null`, `signal_exit=null` | `Order.take_profit=None`; only deadline close, `uses_session_break_even=False` | `test_side_map_and_frozen_stop`, `test_time_exit_first_available_close` |
| `math.parameters.holding_minutes`, `exits.time_exit`, `maximum_holding` | config holding; UTC `_deadline`; `LondonFix.exits`; existing `engine/backtest.py: _signal_exits` | `test_time_exit_first_available_close` (exact and data gap) |
| `exits.end_of_session`, horizon-crossing edge | config force-close; min of UTC deadlines | `test_force_close`; missing deadline limitation above |
| `exits.priority`, stop/time collision, adverse gap edge | existing engine `_manage_candle` before `_signal_exits` | `test_stop_before_time_exit_and_adverse_gap` |
| `entries.restrictions[0]`, one entry/day | `_entry_day` guard; consumed on order emission | `test_one_entry_per_day_and_open_position_blocks` |
| `entries.restrictions[3]`, `risk.concurrent_positions` (per symbol) | active `_ref`, engine skip/close callbacks | `test_one_entry_per_day_and_open_position_blocks`, `test_closed_and_skipped_callbacks_allow_next_day` |
| Missing signal / holiday without bars edge | exact close equality, no delayed entry | `test_missing_signal_never_uses_later_bar` |
| Duplicate / stale / out-of-order bars, duplicate fix-window edge | existing `core/series.py: CandleSeries` rejects invalid order; callback timestamp guards | `test_bad_timestamps_rejected_and_stale_call_skipped`, `test_one_entry_per_day_and_open_position_blocks` |
| `implementation.edge_cases[4]`, holiday contamination; known gap | assumption 3, no calendar filter or invented holiday tag | `test_weekend`; later disclosure, not automatically identifiable |
| `experiment.robustness_tests[3]`, month-end reporting | `_month_end`, `Order.tags` propagated by engine | `test_month_end_tag` |
| Completed-bar-only definitions, implementation pseudocode, no lookahead | shared `Atr.update(SeriesView)`, incremental `LondonFix.on_candle` | `test_no_lookahead_incremental_prefix`; generic strategy contract prefix test |
| `math.parameters.risk_fraction_equity`, `risk.position_sizing`, `maximum_risk_per_trade`, `gross_exposure_limit`, `leverage`, aggregate `concurrent_positions` | deferred existing account/risk evaluation; requested 0.0025, 6 positions / 1.50%; no strategy money fields | generic contract `test_trade_result_has_no_money_fields`; account configuration is outside i8 |
| `risk.accounting_type=R_STOP_DEFINED` | price-defined fixed stop, engine R results | generic contract `test_trades_are_in_r_with_a_stop_and_an_exit_reason` |
| `experiment.baseline`, parameter domains, `total_grid_size`, multiple testing | `research/grids/london_fix.toml`, existing `tools/research_grid.py` | `test_grid_identity_and_nine_variants`, `test_defaults_fixed_map_and_registry` |
| Fixed tuple/defaults, settings validation and round trip | `LondonFixConfig.__post_init__`; registry and `runner.StrategyConfig` integration | `test_invalid_config`, `test_defaults_fixed_map_and_registry`; generic contract JSON round trip |
| `experiment.costs[0:2]`, `data.dependencies` V2 costs | unchanged shared `EngineConfig/CostConfig`; doubled-cost reporting deferred per assumption 2 | existing cost tests; no cost override in pilot grid |
| `experiment.costs[2]` no-swap premise | not guaranteed; unchanged V2 New York rollover; discrepancy above | later experiment must disclose actual `swap_r` |
| `data.minimum_history`, `experiment.stage_protocol`, robustness / benchmarks / rejection criteria, research limitations | subsequent development evaluation and intake result envelope; fixed split, no holdout here | grid identity test verifies intended DEVELOPMENT identity; no experiment executed |
| `implementation.computational_requirements`, required libraries / structures | incremental shared ATR, ZoneInfo, frozen config / orders, existing runner | prefix test and generic deterministic / settings contracts; caching/logging of runs remains runner-owned |
