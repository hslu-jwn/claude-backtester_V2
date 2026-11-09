# Candidate discovery ledger

Updated: 2026-11-03  
Scope: territories outside the frozen 62-item backlog. This is a research-priority ledger, not a
strategy registry or authorization to test.

## Admission gates

A territory may advance to a research record only when all of the following are true before local
outcome access:

1. **Independent estimand:** the event, prediction, and direction are not an alias of a frozen,
   failed, parked, or already-counted family.
2. **Transferable primary evidence:** at least one opened primary source tests the same time-series
   mechanism on a reasonably transferable market; cross-sectional, execution-only, or volatility-
   only evidence is not enough.
3. **Causal supported inputs:** every signal field, calendar, timestamp, and transform is knowable at
   decision time and either supported now or named as a blocking contract dependency.
4. **Executable horizon:** evidence remains after the platform's causal entry latency and does not
   rely on an unobservable same-bar path or privileged sub-minute access.
5. **Cost feasibility:** an authoritative or deliberately conservative round trip leaves plausible
   room; passing this gate means edge unknown, not validated.
6. **Modern stability:** an untouched later sample is not adverse, and the finding is not dominated
   by one era, market, crisis, or selected subgroup.
7. **Bounded multiplicity:** one primary rule and rejection gate can be frozen without searching
   signs, clock buckets, thresholds, assets, or rescue filters.

Failure of any gate parks or rejects the territory. Local parameter exploration is not permitted to
repair a failed admission gate.

## Screened territories

| Territory | Primary evidence | Failing gate(s) | Disposition |
|---|---|---|---|
| Same-clock intraday recurrence | Heston, Korajczyk, Sadka (2010): strong next-day same-half-hour continuation across 1,715 NYSE stocks; about 3 bp winner-minus-loser spread | Cross-sectional relative-stock mechanism, unsupported constituent/bid-ask data, effect comparable to trading spread; no single-instrument time-series evidence | Reject for current platform; no clock/lag grid |
| Scheduled macro-announcement response | Andersen et al. (2003), Ederington–Lee (1995), Frino–Hill (2001), Erenburg et al. (2006): signed surprises move FX/futures rapidly | Requires point-in-time consensus/actual/revision data and sub-minute/event-cost execution; M1 price-sign rule aliases R-2026-004 after most adjustment | Blocked data/microstructure territory; no strategy or filter |
| Europe-open U.S. index-futures drift | Boyarchenko, Larsen, Whelan (2023): 1.48 bp/day gross ES drift in 1998–2020 | Same authors find 2021–2025 flat across ES/NQ/YM; no modern gross margin; nearby-hour/regime selection would be rescue search | Reject as current candidate; retain historical anomaly and decay |
| Cross-market intraday lead–lag | Stoll–Whaley (1990), Huth–Abergel (2014), Alsayed–McGroarty (2013), Alemany et al. (2020): futures price discovery and very short leader/lagger relations | Slower effects mainly reflect stale cash indexes; modern opportunities last hundreds of milliseconds and naïve market orders lose the spread; supported CFD proxies are not arbitrage legs | Reject for M1 platform; no pair/lag/regime grid |
| Derivatives-expiration intraday effect | Golez–Jackwerth (2012), Stoll–Whaley (1991), Xu (2014), Caporale–Plastun (2023): settlement pinning, opening/closing reversals, and daily witching returns | Strongest effect needs option strikes/open interest and serial-expiration settlement; quarterly S&P pinning and Swedish price effects are null; recent direction uses excluded open-to-close execution and omits all costs | Reject for current platform; no midday, strike-proxy, or expiration-class grid |
| Pre-FOMC equity drift | Lucca–Moench (2015): about 49 bp over the 24 hours before 138 scheduled meetings; Kurov–Wolfe–Gilbert (2021): matched S&P futures extension | Original estimand includes overnight and the excluded opening; 2011–2019 mean is 4.7 bp versus 3.8 bp ordinary days and the effect disappears after 2015; no source-matched day-flat subwindow or cost margin | Reject as current candidate; no clock, meeting-type, or VIX rescue grid |
| Pre-holiday equity premium | Ariel (1990): 1963–1982 daily and hourly market premium; Ko–Yang (2024): 1983–2019 out-of-sample extension | Opening and last hour contain a material share of the original return; large-firm premium becomes insignificant, especially after 1990, and survives only among small firms; no modern index-CFD cost margin | Reject for index proxies; no holiday, early-close, or interior-hour grid |
| Turn-of-the-month equity premium | McConnell–Xu (2008), Han–Han–Tian (2025), Kayacetin (2026): daily four- and eight-day calendar windows | Classic U.S. four-day effect disappears after 2001 while a broader international eight-day/risk-conditioned definition is favorable; all are multi-day close returns with no allowed interior-session localization or executable-cost test | Reject as day-flat candidate; no window, risk-state, or clock grid |
| London gold benchmark leakage | Caminschi–Heaney (2014), Crain–Hoelscher–Jones (2020), FCA (2018): old private fixing leak and post-2015 electronic-auction reform | Four-minute edge uses contemporaneous trades to infer unpublished fixing direction, overlaps the failed benchmark-fix family, predates a structural reform, and has no modern causal OHLC/cost-adjusted rule | Reject; no AM/PM, leak-proxy, breakout, or reversal grid |
| U.S. Treasury auction price pressure | Lou–Yan–Zhang (2013), Smales (2021), Fleming–Liu–Nguyen (2026): Treasury prices weaken before auctions and recover after them; modern one-minute evidence excludes the result jump | No Treasury or bond-futures instrument/cost model in V2; no primary evidence transfers the signed effect to a supported proxy; auction calendar is not contracted | Promising but capability-blocked; no proxy, maturity, or window grid |
| EIA petroleum-inventory releases | Ye–Karali (2016), Rousse–Sévi (2019), Alturki–Kurov (2022), Wen et al. (2023), EIA: signed surprise response, sequential-report predictability, and EIA-day late momentum | Direction needs consensus/API/EIA fields; multi-hour reversal is surprise-conditioned and old; OHLC-only predictor targets the excluded final half-hour; event-bar proxy would overlap R004 | Reject; no surprise-proxy, component, continuation/reversal, or exit-time grid |
| Natural-gas storage announcement-day short | Prokopczuk–Wese Simen–Wichmann (2021), Chen (2023), EIA: fixed two-hour NATGAS short historically earns 12% annualized net with Sharpe 1.76 | Original effect is absent in 2014–2018; independent 2008–2019 announcement-day coefficient is insignificant; pre-release leg appears only on ex-post positive surprises | Reject for modern instability; no era, season, surprise, or window rescue grid |

| High-dimensional factor-zoo market timing | Aleti–Bollerslev–Siggaard (2025): 272 lagged high-frequency portfolio returns predict 15-minute aggregate-market returns; reported SPY strategies are positive after quoted-spread and borrow costs | Requires synchronized constituent/factor portfolios, ETF execution, ML and jump decomposition; opening weight is initialized from an overnight long position; evaluation ends in 2020 | Park as unsupported cross-sectional-data territory; no single-index OHLC proxy, local grid, or draft |

## Existing constrained territories

- R-2026-004 is the sole final shock-response falsification and awaits V2 calendar/result-map
  confirmation plus independent review.
- R-2026-005 is a diagnostic design with no supported study route and no strategy semantics.
- The frozen 62-item backlog is mapped exactly once in
  `REMAINING_DAY_FLAT_BACKLOG_OVERLAP_MAP.md`; use `tools/check_backlog_coverage.py`.
- Parked ETF momentum and final-30-minute continuation drafts remain capability/data exceptions,
  not active candidates.

## Next search rule

Prefer an economically identified event with a single-instrument time-series prediction and a
holding horizon comfortably longer than one M1 bar. Exclude opening/gap, closing/final-30-minute,
generic shock continuation/reversal, raw-price mean reversion, zones, and post-result filters unless
new primary evidence is materially independent of those families. The bounded post-saturation
update and exact transfer audit are in `R006_POST_SATURATION_UPDATE_2026-11-03.md`.
