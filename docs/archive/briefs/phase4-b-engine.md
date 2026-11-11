# Brief B-engine: user decisions B4-B7 (V2.4; changes strategy trades on purpose)

Decisions are final (`docs/review/README.md` › B, rule set by the user 2026-10-22). Update the
specs (`docs/ARCHITECTURE.md` engine section / cost sections, `docs/risk-management.md` for
random fills) in the same change, "(rule set by the user, 2026-10-22)". Test first with
hand-built candles where the right answer is obvious. Keep SL-first and no-lookahead.

- **B4 slippage (ROADMAP 12.8, audit 13.20; review engine #1, analytics #11):** the configured
  `SymbolCosts.slippage` (price-scaled like the spread) applies against the trader to market
  entries, stop fills (SL, including gap stops) and time / signal / end-of-data exits; never
  to limit entries or TP fills. Random fills Kind C: time / signal / end-of-data exits get the
  exit draw too.
- **B5 break-even beyond TP1 (engine #2):** when TP1 fills and the break-even level is already
  crossed at the TP1 price (long: BE >= TP1 price; short mirrored), the stop is not moved; the
  original SL stays.
- **B6 costs (engine #8, #9):** percentage commission on the entry **fill** price; break-even
  level solved so the remaining part nets exactly zero after commission at its exit fill.
- **B7 MAE / MFE (engine #6):** an exit at the candle open (gap) counts excursions only up to
  that open.

Do NOT rewrite the golden lists (`tests/golden/`); Opus does that after review. Existing tests
whose expected values change because of exactly these decisions: update them and list each
one (test, old -> new, which decision). Done = full suite green (output to a file), `ruff
check .` clean. Report per decision.
