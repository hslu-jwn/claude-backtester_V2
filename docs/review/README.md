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

## B. Needs the user (changes results or a rule)

See the decision list in `docs/HANDOFF.md` › Open.
