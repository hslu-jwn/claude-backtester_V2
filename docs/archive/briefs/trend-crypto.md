# Brief: pre-register hypothesis "crypto trend following" (strategy 4 on BTCUSD / ETHUSD); no code change

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). Do NOT run the
grid. Spec: `docs/strategy-trend-following.md` (read the signals, timeframes, stop and swap sections).

## Why

Strategy 4 never ran on crypto. Published: time-series momentum is strong in crypto at 1-4 week horizons
(Liu and Tsyvinski, "Risks and Returns of Cryptocurrency", RFS 2021; Liu, Tsyvinski, Wu, JF 2022). Costs on
FTMO BTCUSD / ETHUSD: spread about 1.0 / 0.66 at reference price (tiny vs daily ranges), commission 3.25 bp
per side, swap -30 %/year on both sides (`engine/costs.py`), triple on Friday: about 8 bp per night held.

## Write (only these files)

1. `research/grids/trend_following_crypto.toml`: symbols BTCUSD (primary), ETHUSD (breadth); data from
   the cache (BTCUSD MT5 from 2017, ETHUSD from 2018; development ends 2021-09-13). Daily timeframe (or the
   strategy's D1 equivalent; check the config). At most 12 cells, chosen before any run: signal
   {breakout, momentum} x period {20, 55} x stop (the spec's ATR stop) {2, 4} -> 8 cells, plus nothing
   else. Primary: breakout 20, stop 4 ATR. Diagnostics off (monkeys / sensitivity / entry_screen false).
   Swap on (as the spec's default).
2. A new section in `docs/strategy-trend-following.md`: "Hypothesis C1: crypto trend following
   (pre-registered 2026-11-10, before any run)": source, mechanism, costs above, the grid and primary,
   and **gates fixed now**: primary BTCUSD net R > 0 at normal costs and with every cost doubled (swap
   included); net R > 0 in both halves of the BTCUSD development period; ETHUSD net R > 0 (breadth, 1 of
   1, correlated); without the 5 best trades net R > 0; bootstrap 2.5 % of mean net R per trade > 0 (blocks
   of 5, 10,000 resamples, seed 2026110); min 40 trades; long and short reported separately (the 2017 and
   2020-21 bull runs); integrity: missing exit candles. Note the multiple testing (8 cells, hypothesis
   count of the program).
3. Say which existing gates tool computes these (e.g. `tools/timed_hold_gates.py` pooled / per-symbol
   functions, or the runner's scorecard) and the exact command; if none fits, list what is missing.

Report files and the command. `python -m pytest tests/tools -q -k grid` or the grid-loading test green.
