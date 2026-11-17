# Scout 8: newest work (2024-2026) - candidate directions

Method note: web search snippets only; PDFs (Baltussen EOD, Harvey et al.) could not be text-extracted, so effect sizes there are UNVERIFIED. Quotes come from search-result text, not full-text reads. Nothing tested.
Already in ledger and therefore NOT proposed again: noise-band intraday momentum (I-85/86), dealer gamma days (I-86), last-30-min index momentum (H02/H06), month-end/turn-of-month (H04/I67), opex week (I70), CME BTC expiry (I69), overnight premium (I87), liquidation reversal (I76), listings (I81), earnings/gap reversal on shares (I-96 family), index-review auction (I71).

## 1. End-of-day cross-sectional reversal in US stocks (last 30 min -> next open)
- Mechanism: intraday losers receive positive price pressure in the last 30 min (market-maker hedging / institutional close flow); partial reversal after. Authors name hedging by market makers as candidate driver; a summary says gamma/liquidity does not explain it (sources conflict).
- Venue/symbols: US large caps (Alpaca M1 owned: ~46 names + sector ETFs; paper uses full CRSP-style universe, so a 46-name universe is a power risk). Horizon: 30 min to overnight/next open.
- Data: OWNED (Alpaca minute bars, download in progress). Trading via FTMO share CFDs (~46) or just research.
- Published effect: UNVERIFIED size (paper: Baltussen, Da, Soebhag, "End-of-Day Reversal", Apr 2025 draft, Quantpedia Awards 2025 2nd place). Sample long (US, decades).
- Source: https://www3.nd.edu/~zda/EOD.pdf (moved to https://academicweb.nd.edu/~zda/EOD.pdf); quote (search summary, UNVERIFIED verbatim): "sharp intraday return reversals in the cross-section during the last 30 minutes"
- Differs from ledger: I-96 was overnight->intraday gap reversal, H02 was index time-series momentum. This is intraday-loser -> last 30 min buy, cross-sectional, closes at the bell.
- Capacity: close pressure is large-cap, thin per-stock; funds with 0.2 bp costs cannot trade the closing auction with size in all names without moving it; 46-name universe small. Prior survive costs: 12 % (CFD spread 10 bp class kills it; only ETFs/very liquid names possible).

## 2. VIX ETP rebalancing -> end-of-day VIX futures drift
- Mechanism: VIX ETP issuers (VXX, UVXY, SVXY etc.) must rebalance futures to hold constant maturity / leverage, trading near the close, mechanically after large VIX moves.
- Venue/symbols: VX futures (not owned); proxy via SPY/VIX-correlated only. Horizon: last 30-60 min.
- Data: PAID (VX intraday, CBOE/Databento) - NOT owned; FTMO has no VIX CFD verified (UNVERIFIED).
- Effect: O'Neill & Whaley (J. Futures Markets 2023, vol 43, pp 33-68): rebalancing "has significantly positive predictive power for end-of-day futures returns"; impact has DECLINED as hedge funds added liquidity. No bp size found. Sample not seen.
- Source: https://econpapers.repec.org/RePEc:wly:jfutmk:v:43:y:2023:i:1:p:33-68
- Differs from ledger: HV-T0067/0083 VIX backwardation were daily-signal, unfetchable. This is a mechanical flow signal computed from the VIX level change.
- Capacity: decayed already; futures-only. Prior 5 % (data not owned and fading).

## 3. Leveraged / inverse ETF rebalancing flow on indices, 2024-2025 update (see-saw effect)
- Mechanism: LETF issuers must rebalance daily at the close proportional to the day's index return squared (+leverage); intermediary options delta-hedging adds a second flow. Barbon et al.: LETF part decreasing over time, option-gamma part persistent; effects revert at next open.
- Venue: SPY/QQQ + index CFDs (US500, NAS100) and sector ETFs; horizon: last 30 min then next open.
- Data: OWNED (Alpaca SPY QQQ IWM sector ETFs M1; FTMO indices); LETF AUM paid/UNVERIFIED but can be approximated from public AUM snapshots.
- Effect: 6.9 bp for a 1 % index move on the average large-cap stock (Fed FEDS 2013, old). 2025: Pagano/Rodriguez/Jain/Mishra see-saw paper (Aug 2025), Goel (SPX option spreads) - sizes UNVERIFIED.
- Source: https://papers.ssrn.com/abstract=3925725 quote (snippet): "induce end-of-day momentum and mean-reversion in returns"
- Differs from ledger: H02 (sign right gross, cost wall) tested last-30 momentum unconditionally; here conditioned on the mechanical flow size (squared return x LETF AUM) and including the next-open reversal leg. Likely still cost wall: CFD spread vs 2-5 bp effects.
- Capacity: 0.2 bp funds already trade it (decreasing over time). Prior 6 %.

## 4. Sequential rebalancing front-run: equity-bond threshold / calendar signals (Harvey, Mazzoleni, Melone 2026)
- Mechanism: 60/40 and target-date funds must sell equities and buy bonds when equity drifts past threshold or at month/quarter end; flows predictable, effects fade in "a couple of weeks" (Inquire Europe summary).
- Venue: US500 / US2000 + Treasury futures (not owned) ; horizon: days to 2 weeks. FTMO has no bond CFD verified (UNVERIFIED).
- Data: OWNED for equity side (US500, SPY daily + 60-day return / bond proxy via TLT daily from Yahoo, FREE).
- Effect: for 60/40, threshold signal lowers equity returns about 16 bp, calendar signal about 17 bp; bonds up about 4 and 2 bp (EDHEC copy of SSRN 5122748, summary from search; UNVERIFIED in PDF). Cost est $16 bn a year.
- Source: https://www.edhec.edu/sites/default/files/2026-03/Scientific%20paper.%20ssrn-5122748.pdf
- Differs from ledger: I67 (month-end conditional sign) used a calendar rule on month-end only (t 0.95). This uses a THRESHOLD trigger (relative equity-bond drift beyond band) and multi-day window; 16-17 bp per event for ~tens of events a year: power likely fails (needs ~Event count x sd). Probably closed on power.
- Capacity: authors say funds do not fix it, so some capacity remains; but 17 bp gross per ~12 events a year is low. Prior 5 %.

## 5. Spot bitcoin ETF flow/time-of-day structure (US ETF hours vs rest of day)
- Mechanism: ETF creations/redemptions (cash, in-kind since July 2025) force the AP/issuer to trade BTC spot, concentrated around US hours; most BTC price change occurs OUTSIDE ETF hours (Mazur & Polyzos 2025, JAI). Flow data is published after the close, so a next-day follow-through test is possible.
- Venue: BTCUSDT Binance/Bybit perps and FTMO BTCUSD CFD; horizon: intraday to 1-3 days.
- Data: OWNED for price (Binance 1h/aggTrades/taker-flow); daily ETF flows FREE (Farside, public) but UNVERIFIED availability/licence; crypto dev 2020-23 cannot test ETF era (2024+ only) - the pre-registered split would burn the test period. Weakness.
- Effect: R2 95 % on levels (not a trading effect); no intraday bp size.
- Source: https://zuscholars.zu.ac.ae/works/7267 ; Volmex (undated) https://volmex.finance/Cryptocurrency-Market-Dynamics-Following-the-Approval-of-Bitcoin-ETFs.pdf
- Differs from ledger: all crypto ledger rows are cross-sectional or on-perp flow; none uses spot-ETF creation flow as a forced-trader signal. Problem: ETF era sample < 3 years, whole thing falls in the test period; dev-test split makes it close-able only as a forward log.
- Prior 5 % (also flows already priced by hourly arbitrage).

## 6. Hourly time-of-day pattern in Bitcoin around US cash open/close (post-ETF era)
- Mechanism: when ETF/futures/options venues are open, flow and volatility cluster; CME moved to 24/7 crypto futures (announced to launch 29 May 2026), removing the weekend gap, a structure break.
- Venue: BTCUSD / ETHUSD; horizon: 1-6 h.
- Data: OWNED (Binance 1h, FTMO M1).
- Effect: none reliable published; "CME gap fill" rate 79 of 80 gaps (CoinDesk March 2025, small sample, UNVERIFIED), later estimates 70-80 %, now fading. Gap fill is a basis artefact per sources.
- Source: https://weissratings.com/en/weiss-crypto-daily/the-cme-gap-trade-is-fading
- Differs from ledger: C3 crypto intraday momentum killed on costs; this is a gap-fill / hour-of-day structure and ends with the structural break (24/7), so only pre-2026 sample is usable. Prior 3 % (practitioner folklore, cost wall as C3, structure change kills it).

## 7. Retail-driven overnight (8pm-4am ET) US ETF / equity session: next-open continuation or reversal
- Mechanism: new market structure - Blue Ocean ATS and 24x5 venues: retail-dominated, thin overnight flow; price discovery of non-US news and macro ETFs happens at night; mispricing vs the cash open could mean-revert (retail flow).
- Venue: ETFs (SPY, QQQ, TLT, GLD) overnight vs open; FTMO indices trade 24h so the CFD already prices the night.
- Data: PAID/UNVERIFIED (Blue Ocean tick data via ICE); proxies OWNED: FTMO index CFD overnight M1 (2019+) vs US cash open.
- Effect: "Nocturnal Trading" (Eaton, Shkilko, Werner, Jan-May 2024 data) - no return size; qualitative: price discovery concentrated in non-US stocks and macro ETFs, ~80 % of volume from Asia-Pacific (UNVERIFIED).
- Source: https://haslam.utk.edu/wp-content/uploads/2024/11/Eaton-Paper.pdf
- Differs from ledger: I-87 / H02 / gap fade did not condition on retail overnight order flow; no overnight venue data owned. Practically a data problem -> likely closed. Prior 3 %.

## 8. Hyperliquid / on-chain forced liquidation + ADL (post Oct 10 2025) as crowding signal
- Mechanism: public Hyperliquid order book and liquidations (L2 archive free); ADL closed about 2.1 bn USD in 12 minutes on 10 Oct 2025 (Chitra, arXiv 2512.01112); liquidation bands as proxy for where broader market liquidations sit (Glassnode, practitioner).
- Venue: HL perps / Binance perps; horizon: minutes to days.
- Data: FREE (HL archive / API, only recent history from 2023+; cannot satisfy the development 2020-23 split) - UNVERIFIED depth.
- Effect: no return-prediction paper found.
- Source: https://arxiv.org/html/2512.01112 ; quote (snippet): "last-resort loss-socialization step that runs when liquidations fail" UNVERIFIED verbatim.
- Differs from ledger: I-76 used Binance liquidation clusters (t 2.50, net -4.7 bp, killed). HL is on-chain visible per-wallet positions (known liquidation prices), so "who must trade" is knowable ex ante - a new information set, not a re-run. Events rare (7 cascades 2022-2025) -> power fail likely. Prior 4 %.

## 9. Russell semi-annual reconstitution (June + December from 2026): addition/deletion trading
- Mechanism: index funds and Russell 2000/1000 benchmark ETFs must trade additions/deletions on a known date; move from annual to semi-annual from Dec 2026 creates a NEW second event per year. CME suggests long additions / short deletions (vendor view).
- Venue: Russell 2000 stocks (not owned; ~46 large caps useless) and RTY/IWM; FTMO US2000 CFD only index level.
- Data: PAID (Russell membership lists) / small caps not owned; US2000 CFD owned, but index-level effect weak.
- Effect: none found; deletions averaged 11.3 % index weight historically (Brown Advisory, marketing).
- Source: https://www.cmegroup.com/articles/2026/the-2026-russell-reconstitution.html
- Differs from ledger: I71/FB215 were index-review closing auction (UK100 etc.); this is a new US event class. Event count 2-4 a year -> power-closed before any look, and untradeable on owned data. Prior 2 %.

## Ranking by probability (all low)
1) End-of-day cross-sectional reversal (12 %, data owned, testable in a day once Alpaca finishes; cost wall at 10 bp CFD spread is the main risk - screen it on ETF-like liquid names first).
2) LETF see-saw conditional last-30 / next-open (6 %).
3) Harvey-Mazzoleni-Melone threshold rebalancing (5 %, power).
Others <= 5 %.

## Honest summary
The newest literature mostly repeats mechanisms the ledger already killed (noise-band, gamma, last-30 momentum, rebalancing calendar) or needs data not owned (VX, Russell membership, overnight ATS). Only the end-of-day reversal paper (Baltussen/Da/Soebhag 2025) gives a new, ownable, cross-sectional short-horizon effect; it is closest to the I-96 family that failed on spread, so expect a cost-wall result. Items 5-8 are structural-break or short-sample ideas that cannot be developed under the pre-2021 / 2020-23 split.
