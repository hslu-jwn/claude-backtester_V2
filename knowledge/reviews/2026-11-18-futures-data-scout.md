# Free futures data sets, scout 2026-11-18 (the user: "Futures data hunt"; M12)

One Sonnet web subagent (read-only); "opened" = the subagent opened the URL on 2026-11-18. Several fetches timed out
(CME, Stooq, Barchart; SSRN 403). Background, not rules. Owned data excluded (Yahoo ZN=F, EIA CL / HO / RB / NG
contracts 1-4, Cboe VX, FRED, NY Fed / Treasury / SEC / FINRA sets).

## Non-price data

| Data set | URL | History, frequency | Notes |
|---|---|---|---|
| CFTC Commitments of Traders, bulk zips (opened) | https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm (files under `https://www.cftc.gov/files/dea/history/`: `deacot{YEAR}.zip`, `fut_disagg_txt_{YEAR}.zip`, `fut_fin_txt_{YEAR}.zip`, `dea_cit_txt_{YEAR}.zip`) | legacy 1986+, disaggregated 2006 / 2009+, TFF 2010-07+, CIT 2006+; weekly | Tuesday positions, released Friday 15:30 ET; no key |
| CFTC public reporting API (opened) | https://publicreporting.cftc.gov/ (Socrata; legacy 6dca-aqww, disagg 72hh-3qpy, TFF gpe5-46if, CIT 4zgm-a668) | as above | endpoint pattern from memory, not tested |
| CFTC Index Investment Data (opened) | https://www.cftc.gov/MarketReports/IndexInvestmentData/index.htm | 2007-12 .. 2015-10, monthly | discontinued; manual files |
| EIA weekly crude stocks (opened) | https://www.eia.gov/dnav/pet/xls/PET_STOC_WSTK_DCU_NUS_W.xls | 1982+, weekly (Wednesday) | a surprise needs consensus forecasts (not free) |
| EIA natural gas storage (opened) | https://www.eia.gov/dnav/ng/hist/nw2_epg0_swo_r48_bcfw.htm | 2010+, weekly (Thursday) | same |
| CME volume / open interest / settlements | https://www.cmegroup.com/market-data/settlements.html (not opened) | - | history appears to be paid (DataMine); unverified |

Not checked: warehouse stocks, USDA calendars, GSCI / BCOM weights, ETF futures holdings, Treasury CTD / delivery.

## Free daily prices per contract month

None found. Yahoo serves no expired contracts (Opus tested ZCZ24.CBT, CLZ19.NYM, ESZ15.CME on 2026-11-18: "No data
found, symbol may be delisted"); Barchart allows one manual CSV a day (not scriptable); Stooq unverified; Norgate /
Premium Data are paid. Usable free futures prices stay: Yahoo continuous front (=F, roll gaps not adjusted, 2000+)
and the EIA energy strips (contracts 1-4, 4 markets).

## Ideas checked with M4 (no data loaded)

- **I-74 hedger position-change reversal (COT)**, now on futures: tradeable ~21 bp per 20 days per unit, halved ~11;
  ~25 markets, 20-day long-short sd ~250 bp (estimate), ~270 independent periods 2000-2021: se ~15, t 3 needs ~45 bp.
  c ~0.02 (cost ~4 bp / sd 250); pass chance < 5 %: PARKED (M4).
- **I-118 hedging-pressure level premium (COT)**: published ~7.6 % a year (energy study, secondary snippet), halved
  ~3.8 %; long-short sd ~10-12 % a year: t over 21 years ~1.4-1.7; pass chance < 10 %: PARKED (M4).
- **I-119 USO roll front-running** (Kumar & Venkataraman, ETFs pay ~30 bp for their rolls, snippet only): USO rolled
  CL over 4 days about two weeks before expiry, inside I-115's window (business days 5-9) on the same CL spread; not an
  independent hypothesis: covered by I-115 (FALSIFIED at its test). No new look.

Free futures prices limit goal-2 futures research to continuous front series and the energy strips; per-contract
history (needed for roll, curve and spread ideas outside energy) is paid. Optional for the user: a paid per-contract
history (e.g. Norgate) only if a carded idea needs it.

## Paid per-contract history: prices (web search 2026-11-18; vendor pages not all opened, check before paying)

| Vendor | Coverage | History | Price | Notes |
|---|---|---|---|---|
| Databento (GLBX.MDP3) | CME / CBOT / NYMEX / COMEX, every contract incl. expired | 2010+ | pay per use from $0.50 / GB; $125 free credit | daily bars are tiny (likely inside the free credit); exact cost from a free metadata call before download; Python API key |
| Norgate Data futures | ~100 markets, 11 exchanges, individual + continuous | ~1980+ (third-party claim) | ~$270 a year (third-party, unverified) | Windows updater + Python package; access ends with the subscription |
| FirstRate Data | 130 most active futures, individual + continuous, daily incl. open interest | 2007+ (individual contracts from ~2011 on some) | $299 one-time bundle (third-party) | perpetual licence; updates extra |
| CSI Unfair Advantage | 49 North American + 69 world futures | long | from $37 a month | export only during the subscription month |

Opus: Databento first (likely free for daily bars, clean API; but only 2010+, i.e. ~11.7 development years); Norgate only
if a card needs pre-2010 per-contract history for power.
