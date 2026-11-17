# Card 2 questions 1-2: Alpaca coverage audit (signal-free, 2026-11-17)

Probed by Opus inline with the user's Alpaca keys (free Basic plan); no return was computed.

| Question | Finding |
|---|---|
| (1) History of names delisted 2016-2021 | **Yes, 20 of 20.** Daily SIP bars from 2016-01-04 to the last trading day for LNKD, YHOO, WFM, KATE, MON, TWX, AET, COL, CA, ESRX, SCG, RHT, APC, CELG, RTN, AGN, JCP, ETFC, TIF, CXO. Last prices match the deal terms (LNKD 195.96 vs Microsoft's USD 196; TIF 131.16 vs LVMH's 131.50; JCP 0.18 in bankruptcy). |
| (2) Official auction prints on the free plan | **Yes.** `/v2/stocks/auctions` (feed sip) returns the opening and closing auction price and size per day from 2016 (AAPL 2016-01-04: open 102.50 / 883,414 sh, close 105.35 / 3,440,267 sh). |
| Point-in-time symbol list | `/v2/assets?status=inactive` lists 19,149 inactive symbols (mostly OTC) and holds CELG and TIF but **not** LNKD or YHOO: names delisted before ~2018 are missing. The bars exist for them, so the universe needs another symbol source for 2016-2017 (e.g. index-membership or exchange delisting lists), or development starts 2018. |
| (3) Names above USD 20 M median dollar volume | not run: needs the symbol list above; card 2 is venue work and waits on M13. |

Reading: survivorship can be controlled on Alpaca (delisted prices are served), and the auction prints remove the
open-print bias noted in I-96. The open point is the symbol list for 2016-2017.

## Question 3 and the universe build (2026-11-17, `research/screens/2026-11-17_card2_share_universe.py`)

- Candidates: 23,756 symbols (FINRA files of 137 months: 23,542; plus Alpaca listed assets). Daily bars 1.8 GB.
- 18.8 M security-days; 1.01 M duplicate rows dropped (renamed tickers served twice); 8,921 fund symbols excluded
  (ARCA / BATS listing, fund names, A4 list).
- Universe 2016-04 .. 2026-12 (A5: Alpaca history starts 2016-01), 1,000 names every month, 2,418 distinct symbols.
  Rank-1,000 median dollar volume USD 28 M (2016) .. 83 M (2026): **all 1,000 names clear USD 20 M every month.**
- Members without an Alpaca asset (delisted before the list, caught through FINRA): ~220 a month in 2016, ~120 in
  2021: survivorship is controlled. A4: reading all 532 such names found 11 delisted ETPs (XIV, TVIX, ...) and two
  non-common symbols; excluded before any return.
