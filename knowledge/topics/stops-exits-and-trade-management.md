# Stops, exits and trade management

Sources: K = Kaufman *TSM* ch. 5, 8, 16, 20, 22-23; D = Douglas; H = Hougaard.

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
