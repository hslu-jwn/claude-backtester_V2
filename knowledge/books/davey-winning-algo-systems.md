> Reading notes, own words, made 2026-10-16 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

> Cited as KD with the print page.

# Notes: Kevin J. Davey, Building Winning Algorithmic Trading Systems (Wiley 2014)

Read in full (text pp. 1-269). Page numbers = book pages. Everything below is paraphrased.

## Overview
- Practitioner book: the author (futures trader, 3x World Cup of Futures Trading top-2 finisher 2005-07 with a 48-bar breakout + RSI filter trend system, daily bars, ~9 futures) explains the factory-style pipeline he uses to produce tradable systems. He needs roughly 100-200 entry/exit ideas to find one worth real money (pp. 73, 244).
- Core pipeline (Fig 8.1, p.72): SMART goal -> idea -> limited testing (1-2 yrs of data, entry/exit/core/monkey tests) -> walk-forward on the rest -> Monte Carlo (1 yr of resampled trades) -> incubation 3-6 months -> diversification + position sizing -> live small -> monitoring with pre-written quit rules. Each step is a hard gate; failing strategies are scrapped, not patched (every patch is hidden curve fitting).
- Stance: simple (1-2 optimisable parameters per entry), logical edge ("if you cannot say what your edge is, you probably have none", p.150), costs always included, treat tested data as fragile ("burned" after each look), position sizing and psychology are icing; the strategy edge is the cake. No Holy Grail except diversification of uncorrelated systems.
- Weak spots for our use: futures world, dollar-per-contract thresholds, no formal multiple-testing correction (he uses "70% of parameter grid profitable" as a robustness heuristic instead), Monte Carlo is a plain trade bootstrap (iid assumption, he notes the serial-correlation caveat). The example euro system is only ~4 years of data and its live record was mediocre in the first 15 weeks.
- Part I (biography, chapters 1-4) skimmed: lessons are "pattern on a chart looks good only in hindsight", never average down / martingale / scale in against a position, do not test many markets and pick the best (optimising by market), contest wins mean little (position sizing), start with enough capital.

## Chapter notes

### Ch 5 - Testing and Evaluating a Trading System (pp. 43-52)
- "Too good to be true" rule: future results are almost always worse than historical; better backtest -> bigger expected degradation. Survivorship bias: only good systems get shown.
- Four result types: (1) full-sample optimised backtest (worthless, "bogus"), (2) out-of-sample (hold back 10-20% of data, usually the newest; params frozen forever), (3) walk-forward (many stitched OOS periods, his preferred), (4) real time (cleanest but slow; any rule change resets the clock).
- Treat any result not produced in your own account as hypothetical. Trust order: experienced DIY developer < broker/CTA signals < novice DIY < vendors.
- Walk-forward example picture: 4-year in-sample, 1-year out-of-sample, windows rolled forward (Fig 5.5).

### Ch 6 - Preliminary Analysis (pp. 53-59) - first screening report
- Ground rules: report must be walk-forward or live, not optimised; 5-10 years and 30-100 trades per rule in the system (4 rules -> 120-400 trades); no position sizing (1 unit per trade) for apples-to-apples; realistic commission and slippage must be in (he discards any report with zero costs).
- Costs lesson: optimising without costs favours systems that trade too often with tiny edge per trade (example: $25/trade x 1000 trades beats $50 x 300 until $25 costs are added; then 0 vs +$7,500).
- Thresholds (futures, per contract, walk-forward): net profit >= $5k/yr minimum, $10k+ preferred; profit factor >1.0 acceptable, <1.5 rarely survives later gates, >1.5 ideal; average trade >= $50 net; "Tharp expectancy" = (avg win*win% + avg loss*loss%) / |avg loss| (i.e. average R) > 0.10; commission ~ $5 round turn; slippage 1-2 ticks per round turn for market and stop orders, 0 for limit (assume 1.5-2 ticks for mixed); max drawdown should be much smaller than net profit (10k DD on 15k profit = alarm).
- Equity curve eyeballing: slope (~45 degrees ideal), flat periods short, drawdown depth/length proportional, no zero-drawdown fantasies, low "fuzziness" (daily noise).

### Ch 7 - Detailed Analysis: Monte Carlo (pp. 61-69)
- Method: resample the walk-forward trade list with replacement, build a one-year equity path with N = trades per year, repeat 2,500 times per starting equity (table over several account sizes). Needs trades on the same unit basis. Caveat: assumes independent trades; if serial correlation (Durbin-Watson check) use start-trade / moving-start analysis instead.
- Inputs: starting equity, "quit" (ruin) equity level, trades per year, trade list.
- Outputs and his pass levels (Table 7.1): risk of ruin (equity falls below the quit level within one year) < 10%, ideal 0-1%; median max drawdown < 40% (he accepts up to 40%; note traders tolerate only about half of the drawdown they claim); median annual return > 40-50%; return/max-drawdown (median return / median max DD, a 1-year Calmar) > 2.0 (the number he considers most important); probability of a profitable year reported too (89-97% in examples).
- Percentile choice is arbitrary: median DD for comparison, 95th/99th percentile for worst case.
- Small accounts: a positive-expectancy system ($200 win/$175 loss, 50/50, 2 trades/day) still has a large ruin probability if the start equity is only 1-2x the ruin buffer; ruin falls steeply with capital.

### Ch 8 - Designing and Developing Systems (pp. 71-77)
- Software makes it too easy to produce overfitted systems. Factory metaphor: ideas in, tests as machines, garbage bin outside, rare gold. Tips: write every idea down; no idea too silly to test; test even coding "mistakes"; try the opposite of a bad idea (careful, costs double); aim at 1-5 strategy ideas tested per week; if stuck, relax criteria temporarily to learn, then tighten again.
- Three explanations for a strategy that passes everything: true edge, overfit, or pure luck from testing many (scenario 3, he admits it cannot be ruled out). Defences: a logical reason for the edge, simplicity, no random indicator stacking, gentle optimisation.

### Ch 9 - Goals and Objectives (pp. 79-82)
- SMART goals (specific, measurable, attainable, relevant, time bound), then SMARTER (re-evaluate when unattainable). Example goal: one market, 50% annual return, 30% max DD, 45% win rate, defined process, 6 months. Wish list of non-core preferences (no overnight, <= 2 indicators, <= 2 trades/day, never adds to losers, fully mechanical).
- Goals are written before any testing so that failing systems are rejected without argument.

### Ch 10 - Trading Idea (pp. 83-92)
- Entry importance scales with how long you hold; for scalping a tick matters, for swing trades it does not. Entry tips: keep it simple (explainable in plain English, write pseudo code first), 1-2 optimisable parameters, think differently from the usual moving-average crossovers, start with a single condition and add only if it clearly improves.
- Exits: stop-and-reverse, technical exits, break-even stops (he finds they cut winners), stop-loss (if a far stop destroys performance, the entry is the problem), profit target (he tests targets plus a huge upper cap), trailing stops (many parameters).
- Markets: one-size-fits-all (more robust but harder) versus single-market (easier, can mix for diversification). Warning: testing 20-25 markets and trading only the best 5-10 is optimisation by market.
- Time frame: day trading is attractive but 9 out of 10 short-timeframe ideas fail; moving from 1-5 min to 60 min/daily nearly always improves results. Reasons: costs per move, more noise at small bars, tiny stops make entry precision critical, competing with HFT firms, and "fewer trades = less statistical confidence" caveat. Time-frame dilation (test 9, 10, 11 min bars) he finds unreliable because the number of bars per day changes.
- Data detail: settlement vs last price; he rarely uses daily highs/lows when history mixes pit and electronic sessions.

### Ch 11 - Data (pp. 93-101)
- Use as much data as possible (10 yrs for daily swing; 5-10 for intraday); minimum 30-100 trades per rule/parameter. Longer samples make development harder because the gross edge reverts to zero.
- Keep the data definition consistent across history (one standard session time applied everywhere); continuous contracts: non-adjusted show fake gaps, back-adjusted prices can go negative and make ratio/percent indicators change retroactively (never multiply or divide back-adjusted prices).
- Forex: each broker has its own prices, so changing broker invalidates tests. Limit and stop orders on bid-only data give phantom fills (winners fill in backtest but not live). Therefore he uses only market orders for forex and adds spread to every trade.

### Ch 12 - Limited Testing (pp. 103-114) - the screening stage
- Do not run the full history. Use 1-2 years (about 25% in the example) picked at random, not the crisis years, enough trades to be meaningful. Every extra test on a data set "burns" it; strategy B vs A chosen on the same data is itself an optimisation. Touch the data lightly.
- Entry testing, three ways (strip the exit so only the entry is judged):
  1. Fixed stop and fixed target (equal dollar amounts: a no-edge entry wins ~50% before costs).
  2. Fixed-bar exit: close after X bars (he used 1-5 bars). Good entries show profit almost at once; if profit only appears after 10+ bars, the entry is early.
  3. Random exit.
  Evaluation: win rate (random = 50%; 52-60% suggests a worthwhile entry) plus average profit per trade (trend entries have low win rates but big winners). Run a small parameter sweep and look at ALL results, not the best: pass if >= 70% of settings are favourable, discard if only a handful are.
- Exit testing: pair the exit with a generic entry of the same style (breakout for trend exits, RSI for countertrend), or with random entries; judge by overall profit and MAE/MFE rather than win rate.
- Core system test (entry + exit together, gentle optimisation, e.g. 10x10 grid = 100 runs): want >= 70 profitable out of 100. 30-70% is "no man's land": allow at most one or two added rules or filters, if no dramatic improvement scrap it. Below 30%: reverse the signals (George Costanza test) but remember costs apply twice: a -$50 net system with $30 costs is -$20 gross, reversed it is +$20 gross then -$10 net, so most reversals do not work.
- Monkey tests ("Monkey See, Monkey Do", pp. 109-114): 8,000 random runs each, matched to the strategy on trade count, long/short ratio, average bars in trade, same exit-at-end-of-day behaviour:
  - Monkey entry with the real exit; monkey exit with the real entry; monkey entry + monkey exit.
  - Pass: strategy beats ~90% of the monkeys on both net profit and max drawdown (about 7,200 of 8,000 runs worse).
  - Same test reused live: on the last 6-12 months (3 months if enough trades). If most percentiles fall to 60-70% be concerned; if most < 50% the edge is gone -> stop. Example: percentiles 99-100% in development, then 49-73% after a drawdown (borderline), then ~1-72% (edge gone, stop).

### Ch 13 - In-Depth Testing / Walk-Forward (pp. 115-128)
- No-parameter systems: a single historical run, no tweaking afterwards (swapping the pattern is optimisation too). Better: turn alternatives into one optimisable index parameter so the optimisation is explicit.
- Definitions: in period, out period, fitness function, anchored vs unanchored. Worked example: ES daily countertrend breakout, 5-year in-sample, 1-year out, net profit fitness, unanchored: optimised curve beautiful (+$55k over 10 years), walk-forward curve poor and chosen parameters jumped every year (7/17/600, 7/45/100, 49/7/600, 21/11/1000, 9/5/600) with OOS results -3.1k, -2.3k, +6.0k, -19.1k, +8.7k. Afterwards the optimised version went flat live while walk-forward stayed flat/negative as predicted: walk-forward is a harsh but realistic test, most strategies fail it.
- Settings guidance (must be fixed BEFORE the run, otherwise it is optimisation):
  - In period: enough trades per optimised input, 25-50 trades per input (e.g. 4 inputs -> 100-200 trades); 30 trades/input rule of thumb. Example choices: 4-5 years in.
  - Out period: 10-50% of the in period (1000-day in -> 100-500 day out); robust systems are not sensitive to this.
  - Fitness function: net profit most used (profit and low drawdown usually go together); alternatives are equity-curve linearity (R^2, tends to pick tiny-profit settings) and return on account (net profit / (max DD + margin)), but non-additive metrics (DD, ROA) break unanchored software walk-forward unless computed per window.
  - Unanchored (rolling window) preferred so old data does not dominate.
- Walk-forward efficiency in the usual sense (OOS/IS ratio) is NOT used; he compares the stitched walk-forward curve to goals and later to incubation.
- If the walk-forward fails, normally discard; relaxing goals or retesting different in/out windows is optimisation. If you must pick best in/out lengths, do it as a nested walk-forward: choose in/out on the early data (e.g. 2000-2008), then run the chosen pair on the last ~3 years untouched; if that fails, abandon.
- Build a single "walk-forward history strategy" (parameters switch by date) to get one continuous trade list. Beware that parameter switches mid-trade change swing trades, so test the stitched version.

### Ch 14 - Monte Carlo and Incubation (pp. 129-132)
- Monte Carlo on the walk-forward trade list; needs return/DD > 2.0, plus all Ch 7 thresholds.
- Incubation = wait 3-6 months before real money, check about monthly, treat as another OOS period. Reasons: euphoria after finishing, fresh look at the system, catches development errors and hindsight bias, tests whether you can live with its behaviour. Usually done paper/simulated, real money small only if fills are uncertain (limit orders, exotic bars).
- Red flags in a backtest he refuses to trust: buys at exact bar lows / sells at highs, limit orders filled merely on touch, exotic bar types (Renko, Kase, point and figure), same-bar entry and exit or stop/target so tight both can fall in one bar.

### Ch 15 - Diversification (pp. 133-138)
- Systems fail and sit in drawdowns; many uncorrelated systems give fewer fill problems, a smoother curve and are the closest to a Holy Grail.
- Design for diversification by changing two or three of: market, bar size, session, entry, exit. Example: two euro systems (night 105-min bars, small wins/large losses, limit mean reversion; day 60-min bars, rare large winners) on the same market.
- Measuring: correlation of daily returns (whole history and 6-12 month windows; low long-run correlation can spike in crises), R^2 of the combined equity curve (0.937 and 0.975 alone vs 0.982 combined), max DD of the combination, and Monte Carlo return/DD (2.2 and 5.2 alone -> 6.7 combined; probability of profit 89%/97% -> 98%). Daily results (not individual trades) must be combined for the Monte Carlo of a portfolio.
- Corollary: with diversification, individual systems can be "decent" rather than "super"; relax individual targets slightly.

### Ch 16 - Position Sizing and Money Management (pp. 139-146)
- No single best sizing method; risk and reward go together; sizing the winners cannot save a losing system but can ruin a winning one; testing 5-10 sizing methods and picking the best is itself optimisation (use Monte Carlo to compare). Martingale: wins almost always in the short run, ruin in the long run. Develop first with fixed size (1 contract), size afterwards (Andrea Unger disagrees: he develops with sizing in the loop so that smaller-loss setups get chosen).
- Start live at the smallest size, add size from profits.
- Fixed fractional formula: N = floor(x * equity / largest historical loss (walk-forward)). Choose x by Monte Carlo sweep: maximise return/DD subject to max median DD (45% in his example) and ruin <= 10%. Example x = 0.175 vs optimal-f peak at x = 0.32 (would give 67% median DD and 21% ruin). For multiple systems sweep each system's x jointly because of correlation.

### Ch 17 - Documenting the Process (pp. 147-153)
- Checklist spreadsheet per strategy (goals, idea, edge, markets, bar, test period, data, entry/exit, each limited test, walk-forward settings, Monte Carlo inputs and result, incubation, diversification, sizing, notes). Naming convention with version letters (many letters = too much tweaking). Separate list of loose entry and exit ideas.

### Ch 18 - Goals, Initial and Walk-Forward Testing (pp. 155-162) - the example system
- Goal: euro futures intraday, 50% annual return, median max DD <= 25%, return/DD >= 2, >= 55% winning days, <= 2 trades per day, 1 month of development. Data 2009-2013, limited test on 2009 only (about 25%).
- Both systems: stop <= $450 incl. costs ($17.50 per trade; 34 ticks), exit all at session end, entries are reversal (mean-reversion) limit orders.
  - Euro night (105-min bars, 18:00-07:00 ET, new trades only until 01:00): long limit at average(High, Nb) - ATRmult * ATR(NATR); short mirror (average(Low, Nb) + ATRmult * ATR). Profit target TRmult * TrueRange from entry. One entry per day, pick the order closest to price. Walk-forward parameter ranges: Nb 9-19, NATR 73-93, ATRmult 2.55-3.15, TRmult 0.51-0.71, stop 375-425.
  - Euro day (60-min bars, 07:00-15:00 ET): short limit at high + pipadd pips when the high is the highest high of Xb bars (3-5) and close < close Xb2 bars ago (Xb2 70-80); long mirror. Stop 225-425, target $5,000 (effectively none), exit at 15:00. One trade per day. pipadd 2-11.
- Limited-test results: night 82% of optimisations profitable (entry test), 85% core test; day 76% / 81%. Fixed-bar exit of 1-5 bars good; monkey tests passed. Walk-forward re-optimised regularly (code in appendices B, C; windows look like 6-12 months parameter sets).

### Ch 19 - Monte Carlo and Incubation of the example (pp. 163-174)
- Required start equity ~ $6,250 for ruin < 10% (stop-trading level $3,000). Day: median DD 23.7%, return 129%, ret/DD 5.45, ruin 4%, P(profit year) 94%. Night: DD 25%, return 52%, ret/DD 2.0, ruin 6%, P(profit) 85%. Combined (daily results merged): DD 25.8%, return 176%, ret/DD 6.6, ruin 5%, P(profit) 95%.
- Incubation: ~3.5 years walk-forward history (7/2009-3/2013) plus 5 months incubation. Match check by three methods: t-test of walk-forward vs incubation trade distributions (p ~ 0.56 that they do not differ; worried below 0.2), overlay histograms, and a visual equity curve to see whether a break appears where incubation starts. Better than walk-forward in incubation "does concern me a bit".
- Final checks: can reasonable position size be applied (a 50% win, +$5,000/-$3,000 system needs $20k for 6% ruin and $35k for <25% DD, per single contract: maybe untradable); correlation with existing systems (halve each size if highly correlated).
- Consistency from Monte Carlo: % of profitable weeks 59.6, months 74.8, quarters 86.2, years 98.8; define the minimum acceptable per period for your circumstances.
- Outlier dependence: removing the 20 days > $1,000 (of 614 days) leaves the system barely profitable; only 4-6 such days expected per year; 13.6% chance of 0-2 in a year. So take every trade.

### Ch 20 - Account and Position Sizing (pp. 177-185)
- Quit rule for the system: (A) 1.5x worst daily-basis walk-forward drawdown ($3,265 -> $4,898) and (B) 95th percentile Monte Carlo max DD ($5,082; 99th $6,512); average them -> quit at $5,000 single-contract drawdown, written down in advance. Minimum account = quit drawdown + exchange margin ($2,750) = $7,750, used $8,500 so that a second contract needs only ~+50%.
- Sizing: fixed fractional x = 0.175, BigLoss = largest daily loss $885 -> contracts table. Monte Carlo table (start equity $8,500): ff 0.1 -> median DD 22%, return 155%; 0.15 -> 32%/249%; 0.175 -> 38%/362%; 0.2 -> 44%/460%; 0.25 -> 54%/714%; fixed 1 contract -> 19.6%/141%. He distrusts a 362% median and looks at the return histogram. Unequal sizing (2:1) was worse.
- Always start live with 1 contract (finds code/slippage faults cheaply, keeps emotion low).

### Ch 21 - Psychology (pp. 187-193)
- Decide beforehand: when to start (after fixed N months of incubation regardless of the equity curve), what to do with an open position (his rule: enter if it is currently a loser or near break-even, skip if a big winner, wait for next signal), and when to quit (written rule examples: max DD, consecutive losers, loss per week/month, profit after X months, win rate below X, equity-curve MA break, SPC). Skipping or front-running signals invalidates the testing. Trade 3+ systems so no single one is micro-managed. After an operational error, just sync the position back with market orders.

### Ch 22 - Other considerations (pp. 195-201)
- One system per account, multiple brokers, backups, automate but stay attended, know where each order lives (local, broker, exchange). Futures roll: back-adjusted continuous contract does not lose the roll premium in P&L, cost is two spreads plus one commission (quick roll, leg-in roll, exchange spread roll; never limits on both legs).

### Ch 23 - Monitoring a Live Strategy (pp. 205-217)
- Bird's-eye equity chart with walk-forward + incubation + live in one colour-coded line; monthly summary on ONE-unit basis: return efficiency = actual / expected return (he sees 70-100% across strategies) and drawdown efficiency = 1 - actual DD / expected DD (100% ideal).
- Too-good-to-be-true early results and large month-to-month variance are warnings; most incubated strategies revert to their mean.
- Daily/trade performance cone: plot cumulative P&L against n*avg with bands n*avg +- sqrt(n)*sd*X (X = 1 or 2), or better, percentile bands taken from Monte Carlo (2.3% and 97.7% for "2 sigma", 10% line as a warning line). A winning system can stay under the lower band for a long time; falling below the 10% percentile line is the warning, below ~0 percentile (impossible under the model) is a stop. Track actual vs. predicted performance, with conservative cost assumptions so live is the same or better.

### Ch 24 - Real Time (pp. 219-231)
- Live diary of the euro systems: weeks 4/7/8/12 near the Monte Carlo 10% line (day count 18 days of trading in 7 weeks, 53% vs 60% normal); he keeps trading because his written quit is the $5,000 DD; an uncancelled limit order cost $550 (check statements daily); real fills were $400-700 better than the backtest because limit orders penetrating by zero ticks sometimes fill; week 13: twice-a-year review of "next best alternative" system; the system relies on a handful of big winners and had none in 15 weeks.

### Ch 25 - Cautionary tales (pp. 235-241) and Conclusion
- Character sketches; lessons: demo success is not real success, beware non-trading gurus, no one predicts markets, simple beats complicated, do not start with $500, back tests of vendors are garbage unless walk-forward/live. Conclusion: need 100-200 ideas per tradable system; strategies do not last forever; one in, one out (keep a pipeline of replacements).

### Appendix A - Monkey code (pp. 247-253)
- Baseline: after 2 down closes buy / after 2 up closes short at next open, ATR-based stop (ssl1 * ATR14 * point value, capped at $2,000), ssl1 reoptimised yearly (0.5-1.25). Random entry variant: each day trade with probability 0.47 (odds tuned to match trade count), long probability 0.4. Random exit: exit after random(2*holdbars) bars, mean hold 2.5 bars, optionally at close. Baseline stats for tuning: 430 trades in 1,165 days, 40% longs, average 2.5 bars.

## Topic tags

### trend
- His contest system: close = highest close of 48 bars, RSI(30) > 50 filter (short mirror), stops of fixed $1,000 / Y*ATR, target Z*ATR, wait 5 bars after a loss and 20 bars after a win, daily bars, ~9 uncorrelated futures; 100%/yr with 40-75% drawdowns; one trade made 95% of one year's profit. Trend following means long flat periods then a few big wins; hard psychologically (pp. 24-28).
- "Currencies tend to trend, so breakout may suit them; equities mean-revert with long bias" (p.87), as a prior only.

### breakout
- Simple X-day highest-close breakout was his base idea; countertrend variant used as walk-forward demo (sell X-day high close, buy Y-day low close, stop Z) and failed walk-forward (p. 118-121).

### mean-reversion
- Euro night/day reversal limit entries: fade a stretched average high/low by ATR multiple (night), or fade a new Xb-bar extreme if the longer Xb2-bar momentum points the other way, with a limit order several pips beyond the extreme to wait for one more thrust (day). Small wins/higher win rate (night) and rare big winners (day). Also baseline of "after two down closes buy" used in the monkey example.

### momentum/oscillators
- RSI(30) > 50 as a trend filter; X-bar momentum sign as a filter in the day system. No deeper treatment.

### patterns
- Head and shoulders: looks good only in hindsight, false signals dominate (pp. 10-12). Candlestick patterns mentioned only as a "no parameters" example.

### intraday/sessions
- 9 of 10 short-timeframe ideas fail; results improve on 60-min/daily. Session-defined systems: night session 18:00-07:00 ET (new trades until 01:00) and day session 07:00-15:00 ET with forced end-of-session exit; exit before the thin 15:00-17:00 period; one trade per day max for the day system. Keep session definitions constant across history.

### seasonality/time
- Not covered, apart from waiting-period rules (5 bars after loss, 20 after win) and picking test years at random but avoiding crisis years for the limited test.

### volatility
- ATR for stops and entry distance (ATR(14)-based stop in monkey example; ATR(73-93) multiple for night entries). Lower volatility reduced trade count of the euro day system ("volatility has been low", p.221). Possible temporary quit when markets are "super-crazy" mentioned, never implemented.

### stops-and-exits
- Always test entries with exits removed (fixed bar, fixed stop/target, random exit); exits tested with a similar-style generic entry or random entry; break-even stops cut winners; if a far stop kills the system the entry is the issue; profit target with a very large cap acts as "hold to session end"; stop of 34 ticks after costs both strategies; do not rely on same-bar stop and target fills.

### position-sizing/risk
- Fixed fractional with Monte Carlo selection of x (return/DD max subject to DD and ruin caps); quit drawdown = average of 1.5x worst historical DD and 95th percentile simulated DD; start equity sized so that ruin < 10%; start small, add from profits; account must cover quit-drawdown + margin; reward and risk are a team; optimal f (x = 0.32) rejected as too risky (21% ruin, 67% median DD). Traders realistically tolerate about half the drawdown they say they can.

### testing-and-robustness/overfitting
- Burned data; one look per data set; limited test on 1-2 random years; pass bar of >= 70% of grid profitable; <= 1-2 rules added; max 1-2 parameters per entry; walk-forward with pre-set in/out/fitness; nested walk-forward for window selection with last ~3 years untouched; monkey tests of entry, exit and both (8,000 runs, beat >= 90% on net profit and DD); Monte Carlo gates; incubation 3-6 months with t-test and curve comparison; cap on version letters; honest "100-200 ideas per winner" base rate; ideal: have an economic reason for the edge.

### costs/execution
- Always include costs; never zero; optimise net. $5 round turn commission, 1-2 ticks slippage for market and stop, 0 for limits, conservative bias (assume limit orders fill only when price trades through; real fills were better). Reversing a loser doubles the cost. Forex bid-only data creates phantom fills, so use market orders plus spread. Fewer trades are better for retail due to costs.

### psychology/discipline
- Write start rule, open-position rule and quit rule in advance; skip no signals; sync positions with market orders after errors; trade 3+ systems; keep a record of actual vs expected; remember events as they were.

### portfolio/diversification
- Diversify by varying market, bar size, session, entry and exit; test with daily-return correlation (full history and 6-12 month windows), R^2 of combined curve, combined max DD, Monte Carlo return/DD of daily-merged results. Combined 6.6 > 5.45 and 2.0 (single systems). Check new strategy correlation to live ones; if correlated, halve sizes. Twice-yearly replacement review.

## Testable ideas

### Ideas about process (most valuable for our bulk-testing plan)

★ **Entry-only screening battery (fixed-bar exits + random-exit comparison)** - For each candidate entry signal, strip the real exit and run (a) exit after N bars for N in a small set (he used 1-5 bars on 60-min bars; for us 1,2,3,5,10,20 bars on the signal timeframe) with costs; (b) fixed stop and target equal in R (1R/1R) for a ~50% random baseline; (c) exit at random times with the same mean holding time. Pass if win rate clearly above 50% (his heuristic 52-60%) and average net R per trade > 0 in >= 70% of the (parameter x hold-bar) grid. Source Ch 12 pp. 105-106 - claimed use: filters out most ideas fast; he discards most ideas here - fit: good, cheap with our M1 data and R-multiples; use net-of-spread-and-swap R and keep holds intraday to avoid swap - differs from failed strategies: it is a screening harness, not a strategy, and works on any candidate signal (sweep, FVG, gap, ORB, no-wick, etc.).

★ **70%-of-grid robustness gate** - For any rule with a small parameter grid (e.g. 10x10), require >= 70% of settings net-profitable on the limited sample; 30-70% = allow at most 1-2 added filters then retest, else scrap; <30% test the reversed signal with double costs. Source Ch 12 pp. 106-109 - evidence: his stated experience, no numbers beyond the euro example (76-85% in the passed systems) - fit: good, trivially added to our robustness report ("share of profitable variants" already exists; set the numeric gate at 70% and add the reverse-signal-with-double-cost check) - differs: this is a rule for accepting ideas, avoiding cherry-picking of the best cell.

★ **Matched-monkey test (random entry, random exit, both)** - Replace entry by random entry matched on trade count, long/short share and holding bars; same for exit (random exit time, same distribution of hold bars, same session end rule); 8,000 runs; require the real strategy to beat >= 90% of runs on net R and on max drawdown. Reuse live/forward: the last 6-12 months vs fresh monkeys; below 50% on most metrics = edge gone, 60-70% = warning. Source Ch 12 pp. 109-114 - evidence: example 99-100% in development, 49-73% then ~1-72% in the degraded phases which preceded a stop - fit: good and cheap; we already have random entries/fills in the Monte Carlo report, so add monkey exit and combined, matched trade count and long/short share - differs: judges the edge against randomness controlling exposure, not against zero.

★ **Hurdle pipeline with pre-registered gates** - Define in advance (docs spec) numeric pass/fail per stage: limited test on 1-2 random years (25% of sample) -> walk-forward on the rest (fixed in/out/fitness chosen before) -> Monte Carlo 1-year resample (ruin < 10%, median DD < ~40% scaled to FTMO limits, return/DD > 2, P(profit year) reported) -> 3-6 months incubation on MT5 data -> go live at minimum size. Record per-idea checklist with version letters. Source Ch 8, 12-14, 17 - evidence: ~100-200 ideas per winner - fit: matches our dev/test split (pre-2021-09-14 develop, MT5 data test once); the "incubation" equals our MT5 FTMO forward set - differs: process, not a strategy.

★ **Combined daily-result portfolio Monte Carlo** - To combine strategies, merge trades into daily R results (same day netted), resample days (block of whole days), compute median max DD, return, return/DD, P(profit year), and compare with each alone; first check daily-return correlation on the full history and on rolling 6-12 month windows. Source Ch 15, 19 pp. 135-138, 167-169 - evidence: ret/DD 2.2 and 5.2 -> 6.7 combined for two uncorrelated euro systems - fit: directly relevant for combining weak edges; our day-reshuffle Monte Carlo already exists, add correlation by window and "diversification gain" metric - differs: tests combination not a signal.

### Trading ideas (his example system and other rule sets)

★ **Euro-night style mean reversion: fade ATR-stretched average-extreme with limit order, session exit** - Rule: on each bar compute LongPrice = SMA(High, Nb) - ATRmult * ATR(NATR) and ShortPrice = SMA(Low, Nb) + ATRmult * ATR(NATR) (defaults Nb 9-19, NATR 73-93, ATRmult 2.55-3.15). Place a limit order at whichever is closer to the close; one trade per day, new entries only in the first part of a defined session (his: 18:00-01:00 ET for a 18:00-07:00 session). Exit: limit target TRmult * TrueRange (0.51-0.71) of the signal bar, stop <= ~34 ticks, close everything at session end (07:00 ET), 105-min bars. Source Ch 18 pp. 157-158, App. B - evidence: 82-85% of optimisations profitable, walk-forward, Monte Carlo ret/DD 2.0, 85% P(profit year); live first 15 weeks flat - fit: FX majors (GBPUSD) and XAUUSD intraday, no swap if flat before rollover (his night session is naturally flat by 07:00 ET), but limit order fill assumption must be penetration-based and the stop/target same-bar rule is critical (he warns about tight stop and target in the same bar); costs: spread on a market-exit and stops, limit entries at 0 slippage - differs: uses long-window (ATR 73-93) stretched distance mean reversion, limit-order entry beyond an extreme, forced session exit; none of the four failed strategies does this, but it is a fade of range extremes which overlaps in spirit with the gap fade (already no edge) and sweeps.

★ **Euro-day style exhaustion fade: new Xb-bar extreme against longer momentum** - Rule: on 60-min bars during 07:00-15:00 ET: if High >= highest High of Xb bars (3-5) AND Close < Close[Xb2] (Xb2 70-80), place a sell-short limit order at High + pipadd pips (2-11) for the next bar; mirror for longs (low <= lowest low of Xb and close > close[Xb2], buy limit at low - pipadd). One trade per day (no trade if one already happened), stop 225-425 dollars (~18-34 ticks), no target (cap 5,000), exit at 15:00 ET. Source Ch 18 p.158-159, App. C - evidence: 76-81% of optimisations profitable, Monte Carlo 129% return, ret/DD 5.45, 94% P(profit year); relies on 4-6 large winners per year - fit: FX/gold/indices intraday on 60m bars; we can test it with R multiples (stop R = distance), costs from spread table, flat each night so no swap; risk that profit is from a few outliers (removing 20 days of 614 killed it) - differs: counter-trend fade of short-term extremes beyond a long-lookback trend filter with limit entry beyond the extreme; our failed strategies were not "wait for one more thrust" limit fades.

**Two-down-closes / two-up-closes mean reversion with ATR stop (monkey baseline)** - Rule: after 2 consecutive down closes buy at next bar's open (after 2 up closes sell short); stop = ssl * ATR(14) with ssl in 0.5-1.25 (reoptimised yearly); exit via signal (short side) or stop; futures daily/swing. Source App. A p.248-249 (illustrative baseline only). - evidence: used only to demo monkey test (net profit 99-100% better than monkeys over 2007-2011) - fit: daily bars on indices, cheap to test as a simple benchmark; swap if held overnight - differs: very short-term daily mean reversion; our failures were trend/sweep/gap.

**Wait-after-win / wait-after-loss cool-down on a trend entry** - Entry: close = highest close of 48 bars with 30-bar RSI > 50 (mirror short); after a losing trade wait 5 bars, after a winning trade wait 20; exit: fixed $-stop, Y*ATR stop, Z*ATR target. Source Ch 3 p.24 - evidence: 148%/107%/112% contest returns with 40-50% drawdowns (not a clean test; he also admits market selection by hindsight) - fit: poor on our data (daily trend following with swap, cf. failed strategy 4) except as a filter test on re-entry timing - differs: cool-down logic only; likely same fate as strategy 4.

**Time-frame lift test** - For any intraday rule that fails on 1-5 min, rerun on 15m, 60m, 240m and daily with the same logic and compare; he finds almost every idea improves with larger bars because costs per move fall and noise falls. Source Ch 10 pp. 88-89 - evidence: anecdotal, "nine times out of ten" - fit: good screening step with our resample; need to keep swap in mind for holds past 17:00 NY - differs: a standing step, not a strategy.

**Reverse-the-losers test with correct costs** - If a rule is clearly negative net (< 30% of grid profitable), test the mirrored signal and add double costs (gross loss reversed, minus full cost again). Source Ch 12 pp. 108-109 - fit: good; our sweep/no-wick/gap failures may show gross negative edge worth checking (but he warns reversal rarely survives costs) - differs: tests the contrarian version of the failed strategies.

## Warnings / pitfalls
- Testing the same data repeatedly "burns" it: choose A vs B on one sample = optimisation; keep most data untouched for walk-forward/incubation; revisions raise the chance of fit (track version letters).
- Selecting the best of 20-25 markets, best in/out windows, best sizing method, or best fitness function is optimisation too; set walk-forward settings before running; use nested walk-forward if you must choose.
- Optimised backtests degrade; walk-forward is harsh but unbiased; most strategies fail it, and his base rate is 100-200 ideas per winner (scenario 3, lucky pass, cannot be excluded).
- Costs: optimising without costs favours overtrading; zero-cost reports are invalid; limit orders filling only on touch overstate results; same-bar stop/target, exotic bars and fills at exact highs/lows are red flags; bid-only forex data creates phantom fills; reversals pay costs twice.
- Few trades or outlier dependence: need 30-100 trades per rule; the euro day system had ~20 days > $1,000 of 614 and was barely profitable without them, so every signal must be taken; live results lagged for 15 weeks.
- Monte Carlo assumes iid trades and a stable distribution (use moving-start analysis with serial correlation); percentile bands rather than normal assumptions; the median hides tails; a median return that looks absurd (362%) is a warning not a target.
- Small accounts: ruin probability is high even for positive expectancy; traders tolerate about half the drawdown they claim; reward comes with hidden risk that never shows in the equity curve.
- Diversification correlation can jump in crises; verify rolling-window correlation.
- Short timeframes: more noise, bigger relative costs, precise entry required, HFT competition; prefer fewer trades and larger bars.
- Data consistency: same session definition throughout history, same broker data for test and trade, no ratios on back-adjusted series.
- Do not tweak after a poor start: a positive-expectancy system can sit under the lower band for a long time; use pre-written quit rules and percentile bands, not feelings.
- Statistics can be bent (his statistician anecdote): pre-register hypotheses and gates.
