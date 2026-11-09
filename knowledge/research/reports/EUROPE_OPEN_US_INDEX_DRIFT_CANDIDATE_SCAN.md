# Europe-open U.S. equity-index drift candidate scan

Date: 2026-10-29  
Decision: **reject as a current candidate; the original authors' post-publication sample is flat**.

## Candidate and primary result

Nina Boyarchenko, Lars C. Larsen, and Paul Whelan, “The Overnight Drift,” *Review of Financial
Studies* 36(9), 2023, 3502–3547, [DOI/record opened](https://doi.org/10.1093/rfs/hhad020),
[full accepted manuscript opened](https://research.cbs.dk/files/101311522/nina_boyarchenko_et_al_the_overnight_drift_acceptedversion.pdf).

The paper documents a positive E-mini S&P 500 futures return around the European equity-market
open. In the 1998–2020 sample, 02:00–03:00 U.S. Eastern averaged about 1.48 basis points per trading
day, or 3.7% annualized. The study uses hourly and five-minute futures data, explicitly corrects for
multiple hour searches, reports broad calendar persistence, and links the effect to resolution of
the prior U.S. close's order imbalance under limited dealer risk-bearing capacity. This is a real,
mechanically distinct historical anomaly—not an opening-range breakout rule.

## Decisive post-publication evidence

The same authors re-examined the effect in “The Disappearing Overnight Drift,” Federal Reserve
Bank of New York, *Liberty Street Economics*, 1 July 2026,
[full post opened](https://doi.org/10.59576/lse.20260701).

Using January 2021–December 2025 (1,245 trading days), they report that the 02:00–03:00 ET return
was close to zero. The pattern was likewise flat in E-mini Nasdaq-100 and E-mini Dow futures. They
also document a large decline in closing order-imbalance dispersion and a breakdown in the
imbalance-to-overnight-return relationship, consistent with weakening of the proposed mechanism.
Two ETFs launched in 2022 to exploit overnight equity returns closed fourteen months later,
although ETF-specific costs also matter.

## Candidate assessment

1. **The modern untouched sample fails.** The post-publication interval is the most relevant
   adjudication and does not support positive expectancy.
2. **The historical margin was small.** The original unconditional mean was 1.48 bp per day before
   any retail-CFD spread, commission, or slippage. There is no positive modern gross margin to test
   for cost survival.
3. **Conditioning would be a rescue search.** Selecting selloff closes, high-volatility states,
   alternative hours, weekdays, months, or DST regimes after observing the decay would convert the
   original anomaly into a new interaction grid. The required signed order-flow field is not
   available in supported OHLC data in any event.
4. **Shifting the hour is not replication.** Europe/US DST mismatches can be frozen for a future
   independent study, but searching nearby UTC buckets on local outcomes would merely optimize the
   clock after failure.
5. **It cannot be imported from futures to CFDs by label.** Continuous-futures session mechanics,
   dealer inventory, and executable costs differ from a broker's US500/NAS100 proxy.

## Decision

Retain the anomaly and its failure as useful research evidence, but create no strategy draft,
diagnostic, or nearby-hour scan. Do not use the post-2020 decay to discover a favorable regime.

Reconsider only if a later, independent post-2025 primary study finds renewed unconditional
Europe-open drift across a predefined futures sample, survives realistic costs, and supplies a
causal mapping to supported proxy execution. The original 1998–2020 result alone is obsolete for
candidate promotion.
