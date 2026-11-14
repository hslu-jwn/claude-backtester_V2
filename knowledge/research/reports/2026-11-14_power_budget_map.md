# Power budget map (2026-11-14, Opus; Fable directions row 5)

Smallest effect per event that a screen on development data (2015-01-01 .. 2021-09-13) could show at t 3, per
FTMO symbol, hold and event frequency, against the engine's round-trip cost. Signal-free: entry at the close of
the 13:00 UTC M1 bar on every weekday (Asian indices are closed then), exit at the first bar at or after entry +
hold. MDE(t 3) = 3 sd / sqrt(N), N = events in 6.7 years: daily 1,700, weekly 350, monthly 80, 8 a year 54.
Cost = spread (fill_spread_time) + 2 x slippage + commission at the entry, median, bp. **Swap excluded** (1d and
5d holds pay it on top). NATGAS has no development data. Script: `research/screens/2026-11-14_power_budget_map.py`.

| symbol | cost bp | sd 30m | sd 1h | sd 6h | sd 1d | sd 5d | MDE t3 bp: daily 1h / daily 6h / weekly 1d / weekly 5d / monthly 1d / monthly 5d / 8 a yr 1h |
|---|---|---|---|---|---|---|---|
| AUDJPY | 3.6 | 13 | 18 | 37 | 72 | 126 | 1 / 3 / 12 / 20 / 24 / 42 / 7 |
| AUDUSD | 2.1 | 12 | 17 | 37 | 64 | 108 | 1 / 3 / 10 / 17 / 21 / 36 / 7 |
| AUS200 | 3.2 | 14 | 25 | 52 | 108 | 176 | 2 / 4 / 17 / 28 / 36 / 59 / 10 |
| BTCUSD | 7.3 | 79 | 118 | 246 | 456 | 915 | 9 / 18 / 73 / 147 / 153 / 307 / 48 |
| CADJPY | 3.3 | 13 | 21 | 42 | 67 | 116 | 2 / 3 / 11 / 19 / 22 / 39 / 9 |
| CHFJPY | 3.0 | 9 | 14 | 28 | 67 | 101 | 1 / 2 / 11 / 16 / 22 / 34 / 6 |
| DXY | 4.8 | 7 | 11 | 25 | 36 | 62 | 1 / 2 / 6 / 10 / 12 / 21 / 4 |
| ETHUSD | 11.5 | 86 | 129 | 286 | 537 | 1175 | 9 / 21 / 86 / 188 / 180 / 394 / 53 |
| EU50 | 5.3 | 19 | 31 | 70 | 122 | 210 | 2 / 5 / 20 / 34 / 41 / 71 / 13 |
| EURAUD | 2.1 | 11 | 15 | 32 | 57 | 97 | 1 / 2 / 9 / 16 / 19 / 33 / 6 |
| EURGBP | 1.7 | 10 | 15 | 30 | 54 | 98 | 1 / 2 / 9 / 16 / 18 / 33 / 6 |
| EURJPY | 1.9 | 10 | 16 | 30 | 56 | 92 | 1 / 2 / 9 / 15 / 19 / 31 / 6 |
| EURUSD | 1.0 | 11 | 16 | 33 | 51 | 86 | 1 / 2 / 8 / 14 / 17 / 29 / 7 |
| GBPAUD | 2.8 | 11 | 16 | 33 | 62 | 107 | 1 / 2 / 10 / 17 / 21 / 36 / 7 |
| GBPJPY | 3.1 | 13 | 19 | 37 | 75 | 131 | 1 / 3 / 12 / 21 / 25 / 44 / 8 |
| GBPUSD | 1.8 | 11 | 16 | 34 | 61 | 108 | 1 / 2 / 10 / 17 / 20 / 36 / 7 |
| GER40 | 1.1 | 19 | 33 | 71 | 119 | 239 | 2 / 5 / 19 / 38 / 40 / 80 / 13 |
| HK50 | 3.9 | 13 | 24 | nan | 126 | 218 | 2 / nan / 20 / 35 / 42 / 73 / 10 |
| JP225 | 5.3 | 14 | 26 | 64 | 132 | 235 | 2 / 5 / 21 / 38 / 44 / 79 / 11 |
| NAS100 | 1.7 | 18 | 37 | 87 | 118 | 206 | 3 / 6 / 19 / 33 / 40 / 69 / 15 |
| NZDJPY | 4.4 | 13 | 18 | 35 | 70 | 120 | 1 / 3 / 11 / 19 / 24 / 40 / 7 |
| NZDUSD | 4.0 | 13 | 18 | 38 | 68 | 109 | 1 / 3 / 11 / 18 / 23 / 37 / 7 |
| UK100 | 2.6 | 15 | 26 | 58 | 99 | 186 | 2 / 4 / 16 / 30 / 33 / 62 / 10 |
| UKOIL | 13.5 | 43 | 68 | 169 | 250 | 459 | 5 / 12 / 40 / 74 / 84 / 154 / 28 |
| US2000 | 5.0 | 21 | 48 | 99 | 144 | 248 | 3 / 7 / 23 / 40 / 48 / 83 / 19 |
| US30 | 1.0 | 15 | 30 | 76 | 116 | 192 | 2 / 5 / 19 / 31 / 39 / 65 / 12 |
| US500 | 2.2 | 18 | 29 | 70 | 97 | 174 | 2 / 5 / 16 / 28 / 33 / 58 / 12 |
| USDCAD | 1.4 | 11 | 17 | 35 | 51 | 84 | 1 / 3 / 8 / 13 / 17 / 28 / 7 |
| USDCHF | 2.1 | 10 | 15 | 32 | 63 | 98 | 1 / 2 / 10 / 16 / 21 / 33 / 6 |
| USDJPY | 1.2 | 10 | 14 | 30 | 52 | 88 | 1 / 2 / 8 / 14 / 17 / 30 / 6 |
| USOIL | 11.6 | 53 | 88 | 201 | 300 | 507 | 6 / 15 / 48 / 81 / 101 / 170 / 36 |
| XAGUSD | 30.0 | 42 | 57 | 105 | 149 | 316 | 4 / 8 / 24 / 51 / 50 / 106 / 23 |
| XAUUSD | 2.3 | 21 | 30 | 58 | 84 | 158 | 2 / 4 / 13 / 25 / 28 / 53 / 12 |

## Reading

1. **Daily events with intraday holds are not power-limited:** MDE 1-3 bp (FX), 2-6 bp (indices, gold) at
   1-6 h. There the binding limit is the effect itself against cost (cost wall: published effects give 1-3 bp).
2. **Weekly events need ~8-20 bp (FX) or ~16-40 bp (indices) at a 1-5 day hold; monthly ~17-50 / 33-80 bp; eight a
   year at 1 h ~6-15 bp.** Halved published effects rarely reach that (I-67, I-70, I-71 died there): an event
   rarer than weekly is only worth a screen when the halved published effect is above the MDE column.
3. **Combined with the pass map** (`2026-11-14_challenge_pass_map.md`: ~+0.05 R net at ~300+ trades a year):
   a goal-1 stream must be roughly daily, and at a 0.5 daily-ATR stop +0.05 R net is ~1.5 bp on EURUSD / USDJPY
   (stop ~30 bp) and ~3 bp on US30 / GER40 / NAS100 (stop ~60 bp). With cost 1-2 bp that means **~2.5-5 bp gross
   per daily event** on the cheapest symbols: about 2x the published intraday effects measured so far.
4. Crypto CFDs (BTCUSD 7 bp, ETHUSD 12 bp cost, sd 4-5x FX) and XAGUSD (30 bp) / oil (12-14 bp) are cost-bound
   at any frequency for intraday holds.
