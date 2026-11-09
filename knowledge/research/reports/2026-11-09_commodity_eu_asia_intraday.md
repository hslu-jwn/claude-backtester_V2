# Intraday / session-level predictability: gold, oil, EU and Asian indices (2026-11-09)

Scope: day-trade rules (in/out same session, stop 0.5 x daily ATR, results in R) on XAUUSD, USOIL, GER40, UK100, JP225, EU50.
Cost hurdle from our table: ~0.04 R (gold, DAX, FTSE, Nikkei), ~0.10 R (oil). A stop of 0.5 ATR is roughly 50-70 bp on index CFDs, so 0.04 R is ~2-3 bp and a rule needs gross edge well above that.

## Source status (honest)

Only ONE paper was read in full. Most others were reached only through web-search summaries; the publisher pages were blocked (403/404/Anubis) or abstract-only. Nothing below marked NOT-OPENED was verified against the paper text.

| Source | Status | Notes |
|---|---|---|
| Baltussen, Da, Lammers, Martens (2021), "Hedging demand and market intraday momentum", JFE 142:377-403 (author PDF academicweb.nd.edu/~zda/intramom.pdf) | OPENED-FULL (pdftotext; tables partly garbled, numbers below are those I could read unambiguously) | Main source |
| Barbon, Buraschi, "Gamma Fragility" (abarbon.com/papers/gamma-fragility) | OPENED-ABSTRACT (project page only) | Single stocks, no magnitudes, no costs |
| Wen, Indriawan, Lien, Xu (2023), Energy Journal 44(5):149-171, "Intraday return predictability in the crude oil market: the role of EIA inventory announcements" | NOT-OPENED (abstract text via search summaries; Adelaide PDF returned only "DSpace") | No effect sizes obtained |
| Rousse, Sevi (2019), "Informed trading in the WTI oil futures market", Energy Journal 40(2):139-160 | NOT-OPENED (search summary of abstract; HAL blocked) | |
| Alturki, Kurov (2022), "Market inefficiencies surrounding energy announcements", JFM 42(1):172-188 | NOT-OPENED (bibliographic + one sentence of abstract) | |
| Gu, Kurov (2018), JFM 38(9):1079-1096 (natural gas, not crude) | NOT-OPENED | An earlier search summary wrongly attributed crude-oil drift to it; it is natural gas |
| Geman, Li, J. Energy Markets, crude inventory shocks (response lasts ~25 min) | NOT-OPENED | |
| Kurov, Sancetta, Strasser, Wolfe (2019), JFQA 54(1):449-479, price drift before US macro news | NOT-OPENED (abstract versions via search) | E-mini S&P and 10y Treasury futures, not gold/oil |
| Lucca, Moench (2015 JF) pre-FOMC drift; NY Fed Liberty Street update 2018 | NOT-OPENED (search summaries) | |
| Gao, Han, Li, Zhou (2018 JFE), Heston-Korajczyk-Sadka (2010 JF) | NOT-OPENED (abstract summaries) | |
| Aspris et al., "Towards a new fix" (LBMA auction, working paper) | NOT-OPENED (403; search summary) | |
| Batten et al. (2017) precious-metals intraday seasonality; Hauptfleisch, Putnins, Lucey (2016 JFM); Iwatsubo, Watkins, Xu (RIETI 2017) | NOT-OPENED (search summaries) | |
| Osaka Univ. DP on Nikkei/S&P lead-lag (1985-89 data) | NOT-OPENED | Old sample |

## 1. Crude oil around the weekly EIA report (Wed 10:30 ET)

Claims found (all NOT-OPENED unless noted):
- Wen et al. 2023: on EIA days the return of the "third half-hour" (they say this is when the news is released) significantly and positively predicts the LAST half-hour return; on non-EIA days only the first half-hour return predicts (and that comes mostly from the overnight part). Mechanism offered: more informed traders plus thinner liquidity around the release. Abstract says "substantial economic gains"; I obtained NO bp, Sharpe, sample or cost figures. Exact window definition (is the 3rd half-hour 10:00-10:30 or 10:30-11:00 ET?) not verified.
- Rousse, Sevi 2019 (abstract via summary): buyer-initiated order imbalance in the 2 h before release on days when the EIA figure beats forecasts; average price about -0.25% before the news on such days; over-reaction after the release partly reversed over the following hours. Profit after costs not reported in what I saw. Needs the surprise (actual vs analyst consensus) which is known only after the release for the post-release leg.
- Geman, Li: response to inventory shock is fast and lasts about 25 minutes; hint that some participants know ~10 minutes early.
- Alturki, Kurov 2022: inefficiency in crude futures and stocks around sequential inventory announcements (API Tuesday then EIA Wednesday) - details unverified.
- Gu, Kurov 2018: pre-announcement drift is natural gas (about half of the 2-hour window return is pre-release); it does not establish crude.

Candidate rule 1A (EIA-day intraday momentum, from Wen et al., unverified details):
- Mechanism: informed trading plus low liquidity at release gives a signed drift that persists to the close of the pit/settlement period.
- Entry/exit: signal = sign of the half-hour return containing 10:30 ET (window to be confirmed from the paper). Trade the same sign from 14:00 to 14:30 ET (NYMEX settlement window) - this is a copy of the last-30-min rule, restricted to EIA days.
- Gross effect: UNKNOWN (not obtained). Trades per year: about 50.
- Evidence status: published peer-reviewed (abstract-level only), no independent replication found, post-2020 behaviour unknown.
- Skeptics: ~50 trades/year means a standard error larger than any plausible edge; the last 30 min on a USOIL CFD is not a stop-defined 0.5 ATR trade (the stop would almost never be the binding limit); oil cost 0.10 R means the edge must exceed ~10 bp (oil ATR ~2-2.5%, so 0.5 ATR ~110 bp, 0.10 R ~11 bp) for a 30-min hold, which is large. CFD "last half-hour" differs from the futures settlement window.
- M1+calendar buildable: yes for the window rule (EIA date list needed; Wednesday except holiday shifts). Surprise-based variants need the consensus number: check whether the news calendar in backtester-news has forecast/actual fields for EIA; if not, not buildable.

Candidate rule 1B (pre-release drift in the direction of surprise): not tradable ex-ante; the surprise is unknown before 10:30. A price-only proxy (trade the sign of 10:00-10:29 return into 10:30) is a hypothesis only; no paper found that tests it for crude.

Candidate rule 1C (fade the post-release overreaction, Rousse-Sevi): direction is opposite to the 10:30-10:35 spike, hold hours. Evidence abstract-level, size unknown, conflicts with 1A (continuation to the close). Both cannot be right on the same data horizon; test on our data only as a pair.

## 2. Gold

- Macro releases (CPI, NFP, FOMC): the search found NO peer-reviewed paper that I could open measuring a tradable pre- or post-announcement drift in gold. Only practitioner commentary (CME, Mining.com, e.g. a -1.6% move in the two hours after one FOMC; anecdote). Status: no evidence. Batten et al. 2017 is said to cite earlier work on gold's response to announcements - not verified.
- Pre-announcement drift in other assets (NOT-OPENED): Kurov et al. 2019 - in E-mini S&P and 10y Treasury futures, prices move in the eventual direction in the ~30 minutes before scheduled releases, about 40% of the total adjustment (published version), only for some releases (a 2017 draft: 9 of 20 market-moving ones, 2008-2014). Not tested for gold. Hypothesis for us: sign of the 30-min pre-release return in XAUUSD predicts the release move. Skeptic: CFD spread and slippage around CPI/NFP are largest exactly then; the paper itself does not claim a tradable profit after costs.
- Pre-FOMC drift (Lucca-Moench, NOT-OPENED): about +49 bp in the 24 h before FOMC for the S&P 500 (1994-2011); other major equity indices (ex Japan) show similar behaviour around FOMC; per the NY Fed 2018 update the drift persisted but was mainly in meetings with a press conference and shifted earlier (into the morning of the day before). It is a 24-hour hold, equity beta, ~8 events/year, so it is not a stop-defined day trade and does not apply to gold. Dropped.
- LBMA auction (10:30 and 15:00 London, electronic since March 2015): only a working paper (Aspris et al., NOT-OPENED, 403) with mixed findings, as summarised by search: no clear evidence of exploitable return clustering after the reform, reduced leakage. The older fix manipulation evidence (UWA case study) concerns the pre-2015 process. Status: no tradable evidence; do not build.
- Sessions (Asia / London / NY): descriptive evidence only (NOT-OPENED): Batten et al. 2017 intraday periodicity in gold returns, volatility, volume, spreads (5-min data, 15+ years); Hauptfleisch et al. 2016: NY futures lead price discovery; Iwatsubo et al. 2017: informed trading dominates the NY day session, uninformed Tokyo; a weekday-effect paper (Banks and Bank Systems 2016) says London has the highest returns, then NY, then Tokyo; a CBS student thesis claims hat-shaped intraday seasonality. No mean-return table obtained, no costs; a retail survey (TradersUnion) is not evidence. Status: seasonality of volatility is established, seasonality of signed return is not shown in a tradable size.
- Gold in Baltussen et al.: commodity futures pooled (Panel C) show weaker intraday momentum; gold-only coefficient could not be read from the garbled Table B3. Not usable.

## 3. European / Asian index futures

### 3A Last-30-minutes intraday momentum (Baltussen et al. 2021, OPENED-FULL)
Predictor rROD = return from the previous close to 30 minutes before the close; target = last half-hour return. Table B1, Panel B, equity index futures (sample ends May 2020; start varies; slope coefficients and R2 shown x100 in the paper):

| Future | rROD slope x100 (t) | R2 % | R2 out-of-sample % | rONFH slope x100 (t) |
|---|---|---|---|---|
| DAX (DA) | 3.42 (6.28) | 2.13 | 0.42 | 4.57 (5.45) |
| Euro Stoxx 50 (XX) | 4.98 (7.61) | 4.06 | 3.67 | 5.66 (6.02) |
| FTSE 100 (FT) | 4.28 (7.35) | 3.09 | 2.03 | 5.76 (6.91) |
| Nikkei 225 SGX (EN) | 2.70 (3.74) | 1.30 | 1.20 | 3.31 (3.13) |
| Nikkei TP (Topix) | 2.77 (3.22) | 1.47 | 1.24 | 3.92 (3.59) |

Reading of the column order from the garbled text is my best parse; the DA and FT out-of-sample figures and the EN/XX t-values are consistent across two places in the text, but verify against the PDF before relying on them.
- Tables 2 and 5: pooled equity slope in 2000-2020 is of similar size to 1974-1999 (not decayed in the pooled number; I did not extract the exact sub-period values). The authors state intraday momentum became stronger in recent years and especially in Feb-May 2020.
- The user's recall "DAX weak, FTSE/Nikkei stronger" is only partly right: FTSE and Euro Stoxx are the strongest; DAX is statistically significant but its OOS R2 is small (0.42%); Nikkei SGX is the weakest of the four (but OOS R2 1.2%).
- Table 6: equity timing strategy long/short the last half hour has annualised Sharpe above 1 (gross; the paper states it does NOT include transaction costs and says only S&P 500 futures with one tick cost keep a positive net Sharpe). The Table 6 numbers are garbled in my extract; I do not quote them.
- Mechanism (paper, Table 7-8, S&P 500 only, 1996-2020): the effect is concentrated where option market makers are net short gamma (see section 4) plus rebalancing and late informed trading.

Size per trade (my arithmetic, not from the paper): slope b ~0.034-0.050; mean |rROD| for an index is ~60-90 bp, so expected gross move in the last 30 minutes is b x |rROD| ~ 2-4 bp per trade (FTSE ~3 bp, DAX ~2.5 bp, Euro Stoxx ~3.5 bp, Nikkei ~2 bp). Against a stop of 0.5 ATR (~55-70 bp) this is ~0.03-0.06 R gross versus a cost of 0.04 R. Net edge ~0 to +0.02 R, with 250 trades/year.
- Entry/exit: enter 30 min before the cash close (UK100 16:00 London, GER40 and EU50 17:00 CET, JP225 14:30 JST); exit at the cash close. Direction = sign of previous close to entry-time return (in the paper).
- Evidence: peer-reviewed JFE, many markets, OOS R2 positive for FTSE/Euro Stoxx; but gross of cost; CFD index prices in the closing window reflect the futures/cash close and wider spreads; the pit-close hold is not a 0.5 ATR day trade.
- Skeptics: R2 of 2-4% is tiny; 0.42% OOS for DAX; only |rROD| > ~1.5 x median trades have a meaningful edge (an unverified refinement - the effect is linear in rROD, so large days carry most of it); 20-30 filtered trades a year make a test noisy.
- M1+calendar buildable: yes (previous close, close time per session, DST handling, holiday half-days). This is the only rule here that is fully M1-testable and has a published multi-market backing.

### 3B Opening auction and US-open spillover
- Opening-auction effects in DAX/FTSE/Nikkei: no peer-reviewed tradable paper found in the searches done (the search was shallow here). Status: no evidence.
- US open (14:30-15:30 CET) / 8:30 ET macro spillover into DAX/FTSE afternoon: search returned only practitioner wraps and an unverifiable "66% of highs/lows in first 30 min" claim for ES. Baltussen et al. show first-half-hour predicts last-half-hour inside the same market, but I did not find a cross-market (US to Europe) intraday test. Status: no evidence; hypothesis only (testable with M1 on our data: sign of 14:30-15:30 CET GER40 or US-proxy return vs 15:30-17:30).
- Heston-Korajczyk-Sadka 2010 (NOT-OPENED): half-hour return periodicity at daily lags, individual NYSE stocks; "periodicity at 13/26/39 half-hour lags" gives a same-time-of-day-yesterday effect; not shown for indices or CFDs, magnitudes tiny.

### 3C US close to Nikkei open (note only)
Older work (Osaka DP citing 1985-89 data, NOT-OPENED): US-to-Japan effect is absorbed in the first hour of Tokyo trading; Tsutsui (2002): Nikkei reacts to a >1.5% Dow move by the next close, no later. This is an overnight/gap effect, so not a day trade by definition. The reaction inside the first hour is a day-trade candidate only if the CFD gap closes slowly, which we can test on M1. No post-2010 evidence found. Status: no evidence for a day-trade rule.

## 4. Volatility-regime / option-gamma conditioning

- Baltussen et al. Table 7 (OPENED-FULL; S&P 500 futures, Jan 1996-May 2020, Newey-West t): when prior-day net gamma exposure NGE < 0 (dealers net short gamma) the rROD slope is 6.63 (t 4.78), R2 3.58%; when NGE >= 0 the slope is 0.82 (t 1.03), R2 0.05%. Table 8 regressions confirm that more negative NGE gives stronger momentum. So the claim "gamma sign decides momentum vs no momentum" is supported for S&P 500 last-30-min, gross, with NGE reconstructed from OptionMetrics open interest (assumption: dealers short customer positions).
- Barbon, Buraschi "Gamma Fragility" (OPENED-ABSTRACT only): gamma imbalance sign predicts intraday momentum (negative) vs reversal (positive) in single stocks; effect strongest in illiquid stocks and linked to flash crashes. No magnitude or cost information obtained. Reversal in the positive-gamma case is claimed here, but Baltussen finds ~zero momentum, not reversal.
- 0DTE/SpotGamma-type claims: practitioner sources only; one secondhand mention of a 2026 SSRN paper (Adams et al.) finding lower realised vol and muted momentum with 0DTE; NOT-OPENED. No clean published after-cost backtest of gamma-conditioned intraday trading in index futures was found.
- Buildability: gamma needs option open interest by strike; we have none for these CFDs, and the paper is S&P 500 only (nothing found for DAX/FTSE/Nikkei options). Not buildable. A realised-volatility proxy (e.g. high prior-day range) is a different hypothesis with no published support found here; if tested it must be flagged as an unsupported proxy.

## Summary table

| # | Rule | Instrument | Entry / exit | Gross per trade (published or derived) | Trades/yr | Status | M1+calendar? |
|---|---|---|---|---|---|---|---|
| 3A | Last-30-min momentum on sign of rest-of-day return | UK100, EU50, GER40, JP225 | enter close-30 min, exit close | ~2-4 bp (my derivation from slope x |rROD|; paper gross-of-cost) | ~250 | peer-reviewed, OPENED-FULL | yes |
| 1A | EIA-day momentum into settlement | USOIL | signal from 10:30 ET half-hour, hold 14:00-14:30 ET | unknown | ~50 | peer-reviewed, NOT-OPENED | yes (calendar) |
| 1C | Fade post-EIA overreaction | USOIL | after 10:30 ET spike, hold hours | unknown | ~50 | abstract-level, NOT-OPENED | partly (needs surprise) |
| 2a | Pre-release drift continuation before CPI/NFP | XAUUSD | sign of pre-release 30 min, into release | untested for gold | ~24 | paper on ES/ZN only, NOT-OPENED | yes, but news spread |
| 4 | Gamma-conditioned momentum | indices | as 3A conditioned on NGE<0 | slope 6.63 vs 0.82 (S&P only) | ~125 | OPENED-FULL, S&P only | no (needs options OI) |

## Dead or unsupported
- Gold LBMA auction trades, gold around CPI/NFP/FOMC, gold session-return rules: no usable published evidence found.
- Pre-FOMC drift: 24-hour equity hold, decayed/shifted post-publication, not a day trade, not gold.
- Cross-market US-to-DAX intraday spillover, opening-auction rules, Nikkei overnight lead-lag: no post-2010 evidence found; overnight is not a day trade.
- Gamma/GEX rules: need options data we do not have; evidence is S&P 500 only.
- Bare 3A on JP225 (weakest slope) and on GER40 (OOS R2 0.42%) at 0.04 R cost: edge indistinguishable from cost.

## Limits of this note
Search tool only; most full texts blocked. Numeric entries marked "unknown" were not obtained, not zero. The Table B1 values come from a garbled PDF-to-text extraction and need a check against the original before they go into a spec.
