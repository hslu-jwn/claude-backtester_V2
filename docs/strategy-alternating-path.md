# Strategy 9: alternating M15 close path

Registry/folder: `alternating_path`. Implements the claimed submission with the
decided assumptions A1-A9 below. This is an implementation handover, with no
profitability claim, experiment run or holdout access. The canonical submission
and shared schemas remain outside V2.

## Submission

- strategy_id: `M15_ALTERNATING_PATH_BATCH`
- specification_version: `0.2.0`
- submission_sha256: `d09d44b96cde33f45b718803eb385cc9a9fd908641d06148ea47de61acff31c5`
- Canonical source: `../Shared_Interface/queue/claimed/M15_ALTERNATING_PATH_BATCH__v0.2.0.json`
  (read-only; SHA256 verified against the original bytes).
- Research ID: `R-2026-014`. Source literature and hypotheses are provenance,
  not additional trading rules.

The following quotes are from the submission.

## Entries

`math.definitions.alternating_event`:

> every delta_j is nonzero and sign(delta_j)=-sign(delta_{j-1}) for j=2..4

`entries.signal_time`:

> Close of London M15 interval ending 09:00 through 13:45 on weekday when signal time plus holding_minutes <=15:00

On the six symbols EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCHF and USDCAD, build
completed M15 bars internally from M1. Five physically adjacent M15 closes
produce four changes. Require strict alternating signs, no exact-zero change,
and total absolute change / prior ATR >= 1.0. Equality qualifies.
FOLLOW_LAST uses the sign of the last change; FADE_LAST uses its negative.
Unsupported symbols produce no orders. Both sides use the same signed formula.

The signal is known only when the final M1 candle closes. Enter at that candle's
close using a market `Order`, `limit_fill=False`, without take profit.
Use `ZoneInfo("Europe/London")` for eligibility; store and compute timestamps in UTC.
There is no holiday filter beyond London Monday-Friday.

## ATR and stop

`math.definitions.atr96_prior`:

> Wilder ATR(96) through t-1 over valid observed true ranges

The first valid M15 bar establishes a previous close without a TR. For later
valid bars, TR = max(high, previous valid close) - min(low, previous valid close),
including across gaps. Seed ATR with the mean of 96 TRs, then recur with
(95 * prior ATR + TR) / 96. Snapshot ATR before processing signal bar t;
the earliest signal is therefore valid bar 98. Require finite positive prior ATR.

Stop = entry - side * stop_atr_multiplier * prior ATR; multiplier is fixed at 1.
Features update even while a position is open. No trailing or session break-even:
`uses_session_break_even=False`. Engine fills, rounding, executable ask stops
for shorts and adverse gap handling remain unchanged. The entry candle cannot
stop the newly entered market trade; management starts on the next M1.

## Time exit

`exits.priority`:

> STOP_LOSS
> TIME_EXIT
> DATA_INTEGRITY_FAILURE

Due = signal close + holding_minutes in elapsed UTC time. On the first available
M1 close >= due, `exits()` requests the active order reference. The unchanged
engine reports this as `ExitReason.SIGNAL`; stops are processed first, so a stop
in the due candle wins. End of data retains the engine's `END_OF_DATA` behavior.

One position per symbol: an emitted order blocks further signals until
`on_trade_closed` or `on_order_skipped` releases its reference. Overlapping events
do not reset the deadline, pyramid or queue a later re-entry. After release,
a fresh qualifying bar may enter using the continuously updated features.

## Configuration

`AlternatingPathConfig` is frozen. Only `response_mode` and `holding_minutes`
vary. Strings are supported by the existing settings and research-grid parser.

| Field | Baseline | Allowed values |
|---|---|---|
| response_mode | FOLLOW_LAST | FOLLOW_LAST, FADE_LAST |
| holding_minutes | 60 | Integer 30 or 60 |
| aggregation_minutes | 15 | Fixed |
| alternating_changes | 4 | Fixed |
| path_activity_atr_min | 1.0 | Fixed |
| stop_atr_multiplier | 1.0 | Fixed |
| atr_period | 96 | Fixed |
| first_signal_london | 09:00 | Fixed |
| last_signal_london | 13:45 | Fixed |
| exit_deadline_london | 15:00 | Fixed |

All fixed fields reject changes; boolean values cannot masquerade as numbers.
`min_warmup_days=5`, `base_timeframe=M1`, `timeframes=(M1,)`.

## Assumptions (decided by Opus; implementation brief)

**A1 M15 bars.** Built inside the strategy from completed M1 candles in 15-minute
buckets [hh:00, hh:15) etc. UTC buckets equal Europe/London wall-clock buckets,
as London's offset is a whole hour. A bar is valid only if its bucket has exactly
15 M1 candles with consecutive ts one minute apart, each with finite positive
OHLC, high >= max(open, close), low <= min(open, close), high >= low. Bar OHLC =
first open, max high, min low, last close. An invalid or incomplete bucket produces
no bar (not observed). V2's cache has unique timestamps, so duplicates cannot
occur; no extra check. The shared CandleSeries boundary already rejects duplicates.

**A2 ATR(96) Wilder, observed sequence.** Over valid bars only. TR_i =
max(high, prev_close) - min(low, prev_close), with prev_close the previous valid
bar's close across any gap. The first valid bar has no TR. Seed = mean of the
first 96 TRs; then ATR_i = (95 * ATR_{i-1} + TR_i) / 96. The ATR used at signal
bar t is the one through t-1, frozen before t; first possible signal is the 98th
valid close. Require finite > 0.

**A3 Event.** At valid bar t, bars t-4..t (five closes) must be physically adjacent:
each bucket start exactly 15 minutes after the previous one. delta_j =
close_{t-4+j} - close_{t-5+j}, j=1..4; every delta nonzero (exact float zero
invalidates) and signs strictly alternate. path_activity = sum |delta_j| /
atr_prior >= 1.0; equality qualifies. last_direction = sign(delta_4).
FOLLOW_LAST trades last_direction; FADE_LAST trades its negative. One code path,
parameterized by side.

**A4 Eligibility.** London weekday (Mon-Fri, London date), M15 close time in London
between 09:00 and 13:45 inclusive, and close time + holding_minutes <= 15:00 London.

**A5 Entry / stop.** Market order at the close of the M1 candle completing bar t
(its close = bar t's close; Order.entry = candle.close, limit_fill=False). Stop =
entry - side * stop_atr_multiplier * atr_prior, multiplier fixed 1.0. No take
profit. The engine fills at that close and checks stops from the next M1 candle;
entry candle cannot stop the trade. Shorts trigger on the ask by the engine's
default short_sl_on_ask. Do not change the engine.

**A6 Time exit.** Due at signal close + holding_minutes. Request exit through
exits() on the first M1 candle whose close time is >= due, normally exactly due.
The engine processes stops before exits(), so a stop in the due bar wins
(STOP_LOSS before TIME_EXIT). Missing M1 candles inside (entry, due] are not
handled in the strategy; they are counted after the run from the cache by a
data-integrity report in a later step.

**A7 One position per symbol.** While the strategy's trade is open, until
on_trade_closed or on_order_skipped, no new signal; no pyramiding or re-entry
from overlapping events. Features (M15 bars, ATR, five-close window) keep updating
while in a trade.

**A8 Cells.** The four response_mode FOLLOW_LAST / FADE_LAST x holding_minutes
30 / 60 cells are separate grid variants, each its own run with isolated state.
Money sizing (0.25%, 1.5% cap) is the existing account layer; strategy outputs R only.

**A9 Warm-up.** min_warmup_days large enough for 98 valid M15 bars over a weekend:
five calendar days. Valid-bar count and ATR guards still apply when data is sparse.

## Backtest options and research handover

`research/grids/alternating_path.toml` contains exactly four independent variants,
baseline FOLLOW_LAST / 60 and min_trades=300. Each variant constructs its own
strategy instances; no cell shares trade state. No sweep is run for this change.
Use `--strategy alternating_path` and the six declared symbols with existing
cost and account settings. No money sizing or cost defaults are added here.

Deferred to later evaluation: cache-based post-entry integrity/failure reports,
full breadth ledger, UTC-half and symbol tables, doubled individual costs,
common five-date removal, 10,000 circular five-date block bootstraps with seed
2026014, and the submission's joint cell/mode promotion gates. Record every trial
and required cell. Final holdout access still requires explicit user authorization.
The strategy alone does not guarantee integrity gates or portfolio sizing.

## Rule to config / code / test mapping

Paths are relative to `src/backtester/strategy/alternating_path/`; tests refer to
`tests/strategy/alternating_path/test_alternating_path.py`.

| Submission / assumption | Config / code | Verification |
|---|---|---|
| Universe, M1 execution | SYMBOLS; AlternatingPath.timeframes/on_candle | test_direction_and_market_stop; test_weekend_and_unsupported |
| A1 complete valid M15 buckets | aggregation_minutes; _M15Aggregator.update | test_complete_aggregation; test_invalid_bucket_is_not_observed |
| A2 observed ATR seed, recursion, gaps | atr_period; _ObservedAtr.update | test_observed_atr_seed_recursion_and_gap |
| A2 prior ATR, 98 valid closes | prior snapshot in on_candle | test_prior_atr_and_first_possible_signal |
| A3 alternation, zero, threshold | alternating_changes, path_activity_atr_min; window guards | test_event_threshold_and_signs; test_event_window_gap |
| A3 mode mapping, A5 signed stop | response_mode, stop_atr_multiplier; signed Order | test_direction_and_market_stop |
| A4 London window, deadline, DST | first/last_signal_london, exit_deadline_london; ZoneInfo | test_london_window_dst; test_weekend_and_unsupported |
| A5 market close, next-bar short stop | Order; unchanged engine | test_engine_short_stop_and_time_exit |
| A6 exact/later due, stop priority | holding_minutes; _due, exits | test_time_exit_and_position_guard; test_engine_short_stop_and_time_exit |
| A7 overlap guard, continuing features | _ref; _forget; callbacks | test_features_continue_and_callback_releases; test_time_exit_and_position_guard |
| A8 isolated four cells, baseline, provenance | research/grids/alternating_path.toml | test_grid_four_cells |
| A9 warm-up | min_warmup_days=5; ATR readiness | test_config_registry_and_settings; test_prior_atr_and_first_possible_signal |
| No lookahead, stale callbacks | only SeriesView.current; incremental state | test_no_lookahead_and_stale_callback |
| Fixed parameters and strings | frozen config, __post_init__; registry/settings | test_config_validation; test_config_registry_and_settings |
| Risk/account, costs and integrity gates | existing account/engine; deferred reports | No strategy money/cost changes; later evaluation required |
