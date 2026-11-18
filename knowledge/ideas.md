# Strategy ideas backlog

**Live again since 2026-11-09 (the user):** research is back in this team. New ideas are added
here (skill `continue-research`). The former research department's evidence checks of these
ideas (I-xx) are in `knowledge/research/reports/`, its unbuilt drafts in `research/candidates/`.

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
| T-03 | SL and TP inside one candle: resolve the order from M1 instead of "SL first" | tooling | all | – | NautilusTrader | measured on 2023 golden setups (2026-10-23, results/intrabar.md); default sl_first; limit-entry timestamp decision and Opus review pending (ROADMAP 12.2 / V2.4c) |
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
| I-17 | Time-of-day drift by session | study | XAUUSD, FX | none | K p.689-699; EC p.63, 96 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: clock windows (SC1 / SC2, 1,452 cells)) |
| I-07 ★ | Volatility-scaled opening range breakout | signal | indices, gold; 5-15m | none | K p.759-764; A ORB | development 2026-10-16 (ROADMAP 11.10): price-only no edge (0/23 variants net positive, costs ~0.1 R/trade); candidate only with the volume filter on US indices; test period 2021-09..2026 (ROADMAP 11.10): band 0.25 ATR + volume +30 R net / 301 trades (+0.10 R/trade) but 2024-26 only +2.7 R: positive, fading, not significant |
| I-08 ★ | ORB only after inside / NR4 day or low vol | filter+signal | all; 5-15m | none | K p.759-764 | development 2026-10-16: inside-day filter best gross (+0.08 R/trade) but net -0.02 R/trade; NR4 net -0.07 |
| I-16 ★ | Intraday volatility-shock fade | signal | gold, indices; 5-30m | none | K p.775-777, 626-634 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: H1 shock / bar pattern) |
| I-03 ★ | RSI(2) mean reversion | signal | indices (1h-1d) | 0-1 night | K p.389-390; KD App.A | tested (ledger H10, I-03 RSI(2) index mean reversion) |
| I-05 ★ | Pullback entry inside a slow trend | signal | all; 15m-1d | some | K p.950, 418, 835; JK p.101 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: trend + bar pattern) |
| I-11 | Midday support/resistance + afternoon breakout | signal | indices; 15-30m | none | K p.754 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: bar / level pattern) |
| I-10 | Opening inside-bar break with double top | signal | indices; 10m | none | H | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: bar pattern) |
| I-12 | Fade outside bar / key reversal with range filter | signal | all; 1h-1d | short | K p.111, 157-158 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: bar pattern) |
| I-13 | Nofri congestion third-bar reversal | signal | FX, gold; 15m-1h | none | K p.155-157 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: bar pattern) |
| I-14 | ATR swing-filter (event) trend | signal | all; 1h-1d | yes | K p.182-191, 218 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: trend at any speed) |
| I-15 | 3-ATR momentum continuation bar | signal | indices, gold | short | K p.333, 380 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: bar pattern / H1 shock) |
| I-18 | Month-end index flow | signal | NAS100, US500 | ~5 nights | K p.726-729, 480 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: month-end in any form) |
| I-19 | Gustafson 4-down-closes long | signal | indices; 1h-1d | 1-8 nights | K p.1010; KD App.A | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: daily reversal) |
| I-20 | NAS100/US500 ratio stress (pairs) | signal | NAS100+US500 | both legs | K p.583-612 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: pairs (P01 / P02) and two-leg costs) |
| I-23 | Coded chart patterns (rectangle, double top, H&S) | signal | all; 1h-1d | yes | K p.176-178 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: bar pattern) |
| I-30 | Round numbers and daily pivots (also as target/skip layer) | signal+filter | all; 1-15m | none | K p.81, 143, 167; V ch.7-15; A | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: round numbers) |
| I-31 | Value area (Market Profile from M1) | filter+signal | all | none | K p.822-830 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: level rule at tight stops) |
| I-32 | Squeeze breakout (Bollinger-in-Keltner, or low short / long volatility ratio) | signal | all; 15m-4h | some | K p.330; JK p.103-105 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: compression family) |
| I-04 | Low-vol entry filter, high-vol / shock exit with re-entry | filter+exit | trend systems | – | K p.861-866, 992 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-06 | Wait-for-pullback window, scale in over bars | entry mgmt | any signal | – | K p.1076-1079 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-24 | Scale out in thirds; minimum 3:1 target gate | exit mgmt | any signal | – | D ch.11; JK p.187, 199 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-25 | Press winners: ATR pyramiding / add on new highs | exit mgmt | any signal | – | H; K p.1080-1084, 229 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-26 | Drawdown-scaled risk; 20-loser check; daily give-back stop | risk | R lists | – | K p.231; D ch.11; A ch.7 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-27 | Volatility-targeted sizing | risk | R lists | – | K p.1046-1054, 1142; RC ch.9; EC ch.8 (see I-53) | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-21 | Hourly / seasonal volatility sizing, skip low-range hours | risk | all | – | K p.453-454, 561; LP 19.3 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-28 | Streak dependence test; equity-curve filter | risk/study | R lists | – | D ch.5; K p.1086 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-29 | Carry: hold the positive-swap side with a trend/stop guard | signal | GBPJPY etc. | earns | K p.596-599; RC App.B (see I-51) | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: carry / trend with swap (I-51)) |
| I-33 ★ | Compression block/range break with EMA squeeze and tension | signal | all; M1-M5 (15m for zones) | none | V ch.10-13; C ch.7 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: compression family (M15 drafts triaged)) |
| I-34 | Zone duration vs breakout move size (cause and effect) | study/filter | all | – | C ch.4, 7 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: study for a dead family) |
| I-35 | Second break (W/M) at the 20 EMA, micro pullback | signal | FX, gold; M1-M3 | none | V ch.7-9 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: bar pattern) |
| I-36 ★ | Tipping-point exit module; breakeven vs no breakeven A/B | exit mgmt | any entry | – | V ch.14; A; C ch.8; RC ch.13 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-37 ★ | Free-path-to-target skip filter | filter | any entry | – | V ch.15; A rule 5 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-38 | Session-mean (VWAP proxy) hold / rejection | signal | indices; 5m | none | A VWAP | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: bar / level pattern) |
| I-39 | Previous-close magnet on gap days (red-to-green) | signal | indices; 5m | none | A ch.7; EC p.93-96, 155-157 (opposite side: I-46) | no edge 2026-10-16 (ROADMAP 11.4-11.7: weak positive 2020-26, negative 2018-19, walk-forward +0.6 R / 1423 trades, Monte Carlo verdict NO EDGE for walk-forward and default; random fills and costs x1.5 kill it) |
| I-40 | Exhaustion reversal: 5+ candles, RSI extreme, at a level | signal | indices, gold; 5m | none | A reversal | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: oscillator / exhaustion) |
| I-41 | Wick rejection at a zone, spring / upthrust (price-only) | signal | all; 15m-1h | some | C ch.5-6 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: wick rejection) |
| I-42 | Breakout retest / role-reversal second entry | signal | all; M1-1h | none | V ch.13; C ch.7 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: bar pattern) |
| I-43 | M1 path-length activity proxy (absorption study) | study | all | – | C ch.4 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: study for a dead family) |
| I-44 | Volume rules (relative tick volume, climaxes, true VWAP) | signal+filter | needs MT5 tick volume | – | C; A | unblocked 2026-10-15 (MT5 tick volume, ROADMAP 11.5); user 2026-10-15: test it as an A/B activity filter, first on the opening-range breakout; result 2026-10-16: relative tick volume >= 1.5 improves 17 of 18 ORB variants (+0.013 R/trade) |
| I-45 ★ | Cost-to-target filter: skip when spread/target > 0.10-0.15 | filter | any entry | – | V ch.1, 14; RC ch.12 (see I-52) | built as cost / stop (`CostConfig.max_cost_r`, 2026-10-14); strategy 2 at 0.10 R: net +57 R better, still negative (ROADMAP 10.5) |
| I-46 ★ | Gap momentum: open beyond the previous high / low by 0.1 sd of daily returns, exit at the close; FX version from the London open | signal | NAS100, US500, XAUUSD; GBPUSD (05:00-17:00 ET); 5m-1h | none | EC p.155-157 | tested 2026-10-20 (ROADMAP 11.12): indices and GBPUSD / EURUSD no edge (decayed after 2018); XAUUSD London-open version positive on MT5 2021-26 (+17.8 R, 347 trades) but NO EDGE verdict (t 1.0) |
| I-47 | Euro-night style fade: ATR-stretched average high / low limit entry, session exit | signal | GBPUSD, XAUUSD; 60-105m | none | KD ch.18 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: session fade (London fix family)) |
| I-48 | Euro-day exhaustion fade: new 3-5 bar extreme against 70-80 bar momentum, limit beyond the extreme | signal | FX, gold, indices; 60m | none | KD ch.18 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: session fade / exhaustion) |
| I-49 ★ | Volatility-percentile regime filter: decile rank of realised vol vs own history, strategies run per bucket | filter | all | – | JK p.64-72; EC p.184-186 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-50 | Meta-labelling of an existing primary signal: rule-based features, purged time blocks, trade / skip | filter | strategies 1-6 | – | LP 3.6-3.8, 8, 9.4 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-51 | EWMAC multi-speed (16:64, 32:128, 64:256) with swap as the carry forecast | signal | all; D1 | yes (carry) | RC ch.7-8, App.B; EC ch.6 | killed 2026-11-12 (D3 screen, ledger I51) |
| I-52 | Cost-limit screen: turnover x standardised cost <= 1/3 of the plausible pre-cost Sharpe | filter | all | – | RC ch.12 | done in effect 2026-11-14 (cost wall §3-4, power budget map, pass map) |
| I-53 | CPPI sub-account and Kelly per strategy for the FTMO limit | risk | R lists | – | EC ch.8 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-54 | Cool-down after a win / loss (re-entry timing) on a breakout entry | entry mgmt | any | – | KD p.24-28 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-55 | CUSUM event triggers (volatility-scaled filter rule), continuation or fade | signal | all; 5m-1h | none | LP 2.5.2.1 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: H1 shock family) |
| I-56 | Structural-break (CUSUM, SADF) and entropy regime flags | filter | all; H1-D1 | – | LP 17, 18 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-57 | Probability-to-size mapping and concurrency sizing | risk | R lists | – | LP 10, 4.3 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-58 | Half-life z-score mean reversion (linear or Bollinger), gated by T-11 | signal | all; M15-H4 | none intraday | EC p.48-50, 70-72 | closed 2026-11-14 (Fable row 24 triage: stop list, cost-wall §4: no stationarity (T-11)) |
| I-59 | FX cointegration pair (AUDUSD vs CADUSD style) | signal | needs AUDUSD, USDCAD from histdata | rollover | EC p.108-112 | blocked (symbols not in the data) |
| I-60 | Sigma-band stops and targets scaled with sqrt(holding time) | exit mgmt | any entry | – | JK p.161, 91-95 | parked 2026-11-14 (Fable row 24 triage: management layer, cannot create an edge; only on a stream with a net edge) |
| I-61 | Momentum after a large hourly move: after an H1 bar beyond k robust sd, trade its direction for h bars (11.11: small moves revert, big ones continue) | momentum | FX, metals, indices / H1 | none if flat by the session end | 11.11 study | tested 2026-10-20 (ROADMAP 11.13): no robust edge; continuation carried by the top 1 % events; NAS100 H1 k4 h2 closest (+0.20 sd trimmed, t 1.7, decaying) |
| I-62 | No-wick retest: limit at the no-wick end of a trend candle (Bard FX video), many stops / targets / filters | signal | all; 5m-1h | none (16:55 exit) | user 2026-10-21 | **no edge** 2026-10-21 (ROADMAP 11.17): 0.4 % of 4,608 variants positive; gold H1 cluster failed out of sample (-0.02 R/trade) |
| I-63 | FX local-hours depreciation (Breedon & Ranaldo 2013): short EURUSD in European hours, long XXXUSD in US hours; extends I-17 | time of day | EURUSD, GBPUSD, AUDUSD, NZDUSD; session hold | none (exit 20:30 London) | PUBLISHED (sample to 2007, unreplicated); `knowledge/research/reports/2026-11-09_fx_gold_time_of_day.md` | tested 2026-11-09 (strategy 10 F1a / F1b): F1 not supported (joint rule); F1a EURUSD alone +0.042 R / trade net, p 0.008, but GBPUSD and F1b fail; lead for the user |
| I-64 | Index last-30-minute momentum (Baltussen et al. 2021): sign of previous close -> 15:30 return, hold to 16:00 | intraday momentum | US500, NAS100, US30 | none | PUBLISHED (60+ futures to 2020; one blog: flat 2022-26); `2026-11-09_index_intraday_momentum.md` | tested 2026-11-09 (strategy 10 F2): gross positive in 5 indices, net negative (cost > edge); no edge after costs |
| I-65 | FOMC-morning long (Lucca & Moench 2015 pre-FOMC drift, decayed after 2015) | event | US500, NAS100 | none | PUBLISHED, decayed; falsification only; `2026-11-09_macro_announcement_equity.md` | tested 2026-11-09 (strategy 10 F3): falsified, FOMC mornings -0.27 R / trade vs other days |
| I-66 | Turn-of-month open-to-close long (T-1..T+3), day-trade form of I-18 | calendar | US500, NAS100, US30 | none | ADAPTATION (published close-to-close only); `2026-11-09_calendar_effects.md` | tested 2026-11-09 (strategy 10 F4): no effect open to close |
| I-67 | Month-end rebalancing with a conditional sign: sign of T-3..T-1 given the sign of T-8..T-4 | calendar | US500 | earns / pays (multi-day) | Etula et al. 2020 "Dash for cash" (`2026-11-09_calendar_effects.md:23`); review D2 | killed 2026-11-12 (t 0.95 < 2; ledger I67); same family as F4 / F4M |
| I-68 | Oil carry from the futures curve: long when backwardated, flat or short in contango | carry | USOIL | modelled from the curve | Gorton & Rouwenhorst 2006; Koijen et al. 2018 (UNVERIFIED); review D4 | closed 2026-11-12 on power (ledger I68) |
| I-69 | Bitcoin CME futures expiration week: long BTCUSD in the week of the last-Friday expiry | event | BTCUSD | pays swap (crypto -30 %/yr) | harvest HV-T0014-1 (econstor jrfm-15-00092, quote verified) | killed 2026-11-12 (net -100 bp / week, t -0.72; ledger I69) |
| I-70 | Option-expiration week on US500: long from the Friday close before to the expiry Friday close | event | US500 | pays swap (multi-night) | Stivers & Sun (via Quantpedia, harvest HV-T0015-1; HV-T0018-2) | killed 2026-11-12 (net -3.8 bp / week; ledger I70) |
| T-20 | Resting limit entries for clock-based holds (cost side, no new edge) | tooling | cheap FX / indices | – | review D5 | open, UNTESTED |

Not carried forward from the 2026-11-09 literature pass (dead or no evidence): pre-holiday,
day-of-week, generic macro-day long, pre-ECB drift, gold session pattern, overnight drift. The 18
M15 candidates: cost-infeasible or duplicates of failed families
(`knowledge/research/reports/2026-11-09_m15_candidate_triage.md`); only INTRADAY_H1_SHOCK_RESPONSE
passes the cost screen (low prior, I-61 re-study).

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
Review 2026-11-11 (D3; screened 2026-11-12: KILLED, net Sharpe -1.03, gross -0.13, ledger I51): judge it as **one** volatility-scaled portfolio over all cached D1
symbols (12-month sign, monthly rebalance, spread and swap charged), not symbol by symbol as strategy 4
was. Kills it: net portfolio Sharpe < 0.4 on development; more than half the profit from 3 symbols; the
result needs positive swap credits (off by default since 2026-11-11, review B5). Same family as strategy 4.

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

### I-67 Month-end rebalancing with a conditional sign (review D2, 2026-11-11; screened 2026-11-12: KILLED on t < 2, ledger I67)
Funds with fixed weights sell equities after a strong month and buy after a weak one, so the sign of the
last days is known before the trade. F4 (open to close) and F4M (unconditional close to close) were
falsified; the conditional sign was not tested. Cheap test (pandas, development D1 closes, US500 only):
signed T-3..T-1 return given the sign of T-8..T-4. Kills it: signed mean < 15 bp, t < 2, or opposite
signs in the two halves (declare the 2017 T+2 settlement shift first). Counts in the F4 family.

### I-68 Oil carry from the futures curve (review D4, 2026-11-11; parked, needs data)
Theory of storage: backwardation (scarce inventory) has paid longs, contango the opposite. Needs daily
front and second-month WTI settlements (EIA, free; download needs the user's go). Financing must come
from the curve, not today's swap. Kills it before any build: fewer than 10 regime changes in development,
or net <= 0 after a 3 % per year broker markup.
**Closed 2026-11-12 on power (no download, no edge look):** WTI monthly sd 12.5 % (USOIL 2010-2021); a halved
published single-commodity carry of ~0.7 % per month needs ~2,700 months for t 3, and all of EIA's 1986-2021 (420
months) gives an expected t of ~1.2. Monthly trades (12 a year) cannot reach the FTMO goal either. A forward demo
cannot settle it in any useful time. Revisit only inside a diversified commodity-carry portfolio with futures data.

### I-69 Bitcoin CME futures expiration week (harvest batch 3, 2026-11-12; screened the same day: KILLED, ledger I69)
Source (quote verified by `harvest check`): econstor `jrfm-15-00092` (J. Risk Financial Manag. 15, 2022):
of the calendar anomalies tested on bitcoin, only the week of a futures expiration showed abnormal
returns, positive in 65 % of cases and on average about 5x a usual week (2018-2021, costs ignored).
Mechanism (weak, SPECULATIVE): hedging / basis unwinds of CME futures before the last-Friday expiry.
Rule fixed before any data (2026-11-12): long BTCUSD from Monday 00:00 UTC to Friday 15:00 UTC (CME
expiry 16:00 London) in each week whose Friday is the month's last Friday; CME expiries 2018-01 to
2021-08 (development only). Net = gross minus cost table round trip minus swap (4 nights).
Kills it: net mean per week <= 0; t of the net < 3.0 (new family `crypto_event`, threshold rule);
opposite signs in the two halves (by count). Caveat: the paper's sample IS our development period, so a
pass only replicates it; independent evidence would come only from the one-time test.
Diagnostic (not a gate): the same Monday-Friday window in all other weeks.

### I-70 Option-expiration week on US500 (harvest batch 4, 2026-11-12; screened the same day: KILLED, ledger I70)
Sources (quotes verified by `harvest check`): Quantpedia "Option Expiration Week Effect" (Stivers & Sun,
J. Financial Markets, US large caps, sample ending well before 2010) and therobusttrader.com (practitioner
replication). Claim: index returns are higher in the week ending on the monthly option expiration Friday.
Mechanism (PUBLISHED, partly): dealer hedging and the unwind of option-linked short positions into expiry.
Rule fixed before any data (2026-11-12): long US500 from the cash close (last M1 close <= 16:00 New York)
of the Friday before the third Friday of each month to the cash close of that third Friday (Thursday if
the Friday is a holiday: the last cash close of that week); pre-sample 2010-2014 (histdata_presample)
pooled with development 2015-01 to 2021-08 (out of the paper's sample). Net = gross minus cost table round
trip minus swap for the nights held.
Kills it: net mean per week <= 0; t of the net < 3.0 (new family `opex_week`, threshold rule); opposite
signs in the two halves (pre-sample vs development). Diagnostic (not a gate): all other Friday-to-Friday weeks.

### I-71 Index-review closing-auction short on UK100 (harvest batch 6, 2026-11-13; rule fixed before any data; screened the same day: KILLED, ledger I71)
Source (quote verified by `harvest check`; read by Opus via a fetch the same day): KruegerAlgorithms,
"index rebalancing closing auction" (practitioner, Konstanz; **sells a tool**, "ForcedFlow" on MQL5). Claim:
on the closing-auction day before FTSE 100 / STOXX / MSCI review effective dates, the FTSE 100 falls into the
auction print; reported net (1.5 points round trip) +8.3 bp, n 63, t 2.3 (2015-2022 search) and +11.5 bp, n 27,
t 3.9 (holdout 2023-06/2026); placebo days +0.05 bp. Exact entry minute and stop not published.
Mechanism (PRACTITIONER, plausible forced flow): index funds trade composition changes in the closing auction.
Label: PRACTITIONER / seller source. Expected gross after halving the published effect: ~5 bp per event
against ~2 bp round-trip cost on UK100.
Rule fixed before any data (2026-11-13): short UK100 at the close of the 15:29 London M1 bar (15:30), cover
at the close of the 16:35 bar (after the 16:30-16:35 auction); event days = third Friday of Mar / Jun / Sep /
Dec (FTSE 100 and STOXX quarterly reviews) and the last weekday of Feb / May / Aug / Nov (MSCI reviews;
ASSUMPTION: the press-release dates are not fetched; a day without UK100 bars in the window is skipped).
Data: pre-sample 2010-2014 (`histdata_presample`, outside the source's search period) pooled with
development 2015-01 to 2021-09-13. Net = gross bp minus the cost model's round trip (spread at the entry
via `fill_spread_time` + 2 x slippage, no commission, no swap) in bp of the entry price.
Kills it: net mean <= 0; t of the net < 3.0 (new family `index_review_auction`, threshold rule); opposite
signs in pre-sample vs development. Diagnostic (not a gate): the same window on all other weekdays.
**Result (`research/screens/2026-11-13_i71_review_auction_screen.py`): KILLED on t < 3.0.** 83 event days (10
without both bars): gross +11.7 bp, net +9.0 bp, t 2.16, 67 % positive; pre-sample +12.5 bp (n 34), development
+6.5 bp (n 49); third Fridays +6.7, MSCI month ends +11.4; other weekdays gross +0.0 bp (n 2,630). 2020 -21.9,
2021 -9.9. The sign replicates out of the source's sample, but at ~8 events a year t 3 needs ~160 events
(per-event sd ~38 bp), more than our data holds; and at a 0.5 daily-ATR stop +9 bp is ~0.2 R x 8 a year.

### I-72 Funding-settlement drift on Binance perpetuals (Continue.Research on Binance futures, 2026-11-13; rule fixed before any data; screened the same day: KILLED, ledger I72)
Source: `knowledge/research/reports/2026-11-09_crypto_intraday.md` §2 (no published signed effect; S4 documents
volatility / volume spikes at 00 / 08 / 16 UTC and ties them to funding as a conjecture). Label: ORIGINAL / SPECULATIVE.
Mechanism (a counterparty with a reason to trade at a clock time): when funding is above the 0.01 % default, longs
who would pay it close before the settlement and reopen after (shorts do the opposite when it is negative), so
price leans against the paying side into the settlement and reverts after it.
Venue (AGENTS.md › Venues): Binance USD-M futures prices (`data/cache/binance`, last-trade M1), futures costs:
taker 0.05 % per side = 10 bp round trip (`engine/costs.py`, Binance's published regular-user rate, checked
2026-11-13), no spread or slippage in the model; no funding is paid because no position spans a settlement.
Signal (known in real time): the rate settled at t - 8 h (`binance_funding`; ASSUMPTION: the rate settled at t
is not used, it is fixed only at t). s = +1 if that rate > 0.0001 (longs pay more than the default), s = -1 if
< 0 (shorts pay), event skipped if 0 <= rate <= 0.0001. Settlements t = 00 / 08 / 16 UTC, BTCUSDT and ETHUSDT pooled.
Cells (2, family `funding_settlement`): PRE: position -s from the close of the M1 bar ending t - 60 min to the
close of the bar ending t - 1 min. POST: position +s from the close of the bar ending t + 1 min to the close
of the bar ending t + 60 min. A missing bar skips the event. Data: development 2020-01-01 .. 2021-09-13 only.
Power: hourly sd ~80-100 bp, ~1,000 effective events per cell -> standard error ~3 bp, so a gross effect of
10 bp (the cost) gives t ~3.
Kills it (each cell): net mean <= 0 at 10 bp; t of the net < 3.0; BTC vs ETH opposite gross signs; 2020 vs
2021 opposite gross signs. Diagnostic (not a gate): the same windows around 04 / 12 / 20 UTC (no settlement)
with the same signal; net at 12 bp.
**Result (`research/screens/2026-11-13_i72_funding_settlement_screen.py`): KILLED on net <= 0 in both cells.**
1,758 symbol-events (83 % with s = +1, i.e. funding above the default). PRE: gross -0.3 bp, net -10.3, t -3.1
(BTC +0.8 / ETH -1.2; 2020 +3.0 / 2021 -3.4). POST: gross +2.3 bp, net -7.7, t -1.7 (BTC -0.4 / ETH +4.9).
Per-event sd ~120 bp. No-settlement hours 04 / 12 / 20 UTC: PRE +4.4, POST -1.4 bp, so nothing specific to the
settlement. The few negative-funding events (s = -1) show +3 / +13 bp, too few to matter. Family closed.

### I-73 Cross-sectional funding carry on 17 Binance perpetuals (2026-11-13; rule fixed before the new data was read; screened the same day: KILLED on t; one-time test 2026-11-14: PASSED; replication on 20 unseen perps: FAILED, ledger I73 / I73R)
Source (opened by Opus, full text via pdftotext): Schmeling, Schrimpf & Todorov, "Crypto carry", BIS WP 1087
(2023, rev. 2025). Dated-futures basis on BTC / ETH, March 2019 - January 2022 (Deribit, OKEx, CME, ...): carry
averages above 10 % a year, up to 60 %; it is driven by convenience yields from trend-chasing small investors
using leverage and scarce arbitrage capital; "a positive carry predicts both a decline in the spot as well as in
the futures price" (Fig. 3: Deribit, same period, 1-month: a 1 % higher basis predicts a 6 % lower spot by
expiry, Newey-West); high carry predicts sell liquidations and more negative skew (crashes). No cross-section
across coins, no perpetual funding, no net-of-cost trade. Label: ADAPTATION (cross-section, funding as the
carry measure); the paper's sample overlaps our development period, so a pass only replicates it in-sample.
Mechanism: perps whose longs pay the most funding are the most crowded leveraged longs; a short collects the
funding and is on the side the paper says the price moves; a long in the lowest-funding perps pays least.
Venue: Binance USD-M prices (`binance`, last-trade M1) and costs: 10 bp round trip per leg per rebalance (taker),
funding of every settlement held from `binance_funding` (shorts receive a positive rate), no swap.
Universe: BTC, ETH + the 15 perps downloaded 2026-11-13 (BCH, XRP, EOS, LTC, TRX, ETC, LINK, XLM, ADA, BNB, XTZ,
XMR, NEO, DASH, ATOM); a symbol is eligible once it has 30 days of funding history.
Rule: every Monday at 00:00 UTC rank the eligible symbols by the mean of their last 21 settled funding rates
(7 days, the 00:00 print included: known at the settlement). Short the top 4, long the bottom 4, equal
notional; enter at the close of the M1 bar ending 00:01, exit at the close of the bar ending Sunday 23:59
(before the next Monday settlement); full rebalance every week (ASSUMPTION: no turnover saving, conservative).
Weekly return per 1 unit on each side = mean long return - mean short return + funding received - funding paid
- 20 bp. A symbol missing either bar is dropped from that week's leg (the leg keeps its other members).
Data: development only, first Monday with >= 8 eligible symbols up to the last full week before 2021-09-14.
One cell, family `crypto_carry_xs`.
Power line (before the screen, signal-free): weekly sd of a randomly picked 4-vs-4 portfolio, computed from the
new data before the ranked portfolio is formed; recorded here.
**Power (2026-11-13, before the screen):** 82 weeks, 9-17 symbols a week; random 4-vs-4 weekly sd 909 bp ->
standard error 100 bp; t 3 needs a net mean of ~300 bp a week (~150 % a year). Underpowered for any plausible
carry (the paper: 10 % a year on average); the screen runs as registered and counts as one look.
**Result (`research/screens/2026-11-13_i73_crypto_carry_xs_screen.py`): KILLED on t < 3.0 (t +1.30).** 82 weeks
(2020-02-17 .. 2021-09-06): net +138 bp a week (price part +106, funding +52; cost 20), 56 % positive weeks, sd 960;
halves +2 / +274; without the 2 best weeks +61; net at 30 bp +128; without BTC / ETH +231; worst week -2,626 bp.
2020 -26 bp (46 weeks), 2021 +347 bp (36 weeks). Every other kill passes and the price part has the paper's sign,
but the effect sits in the 2021 alt boom and the design could not reach t 3 below ~300 bp a week. No rescue variant;
whether to spend test data on a pre-registered combined estimate is the user's decision (HANDOFF › Open).
**One-time test, pre-registered 2026-11-14 before any test-period data was read (the user: "Yes, run I-73 test"):**
frozen rule as above, one assumption: the signal is the funding accrued in the 7 days before the Monday print
(rates settled in (Monday - 7 d, Monday]); for 8 h symbols this ranks exactly like the mean of 21 rates (every
symbol is 8 h in development; the re-run must reproduce +138.0 bp, t 1.30), and it keeps "7 days" for XTZUSDT,
which settles every 4 h / 1 h from 2025-07-20. Test weeks: Monday >= 2021-09-20 to the last Sunday exit <=
2026-10-25 (funding data ends 2026-10-31). Passes only if all hold: (1) test net mean > 0; (2) test t >= 2.0;
(3) development + test pooled t >= 3.0; (4) both test halves (by weeks) > 0; (5) test net > 0 without its 2 best
weeks. Diagnostics: price / funding parts, years, without BTC / ETH, net at 30 bp, worst week, longest losing
run. Exactly once; no retest, no variant after it.
**Test result 2026-11-14 (`--test`, script frozen in fc59ab7; development re-run identical): PASSED all five gates.**
266 weeks (2021-09-20 .. 2026-10-19): net +112.0 bp a week (price +102.8, funding +29.3, cost 20), t 2.93, 55 %
positive weeks, sd 624, PF 1.72; halves +105 / +119; without the 2 best weeks +95; net at doubled costs +92;
without BTC / ETH +102; pooled development + test t 3.08 (348 weeks); worst week -3,159 bp, max drawdown -3,967 bp
(1 unit each side), longest losing run 7 weeks; annual Sharpe ~1.3. Years: 2021 +139, 2022 +144, 2023 -18,
2024 +167, 2025 +199, 2026 +46. Most shorted: EOS, DASH, XMR, NEO, LINK, XTZ.
Data check (diagnostic, after the gates): 77 weeks dropped a leg member for missing bars, 73 of them EOS (prices
end 2025-05-21, its funding file continues as a constant 0.01 % placeholder). Ranking only symbols with an entry
bar (known at entry): net +110.2, t 2.98, halves +102 / +119: the pass does not depend on it.
Skeptic notes: the development gate failed (t 1.30) and the test was spent by the user's decision; two looks at one
cell. Last-trade prices, taker fees only, no slippage (doubled costs still +92). Not stop-defined: no R yet, and
the worst week (-32 % on each unit) is the crash risk the paper predicts. Venue: Binance only (not FTMO).
Spec (2026-11-14, the user's go): `docs/strategy-crypto_carry.md` (Strategy 19; not built).
**Replication on unseen coins (I-73R), pre-registered 2026-11-14 before the data was downloaded (the user: "Yes,
replicate I-73"):** universe R20 = the first 20 Binance USDT perps by listing month that are not in the original 17
(archive listing of 2026-11-14, perps trading in 2021-06; index contracts DEFIUSDT / BTCDOMUSDT excluded; ties in a
month alphabetical): BAT, IOST, IOTA, ONT, QTUM, VET, ZEC, THETA, ALGO, COMP, KNC, ZIL, ZRX, BAND, DOGE, KAVA, OMG,
RLC, SXP, DOT (all USDT). Frozen rule unchanged (`CryptoCarryConfig(symbols=R20)`, universe order = that list),
same eligibility, weeks 2021-09-20 .. 2026-10-25 (no development screen of these coins). Passes only if all hold:
net mean > 0; t >= 2.0; both halves (by weeks) > 0; net > 0 without the 2 best weeks. Power line (random 4-vs-4
weekly sd) recorded after the download and before the run. Diagnostics: the 37-symbol union, price / funding
parts, years. Exactly once, no variants. Caveat: perps delisted before 2021-06 are not in the listing probe.
**I-73R power (2026-11-14, before the run, signal-free):** 266 weeks, 20 symbols; random 4-vs-4 weekly sd 690 bp
(weeks where a random leg holds only delisted coins left out: OMG ends 2025-06, SXP 2025-12), standard error 42 bp;
t 2 needs 85 bp a week; at the original test effect (+112) the expected t is ~2.6 (pass chance ~70 % if real).
Data repair before the run: SXP 2023-04-05..30 (52 files, price + flow) had broken parquet footers after the
session's hard restart (no fsync in `write_atomic`); deleted, re-downloaded, full cache scan clean.
**I-73R result (2026-11-14, `research/screens/2026-11-14_i73r_replication.py`): FAILED (t, halves).** 266 weeks:
net +63.4 bp a week (price +35.0, funding +48.5), t 1.05, 53 % positive weeks, sd 987, worst week -4,917 bp; halves
-18.9 / +145.7; without the 2 best weeks +14.8. Years 2021 +18, 2022 +30, 2023 -112, 2024 +154, 2025 +27, 2026 +269.
37-symbol union (diagnostic): +59.6, t 1.11. Reading: the funding carry is collected on unseen coins too, but the
price part (the paper's prediction) is about a third of the original 17's (+35 vs +103): the original pass did not
replicate on new coins. Per the stop rules this independent check counts against the strategy; what to do with
Strategy 19 is the user's decision (HANDOFF › Open).
Kills it: net weekly mean <= 0; t of the net < 3.0; first vs second half (by weeks) opposite signs; net mean
<= 0 after removing the 2 best weeks; price part (without funding) below -20 bp a week (a carry that pays
only by running into the paper's crashes). Diagnostics (not gates): price and funding parts separately; BTC /
ETH excluded; worst week; net at 30 bp a week.

### I-74 Hedger position-change reversal in commodity futures (harvest batch 11, 2026-11-14; not screened: below cost, data missing)
Source (opened by Opus, full text via pdftotext): Kang, Rouwenhorst & Tang, "A tale of two premiums" (NBER
commodities conference 2013), CFTC COT positions, 26 US commodity futures, 1994-01 to 2012-06. Ranking each Tuesday
by the prior week's change in hedgers' net long position, top minus bottom half earns "0.431% (t-statistic = 4.16)"
over the next 20 days (quintiles 0.667 %); about half accrues in days 1-4, before the report is public on Friday.
Mechanism (PUBLISHED, forced counterparty): hedgers demand immediacy, speculators are paid for absorbing it.
Verdict before any data: the tradeable part (after the Friday release) is ~21 bp per 20 days, ~11 bp after halving
for decay, per unit long-short; our venue has 5 commodity CFDs (XAU, XAG, USOIL, UKOIL, NATGAS), not 26 futures,
and 20-day CFD holds pay swap on both legs plus two spreads; the venue method asks for futures prices (no paid
futures data, the user 2026-11-13) and it needs CFTC COT data (free, a new download). Far below cost: card only,
not screened. Ledger HV-T0072-1.

### I-75 Weekly cross-sectional reversal on 37 Binance perpetuals (harvest batch 13, 2026-11-14; rule fixed before any data; screened the same day: KILLED, ledger I75)
Source (abstract only; the PDF answers 403 to the script and web-fetch): Kozlowski, Puleo & Zhou, "Cryptocurrency
return reversals", Applied Economics Letters 28(11), 2021: 200 coins 2015-2019, weekly loser-minus-winner 8.69 %
(t 9.60), present in both halves, "most pronounced among smaller capitalization and less liquid" coins. Label:
PUBLISHED (abstract) / ADAPTATION (large, liquid perps). Mechanism: liquidity provision, paid for absorbing last
week's one-sided flow. Expected: far below the paper on our large coins; halved claim ~4 %/week as the upper end.
Overlap: I-73's price part (high funding ~ recent winners); the weekly correlation is reported.
Venue and costs as Strategy 19: Binance USD-M last-trade M1, 20 bp a week per unit each side, funding of every
settlement held (shorts receive a positive rate).
Universe: the 37 cached perps (I-73's 17 + I-73R's 20), universe order = I-73's list then R20's. Eligible on a
Monday: 30 days of funding history and both signal prices present.
Rule: every Monday, signal = return from the close of the M1 bar opening at the previous Monday 00:00 to the close
of the bar opening this Monday 00:00 (the entry price itself, known at entry). Sort ascending (stable, universe
order); n = floor(eligible / 5) per leg; long the n lowest (losers), short the n highest (winners), equal weight;
no week below 10 eligible. Entry at the close of the bar opening Monday 00:00, exit at the close of the bar opening
Sunday 23:58; a member without its exit bar is dropped from its leg. Weekly net = mean long - mean short return +
funding received - paid - 20 bp.
Data: development only, 2020-02 to the last week with its Sunday exit before 2021-09-14. One cell, new family
`crypto_xs_reversal` (threshold t 3.0).
Power line (signal-free): weekly sd of random legs of the same sizes, recorded before the screen.
Kills it: net mean <= 0; t of the net < 3.0; halves (by weeks) opposite signs; net <= 0 without the 2 best weeks.
Diagnostics: price / funding parts; the 17-symbol universe alone; correlation with I-73's development weeks;
members per leg.
**Power (2026-11-14, before the screen, signal-free):** 81 weeks, 11-37 eligible; random-leg weekly sd 869 bp ->
standard error 97 bp; t 3 needs ~290 bp a week (the paper's 869 bp is small-coin driven).
**Result (`research/screens/2026-11-14_i75_crypto_reversal_screen.py`): KILLED (net <= 0).** 81 weeks, 2-7 per leg:
net -146.8 bp a week (price -116.4, funding -10.4), t -1.05, 47 % positive, sd 1,258, worst -3,745; halves -177 /
-117 (same sign); without the 2 best weeks -241. 2020 -263, 2021 -1. 17-symbol universe -67.7 (t -0.54);
correlation with I-73's development weeks +0.25. On large, liquid perps last week's losers kept losing: the
paper's small-coin reversal is absent (the sign is momentum, not tested as a rule). Family `crypto_xs_reversal`
closed after one falsification would be early, but no rescue variant: a momentum rule would be a new hypothesis.

### I-76 Liquidation-cascade reversal on 37 Binance perpetuals (Fable directions row 10, 2026-11-14; rule fixed before any data)
Source: Fable 5.2 advisory list `knowledge/reviews/2026-11-14-fable-research-directions.md` row 10 (prior 15 %, no
published bp known). Label: SPECULATIVE / ORIGINAL. Related lead, not read: Bank of Canada 2026 DeFi liquidation
recovery (harvest HV-T0089-1, on-chain, untestable). Mechanism (a counterparty that must trade): exchanges close
under-margined positions at market; a burst of one-sided aggressive flow pushes the price past fair value and
liquidity providers are paid for absorbing it. Bearish cascade described (long after it), short squeeze mirrored.
Not covered: S11 / I-61 were CFD H1 bars with no flow condition; C3 / L18 were BTC-ETH momentum and lead-lag.
Venue and costs: Binance USD-M last-trade M1 (`data/cache/binance`, flow from `binance_flow`), taker 5 bp a side =
10 bp a round trip; funding of any settlement inside the hold (a long pays a positive rate). Goal 2 only unless
FTMO's BTCUSD / ETHUSD (about 13 bp, L18) also clears it.
Universe: the 37 cached perps, development only, 2020-01-01 to 2021-09-13 (exit before 2021-09-14).
Rule (one cell, fixed): per symbol, at the close of each M1 bar t: r5 = log(close_t / close_{t-5});
sd5 = sd of the M1 log returns of the 1,440 bars before the window (bars t-1444..t-5, at least 1,000 present) x
sqrt(5); v5 = volume of bars t-4..t; vmed = median M1 volume of the same 1,440 bars; sell share = sell_volume /
volume over bars t-4..t. **Bearish event:** r5 <= -4 sd5, sell share >= 0.65, v5 >= 25 x vmed (5 x the median
5-min volume). **Bullish event:** r5 >= +4 sd5, buy share >= 0.65, same volume rule. Enter at the close of bar
t+1 (one bar later), long after a bearish event, short after a bullish one; exit at the close of bar t+61. A
symbol takes no new event until its exit. A trade without its entry or exit bar is dropped.
Clustering: events of all symbols whose entry lies within 60 minutes of a cluster's first entry form one cluster;
a cluster's value = mean net of its trades. Statistics on clusters. New family `crypto_liquidation_reversal`
(threshold t 3.0).
Power line (signal-free, recorded before the screen): number of event clusters, and the sd of the 60-minute
forward return after the move-only control events (direction-free, sd only).
Kills it: cluster net mean <= 0 at 10 bp; t < 3.0; either calendar half (2020, 2021) net <= 0; net <= 0 at 20 bp
(doubled costs); net <= 0 without the 2 best clusters.
Diagnostics (no rescue): control = the same move rule without the flow and volume conditions; BTC + ETH alone;
long vs short side; holds of 15 / 30 minutes; trades per symbol.
**Power (2026-11-14, before the screen, signal-free):** 21,654 event trades in 5,132 clusters on all 37 perps
(far more than Fable's guess of ~300: 4 sd of the trailing day is common in crypto); 38,777 control trades, 60-min
return sd after move-only events 253 bp -> standard error ~3.5 bp per cluster; t 3 needs ~11 bp net (well powered).
**Result (`research/screens/2026-11-14_i76_liquidation_reversal_screen.py`): KILLED (t 2.50 < 3.0; net <= 0 at
20 bp).** 21,654 trades, 5,132 clusters: net +5.3 bp per cluster (gross price +7.0, funding -0.2), 56 % positive;
2020 +0.0 / 2021 +14.8; at 20 bp -4.7; without the 2 best +4.8. Control (move only, no flow condition): -1.9 bp
(t -1.0), so the flow condition adds ~7 bp. Long after bearish +14.4 bp gross per trade, short after bullish -6.9
(the 2020-21 bull drift is in both); BTC + ETH -14.7 bp (t -3.19): the effect, if any, sits in the alts. Holds
15 min -1.8, 30 min +2.5 (t 1.5). Family `crypto_liquidation_reversal`: one falsification. No rescue: a long-only
or alt-only rule would be a new, post-hoc hypothesis; with maker fees (~4 bp, Fable row 11, unmodelled) the
primary would be ~+11 bp, so the cost model is the binding question, not the signal.

### I-77 Earnings-announcement premium on FTMO share CFDs (venue facts, 2026-11-14; not screened: below cost)
Idea: pool the ~59 FTMO share CFDs (MSFT M1 history from 2010, NVDA only from 2020-11) and hold over scheduled
earnings announcements (~240 events a year, the frequency the pass map needs). Sources opened by a Sonnet web
subagent (2026-11-14; Opus did not re-open them): Frazzini & Lamont, NBER WP 13090 (2007), CRSP 1972-2004: ~60 bp
per announcement month, of which ~21 bp in the 3 days around it and ~25 bp before; Savor & Wilson (JF 2016, 2011
draft), 1974-2009: value-weighted 23 bp a week (t 5.67); Barber, De George, Lehavy & Trueman (JFE 2013): largest
firms ~41 bp a month vs 114 for the smallest. Not opened (403): Heitz, Narayanamoorthy & Zekhnini 2020 "The
Disappearing Earnings Announcement Premium" (snippet: disappeared from US markets in recent years).
Label: PUBLISHED, likely decayed. Size: 3-day window ~21 bp (to 2004) -> ~10 bp halved, and the post-2010 evidence
points to ~0; cost per event ~8-10 bp (share CFD spread plus two nights of swap, MSFT ~2.5-3 bp a night long).
Verdict: not screened (expected net <= 0; the US premium is reported gone). Reopen only if the 2020 paper's
numbers show a large-cap premium after 2010 above ~20 bp per event.

### I-78 / I-79 / I-80 Crypto wide factor set: taker-flow imbalance, MAX, volume shock (Fable rows 9 and 21, 2026-11-14; rules fixed before any data; I-78 one-time test PASSED, I-79 / I-80 KILLED)
First families on the crypto split (rule set by the user 2026-11-14: develop 2020-01-01 .. 2023-12-31, test once from
2024-01-01; `docs/research-runner.md` › Periods). Universe: every Binance USDT-margined perpetual, delisted ones
included (`research/screens/2026-11-14_binance_wide_download.py`, daily klines with taker buy volume, funding).
Sources and labels: I-78 taker-flow imbalance, Fable row 9 (ORIGINAL; related: V1 ROADMAP 11.16 found BTC / ETH
intraday flow effects of 2-5 bp, below fees); I-79 MAX, Bali, Cakici & Whitelaw 2011 "Maxing out" (equities,
UNVERIFIED, not opened; crypto evidence unknown: sign not assumed); I-80 volume shock (no source known, attention
buying; SPECULATIVE). Mechanism: I-78 one-sided aggressive flow (liquidations, worked orders) leaves either
continuation or exhaustion; I-79 lottery demand overprices coins with extreme up-days; I-80 attention buying
overprices coins after volume spikes. None is a forced counterparty: low priors (Fable 10 % each).
Common rule (one cell per factor): every Monday 00:00 UTC, eligible = perps with >= 60 daily bars before the
Monday and a median daily quote volume >= 5 million USDT over the last 30 days; a week needs >= 20 eligible. Signal
from the 7 daily bars before the Monday: I-78 = (taker buy - taker sell) / volume summed over the 7 days; I-79 =
the largest daily close-to-close return; I-80 = 7-day quote volume / (7 x mean daily quote volume of the 60 days
before those 7). Sort ascending (ties by symbol name); n = floor(eligible / 5) per leg; spread = mean return of the
top quintile - bottom quintile, equal weight, from the Monday open to the next Monday open (a member without that
bar exits at its last close in the week: no survivorship). Weekly net of the spread = price spread - funding of
the top leg + funding of the bottom leg - 20 bp (taker 5 bp a side, both legs, full turnover). The sign is not
assumed: the tested direction is the sign of the development mean.
Assumption (Opus): weekly rebalancing for all three (Fable row 9 said daily: at 20 bp a day the effect would need
> 20 bp a day; weekly keeps the cost at 20 bp a week and matches I-73 / I-75).
Kills per factor (two-sided, new family `crypto_xs_factors`, 3 hypotheses -> |t| >= 3.0): |t| of the weekly net
in its own direction < 3.0, or net in that direction <= 0; halves (2020-21, 2022-23) not both > 0 in that direction;
net <= 0 at 40 bp (doubled costs); net <= 0 without the 2 best weeks. Diagnostics: price / funding parts, members
per leg, correlation of each factor's weekly spread with a 1-week past-return sort (I-75's closed signal) and with
the other two factors.
Power line (signal-free, before the screen): eligible count per week and the weekly sd of random quintile legs.
**Power (2026-11-14, before the screen, signal-free):** 265 perps with development data, 186 weeks with >= 20
eligible (2020-05-25 .. 2023-12-25), eligible per week 20-205 (median 132, legs ~26); random-leg weekly sd 481 bp ->
standard error 35 bp; |t| 3 needs ~106 bp a week net (old split, I-75: ~290).
**Development result (`research/screens/2026-11-14_i78_crypto_wide_factors_screen.py`, 186 weeks):**
- **I-78 flow: PASSED all five development gates.** Long the top flow quintile (net taker buying), short the bottom:
  net +145.0 bp a week, t 3.24, price +141.6, funding part +23.4, 58 % positive, worst week -1,438; halves +326.8 /
  +1.7 (2022-23 barely positive); at 40 bp +125.0; without the 2 best +116.8. Correlation with a 1-week past-return
  sort 0.56: partly a short-term momentum proxy (momentum itself is HANDOFF Open 5, not tested).
- I-79 MAX: KILLED (net +34.3, t 0.70; halves +97.7 / -15.8). I-80 volume shock: KILLED (net +5.6, t 0.10; halves
  +51.2 / -30.3; -14.4 at 40 bp).
**I-78 one-time test, pre-registered 2026-11-14 before any test-period data was downloaded (Mode=auto, auto decision
9):** frozen rule exactly as above (flow, long top / short bottom quintile, weekly, 20 bp, same eligibility), test
universe = every USDT perp incl. those listed from 2024 and the delisted ones; test weeks: Monday >= 2024-01-01 to
the last Monday whose Sunday exit is <= the last downloaded day (months to 2026-10); signals may use development
bars before 2024. The development re-run must reproduce +145.0 bp, t 3.24. Power: ~147 test weeks, se ~40 bp: t 2
needs ~80 bp (the development effect would give t ~3.6, half of it t ~1.8). Passes only if all hold: (1) test net
mean > 0; (2) test t >= 2.0; (3) development + test pooled t >= 3.0; (4) both test halves (by weeks) > 0; (5) test
net > 0 without its 2 best weeks; (6) test net > 0 at 40 bp. No momentum or other sort is computed on test data
(Open 5 stays unspent). Pass or fail is recorded; no retest.
**One-time test result (2026-11-14, `--test`, commits 2941156 / d1f79cd; dev re-run identical): PASSED all six
gates.** 147 weeks 2024-01-01 .. 2026-10-19, eligible median 240, legs 34-63: net +147.2 bp a week, t 3.76, 59 %
positive, PF 2.30, worst week -868, max drawdown -1,455 bp; halves +119.9 / +174.2; development + test pooled t
4.81; without the 2 best +126.8; at 40 bp +127.2. Price legs: long +35.3, short -91.6 bp a week.
**Diagnostics after the test (no effect on the verdict): tail-driven.** The long leg catches weekly pumps (ALPACA
+570 % in its delisting week, PIPPIN +444 %, 1000FLOKI +299 %, ...). Member returns clipped at +-50 % a week: test
+77.6 (t 2.38), development +96.5 (t 2.64); clipped at +-30 %: test +56.3 (t 1.90), development +57.8 (t 1.83). So
about half the edge is pump capture in small perps (position limits, slippage and delisting risk not modelled),
the rest ~+56 bp a week, the same in both periods. Not on FTMO: the effect sits in small alts, FTMO lists ~30
large coins at 10-40 bp. Goal 2 only; anything live touches money (the user's decision).

### I-81 New-listing drift on Binance USDT perps (Fable directions row 19, 2026-11-15; rule fixed before any data; KILLED)
Source: Fable 5.2 row 19 (no published source known; label ORIGINAL / SPECULATIVE; IPO long-run underperformance in
equities is the analogy, not checked). Mechanism: early holders, unlocks and market-maker allocations sell into the
first liquid derivatives venue while retail buys the listing; supply arrives over the first weeks. Not strictly
forced (Fable prior 15 %). Crypto split (development 2020-01-01 .. 2023-12-31; test from 2024-01-01).
Events: every USDT perp (no dated quarterlies) whose first daily bar in `data/cache/binance_wide` falls in
2020-03-01 .. 2023-11-30 (the 30-day hold ends inside development); listing day = the first daily bar.
Rule (one cell): short the perp at the close of listing day 2 (its second daily bar), cover at the close of day 30
(its 30th bar, or the last close if it stops trading earlier); hedge with a long BTCUSDT of equal notional over the
same two closes. Net per event = -(coin return) + BTC return + coin funding received (a short receives a positive
rate) - BTC funding paid, settlements strictly between the two closes, - 20 bp (4 taker fills of 5 bp).
Statistics: events clustered by the calendar month of entry; the t-stat is over monthly cluster means (equal-
weighted months). New family `crypto_listing` (1 hypothesis, threshold t 3.0); the sign is predicted (short).
Kills: net (mean of month means) <= 0; t < 3.0; halves (2020-21 entries, 2022-23 entries) not both > 0; net <= 0 at
40 bp; net <= 0 without the 2 best months. Diagnostics: event-level mean and median, coin vs BTC parts, funding part,
events per year, the share of events that stop trading inside the hold.
Power line (signal-free, before the screen): event and month counts, and the sd of 28-day BTC-hedged returns of
established perps (listed >= 180 days) at random dates, scaled to monthly cluster means.
**Power (2026-11-15, before the screen, signal-free):** 234 events in 41 months (2020: 57, 2021: 58, 2022: 27,
2023: 92); 28-day hedged sd 2,735 bp -> month-mean se ~179 bp; t 3 needs ~536 bp net per event (optimistic,
within-month correlation ignored). Weakly powered: only an effect at the top of Fable's "several hundred bp" guess
can pass. Auto decision 10: screen anyway (no published size to compare; one counted look in a new family).
**Result (`research/screens/2026-11-15_i81_listing_drift_screen.py`): KILLED (t 1.16 < 3.0).** 234 events, 41
months: net +611.5 bp per event (mean of month means), event mean +444.7, **median +1,947.8** (most new listings
fall against BTC), coin +287, BTC +824, funding -72 (shorts pay on average); halves +538 / +682; at 40 bp +592;
without the 2 best months +359. The sign is right and large, but the right tail (squeezes of the shorted coin) makes
it too noisy for our sample. No rescue: a capped or median rule would be post-hoc. Family `crypto_listing`: one
falsification.

### I-82 / I-83 / I-84 Wave 1 crypto breadth sorts: daily taker flow, absorption, spot-minus-perp flow (Fable backlog FB-001 / FB-003 / FB-004, 2026-11-15; rules fixed before any data)
Crypto split (development 2020-01-01 .. 2023-12-31; test once from 2024-01-01 for a passer, Mode=auto). Universe,
eligibility, costs, funding convention, quintile legs, tie rule and the two-sided direction rule exactly as I-78
(card above; `research/screens/2026-11-14_i78_crypto_wide_factors_screen.py`), family `crypto_xs_factors` (looks
4-6 of <= 10 -> |t| >= 3.0). Labels: ORIGINAL (Fable 2026-11-15); low priors (Fable 8-12 %).
- **I-82 daily taker flow (FB-001):** every day 00:00 UTC; eligible as I-78 with the day's bar instead of the Monday
  bar and yesterday's bar present; signal = (2 x taker buy - volume) / volume of yesterday's bar; entry at the day's
  open, exit at the day's close; funding of settlements strictly inside the day; 20 bp a day. New vs I-78: horizon
  (1 day, ~7x the observations; the sign may flip at this speed). Kills on the daily series: |t| < 3.0; net <= 0;
  halves (2020-21, 2022-23) not both > 0; net <= 0 at 40 bp; net <= 0 without the 2 best days.
- **I-83 absorption (FB-003):** weekly as I-78; each Monday regress the eligible symbols' 7-day flow on their 7-day
  close-to-close return (OLS across symbols, intercept); signal = the residual (buying the price did not follow).
  Kills as I-78.
- **I-84 spot-minus-perp flow (FB-004):** weekly as I-78; eligible additionally needs the 7 spot daily bars (Binance
  spot `<SYM>` klines, same symbol name); signal = spot 7-day flow - perp 7-day flow (flow as in I-78). Kills as I-78.
Diagnostics (no gate): signal deciles (dose-response), weekly correlation with Strategy 20 (I-78), a shuffled-date
placebo of the signal. Tool canary before any of these looks: the shared tool must reproduce I-78's development
numbers (+145.0 bp, t 3.24) to the digit.
Power lines (signal-free, before each screen): random-leg sd of the series at its horizon.
**Canary and power (2026-11-15, before the screens; tool frozen in 0ba5965):** the shared tool reproduces I-78 (186
weeks, +145.0, t 3.24). I-83 / I-84 weekly: random-leg sd 479 bp -> |t| 3 needs ~105 bp a week net; I-82 daily: 1,314
days, sd 170 bp -> |t| 3 needs ~14 bp a day net (vs 20 bp a day of cost). I-84 waits for the spot download.
**Development results (2026-11-15, `research/screens/2026-11-15_wave1_xs_crypto_screen.py i82 i83`):**
- **I-82 daily taker flow: KILLED** (net -4.2 bp a day, t -0.74; halves +17 / -21; deciles flat; weekly correlation
  with Strategy 20 +0.51). The flow edge does not exist at a 1-day hold after 20 bp a day.
- **I-83 absorption: PASSED all five development gates**: long the top residual quintile, net +145.4 bp a week, t 3.57,
  61 % positive, worst -1,271; halves +294.1 / +28.2; at 40 bp +125.4; without the 2 best +119.1; placebo mean t -0.84
  (0 of 20 |t| >= 3); deciles rising from 85 to 276 bp. **Weekly correlation with Strategy 20 +0.76**: mostly the same
  edge with the linear 7-day-return part removed.
- Tool note: the placebo was computed net of 20 bp, so it is negative by construction (I-82 daily: -20 bp / se gives
  t ~-4.2); from here on it is reported gross (expect ~0). Gates unaffected.
**I-83 one-time test, pre-registered 2026-11-15 before any test-period data was read by this rule (Mode=auto, auto
decision 12):** frozen rule as above (absorption residual, long top / short bottom quintile, weekly, 20 bp, I-78's
eligibility), test universe and weeks as I-78's test (Monday >= 2024-01-01 to the last Monday whose Sunday exit is <=
2026-10-31; signals may use development bars). Passes only if all hold: (1) test net > 0; (2) test t >= 2.0; (3)
development + test pooled t >= 3.0; (4) both test halves > 0; (5) test net > 0 without its 2 best weeks; (6) test
net > 0 at 40 bp. Note: the period was already used once by I-78 (same family, correlated signal); a pass adds
evidence mainly on whether the flow edge survives without its momentum part. Reported with its correlation to
Strategy 20 on the test weeks.
**I-83 one-time test result (2026-11-15, `--test-i83`, tool 6d8e072; dev re-run identical): PASSED all six gates.**
147 weeks: net +101.6 bp a week, t 2.85, 61 % positive, worst -965; halves +64.1 / +138.5; pooled t 4.56; without the
2 best +81.0; at 40 bp +81.6. Test-week correlation with Strategy 20 +0.83: the taker-flow edge survives with the
linear 7-day-return part removed, so Strategy 20 is not just short-term momentum. Not a second independent stream:
kept as evidence for Strategy 20, no separate build.
**I-84 power (2026-11-15, before its screen):** spot daily klines downloaded for 243 of the 265 perps (development
months); 186 weeks with >= 20 symbols with spot data; |t| 3 needs ~105 bp a week net (as I-83).
**I-84 result: KILLED (t 1.76 < 3.0).** Direction long the bottom (perp buying above spot buying): net +70.5 bp a
week, 51 % positive; halves +149.7 / +8.0; at 40 bp +50.5; placebo gross mean t +0.01; correlation with Strategy 20
+0.58 (the perp-flow part). The spot-flow difference adds nothing beyond perp flow.

### I-85 / I-86 Noise-band intraday momentum on US indices, unconditional and on negative-gamma days (Fable FB-199 / FB-201, Wave 2, 2026-11-15; rules fixed before any data)
Sources (UNVERIFIED, not opened): Zarattini, Aziz & Barbon 2024, "Beat the market: an effective intraday momentum
strategy for S&P500 ETF (SPY)" (noise area from the average absolute move by time of day); dealer-gamma conditioning:
Baltussen, Da, Lammers & Martens 2021 (hedging demand and intraday momentum), Squeezemetrics GEX. Label: PUBLISHED
(adaptation) / SPECULATIVE for the gamma split. Mechanism: when dealers are short gamma they hedge with the move, so
intraday moves beyond the normal noise continue; with long gamma they dampen it.
Family `orb` (second look after S06; threshold t 3.0; this is the last look of opening-momentum rules, Fable).
Data: CFD development period (before 2021-09-14), US500, NAS100, US30 M1 via `DEFAULT_SOURCES` (US30 from 2019-02);
GEX from `data/cache/squeezemetrics/DIX.csv` (daily, known after the close: day d uses the GEX of the previous date).
Rule (both cells): New York time. open = the 09:30 bar's open; prev close = the 15:59 bar's close of the previous
trading day; sigma(t) = mean over the previous 14 trading days of |close(t) / open - 1| at checkpoint t; upper =
max(open, prev close) x (1 + sigma(t)), lower = min(open, prev close) x (1 - sigma(t)). Checkpoints every 30 minutes
10:00 .. 15:30 (bar closes at those times). Flat: close above upper -> long at that close; below lower -> short. Long:
exit at a checkpoint whose close is back below upper (short mirrored), else at the 15:55 close. Re-entry allowed at
later checkpoints. Cost per round trip from the engine (spread at the entry time via `fill_spread_time` + 2 x
slippage), in bp of the entry price. No swap (intraday).
- I-85 (FB-199): every trading day.  - I-86 (FB-201): only days whose previous GEX < 0 (192 of 2,610 development
  days in the file).
Statistics: per date, the mean net bp over symbols traded that day (days without a trade count 0 for I-85 only on
eligible days); t over dates. Kills per cell: net <= 0; t < 3.0; halves (by date) not both > 0; net <= 0 at doubled
costs; net <= 0 without the 2 best days. Diagnostics: per symbol, trades per day, gross vs cost, the positive-GEX
days (FB-200 mirror: momentum should be weaker), long vs short.
Power line (signal-free, before the screen): sd of the 10:00 -> 15:55 return per symbol-day and the count of days.
**Power (2026-11-15, before the screen; script frozen aa48dde):** US500 1,621 days (sd 72 bp), NAS100 1,658 (88 bp),
US30 480 (78 bp) of 10:00 -> 15:55 return. I-85: ~1,650 days, se ~1.5-2 bp -> t 3 needs ~5 bp a day net; I-86: 192
negative-GEX days with higher volatility, se ~10 bp -> t 3 needs ~30 bp a day net (weak power).
**Result (`research/screens/2026-11-15_i85_noise_band_screen.py`): both KILLED.**
- I-85 all days: 1,712 days, 1,328 trades; net +0.31 bp a day, t 0.37; per trade gross +2.95, cost 1.70; halves
  +0.89 / -0.26; doubled costs -0.68. NAS100 net +2.9 a trade, US500 -0.1, US30 -3.9; longs +2.5, shorts -0.3.
- I-86 negative-GEX days: 144 days, 121 trades; net -10.8 bp a day, t -1.97: the **opposite** sign (shorts -55.7 bp a
  trade: sharp rebounds on short-gamma days). Positive-GEX days: +3.1 a trade (the FB-200 mirror is not supported
  either). No rescue. Family `orb`: second falsification (S06 not confirmed, I-85 killed): closed.

### I-87 Overnight index premium on CFDs (Fable FB-107 / FB-108, 2026-11-15; not screened: below cost by arithmetic)
Published idea: most of the equity premium accrues overnight (Cliff, Cooper & Gulen 2008; Lou, Polk & Skouras 2019;
UNVERIFIED). Size: a 7 %-a-year premium is ~2.8 bp a night. FTMO cost of one night long: swap ~2.4-2.9 bp (census
2026-11-15: US30 -2.46, US100 -2.43, UK100 -2.52, AUS200 -2.86 bp a night) + spread / slippage 1-2 bp -> ~3.5-5 bp.
Expected net <= 0 before any data; FB-108's "after a down day" variant would need > 5 bp a night on a third of the
nights. Not screened (counted as a card, not a look).

### I-88 SMT divergence at the session extreme, NAS100 vs US500 (Fable FB-079 / FB-080 / FB-078, Wave 2, 2026-11-15; rules fixed before any data)
Source: ICT "smart money technique" (SMT) divergence, practitioner (social media; `docs/confluences.md` › SMT stub);
Fable FB-079 (fade the leg that made the high) / FB-080 (follow the stronger leg). Label: PRACTITIONER / SPECULATIVE.
Mechanism claimed: when correlated indices disagree at an extreme, the new extreme in one is a liquidity grab (stops
taken) that the other market does not confirm, so the move fails. New family `smt` (threshold t 3.0).
Data: CFD development period (before 2021-09-14), NAS100 and US500 M1 via `DEFAULT_SOURCES`, New York time.
Rule (one cell, two-sided): for each symbol, session high so far = max of M1 highs from 09:30 up to the previous
15-minute checkpoint (same for lows). Checkpoints: bar closes at 10:00, 10:15, ..., 15:00. **Bearish event** at t:
leg A closes above its session high so far while leg B's highs in the last 15 minutes stay below B's session high
so far (B does not confirm). **Bullish** mirrored with lows. ICT direction: short A after a bearish event, long A after
a bullish one (A = the leg that made the new extreme), entry at A's close at t, exit at A's 15:55 close. At most one
event per day per direction (the first); both legs can be A on different days. Cost per round trip from the engine
(spread at entry via `fill_spread_time` + 2 x slippage), bp. The tested direction is the sign of the development mean
(two-sided: a significant opposite sign means continuation, FB-080).
Statistics: per date, the mean net of that day's trades; t over dates with a trade. Kills: |t| < 3.0 in its own
direction; net <= 0; halves (by date) not both > 0; net <= 0 at doubled costs; net <= 0 without the 2 best days.
Diagnostics: control = new session extremes where B does confirm (same entry and exit), trading the non-confirming
leg B instead, bearish vs bullish, the US triad version with US30 (2019-02 .. 2021-09) where A breaks and both others
fail, time of day.
Power line (signal-free, before the screen): event count and the sd of A's return from a checkpoint to 15:55.
**Power (2026-11-15, before the screen):** 1,542 events on 1,243 days; sd of A's checkpoint -> 15:55 return 65 bp -> se
~1.9 bp; t 3 needs ~5.6 bp net per day (cost ~1.7-2.1 bp a trade).
**Result (`research/screens/2026-11-15_i88_smt_screen.py`): KILLED.** 1,490 trades on 1,202 days: net -0.26 bp, t
-0.17 (gross +1.7 bp in the continuation direction vs cost 2.0); halves -0.8 / +0.3. Bearish and bullish events
alone, every time-of-day band, trading the non-confirming leg instead, and the US triad (2019-21) are all within
+-2 bp gross: SMT divergence carries no edge here in either direction. Diagnostic only (not a test, post-hoc): when
both legs make the new extreme together (confirmed breakout), continuation to the close gives +4.1 bp net, t 2.33,
both halves positive; that is intraday momentum (family `orb`, closed after I-85) and FB-059 (four-index agreement)
is its pre-listed form: any test of it must state that this diagnostic was seen.

### I-89 / I-90 Intraday index rotation NAS100 vs US500: follow the morning relative move, or fade an extreme one (Fable FB-053 / FB-054, Wave 2, 2026-11-15; rules fixed before any data)
Source: Fable 5.2 (ORIGINAL; growth-vs-broad rotation within the day; related: intraday momentum and its reversal
after extreme moves). Label: SPECULATIVE. New family `index_rotation` (2 cells, threshold t 3.0). Not covered: P01 / P02
were multi-day pairs with swap, L14-L18 daily lead-lag.
Data: CFD development period (before 2021-09-14), NAS100 and US500 M1 (`DEFAULT_SOURCES`), New York time; US30
(2019-02 ..) as a diagnostic pair only.
Spread: s = r(NAS100) - beta x r(US500), beta = OLS slope of the two indices' 09:30 -> 15:55 returns over the previous
60 trading days (at least 40). Position size: 1 unit NAS100 against beta units US500. Cost per day traded = NAS100
round trip + beta x US500 round trip (engine spread at the entry time + 2 x slippage, each in bp of its entry price).
- **I-89 (FB-053):** morning spread m = s from the 09:30 open to the 10:30 close; hold sign(m) x spread from the 10:30
  close to the 15:55 close, every day.
- **I-90 (FB-054):** morning spread m from 09:30 to the 11:00 close; z = m / sd of m over the previous 60 days; days
  with |z| > 2 only: hold -sign(m) x spread from the 11:00 close to the 15:55 close.
Kills per cell (statistics per day, t over days with a trade): net <= 0; t < 3.0; halves (by date) not both > 0;
net <= 0 at doubled costs; net <= 0 without the 2 best days. The signs are predicted (follow / fade), not chosen.
Diagnostics: the same rules on NAS100 vs US30 (2019-21), gross vs cost, long-NAS vs short-NAS days.
Power line (signal-free, before the screen): sd of the 10:30 -> 15:55 spread and days with |z| > 2.
**Power (2026-11-15, before the screen):** 1,569 days; 10:30 -> 15:55 spread sd 30 bp -> t 3 needs ~2.2 bp a day
(I-89); 91 days with |z| > 2, 11:00 -> 15:55 spread sd 27 bp -> t 3 needs ~8.4 bp (I-90). Two-leg cost ~3-4 bp a day.
**Result (`research/screens/2026-11-15_i89_rotation_screen.py`): both KILLED.** I-89 follow: 1,569 days, net -3.1 bp,
t -4.19 (gross +1.3 vs two-leg cost 4.4). I-90 fade: 91 days, net -13.3 bp, t -3.02, gross -8.9: extreme relative
mornings **continue**, they do not revert. NAS100 vs US30 (2019-21) the same (gross +1.4 / -6.9). Family
`index_rotation`: closed after two falsifications. Fable FB-055 (residual z-score fade) is the same fade mechanism and
is not run; FB-095 (continuous SMT) follows I-88 and is not run.

### I-91 / I-92 / I-93 ICT event rules with timed exits, pooled over 8 cheap FTMO symbols: PDH / PDL raid, power of three, candle range theory (Fable FB-128 / FB-131 / FB-146, Wave 4, 2026-11-15; rules fixed before any data)
Source: ICT / smart-money concepts (practitioner, social media; the user asked for a fair test). Label: PRACTITIONER /
SPECULATIVE. Claimed mechanism: stops resting beyond obvious levels are taken ("liquidity raid") and price reverses.
New vs the falsified S01-S03 / H15: timed exits instead of tight stops and targets, breadth (8 symbols pooled),
cost from the engine. Family `ict_levels` (with S01, S02, S03, H15: 7 looks -> threshold t 3.0; Fable proposed 4.0,
the house rule is 3.0 up to 10).
Data: CFD development period (before 2021-09-14); US30, GER40, NAS100, US500, UK100, EURUSD, USDJPY, XAUUSD M1 via
`DEFAULT_SOURCES`; New York time; trading day = 17:00 -> 17:00 New York. ATR = mean daily range (high - low) of the
previous 14 trading days. Cost per round trip = engine spread at the entry time (`fill_spread_time`) + 2 x slippage,
bp of the entry price. No position crosses 17:00 New York (no swap).
- **I-91 PDH / PDL raid (FB-128):** window 03:00 -> 15:55 New York. Event: price trades above the previous trading
  day's high by >= 0.1 ATR, and an M5 close back below that high comes within 30 minutes of the first trade-through:
  short at that M5 close, exit at the 15:55 close. Mirrored at the low. First event per symbol, day and side.
- **I-92 power of three (FB-131):** the 00:00 New York open (open of the bar at 00:00). If price trades >= 0.3 ATR
  below it before 08:30 and an M5 close above it comes between 08:30 and 10:00: long at that close, exit 15:55.
  Mirrored. At most one trade per symbol and day (the first).
- **I-93 candle range theory (FB-146):** H4 candles aligned to 01:00, 05:00, 09:00, 13:00 New York (inside the
  trading day, the 17:00-01:00 block skipped). Candle n trades below candle n-1's low and closes back above it (inside
  n-1's range): long at n's close; mirrored at the high; exit at the close two H4 candles later, or at 16:55 if that
  comes first (no hold over 17:00).
Statistics per rule: per date, the mean net of that date's trades; t over dates. Kills each: net <= 0; t < 3.0;
halves (by date) not both > 0; net <= 0 at doubled costs; net <= 0 without the 2 best days. The direction is the ICT
one (predicted, not chosen).
Controls (diagnostics, no gate): I-91 breaches by >= 0.1 ATR without a reclaim within 30 minutes, the same short from
the 30-minute mark; I-92 days that dip >= 0.3 ATR but do not reclaim by 10:00 (long at the 10:00 close); I-93 candles
that close back inside without having traded beyond the prior extreme (long / short by close position). Per symbol.
Power line (signal-free, before the screen): event counts and the sd of the event-to-exit return.
**Power (2026-11-15, before the screen; script frozen):** I-91 2,196 events on 1,175 days, t 3 needs ~5.1 bp net;
I-92 1,761 events on 1,000 days, ~4.9 bp; I-93 4,256 events on 1,593 days, ~2.8 bp (costs ~1-3 bp a trade).
**Result (`research/screens/2026-11-15_i91_ict_events_screen.py`): all three KILLED.**
- I-91 PDH / PDL raid: 2,196 trades, net -1.5 bp, t -0.87 (gross +2.5 vs cost 1.6); the no-reclaim control -0.5.
  Per symbol (post-hoc, 8 looks, not a finding): US indices positive (NAS100 +11.5, US30 +10.2, US500 +7.0 net a trade),
  UK100 -5.0, XAUUSD -3.3, EURUSD -2.8.
- I-92 power of three: 1,761 trades, net -2.6 bp, t -1.59 (gross -0.8); control -3.0.
- I-93 candle range theory H4: 4,256 trades, net -0.8 bp, t -0.87 (gross +0.8); control (no sweep) +0.1.
With timed exits and breadth, the three most concrete ICT setups show no edge: gross within +-2.5 bp of zero, below
costs, and no better than their controls. No rescue (a US-index-only raid rule would be post-hoc).

### I-94 Level-touch null model for ICT levels: fair value gaps and equal highs / lows (Fable FB-126 / 137 / 138 / 149, Wave 4, 2026-11-15; descriptive, rules fixed before any data)
Purpose: answer the ICT level concepts in one descriptive pass against matched nulls (Fable: closes ~40 backlog rows).
Counts as one look for family `ict_levels`; never a pass. Symbols, period, ATR, trading day and New York time as I-91;
M15 bars from M1 inside the trading day; no costs (descriptive).
- **FVG (FB-126 / 137 / 138):** bullish FVG at M15 bar i: low[i] > high[i-2] with gap >= 0.05 ATR; zone = [high[i-2],
  low[i]]; first touch = the first later bar of the same trading day (up to 32 bars) whose low reaches low[i]; entry
  = low[i]. Outcomes: "held" = no bar in the next 4 trades below the zone bottom; forward return = close 4 bars after
  the touch bar vs entry, in the reversal direction (up for bullish), bp. Mirrored for bearish. **Null:** the same
  zone shifted by u x gap (u uniform 1..3, random sign, seeded), formed at the same bar, same touch and outcome rules.
  (Fixed before data, 2026-11-15: if the shifted zone's near edge is not beyond the formation close on the real zone's
  side, the shift sign is flipped, so the null zone is never "touched" instantly at a price already passed.)
  Also reported: share of FVGs touched within 32 bars (fill rate) vs the null.
- **Equal highs / lows (FB-149):** M15 swing high at j = high[j] above the 2 bars on each side (confirmed at j+2);
  "equal" = within 0.05 ATR of a swing high of the previous 32 bars with no bar between above both. Event at j+2:
  exceeded = a later bar of the same trading day within 16 bars trades above max of the two. **Null:** single swing
  highs (no equal partner), compared within buckets of distance from the event close to the level (0-0.1, 0.1-0.2,
  0.2-0.4 ATR). Mirrored for lows.
Flag (not a pass): a concept is "above its null" when the pooled difference is > 2 bp in forward return (FVG) or > 5
points in exceed rate (equal levels) with t >= 3 (date-clustered); a flagged concept could only become a new,
pre-registered hypothesis with its own one-time test.
**Result (`research/screens/2026-11-15_i94_level_null_model.py`, 2026-11-15): no concept above its null.**
- FVG (54,113 zones, 8 symbols): real zones are touched far more often (81 % vs 47 %: they sit closer to price), held
  4 bars 49 % vs 41 %, but the 60-minute forward return after the touch is +0.38 bp vs -0.26 bp for the shifted
  null: difference +0.2 bp a day, t 0.86. Economically nothing (costs ~1.5 bp); every symbol within +-1.3 bp.
- Equal highs / lows: exceeded within 4 hours **less** often than single swing levels at the same distance (69 vs
  72 %, 50 vs 51 %, 32 vs 35 %; difference -1.4 points, t -4.78): the "equal highs get taken" claim has the wrong sign
  here.
Together with I-91..I-93 and I-88: the ICT level concepts behave like random levels on our data. The ICT backlog rows
(FB-128..161 except those run) are closed by this pass unless a new mechanism is named.

### T-20 Resting limit entries for clock-based holds (review D5, 2026-11-11; UNTESTED)
Cost side only: rest a limit at the bid N minutes before the clock entry, market at the deadline. Reuse
`Order.limit_fill`, `tp_penetration`, `fill_probe` / `fill_report`. Kills it: the 5-minute move after a
fill goes against the order by at least the half-spread saved, or fill rate < 60 %. Only for cells whose
gross is already near cost.

### T-21 Causal graph and type-B check on every card (CF, 2026-11-18; RULE: accepted by the user 2026-11-18, `docs/research-runner.md` › Causal check per card)
Before any data look a card states its causal graph in a few lines: signal X, outcome Y, the forced counterparty M
(mechanism), confounders with their proxies, and any collider or mediator that must NOT be controlled. Plus one
implied absence (where M does not trade, the effect must be gone), tested as a named placebo. Verdict PASSED would
need both checks: type-A (ledger, t threshold, as now) and type-B (graph declared, confounders checked, no collider
controls, placebo absent). Source `books/lopezdeprado-causal-factor-investing.md` C1, C2, C4, C10. I-109 already has a
placebo window (10 trade dates earlier, +10.2 bp, t 2.14: not absent; near the mid-month auctions) and a diff-in-diff
check would be a diagnostic only (its test is spent).

### T-22 Simulation tests for our estimators (CF, 2026-11-18; tooling)
The three seeded 5,000-draw structures of CF ch.7 (fork, collider, confounded mediator) plus one true effect as unit
tests of the scorecard / gates code: the correct specification must report no effect (or recover the true one); a
wrong control must not create significance unnoticed. Cheap, deterministic. Source CF pp.52-60, appendix B.

### T-23 Tail concentration audit of every stream (FT, 2026-11-18; tooling / diagnostic)
For each passed or shelf stream (Strategy 20, Strategy 19, I-109, the shelf rows) report on its net period returns:
the largest observation's share of sum |r|^p for p = 1, 2, 4, gains and losses apart; mean and t without the k largest
gains and, separately, the k largest losses (k = 1, 2, 5) as sensitivity only (the full sample stays the result).
Flag a stream whose sign or t depends on a handful of periods. Source FT p.16-17, 54-55, 148-150, 194-201. Strategy 20
already has the M6 cap (+-50 %); this adds the period view. Diagnostic on spent data, no new look.
**T-23 result 2026-11-18 (`research/screens/2026-11-18_t23_tail_concentration.py`, registered numbers reproduced):**
largest observation's share of sum r^4 / mean without the 5 largest gains / without the 5 largest losses:
Strategy 20 development (186 weeks) 0.45 (one week +3,254 bp: CONCENTRATED) / +84 bp (t 2.32) / +179 (t 4.14);
Strategy 20 test (147 weeks) 0.24 / +103 (t 2.95) / +179 (t 4.75); I-109 development (380 months) 0.16 / +15.1 (t 3.80)
/ +21.3 (t 5.27); I-109 test (61 months) 0.20 / +7.8 (t 0.80) / +37.3 (t 3.33). No stream FRAGILE (all stay > 0 without
their 5 best periods); every largest observation is a gain (right-skewed, not short tail risk). Weak spot: I-109's test
mean leans on a few months (2021-22); its forward log carries the weight. Strategy 20's development leans on one week,
its test does not.

### T-24 Fat-tail power check (FT, 2026-11-18; method, extends M4)
Before a data look, simulate the planned sample under Gaussian, Student-t(3) and volatility-clustered P/L at the card's
expected edge and at zero: report how often the t >= 3.0 gate passes (power) and falsely passes. A card whose power
collapses under the fat-tailed scenario is parked like M4's < 15 %. Source FT p.153-160, 389-396.

### T-25 Stress Monte Carlo beyond the worst seen day (FT, 2026-11-18; BUILT 2026-11-18: `risk/stress.py`, spec risk-management.md › Stress scenarios)
The prop / FTMO pass and funded-phase simulations bootstrap past days, so no path can be worse than history. Add
pre-registered shock scenarios (one day at 1.5x and 2x the worst seen, a clustered week of losses, all legs at once)
and report breach rates per scenario next to the bootstrap. Source FT p.177-181, 232, 469-475.


### I-95 Strategy 20's flow sort on FTMO crypto CFDs (ORIGINAL, goal-1 bridge, 2026-11-15; closed by arithmetic, no data look)
Idea: trade the weekly taker-flow sort (Strategy 20 signal from Binance) on FTMO's 30 crypto CFDs, so goal 1 could use
it at FTMO. Arithmetic (census 2026-11-15, `results/mt5_census.csv`): every FTMO crypto CFD charges -30 % a year swap on
both sides (-8.2 bp a night, 7 nights a week incl. the Friday triple) = ~58 bp a week per side, ~115 bp a week for the
long-short book, plus weekend spreads 1-70 bp per side. The liquid-coin edge is guessed at 50-60 bp a week (FB-017,
I-78 clipped +56): far below the swap alone. **Closed**, not screened; an intraday version is I-82 (daily flow, killed).

### FB-017 liquid-only Strategy 20 (capacity / prop-firm variant; frozen 2026-11-15 before any run)
Why: HyroTrader limits coins under 100 M USD market cap to 5 % of balance; the Bybit check showed the book mostly
trades coins outside the top tier. **Frozen rule:** Strategy 20 exactly (`docs/strategy-crypto_flow.md` › Rule), except
that each Monday the eligible set is cut to the 100 symbols with the highest 30-bar median daily quote volume before
the Monday (ties by symbol name) before the sort; the 20-symbol minimum and quintiles apply to the cut set. Both
historical periods are spent (development seen in I-78, test used by I-78 / I-83), so the run on them is a
**diagnostic** (capacity and prop fit), never a test; the variant goes into the forward log as frozen here. No
rescue: no other N is run.

### I-96 Overnight -> intraday reversal sort on FTMO's US share CFDs (Fable FB-112, Wave 3, 2026-11-15; rule fixed before any data)
Mechanism: attention / retail buying lifts the open of stocks with large overnight moves; liquidity providers and
institutions lean against it during the day (Berkman, Koch, Tuttle, Zhang 2012, "Paying attention"; Lou, Polk, Skouras
2019, both UNVERIFIED here). Label: PUBLISHED finding (direction), ADAPTATION (FTMO large caps, daily L/S).
Prediction: names with the highest overnight return underperform those with the lowest from open to close.
- **Universe (fixed by cost, not by returns):** the 33 US share CFDs with a median FTMO M1 spread <= 10 bp over the last
  20 trading days (`results/share_spreads.csv`, `research/screens/2026-11-15_share_spreads.py`): AAPL AMZN GOOG MSFT
  NVDA TSLA V WMT META GE BA RTX LMT PLTR AMD QCOM AVGO CSCO JNJ MCD SBUX KO MSTR CVX FDX JPM DIS IBM SNOW ASML AZN
  BRK.B XOM; a name joins once it has 20 daily bars.
- **Data:** Yahoo daily OHLC (split-adjusted), dividends added back on ex-days, development only 2010-01-01 ..
  2021-09-13 (download stops there). Overnight r_on = (open_t + dividend_t) / close_{t-1} - 1; intraday r_id =
  close_t / open_t - 1.
- **Rule:** every day with >= 15 names: rank by r_on (ties by name); long the 5 lowest, short the 5 highest, equal
  weight, entry at the open, exit at the close (no swap). Day result per unit side: mean(long r_id) - mean(short r_id).
- **Cost:** per name and fill today's FTMO median spread / 2 at the open (09:35-09:40) and at the close (15:50-15:55)
  + 1 bp slippage per fill; summed over both sides (2-way, ~8-10 bp a day). Today's spreads applied to 2010-2021
  (assumption A1); FTMO share commission UNVERIFIED (assumed 0, A2; the doubled-cost gate covers ~8 bp more).
- **Kills (family SHARES, first look, |t| threshold 3.0):** net <= 0; t(net) < 3.0; halves (2010-2015 / 2016-2021) not
  both > 0; net <= 0 at doubled costs; net <= 0 without the 2 best days. Reported, not gates: signal deciles
  (dose-response), the open-auction caveat (daily open = auction print; a pass needs a 09:35 check on FTMO M1 for the
  2020-2021 names before any spec).
- Power (before data): ~2,900 days, guessed sd of the daily L/S ~150 bp -> MDE at t 3 ~8 bp; halved guess 5-12.5 bp vs
  cost ~9 bp: arithmetic borderline, run because it is the share family's best prop fit (daily, breadth). Prior 10 %.
**Result 2026-11-15 (one look, `research/screens/2026-11-15_i96_overnight_reversal_screen.py`): KILLED.** 2,944 days:
gross +10.1 bp a day (gross t 4.44: the reversal is real), cost 16.1 (the extreme names carry the wide spreads), net
-6.0, t -2.64; halves +1.2 / -13.6; gross by year falls from +15-25 (2010-15) to -7 / +3 / -11 (2019-21). Deciles:
the low-overnight decile earns +8.2 bp intraday, the high one -1.8 (mostly a rebound of the losers). Wave 3 closed
with it: FB-113 / FB-114 (same gap-reversal mechanism), FB-115 (power without outside M1), FB-123 / FB-124 (cost +
financing above the guess) are closed without a look (ledger).

### I-97 Cross-sectional 3-week momentum on all Binance USDT perps (Fable FB-010, HANDOFF Open 3, 2026-11-15; rule fixed before any data)
Source read (summary pages + abstract): Liu, Tsyvinski, Wu 2022 (JF 77(2); NBER w25882): weekly quintile sorts, 3-week
momentum long-short ~4.1 % a week (1 / 2 / 4 weeks: 2.7 / 3.3 / 2.5 %), sample 2014-2018 incl. very small coins.
Label: PUBLISHED finding, ADAPTATION (Binance perps, funding, our costs). Mechanism: under-reaction / attention.
- **Rule:** each Monday, eligibility exactly as I-78 / Strategy 20 rule 1 (`research/screens/2026-11-14_i78_crypto_wide_factors_screen.py`
  `week_rows`); signal mom3 = last close before the Monday / the close 21 bars earlier - 1 (>= 22 bars). Sort ascending
  (mom3, symbol); **long the top quintile (winners), short the bottom** (direction pre-registered: momentum), equal
  weight, Monday open -> Sunday close, funding inside the hold, 20 bp a week. Development 2020-01..2023-12 only.
- **Power (before data):** random-leg sd ~479 bp -> |t| 3 needs ~105 bp a week net; halved published 205 - 20 = 185.
- **Kills (family crypto_xs_factors, 7th look, |t| >= 3.0):** momentum-direction net <= 0; t < 3.0; halves 2020-21 /
  2022-23 not both > 0; net <= 0 at 40 bp; net <= 0 without the 2 best weeks. Reported: placebo (gross, shuffled),
  deciles, weekly correlation with Strategy 20.
- Contamination noted: 1-week momentum was seen (I-75 on 17 perps; Strategy 20 realism check, corr 0.56 with a 1-week
  return sort); 3-week momentum on this universe was not. A pass gets a one-time test on 2024+ (4th use of that period).
**Result 2026-11-15 (one look, `research/screens/2026-11-15_i97_crypto_momentum_screen.py`): KILLED.** 186 weeks: gross
+60.1, net +40.1 bp a week, t 0.68, 49 % positive, worst -4,565; halves +200.8 / -86.7; deciles flat (107-211 bp);
placebo mean t +0.13; correlation 0.47 with Strategy 20. The published 4.1 % a week does not appear on Binance perps
2020-23. With C2 (failed test) this is the second falsification of crypto momentum: FB-009 / FB-011 / FB-220 closed.

### FB-273 maker-fill model for Strategy 20's Monday rebalance (method, 2026-11-15; rule fixed before any data)
Question: does posting a limit order at the touch instead of crossing the spread cut Strategy 20's cost (taker 5 bp,
maker 2 bp a fill on Binance USDT-M at the base tier) once missed fills and adverse selection are counted?
- **Sample (fixed before data):** the 13 Mondays 2023-10-02 .. 2023-12-25 (development), Binance daily aggTrades of the
  Monday for XEMUSDT, BELUSDT (small, ~15 M USD a day), CRVUSDT (mid, ~87 M), SOLUSDT (large); the four picked as
  frequent Q4-2023 book members across the volume range. Each Monday and symbol: one buy and one sell order.
- **Reference P0:** the last trade price before Monday 00:00:00 UTC (from the Monday file's first trade if none).
- **Taker now:** the first trade after 00:00 whose aggressor matches the order (buy: buyer is taker), price + 5 bp.
- **Maker first:** limit at P0, filled at P0 when a later trade prints strictly through it (buy: a trade < P0; sell:
  > P0) within 60 minutes; fee 2 bp. Unfilled after 60 minutes: taker at the first matching trade after 00:60, + 5 bp.
- **Cost per order (bp):** side x (fill price - P0) / P0 x 1e4 + fee. Saving = taker-now cost - maker-first cost.
- **Decision rule:** maker-first is adopted for any live / prop implementation of Strategy 20 if the mean saving is
  >= 1 bp a fill with t >= 2 (clustered by Monday); otherwise taker stays. The backtest cost (20 bp a week) is not
  changed either way (a default; the user's call).
**Result 2026-11-15: keep taker.** Taker 9.9 bp a fill, maker-first 12.0 (93 % filled; misses ~151 bp); saving -2.1 bp,
t -0.44 over 13 Mondays. Taker cost is ~2x the 5 bp a fill in the backtest (spec › Execution).

### I-98 Spot-hedged funding carry on Binance (Fable FB-035, 2026-11-15; rule fixed before any data)
Mechanism: leveraged perp longs pay funding to shorts; a long-spot / short-perp position collects it with no price
bet (cash-and-carry). Hypothesis: trailing funding persists enough week to week that the highest-funding coins pay
more than the turnover cost and basis noise. Label: PUBLISHED mechanism (basis / funding carry, e.g. Schmeling,
Schrimpf, Todorov BIS WP 1087), ADAPTATION. **Not the I-73 / Strategy 19 hypothesis** (those bet on prices of high-
vs low-funding coins and failed replication); here the price exposure is hedged, so it is a new family `crypto_basis`.
- **Universe:** each Monday, Strategy 20's eligibility (rule 1) and a spot kline file with the Monday bar and the
  previous 7 bars (`data/cache/binance_wide_spot`, 243 symbols, development only 2020-01..2023-12).
- **Rule:** rank by the sum of funding rates settled in the 7 days before the Monday (ties by name); hold the 10
  highest **with a positive sum**, equal weight (fewer if fewer qualify; none = flat week). Per name: long spot at the
  Monday open, short perp at the Monday open, both closed at the Sunday close; result = spot return - perp return +
  funding settled inside the hold (Monday 00:00 excluded, as Strategy 20).
- **Cost:** only names that enter or leave pay: 25 bp per name per entry and 25 per exit (spot taker 10 + spread ~5,
  perp ~10 as measured in FB-273), per unit of notional; a name kept from last week pays nothing.
- **Kills (new family, first look, t >= 3.0):** net <= 0; t < 3.0; halves 2020-21 / 2022-23 not both > 0; net <= 0 at
  doubled costs; net <= 0 without the 2 best weeks. Reported: funding vs basis split, turnover, share of flat weeks,
  worst week (a perp squeeze is a basis loss).
- Expected: top-funding coins pay ~20-60 bp a week in 2020-21, less in 2022-23; prior 30 %. Returns are per unit of
  notional with spot fully paid (capital-heavy: an annual figure needs no leverage assumption).
**Result 2026-11-15 (one look, `research/screens/2026-11-15_i98_basis_carry_screen.py`): KILLED.** 186 weeks, 10 names
each: gross +45.2 bp a week (funding +46.5, basis -1.3), turnover cost 33.3, net +12.0, t 1.84, worst -206, sd 89;
halves +55.1 / -22.0 (2020 +38, 2021 +65, 2022 -29, 2023 -15); doubled costs -21.3. The funding is real but the
top-funding set rotates too fast; a hysteresis / lower-turnover rule would be a new hypothesis shaped by this
result (not run: rescue rule). Family `crypto_basis` one falsification.

### I-99 Single-name shock reversal vs a flat index on Alpaca M1 (Fable FB-121, SHARES, 2026-11-16; rule fixed before any data)
Mechanism: a sharp single-name drop while the index is flat is forced or panicked selling (no market news); liquidity
providers who absorb it are paid by a partial rebound into the close (Nagel 2012 "Evaporating liquidity", UNVERIFIED
here; practitioner "flush and reclaim"). Label: PUBLISHED finding (short-term reversal pays liquidity provision),
ADAPTATION (intraday trigger, FTMO large caps). Prediction: after the trigger the stock outperforms from entry to 15:55.
Reopened data question: FB-121 waited for M1 before 2019; Alpaca SIP minute bars 2016+ (the user's account, 2026-11-16).
- **Universe (by cost, fixed before data):** the 33 names of I-96 (FTMO median M1 spread <= 10 bp, `research/share_spreads_2026-11-15.csv`).
  Index = QQQ (Alpaca; NAS100 CFD tracks it). Development only 2016-01-04 .. 2021-09-13.
- **Data:** Alpaca 1Min SIP, split-adjusted, regular session only (09:30-16:00 America/New_York), closes forward-filled
  on the minute grid. r30(t) = close_t / close_(t-30 min) - 1. sigma30 = sd of the 13 non-overlapping 30-min returns
  per session (09:30-16:00) over the previous 20 sessions (needs >= 15 sessions; no same-day data).
- **Rule:** evaluated at every M1 close from 10:00 to 15:00 NY: trigger when stock r30 <= -3 sigma30(stock) and
  |QQQ r30| <= 0.5 sigma30(QQQ). First trigger per stock and day only. Skip the day if the stock's overnight gap
  |open 09:30 / previous 16:00 close - 1| > 2 x the sd of its previous 20 close-to-close returns (earnings proxy; no
  date file). Long at the next M1 bar's open, exit at the close of the last bar with time <= 15:55. No stop.
- **Cost:** FTMO median spread / 2 (`all_bp` at entry, `close_bp` at exit) + 1 bp slippage per fill (today's spreads on
  2016-2021: assumption A1 of I-96; commission assumed 0, A2).
- **Kills (family SHARES, 2nd look; |t| >= 3.0):** net <= 0; t(net, per-date means) < 3.0; halves 2016-2018 / 2019-2021
  not both > 0; net <= 0 at doubled costs; net <= 0 without the 2 best dates. Fewer than 300 events = underpowered: no
  verdict, the card stays a card (still counted). Reported, not gates: the mirror (short after a +3 sigma spike), the
  same trigger on the excluded gap days (earnings control), dose 2.5 / 4 sigma, by year.
- **Power (before data):** guess ~700 events, sd entry -> 15:55 ~200 bp -> SE ~7.6, MDE at t 3 ~23 bp; halved guess
  10-25 bp gross vs ~8 bp cost: underpowered unless the event count is higher; run as the share family's best M1 row
  (intraday, no swap, breadth). Prior 5 %. A pass would need the one-time test on 2021-09-14+ Alpaca bars of the same names.
- **Data fixes before the run (A3, A4; no outcome seen):** Alpaca history starts 2016-01-01 (2015-12 empty), so events
  start once 15 sessions exist (~2016-01-25). Alpaca keeps a reused ticker's old company: SNOW 2016-17 is Intrawest, so
  SNOW counts from its 2020-09-16 listing (PLTR from 2020-09-30). RTX carries a level jump at the 2020 merger (a gap
  day, skipped by the gap rule; same-day returns unaffected). META is mapped to FB's history (checked by price).
**Result 2026-11-16 (one look, `research/screens/2026-11-16_i99_shock_reversal_screen.py`): KILLED.** 2,662 events on
1,016 dates (well powered: SE ~3 bp): gross -2.0 bp, cost 7.5, net -9.5, t -2.47; halves -7.6 / -11.8; every year
negative. Reported: the mirror (short after +3 sigma) gross -3.2 (t -2.72 net), dose 2.5 / 4 sigma gross -2.5 / -7.8,
gap days -18.2: after an idiosyncratic 30-min shock large caps drift slightly further, not back (a few bp, far below
cost). Second falsification in the SHARES family (after I-96): the family is closed (stop rules).

### I-100 Wide funding-carry sort on unseen Binance perps (Fable card 1, 2026-11-16 sweep; family `crypto_carry_xs`, third and last look; rule fixed before any data)
Mechanism and source as I-73 (BIS WP 1087: crowded leveraged longs pay high funding and are the marginal sellers).
Label ADAPTATION. Question: does the carry spread (price + funding) hold on the wide, unseen part of the perp universe,
where I-73R found the funding but only a third of the price part?
- **Universe:** every perp in `data/cache/binance_wide` (incl. delisted) **minus the 37 symbols of I-73 / I-73R**
  (BTC ETH BCH XRP EOS LTC TRX ETC LINK XLM ADA BNB XTZ XMR NEO DASH ATOM; BAT IOST IOTA ONT QTUM VET ZEC THETA ALGO
  COMP KNC ZIL ZRX BAND DOGE KAVA OMG RLC SXP DOT, all USDT). Eligible each Monday by Strategy 20's development rule
  (I-78 `week_rows`: >= 60 daily bars before the Monday, 30-day median quote volume >= 5 M USDT, the Monday bar, 7 bars
  in the prior week) and a funding history that starts at least 7 days before the Monday. Weeks with fewer than 40
  eligible names are skipped.
- **Signal (A1):** funding accrued over the 7 days before the Monday = sum of the rates settled in (Monday - 7 d,
  Monday] (I-73 test assumption: ranks like the mean of 21 rates for 8 h symbols and stays "7 days" for 4 h / 1 h ones).
- **Trade:** n = floor(eligible / 5); short the top n, long the bottom n (ascending sort, ties by name), equal weight;
  entry at the Monday open, exit at the close of the next Sunday bar (I-78 convention). Weekly gross per unit side =
  mean bottom return - mean top return + top funding (received) - bottom funding (paid), settlements strictly inside the
  hold. Cost 20 bp a week; doubled 40.
- **Period:** development only, Mondays 2020-05-04 .. the last week ending by 2023-12-31 (crypto split). The test
  period 2024-01..2026-10 only after a development pass, frozen, once (its 4th use: t 3.3 if the user accepts M8, else
  3.0; decided at that time, not now).
- **Kills (development):** net <= 0; t < 3.0; a half (by weeks) <= 0; net <= 0 at 40 bp; net <= 0 without the 2 best
  weeks; price part < -20 bp a week (I-73's own kill). **Reported, not gates** (proposals M6 / M7 not accepted yet):
  member returns capped at +-50 % (sign kept, share of the mean); smallest half as a share of the mean; years; price /
  funding parts; weekly correlation with Strategy 20's flow spread on the same weeks (above 0.5 = same stream).
- **Verdict wording:** KILLED on any kill. If only t fails with 1.5 <= t < 3.0, the record also says "UNPROVEN-POSITIVE
  under the proposed M1" (shelf only if the user accepts M1). Either way the family `crypto_carry_xs` is closed after
  this look.
- **Power (card, before data):** long-short weekly sd 475-620 bp (Strategy 20's) on ~186 weeks: MDE at t 3 = 105-136
  bp; evidence +112 / +138 (17 perps), +63 (20 perps); expected t 1.4-3.0, pass chance ~20 %. The signal-free line
  (random-quintile weekly sd on this universe) is recorded below before the run.
- **A2 (before the run):** index contracts (BTCDOM, DEFI, FOOTBALL, BLUEBIRD) and 1000x contracts stay in, as in
  Strategy 20's universe (I-73R excluded index contracts only because its rule took the first 20 listings).
**I-100 power (2026-11-17, before the run, signal-free, `--power`):** 153 weeks with >= 40 eligible unseen names
(2021-01-25 .. 2023-12-25; before 2021 fewer than 40), median 98 a week, 194 names; random-quintile weekly sd 522 bp,
se 42 bp: t 3 needs 127 bp a week net. At the I-73 test effect (+112) the expected t is ~2.7, at I-73R's (+63) ~1.5.
**Result 2026-11-17 (one look, `research/screens/2026-11-17_i100_wide_carry_screen.py`): KILLED on t (2.45 < 3.0);
UNPROVEN-POSITIVE under the proposed M1.** 153 weeks: net +107.1 bp a week (price +67.6, funding +59.6, cost 20),
sd 541, 60 % positive weeks, worst -1,767; halves +152 / +63; at 40 bp +87; without the 2 best weeks +86; every other
kill passes. Reported: capped +-50 % +81 (0.75 of the mean, t 2.14); median week +106; years 2021 +228, 2022 -11,
2023 +111; weekly correlation with Strategy 20's flow spread +0.27 (a different stream). Reading: the carry spread
holds on 194 unseen names with about twice I-73R's price part, close to the I-73 test effect, but 153 weeks cannot
reach t 3 and 2022 is flat. Family `crypto_carry_xs` closed after this third look (as pre-registered). Not a
candidate for card 5's book unless the user accepts M1 (then it is a shelf row with a forward log, M3).

### I-101 FINRA short-volume ratio, weekly cross-sectional sort on the wide US share universe (Fable card 3, 2026-11-16 sweep; new family `share_flow`, venue M13; rule fixed before any data)
Mechanism, two readings with opposite signs: (a) short sellers are informed (Diether, Lee, Werner 2009, UNVERIFIED
here: high short volume -> lower returns); (b) off-exchange short volume is mostly wholesalers shorting to fill
retail buy orders, so a high ratio marks retail buying. Label PUBLISHED finding (a) / PRACTITIONER (b), ADAPTATION
(weekly, top-1,000, 2016-2021). The sign is the test: two cells, |t| >= 3.3 (M9 wording, adopted by Opus as the
stricter bar).
- **Universe:** `docs/share-universe.md` (month of the entry day).
- **Data:** FINRA daily short-sale volume files for every trading day 2015-10-01 .. 2021-09-13 (development only):
  `FNSQ` + `FNYX` summed per symbol before 2018-08-01 (A1: the facilities served throughout; `FNQC` / `FNRA` are not
  served for 2016), `CNMS` from 2018-08-01. Symbols mapped `/` -> `.`. Prices: Alpaca daily closes (split-adjusted).
- **Signal:** SVR = sum ShortVolume / sum TotalVolume over the 5 trading days up to the last trading day before the
  entry day, minus the stock's mean daily SVR over the 60 trading days before that window (needs >= 4 window days and
  >= 40 baseline days with TotalVolume > 0). A week is skipped when the window or the baseline spans 2018-08-01
  (the facility break).
- **Trade:** entry at the close of the first trading day of each week (Monday, or Tuesday after a holiday), exit at
  the close of the first trading day of the next week; n = floor(names with a signal / 10); cell A long the lowest
  n SVR, short the highest n (reading a); cell B the mirror (reading b); equal weight; ties by symbol. A name with no
  exit bar exits at its last close (A2).
- **Cost (A3):** per leg 2 fills x (2 bp fee / auction + 1 bp slippage) = 6 bp, short leg + 0.6 bp borrow: 13 bp a
  week on the long-short unit (the card's "~7 bp per unit side", both sides); doubled 26. Dividends not in the prices.
- **Period:** development weeks 2016-01 .. the last week whose exit is before 2021-09-14; test 2021-09-14 .. once,
  only after a development pass.
- **Kills (each cell):** net t < 3.3; net <= 0; halves 2016-2018 / 2019-2021 not both > 0; net <= 0 at doubled cost;
  net <= 0 without the 2 best weeks. Reported, not gates: smallest half / mean (M7 proposal), member returns capped
  at +-50 %, years, decile spread monotonicity (deciles 1..10 mean next-week return).
- **Power (card, before data):** decile long-short weekly sd 100-150 bp (guess) on ~290 weeks: MDE at t 3.3 =
  19-29 bp a week; halved published ~16 bp: expected t 1.8-2.8, pass chance ~8 %. The signal-free line (random
  deciles on the same names and weeks) is recorded below before the run.

### I-102 Overnight -> 10:00 reversal on the wide US share universe, real-share cost (Fable card 4, 2026-11-16 sweep; family `share_reversal_real`, venue M13; rule fixed before any data)
I-96's mechanism (attention buying at the open, supplied by intermediaries paid by the intraday reversal; Berkman et
al. 2012, Lou / Polk / Skouras 2019, UNVERIFIED sizes) in a new cost cell: real shares at ~3.5 bp per name and day
instead of FTMO CFD spreads (I-96: gross +10.1 bp, t 4.44, killed by 16 bp cost; gross faded 2019-21). M13 gives real
shares their own family labels; the fade is the main reason for the low prior. Label ADAPTATION.
- **Universe:** `docs/share-universe.md`, month of the trade day; a day needs >= 500 names with all three prices.
- **Prices (A1):** previous close = Alpaca daily close of the previous session; signal price = close of the 30-min bar
  opening 09:30 (the 10:00 price); entry = open of the 30-min bar opening 10:00; exit = the day's Alpaca daily close
  (a market-on-close fill). SPY's previous close and 10:00 price from the same sources.
- **Signal:** s = (10:00 price / previous close - 1) - SPY's same. Ties by symbol.
- **Trade:** n = floor(names / 10); short the top n, long the bottom n, equal weight, entry 10:00, exit at the close;
  flat overnight. Day gross per unit side = mean(long entry -> close) - mean(short entry -> close).
- **Cost (A2):** 1.5 bp half-spread + 1 bp slippage at 10:00, 1 bp at the close = 3.5 bp per name; 7 bp a day on the
  long-short unit; doubled 14. Short borrow intraday: none.
- **Period:** development trading days 2016-01-04 .. 2021-09-13; test after a pass only, frozen, once.
- **Kills (|t| 3.0):** net <= 0; t < 3.0; halves 2016-2018 / 2019-2021 not both > 0; net <= 0 at doubled cost; net
  <= 0 without the 2 best days. Reported, not gates: smallest half / mean (M7 proposal), years, deciles of s (mean
  entry -> close per decile), the same sort with the open as entry (09:30 open -> close, I-96's original timing).
- **Power (card, before data):** long-short daily sd guessed 40-60 bp, ~1,430 days: MDE at t 3 = 3-5 bp net, i.e.
  10-12 bp gross needed; pass chance ~8 %. Signal-free line recorded below before the run.
**I-101 data check (2026-11-17, before any signal):** FINRA development files complete: 716 trading days before
2018-08-01 with both `FNSQ` and `FNYX` (no day with only one), `CNMS` from 2018-08-01 to 2021-09-13; 499 MB.
**I-101 / I-102 period note (2026-11-17, before any return):** the universe starts 2016-04 (docs/share-universe.md
A5: Alpaca history starts 2016-01), so both development periods start with April 2016; halves stay 2016-2018 /
2019-2021.
**I-101 power (2026-11-17, before the run, signal-free, `power`):** 271 weeks (2016-04-04 .. 2021-09-07; weeks whose
window or baseline spans 2018-08-01 skipped), 977-~990 names a week; random-decile weekly sd 72 bp, se 4.4 bp:
|t| 3.3 needs 14 bp a week net (27 bp gross at 13 bp cost). Better powered than the card's guess (sd 100-150).
**I-101 result 2026-11-17 (one look, `research/screens/2026-11-17_i101_short_volume_screen.py run`): KILLED, both
cells.** 271 weeks, ~987 names: gross spread (long low SVR, short high) +0.8 bp a week, gross t 0.16. Cell A net -12.2
(t -2.55), cell B net -13.8 (t -2.88); every kill hit in both. Deciles 1..10 of SVR earn 33.6, 34.6, 33.4, 33.9, 35.3,
32.0, 31.2, 36.7, 37.4, 32.8 bp the next week: flat. Well powered (se 4.4 bp): the weekly off-exchange short-volume
ratio carries no cross-sectional information about next week's return in the top 1,000 names, in either reading.
First falsification in family `share_flow`.
**I-102 data note (2026-11-17, before any intraday data; share-universe A7):** the 10:00 price = close of the last
1-min bar before 10:00 ET and the entry = open of the first 1-min bar from 10:00 (window 09:57-10:03, one request per
day and 500 names): the same trades the 30-min bars would give; a name with no trade in 09:57-09:59 or 10:00-10:02 is
out that day. The diagnostic's 09:30 open = Alpaca's daily open.

### I-103 Leveraged single-stock ETF rebalance into the close (Fable card 7, 2026-11-16 sweep; new family `letf_single`, venue M13; split set by the user 2026-11-17; rule fixed before any data)
Mechanism (who is forced): a daily-reset fund with leverage L must trade (L^2 - L) x net assets x the underlying's day
return near the close, in the direction of the day's move (2x and -2x funds alike buy on up days); the amount is
known by 15:30. The index version is tiny (H02 / H06: index funds are small against futures volume); single names can
have a far higher flow-to-volume ratio. Label ADAPTATION (Cheng & Madhavan 2009 on index LETFs, UNVERIFIED here).
Prediction: on days when the required flow is large against the underlying's 15:30-16:00 dollar volume, the
underlying continues in the day's direction from 15:30 to the close.
- **Step 1 (signal-free audit; go / no-go fixed now):** funds = US-listed daily-reset single-stock funds (leverage
  +-1.5, +-2, +-3; long and inverse; incl. delisted), found by name in Alpaca's asset lists and checked against
  SEC fund filings; per fund: leverage, underlying, net assets from SEC N-PORT filings (as public; between filings
  carried forward by the fund's own daily return, as the card says; flows between filings are missed, A1), daily.
  Per underlying and day: F = sum over its funds of (L^2 - L) x net assets x |underlying return 09:30 open -> 15:30|;
  ratio = F / dollar volume of the underlying's 15:30-16:00 minute bars. **Go only if >= 300 name-days in development
  have ratio >= 5 %; otherwise closed on size, no return looked at.**
- **Trade (step 2, only after a go):** at 15:30 on name-days with ratio >= 5 %: follow sign(return 09:30 open ->
  15:30), entry = open of the first 1-min bar from 15:30, exit = Alpaca daily close (market-on-close). Control
  (reported): the same days' 15:30 -> close move of the 1,000-name universe's other names with a same-sized move.
- **Cost:** real shares 2.5 bp per trade round trip (1 bp half-spread + 0.5 slippage at 15:30, 1 bp at the close).
  Doubled 5.
- **Periods (the user, 2026-11-17):** development from the first single-stock leveraged fund launch to 2024-12-31;
  test 2025-01-01 .., once.
- **Kills (step 2):** net <= 0; t < 3.0 (per-date means); halves of development not both > 0; doubled cost <= 0;
  without the 2 best dates <= 0; dose check: the mean at ratio >= 10 % not above the mean at 5-10 %.
- **Power (card):** last-30-minute sd on such days ~90 bp (guess), ~300 date clusters: MDE ~16 bp; pass chance ~10 %.
  Step 2's power line from the step 1 counts, before any return.
**I-103 step 1 result (2026-11-17, `research/screens/2026-11-17_i103_step1_flow_audit.py`, signal-free): GO.** 352
single-stock funds found (Alpaca names), 280 with SEC N-PORT reports (quarterly public), 267 usable; in development
(2022-07 .. 2024-12) 20 underlyings carry fund net assets on 5,517 name-days. Ratio >= 5 %: **338 name-days on 175
dates** (2022: 1, 2023: 11, 2024: 326; COIN 133, TSLA 87, NVDA 65, MSTR 30, others <= 4); >= 10 %: 147. Median
ratio 0.08 %, p90 2.5 %, p99 18 %. Caveats: net assets before a fund's first public report count as 0 and flows
between reports are missed (both shrink F: a conservative count); 72 funds are not in SEC's ticker map (mostly
2025-26 launches). Fixed during the audit before any return: a fund without net assets that day adds 0 (a NaN had
dropped whole underlyings; first count was 5).
**Step 2 assumptions (before any return):** A3 halves of development = the event dates split at their median date
(326 of 338 events are in 2024, so calendar halves would leave 12 events in the first); A4 entry prices for the 175
dates fetched as 15:29-15:31 minute bars (the step 1 files kept only the last price before 15:30 and the volume).
**I-103 step 2 power (2026-11-17, before the run, signal-free):** 329 events with an entry price on 175 dates;
per-date sd of the 15:30 -> close return 62 bp, se 4.7: t 3 needs 14.1 bp net (16.6 gross). As the card guessed.
**I-103 step 2 result (2026-11-17, one look, `research/screens/2026-11-17_i103_step2_screen.py run`): KILLED (t,
halves).** 329 events on 175 dates (2022-09 .. 2024-12): gross +6.4 bp from 15:30 to the close in the day's
direction, net per date +3.7, t 0.80, sd 62; halves (split 2024-08-14) -1.2 / +8.6; doubled cost +1.2; without the 2
best dates +1.9; dose >= 10 % +8.8 vs 5-10 % +0.4 (the right order, small). Control: universe names without
leveraged funds and a same-sized 09:30 -> 15:30 move continue +3.2 bp on the same days, so the forced flow adds about
3 bp: real perhaps, far below a tradable size. By underlying: COIN +6.7 (133), TSLA +9.5 (87), NVDA +1.2 (65), MSTR
+9.1 (30). First falsification in family `letf_single`; Fable's long-range item 8 (repeat the size audit yearly as
the funds grow) stays a note.
**I-102 power (2026-11-17, before the run, signal-free):** 1,372 days (2016-04-01 .. 2021-09-13), 855-~1,000 names a
day (median 983); random-decile daily sd 22 bp, se 0.58: t 3 needs 1.8 bp a day net (8.8 gross at 7 bp cost). Better
powered than the card's guess (sd 40-60).
**I-102 result 2026-11-17 (one look, `research/screens/2026-11-17_i102_open_reversal_screen.py run`): KILLED.** 1,372
days: gross +2.55 bp a day (gross t 1.04), cost 7, net -4.45, t -1.82, sd 91 (the realised long-short sd is far
above the random-decile 22: the extremes move together); halves +1.3 / -10.3; every kill hit. Gross by year 2016-18
+8 to +9, 2019 +3.5, 2020 -5.5, 2021 -10: the same fade as I-96. Deciles (10:00 -> close): +1.1 for the lowest s,
-1.4 for the highest: small. **Diagnostic (not a gate, not a cell): sorting at the 09:30 open (I-96 timing, open ->
close) gross +12.9 bp a day, gross t 3.94, positive every year (2021 +20.9)**: the reversal sits in 09:30-10:00. At
the same 7 bp it would be ~+5.9 net, t ~1.8: below the development bar, and it is a new hypothesis whose development
period is now seen; per the stop rules it is not tested. Parked for the user (HANDOFF › Open): a shelf / forward
candidate only if M1 / M3 are accepted. First falsification in family `share_reversal_real`.

### I-104 Wikipedia page-view attention sort on the wide US share universe (Fable card 9, 2026-11-16 sweep; new family `share_attention`, venue M13; rule fixed before any data)
Mechanism: abnormal attention brings uninformed buying that later reverses (Da, Engelberg, Gao 2011 on search volume,
UNVERIFIED here: up for ~2 weeks, then reversal), or attention marks news that keeps drifting. The sign is not fixed:
two cells, |t| >= 3.3. Label PUBLISHED finding (attention), ADAPTATION (Wikipedia page views, top 1,000, weekly).
- **Universe, trade, cost, periods, kills:** exactly as I-101 (weekly, entry at the close of the first trading day of
  the week, exit at the next week's first close; deciles; cell A long the lowest attention / short the highest, cell
  B the mirror; 13 bp a week; development 2016-04 .. 2021-09-13; kills |t| < 3.3, net <= 0, halves 2016-18 / 2019-21
  not both > 0, doubled cost <= 0, without the 2 best weeks <= 0).
- **Signal:** attention = page views of the company's English Wikipedia article over the 7 calendar days before the
  entry day / the mean weekly views of the 8 weeks before that (Wikimedia REST pageviews, daily, `user` agent,
  all-access; from 2015-07). A name needs >= 100 views in the baseline weeks on average.
- **Mapping (frozen before any page view is read, A1):** ticker -> article from Wikidata (items with a ticker symbol
  P249 qualifier on an NYSE / NASDAQ / NYSE American listing P414, plus their English sitelink); a ticker used by
  several items -> the item whose listing period covers the week, else dropped; unmapped names are out of the sort
  (reported: share of the universe mapped per year).
- **Power:** as I-101 (sd 72, se 4.4, |t| 3.3 needs 14 bp net); the signal-free line on the mapped names is recorded
  before the run. Pass chance ~5 % (card).
**I-104 mapping (2026-11-17, before any page view):** Wikidata ticker qualifiers on US listings (NYSE, Nasdaq, NYSE
American; Nordic Nasdaq rows dropped) map 89 % of development member-months (2016 87 % .. 2021 90 %); the unmapped
names (PYPL, XLNX, FITB, ...) lack a ticker statement in Wikidata (A2: unrelated to returns). A3: a renamed article
splits its views across titles (e.g. a company rename); the current title only is read, so a rename can make one
spurious week.
**I-104 power (2026-11-17, before the run, signal-free):** 1,514 articles read (106 without views); 284 weeks
(2016-04-04 .. 2021-09-07), 674-~760 names a week with a signal (median 739, 74 % of the universe after the
>= 100-view baseline); random-decile weekly sd 77 bp, se 4.6: |t| 3.3 needs 15 bp a week net (28 gross).
**I-104 result 2026-11-17 (one look, `research/screens/2026-11-17_i104_attention_screen.py run`; the printout reuses
I-101's labels, "SVR" = attention ratio): KILLED, both cells.** 284 weeks, ~739 names: gross (long low attention,
short high) -2.5 bp a week, gross t -0.27; cell A net -15.5 (t -1.67), cell B net -10.5 (t -1.13); realised sd 156.
Deciles 1..10 of attention: 31.4, 24.6, 28.5, 30.2, 29.4, 32.7, 34.8, 34.4, 33.5, 34.6 bp the next week: no usable
order. First falsification in family `share_attention`.

### I-105 Overnight -> close reversal at the official open, wide US shares (forward only; from I-102's diagnostic; family `share_reversal_real`, second row; registered 2026-11-17 under M3)
Not a development pass: I-102's diagnostic (sort at the 09:30 open, open -> close) gave gross +12.9 bp a day, gross t
3.94, positive every year 2016-2021; at 7 bp ~+5.9 net, t ~1.8. That period is now seen, so the only clean evidence
is forward data. Frozen rule (no change after today): each trading day, universe of the month (docs/share-universe.md,
formed from data known at the month end), s = official open / previous close - 1 minus SPY's same (Alpaca daily
bars); short the top decile, long the bottom decile, equal weight; entry at the official open (market-on-open), exit
at the official close (market-on-close); net = gross - 7 bp a day on the long-short unit. A day needs >= 500 names.
Forward from the first trading day after the logger exists; judged with the FB-254 boundary on daily nets (a look
every 65 trading days, 8 looks = 520 days; c 2.071; early kill z <= -2). Power: at +5.9 bp a day (sd 91) 30 %
confirmed by day 520, at +3 11 %; at 0 the early kill fires 8 %. Unverified: that Alpaca's daily open is the official
opening auction price (checked against the auction endpoint before the first forward day).
**I-105 open-price check (2026-11-17, before the first forward day):** Alpaca's daily open is not the official
opening auction print: 330 symbol-days (15 names, October 2026) differ by a median 3.4 bp, p90 23 bp, max 88 bp (71
exact). The development diagnostic (+12.9 bp) used the daily open, so part of it may be a first-print artefact (I-96
noted the same risk). The frozen forward rule uses the official prints (auctions endpoint, condition Q / M, else O /
6) for the open, the close and the previous close; the forward log decides.

### I-106 Insider open-market purchases on the wide US share universe (Fable long-range item 3, 2026-11-17; new family `share_insider`, venue M13; rule fixed before any data)
Mechanism: officers and directors buy their own stock with their own money when they think it is cheap; the
information leaks into the price over the following weeks (Lakonishok & Lee 2001; Cohen, Malloy & Pomorski 2012,
"opportunistic" insiders ~+80 bp a month, mostly small caps; UNVERIFIED here). Label PUBLISHED finding, ADAPTATION
(top-1,000 large caps, where the effect is smaller). One-sided (the sign is the literature's): |t| 3.0.
- **Data:** SEC "Insider Transactions Data Sets" (quarterly, Forms 3 / 4 / 5 as filed; tables SUBMISSION,
  REPORTINGOWNER, NONDERIV_TRANS), 2016Q1 .. 2021Q3, fetched with the user's contact string. Prices: Alpaca daily
  closes (data/cache/alpaca_1d); universe docs/share-universe.md (month of the filing date).
- **Event:** a Form 4 with at least one non-derivative transaction code P (open-market purchase, acquired) by a
  reporting owner who is an officer or a director, value (shares x price) >= USD 25,000 summed per filing; events of
  one issuer on one filing date merge. Point in time: FILING_DATE.
- **Trade:** long the stock at the close of the first trading day after the filing date, hold 20 trading days, exit
  at the close; short SPY over the same window. Event return = stock return - SPY return (bp). A new event for a name
  already held is skipped until that hold ends.
- **Cost:** 3 bp per stock fill (2) + 1 bp per SPY fill (2) = 8 bp per event; doubled 16.
- **Period:** development filings 2016-04-01 .. holds that end by 2021-09-13.
- **Statistic:** events grouped by entry week; t of the weekly means with Newey-West (4 lags, the 20-day holds
  overlap).
- **Kills:** net <= 0; t < 3.0; halves 2016-2018 / 2019-2021 not both > 0; doubled cost <= 0; without the 2 best weeks
  <= 0. Reported, not gates: dose (events with >= 2 insiders or >= USD 1 M vs the rest), the mirror (officer /
  director sales code S >= USD 1 M: event return in the short direction), by year.
- **Power:** from the signal-free event count and the 20-day abnormal-return dispersion, recorded before the run.
**I-106 power (2026-11-17, before the run, signal-free):** 2,812 events (2016-04-04 .. 2021-08-13) on 867 names, 274
entry weeks; event sd 1,075 bp over 20 days; weekly-mean Newey-West se 29.8 bp: t 3 needs 89 bp net per event (97
gross). Above the halved large-cap literature (~30-60 bp a month): expected t ~1-2, pass chance ~10 %; run as
registered (one look).
**I-106 result 2026-11-17 (one look, `research/screens/2026-11-17_i106_insider_buys_screen.py run`): KILLED, M1
FALSIFIED (net <= 0).** 2,812 events: gross -38.2 bp per event over 20 days vs SPY, net -46.2, weekly NW t -1.46;
halves +20.4 / -119.6; by year 2016 +44, 2017 -22, 2018 +43, 2019 -132, 2020 -127, 2021 -75. Dose: >= 2 insiders or
>= USD 1 M -28.7 (790) vs the rest -53.0. Mirror (short after officer / director sales >= USD 1 M): 12,118 events,
gross -22.2 (the sold names outperformed). In the top 1,000 names insiders buy weakness that kept falling in
2019-2021; the small-cap literature effect does not carry over. First falsification in family `share_insider`.

### I-107 Fails-to-deliver intensity, half-monthly sort on the wide US share universe (Fable long-range item 3, 2026-11-17; new family `share_fails`, venue M13; rule fixed before any data)
Mechanism, two readings: (a) persistent settlement fails mark short sellers who cannot borrow (hard-to-borrow,
crowded shorts): the stock underperforms (Stratmann & Welborn 2016, UNVERIFIED); (b) fails mark short squeezes in
the making: the stock outperforms. The sign is the test: two cells, |t| >= 3.3. Label PUBLISHED / ADAPTATION.
Short interest (the companion card) is not testable on development: FINRA's free exchange-listed files start 2021-06.
- **Data:** SEC fails-to-deliver files `cnsfails<YYYYMM>a/b` (settlement date, CUSIP, symbol, quantity, price),
  2016-01 .. 2021-08, fetched with the user's contact string; Alpaca daily closes and volumes; universe
  docs/share-universe.md.
- **Point in time (A1, conservative):** the a-file (settlement days 1-15 of month M) is used from the first trading
  day of month M+1; the b-file (16-end of M) from the first trading day on or after the 16th of M+1.
- **Signal:** intensity = sum over the half-month of fails quantity x price / sum of the name's dollar volume over the
  same settlement days (0 if the name has no fails).
- **Trade:** at each availability day, among universe members (month of that day): high = top decile by intensity
  (names with fails only), low = all names with zero fails in the half-month; cell A long low / short high (reading
  a), cell B the mirror; equal weight; enter at that day's close, exit at the close of the next availability day.
- **Cost (as I-101 per rebalance):** 13 bp per rebalance on the long-short unit; doubled 26.
- **Period:** development rebalances 2016-04 .. the last exit before 2021-09-14.
- **Kills (each cell):** |t| < 3.3; net <= 0; halves 2016-2018 / 2019-2021 not both > 0; doubled cost <= 0; without
  the 2 best periods <= 0. Reported: the top decile's mean intensity, by year.
- **Power:** signal-free line (random top-decile vs zero-fails split) recorded before the run.
**I-107 power (2026-11-17, before the run, signal-free):** 136 SEC files (three folders on sec.gov); 130 half-month
periods (2016-04-01 .. 2021-09-01); high group median 97 names, zero-fails group median 27 (most large caps fail
something every half-month); random-split sd 77 bp, se 6.8: |t| 3.3 needs 22 bp net per half-month (35 gross).
**I-107 result 2026-11-17 (one look, `research/screens/2026-11-17_i107_fails_screen.py run`): KILLED, both cells.**
130 half-months: gross (long no-fails, short high-fails) -31.0 bp, gross t -1.59. Cell A net -44.0, t -2.26 (M1
FALSIFIED). Cell B (long high-fails) net +18.0, t 0.92, halves -12.9 / +49.8: the gain is 2020 +92 and 2021 +88
(the squeeze era), 2017-2019 negative; t < 1.5, so not UNPROVEN-POSITIVE. First falsification in family `share_fails`.

### I-108 Insider open-market purchases on US mid-caps, ranks 1,001-2,000 (user pick 2026-11-17 after I-106; family `share_insider`, venue M13; rule fixed before any data)
I-106's mechanism where the literature puts the effect: smaller firms (Lakonishok & Lee 2001; Cohen, Malloy &
Pomorski 2012; UNVERIFIED sizes). A new counted hypothesis in family `share_insider`, not a rescue: the universe is
disjoint from I-106's (no name-month overlap), every other rule is I-106's word for word. Seen before this card:
I-106's large-cap result (gross -38 bp, the 2019-2021 halves strongly negative); that weighs on the prior. A second
falsification closes the family (stop rules). Label PUBLISHED finding, ADAPTATION. One-sided: |t| 3.0.
- **Universe:** `docs/share-universe.md` rule with ranks 1,001-2,000 instead of 1-1,000 (same 60-session median dollar
  volume, close > 5, >= 60 bars, de-duplication, fund filter, A4 exclusions), month of the filing date ->
  `data/cache/alpaca_meta/universe_1001_2000.csv`.
- **Data, event, trade, period, statistic:** I-106 unchanged (SEC Insider Transactions Data Sets 2016Q1 .. 2021Q3;
  Form 4, code P, officer or director, >= USD 25,000 per filing, merged per issuer and filing date; long at the close
  of the first trading day after the filing date for 20 trading days vs SPY; overlapping events per name skipped;
  weekly means, Newey-West 4 lags).
- **Cost (A1):** 10 bp per stock fill (half-spread ~7 + slippage 3 for names of roughly USD 5-30 M daily volume) + 1 bp
  per SPY fill = 22 bp per event; doubled 44. Signal-free check in the power step: the Abdi-Ranaldo (2017)
  close-high-low spread estimate, median over the universe name-months; if its half-spread median exceeds 7 bp, the
  stock fill cost becomes that median + 3 bp (rule fixed now).
- **Kills:** net <= 0; t < 3.0; halves 2016-2018 / 2019-2021 not both > 0; doubled cost <= 0; without the 2 best weeks
  <= 0. Reported, not gates: dose (>= 2 insiders or >= USD 1 M vs the rest), the sales mirror, by year.
- **Power:** signal-free event count and weekly-mean NW se, recorded before the run. Prior ~10 %.
**I-108 power (2026-11-17, before the run, signal-free):** universe ranks 1,001-2,000 built (129 months, 3,896 names;
rank-2,000 median dollar volume USD 5-13 M by year). Cost check: Abdi-Ranaldo half-spread median 10.9 bp over 64,922
name-months > 7, so by the card's rule the stock fill is 13.9 bp: 29.7 bp per event, doubled 59.4. 2,848 events
(2016-04-04 .. 2021-08-13) on 1,060 names, 266 entry weeks; event sd 1,315 bp; weekly-mean NW se 54.9 bp: t 3 needs
165 bp net per event (195 gross). The halved small-cap literature (~40 bp per 20 days) gives t ~0.2: pass chance
< 5 %. Run as registered (one look; auto decision 43: an M1 verdict still settles the family).
**I-108 result 2026-11-17 (one look, `research/screens/2026-11-17_i108_midcap_insider_screen.py run`): KILLED, M1
FALSIFIED (net <= 0).** 2,848 events: gross -8.9 bp per event over 20 days vs SPY, net -38.6, weekly NW t -0.24; every
kill hit; halves +36.2 / -110.4; by year 2016 +164, 2017 -7, 2018 0, 2019 -59, 2020 -205, 2021 +44. Dose (>= 2
insiders or >= USD 1 M) -70.0 (726) vs the rest -27.8: the bigger buys did worse. Mirror (sales >= USD 1 M, short):
6,151 events, gross -13.6. Same pattern as I-106 one size class down. Second falsification in family
`share_insider`: the family is closed (stop rules).

### I-109 Treasury month-end duration extension (harvest batch 16, 2026-11-17; new family `rates_month_end`, venue rates: Treasury futures (goal 2) or bond ETFs (M13), not FTMO; rule fixed before any data)
Mechanism: Treasury indices (Bloomberg US Treasury) rebalance on the last business day of the month; new issues enter
and the index duration extends, so index funds and benchmarked managers must buy duration into month-end. A
counterparty that must trade, on a known date. Sources read by Opus: ohlcv.io "The Treasury auction cycle, out of
sample" (2026-10-22; futures 2010-2026: on the last three trade dates of a month ZT +1.2 bp a day (t 3.9), ZF +3.8
(t 4.7), ZN +5.2 (t 4.1), UB +11.3 (t 3.5); three days chosen after seeing the chart; the same study finds the
auction cycle of Lou, Yan & Zhang 2013 gone once month-end days are removed). Label PRACTITIONER / PUBLISHED, ADAPTATION.
Not family `turn_of_month` (closed): that family tested US equity indices on cash / rebalancing flows; this is a
different market and a different forced buyer (auto decision 44).
- **Data:** FRED H.15 constant-maturity yields DGS10 (gated), DGS5 and DGS2 (reported), daily, 1990-01-02 ..
  2021-09-13 (development; the test period is later). Price return per day r = -D * dy, D = modified duration of a
  10-year par bond at the previous day's yield (closed form); carry ignored.
- **Event:** each calendar month's last 3 trade dates (dates with a DGS10 value).
- **Trade:** long 10-year duration from the close of the 4th-last trade date to the close of the last trade date.
  Cost 2 bp of price per event round trip (ZN about one tick round trip, IEF about 1 bp a fill); doubled 4.
- **Gated statistic (A1):** the event's excess return = its 3-day return minus 3 x the mean daily return of that
  month's other trade dates (removes the 1990-2021 rally in bonds, which flatters any long); net = excess - cost.
  t over months (one event per month, no overlap).
- **Kills (one-sided, t 3.0):** net <= 0; t < 3.0; halves 1990-2005 / 2006-2021 not both > 0; doubled cost <= 0;
  without the 2 best months <= 0. Reported, not gates: raw (unhedged) return, the last 2 days, placebo (the same
  window 10 trade dates earlier), DGS5 and DGS2, by decade.
- **Expected size:** ZN +15.6 bp per month-end in the blog; halved ~8 bp. **Power:** signal-free sd of the excess
  over all months, recorded before the run.
**I-109 power (2026-11-17, before the run, signal-free):** FRED DGS10 1990-01-03 .. 2021-09-13, 381 months; excess sd
87.4 bp for 3-day windows 5-14 trade dates before month-end; se 4.5: t 3 needs 13.4 bp net (15.4 gross). The blog's
ZN size scaled to 10-year duration is ~20 bp, halved ~10: pass chance ~25-35 %. FRED needs curl's own user agent.
**I-109 development result 2026-11-17 (one look): PASSED every development gate.** 381 months: excess gross +20.4 bp
per month-end, net +18.4, t 4.42; halves +14.4 / +22.6; doubled cost +16.4; without the 2 best +17.0. By decade net
+12.1 / +18.2 / +25.3 / +16.9 (2020-21). Reported: raw +19.2 (t 4.85); last 2 days +16.2; placebo 10 trade dates
earlier +10.2 (t 2.14; near the mid-month 10- / 30-year auctions); DGS5 +14.1 (t 5.78), DGS2 +5.9 (t 6.41).
Integrity check after the run (CMT curves switch to new on-the-run notes, and 2/5/7-year notes are issued at
month-end): real Alpaca ETF closes over the same 69 months (2016-04 .. 2021-08; ex-dividend dates fall on the 1st
business day, outside the window): IEF +22.1 bp raw (t 3.59), correlation 0.99 with the DGS10 window; TLT +38.6
(t 3.04); SHY +6.9 (t 5.38). Not a curve artefact.
**I-109 one-time test, rule fixed before any test data (2026-11-17, auto decision 45):** frozen variant as above
(DGS10, last 3 trade dates, excess statistic, cost 2 bp), months 2021-10 .. 2026-10 (first month with a whole month
after 2021-09-14; last complete month), ~61 months. Power: se ~11.2, t 3 alone would need ~34 bp, so the gates are:
(1) test net > 0; (2) test t >= 1.5; (3) test doubled cost > 0; (4) tradable check: IEF (Alpaca closes) raw window
mean > 0 over the same months. All four = PASSED (M1); net > 0 with t < 1.5 = not confirmed; net <= 0 = FALSIFIED.
Expected at the development size: t ~1.6 (pass ~55 %). Not blind: the ohlcv.io study (2010-2026 futures) covers this
period and reported the month-end rally; recorded so the result is read as a confirmation on our data, not an
independent discovery. A pass goes to the shelf as a forward log on IEF (M3) and to HANDOFF for the user.
**I-109 one-time test result 2026-11-17 (`research/screens/2026-11-17_i109_treasury_month_end_screen.py test`):
PASSED (M1), all four gates.** 61 months 2021-10 .. 2026-10: excess gross +26.9 bp per month-end, net +24.9, t 2.14;
doubled cost +22.9; IEF real closes raw +23.2 bp (t 2.54). By year 2021 (3 months) +91.5, 2022 +63.2, 2023 +5.5,
2024 +25.0, 2025 +16.3, 2026 -7.8. Development + test: the same sign in both, net ~+19-25 bp per month-end on
10-year duration, about 3 days a month in the market. Not blind (see the test rule). Next: a frozen IEF forward log on
the shelf (M3) and the user's decision on a venue (Treasury futures ZN / bond ETFs, goal 2; FTMO lists no bonds).
Note 2026-11-17 (after the test): the development run counted the partial month 2021-09 (window 9-13 Sep, not a
month-end); without it 380 months, net +18.4, t 4.39: no change. Forward logs `shelf_i109` (DGS10, registered
statistic) and `shelf_i109_ief` (IEF raw) from the 2026-11 month-end; complete months only.
**Venue (decided by the user 2026-11-18):** CME Micro 10-Year Yield futures (10Y, $10 per bp), 1-3 contracts, held in
the next-month contract. Per micro on DGS10 windows: net ~$16-21 a month-end, sd ~$90-96 (research-log 2026-11-18).

### I-110 Treasury month-end duration extension on long bonds (20-year; the user's pick 2026-11-17 after I-109; family `rates_month_end`, 2nd hypothesis; rule fixed before any 20-year data)
I-109's mechanism and rule on the long end, where index extension buys the most duration (ohlcv.io: UB +11.3 bp a
day on the last 3 trade dates vs ZN +5.2). A new counted hypothesis in the same family, not independent of I-109
(same months, same flow): its value is the size per event for a goal-2 sleeve. Seen before this card: I-109's
results, and TLT over 2016-04 .. 2021-08 (+38.6 bp raw, t 3.04, I-109's integrity check). Label ADAPTATION. t 3.0.
- **Data:** FRED DGS20 (20-year constant maturity; FRED's series resumes 1993-10-01), development months 1993-10 ..
  2021-08 (whole months only; I-109's partial-month slip not repeated). Return r = -D * dy with D of a 20-year par bond.
- **Event, trade, statistic:** I-109 unchanged (last 3 trade dates; excess over 3 x the month's other-day mean; t
  over months). Cost 3 bp per event (UB about one tick of ~2.6 bp round trip, TLT about 1 bp a fill); doubled 6.
- **Kills:** net <= 0; t < 3.0; halves 1993-10 .. 2007 / 2008 .. 2021-08 not both > 0; doubled cost <= 0; without the 2
  best months <= 0. Reported: raw, last 2 days, placebo 10 trade dates earlier, excess per unit of event sd vs I-109.
- **One-time test (fixed now, before any test data):** months 2021-10 .. 2026-10, frozen as above: (1) net > 0;
  (2) t >= 1.5; (3) doubled cost > 0; (4) TLT (Alpaca closes) raw window mean > 0. All four = PASSED; net > 0 with
  t < 1.5 = not confirmed; net <= 0 = FALSIFIED. Not blind (the 2026 study covers the period).
- **Power:** signal-free sd from windows 5-14 trade dates before month-end, recorded before the run.
**I-110 power (2026-11-17, before the run, signal-free):** DGS20 1993-10-04 .. 2021-08-31, 335 months; excess sd
136.0 bp, se 7.4: t 3 needs 22.3 bp net (25.3 gross). Expected ~2x I-109's size (~35-40 bp; TLT +38.6 in the check
months), halved ~20: pass chance ~50-60 %, mostly carried by I-109's evidence (same months).
**I-110 development result 2026-11-17 (one look): PASSED every development gate.** 335 months: excess gross +32.4 bp
per month-end, net +29.4, t 4.32; halves +24.9 / +34.1; doubled +26.4; without the 2 best +27.2. Reported: raw +29.5
(t 4.61); last 2 days +26.4; placebo +15.4 (t 1.97); excess per event sd 0.260 (20-year) vs 0.248 (10-year, same
months): the long end scales the size (1.57x) at about the same risk-adjusted edge.
**I-110 one-time test result 2026-11-17 (`... test`): NOT CONFIRMED (gate t >= 1.5 failed; not FALSIFIED).** 61 months
2021-10 .. 2026-10: excess gross +26.0, net +23.0, t 1.33; doubled +20.0; TLT raw +21.6 (t 1.20). By year 2021 (3
months) +136, 2022 +66, 2023 -1, 2024 +35, 2025 +16, 2026 -39. Same sign as development, but the long end earned no
more than the 10-year (I-109 test net +24.9) at ~1.6x the risk in the 2022-26 bond volatility. M1: net > 0 with
t < 1.5 is neither PASSED nor UNPROVEN-POSITIVE; no retest. The sizing case for long bonds is not confirmed; I-109
(10-year) stays the family's row.

### I-111 Threshold rebalancing on US500 (harvest batches 4 / 17: HV-T0037-1, HV-T0124-1; family `rebalancing_threshold`, reopened by the user 2026-11-17; rule fixed before any data)
**Decision by the user (2026-11-17, "Reopen rebalancing"):** threshold rebalancing is its own family
`rebalancing_threshold`, separate from the closed `turn_of_month`; the calendar month-end signal stays closed (I-67).
Mechanism (Harvey, Mazzoleni & Melone, NBER w33554, 2025; read by Opus): balanced funds rebalance a 60/40 mix when the
equity weight drifts beyond a band; the trade is computable from public prices, so stocks fall the day after they
become overweight (one sd of the Threshold signal: S&P futures -15.6 bp next day, 10-year +4.4; trough at day 4,
reverting within two weeks; t > 4 over 1997-2023; strategy Sharpe ~1 with the bond leg). Label PUBLISHED,
ADAPTATION (equity leg only on an FTMO CFD; no bonds on FTMO). Our development data lie inside the paper's sample:
the screen is a replication with FTMO costs, not a discovery.
- **Data:** US500 cash closes (last M1 close <= 16:00 New York; histdata 2010-2014, MT5 2015+), FRED DGS10 daily
  par-bond returns (I-109's function) as the bond leg (A1: the paper uses futures). Days with both values.
- **Signal (paper eq. 2):** for each band d in 0, 0.1, ..., 2.5 % a simulated 60/40 portfolio drifts with the day's
  returns; its equity weight minus 0.60 after the day is Threshold_d; when |Threshold_d| > d the portfolio resets to
  60/40 for the next day (A2: the signal on a reset day is the pre-reset deviation). Signal S = mean over the 26 bands.
- **Position:** p = clip(-S / 1.5 %, -1, 1) (the paper's scale; clip A3), held from the cash close of day t to the
  next cash close. Gross = p x next-day US500 return.
- **Cost (FTMO table, today's defaults):** |change in p| x (half spread + slippage) per side, swap per night on |p| by
  direction (triple Friday). Doubled = both doubled.
- **Period:** 2010-01 .. 2021-08 (pre-sample + development), halves 2010-2015 / 2016-2021-08.
- **Kills:** net <= 0; t < 3.0 (daily, iid); halves not both > 0; doubled cost <= 0; without the 2 best days <= 0.
  Reported: gross, the paper's paired leg (p x (US500 - bond)), without 2020-02-20 .. 2020-04-30, mean |p|.
- **Power:** permutation of S across days (signal-free), recorded before the run. One-time test rule fixed after a
  development pass, before any test data.
**I-111 power (2026-11-17, before the run, signal-free):** 2,700 days 2010-11-16 .. 2021-09-13 (the histdata US500
pre-sample starts 2010-11-16); S sd 0.43 %, mean |p| 0.29; permuted gross sd 38 bp a day, se of the mean 0.58 bp:
t 3 needs 1.74 bp a day net. The paper's size at this scale ~4.5 bp a day gross (halved ~2.3); FTMO swap and fills
~1 bp a day: pass chance ~25-35 %.
**I-111 result 2026-11-17 (one look, `research/screens/2026-11-17_i111_threshold_rebalancing_screen.py run`): KILLED
(t < 3.0); M1: net > 0 with t 1.37 < 1.5, neither FALSIFIED nor UNPROVEN-POSITIVE.** 2,699 days: gross +1.88 bp a day
(t 1.79), net +1.44, t 1.37; halves +0.33 / +2.44; doubled +0.99; without the 2 best days +0.65. Reported: the paper's
paired leg (US500 - 10-year) gross +2.13 (t 1.73); net without 2020-02-20 .. 04-30 -0.08 (t -0.12); by year 2020
+15.5, seven of twelve years negative. Inside the paper's own sample the equity leg on a CFD is one crash; the
published t > 4 leans on 2008-09 and 2020, which the paper also notes (Sharpe 0.90 without them, for the paired
futures strategy). First kill in family `rebalancing_threshold`; no rescue (no paired leg on FTMO).

### I-112 Month-end duration extension in euro, UK and Japanese government bonds (2026-11-17, after I-109; family `rates_month_end`, 3rd hypothesis; rule fixed before any of these data)
Global bond indices (Bloomberg Global Aggregate, FTSE WGBI) and the domestic ones rebalance on the last business day of
the month, so I-109's forced duration buying should show in every member market. An independent-market replication
of I-109 (different bonds, investors and calendars) and a goal-2 diversifier (Bund / Gilt / JGB futures). Label
ADAPTATION of I-109. Seen before: I-109 / I-110 only; none of these series.
- **Data (A1-A3):** euro area: ECB AAA curve 10-year spot (YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y, daily from 2004-09);
  UK: Bank of England nominal spot curve 10-year (glcnominalddata.zip, daily); Japan: MOF JGB 10-year par yields
  (jgbcme_all.csv). Fitted / constant-maturity yields; return r = -D * dy with I-109's 10-year par-bond duration (A2:
  applied to spot yields too). Each market's own trade dates (dates with a value). Cache data/cache/intl_yields.
- **Event, trade, statistic:** I-109 unchanged per market (last 3 trade dates; excess over 3 x the month's other-day
  mean; cost 2 bp per month-end; doubled 4). Pooled = equal-weight mean of the markets with data that month.
- **Development:** months 1990-01 .. 2021-08 (euro from 2004-10). Kills (pooled, t 3.0): net <= 0; t < 3.0; halves
  1990-2005 / 2006-2021-08 not both > 0; doubled <= 0; without the 2 best months <= 0; breadth: any market's own net
  <= 0. Reported: each market's net and t, correlation of the markets' month-end excess with the US (DGS10).
- **One-time test (fixed now):** months 2021-10 .. latest complete month in all three files: pooled net > 0, pooled
  t >= 1.5, doubled > 0, at least 2 of 3 markets net > 0. All = PASSED; else as I-109.
- **Power:** signal-free sd of the pooled excess (windows 5-14 trade dates before month-end), before the run.
**I-112 power (2026-11-17, before the run, signal-free):** files EU 2004-09-06 .., UK 1979-01-02 .., JP 1986-07-05 ..
(levels checked on five dates, no returns); development months: EU 204, UK 380, JP 380; pooled 380 months, sd 53.5
bp, se 2.7: t 3 needs 8.2 bp net. I-109's US size ~20 bp (halved ~10): pass chance ~50 % if the mechanism is global.
Fix before the run: JGB 10-year days at exactly 0 % use the duration limit (10) instead of dropping the day.
**I-112 result 2026-11-17 (one look, `research/screens/2026-11-17_i112_intl_month_end_screen.py run`): KILLED
(t < 3.0, halves, breadth); M1: pooled net > 0 with t 1.00, neither FALSIFIED nor UNPROVEN-POSITIVE.** 380 pooled
months: net +2.5 bp per month-end, t 1.00; halves -2.0 / +7.1; doubled +0.5; without the 2 best +1.4. By market: euro
+8.0 (t 2.08, 204 months), UK +8.6 (t 2.34), Japan -4.8 (t -1.98); correlation of the month-end excess with the US
0.48 / 0.56 / 0.16. Euro and UK lean the US way at less than half its size; Japan does not. No rescue (dropping Japan
would be a new, counted hypothesis on seen data). I-109's month-end effect looks mostly US-specific (the US Treasury
index rebalancing and its trackers), which is consistent with the mechanism but gives no second market.

### I-113 VIX futures basis: short in contango, long in backwardation (2026-11-18, Fable row 16 / scout 2 #8; new family `vix_basis`, venue Cboe VX / VXM futures (goal 2), not FTMO; rule fixed before any VX data)
Mechanism: hedgers and VIX ETPs (VXX and peers roll front into second month every day) are structural buyers of VIX
futures as crash insurance; the futures basis then prices a risk premium, not the expected VIX path, and futures
converge to spot at settlement. Sources read by Opus: Simon & Campasano, "The VIX Futures Basis: Evidence and Trading
Strategies" (EFMA 2013 paper, 2012-08-16 draft, full text): basis has no forecast power for VIX but forecasts VX
returns ~one for one (Table 3); rule p. 14-16; 2007-2011 results Table 4: short 82 trades +$539 hedged / +$656
unhedged per contract, long 42 trades +$908 hedged / ~+$1,040 unhedged, after ~$60 round-trip costs; "the roll
accounts for the profits". Chan *Algorithmic Trading* ch. 5: VX roll about -50 % a year. Label PUBLISHED, sample
2006-2011 inside our development window (only 2012+ is post-publication). Not a closed family: no VIX row in the
ledger was ever run (HV-T0067 / T0083 parked as unfetchable; the data gap is now closed by Cboe's free files).
- **Data:** Cboe CFE daily settlements of the monthly VX contracts (archive files `CFE_<month><yy>_VX.csv` to 2013,
  per-contract files `VX/VX_<settlement date>.csv` after; weekly contracts excluded; settlements before 2007-03-26
  divided by 10, the old 10x quote); VIX close (Cboe `VIX_History.csv`). Hedge cell only: S&P 500 index closes (Yahoo
  `^GSPC`), as a stand-in for ES. Development: trades opened 2007-01-02 .. exited by 2021-09-13 (2006 data only to
  estimate the first hedge ratio, as the paper). Test data (later dates) not downloaded before the test rule is fixed.
- **Rule (paper's baseline, Table 4):** each trade date t, take the front monthly VX with >= 10 business days to its
  settlement (business days = VX trade dates in (t, settlement]); daily roll = (settle_t - VIX_t) / business days.
  Roll > +0.10: short 1 VX at t's settlement; roll < -0.10: long 1 VX. Exit at the settlement 5 trade dates later,
  same contract. One position at a time; earliest re-entry the trade date after an exit (assumption: the paper's
  "trades are entered at the end of the next day that entry conditions are triggered").
- **Cells (2):** U = unhedged VX (gated; one leg, tradable as VX or 1/10-size VXM); H = hedged with the paper's
  eq. 3-4 S&P hedge ratio, fitted on all prior calendar years (expanding), fixed at entry (reported, not gated:
  index closes are 15 minutes earlier than VX settlements and not ES).
- **Cost:** $60 per round trip per contract (the paper's average incl. a full bid-ask spread; VX tick 0.05 = $50);
  doubled $120. Settlement prices stand in for the paper's first <= 0.10-wide quote after 15:00 CT (assumption).
- **Gated statistic:** mean net $ per trade of cell U, t over trades (no overlap by construction).
- **Kills (one-sided, t 3.0):** net <= 0; t < 3.0; halves 2007-2013 / 2014-2021 not both > 0 (the 2nd half is wholly
  post-publication); doubled cost <= 0; without the 2 best trades <= 0; breadth: short trades or long trades net <= 0;
  lag: entry and exit one trade date later (signal at t, fills at t+1 settlements) net <= 0.
  Reported, not gates: cell H; the paper's window 2007-2011 (canary: about 82 short / 42 long trades, short ~+$650
  unhedged); basis summary 2006-2011 against the paper's Table 1 (front basis mean +0.14 points, deciles +2.01 /
  -1.40); by year; worst trades (2008, 2018-02, 2020-03); the 0.15 threshold the paper mentions (footnote 13).
- **Expected size:** unhedged ~+$650 short / ~+$1,040 long per trade in 2007-2011; halved ~+$400 per trade, on a
  contract of ~$15-25k notional (~2 % of notional per 5-day trade). **Power:** signal-free sd of the 5-day unhedged
  front-VX P&L over all start dates, recorded before the run.
- **One-time test:** rule fixed before any test data, only after a development pass.
**I-113 power (2026-11-18, before the run, signal-free):** 199 monthly VX contracts 2005-01 .. 2021-10 (archive +
per-contract files; archive files for 2018 stop on 2018-02-23, so settlement dates come from Cboe's file names, all
within 2 days of the exchange rule). 5-day front-VX P&L over all 3,695 start dates 2007-2021: sd $2,673 per contract;
at ~350 trades se $143, t 3 needs ~$430 net. The halved paper size (~$400) gives t ~2.8: pass chance ~35-45 %.
**I-113 development result 2026-11-18 (one look, `research/screens/2026-11-18_i113_vix_basis_screen.py run`):
KILLED on t.** 359 trades 2007-01 .. 2021-09 (no missing front settlement): cell U net +$383 per contract (gross
+$443), t 2.19 < 3.0; every other gate passes: halves +$666 (2007-13) / +$148 (2014-21, t 0.59), doubled cost +$323,
without the 2 best +$258, short +$433 (285 trades, t 4.40), long +$191 (74, t 0.25), lag 1 day +$382. Reported: H hedged
+$328 (t 2.69); paper window 2007-2011 short U 84 trades +$716 (paper 82, ~$656), H short +$555 (paper $539), H long
37 trades +$1,108 (paper 42, $908): the paper reproduces on Cboe settlements. Basis canary 2006-2011 (front >= 10
days, not the paper's nearest contract) +0.40 points. By year U: 2014-2016, 2018, 2019 negative; worst trades are
longs in crashes (2020-03-19 -$20.5k, 2008-11-20 -$13.1k) and 2018-02-05 (-$8.2k). Short leg by half: +$632 (t 3.73)
/ +$276 (t 2.42); long leg +$782 / -$400. Read: the roll premium is real and the paper's numbers hold in its window,
but it roughly halved after publication and the long leg is crash noise. No rescue on development data.

### I-114 VIX futures roll, short leg only: one independent check (2026-11-18, after I-113; family `vix_basis`, 2nd hypothesis; rule fixed before any test data)
Auto decision 47. The short leg is the economic core of I-113 (ETPs and hedgers roll long VX in contango; Chan's
-50 % a year roll), the long leg is crash noise. It was picked after seeing I-113's development result (one of two
legs), so development cannot judge it: it gets exactly one independent check on data not yet downloaded, and is
closed if that fails (lead rule). A pass is a confirmed lead with selection on record, weaker than a
pre-registered pass; it would go to the shelf as a forward log and to HANDOFF (venue VX / VXM, money: the user).
- **Rule (frozen):** I-113 cell U, short side only: each trade date t, front monthly VX with >= 10 business days to
  settlement; daily roll = (settle - VIX close) / business days; roll > +0.10: short 1 VX at t's settlement, cover at
  the settlement 5 trade dates later; one position at a time, earliest re-entry the trade date after an exit; roll
  < -0.10 does nothing. Cost $60 per round trip, doubled $120. Same script and readers as I-113.
- **Test period:** signals from 2021-09-14 (day after development) to the last VIX close in the file (~2026-11-16);
  contracts settling 2021-10 .. 2027-01 as needed. Test data are downloaded only after this card is committed.
- **Power:** development post-publication half: +$276 per trade, sd ~$1,440; ~100 trades in 5 years: se ~$144,
  expected t ~1.9 (pass chance ~60 % if the post-publication size holds).
- **Gates:** (1) net > 0; (2) t >= 1.5; (3) doubled cost > 0; (4) without the 2 best trades > 0. All four = CONFIRMED
  lead; net > 0 with any other gate failing = NOT CONFIRMED (closed); net <= 0 = FALSIFIED (closed). No retest.
  Reported: by year, worst trades (2024-08-05, 2025-04 sell-offs), lag 1 day, H hedged.
**I-114 one-time check result 2026-11-18 (`research/screens/2026-11-18_i113_vix_basis_screen.py test`): FALSIFIED.**
95 short trades 2021-09-14 .. 2026-11-16: gross +$30 per contract, net -$30 (t -0.22); doubled -$90; without the 2 best
-$98; lag 1 day -$164; H hedged -$66. By year U: 2021 -2.1k, 2022 -2.8k, 2023 +4.0k, 2024 -6.4k (7 trades), 2025
+3.9k, 2026 +0.6k. Data fix found in the test run: Cboe's VIX file lists US holidays from 2022 on (no VX settlement);
they were counted as trade dates; the fix (trade dates = VX settlement dates, as the card says) changed 96 trades
-$23 (t -0.17) to 95 trades -$30; development unchanged. Read: the VX roll premium in this rule shrank from +$632
(2007-13) to +$276 (2014-21) to ~0 gross (2021-26). Family `vix_basis` closed (auto decision 48). Telegram sent.

### I-115 S&P GSCI roll front-running in energy calendar spreads (2026-11-18; ledger HV-T0007 data gap closed by EIA strips; new family `index_roll`, venue NYMEX calendar spreads (goal 2), not FTMO; rule fixed before any EIA data is read)
Mechanism: commodity index funds (S&P GSCI, BCOM, USO and peers) must sell the held contract and buy the next on fixed
business days 5-9 of each month (20 % a day); a forced, dated counterparty. Front-runners take the same spread
earlier and unwind into the roll. Source read in full by Opus: Mou 2010, "Limits to Arbitrage and Commodity Index
Investment: Front-Running the Goldman Roll" (CFTC study / SSRN 1716841): 2000-2010 energy portfolio, Strategy 1
(build 20 % a day 10..6 business days before the first roll date, unwind 20 % a day over the roll days) ~4.4 % a year
unlevered, Sharpe 2.2; 1980-1999 (no index money) ~0; control group of non-index commodities ~0. Counter-evidence
(scout 2, not read): Marechal 2021 finds no systematic roll-day effect later. Label PUBLISHED, sample 2000-2010
inside development; 2011-2021 is post-publication. Prior ~15 %.
- **Data:** EIA daily futures settlements, contracts 1-3: WTI CL (RCLC1-3), NY Harbor No. 2 heating oil / ULSD HO
  (EER_EPD2F_PE1-3), RBOB RB (EER_EPMRR_PE1-3, 2005-10+), Henry Hub NG (RNGC1-3, 1994+). Business days = dates with a
  CL contract 1 price. Development months 2000-01 .. 2021-08 (Sept 2021 roll ends after 2021-09-13); EIA's series end
  2024-03, so the test can only be 2021-10 .. 2024-03.
- **Contract the index holds in month M:** delivery M+1; it rolls into M+2 (Mou's example: February, March -> April).
  EIA position of delivery month D on date d = 1 + number of delivery months D' < D whose last trade date >= d. Last
  trade date of D: CL 3 business days before the 25th of D-1 (25th not a business day: before the business day
  preceding it); HO, RB the last business day of D-1; NG the 3rd last business day of D-1. Positions > 3: skipped.
- **Trade (Strategy 1, gated):** roll days R1..R5 = business days 5..9 of month M. Tranche k (1..5): at the close
  of business day R1-11+k (10..6 business days before R1) short delivery M+1, long delivery M+2, equal quantity;
  close it at the close of Rk. Return = (short leg gain + long leg gain) / mean of the two entry prices. Commodity
  month = mean of its 5 tranches; energy month = mean of the commodities with data.
- **Cost:** 3 bp of the collateral per tranche round trip (spread instrument ~1 tick plus fees; Mou: CL bid-ask ~1 bp);
  doubled 6 bp.
- **Gated statistic:** energy portfolio net bp per month, t over months (no overlap: one roll per month).
- **Kills (one-sided, t 3.0):** net <= 0; t < 3.0; halves 2000-2010 / 2011-2021 not both > 0; doubled cost <= 0;
  without the 2 best months <= 0; breadth: CL net <= 0 or fewer than 3 of 4 commodities net > 0.
  Reported, not gates: Strategy 2 (5..1 days before R1, 5-day hold), placebo 1986-1999 (pre-index), by commodity,
  by year, a placebo window (the same trade 10 business days later, after the roll).
- **Expected size:** Mou energy Strategy 1 ~37 bp per month; halved ~18 bp; post-2010 likely less. **Power:**
  signal-free sd of the same spread trade over other windows, recorded before the run.
- **One-time test:** rule fixed before test data, only after a development pass (test window ~30 months: power-sized
  gates or a combined estimate).
**I-115 power (2026-11-18, before the run, signal-free):** EIA strips to 2021-09-13 (CL 1983+, HO 1980+, RB 2005-10+,
NG 1994+; HO has ~8 % blank days since 2000, those commodity-months are skipped). Mapping check at 2000-2021 expiries:
the mapped delivery month moves like a normal day for CL / RB / NG (HO's curve is too flat to tell). sd of the same
10-day spread trade started at R1 or later: 175 bp per energy-month; 260 months: se 10.9, t 3 needs ~33 bp net. Mou's
~37 bp halved (~18) gives t ~1.7: pass chance ~10-15 %. Run anyway: one cheap look, and it closes HV-T0007.
**I-115 development result 2026-11-18 (one look, `research/screens/2026-11-18_i115_gsci_roll_screen.py run`):
PASSED every development gate (mechanically).** 245 energy-months 2000-01 .. 2021-08: gross +29.1 bp, net +26.1
(t 3.37); halves +51.9 (t 3.83) / +2.5 (t 0.33); doubled +23.1; without the 2 best +18.4; CL +15.2 (t 1.19), HO +0.4,
RB +4.6, NG +28.2 (t 2.47). Reported: S2 +9.6 (t 1.96); Mou's window 2000-2010-03 +55.8 (Mou ~37); the same trade 10
days later (after the roll) -44.6 (t -4.99); placebo 1986-1999 +20.1 (t 1.38), but CL -14.8 and NG +135.4 (t 3.79,
before index money). By year: 2000-2006 large, 2007-2021 near zero. Missing commodity-months: CL 30, HO 85, RB 89
(incl. before 2005-10), NG 51. Read (Opus): the gates pass, but the edge sits in 2000-2006 and the post-publication
half is ~0; NG's pre-index placebo says part of it is NG's own expiry-cycle pattern, not index pressure.
**I-115 one-time test, rule fixed before any test data (2026-11-18, auto decision 50):** frozen Strategy 1 as above,
months 2021-10 .. 2024-03 (EIA's series end 2024-04), ~30 months. Development sd ~121 bp per month: se ~22, so the
gates are power-sized as for I-109: (1) test net > 0; (2) test t >= 1.5; (3) test doubled cost > 0. All three =
PASSED; net > 0 with t < 1.5 = NOT CONFIRMED; net <= 0 = FALSIFIED. No retest. Expected: t ~1.2 at the development
size, ~0.1 at the post-publication size: pass chance ~10-25 %. A pass would still need a futures venue (the user).
**I-115 one-time test result 2026-11-18 (`research/screens/2026-11-18_i115_gsci_roll_screen.py test`): FALSIFIED.**
30 months 2021-10 .. 2024-03: gross -18.5 bp, net -21.5 (t -1.13), doubled -24.5; CL +1.7, HO -19.3, RB +8.8, NG -78.4.
By year 2021 +1.0, 2022 -22.3, 2023 +1.7, 2024 (3 months) -133.6. The same trade after the roll -5.2. With the
development second half (+2.5 bp), the front-running edge Mou found in 2000-2010 is gone. Telegram sent. No retest.
**I-109 venue diagnostic on 10-year Treasury futures (2026-11-18, auto decision 53; not a new look, the test is
spent; `research/screens/2026-11-18_i109_zn_futures_check.py`):** Yahoo continuous front contract ZN=F daily closes
2000-09 .. 2026-11, same window and excess statistic. Development 251 months (2000-10 .. 2021-08): ZN excess +19.2 bp
of price per month-end (t 4.63), raw +18.1; DGS10 over the same months +23.6; correlation 0.96; ZN earns ~0.8x the
DGS10 figure (ZN's duration ~6-7 vs 8.5). Test months 2021-10 .. 2026-10 (61): ZN excess +20.6 (t 2.36), raw +13.1
(t 1.83). Contract-roll days (> 150 bp) fall inside a window in 1 month per period; without them the result holds.
Feb / May / Aug / Nov (futures roll and delivery months) +20.0 vs others +19.2: no roll artefact. Size: ~$230 gross per
ZN contract per month-end (1 bp of price ~ $11.5), ~$210 after ~2 bp (1 tick + fees). The futures venue captures the
effect; ZN or the 1/10-size micro 10-year (if listed by the broker) is the natural instrument (HANDOFF Open 1, money: the user).

### I-116 Primary-dealer Treasury inventory price pressure (2026-11-18, data scout + harvest HV-T0129-1; family `rates_dealer`; PARKED before any data)
Mechanism: dealers charge a concession to hold inventory; large net long inventory should lift yields temporarily.
Source read by Opus: Mixon & Tuzun, FEDS 2018-065 (full text): a Nelson-Siegel model with weekly dealer DV01 finds a
transitory, same-week price-pressure effect ("dealers ... typically short Treasury exposure during the 2001-2013
period ... decreased 10-year Treasury yield by nearly 5 basis points, on average"); partly confidential CFTC data. No
forward-looking (next-week) size is published. Free data: NY Fed primary dealer statistics, weekly from 1998, released
about a week after the Wednesday they describe. Power: 10-year weekly price sd ~110 bp; ~1,000 development weeks: se
~3.5 bp, t 3 needs ~10 bp a week net, against a published total level effect of ~5 bp (not per week). PARKED (no
published predictive size; far below power). Revisit only with a source that reports a next-week effect.

### I-117 13F "best ideas" of institutional managers (2026-11-18, data scout: SEC 13F data sets 2013-Q2+; family `share_13f`; CLOSED on power before any data)
Mechanism: the stock a manager overweights most against the market is his highest-conviction pick. Source (abstract via
search, not the full text): Cohen, Polk & Silli, "Best Ideas": best ideas beat the market by ~2.8-4.5 % a year
(1991-2005, strongest in illiquid stocks). Halved ~1.5-2 % a year. Development 2013-Q2 .. 2021 is ~100 months after the
45-day filing lag; a best-ideas book's monthly tracking error ~2-3 %: se ~0.25 % a month, t 3 needs ~9-11 % a year.
CLOSED on power without a look (needs ~5x the halved published size).

### I-118 COT hedging-pressure level premium in US commodity futures (2026-11-18, futures data scout; family `futures_hedging_pressure`; PARKED on power (M4) before any data)
Mechanism (PUBLISHED): hedgers who are net short pay speculators a premium to carry the risk (Keynes; Bessembinder 1992;
De Roon, Nijman & Veld 2000; Kang, Rouwenhorst & Tang 2020). Data: CFTC COT free from 1986 (weekly, released Friday);
prices only as Yahoo continuous front series (roll gaps) or the EIA energy strips; per-contract history is not free.
Size: an energy study (secondary snippet, not opened) ~7.6 % a year; halved ~3.8 %. A long-short sort over ~25
markets has an sd of ~10-12 % a year (estimate): t ~1.4-1.7 over 2000-2021. c ~0.02 (M4 passes), pass chance < 10 %:
PARKED, not closed. Also known as a commodity factor next to carry and momentum (crowded).
I-74 (hedger position-change reversal) re-checked under M4 the same day on a futures venue: se ~15 bp per 20 days,
t 3 needs ~45 bp vs ~11 halved: PARKED.

### I-119 USO roll front-running (2026-11-18, futures data scout; family `index_roll`; no look: covered by I-115)
Kumar & Venkataraman (snippet only): crude oil ETFs pay ~30 bp for their roll trades. USO rolled CL over 4 days about two
weeks before expiry, inside I-115's window (business days 5-9) on the same CL calendar spread, which I-115 tested and
its one-time test falsified. Not an independent hypothesis; recorded, not screened.

### I-120 FX speculator positioning turn from CFTC COT (AC ch.9, 2026-11-18; new family `fx_cot_positioning`, venue FTMO FX CFDs (goal 1); PARKED on power (M4) before any data)
Donnelly (AC ch.9 › Positioning): an extreme non-commercial net position in a currency's CME future that has started to
turn marks a crowded trade that may unwind; he trades the turn, never the level alone (positions can stay extreme for
months). M11 allows a look: COT is a new non-price data set for the FX CFDs (futures scout 2026-11-18).
Causal graph (T-21): X = change of speculators' net position from an extreme, Y = next weeks' FX return, M = crowded
speculators forced to cut (stop-outs, risk limits); confounders: trend (momentum in the same pair), rate news (carry);
placebo: the same turn in a non-extreme position must show nothing.
Power (M4), before any data: c = round trip (~1.5 bp + ~0.5 bp swap a week) / weekly sd of a major (~130 bp) ~0.015 <
0.03. Published effect: Klitgaard & Weir 2004 (NY Fed EPR, 1993-2003): weekly position changes track 30-45 % of the SAME
week's move but do not predict the next week. Cross-asset "speculative pressure" (net position vs its past-year average,
84 futures incl. 11 currencies, 1992-2018; secondary summary, CXO Advisory, UNVERIFIED): gross Sharpe ~0.55 a year, works
for currencies. Halved ~0.27; on ~15 development years expected t ~1.05, two-sided M9 threshold t 3.3: pass chance ~1 %
< 15 %. PARKED, not closed: reopens only on a primary source with an FX-only Sharpe >= ~1.2 gross or a much longer
sample. No data read.

### I-121 Refinery crack-spread carry and trend on energy futures (AFTS S29, 2026-11-18; new family `energy_crack`, venue NYMEX CL / RB / HO futures (goal 2), not FTMO; PARKED on power (M4) before any data)
Carver (AFTS S29): an industry-weighted gasoline / crude / heating-oil triplet traded as one synthetic instrument with
carry (60-day smoothed curve slope) or EWMAC16,64 trend; Jumbo-portfolio net Sharpe carry 0.62, trend 0.46, but
correlation with the outright crude rule 0.75 / 0.92 (largely an oil bet). The exact legs and unit conversion did not
survive the extraction. Causal graph (T-21): M = refiners hedging margins and storage carry (convenience yield),
confounder = the crude level / crude carry itself (control: outright CL carry); placebo: a time-shifted curve slope.
Power (M4), before any data: EIA strips 1-4 hold RB only from 2005-10 (16 development years; no RB in the test strips).
c = round trip of three legs (~3 ticks each) / monthly sd of the crack well under 0.03. Halved published Sharpe 0.31
(carry) -> expected t ~1.24 over 16 years vs t 3.0: pass chance ~4 % < 15 %. PARKED, not closed. Calendar spread and
butterfly variants (AFTS S30: WTI spread carry 0.27, butterfly -0.02 / -0.37) are weaker: no card. No data read.

### I-122 S&P 500 index additions and deletions, price pressure (ER 5.2.6, 2026-11-18; new family `share_index_change`, venue M13 real US shares; CLOSED on published decay before any data)
Ilmanen (ER 5.2.6, Shleifer 1986, Wurgler-Zhuravskaya): index funds must buy additions and sell deletions, so prices
jump and the jump is larger without close substitutes. Forced counterparty, clean causal story (T-21: M = index
trackers; placebo = migrations from the S&P MidCap 400, where MidCap trackers sell what S&P 500 trackers buy).
Closed before any data: Greenwood & Sammon, "The Disappearing Index Effect" (J. Finance 80(2) 2025, NBER w30748):
addition abnormal return 7.4-7.6 % in the 1990s, under 1 % (0.8 %) in 2010-2020; deletions -16 % in the 1990s,
-0.6 % / +0.1 % in 2010-2020; cause: >70 % of additions are MidCap migrations (offsetting flows), cheaper liquidity.
Our share data starts 2015, inside the dead decade. Not reopened unless a non-migration subset with a published
post-2010 effect turns up.

### I-123 Cross-sectional FX carry on FTMO pairs with the real swap (ER 13.2-13.3, AFTS S10 / S20, 2026-11-18; family `fx_carry`, venue FTMO FX CFDs (goal 1); PARKED on power (M4) before any data)
Rank the FTMO FX pairs by carry (the CFD long-minus-short swap is the carry after FTMO's markup), long the top 3,
short the bottom 3, weekly or monthly, volatility-scaled. Mechanism: compensation for crash risk (carry unwinds),
not a forced trade. M11 would need the rate history as the non-price data (FRED policy / 3-month rates).
Power (M4), before any data: published G10 carry Sharpe 0.61 gross 1983-2009 (ER 13.2), much lower after 2008;
Carver's median FX carry instrument 0.30 net (AFTS S10). Halved ~0.3; development ~2008-2021 (13 years): expected
t ~1.1 vs 3.0, pass chance ~3 %. FTMO's swap markup cuts the carry further. PARKED. Ledger HV-T0049-1 / HV-T0103-1
(same family, needs_data) are covered by this card.

### I-124 Spin-off forced selling and rebound on real US shares (EI pp.308-309, 2026-11-18; new family `share_spinoff`, venue M13 real US shares; OPEN: primary-source size and an event list first, no data read)
Pedersen (EI pp.308-309, event-driven chapter): a spun-off subsidiary lands in portfolios of holders who do not want
it (index funds of the parent's index, mandates that cannot hold a small cap, income funds without a dividend), so it
is sold in its first weeks regardless of value; event-driven funds buy after the dump. Forced counterparty, the
same type as I-122 but without the MidCap-migration offset that killed the index effect.
Causal graph (T-21): X = days since the spin-off's first regular-way trade, Y = return vs a size / sector match,
M = mismatched holders' selling; confounders = small-cap and new-listing returns (control: matched non-spin-off IPOs
and small caps); placebo: carve-out IPOs (no inherited holders) should show no early dip.
Evidence so far (search 2026-11-18, all weak): a 2000-2022 thesis (Copenhagen Business School, not peer reviewed)
reports -1.7 % abnormal over the first 14 trading days and +12.9 % over 12 months; the older literature (Cusatis
et al. 1993, McConnell et al. 2004) found long-run excess returns. No peer-reviewed post-2010 size found.
Power sketch (M4, before any data): ~30-40 US spin-offs a year, ~200 in 2015-2021 with data. Short-run rebound at a
halved 0.85 % vs ~12 % 14-day residual sd: expected t ~1.0 (PARK level). Long-run drift halved to 6.5 % a year
vs ~40 % sd: t ~2.3 before cross-correlation, pass chance maybe 20 %. Next step (research): a peer-reviewed post-2010
source and a spin-off date list (Alpaca corporate actions or SEC Form 10 filings); then the M4 check decides.
