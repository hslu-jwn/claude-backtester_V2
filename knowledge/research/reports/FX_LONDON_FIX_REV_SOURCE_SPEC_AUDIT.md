# FX_LONDON_FIX_REV v1.0.0 source and specification audit

Date: 2026-10-28  
Scope: research-side review of the two cited sources and the immutable submitted specification.  
Decision: **retain as a development-only integration and falsification pilot; do not promote.**

## Source verification

### Krohn, Mueller, and Whelan (2024)

The full open-access *Journal of Finance* article was inspected at
<https://doi.org/10.1111/jofi.13306>. It uses tick-level G9 FX data from January 1999 through
December 2019. Its quote convention is USD per unit of foreign currency. The article defines the
post-London interval from the London fix to the 17:00 New York FX close and reports foreign-currency
appreciation (USD depreciation) across the G9 except JPY. This supports the submitted side map,
JPY exclusion, and the longest six-hour horizon.

The paper does **not** support a favorable net-return prior for a CFD market taker. Its explicit
transaction-cost exercise covers AUD and GBP in 2006-2019 and reports negative postfix returns for
the liquidity demander after bid/ask costs: -2.83 bps for AUD and -0.44 bps for GBP. The
corresponding liquidity-provider returns are positive. This evidence is adverse and directly
supports the pilot's cost-survival rejection framing.

The published strategy reverses at the fix and uses a time exit. The submitted 16:03 London entry,
ATR safety stop, CFD instruments, and 60/180/360-minute grid are adaptations, not replications.

### Ito and Yamada (2018)

The published article page and the authors' NBER working-paper version were inspected at
<https://doi.org/10.1016/j.jimonfin.2017.10.004> and <https://doi.org/10.3386/w23327>. The paper
studies the February 2015 widening of the WM/Reuters window from one to five minutes. It documents
that abnormal fix-centered price dynamics persisted after the reform while the volume pattern and
bank execution behavior changed. It supports waiting until the full five-minute window has ended.

It is corroborating market-structure evidence only. It does not establish the profitability of the
submitted directional postfix CFD trade, its horizons, or its ATR stop.

## Specification audit

- **Direction:** consistent with USD depreciation after the London fix; USDJPY is correctly
  excluded as the published exception.
- **Timing:** 16:03 Europe/London avoids trading inside the post-reform 15:57:30-16:02:30 window.
  The 360-minute horizon approximately spans the source's full post-London interval; 60 and 180
  minutes are declared adaptations and all three remain counted.
- **Costs:** the source prior is explicitly adverse. Resolved V2 costs and doubled costs are proper
  rejection gates. Linked canonical feedback supersedes the submitted payload's stale no-swap
  sentence and requires real rollover swap, including Wednesday triple swap.
- **Dependence and multiplicity:** six USD pairs are not independent. The specification correctly
  requires a pooled daily series, per-symbol reporting, all nine grid cells, and prior trials.
- **Robustness:** development halves, non-month-end observations, removal of the five best days,
  and matched random-time entries are report-only gates and may not create extra selectable cells.
- **Data limitation:** no authoritative London-fix holiday calendar is available. Any apparent
  performance must be reported both with the mechanically eligible sample and with contaminated
  dates flagged where identifiable; this limitation cannot be optimized after results.
- **Holdout:** no final-test access is authorized.

## Verdict and interpretation rule

The hypothesis is sufficiently precise for the already-claimed development pilot, but the prior
probability of net CFD profitability is low. A positive gross result alone is not a success. The
pilot passes its research purpose only by producing a traceable canonical result and answering the
predeclared net-cost and stability gates without reinterpretation. Failure is informative and must
be retained; it must not trigger a same-data redesign of the fix rule.

