# Cross-market intraday lead–lag candidate scan

Date: 2026-10-29  
Decision: **no M1 CFD candidate; documented exploitable lags are sub-second, while slower results
mainly measure spot-index staleness and price discovery**.

## Candidate boundary

The screened idea was to use a fully observed return in one liquid market to predict a subsequent
return in another supported instrument. A valid design would require synchronized causal clocks,
a lag comfortably exceeding M1 entry latency, distinct tradable legs, and net profitability after
the lagging instrument's spread. Volatility transmission without signed return prediction did not
qualify.

## Primary evidence

- Hans R. Stoll and Robert E. Whaley, “The Dynamics of Stock Index and Stock Index Futures
  Returns,” *Journal of Financial and Quantitative Analysis* 25(4), 1990,
  [abstract opened](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/dynamics-of-stock-index-and-stock-index-futures-returns/6C0C02141F02160D48AB9CA1FDFB2785).
  Five-minute S&P 500 and Major Market Index futures returns lead their cash indexes by roughly five
  minutes and sometimes longer. The relationship is largely futures-versus-stale cash price
  discovery for the **same underlying**, not one independently tradable futures contract predicting
  another.

- Nicolas Huth and Frédéric Abergel, “High Frequency Lead/Lag Relationships—Empirical Facts,”
  *Journal of Empirical Finance* 26, 2014, 41–58,
  [DOI/abstract opened](https://doi.org/10.1016/j.jempfin.2014.01.003). Tick data show liquid assets
  lead less-liquid stocks and forecast the next midquote move with about 60% accuracy, but the paper
  explicitly finds that a naïve market-order strategy cannot profit after the bid/ask spread.

- Hamad Alsayed and Frank McGroarty, “Ultra High Frequency Statistical Arbitrage across
  International Index Futures,” 2013,
  [full working paper opened](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID2225753_code1490771.pdf?abstractid=2225753&mirid=1&type=2).
  S&P 500, FTSE 100, and DAX futures exhibit opportunities lasting a few hundred milliseconds; the
  most profitable ones rarely persist beyond 300 ms and are slippage-sensitive. That is far below
  M1 bar and retail-CFD latency.

- Nuria Alemany, Vicent Aragó, and Enrique Salvador, “Lead-Lag Relationship between Spot and
  Futures Stock Indexes: Intraday Data and Regime-Switching Models,” *International Review of
  Economics & Finance* 68, 2020, 269–280,
  [DOI/abstract opened](https://doi.org/10.1016/j.iref.2020.03.009). Five-minute DAX spot/futures
  data from 2014–2015 show regime-dependent futures price discovery when arbitrage bounds change.
  The study models equilibrium adjustment; it does not establish a net standalone strategy after
  causal signal formation and execution.

## Why this does not transfer

1. **The older lag is partly measurement.** A calculated cash index updates as constituents trade;
   futures incorporate information continuously. A broker's US500 and NAS100 quotes are not a
   tradable cash-index/futures arbitrage pair and can share the same upstream pricing latency.
2. **Modern economic lags are too short.** Hundreds of milliseconds expire before an M1 signal can
   be formed, submitted, and filled. Using the signal-bar close as an earlier fill is lookahead.
3. **Spread consumes naïve predictability.** The strongest tick-level peer-reviewed evidence states
   that market orders do not profit after bid/ask cost.
4. **Pair and lag selection would be a large grid.** Trying every supported leader, lagger, sign,
   minute lag, session, and volatility regime would manufacture multiplicity without a source-
   matched primary pair.
5. **Volatility spillover is not direction.** Cross-market variance transmission may aid risk
   forecasts but cannot promote an entry rule.

## Decision

Do not create a cross-market M1 strategy, Granger-causality mining study, or pair/lag grid. The
territory belongs to execution/market-microstructure research requiring synchronized tick quotes,
venue-specific bid/ask data, and sub-second infrastructure.

Reconsider only with independent evidence for a predefined pair of actually supported tradable
instruments, a directional lag longer than the platform's causal latency, an untouched modern
sample, and net results using executable quotes. Statistical price discovery alone is insufficient.
