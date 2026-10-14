> Reading notes, own words, made 2026-10-14 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

# Aziz, "How to Day Trade for a Living" - notes

(Page numbers are not in the extracted text; locations are given as chapter / section. Text line refs in brackets, e.g. [L3731], refer to the .txt file.)

## Overview
- Short beginner book on discretionary US stock day trading by Andrew Aziz (Bear Bull Traders). Core thesis: you are only as good as the stocks you trade; trade only "Stocks in Play" (news catalyst, gap, high relative volume), keep a few simple setups, manage risk first, never hold overnight.
- Nine setups in Ch 7: ABCD, Bull Flag momentum, Bottom/Top Reversal, Moving Average trend (9 EMA), VWAP, Support/Resistance, Red-to-Green (previous-day close), Opening Range Breakout (ORB). All are described in loose, chart-reading terms with screenshots of single trades; thresholds are often vague.
- No backtest statistics at all. Evidence is single anecdotes, plus the claims "all strategies in Ch 7 show positive expectancy if executed properly" and "about 30% of my trades lose" (Ch 3). No sample size, no costs study, no out-of-sample test.
- The author explicitly says trading is discretionary, "indicators only indicate, they do not dictate" (Rule 10), and that mechanical systems lose to institutions. So the rules are NOT meant to be coded; coding them is our interpretation.
- Heavy dependence on stock-only inputs: pre-market gap scanner, float, relative volume, catalyst news, short interest, Level 2, volume-based VWAP. Few of these exist in our M1 price-only CFD data.
- Value for us: a clean list of intraday price-structure setups (VWAP, ORB, prev-close, 9 EMA, S/R, reversal after 5+ candles), the time-of-day rules, a 2:1 minimum R and 2 percent max risk framework, and a daily-loss/give-back rule.

## Chapter notes

### Ch 1 - Introduction
- 16 percent of day traders profit after 6 months (Massachusetts court records, as cited). Learning curve 6-8 months typical; simulator for >= 3 months before real money.
- Day trading is a business; startup capital, education; "average successful day trader makes $500-1000 per day" (anecdotal).

### Ch 2 - How Day Trading Works
- Rule 3: never hold overnight; close at a loss rather than convert to a swing trade. (Fits us: avoids swap.)
- Long and short both allowed; some setups long only (Bull Flag, Bottom Reversal), Top Reversal short only, others both.
- Retail edge vs institutions: free to not trade; must not overtrade. Algorithms/HFT (over 60 percent of volume per author) make choppy noise; avoid stocks dominated by them.
- Rule 4: ask whether the move is market/sector-driven or has its own catalyst. Reversals do not work in stocks trending with a weak sector.
- Time of day: most volume and volatility 9:30-11:30 NY; he trades mostly the first 1-2 hours and stops once the daily goal is hit (about 10:30). Avoids pre-market (thin).

### Ch 3 - Risk and Account Management
- Three legs: psychology, strategies, risk plan.
- Rule 5: minimum reward:risk 2:1 ("with 2:1 I can be wrong 40 percent of the time and still make money" - note: with 2:1 breakeven win rate is 33 percent, so he is conservative). Example MOH short: entry 50.00, stop 50.40 (above VWAP), target 48.80 = 3R. Same setup entered later at 49.60 with stop 50.20 and target 48.80 = 1.3R, rejected; he says do NOT tighten the stop to improve the ratio, stop must sit at a logical technical level - skip the trade instead.
- 2 percent rule: max risk per trade 2 percent of equity (he suggests 1 percent for the conservative case). Share size = max dollar risk / stop distance per share. If the logical stop implies more than the cap, take fewer shares or pass.
- Own numbers: 25k account, 800 shares, daily goal 500 USD (2 percent/day on his account), later says day traders aim for 0.5-1 percent of account per day.
- Losses: many small stops; "most good day traders have few losses larger than 30 cents/share"; "winning trades should work right away" (if flat for a few minutes in reversal trades, exit).
- Rule 6: your only job is risk management. Rule 8: guerrilla style, 2-3 trades a day, boring is good, overtrading = commissions + risk.
- Psychology: hide the P&L column, a good day = rule-following day, stress -> stop trading/go to simulator.

### Ch 4 - Finding stocks
- Stocks in Play (Rule 7): high RELATIVE volume stocks with a catalyst, independent of market. Examples of catalysts: earnings, FDA, M&A, contracts.
- Float classes: low float (<5M shares, price <10 USD) = only Bull Flag momentum long; medium float (5-500M, 10-100 USD) = all strategies, mostly VWAP and S/R; large (>500M) = mostly MA trend and reversal, and only with a catalyst.
- Pre-market Gapper scan criteria: gap >= 2 percent pre-market; >= 50,000 shares traded pre-market; average daily volume > 500,000; ATR >= 0.50 USD; fundamental catalyst; short interest < 30 percent. From ~4000 stocks to ~8 candidates, he watches 2-3.
- Intraday "volume radar": gapped >= 1 USD, ATR > 0.50, relative volume >= 1.5, avg daily volume >= 500k. Bull Flag scanner: high RVOL, low float. Reversal scanner: stock with >= 4-5 consecutive candles in one direction and extreme RSI. Scanners cost ~100 USD/month.
- Watchlist frozen by 9:15 NY; nothing added later; plan written on note cards (if-then statements).
- Some stocks have meaningful range only on days with abnormal volume/gap (AAPL example); trade AAPL only on those days.

### Ch 5 - Tools
- Chart contents: candles, volume, 9 EMA, 20 EMA, 50 SMA, 200 SMA, VWAP (blue, "most important day trading indicator"), previous-day close, manually drawn daily S/R. 5-min main chart, 1-min watched too.
- Orders: avoid market orders; uses marketable limit orders (ask+5 cents / bid-5 cents). Leverage 1:4 (up to 1:6 offshore). Commissions: IB under 1 USD/trade vs 4.95 retail; spreads widen in fast moves (up to 2 USD).

### Ch 6 - Candlesticks
- Bullish/bearish body = who is in control; spinning top and doji (also shooting star = long upper wick, hammer = long lower wick) = indecision, possible reversal only with confirmation and a level. He rejects named multi-candle patterns and diagonal trend lines as subjective; uses only horizontal levels.

### Ch 7 - The nine strategies (precise rule extraction)
General: 5-min chart main, 1-min as second view; stop is always at a technical level; take half at first target and move stop to breakeven; remainder trails until sign of weakness. Position handling example (800 shares in 10-50 USD range): buy 400, add 400 when in profit, sell 400 at first target + stop to breakeven, sell 200 at next target, keep last 200 until stopped. Never average down (he lost a margin call on LABU; Amaranth example). Scaling in only into winners.

**1. ABCD** (long shown; mirrored implied). A = start of surge, B = new high of day, C = pullback low that holds above A (support), D = new move toward/above B. Enter near C once it holds (not at D, not at B), stop = loss of C, sell half at D (about B or beyond) and move stop to entry, exit rest when a new 5-min low prints (sign of exhaustion). Volume spikes at B and D. Works because many retail traders watch it. No numeric rule for "holds".

**2. Bull Flag momentum** (long only, low float under 10 USD). Pole = several large candles up; flag = small sideways candles. Entry: price breaks above the high of the consolidation candles; stop = below the consolidation low; sell half on the way up, stop to breakeven; exit rest on lost steam. Only trade 1st and 2nd consolidation, never 3rd+. Works on 1, 2, 5-min; breakout bar should come with higher volume. Only at the Open; never mid-day or close. Needs fast execution/scalping; he does not do it much himself.

**3/4. Bottom / Top Reversal.** Setup (all together): (1) >= 5 consecutive 5-min candles in one direction (scanner uses >= 4); (2) 5-min RSI > 90 (top) or < 10 (bottom) (scanner highlights >80 / <20); (3) price at/near a significant intraday-daily support (bottom) or resistance (top); (4) indecision candle (doji/spinning top/hammer/shooting star) or a strong opposite-colour body; high volume at the reversal point. Entry (long): first 1-min or (preferably) 5-min candle to make a new high after the extreme (short: first to make a new low). Stop: low of the previous (red) candle or low of the day (short: high of previous candle / high of day). Targets: next S/R level, or VWAP / 9 EMA / 20 EMA whichever closer, or exit when a new opposite 5-min extreme prints. Time stop: if price just goes sideways for a few minutes after entry, get out. After profit: stop to breakeven, then trail to the low of the last 5-min candle. Example: BBBY short 44.10, VWAP target 43.10 (stop at high of last candle / day high). Not valid in a stock trending down with its sector. Needs the extremes; slow drifts excluded.

**5. Moving-average trend (9 EMA).** Stock trending after the morning (about 11:00 NY on), 1-min or 5-min chart. Long: price consolidating above the 9 EMA (sometimes 20 EMA) and the EMA holds as support; buy as close to the EMA as possible; stop 5-10 cents below the EMA or (better) a candle CLOSE below it; ride until a 5-min candle closes the other side; no trailing stops (he watches by eye); may take half profit when far from EMA and re-add on a pullback to the EMA. Check that yesterday's behaviour on the same timeframe respected that MA. False breaks happen on low volume - require a close. Best mid-day and into the close (ends about 3 PM when pros dominate). Short mirrored (AMAG sold 31 to 23 under 9 EMA).

**6. VWAP.** Core idea: above VWAP buyers in control, below sellers. Wait 10-15 min after the open (first 5 min are chaos). Long: price pulls back to and holds above VWAP (support found), buy close to VWAP; stop = 5-min close below VWAP; target next S/R or round half/whole dollar; sell half near first target, stop to breakeven. Short: price rallies to VWAP, fails to break it (rejection) on the 5-min chart, short near VWAP; stop = 5-min close above VWAP. If price chops around VWAP with no interest, stay out. Also uses VWAP as stop for other setups (MOH short entered on a 5-min close below VWAP, SRPT short after two 5-min candles below VWAP, entry 18.20, target 17.00-17.40, exit on new 5-min high). Best at the Open and at the Close (and mid-day).

**7. Support/Resistance.** Horizontal levels only, from the daily chart, drawn at wicks/extremes (day-trading style, opposite of swing trading where congestion edges count). Guidelines: indecision candles at the level; round and half dollars matter; use recent data, only levels near the current price; a level is a zone (5-10 cents on a 20 USD stock); must show a clear bounce; more touches = stronger; high volume at the level confirms. Entry on the 5-min chart when an indecision candle forms at the level, as close to the level as possible; stop = 5-min close beyond the level (KMX: stop below 47.93); target next S/R level (sell half, rest at the next, stop to breakeven); if no level, round/half dollars. Short mirrored. If no clear level exists, skip the stock.

**8. Red-to-Green / Green-to-Red (previous-day close).** For a stock that gapped: price moving toward the previous close with rising volume; target = previous close; entry usually from VWAP or the nearest technical level; stop = break of that level (VWAP/MA/support); take all at target; if in profit move stop to breakeven (should work immediately). Examples: MNK short from VWAP 47.80 to prev. close 46.52 (+1.20 vs risk not stated); CUDA short VWAP 24.40 to prev. close 23.81.

**9. Opening Range Breakout (ORB).** Opening range = high/low of first 5 min (alternatives 15, 30, 60 min; he now prefers 15 or 30). Condition: the opening range must be much smaller than the stock's daily ATR (PG example: range 0.05 vs ATR 0.79; if the first range is near or above the ATR, skip). Prefer mid/large caps; not low-float gappers. Entry: after the first range closes, when price breaks the high (long) or low (short). Stop: close below VWAP (long) / break above VWAP (short). Target: next important technical level (daily S/R, daily MA, previous close); if none, exit on the first new 5-min low (long) / new 5-min high (short). ORB is an entry signal only, exit must come from the other tools. ELF example: gapped up 19 percent, short on break of opening range below VWAP to the daily level 28.62.

**Other / meta**
- Time-of-day table: Open 9:30-11:00 (his most profitable, most size; Bull Flag + VWAP best); Mid-day 11:00-15:00 (worst for him, lower size, tight stops; Reversal, VWAP, MA, S/R); Close 15:00-16:00 (directional, trade with the pros; VWAP, S/R, MA). Never Bull Flag outside the Open.
- Give-back rule: max loss of 30 percent of the profit earned in the Open during mid-day + close, otherwise stop (or switch to simulator).
- Develop one strategy first; "must trade a written strategy with historical data verifying it" (said, but no method given).

### Ch 8 - Step by step
- Example SRPT (gap down 14.5 percent, float 36M, ATR 1.86): waited 10 min, VWAP short on 5-min close below VWAP at about 18.20, covered 17.40 on new 5-min high, +650 USD.
- Process: routine, watchlist by 6:15 PT, written plan, execute without second guessing, journal.

### Ch 9 - Next steps
- Seven fundamentals; simulator at real size 3 months, then small real size. If-then planning example (DKS): "if price cannot push above VWAP in first 15 min, short to previous close 48.10; if it sells off to prev close, go long back to VWAP; if it pushes above VWAP on high volume, long to next daily resistance 53.25; if 53.25 rejects, short back to VWAP". Questions to ask: who controls price, stock stronger than the market, bid-ask spread, etc.
- Remainder: discipline, mentoring, journaling, glossary, "11 rules" (all restated in the text above; none are numeric beyond 2:1 and 2 percent).

## Topic tags
- trend: 9 EMA trend ride (mid-day), ABCD/bull flag continuation, VWAP side as trend filter. Trend lines rejected as subjective.
- breakout: ORB (5/15/30/60 min) with range < ATR filter; bull flag breakout of consolidation high.
- mean-reversion: Bottom/Top reversal after >= 5 one-way candles + RSI extreme (90/10, scan 80/20) at S/R; VWAP rejection fades; previous-close magnet (Red-to-Green).
- momentum/oscillators: only RSI (5-min) as an extreme filter, not as a trigger; EMAs 9/20, SMAs 50/200 drawn but only the 9 EMA is traded.
- patterns: ABCD, bull flag, doji/hammer/shooting star as confirmation only. Named candle patterns rejected.
- intraday/sessions: everything keyed to NY cash open 9:30; windows Open / Mid-day / Close with different strategy sets.
- seasonality/time: first 5 min chaos, wait 10-15 min before VWAP trades; ORB lengths; mid-day lowest quality.
- volatility: ATR >= 0.5 USD filter; opening range must be smaller than ATR; relative volume >= 1.5; range-expanding days only (gap days).
- stops-and-exits: stop at structure (VWAP close, consolidation low, level), never tightened to improve R; half off at first target + breakeven; exit on first opposite 5-min extreme; time stop for flat reversal entries; no trailing stops in the MA trend trade.
- position-sizing/risk: max 2 percent per trade, size = risk / stop distance, min 2:1 R, 2-3 trades per day, scale only into winners, never average down, 30 percent give-back rule.
- testing-and-robustness: none provided (anecdotes only). Says to use written strategy verified with historical data, simulator for 3 months.
- costs/execution: avoid market orders, marketable limit; commissions matter for overtrading; slippage and spread widening in fast markets.
- psychology/discipline: large part of the book; hide P&L, process over money, stop when stressed.
- portfolio/diversification: not covered (watch 2-3 stocks only).

## Testable ideas (for NAS100 / US500 / XAUUSD, FX; price-only M1 data)

Substitute for VWAP: no real volume. Options (a) session-anchored equal-weighted mean of typical price (H+L+C)/3 or close from the session start (anchored at NY 9:30 for indices, or at the 0:00/London 8:00 for gold/FX), (b) time-weighted average, (c) later MT5 tick volume (tick count per M1 bar is a decent volume proxy; get it from FTMO/MT5, not histdata). Note the index CFD volume in histdata is absent; tick volume must be collected separately.
Substitute for "Stocks in Play": (i) gap vs previous close (cash close 16:00 NY to open 9:30 on indices; for CFDs the 24h feed makes the "gap" the move from 16:00 to 9:30, measured from the data), (ii) pre-open range expansion relative to ATR (a price-only relative-activity proxy), (iii) ATR(daily) percentile. Float, short interest, news catalyst, Level 2 have NO substitute.

1. ★ **NY-open ORB with range-vs-ATR filter** - Open range = high/low of first N minutes after 9:30 NY (N = 5, 15, 30, 60; author now prefers 15/30). Trade only if range < k x daily ATR(14) (author: "much smaller"; try k 0.1-0.3). Entry: first close/break beyond the range after the range closes; stop: the opposite side of the range (cleaner than VWAP) or session-mean/VWAP-proxy close; targets: 1R/2R fixed, prior-day close, prior-day high/low, or first opposite 5-min extreme; flat at 11:30 or 16:00 NY (no swap). Source Ch 7 Strategy 9. Evidence: anecdotes only. Fit: good (NAS100/US500 are the mid/large-cap-like instruments the author says suit ORB; intraday only so no swap; ~2-3 trades/week at most per symbol). Difference from failed: strategy 2 was a sweep of a session level; this is a plain breakout with a volatility-compression filter and ATR-based expectation, and tests several window lengths.
2. ★ **Session-mean (VWAP-proxy) rejection / hold** - Compute anchored average from NY 9:30 (equal-weight typical price, or tick-volume weighted later). After 15 min: long if price pulls back to the mean from above and a 5-min close holds above it (price must have been above for >= 1 bar); short on a failed test from below. Stop: 5-min close through the mean (+ buffer in ATR); target: prior-day close, prior high/low, or 2R; half at 1R + breakeven. Source Ch 7 Strategy 6. Fit: index CFDs do respect the intraday mean; without volume weighting the line is smoother but similar. Risk: the author's evidence is single anecdotes and the 5-min-close stop is large relative to the entry, so R is often < 2 unless entry is very near the line (this is exactly the rule "do not tighten the stop"; test whether the 2:1 filter leaves enough trades). Differences from failed: no liquidity-sweep logic, a mean-reversion-to-trend anchor.
3. ★ **Previous-close magnet (Red-to-Green) on indices** - On days where the open (9:30) gaps away from yesterday's 16:00 close by more than x% or x ATR: after the first 15 min, if price fails at the session mean in the gap direction, fade toward the previous close; target = previous close; stop = beyond session mean / opening range extreme; time stop 11:30 or 15:00 NY. Also the reverse: gap-fill continuation. Source Ch 7 Strategy 8. Fit: gap fill statistics for NAS/US500 are a known effect and testable cheaply, price-only; the CFD "gap" must be defined using the 16:00 NY close of the cash session (data is 24h). Differences: not a sweep; uses prior-close level.
4. ★ **Exhaustion reversal (5+ candles, RSI extreme, level)** - On M5: >= 5 consecutive same-direction candles (or >= 4) AND RSI(14) on M5 > 90 / < 10 (scanner level 80/20) AND price within a zone around a prior-day high/low/round number; trigger: first M5 candle that makes a new high (bottom) / new low (top) after an indecision or opposite candle; stop at the extreme of the move (low of the day / previous candle); target: session mean (VWAP proxy), 9/20 EMA, or next level; time-stop 3-4 bars if flat. Source Ch 7 Strategies 3-4. Fit: poor-to-OK on indices (RSI 90 on M5 is rare in indices; may need RSI 80/20 and 3-4 candles to get samples); gold/FX could provide more events. Intraday, no swap. Differences: contrarian; none of the four failed strategies is an exhaustion fade.
5. **9 EMA trend ride (M5/M1), mid-day** - Between 11:00 and 15:00 NY: price above rising 9 EMA for >= n bars and pulls back to touch the 9 EMA; entry on first M5 close back above / bounce candle, stop 1 candle close below the EMA (or 5-10 ticks), exit on first M5 close beyond the EMA; optional half off at 2R and re-add. Source Ch 7 Strategy 5. Fit: simple, easy to test. Likely weak (EMA ride in noise, costs per trade), but cheap. Differences: Kaufman trend following was daily-scale with a 3 ATR stop; this is an M5 scalp-trend with a tight EMA-close stop.
6. **ABCD / flag continuation on trend days** - Strong-move detection (use ATR), A to B surge, C pullback low above A held for >= m bars, enter near C, stop below C, half at the B level (leg symmetry: D = C + (B - A)), rest on first new 5-min low. Source Strategy 1/2. Fit: imprecise to code, need defined thresholds; works on gold/indices only on trend days. Medium-low priority. Differences: overlaps somewhat with the BOS/FVG logic of strategy 1 (pullback entries), but without zone logic.
7. **Previous-day high/low and round-number support/resistance bounce** - Horizontal levels from prior-day wicks (high/low), prior weekly extremes, and half/whole round numbers (e.g., 100/50 points on NAS); zone = fraction of ATR (author: 5-10 cents on a 20 USD stock = 0.25-0.5 percent); entry when an indecision candle forms at the zone on M5; stop = M5 close beyond; target = next level; half at first level. Source Strategy 7. Fit: round numbers matter on indices and gold. Differences: the failed session-zone strategy used session boxes with sweeps; here levels are daily extremes and round numbers. Moderate priority.
8. **Time-of-day filters as a general overlay** - Test existing strategies per window (NY open 9:30-11:00, mid-day, last hour). Aziz's claim: Open = best, mid-day = worst, the close trends. Use as a check on strategy 2 results and as an overlay for any new idea.
9. **Daily give-back / stop rules for risk module** - max 2 percent risk per trade (FTMO fits: 1 percent or less), 2-3 trades per day, stop for the day when more than 30 percent of the morning profit is lost, daily profit goal 0.5-1 percent. Directly implementable in risk/ simulation. Fit: good (prop-firm compatible).
10. **Gap-direction filter + VWAP side** (hybrid) - Only trade the first-hour direction consistent with the pre-open gap and session mean; conditions "price can't hold above mean in first 15 min => short to prev close". Based on the DKS if-then example. Fit: good on NAS/US500.

## Transfer judgment: what needs stock-only inputs
- Needs stock inputs, no substitute: float, short interest, news catalyst, Level 2, pre-market volume scan, relative volume (RVOL) as such, low-float momentum (Bull Flag micro-caps). Drop these (strategy 2 low-float bull flag, "Stocks in Play" selection).
- Price-only substitutes: RVOL -> range or ATR expansion vs last 20 sessions; gap % -> open vs previous 16:00 NY close; ATR filter -> same; VWAP -> anchored session mean (or tick volume weighted later); float class -> not applicable (indices are mega-cap by construction, so Aziz would assign them to ORB, MA trend, reversal strategies).
- Indices are exactly the "mega cap, institution-dominated" class he says is hard to day trade except on abnormal volume days; his own advice is therefore ORB (mid/large cap), MA trend and reversals there, and only on gap/event days. A price-only "event day" filter (large overnight gap or high pre-open range) is the key missing piece and the main thing to test.
- Gold/FX have no cash-open gap; session opens (London 8:00, NY 8:00-9:30) can be used as the ORB anchor; "previous close" would be the 17:00 NY rollover.

## Warnings / pitfalls
- No statistical evidence anywhere; all examples are hand-picked winners. Do not infer expectancy. Several rules are vague (what "holds support" means, what "much smaller than ATR" means, "strong" volume).
- He says himself these methods are discretionary; automated mechanical versions "lose to algorithms" (his view) - treat as hypothesis generation only.
- Stops placed at structure produce wide stops relative to targets; the 2:1 rule then removes many trades (he skips them). Our tests must include that filter or R will be inflated/deflated.
- Retail self-fulfilling edge claims (many traders watching VWAP/levels) cannot be verified and may decay.
- Mid-day thinness, spread widening in fast markets; on CFDs, spread and slippage at the 9:30 open can be large (model costs at open separately).
- Averaging down and holding losers overnight are the cited account killers; our R-based testing avoids both by design, but the swap/overnight rule (Rule 3) should be kept: all ideas above are flat by the NY close.
- RSI > 90 on M5 is extremely rare in index CFDs; threshold calibration needed or it yields no samples.
- Author's own numbers on risk: 2 percent max per trade; real FTMO limits (5 percent daily, 10 percent total) are far more restrictive than his daily goals imply - sizing should be much lower (0.25-1 percent).
