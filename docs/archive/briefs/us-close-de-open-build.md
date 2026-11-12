# Brief: build strategy 14 `us_close_de_open` (first reference-symbol strategy), test-first

Read `AGENTS.md` first; hard limits apply (no commits, no branches, no servers, no `live/`, no `.env`).
You work in the lane worktree `bt-lane-us_close_de_open`. You may change ONLY:
`src/backtester/strategy/us_close_de_open/`, `docs/strategy-us_close_de_open.md`,
`tests/strategy/us_close_de_open/`, `research/grids/us_close_de_open*.toml`.
Do NOT edit `strategy/registry.py` or any shared code (Opus adds the registry entry); tests build the
strategy directly. If a rule is unclear, stop and report it with the spec line; never guess a trading rule.

## Sources (read them)

- Spec: `docs/strategy-us_close_de_open.md` (all of it, incl. Assumptions, Opus decisions G1-G5/S14,
  and the user's decisions U1-U4 at the end).
- Reference-symbol API: `docs/ARCHITECTURE.md` › Reference symbols; `docs/research-runner.md` ›
  Reference symbols; `src/backtester/strategy/base.py` (`MarketAwareStrategy`, `references`),
  `src/backtester/core/market.py` (`ReferenceInput`, `MarketView`), `src/backtester/engine/market_replay.py`.
  Example test harness: `tests/engine/test_market_backtest.py` (Backtest + MarketReplay + build_series).
- Pattern to reuse (do not copy-paste more than needed): `src/backtester/strategy/timed_hold/`
  (`SessionStats`, `TimedExit` from `strategy/session_stats.py`; NYSE calendar
  `strategy/timed_hold/calendars/nyse_holidays.csv`, reading as in `timed_hold/day_filter.py`; warm-up
  `min_warmup_days` as in `TimedHold`). Template: `strategy/_template/`.

## What to build

`strategy/us_close_de_open/{__init__.py,config.py,strategy.py}`: `UsCloseDeOpenConfig` (frozen, every
value with the spec default, validated in `__post_init__` like `TimedHoldConfig`) and `UsCloseDeOpen(MarketAwareStrategy)`,
base timeframe M1, `uses_session_break_even = False`, constructor `(symbol, config=None, detectors=None)`.

Config keys (rename the grid's "proposed" keys to exactly these; drop `ref_day_offset`, the only rule is
previous weekday): `zone="Europe/Berlin"`, `entry_time=09:00`, `exit_time=09:30`,
`direction="with_ref"` (`with_ref | long | short`), `min_ref_return_pct=0.10`, `stop_atr=0.5`,
`atr_period=14`, `atr_zone="Europe/Berlin"`, `atr_open=09:00`, `atr_close=17:30`,
`atr_close_tolerance_min=0`, `ref_symbol="US500"`, `ref_zone="America/New_York"`, `ref_from=15:30`,
`ref_to=16:00`, `skip_nyse_short_days=True`, `calendar_dir=""` (= the timed_hold calendars folder).

`references` (instance attribute, set in `__init__` from the config):
`(ReferenceInput(ref_symbol, "signal", (Timeframe.M1,), max_age=timedelta(days=7), required=False),)`.
Decision U2: US500 is optional, staleness never blocks; only the two signal candles decide (G5).

Rules (spec › Definitions; times are candle CLOSE times in the named zone; candle ts = open = close - 1 min):
- `D_t` = local date (in `zone`) of the entry candle, Mon-Fri. `D_s` = the previous weekday (Monday -> Friday).
  With `skip_nyse_short_days`, both `D_s` and `D_t` must be full NYSE sessions (not closed, not early close).
- At the GER40 candle closing at `entry_time` on `D_t` (`now` is that close time), and only then:
  - ATR (daily Wilder ATR of the `atr_zone` sessions `(atr_open, atr_close]`, finished sessions only, as
    timed_hold) must exist, else no trade.
  - `direction == "with_ref"`: read `market.views[ref_symbol][M1]`; find the candles CLOSING at `ref_from`
    and `ref_to` in `ref_zone` on `D_s` (exact timestamps, binary search on ts; no neighbour fallback).
    Either missing or the view `None` -> no trade. `r = 100 * (C_to / C_from - 1)`. Long if
    `r >= +min_ref_return_pct`, short if `r <= -min_ref_return_pct` (compare with a 1e-9 tolerance so an
    exact threshold move trades, Assumption 3), else no trade.
  - `direction == "long" | "short"` (control family C, decision U1): same day filter, no reference candle
    needed.
  - Order at the entry candle's close, stop `stop_atr x ATR` against the direction, no target, timed exit
    at `exit_time` via `TimedExit` (first later candle if the exit candle is missing). One trade per day.
- Touch the reference view only at the entry candle (performance: the callback runs every minute).
  Feed the ATR every candle as timed_hold does.

Grids: fix `research/grids/us_close_de_open.toml` to the real keys (keep cells, primary, comments, the
"do not run" note becomes "development only, --dev-only; gates tool pending (U4)"). Add
`research/grids/us_close_de_open_uk.toml` (decision S14): UK100 traded, `zone/atr_zone =
"Europe/London"`, `entry_time = 08:00`, `atr_open = 08:00`, `atr_close = 16:30`, exits `08:30 / 09:00`,
same S and C families, `min_trades = 200`.

## Tests first (`tests/strategy/us_close_de_open/test_us_close_de_open.py`), hand-built candles

Write them before the code, then make them pass. Expected values written in the test. Cover:
1. Long / short / no trade around the threshold, incl. an exact-threshold move (trades) and |r| below.
2. No lookahead: at the entry, the reference view never contains a candle closing after `now`; a
   reference series with extra future candles gives identical orders; US500 candle closing at 16:00 on
   `D_t` (same day) is never used.
3. Monday uses Friday's signal; Tuesday after a NYSE-closed Monday: no trade (`D_s` not a full session);
   a 13:00 early close on `D_s` or on `D_t`: no trade (use a tmp `calendar_dir` csv).
4. Missing 15:30 or 16:00 US500 candle: no trade; missing 09:00 GER40 candle: no trade that day.
5. DST mismatch week (e.g. 2019-03-11..2019-03-29: US on DST, Berlin not): signal still the 15:30 / 16:00
   New York local candles.
6. Stop = stop_atr x ATR from the entry close; timed exit at 09:30 Berlin; no trade before ATR exists.
7. Control `direction = "long"`: trades on a qualifying day without any US500 data; not on a NYSE-closed `D_s`.
8. Config validation (bad direction, exit <= entry, stop <= 0, unknown zone).
9. `references` is built from the config (`ref_symbol` change -> declaration changes), `required` False.
10. UK100 config (08:00 London entry) works with the same signal.

## Done =

`python -m pytest -q -p no:cacheprovider tests/strategy/us_close_de_open tests/engine/test_market_backtest.py`
green and `python -m ruff check src tests` clean (run both from the lane folder with
`..\backtester-claude_V2\.venv\Scripts\python.exe`; Opus runs `lanes check`). Spec docstring references
(`Spec: strategy-us_close_de_open.md › ...`). Report: files, test results, any spec question.
