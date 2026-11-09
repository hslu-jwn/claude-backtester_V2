# Day-flat frozen-backlog triage

Date: 2026-10-28  
Scope: open ideas in `existing_material/backtester_v2/ideas.md` that could use supported OHLC data,
avoid overnight exposure, and do not require holdout access.  
Outcome: **no new strategy draft.** Continue the existing diagnostics before expanding the trial
family.

## Decision criteria

An item ranks higher only if it has independent empirical evidence, a mechanically distinct
signal, supported data and execution, plausible cost survival, and limited overlap with recorded
failed trials. A method for sampling or filtering events is not itself evidence of directional
edge. Book examples without a reproducible sample are hypothesis prompts, not validation.

## Triage

| Backlog item | Decision | Reason |
|---|---|---|
| I-17 time-of-day drift | Continue only as R-2026-005 diagnostic | The source effect is real gross, but published cost evidence is adverse and fixes/openings are competing explanations. The residual study is already fully specified. |
| I-16 intraday volatility-shock fade | Absorbed by R-2026-004; do not open another family | The sign-agnostic continuation/reversal grid already tests both fade and continuation after large H1 moves and retains failed I-61 in multiplicity. |
| I-55 CUSUM event trigger | Method only; park | CUSUM changes event sampling but supplies no directional prediction. Adding it after I-61/R-2026-004 would be another same-data event-definition search. |
| I-47 Euro-night stretched-limit fade | Park; bounded independent-evidence search negative | No peer-reviewed study matching its ATR-stretched session limit was found. Adjacent reversal evidence uses daily, opening, or fix events, while broad intraday FX rule evidence is adverse after costs. See `I47_I48_INTRADAY_FADE_EVIDENCE_CHECK.md`. |
| I-48 Euro-day exhaustion fade | Park; bounded independent-evidence search negative | No independent study matching its short-extreme/long-momentum next-bar limit was found. The book result depends on a few large winners and broad cost-aware evidence does not raise its prior. See `I47_I48_INTRADAY_FADE_EVIDENCE_CHECK.md`. |
| I-33 compression breakout | Park; bounded independent-evidence search negative | The cited price-action/volume books provide no statistical sample. A 2026-10-28 check found no direct peer-reviewed compression-to-intraday-direction study; adjacent opening/long-horizon breakout evidence does not transfer and a registered daily-squeeze preprint is adverse. See `I33_COMPRESSION_BREAKOUT_EVIDENCE_CHECK.md`. |
| I-49 volatility-percentile regime filter | Reporting/risk diagnostic only; never rescue a failed primary | Volatility predicts risk, but published conditional performance is strategy-specific and real-time out-of-sample benefits are not systematic. No evidence supports the universal "trend low/fade high" map. See `I49_VOLATILITY_REGIME_FILTER_EVIDENCE_CHECK.md`. |
| I-52 cost-limit screen | One-sided pretest rejection/ranking tool only | Turnover times real cost can reject an idea whose optimistic gross bound is already too small, but the book's fixed 0.13 cutoff assumes an unearned gross Sharpe. Passing means cost-feasible/edge-unknown, not validated. See `I52_COST_LIMIT_SCREEN_METHOD_CHECK.md`. |
| I-50 meta-labeling | Park; never rescue a failed base signal | Method demonstrations do not supply transferable net evidence, and every feature/model/threshold adds trials. The proposed base strategies already failed, so filtering them would be a same-data search for favorable pockets. See `I50_META_LABELING_EVIDENCE_CHECK.md`. |
| I-58 half-life z-score mean reversion | Park; bounded independent-evidence search negative | Supportive OU evidence trades stationary pairs or factor residuals, not a single raw price. Half-life and Hurst estimates are noise/bias sensitive, while direct intraday FX studies find costs erase most price-rule predictability. See `I58_HALF_LIFE_MEAN_REVERSION_EVIDENCE_CHECK.md`. |
| I-38 session-mean “VWAP proxy” | Park; bounded independent-evidence search negative | VWAP research treats it as an execution benchmark for a parent order, not a directional fair-value signal. The proposed OHLC mean is not volume weighted, its hold/rejection event is flexible, and it overlaps failed opening/gap families. See `I38_VWAP_PROXY_EVIDENCE_CHECK.md`. |
| I-30 round numbers and daily pivots | Diagnostic annotation only; no directional or target/skip rule | Primary FX evidence confirms conditional orders cluster at round numbers, but take-profit orders imply reversal while stop-loss orders imply continuation. OHLC does not identify the latent order type, and the studies do not establish net profitability or validate gold/index increments or daily pivots. See `I30_ROUND_NUMBER_EVIDENCE_CHECK.md`. |
| I-31 M1 time-at-price value area | Park; closest systematic breakout evidence is null | The nearest ES value-area study finds the unconditional breakout insignificant, while a positive one-year thesis requires centralized tick volume and footprint absorption and excludes fees. M1 time occupancy is not executed volume, and the level does not select breakout versus fade. See `I31_TIME_AT_PRICE_VALUE_AREA_EVIDENCE_CHECK.md`. |
| I-11 midday support/resistance breakout | Park; cited result does not identify day-flat P&L | The book reports $268/trade gross on 8,404 S&P futures trades, but notes positions may be held overnight and does not disclose whether the result forces a close. Costs, execution ordering, component attribution, and independent out-of-sample evidence are absent. See `I11_MIDDAY_SUPPORT_RESISTANCE_EVIDENCE_CHECK.md`. |
| I-13 congestion third-bar reversal | Reject; direct programmed replication is null/adverse | A 1991 test of explicit Nofri adaptations across wheat, gold, and S&P daily series produced 3,825 trades, no significant long/short separation, and losses on both S&P sides. The frozen intraday/ATR version adds unsupported parameters and greater cost burden. See `I13_NOFRI_CONGESTION_REVERSAL_EVIDENCE_CHECK.md`. |
| I-40 exhaustion reversal | Park; compound filters add no independent evidence | Consecutive candles, extreme RSI, prior-day/round-number location, reversal candle, confirmation, and three target choices create a large interaction search. Adjacent candle evidence conflicts, RSI filtering is not generally additive, intraday costs are adverse, and the rule aliases I-16/R-2026-004. See `I40_EXHAUSTION_REVERSAL_EVIDENCE_CHECK.md`. |
| I-41 wick rejection / spring-upthrust | Park with I-42 inside the I-33 zone family | Intraday candle studies find no robust after-cost, data-snooping-controlled edge, the parent zone is unsupported, and wick/tolerance/HTF definitions add discretion. See `I41_I42_ZONE_ENTRY_VARIANTS_EVIDENCE_CHECK.md`. |
| I-42 breakout retest / role reversal | Park with I-41 inside the I-33 zone family | Daily trading-range-break evidence does not establish that waiting for an intraday retest improves the same breakout net of missed winners and costs. Fade and retest-follow are opposing labels on one zone event and must not become parallel rescue trials. See `I41_I42_ZONE_ENTRY_VARIANTS_EVIDENCE_CHECK.md`. |
| I-43 M1 path-length activity proxy | Volatility/path diagnostic only; never volume or absorption | Established realized-range estimators use normalized squared log ranges and estimate volatility. Raw summed ranges and direction changes are scale/feed/microstructure dependent and do not reveal executed volume, order side, depth, or absorption. See `I43_M1_PATH_LENGTH_PROXY_METHOD_CHECK.md`. |
| I-44 tick-volume rules | Blocked pending a canonical field and data-semantic validation | Broker update counts are feed-specific activity, not executed volume; they cannot reconstruct true VWAP or absorption. A frozen coverage/clock/stability/proxy-validation study must precede one counted A/B interaction. See `I44_TICK_VOLUME_RULES_DATA_CHECK.md`. |
| I-45 cost-to-target filter | Absorbed into I-52; one-sided rejection diagnostic only | Cost/target has no universal 0.10–0.15 pass level because break-even also depends on the stop and hit rate. Use authoritative signal-time cost with the already frozen target to reject infeasible designs; passing remains unknown edge. See `I52_COST_LIMIT_SCREEN_METHOD_CHECK.md`. |
| I-46 gap momentum | Reject cited evidence; published code has the opposite payoff sign | The book enters long after an up-gap but computes `(open-close)/open`, which profits from a fade and loses on continuation. The positive FSTX/GBPUSD headlines therefore cannot support momentum; results are also gross, selected across markets, and lack holdout replication. See `I46_GAP_MOMENTUM_SOURCE_AUDIT.md`. |
| I-62 no-wick retest | Reject; broad local search and selected cluster both failed | Only 0.4% of 4,608 variants were positive, no symbol class showed an edge, and the selected gold H1 cluster failed out of sample at -0.02 R/trade. The limit entry has adverse-selection and cost sensitivity; filters, exit changes, reversed direction, and relabeling are not independent hypotheses. See `I62_NO_WICK_RETEST_PRIOR_RESULT_AUDIT.md`. |
| I-03 RSI(2) mean reversion | Outside current day-flat default | The cited form is primarily H1-D1 and can require overnight holding; do not force it into an intraday adaptation without new evidence. |

## Priority rule

1. Finish traceability of `FX_LONDON_FIX_REV` through a canonical development result.
2. If research capacity is available while waiting, refine and compatibility-review R-2026-005;
   it is diagnostic and cannot create another trial merely because one cell looks favorable.
3. Execute R-2026-004 only after compatibility review and only as the final predeclared
   falsification re-study of the I-61 family.
4. Do not create a new strategy from the parked items unless a later primary-source review adds
   evidence that is independent of the frozen book examples and prior V2 failures.
5. Volatility buckets may describe an already pre-registered result only when frozen in advance,
   counted as additional tests, and prohibited from reversing a failed unconditional verdict.
6. A pretest cost screen may reject or rank a new idea, but passing never supplies evidence of
   predictability and its threshold may not be optimized from local outcomes.
7. Meta-labeling requires a frozen, independently positive base signal and a fully predeclared
   nested-validation budget; it may not be applied after failure to discover a rescuing subset.
8. Round-number distance may be reported as a preregistered descriptive subgroup for an
   independently valid signal, but it may not choose breakout versus fade, suppress trades, alter
   targets, or reverse the unconditional verdict.
9. Time-at-price must not be relabeled as volume-at-price. A value-area boundary or POC cannot be
   added to choose direction or rescue a strategy without independent net evidence for the exact
   supported-data construction.

The remaining backlog's alias and multiplicity relationships are classified in
`REMAINING_DAY_FLAT_BACKLOG_OVERLAP_MAP.md`. In particular, I-10 belongs to the failed opening
family; I-12/I-15 belong to R-2026-004/I-61; I-32/I-34/I-35/I-41/I-42 belong to the parked
compression/zone family; and filters, exits, and sizing modules cannot become standalone edges.
