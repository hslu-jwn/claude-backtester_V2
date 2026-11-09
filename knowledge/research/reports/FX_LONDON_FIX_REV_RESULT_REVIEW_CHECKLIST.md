# FX_LONDON_FIX_REV v1.0.0 pre-result review checklist

Date frozen: 2026-10-28, before any canonical result envelope existed.  
Scope: development result interpretation only. No holdout is authorized.

## Identity and traceability

- Identity is `FX_LONDON_FIX_REV` v1.0.0 and the submission hash matches the claimed immutable file.
- Evaluation stage is development with the fixed pre-2021-09-14 split.
- The envelope names the V2 code commit, implementation version, experiment ID, dataset identity,
  requested and resolved cost models, and artifact references.
- Linked canonical feedback is applied: real swap is charged when the 360-minute hold crosses
  17:00 New York, including Wednesday triple swap; an unexpectedly missing 23:55 London force-close
  bar uses the next valid bar. The stale no-swap sentence in the submitted payload is not used.

## Completeness

- All nine stop-multiplier by holding-horizon cells are present and `variants_tried` accounts for
  all nine plus the program's registered prior trials.
- Per-symbol, pooled-by-day, development-half, month-end/non-month-end, doubled-cost, best-five-day
  removal, stop-frequency, and matched-random-time outputs are present.
- The pooled inference treats same-day USD-pair trades as dependent; six pairs are breadth, not six
  independent samples.
- Warnings disclose missing fix holidays, data gaps, forced exits, unresolved assumptions, and any
  divergence from requested execution.

## Primary versus exploratory cells

The submitted specification names `stop_atr_multiplier=4.0, holding_minutes=360` as its baseline
but does not define a mechanical selector for choosing among the other eight cells. Therefore:

- the declared baseline is the only primary confirmatory cell;
- all other cells are robustness/exploratory evidence and remain counted trials;
- a favorable non-baseline cell cannot be promoted, queued as a selected rule, or proposed for the
  final holdout from this result;
- no ranking metric, tie-breaker, or selector may be invented after seeing the nine-cell table.

This interpretation is deliberately stricter than “at least one variant.” It does not alter any
entry, exit, cost, or computation requested from V2; it prevents post-result parameter selection.

## Predeclared economic and stability gates

For the baseline, record each gate separately rather than collapsing them into a score:

1. pooled direction-normalized gross return is positive;
2. at least four of six symbols have the predicted gross sign;
3. pooled net R is positive under resolved V2 costs;
4. pooled net R remains positive under doubled spread, commission, and slippage;
5. both fixed development halves have positive net R;
6. non-month-end observations retain the predicted sign;
7. removing the five most profitable days leaves net R positive;
8. real entries beat at least 90% of matched random-time entries on both net R and max drawdown R;
9. stop frequency is low enough that the wide safety stop did not replace the source's time-exit
   mechanism.

Any failed mandatory gate is reported as failure, even if another variant or gross metric is
positive. The primary paper's after-cost liquidity-demander results are adverse, so a null or
negative net result is the expected and informative outcome.

## Allowed conclusions

- **Integration success** means the canonical claim-to-result trace is complete and semantics are
  faithfully mapped. It does not require profitability.
- **Research failure** means the baseline fails any mandatory net/stability gate. Retain it and do
  not redesign the fix family on the same development result.
- **Research candidate** requires every baseline gate above, independent review of the canonical
  result, and a separate explicit user decision before any one-time holdout. Nothing in this
  checklist grants that decision.

