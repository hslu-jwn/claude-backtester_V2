# B4: question for FTMO support (index CFD dividends)

Why: the engine books no dividends (review B4, confirmed). A cash-index CFD drops by the dividend
points on each ex-date; if FTMO credits longs / debits shorts with that amount, multi-day index results
are unbiased only once the engine books the same. Neither the demo deal exports nor web lookups settle
how FTMO does it. The user sends the message below (chat or support@ form); Opus adds the rule
test-first from the answer (`docs/risk-management.md` › Costs, `engine/costs.py`).

## Message to send (copy as is)

> Hello FTMO team,
>
> I hold index CFD positions overnight and would like to understand how dividends are handled.
>
> 1. When I hold a long or short position in an index CFD (e.g. US500, US30, NAS100, UK100, EU50,
>    AUS200, JP225, HK50, US2000) over an ex-dividend date of the index, is a dividend adjustment
>    booked to my account?
> 2. If yes: is it a separate balance / cash entry, part of the swap, or a price adjustment? Is a
>    long position credited and a short position debited (or the other way round)?
> 3. Which of your indices are affected? Is GER40 excluded because it tracks the DAX performance index?
> 4. How does the adjustment appear in the MT5 account history (deal type and comment), so I can
>    recognise it?
> 5. Do you publish the expected adjustment amounts or dates in advance (a calendar or table)?
> 6. Is the handling the same on FTMO Challenge, Verification and FTMO Account (funded) accounts?
>
> Thank you very much.

## After the answer

- "No adjustment": record it in `risk-management.md` (rule, the user's date); B4 closes; index short
  results stay as they are (the CFD price drop is then a real gain for shorts at FTMO).
- "Adjustment booked": a dividend-points table per index and ex-date, charged on holds across ex-dates
  (long credited / short debited as FTMO books it), test-first; then rerun the multi-day index cells
  that matter (F4M, RSI(2), daily_reversal, index trend) and report old vs new.
