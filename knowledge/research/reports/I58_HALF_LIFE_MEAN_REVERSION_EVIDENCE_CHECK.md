# I-58 half-life/z-score mean-reversion evidence check

Date: 2026-10-29  
Decision: **park; do not create a research family or strategy draft**.

## Question

Does independent evidence support the frozen backlog's I-58 rule: estimate a half-life from recent
prices, trade a single FX/gold/index instrument against its rolling mean or Bollinger z-score on
M15-H4, and close intraday?

The bounded search required a mechanically close, cost-aware study on a single raw asset price.
Evidence for market-neutral residuals or pairs was treated as adjacent rather than transferable.

## Primary and methodological evidence inspected

### Directly adverse intraday FX evidence

- Christopher J. Neely and Paul A. Weller, “Intraday technical trading in the foreign exchange
  market,” *Journal of International Money and Finance* 22(2), 2003, 223–237,
  [DOI](https://doi.org/10.1016/S0261-5606(02)00101-8). **Full paper opened.** It evaluates
  half-hourly intraday rules out of sample on four dollar exchange rates. The rule search includes
  normalized exchange-rate/moving-average inputs. Predictability exists at zero cost, but realistic
  costs and active trading-hour restrictions remove excess profitability. This is broader than the
  exact I-58 z-score rule, but it is directly adverse to the same single-FX, price-history,
  intraday-cost premise.

- Michael Frömmel and Kevin Lampaert, “Does frequency matter for intraday technical trading?”,
  *Finance Research Letters* 18, 2016, 177–183,
  [DOI](https://doi.org/10.1016/j.frl.2016.04.014). **Full paper opened.** It tests more than 8,000
  technical rules on 10-, 15-, 30-, and 60-minute RUB/USD data from 2000 through June 2011 using
  observed time-varying spreads and data-snooping-aware inference. Real costs erase most apparent
  profit; the surviving exception is tied to a stabilizing central-bank regime. It does not
  establish a general V2-symbol z-score edge.

### Mean reversion that does not transfer to I-58

- Marco Avellaneda and Jeong-Hyun Lee, “Statistical Arbitrage in the U.S. Equities Market,”
  *Quantitative Finance* 10(7), 2010, 761–782,
  [working-paper PDF opened](https://jeremywhittaker.com/wp-content/uploads/2021/03/AvellanedaLeeStatArb071108.pdf).
  The paper estimates mean reversion in **market-neutral PCA or sector-ETF residuals**, not raw
  asset prices. It explicitly contrasts its residual approach with price-level mean reversion.
  After-cost results decay after 2002, and 2007 contains a sudden liquidity-unwind drawdown. This
  supports careful residual construction and regime risk, not I-58's unhedged single-asset rule.

- Vladimír Holý and Petra Tomanová, “Estimation of Ornstein-Uhlenbeck Process Using
  Ultra-High-Frequency Data with Application to Intraday Pairs Trading Strategy,” 2018 manuscript,
  revised 2026, [arXiv](https://arxiv.org/abs/1811.09312). **Full manuscript opened.** Its empirical
  application trades 21 pairs among seven oil-company stocks, estimates a stationary spread, and
  closes intraday. The paper shows that ignoring microstructure noise biases mean-reversion
  estimates, that performance is sensitive to thresholds and time variation, and that pairs
  strategies are sensitive to costs, execution speed, formation length, news, and parameter
  drift. Again, the stationary object is a spread, not a raw price.

### Estimation objections

- Jun Yu, “Bias in the estimation of the mean reversion parameter in continuous time models,”
  *Journal of Econometrics* 169(1), 2012, 114–122,
  [DOI](https://doi.org/10.1016/j.jeconom.2012.01.004). **Publisher abstract and extended preview
  opened; full paper not opened.** Standard least-squares/maximum-likelihood estimates of an OU
  mean-reversion parameter are biased; the problem is material near a unit root, an empirically
  realistic case for financial time series. A rolling plug-in half-life is therefore not a stable
  mechanical horizon without bias correction and uncertainty reporting.

- Giuseppe Pernagallo, “Random walks, Hurst exponent, and market efficiency,” *Quality &
  Quantity* 59, 2025, 1097–1119,
  [DOI](https://doi.org/10.1007/s11135-025-02052-7). **Full open-access article opened.** Simulations
  show that estimated Hurst values different from 0.5 can be compatible with random walks; results
  vary with estimator and sample. Thus an estimated `H < 0.5` is not evidence that an executable
  contrarian rule has positive expected return.

## Why the proposed rule is not identified

1. **A raw price is not a demonstrated stationary spread.** The supportive literature first
   removes common factors or constructs a pair. Applying an OU half-life directly to one rolling
   price deviation assumes the conclusion that needs proof.
2. **Rolling normalization creates apparent re-centering mechanically.** Subtracting a moving
   average and dividing by a rolling standard deviation yields a bounded-looking signal even when
   the underlying price follows a random walk. Signal re-centering is not executable return.
3. **The half-life is an unstable estimated parameter.** Near-unit-root bias, sampling error, and
   time-varying dynamics can turn a small coefficient error into a very different horizon.
4. **High-frequency noise mimics reversion.** Bid/ask bounce, discreteness, and quote noise create
   negative short-lag dependence. OHLC bars do not provide the noise-robust transaction/quote model
   used by the strongest estimation paper.
5. **Costs attack the exact proposed frequency.** Two independent intraday FX studies find
   zero-cost or occasional predictability that generally disappears under realistic or observed
   costs.
6. **The local evidence is exploratory and gross.** The backlog cites USD/CAD and GLD/USO examples
   with in-sample half-life selection, gross returns, and a large drawdown. Those examples do not
   provide an independent preregistration anchor for V2 instruments.
7. **The rule surface is large.** Asset, timeframe, estimator, lookback, half-life mapping, entry
   z-score, exit z-score, stop, intraday cutoff, and Hurst gate all create trials. A broad search
   would repeat the same-data rescue pattern already prohibited for failed mean-reversion families.

## Decision and reopening condition

Keep I-58 parked. Do not use Hurst or an estimated half-life as a gate that promotes the idea, and
do not append a z-score filter to a failed strategy.

Reconsider only if independent evidence supplies all of the following before V2 data access:

- the same single-asset intraday construction, rather than a pair or hedged residual;
- causal rolling estimation with parameter uncertainty and a fixed fallback for near-unit-root or
  invalid estimates;
- bid/ask-aware or otherwise realistic net results on a transferable liquid market;
- a frozen, small parameter set and day-flat exit;
- evidence that the z-score signal predicts executable future return, not merely that the rolling
  signal later crosses zero; and
- out-of-sample stability outside a special intervention regime.

No qualifying primary study was found in this bounded check.

