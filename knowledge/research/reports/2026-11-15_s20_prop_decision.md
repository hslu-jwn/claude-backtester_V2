# Strategy 20 at a crypto prop firm: decision package (2026-11-15, Mode=auto; the decision is the user's: money)

**What:** the frozen top-100 Strategy 20 book (`docs/strategy-crypto_flow.md` › Liquid variant), weekly long the top /
short the bottom quintile of 7-day taker flow, run as **7 weekday tranches** (1/7 of the notional rebalanced each day),
on HyroTrader's Two-Step (Bybit demo). Fair forward expectation **~+92 bp a week** per unit side (all-anchor mean,
measured taker ~10 bp a fill, ~55 % turnover). Evidence: one-time test passed (full universe +147, t 3.76; top 100 +166,
t 3.06, diagnostic); robust to the rebalance day; edge switched legs between periods (long-short only).

**Pass chance (Two-Step +10 % then +5 %, 5 % daily loss on start-of-day equity, 10 % static max, 40 % best day; test
weeks bootstrapped at +92 a week; `research/screens/2026-11-15_s20_prop_intraday_tranches.py`):**

| notional per side | daily close marks | hourly close marks (closest to Bybit mark price) | hourly wick bound (all coins at their hourly extreme at once) | median time to pass (wick bound) |
|---|---|---|---|---|
| 10 % | 100 % | ~100 % | 99 % | ~2.9 years |
| 15 % | 96 % | ~96 % | 44 % | ~1.6 years |
| 25 % | 86 % | 86 % | 28 % | ~0.8-1 year |
| 50 % | 49 % | 50 % | 8 % | ~0.2-0.4 year |

**Reading:** hourly closes change nothing against daily closes (worst day -1,463 vs -1,443 bp of one side's notional),
so the daily rule is not a problem at the hourly level; only simultaneous single-exchange wicks are. Bybit values open
positions at a mark price built from several exchanges, which smooths such wicks, so the truth is expected near the
close-mark column but is **not verified**.

**Recommendation (Opus):** if the user buys a challenge, take the HyroTrader Two-Step on the smallest balance, run the
tranched top-100 book at **15 % notional per side** (95 %+ on realistic marks, ~1.5 years; drop to 10 % after any day
that loses more than 2.5 %), and treat the first 13 weeks as the live cost / fill test Fable called a pilot. Expected
funded income at 15 % per side: ~0.14 % of balance a week, ~7 % a year before the 80-90 % split.

**Before paying (the user):** (1) ask HyroTrader in writing: is the 5 % low-cap cap measured on our top-100 coins
(market cap source?), are 40-60 simultaneous basket orders and weekly rebalancing by API fine, is max loss static;
(2) confirm the fee (59-69 USD, refundable) and payout terms; (3) the funded money is simulated at most such firms:
payout-denial risk is the main unmodelled loss. Strategy 19 stays out until its forward boundary confirms.
