# Card 0: Strategy 20 regime and tail audit (descriptive, no gate, no variant)

2026-11-16/17. Script written and run by Fable 5.2 (`research/screens/2026-11-16_card0_s20_audit.py`); Fable hit its
usage limit before writing the report, so Opus wrote this from the raw output (`card0_output.txt`, same folder).
Diagnostic only: the 2024+ test period is spent; nothing here is evidence for a new variant.

## Results

| Item | Finding |
|---|---|
| (a) Per year | Strategy 20 full: 2020 +610 bp/week (t 4.71), 2021 +163, **2022 -32**, 2023 +36, 2024 +73, 2025 +197, 2026 +180. Without 2020: +100 bp/week, t 3.38 (top-100: +125, t 3.49). Strategy 19 (carry): 2022 +144 and 2023 -18, the opposite pattern. |
| (b) S20 vs S19 correlation | Weekly +0.09; 4-week +0.21; 13-week +0.17; 26-week -0.05 (10 blocks only). Top-100: +0.08 to +0.22. Low at every frequency. |
| (c) Joint worst weeks | Worst 10 % of S20 weeks (-606 bp): S19 averages -35 there; worst S19 weeks (-934): S20 +88. Both in the worst decile on 3 weeks (2.7 expected if independent). Equal-risk mix: worst week -3.3 sd vs -5.1 for the worse single stream; mix t 4.23. |
| (d) Tails (members capped at +-50 %) | Full book keeps 60 % of its mean overall (dev 67 %, **test 53 %**); top-100 keeps 65 % (test 53 %). Capped t: full all 3.54, top-100 all 3.84; test alone 2.38 / 2.10. Medians are positive everywhere (full test +99, top-100 +143). |
| (e) Deflated Sharpe | Survives the family (N = 7) and all crypto (N = 32) trial counts (DSR 0.91-1.00). Against the whole ledger (N = 1,665): development alone 0.43, all 333 weeks 0.95, capped 0.56. Strategy 19: 0.93 / 0.79 / 0.33. |
| (f) Prop closed form vs simulator | Years to pass at full size: closed form 3.36 / 1.65 / 0.98 / 0.41 vs simulator 2.65 / 1.29 / 0.76 / 0.34 at Sharpe 0.7 / 1.0 / 1.3 / 2.0: the closed form is ~20-25 % slow, i.e. conservative. **Pass-% column is not trustworthy**: half-size rows show 103-121 %, so the script's pass count and finished-attempt count do not match (likely phase passes counted inside unfinished attempts). Fix before using any pass % from this script. |

## What it means

- **Regime:** Strategy 20 is not one steady edge. 2020 (+610) and 2025-26 carry it; 2022 lost and 2023 was flat.
  Fable's proposed regime gate M7 (no half below 25 % of the mean) fails on development (+327 / +2), as predicted.
- **Diversification is real:** Strategies 19 and 20 are close to independent, also in bad weeks, and they had
  opposite years (2022, 2023). This is the strongest point for card 5 (equal-risk crypto book).
- **Shrink factor for planning:** capped / plain ~0.55-0.65 and Fable's x0.65 proposal (M10) agree. Planning range
  for Strategy 20 top-100: about +90-110 bp/week (capped mean all periods +110; test-only capped +89).
- **Selection:** the edge survives honest trial counts inside crypto; it does not survive "best of the whole
  1,665-cell ledger" on development alone. The forward log stays the decisive test.
- **Prop decision (HANDOFF › Open 1):** a Sharpe ~1.0-1.4 stream (capped) passes a 2-step in roughly 0.8-1.3 years
  on the simulator at full size, faster than the closed form; the book with Strategy 19 should be faster still. The
  pass % must come from the existing prop-fit scripts, not from this audit's (f) column.

## Open

- Fix the (f) pass counting (compare `ftmo_by_risk` keys `passes` vs `attempts` / `unfinished_attempts`) if the
  closed form is to be used.
- Not checked by Opus: the regenerated weekly lists match the frozen ones (the script prints dev / test checks that
  match the ledger: +145.0 t 3.24, +147.2 t 3.76, +171.0 t 3.64, +166.3 t 3.06).
