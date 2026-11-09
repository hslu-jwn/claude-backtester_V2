# I-40 exhaustion-reversal evidence check

Date: 2026-10-29  
Decision: **park; the compound setup has no independent validation and overlaps the shock-fade
family**.

## Question

Does evidence support fading an M5 run of four or five same-colour candles only when RSI is extreme,
price is at a prior-day/round-number level, a reversal candle appears, and a subsequent break
confirms entry?

## Evidence inspected

- Piyapas Tharavanij, Vasan Siraprapasiri, and Kittichai Rajchamaha, “Profitability of Candlestick
  Charting Patterns in the Stock Exchange of Thailand,” *SAGE Open* 7(4), 2017,
  [DOI](https://doi.org/10.1177/2158244017736799). **Publisher/RePEc abstract opened; full paper
  not opened.** Across ten years of SET50 daily OHLC, most bullish and bearish reversal-pattern
  mean returns are indistinguishable from zero, prediction accuracy is unreliable, and adding RSI,
  stochastic, or money-flow filters generally does not improve profitability or accuracy. The
  horizon and market differ, but the result is directly adverse to assuming that a reversal candle
  plus an extreme oscillator creates edge.

- Ahmed S. Alanazi, Ammar S. Alanazi, and David McMillan, “The Profitability of Technical
  Analysis: Evidence from the Piercing Line and Dark Cloud Cover Patterns in the Forex Market,”
  *Cogent Economics & Finance* 8(1), 2020,
  [DOI/full article](https://doi.org/10.1080/23322039.2020.1768648). **Full article page and abstract
  opened.** It reports positive after-cost performance for two precisely defined **daily** candle
  patterns across 24 FX pairs from 2000–2018. It does not test consecutive M5 candles, RSI
  80/20–90/10, location filters, delayed confirmation, or the proposed exit stack. It shows that a
  specific candle rule can be testable, not that arbitrary candle confluence transfers.

- John Coakley, Marwan Marzano, and John C. Nankervis, “How Profitable Are FX Technical Trading
  Rules?”, *International Review of Financial Analysis* 45, 2016, 273–282,
  [DOI](https://doi.org/10.1016/j.irfa.2016.03.010),
  [accepted-version record](https://repository.essex.ac.uk/16362/). **Repository abstract opened;
  full accepted paper not opened.** A search over 113,148 daily FX rules finds that data-snooping
  adjustment sharply reduces significant rules. Some RSI/Bollinger rules survive in its later
  sample, but this broad daily search supplies no preregistered threshold, direction, or intraday
  execution evidence for I-40.

- Christopher J. Neely and Paul A. Weller, “Intraday Technical Trading in the Foreign Exchange
  Market,” *Journal of International Money and Finance* 22(2), 2003, 223–237,
  [DOI](https://doi.org/10.1016/S0261-5606(02)00101-8). **Full paper opened in the earlier I-58
  audit.** Half-hourly predictability on four dollar rates does not survive realistic transaction
  costs and active-hour restrictions. This is the closer prior for a high-turnover, intraday
  price-history setup.

## Why the setup is not identified

1. **Each filter tells a different story without incremental evidence.** Same-colour count measures
   persistence, RSI is another transformation of recent returns, the level adds location, the candle
   adds rejection, and the later break adds momentum. No study shows their conjunction adds net
   predictive value beyond the underlying large move.
2. **Threshold freedom is large.** Four versus five candles, RSI 80/20 versus 90/10, level type and
   tolerance, candle definition, confirmation break, stop, three target choices, and flat-bar timeout
   create a combinatorial trial family.
3. **Direction is unresolved.** Large intraday moves may continue through stop cascades or reverse
   through temporary liquidity pressure. An extreme oscillator merely restates the move and cannot
   choose between these mechanisms.
4. **Adjacent candlestick evidence conflicts.** A broad daily equity study is mostly null and finds
   oscillator filters unhelpful; a positive daily FX study concerns two different fixed patterns.
   Selecting the favorable precedent after proposing I-40 would be literature-level cherry-picking.
5. **Intraday costs are adverse.** Confirmation enters after part of any reversal has occurred,
   while the stop remains at the extreme and targets are nearby. Spread/slippage therefore consume
   a large share of the proposed short horizon.
6. **It aliases existing trials.** The setup is a heavily filtered form of I-16/R-2026-004 shock
   fade plus I-30 level proximity and a candlestick trigger. It cannot create an independent family
   or rescue a failed shock-response result.

## Decision

Keep I-40 parked and counted inside the existing shock-response/reversal multiplicity family. Do
not test its filters sequentially or use them to condition a completed negative result.

Reconsider only after independent evidence fixes the exact M5 event, thresholds, supported level,
execution timing, one exit rule, and realistic net costs before local data, then confirms incremental
value over a simple return-shock baseline out of sample. No qualifying study was found.
