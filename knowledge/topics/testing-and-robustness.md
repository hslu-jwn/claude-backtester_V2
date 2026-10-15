# Testing and robustness

How to test a strategy so the result can be trusted. This is the most useful part of the books for us.
Sources: K = Kaufman *TSM* (ch. 1-2, 5, 8, 21-23 mainly), D = Douglas, H = Hougaard. Page numbers are Kaufman's.

## Core principles
- **Test to validate an idea, not to find one.** Start from a premise with a reason (behaviour, flows,
  structure). A computer scan over everything finds chance patterns (K p.18-19, 331, 470: the
  "18 years of coffee/wheat" story that failed in year 19).
- **Write the expectation first:** trade count, win rate, avg R, holding time, drawdown. A result far
  from the expectation, good or bad, means a bug or a wrong premise (K p.907). Be as suspicious of good
  results as of bad ones (K p.19).
- **The best optimisation result never comes true.** Expect the *average* of all tests over a sensible,
  pre-declared parameter range; better still, mean minus 1 standard deviation (K p.938-945).
- **Simple beats complex:** at most about 4 free parameters (K p.938, Futures Truth). Start simple, add
  complexity slowly, stop early.
- **The market matters more than the formula.** All simple trend methods have about the same profit
  factor on a given market (K ch.8 comparison, p.336-349). Choosing *where* to trade (low-noise
  markets) beats choosing *how*.

## Data and sample
- Sample error is about 1/sqrt(N): 4 trades 50 %, 100 trades 10 %, 400 trades 5 % (K p.28). Ignore
  profit factor below about 30 trades; PF 76 on 8 trades means nothing (K p.946).
- Data must contain bull, bear and sideways phases. A one-way history flatters any biased system (K p.29).
- Use daily equity for drawdown and risk; monthly data hides risk (K p.53).
- Test and trade on the same data source (K p.980): for us histdata vs FTMO feed (see `tools/feed_compare`).
- Douglas's 20-trade sample is an alarm for gross failure only, not a test (D ch.11; with 20 trades the
  win-rate error is about ±20 points).

## In-sample / out-of-sample
- Reserve about **50 %** of the data out-of-sample, decided **before** development. Best split:
  alternating random blocks fixed in advance; stitch daily returns, not block totals (K p.916-917).
- OOS is used **once**. Changing anything after seeing OOS turns it into in-sample (K p.27, 917).
- Typical OOS result is about half the in-sample return; information ratio 2.0 -> 1.0 is fine,
  2.0 -> 0.4 is a fail (K p.917).
- **Sibling markets are free OOS:** an S&P idea should work on Nasdaq. For us: NAS100 <-> US500,
  GBPUSD <-> GBPJPY (K p.945).
- Walk-forward: windows long enough that the best parameter does not jump between fast and slow;
  chain only OOS pieces; keep a final untouched hold-out (K p.918-919).

## Parameter grids and surfaces
- Pre-declare ranges; use **geometric spacing** (5, 10, 20, 40, 80, 160 or ×1.5), not equal steps,
  which overweight the slow end (K p.908-910, 299-301, 330).
- One parameter at a time, most important first (trend speed), then filters, then stops. Stops and
  filters refine; they must not rescue a losing core (K p.908-910; "vertical development" p.989).
- Look at the 1-D curve / 2-D heat map. Accept only **broad plateaus**; a lone spike surrounded by
  losses is a fluke; an erratic map means no edge or a bug (K p.922-931). Smooth each cell with its
  neighbours (3 in 1-D, 9 in 2-D) and pick the centre of the plateau.
- **Robustness score:** share of combinations in the declared range that are profitable. About 70 %
  = robust; under 50 % = reject (K p.945; valid only if the range was not narrowed afterwards).
- A new rule must improve the **average of all tests** (or cut dispersion at the same mean). If it
  only lifts the peak or touches 1-2 trades, it is overfit (K p.937). Compare % profitable combos
  with and without the filter (K p.989).
- Count every variant ever tried. One good configuration in 1000 is not significant (K p.945).

## Stability checks
- **Halves / years table:** P/L per year and per half; slope of periodic returns (declining = decay)
  (K p.941, 1046). 2-sample (Welch) t-test of trade R between halves (K p.47-48).
- **Cross-market:** same rules and parameters on every symbol of a class and on neighbouring
  timeframes; profitable in at least half the markets (K p.954-970; Lukac et al.: only a third of
  systems were consistently profitable).
- **Outliers:** remove the best trade / best move and look again; study the 10 biggest wins and
  losses. Many big wins and no big losses = overfit (K p.941). Kurtosis of daily returns above about
  7-8 is a warning sign (K p.43).
- **Shocks:** mark shock days (range > 3.5-5 × ATR(10)). If more than half of them were profitable,
  the risk is understated; show P/L with shock days removed or reversed (K p.970-975).
- **Surprisingly small max drawdown** = overfit or tiny sample (K p.941).
- Regimes are only known after the fact; a pattern that works in 3 of 4 regimes may fail in the
  current one (K p.694). Several edges in the books flipped sign over time (RSI(2) around 1998,
  outside-day rule in the mid-1980s, ORB after 2000, fast Turtle breakout after the early 1980s).

## Costs in tests
- Costs on from the start. Run **three levels**: 0, realistic (spread + commission + swap), stressed
  (+50 %). Show how the profitable parameter range shrinks (K p.949: Nasdaq MA zone shrank from
  ">15 days" to "45-75 days" with costs).
- Nearly all of Kaufman's published numbers are **gross of costs** and on 1990-2011 futures. Treat
  them as hypotheses.

## Checklist for every backtest (use this)
Derived from K ch.21-24 (full version with page refs: `books/kaufman-tsm-ch21-24.md` › Checklist).

**Before running**
1. Premise written down (why the edge exists) plus expected trades, win rate, avg R, hold time, DD.
2. Parameter ranges pre-declared, geometric spacing, ≤ 4 free parameters, success metric fixed
   (net expectancy in R, R per month, max DD in R, Calmar/Ulcer; not net profit alone).
3. Data split fixed: OOS blocks chosen in advance, sibling symbols named as extra OOS.
4. Rules checked by hand on the chart for a sample of trades; no-lookahead tests green.
5. Costs at 0 / realistic / stressed.

**Robustness**
6. Core signal profitable before any stop/filter tuning.
7. Heat map: plateau, not spike; pick the plateau centre.
8. Report the average and st.dev over the whole range; robustness = % profitable combos (target ≥ 70 %).
9. Sensitivity ±10-20 % around the chosen point: gentle degradation.
10. Every filter must lift the average of all combos, not the peak.
11. All symbols of the class and neighbouring timeframes, same parameters.
12. Walk-forward with stable parameters; final hold-out untouched.
13. Year/half table, slope of returns, best trade removed, top 10 wins/losses studied.
14. Shock-day check.
14a. Random-entry baseline: net R percentile against 1,000 seeded random-entry runs with the same
    exits and costs (T-02; [backtest-frameworks.md](backtest-frameworks.md)).
14b. SL and TP in one candle: resolved from M1, not "SL first" (T-03).
14c. Stressed fills: seeded random slippage; the result must survive it (T-07).
15. Enough trades (dozens to hundreds); standard error of expectancy reported.
16. Time in market and swap in R reported separately.

**Risk (R list -> account)**
17. Fixed fraction (0.25-1 % per trade) and volatility-targeted sizing; Monte Carlo with block
    bootstrap plus the real sequence.
18. Plan for 1.5-2 × the historic max DD; FTMO: P(5 % daily or 10 % total breach) below a stated limit.
19. Risk of ruin against the FTMO limits.
20. Kelly / optimal f only as an upper bound.

**Before live**
21. Paper/demo with worst-of-5-minutes fills, same rules, same data source; compare to expectation.
21a. Reconcile demo trades with the engine on the same candles before trusting either (T-06).
22. Live monitoring: binomial test of the loss streak and chi-square of live vs expected win rate
    decide whether a system is "broken" (K p.1092-1097). Retest only after 5-10 % new data.

See also: [costs-and-execution.md](costs-and-execution.md), [position-sizing-and-risk.md](position-sizing-and-risk.md),
`.claude/skills/backtest-evaluation-research` (online research on the same question).

## Discretionary books: how to read them
- Volman, Aziz and Coulling give **no statistics at all** (no win rates, samples or costs); every example
  is a hand-picked chart. Treat their rules as hypotheses.
- Their real "edge" sits in judgement filters (chart resistance, squeeze quality, "holds support",
  "high volume"). When coding them: fixed numeric thresholds in a config, pre-declared, and check for
  lookahead (equal highs, "first pullback of a new trend" and the surge origin are easy to define with
  hindsight).
- Good use: A/B tests that isolate one claim (breakeven vs no breakeven, with vs without the tension
  filter, price-only vs tick-volume version), and exit modules on a random-entry baseline to separate
  exit edge from entry edge (Volman notes, idea B).
