# R004 canonical result-publication map

Date: 2026-11-02  
Status: frozen research requirement for mutable draft `INTRADAY_H1_SHOCK_RESPONSE__v0.1.0`  
Contract basis: Shared Interface `0.1.0` permits open objects in `statistical_diagnostics` and
`robustness`; V2 committed in `FB_INTRADAY_H1_SHOCK_RESPONSE_20261029T164921Z_e881` to publish the
submission-specific diagnostics in `robustness`.

This map requires compact decision summaries, not trades or return series. It prevents the
preregistered primary from being replaced by a post-result best cell and makes omissions explicit.

## Required canonical location

The result envelope must contain `robustness.r004` with these members:

1. `map_version`: `1`.
2. `calendar`: authoritative calendar name/version, timezone-database version, and the five
   symbol schedules used to classify expected M1 intervals. This is resolved before experiment
   OHLC is read.
3. `data_integrity`: status (`COMPLETED` or `FAILED`), counts by defect type, and any first failing
   symbol/UTC interval. A failed integrity check produces envelope status `TEST_FAILED` and no
   strategy metrics presented as completed.
4. `cell_manifest`: exactly 18 rows, one for every Cartesian tuple of `response_mode` in
   `{CONTINUATION, REVERSAL}`, `event_z_threshold` in `{2,3,4}`, and `holding_hours` in `{1,2,3}`.
   Each row has a stable `cell_id`, complete parameters, event/trade counts, gross and net mean R,
   total net R, stop rate, and both fixed-half net outcomes. Missing values require a status and
   reason. `variants_tried` must equal 18; reporting splits and diagnostic resamples are not extra
   selectable strategy cells.
5. `primary_selector`: pooled `k=3,h=1` raw-q estimate, two-sided day-clustered 95% interval,
   deterministic mapped response mode (`q>0` continuation, `q<0` reversal), and the two counted
   primary cell IDs. Zero or an interval containing zero maps to no advancing mode.
6. `primary_mapped_mode`: mapped cell's mean net R, day-clustered 95% interval, total net R,
   event/trade count, stop rate, fixed-half outcomes, and doubled-cost outcome.
7. `splits`: complete rows for every symbol, event direction, local clock hour, and fixed
   development half, with event count, raw q, gross response, and mode-specific net outcome. Empty
   declared groups remain explicit with zero count.
8. `horizon_samples`: results on each horizon's declared eligible sample and on the fixed common
   three-hour-eligible event subset.
9. `adjacent_sign_gate`: results for exactly `k=2,h=1`, `k=4,h=1`, and `k=3,h=2`; `k=3,h=3`
   remains reported but is not adjacent.
10. `concentration`: primary results after removing the largest one and five profitable events,
    plus March 2020 separately.
11. `placebos`: same-clock non-event and shuffled-event-sign tests.
12. `cost_stress`: resolved-cost baseline and doubled spread, commission, and slippage.
13. `decision_checks`: one row per submitted rejection criterion, with `check_id`, affected
    cell/sample, status in `{COMPLETED, SKIPPED_EARLY_STOP, UNSUPPORTED, FAILED}`, measured values,
    Boolean result where defined, and reason. Omission is not a status.

All raw-q fields are separate from stop-defined executed-R fields. The top-level `metrics` object
may summarize one cell, but `primary_selector` and `primary_mapped_mode` remain authoritative for
the submitted primary decision. If V2 also reports a descriptive best cell, it must label the
selection post hoc and may not give it primary status.

## Skeptical consistency review

- The 18-row manifest matches the declared 2 x 3 x 3 grid; symbol/direction/hour/half rows are
  reporting splits, so they do not create selectable trials.
- Publishing both counted `k=3,h=1` sign cells preserves the two-sided test. The sign selector is
  mechanical and cannot optimize net R.
- The map separates raw price response from executed R and therefore exposes whether the 6-ATR
  safety stop changes the intended fixed-horizon study.
- Explicit statuses prevent an expensive placebo skipped after an early failure from appearing to
  have passed or disappeared.
- Calendar identity and integrity failure details make the frozen expected-M1 predicate auditable
  without inferring closures from the same OHLC file.
- No holdout series, trades, or V2-internal artifacts are required. The same shape can be redacted
  if a separately authorized final holdout is ever run.

Open compatibility dependency: V2 must confirm that the authoritative calendar/version required
by the frozen expected-M1 predicate exists for all five symbols and that it will serialize this
map under `robustness.r004`. Until then R004 remains unqueued.
