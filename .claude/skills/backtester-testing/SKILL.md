---
name: backtester-testing
description: "Use when writing or changing tests, debugging a test failure, or validating a backtester feature. Follow this project's spec-first, no-lookahead, pytest testing rules."
---

# Backtester Testing

Write tests that prove the intended behavior from the repository specifications, not tests that merely mirror the implementation.

## Workflow

1. Read the relevant section of `docs/` and the existing implementation and tests. The docs define trading behavior. If a rule is ambiguous or contradictory, stop and ask rather than deciding it in a test.
2. State the behavior and important edge cases in a small deterministic test. Prefer a hand-built candle fixture using `tests/conftest.py` and `make_candles` when the behavior concerns candles.
3. Run the focused test before changing production code and confirm it fails for the intended reason.
4. Make the smallest implementation change that satisfies the rule, then run the focused test again.
5. Run the relevant test module or directory, followed by `ruff check` on changed Python files when practical. Report commands and results; do not claim tests passed if they were not run.

## No-lookahead checks

Every detector test must exercise incremental `update(view)` calls in candle-close order and prove both:

- No event is emitted before the candle that confirms it.
- Appending later candles does not change events that were already emitted.

Test with views bounded at each simulated close. Never make a test pass by giving a detector full-history data or by catching `LookaheadError`.

## Quality checks

- Cover the relevant boundary and spec-defined edge cases, including dojis, wick-only breaks, confirmation timing, and same-candle SL/TP ambiguity where applicable.
- Assert concrete outcomes (event candle and time, prices, trade result in R, or account values), not only that code ran or returned a non-empty result.
- Use independent expected values and small fixtures; avoid large historical data, network access, sleeps, randomness without a fixed seed, and brittle implementation details.
- For risk and money calculations, test rounding, zero/minimum boundaries, costs, and loss-first behavior when the specification applies.
- For stateful behavior, test sequences and transitions, not just isolated calls.
- Test bug fixes with a regression case that failed before the fix.
- Never weaken or rewrite an expected result just to turn a failure green. Check the spec first; ask if it does not settle the question.

## Project conventions

- Keep tests under `tests/`, mirroring `src/backtester/`.
- Prefer existing fixtures and pytest patterns; do not add testing dependencies without need.
- Follow `CLAUDE.md` and the relevant `docs/` specification even if a generic testing recommendation conflicts.
