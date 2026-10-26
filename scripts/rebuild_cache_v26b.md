# V2.6b cache rebuild queue (not executed by Codex)

Run from the repository with the project virtual environment active. Stop other cache writers.
The measurements are in results/clock_check_histdata.md and results/clock_check_mt5.md.

## Stage 1: histdata

Add these jobs, then run `python -m backtester.tools.queue run --drain` and verify ALL stage 1 jobs succeeded before adding stage 2.
Each symbol imports all neighbouring years in ONE call, completing January 1 across file boundaries.
Duplicate CSV/zip periods below were compared byte-for-byte after normalizing newlines; the plain CSV is selected.
The continuity limit is 25%; an unexplained jump stops that symbol before any cache writes. Do not raise the limit to bypass a wrong instrument.

```powershell
python -m backtester.tools.queue add --name v26b-histdata-AUDUSD -- backtester.data.histdata "data/raw/histdata/AUDUSD/HISTDATA_COM_MT_AUDUSD_M1_2015.zip" "data/raw/histdata/AUDUSD/HISTDATA_COM_MT_AUDUSD_M1_2016.zip" "data/raw/histdata/AUDUSD/HISTDATA_COM_MT_AUDUSD_M1_2017.zip" "data/raw/histdata/AUDUSD/HISTDATA_COM_MT_AUDUSD_M1_2018.zip" "data/raw/histdata/AUDUSD/HISTDATA_COM_MT_AUDUSD_M1_2019.zip" "data/raw/histdata/AUDUSD/HISTDATA_COM_MT_AUDUSD_M1_2020.zip" "data/raw/histdata/AUDUSD/HISTDATA_COM_MT_AUDUSD_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-DXY -- backtester.data.histdata "data/raw/histdata/DXY/HISTDATA_COM_MT_UDXUSD_M1_2015.zip" "data/raw/histdata/DXY/HISTDATA_COM_MT_UDXUSD_M1_2016.zip" "data/raw/histdata/DXY/HISTDATA_COM_MT_UDXUSD_M1_2017.zip" "data/raw/histdata/DXY/HISTDATA_COM_MT_UDXUSD_M1_2018.zip" "data/raw/histdata/DXY/HISTDATA_COM_MT_UDXUSD_M1_2019.zip" "data/raw/histdata/DXY/HISTDATA_COM_MT_UDXUSD_M1_2020.zip" "data/raw/histdata/DXY/HISTDATA_COM_MT_UDXUSD_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-EU50 -- backtester.data.histdata "data/raw/histdata/EU50/HISTDATA_COM_MT_ETXEUR_M1_2015.zip" "data/raw/histdata/EU50/HISTDATA_COM_MT_ETXEUR_M1_2016.zip" "data/raw/histdata/EU50/HISTDATA_COM_MT_ETXEUR_M1_2017.zip" "data/raw/histdata/EU50/HISTDATA_COM_MT_ETXEUR_M1_2018.zip" "data/raw/histdata/EU50/HISTDATA_COM_MT_ETXEUR_M1_2019.zip"
python -m backtester.tools.queue add --name v26b-histdata-EURGBP -- backtester.data.histdata "data/raw/histdata/EURGBP/HISTDATA_COM_MT_EURGBP_M1_2015.zip" "data/raw/histdata/EURGBP/HISTDATA_COM_MT_EURGBP_M1_2016.zip" "data/raw/histdata/EURGBP/HISTDATA_COM_MT_EURGBP_M1_2017.zip" "data/raw/histdata/EURGBP/HISTDATA_COM_MT_EURGBP_M1_2018.zip" "data/raw/histdata/EURGBP/HISTDATA_COM_MT_EURGBP_M1_2019.zip" "data/raw/histdata/EURGBP/HISTDATA_COM_MT_EURGBP_M1_2020.zip" "data/raw/histdata/EURGBP/HISTDATA_COM_MT_EURGBP_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-EURJPY -- backtester.data.histdata "data/raw/histdata/EURJPY/HISTDATA_COM_MT_EURJPY_M1_2015.zip" "data/raw/histdata/EURJPY/HISTDATA_COM_MT_EURJPY_M1_2016.zip" "data/raw/histdata/EURJPY/HISTDATA_COM_MT_EURJPY_M1_2017.zip" "data/raw/histdata/EURJPY/HISTDATA_COM_MT_EURJPY_M1_2018.zip" "data/raw/histdata/EURJPY/HISTDATA_COM_MT_EURJPY_M1_2019.zip" "data/raw/histdata/EURJPY/HISTDATA_COM_MT_EURJPY_M1_2020.zip" "data/raw/histdata/EURJPY/HISTDATA_COM_MT_EURJPY_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-EURUSD -- backtester.data.histdata "data/raw/histdata/EURUSD/HISTDATA_COM_MT_EURUSD_M1_2015.zip" "data/raw/histdata/EURUSD/HISTDATA_COM_MT_EURUSD_M1_2016.zip" "data/raw/histdata/EURUSD/HISTDATA_COM_MT_EURUSD_M1_2017.zip" "data/raw/histdata/EURUSD/HISTDATA_COM_MT_EURUSD_M1_2018.zip" "data/raw/histdata/EURUSD/HISTDATA_COM_MT_EURUSD_M1_2019.zip" "data/raw/histdata/EURUSD/HISTDATA_COM_MT_EURUSD_M1_2020.zip" "data/raw/histdata/EURUSD/HISTDATA_COM_MT_EURUSD_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-GBPJPY -- backtester.data.histdata "data/raw/histdata/GBPJPY/HISTDATA_COM_MT_GBPJPY_M1_2015.zip" "data/raw/histdata/GBPJPY/HISTDATA_COM_MT_GBPJPY_M1_2016.zip" "data/raw/histdata/GBPJPY/HISTDATA_COM_MT_GBPJPY_M1_2017.zip" "data/raw/histdata/GBPJPY/HISTDATA_COM_MT_GBPJPY_M1_2018.zip" "data/raw/histdata/GBPJPY/HISTDATA_COM_MT_GBPJPY_M1_2019.zip" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_2020.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_2021.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_2022.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_2023.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_2024.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_2025.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_202601.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_202602.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_202603.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_202604.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_202605.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_202606.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_202607.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_202608.csv" "data/raw/histdata/GBPJPY/DAT_MT_GBPJPY_M1_202609.csv"
python -m backtester.tools.queue add --name v26b-histdata-GBPUSD -- backtester.data.histdata "data/raw/histdata/GBPUSD/HISTDATA_COM_MT_GBPUSD_M1_2015.zip" "data/raw/histdata/GBPUSD/HISTDATA_COM_MT_GBPUSD_M1_2016.zip" "data/raw/histdata/GBPUSD/HISTDATA_COM_MT_GBPUSD_M1_2017.zip" "data/raw/histdata/GBPUSD/HISTDATA_COM_MT_GBPUSD_M1_2018.zip" "data/raw/histdata/GBPUSD/HISTDATA_COM_MT_GBPUSD_M1_2019.zip" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_2020.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_2021.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_2022.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_2023.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_2024.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_2025.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_202601.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_202602.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_202603.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_202604.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_202605.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_202606.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_202607.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_202608.csv" "data/raw/histdata/GBPUSD/DAT_MT_GBPUSD_M1_202609.csv"
python -m backtester.tools.queue add --name v26b-histdata-GER40 -- backtester.data.histdata "data/raw/histdata/GER40/HISTDATA_COM_MT_GRXEUR_M1_2015.zip" "data/raw/histdata/GER40/HISTDATA_COM_MT_GRXEUR_M1_2016.zip" "data/raw/histdata/GER40/HISTDATA_COM_MT_GRXEUR_M1_2017.zip" "data/raw/histdata/GER40/HISTDATA_COM_MT_GRXEUR_M1_2018.zip" "data/raw/histdata/GER40/HISTDATA_COM_MT_GRXEUR_M1_2019.zip" "data/raw/histdata/GER40/HISTDATA_COM_MT_GRXEUR_M1_2020.zip" "data/raw/histdata/GER40/HISTDATA_COM_MT_GRXEUR_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-JP225 -- backtester.data.histdata "data/raw/histdata/JP225/HISTDATA_COM_MT_JPXJPY_M1_2015.zip" "data/raw/histdata/JP225/HISTDATA_COM_MT_JPXJPY_M1_2016.zip" "data/raw/histdata/JP225/HISTDATA_COM_MT_JPXJPY_M1_2017.zip" "data/raw/histdata/JP225/HISTDATA_COM_MT_JPXJPY_M1_2018.zip" "data/raw/histdata/JP225/HISTDATA_COM_MT_JPXJPY_M1_2019.zip" "data/raw/histdata/JP225/HISTDATA_COM_MT_JPXJPY_M1_2020.zip" "data/raw/histdata/JP225/HISTDATA_COM_MT_JPXJPY_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-NAS100 -- backtester.data.histdata "data/raw/histdata/NAS100/HISTDATA_COM_MT_NSXUSD_M1_2015.zip" "data/raw/histdata/NAS100/HISTDATA_COM_MT_NSXUSD_M1_2016.zip" "data/raw/histdata/NAS100/HISTDATA_COM_MT_NSXUSD_M1_2017.zip" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_2018.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_2019.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_2020.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_2021.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_2022.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_2023.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_2024.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_2025.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_202601.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_202602.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_202603.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_202604.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_202605.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_202606.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_202607.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_202608.csv" "data/raw/histdata/NAS100/DAT_MT_NSXUSD_M1_202609.csv"
python -m backtester.tools.queue add --name v26b-histdata-NZDUSD -- backtester.data.histdata "data/raw/histdata/NZDUSD/HISTDATA_COM_MT_NZDUSD_M1_2015.zip" "data/raw/histdata/NZDUSD/HISTDATA_COM_MT_NZDUSD_M1_2016.zip" "data/raw/histdata/NZDUSD/HISTDATA_COM_MT_NZDUSD_M1_2017.zip" "data/raw/histdata/NZDUSD/HISTDATA_COM_MT_NZDUSD_M1_2018.zip" "data/raw/histdata/NZDUSD/HISTDATA_COM_MT_NZDUSD_M1_2019.zip" "data/raw/histdata/NZDUSD/HISTDATA_COM_MT_NZDUSD_M1_2020.zip" "data/raw/histdata/NZDUSD/HISTDATA_COM_MT_NZDUSD_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-UK100 -- backtester.data.histdata "data/raw/histdata/UK100/HISTDATA_COM_MT_UKXGBP_M1_2015.zip" "data/raw/histdata/UK100/HISTDATA_COM_MT_UKXGBP_M1_2016.zip" "data/raw/histdata/UK100/HISTDATA_COM_MT_UKXGBP_M1_2017.zip" "data/raw/histdata/UK100/HISTDATA_COM_MT_UKXGBP_M1_2018.zip" "data/raw/histdata/UK100/HISTDATA_COM_MT_UKXGBP_M1_2019.zip" "data/raw/histdata/UK100/HISTDATA_COM_MT_UKXGBP_M1_2020.zip" "data/raw/histdata/UK100/HISTDATA_COM_MT_UKXGBP_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-UKOIL -- backtester.data.histdata "data/raw/histdata/UKOIL/HISTDATA_COM_MT_BCOUSD_M1_2015.zip" "data/raw/histdata/UKOIL/HISTDATA_COM_MT_BCOUSD_M1_2016.zip" "data/raw/histdata/UKOIL/HISTDATA_COM_MT_BCOUSD_M1_2017.zip" "data/raw/histdata/UKOIL/HISTDATA_COM_MT_BCOUSD_M1_2018.zip" "data/raw/histdata/UKOIL/HISTDATA_COM_MT_BCOUSD_M1_2019.zip" "data/raw/histdata/UKOIL/HISTDATA_COM_MT_BCOUSD_M1_2020.zip" "data/raw/histdata/UKOIL/HISTDATA_COM_MT_BCOUSD_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-US500 -- backtester.data.histdata "data/raw/histdata/US500/HISTDATA_COM_MT_SPXUSD_M1_2015.zip" "data/raw/histdata/US500/HISTDATA_COM_MT_SPXUSD_M1_2016.zip" "data/raw/histdata/US500/HISTDATA_COM_MT_SPXUSD_M1_2017.zip" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_2018.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_2019.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_2020.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_2021.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_2022.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_2023.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_2024.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_2025.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_202601.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_202602.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_202603.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_202604.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_202605.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_202606.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_202607.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_202608.csv" "data/raw/histdata/US500/DAT_MT_SPXUSD_M1_202609.csv"
python -m backtester.tools.queue add --name v26b-histdata-USDCAD -- backtester.data.histdata "data/raw/histdata/USDCAD/HISTDATA_COM_MT_USDCAD_M1_2015.zip" "data/raw/histdata/USDCAD/HISTDATA_COM_MT_USDCAD_M1_2016.zip" "data/raw/histdata/USDCAD/HISTDATA_COM_MT_USDCAD_M1_2017.zip" "data/raw/histdata/USDCAD/HISTDATA_COM_MT_USDCAD_M1_2018.zip" "data/raw/histdata/USDCAD/HISTDATA_COM_MT_USDCAD_M1_2019.zip" "data/raw/histdata/USDCAD/HISTDATA_COM_MT_USDCAD_M1_2020.zip" "data/raw/histdata/USDCAD/HISTDATA_COM_MT_USDCAD_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-USDCHF -- backtester.data.histdata "data/raw/histdata/USDCHF/HISTDATA_COM_MT_USDCHF_M1_2015.zip" "data/raw/histdata/USDCHF/HISTDATA_COM_MT_USDCHF_M1_2016.zip" "data/raw/histdata/USDCHF/HISTDATA_COM_MT_USDCHF_M1_2017.zip" "data/raw/histdata/USDCHF/HISTDATA_COM_MT_USDCHF_M1_2018.zip" "data/raw/histdata/USDCHF/HISTDATA_COM_MT_USDCHF_M1_2019.zip" "data/raw/histdata/USDCHF/HISTDATA_COM_MT_USDCHF_M1_2020.zip" "data/raw/histdata/USDCHF/HISTDATA_COM_MT_USDCHF_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-USDJPY -- backtester.data.histdata "data/raw/histdata/USDJPY/HISTDATA_COM_MT_USDJPY_M1_2015.zip" "data/raw/histdata/USDJPY/HISTDATA_COM_MT_USDJPY_M1_2016.zip" "data/raw/histdata/USDJPY/HISTDATA_COM_MT_USDJPY_M1_2017.zip" "data/raw/histdata/USDJPY/HISTDATA_COM_MT_USDJPY_M1_2018.zip" "data/raw/histdata/USDJPY/HISTDATA_COM_MT_USDJPY_M1_2019.zip" "data/raw/histdata/USDJPY/HISTDATA_COM_MT_USDJPY_M1_2020.zip" "data/raw/histdata/USDJPY/HISTDATA_COM_MT_USDJPY_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-USOIL -- backtester.data.histdata "data/raw/histdata/USOIL/HISTDATA_COM_MT_WTIUSD_M1_2015.zip" "data/raw/histdata/USOIL/HISTDATA_COM_MT_WTIUSD_M1_2016.zip" "data/raw/histdata/USOIL/HISTDATA_COM_MT_WTIUSD_M1_2017.zip" "data/raw/histdata/USOIL/HISTDATA_COM_MT_WTIUSD_M1_2018.zip" "data/raw/histdata/USOIL/HISTDATA_COM_MT_WTIUSD_M1_2019.zip" "data/raw/histdata/USOIL/HISTDATA_COM_MT_WTIUSD_M1_2020.zip" "data/raw/histdata/USOIL/HISTDATA_COM_MT_WTIUSD_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-XAGUSD -- backtester.data.histdata "data/raw/histdata/XAGUSD/HISTDATA_COM_MT_XAGUSD_M1_2015.zip" "data/raw/histdata/XAGUSD/HISTDATA_COM_MT_XAGUSD_M1_2016.zip" "data/raw/histdata/XAGUSD/HISTDATA_COM_MT_XAGUSD_M1_2017.zip" "data/raw/histdata/XAGUSD/HISTDATA_COM_MT_XAGUSD_M1_2018.zip" "data/raw/histdata/XAGUSD/HISTDATA_COM_MT_XAGUSD_M1_2019.zip" "data/raw/histdata/XAGUSD/HISTDATA_COM_MT_XAGUSD_M1_2020.zip" "data/raw/histdata/XAGUSD/HISTDATA_COM_MT_XAGUSD_M1_2021.zip"
python -m backtester.tools.queue add --name v26b-histdata-XAUUSD -- backtester.data.histdata "data/raw/histdata/XAUUSD/HISTDATA_COM_MT_XAUUSD_M1_2015.zip" "data/raw/histdata/XAUUSD/HISTDATA_COM_MT_XAUUSD_M1_2016.zip" "data/raw/histdata/XAUUSD/HISTDATA_COM_MT_XAUUSD_M1_2017.zip" "data/raw/histdata/XAUUSD/HISTDATA_COM_MT_XAUUSD_M1_2018.zip" "data/raw/histdata/XAUUSD/HISTDATA_COM_MT_XAUUSD_M1_2019.zip" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_2020.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_2021.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_2022.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_2023.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_2024.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_2025.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_202601.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_202602.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_202603.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_202604.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_202605.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_202606.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_202607.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_202608.csv" "data/raw/histdata/XAUUSD/DAT_MT_XAUUSD_M1_202609.csv"
```

Identical duplicate periods:
- GBPJPY 2020-01-01: DAT_MT_GBPJPY_M1_2020.csv, HISTDATA_COM_MT_GBPJPY_M1_2020.zip
- GBPUSD 2020-01-01: DAT_MT_GBPUSD_M1_2020.csv, HISTDATA_COM_MT_GBPUSD_M1_2020.zip
- NAS100 2018-01-01: DAT_MT_NSXUSD_M1_2018.csv, HISTDATA_COM_MT_NSXUSD_M1_2018.zip
- NAS100 2019-01-01: DAT_MT_NSXUSD_M1_2019.csv, HISTDATA_COM_MT_NSXUSD_M1_2019.zip
- NAS100 2020-01-01: DAT_MT_NSXUSD_M1_2020.csv, HISTDATA_COM_MT_NSXUSD_M1_2020.zip
- US500 2018-01-01: DAT_MT_SPXUSD_M1_2018.csv, HISTDATA_COM_MT_SPXUSD_M1_2018.zip
- US500 2019-01-01: DAT_MT_SPXUSD_M1_2019.csv, HISTDATA_COM_MT_SPXUSD_M1_2019.zip
- US500 2020-01-01: DAT_MT_SPXUSD_M1_2020.csv, HISTDATA_COM_MT_SPXUSD_M1_2020.zip
- XAUUSD 2020-01-01: DAT_MT_XAUUSD_M1_2020.csv, HISTDATA_COM_MT_XAUUSD_M1_2020.zip

## Stage 2: offline MT5 repair

Only add after stage 1 has fully completed. No MT5 connection or download is used.
Original affected days are retained in data/cache/mt5/_v26b_original/. Keep these backups.
Per-day proofs, shifts and exclusions are written to data/cache/mt5/_v26b_reports/SYMBOL.json.
The jobs may require substantial backup disk space. Reruns read retained originals and never shift timestamps twice.
Pre-2020 days without a strong direct price match to corrected histdata are excluded (including MT5-only symbols and unavailable pre-2015 references).
Sparse weekdays in any year are excluded at <50% of that symbol/year median. Empty weekends remain closed days.
2020+ clock conversion is unchanged; XAUUSD 2020/March 2021 evidence needs a separate decision.

```powershell
python -m backtester.tools.queue add --name v26b-mt5-AUDUSD -- backtester.tools.cache_repair AUDUSD
python -m backtester.tools.queue add --name v26b-mt5-BTCUSD -- backtester.tools.cache_repair BTCUSD
python -m backtester.tools.queue add --name v26b-mt5-DXY -- backtester.tools.cache_repair DXY
python -m backtester.tools.queue add --name v26b-mt5-ETHUSD -- backtester.tools.cache_repair ETHUSD
python -m backtester.tools.queue add --name v26b-mt5-EU50 -- backtester.tools.cache_repair EU50
python -m backtester.tools.queue add --name v26b-mt5-EURGBP -- backtester.tools.cache_repair EURGBP
python -m backtester.tools.queue add --name v26b-mt5-EURJPY -- backtester.tools.cache_repair EURJPY
python -m backtester.tools.queue add --name v26b-mt5-EURUSD -- backtester.tools.cache_repair EURUSD
python -m backtester.tools.queue add --name v26b-mt5-GBPJPY -- backtester.tools.cache_repair GBPJPY
python -m backtester.tools.queue add --name v26b-mt5-GBPUSD -- backtester.tools.cache_repair GBPUSD
python -m backtester.tools.queue add --name v26b-mt5-GER40 -- backtester.tools.cache_repair GER40
python -m backtester.tools.queue add --name v26b-mt5-JP225 -- backtester.tools.cache_repair JP225
python -m backtester.tools.queue add --name v26b-mt5-NAS100 -- backtester.tools.cache_repair NAS100
python -m backtester.tools.queue add --name v26b-mt5-NATGAS -- backtester.tools.cache_repair NATGAS
python -m backtester.tools.queue add --name v26b-mt5-NZDUSD -- backtester.tools.cache_repair NZDUSD
python -m backtester.tools.queue add --name v26b-mt5-UK100 -- backtester.tools.cache_repair UK100
python -m backtester.tools.queue add --name v26b-mt5-UKOIL -- backtester.tools.cache_repair UKOIL
python -m backtester.tools.queue add --name v26b-mt5-US2000 -- backtester.tools.cache_repair US2000
python -m backtester.tools.queue add --name v26b-mt5-US30 -- backtester.tools.cache_repair US30
python -m backtester.tools.queue add --name v26b-mt5-US500 -- backtester.tools.cache_repair US500
python -m backtester.tools.queue add --name v26b-mt5-USDCAD -- backtester.tools.cache_repair USDCAD
python -m backtester.tools.queue add --name v26b-mt5-USDCHF -- backtester.tools.cache_repair USDCHF
python -m backtester.tools.queue add --name v26b-mt5-USDJPY -- backtester.tools.cache_repair USDJPY
python -m backtester.tools.queue add --name v26b-mt5-USOIL -- backtester.tools.cache_repair USOIL
python -m backtester.tools.queue add --name v26b-mt5-XAGUSD -- backtester.tools.cache_repair XAGUSD
python -m backtester.tools.queue add --name v26b-mt5-XAUUSD -- backtester.tools.cache_repair XAUUSD
```

Then drain the queue again. Opus runs the data check and the 2023 golden check afterwards; stop and report any golden change.
No raw files are modified. GER40 histdata UTC days from 2020-06-15 are removed by its stage 1 job.

## Cleanup audit

The named stray hook file, .vscode/ and data/cache/dukascopy/ were absent. Nothing was removed.

## Validation commands (Opus after rebuild)

```powershell
python -m backtester.tools.check AUDUSD DXY EU50 EURGBP EURJPY EURUSD GBPJPY GBPUSD GER40 JP225 NAS100 NZDUSD UK100 UKOIL US500 USDCAD USDCHF USDJPY USOIL XAGUSD XAUUSD > results/data_check_v26b.log 2>&1
python -m backtester.tools.golden --check > results/golden_v26b.log 2>&1
```

Do not accept changed golden lists. Development-period results may change as expected.
