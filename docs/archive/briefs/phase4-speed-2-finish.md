# Brief: finish speed 2

`briefs/phase4-speed-2.md` was started; you hit your usage limit before reporting. The work so
far is committed as `a2fa2b2` ("Speed 2 (partial)": `detectors/shared.py`, zone keys,
journal / trend-following / analytics / risk changes, `tests/test_speed2.py`). Opus reviewed it:
suite green, golden lists identical.

1. Compare that commit (`git show a2fa2b2 --stat`, its diff) with the brief's steps 4-6 and
   list which items are done, partly done or missing.
2. Finish the missing ones the same way (tests first, no behaviour change; you write tests and
   code, Opus reviews).
3. Measure: `.venv\Scripts\python.exe scripts\profile_runs.py > results\profile\speed2_after.txt`
   (output to a file, ~7 min) and report the three totals against `speed1_after.txt`
   (37.0 / 283.5 / 94.3 s).

Done = full suite green (output to a file), `ruff check .` clean; report per item. Do not run
the golden check (Opus runs it).
