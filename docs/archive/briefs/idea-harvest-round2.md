# Brief: harvest testable strategy ideas from the internet (2026-11-10)

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`, never send
repository content, credentials or account data to any website; only read public pages). Use your web
search / browsing if available; if you have no web access, say so in the first line and stop.

## What we can test

M1 history 2015-2021 (development) of FTMO CFDs: FX majors and crosses (EURUSD, GBPUSD, USDJPY, AUDUSD,
NZDUSD, USDCAD, USDCHF, EURJPY, GBPJPY, AUDJPY, EURAUD, ...), XAUUSD, XAGUSD, USOIL, UKOIL, NATGAS,
US500, NAS100, US30, GER40, UK100, JP225, AUS200, BTCUSD, ETHUSD (+ Binance futures with funding rates).
Rule-based, stop-defined, results in R; day trades and multi-day holds (swap counted). Costs: about
1-2 bp round trip on FX majors / US500, more on crosses, metals, energy, crypto; the lesson so far
(`knowledge/topics/cost-wall.md`, read it) is that small intraday edges of 0.01-0.03 R lose to costs of
0.04-0.06 R per trade: favour ideas with larger moves per trade (wider stops, longer holds, event-driven,
volatility regimes) or rare high-quality setups.

## Already tested or screened out (do not propose again)

Read `docs/research-log.md` (2026-11-09 sections) and `docs/strategy-timed-hold.md` (hypotheses 1-12):
session zone sweeps, NY index sweep, no-wick candles, Kaufman trend following (breakout, SMA band,
momentum, KAMA), gap fade, opening-range breakout, gap momentum, London fix reversal, alternating M15
path, H1 shock response, FX local-hours drift (Breedon-Ranaldo), FOMC day, turn of month (index), RSI(2)
mean reversion, momentum on large-move days, overnight drift, carry, Gotobi, month-end fix, OPEX,
pre-holiday, calendar x clock screens (FX, indices).

## Task

Find 12 distinct, concrete, rule-based ideas from the source types below. Ideas need not be
academically backed (practitioner lore is fine), but they must be specific enough to code. For each:
name; source(s) with URL actually opened; exact rules (instrument, timeframe, entry, stop, exit, filters);
claimed performance if any; mechanism (why it could work); expected trades per year; rough gross move per
trade vs our costs; label (PUBLISHED / PRACTITIONER / SPECULATIVE). Then rank your ideas by how likely
they clear our costs. No hype; say when a claim looks curve-fit.

Write `knowledge/research/reports/2026-11-10_idea_harvest_round2.md`. Report the file and your top 5.

## Source types and focus (this brief, round 2)

Also not again: EIA oil report (falsified), Connors 8-day reversal / capitulation (falsified), crypto
intraday half-hour momentum (2.8 bp gross, below costs), everything in
`knowledge/research/reports/2026-11-10_idea_harvest_*.md`. Focus: setups whose typical gross move per trade
is >= 30 bp and that occur >= 50 times a year across our symbols, or multi-day crypto ideas that survive
FTMO crypto costs (6.5 bp round trip + about 8 bp per night swap). Sources: Substack / X (Twitter) quant
threads with backtests, prop-firm trader blogs, Market Wizards-style interviews with explicit rules,
volatility-regime and volatility-breakout systems (e.g. Larry Williams, Toby Crabel, Linda Raschke),
weekly-chart systems, crypto-native research (Glassnode, Kaiko, Amberdata public posts) on weekly
seasonality, halving cycles, funding extremes and exchange-flow signals that map to price-only rules.
