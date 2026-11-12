# Brief: two-leg trades, increment 2a-2 — paired M1 engine, test-first

Read `AGENTS.md` first (Invariant #1: no lookahead). Hard limits apply (no commits, no branches, no servers,
no `live/`, no `.env`). Worktree `bt-lane-two_leg2`. No backtest or research run. Accepted by the user
2026-11-12. Spec: `docs/design/multi-symbol.md` › B and "Tests and compatibility acceptance" items 1, 2, 5,
6. Builds on 2a-1 (`strategy/group.py`, `engine/group_trade.py`, already merged; read them and their tests).
If something is unclear and not answered here, choose the reading closest to the design and to the legacy
single-leg engine (`engine/backtest.py`, `engine/trade.py`), write it in the module docstring as an
assumption and list it in your report; stop only if two design sentences contradict each other.

## Files you may create / change (nothing else)

- `src/backtester/strategy/group.py` (add the strategy interface below; keep 2a-1 behaviour).
- `src/backtester/engine/group_backtest.py` (new).
- `tests/engine/test_group_backtest.py` (new); `tests/strategy/test_group.py` (add cases only).
- `docs/ARCHITECTURE.md` (extend the 2a-1 paragraph by a few lines).
Legacy files (`engine/backtest.py`, `engine/trade.py`, `engine/market_replay.py`, `strategy/base.py`,
`runner.py`) are NOT changed; golden runs stay identical by construction. Runner / artifacts / CLI are the
next increment (2a-3).

## Strategy interface (`strategy/group.py`)

`class GroupStrategy(ABC)` with: `legs: tuple[str, ...]` (the traded symbols, >= 2), `references:
tuple[ReferenceInput, ...] = ()` (extra read-only symbols, as `MarketAwareStrategy`), `timeframes` per
symbol via `ReferenceInput` declarations; abstract `on_group_candle(now, market: MarketView) ->
list[GroupOrder]`; optional `group_exits(now, market, open_groups) -> list[str]` (group ids to close,
default none); optional `on_group_closed(result)`. Strategies see only `MarketView` (bounded snapshots,
`core/market.py`), never series or candles beyond `now`.

## Engine (`engine/group_backtest.py`)

`run_group_backtest(strategy, series_by_symbol, cfg: CostConfig, values=None) -> GroupRunResult` where
`series_by_symbol` maps each leg / reference symbol to its M1 `CandleSeries` (and declared higher
timeframes, as `MarketReplay` expects). Build ONE `MarketReplay` over legs + references (every leg is
declared as a `ReferenceInput` with M1 and `required=True`) and step a single logical clock over the
UNION of all M1 close times, in order. At each close time `now`:

1. Manage open groups first, leg by leg, on that leg's own M1 candle closing at `now` (a leg without a
   candle at `now` is simply not managed this minute: no fabricated candle):
   - Stops per leg with the legacy conventions (long SL hit when the bid low <= SL, exit fill = SL minus
     adverse slippage; short SL with the config's `short_sl_on_ask` rule as in `OpenTrade`; gaps through
     the stop fill at the candle open, adverse). A leg with SL and TP in one candle: SL first.
   - `ExitPolicy.ALL_LEGS_NEXT_OPEN_AFTER_STOP`: when a leg stops at `now`, every other open leg of that
     group exits at the OPEN of its own next M1 candle that opens at or after `now` (never at an inferred
     intraminute price, never at a same-minute high/low). Two legs stopping in the same minute both exit at
     their stops. Until a leg's next candle exists it is open RESIDUAL exposure (kept, not liquidated).
2. Then `market = replay.advance(now)`; if `market.ready`, call `on_group_candle(now, market)` and
   `group_exits(...)`; group exits also fill at each leg's next open.
3. Entries: `EntryPolicy.NEXT_OPEN_ALL_OR_NONE`: an order with `intent_time == now` becomes pending; it
   fills only at the first later minute `t` at which EVERY leg has an M1 candle opening at `t`
   (simultaneous opens; check this at the close of minute `t`, using only that minute's OPEN for the fill);
   if no such minute exists within `expiry_minutes` after `intent_time`, the whole group is rejected
   (recorded with reason "expired"); if any leg fails validation (no cost settings, nonfinite price,
   stop distance <= 0 after tick rounding) the whole group is rejected ("leg rejected: <why>"). The
   entry open cannot be used to choose the entry (the intent was fixed at `now`).
   Fills: long at ask = open + `cfg.spread(symbol, at, open)` plus adverse slippage; short at bid = open
   minus adverse slippage (mirror the legacy market entry). Stop prices = chart entry -/+ `stop_distance`.
4. End of data: groups with open legs are returned as UNRESOLVED (`residual=True`), with each open leg's
   last close as a mark and its timestamp (staleness), never as executed exits.

Results: closed groups -> `group_result(order, fills, cfg, values)` from 2a-1 (values default: each leg's
`cfg.for_symbol(symbol).value_per_price_unit`, constant; note in the docstring that causal conversion
symbols are a later increment). `GroupRunResult`: `closed` (GroupResults in close order), `unresolved`
(group id, open legs with mark and mark time), `rejected` (group id, reason), and `notes`.

## Tests first (hand-built M1 candles, `tests/conftest.py` style)

1. Cross-symbol lookahead (design item 1): A's candle 10:00-10:01, B's next 10:01-10:02; at 10:01 the
   strategy's market cannot see B's 10:02 close; access beyond raises `LookaheadError`.
2. Appending future candles to either leg never changes earlier decisions, fills or results (design item 2).
3. Next-open entry: the intent at 10:01 fills at the 10:01 open of both legs, never at the signal minute's
   open; a missing leg candle at 10:01 delays to the first common open; no common open within expiry ->
   rejected "expired"; one leg without cost settings -> whole group rejected.
4. Exact fills: long at open + spread + slippage, short at open - slippage (a custom `CostConfig`).
5. Leg stop: leg A stops in the candle 10:04-10:05 (managed at 10:05); leg B exits at the open of its
   next candle opening at 10:05 or later; B's 10:04-10:05 high/low is never used for B's exit. Both legs
   stop in one minute -> both at their stops. Gap through a stop -> adverse fill at the open.
6. Residual: B has no candle after A's stop (market closed) -> B stays open until its next candle; at end
   of data without that candle the group is unresolved with B's last close as a stale mark.
7. Hand-built full example with explicit expected group R gross and net (costs on), reconciled.
8. `group_exits` closes all legs at their next opens; `on_group_closed` gets each result once.
9. Legacy untouched: the legacy `Backtest` on a fixture gives the same trades before and after importing
   the new modules (sanity), and no legacy file is modified (the diff shows it).

## Done =

`python -m pytest -q -p no:cacheprovider -n 8 tests/engine tests/strategy tests/core` green and
`python -m ruff check src tests` clean (worktree, `..\backtester-claude_V2\.venv\Scripts\python.exe`).
Docstrings cite `Spec: design/multi-symbol.md › B`. Report: files, test results, every assumption, open
questions for 2a-3 (runner, artifacts) and 2b (research, risk).
