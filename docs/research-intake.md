# Research intake: how V2 takes strategies from the research department

Process spec (the user, 2026-10-27). **Status: the interface is a proposal, not operational.**
Until ROADMAP V2.6i passes its synthetic end-to-end test, no real submission is claimed or built.
Review of the contract: `docs/review/research-interface-review-2026-10-27.md`.

**Contract 0.1.0 accepted by both teams 2026-10-27** (all 14 requests and D1-D8 applied,
`../Shared_Interface/feedback/messages/CONTRACT_ACK_2026-10-27.json`). Fields the intake checks:
`market.v2_compatibility` = `SUPPORTED` (universe ⊆ `../Shared_Interface/documentation/V2_SYMBOLS.json`),
`market.holding_period` = `DAY_TRADING` (else low priority), `risk.accounting_type` =
`R_STOP_DEFINED` with a non-null `exits.stop_loss`, `entries.execution_timing` = `SIGNAL_CLOSE` or
`LIMIT`, parameter `domain` (`FIXED` / `VALUES` / `RANGE`) with `experiment.total_grid_size` =
product of the tunable domains. Some checks are not expressible in the JSON Schema and live
only in Research's validator (`status: SUBMITTED` + `submitted_at`, `RANGE` needs
min / max / step, grid-size product, symbols list): V2.6i i2 repeats them, never trusts the
producer's check. `V2_SYMBOLS.json` is a snapshot of `data/sources.py` `PRICE_DIGITS`; when V2 adds or
drops a symbol, we propose the update to that file.

## Who owns what

| Research department (`../Research_Department/`) | Backtester team (this repo) |
|---|---|
| Literature, papers, studies, community sources | Implementation, data, costs, engine, risk, live |
| Hypotheses, mechanism, falsifiable predictions | `docs/strategy-<name>.md` spec written from the submission |
| Complete JSON strategy specification, its versions | Mapping submission -> config / code / tests |
| Research priority (`priority` field) | Experiments, statistical validation, trial log, DSR |
| Reads result / feedback envelopes | The one-time test (holdout) and its authorisation |

The backtester team no longer does literature research or invents strategy ideas. `knowledge/`
is frozen background (see `knowledge/README.md`); new ideas arrive only through the queue.
Our evaluation methodology (`knowledge/topics/testing-and-robustness.md`,
`statistics-and-bayes.md`, `costs-and-execution.md`, `backtest-frameworks.md`) stays ours.

## Paths (all canonical, never copy them into V2)

- Submissions: `../Shared_Interface/queue/pending/<STRATEGY_ID>__v<x.y.z>.json`
- Claimed / terminal: `../Shared_Interface/queue/{claimed,completed,rejected}/`
- Our answers: `../Shared_Interface/feedback/results/` (result envelopes) and
  `feedback/messages/` (feedback envelopes)
- Schemas: `../Shared_Interface/schemas/`; contract: `../Shared_Interface/INTERFACE_CONTRACT.md`
- Our claim / mapping records: `results/intake/<STRATEGY_ID>__v<x.y.z>/` (git-ignored)

The strategy queue is **not** the compute-job queue (`results/queue`). A submission becomes a
compute job only after it is a reviewed V2 strategy.

## Pipeline per submission (replaces the old "idea -> spec" pipeline)

1. **Intake** (Opus): pick the highest-`priority` file in `pending/`; validate (name =
   identity, schema, status `SUBMITTED`, no duplicate); claim it atomically. A failure gives a
   feedback envelope, nothing runs.
2. **Compatibility check** (Opus, Codex second opinion): data available for the universe and
   period? stop-defined R trade? fill timing representable? Otherwise feedback
   `UNSUPPORTED_DATA` / `UNSUPPORTED_STRATEGY_TYPE`. Never approximate (no invented far stop,
   no changed sizing, no swapped fill timing).
3. **Clarify**: any rule that needs judgment -> feedback `NEEDS_CLARIFICATION` quoting the field
   (JSON Pointer). Research answers with a new specification version; we never guess.
4. **Spec** (Codex): `docs/strategy-<name>.md` from the submission, with a "Submission"
   section: strategy_id, version, sha256 of the submitted bytes, and a mapping table of every
   parameter and rule to a config field / code location / test. The user approves the spec.
5. **Tests, code, review**: as AGENTS.md › Team and › Testing (test-first, lane, no-lookahead
   review).
6. **Development experiment**: grid from the submission's tunable parameters and ranges only
   (adding a variant = feedback, not a silent extension); everything in the trial log; DSR,
   robustness, Monte Carlo, parameter stability, regime breakdown, flags; job queue.
7. **Result envelope** (development stage): metrics, the submission's rejection criteria
   computed (we report them; the user decides), references to `results/<run-id>/` and
   `results/research/<id>/`.
8. **One-time test** after 2021-09-14: only with the user's explicit go per strategy. Its
   envelope discloses only what the agreed holdout policy allows.
9. **Close**: move the queue file to `completed/` or `rejected/` (never deleted), update
   `docs/research-log.md`, ROADMAP, HANDOFF.

## Decided (the user, 2026-10-27)

Two stages only (develop before 2021-09-14, test once after); the adapter is built after the
V2.6d step-1 fill analysis; `jsonschema` as optional extra `[intake]`; stopless / notional /
target-weight / portfolio strategies and `NEXT_BAR_OPEN` fills are rejected for now
(`UNSUPPORTED_STRATEGY_TYPE`; future options in the review › section 6); the one-time test only
on the user's go; queue files kept forever. Details: review › section 3.

Focus (rule set by the user, 2026-10-27): strategies are **day trading** (flat by the end of
the session / day, no overnight holds); multi-day submissions are low priority.

## Rules that stay

No lookahead; fixed split (develop before 2021-09-14, test once on MT5 after); one parameter
set pooled across markets by default; never change defaults (costs, sweep options, spread
table) without the user; V2 costs are the ones applied, the submission's requested costs are
recorded next to them; do not judge pass / fail, the user decides.

## Intake commands

Run with `python -m backtester.tools.intake`; `--root <umbrella>` selects the umbrella
containing `Shared_Interface/` and this V2 directory. The default is the parent of V2.
Only synthetic temporary umbrellas have been exercised; real intake remains subject to the
operational gate above.

```text
validate
claim [--worker <name>]
recover
reject
progress <STRATEGY_ID>__v<version> CLAIMED|IMPLEMENTING|TESTING
finish <STRATEGY_ID>__v<version> completed|rejected
result <STRATEGY_ID>__v<version> --research-folder <path> --stage DEVELOPMENT [--requested-costs <JSON-object>]
```

`reject` quarantines invalid pending submissions and emits rejection feedback. Unsupported
capabilities on an existing claim use `reject_unsupported()`; data errors take precedence over
strategy-type errors. `result` publishes an envelope and a durable experiment record; `finish`
separately moves the original submission to its terminal directory. Queue collisions retain
both files, using `.dup-<n>.json`. No command starts a research run.

`emit_result(..., stage="FINAL_HOLDOUT")` requires the step-2
`results/intake/<stem>/test_authorization.json` with `authorized_by: "user"`, a nonempty quote,
parseable `authorized_at`, and the development experiment ID recorded in the research folder.
It defaults to `REDACTED`: metrics are null and diagnostics, robustness and artifact references
are withheld. An explicit `holdout_disclosure="FULL"` API argument permits full disclosure;
there is no CLI switch for that. Development disclosure is `NONE` (no holdout disclosure).

## Result metric mapping

Read submission, dataset and code provenance from the selected run's `info.json`, cross-checking
its submission against the research folder's `info.json` and claim. Research `version` records
the implementation format version (legacy format defaults to `1`). Dataset `source_summary`
lists are joined with `; ` for the schema's string field. Select `chosen.id`, otherwise the
lowest recorded rank in `variants.csv`; never choose from holdout performance. Development
metrics use `variants/<id>/`; holdout metrics use the recorded `test.run_folder`.

| Envelope metric | Recorded source |
|---|---|
| `net_r` | `summary.json` → `combined.net_r_net` |
| `max_drawdown_r` | `summary.json` → `combined.max_drawdown_r_net` |
| `expectancy_r` | `summary.json` → `combined.expectancy_r` |
| `sharpe_daily_r` | Development `scorecard.json` → `day_sharpe` (daily R, not per-trade Sharpe) |
| `profit_factor`, `trades`, `win_rate` | Same keys in `summary.json` → `combined` |
| `average_win_r`, `average_loss_r` | `combined.avg_win_r`, `combined.avg_loss_r` |
| Other metrics | Null; only the requested R metric set is exported |

Missing values remain null. Holdout daily Sharpe remains null because the run does not record
that metric in its scorecard. `variants_tried` sums deduplicated trial-log `count` values whose
recorded `series` lies inside this research folder, including its sensitivity trials; unrelated
families and separately published runs do not inflate the count. Zero recorded trials is an
error, not an invented count of one.

`statistical_diagnostics` preserves `significance.json` (Reality Check, PBO, effective counts,
flags), plus recorded DSR / PSR / `deflated_sharpe` / flags when present in the selected
scorecard, or the holdout `test` metadata. `robustness` preserves the research metadata keys
`grid_robustness`, `sensitivity`, `monkeys`, `twins`, `shocks`, `bayes`, `walk_forward`, and
`drawdown_bounds` when available. No statistics are recalculated by intake.
A DEVELOPMENT envelope never carries test-period evidence: `drawdown_bounds` keeps only
`development`, `bayes.tests` is emptied, and `test.csv`, `report.md` and `bayes.json` are left out
of its artifacts.

`settings.json` supplies `run` → `test_configuration`, `strategy` → `parameters`, and `engine`
→ `execution`; `engine.costs` is copied exactly to `resolved_cost_model`. Requested costs are
recorded separately. Cache paths are converted to umbrella-relative paths. Artifacts list
individual files in the research folder and referenced published run folders, each with its
own SHA-256; directory hashes are not invented. Envelope and artifact paths use `/`, must
resolve inside the umbrella, and traversal is refused. Envelopes validate against the canonical
schema when `jsonschema` is installed, publish through a same-directory temporary file and
`os.replace`, and refuse overwrites. Experiment records reserve IDs before publication, so an
interrupted publication cannot reuse an ID.
