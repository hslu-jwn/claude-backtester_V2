# EIA petroleum-inventory release candidate scan

Date: 2026-11-02  
Decision: **reject for an OHLC-only day-flat strategy; the supported directional findings require
inventory-surprise inputs or trade in the excluded final half-hour**.

## Evidence

- Shiyu Ye and Berna Karali, “The Informational Content of Inventory Announcements: Intraday
  Evidence from Crude Oil Futures Market,” *Energy Economics* 59, 2016, 349–364,
  [article record and abstract opened](https://doi.org/10.1016/j.eneco.2016.08.011). Unexpected API
  and EIA inventory changes have an immediate inverse effect on crude-oil futures returns; EIA
  effects last roughly 60 minutes. The signal is defined from Reuters forecasts, API releases, EIA
  actuals, and petroleum-product cross-shocks, not OHLC alone.

- Olivier Rousse and Benoît Sévi, “Informed Trading in the WTI Oil Futures Market,” *The Energy
  Journal* 40(2), 2019, 139–160,
  [full working paper opened](https://doi.org/10.5547/01956574.40.2.orou). In 2007–2014 data, days
  with inventories above expectations show a roughly 0.25% pre-release fall and partial reversal
  during the following four hours. The classification uses Bloomberg expectations and the released
  inventory surprise; the authors interpret pre-release order imbalance as informed or superior-
  forecast trading. The paper does not test an OHLC-sign proxy net of costs.

- Sultan Alturki and Alexander Kurov, “Market Inefficiencies Surrounding Energy Announcements,”
  *Journal of Futures Markets* 42(1), 2022,
  [full text opened](https://doi.org/10.1002/fut.22264). A 30-minute post-API futures return predicts
  the return from 60 minutes to one minute before the next EIA release in a 2010–2019 sample of 385
  announcements. Its trading predictor combines the prior evening's API actual with Bloomberg
  consensus and is strongest in a selected low-liquidity subset. API publication is outside the
  permitted same-day OHLC-only input set.

- Zhuzhu Wen, Ivan Indriawan, Donald Lien, and Yahua Xu, “Intraday Return Predictability in the
  Crude Oil Market: The Role of EIA Inventory Announcements,” *The Energy Journal* 44(5), 2023,
  149–172, [accepted manuscript and executive summary opened](https://doi.org/10.5547/01956574.44.4.zwen).
  The 10:30–11:00 return on EIA days positively predicts the final half-hour return. That is an
  OHLC-only event signal, but its target is precisely the excluded final-30-minute anomaly; moving
  the exit earlier is not source-supported.

- U.S. Energy Information Administration, “EIA Information Releases,”
  [official page opened](https://ir.eia.gov/). The Weekly Petroleum Status Report is usually
  released Wednesday at 10:30 ET, with a separate holiday schedule. This supports the event's
  existence but is not yet a versioned historical calendar contract for V2.

## Admission result

USOIL is supported and the scheduled release is an interior-session event, but the published
directional estimands do not produce an admissible fixed rule. Immediate response and later
overreaction depend on the sign and composition of the inventory surprise. The sequential API/EIA
predictor requires API actual and analyst-consensus fields. The only direct OHLC-only continuation
finding trades the final half-hour, which this program excludes. Using the first post-release bar as
a surprise proxy and selecting a 20-, 60-, or 240-minute continuation/reversal horizon would be an
unpublished event-filter grid and would overlap the frozen R-2026-004 shock-response question.

Create no surprise proxy, inventory component, API/EIA, latency, continuation/reversal, or exit-time
grid. Reconsider only if a primary study predefines an interior-session OHLC-only return on modern
WTI data, reports executable costs, and does not depend on the final half-hour or external surprise
fields.
