# Multi-symbol idea harvest — 2026-11-10

Research shortlist, not strategy specs or evidence of profitability. Twelve independently defined ideas are ranked by the *judged* chance that their gross directional edge exceeds all costs, not by measured results. No backtest was run. All linked pages below were actually opened; access to some publisher pages was denied, so only accessible copies are used. PUBLISHED means the broad phenomenon was published, not that this exact CFD implementation was published. PRACTITIONER means an industry source describes the relationship. SPECULATIVE denotes our extrapolation. All precise thresholds, stops, sizes, and frequency/move estimates below are proposed assumptions, not claims from the sources.

## Common definitions and execution

- Daily bars close at 21:00 UTC on weekdays, constructed from M1; omit weekend stubs. H1 bars close on the UTC hour. At each decision use only fully closed bars for every required symbol. Enter on the first common M1 open after the signal; if no common valid minute within five minutes, skip. No stale prices. Use actual exchange holiday calendars for cash-open ideas. No same-bar hindsight.
- ATR14 is the simple mean of the last 14 complete daily true ranges, including the bar that produced the signal. Skip missing days and require 60 prior aligned observations for rolling spreads; use 120 where specified. Each position has a fixed stop placed at entry. Stops execute with adverse gap/slippage assumptions; timer exits execute at the first common valid minute at or after the deadline. If only one leg can trade, model leg risk and fail the clean-fill sensitivity test rather than assume a synchronous fill. No overlapping baskets of the same idea. When a stop closes one leg, close all remaining legs at their next executable prices. Apply the existing conservative SL-first intrabar rule; M1 cannot resolve the exact ordering of two different symbols' intraminute prices, so add a pessimistic ordering sensitivity. Pair R is net dollar P/L divided by initial combined dollar risk; do not add unweighted per-leg R.
- Cost estimates are **illustrative planning hurdles in bp of gross entry notional**, not measured spreads: major FX round trip 1–2 bp per traded leg; indices 2–6; oil 5–15; metals 5–20; crypto 10–30. They exclude swap/funding unless stated. A 50/50 pair's hurdle is the average of its legs' bp costs on gross notional; two $1 legs cost the sum on a $1-per-leg basis. Measure actual historical symbol/time spreads, commission, slippage, swap and crypto funding before ranking. Illustrative move ranges are **absolute favourable-or-adverse path/relative movement scenarios**, not expected signed gross profit; signed conditional gross expectancy is unknown and may be negative. Estimates of annual trades are order-of-magnitude guesses, not observed counts. Larger absolute moves and wider stops alone do not imply a cost-clearing edge.
- For a spread, use fixed 50/50 gross USD notional, positive-price log spread `s = ln(A) - ln(B)`. Compute z using the most recent 120 *previous* aligned daily spread closes, mean and sample SD. Enter when z crosses from inside to outside ±2; short A/long B at +2 and reverse at -2. Freeze entry mean and SD and exit when the spread crosses that mean, after 20 completed daily bars, or on a leg stop, whichever first. Stop each leg at 1.5 ATR14. Check spread exits on aligned daily closes, not M1 highs/lows. Treat CFDs in common USD P/L using point values and contemporaneous FX conversion, with capital/margin constraints. This is a fixed-ratio hypothesis, not proof of cointegration. Commodity CFD roll adjustments and contract specifications must be investigated before use.

## 1. Weekly currency relative-strength cross — PUBLISHED

**Source:** [Menkhoff et al., Currency Momentum Strategies](https://faculty.washington.edu/ss1110/IF/Sarno%20Currency%20Momentum%20JFE%20%281%29.pdf), full paper opened; [CEPR author summary](https://cepr.org/voxeu/columns/limits-currency-momentum-trading), opened. Paper reports winner-minus-loser excess returns up to 10% yearly in a much broader universe. Authors estimate costs absorb 30–50% in their setting; emerging currencies contribute. Later [Hutchinson et al.](https://repository.adu.ac.ae/items/49b11e04-d4e2-4397-96aa-dac0c017647b), opened abstract, report out-of-sample decay. Neither claim establishes this rule.

**Rule:** Signal on Friday 21:00 UTC from EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD, expressed as USD value of each non-USD currency (invert USD-base quotes). Rank 20-week log returns using 100 completed weekday bars. Buy strongest and sell weakest using both USD legs at equal USD notional; close next Friday 21:00 UTC, or at individual 2 ATR14 stops under common rules. Skip if either signal leg is unavailable; repeat only after prior basket closes. This requires multiple symbols to choose the legs. No carry ranking.

**Mechanism:** Cross-country information diffusion and persistent investor positioning. **Estimate:** ~35–50 basket entries/year; hypothetical 20–150 bp absolute weekly relative move on gross notional vs 1–2 bp round trip plus up to a week of two-leg swap. Gross signed edge unknown. Losses in momentum reversals and the restricted major-currency universe could erase the source effect.

## 2. Monthly country-index relative momentum — PUBLISHED

**Source:** [Country equity return literature review](https://www.mdpi.com/1911-8074/12/4/165), opened, discusses country momentum and sensitivity to index, currency and return construction. No numerical claim transferred.

**Rule:** At 21:00 UTC on the last weekday of each month rank 126-day price returns for US500, NAS100, GER40, UK100, JP225, AUS200; require all six aligned and verified trading availability. Equal USD notional long top and short bottom for one month, 2 ATR14 stop per leg; close on the next month-end decision. Compute USD P/L with contract currency conversion. Signal uses price indices and CFD financing, not total-return indices; US500/NAS100 concentration is a limitation.

**Mechanism:** Relative macro and earnings trends diffuse over months. **Estimate:** 8–12 baskets/year; 100–500 bp absolute relative monthly movement vs ~2–6 bp round trip plus substantial long/short financing and dividends. Signed gross edge unknown; country effects may be dominated by index composition, currency and dividend adjustments.

## 3. WTI–Brent relative-value reversion — PUBLISHED

**Source:** [Commodity pairs and data-snooping review](https://www.jpmcc-gcard.com/wp-content/uploads/2018/05/GCARD-Summer-2018.pdf), opened pp. 77–80. The best Brent–WTI rule reports 17.6% annual excess in sample among hundreds of rules; other out-of-sample results vary and some decay. This selected figure is visibly exposed to data mining and is not this implementation's expectation.

**Rule:** Apply common spread definition to USOIL and UKOIL at daily close, fixed equal gross USD notional; 2 SD entry, frozen mean exit, 20-day timeout, 1.5 ATR stops. Only trade when both series have positive prices, simultaneous valid bars, and documented compatible contract/roll histories.

**Mechanism:** Similar crude products can diverge temporarily due to local supply, transport and positioning; structural infrastructure and grade changes can persist. **Estimate:** 3–15 baskets/year; 50–300 bp absolute spread move vs 5–15 bp on gross notional plus two-leg swap/roll. Unadjusted CFD rolls and April 2020 WTI negative prices make this especially fragile; skip nonpositive prices and investigate gaps, don't silently splice contracts.

## 4. Commodity-currency signal → oil — SPECULATIVE

**Source:** [Chen, Rogoff and Rossi, Can Exchange Rates Forecast Commodity Prices?](https://www.rba.gov.au/publications/workshops/research/2008/rossi.pdf), opened working-paper copy. They report commodity currencies forecast broad commodity price indices and find the reverse less robust. Their macro-frequency finding does not establish USDCAD forecasting this specific oil CFD.

**Rule:** At Friday 21:00 UTC compute five-day return on CADUSD, the inverse of USDCAD. If CADUSD rose at least 0.5%, buy USOIL; if it fell at least 0.5%, short USOIL. Enter only with valid aligned USDCAD and USOIL bars; stop 2 daily ATR14 and exit next Friday 21:00 or stop. No trade inside threshold.

**Mechanism:** FX may incorporate forward-looking commodity demand before physical oil prices. **Estimate:** 15–35/year; 100–500 bp absolute oil move/week vs 5–15 bp plus oil financing/roll. No claimed gross profitability, and the cited study's aggregate target and longer horizon are material differences.

## 5. Gold–silver relative-value reversion — PRACTITIONER

**Source:** [World Gold Council gold vs silver study](https://www.gold.org/goldhub/research/gold-safe-haven-versus-silver-wildcard), opened; discusses common drivers and silver's changing beta, not profitability of ratio reversion. [Pairs-trading limitations](https://arxiv.org/abs/2010.01157), opened, reports declining equity-pairs profitability and unstable tuned parameters.

**Rule:** Apply the common 120-day, ±2 SD log-spread rule to XAUUSD / XAGUSD at 50/50 USD notional, with frozen mean, 20-day timeout and 1.5 ATR per-leg stops. Ratios with a persistent regime shift can keep diverging.

**Mechanism:** Shared monetary exposure can cause temporary relative overshooting, but silver has industrial demand and different volatility. **Estimate:** 3–15/year; 100–500 bp absolute spread move vs 5–20 bp on gross notional plus potentially large asymmetric metal swap. Equal dollar hedge leaves directional exposure; no source claim of profits.

## 6. US growth versus broad equity relative value — SPECULATIVE

**Source:** [Equity pairs trading evidence and instability](https://arxiv.org/abs/2010.01157), opened; concerns individual US equities, not index CFDs. No claimed performance for this pair.

**Rule:** Apply common 120-day spread method to NAS100 / US500 at equal USD notional, ±2 SD entry, fixed mean exit, 20-day timeout and 1.5 ATR stops. Verify matched opening hours, index price treatment, dividends and financing; no entries when either index has a missing close.

**Mechanism:** The indices share broad US risk; large relative price divergences may partially unwind. **Estimate:** 3–15/year; 50–250 bp absolute spread movement vs 2–6 bp plus financing/dividend adjustments. Concentration and structural growth/sector trends can make the ratio nonstationary; do not market-neutral-label the equal-dollar position.

## 7. European index relative-value spread — SPECULATIVE

**Source:** [Country equity return review](https://www.mdpi.com/1911-8074/12/4/165), opened, plus [pairs-trading caveats](https://arxiv.org/abs/2010.01157), opened. Neither establishes GER40–UK100 reversion.

**Rule:** Use common spread recipe on GER40 / UK100, ±2 SD, frozen mean, 20 days maximum, 1.5 ATR stops, 50/50 USD notional. Convert contract P/L to USD and explicitly include GBPUSD and EURUSD exchange effects. Only compute signal when both index and FX prices are current. Validate historical GER40 index membership and dividend conventions.

**Mechanism:** Shared European risk may generate transitory relative divergence; national sector exposure and GBP can also generate persistent differences. **Estimate:** 3–15/year; 75–300 bp absolute spread movement vs 2–6 bp plus swap, dividend and conversion costs. Index price-ratio signal does not eliminate currency risk.

## 8. Dollar breadth → USDCAD — SPECULATIVE

**Source:** [Bank of Canada, commodity prices and CAD](https://www.bankofcanada.ca/2016/03/staff-analytical-note-2016-2/), opened. Its USD multilateral factor has stronger predictive ability than individual commodity factors; its analysis includes contemporaneous relationships, not a guarantee of a lagged executable signal.

**Rule:** At 21:00 UTC daily, calculate one-day USD strength as minus the equal-weight mean daily log returns of EURUSD, GBPUSD, AUDUSD, NZDUSD, plus USDJPY and USDCHF expressed as currency-per-USD with positive signs; all six are required. If four or more of six show USD strength and mean exceeds +0.2%, buy USDCAD; symmetric signal below -0.2% and four votes sells. Exit next daily close or 1.5 ATR14 stop. The target USDCAD is excluded from breadth.

**Mechanism:** Common dollar information may diffuse unevenly into CAD. **Estimate:** 30–90/year; 20–100 bp absolute daily target move vs 1–2 bp plus one rollover swap. Same-day common USD moves may already be fully priced, so directional edge can be zero despite correlation; no published rule or bp profit claim.

## 9. Oil shock → CAD next day — SPECULATIVE

**Source:** [Bank of Canada note](https://publications.gc.ca/collections/collection_2016/banque-bank-canada/FB3-7-2016-2-eng.pdf), opened: it discusses earlier daily predictability but explicitly studies contemporaneous relations, which cannot be traded after the fact. No claimed profit for this delayed rule.

**Rule:** At 21:00 UTC daily calculate USOIL daily close-to-close return. If above +2%, short USDCAD; below -2%, buy USDCAD; otherwise flat. Execute after both bars close, exit next 21:00 UTC or 1.5 ATR14 USDCAD stop. One signal/position at a time. Reject nonpositive oil prices and roll-discontinuity dates.

**Mechanism:** Oil income expectations can affect CAD with a lag, although prompt FX adjustment and common USD factors may absorb it. **Estimate:** 20–60/year; 20–100 bp absolute CAD move vs 1–2 bp plus overnight swap. Gross signed effect unknown; a same-day correlation would be insufficient.

## 10. US closing impulse → next German open — PUBLISHED

**Source:** [Xu et al., Cross-market overnight time-series momentum](https://www.researchgate.net/publication/398174368_Cross-market_overnight_time-series_momentum), opened abstract page; reports US final-half-hour signal predicts next first-half-hour international returns, with positive profits after assumed costs. Original publisher full text was inaccessible. Different instruments, timing and CFD fill assumptions prevent treating this as a replication.

**Rule:** On NYSE regular full sessions, compute US500 return 15:30–16:00 America/New_York. On the next day when both NYSE and Frankfurt have normal sessions, at 09:00 Europe/Berlin buy GER40 if US return > +0.1%, sell if < -0.1%; exit 09:30 Berlin or 0.5 GER40 daily ATR14 stop. No trade if the exact US signal bars or German entry candle are missing. Measure return only after entry, never include the overnight gap.

**Mechanism:** US information may diffuse into German cash-open order flow. **Estimate:** 60–130/year; 10–50 bp absolute 30-minute move vs 2–6 bp and open spread/slippage. Gross conditional edge could be only a fraction of the move; first-open pricing may already incorporate US news. This is cross-market, distinct from the rejected same-index last-half-hour timed hold.

## 11. Gold impulse → silver delayed continuation — PRACTITIONER

**Source:** [World Gold Council](https://www.gold.org/goldhub/research/gold-safe-haven-versus-silver-wildcard), opened; reports one-minute gold-to-silver Granger significance, not trading P/L. The publication pools data through 2026, overlapping the protected test era; no use of its sample as an independent holdout.

**Rule:** At each H1 close, during 12:00–19:00 UTC, calculate XAUUSD one-hour log return. If above +0.5%, buy XAGUSD; if below -0.5%, sell. Enter after both H1 bars close; exit after two hours or 1 daily ATR14 XAG stop. No overlapping trades and no filter based on the future silver return.

**Mechanism:** Silver may react more slowly to information first expressed in gold. **Estimate:** 10–50/year; 20–150 bp absolute silver movement over two hours vs 5–20 bp and potentially elevated event spreads. One-minute statistical causality does not demonstrate a one-hour delayed tradable effect; strong risk the edge is gone before entry.

## 12. BTC impulse → ETH delayed continuation — SPECULATIVE

**Source:** [Chernoff, BTC/ETH price discovery](https://www.mdpi.com/1911-8074/19/9/678), opened. High-volatility Granger results depend on metric; the study finds no delayed cross-asset adjustment after extreme shocks. This is direct contrary evidence, not support for a profitable strategy. Its 2022–25 sample overlaps the reserved test era.

**Rule:** On Binance BTC and ETH perpetuals at each UTC H1 close, if BTC rose > 2% over the last hour buy ETH; if it fell > 2% short ETH. Enter next common M1 open, exit after four hours or 1.5 daily ATR14 ETH stop, one position at a time. Use same-venue mark/trade data consistently, charge actual funding at every settlement and both taker fees/slippage. CFD implementation is separate and must use its own cost and swap series.

**Mechanism:** Information can propagate from BTC into ETH during stress. **Estimate:** 10–50/year when data exists; 50–300 bp absolute ETH move over four hours vs 10–30 bp plus funding. Gross edge unknown and evidence against delay is strong; available 2015–21 crypto histories may be much shorter, reducing sample and power.

## Research and implementation gates

1. These are 12 hypotheses, not 12 independent discoveries: shared sources, highly correlated legs and ranking choices inflate selection risk. Fix one primary rule and universe before development; log all attempts. Test breadth, halves, cost doubling, outlier removal and uncertainty intervals, then a truly independent pre-sample if feasible. The reserved MT5 test remains one-time and requires the user's explicit go.
2. Report gross signed bp, net bp and R per basket, total leg costs and financing, leg-specific fills, gap exposure, overlap, missing minutes, stability by year, source vintage and exact dates. A big absolute move cannot stand in for gross expectancy.
3. Verify data availability by symbol and year, point values, quote currency, spreads around entry, financing history, dividend adjustments, commodity rolls, M1 synchronization, session clocks, cash calendars, 2020 oil price discontinuities, and whether continuous CFD histories are economically comparable. Reject results dependent on fabricated common bars or future-available data.
4. `docs/design/multi-symbol.md` referenced in the brief did not exist at inspection. Multi-symbol clock alignment, simultaneous fills, cross-leg stop ordering and basket-level R require a reviewed design before implementation; stop handling is not a promise of maximum loss.
