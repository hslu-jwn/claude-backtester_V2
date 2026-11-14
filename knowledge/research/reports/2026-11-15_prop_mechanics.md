# Prop mechanics: sizing policy and concurrent weak streams (2026-11-15, Opus; Fable directions rows 2 and 13)

FTMO 2-Step pass chance on synthetic trades (-1 R or +1.5 R, p set for the edge), played by the house simulator
(`risk.monte_carlo.ftmo_by_risk`; static 10 % max loss, 5 % daily loss on the worst point incl. every open trade's
full stop, 4 days, no time limit). 150 histories per cell. Script: `research/screens/2026-11-15_prop_mechanics.py`.
**Pass % here counts attempts still open at the end of a history as not passed** (a policy that slows failures must
not look better by leaving attempts open), so the small-risk cells read lower than the pass map
(`2026-11-14_challenge_pass_map.md`, finished attempts only); the truth lies between.

## A. sizing policy, 1 trade a day: pass % (unfinished attempts count as not passed) / mean trading days to pass (both phases) / share of attempts still open at the end of a 4,000-day history
| edge R | policy | 0.25% | 0.50% | 1.00% | 2.00% |
|---|---|---|---|---|---|
| -0.02 | fixed | 7 % / 1152 d / 22 % open | 16 % / 343 d / 7 % open | 21 % / 94 d / 2 % open | 21 % / 27 d / 1 % open |
| -0.02 | adaptive | 5 % / 1267 d / 45 % open | 15 % / 454 d / 17 % open | 22 % / 139 d / 5 % open | 22 % / 42 d / 1 % open |
| +0.00 | fixed | 22 % / 1318 d / 27 % open | 28 % / 383 d / 7 % open | 29 % / 99 d / 2 % open | 25 % / 27 d / 1 % open |
| +0.00 | adaptive | 26 % / 1299 d / 48 % open | 30 % / 546 d / 18 % open | 31 % / 153 d / 5 % open | 27 % / 45 d / 2 % open |
| +0.02 | fixed | 45 % / 1131 d / 27 % open | 41 % / 373 d / 8 % open | 35 % / 95 d / 2 % open | 28 % / 27 d / 1 % open |
| +0.02 | adaptive | 44 % / 1422 d / 48 % open | 44 % / 659 d / 21 % open | 39 % / 166 d / 6 % open | 32 % / 46 d / 2 % open |
| +0.05 | fixed | 70 % / 943 d / 22 % open | 59 % / 339 d / 8 % open | 46 % / 94 d / 2 % open | 33 % / 27 d / 1 % open |
| +0.05 | adaptive | 69 % / 1113 d / 30 % open | 71 % / 571 d / 16 % open | 55 % / 180 d / 6 % open | 40 % / 52 d / 2 % open |

## B. K concurrent streams (one trade a day each), fixed risk per trade: pass % / months to pass (21 days) / daily-loss fails %
| edge per stream | rho | K | 0.25 % | 0.5 % | 1 % |
|---|---|---|---|---|---|
| +0.02 | 0.0 | 1 | 39 % / 49.4 m / 0 % | 40 % / 16.0 m / 0 % | 34 % / 4.4 m / 0 % |
| +0.02 | 0.0 | 2 | 51 % / 29.8 m / 0 % | 42 % / 8.9 m / 0 % | 32 % / 2.4 m / 0 % |
| +0.02 | 0.0 | 3 | 49 % / 20.9 m / 0 % | 40 % / 5.9 m / 0 % | 28 % / 1.6 m / 0 % |
| +0.02 | 0.0 | 5 | 54 % / 12.7 m / 0 % | 39 % / 3.5 m / 0 % | 0 % / nan m / 100 % |
| +0.02 | 0.3 | 1 | 39 % / 55.2 m / 0 % | 41 % / 16.9 m / 0 % | 35 % / 4.5 m / 0 % |
| +0.02 | 0.3 | 2 | 46 % / 27.6 m / 0 % | 40 % / 7.8 m / 0 % | 31 % / 2.0 m / 0 % |
| +0.02 | 0.3 | 3 | 47 % / 16.6 m / 0 % | 38 % / 4.3 m / 0 % | 27 % / 1.2 m / 0 % |
| +0.02 | 0.3 | 5 | 43 % / 7.6 m / 0 % | 33 % / 2.1 m / 0 % | 0 % / nan m / 100 % |
| +0.03 | 0.0 | 1 | 47 % / 50.1 m / 0 % | 44 % / 16.7 m / 0 % | 37 % / 4.5 m / 0 % |
| +0.03 | 0.0 | 2 | 54 % / 27.3 m / 0 % | 46 % / 8.5 m / 0 % | 34 % / 2.3 m / 0 % |
| +0.03 | 0.0 | 3 | 62 % / 19.8 m / 0 % | 47 % / 5.8 m / 0 % | 32 % / 1.6 m / 0 % |
| +0.03 | 0.0 | 5 | 63 % / 11.6 m / 0 % | 44 % / 3.4 m / 0 % | 0 % / nan m / 100 % |
| +0.03 | 0.3 | 1 | 48 % / 52.6 m / 0 % | 45 % / 16.3 m / 0 % | 38 % / 4.5 m / 0 % |
| +0.03 | 0.3 | 2 | 56 % / 23.8 m / 0 % | 45 % / 7.3 m / 0 % | 34 % / 2.0 m / 0 % |
| +0.03 | 0.3 | 3 | 56 % / 15.0 m / 0 % | 43 % / 4.3 m / 0 % | 29 % / 1.2 m / 0 % |
| +0.03 | 0.3 | 5 | 50 % / 7.6 m / 0 % | 38 % / 2.0 m / 0 % | 0 % / nan m / 100 % |
| +0.05 | 0.0 | 1 | 63 % / 40.6 m / 0 % | 60 % / 15.5 m / 0 % | 45 % / 4.3 m / 0 % |
| +0.05 | 0.0 | 2 | 74 % / 24.0 m / 0 % | 61 % / 8.4 m / 0 % | 42 % / 2.4 m / 0 % |
| +0.05 | 0.0 | 3 | 77 % / 16.2 m / 0 % | 59 % / 5.5 m / 0 % | 38 % / 1.6 m / 0 % |
| +0.05 | 0.0 | 5 | 81 % / 9.9 m / 0 % | 58 % / 3.2 m / 0 % | 0 % / nan m / 100 % |
| +0.05 | 0.3 | 1 | 65 % / 43.1 m / 0 % | 57 % / 15.8 m / 0 % | 45 % / 4.4 m / 0 % |
| +0.05 | 0.3 | 2 | 72 % / 20.4 m / 0 % | 57 % / 7.0 m / 0 % | 41 % / 2.0 m / 0 % |
| +0.05 | 0.3 | 3 | 72 % / 12.9 m / 0 % | 52 % / 4.2 m / 0 % | 34 % / 1.2 m / 0 % |
| +0.05 | 0.3 | 5 | 64 % / 6.9 m / 0 % | 45 % / 2.0 m / 0 % | 0 % / nan m / 100 % |

## Reading

1. **Adaptive risk does not beat fixed risk at equal time.** The house adaptive policy (risk x room to the loss
   line, floor 25 %, daily budget 3 %) raises the pass chance at the same base risk (+0.05 R at 0.5 %: 71 vs 59 %)
   only by trading smaller and slower (571 vs 339 days). At equal duration it gains about 0-3 points (+0.05 R:
   adaptive 1 % = 55 % in 180 days vs fixed ~52 % interpolated), below Fable's 5-point keep threshold; with zero or
   negative edge it changes nothing. Fixed small risk stays the simple choice.
2. **K uncorrelated streams divide the time to pass by about K at the same risk per trade** (+0.03 R per stream at
   0.5 %: 1 stream 16.7 months, 3 streams 5.8, 5 streams 3.4; pass chance ~44-47 % throughout). Correlation 0.3
   costs a few points at K = 3 and up to ~6-17 points at K = 5.
3. **The daily-loss rule caps concurrency:** with K trades open together the worst point counts K full stops, so
   K x risk per trade must stay below the 5 % daily limit with room: 5 streams at 1 % fail 100 % of attempts on the
   daily loss. Keep K x risk <= ~3 %.
4. Fable's closed form (three +0.03 R streams at 0.5 %: ~64 % in ~9 months) is too optimistic on the pass chance;
   the simulator gives ~47 % in ~6 months (it ignored the daily-loss rule and fat tails).
5. None of this creates an edge: with zero edge every policy stays near the ~30 % luck baseline. The value of
   several weak streams is time, which matters only once each stream is net positive.

Caveats: iid synthetic trades, one payoff shape, streams of equal edge, trades of a day held together for the whole
day (a conservative daily-loss case); end-of-history open attempts lower the small-risk pass chances.
