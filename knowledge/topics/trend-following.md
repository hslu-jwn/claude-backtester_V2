# Trend following

Sources: K = Kaufman *TSM* ch. 1, 5-8, 17, 19, 21-23; H = Hougaard; D = Douglas.
Our strategy 4 (`docs/strategy-trend-following.md`) already implemented breakout, SMA + ATR band,
momentum, KAMA and Dunnigan; it failed with FTMO swap and was unstable across halves (ROADMAP 10).

## Why it works, when it fails
- Price runs have a fat tail: more long runs than a coin-flip model. One trade can pay for 30 losses
  (K p.309-312). Trend systems **need** this tail; profit targets and tight stops cut it off (K p.320, 1057).
- Typical profile: 30-40 % winners, avg win/avg loss > 2, winners held ~5× longer than losers,
  10 losses in a row are normal (K p.319, NASDAQ 40-day MA: 34.7 % winners, ratio 2.22).
- It fails in sideways markets; nothing avoids that (K p.309-311). Equity indices trend worst
  (see [markets-and-regimes.md](markets-and-regimes.md)).
- Intraday trend following hardly works: below about 3 days of holding the bars are mostly noise;
  by the time an intraday MA confirms, only ~25 % of the day's range is left (K p.745).

## Methods compared (K ch.8, p.336-349)
- n-day momentum, SMA direction, EMA, regression slope, n-day breakout, swing breakout: profit
  factors are close; **the market matters more than the formula**. Longer periods do better.
- MA/momentum ≈ 34 % winners, many small losses; regression slope/EMA ≈ 43 %; breakout ≈ 50 % winners
  but half the trades and much larger risk per trade (distance between n-day high and low).
- Systems trading more than ~200 times in 20 years were clearly worse (thin margin per trade).
- MA **direction** (turning up/down) beat price-crosses-MA: 26-37 % fewer trades, better PF (K p.315).
- Bands help noisy markets (S&P), hurt smooth ones (K p.321).
- Best N is unstable: crude N-day breakout best at 75 days in the 1990s, 15 days in the 2000s
  (K p.225-227). Judge by the share of profitable N, not the best one.

## Improvements the books suggest (testable on top of strategy 4)
- **Pullback entry inside a slow trend:** buy when slow trend up and fast trend turns down; exit when
  the slow trend flips. Nasdaq 1991-2011: PF 1.51 → 2.26, win rate 35 → 47 %, trades −66 % (K p.950-951). → I-05
- **Wait for a better price:** after a signal wait up to N bars for a pullback, else enter at bar N.
  Trades −40 %, profit per trade ~2× (K p.1078). → I-06
- **Scale in over several bars** (best spacing ~2 bars) (K p.1076). → I-06
- **Two trends:** fast signals only in the slow trend's direction; about the same profit with half the
  time in market (K p.350-357, Table 8.7) → less swap.
- **Trend quality gate:** ER, regression r / R², strength oscillator (K p.275-276, 408, 1062).
- **Low-volatility entry filter**, **high-volatility exit with re-entry** (K p.861-866). → I-04
- **Consensus of periods:** average the direction of many MA lengths instead of choosing one (K p.363-366).
- **Speed rule of thumb:** MA ≈ ¼ of the average swing length you want to catch (K p.360).
- **Event-driven (time-free) trend:** swing chart with an ATR-sized filter; P&F with an ATR box gave
  uniform results across EUR, S&P, gold where fixed-% boxes were erratic (K p.182-191, 218-220). → I-14

## What practitioners add
- Hougaard trades with the trend intraday ("buy high, sell higher"), never fades, joins late if
  needed, and presses winners (see [stops-exits-and-trade-management.md](stops-exits-and-trade-management.md)).
- Douglas: lowest-risk trade = pullback to support in the direction of the daily trend (higher highs,
  higher lows) (D ch.11). Not precise enough to code as is; close to our strategy 1 and 3.

## Costs and swap
- Holding days to weeks means swap; with FTMO rates XAUUSD longs cost about $61 per lot per night
  (ROADMAP 10.4). Prefer variants with less time in market (two-trend, pullback entry) and report swap
  in R separately.

## Micro-timeframe pullbacks (Volman, Aziz)
- **Volman's with-trend setups on a 70-tick chart + 20 EMA:** DD (2+ small dojis at the EMA after a
  40-60 % diagonal pullback, enter 1 pip beyond their trend-side extreme), FB (first pullback after a
  violent surge, rarely taken), **SB (second break: the first break fails, W/M at the EMA, enter on the
  second signal bar; his preferred setup)**. EMA 15-25 all work; the EMA is a guide, not support.
  "Trend equals trend": the move after a pullback mimics the move before. → I-35
- **Aziz 9 EMA ride:** from ~11:00 New York, price consolidating above a rising 9 EMA; buy near the EMA,
  exit on the first 5-min close on the other side. Probably weak in noise but cheap to test.
- Both are intraday, so no swap; costs per trade are the problem (see costs topic).
