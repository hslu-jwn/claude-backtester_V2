# Brief: I-145 maker-first fill model for Strategy 20 (Codex terra)

Rules: `knowledge/ideas.md` › I-145 (read it fully; it is the spec, do not change it). Pattern to follow:
`research/screens/2026-11-15_fb273_maker_fill.py` (the older 4-symbol version).

## Write

1. `research/screens/2026-11-26_i145_fill_model.py` with subcommands:
   - `orders`: build the order list from Strategy 20's frozen book. Use `backtester.tools.crypto_flow` (`load`,
     `compute_weeks`, the default config, not `--liquid`) to get each week's legs; derive the Monday orders as in the
     card (leave / enter / flip; a flip is one order). Write `results/i145/orders.csv` (monday, symbol, side +1 buy
     / -1 sell, p0 = Sunday daily close, qvol30 = 30-bar median quote volume before the Monday). Mondays: every
     Monday of 2023 and 2026-04-27 .. 2026-10-19. Needs the first Monday's previous book: use the week before.
   - `size`: S3 listing (`backtester.data.binance_wide._listing`, prefix `data/futures/um/daily/aggTrades/<SYM>/`)
     for every (symbol, Monday) in orders.csv; print the total zip size in GB and the count of missing files. No
     download.
   - `download`: fetch the missing Monday files from `binance_wide.CDN + key` into
     `data/cache/binance_aggtrades/<SYM>-aggTrades-<YYYY-MM-DD>.zip` (same names as FB-273; skip existing; write to
     a `.part` file then rename; print progress every 100 files).
   - `run`: the arms, the decision line and the reported items exactly as in the card. Read only the columns
     price, transact_time, is_buyer_maker, and only rows with transact_time < Monday 00:00 + 3 h (filter while
     reading in chunks to keep memory low). Saving t clustered by Monday (mean of per-Monday means / se).
2. `tests/tools/test_i145_fill_model.py`: hand-built trade frames (no network, no real cache): taker fill with the
   1 s latency (a trade at 00:00:00.500 is skipped); maker fill needs at least 1 tick through P0 (a print exactly at
   P0 does not fill; with the 2-tick rule a 1-tick print does not fill); unfilled maker pays taker after the window;
   tick inferred from the price steps; order derivation (leave, enter, flip, stay) from two hand-made books;
   cost sign for buys and sells.

## Limits

Do not run `download` or `run` (Opus runs them). Do not touch `src/`, other screens, `docs/`, `knowledge/`, the
ledger. No commits, no branches, no long-running processes. Done = the new tests pass, `ruff check` clean on both new
files, `python research/screens/2026-11-26_i145_fill_model.py --help` style usage prints. Report the files and test
output. If a card rule is unclear, stop and write the question in your answer; do not guess.
