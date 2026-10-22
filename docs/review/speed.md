# V2.4 speed: profile and plan (2026-10-23)

`python scripts/profile_runs.py > results/profile/summary.txt` (cProfile, in-process,
workers=1, development period 2019-01-01..2021-09-13, spec defaults; cProfile roughly doubles
the times, the shares hold). Raw profiles: `results/profile/<strategy>.prof` (not in git).

| Run | Total | Where the time goes |
|---|---|---|
| opening_range US500 + NAS100 (1,362 trades) | 51 s | load 20 s (cache adapter builds 1.85 M `Candle`s one by one: adapter 5.8 s own time, `Candle.__post_init__` validation 7.4 s); engine loop 31 s: strategy 9.3 s, `replay.close_time` 7.5 s, views / `current` / `__getitem__` ~10 s, `Timeframe.duration` 2.7 s |
| ny_index_sweep NAS100 (367 trades) | 310 s | strategy frames 199 s: FVG 69 s, BOS 52 s, zones 44 s, BPR 43 s, OB 41 s, ATR 41 s (FVG / BOS / ATR computed again for every consumer, review detectors #5); `Timeframe.duration` 10.4 M calls 18 s; `higher_view` / `close_time` 34 s |
| session_zone_sweep XAUUSD (2,632 trades) | 96 s | strategy 71 s; frozen-dataclass hashing 43 M `hash` calls ~25 s; journal export one call 11 s (quadratic, review strategy #7); session clock 9 s |

## Plan (each step: golden lists identical, before / after with the same script)

1. `Timeframe.duration` and other per-candle constants computed once (cached on the enum).
2. Engine: reuse the base candle's close time for every higher-timeframe lookup (review
   engine #11); cheaper views.
3. Loading: validate a day's OHLC with numpy once, then build candles without per-object
   re-validation (same checks, done vectorized; results identical).
4. Detector sharing: one FVG / BOS / ATR per timeframe and view, shared by OB, breaker, BPR
   (review detectors #5); sweep breakout scan incremental (detectors #4).
5. session_zone_sweep: hash-heavy sets keyed by ids instead of frozen dataclasses; journal
   grouped in one pass (strategy #7).
6. trend_following updates only the selected signal (strategy #8); analytics / risk items
   (analytics #12, #13; risk #12).
