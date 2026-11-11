# Brief: Phase 3 clean-up inventory (read-only)

Context: V2 of the backtester is being cleaned up. ALL strategies under
`src/backtester/strategy/` (7 incl. gap_momentum) and their tests stay. Trading rules,
defaults (costs, sweep options, spread table, data split) and test expectations must not
change. Nothing is deleted yet; you only produce the inventory.

## Do

1. For every module in `src/backtester/tools/` (incl. `archive/`): who imports it
   (`rg "tools\.<name>|from .<name>|<name> import" src tests`), is it a reusable tool (data,
   research runner, Monte Carlo, portfolio...) or a one-off study whose result is already
   recorded in `docs/ROADMAP.md` / `knowledge/`? Note import chains: an archive module that a
   live module imports cannot simply go.
2. Duplicate code: look for functions or blocks repeated across `tools/`, `analytics/`,
   `runner.py`, `run.py`, `ui/` (e.g. several grid runners, metric helpers, CSV/JSON writers,
   date parsing). Name the files and functions, and which copy should survive.
3. Other candidates: `restart_app.bat`, `docs/portfolio_first.json`, `docs/ui-mockups/`,
   `.claude/skills/*` (ponytail*, backtester-testing, backtest-evaluation-research), `README.md`,
   `research/grids/*.toml`, stray files anywhere in git.

## Answer (markdown, max ~60 table rows)

A table: `item | verdict (keep / delete / merge / rewrite) | reason (one line) | depends on`.
Then a short list "risky: needs Opus or the user" for anything where deleting could change a
test, a default, a trading rule or a result. Do not change any file.
