# Brief: draft the spec of strategy 14 `us_close_de_open` (first reference-symbol strategy); docs only

Read `AGENTS.md`; hard limits apply (no commits, no servers, no `live/`, no `.env`). Write ONLY
`docs/strategy-us_close_de_open.md` and `research/grids/us_close_de_open.toml` (the grid will not load
until multi-symbol step 1a lands; that is fine; mark it "do not run before integration"). Do not touch
`src/` or `tests/` (another job is changing the engine).

Source: `knowledge/research/reports/2026-11-10_idea_harvest_multisymbol.md` idea 10 (Xu et al., cross-market
overnight time-series momentum; open the abstract page yourself if you can). Design for reference symbols:
`docs/design/multi-symbol.md` › A.

Spec content: rule (US500 15:30-16:00 New York return as the signal; next day both NYSE and the German
cash session open normally; GER40 entry at the close of the 09:00 Berlin candle in the signal's direction if
|signal| >= threshold; exit at 09:30 Berlin or stop k x GER40 daily ATR(14)); calendars (NYSE holidays exist in
`strategy/timed_hold/calendars/`; German holidays: name the source you would use or treat a missing 09:00
GER40 candle as a closed day, conservatively); data (GER40 histdata ends 2020-06-15 by rule, so the development
period is 2015-01..2020-06; US500 histdata); cells (threshold {0.10 %, 0.20 %} x stop {0.5, 1.0} ATR x exit
{09:30, 10:00} = 8; primary 0.10 % / 0.5 / 09:30); control (the same GER40 window on all days, direction
from a coin flip is NOT allowed: use the all-days long and short baselines, disjoint from signal days,
for the effect gate); gates fixed now (timed_hold gates pattern: costs doubled, halves, effect vs control
bootstrap, best-5-dates removal, min 200 trades, integrity; breadth: UK100 at 08:00 London as a secondary
symbol); an Assumptions section (conservative choices, list each). Report the files.
