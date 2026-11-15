# FB-263: futures re-cost of the intraday index rows (2026-11-15, arithmetic, no data look)

Question: would the intraday index rows killed on FTMO CFD costs survive at CME futures costs (futures prop firms)?

Futures cost per round trip (CME specs; commissions ASSUMED, not verified): ES / MES tick 0.25 pt = ~0.6-1.2 bp of
notional (index 2,000-4,500), NQ tick 0.25 = ~0.2-0.6 bp, YM tick 1 = ~0.3-0.6 bp. With 1 tick spread, half a tick
slippage per fill and ~$4 RT on a full contract (or ~$1.5 on a micro, ~1 bp at 2018 levels) the all-in round trip is
~1.0-1.7 bp for ES, ~0.5-0.8 for NQ, ~0.6-0.9 for YM. FTMO CFD at the same hours (cost wall table): US500 ~2.4 bp,
NAS100 ~1.7, US30 ~0.55, GER40 ~0.8. So futures halve the cost only on US500 / NAS100 and are no cheaper on US30.

Upper bound: the t-statistic at **zero** cost (gross only), from the recorded results:

| Row | Recorded | Gross t at zero cost |
|---|---|---|
| I-85 noise-band momentum (US500, US30, NAS100) | net +0.31 bp a day, t 0.37; gross ~1.6 bp a day | ~1.9 |
| I-89 index rotation follow | gross +1.3 bp a day, net t -4.19 (se ~0.74) | ~1.8 |
| I-88 SMT NAS100 / US500 | gross +1.7 bp, net t -0.17 (se ~1.8) | ~1.0 |
| H06 / F2 last-30-min momentum US500 | gross +0.008 / +0.010 R a trade, ~650-1,600 trades | ~0.2-0.4 |
| S06 ORB test (US indices) | net +0.10 R, t ~1.5 (already net) | ~1.7 |
| I-91..I-93 ICT event rules | gross +0.8..+2.5 bp, net t -0.87..-1.59 | < 1.5 |

No row reaches t 3 even with free trading, so no futures cost model can rescue them. **FB-263 closed.** A futures
idea needs its own gross edge (AGENTS.md › Venues), not a re-costed CFD failure.
