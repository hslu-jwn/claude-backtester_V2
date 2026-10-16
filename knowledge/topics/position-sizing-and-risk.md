# Position sizing and risk

Sources: K = Kaufman *TSM* ch. 2, 5, 21-24; D = Douglas; H = Hougaard; RC = Carver; EC = Chan; KD = Davey;
LP = López de Prado; WK = Kurt. Applies to `risk/` (Phase 5),
which works on the R trade list. Spec: `docs/risk-management.md`.

## Basic rules
- Risk a small fraction per trade: never > 5 %, 1-3 % common (K p.1032). For FTMO's 10 % total
  loss, Douglas's test "can I lose the next 20 trades?" means ≤ 0.5 % per trade (D ch.11). → I-26
- Define the exit before entry; exit wrong trades fast; never average down; never meet a margin call
  (K p.1032; H "never add to losers").
- Large profits imply large risk: ask whether the account survives the same move the other way
  (K p.1027-1028). Be in the market as little as possible.
- Capital ≈ 3 × the historic max drawdown; plan for 1.5-2 × (K p.941). The historic max DD is a
  floor, not a forecast.

## Sizing methods
- Equal dollars, equal volatility and equal ATR risk give very different sizes. Prefer **ATR /
  volatility-based** sizing: equal risk per trade is the most conservative when trades cannot be
  ranked (K p.1050-1054). ATR sizing cut one stock's trend P/L volatility by ~27 %.
- Our R model already sizes each trade to its stop, i.e. equal risk per trade.
- **Volatility targeting:** scale exposure to target vol / lagged realised vol (10-20 day); rebalance
  only when the factor moves > 20 %; info ratio 1.27 → 1.38 over 17 years (K p.1142-1145).
  Target vol 6-15 % a year; 15 % is aggressive (K p.1046-1050). → I-27
- **Drawdown scaling (Turtles):** cut size 20 % for every 10 % drawdown, restore 10 % per ~6.7 %
  recovery (K p.231). For FTMO use finer steps of the 10 % limit. → I-26
- Kelly / optimal f: f = [p(PLR+1) − 1] / PLR. Over-betting leads to ruin; use only as an **upper
  bound** to *reduce* leverage (K p.1088-1092). Carver and Chan agree: Kelly vol target = Sharpe, overbetting hurts
  more than underbetting, use **half Kelly** of a pessimistic Sharpe (RC ch.9; EC p.172-173); Davey rejects his optimal f
  (21 % ruin, 67 % median DD) (KD ch.16). Details below.
- Martingale / averaging down: works only in strongly trending low-noise markets with caps; blow-up
  risk; not for us (K p.1000-1011).
- Equity-curve trading (trade only when equity > its MA): inconsistent in Kaufman's tests (K p.1086).
  Check autocorrelation of trade outcomes first. → I-28

## Risk of ruin and "is it broken?"
- Streak and "k losses in n trades" odds are binomial tails (WK ch.4); P(at least one success in n trials) = 1 − (1−p)^n.
- Equal win/loss: R = ((1−A)/(1+A))^c, A = 2p − 1, c = capital units (K p.1072).
- Unequal (Gehm/Vince): ruin = ((1−P)/P)^(MaxRisk/A) with P = ½(1 + Z/A); ruin grows faster than
  capital shrinks (K p.1073-1075; worked example 0.63 % → 7.9 % → 28 % as capital halves).
- Binomial probability of a loss streak and chi-square of live vs expected win rate decide whether a
  live system is broken (K p.1092-1097). With 20 trades win-rate error is ±20 points (D's sample).
- Douglas: do not size up after winning streaks (euphoria) or skip signals after losses (fear). Test
  whether outcomes after streaks differ from baseline; if not, flat fractional risk is justified.
  → I-28

## Risk measures beyond Sharpe
- Information ratio, Calmar (return / max DD), Sortino, Ulcer Index (RMS drawdown), average maximum
  retracement, time to recovery (K p.1034-1045). Use daily data; monthly data looks better than it is.
- VaR fails exactly in crises (kurtosis up to 25 vs 3 normal); use stress tests (K p.1034-1045).
- Run statistics (LP 14.5): drawdown and time under water, both as 95th percentile; concentration of returns by a
  Herfindahl-type index for wins, losses and bets per month (0 = uniform, 1 = one return dominates): want low
  concentration, no reliance on a few outliers.

## Portfolio
- Diversify across unrelated markets **and** strategy types; all trend followers share one profit
  source (correlation 0.4-0.8, same side 55-83 % of days) (K p.1021-1026, 1099-1106).
- Correlations go to 1 in crises; cap total leverage (K p.1105-1106).
- Mean-variance fails for trade streams (a strategy flat half the time looks low-risk); use a
  drawdown-based objective (K p.1114-1141).
- Benefit flattens after about 4 uncorrelated assets (K p.1100).

## FTMO context
- Hougaard sizes 2 % per unit and adds aggressively; that style would breach a 5 % daily limit
  quickly. Any pyramiding test must include the daily-loss guard.
- Carry unwinds (2008, 2020, Aug 2024) are violent; a carry-earning position can breach the 10 %
  limit (K p.596-599).

## From the day-trading books
- **Aziz:** max 2 % per trade (1 % conservative), size = risk / stop distance, minimum 2:1, 2-3 trades a
  day, scale only into winners, never average down, never hold overnight; **give-back rule:** stop for
  the day once 30 % of the morning's profit is lost. → I-26
- **Volman (ch.16):** fixed fraction of 1-2 % on the stop, recomputed once a day; same size for every
  valid setup (no "quality" sizing); one position at a time; ignore new setups while in a trade.
- Both are far too large for FTMO's limits: use 0.25-0.5 % per trade with a daily stop.

## Volatility target and Kelly in practice (Carver, Chan, Davey)
Sources: RC ch.9-10 (Tables 20-27), EC ch.8, KD ch.7, 16, 20. Idea links: I-27, I-53, T-16.
- The **volatility target** is the long-run annualised sigma of the account as a % of *current* capital, the most important
  choice. Cash target = % target × current capital / 16 per day (256 days); recompute capital daily so the account compounds
  and de-risks after losses. Do not change the percentage afterwards (meddling).
- Kelly: optimal vol target = expected Sharpe (SR 0.5 → 50 %). Use half Kelly of a **pessimistic** Sharpe: back-tested SR
  0.25 / 0.40 / 0.50 / 0.75 / 1.0+ → target 12 / 20 / 25 / 37 / 50 %, halve for negative skew; semi-discretionary 10 / 15 / 20 / 25 %
  for SR 0.2-0.5 (RC Tables 25-26). Ten-year chance of losing half at SR 0.5: < 1 % at a 25 % target, 10 % at 50 %, 40 % at
  100 %, 93 % at 200 % (RC Table 23).
- Rules that risk a fixed % per trade imply huge vol targets: with 2.5 % max risk per trade and ~2 positions, a 1-day hold is ~100 %
  a year, 1 week ~40 %, 6 weeks ~10 % (RC Table 27). For FTMO's 10 % limit this is why day-trade risk must stay at 0.25-0.5 %.
- Chan: Gaussian Kelly f = m/s² (mean excess return over variance); several strategies F = C⁻¹M. Non-Gaussian: draw from a
  distribution with the strategy's four moments and maximise mean log(1 + fR); leverage above 1/|worst bar| is certain ruin;
  simulated drawdowns are far worse than historical ones (unconstrained f: −99.9 %; half Kelly still −96 %; a seven-fold cut was
  needed for −50 %, only 1.5× on the historical sample). When a broker cap binds, scaling all strategies proportionally is **not**
  growth-optimal (EC p.172-179). Apply Kelly **per strategy** so a failing one withers (EC p.188).
- **CPPI for a drawdown cap** (EC p.180-182): trade a sub-account of size D × equity with Kelly leverage f on it, rest in cash; reset
  to D × equity only at a new equity high, never top up after losses. Growth is close to leverage f·D on the whole account but the
  drawdown is bounded by D; useless against gaps, and not for a multi-strategy book. For FTMO D could be a buffer below 10 %.
- **Fixed fractional (Davey):** contracts = floor(x × equity / largest historical loss); choose x by Monte Carlo (maximise
  return/DD subject to median DD and ruin ≤ 10 %), not by optimal f (x 0.175 vs optimal-f peak 0.32). Start equity is sized so ruin is
  < 10 % (small accounts have large ruin odds even with positive expectancy); traders tolerate only about half the drawdown they
  claim; a 362 % median return is a warning, not a target; start at the smallest size and add from profits (KD ch.16, 19-20).
- **Quit rule in advance** (KD ch.20): average of 1.5 × the worst daily-basis walk-forward drawdown and the 95th-percentile Monte
  Carlo max DD; minimum account = quit drawdown + margin. Skipping or front-running signals invalidates the test (KD ch.21).
- Practicalities: position inertia of 10 % cuts costs without changing the pre-cost result for holds above a few days; want at
  least 4 blocks at maximum forecast, else drop the instrument or raise its weight (RC ch.11-12).

## Bet sizing from a probability and strategy risk (López de Prado)
Sources: LP 3.7, 10, 15. Idea links: I-57, T-16.
- Size from a predicted win probability p (side from the primary rule): z = (p − ½)/sqrt(p(1 − p)), size m = 2·Z(z) − 1 with Z the
  normal CDF (p = 0.5 → 0, saturating toward 1). Average the sizes of the bets still open, discretise to steps of 0.05-0.2 to avoid
  jitter trades (LP 10.3-10.5). Concurrency sizing: budget = (concurrent longs − shorts)/maximum concurrent (LP 10.2).
  High accuracy with bad sizing still loses (LP 10.1). Allocation to a strategy should grow only with live evidence (LP 1.3.1.6).
- **Strategy risk = binomial precision.** Each bet wins +π⁺ with probability p, loses π⁻. Symmetric payoff: annualised SR =
  (2p − 1)/(2·sqrt(p(1 − p))) × sqrt(n), n = bets per year (p = 0.55 needs ~396 bets a year for SR 2). Asymmetric: SR = sqrt(n)(
  (π⁺ − π⁻)p + π⁻)/((π⁺ − π⁻)·sqrt(p(1 − p))); the p* that reaches a target SR is the root of a quadratic in p (LP 15.3). In R:
  break-even precision = |π⁻|/(π⁺ + |π⁻|) before costs (33 % for 1R stop, 2R target).
- Probability of failure: bootstrap the bet outcomes (n × k years, draw with replacement), get the distribution of precision, and
  report P[p < p_threshold] (LP 15.4). A drop of precision from 0.70 to 0.67 can erase the profit; strategies with large n are
  fragile to small precision changes. Discard if the failure probability exceeds the tolerance (e.g. 5 %).
- Bayesian version: draw p (and payoffs) from the Beta / mean-R posterior and simulate the FTMO account for each draw; the pass rate
  averaged over draws is wider and more honest than the plug-in rate; the 20th percentile p is a defensible go/no-go for demo
  (WK notes M6, [statistics-and-bayes.md](statistics-and-bayes.md)).
