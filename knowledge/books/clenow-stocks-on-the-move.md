# Andreas F. Clenow, *Stocks on the Move* (2015)

Short: **SOTM**. Read 2026-11-18 by Codex.

**Citation limitation:** The supplied text contains chapter headings and form feeds, but no identifiable printed page numbers or table of contents. The title and copyright pages also do not identify a publisher. I therefore use section and figure references below rather than inventing `SOTM p.N` citations; the PDF’s presence in the Tier 3 library was not verified.

The book presents a long-only US equity momentum portfolio: rank stocks by the strength and smoothness of their recent advance, size positions by volatility, and use stock and index trend filters. It reports a historical portfolio simulation, examines variations in the rules, and discusses the data needed to reproduce it. Its main strategy belongs to a family the project has already judged. (SOTM, “The Exact Trading Rules”; “Momentum Strategy Performance”; “Simulating the Strategy”)

## Testable ideas

- **Ranked equity momentum portfolio** (SOTM, “The Exact Trading Rules”; “Momentum Strategy Performance”; “The Rational Behind Momentum Investing”): On Wednesdays, rank point-in-time S&P 500 constituents by the annualized exponential regression slope of the past 90 trading days multiplied by its R². Buy eligible highest-ranked stocks until cash is exhausted, provided the index is above its 200-day moving average. Exclude stocks below their 100-day average or with a move over 15% in the past 90 days. At the weekly review, sell holdings outside the top 20%, below their 100-day average, with an excessive gap, or no longer in the index. Size each position as account value × 0.001 / ATR20 and review sizes every second Wednesday. Holding periods vary.

  The author discusses investor feedback and underreaction to information as possible explanations; neither establishes a counterparty required to trade. For the 16-year simulation, the book states **over 12% annualized** versus **5% per year** for the equity market, with maximum drawdowns of **24%** and **55%**, respectively. These are portfolio results, not bp per event or day. Required data: daily stock and index prices, point-in-time membership, delistings and dividends. Our venue: real US shares. **MAPS TO: diversified or single-symbol trend following at any speed.**

## Method notes

- Use point-in-time index constituents and include delisted stocks; testing historic periods on today’s survivors biases results. Account for cash dividends through total-return adjustments or explicit cash flows. (SOTM, “Survivors”; “Simulating the Strategy”)
- Simulate the portfolio’s actual cash constraints, position sizes and rebalances rather than evaluating selected stocks independently. The book’s ATR sizing targets a daily move of 10 basis points per position; that is a risk-sizing input, not an estimated return. (SOTM, “The Exact Trading Rules”; “Simulating the Strategy”)
- The book calculates indicators from daily data even though its portfolio decisions occur weekly. It describes calculating analytics at day-end before taking action; a reproduction needs an executable fill assumption consistent with that timing. (SOTM, “The Exact Trading Rules”; “Structuring the Simulation”)
- Check sensitivity across plausible parameters rather than selecting a precise historical optimum. The author compares regression windows of 60, 90, 120 and 240 days and reports broadly similar behavior, though the extracted comparison table supplies no readable figures. (SOTM, “How important is Momentum Period?”)
- Compare against a dividend-consistent benchmark and account for commissions. The book explicitly warns that comparing dividend-adjusted stock results with a price-only index and omitting commissions can exaggerate apparent performance; that warning appears in its discussion of an earlier illustrative test, so it does not by itself establish the cost treatment of the core result. (SOTM, discussion following the earlier simulation; “Divide and Conquer”)
- Examine drawdown and periods of weak performance as well as annualized return. The author’s filter comparison attributes much of its historical benefit to two major bear-market periods, a limited sample for judging that protection. (SOTM, “Momentum Strategy Performance”; “How important is the Trend Filter?”)

## Verdict

**No NEW idea merits a card from this text under the brief.** The central result is an already-judged equity trend/momentum portfolio. It has a stated portfolio-level historical return, but the proposed explanations do not identify a counterparty that must trade, and the book does not state a return in bp per event or day. The point-in-time data and portfolio-simulation cautions are useful method notes.

