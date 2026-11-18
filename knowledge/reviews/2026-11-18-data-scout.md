# Free non-price data sets, scout 2026-11-18 (auto decision 54)

One Sonnet web subagent; every URL below was opened by it on 2026-11-18 (API endpoints returned live data). Terms of use
were not read unless stated. Owned data was excluded (see HANDOFF). Background, not rules.

| Data set | URL (opened) | History, frequency | Measures | Use so far |
|---|---|---|---|---|
| NY Fed primary dealer statistics (Treasury / MBS / corporate positions, financing, fails) | https://markets.newyorkfed.org/api/pd/list/timeseries.json | 1998+, weekly (series breaks; latest 2024) | dealer inventory | I-116 card, parked |
| NY Fed SOMA holdings (summary and per CUSIP) | https://markets.newyorkfed.org/api/soma/summary.json | 2003-07+, weekly | Fed QE / QT holdings | none: flow effects ~0.3 bp per operation (D'Amico & King) |
| NY Fed repo / reverse repo operations | https://markets.newyorkfed.org/api/rp/all/all/results/last/2.json | start unverified, daily | liquidity operations | none |
| Treasury auctions (Fiscal Data) | https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query | 1979-11+, per auction | supply dates and sizes | auction cycle already rejected (batch 16) |
| Treasury buybacks (Fiscal Data) | .../v1/accounting/od/buybacks_operations | 2024+ | buyback operations | too short |
| Daily Treasury Statement (TGA, debt) | https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/ | 2005-10+, daily | Treasury cash / liquidity | none (macro, weak power) |
| SEC Form 13F data sets | https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets | 2013-Q2+, quarterly | institutional holdings | I-117 card, closed on power |
| FINRA consolidated short interest | https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest | listed shares free from 2021-06 (checked 2026-11-17) | short positioning | not testable on development |
| FINRA margin statistics | https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics | 1997-01+, monthly | margin debt | none (monthly, low power) |
| DefiLlama stablecoin supply | https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=1 | 2017-11+, daily | stablecoin mint / burn | none yet |

Not found free: daily ETF shares-outstanding history, index-rebalance announcement history, OCC open interest, Cboe
put / call after 2019-10, ICI ETF flows (404).
