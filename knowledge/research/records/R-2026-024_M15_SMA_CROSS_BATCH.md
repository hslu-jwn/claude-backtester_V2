# R-2026-024 — M15 fast-slow SMA cross batch

Status: independently reviewed speculative compact design; compatibility preflight requested and unqueued.  
Date: 2026-11-06

## Evidence boundary

Brock, Lakonishok and LeBaron (1992) was opened at the publisher. It tested moving-average and
trading-range rules on the Dow Jones Index, 1897–1986, with bootstrap analysis. It does not test
modern FX, M15 bars, the 4/16 windows, signal-close costs, or this day-flat rule. This is therefore
an original four-cell falsification; the null is the expected result.

## Frozen rule

On 17 physically consecutive completed London M15 closes, trigger only when SMA4 strictly crosses
SMA16 after equality-or-opposite ordering at t-1. Test FOLLOW_CROSS and FADE_CROSS, each at 30 and
60 minutes, with a chart one-ATR stop frozen through t-1 and an executable signal-close fill. Any
post-entry M1 or due-fill defect invalidates the complete cell rather than inserting a price.

The four cells lift the common inventory from 352 to 356. Exact-artifact review approved SHA-256
`5bb493702405265032f450357da454301976bb1c78ea8cf5b48adba1627594d3`. No queue, execution,
best-cell rescue or holdout is authorized; compatibility confirmation is still pending.
