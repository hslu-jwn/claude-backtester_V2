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
3. **5m BOS up:** a 5m bullish BOS (`confluences.md` › Break of structure) during that 30m candle or after. **Only a real BOS counts** (rule set by the user): if the 5m chart is already in an uptrend, a close above the last 5m swing high is no BOS and does **not** fulfil step 3. Setting `entry_bos_with_trend` (default **off**): when on, any green 5m close above the swing high right before it counts as step 3, also in a 5m uptrend, so backtests can compare both.
4. **Confluence:** an FVG, OB, breaker or BPR (FVGs are most promising), usually formed in the BOS move; a breaker comes from the move before. Price taps it, then a green 5m candle closes above it → **enter at that close**. No confluence = no trade.
   Only FVGs in the direction of the trend of their own timeframe are used: bullish FVGs in a 5m uptrend, bearish ones in a 5m downtrend (the trend after the FVG's candle 3 closed, including a BOS made by candle 2 or 3; no trend yet = no FVG used). The FVG detector itself finds gaps in both directions (`confluences.md` › Fair value gap).

## Invalidation & reset
- A 5m close below the confluence invalidates it.
- A bearish BOS after the bullish BOS cancels the setup; restart from step 1.
- Untriggered setups die at the next session start.
- The same zone can produce more trades if the full sequence repeats from a new 30m close.
- Long and short setups may build in the same session.

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
- The SL is fixed, except at the next session start, if the trade is still open:
  - in profit → SL moves to break-even
  - in loss → original SL stays
- The trade runs until SL or TP is hit.

## Take profit
1. **Target** = the lowest point of the resistance zone, capped at **3R**.
2. **Price already above the zone** → aim for 1.2–2R at earlier 1h highs/lows or confluences.
3. **Obstacles:**
   - A major obstacle is an untouched 1h swing high, or an unmitigated bearish 1h FVG / OB / breaker, that existed before entry.
   - Obstacles less than ⚙️ 0.2R apart count as one.
   - TP may pass at most ⚙️ N obstacles and sits just below the next one.
4. **Final TP < 1.2R → no trade.**

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
- TP cap (3R), minimum R:R (1.2R), obstacles passable N (test 0–3), obstacle clustering (0.2R)
- Last 1.5h before the next session start: trades simulated but tagged; include/exclude toggle to compare the net result
- Zone kill: the 3rd break kills a zone (default); in the settings menu (4.1) as on/off plus the number of breaks; later maybe only within a time window
- Session times following each city's DST; session end = next session start (may revisit)
- Friday NY → Monday Tokyo carry-over (watch for odd behavior)
- Possibly skip the Tokyo session (low volume)
- Possibly add an overall market-bias filter
- Possibly add equilibrium back as a confluence
