# R-2026-004 - Intraday response after unusually large hourly returns

Status: source-reviewed study design with an unqueued draft specification; no profitability claim.
Date: 2026-10-28

## Research question

After an unusually large, fully observed H1 return, do the next one to three hours continue in
the same direction or reverse? The question is deliberately sign-agnostic. It was prompted by
the frozen V2 backlog's exploratory I-61 diagnostic, where ordinary H1 returns looked different
from the largest observations. That diagnostic is hypothesis-generating evidence, not an
independent result, and no selected symbol or threshold may be presented as confirmatory.

The frozen backlog records I-61 as already tested on 2026-10-20 with **no robust edge**:
continuation was carried by the top 1% of events, and the closest cell was NAS100 H1 `k=4`,
two-hour hold, with a trimmed standardized effect near 0.20, t-statistic 1.7, and decay. That is
adverse local evidence and all of its trials remain part of the research program's multiplicity
history. This record is not a claim that the family is untested. It asks whether a stricter,
sign-agnostic design with same-clock robust scaling, an absolute cost floor, both response signs,
and concentration rejection can resolve the earlier failure; a second failure ends the line.

The intended local universe is the complete five-symbol core set named in the frozen backlog:
`XAUUSD`, `GBPUSD`, `GBPJPY`, `NAS100`, and `US500`. Testing all five prevents retaining only the
four whose exploratory Pearson correlations had the desired sign.

Competing mechanisms are predeclared. Continuation would be consistent with gradual information
incorporation, directional order-flow persistence, or stop cascades after a genuine shock.
Reversal would be consistent with temporary liquidity pressure, overreaction, or dealer inventory
rebalancing. A zero result after costs is the default null and a useful outcome.

## Primary sources actually inspected

### Caporale and Plastun (2020) - same-day FX continuation

Guglielmo Maria Caporale and Alex Plastun, *Daily abnormal price changes and trading strategies
in the FOREX*, Journal of Economic Studies 48(1), 211-222. DOI
`10.1108/JES-11-2019-0503`.

Direct sources: https://doi.org/10.1108/JES-11-2019-0503 and
https://bura.brunel.ac.uk/bitstream/2438/20567/5/FullText.pdf

The full paper was opened. It uses MetaQuotes daily and hourly observations for EURUSD, USDJPY,
USDCAD, AUDUSD, and EURJPY from 2008-01-01 through 2018-12-31. An abnormal day is the open-to-close
return beyond a period mean plus or minus two standard deviations. The paper reports continuation
through the abnormal day and reversal on the following day. Its tables contain roughly 55-79
positive or negative events per currency, depending on direction. The trading exercise omits
spread, commission, slippage, and swap; therefore its reported profits are gross proxies, not
evidence of net implementability. It detects the abnormal *daily* move progressively, usually
around 16:00-19:00, so it does not directly establish what follows an isolated extreme H1 bar.

### Borgards, Czudaj, and Hoang (2021) - commodity-futures reversal

Oliver Borgards, Robert L. Czudaj, and Thi Hong Van Hoang, *Price overreactions in the commodity
futures market: An intraday analysis of the Covid-19 pandemic impact*, Resources Policy 71,
101966. DOI `10.1016/j.resourpol.2020.101966`.

Direct sources: https://doi.org/10.1016/j.resourpol.2020.101966 and
https://pmc.ncbi.nlm.nih.gov/articles/PMC9759686/

The full open-access paper was opened. It studies front-contract midprices for 20 commodity
futures, including COMEX gold, at 1-minute through 1-hour frequencies from 2019-11-20 through
2020-06-03. Large turning-point legs are followed by proportionally large contrary legs, with
particularly strong pre-pandemic evidence for precious metals. The sample is only about 6.5
months and intentionally spans the Covid shock. More importantly, the exercise locates peaks and
troughs using a smoothing algorithm and assumes capture of 20% of the subsequent reversal. It
abstracts from fees and slippage. Successive turning-point legs also alternate sign by construction;
the empirical test concerns whether larger first legs have proportionally larger opposite legs,
not whether a causal trader can identify the turning point. That is not a real-time rule based only
on a just-closed H1 bar, so its positive returns cannot be transferred directly to V2.

## Additional primary context inspected

- Alexandru Rif and Sebastian Utz, *Short-term stock price reversals after extreme downward price
  movements*, Quarterly Review of Economics and Finance 81 (2021), 123-133, DOI
  `10.1016/j.qref.2021.05.004`; open full text:
  https://opus.bibliothek.uni-augsburg.de/opus4/files/94257/1-s2.0-S1062976921000922-main.pdf.
  The full paper was opened. It analyzes more than 46 million one-minute intervals for Nasdaq-100
  constituents from January 2014 to January 2019 and identifies 15,242 extreme negative intervals.
  About 31% of the crash-minute return reverses in the following minute, especially for the most
  liquid and largest firms. The mean quoted spread rises from 5.72 bp in normal intervals to
  14.67 bp in crash intervals. The paper motivates ultra-fast liquidity provision, not a costed
  H1 index-CFD rule; it examines negative moves only and does not establish post-spread retail
  profitability. It nevertheless shows that very short reversal survived in newer market data.
- Adam G. Zawadowski, Gyorgy Andor, and Janos Kertesz, *Short-term market reaction
  after extreme price changes of liquid stocks*, Quantitative Finance 6(4), 283-295 (2006),
  DOI `10.1080/14697680600699894`; full preprint:
  https://arxiv.org/abs/cond-mat/0406696. The full preprint was opened. It examines causal
  maximum-60-minute events in 2000-2002 NYSE/NASDAQ TAQ data, requiring both a 4% move and eight
  times the same-clock volatility of the prior 60 days, separating events by at least 60 minutes
  and omitting the last hour. For the main filter it reports 175 increases and 222 decreases on
  NYSE and 273 increases and 215 decreases on NASDAQ, followed by significant 30-60-minute
  reversal. Buying at best ask and selling at best bid leaves strong NASDAQ profits, while NYSE
  spread widening removes most significance; commissions, slippage, depth, and monitoring costs
  remain omitted. The filters were calibrated on NYSE data and are far more extreme than the
  proposed 2-4 robust-scale H1 thresholds. This is direct reversal evidence, but for individual
  stocks under 2000-2002 market structure, not modern index/FX/metal CFDs.
- A. G. Zawadowski, János Kertész, and György Andor, *Large price changes on small scales*,
  Physica A 344 (2004), 221-226, DOI `10.1016/j.physa.2004.06.121`; full preprint:
  https://arxiv.org/abs/cond-mat/0401055. The full preprint was opened. Using 2000-2002 NYSE and
  NASDAQ TAQ data, it defines causal extreme 15-minute events with combined absolute and
  same-clock relative-volatility filters, omits opening effects and overlaps, and retains 197
  increases plus 182 decreases on NYSE and 623 plus 500 on NASDAQ. It reports roughly 1% reversal
  over the next 10-30 minutes. The paper explicitly leaves economic significance to separate
  work; it studies individual stocks, not index futures or CFDs, and does not establish net
  profitability. Its strongest contribution here is methodological support for same-clock
  normalization, causal event detection, and non-overlapping events.
- James L. Grant, Avner Wolf, and Susana Yu, *Intraday price reversals in the US stock index
  futures market: A 15-year study*, Journal of Banking & Finance 29 (2005), 1311-1327, DOI
  `10.1016/j.jbankfin.2004.04.006`. The indexed article abstract and extract were inspected; the
  full PDF endpoint was inaccessible. S&P 500 futures from November 1987 through September 2002
  show about ten minutes of continuation after a large market-open move and then reversal, but
  bid/ask adjustment sharply weakens significance. Because the event is the market open, this is
  contrary context only and will not define the proposed study.
- Jun Cai, Yan-Leung Cheung, and Michael C. S. Wong, *What moves the gold market?*, Journal of
  Futures Markets 21 (2001), 257-278, DOI
  `10.1002/1096-9934(200103)21:3<257::AID-FUT4>3.0.CO;2-W`. The publisher abstract and article
  metadata were opened. COMEX gold intraday volatility is strongly seasonal and responds to US
  employment, GDP, CPI, and personal-income releases. It does not test shock continuation, but it
  shows why same-clock normalization and scheduled-news diagnostics are mandatory.
- Louis H. Ederington and Jae Ha Lee, *The Short-Run Dynamics of the Price Adjustment to New
  Information*, Journal of Financial and Quantitative Analysis 30(1) (1995), 117-134, DOI
  `10.2307/2331256`. The indexed abstract and metadata were opened; the full paper was not
  accessible. Using 10-second returns and tick data for interest-rate and foreign-exchange
  futures, the authors report that scheduled-news adjustment begins within ten seconds, is
  essentially complete within forty seconds, and that limited initial overreaction is corrected
  in the second or third minute after release after correcting for bid/ask and tick-data biases.
  This is evidence against assuming that news-driven reversal remains available at an H1 close.

## Falsifiable development study

This is a study before a strategy. On fixed V2 development data only:

1. Aggregate M1 bars into H1 bars using the draft's predeclared per-symbol IANA timezone and
   DST-safe boundaries. Every signal uses only the completed H1 close.
2. For each symbol and clock hour, normalize the open-to-close H1 log return by a robust scale
   estimated only from the prior 60 structurally complete observations at that same clock hour.
   Prior extreme/event bars and entry-ineligible session bars remain in this baseline; only
   predeclared missing/duplicate/stale/reopen/weekend/DST-defect bars are excluded. Predeclare thresholds
   `k in {2, 3, 4}` and forward horizons `h in {1, 2, 3}` H1 bars. These are nine event-response
   estimates; serializing both `CONTINUATION` and `REVERSAL` produces exactly 18 execution cells
   before symbol/direction reporting splits. Also require the event's absolute open-to-close price move
   to be at least five times twice V2's one-way spread, commission, and slippage schedule resolved
   at the signal timestamp and expressed in price units. The event floor is identical across
   holding horizons; actual future exit costs remain charged in P&L. This fixed floor prevents
   tiny low-volatility moves from becoming events without changing the sample by horizon.
3. Exclude bars crossing the daily data reopen or weekend. For NAS100 and US500, reject any event
   or holding interval intersecting [09:30,10:30) or [15:30,16:00) `America/New_York` and require
   exit no later than 15:30 New York. For XAUUSD, GBPUSD, and GBPJPY, reject any event or holding
   interval intersecting [08:00,09:00) `Europe/London` and require exit before the 16:55
   `America/New_York` broker rollover. These masks and the missing-bar rule may not be changed after
   seeing returns. Only deterministic calendar/session exclusions knowable at signal time may gate
   the proposed future horizon. A later unexpected data defect may not retroactively erase an
   entry: if an M1 bar is missing, duplicate, or stale while a position is open, the affected
   experiment is `TEST_FAILED`, with no imputed stop survival or earlier backfilled exit.

### Frozen expected-M1 predicate

“Unexpected” is defined independently of the observed price file. Before experiment OHLC is read,
V2 must resolve one immutable, version-identified expected-M1 schedule for every in-scope symbol
and date from its authoritative CFD symbol-session calendar. In UTC, an expected M1 interval is
exactly a half-open minute that this frozen schedule marks open after accounting for the regular
weekly session, recurring daily break, weekend, exchange holiday, and early close. Bar absence may
not be used to infer any of those closures.

For an expected interval, there must be exactly one fresh OHLC record with the correct timestamp.
No record is an unexpected missing bar; more than one record is a duplicate; and a record whose
timestamp or OHLC state does not advance under V2's existing integrity check is stale. If the
first such defect occurs after entry and before or at the M1 bar needed to establish the actual
close, the affected experiment is `TEST_FAILED`. Publish the symbol, UTC interval, calendar
version, and defect type; do not erase the trade, infer stop survival, or backfill an exit. A
scheduled-closed interval is not missing and is never bridged into an H1 bar or holding horizon.

If the authoritative calendar or its version identifier is unavailable or ambiguous for any
in-scope symbol-date, fail before publishing strategy metrics. Do not infer expected intervals
from bar presence, absence, neighboring dates, or realized returns. This corrects the circular
part of V2's proposal—“exchange holidays visible in the data”—while preserving its regular-hours,
daily-break, weekend, and exchange-holiday intent.
4. Let `q = sign(event_return) * forward_return`. The continuation gross return is `q`; the
   reversal gross return is `-q`. For each response mode, compute its own hypothetical net return
   by subtracting that mode's resolved entry and exit costs from its gross return. Report raw price,
   both mode-specific gross returns, and both mode-specific net returns; do not optimize the sign
   per symbol.
5. Report pooled estimates with day-clustered uncertainty, every symbol and direction, both fixed
   development halves, event counts, and concentration after removing the largest one and five
   events. Each horizon keeps its predeclared session-eligible sample, but also report all horizons
   on the fixed subset of events whose complete three-hour horizon is eligible; this common-event
   sensitivity is report-only and prevents cutoff-driven sample composition from masquerading as
   horizon decay. Compare with same-clock non-event returns and shuffled event signs.
6. The sole primary diagnostic setting is `k=3, h=1`. Its response mode is determined
   mechanically from the sign of the pooled `q` estimate: positive maps to continuation and
   negative maps to reversal; both mode cells remain counted as a two-sided test. A later trading
   specification is allowed only if this primary setting's common sign is stable at adjacent
   thresholds and horizons, in both development halves, and across at least three of five symbols,
   with at least 100 pooled events and 20 events per supporting symbol. The fixed common-event
   sensitivity must preserve the sign. No non-primary cell may rescue a failed primary setting;
   all 18 execution cells and all earlier I-61 trials remain counted.

For avoidance of doubt, `q` is also serialized in the strategy artifact as
`q_s_H_h = sign(event_return_s_H) * ln(close_s_H_plus_h / close_s_H)`. A supporting symbol is
exactly one whose primary mean `q` has the pooled primary `q` sign, so the mechanically mapped
mode has positive gross expectancy for that symbol. The primary must also clear two frozen
uncertainty gates: the two-sided day-clustered 95% confidence interval for pooled raw `q` must
exclude zero, and the day-clustered 95% confidence interval for the mapped mode's mean net R must
be wholly above zero. Point-estimate signs alone cannot advance the family.

For the mandatory adjacent-cell sign gate, "adjacent" is frozen as exactly `k=2,h=1`, `k=4,h=1`,
and `k=3,h=2`. The `k=3,h=3` cell and every other cell remain reported and counted but are not
called adjacent. This removes any post-result choice over which neighbors must agree.

The primary-setting rationale is fixed before results. `k=3` is the middle declared threshold,
avoiding both the broadest event definition and reuse of I-61's locally closest `k=4` cell.
`h=1` is the shortest H1 horizon and is closest to the 30-60-minute post-event interval in the
causal Zawadowski et al. evidence; it also minimizes the unsupported assumption that a response
persists for several hours. This rationale does not create a favorable prior: Ederington-Lee is
direct evidence that news-related corrections can finish long before the H1 entry is observable.

## Quantitative-skeptic review

- **Selection bias:** I-61 arose after examining local correlations. All five core symbols and
  all nine threshold/horizon study cells and both response signs must be reported, including
  failures. Earlier I-61 trials count in the program-wide trial history.
- **Parameter selection:** `k=3, h=1` is the only primary setting. The other threshold/horizon
  cells diagnose robustness and decay but cannot become a winner after results. Response sign is
  mapped mechanically from the predeclared pooled `q` sign rather than chosen by net performance.
- **Statistical threshold:** the primary raw response must reject zero with a two-sided
  day-clustered 95% interval and the mechanically mapped mode's mean net R interval must be wholly
  positive. This prevents a favorable point estimate or a secondary cell from advancing an
  underpowered family.
- **Sign ambiguity:** the strongest directly relevant sources disagree. FX daily shocks continue
  intraday; commodity turning-point shocks reverse. Either sign, or no stable sign, is plausible.
- **Lookahead:** a turning-point reversal method cannot be implemented when the turning point is
  only knowable later. Alternating turning-point legs also make a contrary next leg partly
  definitional. The local event must be triggered strictly at the closed H1 bar.
- **Time-of-day confounding:** volatility and news arrival vary sharply by clock hour. A global
  volatility threshold would mostly rediscover scheduled announcements and active sessions. The
  Zawadowski et al. design independently supports a same-clock filter rather than a global one.
- **News confounding:** without a point-in-time news calendar, results must at least be broken out
  by clock hour and flagged as potentially announcement-driven. A news filter cannot be invented
  after results. Ederington-Lee also implies that a news-related correction may finish long before
  the proposed H1 entry becomes observable.
- **Dependence and sample size:** adjacent extreme bars and correlated indices are not independent.
  Execute each grid cell independently, use one event per symbol until that cell's originally
  scheduled forward horizon expires even after an early stop, and cluster inference by date.
- **Future-data availability:** planned session/rollover eligibility is deterministic, but an
  unexpected future missing bar is not knowable when the signal fires. It cannot be used to cancel
  the historical entry. Because an interior gap also makes stop survival unknowable, the affected
  experiment fails rather than imputing a path or using the last earlier bar as an exit.
- **Horizon eligibility:** longer horizons mechanically lose more events near excluded windows.
  Report the predeclared per-horizon samples and the fixed common three-hour-eligible event subset;
  neither view may be selected after results.
- **Crash dominance:** March 2020 and a few macro shocks may create the entire Pearson result.
  Largest-event exclusions are rejection tests, not optional robustness decoration.
- **Costs:** Caporale-Plastun omits all costs; Borgards et al. also abstracts from fees/slippage;
  Grant et al. finds cost adjustment materially weakens index-futures reversal. Zawadowski et al.
  shows that spread widening can remove most NYSE reversal profit even when NASDAQ remains
  positive, and Rif-Utz finds crash-interval spreads nearly triple. Net survival under each CFD's
  resolved costs is mandatory before any submission.
- **No holdout:** no final-holdout access is requested or authorized.

Decision: retain as a low-priority, low-cost falsification re-study because its causal baseline
and rejection rules differ materially from the prior I-61 test. Keep the existing two-sign draft
unqueued; do not select or queue a directional strategy until the sign study passes its
predeclared breadth, sample-size, stability, event-concentration, and cost screens. If it again
fails, do not re-specify the shock family from the same data.

Resume point: Gate 1's pilot is terminal and retained in canonical `rejected/`. V2 answered all
seven mapping questions in `FB_INTRADAY_H1_SHOCK_RESPONSE_20261029T164921Z_e881`: mixed-timezone
aggregation, causal same-clock robust state, signal-time costs, independent cells, diagnostic
publication, and separate raw/executed responses are supported or buildable. Research has now
frozen “unexpected” through the pre-OHLC, immutable, version-identified expected-M1 predicate above
and in the mutable v0.1.0 JSON. Next reconcile promised result fields with the current contract and
independently review both the predicate and publication mapping. It remains unqueued and no
holdout is authorized.

Update 2026-11-02: the result fields are reconciled in
`reports/R004_CANONICAL_RESULT_MAP.md`, and the exact JSON candidate is bound to SHA-256
`FF8C351894E02DF22163C475470C399F96D3F075A8801CFF4BACC5B2A9E6EA73` in
`reports/R004_INDEPENDENT_REVIEW_PACKET.md`. That packet is only a reviewer checklist: V2 calendar
and serialization confirmation plus an actually independent verdict remain required before any
promotion or queue action.

Update 2026-11-03: V2 canonically confirmed in
`FB_INTRADAY_H1_SHOCK_RESPONSE_20261102T232536Z_ca99` that the required authoritative CFD
symbol-session calendar does not exist. This is an `UNSUPPORTED_DATA` outcome, not permission to
queue the draft so implementation can begin. R004 is now capability-blocked, its review binding is
`BLOCKED_EXTERNAL`, and independent review is suspended. The draft remains unqueued and immutable
at the bound hash. If V2 later publishes a sourced, versioned calendar independently, research must
repeat compatibility confirmation and independent review before considering a new handoff; no run
or holdout access is authorized.
