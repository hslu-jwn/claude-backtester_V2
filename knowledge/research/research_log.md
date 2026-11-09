# Research log

## 2026-11-06 — Alternating-path batch terminal rejection

- V2 completed `M15_ALTERNATING_PATH_BATCH` v0.2.0 on the fixed development segment. All four
  cells were negative after costs (net -2,585 to -3,925 R); gross FADE_LAST was positive but
  insufficient after costs, while FOLLOW_LAST was negative. Both modes failed every declared gate
  except the 300-trade minimum.
- The user rejected the batch. Canonical feedback assumptions were answered field-for-field,
  including disclosure that the V2 implementation retained trades with post-entry M1 defects and
  reported them, rather than applying the draft's affected-cell failure rule. The rejected payload
  and result remain immutable; no rerun, same-data redesign, queue resubmission, or holdout.

## 2026-11-05 — Serial-dependence transition family

- Produced and independently reviewed R-2026-023: a four-cell signed lag-one M15 return-correlation
  neutral-to-extreme transition falsification, with consistent/inverted response mappings and
  30/60-minute holds. The two primary sources are explicitly adverse or non-transferable to a
  modern FX edge; the expected result is null.
- The skeptic required and verified executable signal-close suppression, executable-distance sizing,
  deterministic cell invalidation after post-entry data defects, 15:00 flatness, fixed bootstrap and
  date-removal definitions, informative overlap complements, and an auditable 352-cell inventory.
  Bound SHA-256 `7ece150e58f6be9a6d570cacb62de772804f0693e6a85f7506ee6853357dd558`.
  The reviewed draft is not yet compatibility-preflighted; no queue, run, or holdout is authorized.

## 2026-11-05 — Four-cell alternating-path family

- Produced and independently reviewed R-2026-014: a fixed four-change alternating-sign event with
  only follow/fade response and 30/60-minute hold selectable.
- Bound SHA-256 `a422fb6aa8bd74053d506bf1446b9465f4851fb8d8b6ce3df1ee68cf68d07317`
  and sent a non-executing preflight. Throughput is 8 families, 8 reviewed drafts, 316 cells,
  0 results and 0 queued runs; 12 families retain 84 cells of ceiling headroom.

## 2026-11-05 — Compact outside-envelope family

- Produced and independently reviewed R-2026-013: eight cells requiring a strict two-sided
  outside bar and completed close beyond one prior extreme, tested for follow versus fade.
- Bound SHA-256 `7263a68e55a7f8e83ed4ff3067d0a5349ea8424a3cb17bbf40b98f899be6c067`
  and sent a non-executing preflight. Throughput is 7 families, 7 reviewed drafts, 312 selectable
  cells, 0 results, and 0 queued runs; 13 families retain 88 cells of ceiling headroom.

## 2026-11-05 — Compact rolling-median cross family

- Produced and independently reviewed R-2026-012: eight cells crossing/fading a causally frozen
  8/16-bar close median, with contrary adjacent Rosa evidence and explicit I-58 overlap.
- Bound SHA-256 `49fefbb9047ec30079162220322944ed60f79dcda6f977178a388f9601c5e0e5`
  and sent a non-executing preflight. Throughput is 6 families, 6 reviewed drafts, 304 selectable
  cells, 0 results, and 0 queued runs; 14 families retain 96 cells of ceiling headroom.

## 2026-11-05 — Compact-family phase begins

- Produced R-2026-011 as an eight-cell trend-plus-pullback response family: an ATR-material
  eight-change move, then one/two strict opposite changes, tested for resumption versus failure.
- The reused Terra skeptic approved exact event alignment, contiguity, causal ATR, mappings,
  isolated state, compact neighbor gate, bootstrap, overlap disclosure, and source boundary.
- Bound SHA-256 `f048cef9d8c7d6ab0e831fc2cdbe4dfc860b813c9f01e5032b2b539a9940452a`
  and sent a non-executing preflight. Throughput is 5 families, 5 reviewed drafts, 296 selectable
  cells, 0 results, and 0 queued runs. Fifteen more families have 104 cells of ceiling headroom.

## 2026-11-05 — Fourth throughput family and common multiplicity ledger

- Produced R-2026-010 as a distinct multi-bar path family: 72 M15 continuation/exhaustion cells
  defined by 3/5/7 strict same-direction close changes and ATR-normalized net displacement.
- Reused the same Terra skeptic. The mechanics passed, but the first review correctly rejected a
  family-local trial ledger because R010's displacement filter can overlap R007 large-move events.
  R010 now freezes the complete contemporaneous ledger: all 288 selectable R007-R010 cells, R008's
  two diagnostics, and all named legacy trials. Cross-batch promotion uses the full ledger and
  best-family rescue is prohibited.
- Removed an untraceable Davey attribution; only publisher-verified Kaufman metadata and the
  explicitly unopened, edition-unspecified legacy page reference remain.
- Bound the approved draft to SHA-256
  `652dd291c63027292d8a75b7eba75b5c49e6fc9c0bc6f96e20bdc9d6c7eb63f0` and sent a canonical
  non-executing V2 preflight. Throughput is 4 families, 4 reviewed drafts, 288 cells, 0 results and
  0 queued runs; no holdout is authorized.

## 2026-11-05 — Third throughput batch reaches the initial cell floor

- Produced R-2026-009 as a distinct candle-geometry family: 96 selectable M15 wick-rejection
  follow-through/failure cells across six supported FX pairs. Unlike R007 and R008, it conditions
  on one completed candle's wick fraction and close location rather than return shock or a prior-
  range break.
- Verified Kaufman's current sixth-edition bibliographic identity on Wiley, but explicitly recorded
  that the frozen legacy backlog does not identify its edition and that the cited pages were not
  opened. No direct academic or cost-aware M15 FX evidence is claimed; the rule is original and
  speculative with a low prior.
- Reused the same Terra skeptic. It verified causal ATR/geometry timing, every feasible grid
  combination, direction mutual exclusivity, independent 96-cell state, six exact neighbors,
  costs, defects, bootstrap, and multiplicity. An ambiguous optional unconditional benchmark was
  removed rather than retrofitted after review.
- Bound the approved draft to SHA-256
  `065d03c8ce5061480871be263847c6b7fd52d7c515afe5ee98c6df24115ac8b4` and sent a canonical
  non-executing V2 compatibility preflight. No queue, run, result, or holdout is authorized.
- Throughput now totals 3 families, 3 reviewed drafts, 216 selectable cells, 0 canonical
  development results, and 0 queued submissions. This passes the initial 200-cell floor but not the
  20-family target; future breadth must add distinct families rather than gratuitous grid axes.

## 2026-11-05 — Second throughput batch and gap-semantics correction

- Produced R-2026-008 as the second fast-lane family: a schema-valid 72-cell M15 compression-break
  continuation/reversal draft across six supported FX pairs, plus two frozen non-selectable plain-
  break diagnostic rows. It remains an explicitly speculative falsification inside the adverse-
  prior I-32/I-33/opening-breakout family.
- Reused the same Terra quantitative skeptic instead of spawning more agents. The review froze
  independent per-cell virtual portfolios, exact ATR/median/timing/fill/failure rules, exact center
  neighbors, diagnostic isolation, zero-filled weekday bootstrap semantics, and historical trial
  accounting.
- Corrected a cross-batch warm-up defect before handoff. Indicator histories now advance over
  valid observed M15 bars and retain routine daily/weekend gaps through the previous observed close;
  R007 requires a physically adjacent event pair and R008 requires a physically contiguous full
  event window, so a gap cannot itself create either signal. The skeptic independently approved
  the correction.
- Rebound R007 to SHA-256
  `1f78947d609e81057bbfa33e92256a49216a94fdf6bc91265b0aa5c70e2c9af1` and bound R008 to
  `b7886bc04718bd6bd392771d2e7e9007194dee1f0b93bc9710182c10f08cd2bb`. Sent a canonical R007
  correction addendum and R008 compatibility preflight. Neither draft is queued; no run or final
  holdout is authorized.
- Added an explicit throughput ledger: 2 families, 2 drafts, 120 selectable cells, 0 development
  results, and 0 queued submissions. Sources, backlog items, tests, and diagnostic rows remain
  separate from strategy counts.

## 2026-11-04 — Throughput mandate and delegation budget

- Audited the prior continuous run: the coding queue was empty while rapid repeated validation
  units expanded research controls. The user redirected the department toward hundreds of
  testable candidates without weakening the final holdout.
- Added a low-concurrency, reuse-first delegation rule: one research sub-agent by default, related
  follow-ups stay with it, and replacement occurs only after completion, blocking, useful-context
  exhaustion, or a genuine specialty change.
- Established a two-lane funnel. Explicitly speculative, capability-compatible batches may be
  rejected cheaply on development data; only stable, multiplicity-aware survivors receive the
  deeper confirmatory review required for possible final-holdout promotion.
- Froze non-blocking infrastructure hardening and set the first production target to 20 families
  and 200-400 fully declared cells. No V2 code, queue state, result, or holdout was touched.
- Produced R-2026-007 as the first fast-lane batch: one schema-valid 48-cell M15 continuation/
  reversal draft, transparently retained inside the adverse-prior I-61/R004 family. A single
  reusable Terra skeptic reviewed three revisions; index/calendar exposure was removed in favor
  of six previously exercised FX pairs, and exact timestamp, fill, stop, data-failure,
  multiplicity, bootstrap, sizing, and result semantics were frozen. Bound the final review to
  SHA-256 `961df13b96395e8ea356c9f266cbddc353a0750f1085f724552653c284c27835` and sent a non-executing
  canonical V2 compatibility preflight. It is not queued and no run or holdout was authorized.

## 2026-10-27 — Department initialization

- Inspected the umbrella project, V1, active V2 repository, and `bt-live` worktree.
- Kept all existing research and backtester files in place.
- Established a local-only research department and proposed shared file contract.
- Opened a limited, source-driven pilot across distinct research territories.
- Next: review pilot hypotheses skeptically, validate candidate JSON, and seek backtester-team
  agreement before queue submission or implementation.

## 2026-10-27 — Pilot skeptical review

- Reviewed three externally sourced concepts: ETF long/cash time-series momentum, final-30-minute
  continuation, and cross-asset futures/CFD time-series momentum.
- Created two `DRAFT` adaptations only. Neither is queued or claimed to be profitable.
- Parked the cross-asset concept pending a contract-level dataset/roll/accounting specification and
  a compatible stopless, target-notional, daily mark-to-market simulator plan.
- Recorded current V2 incompatibilities in each draft and in the backtester handover.

## 2026-10-27 — Backtester response applied

- Accepted and implemented the V2 team's fourteen contract requests and user decisions D1-D8.
- Fixed the interface at two stages: development and one user-authorized final holdout.
- Added structured parameter domains/grid size, accounting and execution enums, V2 compatibility,
  unit-named result metrics, resolved costs, hashes/commit metadata, and contract-scoped feedback.
- Accepted the one-worker claim/one-hour recovery/immutable experiment-ID proposal in the
  canonical contract. The adapter remains V2 ROADMAP V2.6i and is not operational yet.
- Made day trading on V2 M1 symbols the research priority. The ETF pilot is now a low-priority
  overnight exception; both existing drafts remain unsupported and unqueued.
- Copied the frozen V2 idea backlog with source commit/hash provenance; left the V2 original
  unchanged.
- Added durable `Begin.` / approximate-stop / context-limit / `End.` session control and Gemini
  scratch/logging instructions. No Gemini quota was used.

## 2026-10-28 - First real intake pilot

- Began the user-authorized research session and verified that V2 intake is operational.
- Attempted one narrow Gemini literature lead; it returned `RESOURCE_EXHAUSTED` with zero model
  tokens, was logged, and was not retried after the quota response.
- Independently inspected primary evidence for the London-fix FX reversal and recorded the adverse
  transaction-cost result as the pilot's main falsification risk.
- Pre-registered `FX_LONDON_FIX_REV` v1.0.0: six supported FX symbols, nine variants, signal-close
  entry after the fix window, ATR stop, same-day exit, resolved V2 costs, and no holdout access.

## 2026-10-28 - Asynchronous V2 questions accepted

- Accepted V2's nonblocking question protocol: small conservative assumptions proceed and are
  disclosed; ambiguity that changes a trading rule parks the submission for clarification.
- Added "answer open V2 questions first" to the durable `Begin.` sequence. Replies preserve the
  original field pointer and use `CONFIRMED` or `CORRECTED`; trading-rule corrections require a
  higher immutable specification version.
- Confirmed all three `FX_LONDON_FIX_REV` v1.0.0 implementation assumptions. No strategy rule
  changed and no new queue version was created.

## 2026-10-28 - Intraday shock-response study designed

- Answered two later `FX_LONDON_FIX_REV` assumptions: confirmed real V2 swap when the 360-minute
  variant crosses the 17:00 New York rollover and confirmed the missing-23:55-bar fallback. The
  earlier research premise that every same-London-date exit has no swap was corrected; no trading
  rule, grid, or specification version changed.
- Inspected primary studies with opposing predictions after large moves: same-day continuation on
  abnormal FX days and reversal after intraday commodity-futures turning points, plus index-futures
  cost counterevidence, a causal same-clock individual-stock event study, and gold
  announcement-seasonality context.
- The extended 60-minute stock study showed why net evidence is market-structure dependent: best
  bid/ask costs preserve NASDAQ reversal but remove most NYSE significance, and its 4%-plus-8x
  trigger is much more extreme than the local draft's thresholds.
- A 2014-2019 Nasdaq-100 constituent study confirms that one-minute negative shocks reverse by
  about 31% in the next minute, but quoted spreads nearly triple during those shocks. This supports
  a modern micro-reversal mechanism while weakening transfer to an H1 retail-CFD fill.
- Created `R-2026-004` as a sign-agnostic development study across all five core symbols and nine
  predeclared threshold/horizon cells. It is not a strategy, has no profitability claim, and does
  not authorize final-holdout access.
- Created schema-valid draft `INTRADAY_H1_SHOCK_RESPONSE` v0.1.0 with both response signs, yielding
  18 counted development cells. A skeptic pass changed UTC-clock normalization to per-symbol IANA
  local-clock normalization, excluded DST transition days, and added a fixed five-times-resolved-
  cost absolute event floor so quiet-hour quote noise cannot pass a relative threshold. The draft
  remains unreviewed and unqueued until Gate 1 and V2 compatibility review are complete.
- Reconciled the study and draft on open-to-close H1 event returns and corrected stale prose that
  incorrectly said no draft existed. Added Ederington-Lee's scheduled-news FX-futures evidence as
  adverse horizon context: limited overreaction corrected within minutes, so an H1-close entry
  cannot assume the micro-reversal remains available. The design and 18-cell grid did not change.
- Clarified event independence: every grid cell owns separate position/cooldown state, while an
  entered symbol stays ineligible within that cell through its originally scheduled horizon even
  if the wide safety stop fires early. This prevents overlapping samples and cross-cell leakage.
- Defined the same-clock W60 baseline independently of signal outcomes: structurally complete
  prior event bars and session-ineligible bars remain included, while only predeclared data and
  calendar defects are excluded. This blocks outcome-conditioned baseline trimming.
- Made the event cost floor horizon-independent. It now uses two one-way costs resolved at the
  signal timestamp for event selection; each variant still pays its actual future exit costs.
  This prevents holding-time cost schedules from changing the event population being compared.

## 2026-10-28 - Residual FX session-drift diagnostic designed

- Inspected primary evidence for local-currency depreciation during local trading hours. The
  strongest executable source found most pairs unprofitable after interdealer bid/ask costs;
  EURUSD was the exception. Later work reports significant hourly effects but accessible cost and
  multiple-testing detail is incomplete.
- Treated modern fix-centered evidence as a competing explanation rather than independent support.
  Designed `R-2026-005` to remove opening, closing, fix-adjacent, rollover, overlap, and corrupt-data
  intervals before testing a residual local-versus-US session sign on six evidence-matched pairs.
- Initially fixed 12 pair/session diagnostic cells, quote-sign normalization, breadth/stability
  gates, concentration checks, and doubled-cost rejection. The later pre-data methodology audit
  reduced this to 10 identifiable cells by excluding the coincident Toronto/New York contrast.
  No strategy draft or holdout was authorized.
- Required one full round trip of hypothetical cost for every contiguous eligible session block;
  opening/fix/overlap exclusions cannot be bridged as if a single position remained open.
- Audited the claimed London-fix pilot against its linked feedback. The immutable v1.0.0 still
  contains its superseded no-swap rationale, but V2 explicitly marked real rollover swap as a
  conservative non-revisionary assumption and research confirmed it. Added that provenance to
  R-2026-003 and both registries; the claimed bytes were not edited.
- Corrected R-2026-004's treatment of local prior evidence: frozen I-61 was already tested and
  failed, with continuation dominated by the top 1% of events and only a decaying NAS100 cell near
  significance. Reclassified the stricter design as a priority-40 falsification re-study, retained
  all earlier trials in multiplicity, and added a stop rule against another same-data re-spec.
- A bounded `gpt-5.6-terra` audit of R-2026-005 corrected quote orientation, UTC date anchoring,
  mechanical fix-adjacency removal, block-level direction-normalized cost accounting, and the
  leave-one/leave-five sensitivity definition. The diagnostic remains unqueued and no V2 data or
  implementation was accessed.
- Added `tools/validate_memory.py` with unit coverage for registry/artifact integrity. Its first
  real run found the ETF draft still carried priority 40 after the registry/log had downgraded the
  unsupported overnight exception to 5; corrected the mutable draft to the intended priority 5.
- Extended memory validation to reconcile strategy result counts/statuses with canonical result
  envelopes. Refined R-2026-005's date anchor to the next 17:00 New York FX close so Asia-Pacific
  local sessions align with their corresponding New York comparison session under DST.
- Completed a separate source/specification audit of the claimed London-fix pilot. The full Krohn,
  Mueller, and Whelan article confirms the side map, JPY exception, and fix-to-17:00-New-York
  horizon, while its explicit cost table is even more adverse than the summary: liquidity-demand
  postfix returns are negative for both AUD and GBP after bid/ask costs. Ito and Yamada supports
  waiting past the five-minute benchmark window but not CFD profitability. Retained the pilot only
  as a development integration/falsification exercise and prohibited same-data redesign after a
  failure.
- Re-triaged the frozen backlog under the current day-flat/OHLC/cost-survival rules. I-16 and I-55
  are already covered by the R-2026-004/I-61 event family; I-33, I-47, I-48, and related fast
  breakout/fade rules have book-only support or overlap recorded failures. Created a durable
  no-new-draft decision so later sessions do not recycle these ideas without independent evidence.
- A methodology pass found that R-2026-005's Toronto local session and New York comparison session
  were physically coincident, so the nonoverlap rule made USDCAD unidentifiable. Before any data
  access, reduced the design from six pairs/12 cells to five pairs/10 cells, changed the breadth
  gate to four of five, and fixed the primary pooled series to the complete five-pair date
  intersection. This is a pre-data correction to the diagnostic, not result-driven selection.
- Reconciled R-2026-004's nine threshold-by-horizon response estimates with the draft's 18
  response-mode execution cells. Defined continuation and reversal gross/net returns separately,
  froze the exact session exclusions in the research record, and added a report-only common set of
  three-hour-eligible events so differing cutoff eligibility cannot mimic horizon decay. All 18
  execution cells and the earlier failed I-61 trials remain counted.
- Resolved R-2026-005's ECB timing dependency from official ECB sources: the setting snapshot is
  14:15 Europe/Frankfurt on TARGET business days through 2023-04-02 and 14:10 thereafter; the 2016
  change moved publication only. Froze the TARGET closing-day rule and prohibited masking the
  publication time. The Tokyo/London administrator-calendar question was then resolved with the
  conservative weekday-mask rule recorded below.
- Replaced the unresolved Tokyo/London administrator-calendar dependency with a pre-data
  conservative mask: remove the 09:55 Tokyo and 16:00 London fix-adjacent buckets on every local
  weekday. LSEG's WMR holiday policy is conditional across financial centres and Tokyo fixes are
  bank-specific, so this deterministic over-exclusion is more reproducible than reconstructing a
  rate-publication series from price behavior. Remaining session results stay holiday-contaminated.
- Ran a price-free UTC calendar audit of R-2026-005 across winter, aligned DST, and both
  US/Europe mismatch regimes. All five retained pairs remain identifiable, but the conservative
  masks leave only one or two New York H1 buckets and two to five local buckets per day. Added
  expected bucket-count ranges and required exclusion-count reporting so the result cannot be
  described as broad whole-session drift.
- Confirmed that Shared Interface 0.1.0 has no honest route for a pre-strategy diagnostic: intake
  requires stop-defined executable strategy semantics. Kept R-2026-005 research-local, wrote a
  minimal future study-envelope proposal, and sent a schema-valid non-blocking contract warning.
  The same notice flags the queue README's stale claim that automatic intake is not operational;
  no jointly owned contract text was edited.
- Froze the London-fix pilot's result-review checklist before any envelope arrived. The submitted
  v1.0.0 names 4xATR/360 minutes as baseline but has no mechanical selector among nine cells, so
  only that baseline is primary; a favorable non-baseline-only result is exploratory and cannot
  trigger a selected rule or holdout. Integration success remains independent of profitability.
- Extended memory validation after catching manual UTC drift: research updates must not precede
  creation or be more than five minutes in the future. Added deterministic tests; the focused
  memory/contract suite now has 12 passing tests and both production validators remain clean.
- Re-opened the full Breedon-Ranaldo working paper for R-2026-005. Its Table 1 exactly matches the
  design's pre-exclusion US, Europe, Japan, and Australia hours, and the current five pairs are its
  five USD crosses. Table 2 shows a weaker US-session prior: USDJPY is zero and AUDUSD loses
  significance after GARCH adjustment. Added this asymmetry so local and US aggregates must stand
  separately under the fixed four-of-five gate.
- Closed R-2026-004's pre-submission parameter-selection gap. Froze k=3/h=1 as the sole primary
  diagnostic setting and made response mode a mechanical mapping from the pooled q sign. The other
  16 threshold/horizon-mode cells remain counted robustness evidence and cannot rescue a failed
  primary; the common-event subset must also preserve the primary sign.
- Re-audited US500_FINAL30_CONT's priority. Its fixed development segment does not establish the
  draft's own five-year minimum, and current intake cannot represent next-bar-open, stopless
  unit-notional, close-fill, or early-close-calendar semantics. Downgraded the mutable unqueued
  draft from priority 60 to 10 and marked it parked; no approximation or new trial was created.
- Added a durable canonical open-feedback checker. It only closes an assumption or clarification
  point when a research-produced envelope links through `in_reply_to` and answers the same field
  with CONFIRMED or CORRECTED. Four checker tests pass, the combined focused suite now has 16
  tests, and Begin/validation instructions require the checker; current canonical state is clean.
- Corrected Gate 1 bookkeeping: the first real submission was atomically claimed and canonical
  implementation/testing feedback was observed, so that portion is complete. Completed mapping,
  terminal result publication, crash recovery, and end-to-end run traceability remain open.
- Performed a bounded independent-evidence check for parked I-33 compression breakout. No direct
  peer-reviewed study was found linking pre-existing compression to cost-surviving intraday
  directional breakouts in transferable markets. Adjacent opening-range and multi-month breakout
  papers do not validate the rule; a recent registered daily-squeeze preprint is adverse. Kept
  I-33 parked and created no new research family or draft.
- Performed the planned bounded source audit for I-47/I-48. No independent study matching either
  Davey limit-entry mechanism was found. Daily abnormal-move, opening-reversal, and named-fix
  studies use different events, while two cost-aware intraday FX studies find that generic
  price-rule predictability does not reliably survive realistic spreads. Kept both ideas parked;
  no research family, strategy draft, or additional trial was created.
- Audited R-2026-004 for causal implementability before any handoff. Removed an implicit
  future-data filter that could suppress an entry after seeing a later missing bar, prohibited
  hindsight exits at the last earlier valid bar, and made an open-position M1 defect a
  `TEST_FAILED` condition. Also defined the mandatory adjacent-sign cells exactly and removed an
  undefined robust-scale epsilon. The mutable draft remains unqueued and requires V2 compatibility
  review; no experiment or holdout was run.
- Wrote a pre-handoff compatibility checklist for R-2026-004. JSON Schema can carry the draft, but
  V2 still needs to confirm mixed-local-time H1 aggregation, per-clock robust state, causal
  signal-time cost conversion, independent 18-cell state, data-defect failure, complete diagnostic
  publication, and separation of raw event response from stop-defined executed R. Queueing remains
  blocked on Gate 1 completion and that review.
- Audited I-49's volatility-percentile filter against primary evidence. Prior realized volatility
  can support causal risk scaling, but improvements are not systematic out of sample and the sign
  of conditional intraday performance varies by strategy. Retained volatility rank only as a
  predeclared, multiplicity-counted reporting/risk diagnostic; it cannot rescue a failed
  unconditional strategy, and no new draft was created.
- Converted the generic diagnostic-interface idea into a concrete R-2026-005 handoff blueprint.
  It maps all ten cells, calendar/quote/cost invariants, coverage, inference, and gate outputs while
  explicitly forbidding fabricated stop-R metrics or strategy status. Five joint-review decisions
  remain; the blueprint is research-owned and non-operational under contract 0.1.0.
- Closed a validation blind spot: `validate_contract.py` now checks immutable payloads in all four
  canonical queue stages, not only pending, and rejects the same identity appearing in multiple
  stages. Added coverage for the current claimed pilot, every current draft's grid, and duplicate
  stage identities. The validator remains read-only with respect to canonical queue state.
- Added canonical result-to-submission traceability checks to `validate_memory.py`: every result
  identity must resolve to exactly one retained payload across the four queue stages, and its
  declared submission SHA-256 must match the payload's actual bytes. Added positive, missing-payload,
  and hash-mismatch tests before the first real result arrives.
- Hardened open-feedback closure semantics. A research `CONFIRMED`/`CORRECTED` reply now closes a
  point only when its parent ID resolves uniquely and scope, subject, strategy identity, version,
  and submission hash all match the original envelope. Added tests for mismatched identity,
  missing parent, and duplicate feedback IDs; current canonical feedback remains clean.
- Audited I-52's proposed cost ceiling. Turnover times endpoint cost is useful as a one-sided
  necessary-condition screen, but the fixed 0.13 threshold assumes a gross Sharpe an untested rule
  has not earned. Reframed it as `COST_FEASIBLE_UNKNOWN_EDGE`: conservative costs may reject or
  rank an idea, while passing cannot validate or rescue it. No current study gained another
  optimized cost parameter.
- Audited I-50 meta-labeling. Available evidence is methodological, commercial, inaccessible, or
  contract-dependent rather than an independent cost-aware validation of the proposed V2 use.
  Because strategies 2, 5, and 6 already failed, fitting features to their outcomes would be a
  same-development-data rescue search. Parked I-50 and froze minimum future admissibility rules;
  no model, feature grid, strategy draft, or holdout access was created.
- Extended cryptographic traceability from results to feedback: every identified
  submission-scoped canonical feedback envelope must now resolve to exactly one retained queue
  payload and carry that payload's actual SHA-256. Unknown-submission contract feedback remains
  permitted. Added matching and mismatch tests; the live pilot's feedback chain remains valid.
- Added the corresponding submitted-copy invariant: every submitted strategy registry identity
  must have exactly one retained canonical queue payload, and the research-owned submitted copy
  must be byte-identical to it. Positive and deliberate-drift tests pass; the current London-fix
  research copy and claimed payload share SHA-256 `8ec6b914...ae6263`.
- Reconciled R-2026-004's record and JSON with its compatibility audit: all seven handoff questions
  now appear in the mutable draft's known gaps, and the record's resume point links the full
  checklist rather than naming only two adapter concerns. The draft remains schema-valid and
  unqueued.
- Reviewed the first canonical real-pilot result. FX_LONDON_FIX_REV v1.0.0 is a retained
  development failure: all nine grid cells are net-negative, so the frozen 4xATR/360-minute
  primary necessarily fails and no holdout is authorized. Exploratory selected v0007
  (5xATR/180 minutes) lost 1043.4 R over 10,397 trades and -2267.7 R under doubled costs despite
  four-of-six predicted gross signs and +181.0 pooled gross R. This confirms the source paper's
  adverse cost prior and prohibits same-data redesign.
- Separated scientific failure from integration status. The result preserves the exact immutable
  submission hash, fixed development boundary, run ID, V2 commit, and `NONE` holdout disclosure,
  but it falsely labels an answered assumption open, omits the frozen primary cell's detailed
  metrics from the canonical envelope, and leaves the terminal payload in the claimed queue
  stage. Published a schema-valid non-blocking contract warning; no rerun or strategy revision was
  requested.
- Updated both registries for one `COMPLETED` canonical result and research status
  `development_failed`. Contract, memory, and open-feedback checks pass; the complete focused
  suite now has 30 passing tests.
- Converted the pilot's selected-cell ambiguity into a bounded result-envelope proposal. Future
  canonical results should carry one structured row per tried evaluation, explicitly distinguish
  preregistered primary cells from a post-hoc reported best, publish the metrics needed for each
  declared decision check, record skipped tests structurally, and resolve feedback links at
  publication. The proposal is research-only and does not edit Shared Interface 0.1.0.
- Completed a bounded primary-source audit of I-58 half-life/z-score mean reversion. Positive OU
  evidence applies to market-neutral residuals or pairs, not single raw prices; parameter estimates
  are biased/noise-sensitive near a unit root, and Hurst below 0.5 does not establish tradable
  predictability. Two direct intraday FX studies find that realistic or observed costs erase most
  technical-rule profit. Parked I-58 with no research family, draft, or trial.
- Audited I-38's session-mean “VWAP proxy.” The primary VWAP literature studies execution quality
  for an already-sided parent order, not a directional fair-value signal; the proposed equal-bar
  OHLC mean is not VWAP. No exact cost-aware validation was found, while adjacent opening-session
  evidence and local opening/gap trials are adverse. Parked I-38 and prohibited using it to reopen
  failed opening/gap families; no draft or trial was created.
- Mapped the remaining day-flat backlog into explicit trial families. I-10 is an opening-breakout
  variant; I-12/I-15 are aliases of the R-2026-004/I-61 shock-response family; I-32 and downstream
  zone entries belong with parked I-33; filters/exits/risk layers cannot create or rescue edge.
  The map closes multiplicity loopholes without altering the frozen source backlog or starting a
  new strategy.
- Hardened canonical result semantics after the pilot: development periods must precede the fixed
  cutoff and disclose no holdout; tried variants cannot undercount the submitted grid; selected
  tunable values must belong to submitted domains; variant IDs/chosen ID and grid-summary counts
  must be internally consistent. The current result passes and five new negative tests bring the
  complete focused suite to 35 passing tests.
- Decomposed the exploratory pilot cell's economics from canonical values. Gross expectancy is
  only about +0.0174 R/trade versus 0.1178 R/trade of resolved cost burden; approximately an 85.2%
  cost reduction would be needed just to break even. USDCAD and EURUSD contribute about 78.8% of
  pooled gross R, and month-end net loss is materially worse per trade. These diagnostics reinforce
  rejection and are explicitly not attributed to the frozen primary cell.
- Sent R-2026-004's seven frozen compatibility questions as a schema-valid, non-blocking canonical
  contract preflight. It asks about mixed-local H1 bars, causal per-clock robust state, signal-time
  cost floors, independent 18-cell state, data-defect failure, complete canonical outputs, and raw
  response versus executed R. The v0.1.0 draft remains mutable and unqueued; no claim, run, or
  holdout was requested.
- Audited I-30 round-number levels against primary FX microstructure evidence. Conditional orders
  genuinely cluster near round numbers, but take-profit orders can produce reversals while
  stop-loss orders can propagate continuation and cascades. The studies do not establish an
  OHLC-observable net trading rule, and they do not validate daily pivots or the proposed gold/index
  increments. Retained round-number distance only as a preregistered descriptive annotation; no
  strategy, filter, target rule, or trial was created.
- Audited I-31's M1 time-at-price value area. The closest systematic ES value-area breakout study
  reports a negative, insignificant unconditional mean; a positive one-year thesis requires tick
  volume plus footprint absorption and explicitly omits fees. Because time occupancy is not
  executed volume and the same boundary admits breakout or fade stories, I-31 remains parked with
  no POC target, overlay, strategy draft, or trial.
- Audited I-11's cited Kaufman midday result. The book reports $268/trade gross over 8,404 S&P
  futures trades, but says positions can be held overnight and does not resolve whether the reported
  P&L forces the day-flat close in the frozen adaptation. Costs, event ordering, component
  attribution, reproducible code/data, and independent out-of-sample evidence are absent. Parked
  without splitting or testing its four fade/breakout components.
- Audited I-13 against a direct 1991 programmed replication of Nofri's congestion system. Across
  3,825 daily wheat, gold, and S&P trades, long/short outcomes were not significantly different and
  both S&P sides lost. The original 75% runs rationale is a conditional-probability error, and the
  proposed intraday/ATR version adds unsupported parameters and costs. Rejected the candidate; no
  volatility rescue, draft, or trial was created.
- Audited I-40's exhaustion reversal. Its candle count, RSI threshold, level, reversal candle,
  confirmation, stop, three targets, and timeout are an unvalidated interaction search; adjacent
  candlestick evidence conflicts and closer intraday FX evidence is adverse after costs. Classified
  it inside the I-16/R-2026-004 shock-response multiplicity family and created no draft or filter
  trial.
- Audited I-41 wick rejection and I-42 breakout retest together. Relevant intraday candlestick
  studies are adverse after costs/data-snooping control, daily range-break evidence does not validate
  a retest, and both variants depend on the unsupported I-33 zone. Kept both inside one zone-family
  trial budget; no opposing fade/follow variants, HTF filter, draft, or trial were created.
- Audited I-43's M1 path-length proxy. Properly normalized squared log ranges estimate realized
  volatility; raw summed ranges and direction changes do not measure volume, order flow, or
  absorption and are feed/microstructure sensitive. Restricted any future use to preregistered
  descriptive method validation; no activity filter, directional signal, draft, or trial was created.
- Audited I-44 tick-volume rules and I-45 cost-to-target. I-44 remains blocked: broker update counts
  are feed-specific activity and cannot supply true VWAP, executed volume, or absorption without a
  frozen data-semantic/proxy-validation gate. I-45 is absorbed into I-52's one-sided cost screen;
  its 0.10–0.15 ratio is not universal and passing remains unknown edge. No filter or trial was added.
- Audited I-46's primary source and found a direction-reversing code defect: after assigning long to
  an up-gap, the published return is `(open-close)/open`, so its positive result rewards gap fading,
  not momentum. An independent reproduction report corroborates that the fade sign reproduces the
  headline while the prose-consistent sign reverses it. Rejected the momentum evidence and did not
  reopen the failed gap/opening family.
- Re-ran a research-side quantitative-skeptic pass on mutable R-2026-004. Serialized the previously
  record-only definition of raw direction-normalized q, defined “supporting symbol” by the frozen
  primary gross-q sign, and added mandatory day-clustered 95% confidence gates: raw pooled q must
  exclude zero two-sided and mapped-mode mean net R must be wholly positive. The seven compatibility
  questions are unchanged; the draft remains unqueued and positive point estimates cannot advance it.
- Tightened research-local R-2026-005 after a skeptic pass. Replaced the unsupported claim that its
  five source-matched pairs are already V2-compatible with a future all-five capability gate; a
  missing symbol parks the study rather than changing the primary universe. Local and USD residual
  effects are now two separately adjudicated co-primary tests, each requiring predicted-sign breadth,
  both halves, raw-return exclusion of zero, and a wholly positive doubled-cost net 95% interval.
- Closed the I-62 no-wick retest alias gap using only the frozen imported result. The prior 4,608-
  variant search left 0.4% positive, no symbol-class edge, and a selected gold H1 cluster that failed
  out of sample at -0.02 R/trade. Recorded filters, exit changes, reversed sign, and order-block-style
  relabeling as non-independent rescue attempts; no draft or new trial was created.
- Audited frozen-backlog coverage and found five documentation omissions, not five open candidates:
  completed diagnostics I-01/I-22, R-2026-005 parent I-17, and parked session fades I-47/I-48.
  Added them to the family map and a deterministic checker requiring all 62 imported ideas to appear
  exactly once, preventing silent omission or double-family multiplicity.
- Screened same-clock intraday return recurrence as a genuinely distinct candidate territory. The
  primary Heston–Korajczyk–Sadka effect is a 1,715-stock cross-sectional long–short relation, not an
  aggregate time-series rule; its roughly 3 bp next-day spread is comparable to two half-spreads.
  Transferable futures papers found in the bounded search instead use opening/closing windows already
  represented locally. Recorded no candidate, grid, research draft, or queue submission.
- Screened scheduled macro-announcement response. Primary FX/futures studies show price discovery
  largely within 40–240 seconds, release-time spread deterioration, and direction defined by
  point-in-time consensus surprises rather than the calendar. A sign inferred from the first M1 bar
  is merely another R-2026-004 continuation/fade cell after most adjustment. Classified this as a
  data/microstructure dependency; no strategy, filter, or event grid was created.
- Screened the Europe-open U.S. equity-futures drift. The 2023 RFS paper reports a genuine 1.48 bp
  daily gross ES anomaly in 1998–2020, but the original authors' July 2026 post-publication study
  finds the 02:00–03:00 ET return flat in 2021–2025 across ES, NQ, and YM. Rejected it as a current
  candidate without searching nearby hours or rescuing regimes; no draft or trial was created.
- Added a candidate-discovery ledger with seven pre-local-data admission gates and the three new-
  territory decisions. It separates source interest from test eligibility and prohibits local grids
  from repairing failed transfer, data, latency, cost, stability, or multiplicity gates.
- Registered that program as R-2026-006 with nine opened primary or official follow-up sources. Its
  reviewed outcome is explicitly negative for all three screened territories and has no linked
  strategy specification.
- Extended R-2026-006 with cross-market lead–lag evidence. Older five-minute results largely measure
  futures leading a stale cash index of the same underlying; modern cross-futures opportunities last
  only hundreds of milliseconds, and naïve market-order capture loses the spread. Rejected an M1
  pair/lag/regime grid and increased the traceable source count to 13.
- Consolidated capability priorities without editing the shared contract: terminal lifecycle and
  canonical per-trial reviewability are P0; diagnostic envelopes and supported-data declarations are
  P1; validated cost/tick-activity semantics are P2. Macro-surprise data is evidence-gated, while
  cross-sectional and sub-second infrastructure is deferred or outside the M1 CFD mandate.
- Integrated exact-once frozen-backlog coverage into `validate_memory.py` and added a regression
  test, so the standard validator now fails if any imported I-01–I-62 idea is omitted or assigned to
  multiple overlap families.
- Added a durable 13-row source registry for fully catalogued R-2026-006. Access level, source type,
  evidentiary role, DOI/URL, and check time are now explicit. Memory validation reconciles exact
  counts only for records marked source-registry complete and validates source provenance fields.
- Prepared the planned-stop handoff after the execution environment resumed beyond the requested
  2026-10-29 stop window. No additional research was launched after detecting the clock discontinuity;
  the R-2026-006 source registry received only the verified Ederington-Lee DOI correction.
- During the final canonical audit, found the pilot lifecycle had completed after the last check:
  the user rejected v1.0.0, unchanged bytes moved to `queue/rejected/`, and no holdout ran. Canonical
  follow-up also maps the frozen primary to v0005 (net -2,754 R / 10,397 trades) and resolves the
  stale warning. Updated roadmap/registries and made contract tests queue-stage agnostic.
- Recorded V2's R-2026-004 preflight answer: local clocks, causal MAD history, signal-time costs,
  cell isolation, requested diagnostics, and separate raw response are supported/buildable. The
  mutable draft remained unqueued because “unexpected” missing M1 still needed a frozen definition.
- Replaced R-2026-004's circular “holiday visible in the data” proposal with a frozen causal
  expected-M1 predicate: an immutable, version-identified authoritative symbol-session calendar is
  resolved before OHLC is read; absence never defines a closure. A calendar-open minute without
  one fresh record fails the affected experiment, while unavailable calendar identity fails before
  metrics.
- Froze R-2026-004's compact canonical publication map under proposed `robustness.r004`: exactly 18
  cells, deterministic primary sign mapping, separate raw-q/executed-R outputs, all required splits
  and decision checks, and explicit skipped/failed statuses. Sent the validated non-executing
  canonical reply requesting V2 calendar and serialization confirmation; no run or holdout was
  authorized.
- Screened derivatives-expiration effects as R-2026-006's fifth distinct territory. S&P futures
  pinning is strike- and settlement-relative, requires unsupported option state, and is absent for
  quarterly futures; the broader recent witching-day short enters at the excluded open, exits at
  the close, and omits all costs; Swedish natural-experiment evidence is broadly null. Rejected any
  midday adaptation, strike proxy, or expiration-class grid and raised the complete R006 source
  registry to 17 rows.
- Screened the pre-FOMC equity drift as the sixth R-2026-006 territory. The original 49 bp estimate
  is a prior-day 14:00 to announcement-day 14:00 hold containing overnight and the excluded open.
  A matched S&P/E-mini extension finds only 4.7 bp in 2011–2019 versus 3.8 bp on ordinary days and
  disappearance after 2015. Rejected any same-day clock, meeting-type, press-conference, or VIX
  rescue grid and raised the complete R006 source registry to 19 rows.
- Screened the pre-holiday equity premium as the seventh R-2026-006 territory. Ariel's original
  market effect included a positive open and a last hour responsible for roughly one third of the
  return. The 1983–2019 replication finds the large-firm effect insignificant, especially after
  1990, with survival only among small firms. Rejected transfer to US500/NAS100 and any holiday,
  early-close, or interior-hour grid; the complete R006 source registry now has 21 rows.
- Screened turn-of-month equity returns as the eighth R-2026-006 territory. A 2025 U.S. study finds
  the classic four-day effect gone after 2001, while a 2026 international paper finds a broader
  eight-day and risk-conditioned effect. Neither identifies an allowed interior-session return.
  Rejected selection among windows, risk states, or clock buckets; the R006 registry now has 24
  traceable sources.
- Screened the London gold benchmark as the ninth R-2026-006 territory. The only source-matched
  economic advantage is a four-minute contemporaneous-trade leak under the pre-2015 private PM
  fixing; the electronic-auction reform changed the mechanism and later evidence supplies no modern
  fixed direction or net strategy. Rejected AM/PM, leak-proxy, breakout, and reversal grids; the
  complete R006 source registry now has 27 rows.
- Screened U.S. Treasury auction pressure as the tenth R-2026-006 territory. A 1991–2024 New York
  Fed study identifies a fixed three-hour pre-auction price decline and three-hour post-result
  recovery, excluding the result jump and retaining modern significance for selected maturities.
  V2 has no Treasury or bond-futures instrument, cost model, or contracted auction calendar, and no
  cited source supports substituting DXY or an equity index. Retained it as promising but
  capability-blocked with no proxy/maturity/window grid; the complete R006 registry now has 30 rows.
- Screened EIA petroleum-inventory releases as the eleventh R-2026-006 territory. Immediate and
  multi-hour WTI directions are conditioned on inventory surprises or API/Bloomberg inputs; the
  recent OHLC-only EIA half-hour signal predicts the explicitly excluded final half-hour. Rejected
  event-bar surprise proxies and continuation/reversal or exit-time scans, which would also overlap
  R004; the complete R006 source registry now has 35 rows.
- Screened the natural-gas storage announcement-day short as the twelfth R-2026-006 territory. The
  published fixed two-hour short earned 12% annualized and Sharpe 1.76 after costs, but the same
  study finds no effect in 2014–2018 and says efficiency returned; an independent 2008–2019 model
  also finds an insignificant announcement-day coefficient. Rejected historical-era, season,
  surprise, and window rescues; the complete R006 registry now has 37 rows.
- Completed an R006 saturation review after twelve territories. Only Treasury auction pressure
  clears the evidence, timing, and modern-stability gates, but it is outside V2's supported universe;
  all other screens have adverse evidence or unsupported estimands/inputs. Paused adjacent-anomaly
  search and refreshed capability priorities: terminal lifecycle is closed, while R004's versioned
  symbol-session calendar is now an explicit P1 blocker.
- Bound the exact current R004 JSON draft to SHA-256
  `FF8C351894E02DF22163C475470C399F96D3F075A8801CFF4BACC5B2A9E6EA73` and prepared a ten-check
  independent-review packet covering causality, gaps, grid/primary accounting, costs, result
  completeness, and holdout protection. This is reviewer preparation, not a review or handoff;
  V2 calendar/serialization confirmation and an independent verdict remain pending.
- Added machine-readable `knowledge_base/review_bindings.json` and memory-validator enforcement
  for review identity, research linkage, contained artifact/packet paths, UTC binding time, status,
  and exact SHA-256. Two tests prove matching bindings pass and artifact drift fails; the full
  Research Department suite now contains 44 passing tests.
- Audited the R005 diagnostic handoff blueprint and found it scientifically bounded but not
  implementation-ready. Frozen seven joint-review blockers: return/cost unit, pair-day aggregation
  order, uncertainty input, authoritative calendar, endpoint timestamp semantics, canonical table
  transport, and terminal statuses. No schema, queue payload, strategy semantics, or data run was
  created.
- Audited the real pilot envelope using canonical files only. Confirmed that 17 evaluations are
  counted but only nine grid IDs are named, the top-level cell is post-hoc `v0007`, primary `v0005`
  lacks a canonical metric row, eight sensitivities are collapsed to a count, and six decisions
  remain warning prose. Frozen ten future acceptance semantics and a 3×3/17-evaluation fixture;
  no shared schema or failed result was edited.
- Added backward-compatible semantic validation for future optional result-reviewability fields.
  Legacy 0.1.0 results remain valid, while any supplied manifest, selection, decision checks,
  feedback trace, or scientific disposition must be internally complete and consistent. Added
  three focused tests; the complete Research Department suite now has 47 passing tests.
- Added the complete research-owned 17-evaluation reviewability fixture: nine grid rows, eight
  parent-linked sensitivities, distinct primary/post-hoc reported cells, six structured checks,
  one explicit early-stop skip, answered feedback, and a separate scientific rejection. Its focused
  conformance test raises the full suite to 48 passing tests; this is not a shared-schema edit.
- Strengthened source-memory integrity after auditing all 37 registered R006 sources. The memory
  validator now rejects materially future `checked_utc` values and duplicate DOI or normalized
  primary URL identities within the same research record, preventing false inspection chronology
  or inflated evidence counts. Two regression tests raise the full suite to 50 passing tests.
- Made the user's continuous usage-limit instruction durable in the Research session protocol:
  persist the bounded unit, never escalate model/provider merely to bypass quota, wait through a
  known reset when the platform permits, continue safe local work where possible, and use a
  resumable `SESSION_LIMIT` checkpoint only when the host cannot keep the turn alive.
- Added a non-pausing `session_control.py refresh` operation so an active continuous session can
  persist its current summary, next action, and artifact set without checkpointing or changing
  session identity. Active `begin` calls now preserve a useful prior summary unless a new note is
  supplied. Three regression tests raise the complete suite to 53 passing tests.
- Sent canonical non-executing contract-review request
  `FB_CONTRACT_REVIEWABILITY_PROPOSAL_20261102T173559Z_RESEARCH`. It asks V2 to assess the tested
  per-evaluation result shape jointly with the diagnostic-study route and to return exact
  compatibility conflicts. It authorizes no schema edit, queue transition, pilot rerun, diagnostic
  handoff, or holdout access.
- Processed V2's adverse R004 capability answer
  `FB_INTRADAY_H1_SHOCK_RESPONSE_20261102T232536Z_ca99`. V2 has no authoritative versioned CFD
  holiday/early-close calendar, so the frozen expected-M1 predicate is unimplementable. Marked R004
  capability-blocked, changed its exact review binding to `BLOCKED_EXTERNAL`, suspended independent
  review, and canonically refused to queue an incompatible draft merely to trigger implementation.
- Audited V2's scattered symbol/data declarations against R005. All five frozen pairs appear in
  source and cost mappings, but mutable caches, code constants, and dated prose do not prove one
  common immutable study snapshot. Added a research-only synthetic all-five capability fixture,
  validator, and six tests covering partial/missing pairs, interval gaps, unknown-spread semantics,
  and post-resolution identity drift. No V2 data values were read and no capability was claimed.
- Audited V2.6l's new `robustness.cell_manifest` and `trial_accounting` implementation. It closes
  future declared-grid opacity and separates sensitivities from selectable counts, but does not
  address sensitivity identities/metrics, primary/reported selection, decision checks, feedback
  trace, scientific disposition, or fail-closed cost provenance. Sent the exact partial-
  compatibility findings in canonical reply
  `FB_CONTRACT_REVIEWABILITY_REPLY_20261103T103951Z_RESEARCH`.
- Extended the research contract validator to enforce V2.6l semantics when those optional nested
  fields appear: unique/resolved cells, complete metrics and stresses, consistent trial accounting,
  no default-cost substitution, and one addressable row per counted sensitivity. Three focused
  tests preserve legacy-envelope compatibility while preventing partial future output from looking
  complete.
- Resolved four research-owned R005 semantic blockers before data access. Frozen exact scheduled
  M1 endpoints, direct/inverse quote math, adverse effective-fill and doubled-cost formulas,
  sum-then-equal-weight complete-case daily aggregation, and a synchronized five-day moving-block
  bootstrap with Holm control across the two co-primary sessions. Calendar/capability, canonical
  transport, terminal statuses, and future adapter conformance remain blocking.
- Added the price-free R005 accounting reference and six tests. Direct/inverse orientation,
  effective-fill doubled costs, split-block summation, exact all-five composition, the 100-date
  inference floor, and seeded moving-block resampling now have executable expected behavior. A
  future adapter must reproduce it; no market data or outcome was computed.
- Traced V2's I-44 activity field without reading market values. MT5 `tick_volume` is broker update
  count, duplicated into bid/ask cache columns; generic resampling converts all-unknown histdata
  `NaN` activity to zero and drops source identity. Froze the missingness/source declaration needed
  before any coverage or proxy-validation study. I-44 remains blocked and no A/B was authorized.
- Added an executable I-44 missingness reference and five tests: known same-source counts sum,
  observed zero remains distinct from unknown, partial unknown remains unknown, mixed feeds fail,
  and same-clock ratios require complete positive history. This is not a data-capability claim.
- Added an outcome-free R005 diagnostic-result envelope, validator, and six negative/positive
  tests. The fixture requires the exact ten cells and five-pair universe, both co-primary rows,
  frozen semantic identities, explicit exclusions and cost provenance, all decision checks,
  non-primary sensitivity labeling, separate run/scientific states, and no holdout. It makes the
  proposed acceptance shape reviewable without creating a shared schema, queue payload, run, or
  capability claim.
- Audited V2 cost provenance read-only. The engine has strong mechanics and serializes resolved
  numeric settings, but nearest-year spread substitution (including later years), silent fixed
  fallback, mixed measurement windows, rough slippage, and current schedules do not establish a
  complete historical signal-time series. Froze separate `HISTORICAL_RECONSTRUCTION` and
  `CONSERVATIVE_STRESS` meanings so later estimates cannot silently acquire causal status.
- Added an outcome-free cost-declaration fixture, validator, and six tests. Historical mode now
  requires immutable sources, exact component/symbol/interval coverage, no fallback, fail-closed
  missingness, mode-consistent evidence labels, and stable post-resolution identity. This is not a
  V2 capability claim and no backtester file or market result was changed.
- Made the authoritative symbol-session calendar gate executable without OHLC or market values.
  The synthetic declaration, validator, and six tests require exact symbol/interval coverage,
  recurring schedules, complete holiday/early-close exceptions, timezone/source hashes,
  OHLC-independent pre-resolution, fail-before-metrics behavior, and stable identity. This
  sharpens R004's unblock condition but does not satisfy it; R004 remains capability-blocked and
  unqueued.
- Added a synthetic broker-tick-activity declaration, validator, and six tests for I-44. The gate
  requires immutable MT5 feed/snapshot identity, complete single-source coverage, preservation of
  unknown versus observed zero, same-clock normalization, clock/calendar identity, break
  diagnostics, and stable resolution. It expressly forbids interpreting update counts as executed
  volume, VWAP, order flow, absorption, or trade direction. No real capability or A/B was claimed.
- Consolidated eight price-free conformance controls into
  `fixtures/research_control_manifest.json` and one safe runner. Four manifest tests reject
  duplicate IDs, path escape, and missing validator functions. The standing department/session
  instructions now require the consolidated command whenever a synthetic control changes; it does
  not replace memory, contract, feedback, or external capability validation.
- Closed the control-inventory omission gap: every JSON fixture other than the manifest must now
  be declared exactly once. Two additional tests reject unmanifested and duplicate fixtures, so a
  future synthetic gate cannot silently fall outside the one-command validation surface.
- Audited V2's news/event capability read-only. The hashed schedule is suitable for blackout and
  descriptive splits, but it is retrospective: forecast/previous values are unavailable,
  known-at and point-in-time flags are discarded from runtime objects, and the unwired actual
  accessor uses scheduled time plus a caller delay without consensus or revision history. Kept
  directional macro research P3/deferred until independent post-M1-latency evidence exists; no
  event-data fixture, implementation request, or strategy was created.
- Reconciled proposal sequencing with the terminal first pilot. Removed the stale instruction to
  wait for a still-open pilot while preserving the actual state: the sequencing prerequisite is
  met, but the joint diagnostic-route/result-manifest review is only scheduled and has no
  acceptance verdict. R005 therefore remains research-local and unqueued.
- Audited deferred platform data read-only. V2 has no Treasury instrument, futures roll/duration,
  Treasury cost/calendar/auction contract, or point-in-time equity security master, membership,
  corporate actions, adjusted returns, borrow and synchronized portfolio accounting. Kept R006
  and cross-sectional research deferred; current CFDs and present-day constituent lists are not
  faithful proxies and no expansion request is justified.
- Corrected the department README's obsolete blanket statement that the shared interface was only
  proposed and unintegrated. It now distinguishes the operational retained strategy-intake/pilot
  lifecycle from still-incomplete diagnostic routing, result reviewability, and broader scaffold
  work, and points future sessions to the consolidated synthetic-control command.
- Bound every consolidated control to its non-empty research report as well as its fixture and
  validator. The runner now enforces report containment under Research Department ownership, so a
  passing implementation remains traceable to the human semantic authority it is meant to encode.
- Closed the remaining semantic-authority binding gap in the consolidated control runner. A
  contained non-empty but unrelated report could previously satisfy the manifest; every authority
  report must now explicitly name its bound fixture and validator. Added a regression test,
  repaired the missing result-reviewability fixture reference, and required every consolidated
  fixture to carry the machine-readable `fixture_only: true` marker. Fixture inventory is now
  recursive, excludes only the exact manifest path, and binds reports to full relative artifact
  paths rather than ambiguous basenames. Unknown or misspelled manifest/control fields now fail
  closed. The full gate passes all eight controls and 107 department tests. This strengthens
  internal traceability and synthetic provenance only and makes no external capability,
  profitability, run, or holdout claim.
- Ran one bounded post-saturation R006 update and opened Aleti, Bollerslev, and Siggaard (2025) in
  full. Its reported cost-adjusted 15-minute SPY predictability is genuine adjacent evidence, but
  the signal requires 272 synchronized factor/industry/characteristic portfolios, ETF execution,
  ML and jump decomposition, initializes the opening weight from an overnight long, and ends in
  2020. Registered it as source 38 and a thirteenth screened territory, parked it for unsupported
  inputs and non-transferable day-flat semantics, and created no proxy, grid, draft, run, or
  holdout request.
- Corrected the research roadmap's stale R006 rollup from 12 territories/37 sources to the
  registered 13/38. Found a separate jointly owned contract-status drift: its final compatibility
  paragraph still described the now-terminal first pilot's result publication and traceability as
  under observation. Sent schema-valid non-executing feedback
  `FB_CONTRACT_PILOT_STATUS_DRIFT_20261103T214654Z_RESEARCH` requesting joint wording review; did
  not edit the shared contract, rerun the pilot, move queue state, or access holdout data.
- Applied the previously reviewed queue-README correction: research had identified the stale
  non-operational warning, and V2 accepted it with exact live-queue wording in canonical feedback.
  Updated the research proposal to record that resolution and clarified the R006 saturation
  report's initial-versus-current scope. The newer contract pilot-status wording remains only a
  proposal pending joint review.
- Propagated the new factor-zoo source through the deferred-capability decision. The platform audit,
  priority matrix, and roadmap now state the actual 272-portfolio synchronization, immutable
  portfolio-definition, jump/ML transform, SPY cost, and overnight-initialized opening-position
  dependencies. This prevents the positive net paper result from being misread as support for a
  single-index OHLC proxy; cross-sectional expansion remains deferred and no implementation or
  data request was created.
- Reconciled R004's strategy-registry status with its canonical feedback chain. The registry had
  still said capability confirmation was pending even though V2 had confirmed the authoritative
  CFD calendar unavailable and research had acknowledged `BLOCKED_EXTERNAL`. Updated only the
  registry note; preserved the v0.1.0 draft byte-for-byte at its recorded SHA-256 because its
  review packet deliberately binds that artifact. R004 remains unqueued, review-suspended, and
  unauthorized for any run or holdout.
- Audited R005's pre-data five-pair/ten-cell correction across active records and found no surviving
  operational six-pair/twelve-cell instruction. The deeper cross-control check found that the
  independently valid capability and result fixtures used different synthetic calendar identity
  strings. Aligned the result fixture to `SYNTHETIC_FX_CALENDAR` and made the consolidated runner
  join declaration ID/version, snapshot hash, ordered universe, calendar, and cost identities.
  Added a regression test; all eight controls and 108 department tests pass. This is synthetic
  coherence only, with no real capability, result, run, or holdout claim.
- Completed the companion R005 accounting/uncertainty identity audit. The result fixture named
  frozen semantics, but the accounting fixture and reference code did not machine-bind those names
  or their bootstrap defaults. Added exact accounting/uncertainty identities and the 10,000
  circular-resample, five-day-block, seed-2026005 parameter declaration; the reference validator
  enforces it and the consolidated runner joins both identities to the result fixture. This closes
  silent default/label drift without asserting any external capability or result.
- Audited I44's two price-free controls and found that they passed independently despite different
  feed labels: the missingness examples named an FTMO demo source while the broker declaration
  named a synthetic MT5 feed. Added one explicit measurement block to the missingness fixture,
  bound its cases to that source, and made the consolidated runner join semantic/raw-field, source,
  aggregation, normalization, clock/calendar, and proxy-claim identities across both fixtures.
  Replaced the real-broker-like example label with the existing synthetic identity. Focused drift
  tests pass; this establishes synthetic coherence only and does not repair V2, prove historical
  availability, authorize I44 testing, or make an external broker/data claim.
- Reconciled the result-reviewability proposal with its executable acceptance validator. The
  proposal required every tried evaluation to publish gross/net outcome, drawdown, trades, and
  state frequency or structured absence, but the validator accepted `net_r` alone and allowed
  skipped manifest rows without reasons. The research-owned extension now enforces exact completed-
  row fields and types/ranges, field-specific reasons for nulls, row-level reasons for every non-
  completed evaluation, and equality between selected primary IDs and manifest primary-role rows.
  Updated all 17 synthetic evaluation rows and added regression tests. This changes no canonical
  schema, V2 implementation, real result, lifecycle state, or holdout disclosure.
- Audited the synthetic signal-time-cost and authoritative-calendar controls as an integration
  pair. Their separate validators allowed incompatible stage, required interval, or symbol order
  to pass independently. Added a consolidated join for the shared experiment context: development
  stage, resolution before OHLC, exact interval, and ordered universe. Explicitly kept broker/feed
  cost sources independent from venue/product calendar sources and added a regression test proving
  that distinct provenance remains valid. This is synthetic acceptance coherence only; it does
  not assert either real capability or authorize a study.
- Closed a common chronology gap in the cost, authoritative-calendar, and tick-activity
  declarations. Each validator parsed `generated_at` and `resolved_at` but allowed a declaration
  to resolve before it was generated. All three now require `resolved_at >= generated_at`, with
  focused regressions and explicit documentation that valid metadata order does not prove causal
  pre-data resolution. The existing pre-OHLC/pre-activity assertions remain independently
  mandatory.
- Audited the repeated claim that declaration identities cannot drift after resolution. The four
  gate functions supported an optional anchor, but the consolidated manifest never supplied one,
  so the common entry point did not enforce that claim. Added one fail-closed manifest
  `resolved_identity` object and wired it through R005 capability, signal-time cost, calendar, and
  I44 activity gates. Mutation tests now reject drift for all four and malformed anchor fields.
  The anchors pin declared tuples only: their all-zero synthetic hashes remain placeholders and do
  not prove content immutability, external data identity, or capability.
- Separated local fixture-byte integrity from declared semantic identities. Added mandatory exact-
  byte `fixture_sha256` values for all eight consolidated controls and verify each digest before
  JSON parsing or validator loading. A digest mutation now fails the common runner, and omission
  fails the manifest schema. Documented that whitespace/newline changes also require an explicit
  update and that these hashes prove only agreement with the local manifest—not authorship,
  external provenance, market-data identity, or scientific validity.
- Audited non-finite result handling. Python numeric checks and its permissive JSON parser allowed
  `NaN`/infinity to enter reviewability, V2.6l compatibility, and R005 diagnostic paths; range
  comparisons could then behave inconsistently. Added one finite-number rule to payload checks,
  strict rejection of non-standard JSON constants in result file loaders, and regressions for
  variant metrics, cell metrics, cost stresses, confidence intervals, and probabilities. No
  fixture bytes changed, so the eight manifest content hashes remain valid.
- Extended finite-number enforcement to the price-free computational references. R005 now rejects
  non-finite prices, costs, multipliers, block summaries, complete-five inputs, bootstrap series,
  and percentile inputs before arithmetic. I44 now reserves unknown strictly for explicit
  `None`; `NaN`, infinity, negative counts, booleans, and other invalid known values fail rather
  than becoming missing or propagating through a ratio. Added focused regressions. Fixture bytes
  did not change, so manifest content hashes remain valid.
- Added finite-output postconditions after finding that extreme but finite inputs could still
  overflow cost multiplication, sums, means, or activity ratios. R005 now checks computed costs,
  effective fills, returns, pair-day totals, complete-five and bootstrap means, and percentile
  interpolation; log returns use log differences to avoid needless ratio overflow. I44 checks
  aggregate, same-clock mean, and ratio outputs. Extreme-value regressions fail closed without
  changing fixture bytes or claiming realistic market magnitudes.
- Made conformance-case coverage fail closed. The R005 accounting fixture now requires exactly the
  four structurally derived direct/inverse × LOCAL/US orientation IDs; I44 requires exactly the
  known-sum, known-zero, all-unknown, partial-unknown, and mixed-source-error IDs. Both validators
  reject missing, duplicate, extra, or mislabeled cases rather than validating whatever subset is
  present. Added mutation regressions and refreshed only the two changed fixture byte hashes in
  the consolidated manifest.
- 2026-11-05T14:21:19Z — R015 independently approved and bound to SHA-256
  `12e34e1cc90eb1658bd346ebaa3a33651eb8bebc038ccf8ac6a8e38ff6c1f5b8`.
  Sent canonical exact-decimal-grid, fill/state, and 320-cell result-ledger compatibility preflight.
  Throughput is now nine distinct families, nine reviewed specifications, 320 selectable cells,
  zero development results, and zero queued submissions. No experiment or holdout was accessed.
- 2026-11-05T14:27:58Z — R016 required and received an independent clock correction before approval:
  signals now start 09:30 so both adjacent event bars lie inside the current session, and crosses
  outside 09:30–13:45 do not consume the day. Bound corrected SHA-256
  `f1b5db35c43da8687123deba70c5a02cf034872034791ec0fed2b7e2d8c86b86` and sent canonical
  prior-weekday range, first-cross state, and 324-cell ledger preflight. Throughput is ten distinct
  families, ten reviewed specifications, 324 selectable cells, zero results, and zero queued.
- 2026-11-05T14:31:47Z — R017 independently approved and bound to SHA-256
  `6b910a470d2871da232bef4d70c61fd6b000e63c282f4b868c8670ab8fe83d11`.
  The review confirmed the shifted eight-change ER windows and rising-edge semantics. Sent canonical
  ER transition, fill/state, and 328-cell result-ledger compatibility preflight. Throughput is now
  eleven distinct families, eleven reviewed specifications, 328 selectable cells, zero results,
  and zero queued submissions.
- 2026-11-05T14:36:48Z — R018 required a persistence clarification before independent approval:
  same-side RSI persistence cannot retrigger, while a direct opposite-extreme transition qualifies
  under the other threshold Boolean. Bound corrected SHA-256
  `bcb8b865c65594bd443d6455d9eb2e95118af17e2d94007c01b41f5fbf76401a` and sent canonical
  Wilder-RSI, persistence/fill, and 332-cell result-ledger preflight. Throughput is twelve distinct
  families, twelve reviewed specifications, 332 selectable cells, zero results, and zero queued.
- 2026-11-05T14:43:11Z — Rejected CUSUM as a separate R019 because the durable overlap map places it
  inside the shock-response event-definition family. Instead completed the first synchronized
  multi-symbol family: R019 USD breadth basket, independently approved and bound to SHA-256
  `0c41d96343f55aca7eb918a46eef1734d090ded4560c9cd4ff3603a87dee95f0`. Opened Menkhoff et al.
  (2012) in full and retained it only as a monthly cross-currency boundary. Sent canonical
  synchronization, atomic-basket, and 336-cell result-ledger preflight. Throughput is thirteen
  families/specifications, 336 cells, zero results, and zero queued.
- 2026-11-05T14:48:08Z — R020 independently approved and bound to SHA-256
  `b8a170b99f4cd39eb4d0bbd2c68aa272537d2133e8e83905782754ac3ea4855d`.
  It adds a relative winner-minus-loser FX rank basket, distinct from R019 common USD breadth.
  Sent canonical rank, atomic-basket, and 340-cell result-ledger compatibility preflight. Throughput
  is fourteen families/specifications, 340 cells, zero results, and zero queued submissions.
- 2026-11-05T14:53:39Z — R021 independently approved and bound to SHA-256
  `dcc0dd7b0850de4f03fb10100cb2481595c4e1c59a1ac6e15a0028f2d99e5fa9`.
  It adds a fixed EURUSD-GBPUSD robust-standardized relative-dislocation pair, distinct from R020's
  six-currency cross-sectional rank basket. Gatev et al. remains only a daily selected-equity-pair
  boundary. Sent canonical synchronization/MAD, atomic-pair, and 344-cell result-ledger compatibility
  preflight. Throughput is fifteen families/specifications, 344 cells, zero results, and zero queued.
- 2026-11-05T15:01:15Z — R022 independently approved and bound to SHA-256
  `a1f1c26471b8be419e760a88ab4cb8bb75df616fd0097b21ba42de372f2b9085`.
  The initial EMA-cross candidate was rejected because it reopens the failed Kaufman trend family.
  R022 instead adds an intrahour positive/negative realized-semivariance imbalance transition with
  explicit one-jump diagnostics. Liu et al. remains only a daily Chinese-commodity boundary. Sent
  canonical 76-close window, fill/state, and 348-cell result-ledger preflight. Throughput is sixteen
  families/specifications, 348 cells, zero results, and zero queued submissions.
- 2026-11-05T15:03:56Z — Consolidated R007–R022 implementation readiness instead of manufacturing
  an overlapping R023. The 16 drafts share one causal M15 fill/state/accounting/result harness;
  feature work is grouped into five incremental tiers. R014 is the suggested four-cell plumbing
  proof after the existing V2.6i synthetic end-to-end gate passes. Sent one canonical bulk review
  request covering common semantics, tier order and complete 348-cell result capacity. This is not
  a queue, run, schema-change or holdout request.
- Added `reports/FAST_LANE_SPEC_MANIFEST.json`, a non-authorizing machine-readable index of the 16
  exact review-bound paths and hashes, priorities, compatibility tiers, preflight IDs and 348-cell
  total. An integrity audit confirmed all hashes/bindings/preflights and recomputed every tunable
  Cartesian product: all 16 declared sizes match and sum to 348. The manifest references canonical
  specifications and does not copy their rules or create queue state.
- Corrected the initial Tier-0 interpretation after reading V2's authoritative intake documents:
  V2.6i i1–i7 and the synthetic end-to-end test are built/accepted and a real pilot completed. Sent
  a canonical correction to the bulk preflight. Selected R014 as the smallest first queue candidate;
  its v0.2.0 revision updates only lifecycle metadata and the contemporaneous ledger from 316 to 348
  cells before a fresh exact-artifact review and atomic publication.
- 2026-11-05T15:11:35Z — R014 v0.2.0 passed exact-artifact re-review with no trading-rule drift and
  was atomically published to the canonical pending queue. Research archive and queue bytes match at
  SHA-256 `d09d44b96cde33f45b718803eb385cc9a9fd908641d06148ea47de61acff31c5`.
  The first publish attempt safely failed before any queue write because `submit_strategy.py`
  imported a removed validator constant; fixed the research-owned publisher and added a regression,
  bringing the suite to 134 tests. The submission authorizes intake/implementation mapping only;
  zero development results exist and no run or holdout is authorized.
- 2026-11-05T20:36:53Z — Began R023 as an explicitly unreviewed four-cell serial-dependence
  transition falsification while R014 remained the sole pending submission. Opened Bianco and Renò
  (2006) at the publisher and Li, Giraitis and Sucarrat (2025) in full. The latter's robust tests find
  15-minute FX autocorrelation generally absent and unstable, so the expected result is null. Froze
  a 12-pair lag-one Pearson transition, consistent/inverted response mappings and 30/60-minute holds
  in draft SHA-256 `52319035d6d9e3116a69e74fb15ab39d6a77a816e36730257dc4bbaa6412b9aa`.
  Work stopped on user `End.` before independent review, registry entry, breadth-ledger update,
  compatibility preflight or queue action; none of those stages should be inferred.
- 2026-11-05T21:46:00Z — Completed independent challenge and re-review of R023. The revised exact
  artifact SHA-256 `7ece150e58f6be9a6d570cacb62de772804f0693e6a85f7506ee6853357dd558`
  was approved, registered and ledgered as the seventeenth family/four cells. Sent a canonical
  non-executing compatibility preflight; no queue, run or holdout was authorized.
- 2026-11-06T07:10:00Z — Recorded R014 v0.2.0 as a terminal development failure after all four
  cells were net-negative after costs. The immutable submission remains in canonical `rejected/`;
  no rerun, same-data redesign, resubmission or holdout is authorized.
- 2026-11-06T11:06:12Z — Completed R024 after iterative independent quantitative review. The
  exact SMA4/SMA16 four-cell artifact SHA-256
  `5bb493702405265032f450357da454301976bb1c78ea8cf5b48adba1627594d3` was certified,
  registered and ledgered as the eighteenth family, bringing the breadth inventory to 356 cells.
  Sent a canonical non-executing compatibility preflight; no queue, run or holdout was authorized.
- 2026-11-06T11:10:10Z — Ran one bounded family-19 admission screen. Neely and Weller's full
  intraday FX paper and publisher previews for modern intraday gold technical trading and
  directional-duration evidence produced only adverse cost/out-of-sample evidence or mechanisms
  already represented by existing families. Recorded the exact access limits and overlap decision
  in `reports/FAST_LANE_FAMILY_19_ADMISSION_SCREEN_2026-11-06.md`; no R025, grid, queue, run or
  holdout was created.
- 2026-11-06T11:10:57Z — Rechecked V2 result-reviewability read-only. No capability later than
  V2.6l is present; the documented and implemented gaps in sensitivity identity, resolved
  parameters, fail-closed cost provenance, selection, decision checks, feedback trace and
  scientific disposition remain. Appended the exact status to
  `reports/V26L_RESULT_MANIFEST_COMPATIBILITY_AUDIT.md`; sent no duplicate feedback and made no V2
  or shared-schema change because V2 records the joint review as user-directed after V2.8.
- 2026-11-06T11:12:16Z — Tightened the family-19 evidence screen to high/low-range and intrabar
  predictors. A full 2026 MNQ OHLCV falsification preprint found no common family passing its joint
  cost/OOS/stability gates, while a 2026 FX tick abstract predicted move occurrence rather than a
  supported directional edge. Added both with peer-review, data, calendar and access caveats. The
  admission verdict remains negative; no candidate or trial count was added.
- 2026-11-06T11:44:35Z — Audited the first real post-V2.6l result using only the canonical R014
  development envelope. All four declared cells have complete parameter/metric/stress rows and no
  default-cost warning, so the all-negative terminal rejection is independently reviewable. The
  top-level result matches `v0003` (`FADE_LAST/60`) rather than the preregistered `v0001`
  (`FOLLOW_LAST/60`) baseline, but no reported-cell ID, selection rule, roles, decision checks,
  feedback trace or scientific disposition is serialized. Added the canonical-only evidence to
  `reports/V26L_RESULT_MANIFEST_COMPATIBILITY_AUDIT.md`; no result, V2 or schema file was changed.
- 2026-11-06T12:13:41Z — Audited current-facing research memory for stale R014 pending/zero-result,
  pre-R023/R024 family-count and unreviewed-status claims. None remain outside explicitly dated
  historical packets and the superseded prior-session handoff. The complete research-owned
  regression suite passes: 134 tests in 1.062 seconds.
- 2026-11-06T12:43:27Z — Reconciled the high-throughput roadmap with the negative family-19
  admission screen. The 20-family objective is now explicitly quality-gated rather than a quota;
  R025 requires new evidence or a genuinely independent measurement/prediction pair. No candidate,
  specification, parameter cell, queue action, run or holdout was added.
