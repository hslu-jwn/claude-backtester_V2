# Brief speed 2: detector sharing, hashing, journal, small items (V2.4; results identical)

Read `docs/review/speed.md`; profile after speed 1: `results/profile/speed1_after.txt`. Do
plan steps 4-6:

4. Detector sharing (review detectors #5): in `strategy/ny_index_sweep/frames.py` (and any
   other place that composes detectors the same way) compute FVG / BOS / ATR / swings once per
   timeframe and closed view, and let order block, breaker and BPR consume those events
   instead of running their own copies; the event order must stay exactly the same. Sweep
   breakout scan incremental instead of walking back each update (detectors #4).
5. session_zone_sweep: hash-heavy sets / dicts keyed by frozen dataclasses (see the profile:
   43 M `hash` calls) keyed by cheap stable ids instead, same iteration order where order
   matters; journal export grouped in one pass (strategy #7).
6. trend_following updates only the configured signal indicator and ATR (strategy #8);
   analytics #12 (bisect for weekday lookup), #13 (no runs x trades matrices), risk #12
   (reuse risk-independent sequences across risk levels).

Rules: no behaviour change of any kind; no-lookahead tests stay green; detectors stay
incremental. Measure with `.venv\Scripts\python.exe scripts\profile_runs.py >
results\profile\speed2_after.txt` (output to a file; ~7 min) and report the three totals
against `speed1_after.txt` (37.0 / 283.5 / 94.3 s). Full suite green (output to a file),
`ruff check .` clean. Do not run the golden check (Opus runs it).
