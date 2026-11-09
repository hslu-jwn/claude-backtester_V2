# R-2026-016 — M15 prior-session extreme outward-cross response batch

Status: speculative compact development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test the first close moving outward through the immediately preceding London weekday's completed
09:00–15:00 high or low. Brock, Lakonishok, and LeBaron (1992) found historical information in
daily Dow trading-range breaks, but that does not establish an intraday FX transfer, modern cost
survival, or the response sign. This four-cell version is an original compact adaptation.

## Four-cell design

Require all 24 prior-weekday M15 reference bars; otherwise suppress the current date rather than
infer a holiday or substitute an older observed session. On the current date, scan signal closes
ending 09:30 through 13:45; the first physically adjacent pair wholly inside the current session
whose first close is inside the frozen range and second close is strictly above its high or below
its low fixes the only event for that symbol-day. Out-of-window crosses are ignored. Select response
`{FOLLOW_CROSS, FADE_CROSS}` and hold `{30, 60}`: exactly four cells. A frozen prior ATR96 supplies
the one-ATR stop; fills, costs, state, and data failures use the common fast-lane controls.

## Distinctness, advancement, and multiplicity

This is cross-session reference memory, not R013's adjacent two-bar envelope, R008's compression
box, or R015's invariant price grid. The 60-minute center and 30-minute neighbor must both pass
normal/doubled costs, UTC halves, three positive symbols per half, 300 center trades, common
five-date removal, and seed-2026016 circular five-date bootstrap over all eligible weekdays,
including zero-event dates.

The breadth ledger would contain 324 selectable R007-R016 cells, two R008 diagnostics, and all
named prior-session range/extreme trials. No best-cell rescue, queue, run, or holdout is authorized.

## Pre-review skeptical boundary

The historical daily-equity result may not transfer, decentralized FX may not remember this
arbitrary session, and apparent breaks may simply proxy volatility. Complete prior-weekday
requirements avoid stale references but can reduce sample size around holidays and data defects.
