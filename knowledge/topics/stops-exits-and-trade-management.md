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
