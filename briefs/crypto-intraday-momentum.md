# Brief: pre-register hypothesis C3 "crypto intraday momentum" (no code if timed_hold can express it)

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`; only read public
web pages, send nothing from the repo). Do NOT run anything on market data.

1. Web: open and read the source(s) on intraday return predictability in Bitcoin / crypto, e.g. Wen, Bouri,
   Xu, Zhao (2022, North American Journal of Economics and Finance, "Intraday return predictability in the
   cryptocurrency markets: momentum, reversal, or both") and any follow-up (Gao/Han/Li/Zhou-style intraday
   momentum on BTC). Extract: which interval predicts which (e.g. first half-hour -> last half-hour of the
   UTC day), sample, effect size (bp), whether it survives costs, post-2018 evidence. Quote numbers exactly;
   say what you could not open.
2. If the rule can be expressed with strategy 10 `timed_hold` (`docs/strategy-timed-hold.md`: zone, entry /
   exit times, direction `with_day` = sign of the move since the session open, ATR stop), write the grid
   `research/grids/timed_hold_crypto_intraday.toml` (BTCUSD primary, ETHUSD breadth in a separate grid file
   if their caches start in different years) and a section "Hypothesis C3" in `docs/strategy-timed-hold.md`
   with source, rule, at most 8 cells, the primary cell, and gates fixed now (the seven timed_hold gates,
   time-of-day family: bootstrap of mean net R > 0; breadth ETHUSD; min trades 300; trades must exit
   before the FTMO daily rollover or swap is counted). If `with_day` measures from a different anchor than
   the paper's predictor interval, say so and propose the minimal config field instead of guessing.
3. Report what the paper says, the files written, and the exact run command. Grid-loading test green.
