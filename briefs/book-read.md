# Brief: read one trading book and return a book note (read-only)

The book's text file and short code are named in the prompt. The text is `results/books/<file>.txt`
(pdftotext -layout; find printed page numbers in the text, cite as `<CODE> p.<page>`).

Do NOT read the whole file into one pass blindly: first find the table of contents (`rg -n "Contents|CHAPTER|Chapter" ...
| head`), then read the chapters with trading rules, flows or effect sizes. Skip pure pricing math, biography, psychology.

## Context (our project)

Rule-based research. Venues: FTMO CFDs (forex, indices, gold; costs kill short holds), exchange futures,
real US shares (long-short, daily data via Alpaca), Binance crypto futures. We want effects with a
**mechanism** (a counterparty that must trade: rebalancing, hedging, index rules, settlement, funding, issuance) and a
**size in bp per event or per day**, testable on daily or M1 price data or free public data.

Already judged / stop proposing (do not list these as new ideas, only map a book idea to them by name):
any M15 / H1 bar pattern, oscillator, MA-cross, candle rule at short stops; gap fade / gap momentum; ORB; FX relative
strength baskets; pre-holiday, day-of-week, pre-FOMC drift, macro-day long, month-end / turn-of-month in any form,
option-expiry effects; daily lead-lag across markets; VIX futures basis / roll; commodity index roll front-running;
diversified or single-symbol trend following at any speed; daily reversal; crypto carry and taker-flow (already built);
Treasury month-end duration (already built); index additions / deletions; spin-offs; COT positioning; FX carry.

## Output (your answer, markdown, max ~250 lines)

```
# <Author>, *<Title>* (<publisher year>)

Short: **<CODE>**. Cite by printed page (`<CODE> p.N`). Read <date> by Codex; PDF in the library folder Tier 3.
<3-5 line summary of what the book is about.>

## Testable ideas
For each concrete rule or effect (max 12, best first):
- **<name>** (<CODE> p.N): exact rule (entry, exit, holding, universe), mechanism claimed, effect size and sample as
  the book states it (quote numbers verbatim, max one short quote each), data needed, our venue, and
  `MAPS TO: <judged family>` or `NEW`.

## Method notes
Useful backtest / risk / portfolio method points (max 10 bullets, page refs).

## Verdict
One paragraph: which NEW ideas (if any) have a mechanism + stated size worth a card, which do not and why.
```

Rules: page refs for every claim; never invent numbers; if the book gives no size, say "no size given".
Read-only: change no files.
