# Costs and execution

Sources: K = Kaufman *TSM* ch. 1, 8, 16, 21-23; H = Hougaard; RC = Carver ch.12; KD = Davey; EC = Chan; JK = Kaeppel;
LP = López de Prado.

- **Costs decide fast systems.** Systems with > ~200 trades in 20 years were clearly worse; 5-day MA
  systems lose everywhere (K p.315, 347-348). Davey agrees: optimising without costs favours systems that trade too often
  with a tiny edge per trade, and he discards any report with zero costs (KD ch.6). Carver puts a number on it below. Small ORB breakouts earned $5-25 per trade before costs
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

## Scalping arithmetic (Volman)
- Volman's EURUSD economics: spread 1 pip = 10 % of the 10-pip target; risk 6-7 pip; break-even win rate
  about 41 % at +10 / -7 (spread included). The trade starts at -1 pip, so a 10-pip target needs 11 pips of
  chart travel (V ch.14).
- A fixed 10/10 bracket does not carry over: estimates (to measure on our data) put the spread at
  20-35 % of a 10-pip target on GBPJPY and XAUUSD. Scale the target in ATR and require
  target >= 10 x spread, i.e. target = max(2.5-5 x M1 ATR(14), 10 x spread); skip when spread/target
  > 0.10-0.15. → I-45 (cost-to-target filter, also HANDOFF open point 3)
- Stop orders hit at market slip 1-1.5 pip in fast markets; news spreads widen up to 10 pip (V ch.1, 8).
  Avoid releases or model wide spreads.
- Histdata M1 has **no volume** (column always 0, checked 2026-10-14) and no tick spread. M1 bars are
  about 2x coarser than Volman's 70-tick bars (~30 s in active hours), so signal-bar/entry-bar details
  inside one M1 bar are lost; SL-first applies.

## Cost speed limit (Carver, ch.12)
Sources: RC ch.12 (Tables 34-36), ch.2 (Table 2). Idea link: I-52.
- **Rule of thumb: trading costs must never exceed one third of a conservative pre-cost Sharpe.** Assume a maximum pre-cost SR of 0.40
  for a staunch system trader (annual cost limit 0.13 SR) and 0.25 for discretionary / static (limit 0.08).
- **Standardised cost per round trip** (in Sharpe units) = 2 × cost of one block / (16 × daily instrument currency volatility); a small
  trader pays about half the bid-ask spread per trade plus fees. Annual cost = turnover (round trips a year of an average position)
  × standardised cost; turnover from a backtest = blocks traded per year / (2 × average absolute blocks held). Low-volatility
  instruments have higher standardised cost (cheap futures 0.001-0.002, index spread bet 0.01, low-vol bond ETF 0.08).
- Maximum standardised cost = limit / turnover. At 0.08 SR: a 1-day hold (turnover 256) needs 0.0003, which no instrument offers;
  3 days (85) 0.001, 1 month (12) 0.0067, 6.5 weeks (8) 0.01, 3 months (4) 0.02, 1 year (1) 0.08 (Table 34). At 0.13 SR: turnover
  128 / 54 / 28 / 12.5 / 7.5 → 0.001 / 0.0024 / 0.0046 / 0.01 / 0.017 (Table 35). **Day trading (500+ round trips) needs about
  0.00025 per round trip: effectively zero spread, impossible for retail without a proven execution edge.**
- Table 2: if a monthly-holding rule has SR 0.40, theory gives 0.83 weekly, 1.8 daily, 5.2 hourly gross; after retail spread-bet
  costs 0.28 / 0.27 / −0.75 / −2.5 / −16.4. Speed pays only with tiny costs.
- Faster rules show no consistent higher pre-cost Sharpe; most markets do not trend at short horizons. Costs should be compared
  after costs when setting the vol target. Use *today's* costs for old data (old costs were higher, so fast rules may only look good).
- Position inertia (10 % band) and a slower volatility look-back cut turnover; slow vol estimation matters only for very slow systems
  (Table 36). More expensive instruments are not worse after costs if turnover is under ~15 a year.
- Our R model: express spread + commission in R of the stop and in Sharpe units per round trip, then check turnover × cost against
  1/3 of the plausible pre-cost Sharpe (a new screen, not yet built).

## Execution realism (Davey, Chan, Kaeppel, López de Prado)
- Davey: slippage 1-2 ticks per round trip for market and stop orders, 0 for limits; a limit order filled merely on touch overstates
  results, require penetration; bid-only forex data creates phantom fills, so use market orders plus spread; reversing a loser pays costs
  twice; same-bar stop and target is a red flag (KD ch.6, 11, 14). His live fills were better than the backtest only because the
  assumption was conservative.
- Chan: his example Sharpes **exclude costs** (stated repeatedly, EC p.49, 63, 88, 120); open-price signals cannot be traded at the open
  (EC p.95); FX needs bid/ask from the venue you trade (EC p.11); rollover interest matters only for multi-day holds, triple day by
  settlement (EC p.113-115).
- Kaeppel (options, but the principle transfers): a round trip at market costs the whole spread; a market-on-open order after a gap is
  filled far from the plan; limit entries risk missing the move (JK p.113-116).
- López de Prado: implementation-shortfall statistics: fees and slippage per unit of turnover, dollar performance per unit of turnover
  (how much costlier execution can become before break-even), return on execution costs (should be a large multiple) (LP 14.6).
  The Roll estimator (2·sqrt(−cov of consecutive price changes)) and the Corwin-Schultz two-bar high-low estimator give an effective spread
  from OHLC alone, a cross-check for the spread table (LP 19.3).
