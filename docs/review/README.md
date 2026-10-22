# V2.4 code review (2026-10-22)

Codex (gpt-6.1-sol, high effort, read-only, `briefs/phase4-review.md`) reviewed every module;
the raw findings with evidence are in the files here (`<module>.md`, numbered per module, e.g.
`engine #2`). Opus triaged them. 84 findings: core 3, detectors 5, engine 11, risk 12,
analytics 13, strategy 8, ui 11, live 21.

Audit items: 13.19 (no-wick limit fill lookahead) **refuted** by two reviews (pending limits
precede the fill candle); 13.6, 13.7, 13.8, 13.9 (part), 13.10, 13.11, 13.17, 13.20, 13.21,
13.23 **confirmed**.

## A. Fix directly (no trading rule, golden trade lists stay identical)

Test first, small commits, golden `--check` after each; Codex writes, Gemini / Claude 4.6
review, Opus runs the tests. `live/` fixes are written by Opus (models may not edit `live/`).

- Input validation / crash hardening: core #1-#3, detectors #2-#3, engine #3-#5, risk #3,
  #8-#10, analytics #8-#10, ui #9.
- Paths independent of the working folder (13.17): engine #7, risk #11, analytics #7, ui #8,
  live #21.
- Study / report bugs (no golden change): analytics #1 (walk-forward training used trades
  closing in the test year), #2-#6; engine #10; strategy #3, #4, #6 (options off by default).
- UI: ui #1-#2 (replay shows future trade results), #5 (presets drop costs of hidden symbols),
  #6, #7, #10, #11.
- Live bot (demo): live #1-#16, #18-#20 (clock skew, swallowed LookaheadError, failed queries
  counted as flat, lost tracking, daily-stop latch, control files at start, credential
  scrubbing, partial fills, fees, risk validation, cache repair).
- Speed: detectors #4-#5, engine #11, risk #12, analytics #12-#13, strategy #7-#8, after the
  profile of a real sweep (V2.4 step 3), measured before / after.

## B. Changes results or a rule: decided (rule set by the user, 2026-10-22)

The user approved all nine ("if it makes a more realistic scenario, implement it"; the exact
choice left to Opus). Each is one commit that updates its spec and rewrites the golden lists
(`tools/golden.py --write`), with the changed trade counts in the commit message.

1. **FTMO daily loss (13.11; risk #2, ui #3, live #17):** the limit is 5 % **of the initial
   balance**, measured from the day-start balance (FTMO's rule), in risk, UI and bot.
2. **Monte Carlo pass rate (13.23; risk #4, #5):** a passing day is played to its end (a later
   loss that day can still breach); unfinished attempts are reported separately (count and
   share) instead of being dropped.
3. **Adaptive risk (risk #1):** entry decisions use only the risk known at entry (open trades'
   initial risk), never an open trade's later result.
4. **Slippage (12.8, 13.20; engine #1, analytics #11):** the configured slippage applies to
   market entries, stop fills (SL, also gap stops) and time / signal / end-of-data exits; not
   to limit entries or TP fills.
5. **Break-even beyond TP1 (engine #2):** when the break-even level would already be crossed at
   the moment TP1 fills (a long's BE above the TP1 price), the stop is not moved (a broker
   rejects a stop on the wrong side of the price); the original SL stays.
6. **Costs (engine #8, #9):** percentage commission on the entry fill price; the break-even
   level solved so the remaining part nets zero after commission.
7. **MAE / MFE (engine #6):** an exit at the candle open counts excursions only up to that open.
8. **Strategy bugs (strategy #1, #2, #5):** strategy 1 zones live until the real session end;
   ignored weekend candles no longer change swings; strategy 2 rejects events past their
   deadline after a data gap.
9. **Doji threshold (detectors #1):** the inclusive body threshold is compared with a small
   relative tolerance (config value) so float rounding cannot flip an exact-threshold candle.
