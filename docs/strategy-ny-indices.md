# Strategy 2: New York Open Index Sweep

**Instruments:** NAS100, US500. Long described, short mirrored. Detection rules (swing, BoS, trend, sweep, confluences, EQ) are in `confluences.md`. Defined with the user on 2026-10-09/10. Strategy logic goes in `strategy/ny_index_sweep/`.

> Note: **order blocks** use the first OB version (the new OB rules are on hold, `confluences.md` › Order block).

## General
- **Windows (ET, NY DST)** ⚙️:
  - AM: open 09:30 → window 09:00–11:30
  - PM: open 14:00 → window 13:30–16:00
- The whole setup, from sweep to entry, must happen inside the window. Untriggered setups die at window end. Open trades keep running (no force close).
- Best time AM 09:50–10:10 and PM 13:50–14:10: trades are tagged, with an include/exclude toggle.
- ⚙️ Max trades per session per index (default 1). Counted separately for NAS100 and US500. Every re-entry counts.
- **Candles:** 1h on full hours; 4h closing at 02/06/10/14/18/22 ET (TradingView alignment, built from 1m data); all other timeframes standard.
- **Read once before the session (frozen):** the bias and, for the AM, the timeframe route. Only trades in the bias direction.
- **Trend:** › `confluences.md` › Trend (defined only by BoS). No sideways state.
- **BoS = a real BoS only** (`confluences.md` › Break of structure: only against the current trend of that timeframe; rule set by the user 2026-10-10, **no setting**). If the setup TF is already in the bias direction's trend when the sweep happens, a close above the swing high is no BoS and the setup does not continue. Same for the entry-TF BoS.
- **Which swing high the BoS breaks:** the **most recent** confirmed swing high (`confluences.md` › Break of structure), also when a lower high formed between the sweep and the BoS (rule set by the user 2026-10-11; "the last swing high before the sweep" is to become a backtest setting later, ROADMAP 8.4).
- **Sweep:** › `confluences.md` › Liquidity sweep: wick beyond the **most extreme** of the last ⚙️ 3 swing lows/highs on the sweep TF (bullish: below the lowest of the last 3 lows; rule set by the user 2026-10-11), followed by a BoS in the bias direction within ⚙️ 10 sweep-TF candles (separate setting for AM and PM).
- **No trend yet** (rule set by the user 2026-10-11): no 4h trend (AM) or no 15m trend (PM) = no bias = no trades in that window. A 1h trend of "none" counts as "different from 4h" (→ 15m / 5m route). In practice only at the start of the data.
- **3rd confluence:** the confluence of step 3. It must lie inside the BoS move (sweep extreme → BoS candle). A tap (wick) is enough.
  - **Inside the move = by time** (rule set by the user 2026-10-11): formed by candles from the sweep extreme up to and including the BoS candle. Price-wise it can never lie below the sweep extreme (a close there would be an opposite BoS and cancel the setup). Confluences formed **after** the BoS candle (while price keeps running before the retracement) do **not** count.
  - Confluences **created by that BoS** count as inside the move even if their candles are older: the breaker (move into the broken high) and the OB of the sweep (rule set by the user 2026-10-10), and the EQ of the move. Same on the entry TF (entry-TF BoS move).
  - **The tap** is any closed **entry-TF** candle (1m, or 5m on the 15m route) whose wick goes into the zone, after the BoS candle (rule set by the user 2026-10-11; like the AM HTF sweep, registered at the moment of the wick, not at the setup-TF close).
  - **Order:** the entry-TF BoS candle closes at or after the tapping candle; the tapping candle itself may be the BoS candle.
- **Entry confluence:** formed in the entry-TF BoS move. Needs a tap AND a confirmed close beyond it (EQ too).
- ⚙️ **Entry-TF confluence entry** (default ON). OFF = enter immediately at the close of the entry-TF BoS candle; no entry-TF confluence is needed. SL/TP rules stay the same (SL is based on the 3rd confluence).
- **Confluence ranking:** OB > BB > BPR > FVG > EQ. Only used when several confluences are **hit by the same candle**; if zones overlap but only one gets hit, that one counts even if it ranks lower (`confluences.md` › Overlapping confluences). ⚙️ Each type can be switched on/off. Only confluences in the bias direction are used.

## PM Session
1. **Bias:** 15m trend before the window.
2. **Sweep** against the bias on 15m or 5m (bullish: the wick goes below the lowest of the last 3 swing lows).
3. **BoS** in the bias direction on the same timeframe as the sweep: close above the last swing high before the sweep.
   - If a 5m setup is running and a 15m BoS forms from the same sweep, the 15m setup replaces it (new move, new 3rd confluences, counts on 15m). A trade already opened from the 5m setup keeps running.
   - **Same sweep** (rule set by the user 2026-10-11): the 15m sweep extreme has the same price as the 5m sweep extreme, and the 5m sweeping candle lies inside the 15m sweeping candle.
4. **3rd confluence:** on 5m, inside the BoS move (for EQ: the 15m leg if the BoS is on 15m). Wait for a tap.
5. **1m BoS** in the bias direction: close above the previous 1m swing high.
6. **1m confluence** formed in that 1m BoS move: tap, then a confirmed close beyond it.
7. **Enter** at that close. (Setting OFF: enter at the close of the 1m BoS candle, skip step 6.)

## AM Session
1. **Bias:** 4h trend before the window.
2. **Route** (decided before the window, frozen): 1h trend same as 4h → setup TF 5m, entry TF 1m. Different → setup TF 15m, entry TF 5m.
3. **HTF sweep** on 1h or 4h against the bias (bullish: the wick goes below the lowest of the last 3 confirmed swing lows of the 1h or of the 4h).
   - Registered at the moment of the wick; at the HTF candle close it is checked that it is still a valid sweep. The only check is the close-beyond setting (rule set by the user 2026-10-11): with the default (a close beyond still counts) nothing cancels at the close; with the setting off, a close beyond the swept level cancels the sweep and the setup built on it.
4. **Setup TF:** BoS in the bias direction, then the 3rd confluence in that move. Wait for a tap.
5. **Entry TF:** BoS in the bias direction.
6. **Entry-TF confluence** formed in that move: tap, then a confirmed close beyond it.
7. **Enter** at that close. (Setting OFF: enter at the close of the entry-TF BoS candle, skip step 6.)

## Rules
- **New setup = new sweep.** A new setup can start at any time, even while a trade of an earlier setup is open.
- **One open trade per setup at a time.** No entries on several overlapping confluences of the same setup.
- **3rd confluence invalidated** (close through it): use the next 3rd confluence in the same move.
- **Entry confluence invalidated or not confirmed:** wait for another one, as long as the 3rd confluence is still valid.
- **Opposite BoS on the entry TF:** go back to step 5 and wait for a new entry-TF BoS.
- **Opposite BoS on the setup TF** after our BoS: the whole setup is cancelled.
  - Before our BoS, a close beyond the swept level is still part of the sweep (⚙️ setting).
- **Re-entry:** allowed after any closed trade (SL, BE or TP) as long as the setup is still valid and the max trades per session isn't reached.
  - After a wick SL: re-enter via a new entry-TF BoS + confluence in the same 3rd confluence, or via the next 3rd confluence in the move.
  - SL/TPs are recalculated for each new entry.
- **Timeout:** if the 3rd confluence isn't tapped within ⚙️ 25 setup-TF candles after the original BoS candle, the setup is cancelled. Re-entries keep counting from the original BoS. The tapping candle must close at most 25 setup-TF candles after the original BoS candle's close (rule set by the user 2026-10-11).

## Stop Loss
- **Standard:** below the low of the 3rd confluence, plus a buffer of ⚙️ 10% of its height.
- ⚙️ Narrow-confluence threshold (default 0 = off). If on and the confluence is narrower, the SL goes below the sweep extreme instead.
- **EQ as 3rd confluence** (zone = whole leg):
  - Default: SL beyond the swing extreme, buffer = 10% of the distance swing extreme → deepest wick into the EQ (before entry).
  - ⚙️ EQ-only toggle: SL beyond the deepest wick into the EQ instead, buffer = 10% of the same distance.
  - A wick beyond the swing extreme (no close): SL beyond that wick (`confluences.md` › Equilibrium).
  - Example long: swing low 100, BoS high 200, 50% = 150, deepest wick 140 → distance 40 → default SL 96, toggle SL 136.
- After TP1 is hit, the SL moves to break-even (incl. spread and fees) and stays there.

## Take Profit
- The position is split into 3 equal parts.
- **Rejection zones:** untouched swing highs and unmitigated opposite confluences (FVG/OB/BB/BPR).
  - AM: 1h + 4h. PM: 15m.
  - Higher TF is stronger: when two zones are close together, the higher-TF one is used.
  - Zones less than ⚙️ 0.2R apart count as one; within such a cluster the higher-TF zone's level is used.
  - Untouched swing high = no later wick has reached it; unmitigated confluence = never tapped since it formed (as in strategy 1). The TP sits at the zone's near edge (bottom for a long). (Rules set by the user 2026-10-11.)
- **TP1:** near edge of the first rejection zone ≥ 1.2R. Zones below 1.2R are ignored. No upper limit, so there is always a trade.
- **TP2 / TP3:** the next rejection zones beyond TP1.
- **ATH fallback** (no rejection zone left above the entry / TP1 / TP2; the same as the entry being above the highest high of all data **before the entry**, no lookahead: below the all-time high there is always an untouched high above; rule set by the user 2026-10-11). ⚙️ Mode:
  - **Fib** (default): extension of the setup-TF BoS leg (sweep extreme = 0, BoS high = 1). Levels 1.382 / 1.5 / 1.618 / 2.0. TP1 = first level ≥ 1.2R, TP2/TP3 = the next levels.
  - **Fixed R:** TP1 = 1.2R, TP2 = 1.5R, TP3 = 1.8R.
  - If zones run out after TP1 or TP2, the remaining TPs use the fallback levels above the last TP.
  - If the levels run out, the remaining parts close at the last available TP (e.g. TP2 closes ⅔).

## Backtest options (⚙️)
- Trading windows (AM/PM) and best-time tag (toggle)
- Max trades per session per index (1)
- Sweep: lookback N swings (3; the wick must go beyond the most extreme of them), close beyond the level allowed (yes), BoS within X sweep-TF candles (10, separate for AM/PM)
- 3rd-confluence timeout (25 setup-TF candles)
- Confluence types on/off (OB, BB, BPR, FVG, EQ)
- Entry-TF confluence entry (ON; OFF = enter at the entry-TF BoS close)
- SL buffer (10%), narrow-confluence threshold (0 = off), EQ SL at deepest wick (off)
- Rejection-zone clustering (0.2R), minimum TP1 (1.2R)
- ATH fallback mode (fib / fixed R) and its levels
- Risk management (risk per trade, costs, daily stop, open risk, starting balance 100,000 USD): `risk-management.md`, not part of this strategy (trades in R only).

## Chart / UI
- The Sessions button changes with the chosen strategy: for Strategy 2 it shows the AM/PM windows.
- Session view (like Strategy 1): pick one AM or PM session and see everything the strategy used there (sweep, BoS, 3rd confluence, entry confluence, SL/TPs).

## Open points
- Strategy 1 keeps its zone sweep; EQ is now on there too, with the same EQ SL rules.
- ATH fallback section might get a rework later (fine for now).
- Data must reach back far enough before the backtest start for the ATH check (warm-up period). histdata.com has both indices from 2010; cached: 2018-01 .. 2026-09, so backtests can start 2020-01-01 with 2018-2019 as ATH and warm-up history (ROADMAP 0.5).
