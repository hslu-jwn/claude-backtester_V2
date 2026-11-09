# R006 post-saturation evidence update

Date: 2026-11-03  
Decision: **record one new primary source; do not reopen candidate discovery or create a draft.**

## Source actually opened

Saketh Aleti, Tim Bollerslev, and Mathias Siggaard, “Intraday Market Return Predictability
Culled from the Factor Zoo,” *Management Science* 71(9), 2025, pp. 7731–7751,
DOI `10.1287/mnsc.2023.01657`. Full text opened at
https://public.econ.duke.edu/~boller/Papers/MS_2025.pdf on 2026-11-03.

The study predicts the next 15-minute aggregate U.S. market return from lagged high-frequency
returns on 272 portfolios: 218 characteristic portfolios, 48 industries, and six standard
factors. Regularized machine-learning models and a continuous-versus-jump decomposition are then
used to trade SPY. The reported 2004–2020 out-of-sample intraday strategies include quoted-spread
costs and a fixed borrow charge; the strongest ensemble/selection variants have positive net
returns and Sharpe ratios above one.

## Admission-gate audit

1. **Unsupported causal inputs:** V2 has no point-in-time constituent security master, the 272
   synchronized portfolio return series, ETF execution, or the paper's jump/continuous and ML
   model pipeline. A single-index OHLC proxy would change the estimand.
2. **Day-flat transfer is not exact:** the paper fixes the position entering the first interval to
   one because the strategy is long SPY overnight. Its intraday performance excludes the
   overnight return, but a flat-at-open implementation would have different initial position and
   turnover costs.
3. **No modern untouched confirmation:** the factor data end in 2020 and the reported trading
   evaluation ends in 2020. The 2021–2026 regime is not an untouched validation sample in the
   opened paper.
4. **Multiplicity/model scope:** the evidence is a high-dimensional forecasting system across
   several models and position mappings, not one predefinable OHLC-only mechanical rule that can
   enter the current stop-defined intake without reinterpretation.

The paper is strong adjacent evidence that cross-sectional information can predict an aggregate
intraday return after estimated equity-market costs. It does not satisfy R006's admission rule for
a supported V2 symbol or justify building an index-CFD approximation. The territory is therefore
parked as unsupported high-dimensional equity data, with no strategy specification, parameter
grid, run, or holdout access.

## Search boundary

The bounded update also surfaced opening-gap FX, first-30-minute Nikkei, Chinese commodity-futures,
NBBO event-time S&P 500, and proprietary retail-alpha leads. They were not registered as opened
primary support: the first two violate the opening exclusion, the commodity market is unsupported,
the NBBO horizon/input does not transfer to M1 CFDs and overlaps shock response, and the retail
paper is not an independent academic source. No conclusion here relies on those leads.
