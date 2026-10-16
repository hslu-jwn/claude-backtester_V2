# Combining edges

How to put several weak signals, speeds or strategies into one book, and what filtering a signal with a
second model can and cannot do. Sources: RC = Carver *Systematic Trading*, LP = López de Prado
(chapter.section), KD = Davey, EC = Chan, K = Kaufman. Ideas: T-12 (forecast engine), T-18 (combination
report), I-50 (meta-labelling), I-51 (EWMAC + swap carry). None of our 5 strategies has a net edge, so
combining is a tool for later; **combining zero-edge parts gives zero-edge** (RC ch.8: weak edges add only
if their pre-cost Sharpe is positive).

## Why combine
- Sharpe grows with the square root of the number of independent bets; four uncorrelated assets double it, a
  half-dozen asset classes give 2-3× a single asset (RC ch.2, p.52). Diversifying over instruments is worth more
  than adding rules (correlation between rules on one instrument is higher than between instruments on one
  rule); trend + carry alone gave ~85 % of Carver's full system (RC ch.3).
- Equal blending beat picking: 90 variations of a rule on gold, picking last year's best by trailing 12-month
  Sharpe gave SR 0.07, a random variation each year 0.20, the equal blend of all 0.33 (RC ch.3).
- Davey: diversify by changing two or three of market, bar size, session, entry, exit; with diversification
  individual systems may be "decent" rather than "super" (KD ch.15). K p.1021-1026: all trend followers
  share one profit source.

## Carver's forecast framework (RC ch.7-11, App. B, D)
- A **forecast** is a continuous number proportional to the expected risk-adjusted return: scaled so the
  average absolute value is 10, capped at ±20 (extremes are rare, often mean-revert, or are just low vol).
  Binary signals are worse: near-zero forecasts earn less, binary costs more to trade.
- Make every rule volatility-standardised (divide by recent daily sigma in price units), recompute it every
  bar (no separate entry and exit rules), and fix the **forecast scalar** = 10 / average absolute raw forecast
  measured over many instruments without looking at performance.
- Several speeds per rule; choose variations by behaviour (speed, correlation, cost), never by performance.
  Drop a variation only at correlation > 95 %, or if too costly or too slow. Rule-of-thumb correlations: one
  rule's variations 0.7 (adjacent speeds 0.9), different rules of one style 0.5, different styles 0.25.
- **Combined forecast** = weighted average (weights positive, sum 100 %), then × **FDM** = 1/sqrt(w' H w) (H
  forecast correlation matrix, negative correlations floored at 0), cap again at 20, FDM capped at 2.5 (a high
  FDM makes capped forecasts the norm, i.e. effectively binary). Equal weights, identical correlation:
  N=2 gives 1.15 at corr 0.5, N=4 1.27, N=10 1.35, N=50+ 1.40 (RC Table 18, ch.8).
- **Position** = forecast × (daily cash vol target / instrument value volatility) / 10 per subsystem; then
  instrument weight × **IDM** (same formula on subsystem returns, cap 2.5; subsystem correlation is about
  0.7 × the instrument correlation; do not adjust instrument weights for Sharpe). Position inertia: trade only
  if the current position is > 10 % from the target (RC ch.11). Keep at least 4 blocks at forecast 20.
- **Handcrafting** (RC ch.4): group similar assets bottom-up; any two assets 50/50; three assets by the
  correlation pattern (e.g. 0.5 / 0 / 0.5 → 37/26/37; adjacent 0.9 speeds → 42/16/42); round correlations to 0,
  0.5, 0.9; weights multiply down the tree. Sharpe tilts only when the difference is certain (costs) or from > 10
  years of data, and small (multiplier 0.65-1.35 for ±0.5 SR). Bootstrapping random 10 % of the history
  100-200 times and averaging the optimal weights is the data-driven alternative; single-period optimisation
  gives extreme unstable weights (68/32/0 in the example; in-sample SR 0.84 turned 0.30 out of sample).
- Do not fit rules per instrument (narrative fallacy); pool instruments; compare rules only within the same
  skew (steady wins and a high hit rate usually hide negative skew).

## Hierarchical risk parity (LP 16)
- Problem: mean-variance optimisation inverts a noisy covariance matrix (Markowitz's curse) and loses to
  equal weights out of sample.
- HRP: (1) cluster on distance sqrt((1 - rho)/2); (2) reorder the covariance matrix by the dendrogram;
  (3) recursive bisection, splitting weight between the halves in inverse proportion to their variance (inverse
  variance inside each half). No matrix inversion, weights positive and sum to 1. Monte Carlo (10 assets, 520
  days): out-of-sample variance min-variance 0.1157, inverse variance 0.0928, HRP 0.0671 (LP 16.6).
- With only 2-4 strategies HRP, equal weight and inverse variance are nearly the same.

## Combining by daily results (Davey ch.15, 19)
- Merge the strategies' trades into **daily** results (same day netted), resample whole days, and compare
  median max drawdown, return, return/DD and P(profit year) with each alone: two euro systems 2.2 and 5.2 →
  6.7 combined, P(profit) 89 / 97 % → 98 % (KD p.136-138, 167-169).
- Check daily-return correlation over the whole history **and** in rolling 6-12 month windows (it spikes in
  crises); R² of the combined curve; if a new system correlates highly with a live one, halve both sizes.
- Chan: apply Kelly to each strategy separately so a failing strategy withers fast; a multi-strategy CPPI
  lets winners subsidise losers; momentum and mean-reversion books diversify each other (EC p.154, 182, 188).
- Concurrency: when several signals fire together, scale each by 1 / (number of concurrent positions) or
  budget size = concurrent / maximum concurrent (LP 4.3, 10.2); mainly a daily-loss tool for FTMO.

## Meta-labelling (LP 3.6-3.8, 8, 9.4)
- A primary rule gives the **side**; a secondary binary model decides whether to **take** the bet (label 1 if
  the triple-barrier outcome was a profit). Tune the primary for high recall, let the filter raise precision
  (higher F1); the predicted probability can size the bet (see [position-sizing-and-risk.md](position-sizing-and-risk.md)).
  Barriers may be asymmetric because the side is known.
- Claimed benefits: it limits overfitting (the model does not choose the side), long and short logic can be
  separated, any rule even a discretionary one can be wrapped (no numeric evidence given).
- **It only filters.** If the primary has negative expectancy overall the filter must find pockets of positive
  expectancy, which with a few hundred trades per symbol is easily a fluke. The secondary model can overfit its
  own features, so the same purged, time-blocked validation applies (LP 3.8, 7.4); count every feature tried.
- Rule-based version for us (no ML): 3-6 pre-registered features at the signal bar (volatility rank,
  position in the prior-day range, sign of recent serial correlation, weekday, minutes since the open, stop in
  ATR); bucket by quantile and compare mean R in train blocks vs held-out blocks (single-feature importance).
  Strategy 2's optional trend / 16:15 / cost filters already act as hand-made meta-labels (best −17 R).
- Score with F1 or a PnL-weighted measure, not accuracy (most meta-labels are 0, so "never trade" scores
  well); class weights balanced (LP 4.8, 9.4, 14.8).

## Our context
- Five symbols, strongly grouped: NAS100 / US500 correlate 0.75-0.9 (RC App. C: same country, similar
  industry 0.7-0.8), gold and the two FX pairs are moderate, so expect an IDM of only about 1.2-1.4.
- The five strategies are not forecasts yet; turning each signal into a ±20 number (distance / ATR) and
  testing whether the blend beats its best part is the T-12 / T-18 experiment. If each part is net negative
  the blend will be too.
- Swap enters as a cost of any held forecast; for FX it can earn (carry forecast) → I-51.

See also: [statistics-and-bayes.md](statistics-and-bayes.md), [trend-following.md](trend-following.md),
[position-sizing-and-risk.md](position-sizing-and-risk.md), [costs-and-execution.md](costs-and-execution.md).
