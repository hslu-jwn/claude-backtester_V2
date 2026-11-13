# Proposal: hourly spread table for the symbols without one (2026-11-13)

**Accepted by the user 2026-11-13: option A** ("A: full table"), applied the same day. Opus, local scripts.

## Why

Five symbols (GBPJPY, GBPUSD, NAS100, US500, XAUUSD) use the hourly table `engine/ftmo_spread_median.json`
(median bar spread by New York year and hour). The other 29 cached symbols pay one fixed 2026 spread at
every hour and in every year: the rollover hour 17 New York (10-20x wider), Asia hours and older years
(FX 2-8x wider in 2015) are under-charged, and London / New York hours partly over-charged, because the
fixed spreads were raised on 2026-11-09 to the live mean of all hours.

## How measured

- Source: the MT5 cache (`data/cache/mt5`), ask - bid = MT5's bar spread; median per (symbol, New York
  year, hour) with >= 100 bars, from 2015 (or the symbol's first MT5 year). Same method as the packaged
  table: GBPUSD / XAUUSD rebuilt from the cache match it in 239 / 254 cells, the rest one tick apart.
  `scripts/cache_spread_table.py`.
- Live check: fill probe runs 3 + 4 (`results/fill_report_2026-11-09/fills.csv`), mean bar spread / table
  value at the bar-close lookup (`fill_spread_time`), the method of `LIVE_TABLE_FACTOR`.

## Table against today's fixed spread (ratio; 2026 row unless stated)

| Symbol | all hours | NY 3-11 (London + NY morning) | hour 17 | first year, all hours | live / table |
|---|---|---|---|---|---|
| EURUSD | 1.06 | 0.50 | 14.0 | 4.0 (2015) | 0.62 |
| AUDUSD | 1.20 | 0.63 | 10.6 | 3.4 | 0.99 |
| NZDUSD | 2.29 | 1.67 | 16.0 | 7.7 | - |
| USDCAD | 1.13 | 0.65 | 10.2 | 2.2 | 1.09 |
| USDCHF | 1.38 | 0.69 | 14.4 | 3.2 | - |
| USDJPY | 1.43 | 0.80 | 14.9 | 2.2 | 0.89 |
| EURJPY / AUDJPY | 1.36 / 1.49 | 0.95 / 0.98 | 8.7 / 11.6 | 1.1 / 2.4 | 0.80 / 0.81 |
| EURAUD / EURGBP / GBPAUD | 1.57 / 1.48 / 1.87 | 0.90 / 1.00 / 1.02 | 14 / 12 / 19 | 3.1 / 2.7 / 5.8 | 0.74 / - / - |
| CADJPY / CHFJPY / NZDJPY | 1.82 / 1.77 / 1.56 | 1.19 / 0.93 / 0.98 | 14 / 20 / 13 | 4.2 / 1.8 / 2.8 | - |
| GER40 / UK100 / EU50 | 0.94 / 0.90 / 1.14 | 0.54 / 0.30 / 1.25 | closed | 1.1 / 0.8 / 1.7 | 1.07 / 1.09 / - |
| US30 / US2000 / JP225 / HK50 / AUS200 | 0.90 / 1.03 / 0.95 / 1.09 / 1.02 | 0.87 / 1.03 / 0.91 / 1.19 / 1.00 | - | 0.5 / 0.3 / 0.7 / 1.6 / 14.7 | 1.10 / - / 0.98 / - / 1.00 |
| USOIL / UKOIL / NATGAS | 0.92 / 0.92 / 0.98 | 0.99 / 0.98 / 0.99 | closed | 0.2 / 0.5 / 0.7 | 1.08 / 1.09 / 1.02 |
| XAGUSD | 1.10 | 1.03 | - | 0.7 | 0.73 |
| BTCUSD / ETHUSD / DXY | 1.00 / 0.91 / 1.00 | 1.00 / 0.91 / 1.06 | - | 12 / 6.3 / 6.1 | 1.00 / 1.00 / - |

"-" = no live fills or no value. Old-year ratios compare raw spreads with the 2026 fixed value; for
indices / oil the fixed spread is already scaled down with the price in old years, so their effective
change there is smaller than the ratio.

## Effect on the strategies that trade these symbols (net R, today -> proposal)

| Strategy | Year | A: table | B: table, never below fixed | C: hour 17 only |
|---|---|---|---|---|
| alternating_path | 2023 | -491.1 -> -482.9 | -517.3 | -491.1 |
| alternating_path | 2016 | -514.4 -> -746.6 | -746.6 | -514.4 |
| london_fix | 2023 | -273.4 -> -368.5 | -380.0 | -370.3 |
| london_fix | 2016 | -191.7 -> -326.7 | -326.7 | -239.1 |
| opening_range | 2023 | -36.6 -> -27.5 | -50.0 | -36.6 |
| daily_reversal | 2023 / 2016 | 3.9 -> 4.0 / -4.3 -> -9.5 | 3.4 / -9.9 | 3.9 / -6.6 |

london_fix's time exit fires at 17:05-17:07 New York (first close after the FTMO break): its shorts close
at the ask in the rollover spread, which the fixed spread hides. All four strategies are falsified or
closed; no verdict changes.

## Data caveats (excluded from the proposal)

- AUS200 2019-2021: 12-18 points against 1.0-1.2 from 2022 on (zero-spread bars 5-26 %): a feed change,
  not a cost. Dropped; those years take the nearest year (2022) by the table's rule.
- BTCUSD / ETHUSD: spread history jumps (BTCUSD 3.6-44 against 1.0 in 2026; ETHUSD 1.7-4.3 against
  0.6), no rollover break (24/7). Not added; they keep the fixed spread.
- DXY 2024: 29 k bars, 6x the later years. Dropped (nearest year 2025).
- US2000 moves between 0.2 and 1.13 from year to year (2023-24: 0.2): kept, as measured.

## Options

- **A (pick): extend the table** to 27 symbols as measured (median, 2015+, without the caveats above;
  the impact runs above contained them, but no run trades an excluded symbol-year), plus the live factor
  where it is >= 1.05 (as for the five table symbols): GER40 1.07, UK100 1.09, UKOIL 1.09, US30 1.10,
  USDCAD 1.09, USOIL 1.08; factors below 1 keep the table (as XAUUSD). Closest to the live fills: the
  table is never below the live mean by more than 10 %, and for EURUSD / EURAUD / XAGUSD it still
  charges more than live. Lowers London / New York costs of the FX majors, UK100 and GER40 in recent years.
- **B: as A, but no cell below today's fixed spread.** Never lowers a cost; keeps the 2026-11-09 raises
  (set to the all-hours live mean) in the hours where live fills are cheaper.
- **C: hour 17 only** (rollover); all other hours keep the fixed spread. Smallest change; old-year FX and
  Asia hours stay under-charged.

The p90 stress table is extended the same way in A / B / C. Golden lists are rewritten after the change.
