# Strategy 1: Session Zone Sweep (Forex)

**Pairs:** XAUUSD, GBPJPY, GBPUSD. **Timeframes:** 30m for zones and the reaction, 5m for the BOS and entry, 1h for TP obstacles. Long described, short mirrored. Detection rules are in `confluences.md`.

## Sessions
- Starts (ET): New York 08:00, London 03:00, Tokyo 20:00. Each session follows its own city's daylight-saving shifts and ends when the next one starts.
- Local start times: Tokyo 09:00 Asia/Tokyo (no DST: 20:00 ET in US summer, 19:00 ET in US winter), London 08:00 Europe/London (04:00 ET in the weeks when US and European DST dates differ), New York 08:00 America/New_York. The ET times above are the US summer values. Sessions run Monday to Friday by their own city's date.
- A chart line is drawn at each session start, through the middle of the candle the session starts on (rule set by the user): NY 08:00 → the 08:00 candle; on 4H the candle the start falls in.
- **A candle belongs to the session it closes in** (rule set by the user): the 30m candle closing at the New York open (12:30–13:00 UTC in winter) is New York's first candle, not London's last. This holds on every timeframe, each for its own candles: 1m or 5m candles that close before the open still belong to the previous session (5m: the 12:55 candle is New York's first). Candles closing on the weekend before Tokyo's start (the Sunday open) are ignored and form no zones; the candle closing at Tokyo's start is Tokyo's first.

## Session zones (30m)
- For each session, take the single most extreme **confirmed** high and low (swing rule). If the absolute extreme is unconfirmed, use the most extreme confirmed one. A swing confirmed by the first candle of the next session doesn't count.
- **A swing belongs to the session of its extreme-wick candle** (rule set by the user): candles of a session only count for that session. A swing whose extreme is on the last London candle and that is confirmed by the first New York candle counts for neither; a swing whose extreme is on the first New York candle counts for New York. If its other turn candle is London's last, that candle doesn't count: the zone (and its box) come from the New York candle only.
- Zone size is as big as possible: the high zone runs from the highest wick to the lowest body top of its swing candles in that session; the low zone is mirrored.
- Zones are valid only during the next session (London→NY, NY→Tokyo, Tokyo→London). Friday NY zones carry into Monday Tokyo.
- **No confirmed swing** on one side in a session → no zone on that side for the next session (rule set by the user).
- **Support or resistance by price** (rule set by the user): the close of the forming session's last candle decides: a zone below that close is **support**, a zone above it is **resistance**. Example: London's zones in New York take their role from London's last close (12:00–12:30 UTC candle in winter), and New York's first candle (12:30–13:00) can already break them. If that close is inside the zone, its role is set by the first 30m close outside it (that close is no break; a doji's close never sets it; confirmed by the user).
- **Weekend** (rule set by the user): Sunday-open candles before Tokyo's start are ignored for the zones too: they form no swings and break nothing, and the role of a Friday NY zone in Monday Tokyo comes from Friday's last close.
- **Break** (rule set by the user): a 30m candle **closes beyond the whole zone** on the other side (support: close below its bottom). A wick never counts, and neither does a doji's close (rule set by the user).

## Entry sequence (long)
1. **Sweep:** a wick into the support zone.
2. **30m reaction:** a green 30m candle closes above the zone. It need not be the sweep candle; a red close never counts.
3. **5m BOS up:** a 5m bullish BOS (`confluences.md` › Break of structure) during that 30m candle or after. **Only a real BOS counts** (rule set by the user): if the 5m chart is already in an uptrend, a close above the last 5m swing high is no BOS and does **not** fulfil step 3. Setting `entry_bos_with_trend` (default **off**): when on, any green 5m close above the swing high right before it counts as step 3, also in a 5m uptrend, so backtests can compare both. In the user's manual trades this happens sometimes ("just a lower low", short case), always with a **close** beyond the swing, never a wick only (rule set by the user, 2026-10-07): worth testing with the setting on.
4. **Confluence:** an FVG, OB, breaker, BPR or **equilibrium** (FVGs are most promising; equilibrium added by the user 2026-10-07, own on/off switch `use_equilibrium`, default on), usually formed in the BOS move; a breaker comes from the move before. Price taps it, then a green 5m candle closes above it → **enter at that close**. No confluence = no trade.
   **Equilibrium entry** (user's trade 1 on 2026-09-14, confirmed by the user 2026-10-07): the leg is the BOS move, from the BOS leg's low to the move's high: the **first** 5m swing high confirmed after the BOS candle (the pullback has started). The leg stays fixed, even if price makes a higher high before the pullback reaches the discount half. Its lower half (discount: from the 0.5 level down to the leg's low) works like a zone: a wick below 0.5 is the tap, a green 5m close back above 0.5 confirms → enter at that close; a **close** below the leg's low invalidates it (a wick doesn't, rule set by the user). SL below the leg's low, like any confluence. Short mirrored (upper half, premium).
   Only FVGs in the direction of the trend of their own timeframe are used: bullish FVGs in a 5m uptrend, bearish ones in a 5m downtrend (the trend after the FVG's candle 3 closed, including a BOS made by candle 2 or 3; no trend yet = no FVG used). The FVG detector itself finds gaps in both directions (`confluences.md` › Fair value gap).

## Invalidation & reset
- A 5m close below the confluence invalidates it.
- A bearish BOS after the bullish BOS cancels the setup; restart from step 1.
- Untriggered setups die at the next session start.
- The same zone can produce more trades if the full sequence repeats from a new 30m close.
- Long and short setups may build in the same session.
- Several trades open at once are allowed (the user: very unlikely in practice); no limit for now.

## Zone flips
- A red 30m close below support flips the setup to a short. That close counts directly as the 30m reaction, so go straight to the 5m BOS. Same the other way round.
- **Breaks** (rule set by the user, backtested by them): the 1st break flips the zone (support → resistance), the 2nd break flips it back, the **3rd break kills it** for the rest of the session. The number of breaks that kills a zone is a setting (default 3).

## Session zones on the chart (for testing, provisional)
- Drawn like the other confluences (always visible when the overlay is on). The user wants to change this later (session view, 3.5).
- **Color = the session the zone is active in** (Tokyo yellow, London blue, New York red, like the session lines), so a zone formed in London and active in New York is red. Replaces the light blue for now.
- From the swing candle where the zone formed to the end of the session it is active in; stops at the candle that kills it. Flips are not marked.
- Dotted edge. Only the part in the session where the zone is used is filled; the part in the session it formed in is an outline only (rule set by the user).
- Shown on the 30m chart and below, down to 5m (rule set by the user). On a lower chart a 30m candle counts only from the close of the chart candle that ends with it. The fill starts with the chart candle that closes at the active session's start and the box ends with the last chart candle closing before its end (5m: 12:55 to 23:50 UTC for New York in winter).

## Stop loss
- Just below the entry confluence's low, plus a buffer ⚙️.
- If the confluence is small (⚙️ height < 0.5 × ATR): SL goes below the BOS leg's low instead.
- **SL size** (rules set by the user, 2026-10-07), measured in 5m ATR at the entry:
  - **Big SL:** the trade is still taken (smaller position, same risk; in R nothing changes), as long as the SL isn't unreasonable: setting `max_sl_atr_mult` (default off) skips trades whose SL is wider. The TP must then still be at a real level (› Take profit), never a far fixed R.
  - **Small SL:** widened to `min_sl_atr_mult` × ATR when it is tighter than that ("I widen a very small one, but if it's not necessary I leave it"); default **off** (no starting value, confirmed by the user 2026-10-07), to be swept.
- The SL is fixed, except at the next session start, if the trade is still open:
  - in profit → SL moves to break-even. **Break-even includes the costs** (rule set by the user): the SL is placed so that a hit ends at 0R after spread and commission (long: entry + spread + commission in price units; short mirrored). "In profit" = the close is beyond that level; otherwise the original SL stays.
  - in loss → original SL stays
- The trade runs until SL or TP is hit.

## Take profit
Reworked by the user on 2026-10-07 (replaces "zone bottom capped at 3R, otherwise 1.2–2R"). Described for a long, short mirrored. All levels must exist at the entry.
1. **Possible reversal levels** (where a TP may sit), nearest first above the entry:
   - the near edge (bottom) of a resistance **session zone**;
   - an untouched **1h swing high** (a previous high no later 1h wick has reached);
   - the near edge of an unmitigated bearish **1h order block**.
   1h FVGs don't count (rule set by the user). Levels less than ⚙️ 0.2R apart count as one.
   1h OBs and highs are references only: they don't always hold, so a TP may lie **beyond** them.
2. **4H order blocks are a must** (rule set by the user): no TP beyond the nearest unmitigated bearish 4H OB above the entry; a TP sits just below it at the latest. If that OB is closer than the minimum R → no trade.
3. **Two TPs** (rule set by the user): half the position (⚙️ 50%) closes at **TP1**, the rest at **TP2**; after TP1 the SL of the rest moves to break-even (with costs, as above).
   - **TP1 (conservative)** = the first level at or beyond the minimum R (⚙️ `min_rr`, default 1.2R). Levels closer than that are passed.
   - **TP2 (a bit higher)** = the next level after TP1 (⚙️ `obstacles_passable`: how many further levels it may pass), never beyond the 4H OB limit and ⚙️ `tp_cap_r` (3R).
   - No further level before the limit → the whole position closes at TP1.
4. **No level in reach** (none between the minimum R and the 4H limit / cap): TP at the **minimum R** (⚙️ `min_rr`) (rule set by the user: "every trade with a good setup is taken").
5. Result in R = the weighted sum of both parts (e.g. 0.5 × TP1 R + 0.5 × TP2 R, or 0.5 × TP1 R + 0.5 × 0R after break-even).

## Trades on the chart
Rules set by the user (2026-10-07). Part of the strategy-1 UI, like the session view.
- **Overlay "Trades"** (in the Overlays panel): every trade the backtest took on the shown range, as a TradingView-style **position box**.
  - Long: entry line; **green** from entry up to the TP, **red** from entry down to the SL. Short flipped (green below, red above).
  - From the entry candle to the candle where TP, SL or break-even was hit. Still open at the cursor (replay) → up to the cursor.
  - R:R on the box. Hover: entry, SL, TP, result in R (before and after costs), exit reason (TP / SL / break-even / end of data), confluence type.
  - Break-even: a line at the moved SL from the candle it moved on (display choice).
- **Sub-entry "↳ trade confluences"** (one switch, for all trades at once, rule set by the user): draws what led to each trade, in the **normal overlay colors** of each type:
  - the **session zone** that was swept (session-zone style);
  - the **5m BOS** of the setup (red BOS line from the broken swing to the BOS candle);
  - the **entry confluence** (FVG green, OB yellow, BPR purple), from where it formed to the entry candle;
  - the **BOS move's low** (short high for a short) when the SL was placed there because the confluence was small: a line at that price from its candle to the entry (display choice: thin dashed, neutral color, label "SL ref").
  - No markers for the sweep candle or the 30m reaction (rule set by the user).
- **Replay** (no lookahead): a box appears at the close of the entry candle and grows candle by candle until TP / SL; its confluences appear with it.

## Session inspection view (chart)
How the user checks strategy 1 session by session. Part of the strategy-1 UI, so other
strategies are not affected.
- **Default chart is empty:** candles and session lines only, no zones, confluences or trades.
- **Select a session:** left-click a session's vertical start line. The session runs from
  that line to the next session line. Clicking outside the chart turns the session view off.
- **Shown for the selected session** (static by default, from the backtest results):
  - **Session zones** of the previous session (high and low zone): light blue fill with a
    darker blue edge, drawn from where they formed and extended to the end of the selected
    session. No extra markers for flips or kills.
  - **Confluences** (FVG, OB, breaker, BPR) that were part of a setup in this session,
    including setups that never triggered or were cancelled. Light green = bullish,
    light red = bearish; drawn darker if the setup confirmed them. Drawn from the candle
    they formed until they were used for entry, invalidated, or the session ended.
    No reason labels for cancelled setups; the user reads those from the chart.
  - **Trades** as TradingView-style long/short position boxes: entry line, green zone
    entry → TP, red zone entry → SL, R:R on the box. The box starts at the entry candle and
    ends at the candle where TP or SL was hit. No markers for sweep, 30m reaction or BOS.
- **Replay this session:** a button steps through the selected session candle by candle
  (same no-lookahead replay as 1.2); zones, confluences and boxes appear only once they
  exist at the replay time.

## Backtest options (tunable; review periodically)
- Strong-move filter: ATR multiplier (default 2×) and lookback; on/off for FVGs (default off). OBs: on (default) while the first OB version is in use; the new OB rules drop it (on hold, ROADMAP 2.12).
- Step 3 with the 5m trend (`entry_bos_with_trend`, default off: only a real 5m BOS, i.e. against the 5m trend, counts)
- Small-confluence threshold (default 0.5 × ATR); SL buffer
- TP cap (3R), minimum R (1.2R, also the TP when no level is in reach), levels passable for TP2 (test 0–3), level clustering (0.2R), TP1 share (50%), break-even after TP1 (on)
- SL size: `max_sl_atr_mult` (default off), `min_sl_atr_mult` (widen tighter SLs; default off)
- Equilibrium as entry confluence (`use_equilibrium`, default on)
- Last 1.5h before the next session start: trades simulated but tagged; include/exclude toggle to compare the net result
- Zone kill: the 3rd break kills a zone (default); in the settings menu (4.1) as on/off plus the number of breaks; later maybe only within a time window
- Session times following each city's DST; session end = next session start (may revisit)
- Friday NY → Monday Tokyo carry-over (watch for odd behavior)
- Possibly skip the Tokyo session (low volume)
- Possibly add an overall market-bias filter
- Possibly add equilibrium back as a confluence
