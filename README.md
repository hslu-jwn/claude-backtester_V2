# backtester-claude V2

Backtester and research platform for rule-based trading strategies, with a strict
**no-lookahead** guarantee, real costs and swap, Monte Carlo and FTMO / prop-firm simulation,
a research runner with a fixed development / test data split, and a Dash app with a
TradingView Lightweight Charts chart.

- Project rules for people and AI models: [`AGENTS.md`](AGENTS.md) (Claude: [`CLAUDE.md`](CLAUDE.md))
- Trading rules: [`docs/`](docs/) (source of truth); what's next: [`docs/ROADMAP.md`](docs/ROADMAP.md)
- Current state: [`docs/HANDOFF.md`](docs/HANDOFF.md)

## Setup (Windows)

```bash
git clone https://github.com/hslu-jwn/claude-backtester_V2.git
cd claude-backtester_V2
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,ui,data,risk,mt5]"
pytest
python -m backtester.ui.app
```

Market data and results are not in git: copy `data/` and `results/` from the previous PC, or
re-import histdata.com files (`python -m backtester.data.histdata data/raw/histdata/`) and
download MT5 history (`python -m backtester.tools.update_data`). Check the data with
`python -m backtester.tools.check <SYMBOL> ...`.

The MT5 (FTMO demo) login is entered in the app (Settings ⚙ → Trading) and kept in the
Windows Credential Manager, never in a file. Orders are demo-only.

## Status

Built: data import / check / update (histdata, MT5, Binance), chart with replay and
overlays, detectors, 7 strategies, backtest engine with costs and swap, results page, risk
and FTMO simulation (sizer, account simulator, Monte Carlo, adaptive risk), research runner
and Research page, portfolio tool, demo forward-test bot. Step status: `docs/ROADMAP.md`.
