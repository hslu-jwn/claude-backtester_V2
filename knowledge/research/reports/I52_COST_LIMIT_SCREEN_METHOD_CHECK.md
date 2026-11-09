# I-52 cost-limit screen method check

Date: 2026-10-28  
Decision: retain as a one-sided pretest rejection/ranking tool; remove any interpretation that
passing a fixed cost threshold is evidence of edge.

## Question and result

I-52 proposes rejecting a strategy when estimated turnover times standardized round-trip cost is
more than one third of an assumed pre-cost Sharpe of 0.40. The arithmetic intuition is sound:
turnover converts a small per-trade friction into a potentially dominant annual drag. The numeric
`0.13` cutoff is a book heuristic, however, not a transferable empirical constant. It depends on
an assumed gross Sharpe that an untested strategy has not earned.

The safe use is asymmetric. A conservative cost lower bound that already exceeds an independently
defensible gross-edge upper bound can reject or deprioritize an idea before a grid is run. The
reverse is false: low estimated cost does not establish predictability, correct direction, or
positive net expectancy.

## Evidence inspected

- Frazzini, Israel, and Moskowitz, *Trading Costs of Asset Pricing Anomalies* (working paper,
  2012--2014), <https://doi.org/10.2139/ssrn.2294498>. The full paper was opened. It uses nearly
  one trillion dollars of live institutional trades across 19 developed equity markets and shows
  that capacity and cost vary strongly by strategy; short-term reversal is the most constrained.
  Cost-aware portfolio construction can help, but these institutional impact functions do not
  supply a universal retail-CFD cost ceiling.
- Novy-Marx and Velikov, *A Taxonomy of Anomalies and Their Trading Costs* (NBER working paper
  20721), <https://doi.org/10.3386/w20721>. The full working paper was opened. Low-turnover equity
  anomalies survive costs more often, while few higher-turnover strategies do. This supports
  turnover as a triage variable, not the proposed `0.13` constant or intraday transfer.
- Neely and Weller, *Intraday Technical Trading in the Foreign Exchange Market*, Journal of
  International Money and Finance 22 (2003),
  <https://doi.org/10.1016/S0261-5606(02)00101-8>. The full working-paper version and published
  article were opened. Stable half-hourly FX predictability produces no excess return after
  realistic costs and normal trading-hour restrictions. This directly shows why a gross pattern
  cannot substitute for endpoint-cost accounting.
- Frömmel and Lampaert, *Does frequency matter for intraday technical trading?*, Finance Research
  Letters 18 (2016), <https://doi.org/10.1016/j.frl.2016.04.014>. The full paper was opened. Using
  observed time-varying bid/ask costs and more than 8,000 RUR/USD rules, real costs erase most
  apparent profits. The surviving regime is unusually managed and does not justify a general
  threshold.

## Research-department rule

For an untested idea, report a cost burden rather than a pass certificate:

1. estimate annual signal count or round trips from rule mechanics without reading outcomes;
2. use the authoritative V2 resolved cost schedule by symbol and signal clock, reporting median,
   high-cost, and doubled-cost cases rather than a single tranquil spread;
3. express the drag in the strategy's eventual accounting unit (price, return, or stop-defined R),
   with every entry/exit and disjoint block counted;
4. compare it only with an externally supported or explicitly labeled optimistic gross-edge bound;
5. reject when costs dominate that bound; otherwise label the idea `COST_FEASIBLE_UNKNOWN_EDGE`.

For a completed development experiment, actual net results and stressed costs supersede the
screen. Never tune signal frequency, session, holding time, or stop distance until the screen
passes; that creates a new strategy family and multiplicity. Passing I-52 neither raises research
priority by itself nor rescues a failed strategy.

## Implication for current work

R-2026-003 already uses resolved/stressed costs and has a directly adverse source prior. R-2026-004
has a fixed signal-time event-move floor plus actual/stressed P&L costs. R-2026-005 charges a new
round trip for every disjoint residual block. None should acquire an additional optimized I-52
threshold. Use the screen only when triaging a genuinely new, mechanically specified idea.

## I-45 per-trade cost-to-target ratio

I-45's `round-trip cost / target distance` is the trade-level form of the same screen, not an
independent filter. A ratio of 0.10 says only that cost consumes 10% of a full target. With target
`T`, stop loss `S`, and round-trip cost `C`, the idealized break-even win probability is
`(S + C) / (S + T)`; therefore no universal 0.10–0.15 cutoff exists without the stop, fill model,
and independently justified hit-rate distribution.

For example, with `S = T` and `C/T = 0.10`, break-even rises from 50% to 55%. Increasing the target
to force the ratio below the cutoff also changes hold time, hit rate, stop geometry, and strategy
identity. It is not a free cost optimization.

Use I-45 only as a causal signal-time diagnostic with the authoritative resolved cost and frozen
target. A conservative high-cost ratio can reject a trade design before outcomes are read. Passing
must be labeled `COST_FEASIBLE_UNKNOWN_EDGE`. Do not optimize the ratio threshold, target, clock, or
symbol from development P&L, and do not add I-45 separately to strategies that already use an event-
move cost floor and resolved/stressed net accounting.
