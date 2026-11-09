# I-62 no-wick retest prior-result audit

Date: 2026-10-29  
Decision: **reject on the current evidence; do not reopen through filters, exits, or direction reversal**.

## Scope and evidence boundary

This note does not rerun the experiment or inspect V2-internal results. It preserves the result
already present in the frozen research import `existing_material/backtester_v2/ideas.md`:

- the no-wick retest family searched 4,608 variants;
- only 0.4% were positive;
- no symbol class showed an edge; and
- the apparent gold H1 cluster failed out of sample at -0.02 R/trade.

The imported record also identifies the principal mechanism: a limit at the body end tends to fill
when price is returning through the signal candle, creating adverse selection. Tight stops amplify
cost-model sensitivity, while the apparent gold result depended on unpriced overnight exposure and
the daily-reopen spread. Those facts are inherited research evidence, not a new canonical result.

## Multiplicity interpretation

The 4,608-cell search already covered many stop, target, timeframe, symbol, trend-filter, higher-
timeframe, and session choices. The 0.4% positive fraction is therefore evidence against a stable
plateau, not an invitation to preserve the best cells. The failed out-of-sample cluster is the
relevant adjudication of that selection.

The following are not independent hypotheses:

- adding another trend, volatility, volume, session, or higher-timeframe filter;
- widening the stop or changing the target after seeing the failure;
- replacing the limit fill with a slightly different retest tolerance;
- reversing the trade direction because fills showed adverse selection; or
- renaming the same candle geometry as imbalance, order block, role reversal, or mitigation.

Each changes a selected implementation dimension while retaining the same no-wick-candle/retest
event. A direction reversal would also be a post-result choice and would pay another complete cost
burden.

## Decision

Close I-62 on the current data and retain the failed experiment. It cannot be used as a base for
I-49/I-50/I-56 filters or I-54/I-60 exit overlays, because those methods require an independently
positive frozen base.

Reconsider only if genuinely independent external evidence specifies, before local data access, a
materially different causal event, one direction, one entry, one exit, and a cost-aware validation
plan. A new label, filter, or parameter range is insufficient.
