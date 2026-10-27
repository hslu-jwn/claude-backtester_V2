# More symbols before research — proposal (V2.6 step 9, Opus, night 2026-10-27)

The user picks; nothing is downloaded yet (user, 2026-10-26). **Every symbol below is a
candidate to verify**: FTMO's current MT5 list and histdata.com's coverage were not checked tonight
(no terminal session). First step in the morning: `python -m backtester.tools.mt5_info` (lists the
broker's symbols, writes `results/trading.json`) and the histdata download page.

## Today (26 MT5 symbols + Binance)

FX: AUDUSD, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, NZDUSD, USDCAD, USDCHF, USDJPY. Metals: XAUUSD,
XAGUSD. Indices: US30, US500, NAS100, US2000, GER40, UK100, JP225, EU50. Energy: USOIL, UKOIL,
NATGAS. Other: DXY, BTCUSD, ETHUSD (+ BTCUSDT / ETHUSDT on Binance). histdata (2015+) for 21 of them
(not US30, US2000, NATGAS, BTCUSD, ETHUSD).

## What would add the most (for V2.7: members that behave differently)

| Priority | Candidates | Why | Check |
|---|---|---|---|
| 1 | **JPY / commodity crosses**: AUDJPY, CADJPY, NZDJPY, CHFJPY, EURAUD, GBPAUD | risk-on / risk-off and commodity cycles not covered by the USD majors; trend-following (strategy 4) liked GBPJPY | histdata has most FX crosses 2015+; spread vs ATR (costs) |
| 2 | **Asia / Europe indices**: AUS200, HK50, FRA40, SPN35 | sessions outside New York (Tokyo / Sydney / Hong Kong), different regime timing from the US indices | FTMO symbol names; histdata index files (verify which exist) |
| 3 | **EUR / GBP crosses**: EURCHF, EURCAD, GBPCHF, GBPCAD | mean-reverting, low-volatility pairs: candidates for the quiet sideways regime the gap strategies preferred | swap (overnight holds), spreads |
| 4 | **Metals in other currencies / platinum**: XAUEUR, XPTUSD | gold without the USD leg; another metal | FTMO availability |
| 5 | **More crypto**: SOL, XRP (FTMO / Binance) | 24 / 7, different regime | short history (2020+), weekend handling, costs |

Not recommended now: single stocks (earnings gaps, corporate actions, short histories on MT5),
exotic FX (USDTRY, USDZAR: wide spreads, gaps), soft commodities (thin MT5 history).

## Per added symbol (the work, when chosen)

Download MT5 history (and histdata where it exists, with the new clock + continuity check),
`tools/check.py` report, costs in `engine/costs.py` (spread, commission, swap, tick size,
reference price) and the spread table if measured, sessions / trading hours, instrument ->
currency mapping for the news calendar (`data/news.py`), golden lists unchanged. Roughly one queue
job per symbol for the data; the costs need the FTMO contract specs from `mt5_info`.

## Opus's suggestion

Start with priority 1 (six JPY / commodity crosses) and 2 (AUS200, HK50): they add the most
different behaviour for the portfolio at the lowest cost to integrate (FX: same session logic and
cost model as the existing pairs).

## Picked by the user 2026-10-27, checked with `tools.mt5_info --no-save` the same day

AUDJPY, CADJPY, NZDJPY, CHFJPY, EURAUD, GBPAUD, AUS200 (FTMO name `AUS200.cash`), HK50
(`HK50.cash`): all eight exist on FTMO, trade mode full, market execution, FX contract 100 000 /
indices 1, volume step 0.01. JPY crosses 3 digits, AUD crosses 5, indices 2. Swap points (long /
short): AUDJPY 3.54 / -13.32, CADJPY 0.5 / -5.71, NZDJPY 0.77 / -5.45, CHFJPY -11.94 / 1.79,
EURAUD -13.56 / 1.82, GBPAUD -13.4 / -1.25 (triple Wednesday); AUS200 -180.79 / -50.04, HK50
-477.11 / -16.45 (triple Friday). Open points: HK50 tick value read 0 (no HKD rate in the
terminal: costs need a USDHKD quote or a fixed rate); the clock step stopped at AUDJPY H1 "no bars"
(the terminal had no history for the new symbols yet; the clock is already known per date, so
not needed). Spreads to measure after the download.

## Step 9 data state (2026-10-27)

- histdata.com 2015-2021 (year files; 2021 has no month files for these pairs) imported for all
  eight (histdata names AUXAUD = AUS200, HKXHKD = HK50): FX 2184 days, AUS200 2143, HK50 1729.
- MT5: the terminal returned only ~98,000 M1 bars per symbol (FX from 2026-07-22, AUS200 from
  2026-07-01, HK50 from 2026-05-27): its "Max bars in chart" is not Unlimited. **2022-01-01 to
  mid-2026 is missing** (`tools.check`: NOT DOWNLOADED) until the user sets Unlimited and the
  download re-runs; then `cache_repair <SYMBOL> --clock-table results/v26b2_rebuild_server_clock.json`
  per symbol, and the median M5 range (doji threshold) is re-measured (provisional values now).
- `tools.check` of the eight: no duplicate timestamps, broken candles or negative spreads; a few
  minute jumps at known events (2016-06-24 Brexit, 2019-01-02 JPY flash crash, session opens).
- Golden lists unchanged (7 / 7 identical).
