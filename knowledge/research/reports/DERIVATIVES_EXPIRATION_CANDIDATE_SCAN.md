# Derivatives-expiration intraday candidate scan

Date: 2026-11-02  
Decision: **reject for the current M1 CFD mandate; the source-matched effects require option-state
data or opening/settlement execution, and transferable modern evidence is null or adverse**.

## Candidate boundary

The screened territory was a predetermined option/futures-expiration calendar effect in a single
equity-index instrument. Admission required a fixed direction observable without local parameter
search, a causal entry after the excluded U.S. opening hour and before the excluded final 30
minutes, persistence beyond one M1 bar, and plausible net margin. Volatility or volume alone did
not qualify as a directional strategy.

## Primary evidence

- Benjamin Golez and Jens Carsten Jackwerth, “Pinning in the S&P 500 Futures,” *Journal of
  Financial Economics* 106(3), 2012, 566–585,
  [DOI/publisher record opened](https://doi.org/10.1016/j.jfineco.2012.06.010),
  [full working paper opened](https://www.uni-konstanz.de/FuF/wiwi/workingpaperseries/WP_Jackwerth-Golez-12-10.pdf).
  Nearest-maturity S&P 500 futures settled unusually near option strikes on serial option
  expirations in 1987–2009. The prediction is distance and side relative to the live at-the-money
  strike, not an unconditional return sign. The paper uses futures/options settlement, strike,
  volume, open-interest, and exercise data; it reports no executable OHLC strategy net of costs.
  Crucially, it finds no pinning for quarterly futures expirations and no pinning in the S&P 500
  cash index from serial SPX expiration.

- Hans R. Stoll and Robert E. Whaley, “Expiration-Day Effects: What Has Changed?,” *Financial
  Analysts Journal* 47(1), 1991, 58–72,
  [publisher abstract opened](https://rpc.cfainstitute.org/research/financial-analysts-journal/1991/expiration-day-effects-what-has-changed),
  DOI `10.2469/faj.v47.n1.58`. In two-and-a-half-year windows before and after the June 1987
  settlement change, the quarterly reversal shifted from the close toward the open. Monthly
  non-quarterly effects were neither statistically changed nor large. The relevant effects are
  therefore concentrated in the exact opening/closing windows excluded by this program.

- Caihong Xu, “Expiration-Day Effects of Stock and Index Futures and Options in Sweden: The Return
  of the Witches,” *Journal of Futures Markets* 34(9), 2014, 868–882,
  [abstract opened](https://doi.org/10.1002/fut.21620). A contractual change aligning index and
  single-stock expirations created a natural comparison. The paper finds hardly any expiration-day
  effect before or after the change, aside from higher volume; no intensified volatility or price
  distortion survives. The opened abstract does not report the sample dates or an executable
  cost-adjusted strategy.

- Guglielmo Maria Caporale and Alex Plastun, “Witching Days and Abnormal Profits in the US Stock
  Market,” *Cogent Economics & Finance* 11(1), 2023, 2182016,
  [full article opened](https://doi.org/10.1080/23322039.2023.2182016). Daily index data for the Dow,
  S&P 500, and Nasdaq span 2000–20 September 2021. Their rule sells at the **start** of a witching
  day and closes at the end; S&P 500 prices fell on 57% and Nasdaq prices on 67% of those days.
  The authors explicitly omit spreads, fees, swaps, and other transaction costs. This is an
  open-to-close daily rule, not evidence for a post-opening, pre-final-30-minute subwindow.

## Admission-gate assessment

1. **Independent estimand: conditional pass.** Calendar expiration is distinct from generic shock
   response, but strike-relative pinning is an options-state effect rather than an OHLC rule.
2. **Transferable primary evidence: fail.** Quarterly S&P futures pinning is null; Swedish evidence
   is nearly null; the positive U.S. daily result uses index opens and closes.
3. **Causal supported inputs: fail.** The strongest mechanism needs contemporaneous option strikes,
   contract expiration class, open interest, volume, and settlement conventions absent from the
   supported OHLC contract.
4. **Executable horizon: fail.** The documented reversals and daily strategy are tied to the
   excluded open or close. Moving entry to 10:30 and exit to 15:30 New York would create an
   unsupported new estimand.
5. **Cost feasibility: fail.** The only recent directional simulation omits all transaction costs;
   the pinning study is not a trading P&L test.
6. **Modern stability: fail.** The 2014 natural experiment is broadly null, while the 2023 result
   supplies no untouched post-2021 test and conflicts across indices in strength.
7. **Bounded multiplicity: fail.** Expiration class, option market, nearest strike, side of strike,
   entry time, exit time, and index would form a large rescue grid without source-matched inputs.

## Decision

Create no expiration-day strategy, midday adaptation, strike-distance proxy, or clock grid. The
calendar alone identifies possible flow pressure but not a supported directional signal. Do not
replace missing option strikes with round-number distance or infer dealer gamma from OHLC.

Reconsider only if an independent modern study predefines a post-opening and pre-close interval on
a supported index future or faithful CFD proxy, reports a fixed direction net of executable costs,
and does not require option-chain or settlement fields absent from the contract.
