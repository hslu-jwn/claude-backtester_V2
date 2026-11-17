# Scout 1: US shares and ETFs with minute data

Caveat up front. Web search returned summaries, not full texts. Quotes marked [V] were fetched from the source page; others are from search snippets or secondary summaries and are UNVERIFIED verbatim. Ledger overlap: H02/H06 (index last-30 momentum, sign right gross, died after costs), I-96 and gap-reversal rows (overnight/intraday single-name reversal, killed), index_rotation, I-99 shock reversal, calendar rows, event rows closed on power. Most ideas below sit close to those, so my priors are low. Honest summary: the shares domain is cost-limited. The only unexplored structural angles are the ones where the signal is a state variable (leveraged-ETF rebalancing size, dealer gamma) rather than a calendar or price pattern, and where one trade replaces many.

## 1. Leveraged-ETF rebalancing size as a conditioned last-30-minute trade (single ETF, state-dependent)
- Mechanism: daily-reset 2x/3x/inverse ETFs must buy after up days and sell after down days, in the last 30-60 min. Required trade is about L(L-1) x AUM x day return. This is forced and sized in advance (AUM x return is known at 15:00).
- Venue / symbols: SPY, QQQ (shares via Alpaca research), trade on US500 / NAS100 CFD or MES / MNQ futures. Sector ETFs (XLE, XLF etc.) as breadth. Extra: single-name LETFs (NVDL, TSLL) from 2022+ create stock-level pressure (needs AUM data, PAID/scrape).
- Horizon: 15:30 to 16:00 ET hold, or fade at next open. Intraday only, no swap.
- Data: SPY/QQQ minute OWNED. LETF AUM: FREE-ish (issuer sites, ETF.com, Yahoo shares-outstanding history is patchy, UNVERIFIED). Minimum version uses only the day's return as proxy for flow sign and size (OWNED).
- Published effect: Tuzun (Fed FEDS 2013-48): for a 1 % S&P gain, rebalancing gives +6.9 bp price and +22.7 bp daily volatility in an average large-cap stock (secondary snippet, UNVERIFIED digits). Baltussen, Da, Lammers, Martens (JFE, 1974-2020, 60+ futures): last-30-min return is "highly significant" and reverts over following days [V abstract page, no bp given].
- Source: https://pure.eur.nl/en/publications/hedging-demand-and-market-intraday-momentum/ ; quote [V]: "Hedging short gamma exposure requires trading in the direction of price movements". Also https://www.federalreserve.gov/pubs/feds/2013/201348/
- Difference from ledger: H02/H06 used an unconditioned or first-half-hour signal on index CFDs and died after cost with gross sign right. This version scales by predicted forced flow (return x LETF AUM x leverage factor, plus dealer gamma from SqueezeMetrics GEX which is OWNED) and trades only the top few days a year, so cost per trade matters less. Overlap with the "short-gamma days rebound" kill (t -1.97) is real: that tested GEX regime on next-day, not last-30 inside the day.
- Capacity: flow is about USD 10-15 bn on big days vs hundreds of bn volume, so it is an edge for any desk with 0.2 bp costs. Why still alive: signal is crowded by HFT who front-run at 15:50; retail-cost trader gets the tail only. Honest.
- Prior surviving costs: 8 %. Power: needs ~10 large-move days a year, which kills the 300-trades goal; pass only if 25 bp+ on 40 days a year.

## 2. Overnight versus intraday decomposition on ETFs as a market-timing filter (clientele tug of war)
- Mechanism: institutions trade intraday, retail overnight; Lou, Polk, Skouras show momentum earns overnight, reversal intraday. Aggregate: SPY overnight return positive, intraday about flat for decades. Clientele: sellers at the close leave a premium for providing liquidity overnight.
- Venue: SPY/QQQ via NAS100/US500 CFD (swap is a cost: one night of financing per trade, ledger already notes swap eats multi-day holds); futures is cleaner (MES, no financing in price).
- Horizon: close to next open, 1 night.
- Data: OWNED (Alpaca minute).
- Published effect: Lou-Polk-Skouras JFE 2019, 14 strategies, profits earned entirely overnight or entirely intraday; momentum hedge about +0.89 % per month overnight vs -0.18 % intraday (CXO summary, 1993-2013, UNVERIFIED digits). Quote [V]: "strong overnight and intraday firm-level return continuation"
- Source: https://researchonline.lse.ac.uk/id/eprint/87481 ; https://www.cxoadvisory.com/calendar-effects/momentum-happens-at-night/
- Difference from ledger: ledger closed an overnight-premium row on power (MDE 4.4 bp a night vs 1.4-2 bp) and I-96 gap reversal. The only new variant is a conditioning filter (last-30 min flow sign x overnight premium) rather than the unconditional premium. Largely a duplicate of ledger; listed for completeness.
- Prior: 3 %.

## 3. Closing-auction imbalance (NOII) trade: fade or follow the published imbalance
- Mechanism: NYSE / Nasdaq publish net order imbalance at 15:50 onward; imbalances must be absorbed by the close. Large imbalances move closing prices and partially reverse next day.
- Venue: large caps and ETFs on shares or index CFD proxies. FTMO share CFDs trade up to 22:00 so close-to-next-open exposure is possible but spread at close is wide.
- Horizon: 15:50 to 16:00, or close to next open.
- Data: PAID/not owned. NOII feed is Nasdaq TotalView / NYSE Imbalance, not in Alpaca free tier (UNVERIFIED for Alpaca). Proxy owned: minute volume jump 15:50-16:00 vs average (weak substitute).
- Published effect: an off-exchange-order-flow paper reports overnight alpha 15 bp for a large-imbalance long-short; NYSE-Nasdaq buy-imbalance decile impact 32 bp larger than sell decile (Emory thesis, UNVERIFIED, thesis not peer reviewed). Bogousslavsky-Muravyev: auction-to-total volume ratio predicts returns (working paper).
- Source: https://papers.ssrn.com/abstract=3925725 (adjacent leveraged-ETF paper); search hits: Morand Imperial thesis on NOII, Emory dissertation, Bogousslavsky-Muravyev (URLs not verified).
- Difference from ledger: no NOII row; data not owned so it is "needs_data" at best.
- Prior: 4 % (data barrier plus 2 legs of cost on the CFD).

## 4. Dealer gamma and 0DTE intraday path conditioning on SPY/QQQ
- Mechanism: options market makers short gamma must hedge in the direction of the move; long gamma damps the path. 0DTE adds same-day gamma peaking into the afternoon.
- Venue: US500 / NAS100 CFDs, ETF shares.
- Horizon: intraday (13:00 to 16:00), possibly volatility-regime filter for other strategies rather than a signal itself.
- Data: SqueezeMetrics DIX/GEX daily OWNED; intraday gamma needs OPRA options data (PAID).
- Published effect: Cboe says 0DTE net dealer gamma is 0.04-0.17 % of daily S&P futures liquidity (exchange-sponsored, stake in answer); academic studies disagree on sign (Princeton 2026 thesis says gamma channel not supported). Quote (snippet, UNVERIFIED): dealer exposure small relative to futures liquidity.
- Source: https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options
- Difference from ledger: ledger row "short-gamma days rebound" (t -1.97, opposite sign) already used GEX daily. A new angle would need intraday gamma, which costs money.
- Prior: 3 %.

## 5. ETF price-versus-NAV dislocation (creation/redemption) on sector or country ETFs
- Mechanism: when an ETF trades at a premium or discount to NAV, authorized participants create or redeem; the flows that close the gap trade the underlying stocks. Fund-flow demand shocks reverse.
- Venue: shares only; FTMO CFD universe has no sector ETFs, so execution is not on FTMO (would need a stock broker or futures).
- Horizon: days to weeks.
- Data: needs iNAV or daily NAV (PAID or scrape; Alpaca gives price only). Sector ETFs OWNED.
- Published effect: Brown, Davies, Ringgenberg (Review of Finance 2021): low-flow minus high-flow ETF portfolio earns 1-4 % per month (secondary). FCA Occasional Paper 68 (Kirilenko et al., 128 ETFs 2018-22): AP inventory and demand explain deviations from NAV. Quote: not fetched (revfin page failed, HTTP 425), UNVERIFIED.
- Source: https://revfin.org/?p=2019 ; https://www.fca.org.uk/publications/occasional-papers-fca-research/occasional-paper-68-etf-mispricing
- Difference from ledger: no row; but fails Goal 1 on venue (not on FTMO) and needs NAV data. Fits Goal 2 if a stock account exists.
- Prior: 6 %. Large effect claims, probably smaller net and for illiquid ETFs not the 15 liquid ones owned.

## 6. Intraday momentum on SPY / QQQ via Noise-Area breakout (Zarattini, Aziz, Barbon)
- Mechanism: not forced; claims supply-demand imbalance persistence when price leaves the 14-day average intraday range band; plus leveraged-ETF and gamma flows (see #1).
- Venue: SPY/QQQ shares or US500/NAS100 CFDs.
- Horizon: intraday, 30-min checks, flat at close. Several trades a year-week.
- Data: OWNED (also on index CFDs from FTMO).
- Published effect: net of costs 19.6 % a year, Sharpe 1.33, SPY May 2007 to April 2024; the authors' own result and in-sample (secondary summary, UNVERIFIED).
- Source: https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy ; quote not fetched (UNVERIFIED).
- Difference from ledger: ledger killed ORB (t ~1.5, fading since 2024), no_wick and index last-30 momentum. This is an ORB-family relative with a volatility-scaled band and trailing stop; the leverage up to 4x in the paper is what drives the headline, so edge per unit risk is the thing to check. Close to a duplicate of ORB family (family closed after 2 falsifications), so it could be closed on that rule.
- Prior: 5 %.

## 7. Index reconstitution / migration pressure (Russell R1/R2 boundary) on small caps
- Mechanism: index funds must trade at the close on reconstitution day; stocks migrating between Russell 1000 and 2000 show pressure then reversal.
- Venue: shares only; Russell 2000 names not in the owned 46 large caps (US2000 CFD exists but is the index, not names).
- Horizon: 20 trading days; once a year.
- Data: PAID (Russell membership lists, minute data for small caps).
- Published effect: migrating stocks recover about 2 % over the 20 days after reconstitution (Dimensional, 2014-2023, small samples like 18 additions in 2019). Sample: UNVERIFIED digits from search snippet.
- Source: https://www.dimensional.com/us-en/insights/even-migrating-stocks-face-index-reconstitution-costs
- Difference from ledger: ledger "index reviews" closed on power (36 entries, ~3 a year). Same fate here: one date per year.
- Prior: 2 %. Fail on power before data.

## 8. Retail order-flow timing (Barardehi, Bernhardt, Da, Warachka): internalized retail flow predicts institutional price pressure and overnight reversals
- Mechanism: institutions execute through the day and push price; retail internalization absorbs; the pressure reverses overnight.
- Venue: shares; trade as an intraday-to-overnight reversal.
- Horizon: intraday to next open.
- Data: PAID (TAQ and retail-flow identification from SEC rule 605 or TAQ subpenny). Proxy: signed volume imbalance from minute bars (OWNED, noisy).
- Published effect: no bp found in snippet; UNVERIFIED. Related: retail imbalances predict cross-sectional returns daily-weekly (Boehmer, Jones, Zhang), aggregate retail imbalance does not predict market returns.
- Source: search hit https://warwick.ac.uk/fac/soc/economics/research/workingpapers/2022/twerp_1394_-_bernhardt.pdf (title not confirmed from this URL).
- Difference from ledger: overlaps I-96 gap reversal (killed t -2.64, gross fades to negative after 2019).
- Prior: 2 %.

## Not recommended (checked, thin)
- Sector ETF to stock lead-lag at minutes: Box, Davis, Evans, Lynch find ETF flow does not lead constituent returns at 1-10 minute horizons and ETF returns mostly follow underlying (https://alphaarchitect.com/2021/02/do-etfs-adversely-affect-market-quality-nope/). Evidence points against; skip.
- Buyback blackout windows: Alpha Architect summary found no significant return difference in blackout periods; skip.
- Option pinning on expiration Fridays (Ni, Pearson, Poteshman JFE 2005): real but modest, a few cents around strikes, not tradable after spread; weekly-expiry pinning differs. Skip unless Opex-day close-hour mean reversion is wanted (ledger calendar rows already died).

## Picks if forced to choose one for a first pre-registered look
1. Idea 1 in the narrow form: one SPY (or US500 CFD) trade, 15:30 to 16:00, only on days where |day return at 15:30| exceeds the top decile, direction = sign of day return, with the reversal at the next open as the second leg. Power check: ~25 days a year, 5 years of Alpaca minute data owned, MDE will likely exceed a halved published effect, so run the power arithmetic before any data look and close without a look if it fails (likely).
2. Idea 6 only if the ORB-family closure rule is overridden by Chef.
Everything else: no owned data or no venue.
