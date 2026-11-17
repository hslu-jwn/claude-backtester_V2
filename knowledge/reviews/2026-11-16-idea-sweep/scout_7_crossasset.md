# Scout 7: cross-asset lead-lag / regime (A) and portfolio construction from weak streams (B)

Method note: sources were read as search-result excerpts, not full papers. Anything not shown in an excerpt is marked UNVERIFIED. Priors are rough and mean "helps after costs on owned data".
Ledger overlap checked: L14-L18 (lead-lag, all falsified on cost), I51 (daily CFD trend killed, net Sharpe -1.03), H02/I85/I86 (index last-30 / noise-band momentum killed), C1/C2/I97 (crypto momentum killed), multi-day CFD holds (swap).

## A1. Volatility-managed overlay on surviving streams (Moreira-Muir; Man AHL vol targeting)
- Mechanism: scale exposure by inverse of recent realized variance; variance is forecastable, expected return barely moves with it. Applied to our own R-streams (Strategy 20, I-73) and to index/ETF beta.
- Venue/symbols: overlay on crypto weekly sorts (Binance) and Alpaca ETFs (SPY QQQ IWM); FTMO indices as a hedge-free test. Horizon: daily/weekly rescale.
- Data: OWNED.
- Effect: market portfolio alpha 4.9 %/yr, Sharpe +25 % vs buy-and-hold (1926-2015, factors +50-100 % Sharpe). Man AHL (Harvey et al., JPM 2018): US equity Sharpe 0.40 -> 0.48-0.51; little effect for bonds, FX, commodities; fewer tail events in all classes (60+ assets, daily from 1926).
- Source: https://www.nber.org/papers/22208.pdf ; https://people.duke.edu/~charvey/Research/Published_Papers/P135_The_impact_of.pdf . Quote (search summary, not verbatim paper text): UNVERIFIED verbatim; paper title "Volatility Managed Portfolios".
- Differs from ledger: not an entry signal, an overlay; no ledger row tests vol-scaling of the survivors. Cheap: one scaling column on existing trade lists, zero extra trades, zero extra spread.
- Prior it helps (Sharpe or drawdown of the survivors after costs): 30 %. As new standalone alpha: under 10 %.

## A2. Defensive trend filter on US equity ETFs plus cross-asset ETF TSMOM (no swap)
- Mechanism: time-series momentum / 10-month-style filter across asset classes; crisis "smile". I51 died on CFDs because swap and spread ate it (gross Sharpe already -0.13), so the testable version is ETFs (no CFD swap) from the free Alpaca account: extend the download with TLT IEF GLD SLV USO DBC UUP EEM etc. (ETF list is my suggestion, not tested).
- Venue: US ETFs, goal 2 (not FTMO). Horizon: monthly rebalance, daily bars.
- Data: FREE (Alpaca account, daily bars of ETFs; extra symbols need download) / OWNED for SPY QQQ IWM DIA and 11 sectors.
- Effect: Hurst-Ooi-Pedersen, 67 markets, 1880-2013, net Sharpe about 0.77 (after 2-and-20 fees), correlation to S&P about 0.00; losses up to 25 % over long periods. Post-2010 decay UNVERIFIED (not seen in excerpts).
- Source: https://oxfordstrat.com/coasdfASD32/uploads/2016/03/A-Century-of-Evidence-on-Trend-Following-Investing.pdf . Quote: UNVERIFIED verbatim (summary says "smile" pattern in extreme years).
- Differs: I51 was CFD universe with swap; this is ETFs and no daily-loss-limit use. Honest limit: monthly trades, so only ~12 rebalances a year per sleeve; t >= 3 on a 2016+ ETF sample is unlikely (power).
- Prior: 12 % (clears t 3 on 2016-2026 ETFs). Value is as a regime sleeve in the portfolio, not as a gate-passing screen.

## A3. Overnight drift timed to the European open (NY Fed SR 917)
- Mechanism: US equity futures return is earned overnight, concentrated around 02:00-03:00 ET (European open); linked to inventory risk and close order imbalance.
- Venue: FTMO US500 / NAS100 / US30 / GER40 / EU50 M1; hold a short window (1-2 h) around the European open, avoiding swap by not holding through rollover. Horizon: intraday window.
- Data: OWNED.
- Effect: 1998-2019, close-to-close 4.5 %/yr, overnight 3.1 %/yr, intraday 1.4 %/yr (CEPR DP14462 summary). Hour-level bp per day UNVERIFIED; at about 3 %/yr over 252 days it is roughly 1.2 bp/day total overnight, so the one-hour slice is under the index spread (likely cost wall).
- Source: https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf . Quote: "bulk arriving around the European open" (paraphrase from excerpt, UNVERIFIED verbatim).
- Differs: L14 tested US close -> DE open lead-lag, not a fixed-window drift; calendar-effect kills (turn of month etc.) are different clocks. Likely overlaps in spirit with L14 and the cost wall.
- Prior: 5 %. Listed so it is closed on a power/cost line, not because it is promising.

## A4. Hedging-demand intraday momentum beyond equity indices
- Mechanism: gamma-hedging flows push the last 30 minutes in the direction of the rest of the day; 60+ futures across equities, bonds, commodities, currencies; reverts over following days.
- Venue: FTMO commodities and metals (XAUUSD, USOIL, UKOIL, NATGAS), FX, bond proxies absent. Horizon: last 30 min.
- Data: OWNED.
- Effect: Gao-Han-Li-Zhou SPY first-half-hour -> last-half-hour R2 1.6 % in-sample, 1.2 % out-of-sample, 1993-2013; rule earns about 6.3 % gross per year vs -0.5 % (CXO summary), and cost may erase it. Baltussen et al. (JFE 2021), 1974-2020: "highly significant" predictive power across markets (effect size UNVERIFIED).
- Sources: https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403 ; https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414 .
- Differs: H02/H06 (index last-30) and I85/I86 are falsified on indices; non-index markets (gold, oil, FX) with no gamma-hedging mechanism have no stated theory, so expect null.
- Prior: 4 %. Mostly a closure note: index family is already dead on cost.

## A5. Crypto jump spillover into US index CFDs (event-driven, not lead-lag drift)
- Mechanism: BTC jumps transmit to US tech / financial sectors at high frequency; Chicago Fed 2026 finds BTC beta to US equities has risen (clearer vs Dow than Nasdaq).
- Venue: BTCUSD/ETHUSD (FTMO M1 or Binance 1 min) -> NAS100/US30 next 1-15 minutes; Horizon: minutes.
- Data: OWNED.
- Effect: Leong and Kwok, Financial Review 2025: positive jump and diffusion spillovers from BTC to equity sectors (no bp figure in excerpt, UNVERIFIED). Thesis evidence says BTC often lags in crypto lead-lag.
- Sources: https://econpapers.repec.org/RePEc:bla:finrev:v:60:y:2025:i:2:p:453-479 ; https://www.chicagofed.org/-/media/publications/working-papers/2026/wp2026-16.pdf
- Differs: L18 was BTC/ETH pair; no ledger row for crypto -> equity index. Weakness: weekend/overnight crypto moves vs index closed; spread 1-3 bp on NAS100.
- Prior: 5 %.

## B1. Deflated Sharpe, Harvey-Liu haircut, and McLean-Pontiff decay as the gate for near-misses
- Mechanism: judge each stream by Sharpe deflated for number of trials (expected max Sharpe under N zero-skill trials, skew/kurtosis adjusted); Harvey-Liu haircut is non-linear (marginal strategies lose most). Decay evidence: 26 % lower out-of-sample, 58 % lower post-publication (97 predictors, McLean-Pontiff); Quantpedia database: out-of-sample Sharpe 33 % lower on average, 44 % lower median.
- Venue: all; uses the ledger itself (190 rows, effective N from correlated trials, e.g. family-level N). Horizon: n/a.
- Data: OWNED (the ledger and trial log).
- Sources: https://papers.ssrn.com/abstract=2460551 ; https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF ; https://Www.Gwern.net/doc/economics/2016-mclean.pdf . Quote: "highly significant in a single test" (Harvey-Liu, from excerpt, so UNVERIFIED verbatim).
- Differs: the project uses fixed t >= 3 and a halved-effect power rule; it does not compute DSR with the actual trial count. Concrete, testable: compute DSR for I-73, I-78, I-83 with N = per-family trial count from results/trials.jsonl and report the probability the true Sharpe > 0. Decision aid, not alpha.
- Prior it improves decisions: 60 % (cheap, no new data). Prior it creates new alpha: 0 %.

## B2. Combine many weak streams: forecast combination, diversification multiplier, fundamental law
- Mechanism: IR ~ IC x sqrt(breadth) (Grinold) so many weak, low-correlation rules beat one; Carver weights rules by equal volatility and scales with a forecast diversification multiplier from the correlation matrix (e.g. 2 assets, rho 0.5 -> 1.15; rho 0 -> 1.44). AHL: weak signals everywhere, combined. Quote (Sargaison, Risk.net): "Momentum is a relatively weak signal" (excerpt, UNVERIFIED verbatim).
- Test: pre-register a pool rule that picks streams by criteria set BEFORE their sample (family-level, not by looking at t), cap each weight, estimate correlation on the dev window only, and run the single OOS test on the combined stream. Caveat: pooling streams chosen for t 1.5-2.5 on the same sample inflates pooled t (selection bias, see B1); only streams with independent signals and a fixed rule qualify. Carver: Sharpe consistently above 1.0 is rarely achieved; backtested 2.0+ is overfit.
- Source: https://www.risk.net/awards/5368836/quant-hedge-fund-of-the-year-man-ahl ; https://the7circles.uk/?p=24066 (book itself not read: UNVERIFIED).
- Venue: crypto weekly sorts (I-73, I-78, I-83, FB-017 are already corr 0.83) plus near-miss CFD streams on owned data. Horizon: weekly.
- Differs: no ledger row combines near-miss rows; killed rows are closed, so pool candidates are the t 1.5-2.5 rows only.
- Prior it lifts Sharpe of survivors after costs: 15 % (survivors are correlated 0.83); prior it rescues near-misses to t >= 3 honestly: under 5 %.

## B3. Strategy-level allocation: inverse-vol versus HRP for daily-loss limits
- Mechanism: Lopez de Prado HRP clusters strategies by correlation, allocates top-down; claimed lower out-of-sample variance than CLA min-variance (in the paper's Monte Carlo). Independent blog replication: HRP did not beat simple risk parity.
- Test: inverse-volatility vs HRP vs equal-risk on the R-stream matrix with the existing FTMO simulator; metric = probability of breaching the 5 % daily limit and max drawdown.
- Venue: portfolio layer (risk/), no new data. Data: OWNED.
- Source: https://papers.ssrn.com/abstract=2708678 ; https://gmarti.gitlab.io/qfin/2019/12/04/hierarchical-risk-parity-part-3.html .
- Differs: ledger has no portfolio-weighting test. Expect inverse-vol to be enough with only 2-4 streams.
- Prior it helps (lower breach probability): 25 %.

## B4. Prop-firm challenge as a barrier problem: size per stream and a daily-stop rule by Monte Carlo
- Mechanism: pass = hit +10 % before -10 % (and 5 % daily); pass odds rise steeply with Sharpe (blog: 10-17 % at Sharpe 0.5, 60-75 % at Sharpe 2.0; low-quality source) and with lower correlation between streams. Optimise risk per trade and a daily-stop that cuts risk after a loss; trailing drawdown cuts pass rate by about a third (same blog, UNVERIFIED).
- Venue: FTMO 2-step rules; crypto prop firms (HyroTrader etc.). Data: OWNED (R-streams plus existing risk/ simulator).
- Sources: https://delphicalpha.substack.com/p/prop-firm-math-what-the-rules-actually ; https://curupira-blog.pages.dev/blog/starting-from-the-end-prop-firm-monte-carlo/ (blogs, not peer reviewed). Academic anchor: Lehoczky 1977 (UNVERIFIED, cited secondhand).
- Differs: project already has FTMO pass-probability Monte Carlo; the new part is optimising stream mix and stop rules on the multi-strategy R matrix, and trading frequency (fewer strategies can still pass).
- Prior it improves pass probability materially for the same streams: 30 %. It adds no edge; with zero edge pass odds are non-trivial but net-negative after fee.

## B5. Combine survivors with a regime switch by volatility state (defensive switching)
- Mechanism: run the crypto weekly sorts (Strategy 20 and I-73) at full size in low-volatility regimes of BTC and halve them in high-variance regimes (A1 scaling applied to the portfolio, not to one stream); same variance-forecastability argument.
- Data: OWNED. Horizon: weekly.
- Source: same as A1. Differs: Strategy 20 is tail-driven, so vol scaling may cut the winning tail weeks; this is the specific risk that makes the test informative.
- Prior: 20 % that drawdown falls without losing more than 20 % of net R.

## Ranking by usefulness (my pick)
1. B1 (cheap, directly raises the quality of go/no-go on survivors).
2. A1 / B5 (vol overlay on survivors; no new data).
3. B4 / B3 (portfolio and challenge optimisation).
4. A2 (ETF cross-asset trend sleeve; needs a small Alpaca download).
5. B2 (only with strict pre-registration).
A3, A4, A5 are listed for closure; priors below 6 %.
