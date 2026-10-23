# Brief speed 1: per-candle overhead and loading (V2.4; results must not change at all)

Read `docs/review/speed.md` (profile and plan). Do plan steps 1-3 only:

1. `Timeframe.duration` (and similar per-candle constants) computed once, e.g. cached on the
   enum members; `replay.close_time` / views stop recomputing them.
2. Engine: reuse the base candle's close time for every higher-timeframe lookup in one step
   (review engine #11); avoid rebuilding views / tuples per candle where the same object can
   be reused safely (views must stay read-only and closed-only: no lookahead, `LookaheadError`
   untouched).
3. Loading (`data/adapters/cache_adapter.py` building `Candle`s): validate each day's OHLC
   once with numpy (the same checks `Candle.__post_init__` does: finite, high >= low, open /
   close within the range, aware UTC time) and then build the candles on a fast path that
   skips the per-object re-validation; a bad row must still raise the same error type.

Rules: no behaviour change of any kind. Measure before and after: run
`.venv\Scripts\python.exe scripts\profile_runs.py > results\profile\speed1_before.txt` before
your first change and `... speed1_after.txt` at the end (both with output redirected to a
file; this PC's terminal stalls unread output; the script takes ~8 min). Report the three
totals before / after. Test first where behaviour is observable (e.g. a bad OHLC row in the
cache still raises). Full suite green (output to a file), `ruff check .` clean. Do not run
the golden check (Opus runs it).
