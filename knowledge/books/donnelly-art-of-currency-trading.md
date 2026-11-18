# Brent Donnelly, *The Art of Currency Trading* (Wiley 2019)

Short: **AC**. Cite by chapter and section (`AC ch.4 › 4:00PM WMR Benchmark Fix`); the extraction has no reliable
printed pages (part 3 uses index pages). Read 2026-11-18 by Codex (gpt-6.1-terra medium, read-only, 3 parts,
`knowledge/reading-brief.md`); PDF in the library folder Tier 1. Discretionary bank-trader book: market structure, who
must trade and when (corporates, real money, benchmark fixes, option expiry), positioning, news, risk. Evidence is
selected examples, no costed tests. Opus checked the ideas against the ledger: month-end WMR hedge flow (H12
falsified), London fix reversal (S08 rejected), Gotobi / Tokyo (H11 tested), oil -> CAD (L15 screen fail), macro-release
continuation (FB186 rejected), central-bank continuation (FB190 rejected), gap fade (strategy 5) are all spent; the one
new item is I-120 (COT positioning turn), PARKED on power. Open fact: the book gives the Tokyo fix as both 8:55 and
9:55 Tokyo (the official time is 9:55 JST; H11 used 09:55).

# Part 1: ch.1-6, FX basics, market structure, fundamentals, technical analysis I

### Overview

Donnelly presents FX trading as a discretionary combination of macroeconomics, market structure, positioning, technical analysis and risk management. His strongest contribution for this project is the description of **who must transact, when, and why**: corporate conversions, portfolio hedges, benchmark fixings and option hedging can create concentrated flows.

He regards charts mainly as tools for timing and risk management, and is skeptical that familiar technical patterns work reliably as standalone signals. Much of the evidence in these chapters consists of market observations and selected historical examples, not costed, out-of-sample tests.

**Source-location limitation:** The supplied extraction contains form-feed breaks but no reliable printed book page numbers. I therefore cite chapter, section and text-file line numbers rather than inventing `AC p.` references. Line numbers are approximate locations in the supplied file. The assignment ends at line 4846; later chapters on positioning and news were not read.

The current handoff confirms the supplied context, including the two surviving streams and the pause on new goal-1 CFD signal screens. The reference to “the 4 failed strategies” is not identified in the assignment, so the comparisons below use the described failed *families* rather than claiming a comparison to four named strategies.

### Chapter notes

### Ch 1 — Introduction: This Book Will Make You a Better Trader

- The author advocates combining fundamentals, technicals, market psychology, positioning and risk management rather than relying on a single school of analysis.
- A setup supported by several independent lines of reasoning is, in his view, preferable to a chart pattern considered alone. This is a practitioner’s assertion, not a measured probability in this chapter.
- Discipline and adaptation matter because a sound decision can lose and a poor decision can win on an individual trade.
- His 2016 US election account illustrates how a large initial market reaction can reverse when participants reassess the implications. It is a selected episode, not evidence that election reactions generally reverse.  
  **Source:** AC ch. 1, Introduction, lines 680–960.

### Ch 2 — A Very Brief History of FX

- The author traces the shift from gold-backed and fixed exchange-rate systems to predominantly floating major currencies after the breakdown of Bretton Woods.
- He describes coordinated intervention episodes, including the Plaza and Louvre accords, as reminders that exchange rates are not always left entirely to private market forces.
- Trading evolved from telex and direct dealing toward electronic platforms and algorithmic execution; the mechanics and competitors of one period need not persist into another.
- Historical changes in market structure make old chart-based results particularly uncertain as forecasts of present execution opportunities.  
  **Source:** AC ch. 2, “A Very Brief History of Currency Markets” and “A Short History of Currency Trading,” lines approximately 980–1220.

### Ch 3 — Currency Trading Basics

- An FX position is simultaneously long one currency and short another. P&L is initially denominated in the quote currency and may require conversion into the account currency.
- The author recommends liquid pairs for short-term trading because spread consumes a larger fraction of the attainable move in less liquid pairs. Crosses can inherit liquidity and volatility from their component legs.
- Spot FX is decentralized: interbank platforms, banks and retail providers form a connected market rather than a single order book. A broker’s price and spread are consequently important to realized results.
- Marketable orders provide immediacy at a cost; limit orders may improve the execution price but can miss the trade. A candle touching a limit price is not proof that a real limit order would have filled.
- A stop becomes an execution order after its trigger; its fill price is not guaranteed. The author cites ordinary major-pair stop slippage of roughly 1–3 pips in his experience, while warning that fast markets can be much worse.
- Large orders may be split over time using TWAP or VWAP, reducing immediate footprint but exposing the participant to price movement while execution is incomplete.
- Overnight positions earn or pay rollover based on the two currencies and market forward pricing. Weekend and holiday settlement can generate multiple days of roll. Actual FTMO swap schedules and charges must govern a CFD test.
- His historical roll convention is generally 5 p.m. New York, with a different convention described for NZD; this is a market-mechanics discussion, not a guarantee of the broker’s swap cutoff.  
  **Source:** AC ch. 3, “Quotes, Spreads, Market Structure, and Order Types,” “Understand Profit and Loss,” and “Understand the Roll,” lines approximately 1220–1950.

### Ch 4 — Understand Market Structure

- Corporations must convert foreign revenues and fund cross-border purchases; real-money investors convert or hedge foreign assets. Their timing and motives can differ from those of directional speculators.
- Banks intermediate client flow and take inventory risk; funds, central banks, systematic traders and retail participants have different horizons and objectives.
- Central banks influence FX through rates, communication, intervention and reserve management. Reserve diversification can induce trading in currencies other than the currency directly involved in an intervention.
- Currency relationships are conditional. The author groups commodity exporters and safe havens but cautions that correlations change and that a cross may be dominated by its more volatile leg.
- In his 500-day example through January 2017, AUDCAD correlated 61.8% with AUDUSD and 17.5% with USDCAD; CADMXN correlated 76.0% with USDMXN and −10.2% with USDCAD. These are historical examples, not stable coefficients.
- Carry can attract crowded positions during calm markets and unwind abruptly. The author cites AUDJPY falling from about 107 to 86 in roughly a month in 2007 and subsequently reaching about 60 in 2008.
- London–New York overlap concentrates liquidity and activity. His historical charts show spikes around US releases, option expiry and the London benchmark fix; activity is not equivalent to predictable net returns.
- He identifies the London open as 7 a.m. London and the New York open as approximately 7 a.m. New York, with the latter sometimes extending a London move before reversing.
- The 4 p.m. London WMR fixing window is described as 3:57:30–4:02:30 London. Benchmark users can create large imbalances; the final business day of the month is described as especially large because funds rebalance FX exposures after asset-price changes.
- The author says fix-related moves sometimes reverse after pressure ends, **but explicitly rejects automatically fading every large fixing move**.
- The text conflicts on the Tokyo fix: its heading and first explanation say **8:55 a.m. Tokyo**, while the accompanying chart discussion says **9:55 a.m. Tokyo**. Resolve this against an authoritative fixing specification before defining a trading rule.
- Other cited activity points include 10 a.m. New York option expiry, the historical Bank of Canada noon rate, and 3 p.m. New York futures-related marking. Conventions and usage may change.
- The 5–6 p.m. New York period is described as especially thin. Weekend opens and scheduled news can gap through stops.
- One Australian employment example moved AUDUSD 72 pips, approximately 1%, after an expected −10,000 jobs versus an actual +78,000. The author also cites research attributing 25%–40% of FX returns over 1–3 months to jumps; this is a cited research claim, not his own test.
- His personal intraday P&L review found profits concentrated from 7–11 a.m. New York, with 20%–40% of those gains given back from 11 a.m.–5 p.m. This is one trader’s experience.  
  **Source:** AC ch. 4, “The Players,” “Understand Volatility and Liquidity,” “Understand Time of Day,” and “Understand Jump Risk,” lines approximately 1980–2820.

### Ch 5 — Understand Fundamental Analysis

- Purchasing-power parity may describe very long-run valuation but can remain far from spot for years; it is a poor short-term timing rule in the author’s view.
- Global growth, commodities, risk appetite and geopolitics can dominate local fundamentals. Domestic monetary policy, relative yields, capital flows and trade balances also matter, with their importance varying by regime.
- Changes relative to expectations matter more for a release reaction than whether the published level looks objectively strong or weak. Central-bank reaction functions can change whether inflation news helps or hurts a currency.
- The author suggests comparing yields across countries and maturities, not just looking at one country’s rates in isolation. The available FRED US yield series alone cannot reproduce a full bilateral yield differential.
- Reserve intervention can generate secondary diversification trades. His example: if reserves fall by $1 trillion and a manager maintains a 20% euro allocation, a large euro sale could be needed. Actual allocations, timing and intervention flows are not observable from the price data alone.
- Event importance changes over time. He emphasizes the timeliness, relevance and reliability of each release and the difference between the published number and the pre-release consensus.
- For 2010–2018, he reports an average absolute US payroll miss of 72,200, a miss standard deviation of 83,600, and an average five-minute USDJPY range of 66 pips. These are descriptive historical figures, not a net trading return.
- The author reports average misses of 0.35 percentage points for advance US GDP versus 0.10 for final GDP, illustrating why the first release can matter more.
- Headline, components and revisions can point in different directions. Durable-goods headlines, for example, can be distorted by large transportation orders.
- Historical consensus forecasts, original releases, revisions and precise publication timestamps are required to reproduce surprise-based tests without hindsight; the supplied project data list does not establish that these are available.  
  **Source:** AC ch. 5, “Domestic Drivers,” “Understand Intervention and Reserve Recycling,” and “Understand US Economic Data Releases,” lines approximately 2860–3900.

### Ch 6 — Understand Technical Analysis I

- Donnelly treats technical analysis as an execution and risk tool, not a sufficient reason to initiate a trade. He warns against finding attractive patterns after looking at outcomes.
- He summarizes a review of 92 modern studies: 58 positive, 24 negative and 10 mixed. He also highlights data snooping, selection of rules after the fact, risk estimation and transaction costs as obstacles to interpreting the literature.
- He describes support and resistance through resting orders, shared trader attention, option hedging and round-number preferences. These are plausible mechanisms; price data alone do not establish which one caused a particular bounce.
- For short-term charts he uses 20-, 55-, 100- and 200-period moving averages on 10-minute or hourly bars, favoring the 55-hour and 200-hour measures. He cautions against selecting the historical optimum.
- Moving-average and parabolic-SAR methods can follow trends but suffer repeated reversals in ranges. Several indicators calculated from the same prices do not provide independent confirmations.
- RSI levels of 30 and 70 are presented as conventional oversold and overbought thresholds; he discusses waiting for RSI to return across the threshold rather than immediately fading the first extreme.
- Candles such as dojis and hammers can indicate indecision or rejection in his interpretation, especially after a sustained move. His examples are illustrative and do not define quantitative wick, body or trend thresholds.
- Range boundaries are difficult to identify in real time; apparent breaks can fail, and by the time a range is obvious it may be near its end.
- For a flag breakout, he illustrates buying after a daily close above the flag, placing a stop below its bottom, and projecting a target using the prior flagpole length. Elsewhere he gives approximately 1.5 times average daily range as a general breakout stop; these are alternatives, not a single unambiguous combined rule.
- Technical levels should be chosen before the trade, with room for noise; a stop that is too close can turn an otherwise correct view into repeated losses.
- A take-profit level should reflect the market and the thesis, in his opinion, rather than being selected solely to produce a desired reward-to-risk ratio.  
  **Source:** AC ch. 6, “Technical Analysis: Does It Work?”, “Basic Indicators,” “Identify the Regime,” and “Reversal Patterns,” lines approximately 3900–4846.

### Topic tags

- **Trend:** The author favors trading pullbacks within a fundamentally supported trend, while acknowledging that trend indicators whipsaw in ranges. MA examples include 55 and 200 hours. AC ch. 6, “Basic Indicators” and “Identify the Regime.”
- **Breakout:** Flags, pennants and triangles are presented as continuation patterns, with a daily flag example using a close above the formation and a stop below it. Selected charts do not establish an edge. AC ch. 6, “Identify the Regime.”
- **Mean-reversion:** A fixing-related move can reverse after flow subsides, but the author rejects unconditional fading; range extremes and oscillator signals are also discussed with discretion. AC chs. 4 and 6.
- **Momentum/oscillators:** RSI 30/70, MACD divergence and SAR are aids to timing; indicators derived from the same price history are partly redundant. AC ch. 6, “Measuring momentum.”
- **Patterns:** Dojis, hammers and repeated tops or bottoms may focus attention, but visual definitions and examples are susceptible to confirmation bias. AC ch. 6, “Candlestick charts” and “Reversal Patterns.”
- **Intraday/sessions:** London and New York overlaps, data releases, option expiry and benchmark fixes concentrate activity; thin periods worsen execution and can magnify individual flows. AC ch. 4, “Understand Time of Day.”
- **Seasonality/time:** Month-end WMR is described as especially large because funds rebalance hedges. No distinct quarter-end rule or measured quarter-end result is specified in the assigned portion. AC ch. 4, “4:00PM WMR Benchmark Fix.”
- **Volatility:** Both liquidity and volatility vary by regime and hour. Quiet historical volatility can produce dangerously large risk allocations before a jump. AC ch. 4, “Understand Volatility and Liquidity.”
- **Stops-and-exits:** Stops can gap; wide enough placement must be balanced against position size. Market structure should inform targets, and orders may fail or slip. AC chs. 3, 4 and 6.
- **Position-sizing/risk:** Normalize exposure for volatility and recognize cross-pair dependence. Historical volatility alone understates sudden regime changes and tail risk. AC ch. 4.
- **Testing-and-robustness/overfitting:** Technical-rule selection, repeated optimization, hindsight pattern identification and inadequate cost estimates undermine historical results. AC ch. 6, “Technical Analysis: Does It Work?”
- **Costs/execution:** Spread, stop slippage, missed limits and overnight roll materially affect results, particularly around events and illiquid periods. AC ch. 3 and ch. 4.
- **Psychology/discipline:** Predefined plans reduce reactive trading; a good process can lose on an individual trade. The author warns of overtrading during quiet hours. AC chs. 1, 4 and 6.
- **Portfolio/diversification:** A basket can express a USD view while reducing exposure to a single counterpart currency, although the basket still shares USD and global-risk exposure. AC ch. 4, “A Note on Choosing Currencies.”

### Testable ideas

The following are **research candidates, not complete trading specifications**. Where the book omits an entry threshold, exit, stop or holding period, those fields remain open; they must be preregistered rather than inferred from the examples. None has demonstrated profitability in this book section. The starred items have the clearest fit with the project’s mechanism-first research, subject to the current pause on new CFD screens.

### ★ Month-end equity-hedge rebalancing into WMR

**Rule:** On the final relevant business day of each month, estimate the direction of required FX hedge rebalancing from observable prior equity returns and an explicitly specified hedge convention. Measure the corresponding FX move into the 4 p.m. London fix, then separately measure post-fix returns. Entry time, proxy, threshold, exit and stop are **not specified by the author**.

**Source and evidence:** AC ch. 4, “4:00PM WMR Benchmark Fix,” approximately lines 2480–2540. He reports large month-end flow and pre-positioning, but gives no costed strategy result or universal direction.

**Fit:** Good for M1 timing and available US equity prices; the proxy is incomplete without foreign asset returns, investor domicile, hedge ratios and actual flow. Model local London time, holidays, fixing-window spreads and slippage; a same-day trade has no overnight swap. Unlike generic intraday breakouts, this begins with a potentially compulsory portfolio rebalance. The sign must follow the chosen hedge model, not be guessed.

### ★ Fixing-pressure exhaustion after a large WMR move

**Rule:** Measure the signed move into or through the 3:57:30–4:02:30 p.m. London fixing window. Once the window has ended, evaluate a reversal **only when an independently defined prior directional reason is present**, as the author requires. The magnitude threshold, prior signal, entry, exit and stop are unspecified.

**Source and evidence:** AC ch. 4, “4:00PM WMR Benchmark Fix.” Rebounds are described as observations; he explicitly warns against fading every large move.

**Fit:** Good timestamp coverage, but potentially poor net economics because spreads and slippage can peak around the event. M1 bars cannot represent the half-minute boundary exactly; use only fully closed bars after 4:02:30. Usually intraday, so no swap if closed before the broker cutoff. It differs from a generic reversal candle by conditioning on a benchmark-flow mechanism and a separately established view.

### ★ Tokyo corporate fixing activity

**Rule:** Around the verified Tokyo fixing time, measure USDJPY and related yen-cross returns before and after the fix; distinguish directional continuation from reversal. The author specifies neither a directional signal nor an entry, exit or stop.

**Source and evidence:** AC ch. 4, “Tokyo Fix,” approximately lines 2560–2610. He attributes an activity spike to Japanese corporate and institutional benchmarking, without reporting a profitable rule.

**Fit:** Good for existing M1 yen pairs and intraday costs. **Blocked as a precise rule until the book’s 8:55 versus 9:55 Tokyo contradiction is resolved.** Use the `Asia/Tokyo` zone and actual broker spreads; same-day positions need no swap if closed before cutoff. Unlike a generic session breakout, the proposed event is a specific benchmark with identifiable users.

### ★ Relative US equity performance as a month-end flow proxy

**Rule:** Before the final-business-day London fix, compute an equity-return differential between the foreign assets held and the investor’s home assets; map it to hedge demand under a stated constant-hedge-ratio model. Test the resulting signed FX move over a prespecified pre-fix interval and the following interval. Proxy universe, mapping, thresholds and execution rules remain open.

**Source and evidence:** AC ch. 4, “4:00PM WMR Benchmark Fix.” The author specifically highlights large stock and bond moves, particularly US equities, as causes of rebalancing; he supplies no formula or backtest.

**Fit:** Potentially good if suitable point-in-time equity benchmarks are available; US stocks alone do not identify all bilateral hedge flows. A daily-bar signal must use only prices actually known before the London fix, so the same day’s US close is unavailable. Model spreads and same-day execution. This is a directional flow forecast rather than a price-only month-end pattern.

### ★ Option-expiry activity around 10 a.m. New York

**Rule:** Compare FX volatility, spread and subsequent returns around 10 a.m. New York with matched non-event minutes. A directional trade would additionally require a prespecified option-strike or dealer-position signal; the book gives none. Entry, exit and stop are unspecified.

**Source and evidence:** AC ch. 4, “Option Expiry,” approximately lines 2460–2480. The author attributes activity to changing option hedges and expiry, but presents no direction or returns.

**Fit:** M1 candles can test timing and cost, but absent option strikes, expiries and exposures, they cannot establish a hedging direction. An intraday design avoids swap. This differs from a generic clock-time strategy because the proposed cause is expiry-related hedging, though the relevant flow is unobserved.

### News-surprise response and reversal

**Rule:** For a specified release, calculate actual minus contemporaneous consensus, scaled by a standard deviation estimated using prior releases only. Test a prespecified post-release holding period, including a continuation and a separately registered reversal hypothesis. The author provides no entry delay, surprise threshold, exit or stop in this section.

**Source and evidence:** AC ch. 5, “Understand US Economic Data Releases”; historical payroll surprise and five-minute-range statistics above. Those statistics do not show tradable profits.

**Fit:** M1 price data are available, but point-in-time consensus, original releases and precise timestamps are not established in the project context. News spreads, jumps and slippage are material; minute bars cannot establish realistic instantaneous fills. Intraday exits avoid swap. Unlike a price breakout, the signal is new information relative to expectations.

### New York extension of a London move

**Rule:** Identify the direction and size of a move during a predefined London interval, observe the move after 7 a.m. New York, and test whether an extension reverses later. The book supplies no fixed interval, minimum move, entry trigger, exit or stop.

**Source and evidence:** AC ch. 4, “New York Open.” The author recalls a recurring EURUSD extension-and-reversal pattern during the Eurozone crisis, not a quantified test.

**Fit:** Good M1 coverage, but poor prior odds against the project’s intraday cost wall; the narrative has no directly observed compulsory counterparty. Usually no overnight swap. It is close to previously failed session and reversal families, with only a session-sequence distinction.

### Round-number order placement

**Rule:** For an independently established bullish view, the author illustrates placing a buy limit at 1.3001 rather than below the 1.3000 round number; mirror for a sell. The underlying signal, order lifetime, stop and target are unspecified.

**Source and evidence:** AC ch. 6, “Support and resistance.” He asserts that his own data show daily highs and lows cluster at round numbers, without reporting a costed execution comparison.

**Fit:** M1 can compare observed touches, but cannot validate queue position, spread-side fills or missed executions. Swaps apply if positions cross the broker cutoff. This is an execution experiment on an existing signal, not a new standalone pattern strategy; compare against the same signal’s ordinary execution.

### Moving-average pullback in a supported trend

**Rule:** The author describes buying a pullback to a fast moving average when a slower average and its slope indicate an uptrend, with a stop below a slower average or support; reverse for shorts. Examples use 55- and 200-hour averages. The exact touch/fill rule, stop distance and exit are not fixed.

**Source and evidence:** AC ch. 6, “Simple and exponential moving averages” and “Identify the Regime.” Evidence is selected chart examples.

**Fit:** Available on M1-derived bars, but poor priority given failed trend and price-pattern families and costs. Overnight positions incur swap. A separate macro thesis is part of the author’s intended use, but it is not quantified here; without it this resembles a previously failed trend strategy.

### Daily flag breakout

**Rule:** After a sharp advance and consolidation, buy when a daily bar closes above the flag; stop below the flag’s bottom and project a target from the flagpole length. Mirror for a decline. The author does not quantify what qualifies as a sharp advance or a valid flag.

**Source and evidence:** AC ch. 6, “Trade breakouts and continuation patterns.” In his CADJPY example a 140-pip flagpole gave a projected 95.00–95.40 target, reached within ten trading days.

**Fit:** Daily bars can be constructed, but subjective formation definitions and a selected winner make this poor priority after failed breakout tests. Multi-day holding requires swap and gap-aware execution. This is substantially similar to the failed price-pattern and breakout families, with a particular stop and target.

### Warnings / pitfalls

- **Tokyo fixing time is internally inconsistent.** Do not translate it into a strategy until the relevant historical benchmark time is established.
- **No automatic WMR fade:** the author specifically says a large fixing move alone is insufficient. A month-end imbalance can also reflect information, pre-positioning or persistent flow.
- **Flow is inferred, not observed:** price, tick activity and equity returns do not reveal actual fix orders, hedge ratios or dealer inventory.
- **No lookahead in event work:** use completed M1 candles, point-in-time release information and market closes available at the decision time. Do not use the later US equity close to predict the earlier London fix.
- **Historical conventions are not current specifications:** fixing use, option-expiry conventions, spreads and event relevance can change. The book’s historical figures should not be treated as current broker terms.
- **Spread, slippage and missed fills can erase small intraday effects.** Test stressed event-time costs and account for rollover on positions held across the actual broker cutoff.
- **Jumps can exceed stops**, especially at releases, interventions and weekend opens. Candle OHLC alone cannot guarantee the order of prices or an executable fill.
- **Technical examples are selected after the fact.** Treat parameter fitting, visual pattern recognition and multiple correlated indicators as potential sources of overfitting.
- **COT and risk reversals:** the assigned lines do not provide a precise COT or risk-reversal trading rule. They are not silently filled in from later chapters. Likewise, no distinct quarter-end hedge-rebalancing rule is given in this range.


# Part 2: ch.7-10, seven setups, intermarket, behavioral finance, news

### Overview

Donnelly combines technical, macroeconomic, behavioral and news analysis, looking for several independent reasons to hold a trade. His preferred style leans toward mean reversion, but he also follows strong surprises and momentum.

His technical setups use identifiable invalidation levels, though many entries depend on judgment about important prices or the fundamental backdrop. Cross-market divergences are clues, not arbitrage: relationships change and either market can adjust. Positioning and sentiment can remain extreme throughout a trend; he favors watching for an actual turn. For news, he emphasizes the difference between the outcome and what was already expected.

Most examples are individual historical trades. The book’s confidence in them should not be mistaken for evidence of positive expectancy after spread, slippage and swap. The current handoff says **new FTMO signal screens are paused**; the ideas below are notes for later consideration, not a recommendation to run them now.

### Chapter notes

### Ch 7 — Understand Technical Analysis II: The Seven Deadly Setups

- **Slingshot reversal:** a widely watched support or resistance breaks, then price returns through it. The proposed mechanism is that breakout traders and stopped-out participants are caught on the wrong side. In the USDJPY example, resistance at 114.50 broke to 114.73; the proposed short entry was approximately 0.1% below the level, with a stop approximately 0.1% above the new high. A target of 1.5–2 average daily ranges is suggested, or a relevant opposing level. The importance of the level remains subjective. *(AC, Ch 7, “Slingshot Reversal,” Fig. 7.1.)*
- **Hammer and shooting star:** use a reversal candle to time an existing countertrend thesis, with a stop beyond the extreme. The author’s dollar-index example enters at 79.35 and stops at 78.75; it is a selected successful example, not a measured hit rate. *(AC, Ch 7, “Shooting Stars and Hammers,” Figs. 7.2–7.4.)*
- **100-hour deviation:** for USDCAD, the author considers spot more than roughly **1%** from the 100-hour moving average stretched. He describes entering at that deviation and allowing another **0.7%** for the stop. He uses it with another reason for the trade, not alone. A moving average can catch up to stationary price, so a closing deviation does not necessarily pay the trader. *(AC, Ch 7, “Extreme Deviation,” Fig. 7.5.)*
- **Volume climax:** after a price extreme on very high volume, he waits for **two or three declining 30-minute volume bars**, then enters against the move with a stop beyond the extreme. Futures volume is his preferred proxy for decentralized FX volume. *(AC, Ch 7, “Volume Spike at a Price Extreme,” Fig. 7.6.)*
- **Broken triangle:** after a triangle breaks against his prior directional view and price closes back inside, he trades the reversal with a stop outside the broken boundary. He watches hourly and daily charts. The geometric definition and prior bias are discretionary. *(AC, Ch 7, “Broken Triangles,” Figs. 7.7–7.9.)*
- **Multiple tops or bottoms:** trade near a repeatedly tested level with a stop just beyond it. His USDCAD example sells 1.3980 with a stop at 1.4017 around the 1.4000 round number. This is a single illustration. *(AC, Ch 7, “Double and Triple Top,” Figs. 7.10–7.11.)*
- **Sunday gap fade:** take the other side during the opening hour, stop one average daily range away, and take profit after **90% of the gap** fills. The proposed mechanism is an opening order imbalance amid thin liquidity. The Greek referendum and Turkish lira examples both filled; there is no full-sample success rate. *(AC, Ch 7, “Sunday Gaps,” Figs. 7.12–7.13.)*
- **Combined signals:** the author favors several aligned technical and fundamental reasons and avoids conflicting evidence. More conditions do not by themselves establish independent evidence; the combinations also increase selection risk. *(AC, Ch 7, “Combo Setups.”)*

### Ch 8 — Understand Correlation and Intermarket Relationships

- Cross-market analysis seeks a currency lagging another asset. The author ranks relationships by perceived reliability: other FX pairs, interest rates, commodities, equity indices, then individual stocks or ETFs. He stresses that all can change. *(AC, Ch 8, “How to Trade Cross-Market Correlation.”)*
- Before using a relationship, ask whether it has economic logic, whether both rising and falling observations support it, whether a third variable drives both series, and whether it is likely to persist. Searching many overlays naturally produces spurious relationships. *(AC, Ch 8, “Understand Correlation.”)*
- Relative interest rates are a major historical FX driver in his experience. An unexpected RBA 25 bp hike is illustrated by an immediate AUDUSD jump from about 0.9880 to 0.9990. Magnitudes and timing between rates and currencies need not match. *(AC, Ch 8, Fig. 8.3 and “Correlation … versus Interest Rates.”)*
- For CAD and oil, he proposes export income, conversion of oil receipts into CAD, and Canada’s status as an oil producer as possible links. For AUD he watches gold and copper; for NZD, dairy. These are hypotheses about economic links, not proof of an exploitable lead. *(AC, Ch 8, “Correlation … versus Commodities.”)*
- Equity–FX correlations can reverse with the regime. His examples contrast the late-1990s relationship with the 2003–2010 risk-on/risk-off period; he also describes a historically strong Nikkei–USDJPY relationship. *(AC, Ch 8, “Correlation … versus an Equity Index,” Figs. 8.6–8.8.)*
- His January 2012 EURUSD example uses a **3% DAX rise on a US holiday** while EURUSD lagged; EURUSD subsequently rose about 150 pips. This is one selected event and does not establish a general holiday effect. *(AC, Ch 8, Figs. 8.12–8.13.)*
- A large, price-insensitive corporate FX order can temporarily hold a currency away from related markets; the author offers an acquisition-related AUD sale as an illustration. That mechanism is plausible but its presence cannot be inferred from price divergence alone. *(AC, Ch 8, “FAQ about Correlation Trading.”)*
- He normally uses **21–42 days of hourly observations** for overlays and warns that changing chart scales to support a thesis invites confirmation bias. Predefine a stop rather than adding indefinitely as a divergence widens. *(AC, Ch 8, “FAQ about Correlation Trading”; “A Note on Stop Losses and Discipline.”)*

### Ch 9 — Understand Behavioral Finance

- **Sentiment** is what participants say or believe; **positioning** measures positions actually held. A bearish but lightly positioned market can have future sellers; a bearish and crowded short can be vulnerable to covering. Neither condition guarantees the next move. *(AC, Ch 9, “Positioning and Sentiment.”)*
- The author discusses COT non-commercial currency-futures positions as a partial proxy for broader FX positioning. He notes sampling limitations and that futures are only part of the market. He attributes the report to CME; operationally, it is the **CFTC** report. *(AC, Ch 9, “Positioning,” Fig. 9.1.)*
- He warns against automatically fading extreme positions: they can remain extreme for months. In his EUR example, a short position exceeding 100,000 contracts preceded a reversal in one episode, but later grew beyond 200,000 while EURUSD continued lower. He favors looking at change and divergence as well as level. *(AC, Ch 9, Fig. 9.1.)*
- A suggested setup is extreme positioning or sentiment **plus evidence of a turn**, ideally also a change in fundamentals or a reversal pattern. “Extreme” and “turn” are not given fixed thresholds. *(AC, Ch 9, “Positioning and Sentiment.”)*
- Confirmation bias can lead traders to select favorable charts, time horizons and news details. Overconfidence and extrapolation make a recent trend feel more certain than it is; anchoring can make traders hold a position until it returns to entry. *(AC, Ch 9, “Cognitive Bias.”)*
- Round-number order clustering may make FX highs and lows concentrate around round prices. His EURUSD plot covers **1999–2011**; he suggests placing a buy limit just above a sought round level and a sell stop below it. Spread and quote precision matter to any replication. *(AC, Ch 9, “Round Number Bias,” Fig. 9.4.)*
- Herding and career incentives can produce correlated decisions and forecasts. The author’s retail-sales chart suggests forecasts were more clustered than releases during 2010–2014; surprise distributions need not resemble forecast distributions. *(AC, Ch 9, “Herding Bias,” Fig. 9.6.)*
- He and a colleague report that strongly directional *Economist* covers were contrarian indicators one year later about **68%** of the time. The chapter does not provide enough sample and selection detail to assess that figure. *(AC, Ch 9, “Anecdotal Evidence.”)*
- He explicitly warns that anecdotes have selection and sample-size problems. In his bullish-EUR example, early extreme anecdotes preceded a further move of roughly **12 big figures over six months** before the peak. *(AC, Ch 9, Fig. 9.10.)*

### Ch 10 — Trading the News

- The market reacts to information relative to what was **already priced in**, not simply whether a headline is good or bad. His RBNZ example describes a hike anticipated over months followed by NZD selling after the expected decision. *(AC, Ch 10, “Understand What Is Priced In,” Figs. 10.1–10.2.)*
- A rumor/fact reversal requires an anticipated event, the expected outcome, and prior pricing of that outcome. The author warns that fading every release is dangerous. *(AC, Ch 10, “Buy the Rumor/Sell the Fact.”)*
- Immediate headline trading is highly competitive. He suggests that an extreme surprise can nevertheless produce subsequent waves of positioning. More than **two standard deviations** of surprise is his rough definition of an important data extreme; expectations and positioning still matter. *(AC, Ch 10, “Trade the Extreme Data.”)*
- A **NewsPivot** is the price immediately before a release. In his April 2015 USDJPY example, the weak retail-sales release first drove price from 119.92 to 119.57; he sold a rebound at 119.66, placed a stop at 120.03 and exited around **11:00 New York time**. He argues activity tends to diminish after that time; this is not a tested universal cutoff. *(AC, Ch 10, Fig. 10.6.)*
- A strong headline with weak details can reverse the initial reaction. His Australian jobs example shows an initial rise followed by a fall of about **1.5% over the next few hours** after a data-methodology warning. That is an exceptional historical case. *(AC, Ch 10, “Reversal for a Good Reason,” Fig. 10.7.)*
- In another case, Canadian CPI beat the highest forecast and USDCAD initially fell, then regained its pre-release pivot and later rose. The author treats an unexpected price response as information about supply and demand; the cause is not demonstrated. *(AC, Ch 10, “Reversal for No Reason,” Figs. 10.8–10.9.)*
- For pre-meeting trades, he estimates outcome probabilities and conditional payoffs. In the Norges Bank example he estimated a **65%** chance of a cut versus market pricing around **40%**; the bank cut 25 bp and he reports nearly **$200,000** profit. The probabilities and payoff estimates were discretionary. *(AC, Ch 10, “Positioning into a Central Bank Meeting,” Figs. 10.10–10.11.)*
- His rule is to follow rather than fade unexpected central-bank moves. A surprise 2015 Bank of Canada cut moved USDCAD from approximately 1.2070 to 1.2230 immediately; it closed near 1.2340. Execution at or near the initial move cannot be assumed from M1 candles. *(AC, Ch 10, “Trading the Outcome of a Central Bank Meeting,” Figs. 10.13–10.14.)*
- Other possible catalysts include central-bank speeches, OPEC decisions, US energy inventories, dairy auctions, geopolitical events and disasters. He cites the US energy inventory release at **10:30 a.m.**, with day and timing subject to the actual historical release calendar. *(AC, Ch 10, “Other Headlines and News Events.”)*

### Topic tags

- **Trend / breakout:** failed breaks can reverse sharply; strong positioning can also accompany persistent trends. Unexpected central-bank decisions are, in the author’s view, momentum events. *(AC, Chs 7, 9–10.)*
- **Mean reversion / patterns:** slingshots, extreme 100-hour deviations, volume climaxes, failed triangles, multiple tops and Sunday gaps. These need objective definitions and evidence beyond the illustrated winners. *(AC, Ch 7.)*
- **Intraday / sessions:** the Sunday opening hour is central to the gap idea; the author uses about 11:00 New York as an example news-trade exit. The assigned chapters give no London-fix or Tokyo-fix trading rule. *(AC, Chs 7, 10.)*
- **Seasonality / time:** year-end risk reduction may leave sentiment and positioning out of alignment; he offers this as a scenario, not a measured calendar anomaly. No month-end or quarter-end hedge-flow rule appears in this range. *(AC, Ch 9, “Positioning and Sentiment.”)*
- **Volatility:** wide event moves and feedback loops can overshoot; a mean-reversion stop must allow for continued extension. A stop is not a guaranteed fill during a jump. *(AC, Chs 7, 9–10.)*
- **Stops and exits:** technical invalidation, one daily range on a Sunday gap, 90% gap fill, and NewsPivot-based invalidation are proposed examples. *(AC, Chs 7–8, 10.)*
- **Position sizing / risk:** the author sizes by conviction and stop distance; he recommends smaller contrarian positions in emotional, volatile conditions. His aggressive-sizing examples are opinions, not validated portfolio rules. *(AC, Chs 7, 9–10.)*
- **Testing and robustness:** watch spurious correlations, selective anecdotes, changing overlay scales and unstable regimes. His preferred visual confirmation and many-signal approach still needs protection against multiple testing and hindsight. *(AC, Chs 8–9.)*
- **Costs and execution:** OTC FX lacks a centralized volume measure; Sunday openings and news releases are especially sensitive to executable prices, spread and slippage. M1 OHLC cannot establish a microsecond fill. *(AC, Chs 7, 10.)*
- **Psychology / discipline:** confirmation, overconfidence, anchoring, fear, herding and longshot preference affect decisions. The author advocates being flat when confused. *(AC, Ch 9.)*
- **Portfolio / diversification:** the author distinguishes concentrated directional FX trading from relative-value traders who hold many smaller positions; he does not specify a portfolio construction system here. *(AC, Ch 8, “FAQ about Correlation Trading.”)*

### Testable ideas

The four failed strategies mentioned in the brief are not identified as a group in the supplied context. I therefore **cannot reliably compare each idea against all four**. The handoff and idea index identify the spent **gap momentum** test and a failed **gap fade**; similarities to those are flagged below. Missing parameters are explicitly marked, rather than supplied as author defaults.

1. **★ COT positioning turn.** On the CFTC report’s actual public release, identify an extreme non-commercial net position that has begun to reverse; trade the corresponding currency in the direction of the positioning change. Exit, stop, normalization, extreme threshold and holding period are **unspecified** and would need a separate spec. The author cites historical EUR positioning charts, not a backtest. **Fit:** potentially good because free COT and FX candles exist, but report timing, contract orientation and incomplete coverage of OTC positions matter; overnight swap applies. Unlike a price-only gap rule, the hypothesized driver is position liquidation. *(AC, Ch 9, “Positioning,” Fig. 9.1.)*

2. **★ Surprise-release NewsPivot continuation.** For a major release with a surprise beyond **2 historical standard deviations**, wait for the initial move and a rebound, then enter in the surprise direction; invalidate beyond the pre-release price and consider exiting around **11:00 New York**. The exact rebound and stop buffer are unspecified. Evidence is a selected USDJPY example. **Fit:** conditional on point-in-time actuals, consensus, event timestamps and realistic event spreads; none is established by M1 candles alone. Usually intraday, but charge swap if held through rollover. The distinction from gap momentum is a separately observed fundamental surprise and event reaction. *(AC, Ch 10, “Trade the Extreme Data,” Fig. 10.6.)*

3. **★ NewsPivot rejection.** Following a material surprise, wait for price to reverse its initial move and cross the pre-release price; enter in the reversal direction. The author gives no fixed crossing confirmation, stop or exit rule. The Canadian CPI episode is one illustration. **Fit:** FX candles plus historical releases and expectations are needed, with event spreads and execution delay; intraday unless specified otherwise. Its differentiator is a failed response to externally observed news, not a generic price reversal. *(AC, Ch 10, “Reversal for No Reason,” Figs. 10.8–10.9.)*

4. **★ Unexpected central-bank move continuation.** After a genuinely unexpected rate decision, enter in the direction of its initial currency impact and exit on a return through the pre-announcement NewsPivot. The author does not provide a fixed delay or profit-taking horizon; the 2015 BoC case is one example. **Fit:** poor without historical meeting expectations or rate-implied probabilities, and few genuine surprises limit power. News slippage is material; multi-day holds incur swap. The independent catalyst distinguishes it from a routine breakout. *(AC, Ch 10, “Trading the Outcome of a Central Bank Meeting,” Fig. 10.13.)*

5. **★ Oil–CAD divergence.** When oil moves strongly while USDCAD remains comparatively unchanged, trade USDCAD in the direction implied by the oil move, provided other evidence supports the thesis. Use a predefined price stop and a target informed by the prior relationship; thresholds and holding horizon are unspecified. The author reports selected successful examples. **Fit:** plausible with available oil and FX data only if timestamps and the actual oil instrument align; intraday oil information is needed for an intraday claim, and overnight positions incur swap. This adds an external export and conversion-flow hypothesis to a price signal. *(AC, Ch 8, “Trading the Correlations,” Figs. 8.14–8.18.)*

6. **USDCAD 100-hour deviation.** On an hourly view, consider fading a move **1%** above or below the 100-hour moving average, with a stop another **0.7%** away. The author requires another reason for the trade and does not fix a profit exit. His support is experience and a chart, not an expectancy estimate. **Fit:** candles are available, but it is a crowded price mean-reversion family and may hold overnight with swap. No demonstrated distinction from prior failed price-pattern work. *(AC, Ch 7, “Extreme Deviation,” Fig. 7.5.)*

7. **Sunday gap fade.** During the first trading hour, trade against the gap from Friday’s close; stop one average daily range away and exit when **90%** of the gap is filled. The average-range lookback and exact entry time are unspecified. Evidence is two selected fills. **Fit:** opening spreads, missing first quotes and gaps through stops are decisive; swap may apply if the trade persists. This is directly related to the project’s **failed gap fade** and should not be presented as a new independent edge. *(AC, Ch 7, “Sunday Gaps.”)*

8. **Slingshot at a watched level.** After a significant level breaks, enter on a reversal approximately **0.1%** back through it; stop about **0.1%** beyond the new extreme and target **1.5–2 daily ranges** or an opposing level. The author’s evidence is a USDJPY example; how to identify a broadly watched level beforehand is unspecified. **Fit:** candles suffice only for an objective proxy, with spread and possible swap. It is closely related to existing failed price-pattern families. *(AC, Ch 7, “Slingshot Reversal,” Fig. 7.1.)*

9. **Volume-climax reversal.** Following an extreme price move on exceptional volume, wait for **2–3 declining 30-minute volume bars**, enter against the move and stop beyond the extreme. Volume threshold and exit are unspecified. Evidence is one USDJPY example. **Fit:** poor without suitable point-in-time FX futures volume; broker tick volume is a different measure and needs separate validation. Overnight swap may apply. Its additional hypothesis is position transfer during a liquidity event, but volume alone does not prove that mechanism. *(AC, Ch 7, “Volume Spike at a Price Extreme,” Fig. 7.6.)*

10. **Round-number execution study.** Compare otherwise identical buy limits just above a round FX level with orders at or below it, and compare protective sell stops below the level. Measure fill probability, adverse selection and net results rather than assuming the clustering is profitable. The author shows EURUSD high/low clustering for 1999–2011. **Fit:** M1 data allow only approximate analysis; executable bid/ask and intrabar order sequencing are needed for reliable fills. Swap depends on the underlying trade. This is primarily an execution question, not a standalone signal. *(AC, Ch 9, “Round Number Bias,” Fig. 9.4.)*

11. **Headline–details reversal.** After a strong headline causes an initial currency move, fade it if contemporaneous report details materially contradict the headline; stop and exit are unspecified. The Australian employment release is the selected example. **Fit:** poor without timestamped component releases and expectations; discretionary interpretation must be specified before looking at outcomes. Event spread and possible swap apply. The proposed distinction is conflicting information inside the release, not price shape alone. *(AC, Ch 10, “Reversal for a Good Reason,” Fig. 10.7.)*

12. **Holiday cross-market catch-up.** When one market is open and a related market is on holiday, observe a substantial move in the open market and a lagging FX pair; trade the FX catch-up with a stop beyond its recent extreme. The author gives no general threshold or exit. The DAX/EURUSD example is one event. **Fit:** requires synchronized historical market data and holiday calendars; spreads and overnight swap matter. Its proposed mechanism is temporarily uneven participation, but the example alone does not establish it. *(AC, Ch 8, Figs. 8.12–8.13.)*

### Warnings / pitfalls

- A story about forced trading, crowding or a liquidity imbalance is a **hypothesis**, not evidence that the flow occurred. Price alone rarely identifies the counterparty.
- COT observations describe positions at an earlier observation date and become usable only when publicly released. Do not align them to Tuesday as though known then; account for release delays and contract conventions.
- Economic releases need historical consensus and actual values as available at the event, including revisions and timestamps. Do not substitute later revised data for what a trader knew.
- A plotted divergence can disappear with another chart scale, another regime, or a move in the non-FX asset. Fixed, pre-registered measurements and genuinely prior information are essential.
- The author’s selected examples, strong language and high-conviction sizing do not establish a strategy’s win rate or expected value. Count related variants in the multiple-testing ledger and check power before inspecting results.
- News and Sunday-open candles can hide gaps, spread spikes and unavailable fills. Model executable sides, conservative intrabar ordering and slippage; include CFD swap whenever positions cross rollover.
- Extreme positioning can grow more extreme; apparent sentiment reversals can be months early. A protective stop does not guarantee the assumed loss in a discontinuous market.
- The author’s preference for many aligned signals creates degrees of freedom. Predefine the conditions and test whether each adds information rather than selecting combinations after seeing outcomes.


# Part 3: ch.11-16, free capital, position sizing, trader traits and weaknesses

### Overview

Chapters 11–16 focus on capital preservation, position sizing, trading discipline and the author’s experience managing discretionary FX risk. Donnelly treats the amount a trader can actually afford to lose as the relevant capital base, then adjusts risk as that cushion changes.

His examples offer several numerical risk-management rules, but most are personal practices or illustrations, not controlled strategy tests. He emphasizes fat tails, stop slippage, the difference between decision quality and a single outcome, and the damage caused by unnecessary trading.

The assigned passage contains **little on the requested flow mechanisms**. It mentions an 11 a.m. New York fixing and the London/New York overlap, but does not give a month-end hedge-rebalancing rule, Tokyo-fix rule, COT signal or risk-reversal strategy. Those subjects appear elsewhere in the book.

The extracted text does not consistently preserve printed page headers. Page references below use identifiable index entries; chapter ranges are approximate where the extraction does not establish exact boundaries.

### Chapter notes

### Ch 11 — Understand Free Capital (approximately AC pp. 295–320)

- **Free capital** is the amount available to lose before a binding financial or employment limit is reached. It is not leveraged notional: a $100 million mandate with a $10 million maximum loss has $10 million of free capital.
- Set return and volatility objectives alongside the loss constraint. The author prefers monthly risk and P&L intervals for short-term discretionary trading; he acknowledges that calendar resets create arbitrary breaks.
- His example starts with a $5 million loss cushion: a monthly stop is **10% of free capital**, or $500,000, and the monthly objective is **twice that stop**. At the next month’s start, update the cushion using year-to-date P&L. Stop trading for the month if its loss limit is reached; slow down after reaching the profit objective. These are his personal rules, not verified optima. (AC pp. 295–298.)
- Record daily P&L open, high, low and close; examine whether gains are repeatedly given back, whether the strategy recovers from large intraday losses, and whether product or time-of-day attribution reveals a recurring leak. (AC pp. 298–301.)
- A stylized trader earns more than $15 million despite winning only 46% of days: average winning day $411,000 versus average losing day $273,000. The chart is explicitly illustrative, not actual audited performance. (AC pp. 299–302.)
- Win rate and average win/loss must be interpreted together. Donnelly describes sticking to planned profitable exits after noticing he often took gains early. His claim that monthly and annual results are largely skill-driven should not be assumed for small, dependent or fat-tailed samples. (AC p. 302.)
- Sharpe is useful for comparing return per unit of volatility but can conceal asymmetric tail exposure, especially with short samples or option-selling-like returns. Pair it with drawdown and examination of the return distribution. (AC pp. 302–304.)
- The EURCHF floor appeared to make buying near 1.2000 attractive until the SNB removed it on 15 January 2015. He describes initial trading near 1.0100 and a rapid fall toward 0.8500: a stop level was not a reliable maximum loss. (AC pp. 304–309.)
- His Bloomberg chart identifies eight daily G7/USD ranges of at least 6% after 2008 through September 2017, including three above 10%. He proposes several market-structure explanations, but these are hypotheses rather than established causal results. (AC pp. 310–315.)
- In his own hedge-fund P&L, performance tended to rise between **7 and 11 a.m. New York** and decline afterward. He began reducing exposure near 11 a.m. This is a personal attribution observation, not evidence that buying at 7 and selling at 11 has positive expectancy. (AC pp. 315–317.)
- Keep a journal with the trade’s rationale, intended risk and target, factor category and subsequent result. Wait for a meaningful sample before drawing conclusions, and investigate hypotheses rather than collecting every available statistic. (AC pp. 317–320.)

### Ch 12 — Understand Position Sizing (approximately AC pp. 321–350)

- Size depends on free capital, conviction, instrument volatility and stop location. The author’s illustrative risk allocations are **1%, 3% and 6% of adjusted free capital** for three-, four- and five-star ideas. Adjusted free capital incorporates year-to-date P&L. He describes five-star opportunities as rare, perhaps ten in a good year. (AC pp. 321–326.)
- His combined risk approach limits a new trade by the remaining monthly allowance. He normally prefers aggregate open risk around **3–5% of free capital**, and says he avoids exceeding **8%**, even across apparently unrelated trades. Shared currency exposure should be treated as a common theme. These are personal limits, not project rules. (AC pp. 325–326.)
- Alternative daily frameworks risk at most **2%** of opening free capital; a simpler novice example uses **1%**. Both mechanically increase nominal risk after gains and reduce it after losses. Neither guarantees the cap during gaps. (AC pp. 326–328.)
- Kelly sizing is an educational benchmark based on assumptions about probabilities and payouts. Since future probabilities are estimated rather than known and bets can overlap, he suggests considering half- or quarter-Kelly. Uncertainty and model error remain material even with fractional Kelly. (AC pp. 328–330.)
- Determine the stop first, estimate loss per unit including execution costs, then calculate position size as risk budget divided by estimated loss per unit. His EURUSD example risks $20,000 over a 48-pip stop plus 2 pips estimated slippage, producing a €4 million position. Actual slippage can exceed the estimate. (AC pp. 330–332.)
- Constant notional ignores differences in pair volatility and stop distance. Very large size can force emotional exits; very small size can fail to meet a professional trader’s economics. Conviction-based variation is his discretionary judgment, not a demonstrably calibrated forecast. (AC pp. 333–337.)
- For stops, he describes placing the stop beyond a technical area with an additional **20% of average daily range**, ordinarily allowing at least approximately one daily range from entry. Illustrative distances are **1.2 daily ranges** for shorter trades and **2.5** for medium-term trades. These are alternatives and heuristics, not a fully specified entry system. (AC pp. 337–340.)
- A trailing exit can follow a prearranged price trigger or a moving average; his chart example uses a **40-hour EMA**, with an hourly close through the average as an exit. He also mentions a 100-hour average and updating a stop every 12 or 24 hours with extra room. (AC pp. 339–341.)
- Reward/risk alone is insufficient: probability matters. He illustrates that 3:1 with a 20% win rate can be inferior to 1:1 with a 65% win rate. These probabilities are examples, not measured strategy results. Subjective probability estimates can be highly inaccurate. (AC pp. 341–342.)
- Record the stop, avoid moving it farther away to rationalize a loss, and automate execution when possible. After being stopped, his personal cooling-off rule allows a renewed trade after **four hours**. He allows planned protective changes such as trailing a profitable stop or reducing event risk. (AC pp. 342–344.)
- He gives a rough historical practitioner estimate of **2–3 pips** stop slippage in many liquid G10 pairs for relatively small institutional orders, while warning that event and gap slippage can be much larger. This must not substitute for FTMO-specific observations. (AC pp. 343–345.)
- A good decision can lose and a bad decision can win. His 55%-winning-day illustration assumes a stable, favorable process; it does not establish that an observed trading edge is stable or that losses cannot cluster. (AC pp. 347–350.)

### Ch 13 — Characteristics of a Successful Trader (approximately AC pp. 353–360)

- Balance willingness to take risk with a process that limits it. Independent thinking is different from automatically opposing the consensus. (AC p. 353.)
- Know the source of the edge: transaction costs make repeated trading a negative-sum activity before skill or other compensation. (AC p. 354.)
- Define a trading horizon before entry. Donnelly says his own trades generally last **three hours to seven days**, most often **one to three days**. He warns against converting losing short-term trades into investments or prematurely cutting longer-horizon winners. (AC pp. 354–355.)
- Prepare a written daily plan and accept that being flat is a valid position. His “tight/aggressive” analogy means waiting for strong opportunities while avoiding uncontrolled exposure. (AC pp. 355–357.)
- Review emotional state, biases and recurring mistakes. He recommends reducing risk when euphoric as well as when frustrated. Claims about intuition are experiential: experienced intuition can encode useful patterns but can also reflect fear, hope and confirmation bias. (AC pp. 357–360.)
- Adapt to changes in liquidity, volatility and correlations, but investigate contrary explanations rather than merely searching for evidence supporting an initial view. (AC pp. 358–360.)

### Ch 14 — Common Weaknesses in Trading (approximately AC pp. 361–368)

- The author identifies poor risk control, extending losers, cutting winners and adding losses to losses as major failure modes. (AC p. 361.)
- Boredom, excitement, loss chasing and the desire to appear clever can produce transactions without a valid economic reason. He describes these as behavioral risks, not as a quantitative study of traders. (AC pp. 361–364.)
- Fear of missing out can turn a planned entry into a late, expensive chase; it can also keep a stale view alive long after its original rationale has deteriorated. He recounts three persistent USDJPY bears who lost their jobs before the eventual large decline. (AC pp. 364–366.)
- Overconfidence after success can be as damaging as frustration after losses. His own spreadsheet highlights exceptionally strong performance as a reminder to reassess risk. (AC pp. 366–367.)
- Some risk-averse discretionary traders may benefit from a minimum trade quota, in his opinion; this conflicts with his own warning about low-conviction trading and should not be treated as evidence that forced trades have an edge. (AC pp. 366–367.)
- Examine persistent long or short biases and update views as evidence changes. Separate constructive review of past mistakes from fixation on missed profits. (AC pp. 367–368.)

### Ch 15 — The Voice of Experience (approximately AC pp. 369–378)

- Unplanned, low-conviction trades can consume profits from stronger ideas. The author proposes either a maximum trade count or designated trading windows to restrain repeated entries and exits. (AC pp. 369–371.)
- His example is to enter or adjust around **7 a.m. New York**, then leave positions until at least **11 a.m.**; he often reduces risk at 11 a.m. or 4 p.m. New York. He describes an **11 a.m. fixing** as a high-volume time. This is a discretionary schedule, not a directional fixing strategy. (AC pp. 370–371.)
- As a personal accommodation for overtrading, he uses one unit of risk for exploratory trades versus **5, 10 or 20 units** for high-conviction ideas. He acknowledges this is more open-ended than enforcing trading windows. (AC pp. 371–372.)
- He states that a trader winning 55% of days can experience several five-day losing streaks and a six-day streak in a year. The exact frequency depends on the number and dependence of trading days; do not treat his rough figures as universal. (AC pp. 372–373.)
- During a slump, he may reduce normal size to **20%**, cut further if needed, or stop for a day or two. His stated recovery process includes closing positions, talking to someone, researching and reassessing circumstances. This is discretionary practice, not demonstrated alpha. (AC pp. 373–375.)
- Sleep, exercise, time away and flat vacations support sustainable decision-making in his experience. He warns against confusing a bad outcome with a breach of the trading process. (AC pp. 375–378.)

### Ch 16 — Conclusion (approximately AC pp. 379–380)

- Electronic execution reduced the number of human FX traders on bank desks and changed the work toward managing larger trades and interpreting markets; his account is a practitioner’s historical observation.
- Market regimes and relationships change. The author argues that continued learning, discipline and adaptation matter, but presents no new mechanical rule or performance study in the conclusion.

### Topic tags

- **Trend:** Donnelly warns against reflexively fading an obvious trend merely to feel contrarian. A moving average may serve as a preplanned exit, but the passage gives no complete trend-entry strategy. (AC pp. 339–341, 363–364.)
- **Mean-reversion:** He suggests his own P&L can retreat after unusually strong periods and describes intraday P&L giveback. Neither claim establishes a tradable price reversal. (AC pp. 297–299, 315–317.)
- **Intraday / sessions:** His favored activity window is the New York/London overlap, roughly 7–11 a.m. New York; he often reduces exposure at 11 a.m. or 4 p.m. (AC pp. 315–317, 370–371.)
- **Seasonality / time:** Monthly P&L resets are a risk-management convention. He observes that opportunities can cluster around month boundaries, but this passage does not specify a directional month-end FX signal. (AC pp. 295–298.)
- **Volatility:** Account for different daily ranges when sizing and setting stops; ordinary volatility estimates do not capture all discontinuous moves. (AC pp. 310–315, 324, 337–340.)
- **Stops and exits:** Specify the stop and target before entry, avoid widening stops to excuse a losing position, and allow for gap and event slippage. (AC pp. 337–345.)
- **Position sizing / risk:** Size to estimated loss, not fixed notional; consider correlated positions jointly and base risk on the actual loss cushion. (AC pp. 321–332.)
- **Testing and robustness:** Separate process from realized outcomes; a short sample and a high Sharpe can obscure tail risk. The author’s personal examples are hypotheses, not independent validation. (AC pp. 302–304, 347–350.)
- **Costs / execution:** Repeated discretionary adjustments can generate costly churn. Stop fills are uncertain, especially at announcements or during market dislocations. (AC pp. 343–345, 370–371.)
- **Psychology / discipline:** Written plans, journals, emotional awareness and limits on impulsive trading are central themes. (AC pp. 317–320, 353–378.)
- **Portfolio / diversification:** Several apparently separate trades can express the same underlying dollar view; aggregate the potential risk across the theme. (AC pp. 325–326.)

### Testable ideas

The ideas below are **research specifications proposed from the passage**, not complete systems supplied by the author. Entry directions, comparison groups and unspecified parameters must be pre-registered before any data look. Apply the project’s power check, cost model, trial ledger and one-time-test rules. The brief does not identify the four failed strategies, so exact strategy-by-strategy differences cannot be verified from the supplied context.

**★ New York/London overlap holding window** — For an existing independently specified FX signal available by 7:00 a.m. New York, compare execution at 7:00 and exit at 11:00 against a separately pre-registered later exit. No new directional signal or stop is supplied by Donnelly. Source: AC pp. 315–317, 370–371. Evidence: his own P&L attribution, not a controlled price-return test. Fit: good for FTMO M1, with observed spreads and DST-aware session times; intraday comparison has no overnight swap. Difference: a **trade-management overlay**, not another standalone CFD pattern or breakout.

**★ Fixing-window response study** — On liquid FTMO FX pairs, pre-register returns and spreads before and after the **11:00 a.m. New York** reference, with separate DST-aware treatment of a **4:00 p.m. London** reference. Test whether pre-fix directional movement continues or reverses after the reference; fix the pre/post windows and thresholds before looking. No stop, holding period or direction is specified in this passage. Source: AC pp. 315–317, 370–371. Evidence: the author’s description of a liquid fixing period and his discretionary risk reduction, not a demonstrated reversal. Fit: M1 prices are available, but actual fixing orders and benchmark flow direction are not; spread and slippage near the benchmark can consume a small move. Difference: a benchmark-timing hypothesis rather than a generic intraday price pattern. **Do not equate 11 a.m. New York with 4 p.m. London on every date:** UK and US DST changes do not always coincide.

**★ Monthly loss-budget overlay** — On an existing strategy’s dated trade stream, define opening free capital as the actual remaining loss cushion. At each month’s start, set the author’s illustrative stop to **10%** of that cushion; stop new trades for the month after the threshold is reached and resume at the next month, updating free capital for realized P&L. Specify treatment of open positions and simultaneous breaches before testing. Source: AC pp. 295–298. Evidence: author’s personal framework, no controlled test. Fit: good as a risk simulation; preserve the strategy’s actual spread, commission and overnight swap. Difference: changes exposure and drawdown rather than proposing a new entry edge. Test for skipped subsequent gains and gap overshoots.

**★ Stop-distance and sizing sensitivity** — For a fixed existing entry signal, compare a pre-registered stop at **1.2 prior-day average ranges** with a wider **2.5-range** variant, sizing each position to the same estimated cash loss and including realistic stop slippage. Use only completed candles for the range and keep the exit horizon fixed in advance. Source: AC pp. 337–340. Evidence: practitioner heuristics, no comparative test. Fit: good on FTMO M1, though M1 bars cannot reconstruct executable prices inside a fast gap; include swap if positions cross rollover. Difference: tests risk and implementation sensitivity of an existing signal, rather than a new chart-pattern strategy.

**★ Preplanned moving-average exit** — For an existing short signal, hold until a completed hourly candle closes above its **40-hour EMA**; mirror for longs. Pre-register the initial stop, maximum holding time, EMA warm-up and execution on the next available price. Source: AC pp. 339–341. Evidence: one illustrated EURUSD trade, not a strategy result. Fit: FTMO M1 can form closed hourly candles and model costs; likely overnight swap. Difference: exit overlay, although it can inherit the same cost wall as the underlying failed trend strategies.

**Four-hour re-entry cooldown** — On a strategy that permits repeated entries in the same direction and pair, compare its normal re-entry policy with a prohibition on re-entry for **four hours after a stop**. Keep all other signals and exits fixed. Source: AC pp. 342–343. Evidence: author’s personal discipline rule, no measured performance claim. Fit: good if the trade log preserves stop time and subsequent signals; include spread, slippage and swap where relevant. Difference: reduces repeated entry costs rather than claiming a new directional signal.

**Daily risk scaling** — At each day’s start, cap intended new risk at **1%** of remaining free capital; compare with a separately pre-registered 2% variant on an existing trade stream. Specify the account reset time, open exposure and what happens when gaps exceed the cap. Source: AC pp. 326–328. Evidence: author’s examples, not a comparative validation. Fit: risk simulator; actual FTMO daily limits and reset rules must be applied separately. Overnight positions retain swap and gap exposure. Difference: account-level sizing, not a CFD entry strategy.

**Trade quota / restricted adjustment times** — On a strategy that produces multiple same-day actions, compare its unchanged baseline with at most **three** entries per day, or with entries restricted to a pre-registered 7 a.m. New York decision time and exits at 11 a.m. except for protective stops. Source: AC pp. 369–371. Evidence: author’s overtrading advice; no measured alpha. Fit: good for timestamped signals and M1 execution, but an existing discretionary trade log may be needed to test the behavioral claim. Intraday version avoids overnight swap. Difference: controls turnover; it does not supply a directional forecast.

### Warnings / pitfalls

- **No complete forced-flow rule in this assignment.** The passage does not specify Tokyo-fix direction, WM/R order imbalance, month- or quarter-end hedge flows, COT thresholds, risk reversals or a news-surprise trading rule. The book’s index points to Tokyo fix at AC pp. 58–59 and COT positioning around AC pp. 225–226; those are outside this assigned reading.
- A fixing timestamp is not proof of forced buying or selling. M1 prices alone cannot identify actual benchmark orders or distinguish hedge rebalancing from other news and liquidity effects.
- Stop-based sizing estimates ordinary loss; it cannot guarantee a loss ceiling through gaps, spread widening or execution failure. Stress CHF-type events separately.
- Conviction ratings, regime changes and discretionary changes in size are vulnerable to hindsight and confirmation bias. A backtest needs observable inputs and rules fixed before outcomes.
- Session comparisons can multiply rapidly across pairs, windows and directions. Record all variants and account for dependence across pairs sharing a currency and for repeated observations around the same event.
- The author’s Sharpe thresholds, monthly performance claims and losing-streak examples should not be imported as statistical gates. Serial dependence, fat tails and estimated parameters can materially change uncertainty.
- The excerpt’s personal trading examples are useful for generating hypotheses, but they do not establish that those hypotheses overcome FTMO spreads, swap or slippage.

