# M15 candidate triage (no runs)

Date: 2026-11-09. Scope: 18 M15 drafts + INTRADAY_H1_SHOCK_RESPONSE in `research/candidates/`. Read-only paper triage from the JSON specs, `research_registry.csv`, the R007-R024 review packets and the I-30/I-33/I-40/I-47/I-48/I-52/I-62 evidence checks. Nothing was executed.

## Method

- Reference (R014, `docs/research-log.md` 2026-11-06): gross about +0.025 R/trade, costs about 0.21 R/trade at a 1-ATR M15 stop (net -3,925 R on 17,673 trades = -0.22 R/trade; gross -162 R). So cost_R ~ 0.2 / stop_in_M15_ATR: 0.2 R at 1x, 0.1 R at 2x.
- All M15 drafts: 6 FX pairs (EURUSD GBPUSD AUDUSD NZDUSD USDCHF USDCAD), London 09:00-12:45 or 13:45 signal bars (16 or 20 bars/day), market order at signal close, ATR stop (ATR96 of prior M15 bars; SHOCK uses ATR20 M15), no target, time exit 15-120 min, flat by 15:00, no swap.
- Trades/year = 6 symbols x 260 days x 16 or 20 bars = 25,000-31,000 symbol-bars/yr, times a rough event frequency of the rule (generic M15 FX tail, run, cross and oscillator frequencies, not V2 data), minus overlap (each cell holds one position per symbol; a 30-60 min hold removes 1-3 bars). Cross-check: R014 had ~15,000 trades/cell in 6.7 dev years = ~2,300/yr, about 8 % of its bars. Order-of-magnitude only (+-2x).
- Annual cost drag in R = trades/yr x cost_R (2,000 x 0.2 = ~400 R/yr, which the gross edge must beat).
- "Best supported gross edge": strongest external or in-house evidence for a positive gross move per trade. For every M15 draft it is "none" (registry evidence_class: legacy_book_context_only, adjacent_contrary_only, adverse prior, monthly/daily horizon transfer, equity-only). The only number available is R014's own measured +0.025 R (FADE mode), the closest-shaped rule.

## Table

Stop = ATR multiple of M15. Hold in minutes. cost_R at the stop(s) the grid offers.

| Candidate (R) | Signal | Stop | Exit / hold | Cells | Trades/yr (all symbols, one cell) | cost_R | Best supported gross edge | Verdict |
|---|---|---|---|---|---|---|---|---|
| M15_SHOCK_RESPONSE (007) | M15 return / prior 96-bar MAD scale >= 2, 3, 4; continue or reverse | 1 or 2 x ATR20 | time 15/30/60/120 | 48 | z2 ~1,500; z3 ~500; z4 ~250 | 0.2 / 0.1 | none; adverse prior I-61/R004 (H1 shock test: no robust edge, top 1 % of events) | COST_INFEASIBLE (M15 variant of tested I-61) |
| M15_COMPRESSION_BREAK (008) | median TR of last 4/8/16 bars / ATR96 <= 0.5/0.75, close outside block; follow or fade | 1 or 2 | 30/60/120 | 72 | ~900 (0.5) to ~3,000 (0.75) | 0.2 / 0.1 | none; I-33 check: no direct study, opening-range evidence (Holmberg 2013) is an opening effect | COST_INFEASIBLE (ORB/squeeze-adjacent) |
| M15_WICK_REJECTION (009) | range >= 0.5/1.0 ATR, wick ratio >= 0.4/0.6, close location; follow or failure | 1 or 2 | 30/60/120 | 96 | ~300 to ~2,000 | 0.2 / 0.1 | none; legacy book context | DUPLICATE_OF_FAILED_FAMILY (candle geometry = no-wick family; I-62: 0.4 % of 4,608 variants positive, "do not reopen through direction reversal") |
| M15_CLOSE_STREAK (010) | N = 3/5/7 same-sign closes + displacement >= 0.5/1.0 ATR; continue or exhaust | 1 or 2 | 30/60/120 | 72 | N3 ~1,900; N5 ~400; N7 ~60 | 0.2 / 0.1 | none; legacy | DUPLICATE_OF_FAILED_FAMILY (R014 close-sign path) |
| M15_TREND_PULLBACK (011) | 8-change move >= 1 ATR, then 1-2 strict opposite closes; resume or fail | 1 | 30/60 | 8 | ~2,000-5,000 | 0.2 | none; legacy | DUPLICATE_OF_FAILED_FAMILY (R014 path + trend following) |
| M15_MEDIAN_CROSS (012) | close crosses 8/16-bar rolling median; follow or fade | 1 | 30/60 | 8 | ~3,500 | 0.2 | none; adjacent contrary (intraday momentum), I-58 adverse | DUPLICATE_OF_FAILED_FAMILY (R014 shape, price-location variant) |
| M15_OUTSIDE_ENVELOPE (013) | outside bar (higher high and lower low), range >= 1.0/1.5 ATR, close beyond one extreme | 1 | 30/60 | 8 | ~350 (1.5) to ~900 (1.0) | 0.2 | none; legacy | COST_INFEASIBLE (breakout-bar / sweep-adjacent) |
| M15_ROUND_NUMBER_CROSS (015) | close crosses exactly one 50-pip level | 1 | 30/60 | 4 | ~2,000 (avg bar move 4-5 pips / 50) | 0.2 | none; I-30 check: Osler 2000 is published-level S/R in 1996-98 quotes, not a profitable OHLC rule; annotation only | COST_INFEASIBLE |
| M15_PRIOR_SESSION_EXTREME_CROSS (016) | first close outside previous London day high/low; follow or fade; 09:30-13:45 | 1 | 30/60 | 4 | ~1,000 (max 1 per symbol-day, ~65 % of days) | 0.2 | none; daily-paper adaptation | DUPLICATE_OF_FAILED_FAMILY (session sweep / previous-day extreme) |
| M15_EFFICIENCY_TRANSITION (017) | 8-change efficiency ratio rising through 0.75; follow or fade | 1 | 30/60 | 4 | ~500 | 0.2 | none; legacy | DUPLICATE_OF_FAILED_FAMILY (R014 path-state) |
| M15_RSI_EXTREME_ENTRY (018) | first Wilder RSI14 cross into >70 / <30 | 1 | 30/60 | 4 | ~700 | 0.2 | none; legacy; I-40: oscillator filters add nothing (SET50 daily) | DUPLICATE_OF_FAILED_FAMILY (R014 path-state) |
| M15_USD_BREADTH_TRANSITION (019) | 5 of 6 pairs agree on 4-change USD direction (transition); basket of 5-6 legs | 1 per leg | 30/60 | 4 | ~100-200 baskets = ~500-1,200 legs | 0.2 per leg | none; monthly paper, horizon not transferable | COST_INFEASIBLE |
| M15_FX_RELATIVE_STRENGTH_RANK (020) | rank 6 currencies on 4-change return; long top-2 / short bottom-2 (or reverse) every signal bar | 1 per leg | 30/60 | 4 | ~1,300-2,600 baskets = ~5,000-10,000 legs | 0.2 per leg | none; monthly momentum transferred to 30 min | COST_INFEASIBLE (highest turnover of the set) |
| M15_EURGBP_RELATIVE_DISLOCATION (021) | z(EURUSD 4-change) - z(GBPUSD 4-change) crosses 2; converge or diverge, 2 legs | 1 per leg | 30/60 | 4 | ~150 pairs = ~300 legs | 0.2 per leg | none; equity-pairs paper only | COST_INFEASIBLE (two spreads per trade, no edge evidence) |
| M15_REALIZED_SEMIVARIANCE_IMBALANCE (022) | intrahour signed semivariance imbalance Q crosses +-0.5; follow or fade | 1 | 30/60 | 4 | ~2,000 | 0.2 | none; commodity daily paper | DUPLICATE_OF_FAILED_FAMILY (R014 path-state) |
| M15_SERIAL_DEPENDENCE_TRANSITION (023) | 12-return lag-1 correlation crosses +-0.30; regime-consistent or inverted | 1 | 30/60 | 4 | ~2,000 | 0.2 | none; record calls FX at 15 min "strongly adverse", expected null | DUPLICATE_OF_FAILED_FAMILY (R014 path-state) |
| M15_SMA_CROSS (024) | SMA4/SMA16 cross; follow or fade | 1 | 30/60 | 4 | ~3,000 | 0.2 | none; equity-index MA evidence only | DUPLICATE_OF_FAILED_FAMILY (R014 shape; trend following) |
| INTRADAY_H1_SHOCK_RESPONSE (004) | completed H1 bar robust z >= 2/3/4 and event move >= minimum cost multiple; continue or reverse; XAUUSD GBPUSD GBPJPY NAS100 US500 | 6 x ATR20 H1 (~12 M15 ATR) | time 1/2/3 h, same day | 18 | z2 ~700; z3 ~300; z4 ~150 | ~0.02 (0.2 / ~12); index and gold spread vs H1 ATR needs a V2 cost check | I-61 (ROADMAP 11.13): NAS100 H1 k4 h2 +0.20 sd trimmed, t 1.7, decaying; elsewhere no robust edge; carried by the top 1 % of events | COST_FEASIBLE_UNKNOWN_EDGE (blocked: no authoritative CFD session calendar; adverse prior) |

The two parked non-M15 drafts (ETF_ABSMOM_12M_LC, US500_FINAL30_CONT) are out of scope.

## Findings

1. No M15 candidate passes the cost screen. At a 1-ATR stop each trade costs ~0.2 R, ~2,000 trades/yr is ~400 R/yr of drag, and no source supports even +0.05 R gross on M15 FX (R014 measured +0.025 R). A 2-ATR stop halves cost_R to 0.1 R, but the R-gross of a given price drift halves too, so cost/edge is unchanged to first order; it rescues nothing.
2. The I-52 screen is one-sided: passing proves nothing about edge. Rejection is justified here because the gross bound is "none or about +0.025 R", far below cost.
3. Lower trade count does not create feasibility: the quietest rules (EURGBP ~300 legs/yr, USD breadth ~500-1,200 legs, efficiency ~500, shock z4 ~250) lose less in absolute R but still pay 0.2 R per trade against no edge.
4. Only the H1 shock candidate has a workable cost profile (~0.02 R, ~150-700 trades/yr) because the stop is ~12 M15 ATR. It is a re-study of I-61 (already counted: no robust edge, NAS100 effect decaying, t 1.7) and is blocked on the missing session calendar.

## Families (differ only by parameters or by the mapping of the same mechanism)

- A. Closed-bar path/run (R014 family, failed): CLOSE_STREAK, TREND_PULLBACK, SERIAL_DEPENDENCE_TRANSITION, EFFICIENCY_TRANSITION, REALIZED_SEMIVARIANCE_IMBALANCE, RSI_EXTREME_ENTRY. All are monotone functions of the last 4-16 M15 returns with the same follow/fade flip, ATR stop and time exit.
- B. Rolling-location cross: MEDIAN_CROSS and SMA_CROSS (differ in smoother and lookbacks only).
- C. Single-bar size/geometry event: SHOCK_RESPONSE (return z), OUTSIDE_ENVELOPE (range >= k ATR plus envelope), WICK_REJECTION (range >= k ATR plus wick/close location). M15 SHOCK is also the same family as INTRADAY_H1_SHOCK_RESPONSE at another timeframe.
- D. Fixed-reference first-cross: ROUND_NUMBER_CROSS (50-pip grid), PRIOR_SESSION_EXTREME_CROSS (previous day high/low), COMPRESSION_BREAK (local block high/low). Differ only in which level is crossed.
- E. Cross-symbol basket of the same 4-change returns: USD_BREADTH, FX_RELATIVE_STRENGTH_RANK, EURGBP_RELATIVE_DISLOCATION. Differ only in how the returns are aggregated.

The 18 M15 drafts reduce to 5 families; the reported cell counts overstate independent trials.

## Build recommendation

Build none of the 18 M15 drafts: ~0.2 R cost per trade against zero supported gross edge; 12 of 18 are mechanically R014 variants or siblings of failed V2 tests (R014, no-wick, session sweep, trend following, ORB); the rest have no supporting evidence; more cells only add multiplicity.

Only INTRADAY_H1_SHOCK_RESPONSE passes the cost screen. It is conditional and low priority: build only once a session calendar exists (or restrict to symbols and hours V2 already models, e.g. GBPUSD and GBPJPY in a fixed London window), and treat it as a falsification re-study of I-61, not a hope.
