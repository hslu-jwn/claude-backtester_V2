# Fill analysis 2026-10-28 (V2.4b), demo probe 2026-10-27 16:00 - 2026-10-28 06:29 UTC

Data: 1,128 demo fills (564 entries, 225 stop-loss, 174 signal / time exits, 165 take-profit),
23 symbols, about 45 market fills per symbol; sessions New York (440) and Asia (688). **No London
session yet** (the export ran 06:29 UTC). Full tables: `results/fill_report/report.md`; deals
exported read-only with `scripts/export_deals.py`. The six time exits stuck in the 2026-10-27
daily break (closed at the reopen) are inside "signal" and inflate its tail slightly.

## Findings

1. **Typical slippage is at or below the model.** Median entry slippage = 0.23 x the model's
   slippage (Asia 0.08 x, New York 0.49 x). Per symbol the median is at or under the model for
   every symbol except EURAUD (4e-05 vs 3e-05) and BTCUSD (0.55 vs 0.50), both small.
2. **The tail is about 3 x the model.** p90 of entries 3.3 x, stop-loss exits 2.1 x, signal
   exits 2.5 x. Largest p90 in price units vs model: JP225 9.8 vs 5, BTCUSD 8.3 vs 0.5, US30
   4.1 vs 1.14, GER40 2.55 vs 0.765, AUS200 2.3 vs 0.5.
3. **Yesterday's BTCUSD alarm (median 6.4) was the small sample**; now median 0.55 (model 0.5),
   p90 8.3.
4. **Spreads:** most symbols within 15 % of the table; GER40 1.9 x and UK100 2.3 x the table,
   because the probe trades them in Asia hours, where their spread widens. Our strategies do
   not trade European indices in Asia, so this does not change their costs.
5. **Commissions** match the model for every symbol (NATGAS rounds to $0 on 0.01-lot deals).

## Proposal (the user decides; nothing changed)

- **Keep the model slippage as the default.** It already covers the median; lowering it to the
  measured median would flatter every backtest.
- **Add the measured p90 per symbol as the stressed-cost level** in the robustness report
  instead of a flat x1.5, once London fills are in (one more day of the probe).
- Re-run after 1-2 more days (London + a second New York session), then stop the probe and do
  12.5 reconciliation.
