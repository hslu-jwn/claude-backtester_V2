# Ranked opportunities and exact next decisions

## 0. Protect the existing forward program and repair I-105

**Priority: highest operational priority.** Do not displace the scheduled 2026-12-03 collection of already-frozen
periods for Strategy 20, I-109, Strategy 19, and the registered forward candidates. Strategy 20 is tail-driven and
I-109 was not blind; fresh
forward rows are more informative than another retrospective variant.

**Exception: I-105 cannot be logged as an executable rule in its frozen form.** It ranks stocks using the official
opening print and claims entry in that same opening auction. Alpaca's documented OPG cutoff is 09:28 ET, before the
official open exists. Keep the historical diagnostic labelled non-tradable. Before any forward return is read,
either freeze a pre-open signal and submit OPG orders, or observe the open and enter later in continuous trading;
that is a new rule with its own costs and cannot inherit the diagnostic result.

## 1. Post-earnings employee selling after high stock compensation

**Decision: highest-priority new US-share audit, but evidence grade B−; one preregistered post-2020 replication only
if coverage, timing, borrow, and power pass without seeing post-event returns.**

Hartzmark and Solomon study 300,473 US earnings observations from 2002–2020. Using annual stock-compensation
expense announced in the prior quarter and scaled by pre-event market capitalization, the top 5% group earns
−87.5 bp characteristic-adjusted from announcement day +1 through +3 (`t=−5.77`). The next bucket is only −23.6
bp (`t=−2.04`), while days +4 through +10 partially reverse +45.5 bp (`t=2.06`). The steep dose response,
lagged information, post-day-0 entry, and reversal support predictable employee selling rather than earnings news.
The evidence is gross, ends in 2020, and lacks an independent replication. This section was omitted from the
authors' 2025 AER article and its supplement, which cover aggregate dividend-payment pressure. It must therefore be
cited as a working-paper result, not a published AER finding.

### Stage A — return-blind data audit

- Map the frozen top-1,000 share universe to SEC CIKs and count coverage of standard and issuer-specific XBRL tags
  for share-based compensation, always using facts filed before the event.
- Build candidate earnings events from Item 2.02 8-K acceptance/exhibit timestamps; audit actual release timing on
  a fixed sample because the press release can precede EDGAR dissemination.
- Count independent event dates and top-5%/5–10% names; estimate a date-clustered minimum detectable effect without
  reading day +1 to +3 returns.
- Audit short availability/borrow proxies and opening/closing execution windows for high-compensation growth names.
- Park if tag comparability, timing, or attainable power implies less than a 15% pass chance.

### Stage B — one frozen rule if Stage A passes

- Signal: lagged annual share-based compensation / market capitalization, ranked across eligible reporting firms.
- Event time `t=0`: first regular session after the public earnings release. Short the top 5% in that session's
  official closing auction; hedge with a prespecified size/value/momentum benchmark or matched low-expense basket;
  cover at day +3 close. This matches the source's close-to-close day +1 through +3 return clock. A next-open entry
  is a conservative adaptation that cannot inherit the reported −87.5 bp effect and would need its own frozen rule.
  Do not adapt the threshold to the local top-1,000 universe after viewing returns.
- Apply actual share costs, borrow, date-and-firm clustered inference, temporal halves, doubled-cost and tail tests.
  Require the 5–10% bucket to be weaker and days +4 to +10 to reverse in sign as type-B checks.
- Use 2016–2020 only as a source-matching/code diagnostic because those years overlap the paper. Freeze costs,
  controls, and the post-2020 holdout before reading any 2021+ event return; that holdout is the first independent
  local replication and must not be tuned after a weak result.

**Main risks:** nonstandard XBRL tags, 8-K timing lag, PEAD confounding, growth-stock squeeze/borrow tails, buybacks
in the same post-earnings window, 10b5-1 regime changes, and a post-2020 decay not visible in the source.

## 2. SEC Rule 201 official-trigger and power census

**Decision: admit to a signal-free official-file census/power audit; run no return test until archive completeness,
symbol mapping, and trigger-time reconciliation pass.**

Rule 201 triggers when an NMS stock falls at least 10% from its prior regular-session close. Aggressive short
sales at or below the national best bid are then restricted for the rest of that day and the next trading day.
This creates a known policy discontinuity at −10%, distinct from the project’s generic share-shock reversals.

The official-source blocker is partly resolved. In its 2024 Rule 605 release, the SEC reports using daily Rule 201
files from NYSE and Nasdaq for April 2015–November 2023; Nasdaq documents a `shorthaltsYYYYMMDD` file with symbol,
market category, and trigger time. Anonymous dated Nasdaq retrieval was verified for 2020-03-16, not merely the
latest day, and Cboe's current-year CSV includes trigger/end/rescission fields. But full trading-day enumeration,
Cboe 2015–2023 access, and any stable anonymous NYSE/NYSE Arca history remain unproved. The first task is therefore
to prove archive retention, listing-market coverage, and clean point-in-time symbol mapping—not to infer
activations from M1 lows.

The primary study uses 2,387 stocks from March 2011–March 2013 and 25,838 threshold observations. Its preferred
regression-discontinuity estimate is +5.79 bp per 65-minute bin (`SE=1.81`), approximately +35 bp/day, alongside
an 8% reduction in short-sale activity. It uses stock/date clustered inference, robustness specifications, and
placebo thresholds. This is strong causal evidence, but it is not a net-cost trading result. A consolidated M1
low below −10% is not itself proof of an official activation: stale closes, bad/off-exchange prints, odd lots,
and Limit-Up/Limit-Down states can break the intended discontinuity.

### Stage A — no-return census

- Point-in-time top-1,000 US shares, price above $5, development dates 2016-04 through 2021-09-13.
- Six fixed 65-minute bins from 09:30 to 16:00 New York.
- Retrieve the NYSE/Nasdaq official daily files, document every expected date, URL, status, byte count, checksum,
  completion timestamp, and missing day; derive events from embedded trigger dates so carryover rows are not
  double-counted; preserve Cboe end dates and rescissions; map symbols point in time; and reconcile a fixed sample
  with official current notices and SIP-consistent M1 crossings.
- Count first session crossings of −10%, near misses, independent dates, symbols, trigger bins, 2020
  concentration, LULD overlap, missing next-day bars, and names with unreliable M1 lows.
- Estimate minimum detectable effect under date clustering without inspecting post-trigger returns.
- Stop under M4 if event breadth or attainable power makes the pass chance below 15%.

### Stage B — one preregistered replication, only if Stage A and trigger validation pass

- Running variable: first completed-bin session-low return relative to prior close.
- Treated bandwidth: `[−10.50%, −10.00%]`; control: `(−10.00%, −9.50%]`, never previously triggered that day.
- Within date/bin, long equal-weight treated and short equal-weight controls at the next M1 open. Keep a control
  that crosses later (intention to treat; no future relabeling).
- Exit both legs at 15:55 the following session.
- Record actual entry/exit spreads before fixing a baseline. In addition to doubled costs, include 25 bp and
  50 bp crash-name stress cases; 0.6 bp overnight borrow cannot be assumed representative near −10% moves.
- Primary statistic: date-clustered mean pair return. The published mechanism fixes the positive direction, so use
  the one-sided project threshold: net positive, `t>=3.0`, both
  temporal halves positive, positive at doubled costs, and positive without the two best dates.
- Required diagnostics: local-linear discontinuity on −12% to −8%; placebo cutoffs; exclude 2020; trigger-bin
  strata; LULD and bad-print audit. Diagnostics cannot rescue a failed primary rule.

**Main risks:** incomplete or difficult-to-access historical archives, crash-day clustering, source/holding-period mismatch, M1-low
measurement, Limit-Up/Limit-Down interactions, hard-to-borrow names, adverse execution, and a modern universe
different from the paper. A null is valuable: it would close this regulatory neighbour of the share-reversal
family.

## 3. CRSP fast-track IPO inclusion flow

**Decision: run a signal-free eligibility/data audit; promote only if public day-one inputs reproduce the index
decision point in time.**

After a March 2017 rule change, qualifying US IPOs can enter CRSP indexes after their fifth trading day. The
source study covers 1,394 IPOs from October 2014–December 2022 and identifies 264 fast-track events. Mechanical
index demand is about 7% of issued shares; eligible IPOs outperform controls by more than five percentage points
from first-day close to inclusion close, with more than half reversing within two weeks.

Public eligibility reconstruction needs day-one close, prospectus shares/float, domicile/security filters, and
the last published small-cap breakpoint. Exact CRSP TSO/FSO values and membership are proprietary, so the first
task is agreement—not returns—on a historical sample.

If the audit passes: identify at day-one close, enter at day-two open, exit in the fifth-day closing auction,
compare with same-week similar-size noneligible IPOs, use official auction prints, and apply fresh-IPO spread and
slippage stress. The closer reversal trade is likely unusable because new-IPO borrow can be unavailable or
extremely expensive.

## 4. Non-overnight follow-on-offering reversal

**Decision: return-blind US event/timestamp/power audit; one post-2015 replication only if the public event clock
and modern event count pass.**

Gustafson's 2018 peer-reviewed study reports that US seasoned equity offerings marketed over more than one session
experience a 2.5% pre-issue decline that reverses within seven days. The reversal is larger for bigger offerings
and larger pre-issue declines, consistent with temporary selling pressure as existing investors make room for new
shares. Overnight offerings show much less post-issue return. The published sample runs through 2014; the accessible
publisher text does not report the exact observation count, while the dissertation predecessor has 652
non-accelerated and 412 accelerated firm-commitment offerings through 2011. Results are gross and not an executable
strategy test.

Before reading returns, reconstruct post-2015 US primary common-stock follow-ons from public 8-K, prospectus, and
`424B5` acceptance timestamps. Exclude rights, units, at-the-market programs, pure secondary sales, financials,
regulated utilities, prices below $5, and events without a clear public announcement and final pricing time. Count
liquid top-1,000 cases with at least one regular session between announcement and pricing, then estimate
date-clustered power. Park if exact timing cannot be reconstructed or the estimated pass chance is below 15%.

If the audit passes, preregister one simple rule: buy all eligible non-overnight issuers at the first executable open
after final pricing becomes public, hedge the market, and exit after seven trading days. Offer size and the known
pre-issue decline are mechanism diagnostics, not optimized entry filters. Use actual spread/slippage and official
auction prints where relevant; test temporal halves, doubled costs, date clustering, and exclusion of the best two
dates. The next-open adaptation cannot inherit the paper's full 2.5% gross estimate.

**Main risks:** sample ends in 2014, overnight issuance now dominates, source event data used proprietary SDC,
announcement information and issuer selection can mimic pressure, public filing acceptance may lag the pricing
release, and the seven-day reversal may have decayed after publication.

## 5. Execution-data corrections, not new alpha

**Decision: adopt as research hygiene.**

- For any share rule claiming open/close execution, use Alpaca SIP official auction prints. The audited median
  daily-open difference is 3.4 bp and p90 23 bp.
- Use Dukascopy historical bid/ask only to stress the shape and tails of placeholder FTMO spread years. It is not
  the FTMO venue and cannot replace the base cost model.
- If the user opens a Databento account, pre-price one narrow pull of classic ZN and Micro 10Y definitions,
  statistics, and M1 month-end windows. Use the current $125 historical credit only to validate I-109 contract
  mapping, rolls, the 15:00 spread, and fills; do not call the already-seen period a new return test.
- Scout, but do not adopt, Binance's current zero-maker USDC-perp promotion. First intersect official live listings
  with each actual Strategy 20 weekly book and verify authenticated Swiss access. A separately frozen forward A/B
  must include missed passive fills, spread, funding, stablecoin basis, and the prior adverse maker result.

## 6. Hyperliquid backstop-inventory unwind

**Decision: signal-free event census only.** The protocol can transfer under-margined positions to an officially
discoverable HLP liquidator vault, which must then manage the inventory. This is more specific than the spent
generic liquidation-cascade family.

Using raw node events/fills, count forced transfers above $500k and 0.1% of trailing 24-hour venue volume,
clustered by coin within 30 minutes. Require at least 50 independent clusters before defining a return test; do
not relax thresholds if JELLY-like interventions dominate. The eventual rule would trade against the received
inventory and exit after 50% unwind or 120 minutes, with taker fees and contemporaneous L2 slippage.

## 7. Renounceable rights-issue arbitrage feasibility

**Decision: signal-free international-venue feasibility audit only; do not import the paper's modeled returns into
the audit.**

A 2025 peer-reviewed study releases an open dataset for 2,583 subscription-rights issues across 27 countries. Its
theoretical trade compares the equivalent cost of new shares bought through tradeable rights with the existing
share price. Reported positive estimated net spreads occur in 1,044 cases, but the aggregate mean is unusable:
the median is −2.32%, 387 observations exceed 1,000%, and same-close Refinitiv quotes do not prove simultaneous
fills. Only 18 US cases appear in the source data, so this is not an Alpaca-US strategy.

Use event metadata—not the supplied return columns—to count post-2015 renounceable cases for which the project
could obtain synchronized right/stock quotes, point-in-time short or CFD availability, subscription ratios and
deadlines, settlement and allocation terms, FX, financing, and actual corporate-action fees. Require at least 50
independent executable cases on a venue the user can lawfully access before defining a return test. Alpaca currently
documents a $100 per-client voluntary-action fee, and rights/warrant elections can produce two fee entries; this
alone makes its route unsuitable for small trades. An Australian 2024 announcement study is also adverse: 1,038
events, including 319 intraday cases, show fast negative information effects but no profitable bid-to-ask short rule.

## 8. Same-calendar-month cross-sectional stock seasonality

**Decision: preserve as the leading data-acquisition candidate; do not test source-matched stocks on 2016+ alone.**

At each month-end, rank stocks on market-relative returns in the same calendar month 24, 36, 48, and 60 months
earlier. Heston and Sadka report about 67 bp/month top-minus-bottom in US shares from 1965–2002; an international
extension finds the pattern across Canada, Japan, and 12 European markets. Keloharju, Linnainmaa, and Nyberg
document related same-calendar seasonalities and a composite stock strategy around 13% per year.

The source-matched rule needs survivorship-safe total returns, delistings, and enough annual lags. The current
share history provides at most about five independent same-month lags and too few post-warm-up months for a
convincing split. Nearly 100% monthly turnover also makes costs and borrow decisive.

### Recommended route

1. A Kenneth French industry-portfolio run is background replication only; aggregation may erase or manufacture
   the stock-level mechanism and cannot promote a tradable card.
2. Do not create a discretionary industry-to-ETF map after viewing results.
3. Full stock test only after acquiring 15–20 years of point-in-time shares with corporate actions, delistings,
   and credible borrow/cost handling.

**Admission gate:** one rule, no month deletion, next-open execution, actual turnover, dividends/borrow, doubled
cost, and the existing untouched-test discipline.

## 9. End-of-day cross-sectional reversal — execution overlay only

**Decision: do not create a standalone strategy card.**

New 2026 evidence reports a last-30-minute reversal among intraday stock losers and winners and finds a similar
gross effect after 2019, except during 2020–2022. The original value-weighted estimate is about 3.78 bp/day and
the modern replication is about 3.05 bp/day in 2023–2026, both gross. The project’s realistic share round trip is
roughly 7 bp before a two-leg implementation, so the standalone strategy fails the cost screen.

Retain only as a preregistered execution-timing overlay: when the portfolio already requires a buy or sell near
the close for an independent reason, compare scheduled execution with the first versus last part of the final
30 minutes. Attribute only implementation shortfall, not alpha, and do not let the overlay create trades.

## 10. Initial Schedule 13D activist filing drift

**Decision: park; revisit only after a signal-free event count and a clean post-2024 cohort exists.**

Historical studies report positive announcement and post-filing returns, but a reproducible 2025–2026 GitHub
study reports a filing-day jump followed by negative 20-day drift. The SEC shortened the filing deadline from
ten to five business days in 2024, changing leakage and price discovery. This makes pooled historical inference
unsafe. EDGAR data are free, but current evidence does not justify spending a test.

If reopened: initial 13D only, acceptance timestamp, enter five minutes after publication or next open, hedge
SPY, fixed +23-session exit, date-clustered inference, and separate pre/post-rule regimes.

## 11. Lower-priority ideas

- **52-week-high momentum:** elegant OHLC rule with strong 1963–2001 evidence, but substantial overlap with
  momentum, post-publication decay, an internal broad momentum failure, and adverse modern community evidence.
- **Residual short-term stock reversal:** historically positive after factor residualization, but two modern open
  replications are negative and the 2016+ sample is underpowered after a 36-month warm-up.
- **Equity pairs:** historically credible, negative or decayed after 2009, and adjacent to already-spent relative
  value/mean-reversion families.
- **Crypto quarter-hour boundary prediction:** current paper forecasts the first 10 seconds, not the first M1 bar,
  and provides no costed strategy. Taker fees likely dominate the M1 transfer.
- **Euro-area sovereign auction cycle:** official evidence confirms a V-shaped BTP auction pattern, but recent
  ordinary-regime moves are only about 0.5 yield bp on each side; hedged historical strategies were negative and
  source-matched futures history is unavailable.
- **Deribit call-IV signal:** the motivating study reports weak pre-cost performance and newer evidence finds no
  robust directional option signal. Preserve only as a post-2023 replication if free trade history is complete.
- **Predicted dividend month:** peer-reviewed US and German evidence supports price pressure before expected
  ex-dates, but the 2016+ local history has only about 120 monthly clusters and the corporate-action feed must be
  validated point in time. Preserve as a secondary data audit, not a return test yet.
- **Cash merger arbitrage:** economically real compensation for deal-break risk, with percentage-point spreads,
  but it needs a hand-built point-in-time deal/outcome database, weeks-to-months capital, and tail-risk accounting.
  It is a data/infrastructure project rather than a first experiment for the current backtester.
- **Binance monitoring-tag short:** deduplicate as existing FB-041. The recent preprint is unreviewed, gross, and
  has only about 27 independent announcement batches after the latest update; tags are not delisting notices and
  perp residual drift is weaker. Build an official timestamp census only, keeping tags, token delistings, and pair
  removals separate, and do not run returns below the cluster gate.
- **IPO lockup expiration:** a distinct forced-supply event and absent from the ledger, but the main US evidence is
  from 1988–1997 (roughly −1.5% over three days), later research shows VC/PE heterogeneity, and modern exact dates,
  amendments, early releases, and historical borrow need hand-built prospectus data. Reuse any IPO-document parser
  built for fast-track inclusion, then run a signal-free date/borrow census; do not spend a return test now.
- **Cash-settled convertible maturity unwind:** a 2025 peer-reviewed study finds about +4% market-hedged return and
  ~70% positive events when arbitrageur short-covering is not offset by option-dealer selling. The clean subsample is
  only 21 events, averaging windows span 10–80 trading days, and the study used Bloomberg plus hand-read indentures.
  Preserve a free-EDGAR feasibility/event census only: exact settlement choice, overlays, principal still
  outstanding, moneyness, and averaging dates must all be known before the window. Park unless at least 30
  independent post-2015 events can be reconstructed without outcome-based selection.
- **Discounted-DRIP pricing-period pressure:** a 2020 working paper on ASX 200 firms reports a gross market-hedged
  9.2 bp/day (`t=2.27`) while arbitrageurs short shares during announced DRIP pricing periods. It omits trading and
  borrow costs, uses one 2007–2018 market, and states that comparable US plan detail is unavailable. This is distinct
  from the project's dividend-payment-flow rows, but it neither clears the evidence gate nor fits current data.
