# Strategy ideas backlog

Testable ideas from the books, merged and de-duplicated. **Nothing here is a trading rule**: an idea
becomes a rule only when the user picks it, it is written into a `docs/` spec and tested (CLAUDE.md ›
Specs are the source of truth). When an idea is tested, set its status and link the ROADMAP step.

Sources: K = Kaufman *TSM* (page), D = Douglas (chapter), H = Hougaard (chapter), V = Volman
*Forex Price Action Scalping* (chapter), A = Aziz *How to Day Trade for a Living* (chapter/setup),
C = Coulling *Volume Price Analysis* (chapter). Evidence in the books
is mostly **gross of costs** on 1990-2011 futures, or anecdotal (V, A, C give no statistics at all). ★ = most promising for our data.

Our data: M1 histdata, XAUUSD, GBPUSD, GBPJPY, NAS100, US500, 2018/2020-2026, price only, costs =
spread + commission + swap, results in R, FTMO limits (5 % daily, 10 % total).

Already tested and failed (do not re-propose unchanged): session-zone sweep (1), NY-open index sweep
(2), no-wick candle (3), Kaufman trend following with stop-and-reverse (4). See ROADMAP 6, 8, 9, 10.

## Overview

| ID | Idea | Type | Symbols / TF | Swap | Source | Status |
|---|---|---|---|---|---|---|
| T-01 | Robustness report: plateau heat map, % profitable combos, halves t-test, shock days, 3 cost levels | tooling | all | – | K ch.21 | open |
| I-22 | "Book of Truths" report: R by hour, weekday, Friday, month-end, Aziz windows | tooling | all | – | H; A ch.7 | open |
| I-01 ★ | Noise / regime study: ER per symbol, timeframe, half | study | all, 15m-1d | – | K ch.1, 17, 20, 23 | open |
| I-02 | Trend-quality gate (ER, regression r, strength osc.) on strategies 2 and 4 | filter | all | – | K p.10-14, 275, 408 | open |
| I-09 ★ | Open / gap / trend-day statistics on indices | study | NAS100, US500 | none | K ch.15-16, H | open |
| I-17 | Time-of-day drift by session | study | XAUUSD, FX | none | K p.689-699 | open |
| I-07 ★ | Volatility-scaled opening range breakout | signal | indices, gold; 5-15m | none | K p.759-764; A ORB | open |
| I-08 ★ | ORB only after inside / NR4 day or low vol | filter+signal | all; 5-15m | none | K p.759-764 | open |
| I-16 ★ | Intraday volatility-shock fade | signal | gold, indices; 5-30m | none | K p.775-777, 626-634 | open |
| I-03 ★ | RSI(2) mean reversion | signal | indices (1h-1d) | 0-1 night | K p.389-390 | open |
| I-05 ★ | Pullback entry inside a slow trend | signal | all; 15m-1d | some | K p.950, 418, 835 | open |
| I-11 | Midday support/resistance + afternoon breakout | signal | indices; 15-30m | none | K p.754 | open |
| I-10 | Opening inside-bar break with double top | signal | indices; 10m | none | H | open |
| I-12 | Fade outside bar / key reversal with range filter | signal | all; 1h-1d | short | K p.111, 157-158 | open |
| I-13 | Nofri congestion third-bar reversal | signal | FX, gold; 15m-1h | none | K p.155-157 | open |
| I-14 | ATR swing-filter (event) trend | signal | all; 1h-1d | yes | K p.182-191, 218 | open |
| I-15 | 3-ATR momentum continuation bar | signal | indices, gold | short | K p.333, 380 | open |
| I-18 | Month-end index flow | signal | NAS100, US500 | ~5 nights | K p.726-729, 480 | open |
| I-19 | Gustafson 4-down-closes long | signal | indices; 1h-1d | 1-8 nights | K p.1010 | open |
| I-20 | NAS100/US500 ratio stress (pairs) | signal | NAS100+US500 | both legs | K p.583-612 | open |
| I-23 | Coded chart patterns (rectangle, double top, H&S) | signal | all; 1h-1d | yes | K p.176-178 | open |
| I-30 | Round numbers and daily pivots (also as target/skip layer) | signal+filter | all; 1-15m | none | K p.81, 143, 167; V ch.7-15; A | open |
| I-31 | Value area (Market Profile from M1) | filter+signal | all | none | K p.822-830 | open |
| I-32 | Bollinger-in-Keltner squeeze breakout | signal | all; 15m-4h | some | K p.330 | open |
| I-04 | Low-vol entry filter, high-vol / shock exit with re-entry | filter+exit | trend systems | – | K p.861-866, 992 | open |
| I-06 | Wait-for-pullback window, scale in over bars | entry mgmt | any signal | – | K p.1076-1079 | open |
| I-24 | Scale out in thirds; minimum 3:1 target gate | exit mgmt | any signal | – | D ch.11 | open |
| I-25 | Press winners: ATR pyramiding / add on new highs | exit mgmt | any signal | – | H; K p.1080-1084, 229 | open |
| I-26 | Drawdown-scaled risk; 20-loser check; daily give-back stop | risk | R lists | – | K p.231; D ch.11; A ch.7 | open |
| I-27 | Volatility-targeted sizing | risk | R lists | – | K p.1046-1054, 1142 | open |
| I-21 | Hourly / seasonal volatility sizing, skip low-range hours | risk | all | – | K p.453-454, 561 | open |
| I-28 | Streak dependence test; equity-curve filter | risk/study | R lists | – | D ch.5; K p.1086 | open |
| I-29 | Carry: hold the positive-swap side with a trend/stop guard | signal | GBPJPY etc. | earns | K p.596-599 | open |
| I-33 ★ | Compression block/range break with EMA squeeze and tension | signal | all; M1-M5 (15m for zones) | none | V ch.10-13; C ch.7 | open |
| I-34 | Zone duration vs breakout move size (cause and effect) | study/filter | all | – | C ch.4, 7 | open |
| I-35 | Second break (W/M) at the 20 EMA, micro pullback | signal | FX, gold; M1-M3 | none | V ch.7-9 | open |
| I-36 ★ | Tipping-point exit module; breakeven vs no breakeven A/B | exit mgmt | any entry | – | V ch.14; A; C ch.8 | open |
| I-37 ★ | Free-path-to-target skip filter | filter | any entry | – | V ch.15; A rule 5 | open |
| I-38 | Session-mean (VWAP proxy) hold / rejection | signal | indices; 5m | none | A VWAP | open |
| I-39 | Previous-close magnet on gap days (red-to-green) | signal | indices; 5m | none | A ch.7 | open |
| I-40 | Exhaustion reversal: 5+ candles, RSI extreme, at a level | signal | indices, gold; 5m | none | A reversal | open |
| I-41 | Wick rejection at a zone, spring / upthrust (price-only) | signal | all; 15m-1h | some | C ch.5-6 | open |
| I-42 | Breakout retest / role-reversal second entry | signal | all; M1-1h | none | V ch.13; C ch.7 | open |
| I-43 | M1 path-length activity proxy (absorption study) | study | all | – | C ch.4 | open |
| I-44 | Volume rules (relative tick volume, climaxes, true VWAP) | signal+filter | needs MT5 tick volume | – | C; A | blocked: no volume in histdata |
| I-45 ★ | Cost-to-target filter: skip when spread/target > 0.10-0.15 | filter | any entry | – | V ch.1, 14 | open |

## Suggested order (Claude's proposal, the user decides)
1. **Tooling first** (T-01, I-22): every later test then reports robustness the Kaufman way.
2. **Cheap studies** (I-01, I-09, I-17): find *where* there is structure (which symbol, timeframe,
   session, half) before building a strategy. Hours of work, no new strategy folder.
3. **Day-trade strategies without swap** (I-07/I-08 ORB family, I-33 compression break, I-16 shock
   fade, then I-03 RSI(2), I-05 pullback). These avoid the swap problem that killed strategy 4 and fit
   the noisy indices. Apply I-45 (cost-to-target) and I-37 (free path) as filters from the start.
4. **Management and risk layers** (I-36, I-25, I-24, I-26, I-27) on the best candidate only: they
   reshape an edge, they cannot create one.

## Details

### T-01 Robustness report (tooling)
Add to every grid run: heat map with neighbour smoothing, average ± st.dev over the whole declared
range, % profitable combos (target ≥ 70 %), Welch t-test of trade R between halves, shock-day P/L
(range > 3.5 × ATR(10)), results at 0 / realistic / +50 % costs, return kurtosis flag (> 7), best-trade
removed. Source: K ch.21 (p.916-981), ch.2 (p.28, 43, 47). See `topics/testing-and-robustness.md`.

### I-22 Book of Truths report (tooling)
Split any strategy's R by hour of entry, weekday, Friday, first/last 3 days of month, holding time.
Shows time structure and is a cheap robustness check. Source: H "The Ideal Mindset".

### I-01 ★ Noise / regime study
ER(n) = |C_t − C_(t−n)| / Σ|C_i − C_(i−1)| for n = 10, 20, 65 on 15m, 1h, 4h, 1d; per symbol, per year,
per half. Compare with strategy 4's per-symbol results. Question: which symbol/timeframe/period is
trendy at all, and does noise explain strategy 4's split halves? Source: K p.10-14 (low noise ↔
higher trend PF across 2000-2012 futures; indices noisiest), p.1070-1072. Fit: excellent, closed bars
only. Leads to I-02 or to a mean-reversion focus.

### I-02 Trend-quality gate
Only take trend entries when ER (or rolling regression r, or strength oscillator SMA(ΔC)/SMA(H−L))
is above a pre-declared percentile of its own history; optional mirror: mean-reversion entries only
when ER is low. Apply to strategy 4 and to strategy 2's new 1h trend filter. Source: K p.10-14,
273-276, 408, 1062-1072. Risk: threshold snooping; declare one value per test. Differs: a regime gate,
none of the 4 strategies had one.

### I-09 ★ Open / gap / trend-day statistics (NAS100, US500)
Measure on cash-session data (09:30 New York open): P(gap filled same day / by day 3) by gap size in
ATR; direction of the first 30 min vs rest of day, per half; share of trend days (open in the bottom
or top 10 % of the range, close at the other end); share of day extremes in the first 90 minutes;
whether a new high in the last hour closes near the high; Friday and month-end effects. Claims to
check: 48 % / 76 % gap fill, 90 % of extremes in 1.5 h, ~20 % trend days (H); first-bar continuation
2000-2011 that reversed in 2009-11 (K p.691-696); open most likely extreme (K p.696-699). Output:
which rule, if any, becomes a strategy (first-bar continuation, gap fade, late-day continuation).

### I-17 Time-of-day drift by session (XAUUSD, GBPUSD, GBPJPY)
Average return, sign persistence and range per 30-min bucket in UTC, split by Tokyo / London /
overlap / New York and conditioned on the first bar of each session; per year and half. Trade only
buckets with a stable sign and a move much larger than the spread. Source: K p.689-699 (EURUSD gain
concentrated in Europe, extremes at the European open). Also gives the range profile for I-21-style
sizing (skip hours whose range is small vs the spread; K p.453-454).

### I-07 ★ Volatility-scaled opening range breakout
Session open O (cash open for indices; London and New York opens for gold/FX). Long when price > O +
k·ATR(n), short when < O − k·ATR(n); one reversal allowed or none; stop at the opposite band; exit at
session end (before 17:00 New York). k ∈ {0.5, 0.75, 1, 1.5, 2}, n = bars per day. Source: K
p.759-764, Table 16.8 (crude 5m PF 1.07-1.18 on 480-740 trades, gross); S&P fixed-point ORB was mostly
negative. Fit: good, no swap; spread is the main cost. Differs: strategy 2 faded the opening sweep;
this follows the break. Aziz adds: opening range of 5/15/30 min, trade only if the range is much
smaller than the daily ATR (try range < 0.1-0.3 × ATR(14) daily), exit on the first opposite 5-min
extreme when no level target exists.

### I-08 ★ ORB after inside / narrow-range day or low volatility
Only on days after an inside day, an NR4/NR7 day, or when 6-day vol < 100-day vol. Entry: stop orders
beyond the prior day's high/low or O ± k·ATR; reverse once on same-day failure; exit at session end or
end of day 2 if not profitable (Raschke). Source: K p.759-764 (crude: profit/trade ~10×, PF 1.5-3.2 on
60-90 trades; Crabel bonds 60 % → 76 % winners). Fit: few trades (~10 % of days) → pool all 5 symbols
and all years. Run together with I-07 as one strategy folder with a filter option.

### I-16 ★ Intraday volatility-shock fade
Shock bar on 5-30m: true range ≥ 3 × average of previous bars, or ≥ 2 × the same time-of-day bar's
100-day average, and close in the top/bottom 20 % of its range → enter against it at the next open;
no stop for 2 bars, then stop beyond the extreme of the shock bar and the next two; exit at session
end. Daily variant: TR / ATR(60) lagged 30 ≥ 2-3 → fade 3-10 days (S&P up-shocks: ~−40 points in
10 days; down-shocks no edge). Source: K p.775-777, 626-634. Fit: good for XAUUSD and indices at
news times; must model wider news spreads; the "no stop for 2 bars" needs a hard FTMO guard.

### I-03 ★ RSI(2) mean reversion (indices)
RSI on 2-bar changes. Long when < 10, short when > 90, exit after 1 bar (daily) or 1-3 bars (1h/4h);
scale-in variant 25/50/75/100 % at 20/15/10/5; optional 200-bar MA trend filter. Source: K p.389-390
(S&P: continuation before ~1998, mean reversion after; both sides worked 2000-2008; cost sensitive).
Fit: good on US500/NAS100; daily holds pay one night of swap. Must hold in both halves 2020-22 and
2023-26. Differs: counter-trend, very short hold.

### I-05 ★ Pullback entry inside a slow trend
Slow trend (e.g. SMA 100-200 or KAMA direction, or 1h trend for 5-15m entries) up AND fast trend
(10-20 bar MA) turns down, or 5-bar stochastic < 20, or RSI(2) < 10 → buy; exit when the slow trend
flips, or at momentum zero; stop k·ATR; no stop-and-reverse. Source: K p.950-951 (Nasdaq: PF 1.51 →
2.26, winners 35 → 47 %, trades −66 %), p.376, 418, 426, 835-838 (Elder triple screen, ratio ~5
between timeframes). Fit: all symbols; less time in market than strategy 4 → less swap.

### I-11 Midday support/resistance + afternoon breakout (indices)
Morning range = open to 12:00 New York. Afternoon, 15-30m bars: flat/short and close in the lowest
25 % of the morning range → long; flat/long and close in the top 25 % → short; break of the morning
low while long → reverse short, and mirror; exit at the close. Source: K p.754 (S&P +$268/trade on
8,404 trades, 2000-2011, gross, no tuning).

### I-10 Opening inside-bar break with double top (indices, 10m)
Bar 1 = first 10-min bar, bar 2 inside bar 1, bar 3 closes beyond bar 2 → trade that way; optional
filter: bar 1's extreme matches a prior high/low (double top/bottom, tolerance to define); stop beyond
the day extreme; breakeven after +1R; no target. Source: H (one DAX example). Low evidence; can be a
variant of I-07.

### I-12 Fade outside bar / key reversal with range filter
Outside bar closing above the prior high → sell at the close (mirror below the low); stop beyond the
bar's extreme; exit after 1-5 bars or on a close back past the prior bar's midpoint. Filter: true range
> 1.5 × ATR(20), previous bar not narrow. Source: K p.157-158 (trend version died mid-1980s, reversed
"much better"), p.111 (filter improved key reversals). 1h-4h avoids most swap.

### I-13 Nofri congestion third-bar reversal
Range: top = high followed by 2 lower closes, bottom = low followed by 2 higher closes; cancelled by
a new extreme; pause 10 bars after a large move (10-bar net change > 2× its average) and 2 bars after
a false breakout. Inside the range, after 2 closes in one direction, enter the opposite way at the
close; exit at the next close if profitable, else re-evaluate; exit when price leaves the range; add
an ATR hard stop. Source: K p.155-157. Many trades → spread matters.

### I-14 ATR swing-filter event trend
Swing chart with filter F = k·ATR(50) (previous bar's value); long when the current upswing high
exceeds the previous upswing high, exit/short on a break of the previous downswing low; optional
Livermore penetration filter ½F. k 0.4-0.8 on daily. Source: K p.182-191, 218-220 (ATR box uniform and
positive on EUR, S&P, gold, gross). Holds overnight → swap; compare head to head with strategy 4's
breakout.

### I-15 3-ATR momentum continuation bar
Close moves > 3·ATR(20) from the previous close → follow at the next open, exit after m bars or on a
trail; also run the fade to confirm it loses. Source: K p.333, 380. Overlaps with I-16 (opposite
direction): test both on the same shock definition.

### I-18 Month-end index flow
Long US500/NAS100 from the close ~4 trading days before month end (or the last day) to the close of
the 1st (or 4th) trading day of the next month. Source: K p.480, 726-729. About 5 nights of swap per
month; compare to the expected move.

### I-19 Gustafson 4-down-closes long
Long at the next open after 4 lower closes; exit after 5 higher closes or 8 bars; add an ATR stop.
Source: K p.1010-1011 (S&P 1982-2001: 76 % winners, long-only bull market). Probably a long bias in
disguise; benchmark against buy-and-hold over the same days.

### I-20 NAS100/US500 ratio stress (pairs)
D = Stoch14(NAS100) − Stoch14(US500); stress = Stoch14(D); stress > 95 → short NAS100 / long US500,
< 5 → reverse; exit at 50; legs sized by equal ATR; skip when ratio volatility is too low to pay two
spreads or has jumped. Source: K p.583-586, 608-612. Caveat: correlation is very high (K wants
0.5-0.7) and the ratio trended in 2019-20 and 2023-24. Needs a two-leg engine feature.

### I-23 Coded chart patterns
Swing-based definitions: rectangle (tops and bottoms within 0.75 % of their averages), double top
(two maxima within 1.5 %, > 22 bars apart), H&S (shoulders within 1.5 %); entry on range/neckline
break; target = pattern height −20 %; stop on the other side. Source: K p.176-178, 133-138 (stocks
1962-96: small positive 3-day returns). Low priority.

### I-30 Round numbers and daily pivots
Levels: round numbers (gold 10/50, FX 00/50, indices 100/500) and prior-day P, R1, S1, R2, S2. Test
breakout orders a small offset beyond the level vs fades at the level. Volman's use as a layer: skip
a small setup when a round number sits inside the target distance; a round number 1.0-1.5 × target
beyond a break helps ("vacuum"). Source: K p.81, 143, 167, 687; V ch.7, 11, 15; A S/R setup.

### I-31 Value area from M1
Prior session's time-at-price distribution; value area = central ~70 %. Follow breaks out of the
value area, fade failed excursions back to the point of control. Source: K p.822-830. Conceptual only
in the book.

### I-32 Squeeze breakout
Bollinger(20, 2) inside Keltner(20) = squeeze; enter on the first close outside the band in the
direction of momentum (MACD histogram instead of the volume-based Chaikin); exit at the middle band.
Source: K p.330. No evidence given.

### I-04 Volatility filters and shock exits for trend systems
(a) Enter only when 20-bar volatility is below a fixed threshold (or short/long vol ratio < 1);
(b) exit when a bar's move > factor × prior volatility, re-enter after the range falls to ¼ of that
move; (c) shock bar (range > 3.5-5 × ATR): windfall → exit, loss → hold and block new entries.
Source: K p.861-866 (low-vol filter improved 5 of 5 markets incl. costs; bonds PF 1.02 → 1.16 with
exit + re-entry), p.992-1000. Apply to strategy 4 and I-05.

### I-06 Wait-for-pullback window and scale-in
After a signal wait up to N bars (scaled to trend speed) for a pullback of x·ATR, else enter at bar
N; cancel if the signal flips. Or enter 1/5 at the signal and the rest every ~2 bars. Source: K
p.1076-1079 (trades −40 %, profit/trade ~2×; S&P loss halved, gold loss → profit).

### I-24 Scale out in thirds; 3:1 gate
Three parts: exit 1 at +0.5-1R, exit 2 at 2-3R or a structural target, then stop to entry, part 3
trails. Separate test: skip setups whose target is < 3R away. Source: D ch.11. Partial exits only
reshape the distribution; they cannot turn a zero-expectancy signal positive. Needs partial exits in
the engine.

### I-25 Press winners
Hougaard: N = session ATR on the trading timeframe; stop 2N; add one equal unit every ½N (also test
1N) of profit; all stops moved to one common level; exit on the common stop. Kaufman: add a unit on
each new profit high at least n bars apart (1/3/5/10), max 5 units; never on losses. Source: H
"Pressing Winners"; K p.1080-1084 (e-mini S&P PF 1.14 → 1.46), p.229-233 (Turtles). Needs multi-unit
positions in the engine and the FTMO daily guard. Fits trend days (I-09) best.

### I-26 Drawdown-scaled risk and the 20-loser check
Cut risk by a step for each x % drawdown from the equity peak, restore slowly (Turtles: 20 % per 10 %,
restore 10 % per 6.7 %; finer steps for FTMO's 10 % limit). Plus: size so that 20 straight losses
stay inside the 10 % limit. Plus Aziz: stop for the day after giving back 30 % of the day's profit;
2-3 trades a day. Source: K p.231; D ch.11; A ch.7. Pure `risk/` work on R lists.

### I-27 Volatility-targeted sizing
Risk per trade = r % / (k·ATR) (what our R model already does) plus an account-level scale = target vol
/ lagged realised vol of the strategy's daily R; rebalance only on > 20 % change. Measure FTMO breach
probability. Source: K p.1046-1054, 1142-1145 (info ratio 1.27 → 1.38).

### I-21 Hourly / seasonal volatility sizing
Average range per hour bucket, weekday and month per symbol (from I-17 / I-09); scale risk down in
historically volatile buckets, skip buckets where the range is small vs the spread (cost-to-range
filter). Source: K p.453-454, 561-562. Links to HANDOFF open point 3 (cost filter).

### I-28 Streak dependence and equity-curve filter
Test whether the outcome after 1, 2, 3 losses or wins differs from baseline (runs test, lag-1
autocorrelation); compare flat risk with size-up-after-wins and skip-after-losses; test trading only
when strategy equity > its 10/60-trade MA. Source: D ch.3, 5, 7; K p.1086 (equity-curve filter
inconsistent). If no dependence, flat fractional risk is justified.

### I-29 Carry (positive swap side)
Hold the direction that earns swap (e.g. long GBPJPY if FTMO's rate is positive), size by volatility,
with a trend filter or an x·ATR drawdown exit; rebalance monthly. Source: K p.596-599 (forward bias;
violent unwinds). The only idea that earns swap; unwinds (2008, 2020, Aug 2024) threaten the 10 % limit.

### I-33 ★ Compression block / range break with EMA squeeze
Box: the last 10-40 bars (M1-M5) with total height ≤ m × ATR and ≥ 2-3 equal highs (lows) on the break
side (tolerance 1 pip or 0.1 × ATR). Tension: the last 2-6 bars small (range ≤ 0.3-0.5 × ATR) and hugging
the barrier, bars between the 20 EMA and the barrier; direction = EMA slope / higher lows inside the box.
Entry: stop order 1 tick beyond the barrier. Stop: box extreme or last higher low + spread, capped.
Target: about 1.4R (Volman's 10 vs 7) or ATR-scaled. Skip: false break (price ran straight from the other
barrier), tease (no squeeze), break into a near round number / cluster (I-37). Coulling's zone version
on 15m-1h: zone from 3-bar pivots, entry on a *close* beyond, stop on the far side. Source: V ch.10-13,
C ch.7-8. Evidence: charts only. Fit: good, fully codeable, intraday; spread decides (I-45).

### I-34 Zone duration vs move size
For every detected congestion zone record duration (bars), height, number of touches; measure the move
after the break (MFE in zone heights and R over 5/10/20 bars). Does a longer zone give a bigger move
(Wyckoff cause and effect)? If yes, use as a filter or to scale targets for I-33. Source: C ch.4, 7, 11.

### I-35 Second break at the 20 EMA
Trend: EMA(20) slope and most recent bars on one side. Pullback to the EMA; a first break of a signal
bar in trend direction fails (no new extreme within 1-3 bars, pullback extreme holds within 1 pip);
second signal bar broken → enter 1 tick beyond; stop beyond the pullback extreme; reject if the second
entry is far beyond the first (no retest). Volman's preferred setup. M1 only roughly matches his
~30-second bars. Source: V ch.9 (also DD ch.7, FB ch.8). Fit: FX/gold active hours; cost-critical.

### I-36 ★ Tipping-point exit module
Exit overlay for any entry: stop 1 tick beyond the setup; no breakeven; trail only after a pullback that
tested a prior level or the EMA *and* a later bar took out that pullback bar's extreme; exit when a
bar trades through the stop; fixed target. Compare with: fixed stop, breakeven at +1R, half off at the
first target + breakeven (Aziz), ATR trail, 3-bar pivot trail (Coulling). Run on a random-entry
baseline as well, to separate exit edge from entry edge. Source: V ch.14, A ch.7, C ch.8.

### I-37 ★ Free-path-to-target filter
For any candidate entry find the nearest opposing obstacle (cluster of bars, equal highs/lows, prior
day/session high or low, round number) within the target distance; skip if it is closer than
x × target. Also skip after a spike without buildup into a prior extreme. Aziz's version: skip if the
next level gives less than 2:1, never tighten the stop. Test on strategies 2-4 entries and on I-33.
Source: V ch.15, A rule 5. Cheap with the swing detector.

### I-38 Session-mean (VWAP proxy) hold / rejection (indices)
Anchored mean of typical price from 09:30 New York. After 15 min: long when price pulls back to the
mean from above and a 5-min close holds above; short on a failed test from below. Stop: 5-min close
through the mean + buffer; target prior-day close / high / low or 2R; half at 1R + breakeven (optional).
Source: A VWAP strategy. Later: true tick-volume VWAP from MT5 (I-44) as A/B.

### I-39 Previous-close magnet on gap days
Gap = 09:30 open vs 16:00 New York close. If the gap ≥ x × ATR and price fails at the session mean in
the gap direction after 15 min, trade back toward the prior close (target = prior close); stop beyond
the mean or the opening range; time stop 11:30 or 15:00. Also the opposite (gap continuation). Shares
statistics with I-09. Source: A red-to-green.

### I-40 Exhaustion reversal
M5: ≥ 5 (or 4) same-colour candles, RSI(14) > 90 / < 10 (calibrate: 80/20), price at a prior-day
high/low or round number; then an indecision or opposite candle; enter on the first candle making a
new high (after a fall) / new low (after a rise); stop at the extreme; target the session mean / 20 EMA
/ next level; exit after 3-4 flat bars. Source: A reversal setups. Overlaps with I-16 (shock fade).

### I-41 Wick rejection at a zone; spring / upthrust
Hammer / shooting star (wick ≥ k × body and ≥ m × ATR) at a zone edge (I-33 zones), with the
higher-timeframe bias; or a brief break of the range edge that returns inside with a narrow bar, entry
on the close back above the range middle. Source: C ch.5-6, 11. Low prior: it is close to the sweeps of
failed strategies 1-2; test only as a cheap variant on non-session zones.

### I-42 Breakout retest / role reversal
After a range break (I-33), wait for price to return to the broken barrier without closing back
inside; enter on the break of the signal bar in the breakout direction; stop behind the last arch of
the range. Compare with entering on the break itself. Source: V ch.13 (ARB), C ch.7.

### I-43 M1 path-length activity proxy
For each 5m-1h bar compute the sum of its M1 ranges (path length) and the number of direction changes
as a stand-in for activity. Test Coulling's anomalies: high activity + small net range at swing
extremes (absorption) vs wide range on low activity. Not real volume; once MT5 tick volume exists,
check how well it correlates. Source: C ch.4.

### I-44 Volume rules (blocked)
Relative tick volume per bar (quantiles of the last N bars, per time of day): breakout valid only on
high and rising volume; climax = 2+ wick bars on ultra-high volume at the end of a range; test bars =
narrow, low volume at the range edge; true VWAP. Needs MT5 history with tick volume (histdata has none).
Plan: A/B against the price-only versions (I-33, I-38, I-41). Source: C ch.5-7, 10; A.

### I-45 ★ Cost-to-target filter
For any entry compute spread (plus commission) / target distance; skip when > 0.10-0.15. Volman's own
economics: 1 pip spread on a 10 pip target. Target scaled as max(2.5-5 × M1 ATR(14), 10 × spread).
Source: V ch.1, 14. Same idea as HANDOFF open point 3 (cost filter) and I-21.
