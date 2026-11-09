# R-2026-004 pre-handoff compatibility audit

Date: 2026-10-28  
Artifact audited: `strategies/drafts/INTRADAY_H1_SHOCK_RESPONSE__v0.1.0.json`  
Outcome: schema-valid but not handoff-ready; remain `DRAFT` and unqueued.

Update 2026-10-29: the seven questions below were sent as one non-blocking canonical contract
preflight, `FB_R004_COMPATIBILITY_PREFLIGHT_20261029T071523Z_RESEARCH`. This is not a submission,
claim, implementation request, or permission to run. At that 2026-10-29 checkpoint, the draft
remained mutable and unqueued while answers and the first pilot's terminal cleanup were pending;
the later updates below supersede that lifecycle snapshot.

Update 2026-10-29 (canonical answer):
`FB_INTRADAY_H1_SHOCK_RESPONSE_20261029T164921Z_e881` confirms questions 1-4 and 7 as supported,
and questions 6-7's new diagnostics/reporting as buildable. Question 5 is only partly resolved:
V2 can add a run-level integrity failure, but research must freeze what counts as an
**unexpected** missing M1 bar. V2 proposes a missing bar inside regular symbol trading hours,
excluding the daily break, weekends, and exchange holidays visible in the data. The draft remains
mutable and unqueued until that definition is made causal and non-circular, then independently
reviewed. The pilot payload has since moved unchanged to canonical `rejected/`.

Update 2026-11-02 (research definition frozen): an expected M1 interval is now determined only by
an immutable, version-identified authoritative symbol-session calendar resolved before experiment
OHLC is read. The calendar must encode regular opens, daily breaks, weekends, holidays, and early
closes independently of price-bar presence. A calendar-open minute without exactly one fresh OHLC
record is unexpected; an unavailable or ambiguous calendar fails the experiment before metrics.
This rejects the circular phrase “exchange holidays visible in the data.”

## What is already representable

Update 2026-11-03 (acceptance gate executable):
`AUTHORITATIVE_SYMBOL_SESSION_CALENDAR_GATE.md`, its synthetic declaration, validator, and six
focused tests now make the price-free unblock condition explicit. Exact universe/interval
coverage, weekly schedules, holiday/early-close exceptions, timezone/source identity,
OHLC-independent resolution, fail-before-metrics behavior, and post-resolution identity stability
are required. The synthetic fixture is not a V2 capability declaration; R004 remains blocked and
unqueued.

- Every universe member is declared supported, execution is `SIGNAL_CLOSE`, accounting is
  `R_STOP_DEFINED`, and the rule has a non-null fixed stop.
- The Cartesian grid is exactly 2 response modes x 3 thresholds x 3 horizons = 18 cells.
- The draft uses the fixed development/authorized-holdout protocol and requests no custom period.
- Parameter domains, entry sides, exit priority, costs, and primary rejection gates are serialized.

Schema validity establishes envelope shape only. It does not establish that the intake adapter can
implement the custom transformations or return every predeclared diagnostic.

## Corrections made during this audit

1. Entry eligibility now uses only deterministic calendar/session information knowable at the H1
   signal close. A later unexpected missing bar cannot retroactively cancel the entry.
2. An unexpected missing, duplicate, or stale M1 bar while a position is open is now a
   `TEST_FAILED` data-integrity condition. The implementation may not assume the stop survived or
   backfill an exit at the last earlier bar.
3. The undefined robust-scale `epsilon` was removed; zero or non-finite MAD causes a skipped event.
4. The required adjacent-sign cells are exactly `k=2,h=1`, `k=4,h=1`, and `k=3,h=2`. Other cells
   remain reported and counted but cannot be selected as convenient neighbors.
5. The strategy JSON now defines raw direction-normalized `q` rather than relying on the research
   record, defines a supporting symbol by the primary gross-q sign, and requires frozen
   day-clustered 95% confidence gates for primary raw q and mapped-mode net R. Positive point
   estimates alone cannot advance the family.

These are pre-data corrections to a mutable draft. No claimed or submitted artifact was changed.

## Compatibility questions and canonical disposition

V2 answered each point without silently simplifying it:

1. Can the adapter build half-open H1 bars in `Europe/London` for FX/gold and
   `America/New_York` for indices from the same UTC M1 dataset, including the differing DST weeks?
2. Can it maintain a separate causal 60-observation median/MAD window for each symbol and local
   clock hour, appending the current return only after signal evaluation?
3. Can commission, spread, and slippage be converted to the fixed signal-time price-unit event
   floor without using future exit costs or a quantity chosen after the event filter?
4. Can all 18 cells keep independent position/cooldown state so one horizon or response mode never
   suppresses another cell's event?
5. Can an open-position data defect fail the affected experiment and remain visible in canonical
   errors instead of producing partial metrics based on an unknowable OHLC path?
6. Can the canonical result carry every cell, per-symbol/direction/clock-hour splits, fixed halves,
   common-three-hour event subset, day-clustered uncertainty, shuffled-sign placebo, concentration
   exclusions, and doubled-cost outcomes? The result schema permits open diagnostic objects, but
   the producer mapping has not been demonstrated.
7. Can the implementation distinguish the raw direction-normalized forward return from the
   stop-defined executed R result and report both? A frequent 6-ATR stop hit materially changes the
   intended response study and must not be hidden inside one aggregate metric.

## Readiness decision

Do not send the draft to the canonical queue merely because it validates against JSON Schema.
The real Gate 1 pilot is now retained in `rejected/`, and the compatibility preflight has been
answered. The unexpected-missing-M1 definition is frozen in both the research record and mutable
JSON. Do not queue this draft until V2 confirms the required independent calendar/version is
available, the result-publication commitments are reconciled with the live contract version, and
an independent review confirms no new ambiguity. Any change to signal timing,
event sampling, independent cell state, future-data handling, or primary diagnostics requires
another mutable draft revision before review. Only an unchanged, reviewed version may later be
promoted and submitted; no final holdout is authorized.

The publication reconciliation is now frozen in `reports/R004_CANONICAL_RESULT_MAP.md`. It uses
the existing open `robustness` object and requires `robustness.r004` to carry exactly 18 cells, the
mechanical primary selector, separate raw-q/executed-R diagnostics, every submitted decision
check, and explicit skipped/failed statuses. V2 confirmation and independent review remain open.

The exact current JSON candidate is bound for independent review in
`reports/R004_INDEPENDENT_REVIEW_PACKET.md` with SHA-256
`FF8C351894E02DF22163C475470C399F96D3F075A8801CFF4BACC5B2A9E6EA73`. Preparing that packet is not
an independent review and does not relax either external confirmation dependency.
