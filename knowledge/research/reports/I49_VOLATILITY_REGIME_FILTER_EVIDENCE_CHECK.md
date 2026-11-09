# I-49 volatility-regime filter evidence check

Date: 2026-10-28  
Decision: retain only as a predeclared reporting/risk diagnostic; do not use it to rescue a failed
strategy and do not create a strategy draft.

## Question and result

The bounded question was whether prior realized-volatility rank supplies a transferable rule that
improves intraday price strategies: trade breakouts/trends only in low-volatility regimes and
fades only in high-volatility regimes. No primary study found supports that universal sign map.
Volatility is persistent and can forecast risk, but the direction of conditional strategy
performance is strategy-, horizon-, and market-specific. Searching multiple percentile buckets
after a strategy fails would create a new selection surface, not independent validation.

## Primary evidence inspected

- Moreira and Muir, *Volatility-Managed Portfolios*, Journal of Finance 72 (2017),
  <https://doi.org/10.1111/jofi.12513>. The full paper was opened. It scales the next month's
  factor exposure inversely with the previous month's realized variance and reports improved
  risk-adjusted performance across several equity factors and currency carry. This supports a
  causal risk-sizing hypothesis, not a low-volatility entry gate or a direction rule for intraday
  breakouts and fades.
- Cederburg, O'Doherty, Wang, and Yan, *On the performance of volatility-managed portfolios*,
  Journal of Financial Economics 138 (2020),
  <https://doi.org/10.1016/j.jfineco.2020.04.015>. The full paper was opened. Across 103 equity
  strategies, volatility-managed versions do not systematically beat unmanaged versions;
  reasonable real-time out-of-sample combinations usually have lower certainty-equivalent returns
  and Sharpe ratios. The authors attribute the shortfall mainly to structural instability. This is
  direct contrary evidence against treating volatility scaling as a universal improvement.
- Gao, Han, Li, and Zhou, *Market intraday momentum*, Journal of Financial Economics 129 (2018),
  <https://doi.org/10.1016/j.jfineco.2018.05.009>. The full preprint and published abstract were
  opened. In SPY from 1993--2013, the first-half-hour return predicts the final-half-hour return,
  and the relation is stronger on more volatile days. That result points opposite to I-49's
  proposed "trend only at low rank" map. It also relies on opening and final-30-minute effects,
  both excluded from the present day-flat research scope.
- Xin, Lam, and Yu, *Effectiveness of filter trading as an intraday trading rule*, Studies in
  Economics and Finance 38 (2019), <https://doi.org/10.1108/SEF-09-2018-0294>. Only the publisher
  abstract/metadata was accessible. It reports a nonlinear relation between realized volatility,
  filter size, and Hang Seng index-futures intraday filter-rule profit. The accessible material
  does not establish a simple low/mid/high rule, transferability to V2 symbols, or a causal
  prior-volatility gate with cost survival. It is a lead, not validation.

## Research-use rule

Volatility rank may be reported for an already pre-registered primary strategy if all of the
following are frozen before its result is seen:

1. one causal measure using only closed bars before the signal;
2. one lookback and fixed bucket boundaries;
3. all buckets reported with event/trade counts and costs;
4. no bucket may turn a failed unconditional primary result into a passing strategy;
5. bucket tests count in the multiplicity ledger.

Inverse-volatility position sizing is a separate risk-management hypothesis and must be compared
out of sample with the unchanged base strategy; it is not evidence that an entry has directional
edge. Do not append I-49 to the claimed London-fix pilot or the frozen R-2026-004 primary gates.
Reconsider an executable filter only if a mechanically close, causal, cost-aware study on a
transferable market supplies the direction and threshold before local results are inspected.

