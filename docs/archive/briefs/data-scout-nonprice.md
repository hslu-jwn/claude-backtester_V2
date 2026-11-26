# Brief: data scout for free non-price data sets (read-only, web search)

Model: Codex `gpt-6.1-terra` (read-only, `--search`). Write nothing in the repo. Never ask for or use credentials;
never sign up for anything. Answer in your final message only.

## Goal

Find FREE, downloadable, historical data sets that measure a FORCED or CONSTRAINED trader (someone who must trade on
a known rule or date: index funds, hedgers, liquidations, funding / margin, rebalancing, auctions, settlement,
expiries), usable with prices we already have. Research rule M12: data sets, not strategies.

Hard filters (drop anything failing one):
- free and downloadable without a paid plan (a free API key is fine; say so);
- history that covers 2020-01 .. 2023-12 for crypto, or starts before 2015 for rates / FX / indices / US shares;
- 100+ names (cross-section) OR a single series with 300+ independent events (e.g. monthly 1990+);
- point-in-time (values known at their timestamp, not revised later; say if revised).

Venues we can trade or price: Binance USD-M perps (daily klines, taker volume, funding already cached), US Treasury
futures / yields (FRED), CME futures (no paid data), real US shares (Alpaca SIP from 2016), FTMO CFDs.

Already have (do not report): Binance klines / taker volume / funding / spot, Binance futures metrics (open interest
only from 2021-12 for the cross-section), Bybit daily prices, Hyperliquid daily candles, FRED yields, ECB / BoE / MOF
yields, TreasuryDirect auctions, Cboe VIX and VX settlements, SqueezeMetrics DIX / GEX, FINRA short volume, SEC
fails-to-deliver, SEC insider Form 4, SEC N-PORT, Wikipedia page views, EIA energy strips, CFTC COT (known).

Stop proposing (dead on our data; knowledge/topics/cost-wall.md §4): bar patterns, oscillators, MA crosses,
session / time-of-day rules, gap fade, ORB, turn of month on equity indices, day-of-week, pre-holiday, generic option
expiry weeks, cross-market daily lead-lag, VIX futures roll, commodity index roll, generic trend following.

Search at least: crypto exchange archives (OKX, Bybit, Deribit, Coinbase, Kraken public data portals; liquidation
history; options open interest / expiry by strike; perp open interest history per symbol before 2021-12); crypto
on-chain flows with exchange labels (free tiers); Treasury / Fed (primary dealer statistics, SOMA holdings, TIC,
reverse repo, Treasury General Account); index provider rebalance / extension announcements (Bloomberg, ICE, FTSE
Russell, S&P) as historical files; ETF creation / redemption or shares outstanding history; pension / insurer
rebalancing proxies.

## Output (final message), max 15 items, best first

For each: name | URL of the download or API doc page you opened | one verbatim sentence from that page proving the
history start or coverage | history start, frequency, number of names | who is forced to trade and on what rule |
which of our venues it would price | free tier limits | a falsifiable one-line prediction it enables.
Mark VERIFIED only if you opened the page and the quote is on it; otherwise UNVERIFIED. Never invent a URL.
