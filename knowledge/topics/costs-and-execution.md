# Costs and execution

Sources: K = Kaufman *TSM* ch. 1, 8, 16, 21-23; H = Hougaard.

- **Costs decide fast systems.** Systems with > ~200 trades in 20 years were clearly worse; 5-day MA
  systems lose everywhere (K p.315, 347-348). Small ORB breakouts earned $5-25 per trade before costs
  (K p.760-764).
- Kaufman's published results are mostly **gross**. Our results are net of spread, commission and
  swap; expect them to look worse than the book's.
- Trend (directional) entries pay full slippage; mean-reversion entries about half (K p.22, 742).
- Do not overstate costs either; that is as misleading as understating them (K p.22). Run 0 /
  realistic / stressed levels (see [testing-and-robustness.md](testing-and-robustness.md)).
- Slippage grows with volatility and order size; model at least slippage ∝ volatility with a floor
  (K p.743). Spreads widen around news; any news-time strategy (shock fade, ORB at data releases)
  must model wider spreads.
- Missed fills after news jumps remove only winners: 10 % unfilled turned PF 1.66 → 1.50 (K p.742).
- Open-to-close is about half the day's range; capturing a quarter of the daily range is the realistic
  ceiling for day trades (K p.740).
- Paper trade with the worst price of the next 5 minutes after an intraday signal (K p.988).
- Monitor live slippage against the system price (K p.980).
- **Swap:** holding overnight costs swap on CFDs (17:00 New York rollover, triple on one weekday).
  FTMO XAUUSD longs cost about $61 per lot per night (ROADMAP 10.4), which killed strategy 4.
  Day trades closed before 17:00 New York avoid it. Positive swap (e.g. long GBPJPY, depending on
  rates) is the only cost that can earn money → carry idea I-29.
- Spreads are much lower today than in 1999 (DAX 0.9 pt vs 6-8), yet retail failure rates are
  unchanged (H). Costs are not the main reason traders fail; behaviour is.
- Reversals (stop-and-reverse) pay the spread twice; separate exits from entries (K ch.23).
