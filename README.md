# backtester-claude

Rule-based price-action strategy backtester (session zones, FVGs, order blocks, BOS,
liquidity sweeps) with a strict **no-lookahead** guarantee, an FTMO challenge simulator,
and a Dash app with a TradingView Lightweight Charts chart.

- Trading rules: [`docs/`](docs/) (source of truth)
- Architecture and build order: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Working with Claude Code: [`CLAUDE.md`](CLAUDE.md)

## Setup

```bash
git clone https://github.com/hslu-jwn/backtester-claude.git
cd backtester-claude
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -e ".[dev,ui,data,risk]"
pytest
```

Historical data comes from **histdata.com** M1 files (MetaTrader format) that you download
yourself into `data/raw/histdata/<SYMBOL>/` (XAUUSD, GBPUSD, GBPJPY, NAS100, US500; histdata's
NSXUSD / SPXUSD files go into `NAS100/` / `US500/`). Import them into the local cache and check
them (`pip install -e ".[data]"`, see `docs/ARCHITECTURE.md` › Data sources):

```bash
python -m backtester.data.histdata data/raw/histdata/
python -m backtester.data.check XAUUSD GBPUSD GBPJPY NAS100 US500
python -m backtester.ui.app
```

Dukascopy is no longer used (its downloader was removed). MetaTrader 5 (FTMO) is used for feed
comparison and later live trading: `pip install -e ".[mt5]"` (Windows only); the login is
entered in the app (Settings ⚙ → Trading) and kept in the Windows Credential Manager, never
in a file. Data files are not committed.

## Status

Built and tested: data import and data check, chart with replay and confluence overlays,
the detectors, strategy 1 (session zone sweep) and strategy 2 (NY Open index sweep)
backtests with a results page, and the settings menu with presets. Not built yet: the risk
and FTMO account simulation (Phase 5). Step status: `docs/ROADMAP.md`.
