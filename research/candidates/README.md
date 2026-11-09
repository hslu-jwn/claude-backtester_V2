# Strategy candidates

Unbuilt strategy specifications drafted by the former research department (2026-10-27 to
2026-11-06), copied here when research moved back into this team (the user, 2026-11-09).
`Continue.Research` takes the next one from this list (skill `continue-research`).

They are **inputs, not rules**: a candidate becomes a strategy only through a `docs/strategy-<name>.md`
spec (rules quoted from the JSON, assumptions listed) and a pre-registered grid in
`research/grids/`. None has been run; none is profitable until tested. Research records and
evidence checks: `knowledge/research/` (record paths in the registries are relative to the
archived department, `../archive/research-department-2026-11/Research_Department/`).

Order = the department's priority (higher first). "Cells" = `experiment.total_grid_size`.

| Priority | Candidate | Cells | Record | Note |
|---|---|---|---|---|
| 65 | M15_SHOCK_RESPONSE_BATCH | 48 | R-2026-007 | reviewed |
| 60 | M15_COMPRESSION_BREAK_BATCH | 72 | R-2026-008 | reviewed |
| 58 | M15_WICK_REJECTION_BATCH | 96 | R-2026-009 | reviewed |
| 56 | M15_CLOSE_STREAK_BATCH | 72 | R-2026-010 | reviewed |
| 54 | M15_TREND_PULLBACK_BATCH | 8 | R-2026-011 | reviewed |
| 52 | M15_MEDIAN_CROSS_BATCH | 8 | R-2026-012 | reviewed |
| 50 | M15_OUTSIDE_ENVELOPE_BATCH | 8 | R-2026-013 | reviewed |
| 46 | M15_ROUND_NUMBER_CROSS_BATCH | 4 | R-2026-015 | reviewed |
| 44 | M15_PRIOR_SESSION_EXTREME_CROSS_BATCH | 4 | R-2026-016 | reviewed |
| 42 | M15_EFFICIENCY_TRANSITION_BATCH | 4 | R-2026-017 | reviewed |
| 40 | M15_RSI_EXTREME_ENTRY_BATCH | 4 | R-2026-018 | reviewed |
| 40 | INTRADAY_H1_SHOCK_RESPONSE | 18 | R-2026-004 | blocked: needs an authoritative CFD session calendar (we have none) |
| 38 | M15_USD_BREADTH_TRANSITION_BATCH | 4 | R-2026-019 | reviewed; multi-symbol basket |
| 36 | M15_FX_RELATIVE_STRENGTH_RANK_BATCH | 4 | R-2026-020 | reviewed; multi-symbol basket |
| 34 | M15_EURGBP_RELATIVE_DISLOCATION_BATCH | 4 | R-2026-021 | reviewed; two-symbol basket |
| 33 | M15_SERIAL_DEPENDENCE_TRANSITION_BATCH | 4 | R-2026-023 | reviewed |
| 32 | M15_REALIZED_SEMIVARIANCE_IMBALANCE_BATCH | 4 | R-2026-022 | reviewed |
| 31 | M15_SMA_CROSS_BATCH | 4 | R-2026-024 | reviewed |
| 10 | US500_FINAL30_CONT | 1 | R-2026-001 | parked: stopless |
| 5 | ETF_ABSMOM_12M_LC | 3 | R-2026-001 | parked: monthly ETF, not supported |

Context before building one: all M15 batches are labelled speculative screens (OHLC only,
London-session FX day trades, fixed ATR stop, time exit), the same shape as R014
(`docs/strategy-alternating-path.md`), which failed after costs: gross edges of about +0.025 R
per trade against about 0.2 R costs at a 1-ATR M15 stop. Check the expected gross edge against
that cost level first (`knowledge/research/reports/I52_COST_LIMIT_SCREEN_METHOD_CHECK.md`).
Their evidence is thin by the department's own grading (`knowledge/research/research_registry.csv`
› evidence_class: mostly "legacy_book_context_only", "adjacent" or "adverse prior"); none has
direct published support on M15 FX after costs.
Done / rejected: FX_LONDON_FIX_REV (2026-10-29), M15_ALTERNATING_PATH_BATCH (2026-11-06).
