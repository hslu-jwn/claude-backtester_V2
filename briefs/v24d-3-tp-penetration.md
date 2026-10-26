# Brief: V2.4d item 3 — take profits and limit entries fill on penetration (a setting, then measured)

Context: ROADMAP › V2.4d (3) (rule set by the user 2026-10-23: build it as a setting, measure
its effect on the golden lists of all 7 strategies, then the user picks the default);
`docs/review/book-app-requirements.md` A2 (Pardo ch.6: a resting limit is only safely filled
when price trades through it). Today `engine/trade.py` `_beyond` fills every TP on a touch
(long: bid high >= TP), and limit entries (strategy 3, `engine/backtest.py` `_fill`) on a
touch. Engine code: Opus reviews every line (AGENTS.md: engine = Opus high review).

## What to build

1. `CostConfig.tp_penetration` (float, **default 0 = today's behaviour exactly**): the
   distance price must trade beyond a take profit or a limit entry level before it counts as
   filled, as a **multiple of the trade's spread** (the spread already used for that trade's
   fills: fixed, scaled or from the spread table), so it scales per symbol and year.
   - TP (long): filled when the candle's high >= TP + d; short: low <= TP - d. The fill
     price stays the TP level (a limit never fills worse than its level). A candle opening
     beyond TP + d keeps today's rule (fill at the TP).
   - Limit entry: low <= entry - d (buy limit), high >= entry + d (sell limit); otherwise the
     order is not filled in that candle (it stays pending as today when the strategy keeps it).
   - Break-even after TP1 and partial TPs follow the same test.
   - MAE / MFE tracking unchanged.
2. `CostConfig.short_tp_on_ask` (bool, default False): a short's TP (a buy limit) is
   triggered by the ask (bid low + the trade's spread <= TP - d) instead of the bid. Same
   default-off rule.
3. **Touched but not filled:** each trade records how many TP levels were touched (old rule)
   without being filled (new rule) in its lifetime; the run summary reports the share of
   touched TPs that were not filled (`trades.csv` column, summary key).
4. Both settings in the settings panel and grid files like every other `engine.costs.*`
   setting (`settings.py` leaves), and in `docs/risk-management.md` › Costs.
5. **Measurement** (no default change): a script `scripts/measure_tp_penetration.py` runs the
   golden setup (`tools/golden.py`: 7 strategies, 2023, spec defaults) for
   tp_penetration 0 / 0.5 / 1.0 / 2.0 and, at 0, short_tp_on_ask on, and writes
   `results/tp_penetration.csv` + `.md`: per strategy trades, wins, net R, avg R, TP exits,
   touched-not-filled share, and the change against the default. Run it (output to
   `results\tp_penetration.log`, it may take a while) and put the table in your report.

## Rules

Spec first, test-case list at the top of the new test file (long and short, partial TPs, TP2,
break-even after TP1, gap open beyond TP, limit entry touched but not penetrated, spread from the
table vs fixed, d = 0 identical to today), failing tests, then code. With both settings at their
defaults the golden lists must stay identical (`python -m backtester.tools.golden --check >
results\golden_v24d3.log 2>&1`). No lookahead. Never edit `src/backtester/live/`.

Done = full suite green (`pytest -q > results\pytest_v24d3.log 2>&1`), golden check identical,
`ruff check .` clean, the measurement table in the report. Report: files changed, test count,
decisions the spec did not settle, open questions.

## Answers from Opus (your questions of 16:05)

1. `short_tp_on_ask = True`: the fill is the TP level itself (the ask reached the buy limit's
   level, so it fills there; no extra spread on that exit). Off: today's rule (bid touch, fill
   TP + spread) stays exactly as it is.
2. Touched but not filled: count each TP level once per trade if it was ever touched (old rule)
   in a candle where it was not filled (new rule), also when it fills later. Report per run:
   levels touched-not-filled / levels touched.

Go ahead with the brief.
