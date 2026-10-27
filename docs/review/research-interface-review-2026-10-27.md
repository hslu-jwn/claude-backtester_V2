# Review: research department interface (contract 0.1.0)

Date: 2026-10-27. Reviewer: backtester team (Opus). Inputs: `../BACKTESTER_TEAM_HANDOVER.md`,
`../BACKTESTER_TEAM_INTEGRATION_PROMPT.md`, `../Shared_Interface/` (contract, three schemas,
`documentation/`), `../Research_Department/reports/` (discovery, migration inventory), the two
pilot drafts. Checked against V2 code (`strategy/base.py`, `engine/backtest.py`, `filelock.py`,
`pyproject.toml`) and V2 docs. No engine, live, data or result file was changed.

Verdict: **the split is sound and we accept the ownership model.** The contract needs the
changes in section 2 before it is frozen as `0.1.0` for a pilot; neither pilot draft can run
faithfully in the V2 engine today (section 1.3).

## 1. Compatibility review

### 1.1 What fits V2 as it is

- Spec-first: the JSON is inert data; V2 `docs/strategy-<name>.md` stays the source of truth.
  Matches AGENTS.md › Specs are the source of truth.
- Separate strategy queue (`Shared_Interface/queue/`) vs V2 compute-job queue
  (`results/queue`): correct, the payloads and lifecycles differ.
- Result envelopes that reference `results/<run-id>/` and `results/research/<id>/` instead of
  copying them.
- Atomic rename on one volume: umbrella, V2 and Research_Department are all on `X:`;
  `os.replace` is atomic there. `backtester.filelock` can serialise the claim.
- Immutable `(strategy_id, specification_version)` and "revision = new version".
- Development before 2021-09-14, one test after on MT5 data: the contract's
  `DEVELOPMENT` / `FINAL_HOLDOUT` stages map onto it.

### 1.2 Contradictions and gaps found

| # | Where | Problem |
|---|---|---|
| C1 | Evaluation stages | V2 has two stages (development, one-time test). The contract has three; `VALIDATION` has no V2 equivalent. |
| C2 | Holdout | V2's holdout is a fixed calendar cut shared by every strategy, not per experiment. Research agents can read V2 `results/` directly, so "redacted" disclosure is not enforceable by envelopes alone. |
| C3 | `experiment.minimum_viable_test` | Free text lets research name periods; periods are fixed by V2 and must not be negotiated per submission. |
| C4 | Stopless strategies | `Order.stop_loss` is a required float and every result is in R (`strategy/base.py`). `exits.stop_loss: null` is not representable. This includes the US500 final-30 pilot, not only the momentum ones (its risk field says "do not infer stop-defined R"). |
| C5 | Fill timing | V2 fills at the signal candle's close (`engine/backtest.py`). "Next M1 open" differs only on a gap / spread jump, but the spec forbids the close. Needs one agreed mapping. |
| C6 | Metrics | `result.metrics` has no units. V2's drawdown, expectancy and Sharpe are in R (daily R for DSR); `net_return` is undefined for R strategies. |
| C7 | Feedback scope | `feedback.schema` requires `strategy_id` + version, so a file whose JSON or name cannot be parsed, or a contract-level question, cannot be answered in-schema. |
| C8 | Progress status | `CLAIMED` / `IMPLEMENTING` / `TESTING` exist in the lifecycle but in no schema; research cannot see progress. |
| C9 | Checksum | The contract rejects on "checksum mismatch" but no schema field carries a checksum. |
| C10 | `status` in the queue | `strategy.schema` allows `DRAFT` and `submitted_at: null` in a submitted file. |
| C11 | Parameters | `math.parameters[].allowed` is free text; V2 grids need exact values (min / max / step or a list) to count variants for the trial log and DSR. |
| C12 | Universe / costs | Universe names are free text (`US500` vs ETF tickers); requested costs can differ from V2's resolved FTMO costs. |
| C13 | Temp files | "Unique temporary file in `pending/`" has no naming rule; a consumer cannot tell a temp file from a bad submission. |
| C14 | Data | V2 has OHLC + tick volume (MT5, histdata, Binance); no real volume, no dividend-adjusted prices, no exchange early-close calendar. |
| C15 | Dependency | `jsonschema` is not a V2 dependency; Research's validator has a hand-written fallback. |

### 1.3 Pilot drafts against V2 today

| Draft | V2 verdict now | Why |
|---|---|---|
| `US500_FINAL30_CONT` v0.1.0 | `UNSUPPORTED_STRATEGY_TYPE` until decision D4 | stopless, notional sizing (C4); needs early-close calendar (C14) and next-open mapping (C5). Otherwise close to V2 (one signal, timed exit, explicit costs). |
| `ETF_ABSMOM_12M_LC` v0.1.0 | `UNSUPPORTED_DATA` + `UNSUPPORTED_STRATEGY_TYPE` | needs adjusted total-return ETF data and monthly target-weight rebalancing. |
| cross-asset TSMOM (parked) | `UNSUPPORTED_STRATEGY_TYPE` | stopless, vol-targeted portfolio, daily mark-to-market. |

The handover calls the final-30 pilot "close to V2's candle model"; it is close in timing, but
the stopless, unit-notional accounting is a model change, not a mapping.

## 2. Recommended edits to the canonical contract / schemas (proposals for Research)

1. `strategy.schema`: when in the queue, `status` must be `SUBMITTED` and `submitted_at`
   non-null (C10). Add `submission_sha256` handling outside the payload: the consumer computes
   the hash of the bytes and records it; drop "checksum mismatch" from the contract or add a
   sidecar `<file>.sha256` (C9).
2. `math.parameters[]`: replace `allowed` with structured `values` (list) or `min` / `max` /
   `step`, plus `grid_size` at the experiment level (C11).
3. Drop period choice from `experiment.minimum_viable_test`; add a fixed note that periods
   follow the backtester's split (C3).
4. `market.universe`: names must be V2 symbols (list in `docs/ARCHITECTURE.md` / `tools.mt5_info`);
   anything else is `UNSUPPORTED_DATA` (C12).
5. `exits` / `risk`: add an explicit `accounting` enum: `R_STOP_DEFINED` (V2 today) or
   `UNIT_NOTIONAL` / `TARGET_WEIGHT` (needs D4); stopless requires a non-R accounting (C4).
6. `entries.execution_time`: add an enum `SIGNAL_CLOSE` | `NEXT_BAR_OPEN` | `LIMIT` with the
   free text as a comment (C5).
7. `result.schema`: rename / annotate metrics with units (`net_r`, `max_drawdown_r`,
   `expectancy_r`, `sharpe_daily_r`, `net_return_pct` only for non-R accounting); add
   `submission_sha256`, `code_commit`, `cost_model` (resolved), `stage_split` (C6, C9).
8. `result.evaluation_stage`: either drop `VALIDATION` or define it as walk-forward inside the
   development period (C1, D1).
9. `feedback.schema`: make `strategy_id` / `specification_version` nullable with a
   `subject_file` field, add `scope: SUBMISSION | CONTRACT`, add progress statuses
   `CLAIMED` / `IMPLEMENTING` / `TESTING`, and `in_reply_to` (C7, C8).
10. Contract: temp files are named `.tmp-<anything>` and every consumer ignores dot-files (C13).
11. Contract: research agents do not read V2 `results/`, `docs/research-log.md` result rows or
    test-period artifacts; they read only envelopes (C2).

## 3. Decisions needed

From the user:

- **D1** Keep V2's two stages (develop before 2021-09-14, test once after) and drop
  `VALIDATION`, or define validation as walk-forward in development? *Proposal: drop it.*
- **D2** When to build the adapter: after V2.6d (fill work) or in parallel in a lane?
  *Proposal: after V2.6d step 1 analysis; the bot keeps running either way.*
- **D3** Add `jsonschema` as an optional V2 dependency (`[intake]`)? *Proposal: yes, optional extra.*
- **D4** Stopless / notional / portfolio strategies: separate vectorised harness, a later engine
  capability, or reject for now? *Proposal: reject now; decide after the first R-type pilot.*
- **D5** Next-bar-open: map to "fill at the signal close" (time-equivalent on M1) or add an
  engine option? *Proposal: an engine option later; until then reject `NEXT_BAR_OPEN`.*
- **D6** The existing V2 idea backlog (`knowledge/ideas.md`) and the pre-registered hypotheses
  (strategy 4 on GBPJPY, 5 / 7 in quiet sideways markets): hand them to Research or keep them
  as V2 work? *Proposal: hand the backlog over; the three pre-registered tests stay V2 work.*
- **D7** Who authorises the one-time test of a submission: the user only (as now)? *Proposal: yes.*
- **D8** Completed / rejected queue files: keep forever (local)? *Proposal: yes.*

From the research team: the edits in section 2, plus lease length, worker identity and
experiment-ID rule (proposal below).

Claim proposal (for D-lease): one worker (Opus session) at a time; claim = `backtester.filelock`
on `queue/.claim.lock`, then `os.replace` pending -> claimed, then write
`results/intake/<strategy_id>__v<ver>/claim.json` (worker, time, sha256). Recovery: a file in
`claimed/` without `claim.json` older than 1 h goes back to `pending/`. Experiment ID =
`<strategy_id>__v<ver>__<stage>__<n>`, `n` counting up per stage; idempotent because an existing
ID is never re-used.

## 4. Test-first plan (V2 ROADMAP V2.6i)

| Step | What | Tests first |
|---|---|---|
| i1 | Contract frozen with the section-2 edits; fixtures: valid, partial JSON, schema-invalid, wrong name, traversal, unsupported major, duplicate | fixture set under `tests/intake/fixtures/` |
| i2 | `tools/intake.py validate`: read-only, containment, name = identity, schema, duplicate | each fixture -> exact error code |
| i3 | claim + recovery with `filelock`; `results/intake/` records | two-worker race, crash before / after `claim.json`, stale recovery |
| i4 | mapping file `docs/strategy-<name>.md` › Submission mapping (every parameter and rule -> config field / code / test) | missing mapping = refusal |
| i5 | metadata in `settings.json` / trial log: strategy_id, spec version, experiment_id, dataset version, commit, stage | round trip; old runs still load |
| i6 | envelope emitters (result, feedback), atomic, references only, sha256 of artifacts | schema-valid; paths inside the umbrella; test-stage run refused without the user's authorisation file |
| i7 | synthetic echo strategy end to end (submit -> claim -> tiny run -> envelope) | full chain in a temp umbrella |
| i8 | first real R-type pilot, development stage only | — |

No engine change in i1-i7. Everything new lives in `tools/intake.py`, `results/intake/`,
`tests/intake/` and one optional extra.

## 5. Reuse and unsupported

Reused: `backtester.filelock`, atomic JSON writes, strategy registry / config / `_template`,
`tools.research` (split, trial log, DSR, robustness, one-time test guard), the job queue (only
after a submission is a V2 strategy), `runner.write_results` run IDs, lanes.

Unsupported now: stopless or notional sizing, target-weight portfolios, monthly rebalancing with
daily mark-to-market, cash / funding accounting, dividend-adjusted data, exchange early-close
calendars, real volume, next-bar-open fills.
