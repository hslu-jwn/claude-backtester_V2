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

Price data goes in `data/raw/<SYMBOL>_<TF>.csv` (e.g. `XAUUSD_M5.csv`) with the header
`timestamp,open,high,low,close[,volume]`, timestamps in UTC. Data files are not committed.

## Status

Core (candles, lookahead-safe views, multi-timeframe clock, CSV loader) is implemented and
tested. Everything else is a documented stub; see the build order.
