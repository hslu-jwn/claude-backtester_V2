# Volume and Wyckoff

Sources: C = Coulling *A Complete Guide to Volume Price Analysis* (chapter); A = Aziz; K = Kaufman ch.12.

**Data status:** histdata M1 has no volume (the column is always 0, checked 2026-10-14). MT5/FTMO feeds
have *tick volume* (number of price changes per bar). Coulling and Kaufman both say tick volume is a fair
proxy as long as it is compared only within one feed ("all volume is relative"). Volume rules can only be
tested once we have MT5 history with tick volume. → I-44

## Wyckoff's three laws (C ch.1, 4)
1. **Supply and demand** move price.
2. **Cause and effect:** a longer build-up (congestion) gives a bigger move afterwards. Testable without
   volume: zone duration vs move size. → I-34
3. **Effort vs result:** volume (effort) should match the bar range (result).

## Reading a bar (C ch.4, 6)
- Wide range + high volume = genuine move; narrow range + low volume = genuine quiet.
- **Wide range + low volume = anomaly**: a trap or fake move (e.g. an opening-bar probe, a news spike
  without participation).
- **Narrow range + high volume = absorption**: in an uptrend supply is being absorbed (weakness); in a
  downtrend buyers absorb sellers (possible bottom).
- Rising price needs rising volume; rising price on falling volume = weakness; falling price on falling
  volume = selling drying up.
- Candles: wick length first; hammer, shooting star, long-legged doji, hanging man are graded by volume
  (low = minor, high/ultra-high = significant). Long-legged doji on low volume (e.g. at NFP) = stop
  hunting, stay out.

## The campaign cycle (C ch.5)
Accumulation (range after a panic drop) → test of supply → mark-up → distribution (range at the top) →
test of demand → mark-down. "Up the stairs, down the elevator." Cycles nest in all timeframes.
- **Test of supply:** after accumulation, a down bar with a narrow range, deep lower wick and *low*
  volume = no sellers left, mark-up follows; the same bar on high volume = failed test.
- **Climax:** repeated (2-3) bars with deep wicks on very high volume at the end of a range; then a fast
  break. *Naming caution:* Coulling calls the top a "selling climax" (insiders selling), which is the
  reverse of usual Wyckoff usage (buying climax = top).
- **Stopping volume** (in a fall: deep lower wicks, narrowing bodies, rising volume) and **topping-out
  volume** (mirror in a rise) precede the climax.
- Spring / upthrust = brief break of the range edge that returns quickly; price-only version overlaps
  with the sweeps in our failed strategies 1-2. → I-41

## Other volume tools
- Volume at price (volume profile): high-volume nodes act as support/resistance, thin areas get crossed
  easily (C ch.9). Kaufman's value area (time-at-price) is the price-only cousin (K p.822-830). → I-31
- VWAP (Aziz): the most important intraday line for stock traders; price-only proxy = session-anchored
  mean of typical price. → I-38
- Intraday volume has a U/W shape (K ch.12); opening-bar volume above normal → higher-volatility day.
- Price-only activity proxy from M1: sum of M1 ranges (path length) inside a bigger bar. Not volume,
  but measures how busy the bar was. → I-43

## Verdict for us
- Coulling's method is discretionary and untested (no statistics); she says it cannot be automated.
- Testable now: zone breakouts with a close, cause-and-effect (duration), role reversal, pivot trailing.
- Later, with MT5 tick volume: A/B test each price-only rule with and without the volume condition. That
  is the only honest test of her main claim.
