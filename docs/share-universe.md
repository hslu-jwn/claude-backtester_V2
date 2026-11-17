# Wide US share universe (card 2 of the 2026-11-16 sweep; venue M13, accepted by the user 2026-11-17)

Frozen 2026-11-17 by Opus (`Continue.Research Mode=auto`) **before any return was computed**. Used by every card on
the real-share venue (cards 3, 4, 9; family labels per card). Signal-free: the rule uses only symbols, prices and
volumes known at the formation date.

## Data

- **Prices:** Alpaca SIP bars (`data/alpaca.py`, the user's free plan), split-adjusted, not dividend-adjusted.
  Alpaca serves a symbol's bars point in time under the symbol it traded as (LNKD, YHOO, AET, ... to their last day;
  audit `knowledge/reviews/2026-11-16-idea-sweep/card2_alpaca_audit.md`). A renamed security is also served in full
  under its new symbol (META carries FB's history, GEN carries SYMC's), and old symbols are reused later (MON, FB).
- **Symbol candidates (point in time):** every symbol in FINRA's daily short-sale volume files on the first trading
  day of each month, 2015-07 .. 2026-11 (`CNMSshvol` from 2018-08-01; before that the union of the per-facility files
  `FNSQ`, `FNYX` and `FNRA` where served), plus every Alpaca `us_equity` asset (active and inactive) on NYSE, NASDAQ,
  AMEX, ARCA or BATS. FINRA symbols are kept only in the form `^[A-Z]+(/[A-Z])?$` (drops preferreds `p`, warrants
  `w`, rights `r`, units `u`, test symbols), with `/` mapped to Alpaca's `.` (BRK/B -> BRK.B).

## Rule

1. **Daily table:** Alpaca daily bars of all candidates, 2015-07-01 .. today.
2. **One row per security and day (de-duplication):** two symbols with exactly the same close and volume on a day
   are one security; keep the symbol in that month's FINRA list, otherwise the alphabetically first.
3. **Not common stock:** excluded when its Alpaca asset is listed on ARCA or BATS, or its Alpaca name matches
   `ETF|ETN|Fund|iShares|SPDR|ProShares|Direxion|Invesco|Vanguard|VanEck|WisdomTree|Global X|First Trust|Schwab|ARK |
   Ultra|Leveraged|Daily .*(Bull|Bear)|Notes|Depositary Shares .*%|Preferred|Warrant|Unit|Right` (case-insensitive). A
   symbol with no Alpaca asset (delisted before Alpaca's list) is kept.
4. **Monthly formation:** after the close of the last trading day of each month, eligible = >= 60 daily bars, last
   close > USD 5; rank by the median of close x volume over the last 60 sessions; the **top 1,000** (ties by symbol)
   form the next month's universe. Universe months 2016-01 .. 2026-11.
5. **Bars for the union:** daily bars (step 1) and `30Min` bars 2015-12 .. today for every symbol that is ever in a
   monthly universe; auction prints (`/v2/stocks/auctions`) for the same symbols when a card needs official open /
   close prices.

## Splits for the cards (unchanged project split)

Development before 2021-09-14, test after, once per card. Cards needing a mechanism that starts later state their
own split and need the user's go. **Card 7 (leveraged single-stock ETF rebalance; rule set by the user,
2026-11-17):** development from the first single-stock leveraged fund launch to 2024-12-31, test 2025-01-01 ..,
once.

## Assumptions (Opus)

- A1: the ETF / non-common filter is a name and venue rule, not a security master; misses are reported by the audit
  (count of universe members per month that look like funds by name).
- A2: FINRA lists only symbols with off-exchange volume that day; an NMS stock with none on the first trading day of
  a month is still caught on another month or through the Alpaca asset list.
- A3: dividends are not in the prices (as everywhere in the repo); a card that holds over ex-dates reports it.
- A4 (2026-11-17, after the first build, before any return): an audit of all 532 universe members without an Alpaca
  asset found 11 delisted exchange-traded products and 2 non-common symbols; they are excluded by name: XIV, TVIX,
  UWTI, DWTI, UGAZ, DGAZ, RSX, SPLG, AMJ, CSJ, CIU, VALE.P, XXXX. The other no-asset members are operating companies
  (delisted, acquired, renamed: YHOO, TWX, AET, LNKD, ...).
- A5: Alpaca's daily history starts 2016-01, so the first month with 60 bars is **2016-04**; the universe and every
  card's development period start there.
- A6 / A7 (2026-11-17, before any intraday data): Alpaca builds every timeframe from minute bars and pages by 10,000
  underlying minutes (~3 weeks per symbol), so 30-min or 1-hour history for the universe is ~170,000 requests. Step 5
  is replaced: a card fetches only the minutes it needs, as one multi-symbol 1-min request per trading day and 500
  names (e.g. card 4: 09:57-10:03 ET; the 10:00 price = close of the last minute bar before 10:00, the entry = open of
  the first minute bar from 10:00; a name with no trade in the window is out that day). Test-period prices only after
  a development pass.
