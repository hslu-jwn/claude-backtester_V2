> Reading notes, own words, made 2026-10-14 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

# Coulling, "A Complete Guide to Volume Price Analysis" (2013) - reading notes

Note: the extracted text has no page numbers, so locations are given as chapter / figure numbers (Fig x.y) and rough .txt line numbers (L...).

## Overview
- Whole book read (Foreword, Ch 1-12). It is a discretionary, chart-reading method (VPA = volume price analysis), built on Wyckoff / Dow / Livermore / Richard Ney. No tested statistics, no backtest, no performance numbers, no risk model beyond "1% rule" and "stop beyond the wick / on the other side of the congestion zone".
- Core claim: price alone only shows what happened; volume validates or contradicts it. Every signal is either "validation" (volume agrees with price move) or "anomaly" (volume and price disagree). Anomalies are the trade cues.
- Author is explicit that the method is "an art, not a science", is subjective, and "cannot be automated". For us this is a red flag (untestable as stated) but parts can be rule-ified.
- Narrative framework: "insiders" (market makers / big operators) run campaigns: accumulation (buy low after fear), test, mark-up, distribution (sell into greed), selling climax, mark-down. Wyckoff's three laws: supply and demand; cause and effect (longer sideways build-up -> bigger move); effort vs result (volume vs bar range).
- Hard-data stance: she says tick volume in spot FX is fine ("all volume is relative", consistency within one feed matters, not accuracy). She trades 5/15/30m FX, daily stocks, futures tick charts.
- Parts that do NOT depend on volume and are testable on our M1 histdata: candle-shape rules (hammer / shooting star / long-legged doji / hanging man), 3-bar pivots, congestion-zone detection and breakouts, "ceiling becomes floor" role reversal, multi-timeframe filter (benchmark / trade / fast chart), rising/falling triangle, pennant, triple top/bottom.
- Overall value for us: low for new alpha (nothing quantified, heavy overlap with our failed SMC strategy 1 and sweep ideas), but gives precise Wyckoff vocabulary, an explicit volume-proxy list, and a few cleanly definable price-only rules.

## Chapter notes

### Foreword and Ch 1 - "There's Nothing New in Trading" (L286-895)
- Foreword: author learned volume from a paid 2-week course (Albert Labos); anecdotal. No method content.
- Ch1: Dow's three trend stages (accumulation, public participation / trend-following, distribution) and primary/secondary/minor trends. Wyckoff's three laws (see Overview). Tape reading = infer accumulation vs distribution from price + volume on each print.
- Richard Ney "specialist as merchant" model: buy wholesale (after drops), sell retail (after rallies); declines must grow ever larger to shake out stock. Used as the narrative backbone.
- Claim "volume cannot be hidden", later softened (dark pools, Ch5).

### Ch 2 - Why Volume? (L896-1288)
- "Uncle Joe widgets" parable: operator spreads a shortage rumour, sells into rising demand, then spreads an oversupply rumour, buys back cheap.
- Spot FX has no true volume; tick volume (count of price changes) is the proxy. She cites "about 90% representative" of real activity; claims accuracy is irrelevant, only consistency in the same feed (Ch4 Principle 3).
- Three points about volume: (1) all volume is relative (compare to recent bars); (2) volume without price is meaningless; (3) time matters (same volume packed into less time = more pressure).
- Buying/selling is always described from the wholesaler's view: a "buying climax" in her usage is insiders buying (bottom, panic selling by public); "selling climax" = insiders selling at the top. Opposite to common usage - watch for this when mixing sources.
- Explicit: technique is discretionary, not suited to automation.

### Ch 3 - The Right Price (L1290-1721)
- Criticises pure "price action trading" as half the story.
- Electronic 24h trading means open/close prices carry less information than before; gaps are rarer; open of a bar = close of previous bar in FX. (Relevant to our data: no gap signal in FX, some in indices.)
- Seven elements of a candle: open, high, low, close, upper wick, lower wick, spread (body size). Wicks and spread carry the sentiment. Long body, no wick = strong conviction in the close direction; narrow body = weak sentiment; wick = sentiment change within the bar.
- Lower-wick bar closing back at open = sellers overwhelmed, bullish at close ("hammer"); upper-wick bar closing at open = buyers overwhelmed ("shooting star"). Exact 50/50 splits are illustrations; any ratio works.
- Time-frame scaling: same pattern means more on daily/weekly than on 1m/5m.
- Mentions Volume At Price (VAP) as inside-the-bar volume profile (Ch9).

### Ch 4 - VPA First Principles (L1724-2644)
- Six principles: art not science; patience (market is a supertanker, signal is a warning not an entry, reversal takes a "mopping up" period of sideways whipsaw); all relative; practice; use other TA (support/resistance, trends, patterns) as context; validation vs anomaly.
- Single-bar logic (effort vs result):
  - wide spread + high volume = validation; narrow spread + low volume = validation.
  - wide spread + LOW volume = anomaly (trap / fake move, e.g. opening-bar test by market makers, news spike with no participation).
  - narrow spread + HIGH volume = anomaly: absorption. In an uptrend = supply being absorbed (weakness); in a downtrend = demand absorbing sellers (strength, possible bottom).
- Multi-bar logic: rising price should come with rising volume; falling price also needs rising volume (it takes effort to fall). Rising price on falling volume = weakness; falling price on falling volume = selling drying up.
- Worked 4-candle examples (Figs 4.16/4.17): candle 2 has high volume but only slightly wider spread (first anomaly), candles 3-4 go wider spread on lower volume (confirmation). Anomaly on one bar, confirmed by subsequent bars.
- Three-step process: Micro (this bar vs recent volume), Macro (this bar vs last few bars), Global (whole chart: trend position, support/resistance, patterns).
- Cause and effect applied across timeframes: a signal that appears on 5m, then 15m, then 30m is a bigger "cause" and has more distance to run ("ripples in a pond", "clockwork car"). Trio used by her: 5/15/30m, trade on the middle (15m); alternative 60/240/D.
- Trend is relative to timeframe; she regards 5m trends as valid as daily ones. Only risk rule given: "1% rule".

### Ch 5 - Building the Picture (L2647-3782)
- Five concepts: accumulation, distribution, testing, selling climax, buying climax (naming as in Ch2).
- Accumulation (Fig 5.10): after bad news, drop fast (panic, high volume), then repeated up/down whipsaws in a range as insiders buy "manageable" amounts; sideways congestion forms; takes days to months depending on timeframe/market.
- Distribution (Fig 5.11): after accumulation, markup slowly on average volume, speeding up toward target; at target price insiders sell into greed in a narrow range with high (not extreme) volume ("natural phase"), then a forced final phase = selling climax.
- Testing supply (Figs 5.12/5.13): after accumulation, as price starts to leave, a down-bar with narrow spread, deep lower wick, LOW volume = successful test (no sellers left); same bar on HIGH volume = failed test, price returns into the range for more accumulation. Testing demand (Figs 5.14/5.15) is the mirror at the end of distribution (up-bar, narrow spread, upper wick, low volume = no demand = markdown follows).
- Selling climax (Figs 5.16, 5.19): several bars with deep upper wick, narrow body, high / ultra-high volume, close at or near open, repeated 2-3 times at the end of a distribution range, then price breaks lower fast. Body colour unimportant; repeated, tall wick + very high volume is the key. Buying climax (Figs 5.17, 5.20): mirror (deep lower wicks, repeated, ultra-high volume at the bottom).
- Why climaxes are messy: insiders cannot sell/buy size in one session without moving price against themselves (dark pools mentioned; admits volume can be hidden there).
- Complete cycle (Fig 5.18): accumulation -> buying climax -> test -> markup -> distribution -> selling climax -> demand test -> markdown. "Up the stairs, down the elevator" (declines faster than advances). Cycles nest in all timeframes ("Russian dolls").
- Target levels for campaigns are existing congestion zones (older support/resistance); markets are "over bought / over sold" there.

### Ch 6 - The Next Level: candles (L3784-4575)
- Five principles: (1) wick length is first focus; (2) no wick = strong sentiment in close direction; (3) narrow body weak, wide body strong; (4) the same candle means different things at different trend locations; (5) volume validates.
- Premier candle 1 - Shooting star (weakness): rise then close near open. Volume grades it: low = minor pause; average = real weakness; high / ultra-high = professionals selling, big move coming. Two or three within a few bars at same price level (same failing high) with rising volume = strong bearish signal. In a downtrend a shooting star can be forced selling of inventory (rally to be sold into) or a test of demand.
- Premier candle 2 - Hammer (strength): fall then recover to close near open. A single hammer rarely stops a "price waterfall"; wait for a sequence of 2-3 hammers on very high volume (buying climax) and then a low-volume hammer/test. Hammer in a short position = reason to take profit / hold judgement via volume of the bounce.
- Premier candle 3 - Long-legged doji (indecision): both wicks long relative to body, open ~ close. Unlike the other two, this one CAN be a volume anomaly: low volume + big swings = stop-hunt / news whipsaw (e.g. NFP), not a reversal; stay out. Needs at least average volume to be meaningful.
- Wide-spread candle: strong sentiment; low volume = warning. Narrow-spread candle: only interesting when volume is high (absorption/"anomaly").
- Hanging man = hammer shape at top of an uptrend: bearish only with above-average volume; stronger if followed within a few candles by a shooting star on high volume.
- Stopping volume (Fig 6.17): in a waterfall, several consecutive bars with deep lower wicks, narrowing bodies, rising volume, closes in upper half of the bar, ending in a hammer; precursor to buying climax. Topping-out volume (Fig 6.18): mirror in an uptrend - upper-wick bars, narrowing spreads ("arcing"), high/ultra-high volume, ending with a shooting star.
- News + volume: a price move on news that is not matched by volume = anomaly; a volume surge with the move = validated.
- Advice: signal means "get ready", not "enter"; wait for the next candles to confirm; market has momentum. VPA also used for holding positions (pullback on falling volume = hold) and exits.

### Ch 7 - Support and Resistance (L4578-5202)
- Markets trend ~30% of the time and move sideways ~70% (rule of thumb, no source). Sideways reasons: pending news, climax phases, running into old trapped-trader zones.
- Floors / ceilings explained by trapped "weak" buyers at wave tops (exit at small loss when price returns) vs "strong" buyers at wave bottoms. Zones are "rubber bands, not rods of steel".
- Congestion entrance detection with isolated pivots (Fig 7.13-7.15): pivot high = 3-candle pattern where the middle candle has higher high AND higher low than neighbours (author's wording); pivot low = middle candle with lower low and lower high. After a pivot high in an uptrend, a following pivot low defines floor and ceiling of the congestion zone. Further pivots reinforce the zone.
- Breakout validation (Fig 7.16/7.17): need a clean CLOSE beyond the ceiling/floor ("clear water", no numeric rule - judgement), plus strong rising volume on the break; pullback to retest the broken line should be on low/falling volume; breakout on low volume = fake-out trap.
- Role reversal ("the house", Fig 7.18): broken ceiling becomes floor and vice versa. Stop-loss placement: opposite side of the congestion zone / below last pivot low. Congestion zones remain relevant for years; deeper/wider/longer zones and zones where a major reversal occurred matter more; higher timeframe zones matter more than lower ones.
- Cause and effect: longer consolidation -> longer subsequent trend (proportional to timeframe).

### Ch 8 - Dynamic Trends and Trend Lines (L5203-5568)
- Rejects classic "wait for three higher highs / lows" trend lines as too late. Instead: after a validated breakout from congestion, enter, then build the trend with successive confirmed pivots: first marker pivot high, second marker pivot low, then require each new pivot high above the previous and each pivot low above the previous (mirror for down). Hold while the sequence holds and volume supports.
- Exit / warning: a pivot high lower than or equal to the previous one = possible secondary congestion; if that congestion breaks the other way, exit (reversal), if in trend direction, continue and restart the pivot sequence.
- Missing pivots or a breakout without the pivot sequence plus average/below-average volume = trend lacking momentum; may revert to congestion.
- Dow-based: minor / secondary / primary trends scaled for intraday as 2-3 hours / 2-3 days / 2-3 weeks. Counter-trend trades (against the higher timeframe trend) are higher risk and short-lived.

### Ch 9 - Volume At Price (VAP) (L5570-5864)
- VAP = volume histogram by price level (rotated sales-volume chart), shows density of past trade at each price; high-volume nodes = strong future support/resistance, thin areas = easy to penetrate. Colour shows up vs down candles per level. Used to rank congestion zones: compare the volume packed in a zone against a benchmark zone (e.g. 3-day congestion vs 1-day congestion with equal volume = latter is stronger/heavier).
- Examples on MSFT 15m, Alcoa 1h, P&G daily (qualitative). Presented as a supporting tool for VPA, "free on most platforms". No stats.

### Ch 10 - Worked examples (L5865-6618)
- Qualitative candle-by-candle commentary on HON daily, Duke Energy daily, SLV 5m, GLD 15m (extreme volume ~6M vs average ~500k on panic selling), AUD/USD 15m (short idea: wide candle with big upper wick, then shooting stars with high volume and a lower high; stop above first wick), AUD/USD weekly selling and buying climax, YM/ES futures openings (gap-up with high volume = genuine; wide up bar with low volume vs prior day's climax = trap), coffee 80-tick, DJIA weekly.
- Notable practical points: define what low / average / high volume is per instrument (extreme volume spikes distort the visual scale for the rest of the session); allow flexibility - volume cannot rise forever in a trend; opening bar test pattern at cash open (low-volume wide bar = market makers probing); tick-chart bars show activity via formation speed.
- No win rates, no P&L aggregates; every example is one hand-picked chart (she says not cherry-picked, but there is no sample).

### Ch 11 - Putting It All Together (L6620-7080)
- GBP/USD 15m: 70-bar congestion with pivots, break on a UK data release, wide close beyond the ceiling and high volume; stop below last pivot low; expected long trend because cause was large.
- GBP/USD 1h: pivots on one side only are acceptable; volume below average defines congestion; hanging man with jump in volume then break below floor = reversal; floor became ceiling; falling-volume waterfall = limited downside.
- Three-timeframe method (Fig 11.12): 30m = benchmark (dominant trend and bias), 15m = trade chart, 5m = fast chart; signals appear first on the fast chart and ripple outwards; trading with the benchmark trend = lower risk and longer hold; against = counter-trend, shorter hold. A single shooting star on 30m = 2 candles on 15m = 6 on 5m (candle aggregation makes patterns clearer on the slower chart).
- Candle/chart patterns "that work consistently": falling triangle (lower highs into flat floor: break down more likely), rising triangle (higher lows into flat ceiling: break up), pennant (lower highs + higher lows, coiled spring, direction unknown), triple top, triple bottom (reversal at tested level; if broken it becomes strong support/resistance). Examples: falling triangle 5m, rising triangle EUR/USD daily, pennant MSFT monthly, triple top AUD/USD daily at 1.0600, triple bottom EUR/CHF 1h.

### Ch 12 - Next Generation (L7082-7340)
- Equivolume (Arms): box width = volume, height = high-low, x axis volume not time; "power box" = wide and tall at breakout. Candle-volume charts: candles with volume-proportional width. Delta volume (volume at ask minus at bid) and cumulative delta. Author has not used these herself; admits she cannot vouch for them. Delta needs bid/ask classification (futures/equities) - not available to us.

## Topic tags

- **trend**: Dynamic trend building via sequential pivots after a congestion breakout (Ch8); higher-timeframe benchmark chart gives the dominant trend, trade with it = lower risk (Ch11); trend duration scales with preceding congestion duration (cause/effect); classic 3-point trend lines dismissed as too late.
- **breakout**: Breakout from congestion needs a clean close beyond the zone, high/rising volume, retest on low volume; low-volume breakout = fake-out (Ch7, 8, 11). Stops go on the opposite side of the zone or below the last pivot low.
- **mean-reversion**: Not a theme. Closest content: failed breakout / fake-out reversal; triple top/bottom bounces; low-volume markup bars expected to be reversed. No numeric rules.
- **momentum/oscillators**: None used. "Over bought / over sold" appears only as congestion-zone context. Volume trend (rising price needs rising volume) is her momentum gauge.
- **patterns**: Hammer, shooting star, long-legged doji, hanging man, stopping / topping-out volume sequences, falling / rising triangle, pennant, triple top / bottom (Ch6, Ch11). Wyckoff structure: accumulation, distribution, test, buying/selling climax.
- **intraday/sessions**: Opening-bar trap: wide up bar at cash open on low volume = market makers probing (Ch4, Ch10); gap-up with high volume at index open = genuine. NFP / news candles with long wicks and low volume = stop-hunting whipsaw (Ch6). Overnight futures make the cash-open gap less informative.
- **seasonality/time**: Only "volume thin on holidays". No seasonal edge claimed.
- **volatility**: Wide/narrow spread (bar range) vs volume; compression into pennants / triangles (coiled spring) before breakout. No ATR use.
- **stops-and-exits**: Stop beyond the signal-bar wick, or beyond the far side of the congestion zone, or below last pivot low; exit on volume signs of stopping/topping-out volume, or a pivot sequence break (lower pivot high = warning). Targets = next congestion zone. No numeric R targets, no trailing rule.
- **position-sizing/risk**: Only "1% rule" and "start with the smallest contract". Trade risk is said to be "quantified by VPA" but no method given.
- **testing-and-robustness/overfitting**: None. The author argues against automation and backtesting ("months of work" comparing feeds convinced her accuracy does not matter). All evidence is a handful of hand-picked annotated charts.
- **costs/execution**: Not discussed (spreads, swap, commissions absent).
- **psychology/discipline**: Fear of loss / fear of missing out used to explain zones and traps; patience (do not enter on the first signal); market-maker manipulation narrative.
- **portfolio/diversification**: None.

## Testable ideas

For each: (a) volume needed? (b) price-only proxy? (c) testable now?

**1. Congestion zone breakout with pivot-defined zones - testable now (price-only core)** ★
- Rule: detect a congestion zone from 3-bar isolated pivots (pivot high: middle bar higher high AND higher low than neighbours; pivot low: middle bar lower low AND lower high). Zone starts when a pivot high is followed by a pivot low (or vice versa) with price staying inside; ceiling = pivot high(s), floor = pivot low(s) (allow a tolerance because lines are "rubber bands"). Entry on the first candle CLOSE beyond the zone by a clear margin (suggest margin in ATR or % of zone height; the author gives no number), stop on the opposite side of the zone (or below the last pivot low), exit options: next opposing zone, or trailing via the dynamic pivot sequence (idea 3).
- Source: Ch7 (Fig 7.13-7.17), Ch11. Evidence: only anecdotal charts.
- (a) Original rule needs rising volume on the breakout. (b) Proxy: breakout bar range relative to average bar range (wide-spread bar), tick count if later from MT5; or close location in the bar (close near extreme). Zone "weight" proxy = number of bars / number of pivots in the zone and zone duration (her cause-effect).
- Fit: good for 15m-4h on XAUUSD/GBPJPY/GBPUSD and indices; intraday holds avoid swap. Differs from strategy 1/2: no session logic, no SMC objects (FVG/OB), no sweep requirement; closest to strategy 4 breakout but zone-based and with structure-based stop instead of 3xATR and no stop-and-reverse. Risk: classic range breakouts are known to have many false breaks; test the false-breakout rate and gross vs net after spread.

**2. Breakout cause-and-effect: move size or duration scales with zone duration - testable now** ★
- Rule: for each detected zone measure duration (bars) and height; test whether subsequent breakout move (in R or in zone heights, e.g. max favourable excursion in 5/10/20 bars) increases with zone duration / number of pivot touches. Use as a filter: only trade breakouts from zones longer than N bars, or scale target by zone height x f(duration).
- Source: Ch4 (cause and effect), Ch7 (Second Principle), Ch8, Ch11. Evidence: qualitative only.
- (a) No volume needed (time-based cause). (b) n/a. Fit: good; easy to test as a conditional-expectancy table, also useful as a diagnostic for any range strategy. Differs: it is a research filter, not a new entry.

**3. Dynamic pivot-sequence trend following and exit - testable now**
- Rule: after a long breakout entry, track confirmed 3-bar pivots; stay in while each new pivot high > previous pivot high and each new pivot low > previous pivot low (mirror short). Exit (or tighten stop to last pivot low) when a pivot high fails to exceed the previous one, or price closes below the last pivot low. No fixed TP.
- Source: Ch8 (Fig 8.11-8.15). Evidence: none beyond illustrations.
- (a) Needs "volume supports" in the text. (b) Optional proxy: bar range expansion. Fit: swing-structure trailing stop is intraday-to-daily; with holding > 1 day, swap matters (FX/gold). Differs from strategy 4: structure-based (3-bar pivots) stop and re-entry, not ATR stop / MA band; but it is close to a Dow-style swing trailing and may fail for the same reasons (swap, unstable halves).

**4. Role reversal retest ("ceiling becomes floor") - testable now**
- Rule: after a validated breakout of a congestion zone, wait for price to return to the broken line (within tolerance) and enter in breakout direction on a rejection candle (see idea 5) with stop just beyond the zone. Compare against entering on the breakout bar itself.
- Source: Ch7 (house, Fig 7.18), Ch11. (a) She wants low volume on the retest. (b) Proxy: narrow range / small bodies on retest bars, or a wick rejection. Fit: good, fewer trades, tighter stops (better R). Differs: entry at structural retest, not at a sweep/FVG/OB.

**5. Hammer / shooting-star rejection candle at a support/resistance zone, multi-timeframe filtered - partly testable now** ★
- Rule: candle with lower (upper) wick >= k x body and >= m x average range, close within x% of the open or of the high (low); require it at a previously defined congestion zone edge, in the direction of the higher-timeframe trend (benchmark chart = 2x timeframe, e.g. trade 15m with 30m or 1h trend), enter on the next bar, stop beyond the wick, targets 1R-3R or next zone. Optional: require 2-3 such bars within a few bars at the same price (author: repetition raises significance).
- Source: Ch3, Ch6, Ch10 (AUD/USD 15m short example), Ch11.
- Author's volume requirement: high / ultra-high volume on the wick bar (low volume = minor). (a) volume needed for her grading; (b) price-only proxies: wick length relative to ATR, total bar range vs average range (large range bar = high activity), and later MT5 tick volume for the true test. Tag the volume as an add-on filter and test both variants on MT5 data.
- Fit: good for 15m-1h on indices/gold intraday. Differs from strategy 3 (no-wick candle in trend, which already failed): here the wick IS the signal; close to strategy 1's sweep idea (wick through a level then reversal), so treat as a likely-correlated variant of an already failed family - quick to test, low prior.

**6. Triple top / bottom and ascending / descending triangles as breakout/reversal triggers - testable now**
- Rule: three touches (within tolerance) of the same level separated by pullbacks = triple top/bottom; flat ceiling with rising pivot lows = rising triangle (long bias break up), flat floor with falling pivot highs = falling triangle (short bias). Entry on close beyond the flat boundary, stop beyond the opposite recent pivot, target = triangle height projection.
- Source: Ch11 (Figs 11.13, 11.14, 11.16, 11.17). Evidence: single chart each.
- (a) volume to confirm break (c) price-only: testable. Fit: moderate; all automated chart-pattern rules tend to be weak out of sample; useful mostly as a subset of idea 1 (conditional on pivot geometry).

**7. Effort-vs-result filter with a price-only proxy (absorption / no-demand bars) - testable now with proxy, properly only with MT5 tick volume**
- Rule (price-only proxy): compute a "result" (bar range, or range/ATR) and an "effort proxy" (tick count from MT5 when available; with histdata only M1 bar count in the aggregate bar is constant, so use e.g. lower-timeframe realized path length = sum of M1 ranges inside the bar, or number of M1 bars with close change, as activity proxy). Flag "absorption" = high activity but narrow net range (many M1 swings, small close-to-open), and "no-demand" = wide range but low activity. Test whether absorption bars at swing extremes predict reversals vs a plain wick-ratio baseline.
- Source: Ch2, Ch4, Ch6. Evidence: none.
- (a) the original needs volume; (b) M1 path length / sum of M1 ranges is a legitimate range-based activity proxy available in our M1 data (not true volume; test whether it correlates with MT5 tick volume once available). Fit: new angle (intrabar activity from M1) that none of the failed strategies used; moderate prior, cheap to test as a feature in a conditional-expectancy study.

**8. Tests after climax (Wyckoff spring / test) as price-only structure - testable now**
- Rule: define a range (idea 1), look for a "spring" = brief close or wick below the floor that quickly returns inside with a narrow-range bar (proxy for low volume test) and then a break above the midline/ceiling; long entry on the first close above the range midpoint after the spring, stop below the spring low. Mirror for upthrust at the ceiling.
- Source: Ch5 (testing supply / demand, climaxes). Evidence: schematics only.
- (a) volume low on the test; (b) proxy: test bar range < k x ATR and wick >= body; the sweep-reclaim structure overlaps with strategy 1/2 "liquidity sweep" which failed. Low prior of being new; but running it with range (congestion) definition from idea 1 instead of session zones is a different base.

**9. Multi-timeframe benchmark filter (trade-chart + 2x slower chart bias) - testable now**
- Rule: bias from the benchmark chart (2x timeframe, e.g. 30m for 15m trade chart; or 4h with 1h) such as sign of last pivot sequence / price vs recent pivots; allow only trades in bias direction ("with the flow"); allow counter-trend trades with half size and shorter max hold.
- Source: Ch4, Ch11. (a) none. Evidence: none. Fit: trivially testable as a filter on top of other entries (strategies 1-3 already used higher-timeframe trend as a filter, so low novelty; still useful to quantify the benefit of the counter-trend rule).

**10. Volume-based ideas that need MT5 tick volume (defer)** ★
- Relative volume (bar volume / mean of last N bars) classified as low / average / high / ultra-high (she gives no thresholds; suggest quantiles of the last N bars). Rules: (i) breakout from congestion valid only when relVol high and rising for 2-3 bars; (ii) climax detection: >= 2 bars with upper (or lower) wick, relVol ultra-high, near the end of a range; (iii) test bars: narrow range + low relVol + wick at range edge; (iv) news bars: wide range with low relVol = ignore.
- Source: Ch5-Ch7, Ch10. Evidence: none. Fit: needs MT5/FTMO history; tick volume differs by broker so re-fit thresholds as relative quantiles (her own "all volume is relative" point). Plan: build the price-only versions first, then test whether volume adds anything (A/B), which is the only honest way to test her main claim.

(Starred: 1, 2, 5, 10. Idea 7 is also worth a quick feature study.)

## Warnings / pitfalls
- Unfalsifiable by design: the author says it cannot be automated and is subjective; no sample sizes, no win rate, no costs, no out-of-sample test. All examples are retrospectively annotated single charts, so selection bias is complete.
- Every pattern has an escape hatch ("a signal is not an entry", "need confirmation", "anomaly OR validation"), so almost any outcome can be rationalised. When coding rules, the discretion must be replaced by fixed numeric thresholds and tested; do not assume her qualitative edge survives.
- Manipulation narrative ("insiders accumulate/distribute") is explanatory story, not tested; the tradable content is only the price/volume structure. In spot FX/gold CFDs there is no centralised volume at all; tick volume is broker-specific (she says relative use in one feed is enough).
- "Clear water" for a breakout, "high volume", "low volume", "wide spread" have no numeric definitions; any backtest must choose and sweep them (risk of overfitting; keep a frozen config and test out-of-sample halves).
- Own warnings: market has momentum, entering at the first signal gets stopped; zones are not exact lines (rubber bands); extreme volume spikes distort the volume scale; trend volume cannot rise forever, allow flexibility; counter-trend trades are higher risk and short-lived; volume can be hidden in dark pools / after-hours.
- Her "buying/selling climax" naming is reversed from common usage (hers: insiders' action). Cross-reference carefully with Wyckoff literature (where buying climax = top, selling climax = bottom in the public sense).
- Price-only parts overlap with what we already tried (sweep / wick reversal / no-wick candle / SMC zones), so expect a low hit-rate; the most distinct areas are zone-duration scaling (idea 2), pivot-sequence trailing (idea 3) and intrabar-activity proxy (idea 7).
- Candle/zone rules from the 1990s-2010s era FX charts: 24h electronic feeds mean open = previous close (no gap signal in FX); only indices show opening gaps, partly pre-signalled by overnight futures.
