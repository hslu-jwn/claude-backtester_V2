# Structure & Confluence Detection Rules

**Global invariant:** no lookahead. Every detector only sees candles up to and including the current closed candle, and a pattern exists only from the candle that confirms it. All tools are timeframe-agnostic; the strategy decides which timeframe uses which tool. Bullish described, bearish mirrored.

## Swing high / low
- High: green candle followed by red. High = highest wick of the two.
- Low: red candle followed by green. Low = lowest wick of the two.
- **Only the two candles at the turn count** (the last green and the first red for a high; dojis between them skipped). Example: green high 4410, green high 4408, red high 4405 → swing high = 4408, not 4410. Lows mirrored.
- The swing is confirmed at the close of the turning candle (the red one for a high).
- Doji/thin candles are skipped and don't break the pattern, so a swing can span more than 2 candles.
- **Doji/thin candle:** body |close − open| ≤ a per-symbol maximum (setting). XAUUSD: 0.065 (user-defined, same on every timeframe). Bid prices, as on the chart.
- **Other pairs: gold is the reference** (rule confirmed by the user). Their threshold covers the same share of a typical candle as gold's: 0.065 is 1.53% of gold's median 5m candle range (4.255, XAUUSD 2026-09-01..07), so a pair's default is 1.53% × its own median 5m range. Every pair's value can be changed in the settings. GBPUSD: median 0.00028 → 0.0000043 (below one point: only zero-body candles are dojis). GBPJPY: median 0.066 → 0.00101 (bodies of 0–1 point). Both measured on histdata.com 2026-09-02..30 (`data.check` prints the values). Pairs without a value get no swings.
- A turning candle also starts the next swing: green, red, green gives a high (confirmed by the red) and a low (confirmed by the second green).
- If both turn candles have the same extreme wick, the swing belongs to the earlier candle.

## Break of structure (BOS)
- **Bullish BOS:** a candle **closes above** the most recent confirmed swing high (its wick price). **Bearish BOS:** a candle closes below the most recent confirmed swing low. A wick alone never counts.
- **Only a move in the BOS direction counts** (rule set by the user): a bullish BOS needs a green breaking candle (close > open), a bearish BOS a red one. A red candle closing above the high (e.g. after a gap up) is no bullish BOS. A doji (body ≤ the symbol's doji threshold, see Swing high / low) is neither green nor red, so it never causes a BOS.
- The swing must already be confirmed when the breaking candle closes (no lookahead). Each swing level can be broken only once (the first close beyond it).
- **Only the most recent swing counts** (rule set by the user): once it is broken, there is no further BOS in that direction until a new swing high (low) is confirmed, even if price later closes above an older, higher high that was never broken. A close through several highs at once is one BOS, against the most recent one.
- **A BOS only happens against the current trend** (rule set by the user): in a downtrend a close below the latest swing low (a lower low) is **no BOS**; in an uptrend a close above the latest swing high (a higher high) is no BOS. Such a close changes nothing, but the swing level counts as broken (each level only once). So BOS directions alternate; before the first BOS on a chart either direction counts.
- Works the same on every timeframe.

## Trend
- **Defined only by BOS** (rule set by the user; replaces the earlier higher-high/higher-low rule):
  - after a bullish BOS the market is in an **uptrend**, after a bearish BOS in a **downtrend**;
  - it stays in that trend until a BOS in the other direction occurs (that BOS flips it immediately);
  - a break in the trend's own direction is no BOS (see above) and changes nothing, so every BOS after the first one flips the trend.
- Before the first BOS on a chart there is no trend yet.
- **Overall trend = the 4H trend** (rule set by the user): the trend above, on the 4H chart. The timeframe is a setting (`TrendConfig.overall_timeframe`, default 4H), so it can be changed and compared in backtests. On a lower timeframe it is read without lookahead: only 4H candles closed at the current candle's close count. Each timeframe also has its own trend from its own BOS (e.g. the 5m trend); "the trend" without a timeframe means the overall trend.

## Strong-move filter
- A candle is a strong move if its range (high − low) ≥ k × ATR(n). Default k = 2, n = 14 (n still to be swept); k and n are settings.
- **ATR as on TradingView:** true range (max of high − low, |high − previous close|, |low − previous close|; the first candle uses high − low) smoothed with Wilder's RMA, seeded with the simple average of the first n true ranges. Gaps (daily break, weekend) therefore count.
- The candle is compared with the ATR of the n candles **before** it (the ATR known at the previous candle's close), so a big candle doesn't raise its own threshold. While fewer than n earlier candles exist, no candle is a strong move.
- The ATR is on the **same timeframe** as the candle being checked (a 5m FVG uses the 5m ATR, a 30m FVG the 30m ATR).
- The filter can be **switched on/off separately** for FVGs and for order blocks (settings, default on), so backtests can compare with and without it.
- **FVG:** the middle candle (candle 2, the push that creates the gap) must be a strong move.
- **Order block:** at least one candle of the move *away* from the OB (from the first opposite-color candle after the leg until the move's next swing point) must be a strong move.
- Breakers and BPRs inherit it: a breaker comes from a filtered OB, a BPR from filtered FVGs.

## Validation (FVG, OB, breaker, BPR, no exceptions)
- **Tap:** a wick into the zone is enough; no close inside needed.
- **Confirmed (usable for entry):** **after a tap**, a candle closes beyond the zone boundary in the zone's bias direction (bullish: green close above the top). It can be the tapping candle itself (wick into the zone, close back outside) or a later candle. Without a tap first there is no confirmation, so an FVG's own third candle never confirms it (rule set by the user).
- **Invalidated:** a candle closes beyond the opposite boundary.
- A zone stays usable for the strategy until it is invalidated (strategy rules may end it earlier, e.g. at the session end). How long it is *drawn* is display only and never limits its use.

## Fair value gap (FVG)
- 3-candle pattern; the gap lies between the wicks of candle 1 and candle 3. Candle 2's wick is ignored.
- Bullish in an uptrend, bearish in a downtrend: the trend of the **FVG's own timeframe** (a 5m FVG uses the 5m trend), not the overall 4H trend (rule set by the user).
- An FVG is used when price **retraces back into it**: a bullish FVG forms in a move up, and a later bearish move into it uses it (taps it). Bearish mirrored.
- **On the chart** (display only, rule set by the user):
  - drawn from the moment it forms (close of candle 3), from candle 1 to the right;
  - extends **8 candles** of its own timeframe after forming (setting); if price hits it (a wick into it) later, the drawing extends up to that hit candle, so it reaches the latest hit;
  - stops at the candle that **invalidates** it, whatever comes first;
  - confirmation changes nothing on the general chart (the strategy's session view draws confirmed confluences darker).
  - The 8-candle limit is only visual: an FVG that was never hit within 8 candles can still be tapped, confirmed and used later.

## Order block (OB)
- Range = the entire consecutive same-color leg from the prior swing point to the swing extreme before reversal, from the lowest wick to the highest wick of the leg.
- Green leg (e.g. HL→HH at the top of an uptrend) = bearish OB. Red leg (e.g. HH→HL, or into a low of a downtrend) = bullish OB.
- A doji inside the leg is ignored. An opposite-color candle ends the leg immediately, and its wick is excluded.

## Breaker block
- An OB invalidated by a later BOS through the level it defended becomes a breaker: same range, OPPOSITE bias.
- Example: an uptrend's HH→HL leg is a bullish OB. If a candle later closes below that HL, the zone becomes a bearish breaker. Works in both directions.

## Balanced price range (BPR)
- Overlap of a bullish and a bearish FVG. One is usually invalidated as the other forms, so the invalidated one's stored range is used.
- Staleness-over-time rule is deferred to the strategy layer.

## Equilibrium (currently NOT used for entries)
- 50% of the most recent swing leg: upper half = premium, lower half = discount.
- Bullish confirmation: price retraces into discount, then a bullish candle closes back in premium.
- Invalidated by a close or wick below the leg's swing low.

## SMT divergence (future, needs multiple symbols)
- Compare the latest swings of two correlated symbols at the same time. If one makes a stronger swing (HL) while the other makes a weaker one (LL), expect the weaker one to reverse and follow the stronger one.
- Only valid on 5m+ timeframes, and requires an overall market bias.
