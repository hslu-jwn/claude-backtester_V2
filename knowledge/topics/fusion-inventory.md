# Fusion inventory

Purpose: inventory recorded components for possible combinations. Date: 2026-11-19. Facts copied from records, no new data look. No fusion is claimed to work.

Source key: [L:id] = research/ledger.csv row; [CW section 1] = knowledge/topics/cost-wall.md section 1; [RL date] = docs/research-log.md on that date; [I:id] = knowledge/ideas.md card; [S19] and [S20] = docs/strategy-crypto_carry.md and docs/strategy-crypto_flow.md; [H] = docs/HANDOFF.md; [screen:file] = research/screens/file; [cache] = folder listing. Unless stated, t is the reported net statistic; gross and cost are not interchangeable with net.

## 1. Alive and near-live streams

| id | what | venue / symbols | dev period | gross edge | t | test result | regime notes | status / source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S19 / I73 | funding-ranked long-short carry | Binance USD-M perps | 2020-02..2021-09 | +158 bp/week (price +106, funding +52) | 1.30 | +112 bp/week net, t 2.93 | dev halves +2 / +274; test +105 / +119; unseen-universe replication +63, t 1.05 | paper forward only; replication failed [S19] [L:I73R] |
| S20 / I78 | weekly taker-flow long-short | Binance USD-M perps | 2020-05..2023-12 | +165 bp/week | 3.24 | +147.2 bp/week net, t 3.76 | dev halves +327 / +2; test +120 / +174; tail-sensitive | alive; forward paper [S20] [L:I78] |
| I109 | month-end long duration | US 10-year Treasury; DGS10 / IEF; Micro 10Y path | 1990-01..2021-09 | +20.4 bp/month-end excess | 4.42 | +24.9 bp net, t 2.14; IEF +23.2 | test not blind; monitor weekend month-ends | passed; shelf forward [L:I109] [RL 2026-11-17] [H] |
| I100 | wide funding carry | unseen Binance perps | 2021..2023 | +127.1 bp/week | 2.45 | n/a (not recorded) | net halves +152 / +63 | unproven-positive; shelf [L:I100] [H] |
| I84 | spot-minus-perp flow | Binance spot / perps | 2020..2023 | n/a (not recorded) | 1.76 | n/a (not recorded) | net halves +150 / +8; correlation with S20 0.58 | unproven-positive; shelf [L:I84] [RL 2026-11-15] [H] |
| I98 | spot-hedged funding carry | Binance spot / perps | 2020..2023 | +45.2 bp/week | 1.84 | n/a (not recorded) | net halves +55 / -22 | unproven-positive; shelf [L:I98] [H] |
| H11 | Gotobi USDJPY long | USDJPY | 2015..2021 | n/a (not recorded) | n/a (not recorded) | +0.021 R/trade net; bootstrap lower -0.012 | dev +0.040 R/trade net; pre-sample +30.9 R net | unproven-positive; shelf [L:H11] [H] |
| I71 | index-review closing-auction short | UK100 CFD | 2010..2021 | +11.7 bp/event | 2.16 | n/a (not recorded) | pre-sample +12.5 / dev +6.5 bp | unproven-positive; shelf [L:I71] [H] |
| I105 | overnight-to-close reversal at official open | US shares | 2016..2021 diagnostic | +12.9 bp/day | 3.94 gross | forward only | diagnostic of I102; not a development cell | shelf, forward only [L:I105] [L:I102] [RL 2026-11-17] [H] |

## 2. Components with a measured positive gross edge

Gross R values in the ledger are per trade except L14, which is a total. A positive figure may describe one cell, not the whole family. Blank statistics are explicitly unrecorded here.

| id / what | venue / symbols | dev period | gross edge | t | test result | regime notes | cost | why killed / status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S02 NY open index sweep | NAS100,US500 | 2020-26 (V1) | 0.018 R/trade | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | 0.055 | falsified [L:S02] |
| S05 Index gap fade | NAS100,US500 | 2020-26 (V1) | 0.047 R/trade | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | 0.024 | no edge (OOS 2018-19 net -0.080; walk-forward +0.6 R) [L:S05] |
| S06 Opening-range breakout | 18 symbols | 2015-21 + 2021+ test | 0.116 (test) | t ~1.5 | n/a (not recorded) | n/a (not recorded) | 0.016 (test) | not confirmed (t ~1.5; fading since 2024) [L:S06] |
| S07 Gap momentum | NAS100,US500,GBPUSD,EURUSD,XAUUSD | 2015-21 | 0.002 R/trade | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | n/a | falsified; quiet-sideways cell pre-registered for the one-time test [L:S07] |
| S08 London fix reversal | 6 USD pairs | 2015-21 | 0.017 R/trade | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | 0.117 | rejected by the user 2026-10-29 [L:S08] |
| H01 F1a EURUSD short 07:00-13:00 London | EURUSD | 2015-21 | 0.066 R/trade | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | 0.023 | closed: failed its pre-sample check 2008-14 (bootstrap -0.009); lead expired (review tip 5) [L:H01] |
| H01b F1b USD-hours long EURUSD | EURUSD | 2015-21 | 0.046 R/trade | n/a (not recorded) | n/a (not recorded) | halves / bootstrap / breadth) | 0.024 | falsified (costs x2 / halves / bootstrap / breadth) [L:H01b] |
| H02 F2 last-30-minute momentum | US500,NAS100,UK100,GER40,EU50 | 2015-21 | 0.010 R/trade | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | 0.044 | falsified after costs (sign right gross) [L:H02] |
| H06 F2L momentum on large-move days | US500 | 2015-21 | 0.008 R/trade | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | 0.043 | falsified [L:H06] |
| H07 F1X European-hours cross shorts | EURJPY,EURAUD,GBPJPY,GBPAUD | 2015-21 | 0.015-0.025 | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | 0.04-0.06 | falsified after costs (sign right gross) [L:H07] |
| H10 I-03 RSI(2) index mean reversion | US500,NAS100 | 2015-21 | 0.006 R/trade | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | n/a | falsified [L:H10] |
| L14 us_close_de_open | GER40,UK100 + US refs | 2015-01-02..2021-09-13 dev | 8.8 R total; +0.015 R/trade [CW section 1] | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | 13.4 | FALSIFIED 2026-11-12 (primary mean net -0.008 R; bootstrap lower -0.041; effect vs control lower -0.020; all 8 S cells falsified; UK100 primary -39.1 R) [L:L14] |
| L15 oil_cad_leadlag | USDCAD,USOIL | 2015-21 | gross +1.20 bp | t -0.18 | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | SCREEN FAIL 2026-11-12: stays a card (primary, timed hold, no stop: gross +1.20 bp, cost 1.67 bp, net -0.47 bp per trade; t -0.18; vs control +1.21 bp) [L:L15] |
| L17 gold_silver_leadlag | XAGUSD,XAUUSD | 2015-21 | gross +3.68 bp | t -2.68 | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | SCREEN FAIL 2026-11-12: stays a card (primary, timed hold, no stop: gross +3.68 bp, cost 15.46 bp, net -11.77 bp per trade; t -2.68; vs control +3.69 bp) [L:L17] |
| P01 wti_brent_spread (DRAFT) | USOIL,UKOIL | 2015-06..2021-09 dev | gross +209.3 bp | t -0.78 | n/a (not recorded) | halves -279.5 / +31.2 | n/a (not recorded) | KILLED 2026-11-12 (pre-build screen): gross +209.3 bp, net -124.2 bp per trade (t -0.78), halves -279.5 / +31.2; cost about 333 bp = both legs' swap over ~17.5 days [L:P01] |
| P02 gold_silver_ratio (DRAFT) | XAUUSD,XAGUSD | 2015-06..2021-09 dev | gross +20.4 bp | t -0.26 | n/a (not recorded) | halves +18.1 / -46.4 | n/a (not recorded) | KILLED 2026-11-12 (pre-build screen): gross +20.4 bp, net -14.1 bp per trade (t -0.26), halves +18.1 / -46.4 [L:P02] |
| I67 Month-end rebalancing with a conditional sign | US500 | 2015-01..2021-08 dev | gross +19.9 bp per month | t 0.95 | n/a (not recorded) | halves +38.1 / +7.8 bp | n/a (not recorded) | KILLED 2026-11-12 on t < 2 (signed gross +19.9 bp per month, t 0.95; halves +38.1 / +7.8 bp; net +14.2 bp) [L:I67] |
| I69 Bitcoin CME futures expiration week (I-69) | BTCUSD | 2018-01..2021-08 dev | gross +95 bp other weeks | n/a (not recorded) | n/a (not recorded) | halves -181 / -23) | n/a (not recorded) | KILLED 2026-11-12: net -100 bp per week (gross -60, t -0.72, 46 % positive; halves -181 / -23); other weeks gross +95 bp [L:I69] |
| I70 Option-expiration week on US500 (I-70) | US500 | 2010-01..2021-08 (pre-sample + dev) | gross +8.7 | t -0.19 | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | KILLED 2026-11-12: net -3.8 bp per week (gross +8.7, t -0.19); pre-sample +4.8 / dev -9.1 bp; other weeks gross +31.1 bp [L:I70] |
| I72 Funding-settlement drift Binance perps (I-72) | BTCUSDT,ETHUSDT | 2020-01..2021-09-13 dev | gross +2.3 bp POST | t -1.7 POST | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | KILLED 2026-11-13: PRE gross -0.3 bp net -10.3 (t -3.1); POST gross +2.3 bp net -7.7 (t -1.7); no-settlement hours 04/12/20 similar (+4.4 / -1.4 bp) [L:I72] |
| I76 Liquidation-cascade reversal 37 Binance perps (I-76) | 37 USD-M perps | 2020-01..2021-09-13 | +7.0 bp | t 2.50 | n/a (not recorded) | halves +0.0 / +14.8 | 10 bp | M1 (2026-11-17): FALSIFIED. KILLED 2026-11-14: t 2.50 < 3.0; net -4.7 bp at 20 bp (halves +0.0 / +14.8; long side +14.4 bp gross, short -6.9; BTC+ETH -14.7 t -3.19) [L:I76] |
| I81 New-listing drift on Binance USDT perps (I-81) | USDT perps listed 2020-03..2023-11 | 2020-01..2023-12 (crypto split) | +632 bp/event | t 1.16 | n/a (not recorded) | n/a (not recorded) | 20 bp | KILLED 2026-11-15: t 1.16 < 3.0 (median event +1,948 bp; right-tail squeezes) [L:I81] |
| I85 Noise-band intraday momentum US indices (I-85) | US500,NAS100,US30 | 2015-21 | +2.95 bp/trade | t 0.37 | n/a (not recorded) | halves +0.9 / -0.3 | 1.70 bp | KILLED 2026-11-15: t 0.37; halves +0.9 / -0.3; family orb closed (2 falsifications) [L:I85] |
| I88 SMT divergence at the session extreme NAS100 vs US500 (I-88) | NAS100,US500 | 2015-21 | +1.7 bp | t -0.17 | n/a (not recorded) | n/a (not recorded) | 2.0 bp | KILLED 2026-11-15: t -0.17; SMT no edge either direction (confirmed-breakout control +4.1 bp t 2.33, diagnostic only) [L:I88] |
| I89 Intraday rotation NAS100 vs US500: follow the morning relative move (I-89) | NAS100,US500 | 2015-21 | +1.3 bp | t -4.19 | n/a (not recorded) | n/a (not recorded) | 4.4 bp | KILLED 2026-11-15: t -4.19 (gross below two-leg cost) [L:I89] |
| I91 ICT previous-day high / low raid with timed exit (I-91) | US30,GER40,NAS100,US500,UK100,EURUSD,USDJPY,XAUUSD | 2015-21 | +2.5 bp | t -0.87 | n/a (not recorded) | n/a (not recorded) | 1.6 bp | KILLED 2026-11-15: t -0.87 (US indices positive per symbol, post-hoc) [L:I91] |
| I93 Candle range theory on H4 (I-93) | US30,GER40,NAS100,US500,UK100,EURUSD,USDJPY,XAUUSD | 2015-21 | +0.8 bp | t -0.87 | n/a (not recorded) | n/a (not recorded) | 1.4 bp | KILLED 2026-11-15: t -0.87 [L:I93] |
| I96 Overnight -> intraday reversal sort, 33 US share CFDs (I-96) | 33 US share CFDs (spread <= 10 bp) | 2010-01..2021-09-13 (Yahoo daily) | +10.1 bp | t -2.64 | n/a (not recorded) | halves +1.2 / -13.6 | 16.1 bp | KILLED 2026-11-15: t -2.64 (gross t 4.44); halves +1.2 / -13.6; gross fades to negative 2019-2021; extreme names carry the wide spreads [L:I96] |
| I97 Cross-sectional 3-week momentum, all Binance USDT perps (I-97) | all USDT perps incl. delisted | 2020-01..2023-12 (crypto split) | +60.1 bp/week | t 0.68 | n/a (not recorded) | halves +201 / -87 | 20 bp | KILLED 2026-11-15: t 0.68; halves +201 / -87; deciles flat; corr 0.47 with Strategy 20 [L:I97] |
| I101 FINRA short-volume ratio weekly decile sort, top-1,000 US shares (I-101, Fable card 3) | US top-1,000 by dollar volume (docs/share-universe.md) | 2016-04..2021-09-13 dev | +0.8 bp/week (cell A) | t 0.16 | n/a (not recorded) | n/a (not recorded) | 13 bp/week | KILLED 2026-11-17 both cells: gross t 0.16, deciles flat (31-37 bp); cell A t -2.55, cell B t -2.88; every kill hit [L:I101] |
| I103 Leveraged single-stock ETF rebalance into the close (I-103, Fable card 7) | 20 US underlyings with single-stock leveraged funds | 2022-09..2024-12 dev (split set by the user) | +6.4 bp | t 0.80 | n/a (not recorded) | halves -1.2 / +8.6 | 2.5 bp | KILLED 2026-11-17: t 0.80, halves -1.2 / +8.6; control same-size movers +3.2 bp (flow adds ~3 bp); step 1 GO 338 name-days >= 5 % [L:I103] |
| I102 Overnight -> 10:00 reversal decile sort, top-1,000 US shares, real-share cost (I-102, Fable card 4) | US top-1,000 by dollar volume (docs/share-universe.md) | 2016-04..2021-09-13 dev | +2.55 bp/day | t 1.04 | n/a (not recorded) | halves +1.3 / -10.3, fades to -10 by 2021 | 7 bp/day | KILLED 2026-11-17: gross t 1.04, net t -1.82, halves +1.3 / -10.3, fades to -10 by 2021; diagnostic open timing gross +12.9 t 3.94 (not a cell) [L:I102] |
| I110 Treasury month-end duration extension on 20-year bonds, last 3 trade dates (I-110) | FRED DGS20 (TLT check) | dev 1993-10..2021-08; test 2021-10..2026-10 | dev +32.4 / test +26.0 bp per month-end (excess) | t 1.33 | n/a (not recorded) | n/a (not recorded) | 3 bp per month-end | NOT CONFIRMED 2026-11-17: dev every gate passed; one-time test t 1.33 < 1.5 (net +23.0, TLT +21.6, t 1.20); not FALSIFIED, not UNPROVEN-POSITIVE (M1); no retest [L:I110] |
| I111 Threshold rebalancing signal (60/40, bands 0-2.5 %) on US500, next-day position (I-111) | US500 (FTMO CFD) + FRED DGS10 signal leg | 2010-11..2021-09-13 (inside the paper's sample) | +1.88 bp/day (t 1.79) | t 1.37 | n/a (not recorded) | n/a (not recorded) | FTMO fills + swap ~0.44 bp/day | KILLED 2026-11-17: t 1.37 < 3.0 (M1: neither FALSIFIED nor UNPROVEN-POSITIVE); net without 2020-02-20..04-30 -0.08 [L:I111] |
| I112 Month-end duration extension in euro (ECB AAA), UK (BoE) and Japanese (MOF) 10-year bonds, pooled (I-112) | EU, UK, JP 10-year yields | 1990-01..2021-08 (EU from 2004-10) | +4.5 bp per month-end pooled | t 1.00 net | n/a (not recorded) | halves -2.0 / +7.1, breadth (JP <= 0) | 2 bp per month-end | KILLED 2026-11-17: t < 3.0, halves -2.0 / +7.1, breadth (JP <= 0); M1 neither FALSIFIED nor UNPROVEN-POSITIVE [L:I112] |
| I113 VIX futures basis: short front VX (>= 10 days) when daily roll > 0.10, long when < -0.10, 5-day hold, unhedged (I-113) | Cboe VX (front monthly) | 2007-01..2021-09-13 | +$443 per contract | t 2.19 | n/a (not recorded) | n/a (not recorded) | $60 round trip | KILLED 2026-11-18: t 2.19 < 3.0 (all other gates pass); H hedged +$328 t 2.69; paper window reproduced (84 short +$716 vs paper 82 / ~$656) [L:I113] |
| I114 VIX roll short leg only (I-113 rule, short side), one independent check (I-114) | Cboe VX (front monthly) | 2021-09-14..2026-11-16 (test; first use of VX data after development) | +$30 per contract | t -0.17 | n/a (not recorded) | n/a (not recorded) | $60 round trip | FALSIFIED 2026-11-18 (net <= 0); before the holiday-calendar fix 96 trades -$23 (t -0.17); H hedged -$66 [L:I114] |
| I115 S&P GSCI roll front-running, energy calendar spreads (CL HO RB NG), Mou Strategy 1 (I-115) | NYMEX CL, HO, RB, NG calendar spreads (EIA strips) | 2000-01..2021-08 | +29.1 bp per month | t -1.13 | n/a (not recorded) | n/a (not recorded) | 3 bp | FALSIFIED at the one-time test 2026-11-18 (2021-10..2024-03: -21.5 bp, t -1.13; NG -78); development PASSED every gate; post-publication half ~0; placebo 1986-99 NG +135 bp [L:I115] |
| H2 12-1 momentum decile long-short (H2) | US shares top 1000 | 2017-05..2021-08 | 85.8 bp | t 0.71 | n/a (not recorded) | halves +41.2/+91.5, 2021 -151 (underpowered as M4 said) | n/a (not recorded) | KILLED 2026-11-19 development on  / t / <3.3 only: net +70.8 bp/month t 0.71, halves +41.2/+91.5, 2021 -151 (underpowered as M4 said) [L:H2] |
| H3 Tax-loss loser basket Dec 15 - Feb 15 (H3 / I-130) | US shares top 1000 | Dec 2016-2020 | 39.6 bp | t 0.26 | n/a (not recorded) | halves -143.6/+198.7 | n/a (not recorded) | KILLED 2026-11-19 development: 4 events (Dec 2020 empty, A6), net +27.6 t 0.26, halves -143.6/+198.7 [L:H3] |
| F2 NAS100 / UK100 / GER40 / EU50 | index CFDs | 2015-01-02..2021-09-13 | +21 / +29 / +36 / +10 R gross total | n/a (not recorded) | n/a (not recorded) | all gross signs positive | n/a (not recorded) | net negative [CW section 1] |
| R014 FADE 30 / 60 min | 6 FX | 2015-01-02..2021-09-13 | +0.021 / +0.028 R/trade | n/a (not recorded) | n/a (not recorded) | largest gross M15 family | ~0.21 R/trade | user rejected [CW section 1] |
| I83 weekly absorption | Binance perps | 2020..2023 | n/a (not recorded) | 3.57 net | +101.6 bp/week net, t 2.85 | dev net +145.4, halves +294.1 / +28.2; test correlation 0.83 with S20 | 20 bp/week [I:I-83] | passed pooled gates; not confirmed alone [L:I83] |
| I84 spot-minus-perp | Binance spot / perps | 2020..2023 | n/a (not recorded) | 1.76 | n/a (not recorded) | halves +150 / +8 net | n/a (not recorded) | shelf; gross not located [L:I84] |

## 3. Measured zero / negative components

Only observations whose recorded gross is zero or negative; net-only failures with unknown gross are not presented as gross-negative.

| id | what | gross | t | verdict / source |
| --- | --- | --- | --- | --- |
| S01 | Session zone sweep | -0.047 | n/a (not recorded) | falsified [L:S01] |
| S03 | No-wick candle in the trend | -0.033 | n/a (not recorded) | falsified [L:S03] |
| S09 | R014 M15 alternating path | -0.019 to +0.028 | n/a (not recorded) | rejected by the user 2026-11-06 [L:S09] |
| H03 | F3 FOMC morning long | -0.225 | n/a (not recorded) | falsified (opposite sign) [L:H03] |
| H04 | F4 turn of month open to close | -0.013 | n/a (not recorded) | falsified [L:H04] |
| I86 | Noise-band momentum on negative-gamma days (I-86) | -15.7 bp/trade | t -1.97 | KILLED 2026-11-15: t -1.97, opposite sign (short-gamma days rebound) [L:I86] |
| I90 | Intraday rotation NAS100 vs US500: fade an extreme morning (I-90) | -8.9 bp | t -3.02 | KILLED 2026-11-15: t -3.02; extreme relative mornings continue (opposite sign); family index_rotation closed [L:I90] |
| I92 | ICT power of three around the midnight NY open (I-92) | -0.8 bp | t -1.59 | KILLED 2026-11-15: t -1.59 [L:I92] |
| I99 | Single-name shock reversal vs flat QQQ, 33 US share CFDs (I-99, FB-121) | -2.0 bp | t -2.47 | KILLED 2026-11-16: t -2.47; halves -7.6 / -11.8; doubled cost -17.0; mirror gross -3.2; shocks drift on, not back; SHARES family closed (2nd falsification) [L:I99] |
| I104 | Wikipedia page-view attention weekly decile sort, top-1,000 US shares (I-104, Fable card 9) | -2.5 bp/week (cell A) | t -0.27 | KILLED 2026-11-17 both cells: gross t -0.27, deciles without order; A t -1.67, B t -1.13 [L:I104] |
| I106 | Insider open-market purchases (Form 4, officers / directors), top-1,000 US shares (I-106) | -38.2 bp/event (20 days vs SPY) | t -1.46 | M1 (2026-11-17): FALSIFIED. KILLED 2026-11-17: net <= 0, NW t -1.46, halves +20.4 / -119.6; mirror (sales) gross -22.2 [L:I106] |
| I107 | Fails-to-deliver intensity half-monthly sort, top-1,000 US shares (I-107) | -31.0 bp/half-month (cell A) | t 0.92 | M1 (2026-11-17): cell A FALSIFIED; cell B t 0.92 (< 1.5, not UNPROVEN). KILLED 2026-11-17 both cells; B's gain is 2020-21 only [L:I107] |
| I108 | Insider open-market purchases (Form 4, officers / directors), US mid-caps ranks 1,001-2,000 (I-108) | -8.9 bp/event (20 days vs SPY) | t -0.24 | M1 (2026-11-17): FALSIFIED. KILLED 2026-11-17: net <= 0, NW t -0.24, halves +36.2 / -110.4; second falsification, family share_insider closed [L:I108] |
| H1 | Low idiosyncratic vol quintile long-short (H1 / I-129) | -50.1 bp | t -0.83 | KILLED 2026-11-19 development: net -65.1 bp/month t -0.83, wrong sign, halves -4.7/-123.6 (not detectable here; M4 power was low) [L:H1] |
| H4 | IWM minus IWB late December (H4 / I-130) | -18.2 bp | t -0.80 | KILLED 2026-11-19 development: 5 events, net -22.2 t -0.80 [L:H4] |
| L16 | usd_breadth_usdcad | -0.94 bp/trade | see verdict | SCREEN FAIL 2026-11-12: stays a card (primary, timed hold, no stop: gross -0.94 bp, cost 1.64 bp, net -2.58 bp per trade; t -1.40; vs control -0.93 bp) [L:L16] |
| L18 | btc_eth_leadlag | -19.59 bp/trade | see verdict | SCREEN FAIL 2026-11-12: stays a card (primary, timed hold, no stop: gross -19.59 bp, cost 13.10 bp, net -32.68 bp per trade; t -2.28; vs control -18.49 bp) [L:L18] |
| I69 | Bitcoin CME futures expiration week (I-69) | -60 bp/week | see verdict | KILLED 2026-11-12: net -100 bp per week (gross -60, t -0.72, 46 % positive; halves -181 / -23); other weeks gross +95 bp [L:I69] |
| I75 | Weekly crypto cross-sectional reversal 37 Binance perps (I-75) | -116.4 bp/week price; -10.4 funding | see verdict | KILLED 2026-11-14: net -146.8 bp/week (price -116.4, funding -10.4), t -1.05, halves -177 / -117, without 2 best -241; 17-symbol -67.7; corr with I-73 +0.25 [L:I75] |


## 4. Conditions / regime variables we can compute

| variable | where computed | period available | used by / source |
| --- | --- | --- | --- |
| VIX level / VX basis | research/screens/2026-11-18_i113_vix_basis_screen.py | 2007..2021 development; test 2021..2026 | I113 / I114 [L:I113] [L:I114] |
| volatility / noise regime; trend and sideways | strategy profiles and noise study | 2015..2021 development | S04, S07; noise study [CW section 1] [L:S04] [L:S07] |
| FOMC / macro release calendar | timed-hold and research/screens/2026-11-15_wave5_power_lines.py | calendar from 2020 in pooled power check | H03, FB186, FB190 [L:H03] [L:FB186] [L:FB190] |
| funding rates and cross-sectional rank | src/backtester/strategy/crypto_carry/book.py | 2020..2026 recorded streams | S19, I73, I100 [S19] [L:I100] |
| taker flow imbalance / residual absorption | src/backtester/strategy/crypto_flow/book.py; research/screens/2026-11-15_wave1_xs_crypto_screen.py | 2020..2026 | S20, I82, I83, I84 [S20] [L:I83] [L:I84] |
| month-end / quarter-end / weekend / Treasury settlement | research/screens/2026-11-18_t26_i109_month_end_diagnostics.py | 1990..2026 for I109 | I109; T26 diagnostics [L:I109] [RL 2026-11-18] |
| index review and option expiration | research/screens/2026-11-13_i71_review_auction_screen.py; research/screens/2026-11-12_i70_opex_week_screen.py | 2010..2021 | I71, I70 [L:I71] [L:I70] |
| short volume / insider / fails / attention | research/screens/2026-11-17_i101_short_volume_screen.py and i104 / i106 / i107 screens | 2016..2021 development | I101, I104, I106, I107 [L:I101] [L:I104] [L:I106] [L:I107] |

## 5. Data sets in data/cache/

Top-level folder listing only; periods below describe documented uses, not a claim of complete coverage. [cache]

| folder | source / contents | period | frequency | used by / source |
| --- | --- | --- | --- | --- |
| alpaca | Alpaca SIP US share bars | 2016..2021 | 1 minute | I99 [L:I99] |
| alpaca_1d | Alpaca US share daily bars | 2015-07 onward | daily | share universe / I101 [screen:2026-11-17_card2_share_universe.py] |
| alpaca_1d_fwd | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) [cache] |
| alpaca_1d_rates_fwd | Alpaca IEF closes | forward | daily | I109 [RL 2026-11-17] |
| alpaca_auctions_fwd | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) [cache] |
| alpaca_late | Alpaca late-session share bars | 2022..2024 | 1 minute | I103 [screen:2026-11-17_i103_step1_flow_audit.py] |
| alpaca_late2 | Alpaca late-session share bars | 2022..2024 | 1 minute | I103 [screen:2026-11-17_i103_step2_screen.py] |
| alpaca_meta | US share universe metadata | n/a (not recorded) | monthly universe | I101 [screen:2026-11-17_card2_share_universe.py] |
| alpaca_meta_fwd | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) [cache] |
| alpaca_ten | Alpaca narrow 10:00 share bars | 2016..2021 | 1 minute | I102 [screen:2026-11-17_i102_open_reversal_screen.py] |
| binance | Binance USD-M perps prices | 2020..2026 used | M1 | S19 [S19] |
| binance_1h | Binance USD-M perp klines | 2023-12..2026-10 | hourly | S20 prop diagnostic [screen:2026-11-15_s20_hourly_download.py] |
| binance_aggtrades | Binance aggregate trades | 2023-10-02..2023-12-25 | daily files, individual trades | FB273 [screen:2026-11-15_fb273_maker_fill.py] |
| binance_flow | Binance volume and buy volume per symbol | n/a (not recorded) | M1 parquet | I76 [src/backtester/data/binance.py] [screen:2026-11-14_i76_liquidation_reversal_screen.py] |
| binance_funding | Binance perp funding | 2020..2026 used | settlement | S19 [S19] |
| binance_wide | Binance USD-M perps | 2020..2023 development | daily | I78 / I100 [L:I78] [screen:2026-11-17_i100_wide_carry_screen.py] |
| binance_wide_spot | Binance spot klines | 2020..2023 development | daily | I84 [RL 2026-11-15] [screen:2026-11-15_wave1_xs_crypto_screen.py] |
| binance_wide_spot_fwd | Binance spot forward klines | forward | daily | I84 / I98 shelf [screen:2026-11-17_shelf_forward.py] |
| binance_wide_test | Binance USD-M perps | 2024 onward | daily | S20 [S20] |
| bybit | Bybit perp instruments, prices, funding | test 2024..2026 | daily / funding | S20 venue diagnostic [screen:2026-11-16_s20_bybit_prices.py] |
| eia_strips | EIA CL / HO / RB / NG contracts 1-3 | 2000..2021 development | daily | I115 [L:I115] [screen:2026-11-18_i115_gsci_roll_screen.py] |
| eia_strips_test | EIA energy contracts 1-3 | 2021-10..2024-03 test | daily | I115 [L:I115] |
| finra | FINRA daily short volume | 2015-07 onward | daily | I101 [screen:2026-11-17_card2_share_universe.py] |
| fred | FRED H.15 constant-maturity yields | 1990..2026 used | daily | I109 / I110 [L:I109] [L:I110] |
| histdata | histdata.com FX M1 | older years; exact coverage n/a (not recorded) | M1 | development history [AGENTS.md] |
| histdata_presample | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | [screen:2026-11-12_i68_power_check.py] |
| hyperliquid | Hyperliquid public perp daily candles | n/a (not recorded) | daily | signal-free audit [screen:2026-11-17_card6a_hyperliquid_audit.py] |
| index_presample_staging | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) [cache] |
| intl_yields | ECB AAA, Bank of England, Japan MOF government yields | EU from 2004; UK 1979+; JP 1974+ | daily | I112 [RL 2026-11-17] |
| live | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) [cache] |
| mt5 | MetaTrader 5 FTMO market history | exact coverage n/a (not recorded) | M1 | backtests [AGENTS.md] |
| s20_prop | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) | n/a (not recorded) [cache] |
| sec_ftd | SEC fails-to-deliver | 2016-01..2021-08 | half-monthly | I107 [screen:2026-11-17_i107_fails_screen.py] |
| sec_insider | SEC insider transactions | 2016Q1..2021Q3 | quarterly files | I106 [screen:2026-11-17_i106_insider_buys_screen.py] |
| sec_nport | SEC N-PORT fund assets | 2022..2024 used | n/a (not recorded) | I103 [screen:2026-11-17_i103_step1_flow_audit.py] |
| squeezemetrics | SqueezeMetrics DIX / GEX | before 2021-09-14 used | daily | I86 [screen:2026-11-15_i85_noise_band_screen.py] [RL 2026-11-15] |
| treasurydirect | TreasuryDirect note issue and settlement calendar | n/a (not recorded) | event dates | I109 T26 [screen:2026-11-18_t26_i109_month_end_diagnostics.py] |
| vix | Cboe VIX and VX per-contract settlements | 2007..2021 development | daily | I113 [L:I113] [screen:2026-11-18_i113_vix_basis_screen.py] |
| vix_test | Cboe VX settlements | 2021-09..2026-11 test | daily | I114 [L:I114] |
| wiki | Wikimedia page views and Wikidata mappings | 2016..2021 used | daily | I104 [screen:2026-11-17_i104_attention_screen.py] |
| yahoo_daily | Yahoo daily US share closes | 2010..2021 used | daily | I96 [L:I96] |
| yahoo_futures | Yahoo ZN continuous front contract | 2000-09 onward | daily | I109 diagnostic [screen:2026-11-18_i109_zn_futures_check.py] |

## 6. Gaps

- The gross, t, test, cost and regime fields marked n/a are not recorded in the cited ledger row / cost-wall table; no value is inferred from a net result.
- I84 and I83 gross values were not located in their cards, ledger rows or research-log headlines; these report net. [L:I84] [L:I83] [RL 2026-11-15]
- Several cache folders have no source, contents, period or frequency recovered from the screen headers and named records; their listing is retained with n/a. [cache]
- The brief names 73 screen scripts; the folder listing contains 72 files. Headers were read, but mapping every screen-only positive diagnostic and every non-ledger cell to a result is incomplete; the ledger and research-log headlines do not supply a complete per-screen index. [cache] [RL 2026-11-19]
- F2 per-index trade-level costs and t, and H11 gross, are not recorded in the cited synthesis / ledger. [CW section 1] [L:H11]
- Untested and power-only ideas have no measured gross edge and are not placed in the positive or negative tables. [research/ledger.csv]
