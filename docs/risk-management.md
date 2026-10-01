# Risk Management & FTMO Simulation Module

**Goal:** pass an FTMO challenge on a $100k account. The strategy outputs trades in **R only**; this module turns them into account money. That way risk settings can be tested on one backtest run, or on the manual R log, without re-running detection.

## FTMO rules (2026; re-check before use, presets stay editable)
| | 2-Step (preferred) | 1-Step |
|---|---|---|
| Profit target | P1 10%, P2 5%, funded none | 10% |
| Daily loss | 5% | 3% |
| Max loss | 10%, static | 10%, end-of-day trailing |
| Other | min. 4 trading days | Best Day Rule: best day ≤ 50% of positive days' profit |

The daily loss counts closed trades plus floating P/L and resets at midnight CE(S)T.

## Risk guidelines (starting points, to be tuned by backtest)
- **Risk per trade:** choose it so that 1.5 × the worst historical drawdown (in R) stays under 10%. Typically 0.5–1%. Phase 2 can be lower (e.g. 0.5%).
- **Personal daily stop:** −2% or 2 losses.
- **Max total open risk:** 2%. Correlated pairs (GBPJPY + GBPUSD) count as one group.
- **Drawdown scaling:** at about −4% from peak, halve risk until recovered.
- **Near-target scaling:** reduce risk when close to the target.
- **Midnight reset:** watch it, because NY trades and break-even runners can stay open past midnight, and their floating loss counts toward the new day.

## Components (`risk/`)
1. **RiskConfig:** all parameters above, plus per-symbol spread, commission and swap. Fully editable in the UI.
2. **PropFirmRules:** FTMO 2-Step and 1-Step presets plus custom.
3. **PositionSizer:** lots = risk $ ÷ (SL distance × value per point), from per-symbol contract specs; always rounds DOWN to the lot step.
4. **AccountSimulator:** replays trades in time order, candle by candle.
   - Tracks equity including floating P/L, using the worst point of each candle, with no lookahead.
   - Handles the daily reset while trades are open.
   - Personal rules can skip trades.
   - Reports pass/fail, the failure reason and the day it happened.
5. **MonteCarlo:** reshuffles whole trading days, not single trades, so bad days stay realistic.
   - Output: pass rate, fail rate (daily vs. max loss), median days to pass, drawdown distribution.
6. **RiskSweep:** grid over the settings (e.g. risk 0.25–1.5% × daily stop 1–3%) to find the setting with the best pass rate.

## UI page: "Risk & Prop Firm" (Dash)
- **Left panel:** preset dropdown, all RiskConfig fields, trade source (strategy backtest or imported R log).
- **Main panel:**
  - pass rate vs. risk % chart
  - fan of simulated equity curves with the daily and max loss lines drawn in
  - failure breakdown
  - sweep heatmap
