> Reading notes, own words, made 2026-10-16 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

> Cited as JK with the print page. The PDF in 00_Literature/Trading is named Option_Volatility_n_Pricing_-_Sheldon_Natenberg.pdf but contains this Kaeppel book; Natenberg's own book has not been read.

# Notes: Jay Kaeppel, *The Option Trader's Guide to Probability, Volatility, and Timing*

**Real identity of the book:** The PDF was labelled Natenberg's "Option Volatility & Pricing", but the text is Jay Kaeppel, *The Option Trader's Guide to Probability, Volatility, and Timing*, a "Marketplace Book" published by John Wiley & Sons (Wiley Trading Series), New York, copyright 2002, ISBN 0-471-22619-X. Foreword by Thom Hartle. 20 chapters + epilogue + 2 appendices (about 270 pages). The data in it is from 2000-2001 (US single-stock options, IBM/AOL/Intel etc., some futures options). Page numbers below are the book's printed pages.

## Overview
- A practical, beginner-to-intermediate guide to listed-option strategies. It is NOT a quant text: no backtests, no statistics on edge, only worked example trades (one trade per strategy, each chosen because it worked out).
- Core message: option outcome depends on (1) probability of reaching break-even, (2) volatility level (cheap vs expensive premium), (3) time decay, (4) a market-timing opinion, (5) real-world friction (bid-ask, assignment, commissions). Decide risk first ("what is my worst case, what is my plan?"), reward second.
- The author's rule set: buy premium when implied volatility is low (rank 1-3), sell premium when it is high (rank 8-10). Write a plan with explicit entry, profit exit and loss exit before every trade, then follow it.
- Eight strategy chapters (12-19) each give a recipe with delta, volatility, days-to-expiry and exit rules; these are options-only and are summarised briefly below.
- Relevance for us: we have no options data and trade spot CFDs, so most of the book (pricing, Greeks, spreads, assignment, order placement) does not transfer. What does transfer: (a) how to measure and rank volatility (percentile of own history, moving-average + SD bands on a volatility series, short/long volatility ratio), (b) converting volatility into probabilities of price reaching a level by a date (normal/lognormal), used for stop and target placement, (c) the idea of conditioning strategy choice on a volatility regime, (d) the "forward-return hit-rate test" for entry signals, (e) friction/spread realism, (f) exit-planning discipline (pre-defined stop, partial profit, trailing stop of half the peak profit, do not hold out for the last dollar).
- Stance of author: cautious, risk-first, "90% of option traders lose" (p. 3, an estimate, no source). Admits timing is a wild card and that most traders overrate their timing (p. 120).

## Chapter notes

### Ch 1 - Introduction (pp. 1-19)
- Estimates that 90%+ of option traders lose money long run (p. 3, unsourced). Wants a structured, objective plan; "no holy grail".
- Process: identify criteria with the best probability; build confidence by defining when to use a strategy, when to enter, exit at profit, exit at loss; then have discipline to follow (pp. 5-6).
- Risk curve idea: plot P/L versus underlying price for several dates, not only at expiry. Break-even and probability of profit come from the volatility of the underlying (IBM example: option needing +4.2% had 39% chance, p. 8).
- Two case studies (ratio spread on coffee with "91% probability of profit"; synthetic long S&P with "80% probability") show that a high probability of profit at expiry hides a large interim loss risk if the market moves early. Lesson: ask "how bad can it get before expiry and what will I do", not "how likely is a profit" (pp. 12-18).
- "Bad things happen to the best traders": gaps against you, long chop, buys filled at the high, size up after wins then a big loss, stop trading after losses then miss the winner (p. 10). Avoid the big hit; address risk before reward.

### Ch 2 - Basics of Options (pp. 21-35)
- Definitions only: call, put, strike, premium, intrinsic vs extrinsic (time) value, ITM/ATM/OTM, naked vs spread, historic vs implied volatility, over/undervalued. Historic volatility explained as the expected +/- percentage move over 12 months (p. 25).
- Example: a far OTM IBM call needed a +24% move to break even, an ITM call needed +1.9% (pp. 27-28). OTM options = more leverage, much lower chance of profit. Not relevant to us beyond the intuition.

### Ch 3 - Reasons to Trade Options (pp. 37-46)
- Three uses: leverage a directional view, hedge a holding (covered calls), profit from neutral/ranging markets (calendars, straddles, butterflies, verticals). Compares payoffs of stock vs options. Options-only; no transfer.

### Ch 4 - Option Pricing (pp. 47-53)
- Black-Scholes inputs: price, strike, rates, days, volatility. Only volatility is unknown; usually the historical standard deviation of price changes is used. Volatility 10 to 50 raises an ATM 33-day call from 0.93 to 5.69 (Table 4.1, p. 50).
- Theory is moot against real bid/ask: the real quote matters more than model fair value (p. 52-53). Near-the-money options are priced closest to the model because they are most liquid.

### Ch 5 - Time Decay (pp. 55-62)
- Premium decays at an accelerating rate toward expiry (IBM 63-day ATM call: -5.9% first week, -29% in the second-to-last week, Table 5.1, p. 57). Buyer's break-even drifts away and probability of reaching it falls (43% to 34% over the option life, Table 5.2, p. 62).
- Options-only. Transfer in spirit: a holding cost (our swap) that works against long holding periods; the exact analogy is weak.

### Ch 6 - Volatility (pp. 63-80)  [high relevance]
- Historical (statistical) volatility = standard deviation of the underlying's price changes over a window (example: 20-day). It swings widely, so the author smooths it: a 500-day moving average of the 20-day HV with bands at +/-1.5 standard deviations (Fig 6.1B, p. 65). Used to see extremely high or low volatility.
- Implied volatility = the volatility that makes the model price equal the market price (needs a computer). Different strikes/months have different IV (skew; OTM puts and nearer months often higher). Single daily IV per stock: (a) average of ATM call and ATM put of the nearest month with more than 2 weeks left, (b) average of all options, (c) compromise: all months, strikes within 2-3 of ATM. Method matters little if consistent (pp. 67-69).
- **Relative volatility rank (p. 69-72):** collect the last 2 years of daily IV readings, sort, cut into 10 deciles. Current reading in the lowest decile = rank 1 (cheap); highest = rank 10 (expensive). Same raw level (IBM 50 vs Merrill 45) can be rank 10 versus low, so use rank, not level. Rank is computed per instrument against its own history.
- Strategy filter (p. 72-73): rank low -> buy premium; rank high -> sell premium. "Buying premium when vol is high and selling when low are low-probability trades."
- Skew: pattern of IV across strikes; try to buy the cheap-IV option and write the rich-IV option against it (pp. 73-74).
- Why it matters: at the low end of IBM's IV range (30) an April 90 call cost 8.80 (needs +4.7%, 41% chance); at the high end (55) it cost 13.44 (needs +9.9%, 32% chance) (Table 6.4, p. 77).
- Vega effect: longer-dated options react more in points to IV changes; if IV falls 55 -> 30 a July ATM-ish call loses about 36%, a February one 31% (pp. 77-79).
- The author asserts IV mean-reverts within a range (he trades the 2-year rank), but gives no statistics; mean reversion of volatility is assumed, not demonstrated.

### Ch 7 - Probability (pp. 81-97)  [high relevance]
- Option buyers almost always have under 50% probability of profit at expiry; writers over 50% (because of time premium). Trade-off: buyers get big payoff/low probability, writers get small payoff/large tail risk (pp. 81-82).
- Delta approximates probability of expiring ITM (delta 33 = about 1 in 3 chance), rough, "not mathematically correct" (p. 89, 96).
- **Probability analysis (pp. 91-95):** with the underlying's historical volatility, compute the probability that price is above/below a target on a date. Example output (Fig 7.6, p. 93): price 49.12, vol 44.49%, 42 days, upper target 59.09 -> probability of reaching 11.03%, lower target 41.04 -> 11.68%, probability of closing between 77.29%. A two-standard-deviation move over the 42 days = 63.89 up or 34.36 down (so 1 SD for 42 days is about 44.49% x sqrt(42/365) x price, which fits). The tool is a standard lognormal calculator.
- Straddle comparison shows the trade-off: wider break-evens = lower chance of profit and a much larger zone of 100% loss.
- Correct use: estimate probability of profit before entering; but once in, manage by dollars and stops, not by the entry probability. A 90% trade still needs a plan for the 10% (p. 96).

### Ch 8 - Market Timing (pp. 99-106)  [high relevance for timing methods]
- Four situations: (1) move in a direction within a specific period, (2) direction but no time frame, (3) big move but unknown direction, (4) range-bound / no move.
- Situation 1 test (p. 100): develop an entry criterion and measure the percentage of cases where price is higher x days later (test many x). Example claim: 70% higher after 5 days would be "very powerful". Also notes a specific time frame removes worry about volatility and time decay if the hold is short (5 days).
- Example system (Fig 8.1, p. 101-102): S&P 100 (OEX): moving average defines trend, Wilder's RSI identifies pullbacks against the trend for entries; exit after 7 trading days or an overbought/oversold reading of another momentum oscillator. No performance stats given.
- Situation 2 (Fig 8.2): trend-following buy-calls/puts signals on Intel; hold until the signal reverses.
- Situation 3 (p. 103-105): consolidation tends to be followed by a trend ("stocks trend for a while, consolidate, then trend again"). A proprietary oscillator reading above 90 or below 10 signals an upcoming trend with unknown direction; 6 of 7 signals on AOL were followed by a move large enough to pay a straddle. Quiet-market measures he lists: ADX, **short/long historical-volatility ratio (e.g., 6-day HV divided by 100-day HV)**, and **days since the last x-day high or low**.
- Situation 4 (p. 105): ADX/DMI above 75 = overbought, likely consolidation (Conseco example: between a >75 reading and a fall below 50 the stock went sideways/down). Also support/resistance bracketing for neutral trades.
- Summary: "market timing is a quest for the holy grail"; entirely different methods suit short-term vs long-term (p. 106).

### Ch 9 - Trading Realities (pp. 107-116)  [relevance: costs/execution]
- Exercise/assignment and automatic exercise at expiry can leave you with an unplanned stock position; deep ITM short options get assigned (parity rule of thumb). Options-only.
- Bid-ask: market orders buy at ask, sell at bid. Example: buy 10 options at 4.88 ask, immediately sell at 4.50 bid = -7.7% (about 375 dollars) before commission (p. 113). Typical option spreads: 0.06-0.25 under 1.00; 0.25-0.375 for 1-10; 0.375-1.00 above 10 (Table 9.2). A stock quote spread of 0.4% vs an option spread of 16% (p. 116).
- Limit orders: "get in at your price, get out at the market" (p. 113). Danger of a limit order: you miss the move. Danger of market-on-open: a gap inflates the fill (call bought at 17 instead of 7 after a 10-point gap, p. 114-115). Choose by confidence in imminent move and probability of profit.
- Also: methods that need more time per day than you have are fatally flawed (p. 107). "Well-established relationships can suddenly stop working completely and permanently" (p. 107).

### Ch 10 - Important Concepts to Remember (pp. 117-129)
- Recap and a "how to lose money" list: only buy cheap OTM options; ignore time premium; assume timing is good enough to beat everything; scan every instrument; comfort in "limited risk" (in the short run an option can lose more on the way down than it gains on the way up, p. 124).
- Keys to success: buy options with mostly intrinsic value; write options mostly time premium; fixed set of strategies; trade liquid options; have a plan; "use a timing method with as high a winning percentage as possible" (p. 129); leverage must be judged with probability (50:1 leverage at 5% chance is worse than 10:1 at 50%, p. 126).
- Filtering advice (p. 123): narrow the universe first, e.g., list instruments whose IV is at the low end of its range for buying strategies, or at the high end for writing strategies.

### Ch 11 - Overview of Trading Strategy Guides (pp. 131-137)
- Two selection variables: volatility (low/high) and directional vs neutral bias. Matrix (Table 11.1): low vol + directional = naked option or backspread; low vol + neutral = calendar or long straddle; high vol + directional = sell vertical spread or naked put; high vol + neutral = covered call or butterfly.
- Each strategy chapter lists: when to use, entry, profit exit, loss exit, example result. Exit criteria are guidelines, not hard rules, but fixed rules prevent emotional errors (p. 137).

### Ch 12 - Buy a Naked Option (pp. 139-150)
- Rules: only when a significant directional move is expected; delta 50 or more (buy ITM); lower IV is better, and the higher the IV the more ITM / shorter dated; at least 30 days to expiry. Mistakes: relying on timing alone, buying only OTM, buying high IV, buying short-dated.
- Example JDSU puts, IV rank 6: bought deep ITM March 65 puts (delta -72, 44% chance of profit). Stop: exit if the stock exceeds the recent resistance (64) or after 2 weeks before expiry. Profit: sell half when the oscillator is oversold, rest by the date. Result +104%, author warns it is a showcase trade.
- "Great paradox": the best single-trade payoff comes from far OTM options; the best long-run result comes from avoiding that (p. 150).

### Ch 13 - Buy a Backspread (pp. 151-164)
- Write 1 ITM/ATM option and buy more (e.g., 2:1, 11:5) OTM options, ideally at a credit; aims to profit from a big move with protection if wrong, and from a volatility rise. Enter at low IV; use long-dated options; exit before expiry (max loss at expiry if price closes at the long strike).
- Exit rule worth noting (p. 161): compute a **2-standard-deviation move for the holding period from historical volatility (5.64 points for 90 days on a 15.69 stock)**; close the trade if price pierces either 2-SD level, or after 3 months. This is a volatility-based stop/target scheme. Example result +1443.

### Ch 14 - Buy a Calendar Spread (pp. 165-177)
- Neutral; sell near-term, buy far-term same strike. Conditions: short option IV at least 15% above the long option IV; relative vol rank below 6 (ideally 1-2); short leg at most 45 days; delta 35-65; range-bound underlying with support/resistance. A fall in IV is deadly for the long leg; a rise helps strongly.
- Exits: exit if short leg time premium falls to 0.125, or open loss over a set dollar amount (about half the max). Example: AOL put calendar, +1300.

### Ch 15 - Buy a Straddle (pp. 179-190)
- Enter at low IV (rank 1-3), after an extended consolidation (a market that has been in a narrow range for months "is likely to break out"), delta neutral, with at least 74 days to expiry so you can hold 60 days before the last two weeks. Probability of profit is the lowest of all strategies (example 27%).
- Exits: stop at half the max loss; take half off if one leg doubles, then trail a stop at **half of peak open profit**; or a fixed target (20% of premium). Warns the position can sit at a loss for weeks and psychologically it is hard to hold; do not stop out too early, do not overstay. Example +1050 in 14 days.

### Ch 16 - Sell a Vertical Spread (pp. 191-200)
- Sell OTM credit spread when IV is high (rank 10), short strike delta 40 or less, 60 days or less, short strike beyond a visible support/resistance. 60%+ of OTM options expire worthless (estimate, p. 191).
- Risk/reward of 1:2.5 (win 725, lose up to 1875) -> stop at loss equal to max profit; take profit at 80% of max profit ("do not hold out for the last dollar": once most of the profit is made, the remaining reward no longer pays for the remaining risk, p. 199-200). Example +600.

### Ch 17 - Sell a Naked Put (pp. 201-209)
- Only for stocks you want to own; sell OTM put when IV rank is 10 and near support; delta 0 to -50; 60 days or less. If assigned, risk the amount saved versus buying outright as the stop. Warns of overnight gap risk on bad news. Example: expired worthless, +360.

### Ch 18 - Write a Covered Call (pp. 211-221)
- Write OTM calls (delta 50 or less, under 60 days) against held stock when IV rank is 10 and the stock is overbought after a sharp rally and expected to pause. Limits upside and gives only limited downside protection. Suggests writing against only part of the position (e.g., 8 of 10) to keep upside. Example +380.

### Ch 19 - Enter a Butterfly Spread (pp. 223-235)
- 1:2:1 call (or put) butterfly, middle strike ATM/slightly OTM, when IV is high and the stock is range-bound with support/resistance, 60 days or less (ideally 30). Use limit orders, watch commissions (3 legs in, 3 out). Exit at first good opportunity with a set profit (500 on 406 risk); close if the short leg's time premium shrinks to 0.125-0.25 to avoid assignment. Example +778.

### Ch 20 - Placing Trades (pp. 237-246), Epilogue (pp. 247-249), Appendix A PROVEST (pp. 251-254), Appendix B (pp. 255-264)
- Order-entry procedures for brokers (phone/online) per strategy. No content for us.
- Epilogue: "real trading is different from paper trading or system development" (p. 248); decide exit criteria when you enter; narrow to a handful of strategies instead of dabbling.
- PROVEST = Probability, Volatility, Expiration, Skew, Timing. Table A.2 summarises per-strategy criteria (same as chapters 12-19).
- Appendix B: exchange lists, brokers, commissions of 2001 (about 15-35 dollars + 1-2.5 per contract), option volume tables. Irrelevant.

## Topic tags

### trend
- Trend-following signals are used only as a timing input for option buying (Ch 8, MA + signal reversal). No rules, parameters or results given.
- Observation (unproven): markets alternate between trending and consolidating; a long consolidation raises the chance of a new trend (pp. 103-104, 183).

### breakout
- Straddle logic: after an extended narrow range ("Reader's Digest traded in a 3-point range for 3 months and has a history of narrow range then breakout", p. 183) buy a big-move bet. Quiet-market measures: low short/long volatility ratio, ADX, days since the last x-day high/low (p. 105). Candidate for a "volatility compression -> breakout" filter on our data; not tested by the author.

### mean-reversion
- Mean reversion of volatility is the foundation of the filter "IV rank high -> sell, low -> buy" (p. 72-73). Stock mean-reversion: pullback in a trend entered with RSI (Fig 8.1); overbought ADX/DMI above 75 -> expect consolidation (Fig 8.4). No quantified edge.

### momentum/oscillators
- Wilder RSI pullback-in-trend entry, exit after 7 days or an opposite-extreme oscillator reading (p. 101). ADX/DMI above 75 = overbought, below 50 = reset (p. 105). A proprietary non-directional trend-onset oscillator (>90 or <10; 6 of 7 AOL signals paid). No parameters beyond these.

### patterns
- Only support/resistance levels used as stop locations and strike placement (resistance at 64 for the put stop; support at 80.06 behind the credit spread stop; trading ranges for calendars/butterflies). Double bottom + key reversal day used once (p. 154).

### intraday/sessions
- None. Everything is daily or longer. Notes that gap opens inflate a market-on-open fill (p. 114).

### seasonality/time
- Not covered, apart from option expiry effects (time decay accelerates in the last 2 weeks; avoid holding in that period).

### volatility  [main value]
- Historical volatility: standard deviation of price changes over a window (20 days used); annualised; expected one-year range of +/-HV (p. 25, 48, 63).
- Volatility regime tools: 20-day HV with a 500-day moving average and +/-1.5 SD bands (p. 64-65); 24-month decile rank of a volatility series (p. 69-72); short vs long HV ratio (6d/100d) (p. 105); ADX; days since last N-day extreme.
- Claim that volatility is range-bound and mean-reverting, so low volatility favours buying convexity (straddles, long options), high volatility favours selling (p. 72-73, 119). Note for us: that is about option prices; for spot CFDs the same ranking applied to realised volatility (ATR percentile) could condition position size or strategy choice, but the book gives no evidence on how price direction behaves per volatility rank.
- Volatility-to-probability conversion (pp. 91-95, 161): probability of price above/below a target at a date from a lognormal with the instrument's volatility; "2 standard deviations over the holding period" used as exit level.
- Implied volatility itself needs options data (we have none).

### stops-and-exits
- Philosophy: define stop, partial profit and final exit before entry. Types seen: dollar stop equal to max profit or half max risk; stop beyond a chart level that must be broken (resistance/support); 2-SD price stop and a 3-month time stop (backspread); time stop before expiry; partial exit when one leg doubles, then trailing stop at half the peak open profit; take profit at 80% of potential and "do not hold out for the last dollar"; fixed profit target (20% of premium, 500 on butterfly).
- Warns that cutting too fast on a long straddle is also a mistake; both over-stay and under-stay hurt (p. 190).

### position-sizing/risk
- Risk before reward; plan the worst case; avoid the single devastating loss (pp. 9-11). Reward/risk of 1:2.5 on a 68% trade means one max loss erases three winners, so cut at 1:1 (p. 197). Trade smaller or skip when probability is low (p. 129). No sizing formula.

### testing-and-robustness/overfitting
- Only the forward-return hit-rate test (p. 100): condition on an entry signal, measure the share of cases higher/lower x days later for several x. Everything else is anecdotal examples. Warns that rules are guidelines, and that setups that "worked once or twice" are not evidence (Foreword). Nothing on out-of-sample, costs of data-mining or multiple testing.

### costs/execution
- Bid-ask spread is a first-order cost; round trip at market costs the whole spread (7.7% on an option, p. 113). Use limits for entries, accept market for exits; limit orders risk missing trades. Gap opens inflate fills. Commissions on multi-leg trades can eat all of the profit. Directly mirrors our spread/slippage/swap issue: small expected edge per trade is destroyed by friction.

### psychology/discipline
- Plan in advance, follow rules, the emotional pain of watching a loss, overtrading/dabbling in many strategies, overrating own timing, size up after wins then big loss, stop after losses then miss the winner (pp. 4-5, 10, 120, 190, 248).

### portfolio/diversification
- Not covered. Only "do not try to track every market; narrow the list with a volatility filter" (p. 122-123).

## Testable ideas
(All are adaptations to price-only spot data. None is claimed by the author with statistics; all evidence below is "none given" unless stated.)

★ **Realised-volatility percentile regime filter** - For each instrument compute realised volatility RV = std of M5/M15/D1 log returns (or ATR/price) over N bars (author uses 20 days), then its rank within the last 2 years (R = 1..10 deciles, p. 69-72) or its z-score versus a 500-day MA with +/-1.5 SD bands (p. 65). Use R as a regime label and run every existing or new strategy per bucket (low / mid / high), for example only trade breakout/trend strategies when R <= 3 and only trade fade/mean-reversion when R >= 8, or reduce size when R is high. Evidence: none; the author uses it only for option pricing. Fit: good (computable from M1 on all 5 symbols; no cost impact; a filter, not a new entry). Differs from the failed strategies: it is a conditioning layer that can be applied to strategies 1-6, tested as "does bucket R explain the sign of expectancy", and the failure to find an edge in the whole sample may hide a regime split. Needs the robustness report (halves, share of profitable buckets) and a multiple-testing correction because we will test many buckets.

★ **Volatility compression -> expansion (squeeze breakout)** - Compute short/long realised-volatility ratio (author example: 6-day / 100-day, p. 105) and/or days since the last 20-day high or low and/or ADX. When the ratio is in its lowest decile (compression), place a stop-entry breakout of the compressed range in both directions (OCO), stop at the opposite side of the range, target 2-3R or time exit; for each instrument on 1h/4h/D1. Author claim: after a long consolidation a trend is likely (p. 103-105), 6 of 7 signals paid on AOL (options straddle, not comparable). Fit: good for gold/FX/indices on H1-H4 with a limited holding time (low swap). Differs from the opening-range breakout and from Kaufman breakout: the trigger is volatility compression (a regime state), not a fixed N-day high/low or session start. Risk: this is a form of breakout already partly tested, so it needs the compression state to add value over plain breakout.

★ **Normal-distribution (sigma-band) stop and target placement** - For any entry, set the stop and target as multiples of the instrument's expected move over the intended holding time: sigma_h = price x RV_annual x sqrt(h/365), with h in hours or days and RV from a 20-day window. Examples from the book: exit if price touches +/-2 sigma for the 90-day horizon, i.e., 2 x sigma_h (p. 161). Test variants: stop = k1 x sigma_h and target = k2 x sigma_h with k in {0.5, 1, 1.5, 2}; compare to the current fixed ATR-multiple stops. Because sigma_h is nearly proportional to ATR scaled by sqrt(time), the difference is mostly the time-scaling, which makes stops tighter for short holds and wider for long ones. Fit: good as a stop/TP parameterisation for all strategies; it also gives a no-edge baseline probability (random-walk chance of hitting a barrier) against which to judge an observed hit rate. Evidence: none beyond the worked example. Differs: not a new entry, an exit framework.

★ **Barrier-probability sanity check / expected hit rate** - For a given stop distance S and target distance T (in sigma units) a driftless random walk has P(hit T before S) = S/(S+T) in continuous time; and the probability of touching a level before a time h is about twice the probability of finishing beyond it (reflection principle; my addition, consistent with the book's finish-beyond tables in Ch 7). Use these as null-model references: if a strategy's win rate at 1R:2R is not above 33%, there is no edge before costs. Also use with the book's probability analysis to compute FTMO daily-loss and max-loss breach odds for a given risk per trade from the instrument's volatility (e.g., 5% daily limit versus daily sigma). Fit: good, no data needed beyond volatility; this is a testing/calibration tool, not a strategy. Differs: purely analytical.

**Forward-return hit-rate scan for entry signals** - For any candidate signal, measure for horizons x = 1, 2, 3, 5, 10 bars the share of cases in which the close is higher (or lower) x bars later and the mean return net of spread (p. 100). Author's yardstick: 70% hit rate after 5 days "very powerful" (an overstatement; we should compare with the unconditional rate and a shuffled null). Fit: good as a cheap first-pass screen before building a full strategy; the test is horizon-agnostic so it avoids stop/target overfitting. Differs: a screening method, replaces designing a full strategy for every idea.

**RSI pullback in the trend, 7-bar time exit** - Trend by a moving average (not specified; use a 50/200 or the strategy 4 SMA+band), enter when Wilder RSI (period 14, default; author does not give thresholds) pulls back against the trend, exit after 7 trading days or when a second oscillator reaches the opposite extreme (p. 101-102, Fig 8.1). Evidence: none (a chart only). Fit: moderate; daily bars on indices/gold hold up to 7 days -> swap, so prefer H1-H4 versions with a 7-bar... time stop translated to hours; poor if costs dominate. Differs: pullback entry with a fixed time stop rather than stop-and-reverse trend following; but closer to failed strategy 4 than to anything new. Low priority.

**Overbought ADX/DMI consolidation fade** - When ADX-DMI exceeds 75 (overbought) expect sideways/down until it falls below 50; use as a "stand aside / take profit" rule on trend strategies rather than a fade (p. 105, Fig 8.4). Parameters from the book only: 75 / 50. Evidence: a single chart. Fit: poor to moderate (indicator definition ambiguous: "ADX DMI index on a 0-100 scale"). Differs: a trend-exhaustion filter.

**Take-profit at 80% of the maximum and "do not hold out for the last dollar"** - For strategies with a fixed target, test an earlier target (80% of the planned R) and a trailing stop at half the peak open profit once +1R (from Ch 15, 16). Evidence: none, but an easy exit-structure test that interacts with spread costs. Fit: good, cheap to test as an exit variant on existing trade lists (but remember intrabar SL-first assumption). Differs: exit-only change, no new entry.

**Partial profit + half-peak trailing stop (position management)** - At +1R close half, then trail a stop at 50% of the peak open profit until the end of the session/day (p. 187). Tests whether skewed exits improve FTMO pass probability even if the expectancy is unchanged (variance reduction). Fit: good as a risk/exit module on any signal; differs: an exit overlay.

## Warnings / pitfalls
- The book has no statistics: no sample sizes, no out-of-sample, no costs of selection. Every "result" is one hand-picked successful trade per strategy; the author even says the showcase trade is not typical (p. 150). Do not treat the rule thresholds (delta, 15% IV gap, 74 days, rank below 6) as validated; they are rules of thumb from one practitioner.
- Probability of profit at entry is not a risk measure: a 91% or 80% probability trade can lose heavily before expiry; manage by loss limits, not by the entry probability (pp. 12-18, 96).
- Win-rate/payoff trade-off: writing high-probability trades gives reward/risk of 1:2.5 and requires strict stops (p. 197). Same logic applies to our fade/mean-reversion strategies with wide stops.
- Volatility estimates change and can fall right after you enter; volatility is not stable, historical volatility from a short window is noisy (20-day swings widely, p. 64). A 2-SD stop based on a stale volatility can be too tight in a vol spike.
- Gaps: a market-on-open order or a short position can be filled far from the planned level (pp. 114-115, 207); stops do not protect against gaps (we see this at index open).
- Friction: spread alone can be 8-16% of an option's price; for us the analogue is that tight stops make spread/slippage a big fraction of R (consistent with the failed gap fade).
- Overrating timing skill and dabbling across strategies are named as top reasons for failure (pp. 120, 122, 127).
- Normal/lognormal volatility assumes thin tails and constant volatility; real FX/index returns have fat tails and volatility clustering, so sigma-band probabilities (and delta as probability) understate extreme moves. The author concedes delta is only an approximation (p. 89). Treat these probabilities as a null reference, not a forecast.
- Most of the book is not transferable: no options data on our side, so IV rank, skew, vega, theta, assignment and spreads cannot be reproduced. Realised volatility is only a proxy for implied volatility (IV usually exceeds RV; the IV-RV gap is the option seller's edge and we cannot observe it).
