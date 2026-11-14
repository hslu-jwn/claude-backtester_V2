# FTMO 2-Step challenge pass map (2026-11-14, Opus; Fable directions row 1)

What net edge per trade, at which risk and trade count, passes the FTMO 2-Step challenge. Synthetic iid
trades (-1 R stop or +1.5 R target, p set for the mean; sd about 1.22 R), played by the house simulator
(`risk.monte_carlo.ftmo_by_risk`: 10 % then 5 % target, static 10 % max loss, 5 % daily loss on the worst
point incl. the open trade's full stop, 4 trading days). No time limit (ftmo.com trading-objectives page,
read 2026-11-14 by a web-fetch subagent: no maximum number of days stated, banner "No time limit").
200 histories of 12,000 trades per cell, attempts chained. Script:
`research/screens/2026-11-14_challenge_pass_map.py` (self-check: zero edge at 0.25 % risk passes 31.6 %,
closed form 0.5 x 10/15 = 33 %). Not a strategy test; no market data.

## Pass chance per attempt (1 trade a day; trades to pass in brackets, both phases)

| Net edge R / trade | 0.25 % risk | 0.5 % | 1 % | 2 % |
|---|---|---|---|---|
| -0.05 | 1 % | 8 % | 16 % | 18 % (27) |
| -0.02 | 10 % | 19 % | 23 % | 22 % (27) |
| 0.00 | 31 % (1,360) | 31 % (370) | 29 % (97) | 25 % (27) |
| +0.02 | 59 % (1,370) | 45 % (370) | 36 % (96) | 28 % (27) |
| +0.05 | 87 % (1,010) | 64 % (340) | 46 % (94) | 33 % (27) |
| +0.10 | 99 % (580) | 89 % (260) | 64 % (88) | 42 % (26) |

4 trades a day: the same numbers up to 1 % risk (trades to pass about equal, days a quarter). At 2 % risk
with 4 trades a day 96-98 % of attempts fail on the daily loss: after two losses (-4 %) the next entry's
worst point (another -2 %) already breaches 5 % (the simulator's conservative worst-point rule, user
2026-10-15).

## Reading

1. **Luck alone passes about 30 %** (zero net edge, any risk up to 1 %); a typical cost-dominated stream at
   -0.02 to -0.05 R still passes 10-23 % at 1 % risk. The baseline to beat is therefore about 30 %, not 0.
2. **Small risk converts a small edge into a high pass chance, at the price of trades:** +0.05 R needs about
   1,000 trades at 0.25 % (87 %) or about 340 at 0.5 % (64 %). +0.02 R barely helps at 1 % risk (36 %).
3. **Bold play only helps a negative edge** (higher risk lifts -0.05 R from 1 % to 18 %); for any positive
   edge lower risk is better if time is free.
4. **Required size for research (goal 1):** a stream worth building needs about **+0.05 R net per trade and
   about 300+ trades a year** to pass in about a year at 0.5 % risk (64 %); +0.10 R net passes 89 % in about
   260 trades. Below +0.02 R net the challenge pass chance is within about 10 points of luck.
5. Open (Fable rows 2, 3, 13): sizing policies, the funded phase (payout every 14 days, 80 % split by default
   for 2-Step per the FTMO FAQ, read 2026-11-14) and combining weak streams; the economic value per fee is
   the user's money question, not research.

Caveats: iid trades (real streams cluster; the simulator's block bootstrap on a real R list is the check),
one payoff shape (B = 1.5), costs assumed inside the net edge, the last attempt of each history unfinished
(about 1 per history, so passes needing more trades than remain are slightly under-counted at 0.25 %).
