# Multi-symbol strategy support

Design proposal, 2026-11-10. Documentation only; no strategy rules, defaults, test-period
access or implementation are authorized by this document. Existing strategies must keep
bit-identical results. All interface and new-file names below are proposed.

## Scope and current constraints

Support three distinct capabilities in order: (A) observe B while trading A; (B) manage
a linked two-leg position; (C) rank a universe and execute a basket. Observing several
inputs does not necessarily require several traded legs: USD breadth and FX strength can
use A when the output is one instrument. Conversely, independent symbol runs merged into
a portfolio do not implement a coordinated spread or basket.

Grounding in the current repository:

- `strategy/base.py`: `Strategy.on_candle(now, views)` receives one symbol's timeframe
  dictionary; `Order` has no symbol because the engine already owns its execution symbol.
- `engine/backtest.py`: `Backtest` indexes input series by timeframe, creates one `Replay`,
  manages existing trades before calling the strategy, then processes signal exits and
  new fills. Close entries are managed from the next candle, with separate pending-limit rules.
- `engine/replay.py` rejects another symbol's series. `core/mtf.py` already selects the
  latest close at or before `now`; returned `SeriesView` snapshots never advance in place.
- `runner.py`: `_load`/`_run_job` create independent symbol jobs; `merge_trades` sorts their
  results. `SeriesCache` retains one symbol/range scope. `_load_timeframe` explicitly uses
  UTC daily boundaries, despite the adapter's New York chart default.
- `tools/research.py` segments and schedules each symbol separately; grids' `symbols`
  currently mean independent traded instruments. `tools/golden.py` compares exact trade
  fields/floats for the existing strategies. `analytics/portfolio.py` combines weighted
  independent results; it supplies neither joint execution nor cross-symbol observations.
- `risk/account_sim.py` is a documented stub. Group account protection cannot be claimed
  complete merely by passing grouped results into today's risk tools.

Relevant requirements: `AGENTS.md` (closed-only views, incremental detectors, R results,
layers), `docs/ARCHITECTURE.md`, `docs/research-runner.md`, `docs/risk-management.md`.
Motivation: `research/candidates/README.md` multi-symbol rows and
`knowledge/research/reports/2026-11-10_idea_harvest_practitioner.md`, ideas 1–5 and 12.
The candidate and harvest documents are research inputs, not executable trading specs;
this design does not revive the rejected M15 candidates or verify the harvest's sources.

## Data contract and shared time

### Declared dependencies

Add a frozen input specification for new strategies, resolved before loading. Each
dependency names its symbol/role, required timeframes, daily boundary, H4 alignment,
warm-up/full-history requirements, calendar identifier and required freshness/coverage
policy. Record the resolved specification in new-mode run manifests. Reject duplicate
or conflicting declarations. Tunable policies have frozen config fields; no hidden age
limit, minimum universe size or implicit calendar conversion.

The runner resolves every dependency through `SymbolSources` and `DataAdapter`; replay
knows no cache paths or provider APIs. Load each distinct input once per job. Private
storage keys include symbol, timeframe, boundary/alignment, range and source identity,
so UTC and New York daily candles cannot overwrite each other. Use a separate bounded
bundle cache rather than changing the legacy one-symbol cache's eviction semantics.
Do not pass a full series, DataFrame or raw history index to a strategy or detector.

### One logical clock, separate cursors

For the new replay path, merge actual M1 **close times** from all declared inputs into a
strictly increasing UTC event stream. A candle is eligible only if
`candle.ts + timeframe.duration <= now`. At each timestamp:

1. Advance every symbol's eligible M1 cursor as one batch. Equal-time closes become
   visible together, independently of symbol iteration order.
2. Manage pre-existing execution positions with each symbol's newly closed candle,
   once only; never reuse a stale candle's range for stops, fills or excursions.
3. Construct an immutable market snapshot of closed views and availability metadata.
   Higher timeframes come exclusively through `HigherTimeframeClock.view_at(now)`.
4. Notify new-mode strategies only on their declared decision events; fills and callbacks
   have deterministic phases. New decisions cannot use earlier intraminute prices.

For A, the only decision events are A's existing base-candle closes. Reference-only events
advance causal observations but cannot trigger an A order or change A's trade lifecycle.
An optimized implementation may batch reference events between A callbacks, provided it
produces the same snapshots and feeds every intervening closed candle to incremental
detectors. This is one simulated time domain, never one independently advancing clock
per symbol. B/C also manage each tradable symbol at its actual M1 closes.

Expose a proposed `MarketView` containing `now` and read-only nested mappings
`symbol -> timeframe -> SeriesView | None`, plus `last_close_time`, cursors, newly closed
ranges and availability status. Mapping immutability complements existing snapshot
semantics; retained views remain fixed. No public future-time lookup is exposed. Symbols'
cursor integers are unrelated: comparisons and joins use close timestamps. A strategy
can process missed intermediate candles using successively bounded `view.at(i)` views,
once per new cursor; repeated snapshots do not trigger duplicate detector updates.

### Missing candles, sessions and freshness

Use a union event stream, not an intersection that discards valid candles. Never
backfill or fabricate OHLC. Before the first close a view is `None`. Thereafter a view
may remain at its last close, accompanied by its actual age and status; retaining that
observation is not permission to execute at its price. Separate:

- scheduled closure/holiday: no fresh candle expected; retain the last observation;
- missing required data: mark unavailable and record a reason;
- insufficient warm-up or an incomplete signal window: mark not ready.

New strategy specs must state which statuses and ages permit a signal. Strict synchronous
signals require matching completed window endpoints; asynchronous ideas (BTC weekend
information used when gold reopens) require an explicit event/window rule. No universal
forward-fill, freshness threshold or intersection-of-trading-days rule can serve both.
If required inputs are unavailable, block new decisions for that setup and log the reason;
continue managing existing A positions. Missing execution data is not a zero-return
minute: record unresolved exposure and invalidate affected risk conclusions if it cannot
be resolved by the specified missing-data policy. Never suppress protective management
because a reference input is stale.

Preserve `SymbolSources.covered_days` and the weekly crypto closure rules in
`docs/research-runner.md`. Their inventory-derived coverage classification is data-quality
metadata, never a price signal. A genuine missing trading-day block in any required
dependency splits new-mode research segments and restarts affected state. Regular
non-overlapping sessions do not split segments just because one market is closed.
Intraday holes additionally require coverage diagnostics; a present day file alone does
not certify complete signal windows. Do not silently drop an unavailable basket member.

Store and compare UTC timestamps. Resolve each session/calendar boundary with its IANA
zone, including US/European DST mismatch weeks and local holidays. Use the resampler's
existing `ts + duration` close convention even for DST-sensitive D1/W1 bars. Let new
strategies explicitly request New York 17:00 daily bars; preserve UTC daily loading for
all legacy strategies. Cross-market returns must declare common endpoints or their
intentional asynchronous windows; equal row numbers do not imply comparable dates.

### No-lookahead argument

At event time t, every supplied view ends at a close <= t, and every higher-timeframe
view is bounded by the same t. Prefix reads and old snapshots cannot advance. All
equal-time inputs are published before any new decision. Incremental events carry their
confirming symbol/index/close time, and actions cannot precede that time. Execution uses
only candles already closed at the execution phase; `LookaheadError` propagates as a bug.

The harvest proposes first-M1-open-after-signal execution, whereas existing strategies
use close fills. This requires an explicit new execution mode, not changing legacy fills.
Queue the intent after the signal; after the candidate execution M1 candle closes, the
engine may use that candle's open for an order fixed before it opened. Record both
decision and execution times. Do not expose that minute's OHLC to the deciding strategy,
or let a decision based on its close fill at its earlier open. A next-open execution mode
needs its own gap, stop activation and callback tests before those ideas are implemented.

## A — read other symbols, trade one symbol

Highest value per effort. Unlocks oil/gold -> US500 (harvest #4), BTC -> gold and
USD-breadth -> one pair, without group trade or risk changes.

Add an opt-in strategy capability with a distinct market-aware callback, for example
`on_market_candle(now, primary_views, market) -> list[Order]`. Keep the existing abstract
`on_candle` signature and legacy call branch intact; a new strategy implements the new
capability explicitly. Do not infer the mode from a nonempty symbols list. The engine
receives a bounded snapshot provider for reference inputs, not source adapters. That
provider cannot be queried later than the current engine time.

A still owns one execution symbol. Orders, `OpenTrade`, `TradeResult`, costs, swap,
pending limits, callbacks and R normalization remain per A exactly as today. Extra
symbols cannot receive orders; their data is absent from trade counts and exposure.
No dependency means no new callback, extra data load, clock event or serialized field.
Existing `Replay` continues rejecting foreign-symbol series; the new observation service
lives alongside it. Strategy-specific cross-market calculations stay in the new strategy's
folder, with one detector state per input/timeframe.

Schedule one job per primary plus its full dependency bundle, never one independent job
per reference. Several primaries may run independently only if their strategies have no
shared position/allocation state. The public CLI can initially offer an explicit input
table/config and keep the existing positional symbols meaning unchanged.

## B — linked two-leg execution and R

Second priority: unlock WTI–Brent and gold–silver (harvest #1/#12). Requires a new
`GroupOrder`/`GroupResult` model and M1 group execution coordinator; two ordinary orders
from separate jobs cannot implement it. Retain legacy trade types unchanged.

A group has a stable ID, ordered leg IDs/symbols/directions, relative exposure ratios,
entry intent time, individual stop distances, declared entry/exit synchronization policy,
and a single initial risk budget. Relative exposures/hedge ratios are fixed from closed
entry-time information, never estimated from the full sample. Equal dollar notionals
do not mean equal contracts or equal stop-risk shares.

Proposed normalization (a design convention to ratify in each new strategy spec): choose
an arbitrary common valuation unit and relative quantities q_i, causal unit price-value
conversion v_i(0), initial price stops d_i > 0, and define

    D = sum_i abs(q_i) * v_i(0) * d_i
    w_i = abs(q_i) * v_i(0) * d_i / D
    R_group_gross = sum_i gross_normalized_leg_PnL_i / D
    R_group_net   = sum_i net_normalized_leg_PnL_i / D

Here q_i are scale-free weights, not account lots, and D is a normalization basis, not
account money. When valuation is constant, this equals sum_i w_i * R_leg_i; for changing
FX conversion, normalize each cashflow with the causally available conversion at its
timestamp before dividing by the fixed D. All required FX conversion symbols are declared
dependencies. Reject nonfinite quantities, zero/nonpositive risk and unavailable conversion.
Do not add unweighted leg Rs or divide by the net notional of offsetting legs. For example,
leg stop budgets 2 and 1 give weights 2/3 and 1/3; leg net returns +1R and -1R yield
+1/3 group R. Two simultaneous initial stops give -1 gross group R before gaps/costs.
An exit on the first leg stop need not lose exactly 1 group R. Costs and gaps may exceed it.

Run the existing per-symbol cost machinery for each leg: bid/ask, tick rounding, spread,
commission, slippage, conversion, rollover swap/triple-day charges and funding when
applicable. Normalize all charges to D; do not charge spread twice through both fills
and diagnostic cost fields. Financing accrues over each leg's actual holding interval,
including an unmatched exit delay. Freeze initial D and weights; trailing stops do not
renormalize historical R. Persist normalized leg attribution and grouped totals.

Entry/exit mechanics are strategy-spec prerequisites. The coordinator must support
predeclared synchronized entry intents, validate all required legs/costs/news constraints
before accepting a simulated atomic group, and reject the whole group if one leg fails.
It cannot scan ahead to promise a future common opening minute. Pending groups wait for
eligible contemporaneous execution events and expire according to the spec. At the M1
close phase it can establish which predeclared next-open intents had valid simultaneous
opens, without allowing strategy use of that minute's later extremes to select entries.

Stops manage every exposed leg on its own fresh candle. If a leg stop triggers a group
exit, do not infer the other leg's price at the unknown intraminute trigger from its
minute high/low. Use a spec-defined executable exit phase after confirmation; a closed
market leaves an explicit residual leg until its next permitted execution. Concurrent
SL/TP ambiguity stays conservative within each leg. Last-close marks can value closed
markets with staleness disclosed, but cannot fill forced exits. End-of-data cannot
pretend both legs liquidated at an earlier shared close: report residual/unresolved
exposure unless a previously declared end policy yields actual executable exits.

`risk/` allocates account capital once per group: account risk budget * w_i to leg stop
risk, then applies instrument value, currency conversion, lot steps and minimum lots.
Reject an infeasible hedge or report changed realized weights under an explicit sizing
policy. Check gross exposure, margin, currency/correlation limits and residual-leg risk;
net notional near zero is no exemption. Consume group totals once for closed-trade
metrics and leg paths for floating equity/daily protection at Prague resets. Never count
both the group row and its legs as independent trades or double-apply `risk_weight`.
Daily MTM must combine contemporaneously available leg marks; independent leg extrema
are at most a labeled conservative bound, not an observed simultaneous equity path.

Extend `risk/sizer.py`, `risk/prop_rules.py`, Monte Carlo and group account simulation
explicitly; filling the `account_sim.py` stub is a separate substantial part of B if exact
account protection is required. Bootstrap a group/dependent daily block together, never
shuffle its legs independently. Existing portfolio weighting operates outside group R.

## C — cross-sectional universe and baskets

Third priority by infrastructure effort. Adds harvest #2/#3 commodity sorts and #5 weekly
index reversal; FX strength needs this stage only when it trades a coordinated basket.
Reuse A's bounded inputs and B's execution/risk groups, extending the leg count and
adding scheduled rebalance state. Declare the universe, membership history, eligibility,
common observation windows, ranking/ties, weights, minimum breadth, replacement rules
and behavior after stops in a strategy spec. No full-sample winner-based universe or
silent re-ranking after a member's data disappears.

At rebalance, rank only eligible closed observations at the declared decision timestamp.
Generate a deterministic target/delta plan, reserve total group risk, then execute according
to explicit market-opening and partial-basket rules. Track holding vintages, turnover,
pending exits and actual remaining weights. Different market holidays cannot be resolved
by treating a stale close as a fresh return. Rebalance costs/financing cover every actual
leg change. Distinguish one rebalance event, one basket holding and individual leg entries
in reports; the research spec must name the unit used for its minimum sample gate.

## Runner, research, artifacts and UI

| Area | A | Additional work for B/C |
|---|---|---|
| Runner | Resolve primary/dependencies; bundle loading/cache; primary-clock snapshots; cancellation/progress; source/coverage notes | One shared-state group/universe job; no splitting legs into symbol tasks; group result and execution journal |
| Grids | Optional explicit mode/input declarations; preserve old `symbols` semantics and hashes when absent | Pair definitions or universe identity, leg/exposure policies and rebalance config; validate before execution |
| Identity/resume | Hash resolved roles, boundaries, freshness, all input symbols and settings; manifest dependency sources and warm-up files | Include group/risk convention version, hedge/sizing/execution policies and universe membership; no resume reuse after changes |
| Data split | Apply 2021-09-13/14 cutoff to all inputs; develop only from closed pre-cutoff observations; pre-test history may warm test indicators | Joint eligible segments and synchronized group state; no trade or fitted parameter carried from development into holdout |
| Trials/selection | Keep net-R selection, trial counting and user-authorized one-time test; dependency variants are trials | Rank group/basket R; count all pair/universe/weight searches; declare group sample unit |
| Daily analytics | Primary trade list unchanged; dependency provenance for diagnostics | Group-aware MTM, leg attribution, daily costs, floating exposure, bootstrap and statistical diagnostics |
| Gates/tools | Dependency coverage/age and causal timestamp checks; every input loaded through saved sources | Joint fill/exit integrity, group risk sum, hedge exposure, residual legs, missing marks and accounting reconciliation |
| UI | Keep single-symbol chart/trade UI; show primary and read-only dependency summary/skip reasons | Explicit group summary and leg tables; until supported, reject group chart/risk actions clearly instead of presenting ordinary single-symbol results |

Extend `tools/research.py` (`_pieces`, period assembly, dataset manifests),
`tools/research_grid.py`, `tools/research_helpers.py` and `tools/research_series.py` with
separate bundle paths. Joint segments use required-input coverage, not today's separately
assembled symbol trades. Warm-up is calculated per dependency and cannot cross genuine
gaps; require each declared indicator's readiness. Holdout warm-up cannot create pre-period
positions or tune development parameters. Preserve existing test-authorization and retest
guards; no actual holdout runs form part of this design or its implementation tests.

Existing submission dataset versions fingerprint resolved day-file paths/sizes, not candle
contents. Extend new-mode manifests to include all inputs (including conversion symbols
and loaded warm-up), while stating this limitation; do not silently change legacy IDs.
New-mode diagnostics needing marks must use saved dependency sources and causal bounds.

Strategy gate tools such as `tools/h1_shock_gates.py` currently load traded `run['symbols']`;
do not globally rewrite these strategy-specific tools. Add dependency/group-aware shared
loaders and dedicated gates for new strategies. Adapt `research_entry_screen`, significance,
monkeys, bounds, profile, Monte Carlo and portfolio readers before claiming they support
group results. Until adapted, mark a diagnostic unavailable with a reason, never pass a
flattened group as independent observations or label the research gates fully passed.

Version new-mode artifacts separately: keep A's `trades.csv` schema; add dependency manifest
and decision journal. B/C add `groups` and `legs` artifacts with IDs, timestamps, fixed
normalization and attribution, plus a common daily R path. A synthetic symbol such as
`WTI_BRENT` must not be used to trick existing price/stop-based readers into accepting it.
Legacy readers and existing saved runs remain readable. No Plotly/Dash imports enter
core, detectors, strategy, engine or risk; shared contracts belong in core/strategy,
execution in engine, data loading in runner/data, account scaling in risk.

## Tests and compatibility acceptance

Implementation must start with test files and hand-built candles, before production code.
This documentation-only task adds no test code and runs no backtests.

1. **Cross-symbol lookahead:** A M1 candle opens 10:00 and closes 10:01; B's next opens
   10:01 and closes 10:02. At 10:01 A cannot read B's 10:02 close: B is `None` or at
   its older cursor and access beyond it raises `LookaheadError`. At 10:02 publish all
   closes together, including an H1 close at exactly 10:02 if present. Repeat with a
   realistic H1 boundary at 11:00, which is invisible at 10:59.
2. Retain snapshots; append or change only future candles of B, A and conversion symbols.
   All earlier views/events/orders/fills/R stay exactly equal. Permuting input mapping
   order cannot change decisions; reject duplicate/unordered candles and non-UTC inputs.
3. Primary M5 callbacks plus multiple intervening B M1 candles: each incremental detector
   processes every new input once, no event precedes confirmation, and no duplicate
   callback occurs during A's closure. A stop still runs when B is missing.
4. Empty histories, short warm-up, intraday holes, missing days versus scheduled crypto
   closures, mismatched holidays and weekends; no fabricated data, stale fills or implicit
   shrinking universe. Test NY 17:00 days, US/EU DST mismatch and retained UTC legacy D1.
5. Next-open intent cannot fill on the signal minute's open; a group cannot use the other
   leg's future open or same-minute extrema to infer a cross-leg stop exit. Test gaps,
   simultaneous stops/targets, rejected second leg, closed-market residual exposure,
   delayed financing and end-of-data without executable liquidation.
6. Group arithmetic: asymmetric stop weights, both stops, zero/NaN risk, conversion
   changes, signed swaps, funding timestamps, tick/lot rounding and group versus leg
   reconciliation. Compare a hand-built example with explicit expected net R. Test daily
   MTM across Prague reset and ensure Monte Carlo preserves linked legs.
7. Research: dependency-only gap splits the bundle; changing a dependency changes only
   new-mode identity; old hashes/resume are unchanged; all inputs respect cutoff; missing
   authorization blocks holdout; no holdout prices enter development diagnostics.
8. Exact regressions: existing registry/default configs, call counts, trade ordering,
   fills, partial exits, costs, swap, warm-up, output schemas and trial IDs remain equal.
   Run existing unit/layer tests and `python -m backtester.tools.golden --check --workers 1`
   in the normal authorized validation workflow with unchanged caches. Never use `--write`
   to bless differences. The current golden period is 2023: do not use this command to
   introduce a new strategy's unspent holdout; use hand-built or development fixtures for it.

Add separate exact A/B/C fixture lists and manifests after their strategy specs exist;
do not regenerate `tests/golden/*.jsonl` or the legacy manifest. Inspect every old trade
field exactly, not just aggregate totals. Byte comparisons of run files exclude volatile
run IDs/creation timestamps only; trade JSON/CSV values have no float tolerance.

**Expected changes to existing results: none.** Likely hazards are switching to union-M1
execution for old strategies, changing daily boundaries, equal-time callback order,
history/warm-up, missing-data policy, arithmetic order or result serialization. Avoid them
by dispatching to new modes only when explicitly declared, leaving the old path and
schemas intact. A nonempty diff in legacy golden trades blocks implementation acceptance;
an unrelated baseline mismatch must be recorded, not overwritten.

## Delivery sequence, estimates and files

Estimates are engineering person-days including test-first implementation and integration,
not elapsed backtest time. They exclude researching/ratifying strategy rules, obtaining
new data, and demonstrating an edge. Ranges reflect the unknown data/calendar quality.

| Rank / increment | Value and completion boundary | Effort | Planned files touched or added |
|---|---|---|---|
| 1a — bounded observations | Shared-time snapshots, readiness and exact legacy regression; no new trading strategy | 3–5 days | `strategy/base.py`; new `core/market.py`, `engine/market_replay.py`; opt-in hook in `engine/backtest.py`; `runner.py`; focused `tests/core/`, `tests/engine/`, `tests/test_runner.py` |
| 1b — research-ready A | Grids, bundle coverage/identity, dependency journal, CLI; ordinary A trades in UI | 3–5 days | `run.py`, `strategy/registry.py`, `tools/research_grid.py`, `tools/research.py`, `tools/research_helpers.py`, `tools/research_series.py`; new bundle gate helpers; `ui/research_model.py`/results metadata; `tests/tools/`, `tests/ui/`; `docs/ARCHITECTURE.md`, `docs/research-runner.md` |
| 2a — paired engine | Two-leg state, risk-normalized result, financing, next-open mode and explicit residual exposure | 7–11 days | New `strategy/group.py`, `engine/group_backtest.py`, `engine/group_trade.py`; `engine/costs.py` only for necessary reusable helpers; bundle runner/artifact writer; `tests/engine/`, `tests/strategy/` |
| 2b — paired research/risk | Group MTM/statistics/gates, sizing and risk consumers; truthful minimal UI | 6–10 days | `analytics/daily.py`, `analytics/trial_log.py`, `analytics/portfolio.py`; `risk/sizer.py`, `risk/prop_rules.py`, `risk/monte_carlo.py`; research diagnostics/profile/pipeline tools and new group gates; `ui/pages/results.py`; matching tests; `docs/risk-management.md` |
| 2c — account protection | Implement and validate grouped floating-equity account simulation where currently a stub | 5–8 additional days | `risk/account_sim.py`, account/prop integration and `tests/risk/`; separate spec-backed scope, never silently included as existing functionality |
| 3 — baskets | Universe eligibility, rankings/rebalance, N-leg allocation/execution and diagnostic extensions | 7–12 days after B | New strategy-local universe/ranking modules and frozen configs; group engine, runner, research grid/gates, risk sizing/exposure, daily analytics; basket tests/fixtures; optional later UI detail |

A total: 6–10 days; B adds 13–21 days plus 5–8 if account simulation is required; C adds
7–12. A-only rank/breadth signals need not wait for B/C. Each new strategy additionally
needs its own `docs/strategy-<name>.md`, `strategy/<name>/`, registry/config entry,
`tests/strategy/<name>/` and pre-registered grid; estimate separately after its rules exist.
All paths in the table are relative to `src/backtester/` unless prefixed `tests/` or `docs/`.

## Decisions required before strategy implementation

No existing trading rule needs reinterpretation to write this design. The harvest explicitly
calls its common conventions “research assumptions to be reviewed in a formal spec”; it
also requires specifying calendar/holiday bars, fills and paired exposure before building.
Consequently this document does not choose missing strategy rules. Before B/C, a strategy
spec must settle common entry eligibility/expiry, partial or atomic execution, the other
leg's exit after a stop, missing marks and end-of-data, ratify the group R convention,
and define account limits and sample counting. Before any A strategy, it must define
observation freshness, calendar/windows and close versus next-open fills. If these are
unclear or contradict a rule, stop and quote the relevant spec to the user. None blocks
this infrastructure proposal; none authorizes a one-time MT5 test.
