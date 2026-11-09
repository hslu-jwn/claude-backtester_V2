# R-2026-005 - FX residual session drift after opening and fix exclusions

Status: source-reviewed diagnostic design; no strategy specification and no profitability claim.
Date: 2026-10-28

## Research question

Do major currencies retain a common directional return during the interior of their local trading
session, after removing market-opening, market-closing, benchmark-fix, rollover, weekend, and
corrupt-data intervals? Published research often finds that a currency depreciates during its own
local trading hours and appreciates during the counter-currency's hours. The question here is
whether that pattern is distinct from the opening and fixing effects that the current research
program deliberately excludes.

This is a diagnostic, not a trading rule. The evidence-matched proposed universe is fixed as
`EURUSD`, `GBPUSD`, `AUDUSD`, `USDCHF`, and `USDJPY`: the five USD crosses in Breedon and
Ranaldo. `USDCAD` is excluded before data access
because its 08:00-16:00 Toronto local session is the same physical window as the 08:00-16:00 New
York comparison session; the nonoverlap rule would leave no local-versus-US contrast. `NZDUSD` is
omitted because it is not in that source universe; its sixth cross is `EURJPY`, which is omitted
because its local-versus-US contrast would differ. The result must not be used to retain only the
best pair, weekday, or hour.

Shared Interface 0.1.0 does not publish a canonical supported-symbol capability list for diagnostic
studies. Therefore the five symbols are source-matched research requirements, not a claim that V2
currently has every field and history needed. A future joint study route must confirm all five
before accepting the design; unsupported coverage parks the study rather than silently changing the
universe or promoting an available-pair sensitivity.

## Primary sources actually inspected

### Breedon and Ranaldo (2013)

Francis Breedon and Angelo Ranaldo, *Intraday Patterns in FX Returns and Order Flow*, Journal of
Money, Credit and Banking 45(5), 953-965. DOI `10.1111/jmcb.12032`.

Direct sources: https://doi.org/10.1111/jmcb.12032 and
https://www.econstor.eu/bitstream/10419/97343/1/690223323.pdf

The full working-paper version was opened. It uses EBS transactions and firm best bid/offer data
from January 1997 to early June 2007 for EURUSD, USDJPY, GBPUSD, EURJPY, USDCHF, and AUDUSD,
aggregated hourly. EBS represented roughly half of activity in its major pairs but less than 5%
for GBPUSD and AUDUSD. Local currencies generally depreciated during local trading hours and the
pattern was mirrored in order flow. Simple bid/ask-executable session trades were mostly
unprofitable; EURUSD was the exception, with reported Sharpe ratios of 1.3 for the morning short
and 0.9 for the afternoon long at interdealer normal size. Those costs and access are materially
better than retail-CFD execution. The study includes openings and fixes, so it does not establish
the residual effect proposed here.

Its Table 1 directly defines the pre-exclusion sessions used below: US 08:00-16:00, Europe
07:00-15:00, Japan 08:00-15:00, and Australia 10:00-16:00 local time, with DST differences
handled. In Table 2 every midquote session return has the predicted sign and is significant in the
simple test except the USDJPY US-session return, which is zero; the AUDUSD US-session coefficient
also becomes insignificant after its GARCH adjustment. Thus the local-session depreciation prior
is stronger and broader than the US-session appreciation prior. The four-of-five breadth gate is
deliberately demanding and each side must be reported separately.

### Krohn, Mueller, and Whelan (2024)

Ingomar Krohn, Philippe Mueller, and Paul Whelan, *Foreign Exchange Fixings and Returns around the
Clock*, Journal of Finance 79(1). DOI `10.1111/jofi.13306`.

Direct source: https://doi.org/10.1111/jofi.13306

The full paper was opened. It studies G9 high-frequency returns from January 1999 through December
2019 and finds that the US dollar appreciates before the Tokyo, ECB, and London fixes and reverses
afterward. The pattern appears in spot, forwards, CME futures, ICE dollar-index futures, and
interdealer VWAPs. DST shifts, holidays without a fix, and pre-benchmark history pin the turning
points to fixes rather than generic market opens. Its transaction-cost analysis is adverse to an
aggressive liquidity demander. This is direct contrary context for interpreting a broad
"session" coefficient as an independent anomaly.

### Khademalomoom and Narayan (2019)

Siroos Khademalomoom and Paresh Kumar Narayan, *Intraday Effects of the Currency Market*, Journal
of International Financial Markets, Institutions and Money 58, 65-77. DOI
`10.1016/j.intfin.2018.09.008`.

Direct source: https://doi.org/10.1016/j.intfin.2018.09.008

The publisher's extended abstract, introduction, methods excerpt, and conclusion were opened; the
full article was not accessible. Hourly rates for AUD, GBP, CAD, EUR, JPY, and CHF against USD from
2004-2014 show local post-opening, major-market, and overlap effects. The authors report a simple
strategy earning up to 18% annually, but the accessible material does not establish realistic
bid/ask, commission, slippage, financing, or multiple-testing treatment. The finding is therefore
statistical motivation, not net-performance evidence.

### Cornett, Schwarz, and Szakmary (1995)

Marcia Millon Cornett, Thomas V. Schwarz, and Andrew C. Szakmary, *Seasonalities and Intraday
Return Patterns in the Foreign Currency Futures Market*, Journal of Banking & Finance 19(5),
843-869. DOI `10.1016/0378-4266(95)00084-T`.

Direct source: https://doi.org/10.1016/0378-4266(95)00084-T

The publisher abstract and indexed article sections were opened; the full paper was not
accessible. IMM futures from 1977-1991 show foreign currencies weakening overnight and
strengthening during US trading, with much of the latter concentrated in the opening hour and
last two hours. That concentration is precisely why the residual study removes opens and closes.

## Operational benchmark timing sources

Official ECB material resolves the historical reference-rate mask. The rate-setting snapshot is
14:15 `Europe/Frankfurt` on TARGET business days through 2023-04-02 and 14:10 from 2023-04-03. The
1 July 2016 change delayed publication from about 14:30 to about 16:00 but explicitly left the
14:15 setting methodology unchanged. For the current fixed V2 development period, only the 14:15
rule applies. Sources:

- ECB, *Setting-up of common market standards* (1998):
  https://www.ecb.europa.eu/press/pr/date/1998/html/pr980708_2.en.html
- ECB, *ECB introduces changes to euro foreign exchange reference rates* (2015):
  https://www.ecb.europa.eu/press/pr/date/2015/html/pr151207.en.html
- ECB Governing Council decision, *Change in the computation time* (2023):
  https://www.ecb.europa.eu/press/govcdec/otherdec/2023/html/ecb.gc230331~1ad86981e1.en.html
- ECB TARGET operating schedule: TARGET is closed on Saturday, Sunday, 1 January, Good Friday,
  Easter Monday, 1 May, 25 December, and 26 December:
  https://www.ecb.europa.eu/paym/target/t2/html/index.en.html

LSEG states that WMR closing spot rates are normally fixed Monday-Friday at 16:00 London and its
methodology applies conditional multi-centre holiday rules. Tokyo has no single administrator:
individual banks sample customer-transaction prices around 09:55 and publish their own rates. A
complete historical administrator calendar is therefore not a clean common input. Before any data
access, this study freezes a conservative rule: mask Tokyo 09:55 and London 16:00 on **every local
weekday**, including a weekday on which a particular rate may not have been produced. This
deterministically over-excludes rather than guessing an event from returns. Sources:

- LSEG WMR benchmark availability:
  https://www.lseg.com/en/ftse-russell/benchmarks/wmr-fx-benchmarks
- LSEG, *WMR FX Benchmarks Methodology*, national-holiday policy:
  https://www.ppe.refinitiv.com/content/dam/marketing/en_us/documents/methodology/wm-reuters-methodology.pdf
- Krohn, Mueller, and Whelan (2024), institutional descriptions of the bank-specific Tokyo fix and
  WMR London fix: https://doi.org/10.1111/jofi.13306

Publication time is not a fix event and must not be masked.

## Falsifiable development diagnostic

Use only fixed V2 development data and causal UTC M1 bars:

1. Aggregate complete M1 data into half-open H1 intervals in each currency's IANA local timezone.
   Express every return as **USD per unit of local currency**: use `ln(close/open)` for EURUSD,
   GBPUSD, and AUDUSD; negate it for USDCHF and USDJPY.
2. Predeclare local sessions directly from Breedon and Ranaldo's Table 1: EUR 07:00-15:00
   `Europe/Berlin`; GBP 07:00-15:00 `Europe/London`; AUD 10:00-16:00 `Australia/Sydney`; CHF
   07:00-15:00 `Europe/Zurich`; JPY 08:00-15:00 `Asia/Tokyo`. The USD comparison session is
   08:00-16:00 `America/New_York` for every pair. USDCAD is not tested because Toronto and New
   York sessions are physically coincident and cannot identify the proposed contrast.
3. Remove each session's first and last complete H1 interval. Also remove every H1 interval that
   contains a fix. For each fix, also remove the immediately preceding and immediately following
   physical H1 buckets in that fix's IANA timezone, including an exact-hour boundary; apply this
   rule to Tokyo 09:55 on every `Asia/Tokyo` weekday, the ECB 14:15 `Europe/Frankfurt` setting on
   TARGET business days (14:10 only from 2023-04-03), and London 16:00 on every `Europe/London`
   weekday. The Tokyo/London weekday masks are deliberately conservative and may remove a day on
   which a particular fix was not produced. Do not mask the ECB publication time.
   Remove broker rollover, weekend boundaries, DST local
   transition dates, and intervals without exactly 60 unique valid M1 bars. These benchmark masks
   and the historical ECB time rule are frozen before computation and may not be refined from
   observed returns.
4. Label every eligible block by the FX trading day whose close is the next 17:00
   `America/New_York` boundary after the block starts; store that label as the New York calendar
   date of the boundary. This aligns Asia-Pacific local hours with the following New York session
   under DST. For each pair/trading-day label, compute the accumulated residual local-session
   return and residual USD-session return. Overlap cannot be counted twice: assign an H1 bar to
   neither contrast when both session masks contain it. This conservative rule isolates
   nonoverlapping local and US hours.
5. The published-sign predictions are local-session return below zero and USD-session return above
   zero. Report all 10 pair-by-session cells and equally weighted five-pair aggregates. The primary
   pooled daily series for each session uses only dates on which all five pair returns are present;
   also report cell-level coverage and an available-pair aggregate as a labeled sensitivity so
   changing symbol availability cannot silently change the primary composition. Report both fixed
   development halves, yearly values, positive-day fractions, date-clustered uncertainty, and a
   mechanical concentration sensitivity: omit each date one at a time, then separately omit the
   single fixed set of five dates with the largest absolute pooled gross contributions, and report
   the worst retained pooled sign. This is report-only, not a selection estimate. No hour, pair, or
   weekday may be selected afterward.
6. For every eligible contiguous block, enter at its first H1 open in the published predicted
   direction (short local currency in a local session; long local currency in the USD session),
   exit at its last H1 close, and compute direction-normalized gross P&L. Charge the resolved V2
   entry and exit cost at those endpoints; an excluded fix/overlap hour splits a block and requires
   another complete round trip. Report block count, gross, net, and doubled-cost net. This is a
   diagnostic accounting convention, not authorization to trade. A later specification is allowed
   only for a co-primary session effect that independently satisfies all of these gates: its
   predicted raw sign holds in both development halves and for at least four of five pairs; its
   two-sided date-clustered 95% confidence interval for pooled raw return excludes zero in the
   predicted direction; its date-clustered 95% confidence interval for pooled direction-normalized
   net block return under doubled endpoint costs is wholly above zero; and the mechanical
   concentration sensitivity retains the pooled predicted sign. Local and USD effects are two
   counted co-primary tests and are adjudicated separately. One cannot rescue, pool with, or lend
   its sign to the other, and an available-pair sensitivity can never satisfy a primary gate.

## Synthetic calendar-mask audit

A price-free UTC schedule dry run was performed for representative winter, aligned-DST, and both
US/Europe DST-mismatch regimes. After removing the first/last session buckets, all fix-adjacent
buckets, and physical local/US overlap—but before missing-data, holiday-contamination, or reopen
checks—the retained local-session counts per day are: EUR 5 H1 buckets, GBP 4, AUD 2-3 depending on
Sydney DST, CHF 5, and JPY 3. The retained New York comparison block has 2 H1 buckets when US and
European DST regimes are aligned and only 1 during their mismatch weeks. No retained pair is
structurally empty.

These counts are a conformance expectation, not a return result. An implementation must report
daily bucket-count distributions and exclusion reasons. A different count is a calendar-mapping
error unless caused by a separately logged data-quality or calendar exclusion.

## Quantitative-skeptic review

- **Fix and opening confounding:** the exclusions intentionally remove much of the published
  signal. A null residual is informative and must not be repaired by moving the windows.
- **Clock leakage:** historical DST and benchmark times must be resolved by date before returns are
  computed. Fixed UTC offsets are invalid. The ECB/TARGET rule and conservative Tokyo/London
  weekday masks are frozen above.
- **Quote convention:** USD-base pairs must be sign-inverted before pooling. A missed inversion can
  manufacture cross-pair agreement.
- **Date anchor and fix mask:** use the next 17:00 New York FX close's local calendar date for
  aggregation and remove exactly the containing physical H1 bucket plus its preceding and
  following buckets for each fix; neither rule may be changed after results are seen.
- **Overlap:** European and US sessions overlap. Dropping overlap from both sides avoids attributing
  one bar to both hypotheses, at the cost of a smaller and narrower estimand.
- **Narrow residual estimand:** the conservative masks leave only one or two New York H1 buckets
  per day and two to five local buckets. This is intentionally not a claim about a whole session;
  report bucket coverage and do not annualize it as though all working hours were traded.
- **Non-identifiable CAD contrast:** Toronto and New York have the same declared physical session.
  USDCAD is therefore excluded before computation rather than producing two empty or duplicated
  cells and calling them independent evidence.
- **Dependence:** all pairs share USD and macro-news dates. Treat five instruments as breadth, not
  five independent samples; cluster by date and report pair-level results. Use the five-pair date
  intersection for the primary pooled series so missing data cannot alter its composition.
- **Holidays:** the primary literature notes holiday effects. Tokyo/London benchmark masks cover
  every weekday, but the remaining session sample lacks authoritative point-in-time local holiday
  calendars and must be labeled holiday-contaminated; holidays may not be filtered after viewing
  their returns.
- **Costs and access:** most Breedon-Ranaldo session trades lost even at firm interdealer spreads.
  CFD taker costs set a low prior for economic value. Exclusion gaps require separate round trips;
  treating noncontiguous residual hours as one position would undercharge the diagnostic.
- **Structural decay:** source samples end in 1991, 2007, 2014, and 2019. Modern V2 development
  evidence must agree in both halves; older significance is not presumed persistent.
- **Prediction asymmetry:** the source's local-session sign is broader than its US-session sign;
  USDJPY is zero in the source US session and AUDUSD is not robust to its GARCH adjustment. Report
  local and US aggregates separately; one cannot rescue the other.
- **Statistical threshold:** each complete-five-pair co-primary must independently exclude zero in
  the predicted raw direction with a two-sided date-clustered 95% interval and have a wholly
  positive doubled-cost direction-normalized net interval. Favorable point estimates are
  insufficient.
- **Multiple testing:** local and US aggregates are two counted co-primary hypotheses. The 10
  pair/session cells are fully reported breadth splits, not a menu. Any later strategy must freeze
  one common mechanism and count both co-primary tests plus all resulting variants.
- **No holdout:** no final-holdout access is requested or authorized.

Decision: retain as a cheap, high-falsifiability diagnostic of whether session drift exists beyond
the opening/fix effects already studied. Do not create a strategy draft until the residual effect
passes the breadth, stability, concentration, and doubled-cost gates.

Update 2026-11-03: `reports/R005_STATISTICAL_ACCOUNTING_RESOLUTION.md` freezes the exact endpoint
observations, raw/inverse quote math, adverse-fill cost conversion, sum-then-equal-weight daily
aggregation, complete-case composition, synchronized five-day moving-block bootstrap, and Holm
control across the two co-primary sessions. This resolves research-owned ambiguity before data
access. The authoritative session calendar, all-five capability declaration, typed interface,
canonical transport, terminal statuses, and price-free conformance fixture still block execution.
