# Marcia Stigum & Anthony Crescenzi, *Stigum's Money Market*, 4th ed. (McGraw-Hill 2007)

Short: **SM**. Cite by printed page (`SM p.542`). Read 2026-11-18 by 3 Sonnet agents (Codex at its limit;
`knowledge/reading-brief.md`), **selected chapters only**: ch.8 Treasury and agencies, ch.10 dealers, ch.12 fed funds,
ch.13 repo, ch.14 Treasury securities, ch.16 Treasury futures (~1,100-page reference; banks, Eurodollars, CP, CDs,
munis, swaps and money funds skipped as off topic). PDF in the library folder Tier 1. Mechanics, not strategies.
Opus's reading for I-109 (month-end duration extension): the book has nothing on index extension, delivery or
cheapest-to-deliver numbers, but names three month-end confounds: (1) 2-, 5- and 7-year notes are auctioned late in
the month and settle on its last day (supply lands in the same window as index demand); (2) quarter-end balance-sheet
and repo stress (SM p.542); (3) the expiring quarterly futures contract stops trading in its last seven business
days, so a Mar / Jun / Sep / Dec month-end long is in the next contract and earns futures carry, not the cash yield
(SM p.768). Diagnostics on spent data: card T-26. The chosen venue (CME Micro 10-Year Yield futures) is monthly and
cash-settled, so delivery and CTD risk do not apply to it. Auction-cycle trading (dealers short into auctions,
Lou-Yan-Zhang 2013) is already judged in I-109's sources: the effect is gone once month-end days are removed (ohlcv.io
2010-2026); no new card. Refunding-week concession: ledger HV-T0112-1 (parked, needs data).

# Part 1: ch.8 Treasury and agencies, ch.12 federal funds, ch.13 repo


### Overview
- Reference text on money-market plumbing, not a strategy book. This part covers the Treasury as issuer and its debt-management history (ch.8, SM pp.301-342), the federal funds market and reserve settlement (ch.12, SM pp.491-530), and repo / reverse / specials / matched book / Fed open-market operations (ch.13, SM pp.531-579).
- Stance: descriptive and practitioner-quote driven. It stresses that Treasury issuance is deliberately regular and calendar-driven (predictability lowers cost), that fed funds desks are run conservatively around a fixed two-week settlement cycle, and that repo is a collateralised loan whose price moves with collateral scarcity and balance-sheet dates.
- Almost nothing on futures, index funds, duration extension, delivery or cheapest-to-deliver (futures are deferred to ch.15/16, not in this range). So direct evidence for I-109 is thin: the book supplies only the funding and calendar context (quarter-end repo spikes, supply concession near refundings, issue calendar, specials), not the index-extension effect itself.
- Useful for us as (a) a catalogue of rule-driven calendar flows with approximate sizes, (b) a warning that quarter-end balance-sheet windows, not plain month-ends, are where funding stress appears, and (c) a list of mechanical risks in short-term rate-linked trades.

### Chapter notes

### Ch 8 - The Treasury and the Federal Agencies (pp. 301-342)
- Marketable debt about $4.26tn of $8.27tn total (Feb 2006); about 48% is non-marketable (trust funds). Foreign holdings about $2.19tn, roughly half of outstanding, up from about 35% five years earlier (p.324). Average maturity of the debt fell from 71 months (2001) to 53 months (2005) (p.317).
- Instruments: bills (6 months or less), notes (2-10 years), bonds (over 10), TIPS. Notes and bonds pay semiannual coupons (pp.302-303).
- Issuance history: subscription and exchange offers (1960s), then price auctions (1970), then yield auctions (1974), then uniform-price auctions for everything by Nov 1998 (p.576). Auction format moved to yield bids because price-based coupons set days ahead went stale when rates were volatile (pp.313-314). Noncompetitive bids capped at $5m (p.309).
- Regularization (1975 on, pp.315-316): fixed cycle, 2-year note at end of each month, 4-year and 5-year mid-quarter, and a quarterly refunding in the middle of the second month of each quarter. Reasons: predictability lowers yields, avoids bunching on four dates, lengthens maturity. Dealers used to be unsure what the Treasury would bring, so they went flat into auctions.
- Predictability point (p.318-319, Treasury official quote): Treasury does not time issuance to rates; its calendar is known to everyone. Entitlement payments are made early in the month; receipts lump around a few tax dates; Treasury cash accounts at banks can swing by more than $50bn within a few days. Forecast error of the year's deficit after 4 months of data averages about $75bn.
- Supply effects (p.328): over the long falling-rate era, supply mattered only briefly, around quarterly refundings, when yields tended to rise a bit as a concession to investors; the concession varied and was often unnecessary. Supply matters most when bearish sentiment is high. Author's view: inflation and central-bank policy dominate supply. Laubach (2003) cited: +1pp projected deficit/GDP gives roughly +25 bp on long yields (p.324).
- Uses of Treasuries (pp.322-323): primary-dealer repo collateral; most interest-rate hedges; 10-year futures open interest over 2 million contracts, notional over $200bn (April 2006), $100,000 per contract; zero risk weight under Basel for banks; pension fund liability benchmark.
- Cash management bills (CMBs) replaced tax-anticipation bills in 1975; short maturity, used around tax-date cash troughs (pp.314-315).
- Treasury buyback programme 2000-2002 (45 operations, $0.75-3bn each) (p.316). Decision to stop the 30-year bond in 2001 surprised the Street and caused sharp bond gains (p.321): a rare example of a discrete supply surprise.
- Agencies (pp.330-341): $2.6tn outstanding, trade at a spread to Treasuries, mostly liquidity-driven; Fannie/Freddie/FHLB etc. Mostly background (S&L crisis, FICO, REFCorp, Ginnie Mae).

### Ch 12 - The Federal Funds Market (pp. 491-530)
- Reserve accounting: two-week maintenance period running Thursday to Wednesday; required reserves are based on deposits in a lagged two-week window (lagged accounting since July 1998). Banks only need the period average to hit the requirement, not each day. Carryover of excess or deficiency up to 4% of requirement (raised from 2% in 1992); cannot be red two periods in a row (pp.492-493).
- Settlement Wednesday is the volatile day; the rate used to move a lot at the close, but lagged accounting, higher carryover and heavy Fed monitoring (reports covering 65% of requirements by 2004) made it quieter (pp.523-524). Fed does open-market operations almost every day now (p.524).
- Intraday pattern: most trading 8:30-10 a.m. ET and 4:30-6:30 p.m. (about 40% of daily volume in the late window); funds rate tends to drift lower in the last two hours before Fedwire closes at 6:30 p.m. (pp.519-521, 527, Fig 12.7). CHIPS nets at 5 p.m., generating a new round of trading.
- On a bad Wednesday all banks can be red or black together if the Fed misestimates reserves; then the rate moves (p.527). If most banks were already black last period, extra surplus earns no credit, so they bid only at very low rates (p.528).
- Fed funds quoted add-on actual/360; broker fee about $0.50 per $1m per day (about 2 bp annualised); round lot $5m. Friday trades span three days; brokers like them; banks shave rates to correspondents on Fridays (pp.512, 514).
- Effective fed funds rate = volume-weighted average of brokered overnight trades (p.506). Target-tracking improved a lot; Fed tracks by adjusting reserves; academic dispute over any "liquidity effect" (Hamilton found it only on settlement day; Thornton doubts it exists; Carpenter-Demiralp find a daily effect) (pp.506-507).
- Fed policy-statement dates: first announced rate move Feb 4, 1994; FOMC has 8 meetings a year (p.565). Before that funds could swing widely intraday (200-400 bp in the 1979-82 monetary-aggregate regime) (p.503).
- Desk behaviour: conservative; no profit in playing the rate in a narrow band; evaluated against the effective rate. Daylight overdraft charge 36 bp annualised on average overdraft (p.526).
- Term fed funds market is small (p.529).

### Ch 13 - The Repo and Reverse Markets (pp. 531-579)
- Size: average repo + reverse outstanding $5.67tn Q1 2006 ($3.38tn repo, $2.29tn reverse); FICC volume $1.6tn per day; foreign investors' repo holdings $151bn (2001) to $701bn (2005); money funds $346bn (pp.531, 537).
- Mechanics: repo is a collateralised loan; add-on interest, actual/360; haircut usually 1-3%, up to 10% for weak borrowers (pp.534-535). Open repo rate set slightly above overnight; term repo for dated funding (p.542-544).
- Overnight repo normally trades a few bp below fed funds; spread averaged 9 bp (std 7 bp) from Jan 2005 to May 2006. The three widest spreads were quarter-ends: 58 bp on 30 Sep 2005, 50 bp on 31 Mar 2005 and 30 Jun 2005. Explanation: window dressing as financial institutions and corporates alter balance sheets for reporting (p.542). Repo-funds spread also widens when the Fed adds heavily and collateral is scarce, and narrows right after big Treasury auctions when dealers hold lots of collateral (p.542).
- Agency repo about 5 bp above Treasury repo (std 5 bp); mortgage collateral up to about 15 bp (p.542).
- Quarter-end collateral-substitution surge: end of June 2004 FICC got over 500 substitution requests above $130bn from interdealer brokers, up over 70% from earlier quarter-ends (pp.544-545). GCF repo (1998) lets dealers net settlement (2002: $101bn net vs $721bn gross daily) and is rolled daily (unwound morning, renewed afternoon) (pp.545-546).
- Repo yield curve: overnight often slightly above 1-2 week term (1 bp on average) (p.546).
- Forward repo / when-issued: dealers trade a new Treasury issue when-issued and the forward repo rate to its settlement date; the WI liquidity premium reflects the expected repo rate of that security (p.548).
- Specials: a security in heavy short demand trades at a repo rate below general collateral, possibly negative (pp.553-554, Fleming-Garbade 2004). Dealers go short into auctions betting the new issue yields more than old issues until distributed (p.552), but this fails when Treasury is paying down debt seasonally. Activity in specific-issue reverses is largest in bear markets; many issues on special can be a sign of a coming rally (p.553). Lending fee for securities loans typically up to 50 bp; collateral 102% (p.556).
- 1991 short squeeze in 2-year notes (Salomon false bids) pushed that issue's repo rate far below others; reforms: more bidders, uniform-price auctions, Treasury may reopen an issue in acute shortage, large-position reporting (pp.575-576).
- Matched book: dealers run repo and reverse books of several trillion dollars, "mismatching" maturities to bet on financing-rate direction (pp.557-563); dealer net Treasury position short $151bn total US government (May 2006) while long corporates/agencies (Table 13.1, p.564).
- Fed operations: repos temporary add reserves (on all but 7 business days in 2005; 204 of 256 short-term operations were overnight, nearly all the rest 14-day repos done every Thursday averaging $8.7bn; one 28-day repo at year-end for seasonal demand) (p.549). MSPs replaced by reverse repos in Dec 2002; Fed did no MSPs in 2005 (p.549, 567). Max repo term 65 business days (p.570).
- Reserve operating factors that move repo/fed-funds pressure: Treasury balances at the Fed, currency, float (higher Tuesdays and in Dec/Jan), settlement concentrations (pp.566-567).
- Leverage gauge: net repo financing is misleading; net financing (securities out minus in) is better (pp.576-578).

### Topic tags
- seasonality/time: Treasury issuance cycle (month-end 2-year, mid-quarter 4/5-year, refunding mid second month of quarter); bi-weekly Wednesday reserve settlement; Friday three-day funding; quarter-end repo spikes (50-58 bp over fed funds); Thursday 14-day Fed repos; year-end 28-day repo; float seasonal in Dec/Jan; refunding concession in yields; entitlement payments early in month; tax dates drain/lump Treasury cash.
- costs/execution: fed funds brokerage about 2 bp annualised; repo haircut 1-3%; securities lending fee up to 50 bp; GCF netting lowers settlement cost; daylight overdraft 36 bp annual. Funding is cheap relative to CFD swap but moves at quarter-end.
- volatility: funds rate very stable except on settlement days and at policy changes; repo-funds spread std only 7 bp with quarter-end tails.
- position-sizing/risk: dealers fund inventory via repo, so financing cost and haircut are the true leverage cost; term vs overnight financing mismatch is a rate bet.
- testing-and-robustness: Stigum quotes Treasury staff: predictability, not timing; supply effects small and brief outside bearish regimes, so effects must be tested around known dates and not assumed long-lived. Fed policy regime change (1979-82, 1994 transparency, 1998 lagged accounting, 2002 reverse repo) means any pre-1998 reserve-cycle pattern may not carry forward.
- portfolio/diversification: not covered beyond bond-market structure.
- trend, breakout, mean-reversion, momentum/oscillators, patterns, intraday/sessions (only fed funds intraday volume and rate drift), stops-and-exits, psychology/discipline: not covered, except one trader quote on aggressive vs conservative desks (not useful).

### Testable ideas
(All are weakly connected to the book; the book gives structure and rough size, not backtests.)

1. ★ **Quarter-end repo/funding stress as a regime flag for I-109** - Rule: on the last 1-3 trade dates of Mar/Jun/Sep/Dec, treat funding-stress as a conditioning variable on the month-end duration trade (compare the 12 quarter-end months with the 36 non-quarter-end months in the sample). Source: ch.13 p.542 (quarter-end repo-minus-funds spreads 50-58 bp). Claimed evidence: 3 widest repo spreads of 2005-06 were quarter-ends. Fit: good; we already hold 10-year futures history and FRED yields; only a split of existing I-109 results is needed (no new data, FRED has SOFR/repo proxies only post-2018). Difference: not a price pattern; a calendar partition of an existing mechanism test, so no extra trial beyond one pre-registered split.
2. ★ **Refunding-week supply concession** - Rule: short or avoid long 10-year Treasury futures from the Friday before the mid-quarter refunding auction week (mid Feb/May/Aug/Nov) to the auction settlement date (the 15th); compare returns with the I-109 month-end window, which is a separate week. Source: ch.8 p.328 (yields rise a bit around refundings, concession varies), ch.8 pp.315-316 (refunding mid second month of quarter, issue dates fixed). Claimed evidence: qualitative, "often" not "always". Fit: good (Yahoo continuous 10-year futures, FRED yields); mid-month futures roll is a separate date, so the delivery/roll calendar must be excluded. Different from failed families: it is a rule-driven supply flow by a mandatory seller (Treasury), not a price pattern; related but distinct from the month-end index purchase.
3. ★ **Auction-day / when-issued run-up for notes** - Rule: dealers go short into auctions betting new issues yield more; test whether 10-year futures drop into auction day (day before, auction day close) and recover after, using the known Treasury auction schedule (2/5/7-year at month end; 3/10/30-year mid-month). Source: ch.13 p.552, ch.8 pp.315-316. Claimed evidence: qualitative statement of dealer behaviour; fails in paydown seasons. Fit: moderate; needs Treasury auction calendar (public) and futures data; many auctions per year (more than 100), giving enough N. Different: mechanism is dealer positioning, not price pattern. Caution: note the 2-year/5-year/7-year auctions fall in the last days of the month, which overlap the I-109 window and could confound or even reduce the extension premium, so decompose them in one test.
4. **Settlement-Wednesday / 14-day Thursday Fed repo cycle in front-end rates** - Rule: examine short-end futures-derived rates (or FRED daily SOFR/EFFR, post-2018 only) for any biweekly maintenance-period pattern. Source: ch.12 pp.492-493, 523-528. Claim: the book itself says Wednesday volatility has largely vanished since 1998-2004. Fit: poor (post-reform effect expected near zero; no short-rate futures data in our set); listed mainly as a falsification candidate.
5. **Friday/weekend three-day funding vs weekday** - Rule: compare funding rate (EFFR or FRED repo proxy) Friday vs other days; the book says Friday buys span three days and are sometimes shaved. Source: ch.12 p.512. Fit: poor; funding rate is add-on actual/360 so a Friday trade already pays three days, no excess return. Probably only a data-quality point.
6. **Special-collateral squeeze as a flag for futures delivery risk** - Rule: when the Treasury note/bond cheapest-to-deliver issue goes special, futures could cheapen/richen into delivery. Source: ch.13 pp.552-556, 575 (2-year squeeze 1991). Fit: poor; we have no CTD or repo-specials data. Note for I-109 risk list only.
7. **Year-end 28-day Fed repo / Dec-Jan float seasonality** - Rule: test whether December-January short rate or bill yield behaves differently. Source: ch.13 pp.549, 566-567. Fit: poor, FRED bill yields only daily; likely tiny and swamped by tax and year-end window dressing.

### Warnings / pitfalls
- Month-end is not stressed in the data here; quarter-end is. A month-end duration trade on a quarter-end could carry a repo spike and a window-dressing balance sheet shrink; split results by quarter-end vs other months before trusting an average (p.542).
- Supply effects are described as brief and sample-dependent (mostly in a 25-year falling-rate regime, bigger when sentiment is bearish); do not expect a stable premium (p.328).
- Predictable Treasury calendar means any known-date edge is public knowledge and can be arbitraged by dealers who hold positions into auctions; the book notes dealers try to finish positions before auctions (pp.318, 552).
- Roll/delivery: ch.13 explains that issues in high short demand trade special, so deliverable-basket prices can distort near delivery; not quantified here (pp.553-556).
- Short squeezes (1991 2-year note) show that concentrated positions can distort a specific issue's price; futures on a continuous Yahoo series will not show this (pp.575-576).
- Regime changes (1979-82 monetary targeting, 1994 announcements, 1998 lagged reserves, 2002 reverse repo) mean pre-2000 reserve-cycle effects are not a good basis for modern tests (pp.503, 523, 567).
- Fed intervention is steady and predictable; it removes most calendar edges in the policy rate (p.524, 549).
- The book is from 2006-07: it predates the 2008 crisis, IOER, ON RRP and SOFR; reserve-maintenance and Wednesday-settlement structure no longer apply (reserve requirements were later set to zero). Treat any money-market calendar effect found here as a hypothesis, not a fact.

# Part 2: ch.14 Treasury and agency securities


Cite as SM p.<page>. Pages covered: about pp. 583-692.

### Overview
- This part is the second half of Ch. 14, "Treasury and Federal Agency Securities". It covers market structure
  (size, history, bills / notes / bonds), settlement, book entry, primary dealers, auction procedure, interdealer
  brokers, electronic trading, the bill market, note and bond trading, the yield curve as a recession predictor, TIPS,
  STRIPS and federal agency debt (Fannie, Freddie, FHLB, other GSEs).
- It is a practitioner's description of mechanics, not a strategy book. It has NO section on month-end index
  extension, index-fund duration demand, futures delivery / cheapest-to-deliver, or month-end repo. Searches of the
  range for month-end, quarter-end and index extension found only the few passing mentions listed below. The futures
  basis and delivery mechanics are deferred to Chapters 15 and 16 (outside this range). So there is NO direct evidence
  for or against I-109 here.
- What it does give: (a) the exact CALENDAR of Treasury supply and settlement (auction days, issue dates on the 15th
  and end of month), which tells us when new-issue and dealer-distribution pressure is present; (b) the idea that
  dealers hedge or pre-position around auctions and that supply matters more in bear markets than in bull markets;
  (c) liquidity and cost numbers for 10-year notes (bid-ask, commissions); (d) the finding that announcements and
  auctions move yields within about 15 minutes; (e) evidence that the 10y-3m spread predicts recession.
- Stance of the authors: Treasuries are the deepest, most transparent market; supply "matters" less than most think
  but more in bear phases; real yields and Fed policy dominate; technicals are followed but fundamentals dominate.

### Chapter notes

### Ch 14 (second half) - Treasury and Federal Agency Securities
#### Market size and activity (SM pp. 583-587)
- Publicly traded Treasuries: about $4.2 trillion at end 2005. Primary-dealer daily volume about $554.5 bn average
  2002-2005 (record), $575 bn in 2005 (pp. 583-584, 595). Volume rises with Fed hikes, bigger issuance, foreign buying.
- Foreign holders about half of all Treasuries; the Fed holds about $736 bn for itself and $1.127 trillion for foreign
  official accounts (p. 584). These large holders buy and hold, which keeps yields low and floats small (p. 593).
- Bid-ask for Treasuries is about half of corporates (p. 585). 10-year notes have the smallest average quote size and
  smallest average trade ($6.2 million) of the main maturities in a 1996-2000 NY Fed study (pp. 587-588, 622).
- Dealers net short Treasuries in every week during 4.5 years to March 2006, average $72 bn short (two-year average
  $109 bn), as hedges against long corporate / agency positions, not as a bearish view (p. 643). Table 14.6 shows
  the net positions by maturity bucket. The authors warn that nobody can infer dealer opinion from this.
- Note and bond futures: early March 2006 about 1 million 10-year note contracts a day, open interest 2.1 million;
  5-year note 700,000 / 1.2 million; bond 400,000 / 600,000 (p. 629). Futures liquidity keeps cash spreads tight. Of
  an open interest, "the billion short is the Street, the billion long is customers" i.e. dealers are the natural
  short and speculators the natural long in the CBOT bond contract (p. 646).

#### Issuance calendar (SM pp. 587-589, Table 14.1)
- Bills: 3- and 6-month bills auctioned every Monday, settle Thursday; 4-week bills auctioned Tuesday, settle
  Thursday. About $50 bn of bills sold per week in late 2006 (p. 587).
- Notes: 2-year and 5-year auctioned every month, issue / settle at END OF MONTH; 3-year and 10-year in Feb, May,
  Aug, Nov, issue / settle on the 15th; the 10-year is reopened in the following months (Mar, Jun, Sep, Dec) (p. 588).
  Long bond (30y) resumed in Feb 2006 after a gap since Aug 2001 (p. 589, 646). Bonds and 10-year notes pay coupons on
  the 15th of Feb, May, Aug, Nov (STRIPS section, p. 668).
- Implication: the end-of-month 2-year and 5-year settlement creates a regular end-of-month supply event of fresh
  issue in the 2y / 5y part of the curve (not the 10y). The 10-year new supply sits mid-month (15th).
- Average maturity of Treasury debt: 47 months (1982), 71 months (2000), 53 months (end 2005) (p. 589). Pension
  reform demand for long duration cited as a reason for reintroducing the long bond.
- Settlement: regular (next-day) settlement for nearly all notes and bonds; cash (same-day) more common in bills (p. 591).
- Fails: average $12 bn a day over 1990-2004; peak $232 bn a day in summer 2003. "Fails tend to be at their highest
  in the weeks before and during the Treasury's quarterly refundings and in the weeks that include the end of a
  calendar quarter" (Fleming and Garbade 2005, quoted pp. 610-611). This is the one explicit quarter-end / refunding
  calendar effect in the range, and it concerns settlement stress, not price.

#### Auctions and when-issued trading (SM pp. 599-604, 617-625, 637-640)
- All marketable debt is sold at auction. Announcements 11 a.m. ET for bills, 2y / 5y notes, 10y reopenings and TIPS;
  9 a.m. ET for 3y, 10y, 30y (p. 599). Noncompetitive bids close before noon, competitive bids at 1 p.m.; results
  within 2 minutes (pp. 600, 602).
- Single-price (Dutch) format for all auctions since 1998 (single price since 1992 for some) (p. 600). A bidder's
  award limit is 35% of the offering less its reportable net long position (including when-issued, forward and FUTURES
  positions) (p. 601).
- Awards 2003: primary dealers 78% of awards, indirect bidders (foreign central banks, customers via dealers) 19%,
  direct only 2.2% of bids (pp. 602-603). About 75% of auction deliveries go through the FICC (p. 603).
- When-issued (WI) trading starts at announcement, on a yield basis, and settles on the issue date. WI trading is a
  price-discovery tool and spreads dealer positioning over days: "people who do not like the market will build up a
  short going into the auction, so half the issue is really taken care of before the 1 p.m. deadline" (pp. 599-600,
  624). Dealers sell WI to customers during the WI period and must buy the offset in the auction.
- Pricing of a WI note before it is announced: three variables, curve (yield difference between neighbouring
  maturities), carry (interest forgone vs a bond), and liquidity (value of being the on-the-run). The "roll" is
  the yield difference between the WI and the issue it replaces (pp. 638-639).
- Supply effect: "when the Treasury is auctioning new securities, it is likely that the new issue will sell at a
  fractionally higher yield than trend until the supply is distributed, and dealers consequently have a profit
  incentive to bid aggressively" (p. 620). So a small concession exists around auction, partly capturable by dealers.
- "Supply Matters - Not" (pp. 603-604): deficits and auction size have NOT explained yield direction over 25 years
  (yields fell despite deficits; Japan the lowest rates with the largest deficit). But: "supply tends to matter more
  in bear markets than in bull markets. When interest rates are trending higher, new supply tends to exacerbate the
  move ... When rates are falling, new supply is of little burden" (p. 604).
- Bid-to-cover, tail and stop-out yield are the numbers dealers talk about before an auction (p. 618). Table 14.4:
  sample 13-week bill, bid-to-cover 2.51. Fed rolls its maturing bills in the auction but is free to roll less,
  which drains reserves without open market operations (pp. 617-618, 621-622).
- Bill weekly cycle (trader quote, p. 624-625): Monday auction; Tuesday sloppy, short sellers active; Wednesday
  shorts think about covering; Thursday busiest, demand arrives (settlement, maturing bills reinvested, shorts
  cover); Friday tails off. Qualitative, no numbers, bill-specific.
- A WI sale is the cheapest way to short in bills: no borrow cost, roll the short week to week (p. 624).
- Dealers hedge new supply along the curve: sell 2s, 3s, 4s to bid for a 5-year auction; "Last week the Treasury sold
  5 billion 5-years, and all of a sudden 2-years, 3-years, and 4-years were all over the place" (p. 636). Generic
  "supply-based" curve plays: buy the short end, short the part of the curve where supply comes next week; the trader
  himself says "They may or may not work" (p. 637).
- Current / on-the-run issue: a note is current from its auction until replaced (2y for a month, 3y for a quarter) and
  trades far more actively, with a liquidity premium. After Russia's 1998 default the on-the-run / off-the-run 5y and
  10y spread widened to 15 bp in one week (pp. 639). Par is a "magic number" for money managers (pp. 639-640).
- Seasoning: how fast an issue gets distributed depends on the auction (retail takes half or more then the float is
  clean; if dealers hold it, it trades cheap for a long time) (pp. 640-641).
- Maturity-date effects: "notes maturing at the end of December are likely to trade differently ... owing to year-end
  positioning. Notes that mature at the end of a calendar quarter are also apt to trade differently" (p. 642). No
  magnitude given. This is the only direct year-end / quarter-end price statement in the range.

#### Interdealer brokers, costs, execution (SM pp. 604-612, 622-623, 626-627)
- Interdealer market: ICAP (BrokerTec) 60%, Cantor (eSpeed) 28% share in 2005; ECNs handled $21.19 trillion of
  on-the-run trades in Q3 2005 (pp. 605-606).
- Spreads: 2y notes averaged 0.83 (GovPX voice) vs 0.21 (eSpeed) in the Mizrach and Neely study, i.e. -75%; 10y notes
  1.72 bp lower, an 82% cut (p. 607). 10-year note typical bid-ask just under 1/32 point; long bond about 2/32; 2y
  about 1/4 of a 32nd (pp. 645-646).
- Broker commission: $39 per $1 million (voice era) down to $2.00-2.50 per $1 million on eSpeed / BrokerTec for the
  best customers by 2005 (p. 608). Commission is paid only by the initiator of the trade.
- Practical cost for a futures trader on 10-year note futures is far below these cash costs (futures cost is not
  quoted here), so the book supports the view that Treasury exposure is nearly the cheapest in the world to trade.
- Brokers' screens go "subject" after major data; traders play games (locked markets, one-man markets) to hide size
  (pp. 607, 623, 644-645). Genuine size is only known by trying to trade.
- Fails come mostly from out trades (pp. 610-611).
- Primary dealers must participate in auctions, and the Fed requires them to quote fair markets; dealer count fell from
  46 (1988) to 22 (2006) (pp. 596-599).

#### Bills (pp. 617-629)
- Bills track the fed funds rate closely (3m bill 0.8% June 2003 with funds 1%; 5.12% Oct 2006 with funds 5.25%)
  (p. 625). Eurodollar / LIBOR has replaced the bill as the relative-value benchmark (pp. 627-628).
- Bills are the flight-to-quality asset: after Russia 1998, 3m bill yield fell from 4.80% to 3.60% in weeks, about
  twice the move in the 10y (pp. 628-629).
- Bill "shortage": much of each auction goes to the Fed, indirect and noncompetitive bidders, who hold; only about
  $12.5 bn each of 3m and 6m bills reached dealers in the sample auction (pp. 620-621, Table 14.5). Money funds
  swap between bills as soon as one is rich vs its neighbour (p. 628).

#### Notes and bonds (pp. 629-648)
- Note market is the largest segment ($2.39 trillion vs bills $0.997 trillion and bonds $0.526 trillion, Feb 2006).
- Data and announcements (pp. 630-633): Goldberg and Leonard (2003): a 1 standard-deviation surprise in German
  employment / GDP moved the German 2y about 3 bp; US data matter more for German yields than the reverse. Fleming
  and Remolona (1997): of the largest 5-minute price changes and activity episodes (Aug 1993 - Aug 1994) all came on
  announcement days and all but one within 15 minutes; ranked by importance: employment, FOMC, 30y auction results,
  PPI, 10y auction results, CPI, NAPM / ISM, GDP, retail sales. Auction results are a recognised price shock.
- Real yield = nominal minus inflation; drivers: inflation expectations, opportunity cost vs equities, growth, Fed,
  budget, liquidity (pp. 633-636).
- Dealers have become hedgers / arbitrageurs rather than outright position-takers (pp. 636-637). Futures are often
  used as the quick, cheap hedge; which is cheaper depends on cash-futures spread, costs and the reverse (repo) rate
  (p. 637).
- Bond traders hedge a purchase of cash bonds by selling the CBOT contract (example: long 100 cash bonds at 97 1/2,
  short 1,500 bond contracts at 111 1/2); then they carry BASIS risk (cash vs futures) and must "sell the basis" to
  basis traders (pp. 647-648). Detail of basis trades is in Ch. 16 (not in range).
- Risk equivalence by duration: $100 mn of 1-year bills about $50 mn 2-year notes about $10 mn long bonds (p. 641, 647).

#### Yield curve (pp. 648-660)
- 10y-3m spread and recession: Estrella and Mishkin (1996): probit table: spread 1.21 pp -> 5% recession probability
  four quarters ahead; 0.02 -> 25%; -0.82 -> 50%; -1.46 -> 70%; -2.40 -> 90% (Table 14.7, p. 656). Curve beat the
  Conference Board LEI and 7 professional forecasters (1965-1995) (p. 651). Yield curve leads by about 12 months vs
  stock market 6-9 months (p. 651). Inversion in Jan 2000 preceded the 2001 recession; earlier inversions 1980, 1982,
  1989 preceded recessions (pp. 653-654).
- Authors' point: Treasury yields below the funds rate mean negative carry for financed longs, and this occurs only
  when a cut is imminent (10-year only 3 times 1989-2005, 2-year 5 times); so inversions to the MONEY MARKET curve
  matter more than 10s-2s inversion (p. 655).
- Curve trading (pp. 658-660): curve trends are long-lasting because policy and the cycle are; duration-weighted
  hedges leave curve risk. Example: 2s vs long bond flattener, short $58 mn 2s / long $10 mn bonds, spread 53 -> 10 =
  +43 bp. Period of the 2000s: the curve flattened and rose.
- Bernanke (March 2006) "conundrum": long yields low due to lower term premium: stable inflation expectations,
  foreign official buying, pension asset-liability matching, scarce global supply (pp. 652-653).

#### TIPS, zeros, STRIPS (pp. 660-671)
- TIPS: break-even = nominal yield minus real yield; caveats are illiquidity, indexation lag (about 3 months), tax on
  phantom inflation, and different risk aversion (pp. 661-664). $395 bn outstanding Sept 2006.
- STRIPS: $183 bn outstanding Feb 2006, 31% of bonds are stripped, only 1.4% of notes; strip / reconstitution arb is
  nearly always inside costs (Sack 2000: only about 15% of 57,084 observations beat a 2/32 bid-offer) (pp. 667-669).
  Strip cost $25 and 30 minutes (p. 670). Zeros are the long-duration buy-and-hold asset of pensions and insurers.
- Zeros trader: "We dictate how rich or cheap" the long bond is; stripping lowered liquidity of the long bond, so the
  10-year note became the main trading vehicle (p. 669).

#### Federal agencies (pp. 672-690)
- GSEs had $2.575 trillion debt at end 2005 (+20% in 4 years). Fannie, Freddie and FHLB are about 95%. Fannie 10y vs
  Treasury 10y spread averaged 40 bp over 3 years to April 2006, as wide as 140 bp in 2000 (p. 675).
- Issuance calendars: FHLB discount notes sold Tuesday and Thursday; TAP reopenings through 23 dealers; Fannie
  benchmark notes 2, 3, 5, 10 years on a published calendar; Freddie reference notes similar (pp. 674-678).
- Agency spreads to Treasuries bear on the "implicit guarantee" and fall under the agency / MBS hedging flows
  (mortgage desks short 10y or shorter notes as a hedge, p. 642). No calendar-driven price effect given.
- Selling group distribution of new agency issues, fee up to $3 per $1,000 (pp. 689-690).

### Topic tags
- trend: yield curve trends are long-lasting because policy and the cycle are (p. 658); inversion as a 4-quarter
  recession signal (p. 656). Bills follow funds rate, not technicals (p. 625).
- breakout: none.
- mean-reversion: strip / reconstitute and on-the-run vs off-the-run curve blips pay 1/32 to 1/16 and are inside costs
  for outsiders (pp. 642, 668-669); brokers' "real market" vs screen (p. 623).
- momentum/oscillators: bill traders use trend lines, Fibonacci, RSI "because other people do" (p. 625); the authors say
  fundamentals dominate.
- patterns: none.
- intraday/sessions: results and announcements move yields within 15 minutes (p. 633); auction results at about 1 p.m.
  ET and announcements at 9 / 11 a.m. ET (pp. 599-602); Treasuries trade around the clock.
- seasonality/time: weekly bill cycle Mon-Fri (pp. 624-625); note issue dates 15th and end of month (p. 588); fails
  peak around refunding and quarter-end weeks (pp. 610-611); notes maturing at year-end / quarter-end trade differently
  (p. 642). Nothing on month-end index extension.
- volatility: bills are the low-risk training desk; the 10-year note has the smallest quote size (p. 622); on-the-run
  / off-the-run spread blows out in stress (15 bp, p. 639).
- stops-and-exits: not covered.
- position-sizing/risk: duration-equivalent positions ($100 mn bills = $50 mn 2s = $10 mn bonds) (p. 641); basis risk
  when hedging cash with futures (p. 648); curve risk of duration-weighted hedges (p. 658).
- testing-and-robustness/overfitting: authors repeatedly say "they may or may not work" about supply-based curve
  plays (p. 637); the "supply matters" claim is weak historically (pp. 603-604); strip arb mostly vanishes after costs
  (p. 668).
- costs/execution: commission $2-2.50 per $1 mn for the best customers in 2005 (p. 608); bid-ask 0.2 bp (2y) to under
  1/32 (10y) to 2/32 (30y); locked markets and one-sided fees (p. 609); WI shorting avoids borrow cost (p. 624).
- psychology/discipline: dealers bluff and hide size; protocol of openness with retail (pp. 626-627, 644).
- portfolio/diversification: dealers net short Treasuries as hedge vs long corporates; pension reform adds long-duration
  demand (pp. 643, 652).

### Testable ideas
(Stigum offers little that is directly backtestable. Items are mechanism-based leads that fit our data.)

1. ★ **Auction-day concession / WI-to-auction drift in Treasury futures** - Using Yahoo continuous 10-year futures
   (and FRED yields), mark the dates of 10-year, 3-year and 30-year auctions (known from the Treasury calendar:
   10y in Feb, May, Aug, Nov around the 8th-12th with settlement on the 15th; reopenings in other months). Test
   whether the 10-year yield rises (price falls) in the days before the auction and recovers after the results, the
   "concession then rally" pattern implied by "the new issue will sell at a fractionally higher yield than trend until
   the supply is distributed" and the dealer pre-auction WI short build-up (pp. 599-600, 620, 624). Entry: long at
   the auction-day close (or the open after the 1 p.m. result), exit 3-5 trading days later; control: random same-weekday
   days. Evidence claimed: qualitative only (traders' statements), no numbers. Fit: good for Yahoo continuous futures
   (daily), but small expected effect (a few ticks), so cost wall risk is high: a 10y future costs about 1 tick round
   trip; a 2-3 tick effect needs t >= 3 across about 100 auctions, power check needed. Differs from our failed families:
   this is a counterparty-must-trade (dealer distribution) flow, not a price pattern, and overlaps conceptually with the
   month-end idea only in being a calendar supply flow. Needs auction dates (public Treasury calendar; we may not have
   them in data, so downloading is a Telegram "Optional" request).

2. ★ **End-of-month 2y / 5y settlement supply, tested as a CONFOUND for I-109** - 2-year and 5-year notes settle at
   month-end (p. 588) and dealers sell the 2s-4s to bid for the 5-year (p. 636). If the month-end Treasury edge is
   partly new supply (negative for price) offsetting index extension (positive), then the edge in 10-year futures
   should differ in the months with a quarterly refunding (settlement on the 15th) vs months without, and between the
   last 3 trade days with and without a 2y / 5y settlement date in them. Rule: split the existing I-109 sample into
   (a) months where the last business day is the 2y/5y issue date, (b) others; also split by the Feb/May/Aug/Nov
   refunding months. No new data needed (the calendar rule is mechanical: last business day of month). Evidence: none
   quoted. Fit: good, uses our existing data and the already-passed test; a diagnostic, not a new strategy. Differs: it is
   a robustness check on the passed stream.

3. **Weekly bill-cycle seasonality in T-bill proxies** - Trader lore: Tuesday sloppy, Thursday strong (settlement
   demand, shorts cover), Friday fades (p. 624-625). Test with FRED 3-month bill yield changes by weekday (and Treasury
   futures if a front-month short-end contract is available). Evidence: none, anecdote. Fit: poor. We do not hold a
   tradable bill instrument and the size of daily bill moves is a fraction of a basis point; cost wall is certain.
   Listed only for completeness; do not run.

4. **Quarter-end / year-end maturity effect and fails** - SM says notes maturing at calendar quarter-end or year-end
   trade differently (p. 642) and fails peak in quarter-end and refunding weeks (pp. 610-611). Test: the
   on-the-run versus off-the-run relationship is not in our data (no per-issue data), so only fails (published NY Fed
   data, not in our data set) could be tested. Fit: poor on our data. Differs: balance-sheet window dressing, same family
   as month-end flow, but not tradable on futures.

5. ★ **10y-3m (or 10y-2y) curve inversion as a regime filter** - Estrella and Mishkin probit (Table 14.7, p. 656): a
   10y-3m spread below about -0.8 pp implies about 50% recession probability four quarters ahead; above +1.2 pp only
   5%. Use FRED Treasury yields (we have them) to build a monthly regime flag: inverted (spread < 0) versus not, and test
   whether month-end duration long (I-109) or other long-bond rules do better / worse in the two regimes, and whether
   equity indices on CFDs behave differently in the 12 months after inversion. Rule: signal = (10y yield - 3m yield)
   at month-end; regimes: < 0, 0 to 1, > 1; statistic: average next-month return of long 10y futures and of US500 CFD.
   Evidence: academic fit for recession prediction, not for monthly returns. Fit: good on data (FRED), but a low
   number of regime changes (inversions only about 4-5 times in the sample) means low power; keep as a conditioning
   variable for portfolio, not a stand-alone strategy. Differs: macro regime filter, not a price pattern.

6. **Dealer net-short positions as a contrarian or squeeze indicator** - Primary dealers are structurally net short
   Treasuries (avg $72 bn, p. 643). A shift in their net position could precede "technical rallies" when shorts must
   be covered (p. 644). Data: NY Fed primary-dealer statistics (weekly) are public but not in our data. Fit: poor to
   unknown; the authors themselves say the position cannot be read as bullish or bearish. Likely falsified by lack of
   interpretability; low priority.

7. **Roll and WI "price the roll" concept for Treasury futures** - Not a trade; it gives the logic of what the roll
   (on-the-run replacement) costs in yield: curve + carry + liquidity (pp. 638-639). Use as a check that the continuous
   Yahoo 10-year series is back-adjusted without creating month-end artifacts around the quarterly contract roll
   (Treasury futures roll in the month BEFORE the delivery month, i.e. roughly the end of Feb / May / Aug / Nov, which
   is the same time as I-109's trading window). See Warnings.

### Warnings / pitfalls
- Direct for I-109: the book gives no evidence on index extension and the month-end duration bid. The only month-end
  Treasury supply facts are (a) 2y and 5y note auctions settle at month-end and (b) quarter-end brings peak fails.
  A month-end supply effect pushing yields up could mask or reduce the index-extension effect; test it separately
  (idea 2).
- Futures roll and delivery: Treasury futures (CBOT) roll to the next contract before delivery month; the continuous
  Yahoo series will contain a roll step that can fall in the same weeks as the month-end window every February, May,
  August, November (and similar quarterly months). Roll-adjusted vs unadjusted returns can differ by several
  ticks; check that the back-adjustment or ratio method does not create a spurious month-end return. The cheapest-to-
  deliver (CTD) switch is not discussed in this range (see Ch. 15/16, not read).
- Basis risk: hedging cash with futures leaves cash-futures basis risk (p. 648); a long-only futures strategy has none
  of that, but the basis can drift to the CTD, so a "10y future" is not exactly the 10y note.
- Supply is a weak predictor of yield direction over multi-year samples (pp. 603-604); effect, if any, appears in bear
  markets. Do not expect an auction effect to be stable across regimes.
- The authors say supply-based curve plays "may or may not work" (p. 637); dealer positions are not readable as views
  (p. 642-643). Anecdotes from traders (weekly bill cycle, games on screens) carry no numbers and should not be treated
  as evidence.
- Costs: brokerage in 2005 was $2-2.50 per $1 mn; retail / prop trader spreads are larger than interdealer quotes.
  Trader tick profits (1/32 to 1/16 on curve arbs) are inside costs for outsiders.
- Fleming and Remolona finding: big price moves cluster in 15 minutes after announcements; daily-bar or close-to-close
  tests will blend announcement jumps into any calendar effect. Month-end windows can include employment (first Friday)
  or FOMC days; control for scheduled news when testing a month-end drift.
- Stale era: data in the book is 2006; auction format, dealer count, SLR rules and post-2008 balance-sheet limits have
  changed. Quarter-end repo / window-dressing effects have become larger since 2015, but nothing in this range says so.

# Part 3: ch.16 Treasury futures and ch.10 dealers


### Overview
- Reference text on market mechanics, written by practitioners' interviews. Not a strategy book; no backtests, no statistics, almost no numbers on calendar flows.
- Ch.16 explains the CBOT Treasury futures contracts (2/5/10-year notes, bond): delivery period, deliverable grades, conversion factor (6% yield world), invoice price, basis (carry + value basis), convergence, delivery options, cheapest-to-deliver (CTD), hedging with futures, basis trades (cash-and-carry via EFP), calendar spreads, NOB (notes over bonds) and TUT (tens under twos), and sentiment indicators (open interest, volume, call/put ratio, COT, basis).
- Ch.10 describes how dealers make money (agent fees, trading, positioning, carry, arbitrage), how they finance (repo, dealer loans, fails), how they size positions (expected value, confidence, maturity extension), shorting via reverse repo, tails, relative value, technical analysis, position limits, clearing banks.
- Stance: dealers are leveraged carry/basis intermediaries whose behaviour (hedging with futures, financing with repo, avoiding delivery) shapes futures-cash spreads. The author is sceptical of charts but accepts they matter because many traders use them.
- Calendar-driven flows in these chapters are thin: the explicit ones are the futures delivery month/expiry rules, the quarterly refunding (Feb/May/Aug/Nov) and quarter-end effects on fails and repo financing. Month-end index extension (our I-109) is NOT mentioned anywhere in these ranges.

### Chapter notes

### Ch 16 - Treasury Futures (pp. 745-791)
- Scale (2006): 10-year note futures traded over 2 million contracts on an active day, open interest 2.0-2.4 million; face value $100,000 per contract ($200,000 for 2-year); about $200bn notional per day vs cash Treasury volume about $550-600bn per day. Since 2001 the 10-year is the benchmark and most active contract (p.745, p.787). Open interest 10-year 1.7m vs T-bond 606k in Jan 2006 (p.779).
- Quotes: bond 1/32 ticks; 10- and 5-year notes in 1/64; 2-year in 1/128. One 32nd = $31.25 per contract (p.746, p.778).
- Contract month = expiry month (Mar/Jun/Sep/Dec). Delivery period: any business day of the delivery month; last business day is the final delivery day. Short gives notice by 8 p.m. Chicago; next day the exchange assigns the long with the oldest position; delivery the day after against fed funds (p.747).
- Important for roll timing: the contract does not trade during the last seven business days of the delivery month, and volume thins in the delivery month because longs fear being assigned (p.747, footnote p.759). So the front quarterly contract is effectively dead for the final week or more of Mar/Jun/Sep/Dec; anyone holding a "last 3 trading days of the month" long in a quarter-end month must be in the next contract (p.747).
- Delivery is used by only ~1% of financial futures (p.747); nearly all positions are closed by offset.
- Deliverable grades: 10-year contract takes notes with 6.5 to 10 years remaining at the first day of the delivery month; 5-year: original maturity max 5y3m, remaining at least 4y2m; 2-year: original max 5y3m, remaining at least 1y9m; bond: at least 15 years (p.748). More than 10 notes deliverable into the 10-year contract (p.764).
- Invoice price = futures settlement (3 p.m. close of notice day) x conversion factor + accrued interest (pp.748-753). Conversion factor = price of the bond at a 6% yield divided by 100; factor above 1 for coupons above 6%, below 1 below 6% (pp.749-751). Table 16.1 shows example bases (p.751).
- Basis b = cash price minus futures price x factor (p.754). Two parts: carry (coupon yield minus repo cost to delivery) and value basis (carry-adjusted basis, never negative because of delivery options; p.756-758).
- Carry sign: positive carry means futures trade below cash by at least the carry; inverted curve with negative carry can give negative bases (p.756). The standard delivery day for carry is the last business day if carry is positive and the first if negative (p.759).
- Convergence: carry decays to zero as expiry nears; at least some deliverables reach near-zero value basis in the delivery period; none negative (p.757-758, 763-764). Convergence does not mean futures equal the cash price of every bond.
- Delivery options (p.758-761): quality (which bond to deliver; worth more with higher volatility and more time), wild card (declare intent until 8 p.m. while futures invoice at the 3 p.m. close; worth little since the 1980s), switch option (bond choice changes in the last week when futures stop trading), timing option. The street now treats the value basis as an upper bound of option value; the actual value basis also contains technicals (p.762).
- Technical drivers of value basis (pp.762-763): unusual investor demand (June 2005: few holders of deliverables, cash rallied faster than futures, basis widened), stripping and buried issues, repo specialness (a bond going special widens its basis; 1986 example of the Japanese holding the 9.25% of 2016 making it trade at near-zero or negative reverse rates).
- Cheapest to deliver (pp.764-767): the issue with the lowest value basis or highest implied repo rate. Below 6% yields the short-duration, high-coupon issue tends to be CTD; above 6% the long-duration, low-coupon issue. Factor bias means a change of CTD becomes likelier when yields are near 6% (author says 6.30% would be within a CTD-switch zone). In 2000-2005 yields stayed below 6% with many similar coupons deliverable (Jan 2006: 10 cheapest coupons from 3.625 to 4.75%, five at 4.25%), so the bias mattered little. Futures price tracks the CTD, so futures duration and convexity are those of the CTD, not of a fixed bond.
- Hedging with futures (pp.767-770): a running hedge that rolls each contract earns approximately the term repo rate instead of the bond's yield (when carry is positive, each roll "sells" the bonds at the forward price, which costs the carry). Hedge ratio by factor or better by yield value of 1/32 on CTD vs hedged issue. Table 16.2 example: 9-month hedge on 4 3/8s of 2012 reduced a $28,000 principal loss per $1m to about $16,000 net, the remainder being the basis falling 46 to 0.5 (32nds). Moral: hedger swaps market risk for basis risk.
- Basis trades (pp.769-775): selling the basis (sell cash, buy futures, invest proceeds in term repo) when expecting convergence. Table 16.3 (May to mid-June 2005, 4 7/8s of 2012, CTD for June 2005): basis fell from 9.4 to 0.4 (32nds), net gain about $1,200 on $1m of bonds and 11 contracts over about one month. Basis broker market is tight: the 10-year basis rarely moves more than about 5/32 on an ordinary day. EFP (exchange for physical) lets the futures leg be done off-pit, 24/7. Convergence trade needs repo; the reverse rate on the dealer's short is an uncertainty.
- Basis trading changed bond liquidity: dealers can warehouse large blocks and hedge in futures via the basis screen (pp.775-776).
- Calendar spreads (pp.777-779): bet on curve slope between contract months; example Sep-Dec 10-year spread bought at 30/32 and sold at 24/32 for a $1,875 loss (p.778). Spread moves reflect carry and curve.
- NOB (notes over bonds) and TUT (tens under twos) (pp.779-784): NOB weighted 1.75 notes to 1 bond (DV01 weight); TUT 1.69 two-year contracts per 10-year in Nov 2006. When the Fed hikes, 2s10s tends to narrow; when it cuts, widen. CTD for 2-year changes often because new 2-year notes are auctioned every month (p.784). The 5-year contract: the newest 5-year note is deliverable and is issued in the delivery month itself (p.780).
- Market intelligence (pp.784-790): open interest/price interpretation table (rally + rising OI = new longs; rally + falling OI = short covering) (p.786); volume as validation; call/put volume ratio on CBOT options with a 10-day average, long-run mean about 1:1 (0.90:1 in 2005), extremes as contrarian signal (p.787-788); CFTC COT noncommercial net positions as contrarian: extreme net shorts in 10-year notes in June 2004 and March 2005 preceded rallies, yield from 4.87% to under 4% in 3 months (p.788-789; anecdotal, two episodes). Bond basis and price direction as commercial-vs-speculative indicator (Table 16.7, p.790).

### Ch 10 - The Market Makers: Dealers and Others (pp. 411-454)
- Dealers wear agent or principal hats; as principals they make markets, hold inventory, underwrite (Treasury auctions bought and distributed to retail) (pp.413-414). The interdealer market produces one prevailing price; retail quotes stay near it.
- Profit sources (p.414-420): agent fees, trading and principal investments (Goldman: about two-thirds of roughly $25bn 2005 net revenue), servicing customers (customer flow is information on market direction), proprietary products, position profits, carry, arbitrage. Tightening spreads and electronic platforms push dealers toward position taking (p.419).
- Dealers are leveraged 40-100x capital and finance mainly with overnight and open repo; money funds, corporates, hedge funds, foreign investors supply repo money (p.421). Dealer loans at the clearing bank rate for odd pieces and fails (pp.421-422, 450).
- Fails (pp.422-424): a fail gives the buyer a free one-day loan; the NY Fed has published fail data since March 2004 (weekly, one-week lag); fails averaged $3.8bn/day in 1990 to 2001 and peaked at $232bn/day in summer 2003 (all securities); Treasury fails averaged $10.7bn/day July 1990 to Dec 2004. Fails rise in the weeks before the quarterly refunding (Feb, May, Aug, Nov), because financing cost of Treasuries rises (owners lend fewer, dealers short more), and around calendar quarter-ends because securities lenders hold back (Figures 10.3 and 10.4, pp.423-425). This is the only explicit quarter-end calendar effect in these chapters; no size in yield terms is given.
- Dealer book and rate view (pp.424-430): dealers position from an expected-value view of the fed funds path (e.g. 70% ease / 30% tighten with payoff $2 / -$1 gives expected $1.10); more confidence means bigger size; bullish bets are extended to longer maturities for more price play (a 1-point fed funds move: about $2,500 per $1m in 90-day bill vs about $21,000 in the 4.5s of 2036). Short rates follow fed funds; long rates depend on inflation expectations, global events, slope (p.429).
- Shorting (pp.430-431): dealers short less than they would go long at the same confidence; they prefer reverse repo to securities borrowing (borrow fee up to about 0.5%); shorts can be called back, a squeeze risk.
- Repo book (pp.431-432): dealers intermediate repo and reverse for a spread; $3.4 trillion repo outstanding (June 2006).
- Arbitrage (pp.432-437): yield-spread arbitrage, curve trades, cash-futures arbitrage. Anomalies come from temporary supply/demand changes (e.g. Treasury auction schedule changes, the 2001 end and 2006 return of 30-year bond issuance moved long-short spreads sharply); opportunities rise in volatile markets (1998 on-the-run/off-the-run spread widened after the Russian default). Hedges can fail: 1998, dealers shorting Treasuries against corporates lost when credit spreads widened (p.420).
- Tails and cash-and-carry (pp.437-439): buying a bill and financing it only part of the period creates a future security; "figure the tail" = effective forward yield. Example: 90-day bill at 3.9375, 30-day term repo at 3.75, fed funds 4.0 gives a future 60-day bill at about 4.03.
- Relative value and technical analysis (pp.440-442): dealers think in spread/risk/liquidity terms; technical analysis is used because clients use it, with levels causing clustered trading; author notes the efficient market view says it is worthless.
- Running a dealer shop (pp.442-447): position limits are arbitrary but protect survival; volatility index (long bonds 7x as volatile as 2-year, so 1/7 of the position size); traders quote indifference levels and earn 1-2/32 per turn; discipline and steady revenue streams beat home-run speculation.
- Clearing banks and dealer loans (pp.449-451); communications and Bloomberg (pp.451-453) - background only.

### Topic tags
- seasonality/time: Treasury futures expire in Mar/Jun/Sep/Dec; trading stops in the last seven business days of the delivery month; delivery notices are possible any business day of the month; quarterly refunding (Feb/May/Aug/Nov) raises Treasury financing cost and fails; fails and repo cost also rise around calendar quarter-ends. No month-end index-extension, reserve maintenance, year-end window dressing or tax-date flow discussed in these ranges.
- volatility: higher bond volatility and more time to expiry raise the quality-option value, widening basis; factor bias matters when yields are near 6% (not in 2000-2005).
- mean-reversion: basis converges to near zero in the delivery period (carry decays, value basis decays for CTD); calendar-spread and NOB/TUT trades are bets on spread normalisation; arbitrage anomalies decay as dealers trade them.
- momentum/oscillators: the call/put volume ratio (10-day average) and COT noncommercial extremes are described as contrarian sentiment signals; evidence is two anecdotes (June 2004, March 2005).
- costs/execution: 1/32 = $31.25; 10-year basis moves about 5/32 per ordinary day; EFP/basis broker market is tight; a dealer quotes about 3/32 wider for risk-bearing cash trades; rolling a hedged long earns the repo rate, not the bond yield (p.768).
- stops-and-exits: position limits arbitrary but survival-oriented; dealers mark to market daily (pp.425, 443).
- position-sizing/risk: size by confidence and expected value; limits scaled by duration/volatility (long bonds 7x the 2-year volatility).
- portfolio/diversification: hedgers trade market risk for basis risk; hedges are only as good as the correlation of the two legs.
- psychology/discipline: dealers' compensation tied to daily marks pushes short-horizon discipline; speculators extrapolate trends (p.788).
- testing-and-robustness/overfitting: none directly; COT/options signals rest on two examples.

### Testable ideas

1. **Roll-aware construction of the I-109 series (method check, not a new idea)** - For a long position in 10-year Treasury futures over the last 3 trading days of each month: in Mar/Jun/Sep/Dec the expiring contract stops trading in its last seven business days, so the holding must be in the next quarterly contract; in other months the front contract is the expiring-cycle one. Check which contract the Yahoo continuous series (ZN=F) uses on those dates and whether the roll gap (switch between contracts) falls inside the 3-day window; test with the window return computed on one single contract, excluding calendar-roll days. - SM p.747, 759 (trading halt in last seven business days, thin volume in delivery month). - Evidence: none claimed; mechanical. - Fit: good, uses our Yahoo series; essential validity check for I-109 results. - Differs: it is a data-integrity gate, not a new strategy.
2. ★ **Carry/roll-down subtraction for futures long (I-109 risk)** - A long in futures versus cash: futures trade below cash by at least positive carry, and a rolled long futures position earns about the excess over term repo, while the underlying yield is not earned (SM p.768). Report I-109 returns as futures-based excess returns; decompose each window return into price change (futures) and compare with a duration-matched cash/yield proxy (FRED 10-year yield change times duration). If the effect is visible in a total-return index but not in the futures series (or vice versa), the claimed edge is partly carry. - SM pp.756, 767-768. - Evidence: textbook. - Fit: good (FRED yields plus Yahoo futures). - Differs: pure accounting control on I-109, no new signal.
3. ★ **Quarter-end and refunding-week effect on the 10-year futures (calendar flow)** - Test the average futures/yield change in (a) the last 3 days of a quarter-end month vs other month-ends, (b) the refunding weeks (auction announced first week of Feb/May/Aug/Nov; auction around the 10th-15th; settlement 15th) using FRED yield changes and Yahoo futures. Signal: long into refunding weeks if financing cost rises/dealer shorts increase and they then cover (hypothesis; fails and specialness rise before the refunding, SM p.423). Gate: t >= 3 on development with a fixed pre-registered window and no peeking. - SM pp.423-425 (fails and financing cost around refunding and quarter-end; no price effect given). - Evidence: only that fails and financing cost rise, not that yields move. - Fit: medium; our data has yields and futures but no repo or fails (NY Fed fails data are free weekly but we do not have them). - Differs: Treasury auction-calendar flow, not index extension; untested in our spent families (month-end index flow is separate).
4. ★ **I-109 split by quarterly-expiry vs non-expiry months** - Run the I-109 return separately for the four expiry-cycle months (Mar/Jun/Sep/Dec, where the front contract is in delivery) and the other eight months, and for the last 3 days when the active contract is within 3 weeks of its first delivery date. Hypothesis: if the edge sits only in months where the roll mechanics distort the series, it is an artefact. - SM p.747, 759-763 (delivery-month distortions: thin trade, basis convergence, CTD switches). - Evidence: none. - Fit: good, same data as I-109. - Differs: robustness slice, adds a pre-registered falsification test.
5. **CTD/basis and futures-vs-cash divergence around delivery** - Compare the Yahoo futures series with a synthetic cash price (FRED 10-year yield converted to a price of a constant-maturity note) in the last month before expiry; the gap should shrink as carry decays. Use the residual as a measure of roll noise to subtract from the I-109 returns. - SM pp.757-758. - Evidence: textbook. - Fit: poor-to-medium; synthetic cash price is crude (factor/CTD not reproducible without per-bond data), tick-level basis cannot be tested. - Differs: data-quality tool.
6. **COT noncommercial extreme as contrarian filter** - When CFTC noncommercial net position in 10-year note futures is in an extreme percentile of its trailing window, expect a bond rally (extreme net short) or sell-off; test as filter on the I-109 window or standalone weekly. - SM p.788-789 (June 2004, March 2005 episodes). - Evidence: two anecdotes. - Fit: good data (free COT), but weekly, small sample, big multiple-testing risk. - Differs: positioning/sentiment, not price pattern.
7. **Call/put volume ratio** - Needs options volume; not in our data. Skip. - SM p.787.
8. **NOB / TUT spread** - Relative value between 10s/2s futures by DV01 weights; could be approximated from FRED 2- and 10-year yields; the book says the spread narrows in hiking cycles and widens in cuts. - SM pp.779-784. - Fit: poor (no 2-year futures data; FRED yields only; cost wall on spread trades unknown). - Differs: curve trade, not flow-driven.

### Warnings / pitfalls
- The CTD changes with yield level and with technicals (stripping, repo specialness, concentrated holdings), so the futures price is not a fixed-bond price; the basis can widen on days of repo specialness even when carry is unchanged (pp.762-767).
- Futures prices are below cash by carry (when carry is positive); a rolled long futures position does not earn the bond's yield, only the excess over repo; the curve slope changes the return over time (p.768). Inverted curves flip the sign.
- Delivery month: volume thins and the contract stops trading seven business days before month end; holders who stay are at risk of assignment (long with oldest position). Do not hold the expiring contract through the window (p.747).
- Quarter-end and refunding periods have more fails and higher financing cost for Treasuries; a long in futures does not pay that financing (it is in the futures price) but cash-based proxies do.
- Hedges swap market risk for basis risk; basis can move against the hedger (Table 16.2, p.769).
- Sentiment indicators (COT, put/call, open interest rules) are shown with anecdotes only; the author gives no statistics, so these are hypotheses (pp.786-790).
- Dealer behaviour: a large part of futures trading is hedging and basis trading, not outright directional views, so volume is not pure information (p.756, 775-776).
- Position limits and volatility scaling: long bonds are about 7x as volatile as 2-year notes (p.443); size by DV01, not face value.
- Not found in the assigned ranges: any quantification of month-end/quarter-end/year-end Treasury yield or repo moves, reserve maintenance period effects, settlement Wednesday effects, or index extension flows. For I-109 these chapters only supply contract mechanics (roll, delivery, CTD, carry) and the quarterly refunding/quarter-end fails tendency, not evidence for the flow itself.

