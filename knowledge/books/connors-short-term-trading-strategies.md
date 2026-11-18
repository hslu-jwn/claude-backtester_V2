# Larry Connors and Cesar Alvarez, *Short Term Trading Strategies That Work* (The Connors Group, 2009)

Short: **STS**. Cite by printed page (`STS p.N`). Read 2026-11-18 by Codex; PDF in the library folder Tier 3.

The book studies short-term trading in US stocks and equity indices, principally buying pullbacks in an established uptrend and exiting into strength. It presents historical tests of intraday limit entries, RSI and volatility filters, stops, exits, and overnight holding. Its explanations often appeal to fear and selling pressure; they generally do not identify a counterparty obliged to trade. (STS pp. 31–37, 40, 43–47, 75–76, 99–100, 112–114.)

## Testable ideas

- **Overnight equity-index return** (STS pp. 35–38): Buy SPY at each close and sell at the next open; compare with buying at the open and selling at the same close. The stated mechanism is compensation associated with assuming overnight risk; the book identifies no counterparty that must trade. For 1995–2007, the figure reports **−70.88 SPY points** for the daytime leg; its extracted overnight figure is not reliably legible, so no overnight size in bp per event is given. A QQQ comparison covers 1999–2007. Data: adjusted daily opens and closes, distributions, and execution costs. Venue: US ETFs or an appropriately costed index future. **NEW**.

- **Intraday extension of a stock pullback** (STS pp. 40, 43, 46–47): Among stocks above $5, above their 200-day simple moving average and averaging at least 250,000 shares over 100 days, find a 10-day closing low; place a buy limit the next day 5% below the prior close, then exit five trading days later. The book attributes reversals to panic selling and subsequent buying or short covering, rather than a specified forced flow. For 1995–2007 it reports **63,154 trades**, **59% correct**, and **+1.97% average gain per trade**. Data: point-in-time US share universe, daily OHLCV, corporate actions and realistic limit fills. Venue: real US shares. **MAPS TO: daily reversal**.

- **Double 7s** (STS pp. 75–76): Buy SPY when it closes at a seven-day low while above its 200-day moving average; sell when it closes at a seven-day high. Holding period varies. The claimed basis is a short-term pullback followed by recovery; no compelled counterparty is identified. From SPY inception in 1993, the book reports **153 trades**, **0.85% average profit/loss** and **80.4% correct**; the table does not specify an ending date. Data: adjusted daily SPY prices and execution costs. Venue: US ETFs or costed index futures. **MAPS TO: daily reversal**.

- **NYSE breadth-filtered market reversal** (STS pp. 99–100): When SPY is above its 200-day average, its two-period RSI is below 50, and NYSE TRIN has closed above 1.00 for three consecutive days, buy at the close; exit at the close when SPY’s two-period RSI exceeds 65. TRIN uses advancing and declining issues and their volumes; the book treats persistent high readings as an oversold condition, without identifying a required counterparty flow. For 1995–2007 it reports **90 trades**, **558.30 total S&P points**, **75.56% correct**, and an average hold under four trading days; no bp-per-trade size is given. Data: historical NYSE breadth and volume, SPY prices, and costs. Venue: US ETFs or costed index futures. **MAPS TO: daily reversal**.

## Method notes

- **Compare exits on the same entry concept.** For stocks above their 200-day average that closed at a 10-day low and were entered on a next-day 5% limit, the book reports 63,101 trades for each exit: **1.97%** average P/L for a five-day hold versus **2.65%** for a close above the five-day moving average. Different holding times and portfolio exposure matter when comparing them. (STS p.114.)
- **Test stops against the entry and market in question.** In one stock pullback test, no stop produced **0.58%** average P/L over 236,237 trades; a 5% stop produced **0.20%** over 286,991 trades. The book says it had not established the conclusion for futures or forex. Different trade counts also limit a simple per-trade comparison. (STS pp. 32, 34.)
- **Treat a high win rate on few signals cautiously.** The VIX-stretch example has 33 trades, despite reporting 84.85% correct; the book itself notes the small number of occurrences. (STS p.93.)
- **Check close-based execution.** Several rules both use that day’s closing indicator and assume a fill at that same close; a practical test needs a signal available before the order deadline or a later executable fill. (STS pp. 76, 100.)
- **Resolve source inconsistencies before implementation.** The cumulative-RSI discussion calls it a three-day cumulative RSI, while the rule specifies the sum of the past two days’ three-period RSI. The book also gives **4.35%** and **4.33%** for the 10% intraday-limit result on adjacent pages. (STS pp. 47–48, 103–104.)

## Verdict

The overnight return comparison is the only item above marked **NEW**, but it does not establish a required counterparty flow or provide a reliably readable overnight bp-per-event figure, so it does not meet the requested standard for a research card. The larger quantified pullback results map to the already judged daily-reversal family. (STS pp. 35–38, 46–47.)

