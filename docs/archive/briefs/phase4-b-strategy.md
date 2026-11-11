# Brief B-strategy: user decisions B8-B9 (V2.4; changes strategy trades on purpose)

Decisions are final (`docs/review/README.md` › B, rule set by the user 2026-10-22). Update the
specs in the same change, "(rule set by the user, 2026-10-22)". Test first.

- **B8 (review strategy #1, #2, #5):** strategy 1 (`session_zone_sweep`): active zones live
  until the real session end (not the last 30m close before it); ignored weekend candles no
  longer change swing state. Strategy 2 (`ny_index_sweep`): an event (BoS, tap) arriving after
  its deadline (after a data gap) is rejected; inclusive boundaries stay.
- **B9 doji threshold (review detectors #1):** the inclusive body threshold is compared with a
  small relative tolerance, a new config value with a documented default (e.g. 1e-9 of price),
  so float rounding cannot flip a candle exactly on the threshold.

Do NOT rewrite the golden lists; Opus does that after review. List every existing test whose
expected value changes (test, old -> new, which decision). Done = full suite green (output to
a file), `ruff check .` clean.
