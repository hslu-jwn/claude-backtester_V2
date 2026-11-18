# Andreas F. Clenow, *Following the Trend: Diversified Managed Futures Trading*, second edition (Wiley, 2023)

Short: **FTT**. Read 2026-11-18 by Codex; the brief identifies the PDF as being in the library folder Tier 3.

The book builds and analyzes demonstration portfolios of diversified futures trend-following strategies, then explores counter-trend trading and futures term structure. It also discusses futures data, portfolio construction, execution and backtest pitfalls. Its models are presented as teaching examples, not ready-to-trade systems.

**Citation limitation:** the supplied text has chapter headings but no identifiable printed page numbers. The references below use chapters and sections; they cannot satisfy the requested `FTT p.N` format without a paginated copy.

## Testable ideas

- **Futures term-structure slope** (FTT ch. 8, “Using Term Structure for Trading”): Each week, calculate annualized implied carry along each market’s futures curve and identify its steepest point. Go long backwardated markets at a slope of at least **7.5%** annualized and short contango markets at at least **15%**; hold until the next week. Positions are equal-sized, targeting **200%** gross portfolio exposure. The stated universe is broad, across asset classes. The proposed mechanism is convergence toward the underlying as expiry approaches, conditional on other prices staying unchanged; the book cautions that convergence does not determine the actual direction of returns. **Realized size:** no numerical return in bp per event or day is given for the model. A soybean curve snapshot implies **−1.52% over 61 days**, or **−8.75% annualized**, but that is a theoretical carry calculation, not an observed strategy return. The model’s performance is shown in a chart with slippage and commissions, without a numerical sample result stated in the inspected text. It needs historical individual-contract prices, expiries, liquidity and execution costs; our venue would be exchange futures. **NEW**, distinct from the judged commodity-index-roll front-running family. The precise tradeable contract and a liquidity rule need clarification before implementation. The text also says “once a month” in a later explanatory paragraph, conflicting with the weekly rules above.

- **Bull-market futures pullback** (FTT ch. 7, “Building a Counter-Trend Model” and “Counter-Trend Performance”): A long-only dip-buying model uses a 40-day EMA above an 80-day EMA as its bull-market filter, buys a pullback from the preceding 20-day highest close, and exits if the trend turns bearish or after 20 trading days. The narrative describes buying near where longer-term trend followers stop out, but does not establish their forced trading as evidence. The book reports **19.7% annualized return**, **−43.0% maximum drawdown**, and **0.83 Sharpe** in its counter-trend table; it describes a **20-year** comparison, includes trading costs and excludes management and performance fees. It gives **no bp-per-trade or per-day size**. Daily futures prices and realistic futures costs would be needed. **MAPS TO: daily reversal.** The rule is internally unclear: the chapter alternates between a 40-day standard deviation and ATR for the pullback, and refers to both a three-ATR threshold and a chart using 20-day ATR. It should not be implemented without clarification.

## Method notes

- Use individual futures contracts in a backtest and construct continuations as needed; a pre-calculated continuation alone may be less realistic. The book’s analyses used Norgate data with Python and Zipline (FTT ch. 11, “Sourcing Your Data”).
- Check data for unexpected spikes and cross-check sources where possible (FTT ch. 11, “Sourcing Your Data”).
- Account for liquidity and execution in deferred contracts: the book warns that spreads can be wide and market orders inadvisable (FTT ch. 8, “Limitations of Term Structure Models”).
- Treat repeated adjustments after inspecting results as a source of curve fitting; an impressive historical backtest need not predict future performance (FTT ch. 11, “The Dangers of Backtesting”).
- Consider diversification across strategy styles as well as markets, while recognizing that correlations change over time (FTT ch. 7, “Counter-Trend Performance”).

## Verdict

The **NEW futures term-structure model** is worth a research lead, but not yet a card meeting the requested evidence standard: the book gives a convergence mechanism and a theoretical curve-implied yield, not a measured bp-per-event or bp-per-day effect, and its trading frequency is contradictory. The pullback model maps to an already judged family and also has ambiguous entry calculations.

