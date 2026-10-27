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
