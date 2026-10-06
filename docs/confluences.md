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
- The filter can be **switched on/off** for FVGs, so backtests can compare with and without it. Default **off** (rule set by the user: at k = 2 it removed far too many FVGs). Order blocks no longer use it (rule set by the user, 2026-10-06: the sweep and the BOS are enough).
- **FVG** (when switched on): the middle candle (candle 2, the push that creates the gap) must be a strong move.
- BPRs inherit it: a BPR comes from filtered FVGs.

## Validation (FVG, breaker, BPR; OBs only use the invalidation, see › Order block)
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

## Liquidity sweep
- **Idea** (user): liquidity causes reversals, a BOS shifts the market's structure, and FVGs and equilibrium are retracement patterns (e.g. once an OB has formed and price revisits it with pressure out of it, an FVG can be used to enter). The sweep is the liquidity part.
- A candle **sweeps a swing high** when its wick goes **above** the swing's price (touching it is no sweep). The candle may also close above it: a close above still counts as a sweep (rule set by the user). Swing lows mirrored (wick below).
- Only **confirmed** swings can be swept: the swing must be confirmed by an earlier candle than the sweeping one.
- **Which highs count** (rule set by the user): any confirmed swing high, not only the most recent one ("depends on context"; in the user's example it wasn't the previous high). The same high can be swept **more than once**.
  ⚠️ Open: how far back a high still counts, and when the same high can be swept again (see the open questions in ROADMAP 2.11).
- Exists at the close of the sweeping candle. Timeframe-agnostic, like every detector.
- Strategy 1's session-zone sweep (a wick into a session zone) is the strategy's own rule and stays in `strategy/session_zone_sweep/`; this detector sweeps swing levels.
- **On the chart:** a thin magenta line at the swept swing's price, from the swing's extreme-wick candle to the sweeping candle, with a small marker on the sweeping wick and a hover (swing, sweep candle, closed back inside or not). Every sweep is drawn, also when no BOS follows, so the detector can be checked on its own (rule set by the user).

## Order block (OB)
Rules set by the user on 2026-10-06; they replace the earlier OB rules (leg into the most recent swing at any BOS, strong-move filter).
Described for a bullish OB, bearish mirrored. The user's example is bearish: XAUUSD, a previous high at 3947.89 is swept by the move up, a big red candle then makes the bearish BOS, and the green candles of the move up into the sweep are the OB; price later came back up into it.
- **Forms when a liquidity sweep is followed by a BOS:** a candle sweeps a confirmed swing low (› Liquidity sweep), and the **next move up** makes a **bullish BOS** (› Break of structure, so only against the trend).
- **The chance ends** when price goes below the sweep's low again before the BOS (rule set by the user). A new low without a BOS just means the market keeps going down; the new low can itself be the next sweep.
- Since a BOS only happens against the trend, a sweep in an established trend's direction gives no OB (confirmed by the user, bearish case: in a downtrend a wick above a high, then a close below the low, is no BOS, so **no OB**). If the sweeping candle itself closes beyond the swept level and that is a BOS, the trend flips and the following BOS in the other direction can form the OB.
- **Range** = the red candles of the move down into the sweep, from the lowest wick to the highest wick (rule set by the user: wicks for now; sometimes only the bodies matter, possibly a setting later). Walking back from the sweep, the first green candle ends the leg and is excluded, so with green, green, red, green, green before a bearish sweep only the last two greens form the OB. Dojis are skipped and their wicks don't count. If the sweep's extreme wick is on a green candle (the low's green turn candle), that candle is not in the bullish OB.
  ⚠️ Open: if the move up from the sweep makes a higher low before the BOS (above the sweep, so the chance is still alive), is the OB the leg into the sweep or the leg into that higher low? (ROADMAP 2.12)
- **Exists from** the close of the BOS candle. **No strong-move filter** for OBs (rule set by the user: the sweep and the BOS are enough).
- **Valid until broken to the other side** (rule set by the user): a candle closes beyond the far edge (bullish OB: a close below its bottom). That close invalidates it for good. Tap and confirmation (› Validation) only matter for strategies and are left out of the OB detector until a strategy needs them.
- Use (strategy matter, not the detector's): higher-timeframe OBs can serve as TP targets / obstacles; a revisit of the OB with pressure out of it, plus an FVG, can be an entry.
- **On the chart:** from the leg's first candle until the candle that closes beyond its far edge, up to the cursor while still valid. Every OB is **yellow**, whatever its direction (rule set by the user). Sub-entry ✕ for the invalidation only.

## Breaker block
- ⏸ **Waiting for the user** ("I'll clarify once it's relevant"). The earlier rule (an OB invalidated by a later BOS becomes a breaker of the opposite bias) is no longer assumed.
- First hint (user, 2026-10-06, not a rule yet): a breaker is usually the previous move up (all its candles, incl. wicks) before a BOS to the upside, and vice versa.
- Decided already (rule set by the user): validation like all zones (› Validation), drawn from the breaking candle onward; every breaker is **orange** on the chart, whatever its direction.

## Balanced price range (BPR)
- Overlap of a bullish and a bearish FVG: an older FVG invalidated by the move that creates a newer FVG in the opposite direction. The older one's stored range is used.
- **Range** = the overlap of the two FVG ranges (no overlap, no BPR).
- **Direction** = the direction of the **newer** FVG (rule set by the user). Example: a bearish FVG, then price reverses up and leaves an overlapping bullish FVG → bullish BPR.
- **Timing** (rule set by the user): the older FVG must be **invalidated by the same move that creates the newer one**, i.e. by a candle from the newer FVG's candle 1 to its candle 3. An older FVG that is still open when the newer one forms, or was confirmed or invalidated before the newer one's candle 1, forms no BPR. (Invalidation by candle 1 can't give an overlap: candle 1's wick is then beyond the older FVG and is the newer gap's edge.)
- **Pairs** (rule set by the user): if the move invalidates several older opposite FVGs that overlap the newer one, each of them forms its own BPR with it. An older FVG forms **at most one BPR**: if the move creates two newer FVGs that both qualify, only the first one (the earlier candle 3) pairs with it.
- Exists from the close of the newer FVG's candle 3. Validation as in › Validation, starting with the next candle.
- Further staleness rules, if any, are the strategy's.
- **On the chart:** like the FVG: from the older FVG's candle 1 until the candle that confirms or invalidates it, up to the cursor while still open. Every BPR is **purple**, whatever its direction (rule set by the user).

## Equilibrium (currently NOT used for entries)
- 50% of the most recent swing leg: upper half = premium, lower half = discount.
- Bullish confirmation: price retraces into discount, then a bullish candle closes back in premium.
- Invalidated by a close or wick below the leg's swing low.

## SMT divergence (future, needs multiple symbols)
- Compare the latest swings of two correlated symbols at the same time. If one makes a stronger swing (HL) while the other makes a weaker one (LL), expect the weaker one to reverse and follow the stronger one.
- Only valid on 5m+ timeframes, and requires an overall market bias.
