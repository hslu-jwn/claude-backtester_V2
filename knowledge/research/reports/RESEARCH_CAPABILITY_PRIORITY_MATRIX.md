# Research capability priority matrix

Date: 2026-11-02  
Status: research planning only; no Shared Interface or V2 implementation change is authorized.

## Decision rule

Prioritize a capability only when it closes an observed scientific-control gap or unlocks a frozen,
source-supported study. Do not build expensive data/execution features merely because a rejected
paper territory used them. Capability support establishes testability, never edge.

| Priority | Capability | Concrete research need | Unlocks | Does not justify | Dependency / acceptance condition |
|---|---|---|---|---|---|
| P0 | Canonical per-trial result manifest and decision checks | V2.6l exposes future declared grid cells but not individual sensitivities, primary/reported selection, decision checks, feedback trace, or scientific disposition | Independent result review, complete trial accounting, resolved-feedback trace | Treating V2.6l partial compatibility as closure; reinterpreting or reopening the failed pilot | Full synthetic acceptance test in `RESULT_ENVELOPE_REVIEWABILITY_PROPOSAL.md` passes using canonical files only; V2.6l gaps in `V26L_RESULT_MANIFEST_COMPATIBILITY_AUDIT.md` are resolved |
| P1 | Versioned authoritative symbol-session calendar | R004's causal expected-M1 predicate cannot distinguish a missing bar from a holiday/closure using OHLC itself; V2 confirmed the capability absent on 2026-11-02 | The already-frozen R004 development-only falsification only after a sourced calendar, fresh compatibility check, and independent review | Queueing R004 to trigger implementation; any run before confirmation; deriving sessions from observed bars | A real declaration reproduces `AUTHORITATIVE_SYMBOL_SESSION_CALENDAR_GATE.md` for the exact universe/interval: source/schedule/exception identities resolve before OHLC; expected minutes are immutable; missing expected M1 fails the run |
| P1 | Typed diagnostic-study route | R-2026-005 cannot be encoded honestly as a stop-defined strategy; research-owned units, endpoints, aggregation, inference, and synthetic result acceptance shape are now frozen | Source-matched diagnostic studies without fabricated trade semantics | Trading or holdout access from a favorable diagnostic | A jointly reviewed route reproduces `r005_diagnostic_result_envelope.json` and preserves the frozen `R005_STATISTICAL_ACCOUNTING_RESOLUTION.md` semantics, exact cells, coverage, costs, warnings, separate run/scientific states, and no-strategy status |
| P1 | Canonical supported-symbol/data-capability declaration | R-2026-005 currently cannot prove its required five-pair universe; V2 mappings are scattered across code, dated prose, and mutable caches | Pre-intake compatibility decisions without silently shrinking a universe | Substitution after seeing results | `R005_DATA_CAPABILITY_DECLARATION_AUDIT.md` fields and synthetic all-five gate pass; versioned list states symbols, snapshot, fields, history, clock, calendar, missingness, and costs |
| P2 | Authoritative signal-time cost semantics and coverage | Cost feasibility/rejection gates need either historically reconstructed executable estimates or explicitly separate conservative stresses | Better pretest rejection and honest stress accounting | Predictive edge when a rule passes; calling current/later assumptions historical observations | `SIGNAL_TIME_COST_CAPABILITY_AUDIT.md` declaration gate passes for the exact universe/components/interval; source identity, side, units, timestamp, gaps and transformations are frozen; historical reconstruction has no fallback |
| P2 | Broker tick-activity semantics | I-44 cannot distinguish update counts from real volume; V2 resampling currently collapses all-unknown histdata activity to zero and loses source identity | A research-only measurement validation and, later, at most one counted A/B | True VWAP, order flow, absorption, or trade direction | A real declaration reproduces `broker_tick_activity_declaration.json` for the exact symbols/interval, then the coverage/clock/stability/proxy study passes; label remains `broker_tick_activity` |
| P3 | Point-in-time event calendar plus actual/consensus/revision data | V2's hashed retrospective schedule supports blackout/splits but discards known-at fields and exposes no consensus/revision history; macro direction requires causal signed surprises | Event studies with true as-of release metadata | Treating the current news CSV or delayed retrospective actual string as point-in-time; a post-M1 tradable drift | `POINT_IN_TIME_EVENT_DATA_CAPABILITY_AUDIT.md`: independent evidence first shows an effect after supported entry latency and event-time costs, then a separate immutable as-of observation snapshot is justified |
| Defer | Treasury instrument, costs, and auction calendar | R006 Treasury-auction pressure is the only screened territory with a fixed interior rule and modern support; V2 has no Treasury instrument/roll/duration contract | A faithful Treasury-specific study if the platform mandate expands | Proxying the effect through DXY, equity indexes, gold, or a yield-sign shortcut | `DEFERRED_PLATFORM_DATA_CAPABILITY_AUDIT.md`: supported Treasury price/contract-roll series, authoritative costs/calendar, and versioned point-in-time auction schedule all exist before design |
| Defer | Cross-sectional constituent/portfolio data | Same-clock evidence ranks hundreds of stocks, while the Aleti–Bollerslev–Siggaard signal requires 272 synchronized characteristic/industry/factor portfolios plus jump/ML transforms and SPY execution; V2 has no point-in-time security master, membership, corporate actions, adjusted returns, borrow, or synchronized portfolio contract | Faithful cross-sectional equity research | A single-index/FX/gold strategy, index-OHLC proxy, or present-day constituent backfill | `DEFERRED_PLATFORM_DATA_CAPABILITY_AUDIT.md`: point-in-time membership/security master, corporate actions, synchronized quotes, immutable portfolio definitions, transforms/models, ETF execution/shorting, and portfolio accounting exist before design |
| Out of scope | Venue tick/order-book and sub-second execution | Modern lead–lag and announcement capture operate in milliseconds | Market-microstructure/execution research | M1 CFD strategies | A different simulator, data license, latency model, and execution mandate would be required |

## Sequencing

1. Jointly review the additive result manifest and diagnostic-study route together, because a study
   route without reviewable cell outputs recreates the same scientific gap. Research sent the
   validated non-executing request as
   `FB_CONTRACT_REVIEWABILITY_PROPOSAL_20261102T173559Z_RESEARCH`; V2 review is pending.
2. Keep R004 capability-blocked after V2 confirmed the authoritative calendar is absent. If that
   capability is later published independently, repeat compatibility and review before handoff;
   schema validity alone is not authorization.
3. Publish a capability declaration before handing off R-2026-005 or any future multi-symbol study.
4. Add P2 fields only with frozen semantic-validation tests; do not infer them from OHLC.
5. Revisit P3/deferred data only after independent evidence passes the candidate-discovery gates.

The former atomic-lifecycle P0 is closed: the failed pilot payload now exists only in canonical
`queue/rejected/` and the terminal result remains immutable. It is retained in the roadmap as a
completed integration lesson, not an active capability request.

No item in this matrix authorizes research to edit jointly owned schemas or V2 code.
