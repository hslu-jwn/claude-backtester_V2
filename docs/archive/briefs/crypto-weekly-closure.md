# Brief: missing Saturdays in the BTCUSD / ETHUSD MT5 cache must not split research segments

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). Test first; never
weaken a test. No lookahead. Decision by Opus (2026-11-10, a data-handling rule, no cost default touched):
a regular weekly closure of the instrument is a market closure, like the FX weekend, not a data gap.

Facts: `data/cache/mt5/BTCUSD/2019/` has no Saturday files (FTMO crypto CFDs did not trade on Saturdays
then; 2022 has all 365 days). The research runner splits a symbol's development period into segments at
cache gaps and restarts indicators per segment (Codex, `results/ai/*fix_d1_replay*.md`: BTCUSD 230
segments, ETHUSD 190, none longer than 13 days), so `research/grids/trend_following_crypto*.toml` (D1,
20 / 55-day lookbacks) produce 0 trades.

Task: find where segments are cut (runner / sources / cache adapter) and how FX weekends avoid a cut. Make
a missing day that is a regular closure for that symbol (here: Saturday for BTCUSD / ETHUSD in years where
the cache has no Saturdays, or the smallest general rule you find that also keeps FX behaviour identical)
not cut a segment. Tests: a hand-built crypto-like cache with Saturdays missing gives one segment; a real
multi-day hole still cuts; FX unchanged. Golden lists must stay identical (run the golden tests; report).
Then run `python -m backtester.tools.research research/grids/trend_following_crypto.toml --dev-only` and the
`_eth` grid, and report segments and per-cell trades / net R. `python -m pytest tests/data tests/tools
tests/golden tests/test_runner*.py -q` green, ruff clean. Report root cause, files, tests, run output.
