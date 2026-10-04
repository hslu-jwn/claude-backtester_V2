# backtester-claude

Rule-based price-action strategy backtester (session zones, FVGs, order blocks, BOS,
liquidity sweeps) with a strict **no-lookahead** guarantee, an FTMO challenge simulator,
and a TradingView-style Plotly/Dash interface.

- Trading rules: [`docs/`](docs/) (source of truth)
- Architecture and build order: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Working with Claude Code: [`CLAUDE.md`](CLAUDE.md)

## Setup

```bash
git clone https://github.com/hslu-jwn/backtester-claude.git
cd backtester-claude
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -e ".[dev,ui]"
pytest
```

Historical data comes from Dukascopy, downloaded into a local cache
(`pip install -e ".[data]"`, see `docs/ROADMAP.md` › Phase 0). MetaTrader 5 (FTMO) is used
for feed comparison and later live trading: `pip install -e ".[mt5]"` and the login in `.env`. CSV files in `data/raw/<SYMBOL>_<TF>.csv` with the header
`timestamp,open,high,low,close[,volume]` (UTC) also work. Data files are not committed.

## Status

Core (candles, lookahead-safe views, multi-timeframe clock, CSV loader) is implemented and
tested. Everything else is a documented stub; next steps are in `docs/ROADMAP.md`.
