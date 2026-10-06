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
- The filter can be **switched on/off separately** for FVGs and for order blocks, so backtests can compare with and without it. Defaults: **off for FVGs** (rule set by the user: at k = 2 it removed far too many FVGs), on for order blocks.
- **FVG** (when switched on): the middle candle (candle 2, the push that creates the gap) must be a strong move.
- **Order block:** at least one candle of the move *away* from the OB (from the first opposite-color candle after the leg until the move's next swing point) must be a strong move.
- Breakers and BPRs inherit it: a breaker comes from a filtered OB, a BPR from filtered FVGs.

## Validation (FVG, OB, breaker, BPR, no exceptions)
Described for a bullish zone (price comes from above), bearish mirrored. Checking starts with the candle after the one that confirms the zone.
- **Tap:** a wick into the zone is enough; no close inside needed. The wick must go **into** the zone (low < top): touching the edge is no tap (rule set by the user).
- **Confirmed (usable for entry):** a candle closes beyond the zone boundary in the zone's bias direction (bullish: green close above the top). **Only after a tap** (rule set by the user); the tap may be on the same candle (wick into the zone, green close above it). A close above the top without a tap does nothing. A doji (body ≤ the symbol's doji threshold) never confirms.
- **Invalidated:** a candle closes beyond the opposite boundary (bullish: below the bottom). Any candle counts, also a doji or a green one, tapped before or not (rule set by the user).
- Confirmed and invalidated are **final**: the zone is no longer checked. What a strategy does with an invalidated zone (e.g. an inverse FVG) is up to the strategy.
- How long a zone is **drawn** on the chart is display only and never limits its use (FVG drawing: ROADMAP 2.5).

## Fair value gap (FVG)
- 3-candle pattern; the gap lies between the wicks of candle 1 and candle 3. Candle 2's wick is ignored. Bullish: candle 3's low > candle 1's high; the zone runs from candle 1's high to candle 3's low. Equal wicks are no gap. Candle 2's color doesn't matter (rule set by the user).
- Confirmed at the close of candle 3.
- **Every gap is an FVG**, in both directions, whatever the trend (rule set by the user). Which direction a strategy **uses** is the strategy's rule (strategy 1: the trend of the FVG's own timeframe, see `strategy-session-zones.md` › Entry sequence).
- Gaps across the daily break or a weekend count like any other.
- An FVG is used when price **retraces back into it**: a bullish FVG forms in a move up, and a later bearish move into it uses it (taps it). Bearish mirrored.
- **On the chart** every FVG is **green**, whatever its direction (rule set by the user). Overlapping FVGs (imbalances) are not drawn separately: their fills stack, so the overlap shows darker.

## Order block (OB)
⚠️ Provisional (user, 2026-10-06): these rules work for now, but OBs may be reworked entirely later.
- Range = the entire consecutive same-color leg from the prior swing point to the swing extreme before reversal, from the lowest wick to the highest wick of the leg.
- Green leg (e.g. HL→HH at the top of an uptrend) = bearish OB. Red leg (e.g. HH→HL, or into a low of a downtrend) = bullish OB.
- A doji inside the leg is ignored. An opposite-color candle ends the leg immediately, and its wick is excluded.
  This also holds for the swing's own turn candle (rule set by the user): if the green candle that confirms a swing low has the lower wick, that wick is **not** in the bullish OB, so the OB's bottom can lie above the swing price.
- **Only OBs that led to a BOS** (rule set by the user, for now): a bullish OB is the red leg into a swing low that is the most recent swing low when a **bullish BOS** happens (the move up from that low breaks structure). A low confirmed by the BOS candle itself counts (one green candle that confirms the low and closes above the high, rule set by the user). Bearish mirrored. Since a BOS only happens against the trend, OBs only form where the trend flips (and at the first BOS).
- **Exists from** (rule set by the user): the close of the BOS candle. With the strong-move filter on (default for OBs), additionally at least one candle of the move away (from the swing's opposite-color turn candle up to the candle **before** the one that confirms the move's next swing point; that candle starts the pullback and doesn't count, rule set by the user) must be a strong move: the OB then exists from the later of the BOS candle and the first strong candle. If the move's next swing point is confirmed with no strong candle, there is no OB.
- Validation as in › Validation, starting with the candle after the one it exists from.
- **On the chart:** like the FVG: from the leg's first candle until the candle that confirms or invalidates it, up to the cursor while still open. No 8-candle limit (rule set by the user, also for FVGs). Every OB is **yellow**, whatever its direction (rule set by the user).

## Breaker block
- An OB invalidated by a later BOS through the level it defended becomes a breaker: same range, OPPOSITE bias.
- Example: an uptrend's HH→HL leg is a bullish OB. If a candle later closes below that HL, the zone becomes a bearish breaker. Works in both directions.

## Balanced price range (BPR)
- Overlap of a bullish and a bearish FVG. One is usually invalidated as the other forms, so the invalidated one's stored range is used.
- **Range** = the overlap of the two FVG ranges (no overlap, no BPR).
- **Direction** = the direction of the **newer** FVG (rule set by the user). Example: a bearish FVG, then price reverses up and leaves an overlapping bullish FVG → bullish BPR.
- **Timing** (rule set by the user): the older FVG must still be **open** (not confirmed or invalidated) when the newer one forms, **or** be invalidated by the same move that creates the newer one, i.e. by a candle from the newer FVG's candle 1 to its candle 3. Older pairs form no BPR.
- Exists from the close of the newer FVG's candle 3. Validation as in › Validation, starting with the next candle.
- Further staleness rules, if any, are the strategy's.
- **On the chart:** no drawing of its own (rule set by the user): overlapping FVGs stack, so a BPR shows as the darker overlap of the green FVG boxes.

## Equilibrium (currently NOT used for entries)
- 50% of the most recent swing leg: upper half = premium, lower half = discount.
- Bullish confirmation: price retraces into discount, then a bullish candle closes back in premium.
- Invalidated by a close or wick below the leg's swing low.

## SMT divergence (future, needs multiple symbols)
- Compare the latest swings of two correlated symbols at the same time. If one makes a stronger swing (HL) while the other makes a weaker one (LL), expect the weaker one to reverse and follow the stronger one.
- Only valid on 5m+ timeframes, and requires an overall market bias.
