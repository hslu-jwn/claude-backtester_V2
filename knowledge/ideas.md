# Strategy ideas backlog

Testable ideas from the books, merged and de-duplicated. **Nothing here is a trading rule**: an idea
becomes a rule only when the user picks it, it is written into a `docs/` spec and tested (CLAUDE.md ›
Specs are the source of truth). When an idea is tested, set its status and link the ROADMAP step.

Sources: K = Kaufman *TSM* (page), D = Douglas (chapter), H = Hougaard (chapter), V = Volman
*Forex Price Action Scalping* (chapter), A = Aziz *How to Day Trade for a Living* (chapter/setup),
C = Coulling *Volume Price Analysis* (chapter), LP = López de Prado *Advances in Financial ML* (chapter.section),
RC = Carver *Systematic Trading* (page), EC = Chan *Algorithmic Trading* (page), KD = Davey *Building Winning
Algorithmic Trading Systems* (page), WK = Kurt *Bayesian Statistics the Fun Way* (chapter; M1-M10 = the notes' own
extensions to R lists), JK = Kaeppel *Option Trader's Guide* (page). Evidence in the books
is mostly **gross of costs** on 1990-2011 futures, or anecdotal (V, A, C, JK give no statistics at all; LP and WK are method
books with no strategy results; RC and KD report after costs on futures; EC excludes costs). ★ = most promising for our data.

Our data: M1 histdata, XAUUSD, GBPUSD, GBPJPY, NAS100, US500, 2018/2020-2026, price only, costs =
spread + commission + swap, results in R, FTMO limits (5 % daily, 10 % total).

Already tested and failed (do not re-propose unchanged): session-zone sweep (1), NY-open index sweep
(2), no-wick candle (3), Kaufman trend following with stop-and-reverse (4). See ROADMAP 6, 8, 9, 10.

## Overview

| ID | Idea | Type | Symbols / TF | Swap | Source | Status |
|---|---|---|---|---|---|---|
| T-01 | Robustness report: plateau heat map, % profitable combos, halves t-test, shock days, 3 cost levels | tooling | all | – | K ch.21; KD p.106-109 (70 % gate) | done 2026-10-15 (ROADMAP 6.4; heat map via plateau on a family, stressed costs x1.5 instead of 3 levels) |
| T-02 ★ | Random-entry baseline (Monte Carlo of entries): percentile of net R vs 1,000 seeded random-entry runs | tooling | all | – | VectorBT; KD p.109-114; EC p.16-22 (see T-14) | done 2026-10-16 (ROADMAP 12.1, in tools/monte_carlo.py) |
| T-03 | SL and TP inside one candle: resolve the order from M1 instead of "SL first" | tooling | all | – | NautilusTrader | open (ROADMAP 12.2) |
| T-04 | Shared walk-forward splitter (rolling / anchored) | tooling | all | – | VectorBT; K ch.21; LP 11.6, 12.2; KD ch.13 (see T-09) | done 2026-10-16 (ROADMAP 12.3, analytics/walk_forward.py) |
| T-05 | Parameter heat map on the results page | tooling | all | – | VectorBT; K ch.21 | open (ROADMAP 12.4) |
| T-06 | Demo vs engine reconciliation of the same trades | tooling | FTMO symbols | – | HftBacktest; prediction-market-backtesting | open (ROADMAP 12.5, before Phase 7) |
| T-07 | Stressed fills: seeded random slippage, touch is not a fill | tooling | all | – | NautilusTrader | random slippage done 2026-10-15 (12.6, analytics/random_fills.py); touch-is-not-a-fill open |
| T-08 ★ | Trial log + deflated Sharpe: every variant / symbol / timeframe / filter logged with its return series; PSR and DSR (effective N) on per-trade net R; shared-prior shrinkage of the best variant | tooling | all | – | LP 8.1, 11.5, 14.7; RC ch.3; WK M7 | done 2026-10-16 (ROADMAP 12.10; N = raw trial count per family, no clustering or shrinkage yet; DSR >= 0.95 is verdict check 7) |
| T-09 | CPCV (N groups, k=2, purged + embargoed), PBO via CSCV, time-reversed run; extends T-04 | tooling | all | – | LP 7.4, 11.6, 12.4 | open |
| T-10 ★ | Bayesian win-rate and A/B report: Beta posterior under flat / weak / strong skeptical priors, P(B > A), Bayes factor, trades needed before the MT5 test | tooling | all | – | WK ch.5, 15-17, M1-M10 | implemented and tested 2026-10-23, review and user acceptance pending (V2.4c); prior odds 1:50 against an edge (user, 2026-10-16); spec: research-runner.md > Bayesian view |
| T-11 ★ | Stationarity / Hurst / variance ratio / half-life / lag-correlation diagnostic per symbol, timeframe and half | study | all; M5-D1 | – | EC p.41-48, 134-137; LP 17 | done 2026-10-19 (ROADMAP 11.11): no stationarity; H1 reversal real but 0.2-0.5 of a spread, not tradeable |
| T-12 | Carver forecast engine: continuous ±20 forecasts, FDM / IDM, vol-target sizing, position inertia | tooling | all | n/a | RC ch.7-11, App.B, D | open |
| T-13 ★ | Entry-only screening battery: fixed-bar exits, equal-R stop / target, random exit, forward-return hit rate, time-frame lift, reversed signal with costs twice | tooling | all | – | KD p.88, 105-109; JK p.100 | built 2026-10-20 (ROADMAP 12.12); first audit of strategies 1-7: all FAIL |
| T-14 | Matched-monkey test (random entry / exit / both, 8,000 runs, matched count, long share, hold) + random entry with vol trailing stop; extends T-02 | tooling | all | – | KD p.109-114; RC ch.13 | matched monkeys implemented and exercised 2026-10-23 (V2.4c), review/user acceptance pending; volatility-trailing null remains open |
| T-15 | Synthetic OU / random-walk null for SL-TP heat maps and barrier-probability reference | tooling | all | – | LP 13; JK p.91-95 | open |
| T-16 | Strategy-risk / precision calculator for FTMO: precision needed for a target Sharpe, P[precision < threshold], posterior Monte Carlo of the account | tooling | R lists | – | LP 15; RC ch.9; WK M6 | open |
| T-17 | Pre-registered gate pipeline: numeric gates in `docs/`, quit rule, MT5 incubation, live performance cone | process | all | – | KD ch.8-14, 20, 23 | open |
| T-18 | Combination report: daily-merged Monte Carlo, correlation (whole history and 6-12 month windows), IDM check, HRP vs equal weight | tooling | strategies | – | KD ch.15; RC ch.8, 11; LP 16 | open |
| T-19 | Effective sample size: uniqueness weights for overlapping trades, count bets not trades | tooling | all | – | LP 4, 14.3 | open |
| I-22 | "Book of Truths" report: R by hour, weekday, Friday, month-end, Aziz windows | tooling | all | – | H; A ch.7 | done 2026-10-15 (ROADMAP 6.5, results page) |
| I-01 ★ | Noise / regime study: ER per symbol, timeframe, half | study | all, 15m-1d | – | K ch.1, 17, 20, 23 | done 2026-10-14 (ROADMAP 11.1): all markets near random-walk noise, indices not noisier; ER explains the sign of strategy 4's gross R, not enough to pay costs |
| I-02 | Trend-quality gate (ER, regression r, strength osc.) on strategies 2 and 4 | filter | all | – | K p.10-14, 275, 408 | dropped by the user 2026-10-15 (ROADMAP 11.1: noise only picks the better part of a signal without net edge) |
| I-09 ★ | Open / gap / trend-day statistics on indices | study | NAS100, US500 | none | K ch.15-16, H; EC p.93-96, 155-157 | done 2026-10-15 (ROADMAP 11.2): gap fill mostly random-walk touch, no first-30 continuation, 7 % trend days; only candidate = I-39 |
| I-17 | Time-of-day drift by session | study | XAUUSD, FX | none | K p.689-699; EC p.63, 96 | open |
| I-07 ★ | Volatility-scaled opening range breakout | signal | indices, gold; 5-15m | none | K p.759-764; A ORB | development 2026-10-16 (ROADMAP 11.10): price-only no edge (0/23 variants net positive, costs ~0.1 R/trade); candidate only with the volume filter on US indices; test period 2021-09..2026 (ROADMAP 11.10): band 0.25 ATR + volume +30 R net / 301 trades (+0.10 R/trade) but 2024-26 only +2.7 R: positive, fading, not significant |
| I-08 ★ | ORB only after inside / NR4 day or low vol | filter+signal | all; 5-15m | none | K p.759-764 | development 2026-10-16: inside-day filter best gross (+0.08 R/trade) but net -0.02 R/trade; NR4 net -0.07 |
| I-16 ★ | Intraday volatility-shock fade | signal | gold, indices; 5-30m | none | K p.775-777, 626-634 | open |
| I-03 ★ | RSI(2) mean reversion | signal | indices (1h-1d) | 0-1 night | K p.389-390; KD App.A | open |
| I-05 ★ | Pullback entry inside a slow trend | signal | all; 15m-1d | some | K p.950, 418, 835; JK p.101 | open |
| I-11 | Midday support/resistance + afternoon breakout | signal | indices; 15-30m | none | K p.754 | open |
| I-10 | Opening inside-bar break with double top | signal | indices; 10m | none | H | open |
| I-12 | Fade outside bar / key reversal with range filter | signal | all; 1h-1d | short | K p.111, 157-158 | open |
| I-13 | Nofri congestion third-bar reversal | signal | FX, gold; 15m-1h | none | K p.155-157 | open |
| I-14 | ATR swing-filter (event) trend | signal | all; 1h-1d | yes | K p.182-191, 218 | open |
| I-15 | 3-ATR momentum continuation bar | signal | indices, gold | short | K p.333, 380 | open |
| I-18 | Month-end index flow | signal | NAS100, US500 | ~5 nights | K p.726-729, 480 | open |
| I-19 | Gustafson 4-down-closes long | signal | indices; 1h-1d | 1-8 nights | K p.1010; KD App.A | open |
| I-20 | NAS100/US500 ratio stress (pairs) | signal | NAS100+US500 | both legs | K p.583-612 | open |
| I-23 | Coded chart patterns (rectangle, double top, H&S) | signal | all; 1h-1d | yes | K p.176-178 | open |
| I-30 | Round numbers and daily pivots (also as target/skip layer) | signal+filter | all; 1-15m | none | K p.81, 143, 167; V ch.7-15; A | open |
| I-31 | Value area (Market Profile from M1) | filter+signal | all | none | K p.822-830 | open |
| I-32 | Squeeze breakout (Bollinger-in-Keltner, or low short / long volatility ratio) | signal | all; 15m-4h | some | K p.330; JK p.103-105 | open |
| I-04 | Low-vol entry filter, high-vol / shock exit with re-entry | filter+exit | trend systems | – | K p.861-866, 992 | open |
| I-06 | Wait-for-pullback window, scale in over bars | entry mgmt | any signal | – | K p.1076-1079 | open |
| I-24 | Scale out in thirds; minimum 3:1 target gate | exit mgmt | any signal | – | D ch.11; JK p.187, 199 | open |
| I-25 | Press winners: ATR pyramiding / add on new highs | exit mgmt | any signal | – | H; K p.1080-1084, 229 | open |
| I-26 | Drawdown-scaled risk; 20-loser check; daily give-back stop | risk | R lists | – | K p.231; D ch.11; A ch.7 | open |
| I-27 | Volatility-targeted sizing | risk | R lists | – | K p.1046-1054, 1142; RC ch.9; EC ch.8 (see I-53) | open |
| I-21 | Hourly / seasonal volatility sizing, skip low-range hours | risk | all | – | K p.453-454, 561; LP 19.3 | open |
| I-28 | Streak dependence test; equity-curve filter | risk/study | R lists | – | D ch.5; K p.1086 | open |
| I-29 | Carry: hold the positive-swap side with a trend/stop guard | signal | GBPJPY etc. | earns | K p.596-599; RC App.B (see I-51) | open |
| I-33 ★ | Compression block/range break with EMA squeeze and tension | signal | all; M1-M5 (15m for zones) | none | V ch.10-13; C ch.7 | open |
| I-34 | Zone duration vs breakout move size (cause and effect) | study/filter | all | – | C ch.4, 7 | open |
| I-35 | Second break (W/M) at the 20 EMA, micro pullback | signal | FX, gold; M1-M3 | none | V ch.7-9 | open |
| I-36 ★ | Tipping-point exit module; breakeven vs no breakeven A/B | exit mgmt | any entry | – | V ch.14; A; C ch.8; RC ch.13 | open |
| I-37 ★ | Free-path-to-target skip filter | filter | any entry | – | V ch.15; A rule 5 | open |
| I-38 | Session-mean (VWAP proxy) hold / rejection | signal | indices; 5m | none | A VWAP | open |
| I-39 | Previous-close magnet on gap days (red-to-green) | signal | indices; 5m | none | A ch.7; EC p.93-96, 155-157 (opposite side: I-46) | no edge 2026-10-16 (ROADMAP 11.4-11.7: weak positive 2020-26, negative 2018-19, walk-forward +0.6 R / 1423 trades, Monte Carlo verdict NO EDGE for walk-forward and default; random fills and costs x1.5 kill it) |
| I-40 | Exhaustion reversal: 5+ candles, RSI extreme, at a level | signal | indices, gold; 5m | none | A reversal | open |
| I-41 | Wick rejection at a zone, spring / upthrust (price-only) | signal | all; 15m-1h | some | C ch.5-6 | open |
| I-42 | Breakout retest / role-reversal second entry | signal | all; M1-1h | none | V ch.13; C ch.7 | open |
| I-43 | M1 path-length activity proxy (absorption study) | study | all | – | C ch.4 | open |
| I-44 | Volume rules (relative tick volume, climaxes, true VWAP) | signal+filter | needs MT5 tick volume | – | C; A | unblocked 2026-10-15 (MT5 tick volume, ROADMAP 11.5); user 2026-10-15: test it as an A/B activity filter, first on the opening-range breakout; result 2026-10-16: relative tick volume >= 1.5 improves 17 of 18 ORB variants (+0.013 R/trade) |
| I-45 ★ | Cost-to-target filter: skip when spread/target > 0.10-0.15 | filter | any entry | – | V ch.1, 14; RC ch.12 (see I-52) | built as cost / stop (`CostConfig.max_cost_r`, 2026-10-14); strategy 2 at 0.10 R: net +57 R better, still negative (ROADMAP 10.5) |
| I-46 ★ | Gap momentum: open beyond the previous high / low by 0.1 sd of daily returns, exit at the close; FX version from the London open | signal | NAS100, US500, XAUUSD; GBPUSD (05:00-17:00 ET); 5m-1h | none | EC p.155-157 | tested 2026-10-20 (ROADMAP 11.12): indices and GBPUSD / EURUSD no edge (decayed after 2018); XAUUSD London-open version positive on MT5 2021-26 (+17.8 R, 347 trades) but NO EDGE verdict (t 1.0) |
| I-47 | Euro-night style fade: ATR-stretched average high / low limit entry, session exit | signal | GBPUSD, XAUUSD; 60-105m | none | KD ch.18 | open |
| I-48 | Euro-day exhaustion fade: new 3-5 bar extreme against 70-80 bar momentum, limit beyond the extreme | signal | FX, gold, indices; 60m | none | KD ch.18 | open |
| I-49 ★ | Volatility-percentile regime filter: decile rank of realised vol vs own history, strategies run per bucket | filter | all | – | JK p.64-72; EC p.184-186 | open |
| I-50 | Meta-labelling of an existing primary signal: rule-based features, purged time blocks, trade / skip | filter | strategies 1-6 | – | LP 3.6-3.8, 8, 9.4 | open |
| I-51 | EWMAC multi-speed (16:64, 32:128, 64:256) with swap as the carry forecast | signal | all; D1 | yes (carry) | RC ch.7-8, App.B; EC ch.6 | open |
| I-52 | Cost-limit screen: turnover x standardised cost <= 1/3 of the plausible pre-cost Sharpe | filter | all | – | RC ch.12 | open |
| I-53 | CPPI sub-account and Kelly per strategy for the FTMO limit | risk | R lists | – | EC ch.8 | open |
| I-54 | Cool-down after a win / loss (re-entry timing) on a breakout entry | entry mgmt | any | – | KD p.24-28 | open |
| I-55 | CUSUM event triggers (volatility-scaled filter rule), continuation or fade | signal | all; 5m-1h | none | LP 2.5.2.1 | open |
| I-56 | Structural-break (CUSUM, SADF) and entropy regime flags | filter | all; H1-D1 | – | LP 17, 18 | open |
| I-57 | Probability-to-size mapping and concurrency sizing | risk | R lists | – | LP 10, 4.3 | open |
| I-58 | Half-life z-score mean reversion (linear or Bollinger), gated by T-11 | signal | all; M15-H4 | none intraday | EC p.48-50, 70-72 | open |
| I-59 | FX cointegration pair (AUDUSD vs CADUSD style) | signal | needs AUDUSD, USDCAD from histdata | rollover | EC p.108-112 | blocked (symbols not in the data) |
| I-60 | Sigma-band stops and targets scaled with sqrt(holding time) | exit mgmt | any entry | – | JK p.161, 91-95 | open |
| I-61 | Momentum after a large hourly move: after an H1 bar beyond k robust sd, trade its direction for h bars (11.11: small moves revert, big ones continue) | momentum | FX, metals, indices / H1 | none if flat by the session end | 11.11 study | tested 2026-10-20 (ROADMAP 11.13): no robust edge; continuation carried by the top 1 % events; NAS100 H1 k4 h2 closest (+0.20 sd trimmed, t 1.7, decaying) |
| I-62 | No-wick retest: limit at the no-wick end of a trend candle (Bard FX video), many stops / targets / filters | signal | all; 5m-1h | none (16:55 exit) | user 2026-10-21 | **no edge** 2026-10-21 (ROADMAP 11.17): 0.4 % of 4,608 variants positive; gold H1 cluster failed out of sample (-0.02 R/trade) |

## Suggested order (Claude's proposal, the user decides)
1. **Tooling first** (T-01, I-22): every later test then reports robustness the Kaufman way.
2. **Cheap studies** (I-01, I-09, I-17): find *where* there is structure (which symbol, timeframe,
   session, half) before building a strategy. Hours of work, no new strategy folder.
3. **Day-trade strategies without swap** (I-07/I-08 ORB family, I-33 compression break, I-16 shock
   fade, then I-03 RSI(2), I-05 pullback). These avoid the swap problem that killed strategy 4 and fit
   the noisy indices. Apply I-45 (cost-to-target) and I-37 (free path) as filters from the start.
4. **Management and risk layers** (I-36, I-25, I-24, I-26, I-27) on the best candidate only: they
   reshape an edge, they cannot create one.

**Addition 2026-10-16 (books LP, RC, EC, KD, WK, JK; Claude's proposal, the user decides).**
**Order agreed by the user 2026-10-16:** T-08 trial log + deflated Sharpe (ROADMAP 12.10) -> T-11 diagnostic study (11.11) -> I-46 gap momentum (11.12). T-10 prior set by the user 2026-10-16: prior odds 1:50 against an edge.

5. **Honesty tooling before any new strategy:** T-08 (trial log + deflated Sharpe) and T-10 (Bayesian report with the required trade count),
   then T-19, T-09, T-14. They decide how any later result is read; the five failed strategies and ~100 variants already count as trials.
6. **Cheap diagnostic study:** T-11 (stationarity, half-life, Hurst, variance ratio, lag-correlation grid, time-of-day autocorrelation with
   I-17) per symbol, timeframe and half. It says which horizon trends or reverts at all, before a rule is written.
7. **Candidates after that:** I-46 (gap momentum, the opposite side of the failed gap fade; two symbol classes, no swap), the screening battery
   T-13 run on every idea first, I-49 as a regime layer for the strategies that exist, then the combination tests (T-12 / T-18, I-51) only if at
   least one part shows a positive net edge. Expect little: Carver's realistic Sharpe is 0.3-0.5 and retail day-trading costs are the main
   obstacle (I-52 checks this per idea).

## Details

### T-01 Robustness report (tooling)
Add to every grid run: heat map with neighbour smoothing, average ± st.dev over the whole declared
range, % profitable combos (target ≥ 70 %), Welch t-test of trade R between halves, shock-day P/L
(range > 3.5 × ATR(10)), results at 0 / realistic / +50 % costs, return kurtosis flag (> 7), best-trade
removed. Source: K ch.21 (p.916-981), ch.2 (p.28, 43, 47). See `topics/testing-and-robustness.md`.
Davey's gate is the same 70 %: ≥ 70 % of a 10x10 grid profitable = pass, 30-70 % allow at most two added rules, < 30 % test the reversed signal
with costs paid twice (KD p.106-109); added to T-13.

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
Extension (EC p.93-96, 155-157): split the gap buckets (in sd of 90-day daily returns) by *beyond the prior high / low or not* and by a 20-day MA
trend filter, and measure open-to-close return per bucket and sign; Chan claims reversion for moderate gaps with the filter and continuation
beyond the prior range. The continuation side is I-46.

### I-17 Time-of-day drift by session (XAUUSD, GBPUSD, GBPJPY)
Average return, sign persistence and range per 30-min bucket in UTC, split by Tokyo / London /
overlap / New York and conditioned on the first bar of each session; per year and half. Trade only
buckets with a stable sign and a move much larger than the spread. Source: K p.689-699 (EURUSD gain
concentrated in Europe, extremes at the European open). Also gives the range profile for I-21-style
sizing (skip hours whose range is small vs the spread; K p.453-454).
Chan's variant (EC p.63, 96): per half-hour bucket compute mean return and lag-1..k autocorrelation of bar returns, per half-sample; candidate
rules only where autocorrelation is robustly negative (reversion window) or positive (continuation window). "Daily bars show a random walk, a
specific window can still revert." Runs with T-11.

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
2023-26. Differs: counter-trend, very short hold. Davey's baseline of the same family: after 2 down closes buy (2 up closes short) with an ATR stop
0.5-1.25 x ATR(14) (KD App.A p.248-249); cheap to run next to I-03 and I-19 as a benchmark.

### I-05 ★ Pullback entry inside a slow trend
Slow trend (e.g. SMA 100-200 or KAMA direction, or 1h trend for 5-15m entries) up AND fast trend
(10-20 bar MA) turns down, or 5-bar stochastic < 20, or RSI(2) < 10 → buy; exit when the slow trend
flips, or at momentum zero; stop k·ATR; no stop-and-reverse. Source: K p.950-951 (Nasdaq: PF 1.51 →
2.26, winners 35 → 47 %, trades −66 %), p.376, 418, 426, 835-838 (Elder triple screen, ratio ~5
between timeframes). Fit: all symbols; less time in market than strategy 4 → less swap. Kaeppel's variant: trend by MA, Wilder RSI(14) pullback against it, exit after 7 bars or
at the opposite extreme of a second oscillator (JK p.101, one chart, no thresholds); low priority next to the Kaufman version.

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
disguise; benchmark against buy-and-hold over the same days. Same family as Davey's two-closes baseline (see I-03).

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
Source: K p.330. No evidence given. Kaeppel's compression trigger (JK p.103-105, no statistics): short / long realised-volatility ratio (6-day / 100-day)
in its lowest decile, or days since the last N-day extreme, then OCO stop entries of the compressed range, stop at the opposite side, target 2-3R or a
time exit, on 1h-4h. Run as a second trigger definition of this idea; ask whether the compression state adds anything over plain I-07/I-08 breakouts.

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
the engine. Kaeppel adds: take profit at ~80 % of the planned target; after +1R take half and trail the rest at half the peak open profit (JK p.187,
199); evidence: showcase trades only. Test as exit variants on existing trade lists (SL-first in one candle).

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
2-3 trades a day. Source: K p.231; D ch.11; A ch.7. Pure `risk/` work on R lists. CPPI and Kelly-per-strategy alternatives: I-53.

### I-27 Volatility-targeted sizing
Risk per trade = r % / (k·ATR) (what our R model already does) plus an account-level scale = target vol
/ lagged realised vol of the strategy's daily R; rebalance only on > 20 % change. Measure FTMO breach
probability. Source: K p.1046-1054, 1142-1145 (info ratio 1.27 → 1.38). Carver: target = long-run annual sigma of the account in % of current capital, half Kelly of a
pessimistic Sharpe (SR 0.4 → 20 %, halve for negative skew), capital recomputed daily, 10 % position inertia (RC ch.9-10); see
`topics/position-sizing-and-risk.md`. FTMO check with T-16.

### I-21 Hourly / seasonal volatility sizing
Average range per hour bucket, weekday and month per symbol (from I-17 / I-09); scale risk down in
historically volatile buckets, skip buckets where the range is small vs the spread (cost-to-range
filter). Source: K p.453-454, 561-562. Links to HANDOFF open point 3 (cost filter). Better volatility denominator: Parkinson high-low sigma² = mean[(ln H/L)²]/(4 ln 2) is more efficient than
close-to-close (LP 19.3).

### I-28 Streak dependence and equity-curve filter
Test whether the outcome after 1, 2, 3 losses or wins differs from baseline (runs test, lag-1
autocorrelation); compare flat risk with size-up-after-wins and skip-after-losses; test trading only
when strategy equity > its 10/60-trade MA. Source: D ch.3, 5, 7; K p.1086 (equity-curve filter
inconsistent). If no dependence, flat fractional risk is justified.

### I-29 Carry (positive swap side)
Hold the direction that earns swap (e.g. long GBPJPY if FTMO's rate is positive), size by volatility,
with a trend filter or an x·ATR drawdown exit; rebalance monthly. Source: K p.596-599 (forward bias;
violent unwinds). The only idea that earns swap; unwinds (2008, 2020, Aug 2024) threaten the 10 % limit. Carver's carry forecast = expected return if prices stay unchanged / annual price sigma, scalar 30,
cap 20; for our CFDs the swap table (long minus short) is the carry (RC App.B); built into I-51.

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
baseline as well, to separate exit edge from entry edge. Source: V ch.14, A ch.7, C ch.8. Carver's null for the exit side: random entry + trailing stop X daily sigma from the best price, no target, X 1-10 (RC ch.13);
goes into T-14.

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
statistics with I-09. Source: A red-to-green. Status note: no edge for the fade (ROADMAP 11.7). Chan's opposite rule is I-46; do not re-run the fade with a MA filter
without new evidence (EC buy-on-gap filter: price above its 20-day MA).

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
Source: V ch.1, 14. Same idea as HANDOFF open point 3 (cost filter) and I-21. The per-strategy version (turnover x standardised cost) is I-52.

## Details of the 2026-10-16 additions (LP, RC, EC, KD, WK, JK)

### T-08 ★ Trial log + deflated Sharpe (tooling)
Log every run (variant, symbol, timeframe, filter, date) with its per-trade or daily net R series in one place. On the selected variant report PSR(0)
and DSR = PSR with SR* = sqrt(V) [(1-g) Z⁻¹(1-1/N) + g Z⁻¹(1-1/(N e))], g = 0.5772, V = variance of the non-annualised Sharpe across the trials, N =
effective (independent) trials, clustered from the return series; pass > 0.95. Also the shared-prior shrinkage of the best variant (WK notes M7).
Source: LP 8.1, 11.5, 12.5, 14.7; RC ch.3 (Tables 3-4: 100 zero-skill rules accept ~30 at SR 0.5); WK M7. Evidence: theory plus simulations; no
strategy results. Fit: excellent, needs only R lists; answers "best of 24 variants". Swap: n/a. Differs from the robustness report T-01: a probability
with the trial count, not a descriptive share. See `topics/statistics-and-bayes.md`.

### T-09 CPCV + PBO (tooling)
N ordered time groups (8-10), every combination of k=2 as test set, purge trades overlapping a test boundary and embargo ~1 % of bars; choose the
parameter set on the training groups, evaluate on the held-out groups, stitch phi = C(N-1,1) = N-1 paths, one Sharpe per path. PBO by CSCV on the
trial matrix (S = 16 blocks): share of splits where the in-sample best ends below the OOS median. Add a time-reversed run (a rule that works only
forward is suspect). Keep the final holdout (after 2021-09-14 MT5 data) outside the groups. Source: LP 7.4, 11.6, 12.2-12.5. Evidence: theory.
Fit: good (2018/2020-2026 intraday, many trades); extends T-04 (done) which is a single path. Swap: n/a.

### T-10 ★ Bayesian win-rate and A/B report (tooling)
Per strategy variant and per sample (pre-2021-09-14, MT5): Beta posterior of the win rate under three priors (flat, weak skeptical mean = break-even
strength 20, strong skeptical strength 100-200; the prior values are fixed in `docs/` first, user decision), 95 % interval, P(win rate > break-even p* =
L/(W+L)); Student-t posterior of mean R with a skeptical Normal(0, 0.05-0.10 R) prior; A/B by sampling both posteriors (P(B > A), distribution of b - a), paired
on common signals for filters; Bayes factor edge vs no edge with the ln-BF formula and the trades needed for a target posterior odds (1,400 trades for 55 % vs 50 %
at prior 1:50); grid posterior with a spike-and-slab prior; Bayesian power table (n vs P(conclude edge)) before the single MT5 test. Source: WK ch.5, 9, 13-19 and notes
M1-M10. Evidence: textbook; the extensions to R multiples are the notes' own. Fit: excellent, cheap. Swap: n/a. Differs: states uncertainty in probabilities
and makes the "no edge" outcome pre-declared.

### T-11 ★ Stationarity / half-life / Hurst diagnostic (study)
For XAUUSD, GBPUSD, GBPJPY, NAS100, US500 on M5, M15, H1, H4, D1 and per half (2020-22, 2023-26): ADF statistic and lambda on log price with 1 lag, generalised
Hurst H(q=2) over lags 2-100 bars and variance-ratio statistics at several q, half-life = -ln 2 / lambda, and the lag-correlation grid between the past k-bar and the
future h-bar return on non-overlapping pairs, k, h in {1, 5, 10, 25, 60, 120, 250}; plus return and autocorrelation per half-hour bucket (I-17). Source: EC p.41-48,
134-137 (tests use every bar and have more power than a trade backtest; half-life > a few hundred bars = no strategy; H < 0.5 short horizons, > 0.5 long is the typical
pattern); LP 17 (SADF, CUSUM as optional extras). Fit: excellent, closed bars only, no new data. It measures; it does not prove tradeability after spread and swap. Also
shows whether strategy 4's horizons (15m-1d) had any momentum at all. Differs from all five failed strategies: it picks the horizon instead of guessing a rule.

### T-12 Carver forecast engine (tooling)
Per instrument: daily-close forecasts for EWMAC 16:64, 32:128, 64:256 (optionally 8:32), price-unit sigma by EWMA(L=36) of daily returns, scalars 3.75 / 2.65 /
1.87 (5.3), cap 20; weights 42/16/42 (or with carry 21/8/21/50); multiply by FDM = 1/sqrt(w'Hw) from the measured correlations (floor 0, cap 2.5), cap 20; position =
forecast x (daily cash vol target / instrument value vol) / 10; trade only when the target differs from the current by > 10 %; vol target 10-20 %. Source: RC ch.7-11,
App.B, D. Evidence: pooled backtests on 40+ futures after costs, SR ~0.5 for 6 instruments, ~1.0 for 45; trend + carry ~85 % of his full system. Fit: method fits (continuous
forecast, no stop-and-reverse); only 5 instruments, indices 0.75-0.9 correlated, so IDM only ~1.2-1.4; swap must be net of carry. Differs from strategy 4: see
`topics/trend-following.md`. Also the test bed for T-18 (does a blend of our six strategies' signals beat the best part).

### T-13 ★ Entry-only screening battery (tooling)
For any candidate entry strip the real exit and run: (a) exit after N bars (N = 1, 2, 3, 5, 10, 20 on the signal timeframe), net of spread; (b) equal-R stop and target (1R/1R,
~50 % before costs for a no-edge entry); (c) exit at random times with the same mean hold; plus the forward-return hit-rate scan (share of cases higher / lower x bars later and
mean net return, compared with the unconditional rate and a shuffled null), a time-frame lift step (rerun an intraday failure on 15m / 60m / 4h / D1), and the
reversed-signal check with costs paid twice for grids below 30 %. Pass: win rate clearly above 50 % (his heuristic 52-60 %) and positive average net R in ≥ 70 % of the grid.
Source: KD ch.12 p.105-109, ch.10 p.88; JK p.100. Evidence: his stated experience (most ideas die here); no numbers beyond the euro example (76-85 % of cells profitable).
Fit: good, cheap with M1 and R multiples; keep holds intraday (swap). Differs: a harness for any candidate (sweep, FVG, gap, ORB, no-wick), not a strategy; replaces designing a
full strategy per idea. Our failed strategies could be re-audited with the reversed-signal check (reversals rarely survive costs).

### T-14 Matched-monkey test (tooling)
V2.4c implementation (2026-10-23): per-symbol exact stop/hold permutations, three kinds,
default 1,000 runs (configurable to 8,000), runner 200 runs, net-R and exit-order DD percentiles.
Spec: `docs/risk-management.md` > Matched monkeys. Development check: default trend following,
XAUUSD, 53 trades, 200 runs; net-R percentiles 47.5 / 12.0 / 37.5 and favorable DD percentiles
34.5 / 11.5 / 31.0 (kinds 1/2/3), all fail. Report:
`results/monkeys/trend_following_20261023T201820334384Z/report.md`.
Independent review and user acceptance pending. The separate Carver volatility-trailing null
and live rolling monitoring remain outside this brief.

Replace entry by a random entry matched on trade count, long share and mean hold; the same for the exit (random exit time, same hold distribution, same session-end rule); both
random; 8,000 runs each; require the real result to beat ≥ 90 % of runs on net R and on max DD. Reuse on the last 6-12 months live: 60-70 % percentiles = warning, < 50 % =
edge gone. Add Carver's null: random daily entries exited only by a trailing stop X x daily sigma (X 1-10), which was profitable on real data from trend capture alone.
Source: KD p.109-114, App.A; RC ch.13. Evidence: example percentiles 99-100 % in development, 49-73 % and ~1-72 % in the phases before a stop. Fit: good, extends T-02 (random entries,
done) with matched exposure, random exit and the combination. Swap: matched by hold. Differs: judges the edge against randomness controlling for exposure, not against zero.

### T-15 Synthetic OU / random-walk null for SL-TP grids (tooling)
Fit phi and sigma of the instrument (or the signal's P&L) by OLS of the deviation on its lag, half-life = -ln 2/ln phi; simulate 100,000 paths with a max holding period; Sharpe heat
map over (profit-take, stop-loss) in sigma or R multiples (e.g. 20 x 20 from 0.5 to 10). (a) Is the optimum a plateau (random walk: flat, no optimum)? (b) Null distribution:
is our best historical grid cell better than the best cell on synthetic random walks of equal length? Add the analytic reference P(target before stop) = S/(S+T) and
the touch probability ~ 2 x the finish-beyond probability. Source: LP 13.4-13.6; JK p.91-95. Evidence: simulations in the chapter (zero equilibrium: small target + large stop best,
Sharpe up to ~3.2 at half-life 5; flat as half-life grows). Fit: very good for the SL/TP sweeps; consistent with the existing random-path Monte Carlo (kind D). Also covers LP's
triple-barrier re-labelling of our trade list (sweep (TP, SL, max hold) in ATR with first-touch, SL first in one candle, all trials logged for T-08).

### T-16 Strategy-risk / precision calculator for FTMO (tooling)
From the trade list: pi+ (mean win R), pi- (mean loss R), n trades per year. Compute the precision p* needed for a target Sharpe (root of the quadratic a p² + b p + c = 0, a = (n + SR²)(pi+ - pi-)²,
b = [2 n pi- - SR²(pi+ - pi-)](pi+ - pi-), c = n pi-²), the break-even precision |pi-|/(pi+ + |pi-|) plus costs, and P[p < p*] by bootstrapping n x k years of outcomes; then map to
FTMO with the Monte Carlo already built, drawing p from the Beta posterior (T-10) for each simulated account. Source: LP 15.2-15.4; RC ch.9 (Tables 20-27); WK M6. Evidence: analytical
examples (a drop of precision from 0.70 to 0.67 erases the profit). Fit: excellent, R based, no new data. Differs: evaluation tool; pairs with I-27 / I-53.

### T-17 Pre-registered gate pipeline (process)
Write numeric pass / fail per stage into a `docs/` spec before any test: goals; limited test on 1-2 random years (25 %) with the T-13 battery; walk-forward with in / out / fitness fixed
beforehand; 1-year Monte Carlo (ruin < 10 %, median DD < the FTMO-scaled limit, return/DD > 2, P(profit year) reported); 3-6 months incubation on MT5 data (t-test of walk-forward vs
incubation trades, overlay of equity curves); live at minimum size with a written quit rule (average of 1.5 x worst walk-forward DD and the 95th-percentile Monte Carlo DD), return and
drawdown efficiency, and a performance cone with Monte Carlo percentile bands (10 % line warning). Per-idea checklist with version letters (many letters = too much tweaking). Source:
KD ch.8-14, 17, 20, 23. Evidence: his base rate of 100-200 ideas per winner; his live euro record was flat for 15 weeks. Fit: matches our develop-before / test-once-on-MT5 split
(2021-09-14); the incubation is the MT5 forward set. Differs: process, not a strategy.

### T-18 Combination report (tooling)
Merge strategies' trades into daily R (same day netted); resample whole days; compare median max DD, return, return/DD and P(profit year) with each alone; daily-return correlation over
the full history and rolling 6-12 month windows; R² of the combined curve; IDM = 1/sqrt(w'Hw) (floor 0, cap 2.5) and the realised vs target vol; HRP weights (distance sqrt((1-rho)/2),
quasi-diagonalisation, recursive bisection) vs equal weight vs inverse variance on a rolling 260-day lookback re-estimated every 22 days; stress with correlations raised. Source: KD
ch.15, 19; RC ch.8, 11; LP 16. Evidence: two euro systems return/DD 2.2 and 5.2 → 6.7 combined; HRP out-of-sample variance 0.067 vs 0.093 (inverse variance) vs 0.116 (min variance)
in simulation. Fit: relevant once at least 3 parts exist; with 2-3 parts equal weight is nearly the same. Zero-edge parts combine to zero edge.

### T-19 Effective sample size (tooling)
For overlapping trades compute the concurrency per bar, label uniqueness = 1/(number of labels using the bar), average uniqueness per trade; report effective N next to the trade count and
use uniqueness weights (and bets instead of trades) in t-statistics and in the Monte Carlo. Source: LP 4.3-4.6, 14.3. Evidence: theory (bootstrap on overlapping labels keeps only
~(1 - 1/e) of K unique draws). Fit: good for strategies with several signals open or multi-bar holds; our t-stats and Monte Carlo may overstate significance.

### I-46 ★ Gap momentum (Chan)
Gap = today's open vs yesterday's high / low. Long if open > prior high + 0.1 x sd (sd of 90-day daily close-to-close returns, entryZscore range 0-0.5), short if open < prior low - 0.1 x sd;
exit at the close (no overnight). Indices: cash open 09:30 New York to 16:00. FX / gold: day from 17:00 ET (close) to 05:00 ET (London open), the weekend gap is the real one. Report both
directions per gap bucket (study part, with I-09). Source: EC p.155-157 (rationale: stop orders cluster beyond the prior extreme and cascade after a long closed period). Evidence:
Eurostoxx 50 future APR 13 %, Sharpe 1.4 (2004-12); GBPUSD APR 7.2 %, Sharpe 1.3 (2007-12); **gross of costs**. A VIX above 35 cut the Sharpe to 0.16 (EC p.184). Fit: moderate; indices
have a genuine gap, FX gaps are small and signals few; spread decides. Swap: none (flat at the close). Differs: it is the **opposite side of the failed gap fade (strategy 5 / I-39)**:
continuation after a gap *beyond the prior range* instead of a fade to the previous close; test with robustness report, halves, stressed costs; if the fade has no edge the continuation
may or may not.

### I-47 Euro-night style fade (Davey)
Bars 60-105 min on GBPUSD / XAUUSD, session 18:00-07:00 ET, new trades only until 01:00. LongPrice = SMA(High, Nb) - ATRmult x ATR(NATR), ShortPrice = SMA(Low, Nb) + ATRmult x ATR(NATR)
(his ranges Nb 9-19, NATR 73-93, ATRmult 2.55-3.15); limit order at the nearer; one trade a day; target TRmult x true range (0.51-0.71), stop ≤ ~34 ticks incl. costs, flat at session end.
Source: KD ch.18 p.157-158, App.B. Evidence: 82-85 % of optimisations profitable, walk-forward, Monte Carlo return/DD 2.0 and P(profit year) 85 %, live flat for the first 15 weeks; futures,
4 years. Fit: intraday, no swap; the fill assumption must be penetration-based and the same-bar stop / target rule is critical; limits at 0 slippage but spread on stops and exits. Differs:
long-window (ATR 73-93) stretched-distance fade with a limit entry beyond an extreme and a forced session exit; overlaps in spirit with sweeps and the gap fade (no edge).

### I-48 Euro-day exhaustion fade (Davey)
60-min bars 07:00-15:00 ET. If High ≥ highest High of Xb bars (3-5) and Close < Close[Xb2] (70-80), sell-short limit at High + pipadd pips (2-11) on the next bar; mirror long; one trade a
day, stop 225-425 $ (~18-34 ticks), no target, exit at 15:00. Source: KD ch.18 p.158-159, App.C. Evidence: 76-81 % of optimisations profitable, Monte Carlo return 129 %, return/DD 5.45,
P(profit year) 94 %; relies on 4-6 large winners a year (removing 20 of 614 days leaves it barely profitable). Fit: FX, gold, indices intraday, R multiples with the spread table, flat each
night. Differs: counter-trend fade of a short-term extreme against a long momentum filter, waiting for one more thrust; low prior (outlier dependent).

### I-49 ★ Volatility-percentile regime filter (Kaeppel, Chan)
RV = std of M5 / M15 / D1 log returns (or ATR / price) over N bars (20 days); rank within its own last 2 years (deciles 1-10) or z-score against a 500-day mean with ±1.5 sd bands. Run
every existing and new strategy per bucket (low 1-3, mid, high 8-10): breakout / trend only at low rank, fades only at high rank, or smaller size when high. Source: JK p.64-72, 91-95
(used only for option pricing, no price-direction evidence); EC p.184-186 (VIX > 35 flipped one strategy's Sharpe 1.4 → 0.16 and helped another; sign is strategy specific). Fit: good,
computable from M1 on all symbols, a conditioning layer; may reveal a regime split hidden in the whole-sample failures. Needs the robustness report and a multiple-testing correction (T-08)
because many buckets are tested; thresholds pre-declared, computed from closed bars only. Merges Chan's VIX-like filter.

### I-50 Meta-labelling of an existing signal
Take every signal of an existing strategy (2, 5, 6), compute the triple-barrier outcome in R (win = TP, loss = SL, time exit by sign) as 0/1; 3-6 pre-registered features at the signal bar
(volatility rank, position in the prior-day range, sign of recent serial correlation, weekday, minutes since the open, stop size in ATR); bucket each by quantile and compare mean R in train vs
held-out purged time blocks (single-feature importance); optionally a depth-2 tree or strongly regularised logistic regression. Score by F1 / PnL, not accuracy. Source: LP 3.6-3.8, 8.3, 9.4;
`topics/combining-edges.md`. Evidence: author's claim that meta-labelled systems are more robust, no numbers. Fit: good as a test of whether a rule has any conditional edge; risk: a negative primary
needs pockets of positive expectancy, easily a fluke with a few hundred trades per symbol; count every feature (T-08), same sign in both halves and on post-2021-09-14 MT5 data. Differs: a conditional
layer over the failed strategies; strategy 2's optional filters (best −17 R) are hand-made meta-labels this would formalise. Overlaps I-02 (dropped trend-quality gate) and I-49.

### I-51 EWMAC multi-speed with swap as carry (Carver)
Daily forecasts as in T-12 for three speeds and a carry forecast from the FTMO swap table: (swap long - swap short) annualised / (16 x daily sigma) x 30, cap 20; combined 50 % carry / 50 % trend
(correlation between styles ~0.25). Optional: Chan's 12-month sign rule held 25 days in staggered tranches, gated by the T-11 lag-correlation grid. Source: RC ch.7-8, App.B; EC p.134-152. Evidence:
Carver SR ~0.5 on 6 instruments after costs, honest haircut 65-75 %; Chan Sharpe ~1.0 on three futures, momentum crash after 2008. Fit: moderate; D1, holds weeks, so swap is the whole cost question;
gold carry is funding only (rule shorts gold), FX carry has negative skew (CHF peg); five symbols give a small IDM. Differs from strategy 4: continuous blend, slow speeds, carry earned by swap
instead of paid. Related: I-29.

### I-52 Cost-limit screen (Carver)
Per idea and instrument: standardised cost = 2 x (half spread + commission) in price units / (16 x daily volatility in price units) (intraday: replace 16 by sqrt(bars per year)); turnover =
round trips a year; reject if turnover x cost > 0.13 (a third of a conservative pre-cost SR of 0.40; 0.08 for discretionary). Day trading (500+ round trips) needs ~0.00025 per round trip.
Source: RC ch.12 (Tables 34-36). Evidence: the book's cost tables; applies directly to our cost model. Fit: excellent, will rule out fast variants at once. Related: I-45 (per trade), I-21.

### I-53 CPPI sub-account and Kelly per strategy (Chan)
From the R trade list f = mean/variance per trade-day return; risk per trade = a quarter to half of f. CPPI: with an internal buffer D (0.06-0.08 of equity, below the 10 % limit) trade only a
sub-account of size D x equity with leverage f; reset to D x equity only at a new equity high; never top up after losses; one strategy at a time. Source: EC p.172-182. Evidence: growth rate
0.002484 vs 0.002525 per day (D = 0.5) with the drawdown bounded by D, while half Kelly alone can still draw down 90 %+ in simulation. Fit: directly relevant to FTMO, goes into `risk/` and the
Monte Carlo; CPPI cannot stop gap losses (index gaps, weekend gaps); the FTMO daily reset at midnight Prague is separate. Related: I-26, I-27, T-16.

### I-54 Cool-down after a win / loss
Davey's contest system waited 5 bars after a loss and 20 after a win on a 48-bar highest-close breakout with RSI(30) > 50. Test as a re-entry timing filter on any breakout entry (strategies 4, 6).
Source: KD p.24-28. Evidence: contest returns 107-148 % with 40-50 % drawdowns, market selection by hindsight; not a clean test. Fit: poor (daily trend, swap); likely the fate of strategy 4. Low priority.

### I-55 CUSUM event triggers
On 5m-1h returns, symmetric CUSUM with threshold h = k x daily-vol estimate, k in {0.5, 1, 1.5}; an event fires when the up (down) sum exceeds h, then reset; trade continuation or fade with ATR-scaled
SL / TP, exit at session end; sample only event bars. Source: LP 2.5.2.1. Evidence: none; avoids repeated triggers around a level. Fit: good (price only, intraday); essentially a volatility-normalised filter
rule, so expect results like breakout or mean-reversion families (prior: filter rules lose after costs); mainly a cleaner event definition for other tests. Related: I-14.

### I-56 Structural-break and entropy regime flags
Chu-Stinchcombe-White CUSUM on H1 / D1 log closes (flag when S exceeds sqrt(4.6 + ln(t - n))) or SADF (min window ~100 bars, constant 'ct', lags 1-5, log prices, quantile version); entropy of
binary / sigma-encoded returns over 100-250 bars. Use the flag to switch momentum on or mean reversion off; evaluate with T-08. Source: LP 17, 18. Evidence: chart on E-mini only; entropy none quantitative.
Fit: OK (prices only; SADF is O(T²), so cap the window); risk: just another trend filter with a weak prior. Related: I-02 (dropped), I-49.

### I-57 Probability-to-size mapping and concurrency sizing
If a filter gives a calibrated win probability p: risk fraction m = 2 Z((p - 0.5)/sqrt(p(1 - p))) - 1 x maximum risk, discretised to 0.05-0.1 steps, averaged over open signals; compare with flat size on
the R series. When several strategies fire together scale each by 1/(concurrent positions). Source: LP 10.2-10.5, 4.3. Evidence: none numeric. Fit: cheap in `risk/`; only useful if I-50 or T-10 yields calibrated
probabilities (p near 0.5 gives size near zero, which also helps the FTMO drawdown limits). Does not create edge.

### I-58 Half-life z-score mean reversion
Position (in risk units, capped at ±3) = -(price - MA(L))/std(L) with L = half-life from T-11 re-estimated on past data only (rolling 250 daily bars); or Bollinger (enter z = 1, exit 0) with the same L. M15-H4, flat
intraday. Source: EC p.48-50, 70-72. Evidence: USD/CAD positive with a big drawdown; GLD/USO Sharpe 0.59 linear vs 0.96 Bollinger, gross, in-sample half-life. Fit: poor-to-medium on single FX / gold / index (near random
walks on D1); mostly a check whether H < 0.5 windows exist (use T-11 as the gate). Differs: pure reversion, no sweeps / zones.

### I-59 FX cointegration pair (blocked)
AUDUSD vs CADUSD (same quote currency) with a Johansen hedge ratio on a rolling 250-day window, 20-day z-score, Bollinger entry 1, exit 0, rollover from the swap table. Source: EC p.108-112 (APR 11 %, Sharpe 1.6,
2009-12, gross; the fixed 1:1 cross AUDCAD only 0.54). Fit: our five symbols contain no commodity-currency pair (GBPUSD / GBPJPY is a USDJPY test); needs new histdata symbols. Parked.

### I-60 Sigma-band stops and targets
sigma_h = price x RV_annual x sqrt(h/365) with h the intended holding time and RV from 20 days; stop = k1 x sigma_h, target = k2 x sigma_h with k in {0.5, 1, 1.5, 2}; compare with fixed ATR multiples. Source: JK p.161
(exit at ±2 sigma of the 90-day horizon), 91-95. Evidence: one worked example. Fit: good as a parameterisation of stops / targets; nearly proportional to ATR scaled by sqrt(time), so the difference is the time-scaling
(tighter for short holds, wider for long). Gives a random-walk reference hit rate (T-15). Exit framework, not an entry.

### I-61 Momentum after a large hourly move (study first)
In 11.11 the H1 lag-1 Spearman / winsorized correlation is negative (small moves revert) while the raw Pearson beta is positive for
XAUUSD, GBPUSD, GBPJPY, US500: the big hours continue. Study first: next-h-bar return after hours beyond k = 2 / 3 / 4 robust sd, per symbol,
half and sign, against shuffled returns; only then a rule (entry at the bar close, time exit after h bars, ATR stop). Fit: price-only, intraday;
few events, crash hours dominate (March 2020, SNB 2015, Brexit) -> results must survive removing the top events. Source: ROADMAP 11.11.

### I-62 No-wick retest (user, Bard FX)
Strategy 3's `body_end` entry (limit at the open of a no-wick trend candle) with wider stop choices, other targets,
a clean-structure trend filter, 4h agreement and the video's session windows. Tested 2026-10-21 (ROADMAP 11.17): no
edge on any symbol class. Lesson: the limit fills mostly when price returns through the candle with momentum (adverse
selection); tight stops make costs and the cost model dominate, and a gold "edge" came only from unpriced overnight
holds and the default spread at the daily reopen.
