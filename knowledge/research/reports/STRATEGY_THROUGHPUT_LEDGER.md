# Strategy throughput ledger

Updated: 2026-11-05T21:43:00Z

This ledger separates economic families, immutable-ready specification drafts, declared parameter
cells, canonical development results, and queue state. A source, backlog item, conformance test, or
diagnostic row is not counted as a strategy. A parameter cell is a tested rule variant, not an
independent economic hypothesis.

| Family | Specification | Selectable cells | Stage | Development results | Queued |
| --- | --- | ---: | --- | ---: | ---: |
| M15 shock response | `M15_SHOCK_RESPONSE_BATCH` v0.1.0 | 48 | Compatibility preflight | 0 | 0 |
| M15 compression-break response | `M15_COMPRESSION_BREAK_BATCH` v0.1.0 | 72 | Compatibility preflight | 0 | 0 |
| M15 wick-rejection response | `M15_WICK_REJECTION_BATCH` v0.1.0 | 96 | Compatibility preflight | 0 | 0 |
| M15 directional close-streak response | `M15_CLOSE_STREAK_BATCH` v0.1.0 | 72 | Compatibility preflight | 0 | 0 |
| M15 trend-plus-pullback response | `M15_TREND_PULLBACK_BATCH` v0.1.0 | 8 | Compatibility preflight | 0 | 0 |
| M15 rolling-median cross response | `M15_MEDIAN_CROSS_BATCH` v0.1.0 | 8 | Compatibility preflight | 0 | 0 |
| M15 outside-envelope close response | `M15_OUTSIDE_ENVELOPE_BATCH` v0.1.0 | 8 | Compatibility preflight | 0 | 0 |
| M15 alternating-close path response | `M15_ALTERNATING_PATH_BATCH` v0.2.0 | 4 | Development failed; terminally rejected | 1 | 0 |
| M15 round-number single-cross response | `M15_ROUND_NUMBER_CROSS_BATCH` v0.1.0 | 4 | Compatibility preflight | 0 | 0 |
| M15 prior-session extreme outward-cross response | `M15_PRIOR_SESSION_EXTREME_CROSS_BATCH` v0.1.0 | 4 | Compatibility preflight | 0 | 0 |
| M15 directional-efficiency transition response | `M15_EFFICIENCY_TRANSITION_BATCH` v0.1.0 | 4 | Compatibility preflight | 0 | 0 |
| M15 Wilder RSI extreme-entry response | `M15_RSI_EXTREME_ENTRY_BATCH` v0.1.0 | 4 | Compatibility preflight | 0 | 0 |
| M15 synchronized USD breadth-transition basket | `M15_USD_BREADTH_TRANSITION_BATCH` v0.1.0 | 4 | Compatibility preflight | 0 | 0 |
| M15 FX relative-strength rank basket | `M15_FX_RELATIVE_STRENGTH_RANK_BATCH` v0.1.0 | 4 | Compatibility preflight | 0 | 0 |
| M15 EURUSD-GBPUSD relative-dislocation pair | `M15_EURGBP_RELATIVE_DISLOCATION_BATCH` v0.1.0 | 4 | Compatibility preflight | 0 | 0 |
| M15 realized-semivariance imbalance transition | `M15_REALIZED_SEMIVARIANCE_IMBALANCE_BATCH` v0.1.0 | 4 | Compatibility preflight | 0 | 0 |
| M15 serial-dependence transition | `M15_SERIAL_DEPENDENCE_TRANSITION_BATCH` v0.1.0 | 4 | Compatibility preflight | 0 | 0 |
| M15 fast-slow SMA cross | `M15_SMA_CROSS_BATCH` v0.1.0 | 4 | Compatibility preflight | 0 | 0 |
| **Total** | **18 specifications** | **356** |  | **1** | **0** |

R008 also freezes two non-selectable plain-break diagnostic rows. They are counted in multiplicity
and output requirements but not in its 72-cell selectable grid. R023 freezes the auditable common
breadth inventory as the pre-R023 348 cells recorded at `2026-11-05T15:11:35Z` plus its four fixed
cells, totaling 352 selectable cells; those two diagnostics and named legacy trials remain context,
not cells. No
compatibility review, isolated winning cell, or best family may be reported as confirmed profit.
R014 v0.1.0 remains a superseded draft and is not double-counted; v0.2.0 changed no trading rule,
produced one terminally negative development result, and is retained in the canonical rejected queue.

Production target: 20 families and 200-400 declared development cells. Current progress is 18/20
families and 356/200-400 cells: the initial cell-count floor is met, but the economic-family target
is not. This is a quality-gated objective, not a quota. The bounded 2026-11-06 family-19 screen
admitted no candidate; a further batch requires a genuinely distinct OHLC-only mechanism and may
not merely inflate cells or rename an existing response family.
