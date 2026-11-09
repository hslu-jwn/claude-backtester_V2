# Cost in R per symbol (development period only), 2026-11-09

Data: only candles before 2021-09-14 (V2 fixed development split). Script (outside the repo):
`scratchpad/costs/cost_table.py`. Everything below is computed, not estimated, except where marked ASSUMPTION.

## How V2 charges costs (src/backtester/engine/costs.py, spread_table.py)

- Spread: one spread per round trip (longs enter at ask, exit at bid; candles are bid). Source order:
  (1) `ftmo_spread_median.json` = FTMO median M1 bar spread by year and New York hour, price units, NOT
  price-scaled, only for GBPJPY, GBPUSD, NAS100, US500, XAUUSD (years outside the table take the nearest
  year; NAS100/US500 start 2021); (2) else the fixed `SymbolCosts.spread` (FTMO median of Aug-Oct 2026)
  x fill price / `reference_price` (2026 median price). So spreads vary by hour only for those 5 symbols.
- Slippage: fixed per symbol (about half the spread), price-scaled like the spread, paid on market entries
  and on every non-TP exit (so a stop-out pays it twice, a TP exit once).
- Commission: FX $5/lot round turn (price = 5 / contract size), XAUUSD/XAGUSD percentage 0.0014 % round
  turn, indices/oil 0.
- Swap: per night over the 17:00 New York rollover (triple on one weekday), USD per lot; zero for intraday.
- Conversion adjustment: 0.7 % of |gross R| on non-USD-profit symbols (JPY, CAD, GBP, EUR indices).
- `cost price` here = spread + 2 x slippage + commission (stop-out case, worst case; a TP exit saves one slippage).
  Not included: swap, conversion adjustment (0.7 % x |R| is negligible against the figures below).

## Method

- M1 loader: `data.cache.read_cached_days`; MT5 cache preferred per day, else histdata (bid only);
  `drop_flat_minutes` then `data.resample.resample` to M15/H1/D1 (D1 = New York day boundary, repo default).
- ATR(14) = Wilder smoothing of the true range (same definition as `detectors/atr.py`, vectorised); median
  over the dev period. M15 and H1: only candles opening 08:00-19:59 UTC (ASSUMPTION: "active hours", so the
  ATR is comparable to the London/NY cost). D1: all days.
- Cost: `CostConfig().spread/slippage/commission_price` at the dev-period median bid close (price-scaling
  base), median over hours 08-15 UTC (London) and 13-19 UTC (NY), in Jan and Jul of 2015-2021.
- R columns use the larger of the London/NY cost (conservative). Cash-session column: cost / (0.5 x D1 ATR).
  ASSUMPTION: same cost for all symbols whatever their own cash session (the fixed spreads do not vary by
  hour; only the 5 table symbols do).

## Table

| Symbol | Data range (dev) | Round-trip cost, price (spread + 2 x slip + comm; Ldn / NY) | ATR M15 / H1 / D1 (price) | Cost in R at 1-ATR stop: M15 / H1 / D1 | Cost in R, cash-session trade, stop 0.5 x D1 ATR |
|---|---|---|---|---|---|
| US500 | 2015-01-02 to 2021-09-13 | 0.5672 / 0.5672 (spread 0.39/0.39) | 2.5947 / 5.02 / 29.585 | 0.219 / 0.113 / 0.019 | 0.038 |
| NAS100 | 2015-01-02 to 2021-09-13 | 1.0594 / 1.0594 (spread 0.6/0.6) | 8.2953 / 16.076 / 95.67 | 0.128 / 0.066 / 0.011 | 0.022 |
| US30 | 2019-02-10 to 2021-09-13 | 2.445 / 2.445 (spread 1.2225/1.2225) | 33.94 / 65.77 / 376.22 | 0.072 / 0.037 / 0.006 | 0.013 |
| GER40 | 2015-01-02 to 2020-06-12 | 1.4128 / 1.4128 (spread 0.7064/0.7064) | 19.083 / 38.009 / 172.45 | 0.074 / 0.037 / 0.008 | 0.016 |
| UK100 | 2015-01-02 to 2021-09-13 | 1.8922 / 1.8922 (spread 0.9461/0.9461) | 9.5581 / 18.892 / 86.151 | 0.198 / 0.100 / 0.022 | 0.044 |
| EU50 | 2015-01-02 to 2018-12-14 | 1.126 / 1.126 (spread 0.56302/0.56302) | 5.3912 / 11.159 / 48.459 | 0.209 / 0.101 / 0.023 | 0.046 |
| JP225 | 2015-01-02 to 2021-09-13 | 6.4257 / 6.4257 (spread 3.2128/3.2128) | 27.209 / 59.719 / 330.14 | 0.236 / 0.108 / 0.019 | 0.039 |
| XAUUSD | 2015-01-02 to 2021-09-13 | 0.30263 / 0.29763 (spread 0.225/0.22) | 1.5926 / 3.4384 / 15.753 | 0.190 / 0.088 / 0.019 | 0.038 |
| XAGUSD | 2015-01-02 to 2021-09-13 | 0.02579 / 0.02579 (spread 0.012777/0.012777) | 0.03732 / 0.079658 / 0.36181 | 0.691 / 0.324 / 0.071 | 0.143 |
| EURUSD | 2015-01-02 to 2021-09-13 | 8.9168e-05 / 8.9168e-05 (spread 1.9584e-05/1.9584e-05) | 0.00082334 / 0.0015067 / 0.0080176 | 0.108 / 0.059 / 0.011 | 0.022 |
| GBPUSD | 2015-01-02 to 2021-09-13 | 0.0001991 / 0.0001991 (spread 0.00011/0.00011) | 0.0011742 / 0.0020963 / 0.01106 | 0.170 / 0.095 / 0.018 | 0.036 |
| USDJPY | 2015-01-02 to 2021-09-13 | 0.01209 / 0.01209 (spread 0.0020892/0.0020892) | 0.07013 / 0.14035 / 0.75528 | 0.172 / 0.086 / 0.016 | 0.032 |
| AUDUSD | 2015-01-02 to 2021-09-13 | 9.1542e-05 / 9.1542e-05 (spread 2.0771e-05/2.0771e-05) | 0.00065853 / 0.0012982 / 0.0067264 | 0.139 / 0.071 / 0.014 | 0.027 |
| USDCAD | 2015-01-02 to 2021-09-13 | 0.00012743 / 0.00012743 (spread 2.824e-05/2.824e-05) | 0.00090662 / 0.0016935 / 0.008959 | 0.141 / 0.075 / 0.014 | 0.028 |
| EURGBP | 2015-01-02 to 2021-09-13 | 0.00011864 / 0.00011864 (spread 4.0482e-05/4.0482e-05) | 0.00069587 / 0.001247 / 0.0066976 | 0.170 / 0.095 / 0.018 | 0.035 |
| GBPJPY | 2015-01-02 to 2021-09-13 | 0.045159 / 0.044659 (spread 0.0335/0.033) | 0.14702 / 0.27289 / 1.3887 | 0.307 / 0.165 / 0.033 | 0.065 |
| USOIL | 2015-01-02 to 2021-09-13 | 0.084406 / 0.084406 (spread 0.042203/0.042203) | 0.16116 / 0.29447 / 1.6449 | 0.524 / 0.287 / 0.051 | 0.103 |

## Caveats

- Costs are today's FTMO spreads applied to 2015-2021 (scaled down by price level for non-table symbols);
  real 2015-2019 retail spreads were mostly wider. Treat the R values as lower bounds for the early years.
- Gaps in the histdata cache: GER40 ends 2020-06-12, EU50 ends 2018-12-14, US30 exists only from 2019-02-10
  (MT5), USOIL has 205 MT5 days (rest histdata). No requested symbol is missing entirely.
- The spread table's GBPUSD values for 2020-21 are 0.0005 in NY hours 0-12 (about 5 x the other years):
  looks like an artefact of the median; it inflates the GBPUSD median cost across the dev years (spread
  0.00011 median shown). Not corrected here.
- US500/NAS100 table spreads are flat across hours (0.39 / 0.6); hour dependence is mainly visible in
  GBPJPY (London 0.034 vs NY 0.033 within the median) and in the rollover hours, which both windows exclude.
- Data cache is bid-only for histdata; no real dev-period ask exists, so dev-period spread is a model, not a measurement.
