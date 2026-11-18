# Robert Carver, *Advanced Futures Trading Strategies* (Harriman House 2023)

Short: **AFTS**. Cite by strategy or tactic number (`AFTS S10`, `AFTS tactic 1`); the extraction has few printed pages
and drops several equations (double-V mapping, volatility-regime multiplier, trend/carry allocation map: check the PDF
before coding any of them). Read 2026-11-18 by Codex (gpt-6.1-terra medium, read-only, 4 parts,
`knowledge/reading-brief.md`); PDF in the library folder Tier 1. 30 daily futures strategies after estimated costs on
a "Jumbo" portfolio of ~100 futures ($50 m). Opus's reading for us: the portfolio Sharpes (trend 1.14, carry 0.94,
blend 1.27) come from ~100 roughly independent instruments; the **median single instrument earns Sharpe 0.2-0.3**
(trend 0.23, carry 0.28, cross-sectional carry 0.11), which our M4 power check cannot detect on a handful of
symbols. Relative value (S28-30) is weaker than outright; the crack spread is the best triplet (carry 0.62, trend
0.46, but 0.75-0.92 correlated with outright oil): card I-121, PARKED on power. Practical lessons: roll before first
notice (matters for I-109's contract choice), costs of a rule <= 0.15 Sharpe, fast mean reversion (S26-27) depends on
optimistic limit fills. Book strategy 20 (cross-sectional carry) is unrelated to our Strategy 20.

# Part 1: introduction, strategies 1-8 (buy and hold, risk scaling, slow and fast trend)

### Overview

This section builds eight increasingly complex daily futures strategies: constant-contract buy and hold; fixed and variable risk sizing; diversified long-only portfolios; and slow and fast trend following.

Carver’s main argument is that the useful unit of analysis is a **risk-scaled, continuously managed position**, rather than a collection of discrete trades. He regards diversification across markets as especially valuable and uses daily data across a broad futures universe to illustrate it.

The futures-specific contribution is substantial: an adjusted futures series represents the price changes earned by holding and rolling contracts, including carry, while execution costs must be deducted separately. Contract choice, roll timing and liquidity therefore matter.

His strongest trend results are for a large, diversified portfolio, not the median individual market. Results are historical, use estimated costs and should not be treated as independent evidence of a future edge.

The project’s four failed strategies are not identified in the brief or handoff. I therefore compare the ideas below with the **reported general failures of CFD trend, breakout and price-pattern ideas**, rather than claiming a precise difference from each of four unnamed strategies.

### Chapter notes

### Introduction and Part One — Strategies 1–8

- The book tests systematic rules on more than 100 futures markets, with more than 50 years of data for some series. It favors common rules across markets, subject to suitability, liquidity and cost constraints.
- Futures expose traders to different sources of risk and return: equity, duration, currencies, commodities and volatility. Market diversification can reduce dependence on selecting the one market that happens to perform.
- Most rules in this section use daily closes and continuously recalculate desired positions. They do not use conventional individual trade targets or fixed stops.
- The author explicitly warns that a backtest selected after seeing its results overstates what could have been achieved without hindsight. A plausible mechanism matters alongside statistical significance.  
  *Source: AFTS introduction; Strategy 1, “Backtesting.”*

### Strategy 1 — Buy and hold, single contract

- Buy one futures contract, hold it and roll into the specified later expiry; calculate P/L from the change in the held contract, futures multiplier and account-currency conversion. This is an illustrative long-only exposure, with no signal exit. *AFTS Strategy 1, pp. 15–24.*
- **Roll mechanics:** selling the old contract and buying the new one at their respective mid-prices creates no immediate economic gain merely because the two prices differ. A naïvely stitched series invents a jump. Additive back-adjustment removes that jump and preserves held-contract price changes; spreads and commissions are separate. The author’s S&P example rolls five days before expiry and conservatively charges both legs. *AFTS pp. 18–24.*
- A back-adjusted futures series contains **spot-related movement and carry**. For equities, the author describes excess return as the index return plus dividends minus financing; it excludes interest earned on idle account cash. The extracted discussion of the futures-price equation is confusing, so use the excess-return identity rather than transcribing that equation. *AFTS Strategy 1.*
- A back-adjusted level can become negative and is unsuitable for interpreting historical round-number levels. Use the actual contract price where its level matters; additive adjustments preserve differences, not historical percentage returns. *AFTS Strategy 1.*
- Contract choices in his illustrations: US 10-year bond rolls roughly 25 days before expiry; WTI holds the next December contract and rolls 40 days before expiry to reduce seasonal variation; VIX holds the second monthly contract. December-only commodity selection requires liquid far-dated contracts. *AFTS Strategy 1.*
- Illustrative single-contract results, with capital set to current notional exposure:

  | Instrument | Years | Annual return | Annual volatility | Sharpe | Monthly skew |
  |---|---:|---:|---:|---:|---:|
  | S&P 500 micro | 41 | 6.0% | 19.2% | 0.31 | −1.37 |
  | US 10-year bond | 41 | 3.75% | 6.39% | 0.59 | 0.15 |
  | WTI crude | 33 | 4.03% | 27.7% | 0.15 | −0.49 |
  | VIX, second month | 17 | −40.6% | 45.9% | −0.88 | 0.96 |

  These are illustrative historical results; roll-cost treatment is approximated rather than a reconstruction of historical fills.
- The bond result benefited from a major historical decline in yields. The long VIX position acted like costly insurance: occasional crisis gains did not offset its persistent drag. The author’s long-only asset-class medians show positive historical Sharpe for equities and bonds, roughly zero for FX and commodities, and strongly negative for volatility. *AFTS Strategy 1.*
- He uses 256 business days for annualization, measures monthly skew separately from Sharpe, and compares lower and upper tail percentiles with a normal distribution. Annualizing daily volatility and Sharpe relies on assumptions that serial dependence can violate. *AFTS Strategy 1.*

### Strategy 2 — Buy and hold with fixed risk scaling

- Stay long and recalculate contracts daily: capital × annual risk target divided by the annual cash risk of one contract. Contract risk uses the **current actual contract price**, multiplier, exchange rate and a fixed volatility estimate. Round to whole contracts; roll as needed. The example target is 20% annualized volatility. *AFTS Strategy 2, pp. 66–72.*
- The fixed volatility used in the historical comparison is estimated over the full sample. Carver acknowledges that this uses future information and is therefore a benchmark, not a faithful historical implementation. *AFTS Strategy 2, note 51.*
- S&P example: annual net return 12.1%, volatility 25.0%, Sharpe 0.48, skew −0.47; the fixed-capital backtest does not compound. The book says live capital should be adjusted for account gains and losses, especially after losses. *AFTS Strategy 2.*
- Across instruments, median Sharpe rises from 0.13 for the single-contract method to 0.34 with fixed risk scaling. This is the author’s historical comparison, including the forward-looking volatility estimate. *AFTS Strategy 2.*
- Contract indivisibility matters: the author prefers enough capital for approximately four contracts at inception, so position risk can be adjusted. Small nominal contracts can still be expensive relative to their low risk. *AFTS p. 72.*

### Strategy 3 — Buy and hold with variable risk scaling

- Remain long and resize daily as in Strategy 2, but replace fixed volatility with a backward-looking estimate. His short estimate is an exponentially weighted standard deviation with **span 32**, approximately α = 0.06061; blend **70% short-run** with **30% long-run** volatility. His estimated blend weights came from regression and were checked using backward-looking estimates. *AFTS Strategy 3, pp. 81–88 and notes 58–61.*
- The short estimate responds to volatility clustering; the long component moderates very large positions after quiet periods and reduces trading. Sudden shocks can still arrive before the estimate reacts.
- S&P comparison: Strategy 3 returns 12.2% annually after estimated costs of 0.06%, volatility 22.8%, Sharpe 0.54 and skew −0.68. Fixed-risk Strategy 2 has 12.1%, volatility 25.0%, Sharpe 0.48 and skew −0.47. The variable version improves the quoted tail ratios but not every measure. *AFTS Strategy 3, table 9.*
- Median instrument: net annual return 6.9%, cost 0.3%, volatility 20.9%, Sharpe 0.32, turnover 2.7 and skew −0.09. Asset-class median Sharpe: equities 0.46, volatility −0.40, FX 0.09, bonds 0.59, metals 0.32, energy 0.27 and agriculture 0.07. These are **long-only** historical results, not proof of future premia. *AFTS Strategy 3, tables 10–11.*
- He estimates current spread plus commission per contract, normalizes by current contract risk, then applies risk-normalized costs historically. This is useful for estimating present feasibility, but it does not reconstruct the historical cost environment. *AFTS pp. 83–88.*
- Liquidity checks include at least 100 contracts daily in the relevant expiry and a risk-adjusted volume threshold. The text gives **$1.25 million/day** in Strategy 3 and **$1.5 million** later in Strategy 4; this discrepancy should be resolved before adopting either as a rule. *AFTS Strategies 3–4.*

### Strategy 4 — Diversified buy and hold with variable risk sizing

- Run Strategy 3 across markets, allocate risk weights and apply a diversification multiplier to reach the portfolio risk target. The author groups markets by asset class and then by similar instruments, splitting allocations within groups. This is a long-only risk-premia portfolio, not a market-neutral strategy. *AFTS Strategy 4.*
- His two-market risk-parity example assigns equal risk weights to S&P 500 and US 10-year bond futures. With an illustrative multiplier of 1.32, aggregate net return is 15.7%, volatility 19.9%, Sharpe 0.79 and annual costs 0.26%. The multiplier shown in that example is inferred from realized risk and is illustrative. *AFTS Strategy 4, tables 12–13.*
- His six-market “All Weather” illustration allocates 25% risk each to stocks, bonds, commodities and gold; the bond and commodity buckets each contain two markets. Aggregate net return is 14.7%, Sharpe 0.77, turnover 9.3 and skew −0.26. This allocation attempts to include inflation-sensitive assets, although it underperforms the simpler historical example. *AFTS Strategy 4, tables 14–15.*
- The **Jumbo** portfolio contains 102 markets and assumes $50 million of capital. It uses backward-looking estimates of grouping and diversification as the investable history expands. Final reported multiplier: 2.47. Aggregate net annual return is **15.4%**, cost **0.8%**, volatility **18.2%**, Sharpe **0.85**, turnover **20.7** and skew **−0.04**. *AFTS Strategy 4, table 17 and notes 88–90.*
- The Jumbo universe was selected using markets liquid and inexpensive at the time of writing; delisted markets are excluded. The early history has far fewer markets—22 in the early 1980s—so it is not a constant 102-market experiment.
- Equity–bond diversification can deteriorate during inflation shocks. Low average correlation does not guarantee protection against joint large losses.

### Strategy 5 — Slow trend following, long only

- On daily back-adjusted prices, calculate EWMA spans **64 and 256 business days**. Hold the risk-scaled long position when EWMA64 exceeds EWMA256; otherwise hold zero. Resize while long and roll as needed. There is no independent stop or profit target. *AFTS Strategy 5, pp. 81 and following.*
- The author reports that fast/slow ratios between two and six produced statistically indistinguishable results in his real and artificial-data research; four is his convenient default. He reports smoother behavior from exponential rather than simple averages, especially at faster speeds. *AFTS Strategy 5, notes 94–97.*
- Median instrument: net return 5.6%, cost 0.23%, volatility 17.2%, Sharpe 0.32, turnover 5.8 and skew −0.07. The comparable unfiltered long-only Sharpe is also 0.32. *AFTS Strategy 5, table 19.*
- Jumbo: net return **16.4%**, cost **0.7%**, volatility **14.8%**, Sharpe **1.11**, turnover **24.1**, skew **0.22**. The filter avoided much of the historical early-1980s portfolio drawdown. *AFTS Strategy 5, table 20.*
- His historical transaction-cost model scales today’s per-contract cost by the ratio of historical to current daily price volatility. He cautions that actual historic costs, especially for retail traders, were likely higher. *AFTS Strategy 5.*
- A static alternative fixes the contract count from entry until trend reversal. Carver reports that dynamic resizing usually improves return and risk statistics despite additional trades; a static position can capture larger positive shocks but also larger adverse shocks.

### Strategy 6 — Slow trend following, long and short

- Use the same daily **EWMA64/256** crossover and risk sizing. Hold long when the fast average is above the slow, short when below, and flat on equality. Reverse when the crossover changes sign and resize daily between reversals. No separate stop is specified. *AFTS Strategy 6.*
- Median instrument: net return **4.8%**, cost **0.34%**, volatility **20.9%**, Sharpe **0.21**, turnover **7.0**, skew **−0.01**. This is weaker than the long-only historical median. *AFTS Strategy 6, table 21.*
- Median Sharpe by class: equities 0.15, volatility −0.02, FX 0.17, bonds 0.27, metals 0.53, energy 0.26 and agriculture 0.21. VIX-like markets have markedly negative skew under a rule that is frequently short; the 2020 volatility spike hurt the short position. *AFTS Strategy 6, tables 22–23.*
- Jumbo: net return **18.5%**, cost **1.1%**, volatility **18.4%**, Sharpe **1.01**, turnover **31.6**, skew **0.16**. The author attributes much of the improvement relative to individual results to diversification between changing long and short strategy exposures. *AFTS Strategy 6, table 24.*
- Regressing Jumbo monthly returns against the long-only benchmark, he reports beta **0.34**, alpha **1.13% per month** and t-statistic **9.6**. This is his historical regression result; the benchmark adjustment alone does not establish causality or eliminate selection and dependence concerns. *AFTS Strategy 6.*

### Strategy 7 — Slow trend following with trend strength

- Calculate `(EWMA64 − EWMA256) / daily price volatility`, scale to a forecast and cap it at ±20. Position equals the Strategy 4 average risk-scaled position multiplied by capped forecast/10. Thus the position changes gradually with both trend strength and volatility. *AFTS Strategy 7.*
- **Scalar ambiguity:** the text attributes **1.9** to EWMAC(16,64) inside this slow-strategy chapter, while Strategy 8 assigns **4.1** to EWMAC(16,64). In context, 1.9 appears intended for the slow 64/256 rule, but this is an inference; verify the book’s formula or companion material before implementation. Do not silently choose one. *AFTS Strategies 7–8.*
- Unbuffered median instrument: net return **4.1%**, cost **0.3%**, volatility **22.9%**, Sharpe **0.18**, turnover **8.9**, skew **0.18**. *AFTS Strategy 7, table 25.*
- Unbuffered Jumbo: net return **21.6%**, cost **1.2%**, volatility **22.5%**, Sharpe **0.96**, turnover **40.1**, skew **−0.33**. Forecast scaling increases return but does not improve every risk statistic over Strategy 6. *AFTS Strategy 7, table 26.*
- The author reports monthly benchmark-adjusted alpha of **1.17%**, compared with 1.13% for Strategy 6. He treats the historical case for slow forecast scaling as modest, while valuing its ability to combine forecasts. *AFTS Strategy 7.*

### Strategy 8 — Fast trend following with trend strength

- Replace the slow crossover with daily **EWMA16/64**. Divide the difference by daily price volatility, multiply by the stated scalar **4.1**, cap at ±20 and size as forecast/10 times the average risk-scaled position. Recalculate daily and roll as needed. *AFTS Strategy 8.*
- Apply a position buffer with half-width **10% of the average long position** around the unrounded target. Trade only when the current position falls outside the band. The extracted equations do not unambiguously specify the exact rounding and destination after a breach; verify those equations before coding. *AFTS Strategy 8.*
- Buffered median instrument: net return **6.5%**, cost **0.5%**, volatility **23.6%**, Sharpe **0.27**, turnover **16.7**, skew **1.00**. The buffered slow rule has Sharpe 0.19 and turnover 8.9 in the same table. *AFTS Strategy 8, table 27.*
- Buffered Jumbo: net return **24.1%**, cost **1.7%**, volatility **22.7%**, Sharpe **1.06**, turnover **60.5**, skew **0.81**. Buffered slow trend has Sharpe 0.96 and turnover 27.5. Fast trend performed well in the author’s 2008 example but costs substantially more to trade. *AFTS Strategy 8, table 28.*
- The printed buffered slow-rule skew in table 28 is **0.61**, versus **−0.33** for unbuffered Strategy 7 in table 26. That is a large change despite the author saying buffering barely affects the slow strategy; treat the figures as reported and check the source before interpreting the discrepancy.

### Topic tags

- **Trend:** Daily 64/256 and 16/64 EWMAC rules; faster trend has higher reported turnover and better historical skew. The broad-portfolio result is stronger than the median single-market result. *AFTS Strategies 5–8.*
- **Seasonality/time:** Holding a fixed commodity delivery month can reduce seasonal contract variation, but requires adequate liquidity far along the curve. *AFTS Strategy 1.*
- **Volatility:** Blend a responsive 32-span estimate with longer-run volatility; a quiet-market position can still be hit before risk forecasts react. *AFTS Strategy 3.*
- **Stops and exits:** Trend reversal is the common entry and exit signal. Carver discusses volatility-scaled stops as an alternative but gives no separate default stop for these rules. *AFTS Strategy 6.*
- **Position sizing/risk:** Size by contract cash risk, account for indivisible contracts and stress losses beyond those already observed. His 20% illustrative volatility target is not a project recommendation. *AFTS Strategies 2–4.*
- **Testing and robustness:** Distinguish historical simulation from a descriptive test of a rule selected with hindsight; use past-only estimates where required; beware short samples, current-universe selection and secular trends. *AFTS Strategies 1–4.*
- **Costs/execution:** Separate carry from roll execution costs. Model the actual held contract and both sides of a roll; present-day risk-normalized costs are approximations. *AFTS Strategies 1, 3 and 5.*
- **Portfolio/diversification:** Long/short signals can reduce correlations between strategy returns even where underlying markets are correlated. Correlations and achievable leverage can change in stressed regimes. *AFTS Strategies 4–6.*

### Testable ideas

All entries below are **research candidates or benchmarks**, not trading rules authorized for deployment. Apply the project’s power, preregistration, ledger and one-time-test rules before looking at new results.

1. **★ Buffered fast time-series trend across available venues**  
   Daily EWMA16/64 on an appropriate total-return or tradable futures-return series; use the 4.1 scaled, ±20 capped forecast and variable risk sizing. Buffer by 10% of average position; exit or reverse as the forecast changes sign. No separate stop.  
   **Source/evidence:** AFTS Strategy 8; Jumbo Sharpe 1.06 after estimated costs, skew 0.81, turnover 60.5.  
   **Fit:** Mixed. Treasury continuous data, selected energy contracts and crypto perps could support research, subject to reliable contract construction, funding, spreads and fees. CFD positions require historical swap on both sides; share shorts require borrow and dividend treatment. High turnover and the limited cross-asset universe are serious obstacles.  
   **Difference from reported failures:** slower daily risk-weighted exposure and cross-market aggregation, rather than the CFD price-pattern and intraday screens described in the brief. It remains a trend hypothesis and is not a mandatory-counterparty mechanism.

2. **★ Slow long-only trend as an exposure filter**  
   Hold a variable-risk long exposure only when daily EWMA64 exceeds EWMA256; otherwise hold cash. Exit on reversal, with no independent stop. Compare against the same long-only exposure without the filter.  
   **Source/evidence:** AFTS Strategy 5; Jumbo Sharpe 1.11, median instrument Sharpe 0.32.  
   **Fit:** Reasonable as a **risk-management benchmark** on Treasury and broad equity data, with actual futures roll costs or share dividends as applicable. CFD overnight swap must be included. The author’s diversified portfolio cannot be assumed reproducible with our narrower set.  
   **Difference:** a filter on an existing exposure rather than a short-horizon breakout entry; it does not identify a forced counterparty.

3. **★ Long/short slow trend as a diversification control**  
   Daily EWMA64/256: long above, short below; reverse at crossover and resize using the 70/30 volatility blend. No fixed stop. Compare its contribution to an existing portfolio, including tail episodes.  
   **Source/evidence:** AFTS Strategy 6; Jumbo Sharpe 1.01, median Sharpe 0.21, and author-reported monthly benchmark alpha 1.13%.  
   **Fit:** Treasury, energy and perps are plausible research inputs if point-in-time returns and financing are sound; VIX shorts have severe jump exposure. CFD swap and perps funding are material overnight.  
   **Difference:** the hypothesis is diversification of **strategy returns**, rather than a claim that each individual CFD has a strong standalone signal. Still a generic trend rule, so prior failures are a strong reason for a stringent incremental-value gate.

4. **★ Actual-contract roll and carry accounting benchmark**  
   Choose a contract and roll date before observing subsequent prices; calculate daily P/L from the held expiry, close and open at the roll, and charge execution on both legs. Compare this with any continuous series used by a signal. No alpha entry or stop: this is a data and accounting validation.  
   **Source/evidence:** AFTS Strategy 1, pp. 18–24; the book demonstrates how an unadjusted stitch produces a false roll jump.  
   **Fit:** Good for EIA contracts 1–4 where history and expiry mapping are sufficient; limited for a single Yahoo continuous Treasury series because the underlying contract legs may be unavailable. This is a useful safeguard for I-109, but does not itself establish a roll edge.  
   **Difference:** a measurement check, not another price-pattern strategy. For CFDs include actual swap; do **not** add futures carry again. The project’s GSCI roll and VIX basis failures remain failures.

5. **★ Dynamic versus fixed volatility sizing of an existing signal**  
   Hold the same frozen signal and compare fixed sizing with daily risk sizing using 70% EWMA32 volatility and 30% long-run volatility; include all resizing costs. Entry and exit are inherited from the existing signal, with no new stop. Define the long-run estimator before a test.  
   **Source/evidence:** AFTS Strategy 3; S&P historical Sharpe 0.54 versus 0.48 for the fixed-risk illustration, although the latter uses full-sample volatility.  
   **Fit:** Good as a methodological comparison on available daily data, provided the signal has not already spent its permitted test and funding, swap, spread and fees are included.  
   **Difference:** asks whether sizing improves the risk profile of an independently justified signal; it does not propose a new CFD pattern edge.

6. **Fixed-delivery-month commodity trend benchmark**  
   If historical liquidity permits, build a WTI December-to-December adjusted series, rolling 40 days before expiry, and apply the 64/256 or 16/64 rule with the parameters above. Exit or reverse according to the chosen rule.  
   **Source/evidence:** AFTS Strategies 1 and 5–8; Carver uses December WTI to reduce seasonal variation, not as a standalone demonstrated seasonal alpha.  
   **Fit:** Likely poor with only EIA contracts 1–4 if they do not cover the required December expiry and historical roll dates. CFD oil plus swap is a different implementation and cannot substitute for those futures prices.  
   **Difference:** controls the delivery-month composition of a trend signal; it is not evidence that a new GSCI roll strategy survives the already failed tests.

### Warnings / pitfalls

- **Carry is not free money from the roll gap.** A rolled futures return already incorporates the economics of the futures curve over time; the visible price gap at the instant of a mid-price roll is not itself a realized gain. Charge execution separately.
- **Do not transplant futures results onto CFDs by deleting swap.** Under the project’s venue rule, CFD swap is largely related to futures carry; use actual CFD prices and swap for CFDs, or futures prices and a futures cost model for futures.
- **No lookahead from adjusted data:** an additive future adjustment may leave a simple moving-average difference unchanged under a common shift, but this does not make every use of a final back-adjusted series safe. Construct point-in-time signals and P/L carefully, particularly percentage volatility, contract selection and roll dates.
- **Jumbo is not our portfolio.** Its 102 current-survivor markets, evolving history, $50 million capital assumption and estimated execution costs limit transfer to our data and account sizes.
- **Risk scaling cannot foresee a jump.** Quiet-period leverage, VIX short exposure, negative prices, gaps and correlated shocks need explicit stress treatment. A historical maximum drawdown is not a loss limit.
- **Regression alpha and attractive skew are not causal proof.** Selection across many markets and rules, non-normal returns, serial dependence and a favorable historical regime can all make reported evidence look stronger.
- **Extraction ambiguities remain:** verify the slow-trend scalar and exact buffer execution/rounding before implementation; the inconsistent liquidity thresholds and buffered skew figures also warrant a source check.


# Part 2: strategies 9-20 (multiple trend, carry, combined, adjusted, regimes, spot trend, accurate carry, allocation, normalised, asset-class, cross-sectional momentum and carry)

### Overview

This section develops a family of daily futures strategies from two ingredients: trend and carry. Carver’s main practical argument is to diversify across instruments, trading horizons and distinct sources of return, while excluding rules whose expected trading costs are excessive.

The most useful new material for this project is his treatment of **what carry measures**, the ways a futures curve can give a misleading signal, and the decomposition of a continuous futures trend into spot movement and carry. His largest reported improvements come from combining directional trend and carry; most later refinements produce small or mixed improvements.

The reported results are **Carver’s historical simulations**, generally for a diversified “Jumbo” portfolio of roughly 100 futures instruments, with his cost assumptions, buffering and risk scaling. They are not evidence that the same rules survive FTMO swap, crypto funding or the project’s current costs. Skew in his summary tables is generally monthly; turnover figures in portfolio tables should not be confused with the separate per-rule turnover estimates used in his cost filter.

The current handoff confirms the supplied context. In particular, VIX-basis idea I-113 and GSCI-roll ideas I-114/I-115 have already been falsified, so related proposals below need a clearly different hypothesis and fresh eligibility under the project’s testing rules.

**Extraction limitation:** several mathematical equations did not survive the supplied text extraction. I describe their prose definitions and flag places where an exact implementation would require checking the book. Strategy-number citations are used throughout because reliable page headers are largely absent from the extracted range.

### Chapter notes

### Ch 9 — Multiple trend-following rules (AFTS strategy 9)

- Use six daily EWMAC pairs: `(2,8), (4,16), (8,32), (16,64), (32,128), (64,256)`. The author finds little reason to fit intermediate speeds or vary the slow/fast ratio; ratios from two to six behave similarly.
- Normalize the crossover by daily price volatility. Forecast scalars for fast spans 2, 4, 8, 16, 32 and 64 are respectively **12.1, 8.53, 5.95, 4.10, 2.79 and 1.91**. Cap each forecast at ±20, average eligible forecasts equally, apply the diversification multiplier and cap the result again.
- Per-rule annual turnover estimates for the six spans are **98.5, 50.2, 25.4, 13.2, 7.6 and 5.2**. These are used for cost eligibility; they are not the portfolio turnovers in the results table. His rule-selection cost ceiling is **0.15 Sharpe units**, including assumed roll costs.
- Adjacent trend-speed returns correlate about **0.85–0.89**; the fastest and slowest correlate **0.12**. Diversification helps, but adding very similar intermediate speeds adds little.
- Across the Jumbo portfolio, individual speeds 2/4/8/16/32/64 have net Sharpe **0.15/0.64/0.92/1.06/1.02/0.96**, turnover **381/195/97.9/60.5/35.3/27.5**, and monthly skew **1.32/0.75/1.48/0.81/0.75/0.61**. These individual-speed comparisons include instruments too expensive for the rule in practice.
- The combined cost-filtered strategy reports net Sharpe **1.14**, monthly skew **0.98**, turnover **62.9**, and annual costs **1.2%**. Median instrument Sharpe is only **0.23**: the strong aggregate result depends heavily on diversification.
- Median instrument Sharpe by class: equities **0.03**, volatility **0.51**, FX **0.19**, bonds **0.43**, metals **0.37**, energy **0.39**, agriculture **0.24**. The volatility sample contains only two instruments.
- The fast rules deteriorated after roughly 1990. Carver considers both decay and underestimated early historical costs plausible. He warns that choosing the best historical speed or dropping rules based on the same backtest can overfit.

### Ch 10 — Basic carry (AFTS strategy 10)

- Carry is the return expected from the contract’s movement along the curve **under an unchanged-spot assumption**, not guaranteed profit. A spot move against the position can erase it.
- For a held contract with a nearer contract available, estimate raw long carry from **nearer price minus held price**. For a front contract, use **held price minus next price** as an approximation. Divide by the expiry separation in years, then by annualized price-unit volatility. The latter approximation assumes a suitable curve shape.
- Sources differ: bond yield versus financing; equity dividends versus financing; currency interest-rate differences; metal funding and storage; and commodity convenience yield, storage and financing. Bond roll-down is simplified in the book’s decomposition.
- Smooth risk-adjusted carry with EWMAs of **5, 20, 60 and 120 business days**; multiply each by **30**, cap at ±20, equally weight the cost-eligible forecasts and apply the corresponding combined multiplier. The four-carry multiplier is **1.04**.
- Estimated per-rule annual turnover for eligibility is **5.75, 3.12, 1.82 and 1.22**, respectively. Individual-span Jumbo results: net Sharpe **0.87/0.87/0.89/0.87**, portfolio turnover **28.5/20.7/16.2/13.2**, and monthly skew **0.57/0.35/0.08/0.24**.
- Combined carry reports Jumbo net Sharpe **0.94**, monthly skew **0.41**, turnover **19.2**, annual costs **0.8%**; median instrument Sharpe is **0.28** and median instrument skew **−0.17**. The portfolio’s better skew should not be assumed for a small, concentrated universe.
- Median carry Sharpe: equities **0.40**, volatility **0.59**, FX **0.30**, bonds **0.48**, metals **0.25**, energy **0.20**, agriculture **0.14**. Volatility carry is mostly short volatility and has particularly poor instrument-level skew.
- The median instrument delivered **115%** of the author’s risk-adjusted expected carry measure; energy delivered **77%** and agriculture **46%**. These are historical descriptive ratios, not forecasts.
- Curve seasonality matters. Natural gas adjacent-month carry varies with seasonal delivery; European equity dividends and some bond cheapest-to-deliver changes can make front-versus-next carry point the wrong way. A smooth reduces noise but does not prove the estimate is correct.
- Trend/carry return correlation is reported as **0.36**.

### Ch 11 — Combined carry and trend (AFTS strategy 11)

- Select eligible rules as above; allocate **60% of forecast weight to trend and 40% to carry**, splitting each allocation equally among that instrument’s eligible speeds. Combine and net forecasts before trading.
- In the Jumbo backtest, the 60/40 blend reports net Sharpe **1.27**, monthly skew **0.76**, turnover **46.5**, annual costs **1.1%**, and average drawdown **−8.9%**. Pure trend reports Sharpe **1.14**; pure carry **0.94**.
- A 50/50 blend also has reported Sharpe **1.27**. The apparent optimum is therefore a broad historical comparison, not a precise estimate supporting a uniquely correct 60/40 weight.
- The diversification gain is much larger in the 100-plus-instrument portfolio than for a single instrument. Carry’s negative instrument-level skew did not disappear by magic: the portfolio benefited from historical non-coincidence of its worst episodes.

### Ch 12 — Adjusted trend (AFTS strategy 12)

- Carver examines subsequent risk-adjusted returns in forecast bins. Very strong fast-trend signals show weaker continuation and sometimes reversal; slower rules show a clearer relationship. Asset-class-specific estimates are too noisy, in his view, to justify separate fitted mappings.
- He tests a symmetric nonlinear “double V” adjustment for EWMAC2, and for EWMAC4 and EWMAC64 a **1.25 scaling with a lower original-forecast cap of 15**. Other speeds remain unchanged. **The exact piecewise double-V equation is missing from the extraction** and should be checked in the book before implementation.
- EWMAC2 adjustment increases Jumbo turnover **381 → 704**, costs **9.3% → 16.7%**, and changes net Sharpe **0.15 → −0.22**. Adjusting all three speeds in the combined strategy changes Sharpe **1.27 → 1.29**, skew **0.76 → 0.70**, turnover **46.5 → 45.6**.
- Carver would not trade the adjustment: the small combined benefit does not justify the added complexity. It is a warning against treating a noisy conditional-return plot as a ready-made rule.

### Ch 13 — Trend and carry in different risk regimes (AFTS strategy 13)

- Define relative volatility as current estimated percentage volatility divided by its trailing **10-year average**. Rank the current value within the instrument’s historical distribution using only information available at that time.
- The forecast multiplier ranges from **2 at the lowest historical volatility rank to 0.5 at the highest**, and is smoothed with a **10-day EWMA**. The precise multiplier equation is absent from the extracted text. For carry the forecast scalar changes from **30 to 23**; the normal cap still applies.
- Carver reports that both trend and carry weaken in high-volatility regimes, especially trend. Historical regime boundaries are descriptive; they must not be estimated using future data.
- Against baseline Sharpe **1.27**, adjusting trend alone gives **1.39**, monthly skew **0.59**, turnover **53.1**, cost **1.2%**. Adjusting carry alone gives **1.25**; adjusting both gives **1.34**, skew **0.43**, turnover **53.8**.
- Reducing risk in high volatility can miss profitable crisis trends: the adjustment underperformed in **2008**. The strategy adds a second volatility-dependent exposure adjustment on top of ordinary volatility sizing.

### Ch 14 — Spot trend (AFTS strategy 14)

- Construct synthetic spot changes by subtracting estimated accrued carry from back-adjusted futures price changes, then accumulate them. Apply the same EWMAC rules to this series. Carry estimation errors flow directly into the synthetic spot series.
- Pure synthetic-spot trend reports Sharpe **0.77**, monthly skew **1.21**, turnover **65.4**, cost **1.3%**, against adjusted-futures trend’s **1.14**, **0.98**, **62.9**, **1.2%**.
- With **40% synthetic-spot trend / 60% carry**, the Jumbo result is Sharpe **1.20**, skew **0.94**, turnover **33.7**, cost **1.0%**. The original 60/40 adjusted-price blend reports **1.27**, **0.76**, **46.5**, **1.1%**.
- The biggest deterioration from removing carry is in bonds and volatility; metals and equities improve slightly in the author’s instrument medians. Much of the historical trend signal in high-carry markets may therefore reflect accumulated carry.
- This is a useful diagnostic even where the synthetic signal itself is inferior: it exposes the implicit carry allocation in a total-return trend.

### Ch 15 — Accurate carry (AFTS strategy 15)

- A nearer-versus-held contract measures the nearby part of a non-front contract’s curve; it is not automatically the right estimate for a long holding horizon. For front contracts, front-versus-next can reflect the *next* delivery interval rather than the carry actually experienced before expiry.
- For predictable seasonal distortions, subtract a trailing one-year average from risk-normalized raw carry; estimate the seasonal component by calendar day across prior years; subtract that component and optionally add it back shifted by approximately one roll interval. Carver suggests at least **three years** and a **five-year EWMA** across years, recalculated using backward-looking information.
- In 57 selected front-contract instruments, original / de-seasonalized / shifted carry have net Sharpe **0.59/0.55/0.51**, skew **0.06/0.02/0.06**, turnover **15.5/15.0/17.1**, and costs **0.6%** for each. More accurate-looking signals did not improve the backtest.
- For fixed seasonal contracts, compare the held contract to the front rather than the adjacent nearer contract when the intended horizon is long. His five-instrument comparison did not improve performance; the sample is too small for a firm conclusion.
- Direct spot can be preferable if synchronized and economically comparable. Bond futures need particular care around cheapest-to-deliver, conversion factors and duration. Using a convenient yield series is not automatically equivalent to a bond-futures carry series.

### Ch 16 — Trend and carry allocation (AFTS strategy 16)

- Form a trailing **one-year** difference between the trend and carry strategy returns, scaled by the **20%** risk target. Map it to a trend weight between 0 and 1: equal performance implies **50%**, a 20% trend advantage implies **100%**, and a 20% disadvantage implies **0%**; smooth with a **30-day EWMA**. The extracted formula itself is missing, so verify the exact mapping before coding.
- The timed allocation reports Jumbo Sharpe **1.33**, monthly skew **0.89**, average drawdown **−10.1%**, versus fixed 60/40’s **1.27**, **0.76**, **−8.9%**. Alpha falls **22.3% → 20.7%** and beta rises **0.30 → 0.46**. The table does not report turnover or costs for this timed variant.
- A separate fitted alternative gives equities **10% trend / 90% carry**, leaving other classes at 60/40: Sharpe **1.33**, skew **0.86**, turnover **36.8**, costs **1.0%**. Carver cautions against more granular fitting.
- An apparent commodity-versus-financial difference in trend/carry performance largely disappears when comparing the same post-mid-1990s period. Unequal history length can create a persuasive but false asset-class story.

### Ch 17 — Normalised trend (AFTS strategy 17)

- Create a normalized price by accumulating each daily price change divided by its contemporaneously available daily price-volatility estimate; the book uses an arbitrary scaling factor of **100**. Apply the same six EWMAC speeds to that series and normalize the crossover again using volatility of normalized-price changes.
- Use the same EWMAC scalars as strategy 9. Eligibility turnover estimates for spans 2/4/8/16/32/64 are **109.9/56.2/28.7/15.2/9.0/6.5**.
- Standalone normalized trend reports Jumbo Sharpe **1.15**, skew **0.93**, turnover **72.1**, costs **1.4%**, versus ordinary trend **1.14**, **0.98**, **62.9**, **1.2%**. Their returns correlate **0.97**.
- Replacing ordinary trend with normalized trend in the carry blend reports Sharpe **1.32**, skew **0.76**, turnover **48.3**, costs **1.1%**. Including both trend types gives **1.32**, **0.75**, **47.6**, **1.1%**.
- Normalization helps make later cross-instrument comparisons possible, but this highly correlated variant is not independent confirmation of a trend edge.

### Ch 18 — Trend following asset classes (AFTS strategy 18)

- Average the daily volatility-normalized returns of the instruments in an asset class, accumulate them into a class index, then apply the same EWMAC rules. Members of a class receive the same forecast at each speed, although eligible speed sets can differ.
- The author uses over **140 instruments** to construct class indices, including instruments he cannot trade, versus roughly 102 in the Jumbo trading universe.
- Median instrument Sharpe improves from **0.23** for ordinary trend to **0.30** for class trend; equities improve from **0.03 to 0.12**. But aggregate Jumbo Sharpe falls **1.14 → 0.97**, with skew **0.94**, turnover **65.5**, and costs **1.3%**, because common signals reduce within-class diversification.
- Adding class trend to a blend already containing ordinary trend, normalized trend and carry reports Sharpe **1.31**, skew **0.71**, turnover **46.1**, costs **1.1%**. A cleaner signal for one instrument need not improve the portfolio.

### Ch 19 — Cross-sectional momentum (AFTS strategy 19)

- Subtract the normalized class index from each instrument’s normalized price. Measure its average relative change over **5, 10, 20, 40, 80 and 160 business days**, then smooth with EWMAs of **2, 3, 5, 10, 20 and 40 days**, respectively.
- Forecast scalars in that order: **56.1, 79.0, 108.5, 153.5, 217.1, 296.8**. Cap each at ±20, select speeds using costs, equally weight eligible rules and cap the combined forecast.
- Five- through 160-day individual-horizon net Sharpes are **−0.65, −0.20, 0.28, 0.36, 0.20, 0.30**; turnovers **598, 407, 172, 85.9, 46.2, 26.4**. The first two are especially expensive.
- The combined standalone Jumbo strategy reports Sharpe **0.34**, skew **0.51**, turnover **81.4**, costs **1.4%**, average drawdown **−40.0%**. Its return correlation is approximately **0 with carry** and **0.31 with trend**.
- Adding it at 15% forecast weight to the broader blend gives Sharpe **1.30**, skew **0.70**, turnover **43.9**, costs **1.1%**, versus **1.31**, **0.71**, **46.1**, **1.1%** without it.
- This is a **relative forecast**, not a guaranteed dollar-, beta- or exposure-neutral long-short portfolio. Position sizing and other forecasts can leave material net exposure.

### Ch 20 — Cross-sectional carry (AFTS strategy 20)

- Smooth each instrument’s risk-adjusted carry with a **90-day EWMA**; subtract the contemporaneous median smoothed carry of its asset class. Multiply the residual by **50** and cap at ±20.
- Median centering gives roughly balanced numbers of positive and negative forecasts when there are no ties, but does **not** ensure equal notional, volatility or beta exposure. The author’s rule-level turnover estimate is **2.9**.
- Standalone Jumbo cross-sectional carry reports net Sharpe **0.31**, monthly skew **0.21**, turnover **17.6**, costs **0.7%**. Median instrument Sharpe is **0.11**; class medians include metals **0.26**, energy **0.22**, equities **0.03**, FX **0.10**, bonds **0.09**, volatility **0.19**.
- Directional and relative carry returns correlate about **0.31**. A 70/30 directional/relative blend reports Sharpe **0.89**, skew **0.09**, turnover **17.3**, costs **0.7%**, versus directional carry’s **0.94**, **0.41**, **19.2**, **0.8%**.
- Adding relative carry to the full multi-rule blend produces Sharpe **1.31**, skew **0.60**, turnover **46.2**, costs **1.1%**, against **1.30**, **0.70**, **43.9**, **1.1%** without it.
- **Book strategy 20 is unrelated to this project’s Strategy 20**, the crypto taker-flow sort.

### Topic tags

- **Trend:** Multiple horizons diversify, but fast daily rules can be dominated by costs; adjusted futures trend includes carry. Normalized and class-level trends are closely related variants, not independent discoveries.
- **Mean reversion:** Fast extreme trend forecasts sometimes precede reversals in the author’s pooled analysis, but the proposed nonlinear mapping performed poorly after costs.
- **Momentum:** Cross-sectional momentum measures relative rather than absolute strength and is not automatically market-neutral. Its standalone futures result is weak.
- **Seasonality/time:** Adjacent futures delivery months can contain weather, dividend or cheapest-to-deliver seasonality. Contract choice determines which interval a carry estimate describes.
- **Volatility:** Performance varies by relative volatility; a regime adjustment improved trend historically but reduced exposure to some crisis winners.
- **Stops-and-exits:** These rules continuously resize and can reverse as forecasts change; they do not specify a separate fixed stop or take-profit. Price gaps and position risk remain relevant.
- **Position sizing/risk:** Carry strength differs structurally by asset class; a common forecast scalar naturally gives different realized risk. Do not interpret a low-volatility allocation multiplier independently of existing volatility sizing.
- **Testing and robustness:** Compare instruments over common calendar periods, separate portfolio from median-instrument results, estimate regime and seasonal statistics backward-looking, and treat small subgroup differences and fitted allocations cautiously.
- **Costs/execution:** Faster rules have sharply higher turnover. Futures require executable contract prices, rolls, spread and commission; a CFD must include its actual swap, and perps their funding.
- **Portfolio/diversification:** Carry and trend diversify in the author’s data, but 100-plus instruments contributed more than many highly correlated rule variants. Historical crisis diversification is not guaranteed.

### Testable ideas

The brief does not identify the **four failed strategies** by name. Comparisons below therefore use the stated failed families—CFD patterns, trends, breakouts and intraday rules—and the specifically identified I-113/I-114/I-115 results; they are not claims of a complete duplication check. None of these ideas is a passed project hypothesis.

1. **★ Carry attribution for Treasury and energy trends** — On a daily contract-level futures series, calculate total-return trend and an otherwise identical synthetic-spot trend after subtracting accrued curve carry; compare both with explicit carry and a 60/40 blend. Use the strategy 9 spans and strategy 10 carry spans, with no separate stop; positions change with forecasts. **Source/evidence:** AFTS strategies 10, 14; synthetic-spot trend Sharpe **0.77** versus **1.14** for adjusted trend. **Fit:** good as a diagnostic where synchronized contract curves and executable returns exist; the single Yahoo continuous Treasury series alone cannot reconstruct historical curve carry. EIA contract series need timestamp and contract-identity checks. CFD versions must include swap and cannot simply remove it. **Difference:** tests the source of returns rather than another entry pattern.

2. **★ Energy curve carry with explicit delivery season** — Daily, estimate annualized `(nearer − held price) / expiry gap`, risk-normalize, and smooth over **5/20/60/120 days**; long positive and short negative combined forecasts, continuously resize, and roll under a fixed documented contract schedule. No separate stop is specified by Carver. **Source/evidence:** AFTS strategies 10 and 15; combined carry Sharpe **0.94** across his diverse portfolio, but energy median **0.20** and realized carry **77%** of his expected measure. **Fit:** potentially good for EIA contracts 1–4 if data are point-in-time and trading/roll prices are executable; limited curve depth and seasonal delivery restrict replication. A fixed December-contract test may need unavailable longer-dated prices. **Difference:** curve compensation rather than a price breakout; review I-114/I-115 first and do not present a small rule variation as an unspent independent test.

3. **★ Cross-sectional energy or crypto carry** — Each day calculate a venue-appropriate risk-adjusted carry estimate, smooth **90 days**, subtract the same-class median, multiply by **50**, and cap at ±20; go long above-median and short below-median forecasts, resizing continuously. Add an explicit neutrality convention only as a separately specified project decision. **Source/evidence:** AFTS strategy 20; standalone futures Sharpe **0.31**, energy median **0.22**. **Fit:** potentially good for multiple EIA energy curves or sufficiently broad Binance perps. Perp funding is a different mechanism and must use timestamped, actually paid/received funding and fees; do not treat a future funding observation as known. CFD swap is an actual holding cash flow and needs broker history. **Difference:** relative compensation across assets, not an absolute CFD pattern; it is distinct from project Strategy 20’s taker-flow signal but may overlap existing carry research.

4. **★ Volatility-regime exposure test** — For an already eligible trend signal, rank current volatility divided by its trailing **10-year** average against its prior history; apply Carver’s bounded **0.5–2** multiplier, smoothed **10 days**, and rebalance the resulting forecast. Verify the missing exact multiplier equation in the book first. **Source/evidence:** AFTS strategy 13; combined Sharpe **1.27 → 1.39**, skew **0.76 → 0.59**, turnover **46.5 → 53.1**. **Fit:** data are available on daily US shares, CFDs and crypto; poor if the underlying trend has already failed after realistic costs. Include swap/funding for overnight holdings. **Difference:** exposure management of an existing signal rather than a new entry; test the incremental effect with paired returns and crisis episodes, not a fresh claim of trend profitability.

5. **★ Cross-sectional stock momentum using normalized class returns** — For a point-in-time universe of liquid US shares, construct an equal-weighted volatility-normalized class index; subtract it from each stock’s normalized series. Use **20/40/80/160-day** relative changes and the author’s quarter-horizon EWMA smooths, retaining only affordable speeds; rebalance continuously or at a predeclared practical frequency. **Source/evidence:** AFTS strategy 19; futures combined Sharpe **0.34** and 40-day individual Sharpe **0.36**; his rule is not guaranteed neutral. **Fit:** potentially good with Alpaca daily shares, but requires point-in-time membership, delistings, corporate actions, borrow availability/fees and realistic execution. **Difference:** relative stock momentum rather than intraday CFD breakouts; must be checked against the project’s prior share momentum trials before registration.

6. **Multi-speed directional trend plus carry** — Use strategy 9’s six daily EWMAC pairs and strategy 10’s four carry spans; exclude rules over the preset cost budget, blend **60% trend / 40% carry**, and resize as forecasts change. No fixed stop is specified. **Source/evidence:** AFTS strategy 11; Jumbo Sharpe **1.27**, skew **0.76**, turnover **46.5**. **Fit:** partial: broad futures replication is unavailable; CFD spot plus actual swap, or perp prices plus funding, can test venue-specific analogues but are not identical. **Difference:** slower diversified forecast combination and explicit carry versus individual CFD price patterns; previous trend failures make this a low-priority replication rather than a fresh forced-flow mechanism.

7. **Seasonally corrected front-contract carry** — For a front-contract strategy, use at least **three prior years** to estimate calendar-day seasonal carry, subtract it from current raw carry, then separately test adding the seasonal component shifted by one roll interval; update annually without future data. Smooth as in strategy 10 and continuously resize. **Source/evidence:** AFTS strategy 15; corrected Sharpe **0.51** versus original **0.59** on 57 instruments. **Fit:** poor to partial for available EIA contract depth; a multi-year history alone does not establish executable contracts or correct expiry mapping. **Difference:** tests measurement error in curve carry, not an entry pattern; the book’s own evidence argues against prioritizing it.

8. **Asset-class trend as a filter for a small portfolio** — Form an equal-weighted index of daily normalized returns within a class, apply the strategy 9 EWMAC speeds and use the resulting signal on a liquid class representative; resize as the forecast changes. **Source/evidence:** AFTS strategy 18; median instrument Sharpe **0.30**, but Jumbo Sharpe **0.97**. **Fit:** technically feasible for US shares, selected CFD groups and crypto; account for selection history, correlation and overnight swap/funding. **Difference:** shared class signal instead of a single-instrument breakout, but still a trend hypothesis and exposed to the established cost wall.

9. **Trend/carry allocation timing** — Compare daily paper returns from eligible trend and carry legs; calculate their trailing **256-business-day** relative return divided by the **20%** risk target, map it to a 0–100% trend weight and smooth **30 days**. Verify the omitted exact mapping before implementation. **Source/evidence:** AFTS strategy 16; Sharpe **1.33** versus **1.27**, with worse drawdown and higher beta. **Fit:** only meaningful after both legs independently survive costs; includes futures rolls, CFD swap or perp funding as appropriate. **Difference:** times existing mechanisms rather than creating a trade trigger; the many allocation choices create substantial multiple-testing risk.

10. **VIX futures carry decomposition** — If point-in-time VIX contract curves and executable histories are sufficient, estimate and smooth futures carry with the strategy 10 spans, then report outcomes separately by volatility regime and stress period; retain explicit roll and short-volatility exposure. **Source/evidence:** AFTS strategy 10; volatility-class median Sharpe **0.59**, but only two instruments and instrument skew **−0.64**. **Fit:** limited by available contract history and crisis concentration; an analogous FTMO CFD requires actual swap. **Difference:** directional carry rather than a generic chart pattern, but I-113 VIX basis was already killed: establish a materially distinct mechanism and test eligibility before any new test.

### Warnings / pitfalls

- **Do not remove CFD swap and call the result futures carry.** FTMO swap is largely the CFD counterpart of futures carry; the two venues have different prices, contract mechanics and costs. A valid comparison models each on its own data.
- A curve spread is an expected return under assumptions, not cash that can be collected without price risk. Annualization, expiry spacing, contract identity, roll timing and the horizon represented by the spread all matter.
- Spot, front and next prices must be synchronized. Seasonal dividends, commodity delivery months and bond cheapest-to-deliver changes can make a mechanically calculated curve signal misleading.
- The author’s high portfolio Sharpes rely on a large and diverse instrument universe, historical costs and particular contract histories. Do not transfer those values to a handful of CFDs or to a short crypto sample.
- The extraction omits several formulas, including the double-V mapping and volatility-regime multiplier. Their exact rules remain **open questions for the book**, rather than parameters to guess.
- Median centering does not guarantee a neutral portfolio; volatility normalization does not ensure stable realized risk; and a favorable monthly skew does not establish favorable daily or annual tails.

# Part 3: strategies 21-27 (breakout, value, acceleration, skew, dynamic optimisation, fast mean reversion)

### Overview

Parts Three and Four add four directional forecasts, a portfolio implementation overlay and two fast mean-reversion strategies. Carver’s central preference remains a diversified collection of simple, economically interpretable rules, with turnover constrained by costs.

The breakout rule is a continuously sized trend forecast; value is five-year **relative** reversal; acceleration measures a change in trend; and skew is a case study in turning a statistic into a forecast. Dynamic optimisation addresses integer futures contracts in small accounts. The fast strategies depend heavily on plausible limit-order execution.

The author’s results are historical backtests, often for a leveraged portfolio of more than 100 futures. They are not estimates of what one of our markets should earn. His especially high Sharpe for safer fast mean reversion warrants his own explicit scepticism.

**Reading limitations:** The assigned text extraction omits several displayed equations and does not consistently expose printed page numbers. Strategy numbers below provide the requested lookup references; I have not reconstructed missing equations as established trading rules. The brief does not identify the “four failed strategies,” so comparisons below describe the distinction from the failed price-pattern, trend, breakout, gap and intraday families in the supplied context, rather than asserting a strategy-by-strategy comparison.

**Project context:** The current handoff confirms the two surviving streams and notes that VIX basis and two GSCI roll ideas have since failed. Goal 1 CFD signal screens are paused.

### Chapter notes

### Strategy 21 — Breakout

- Uses daily **back-adjusted closing prices** and rolling highs and lows over \(h\) business days. The raw signal locates the close in that range, mapping the low to −20 and the high to +20; an EWMA with span \(h/4\) smooths it. This is a continuous position, often entered before an actual breakout, rather than a binary breakout entry. The range itself supplies the volatility adjustment. (AFTS Strategy 21)
- Horizons are 10, 20, 40, 80, 160 and 320 days; respective forecast scalars are 0.60, 0.67, 0.70, 0.73, 0.74 and 0.74. The smoothing choice was arbitrary, followed by sensitivity checks.
- Jumbo results for those horizons, in order: net Sharpe **0.30, 0.83, 0.93, 1.10, 0.92, 0.96**; turnover **365.3, 170.3, 81.4, 42.4, 23.8, 15.2**; monthly skew **0.91, 1.29, 0.94, 0.69, 0.34, 0.39**. These include markets too expensive for the faster variants, making fast-rule costs particularly punitive.
- For the cost-filtered, equal-weighted combination: median instrument Sharpe **0.30**, turnover **16.1**, skew **0.85**; Jumbo Sharpe **1.17**, turnover **55.4**, skew **0.64**, annual costs **1.1%**. Equity futures had median Sharpe only **0.10**.
- Breakout and his trend combination correlate **0.97**. Adding breakout to trend and carry raises Jumbo Sharpe only from **1.27 to 1.29**; the apparent diversification is small. Carver regards it as a close relative of trend, not an independent mechanism.

### Strategy 22 — Value

- “Value” here is not an accounting valuation. It is a **five-year reversal in volatility-normalised performance relative to the instrument’s asset class**. Compute the instrument’s normalised price minus its asset-class normalised price; measure its change over roughly five years, reverse the sign, smooth with a 30-day EWMA, scale by **7.27** and cap. Forecast turnover is **8.7**. The extracted equations do not fully specify the normalised series or averaging denominator; consult the book’s Strategies 17–19 before implementation. (AFTS Strategy 22)
- Five years follows prior academic research. Carver says two- to four-year horizons were similar; he did not see a benefit from combining horizons. An alternative omits the most recent year, but he does not use it.
- Standalone Jumbo: net annual return **−1.0%**, Sharpe **−0.06**, turnover **11.7**, monthly skew **0.21**, costs **0.8%**. He reports positive median results in equity and bond futures, but stresses that a five-year horizon supplies very little independent evidence.
- Correlations with trend and carry were **−0.03** and **0.16**. A blend with 60% trend, 35% carry and 5% value lifted historical Sharpe **1.27 to 1.29**. Carver acknowledges selecting the small value weight to demonstrate improvement **in sample**; the increase is not a validated incremental edge.

### Strategy 23 — Acceleration

- Start with a scaled EWMAC trend forecast using fast span \(N\) and slow span \(4N\). Acceleration is its change over the preceding \(N\) business days. A positive change produces a bullish forecast even if the underlying trend is still negative. Apply a second scalar and the usual cap. (AFTS Strategy 23)
- He uses \(N=8,16,32,64\), with acceleration scalars **1.87, 1.90, 1.98, 2.05**. Faster 2- and 4-day variants are too costly. Adjacent acceleration variants have return correlations around **0.50–0.53**, below adjacent trend variants.
- Individual Jumbo variants \(8,16,32,64\): net Sharpe **0.20, 0.59, 0.43, 0.46**; turnover **258.8, 136.2, 81.6, 57.9**; monthly skew **0.97, 1.55, 1.11, 0.34**. These include all instruments regardless of cost.
- Cost-filtered combined acceleration: median instrument Sharpe **0.08**, turnover **24.9**, skew **0.94**; Jumbo Sharpe **0.72**, turnover **99**, skew **0.98**, annual costs **1.9%**. The large portfolio benefit is not evidence of comparable single-market profitability.
- Adding it to trend and carry produced Sharpe **1.29 versus 1.27**, skew **0.91 versus 0.76**, and turnover **59.1 versus 46.5**. The text’s subsequent reference to a 60% EWMAC allocation conflicts with its immediately preceding 30% trend/30% acceleration split; verify the intended weights before reproducing the blend.

### Strategy 24 — Skew: a case study

- Hypothesis: investors pay for positively skewed outcomes and avoid negatively skewed ones, creating compensation for holding the latter. This is a proposed risk premium, not a demonstrated compulsory counterparty. (AFTS Strategy 24)
- Calculate standard daily-return skew over **60, 120 and 240 business days**; take its negative, smooth each with EWMA span **15, 30 and 60**, respectively, scale and cap. A negative realised skew therefore produces a long forecast. Skew is already dimensionless.
- Rolling skew is highly sensitive to a few extreme returns entering and leaving the window. Carver suggests exponentially weighted or robust alternatives but tests the ordinary statistic. Smoothing the 60-day forecast cuts its turnover by about two-thirds.
- Individual Jumbo variants 60/120/240: net Sharpe **0.60/0.75/0.71**, turnover **43.6/25.6/18.1**, monthly skew **−0.40/0.01/−0.10**. Combined Jumbo: Sharpe **0.80**, turnover **23.9**, skew **0.14**, costs **0.9%**, beta **0.62**. Median instrument Sharpe was **0.26**.
- Combined-skew median Sharpe by asset class: equities **0.32**, volatility **0.09**, FX **0.16**, bonds **0.32**, metals **0.27**, energy **0.43**, agriculture **0.08**. Volatility instruments’ median strategy skew was **−2.21**; the volatility group contained only VIX and VSTOXX. A fixed short-volatility forecast had a higher reported median Sharpe, **0.32**, making the benefit of timing questionable.
- Adding skew to trend and carry raised historical Sharpe **1.27 to 1.38**, but beta rose **0.30 to 0.44** and monthly skew fell **0.76 to 0.62**. The strategy can carry a substantial equity-like long bias.
- Carver distinguishes absolute, historical-demeaned, instrument-relative, cross-sectional and asset-class variants. These select different risks and sources of return; testing every variation invites selection bias.
- He avoids generic calendar and cross-market prediction because many plausible market/date combinations create false discoveries. His scepticism of pension rebalancing is an opinion, not a refutation of our separately specified Treasury month-end mechanism.

### Strategy 25 — Dynamic optimisation

- This is a **position implementation overlay**, not a new return predictor. Given ideal fractional positions, choose integer contracts to minimise the volatility of tracking error versus the ideal portfolio. Use covariance of **underlying instruments**, rather than covariance of strategy returns. (AFTS Strategy 25)
- The described greedy search starts at zero, tries adding one contract at a time in the sign of each ideal position, takes the largest reduction in tracking error and repeats until no single permitted addition improves it. It can miss the global optimum; the sign restriction avoids some unstable proxy hedges.
- Volatility uses a **32-day EWMA**; correlation uses about **six months of weekly returns**. A cost penalty adds estimated trading costs multiplied by **50** to the objective; 50 was calibrated to produce costs comparable with the benchmark, with 10–100 reported as similar.
- After optimisation, compare current and desired portfolios in tracking-error volatility. With a 20% annual risk target, use a **1% tracking-error buffer**; trade partway toward the target if outside it, then round to contracts. Integer rounding means the final error need not equal the buffer.
- At $500,000, dynamic implementation across 100 potential futures reported Sharpe **1.22**, turnover **48.8**, skew **0.79** and 0.99 correlation to the $50 million Jumbo benchmark. A 27-instrument static portfolio had Sharpe **1.18**, turnover **32.1**, skew **0.19**.
- At $100,000, dynamic Sharpe was **1.06**, versus **1.11** for the observed 16-instrument static selection; it averaged seven positions and correlated **0.91** with Jumbo. Carver adjusts static Sharpe down to **0.73** to remove what he regards as fortunate instrument selection. That adjustment is a modelling claim, not an observed return.
- Constraints can freeze an unavailable instrument, prohibit certain holdings or force a closing position before a roll. At a roll, the optimiser can choose another market instead of automatically reopening the expiring exposure. This is a trading-cost decision, not a method for removing futures carry.

### Strategy 26 — Fast mean reversion

- Each day set equilibrium to a **five-business-day EWMA of completed daily back-adjusted closes**. During the following day, forecast proportionally to equilibrium minus the current price, divided by daily price volatility; scalar **9.3**, then cap and size. The strategy adjusts continuously in principle and is backtested hourly. No ordinary position buffer or fixed stop is used. (AFTS Strategy 26)
- Position is long below equilibrium and short above it; it reduces or reverses as the forecast changes. In a continuing trend it can repeatedly add to a losing position. Typical holding periods are one or two days.
- Execution is integral to the result: place one-contract buy and sell limits at prices corresponding to the next desired integer positions. Recalculate after fills; use market orders when the rounded desired position is more than one contract away, such as after a gap. The cap can eliminate the order that would increase exposure further.
- His hourly backtest assumes a limit order fills one hour later at its limit if the next price moves **through** the limit; market orders also lag one hour and pay spread. All orders pay commission. This is an assumption, not proof that real passive fills occur; queue position, adverse selection and gaps matter.
- Since 2013, median single-instrument Sharpe **0.41**, turnover **57.4**, skew **−0.82**. Asset-class median Sharpe: equity **0.54**, volatility **0.75**, FX **0.73**, bonds **0.44**, metals **0.19**, energy **0.04**, agriculture **−0.06**.
- Jumbo net return **17.6%**, Sharpe **0.80**, turnover **39.2**, monthly skew **−1.46**. The displayed **3.1% cost** is commission only; the author says net returns additionally account for market-order spread. It should not be interpreted as total execution cost.
- He could not find a profitable short-horizon directional trend rule even before costs in the tests described. He mentions options-dealer hedging as a proposed explanation in outside intraday research, without establishing it for his rule.

### Strategy 27 — Safer fast mean reversion

- Retain Strategy 26’s equilibrium and execution, but trade only when the mean-reversion forecast and daily **EWMAC(16,64)** trend forecast have the same sign. Close or suppress positions when they disagree; do not open the opposite mean-reversion position until it agrees with the trend. There is no fixed stop. (AFTS Strategy 27)
- Also reduce forecasts when relative volatility is high: compare current volatility with its rolling ten-year average and locate that relative level within its historical distribution. The exact quantile-to-multiplier equation is **missing from the extraction**, so the full strategy cannot be specified faithfully from this text alone. Scalar is approximately **20** after the trend filter; cap remains in force.
- Median instrument results: Sharpe **0.54**, turnover **81.9**, monthly skew **−0.57**, versus **0.41/57.4/−0.82** for pure mean reversion. Median Sharpe by class: equity **0.43**, volatility **0.60**, FX **0.54**, bonds **1.00**, metals **0.43**, energy **0.47**, agriculture **0.46**.
- Since 2013, Jumbo net annual return **31.6%**, Sharpe **2.14**, turnover **65.7**, monthly skew **1.36** and displayed commission costs **1.9%**. Again, the displayed cost excludes spread on market orders. Skew changes materially with measurement frequency: daily **0.25**, weekly **−0.36**, annual **−0.06**.
- Carver distrusts this Sharpe: the hourly history is short, limit fills are difficult to simulate, and the volatility overlay was added after examining the strategy. He warns that a small portfolio cannot be expected to diversify away the individual instruments’ negative skew.
- Dynamic optimisation from Strategy 25 is not suitable for this fast implementation. Carver suggests separate strategy books or accounts, or carefully netting slow-strategy orders against fast orders, with attribution and execution complexity.

### Topic tags

- **Trend and breakout:** Range-location breakout is almost the same return stream as his trend system; acceleration differs more, but trades more and costs more. (Strategies 21, 23)
- **Mean reversion:** Horizons matter: five-year relative reversal and one- to two-day reversal are different hypotheses. The latter’s returns depend on passive execution and can have severe crash exposure. (22, 26–27)
- **Volatility and risk:** High-volatility scaling and a trend-direction filter improved the author’s fast-reversion backtest, but did not remove the need to assess individual-market tails and correlated stress. (27)
- **Stops and exits:** The fast forecasts continuously resize; Strategy 27 exits on trend disagreement. These are not guarantees against gap losses. (26–27)
- **Position sizing and portfolio:** Integer-contract tracking, covariance, trading costs and a portfolio buffer matter when small accounts cannot hold fractional ideal positions. Correlations may change precisely when proxy positions are needed. (25)
- **Testing and robustness:** Perturb input prices and inspect whether forecasts and results change substantially; test sensitivity to windows, execution and allocations. A large menu of forecast transformations is itself a multiple-testing problem. (24–27)
- **Costs and execution:** Back-adjusted futures price changes should be divided by the **contemporaneous tradable contract price** when calculating percentage returns. For passive orders, model non-fills and adverse selection; a touched or crossed historical price is not an observed fill. (24, 26)
- **Seasonality:** Carver warns against searching many calendar effects. A pre-specified mandatory-flow mechanism is a stronger hypothesis than choosing the best month retrospectively, but still needs a properly powered test. (24)

### Testable ideas

★ marks relative priority for **research or an implementation check**, not a recommendation to spend a one-time test. None of the price-only rules establishes a counterparty that must trade.

1. **★ Trend-aligned fast mean reversion.** On completed daily data calculate the five-day EWMA and EWMAC(16,64); during the next day buy below equilibrium only in an uptrend, or short above it only in a downtrend. Scale toward equilibrium and exit when equilibrium or a conflicting trend signal calls for it; no fixed stop. Add the author’s volatility overlay only after recovering its missing equation. **Evidence:** Strategy 27, Jumbo Sharpe 2.14 with the substantial caveats above. **Fit:** Conditional: FTMO M1 and crypto can form hourly bars, but passive-fill modelling is weak without order-book data; include overnight CFD swap or perp funding. Available Treasury futures are daily, so cannot reproduce hourly execution. **Difference:** Continuous position sizing and trend filtering distinguish it from a discrete pattern or breakout, but it still faces the same intraday cost wall.

2. **★ Passive-fill stress test for the fast rules.** Reproduce Strategy 26’s five-day equilibrium and one-hour delayed, through-price limit assumption; compare it with pre-registered less favourable fill, spread, gap and adverse-selection scenarios, using the same signal and no fixed stop. **Evidence:** Strategy 26’s Jumbo Sharpe 0.80 depends on its execution model. **Fit:** Good as a *method check* on our M1 CFD and crypto histories, poor as proof of executable passive fills without order-book/queue data; include swap or funding for overnight holdings. **Difference:** Tests the execution assumption behind a fast-reversion hypothesis rather than searching another price pattern.

3. **★ Portfolio rounding with costs.** For an existing set of independently justified daily forecasts, calculate fractional targets, then use Strategy 25’s greedy integer tracking-error minimisation, cost penalty 50 and 1% tracking-error buffer at a 20% risk target. Rebalance as signals change; apply real contract limits and roll costs. **Evidence:** $500,000 dynamic Sharpe 1.22 against 1.18 observed static, with 0.99 correlation to Jumbo. **Fit:** Potentially good for a future multi-futures portfolio, but our current small set of futures and sparse per-contract history limit replication; CFDs and shares can have different lot constraints. **Difference:** An implementation overlay, not an alternative entry signal or a new edge. Include the financing or carry inherent to each venue.

4. **★ Skew risk-premium forecast.** At each completed daily close take the negative of rolling 60/120/240-day return skew; smooth over 15/30/60 days, scale using training data, combine affordable horizons and resize daily. Exit or reverse as the forecast changes; no fixed stop specified. **Evidence:** Strategy 24 combined Jumbo Sharpe 0.80, skew 0.14, turnover 23.9; VIX-class median Sharpe only 0.09 and skew −2.21. **Fit:** Technically feasible on CFD, Treasury, EIA, VIX, crypto and share returns, subject to data continuity, roll, fees, CFD swap and funding. Likely poor as a new VIX short thesis given the project’s failed VIX basis test and crash exposure; skew is a different signal, not a retest of that rule. **Difference:** A distributional risk-premium hypothesis rather than a chart pattern; control long beta and compare against simple static exposure.

5. **Continuous range-location trend.** Daily, locate the close within its previous 10/20/40/80/160/320-day closing range, map to −20…+20, smooth with span \(h/4\), scale and combine only affordable horizons. Continuously resize and reverse; no fixed stop specified. **Evidence:** Strategy 21 combined Jumbo Sharpe 1.17 but 0.97 correlation with trend. **Fit:** Computable on all listed daily series, with proper futures rolls and overnight CFD swap or crypto funding; likely poor priority after the project’s trend/breakout cost failures. **Difference:** Builds a position inside the range instead of entering only on a break; underlying trend exposure remains very similar.

6. **Trend acceleration.** Each day calculate EWMAC(\(N,4N\)), then its change over \(N=8,16,32,64\) days; scale, cap and combine affordable variants. Rebalance as the derivative changes sign; no fixed stop specified. **Evidence:** Strategy 23 combined Jumbo Sharpe 0.72, turnover 99 and skew 0.98. **Fit:** Data are broadly available, but high turnover makes CFD spread and swap or crypto fees and funding material. Treasury and EIA futures require credible rolling and contract costs. **Difference:** Trades changes in trend strength rather than a breakout event, but remains a price-only hypothesis with weak median-market evidence.

7. **Five-year within-class reversal.** Compare each instrument’s volatility-normalised five-year performance with its asset-class average, reverse the relative move, smooth for 30 days and continuously resize. No fixed stop is given. The exact normalisation must be recovered before implementation. **Evidence:** Strategy 22 standalone Jumbo Sharpe −0.06; reported positive equity- and bond-futures medians have very few independent long-horizon observations. **Fit:** Poor near-term research priority: limited independent five-year episodes, changing share universes and asset-class definitions; include multi-year swap/funding and futures roll. **Difference:** Slow cross-sectional reversal rather than intraday price patterns, but it lacks a specific forced-flow mechanism and the author’s portfolio weight was fitted in sample.

### Warnings / pitfalls

- **Carry and roll are venue-specific.** Back-adjusted futures data must preserve economically correct tradable returns and roll treatment; the change in a continuous chart is not automatically the return of a held contract. FTMO CFD swap is mostly the futures carry in this project’s convention: removing it while retaining CFD prices does not create a futures backtest. Crypto funding and share financing or borrow costs likewise belong to their respective venues.
- The book’s aggregate Sharpe, turnover and skew are portfolio statistics, often using leverage and more than 100 markets. They cannot be transferred directly to our much smaller universe. Turnover is also expressed relative to average position, so higher turnover does not necessarily imply higher cash costs.
- The 2013-onward fast-strategy history is short for rare crises. Passive fills inferred from hourly prices, absent queues and order-book history, are a major source of optimism. Stress non-fills and price gaps before interpreting any apparent edge.
- Carver’s strategy and blend selection involved examination of results. His 5% value allocation and later volatility overlay are particularly clear examples; our pre-registration, power check and multiple-testing ledger remain necessary.
- Standard rolling skew can be dominated by one extreme observation. Apparent improvement from risk filters or diversification should be checked across measurement intervals, instruments and stressed correlations.
- **Open rule detail:** the extraction omits Strategy 27’s volatility-multiplier formula and portions of the value normalisation; the Strategy 23 blend text also conflicts on trend weight. These need the original equations or an authoritative source before faithful reproduction.

# Part 4: strategies 28-30 and tactics (spreads, triplets, calendar trading, rolling, execution, cash, risk)

### Overview

Parts Five and Six extend Carver’s futures framework to relative-value trades and the practical management of a futures account.

- Strategies 28–30 treat a spread or butterfly as a synthetic instrument, then apply trend or carry forecasts to it.
- The hedge reduces ordinary price variation but can require large gross positions. Changing correlations, fat tails, costs and integer contracts can make the apparent risk reduction misleading.
- The limited results are generally weaker than outright futures trading. The oil crack is the strongest of the three cross-instrument triplets examined; it is also highly correlated with outright oil.
- Calendar spreads and butterflies often sit near an equilibrium for long periods, interrupted by abrupt changes in that equilibrium. Neither trend nor carry consistently handles both regimes well.
- The tactics chapters add concrete guidance on contract selection, rolling, execution, cash, and portfolio risk controls.
- The extracted text does not reliably preserve book page numbers or several equations. References below therefore use strategy numbers or named tactics and tables. Rules whose precise equations or defaults are missing are identified as incomplete.

### Chapter notes

### Strategy 28 — Cross-instrument spreads

- A synthetic spread is long \(R\) units of instrument A and short one unit of B, with contract multipliers and currencies accounted for when translating the weights into actual contracts. Its price can be zero or negative, so risk is measured in **price changes**, not percentage changes.
- Carver’s practical fixed hedge ratio uses the ratio of the two instruments’ daily price-change standard deviations, averaged over roughly ten years and rounded to a convenient ratio. He cautions that fixed ratios are imperfect and can leave outright exposure. His reasoning for dropping correlation from the ratio is a heuristic; the result should not be treated as the general minimum-variance regression hedge.
- The 5-year/10-year Treasury example uses 1.5:1. With $500,000, a 10% risk target and an average forecast, the estimated position is approximately +29.5 five-year and −19.7 ten-year contracts; gross notional is about $5.6 million. A modest fall in the assumed correlation from 0.961 to 0.86 nearly doubles estimated spread risk.
- He suggests a 10% annual risk target for relative value, while warning that even this can be aggressive. The 32-day volatility estimate and longer-run blend still apply, but the synthetic instrument’s own price-change volatility is the relevant input.
- Both legs’ execution costs matter. The example 5-year/10-year spread has approximately eight times the risk-adjusted cost of either outright leg. Buffer the base leg, derive the matching other-leg trade, and execute close together.
- Integer hedge ratios can materially increase minimum capital. For example, a 1.5:1 contract ratio requires at least three contracts against two; Carver estimates over $200,000 minimum capital for his example.
- Choose economically related instruments before inspecting performance. An exhaustive search over thousands of pairs invites a story to be invented after the fact. Refining relationships are more defensible than coincidental correlations; historical correlations and production relationships can still change.
- **EWMAC16,64 on ten US Treasury maturity spreads:** Sharpe ranged from −0.12 to 0.40, versus 0.30–0.64 for the five outright maturities. Spread skew ranged 0.90–6.40, but lower-tail ratios were high at 3.01–3.75. Strategy-return correlations with outright 10-year trend were 0.10–0.39. Results have unequal sample lengths; the 30-year series was particularly short. Turnover is not reported in these spread tables. (AFTS strategy 28, tables 147–150.)
- **Carry60 on those spreads:** Sharpe ranged −0.13 to 0.25, mostly near zero, versus 0.20–0.57 for outright bonds. Spread skew ranged −0.93 to 1.04; correlations with outright 10-year carry were −0.50 to 0.07. Carver regards the diversification as insufficient compensation for weak performance. Turnover is not reported. (Strategy 28, tables 151–154.)
- Spread carry combines the carry of the actual legs with their hedge weights, using matched roll conventions. Unsynchronised schedules distort the estimate. A CFD implementation must include both legs’ actual swap; removing swap does not create an exchange-futures equivalent.

### Strategy 29 — Cross-instrument triplets

- A long butterfly is long weighted wings A and C and short middle B: synthetic price \(X P_A-P_B+Y P_C\). For similar adjacent correlations, the proposed wing weights approximate half the middle-to-wing price-volatility ratio. Multipliers and currency conversion determine the actual contract counts.
- The Treasury example uses synthetic weights 1.5 on 2-year, −1 on 5-year and 0.25 on 10-year; contract counts are +0.75, −1 and +0.25 respectively. Integer implementation requires a multiple of four middle contracts. With $500,000 and 10% target risk, its illustrative gross notional is $10.4 million.
- Carver tests three economically interpretable butterflies: US 2/5/10-year yield curvature, soybean crush and oil refining crack. The latter two use industry conventions; the Treasury weights blend historical estimates and duration judgment.
- His table gives risk-adjusted costs of 0.0118 for the Treasury butterfly, 0.00169 for soy crush and 0.000856 for oil crack; indicative minimum capital is $172,000, $1.9 million and $850,000 respectively. These are historical examples, not current executable quotes. (Strategy 29, tables 159–160.)
- **EWMAC16 results, Treasury / soy / oil:** Sharpe **−0.07 / 0.14 / 0.46**; skew **1.20 / 1.26 / 1.14**; turnover **13.0 / 14.5 / 14.7**; annual cost **1.13% / 0.3% / 0.1%**. Lower-tail ratios are **4.16 / 3.97 / 3.72**. Correlation with trend on the middle instrument is **0.36 / 0.96 / 0.92**. (Table 161.)
- **Carry60 results, Treasury / soy / oil:** Sharpe **0.19 / 0.09 / 0.62**; skew **−0.07 / 0.07 / 0.85**; turnover **10.0 / 7.3 / 7.1**; annual cost **0.8% / 0.1% / 0.1%**. Correlation with carry on the middle instrument is **0.23 / 0.96 / 0.75**. (Table 162.)
- The oil crack is the standout in this small selection, but Carver explicitly warns against extrapolating from three triplets and one rule. He suggests fast mean reversion as an untested possibility; near-simultaneous execution across three markets would be difficult.

### Strategy 30 — Calendar spreads and triplets

- Calendar trades use expiries of the **same** future. A long spread holds +1 near contract and −1 later contract. A long butterfly holds +1 near, −2 middle and +1 far: a trade on curve curvature rather than slope. Roll all legs together to preserve the intended structure.
- Carver’s examples include VIX, Eurodollar and WTI. Table 163 specifies VIX spread **3rd/4th**, VIX butterfly **2nd/3rd/4th**, Eurodollar **8th/10th/12th quarterly**, and WTI spread **2nd/8th** or butterfly **2nd/8th/14th** monthly contracts.
- **Source inconsistency:** preceding prose describes WTI as contracts 2/3/4, while table 163 and later discussion describe more widely spaced contracts. Do not infer which produced the reported WTI results without checking the book’s original figures or implementation.
- A spread can often execute as one exchange order, reducing leg risk and potentially cost. A butterfly requires at least two middle contracts under the 1:−2:1 convention. Closely spaced expiries reduce synthetic volatility but increase gross leverage and cost per unit of risk.
- **EWMAC16 calendar spreads, VIX / WTI / Eurodollar:** Sharpe **−0.14 / 0.15 / 0.13**; skew **4.29 / 2.32 / 2.59**; turnover **9.9 / 9.6 / 11.7**; annual cost **1.6% / 0.1% / 2.2%**. Lower-tail ratios are **5.8 / 6.7 / 3.60**. (Table 165.)
- **Carry60 calendar spreads, VIX / WTI / Eurodollar:** Sharpe **−0.12 / 0.27 / −0.06**; skew **0 / 0.84 / 0.73**; turnover **12.4 / 7.82 / 9.3**; annual cost **4.3% / 0.1% / 2.4%**. (Table 166.)
- **EWMAC16 calendar butterflies, VIX / WTI / Eurodollar:** Sharpe **0.12 / −0.37 / −0.87**; skew **1.49 / −2.53 / 0.47**; turnover **8.6 / 7.9 / 8.1**; annual cost **2.9% / 0.1% / 3.9%**. (Table 167.)
- **Carry60 calendar butterflies, VIX / WTI / Eurodollar:** Sharpe **−0.16 / −0.02 / −0.04**; skew **−0.54 / −0.15 / 5.28**; turnover **15.1 / 8.1 / 7.4**. Table 168 prints WTI cost as **+0.1%**, an apparent sign inconsistency with the other cost entries; it should not be silently corrected.
- Carver observes long mean-reverting periods punctuated by changes in equilibrium. He proposes, without testing here, a combination of fast mean reversion and trend. Positive skew does not eliminate dangerous lower tails.

### Tactic 1 — Contract selection and rolling

- Apply liquidity filters to each expiry, using 30-day average volume: at least **100 contracts/day** and approximately **$1.25 million/day of risk-adjusted volume** in Carver’s examples. These are screening thresholds, not proof that a particular order can be filled at an assumed cost.
- Expiries differ in volatility, liquidity and tail risk. The front VIX contract is particularly jumpy; the author generally avoids it. Short-rate futures can instead have exceptionally quiet front contracts and event-driven jumps.
- Where liquidity permits, holding a fixed calendar month can reduce seasonal contamination of carry. Carver uses December WTI as an example. If holding a later expiry, he prefers estimating carry against a nearer expiry; a front holding requires a farther expiry or another reference.
- Physically delivered contracts must be rolled before the relevant broker deadline and, for long positions, before first notice where applicable. Even cash settlement can create settlement-window risk. The author recounts that correcting Treasury roll dates to precede first notice lowered a historical continuous-series return.
- A quoted calendar-spread roll can reduce execution cost and avoid one-leg fills. **Passive rolling** closes reductions in the old expiry and places increases in the new expiry; roll any residual before the deadline. It saves incremental roll trades but temporarily mixes expiries and introduces basis differences.
- For a liquid, distant short-rate contract, his illustration holds within a one-to-three-year maturity window and potentially rolls every two years instead of quarterly. This is an instrument-specific example, not a universal default.
- Changing expiry can change volatility abruptly. Estimating risk solely from a continuous history can hide the change; a moving estimate dampens, rather than eliminates, this issue.

### Tactic 2 — Execution

- Record regularly sampled bid/ask spreads, the spread and order size at submission, and actual fill versus submission midpoint. The three series answer different questions: expected cost, opportunity at the time of trading, and realised execution.
- Costs vary by time, event, order size and participation. Carver suggests avoiding thin opening/closing periods in many futures, major releases and holiday liquidity; this is a general caution, not a substitute for instrument-specific measurement.
- His illustrative execution algorithm starts with a passive limit at the bid for a buy or ask for a sell. It switches to aggressive execution after an adverse midpoint move, an order-book imbalance exceeding **5:1**, or **five minutes**. The text’s wording around the imbalance example is inconsistent, so the direction of that condition requires verification before implementation.
- In his own September 2020–April 2022 sample, estimated market-order spread cost was just over **3.6% of capital**, versus about **3.0%** realised with the algorithm: approximately **0.6 percentage points** saved. This is an observational account-specific result, not an expected saving for our data.
- Passive fills can be adversely selected and delayed; compare with the price available when the decision was made, including missed or delayed fills. Our candle data lacks the order book needed to reproduce his imbalance rule.
- For fast mean-reversion systems, precomputed limit-order ladders reduce reaction requirements but expose information, can accumulate fees and can fill at poor prices after overnight jumps. Carver generally avoids leaving the ladder active overnight.

### Tactic 3 — Cash and compounding

- Futures require both initial margin and free cash for variation margin. A seemingly profitable portfolio can be forcibly reduced if losses or increased margin requirements exhaust available cash.
- Carver prefers fully funding the intended trading capital and retaining readily available cash. Investing margin reserves in bond funds or risk assets adds market and liquidity risk precisely when cash may be needed.
- Foreign-currency collateral creates a choice between currency conversion and borrowing. Conversion incurs FX exposure; borrowing incurs financing charges. His preference is conversion and regular return of excess balances to the base currency, accepting the residual FX noise.
- Published backtests use fixed notional capital for interpretable, non-compounded returns; he warns against keeping position sizes fixed after real losses.
- His “half compounding” caps strategy capital at the original amount, withdraws or segregates gains above that cap, and reduces strategy capital after losses. It is a withdrawal policy with path dependence, not a guarantee of safety or a source of alpha.

### Tactic 4 — Risk management

- Specify the measurement, trigger, action and reversal before a margin problem. His illustration raises concern at **50%** margin usage, acts at **60%**, and reduces exposure toward **50%**; these are examples, not FTMO rules.
- His portfolio overlay takes the smallest of four multipliers, each capped at one: normal estimated portfolio risk, stressed volatility or “jump” risk, adverse correlation risk, and gross leverage. Apply it to unrounded desired positions before buffering.
- For his diversified trend/carry portfolio, illustrative limits are **30%** normal annualised risk, **75%** stressed-volatility risk, **65%** adverse-correlation risk and **20×** gross leverage. They were chosen around historical 99th percentiles for that portfolio and must not be transplanted to ours.
- For the volatility stress, use each instrument’s historical 99th-percentile volatility with the existing correlation estimate. For the correlation stress, assume correlations move in the direction most adverse to the current signed positions; aggregate the absolute individual risk contributions. Historical thresholds in a backtest must use information available at that time.
- The overlay activated just under **5%** of the time. In the author’s sample, Sharpe changed from **1.32 to 1.33**, annual volatility from **20.7% to 20.5%**, and lower-tail ratio from **1.88 to 1.84**. It did not activate during the 2020 COVID crash or early-2022 invasion, so the historical result is not proof that it covers future crises. (Table 171.)
- Extremely low estimated volatility can produce extreme leverage. His front-Eurodollar illustration requires about **81.6×** notional exposure at a 20% target. He recommends avoiding such instruments, limiting leverage per instrument, or using an expiry with more appropriate risk.
- Hard position limits can take the minimum of a maximum-forecast limit, an instrument leverage limit and a fraction of open interest. His example uses a 50% allowance above the calculated maximum-forecast position and, for large traders, a possible 1% open-interest limit.
- Hard daily and weekly trade limits can detect operational failures and abnormal turnover. His slow-strategy illustration uses approximately one-third of the maximum position per day; a faster strategy needs a different allowance.

### Appendix B — Calculations relevant to this range

- Additive back-adjustment removes roll-price jumps by adding the difference between old and new contracts to the earlier history. Maintain an actual-contract ledger for P/L and rolls; an adjusted series alone does not establish executable returns.
- For negative or near-zero prices, Carver recommends price-change volatility and, where a percentage representation is necessary, a consistent positive reference price. The same reference must be used consistently in the sizing calculation.
- For portfolio covariance, he suggests a roughly six-month exponentially weighted correlation estimate, often on weekly returns to reduce mismatched market-close effects, combined with a faster volatility estimate. Correlation and volatility estimates must be point-in-time.

### Topic tags

- **Trend:** EWMAC16,64 can be applied to synthetic spread prices; its strong positive skew in some calendars accompanies long losing stretches and large tails. Strategies 28–30.
- **Mean reversion:** Calendar curves and production spreads provide economic reasons to investigate reversion, but equilibria can shift. The fast-reversion and hybrid suggestions are hypotheses, not demonstrated results. Strategies 29–30.
- **Seasonality/time:** Futures expiry choice changes seasonal exposure and carry; fixed-month WTI is one proposed control. Roll deadlines affect realised history. Tactic 1.
- **Volatility:** Closely hedged legs can have tiny measured volatility and enormous gross leverage. Expiry-specific volatility and its term structure matter. Strategies 28–30; tactics 1 and 4.
- **Position sizing/risk:** Size from synthetic price-change risk, respect contract granularity, stress both volatility and correlations, and impose instrument-level and operational limits. Strategies 28–30; tactic 4.
- **Testing and robustness:** Preselect economically related pairs; account for different histories, changing contract composition, roll feasibility and point-in-time stress calibration. Strategies 28–30; tactic 4.
- **Costs/execution:** Count all legs, actual roll trades, spread, commissions and delayed or missed execution. Calendar combination orders can differ materially from individual-leg costs. Strategies 28–30; tactics 1–2.
- **Portfolio/diversification:** Low correlation can diversify a portfolio, but low or negative standalone expectancy still matters. Commodity triplets can retain substantial outright exposure. Strategies 28–29.
- **Psychology/discipline:** Set margin triggers and corrective action before stress; keep sufficient liquid collateral. Tactics 3–4.

### Testable ideas

The stars mark the most useful **research or infrastructure candidates**, not an endorsement of expected profitability. Where the extracted equations or an author default are unavailable, a precise implementation needs the original formula or a separately preregistered choice.

1. **★ Energy calendar slope trend.** Construct a daily, synchronized, additively adjusted +1 near/−1 later energy-futures spread; apply EWMAC16,64, reverse when the forecast changes sign, and roll both legs together. The book’s WTI choice conflicts between 2/3 and 2/8, so choose only after resolving the source or explicitly preregistering a different specification. No separate stop is specified; risk is managed through the forecast and volatility sizing. **Evidence:** WTI calendar-trend Sharpe 0.15, skew 2.32, turnover 9.6, cost 0.1% annually, subject to that contract ambiguity. **Fit:** EIA contracts 1–4 may support a *different adjacent-curve variant* if dated prices, roll mapping and timing are adequate; they cannot reproduce 2/8. Model exchange spread, fees and rolls. This is relative-curve trend, but still a trend family and needs a mechanism and a fresh trial ledger. (Strategy 30, table 165.)

2. **★ Energy calendar carry.** Hold +1 near/−1 later or its reverse according to a 60-day-smoothed, risk-adjusted carry forecast for the synthetic spread; resize with the forecast and roll both legs together. The extracted equations and WTI expiry conflict prevent an exact replication from this text alone. **Evidence:** WTI spread carry Sharpe 0.27, skew 0.84, turnover 7.82 and annual cost 0.1%. **Fit:** Contracts 1–4 may permit an explicitly different adjacent-contract study, contingent on sufficient nearer contracts to calculate carry and executable cost assumptions. This measures relative roll yield rather than the already spent GSCI roll event; it nevertheless shares curve exposure and needs a distinct causal case. (Strategy 30, table 166.)

3. **★ Energy calendar butterfly.** Form +1 second, −2 third, +1 fourth monthly contracts; run daily EWMAC16,64 or, as a **separate registered trial**, carry60; reverse and roll all legs together. These adjacent WTI expiries appear in the prose, whereas the table uses 2/8/14, so this is not a reliable reproduction of the reported test. **Evidence:** reported WTI butterfly trend Sharpe −0.37, skew −2.53, turnover 7.9; carry Sharpe −0.02, skew −0.15, turnover 8.1, with the printed cost-sign inconsistency noted above. **Fit:** Potentially feasible with EIA 1–4, subject to dated-contract quality, realistic fills and capital. It tests curvature, not a directional breakout or the GSCI roll window. (Strategy 30, tables 167–168.)

4. **★ Risk-overlay counterfactual.** On an existing daily portfolio, compute normal covariance risk, high-volatility stress, adverse-correlation stress and gross leverage using only prior available observations; scale desired positions by the smallest capped multiplier, then apply executable rebalancing costs. Use Carver’s portfolio-specific limits only as a reference; preregister limits appropriate to the tested portfolio. **Evidence:** his sample Sharpe 1.32→1.33 and lower-tail ratio 1.88→1.84, with no activation in two named crises. **Fit:** Good for existing multi-asset return and position histories; test the overlay as risk control rather than a new edge. For CFDs include swap in strategy returns; for perps include funding. It differs from the spent signal families and can complement the existing T-25 stress work. (Tactic 4, table 171.)

5. **★ Futures roll-date and execution sensitivity.** For the existing Treasury month-end implementation, compare the preregistered feasible next-contract holding and actual roll deadlines against alternatives using dated contract prices, first-notice constraints, fees and spread; measure how much results change. Do not treat a more profitable roll date chosen after inspection as a new discovery. **Evidence:** Carver reports that correcting a Treasury series to roll before first notice reduced its historical upward drift; he gives no strategy Sharpe for this anecdote. **Fit:** Good operational question for I-109, but the available continuous ZN series alone cannot establish contract-level fill or roll economics. It validates a live candidate rather than repeating month-end index flow. (Tactic 1, “Does it matter when you roll?”)

6. **VIX calendar slope or butterfly.** For the spread use +1 third/−1 fourth VIX expiry; for the butterfly use +1 second/−2 third/+1 fourth. Run EWMAC16,64 or carry60 as separate trials, reverse according to forecast, and roll all legs simultaneously. **Evidence:** spread trend/carry Sharpe −0.14/−0.12; butterfly trend/carry 0.12/−0.16, with substantial costs above. **Fit:** Depends on dated VIX contracts and tradable combination costs. This is related to the already falsified VIX-basis idea; do not relabel it as independent without a clearly different mechanism and ledger entry. (Strategy 30, tables 165–168.)

7. **Cross-instrument relative trend or carry.** Select an economically justified pair in advance, fix a sensible hedge ratio from prior data, calculate a synthetic daily price, and trade EWMAC16,64 or carry60 with coordinated leg changes. Exit or reverse as the forecast changes; no separate stop is given. **Evidence:** Treasury spread trend Sharpe −0.12 to 0.40; carry −0.13 to 0.25. **Fit:** Treasury reproduction needs additional dated Treasury maturities; a CFD or share-pair adaptation would be a different test with both legs’ financing, borrow and execution costs. Avoid treating the historical correlation search as evidence of a causal edge. (Strategy 28.)

8. **Refinery crack trend or carry.** Construct the author’s industry-weighted gasoline/WTI/heating-oil triplet and trade EWMAC16,64 or carry60 as separate tests. The extracted table does not preserve enough contract-definition detail to certify the exact legs and price-unit conversions; check the source before replicating. **Evidence:** trend Sharpe 0.46 and carry 0.62, with turnover 14.7 and 7.1 respectively; correlations to outright middle-leg strategy 0.92 and 0.75. **Fit:** Plausible only if EIA data includes synchronized dated contracts for all products at suitable maturities; practical execution requires all three legs and substantial capital. It is a refining relationship rather than an intraday pattern, but its high outright-oil correlation limits diversification. (Strategy 29, tables 159–162.)

9. **Calendar mean-reversion/trend hybrid.** Carver suggests combining a fast mean-reversion rule with trend on calendar spreads or butterflies, but provides no entry threshold, exit, stop, allocation or results in this chapter. **Evidence:** hypothesis only; his stated motivation is alternating stable equilibria and abrupt shifts. **Fit:** EIA adjacent contracts might support research, but this is not a complete strategy specification and must not be coded as the author’s exact rule. It would be distinct from gap fading, while still carrying substantial multiple-testing and regime-selection risk. (Strategy 30, conclusion.)

### Warnings / pitfalls

- **Carry is not a free roll-price jump.** Calculate P/L on held contracts and account for actual roll execution. FTMO CFD swap is largely the carry embedded in futures economics; removing it from CFD results is not a valid futures cost model.
- **Synthetic hedges can fail together.** Low recent spread volatility can drive leverage to dangerous levels just before correlation or volatility changes. Stress both legs and liquidity, not only the synthetic standard deviation.
- **Do not infer causality from a good pair or butterfly.** The oil crack is economically interpretable, but three examples and many potential combinations are weak evidence; its returns also closely track outright oil.
- **Avoid future information in research.** Estimate hedge ratios, risk limits, contract selection, correlations and roll schedules using only information available at each decision point. Revised back-adjusted history requires care when signals use price levels.
- **Reported Sharpe, skew and turnover are author-sample figures.** The books’ tables mix instruments and histories; costs and liquidity are historical assumptions. Fat tails and a few crisis observations can dominate skew and performance.
- **Data granularity limits execution claims.** Daily EIA prices, continuous Treasury series and candles do not demonstrate simultaneous fills, spread-market liquidity, bid/ask costs or order-book imbalance. Missing dated expiries prevent exact replication.
- **Source issues remain:** WTI calendar expiry descriptions conflict; the WTI butterfly carry-cost sign is inconsistent; some extracted equations and page numbers are absent; the execution imbalance wording needs checking. None should be guessed into a trading rule.


