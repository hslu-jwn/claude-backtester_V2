# R-2026-003 - London-fix FX postfix reversal

Status: development failed and rejected on 2026-10-29; final holdout prohibited.

## Published evidence

Krohn, Mueller, and Whelan, *Foreign Exchange Fixings and Returns around the Clock*, Journal of
Finance 79(1), 2024, DOI `10.1111/jofi.13306`, is the primary source inspected. Using high-frequency
data for the G9 currencies from January 1999 through December 2019, the paper reports that the
U.S. dollar appreciates before major fixes and depreciates afterward. The turning point follows
the 16:00 Europe/London fix; the postfix pattern appears in spot, forwards, CME futures, ICE dollar
index futures, and interdealer VWAP data. The paper excludes transaction costs from its headline
return series.

Direct source: https://doi.org/10.1111/jofi.13306

The paper's transaction-cost analysis is adverse to an aggressive retail-style implementation:
an unconditional liquidity demander has negative reversal returns after bid/ask costs, while a
dealer acting as a liquidity provider can retain positive returns. This is not a detail to optimize
away; it is the central economic rejection risk for the V2 CFD adaptation.

As corroborating institutional evidence, Ito and Yamada, *Did the reform fix the London fix
problem?*, Journal of International Money and Finance 80 (2018), DOI
`10.1016/j.jimonfin.2017.10.004`, reports that the post-fix reversal persisted after the February
2015 widening of the benchmark window. It does not establish profitability for a CFD taker.

Direct source: https://doi.org/10.1016/j.jimonfin.2017.10.004

## Adaptation and predictions

The pilot trades six V2 FX symbols after the full five-minute London fix window has elapsed. It
buys foreign currency in `EURUSD`, `GBPUSD`, `AUDUSD`, and `NZDUSD`, and sells USD in `USDCHF` and
`USDCAD`. `USDJPY` is deliberately excluded because the primary paper identifies yen as the
post-London-fix exception. A wide ATR stop makes the idea compatible with stop-defined R
accounting while trying not to replace the paper's time-exit mechanism.

Predeclared predictions:

1. Direction-normalized mean postfix return is positive gross in the pooled development sample.
2. At least four of six symbols have the predicted gross sign.
3. Any useful variant remains positive under V2's resolved costs and doubled-cost stress.
4. Results keep the same sign in both development halves and outside month-end observations.

## Quantitative-skeptic review

- **Costs:** the primary paper already finds that aggressive liquidity demand loses after
  transaction costs. The prior for net CFD profitability is low.
- **Instrument transfer:** institutional spot/futures behavior may not survive in retail CFDs.
- **Stop alteration:** the paper has a time exit, not an ATR stop. The wide safety stop is an
  intake/risk adaptation; stop-trigger frequency must be reported.
- **Clock and DST:** entry is in `Europe/London`, after the 15:57:30-16:02:30 fix window.
- **Holiday contamination:** no authoritative fix holiday calendar is available in the contract.
- **Dependence:** the six USD pairs are correlated. Use daily-clustered and per-symbol evidence.
- **Multiplicity:** the grid is exactly nine predeclared variants; robustness splits are not new
  strategies that may be selected after results.
- **No holdout:** only fixed development data may run. Final holdout remains locked until later,
  strategy-specific user authorization.

## Canonical implementation clarifications

V2 feedback `FB_FX_LONDON_FIX_REV_20261028T134544Z_1abf` identified that the 360-minute variant
crosses the broker's 17:00 `America/New_York` rollover even though it exits on the same
`Europe/London` calendar date. Research reply
`FB_FX_LONDON_FIX_REV_REPLY_20261028T151021Z_RESEARCH` confirmed that V2 must charge the real swap,
including Wednesday triple swap. The feedback marked this conservative resolved-cost correction
as `requires_revision: false`: it does not change the holding grid, entries, exits, or any trading
rule, and the claimed v1.0.0 bytes remain immutable. The same exchange confirms that an unexpected
missing 23:55 London force-close bar uses the next available bar. Canonical result interpretation
must use those linked feedback envelopes, not the superseded "No swap" rationale sentence in the
submitted payload.

Decision: worthwhile as an integration and falsification pilot, but with a low prior for net
profitability. Priority 90 reflects complete mechanical compatibility and information value, not
an assertion of profitability.

## Follow-up source and specification audit

The separate research-side audit in
`../reports/FX_LONDON_FIX_REV_SOURCE_SPEC_AUDIT.md` re-opened both primary sources and checked the
immutable submitted rules on 2026-10-28. It confirmed the side map, JPY exclusion, post-window
entry, and adverse transaction-cost prior. It also records that only AUD and GBP have the paper's
explicit liquidity-demander cost table, and that the ATR stop and shorter horizons are adaptations
rather than replications. The verdict remains development-only integration/falsification; no
holdout or post-result redesign is authorized.

## Pre-result interpretation freeze

Before any canonical result existed, research froze
`../reports/FX_LONDON_FIX_REV_RESULT_REVIEW_CHECKLIST.md`. Because v1.0.0 declares the
`stop_atr_multiplier=4.0, holding_minutes=360` baseline but no mechanical selector among nine
cells, that baseline is the only primary cell. Other variants remain fully reported and counted
but cannot be promoted from this result. Integration success is separate from profitability, and
no holdout follows automatically even if the baseline passes every gate.

## Development result and disposition

Canonical experiment `FX_LONDON_FIX_REV__v1.0.0__DEVELOPMENT__1` completed on the fixed
development period with the exact immutable submission hash and no holdout disclosure. Zero of
the nine declared grid cells had positive net R. Therefore the frozen 4xATR/360-minute primary
cell necessarily fails the primary net-profit gate and v1.0.0 is rejected without a holdout.

The envelope's exploratory best cell, `v0007` (5xATR/180 minutes), still lost 1043.4 R over
10,397 trades and deteriorated to -2267.7 R under doubled costs. It showed the predicted gross
sign in four of six symbols and +181.0 gross R pooled, but costs overwhelmed that effect. Both
development halves, non-month-end observations, and the result without the five best days were
negative. This is consistent with the primary paper's adverse liquidity-demander cost evidence.

For scale, v0007's rounded gross expectancy is only about +0.0174 R/trade against an implied
resolved-cost burden of about 0.1178 R/trade. Its gross effect covers roughly 14.8% of that burden,
so linear costs would need to fall by about 85.2% merely to break even. USDCAD and EURUSD provide
about 78.8% of pooled gross R; the breadth result is not uniform across pairs. These are
exploratory-cell diagnostics, not baseline estimates.

The complete research review is in
`../reports/FX_LONDON_FIX_REV_DEVELOPMENT_RESULT_REVIEW.md`. It separates scientific rejection
from integration status and records three non-rescuing interface issues: a false "unanswered"
warning despite the canonical research reply, a terminal result whose payload remains in the
claimed queue stage, and omission of the frozen primary cell's detailed metrics from the
canonical envelope. None warrants a rerun or same-data redesign.
