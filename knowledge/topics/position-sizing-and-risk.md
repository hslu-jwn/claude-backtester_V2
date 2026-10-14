# Position sizing and risk

Sources: K = Kaufman *TSM* ch. 2, 5, 21-24; D = Douglas; H = Hougaard. Applies to `risk/` (Phase 5),
which works on the R trade list. Spec: `docs/risk-management.md`.

## Basic rules
- Risk a small fraction per trade: never > 5 %, 1-3 % common (K p.1032). For FTMO's 10 % total
  loss, Douglas's test "can I lose the next 20 trades?" means ≤ 0.5 % per trade (D ch.11). → I-26
- Define the exit before entry; exit wrong trades fast; never average down; never meet a margin call
  (K p.1032; H "never add to losers").
- Large profits imply large risk: ask whether the account survives the same move the other way
  (K p.1027-1028). Be in the market as little as possible.
- Capital ≈ 3 × the historic max drawdown; plan for 1.5-2 × (K p.941). The historic max DD is a
  floor, not a forecast.

## Sizing methods
- Equal dollars, equal volatility and equal ATR risk give very different sizes. Prefer **ATR /
  volatility-based** sizing: equal risk per trade is the most conservative when trades cannot be
  ranked (K p.1050-1054). ATR sizing cut one stock's trend P/L volatility by ~27 %.
- Our R model already sizes each trade to its stop, i.e. equal risk per trade.
- **Volatility targeting:** scale exposure to target vol / lagged realised vol (10-20 day); rebalance
  only when the factor moves > 20 %; info ratio 1.27 → 1.38 over 17 years (K p.1142-1145).
  Target vol 6-15 % a year; 15 % is aggressive (K p.1046-1050). → I-27
- **Drawdown scaling (Turtles):** cut size 20 % for every 10 % drawdown, restore 10 % per ~6.7 %
  recovery (K p.231). For FTMO use finer steps of the 10 % limit. → I-26
- Kelly / optimal f: f = [p(PLR+1) − 1] / PLR. Over-betting leads to ruin; use only as an **upper
  bound** to *reduce* leverage (K p.1088-1092).
- Martingale / averaging down: works only in strongly trending low-noise markets with caps; blow-up
  risk; not for us (K p.1000-1011).
- Equity-curve trading (trade only when equity > its MA): inconsistent in Kaufman's tests (K p.1086).
  Check autocorrelation of trade outcomes first. → I-28

## Risk of ruin and "is it broken?"
- Equal win/loss: R = ((1−A)/(1+A))^c, A = 2p − 1, c = capital units (K p.1072).
- Unequal (Gehm/Vince): ruin = ((1−P)/P)^(MaxRisk/A) with P = ½(1 + Z/A); ruin grows faster than
  capital shrinks (K p.1073-1075; worked example 0.63 % → 7.9 % → 28 % as capital halves).
- Binomial probability of a loss streak and chi-square of live vs expected win rate decide whether a
  live system is broken (K p.1092-1097). With 20 trades win-rate error is ±20 points (D's sample).
- Douglas: do not size up after winning streaks (euphoria) or skip signals after losses (fear). Test
  whether outcomes after streaks differ from baseline; if not, flat fractional risk is justified.
  → I-28

## Risk measures beyond Sharpe
- Information ratio, Calmar (return / max DD), Sortino, Ulcer Index (RMS drawdown), average maximum
  retracement, time to recovery (K p.1034-1045). Use daily data; monthly data looks better than it is.
- VaR fails exactly in crises (kurtosis up to 25 vs 3 normal); use stress tests (K p.1034-1045).

## Portfolio
- Diversify across unrelated markets **and** strategy types; all trend followers share one profit
  source (correlation 0.4-0.8, same side 55-83 % of days) (K p.1021-1026, 1099-1106).
- Correlations go to 1 in crises; cap total leverage (K p.1105-1106).
- Mean-variance fails for trade streams (a strategy flat half the time looks low-risk); use a
  drawdown-based objective (K p.1114-1141).
- Benefit flattens after about 4 uncorrelated assets (K p.1100).

## FTMO context
- Hougaard sizes 2 % per unit and adds aggressively; that style would breach a 5 % daily limit
  quickly. Any pyramiding test must include the daily-loss guard.
- Carry unwinds (2008, 2020, Aug 2024) are violent; a carry-earning position can breach the 10 %
  limit (K p.596-599).

## From the day-trading books
- **Aziz:** max 2 % per trade (1 % conservative), size = risk / stop distance, minimum 2:1, 2-3 trades a
  day, scale only into winners, never average down, never hold overnight; **give-back rule:** stop for
  the day once 30 % of the morning's profit is lost. → I-26
- **Volman (ch.16):** fixed fraction of 1-2 % on the stop, recomputed once a day; same size for every
  valid setup (no "quality" sizing); one position at a time; ignore new setups while in a trade.
- Both are far too large for FTMO's limits: use 0.25-0.5 % per trade with a daily stop.
