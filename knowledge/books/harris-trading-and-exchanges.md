# Larry Harris, *Trading and Exchanges: Market Microstructure for Practitioners* (Oxford 2003), March 2002 draft

Short: **TE**. Cite by chapter (`TE ch.14`); the library file is the 2002 draft copy with shortened chapters and no
data, so draft pages are not the book's. Read 2026-11-18 by one Sonnet agent (`knowledge/reading-brief.md`); PDF in
the library folder Tier 1. The basic taxonomy of who trades and why (utilitarian, informed, dealers, liquidity
suppliers, parasitic traders), order types, spreads, block trading, volatility components, liquidity and market
structure. Opus's reading against our ledger: its testable consequences (forced-flow price pressure reverses when no
news; reversal is stronger in illiquid names; aggressive taker flow pays the liquidity supplier) are the families we
already screened: I-96 / I-99 / I-102 (share reversals), I-76 (crypto liquidation reversal), I-78 / Strategy 20 (taker
flow). No new card. The full book (2003) would add data and examples; replace this draft if it turns up.


Citation: TE ch.N, using the chapter numbers printed on the chapter heads of this draft (the draft's own table of contents numbers them differently; the draft's page numbers are per chapter, e.g. 14-3). The draft is heavily cut: each chapter is only the first 3-8 pages of the real chapter, and most chapters stop mid-argument. Read lines 1-5483 fully.

### Overview
- Market microstructure for practitioners, written in plain prose, almost no formulas, no empirical tables, no regressions. It is a conceptual map, not a data book. There are no numeric test results of the author's own.
- Core stance: trading is a zero-sum game (relative to the market average). Whoever profits needs a counterparty who loses or who trades for a non-profit reason. So every idea must name its loser.
- Trader taxonomy (TE ch.8): profit-motivated (informed speculators, dealers), utilitarian (investors/borrowers, hedgers, asset exchangers, gamblers, tax-avoiders, cross-subsidizers), futile (think they have an edge, do not). Utilitarian and futile traders lose on average. This is exactly our "counterparty that MUST trade" lens.
- Liquidity = ability to trade when you want; buy side buys it, sell side (dealers, brokers) sells it. Impatient traders pay a spread for immediacy; patient traders earn it. Spread = transaction-cost (transitory) part + adverse-selection (permanent) part.
- Dealers lose to informed traders, so they widen spreads and shade quotes against one-sided order flow; value traders are the "ultimate" liquidity suppliers who stand ready when price deviates from value (TE ch.16).
- Missing from the draft: the real chapters on inventory control, spread-component estimation (Roll, Glosten-Harris style), price impact measurement, opening/closing auctions as such (only a call-market paragraph in ch.5), index rebalancing details (ch.23 stops at index construction and fund replication), sizeable parts of ch.18, 21, 22, 24-26, 28 (crash dynamics stop after the bubble part). No numbers on impact, no auction imbalance rules.

### Chapter notes

### Ch 1 - Introduction (pp. 1-1 to 1-8)
- Five targets: liquidity, transaction costs, informative prices, volatility, trading profits. Recurrent themes: information asymmetry; trading options (a limit order gives a free option to others); order-flow externality; free entry equalizes net profits; zero-sum game.
- Dealers "take trading problems from clients and solve them at a profit"; patient traders get better prices than impatient ones; clients pay for immediacy.
- Free entry and exit: profitable strategies attract entrants and profits fall, losers quit. Useful as a prior for edge decay.

### Ch 2 - Trading Stories (2-1 to 2-3; cut very short)
- Only the retail NYSE example survives. Market order vs limit order; specialist fills market orders from own inventory if no one else will (traders of last resort). Quote montage example: Madoff, regional exchanges, ECNs.

### Ch 3 - The Trading Industry (3-1 to 3-3)
- Buy side buys liquidity; sell side sells it. Buy-side motives table: investors, borrowers, hedgers, asset exchangers, gamblers. Sell side: dealers, brokers, broker-dealers. Section on facilitators is cut.

### Ch 4 - Orders and Order Properties (4-1 to 4-3)
- Offering liquidity (standing limit orders, quotes) vs taking liquidity (marketable orders); "immediacy" is one dimension of liquidity. Prices are firm (orders) or soft.
- Agents who can respond fast beat traders who rely on standing orders: standing orders need contingencies written in.
- Spread has other names (touch, vigorish). Agency orders get precedence over proprietary at the same price in many markets.

### Ch 5 - Market Structures (5-1 to 5-3)
- Continuous vs call markets. Many continuous order-driven exchanges open with a call (single-price) auction and restart after halts with one; open-outcry futures start continuous at once. Governments sell bonds in call auctions. Pari-mutuel betting as a call market: orders only market type, many wait until the last moment to see prices.
- Price clustering on round numbers (whole, half, quarter...), strongest when the tick is small relative to price, volatility is high, and the instrument is thin. Clever traders place limit orders just beyond round numbers.
- Nothing on closing-auction mechanics or imbalance publication in the draft.

### Ch 6 - Order-driven Markets (6-1 to 6-3)
- Price priority is primary; time precedence secondary; tick size: if too small, time precedence is weak and price competition drops; if too large, nobody improves. Leapfrog game around the best bid.
- Rest of the real chapter (call-market pricing, crossing networks) is cut.

### Ch 7 - Brokers (7-1 to 7-3)
- Brokers beat clients on clearing/settlement credit, access, knowledge of who might trade, negotiation. Block market: broker searches for the other side among traders who have not shown interest. Credit-check multiplication example. Principal-agent problem sections are cut.

### Ch 8 - Why People Trade (8-1 to 8-3)
- Zero-sum game statement; profit-motivated traders must understand why losers trade. Stylized traders. Volume has many causes; misreading it is a typical error ("if your strategy depends on volume you must know why people trade").
- Investors/borrowers: intertemporal cash flow timing problems; hedgers, asset exchangers, gamblers, fledglings, cross-subsidizers, tax-avoiders. (Hedgers, speculators, dealers sections are cut off.)
- Informed traders base opinions on insightful analysis of public data or simple analysis of data not widely known.

### Ch 9 - Good Markets (9-1 to 9-3)
- Welfare economics framework: positive vs normative analysis, four-step normative argument. Mostly policy; skipped by the author himself for traders.

### Ch 10 - Informed Traders and Market Efficiency (10-1 to 10-3)
- Fundamental value = best estimate using current information; changes are unpredictable, so efficient prices follow a random walk. Price minus fundamental = noise (Black: within a factor of 2 counts as informative).
- Informed traders move price toward their estimate; with many informed traders with different data the price aggregates forecasts (algebra box: demand proportional to forecast minus price).
- Informed traders can lose short term even if right; in the long run they profit by holding and collecting cash flows.

### Ch 11 - Order Anticipators (11-1 to 11-3)
- Front runners, sentiment-oriented technical traders, squeezers: "parasitic", they do not add liquidity or information. Front runners trade ahead of aggressive (liquidity demanding) or passive traders. Legal front running by observing broker behaviour; "shop the block" raises price for a block buy.
- Large traders split orders to price-discriminate across liquidity suppliers; front runners take the cheap liquidity and re-offer it at worse prices. Larger tick sizes make front running costlier.
- Squeezers (exploit traders who must trade, e.g. cornering) are announced but the section is cut off.

### Ch 12 - Bluffers and Market Manipulation (12-1 to 12-3)
- Long-side bluff story (BNB): accumulate quietly over 40 days (200,000 shares, avg 6), pump with message boards and a non-news release, then buy 50,000 on the "news" so price jumps 7 to 10; momentum traders buy from the bluffer; price peaks at 13 then falls to 8.
- Traders who buy rising / sell falling prices are particularly exposed; liquidity suppliers must be careful about inferring value from price and volume.

### Ch 13 - Dealers (13-1 to 13-3)
- Dealers are passive traders, sell immediacy. They profit buy-low-sell-high but lose when forced to buy high / sell low, usually after meeting informed traders. Their inventory risk is large and they demand compensation when forced to hold large positions.
- Quoted vs realized spread: realized spread is often smaller because prices move between the dealer's two trades. Dell example: quoted 35.0/35.3, sells to client at 35.0, bad news arrives, dealer must lower quotes to 34.6/34.9, buys at 34.9 -> realized spread -0.1.
- Quote skewing: a dealer who wants to buy bids high and asks high (and the opposite when long); two-sided vs one-sided markets. Spread traders (earn only spread) vs position traders (must speculate to survive, competition squeezes pure spread income).
- The sections on inventory control and learning from order flow are not in the draft.

### Ch 14 - Bid/Ask Spreads (14-1 to 14-3)
- Spread = price of immediacy; wide spread favors limit orders, narrow favors market orders. "Uninformed traders lose simply because they trade."
- Competitive dealer markets: free entry drives dealer profit to normal return. Monopoly dealers charge more if clients are insensitive to costs. Public limit orders compete with and undercut dealers.
- Two spread components: transaction-cost ("transitory") component creates bid/ask bounce (price reversal after a jump from bid to ask), the adverse-selection component compensates for informed trades and produces permanent price change. Estimating the split needs econometrics (not in this draft).
- Spread drivers named: adverse selection, volatility, market activity (details cut off).

### Ch 15 - Block Traders (15-1 to 15-3)
- Block = more than about a quarter of average daily volume in an active stock (practitioner view); NYSE statistical cutoff 10,000 shares; suggestion to classify by fraction of ADV.
- Four problems: latent demand (liquidity suppliers who have not issued orders), order exposure (advertised size drives the market away), price discrimination (suppliers fear more size follows), asymmetric information (suppliers fear the initiator is informed).
- Order exposure: traders who learn of a block on the same side accelerate their own trading (they take liquidity ahead), those on the opposite side withhold liquidity; both raise the price impact of the block. Block initiators must give price concessions to attract responsive liquidity suppliers.
- Rest (how blocks are convinced to be uninformed and honest) is cut.

### Ch 16 - Value Traders (16-1 to 16-3)
- Value traders are the ultimate liquidity suppliers: they profit only when uninformed liquidity demanders have pushed price off fundamental value, and their trading pushes it back.
- How price deviates (16.1.1): dealers cannot tell uninformed from informed flow, so one-sided uninformed flow makes them move quotes (adverse selection reaction) and inventory-risk concessions, especially when they fear they cannot find the other side. Price falls below value, value traders buy from dealers at the dealers' discounted asks, dealers lay off inventory to value traders.
- Market resiliency: if value traders step in, dealers will take larger positions from uninformed clients. In non-resilient markets, impact is larger and lasts longer.
- Value traders face adverse selection (trading with news traders) and the winner's curse (misestimated value). They set an "outside spread" (wide, rarely quoted).

### Ch 17 - Arbitrage (17-1 to 17-3)
- Definitions: hedge portfolio, legs, basis, fair value of the basis from carrying costs, arbitrage spread, arbitrage bounds (trade only outside bounds), basis risk, hedge ratios. Arbitrageurs move liquidity between markets and enforce one price. Rest of the chapter (types, risks) is cut.

### Ch 18 - Buy Side Traders (18-1 to 18-3)
- Order submission strategy is the most important determinant of execution quality the trader controls: limit vs market, where to place the limit, display decisions, one broker vs many, time-splitting orders.
- Uninformed rule of thumb (take liquidity when spread is narrow, offer when wide) is only valid if you know nothing about value; example: market 48/50 but true value 45, sell market order is great, buy is bad.
- Execution probability depends on size at better prices, volatility, trader interest. Index funds that must rebalance on index changes named as a special case of buy-side urgency (details cut).

### Ch 19 - Liquidity (19-1 to 19-3)
- Liquidity defined as trading large size quickly at low cost when you want; dimensions (speed, size, cost) tied to a bilateral search. Search theory: continue searching while expected gain exceeds cost; exchanges are search engines. Sections on who supplies liquidity are cut.

### Ch 20 - Volatility (20-1 to 20-3)
- Fundamental volatility (news, unpredictable, random walk) vs transitory volatility (uninformed traders' demands, reverses). Regulators can influence only the transitory part. Dealer inference from order flow creates adverse-selection price changes that count as fundamental volatility.
- Storage costs: expensive-to-store commodities (gasoline US storage about 9 days of consumption, distillates about 18 days; Year 2000 EIA data) show spikes because inventories cannot buffer; inelastic demand adds spikes; perishables most of all. Link to our EIA energy futures.
- Statistical separation of the two volatility types is announced but cut off.

### Ch 21 - Liquidity and Transaction Cost Measurement (21-1 to 21-3)
- Costs = explicit (commission, fees, tax), implicit (spread, price impact), missed-trade opportunity cost (cotton example: limit 64.95 missed a 2.75 cent move, 137,500 dollars on 100 contracts).
- Benchmark method: cost = size * sign * (trade price - benchmark price); costs of both sides of a trade sum to zero; liquidity takers pay, liquidity providers earn negative cost. Benchmark choice and econometric methods are cut.

### Ch 22 - Performance Evaluation and Prediction (22-1 to 22-3)
- Skill vs luck: unforeseeable and unavoidable factors (Sizzler E. coli example), fully invested equity portfolios move with the market. Warns that predictions from past performance are unreliable and sample selection bias causes "more trading losses than any other mistakes". Details cut after the framing.

### Ch 23 - Index and Portfolio Markets (23-1 to 23-3)
- Price-weighted vs value-weighted vs equal-weighted indexes; divisor changes when constituents are added or deleted. Index funds replicate by holding a fixed fraction of each cap-weighted constituent; value-weighted fund only rebalances when the constituent list changes (so list changes force trading). Price-weighted: equal share count; stock splits force rebalancing.
- Index funds (Barclays Global about 571 bn dollars, under 2 percent of world traded equity in 2000). Index products lead cash index prices ("tail wags the dog"). Index futures more liquid than the underlying basket. Arbitrage and market-making in index products are cut.

### Ch 24 - Specialists (24-1 to 24-3)
- Designated market makers must quote two-sided markets when no one else will ("traders of last resort"), without obligation for blocks or to support price in a trend. Systems: single specialist, designated multiple market makers (CBOE rotating obligation). NYSE had 482 specialists, 8 firms, 5 firms handled 95 percent of dollar volume (Dec 2001).
- Affirmative vs negative obligations; privileges compensate. Rest cut.

### Ch 25 - Internalization, Preferencing, Crossing (25-1 to 25-3)
- Payment for order flow, best execution = fill at the NBBO for orders smaller than displayed size; price improvement; dealers filling limit orders only when trades print through the limit price. Mostly retail-execution detail.

### Ch 26 - Competition within and among Markets (26-1 to 26-3)
- Fragmentation vs consolidation; arbitrageurs, dealers moving liquidity in time, and order routing hold fragmented markets together; technology lowered cost of spreading information.

### Ch 27 - Floor vs Automated Trading Systems (27-1 to 27-3)
- Operational fairness, audit trails; examples of migration between floor and screen markets. Pit-trade price report anomaly (Eli's spread order, 70 vs 77 points) illustrates execution risk in pit markets.

### Ch 28 - Bubbles, Crashes, Circuit Breakers (28-1 to 28-3)
- Bubble/crash dynamics: optimism, momentum traders, order anticipators; the price accelerator (wealth transfers from pessimistic short traders to optimistic long traders; margin calls force shorts to cover, pushing price further). Value traders cannot or will not stand against it (capital limits, short sale limits, confidence, timing).
- Crash: sellers (long holders, early buyers taking profit), momentum buyers disappear, margin calls and stop-loss orders force selling, order anticipators sell ahead of them. Circuit breaker discussion is cut.

### Ch 29 - Insider Trading (29-1 to 29-3)
- Definitions and cases (Texas Gulf Sulfur: stock rose from 17 3/8 to 29 3/8 while insiders bought before the April 1964 announcement, then to 71; Chiarella). Regulation FD (2000). Not relevant to our tests except as a reminder that pre-announcement drift can come from informed traders.

### Topic tags

**trend**
- Price changes in efficient markets are unpredictable (TE ch.10, 20). Momentum traders buy rising prices and are fodder for bluffers (ch.12) and for bubble dynamics (ch.28). Trend after uninformed flow is a signature of price pressure, not information, and should reverse (ch.16).

**breakout**
- Nothing direct. Order anticipators and stop-loss hunting: stop orders and margin calls cluster and sellers/buyers anticipate them (ch.28).

**mean-reversion**
- The most useful content. Transitory price changes from uninformed liquidity demand revert as value traders and dealers lay off (ch.16, ch.20). Bid/ask bounce is the shortest-term form (ch.14). Liquidity supply is the economic explanation for mean reversion; it works only when the flow is uninformed.

**momentum/oscillators**
- Momentum traders (buy up, sell down) are the victims of bluffs and the accelerators of bubbles (ch.12, 28). No oscillators.

**patterns**
- None; Harris is critical of inferring information from price/volume without knowing why people trade (ch.8, 12).

**intraday/sessions**
- Call-market opening/restart, closing price clustering; no time-of-day volume or spread pattern in the draft. Price clustering on round numbers is stronger when tick is small relative to price, volatility high, thin instrument (ch.5).

**seasonality/time**
- Nothing, except forced-trade timing: index list changes (ch.23), settlement and cash-flow deadlines (ch.8, 18: "traders who need to raise cash before a deadline or index traders who need to rebalance").

**volatility**
- Fundamental vs transitory volatility (ch.20). Spreads widen with volatility and adverse selection (ch.14). Expensive-to-store commodities spike in volatility when inventory runs out (gasoline 9 days, distillates 18 days; ch.20).

**stops-and-exits**
- Stop-loss and margin-call selling feed crashes; anticipators sell ahead of them (ch.28). Order exposure: fast traders beat standing orders (ch.4).

**position-sizing/risk**
- Dealers demand a price concession for holding a large off-target inventory and when the other side is hard to find (ch.13, 16). Value traders' winner's curse and timing risk (ch.16, 28).

**testing-and-robustness/overfitting**
- Skill vs luck, sample selection bias is the biggest source of trading losses (ch.22). Unforeseeable factors and unavoidable factors (market beta) inflate or deflate apparent skill. Past performance predicts poorly; use economic priors (why would the counterparty lose?).
- The zero-sum test: for any rule, name who loses and why they will keep losing (ch.8).

**costs/execution**
- Spread = price of immediacy; uninformed traders lose by trading at all (ch.14). Implicit costs = spread + impact; missed trade cost (ch.21). Costs of two sides sum to zero: takers pay what providers earn. Active traders with weak edges lose to costs (Part VI intro).
- Limit vs market order choice depends on spread, depth at better prices, volatility (ch.18).

**psychology/discipline**
- Futile traders believe they have an edge (ch.8); confidence and timing problems of value traders in bubbles (ch.28). Dealers must be disciplined against bluffers (ch.1, 12).

**portfolio/diversification**
- Index funds are the passive alternative; most active traders cannot beat them after costs (ch.22, 23). Hedge portfolios reduce risk by offsetting common factors (ch.17).

### Testable ideas

The draft contains almost no quantitative rules, so these are mechanism-derived hypotheses, to be turned into pre-registered tests. All defaults below are mine, not the author's, unless stated.

1. ★ **Forced-flow reversal (uninformed liquidity demand then reversal)** - Condition: a large one-sided move that looks like price pressure rather than news. Proxy: daily US shares with a big return on no news and high volume but no earnings or filing event, or crypto perps with extreme taker-flow imbalance without a funding or price-level break. Rule: fade the move at the next close (shares) or next 8-hour block (perps), hold 1-5 days; the author's mechanism says dealers lay off to value traders, so price returns toward value. Source: TE ch.16.1, ch.20. Author's claimed evidence: none quantitative, a narrative of value traders buying discounted inventory. Fit: good for daily shares (the dealers' inventory story fits stocks with market makers, long-short with real-share costs, no swap); poor for CFDs (costs). Difference from failed families: it is conditioned on an identified uninformed demand, not on a generic gap fade; the news filter is the key difference and is also the main risk (without a news filter this collapses into short-term reversal).

2. ★ **Resiliency by liquidity: reversal strength depends on resilience** - Same event definition as 1, but conditional on measured illiquidity (Amihud-style |return|/dollar volume from our daily data). Prediction from ch.16.1.3: reversals are larger and more reliable where value traders are fewer? (The draft says resilient markets absorb more flow with less price change; we need to test the opposite sign in thin stocks, where impact is large and deviation is larger.) Test: sort events into illiquidity terciles; expect larger deviation and stronger reversal in the least liquid tercile, before costs; then check whether costs eat it. Source: TE ch.16, ch.19. Evidence: none given. Fit: daily shares good (23,700 names, but costs rise with illiquidity); this interaction is a falsifiable refinement of idea 1. Difference: tests where an effect should die (cost-aware).

3. ★ **Crypto perp taker-flow imbalance vs spread/dealer layoff** - Mechanism: market makers on perps carry inventory after one-sided taker flow and must lay off, so price drifts back after extreme one-sided flow, except when the flow is informed (shown by funding or open interest moving with it). Rule: when 8-hour taker buy minus sell volume ratio is at its extreme decile and funding has not moved, fade the next 1-3 periods; if funding and open interest rise together (informed), do not fade or follow. Source: TE ch.13, 14, 16 (informed vs uninformed flow). Evidence: none quantitative. Fit: good, we have prices, funding, taker flow; costs are fees plus funding. Difference from our passed Strategy 20 (weekly taker-flow long-short sort): shorter horizon, conditional on informed/uninformed split, and a reversal rather than a cross-sectional momentum-of-flow sign. Careful: Strategy 20 may already capture this sign at the weekly horizon, so test only at short horizons and report the correlation to Strategy 20.

4. ★ **Dealer inventory skew signal in index and FX CFD M1 data** - Mechanism: a dealer with a long inventory offers lower, a dealer with a short inventory bids higher (ch.13), so after a run of same-direction aggressive flow, quotes lean in the same direction (adverse-selection shift) and then partly revert. Our proxy: M1 close-to-close signed run lengths and range; rule: after N consecutive same-sign M1 candles with expanding range, fade at the next candle close with a time stop of k minutes. This is a spread-bounce/transitory-component test (ch.14). Evidence: none. Fit: poor for FTMO costs (spread would eat any bounce; likely falsified quickly), but cheap to run and gives a clean measurement of the transitory component. Difference: it targets bid/ask bounce and inventory, not patterns or session rules. Use only as a diagnostic, expect the cost wall.

5. **Block-trade acceleration and anticipation** - Mechanism: traders who know a block is coming trade ahead (same side) or withdraw liquidity (opposite side), so price pre-moves before the block (ch.15.2.2, ch.11 shop-the-block). Daily proxy: abnormal volume days in shares followed by continuation for 1-2 days versus reversal; the draft predicts the pre-move is anticipation (a cost to the block initiator, a gain to fast followers). Test continuation after volume spikes that are explained by large single prints (we do not have prints, so only volume spikes). Evidence: none. Fit: poor to medium (proxy is weak). Difference: needs volume, not a price pattern; but risks overlapping with our dead momentum families.

6. **Forced seller windows from margin calls and stops (crash dynamics)** - Mechanism: after a sharp drop, margin calls and stop-loss orders trigger more selling and order anticipators front-run it (ch.28); the price over-shoots and reverses once forced sellers are done. Rule: after a drop of more than X ATR in a day with a volume spike, buy the next open (shares) or the next day's low-volatility close (indices); stop beyond the day's low. Evidence: none. Fit: medium on CFD indices, but this is a classic dip-buy family likely to have been partly tested; the contribution is a defined trigger (volume plus large drop) and a short window. Difference: conditioned on liquidity stress, not on a plain gap or breakout.

7. **Index list-change forced trading** - Mechanism: cap-weighted funds must buy additions and sell deletions on the effective date (ch.23); divisor changes. Test around index additions/deletions of US shares (S&P and Russell reconstitution dates need external lists we do not have in the given data; only partially available). Evidence: none in the draft (the real book discusses it). Fit: poor without constituent-change dates; a research item for data acquisition. Difference: an explicit forced counterparty, distinct from the spent month-end index flow test.

8. **Round-number / price-clustering liquidity** - Mechanism: limit orders cluster at round numbers; clever traders place orders just beyond them (ch.5). Test: M1 or daily CFDs, proximity of price to round numbers and reversal or stall. Evidence: none quantitative. Fit: poor (CFD cost wall, and likely a pattern-family variant). Difference: marginal. Low priority.

9. **Energy futures storage-constraint volatility** - Mechanism: low-storage commodities have price spikes when inventories drop (ch.20). Test: EIA contracts 1-4 curve slope (backwardation) plus inventory proxy -> volatility forecast and spread between contracts. Evidence: only the 9-day / 18-day storage figures. Fit: good data match (EIA contracts 1-4), more of a volatility than a directional test. Difference: not roll-yield (spent GSCI roll test), but a volatility-state forecast; could be used as a filter rather than a strategy.

10. **Open-call or closing-call overreaction** - ch.5 mentions that continuous markets open with a call and restart with one after halts, but the draft gives no rule. Idea left open: daily shares, open price vs prior close and subsequent intraday reversion; we only have daily bars, so test only open-to-close vs close-to-open return split by size of gap and volume. Fit: poor (gap fade family already failed). Listed for completeness.

(Starred: 1, 2, 3, 4.)

### Warnings / pitfalls
- Uninformed traders lose "simply because they trade"; a retail-sized strategy without a named counterparty is probably a loser after costs (ch.14, 8, Part VI intro).
- A move that looks like uninformed price pressure may be informed flow (news, insiders), and dealers cannot tell either; a reversal rule that fades informed flow loses repeatedly (ch.13, 16, 29). Any reversal test needs an explicit informed-flow filter and a no-news screen, and should report both the reverse-fade loss tail and the hit rate.
- Reading volume: many causes (hedging, rebalancing, gambling); misread volume leads to wrong trades (ch.8).
- Bluffing and price manipulation exist, and thin small caps are the preferred target (ch.12); a model that buys price/volume spikes in small caps buys the bluffer's exit liquidity. Exclude microcaps or treat spikes as potentially manipulated.
- Winner's curse and adverse selection for any liquidity-supplying strategy: you get filled mostly when you are wrong (ch.16). In backtests this shows as fills that are too favorable: use realistic fill assumptions, not touch-fills.
- Free entry and exit erodes any observed profit; edges decay as others copy (ch.1).
- Performance skill vs luck: sample selection bias and unavoidable factors (market beta) fool evaluations; separate alpha from beta (ch.22).
- Spread and impact are costs of immediacy and are largest exactly when reversal ideas trigger (stress, wide spreads, thin depth), so estimates of costs from average spreads are too low in the event windows.
- The draft is incomplete and has no data; every idea above is a hypothesis from the author's reasoning, with no evidence quoted. Do not treat the book as support for effect sizes.
