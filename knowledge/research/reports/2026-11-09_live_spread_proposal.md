# Spread / slippage proposal from the live demo fills (2026-11-09)

**Proposal only. Nothing reads `data/spreads/proposal_live_2026-11-09.json`; no default was changed.**

Data: fill probe runs 3 + 4 (FTMO demo), fills 2026-11-03 12:00 .. 2026-11-09 08:30 UTC, `fill_report`
`--since 2026-11-03T11:21` (7,019 fills: 3,517 entries, 1,338 stop_loss, 1,071 signal exits,
1,093 take_profit). 23 symbols, 66-244 entries each (150 typical). Per-symbol numbers:
`symbol_comparison.csv`; all fills: `fills.csv`; the report: `report.md`.

## How measured
- Spread = the bot's logged bar spread at the entry (entry rows only; exit rows reuse the entry
  bar's spread). Compared with (a) the fixed spread in `engine/costs.py` and (b) the table
  (`ftmo_spread_median.json`, NY year/hour). The table exists only for GBPJPY, GBPUSD, NAS100,
  US500, XAUUSD (2026 row); the other 18 symbols use the fixed spread.
- Slippage = adverse `slip` of market fills (entry, stop_loss, signal; spread of buys removed),
  trimmed 1 % each side (BTCUSD has jumps). Everything scaled to the symbol's `reference_price`
  like the model does.
- Entries are every 30 min round the clock, so the spread sample is hour-uniform; a strategy that
  trades only London/NY sees less of the wide Asia/rollover spreads.

## Spread: measured / modelled (mean over all hours; median in the csv)
Under-charged (ratio of the mean spread to the model value that is actually used):
GBPJPY 2.25x (fixed; 1.4x vs table), NAS100 1.95x (fixed; table 1.2x on the median), GBPUSD 1.97x
(mean; median 1.0x), UK100 1.77x (p90 5.1 vs 1.45), XAUUSD 1.63x (fixed; table median 0.82x, mean
vs table ~0.9-1.1), GER40 1.52x, EURAUD/AUDUSD/USDCAD 1.6-1.7x (mean; medians ~1.0x), USDJPY
1.44x (mean), EURJPY 1.23x (mean; median 0.79x), US500 1.23x (fixed, 1.07x vs table).
Right: AUS200, XAGUSD, AUDJPY, NATGAS, BTCUSD, UKOIL, USOIL (0.99-1.07x); US30, ETHUSD, JP225
+9..12 %.
Over-charged (median): EURUSD (0.0 logged median vs 2e-5), AUDJPY 0.68x, EURJPY 0.79x, EURAUD
0.84x. No symbol is clearly over-charged on the mean.
Hour pattern (all symbols, spread / table value, median ratio ~1.0): the mean ratio is 1.15-1.2
in NY hours 19-02 (Asia, wide FX crosses) and 5 at NY hour 18 (rollover; p90 16x, n=128),
0.93-1.0 in NY hours 4-16. London/NY (UTC) mean ratio 0.98.
So the FX gap is the **tail**: median OK, mean 1.4-2x because of Asia/rollover bars; the median
table hides it.

## Slippage: measured / model (trimmed mean, price units at reference)
- BTCUSD: 5.0x (model 0.5, measured mean 2.5, p90 18.7): clearly under-charged. Only symbol.
- GBPJPY 0.91x, USDJPY 0.93x, EURUSD 0.81x, JP225 0.73x, AUDUSD 0.72x, EURAUD 0.64x, NAS100 0.63x,
  US30 0.54x, GBPUSD 0.55x: about right (p90 above the model for most: the model is a typical
  value, the tail is 2-6x).
- Over-charged (< 0.3x): XAGUSD 0.05, USOIL 0.07, UKOIL 0.10, XAUUSD 0.15, GER40 0.21, ETHUSD 0.25,
  US500 0.27, EURJPY 0.26, NATGAS ~0, AUS200 and UK100 negative (price improvement).
- By fill type (pooled, units of model slip): entry median 0, mean 0.78, p90 5.9; stop_loss
  median 0.29, mean 1.17, p90 2.6; signal exit mean 0.15. Stop-loss exits are the expensive ones.

## Proposed changes (`proposal_live_2026-11-09.json`)
Per symbol `proposed_fixed_spread` (mean measured spread) and `proposed_slippage` (trimmed mean,
floored at 0), plus the per-session split (n >= 30) for use in a spread table. Main points:
1. Raise the fixed spread for GBPJPY, NAS100, UK100, GER40, XAUUSD (if the table is off), the
   FX majors/crosses (mean) and US500; leave the rest.
2. Raise BTCUSD slippage (0.5 -> ~2.5); consider a lower slippage for the metals/oil/ETH.
3. Better than a flat mean: replace the 2026 table by a mean-based, session-split table (the
   median hides the Asia/rollover tail). Needs more data per hour than the ~7 per symbol and hour
   here, so only the 3 sessions are proposed.

## Confidence and caveats
- Medium (>= 140 entries) for 20 symbols, low for the rest (XAGUSD 102, XAUUSD 131, NATGAS 66, see json).
  Only 4.6 trading days (Tue-Fri full, Mon 11-09 until
  08:30; Sat/Sun entries are almost only BTC/ETH: 162 of 191, the rest are Sunday-evening reopen fills).
- Demo account, not the real FTMO account: demo spreads/fills are usually looser and have no
  real market impact, so slippage is probably a lower bound for size.
- Fills ~1 s after the bar close, so `slip` mixes latency drift with real slippage; the mean is
  dominated by a few jumps (BTCUSD, indices); the per-symbol mean is noisy, p90 is more stable.
- Bar spread is the M1 bar's spread, not the tick at fill; weekend gaps and the 17:00 NY
  rollover are covered thinly (NY hour 17: 4 entries).
- No change to `data/spreads/*.json` tables, `CostConfig` defaults or `costs.py`.
