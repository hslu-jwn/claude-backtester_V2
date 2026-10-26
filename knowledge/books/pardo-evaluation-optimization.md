# Robert Pardo, *The Evaluation and Optimization of Trading Strategies*, 2nd ed. (Wiley 2008)

Short: **RP**. The ebook text has no page numbers, so cite by chapter: `RP ch.11`.
Source PDF: `X:\Dokumente\Archiv\Trading\The_Evaluation_and_Optimization_of_Trading_Strategies_-_Robert_Pardo.pdf`.
Notes written 2026-10-23, in our own words. Focus: what the **application** must do. The book has
almost no strategy content.

## Overview
- A practitioner's handbook for the whole development pipeline. Its core message: optimization is
  fine if done properly, and **walk-forward analysis (WFA)** is the final go/no-go test.
- Pardo's 8 stages: formulate → specify as code → preliminary test → optimize → walk-forward →
  trade → monitor against the test profile → refine (with feedback loops) (ch.3).
- His own platform requirements (ch.4) read like a feature list for our app: diagnostics on the
  chart, standard reports, a custom objective function, speed, batch automation, built-in WFA,
  portfolio analysis.
- He prefers **different parameters per market** and **periodic re-optimization** on a fixed
  schedule (ch.6, ch.11). Kaufman and Carver say the opposite (one parameter set, pooled across
  markets). Treat that as an open question for the user, not a rule.
- Numbers are futures examples (S&P, T-bonds, yen) from before 2008. They are illustrations, not
  evidence.

## Chapter notes

### Ch 2-3 - Why systematic, and the process
- Benefits: verifiable, quantifiable, objective, consistent, extensible to many markets and timeframes.
- **Perfect Profit** = the sum of all price swings (buy every low, sell every high). It is used later
  as a measure of how much opportunity the market offered (ch.12).
- Risk-adjusted return beats raw profit. His example: $2.5k profit with $500 risk is better than
  $50k profit with $50k risk.
- Skipping signals or changing size by gut changes the measured risk/reward. After that, the test
  results no longer apply.
- Preliminary test: (a) the code does what the idea says, (b) a rough profile over several markets
  and periods. If all of them lose, and badly, drop the idea.
- A good optimization should improve on the preliminary result by roughly 50-100 %, and in all
  markets.

### Ch 4 - The strategy development platform (direct app requirements)
- **Diagnostics:** signal arrows on the price chart; mark bars where a condition is true; write
  intermediate values per bar to a file so they can be checked by hand; step through bar by bar.
- **Reports:** performance summary split into long and short; trade list (entry/exit date, price,
  signal name, P/L, running total); equity curve under the price chart; table per year, quarter or
  month (results spread evenly over time = robust); replay stops and signals bar by bar.
- **Optimization:** a custom objective function (he stresses this most); speed; batch runs
  (N strategies × M markets, reports saved automatically, overnight); built-in WFA; portfolio
  analysis.

### Ch 5 - Elements of strategy design
- Three parts: entry/exit, risk management, position sizing. Rules can be symmetric or
  asymmetric, reversing or not. Each extra filter adds overfit risk.
- Stops are exceeded by **slippage in fast markets** and by **overnight gaps**: a stop that is
  gapped through becomes a market order at the open. Trailing stops behave the same way. A limit
  target that is gapped through fills at the open, at a better price.
- Risk stop kinds: dollar, volatility (e.g. 3-day average range), % of equity.
- **Strategy stop** = max drawdown × safety factor (1.5). Required capital: margin + 1.5 × MDD, or
  (conservative, survives two drawdowns in a row) margin + 2 × 1.5 × MDD.
- Trailing stops never move back. Targets help counter-trend systems and hurt trend systems.
- Sizing: volatility-adjusted (equity × risk % / risk per unit, rounded down), martingale,
  anti-martingale, Kelly = (win % - loss %) / (avg win / avg loss). Small samples and fat tails make
  Kelly inputs unreliable.
- Scaling in and out is described but not tested.

### Ch 6 - The historical simulation (engine accuracy)
- Essential reports: summary (with Sharpe, which many platforms lack), trade list, equity curve,
  year table. Replaying trades on the chart gives a feel for living with the strategy.
- **Tick math:** round data and order prices to the instrument's tick. Floating-point
  near-misses produce wrong fills and overstated P/L (about 10 % of a $250 average trade in his
  example). Fast systems suffer most.
- **Same-bar ambiguity ("phantom trades"):** if the entry and the stop (or stop and target) are
  both inside one bar, OHLC cannot tell which came first. Resolve it from a lower-timeframe series
  (e.g. 5m for daily bars). The "the extreme nearer the open came first" rule is only a guess.
- **Limit orders:** do not fill on a touch. Require the price to trade through by X ticks (his
  example: 8 ticks on the S&P). Citing Kaufman, he says up to 30 % of limit orders go unfilled.
  Missed limit fills ("trade slippage") often skip the winners.
- Slippage costs are dominated by rare events (fills 10× worse than average). Stops placed in
  clusters fill worse. **Silent slippage at the open and close:** the historical open/close is
  often the first tick or the mid of the opening range, while real market-on-open or market-on-close
  fills come near the worst end of that range.
- **Gap slippage should be reported separately:** many stops filled at the open = a design
  weakness; limits gapped in our favour = a hidden strength.
- Cost example: 200 trades a year, $10k gross, $125 cost per trade → -$15k net.
- Test with and without event or shock trades (crash windfalls).
- Data: adjust for splits and dividends; watch for fake opens (previous close copied into the open);
  futures need back-adjusted continuous contracts (which can go negative and break %-based maths).
- **Sample size:** standard error = SD / √N; plan with the pessimistic side (mean − SE). Thirty
  trades is the minimum rule of thumb. With fewer trades, require a theory behind the idea, a broad
  robust parameter region and many markets.
- **Degrees of freedom:** remaining DF % = 100 × (1 − used / available); each lookback bar and each
  rule uses one. Keep at least 90 % (a 30-bar MA on 100 bars leaves only 70 % → do not run that
  test).
- Market types: bull, bear, cyclic (range), congested (the worst; maximum drawdown usually happens
  here). The test window should contain all of them.
- **Window vs model life:** trade (or run the OOS window) for 1/8 to 1/3 of the optimization
  window (24 months of optimization → 3-8 months of trading).

### Ch 7-8 - Specification and preliminary testing
- Write pseudocode, then exact formulas, then code. Turn vague discretionary choices into
  on/off options to test (stop yes/no, target yes/no). Add parameter constraints (e.g. slow ≥ 2 ×
  fast).
- **Robust** = profitable over (1) a broad range of contiguous parameters, (2) diverse markets,
  (3) different market types, (4) long and short.
- Verification: one run where every rule fires a few times; check custom formulas and every rule
  branch by hand or in a spreadsheet; use the trade list and the chart together.
- **Theory check:** trade count, holding time and direction must match the idea. A big deviation
  means a bug, hostile data, or by accident a different strategy.
- **Multimarket / multiperiod test:** one sensible parameter set on 5-10 diverse markets
  (|correlation| < 0.5), 10 years cut into five 2-year segments, shown as a market × period table.
  Segments prevent one or two great years from hiding eight bad ones.

### Ch 9 - Search and judgment (optimizer design)
- Search methods: grid (exhaustive, slow; impossible to read beyond two dimensions); **prioritized
  step search** (scan one parameter at a time, the others held at a constant such as the midpoint,
  most important first, and repeat the loop until nothing changes; the cost is the sum of the
  steps, not their product). Bonus: it shows each parameter's impact; a flat-response parameter
  should be fixed or removed. Also hill climbing, multi-start hill climbing, simulated annealing,
  genetic algorithms (5-10 % of the space evaluated), particle swarm. **All guided searches are only
  as good as the objective function**, and spiky spaces fool them.
- What a good objective should reward: trades and profit spread evenly over time, long/short
  balance, a large contiguous profitable region, works on several markets, acceptable risk, stable
  win/loss runs, enough trades, an upward performance trend.
- **Objective functions:** net profit (only as a floor); annualized return; max DD (as a ceiling);
  **CECPP** = correlation of the equity curve with cumulative Perfect Profit; **PROM** (pessimistic
  return on margin) = [AvgWin × (W − √W) − AvgLoss × (L + √L)] / margin. PROM penalizes small
  samples automatically (10 % haircut at N=100, 33 % at N=9). Stricter versions: PROM without the
  biggest win, and PROM without the biggest winning run.
- Recommended setup: rank by the strictest PROM, with floors and ceilings (net > X, max DD < Y,
  at least 10 trades a year).

### Ch 10 - Optimization
- The framework needs four decisions: parameters and scan ranges; the data sample; the objective
  function (kept the same across projects); evaluation rules.
- Keep the number of optimized parameters small. Find each one's impact with one-at-a-time scans.
- **Scan ranges** must make sense in theory (short MA 2-14, not 1-1000). Steps that are too fine
  cause overfitting. Keep steps roughly **proportional in %** (5 % of 20 = 1, of 100 = 5) and the
  candidate counts of the ranges similar.
- Multimarket × multiperiod optimization: the same grid on each market and each 2-year segment
  (e.g. 96 combinations × 10 markets × 5 periods = 4,800 runs).
- **Robust optimization profile (three tests):**
  1. Share of profitable parameter sets: under 5 % → reject; at least 20 % with significant
     profit → marginal; more is better (ch.13 mentions 40 %).
  2. Distribution: high mean, small max-min range, small SD; the top set within 1 SD of the mean;
     mean > 0; mean − 1 SD > 0; mean − 3 SD > 0 (very strong); profit of profitable runs / total.
  3. Shape: a smooth hill where the top set has profitable neighbours. A spike is a statistical
     fluke.
- **Neighbour-averaged objective:** average each cell with its two neighbours. His example: the
  spike at MA6 (12.5k, neighbours −0.5k and 3k → 5.0k) loses to the plateau at MA13 (7k, 6.5k,
  5k → 6.2k).
- A strategy "benefits from optimization" only if risk-adjusted return improves significantly in
  most markets and periods (5 % → 7 % is not significant; 5 % → 15 % is).

### Ch 11 - Walk-forward analysis
- WFA answers four questions: is it robust? What return should we expect out of sample? How do
  trend, volatility and liquidity changes affect it? Which parameters should we trade now, and for
  how long?
- **Walk-forward efficiency (WFE)** = annualized OOS profit / annualized IS profit. About 25 % →
  overfit or unsound; robust systems reach 50-60 % or more; above 100 % is possible. Expected live
  profit ≈ WFE × the latest IS annual profit.
- Unsound or overfit systems can win a few windows but not many, so use **many windows**: 10-20
  years of data, 10-20 or more walk-forwards. The statistical strength comes from the total
  concatenated OOS length, so the IS windows can be short and recent ("theory of relevant data").
- Window sizes are **parameters of the strategy**; find them empirically. IS: 1-2 years for fast
  systems, 3-6 for slow ones. OOS: 25-35 % of IS. Step = OOS length, so every bar is traded OOS
  exactly once.
- OOS drawdowns are more realistic than IS drawdowns (optimization rejects high-DD parameter sets).
  Report max DD per IS and per OOS window, with mean, min, max and SD.
- Reports: a detail table per window (IS period, chosen parameters, IS P/L, OOS P/L, WFE, DD) and
  a summary over all concatenated OOS trades.
- Example: RSI counter-trend system on the S&P, 1990-2005, IS 36 months, OOS 6 months, objective
  PROM: 30 walk-forwards, 63 % of OOS windows profitable, WFE 135 %.
- Without an automated WFA: one long walk-forward (10 years IS → 5 years forward), plus a
  "walk-backward" to the 5 years before IS, plus a middle block, on at least 10 markets.
- Live trading re-optimizes **on the WFA schedule, pre-emptively**, whether or not it seems needed.
- A low WFE on a strategy believed to be sound: check the framework first (DF, window sizes, ranges
  too wide or steps too fine, too many parameters). If WFE stays low, drop the strategy.

### Ch 12 - Evaluation of performance
- Compare with alternatives: the risk-free rate, other investments, CTAs, and the running costs.
- Max DD is the main risk measure, but it **scales with volatility** (a low-volatility test
  period → DD too small live) and is a fuzzy statistic. Also look at average and minimum DD. If
  MDD is more than about 3 × the average DD, find out why. The MDD should happen in hostile
  conditions (congestion or chop). An MDD in conditions like those of the best run-up is an alarm.
- Required capital = margin + MDD (minimum), + 2 × MDD, or + 3 × MDD (conservative).
- **RAR** (annualized) = annual profit / (margin + 2 × MDD). **Reward/risk** = annual profit / MDD;
  aim for at least 3.
- **Model efficiency** = net profit / Perfect Profit; 5 % or more is very good. A stable value from
  year to year means the strategy turns opportunity into profit consistently.
- **Consistency checks:** mean, SD, max and min of P/L, wins/losses, long/short and win/loss runs.
  Remove the maximum and recompute the mean; a drop of more than 1-2 SD means one outlier carries
  the result. Check how results spread over time.
- **Year-table patterns:** falling profit with rising DD = decay (red flag); one big year hiding
  losses = reject; even and rising = good; rising from early losses = needs an explanation (regime).

### Ch 13 - The many faces of overfitting
- Overfitting = optimization done wrong (good IS, poor OOS). It comes in degrees, and even a sound
  strategy can be overfit.
- **Abuse of hindsight:** adding rules that fix specific past events (a long bias after a bull
  market; a $3k stop that only removes one big loss; tripling size on a T-bond "link"). Cure: test
  every change on all periods and markets.
- **Five causes:** too few degrees of freedom; a small data or trade sample; overparameterization;
  overscanning (steps too fine); one big win in a small sample ("big fish in a small pond"); no WFA.
- **Warm-up bars** count against DF and **bias optimization toward short parameters** in small
  samples (long lookbacks get fewer trades). WFA software must load extra history before each
  window.
- **Overscanning** fills the optimization set with near-identical runs. That inflates the %
  profitable and the mean, and shrinks the SD: robustness that is not real.
- Mild overfitting shows up as live efficiency below the WFE. Compare live/IS with the WFE.

### Ch 14 - Trading the strategy
- **Strategy stop-loss (SSL)**, set before going live: MDD × safety factor (2-3), or combined:
  required capital = (MDD × SF) / maximum capital loss % (6k × 3 = 18k / 40 % = 45k).
- **Live profile vs test profile:** track about 25 statistics in both (annual profit, trades per
  year, % winners, largest/average win and loss with their durations, average/largest winning and
  losing run with durations, max DD and run-up with length and dates), each with its SD. **Alarm:**
  any live statistic below 50 % or above 150 % of the test value needs an explanation. Example: a
  losing run beyond MDD + 1 SD in both dollars and trade count, at the same volatility → suspend.
  Scale by volatility (2× volatility → 2× losses is fine).
- Underperformance has three causes: a poor strategy, less market opportunity (normal), or a
  structural change (T-bills after 1980).

## For the application (what to build)
| Item | Source |
|---|---|
| Walk-forward runner with configurable IS / OOS / step (rolling), many windows, per-window table (period, chosen params, IS & OOS P/L, WFE, DD) and a concatenated-OOS summary | ch.11 |
| **WFE** metric (annualized OOS / IS) plus the expected live profit (WFE × latest IS) | ch.11 |
| Window size as a sweepable parameter (IS 1-6 years, OOS 25-35 % of IS) | ch.11 |
| Objective functions: PROM, PROM without biggest win, PROM without biggest run, CECPP, neighbour-averaged objective; floors and ceilings (min trades/year, max DD) | ch.9-10 |
| Optimization profile report: % profitable, mean / SD / min / max, top within 1 SD, mean − 1 SD and − 3 SD > 0, 1-D/2-D shape | ch.10 |
| Prioritized one-at-a-time parameter scan (parameter-impact report) | ch.9-10 |
| Scan-range checks: proportional steps, DF % (warm-up + lookbacks + rules ≥ 90 % remaining), warm-up loaded before each window | ch.6, 13 |
| Multimarket × multiperiod table (one parameter set; markets × 2-year segments) | ch.8, 10 |
| Engine: tick rounding, limit fills only on penetration by X ticks, gap fills at the open for stops/targets, same-bar ambiguity resolved from a lower timeframe | ch.6 |
| Gap-slippage report (stops filled at the open vs limits gapped in our favour) | ch.6 |
| Consistency report: remove-the-max test, year table with trend of profit and DD, MDD context (conditions during MDD and max run-up) | ch.12 |
| Model efficiency vs Perfect Profit per year | ch.12 |
| Required capital / strategy stop-loss calculator (MDD × SF) | ch.5, 12, 14 |
| Live monitor: about 25 profile statistics live vs test, 50 % / 150 % alarm, volatility scaling | ch.14 |

## Testable ideas (not now, the user wants the app first)
Pardo gives almost no strategies. Examples he uses: "momentum surge" (enter on a move of X % of
the 3-day average range from the prior close, ch.3); range breakout from yesterday's close ±
125 % / 145 % of yesterday's range (ch.7). They come with no evidence and are close to our
volatility breakouts.

## Warnings / pitfalls
- Parameters per market and periodic re-optimization are Pardo's preference, not proven. They
  conflict with Kaufman and Carver: decide with the user.
- WFE above 100 % happens and does not prove skill by itself. One WFA path can also be overfit if
  the window sizes are tuned (see Masters / López de Prado on that).
- His thresholds (20 % profitable sets, WFE 50-60 %, reward/risk ≥ 3, 1/8-1/3 rule) are rules of
  thumb with no data shown.
