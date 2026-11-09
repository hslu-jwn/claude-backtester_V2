# I-41/I-42 zone-entry variant evidence check

Date: 2026-10-29  
Decision: **park together; neither wick rejection nor breakout-retest creates an independent edge**.

## Question

After a separately defined range/zone exists, does independent evidence support either (I-41) a
hammer/shooting-star or spring/upthrust fade at its edge, or (I-42) waiting for a broken edge to
retest and then re-entering in the breakout direction?

The two ideas were reviewed together because they select opposite responses around the same latent
zone. Testing them as separate families would conceal direction and entry-timing multiplicity.

## Evidence inspected

- J. Henning Fock, Christian Klein, and Bernhard Zwergel, “Performance of Candlestick Analysis on
  Intraday Futures Data,” *Journal of Derivatives* 13(1), 2005, 28–40,
  [DOI](https://doi.org/10.3905/jod.2005.580514). **Publisher/author metadata and abstract opened;
  full paper not opened.** Mechanically defined intraday candles on DAX and Bund futures show no
  predictive ability alone or combined with common momentum indicators. This is adverse to treating
  a wick shape as an independently validated futures signal.

- Matthieu Duvinage, Paolo Mazza, and Mikael Petitjean, “The Intra-day Performance of Market Timing
  Strategies and Trading Systems Based on Japanese Candlesticks,” *Quantitative Finance* 13(7),
  2013, 1059–1070, [DOI](https://doi.org/10.1080/14697688.2013.768774).
  **Publisher/RePEc abstract opened; full paper not opened.** It tests 5-minute candles on 30 DJIA
  constituents. Apparent rule performance largely disappears under costs and data-snooping control;
  no single rule or combined automated system outperforms after transaction costs.

- William Brock, Josef Lakonishok, and Blake LeBaron, “Simple Technical Trading Rules and the
  Stochastic Properties of Stock Returns,” *Journal of Finance* 47(5), 1992, 1731–1764,
  [DOI](https://doi.org/10.1111/j.1540-6261.1992.tb04681.x),
  [full paper opened](https://support-and-resistance.technicalanalysis.org.uk/BrockLakonishokLeBaron1992.pdf).
  Long-history Dow data from 1897–1986 reject several null models for moving-average and trading-
  range-break signals. This is supportive of simple **daily new-high/new-low breakout information**,
  but it does not test retests, wick rejection, intraday zones, supported V2 instruments, modern
  execution costs, or the proposed arch stop.

- Carol L. Osler, “Support for Resistance: Technical Analysis and Intraday Exchange Rates,”
  *FRBNY Economic Policy Review* 6(2), 2000, 53–68,
  [full paper](https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf).
  **Full paper opened in the I-30 audit.** Professional FX support/resistance levels predict trend
  interruptions, but the study does not report a net strategy and conditional order flow can also
  propagate momentum after a breach. A zone touch therefore does not determine fade versus follow.

## Why neither entry is identified

1. **The parent zone lacks evidence.** I-41 and I-42 are conditional on I-33-style zones/ranges,
   whose direct evidence check is negative. An entry variant cannot validate an unvalidated event.
2. **Opposite directions share one event.** A wick/return inside is labeled rejection; a hold/retest
   is labeled role reversal. Tolerance, number of bars, and “close inside” choices can relabel nearly
   the same path after observing its outcome.
3. **Intraday candle evidence is adverse after discipline.** Two relevant studies find that apparent
   candle predictability does not survive costs and data-snooping control in liquid equity/futures
   settings.
4. **Daily breakout evidence does not validate a retest.** Waiting for a pullback changes the event
   set, entry price, adverse selection, missed winners, and holding horizon. The retest must show
   incremental net value over the same frozen breakout baseline.
5. **“Higher-timeframe bias” and “last arch” are undefined.** Each adds discretionary state and
   creates another parameter family unless reduced to fixed causal Boolean rules.
6. **OHLC path ambiguity matters.** A bar can pierce, retest, trigger entry, and hit a stop in an
   unknown order. Conservative next-bar execution and explicit same-bar collision rules are required,
   but the source concepts do not supply them.
7. **The local prior is already poor.** The ideas are close to failed sweep, opening-range, and
   compression/breakout families. They cannot be introduced after those outcomes as “cheap” rescue
   variants; every variant is another counted trial.

## Decision

Keep I-41 and I-42 parked inside the I-33 compression/zone family. Do not test both directions, add
a higher-timeframe filter, or compare several retest definitions on development outcomes.

Reconsider only if an independently supported parent zone is fixed first and external evidence then
predefines one entry variant, one direction, causal next-bar execution, collision handling, stop and
day-flat exit, with realistic net out-of-sample improvement over the same plain-zone baseline. No
qualifying study was found.
