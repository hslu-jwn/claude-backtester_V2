# Stops, exits and trade management

Sources: K = Kaufman *TSM* ch. 5, 8, 16, 20, 22-23; D = Douglas; H = Hougaard; RC = Carver; LP = López de Prado; KD = Davey; EC = Chan; JK = Kaeppel.

## Stops
- The stop is set **before** entry from market structure or volatility, never from comfort. If the
  risk is too big, cut the size, not the stop (D ch.11; K p.1054-1062).
- Never move a stop further away, never override it manually (D ch.7, 11; H). Moving it to breakeven
  is allowed once the trade has worked.
- For a random walk, number of hits × distance is constant, so a stop must beat chance; tie it to
  volatility (k × ATR, Kase dev-stop) not fixed points (K p.1054).
- Prefer **close-based** exits in noisy markets: trigger on high/low, exit on the close (K p.861, 1054).
- Stops fill at the worst price in shocks; many systems cluster stops at the same levels (K p.1054-1062).
- Mean reversion needs room; trend systems already cut losses through the signal (K p.1054).
- Shock entries: no stop for the first 2 bars, then beyond the extreme (K p.776).
- Time stops: exit if not profitable within one opening-range duration (Fisher) or by the end of day 2
  (Raschke NR4) (K p.762-770).

## Profit targets
- Targets **hurt slow trend following** (they cut the fat tail) but help short-term noisy trading
  (K p.320, 861, 1057-1059).
- Hougaard uses no targets at all: stop to breakeven, then trail by chart structure; exit on a double
  top/bottom against him or where he would enter the other way (stop-and-reverse level).
- Douglas: ideally ≥ 3:1 reward/risk; then < 50 % winners still pays (D ch.11). → I-24

## Scaling out vs pressing winners (opposite camps)
- **Scale out (Douglas):** thirds; first third after a small early gain, second at a structural
  target, then stop to entry, last third just before the expected stopping level. His early data:
  ~25-30 % of trades become losers after first moving 3-4 ticks his way (D ch.11). Kaufman: taking
  small profits rarely improves return but can improve return/risk (K p.212). → I-24
- **Press winners (Hougaard):** N = session ATR on the trading timeframe; stop 2N; unit risk 2 % /
  2N; add one equal unit every ½N (worked example; text says every N); move all stops to one common
  level so total risk does not grow. Reject partial profits ("never gives the home-run trade").
  → I-25
- **Kaufman's evidence:** adding equal units on **new profit highs** (≥ n bars apart, max 5 units)
  raised PF in futures (e-mini S&P 1.14 → 1.46 at 10-day spacing), mixed on stocks; **averaging down
  was worse in 3 of 4 markets** (K p.1080-1084). Turtles: add 1 unit per ½-1 ATR of profit up to
  4-5 units (K p.229-233).
- Risk: pyramids are top-heavy; a sharp reversal can turn a big open profit into a loss (H's DAX
  example) and can hit FTMO's daily limit.

## Entry management
- Scale in over several bars (best ~2-bar spacing) (K p.1076). Wait up to N bars for a pullback
  (K p.1078). → I-06
- Separate entry and exit rules rather than stop-and-reverse (reversals double the spread, K ch.23
  summary; strategy 4 used stop-and-reverse).

## Shock and volatility exits
- Shock bar (range > 3.5-5 × ATR): windfall profit → exit; loss → hold expecting a partial reversal,
  block new entries; re-arm when volatility falls (K p.992-1000). → I-04
- Exit a trend trade when the daily return > factor × prior 20-day volatility; re-enter when the range
  shrinks to ¼ of the exit-day move: bonds PF 1.02 → 1.16 (K p.865-866). → I-04
- After a crash, trend lines go out of phase for months; re-initialise trend state after volatility
  subsides (K p.992-1000).

## Our context
- Engine: SL/TP and signal exits exist; TP is optional (strategy 4). Partial exits and adding units are
  not supported yet; both would be new engine features (management layer, still in R).
- Intrabar order: if SL and TP are in one candle, SL is assumed first (invariant #1). This matters for
  scale-out tests with near targets.

## From the scalping and day-trading books (Volman, Aziz, Coulling)
- **Tipping point (V ch.14):** the stop is the chart level that, traded through by one pip, makes the
  trade invalid; exit at market at once. Initial stop 1 pip beyond the setup; risk = setup height + ~3 pip
  (break on each side + spread); average real stop 6-7 pip against a fixed 10-pip target. → I-36
- **No breakeven stop** (Volman calls it a cardinal sin; entry levels are often retested). Trail only after a
  "technical feat": a pullback that tested a prior level or the 20 EMA, followed by a bar taking out the
  pullback bar's extreme; then lift the stop behind that pullback. More than half of the trades that reach
  the target go through a serious pullback first (V ch.14).
- **Opposite view (Aziz):** take half at the first target and move the stop to breakeven. Breakeven vs no
  breakeven is a direct A/B test. → I-36, I-24
- **Never tighten a stop to improve the reward/risk ratio; skip the trade instead** (Aziz rule 5;
  V ch.13-14: skip if the technical stop is more than 10 pip away). Our tests must apply the same skip.
- **Aziz:** minimum 2:1 to the next level; stop at a structural close (VWAP, EMA, level); exit on the first
  opposite 5-min extreme; time stop: a reversal trade that goes flat for a few minutes is closed.
- **Coulling (C ch.8):** trail with the 3-bar pivot sequence (exit when a pivot high fails to exceed the
  previous one, or price closes below the last pivot low).
- **Free path to target (V ch.15):** skip when clusters, prior highs/lows or a round number sit inside
  the target distance. → I-37

## Volatility-scaled stops, barriers and what exits can do (Carver, López de Prado, Davey, Chan, Kaeppel)
Ideas: I-36, I-60, T-14, T-15. Rule of this section: exits reshape the payoff distribution, the edge has to come from the entry (LP 13.6).
- **Carver:** no systematic profit targets ("no evidence they work, markets trend"). One exit: a trailing stop X daily sigma (price units)
  from the best price since entry; X sets the holding period and turnover: X=1: 4 days / 64 round trips a year; 2: 9 days / 29; 3: 17 days / 15;
  4: 6.5 weeks / 8; 8: 13 weeks / 4; 10: 26 weeks / 2. When volatility doubles the stop doubles and the position halves, so risk per bet is
  constant. Stops must be in market sigma, never in account or pain terms (RC ch.5, 13).
- **Triple barrier (LP 3.4):** profit-take, stop-loss (both multiples of current volatility) and a vertical barrier (max holding bars); the first
  touch decides. Our SL / TP in R plus a session-end exit *is* a triple barrier with the vertical barrier at the session close. Fixed-horizon
  labels ignore stops and volatility regime.
- **Synthetic OU result (LP 13.6, no costs):** with zero long-run equilibrium (reversion) the best region is a SMALL target with a LARGE stop (Sharpe
  up to ~3.2 at half-life 5), the opposite corner is worst, the symmetric diagonal is near neutral; with a positive forecast the optimum is a
  rectangle (target ~5-6, stop 4-10 sigma); as half-life grows the map flattens and any optimum is noise. Asymmetric trap: small target, wide stop
  gives a high hit rate and a good Sharpe until the tail loss arrives.
- **Davey:** break-even stops cut winners; if a far stop destroys the system the entry is the problem; a profit target with a huge cap acts as
  "hold to session end"; do not trust same-bar stop and target fills (KD ch.10, 14).
- **Chan:** a stop is useless across closed-market gaps and liquidity vacuums; for mean reversion it contradicts the entry and lowers the backtest
  but protects against a regime change into a trend: set it wider than the worst in-sample excursion so it never triggers in sample (1.2-1.5×); for
  momentum the flipped signal is the stop (EC p.153, 182-184).
- **Kaeppel (options, transferable parts):** decide stop, partial exit and final exit before entry; take profit at ~80 % of the potential ("do not hold
  out for the last dollar"); after +1R take half and trail the rest at half the peak open profit; 2-sigma-of-the-holding-period level as a stop / target
  (sigma_h = price × annual vol × sqrt(h/365)); win-rate × payoff: a 68 % trade with 1 : 2.5 payoff means one max loss erases three winners, cut at
  1 : 1 (JK p.161, 187, 197-200). Evidence: showcase trades only. → I-24, I-60
