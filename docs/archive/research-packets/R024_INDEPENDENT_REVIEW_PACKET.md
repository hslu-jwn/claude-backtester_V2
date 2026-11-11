# R024 independent review packet

Date: 2026-11-06  
Reviewer: reusable quantitative-skeptic research sub-agent (`gpt-5.6-terra`)  
Artifact: `strategies/drafts/M15_SMA_CROSS_BATCH__v0.1.0.json`  
Bound SHA-256: `5bb493702405265032f450357da454301976bb1c78ea8cf5b48adba1627594d3`

## Verdict

Suitable for V2 compatibility preflight; not queue-ready. No run or holdout is authorized.

The first review required corrections to executable entry-to-stop risk, prior/current SMA timing,
robustness definitions, breadth-ledger identity and the ATR observed-sequence gap policy. Follow-up
wording review found two remaining ambiguities; both were corrected before the final exact-artifact
certification.

The certified draft fixes SMA4/SMA16 at completed M15 boundaries, qualifies prior equality but not
current equality, skips rather than defers a cross while a symbol/cell is non-flat, and requires a
new qualifying cross for a later trade. It freezes ATR96 through t-1, sizes from the executable
entry-to-chart-stop distance, delays stop eligibility until the next M1 bar, and invalidates the
complete affected cell rather than substituting P&L when post-entry data or a due fill is missing.

The four-cell grid raises the frozen breadth inventory from 352 to 356 cells. Fixed UTC halves,
center-derived date removal, seed-2026024 circular-block bootstrap and informative complements
against R010/R014/R017 prevent an isolated winning cell or overlapping trend/path response from
being promoted. Brock, Lakonishok and LeBaron (1992) is historical daily equity-index boundary
evidence only and does not establish modern intraday FX profitability.
