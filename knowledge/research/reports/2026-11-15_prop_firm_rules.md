# Prop-firm rule table (2026-11-15, Sonnet web subagent; Fable backlog FB-259 / FB-261)

Opened official pages where possible; several returned 403 / 404 (Breakout program rules, FundingPips and The5ers help
roots); some numbers come from search snippets or the fetch tool's paraphrase. Treat every rule as UNVERIFIED until
confirmed by the firm; rules change. Question: can a weekly long-short book of 40-60 USDT perps (Monday 00:00 UTC,
7-day hold incl. the weekend, equal weight, no stop, ~1x gross) run at the firm?

## Crypto firms

| Firm | Instruments | Challenge | Holding / stops / bots | Fees, split | Verdict for Strategy 20 |
|---|---|---|---|---|---|
| HyroTrader (hyrotrader.com, crypto-trading-rules) | Bybit API demo: 700+ USDT perps; low caps (< 100 M USD market cap) limited: > 5 % of initial balance incl. leverage in low caps is a violation | 1-Step 10 % / 4 % daily / 8 % max; 2-Step 10 + 5 % / 5 % / 10 %; no time limit; best day <= 40 % of target | Weekend allowed; stop not required; own bots / API allowed (bought bots, copy trading banned); unrealistic Bybit-demo fills can be flagged | 1-Step 69 USD, 2-Step 59 USD refundable; 80-90 % split; payouts ~24 h | **Probably yes (best fit)**; confirm whether the low-cap 5 % cap is aggregate, static vs trailing drawdown, basket orders not flagged; all simulated (no real-capital stage) |
| Crypto Fund Trader (cryptofundtrader.com/faq) | Bybit: 550+ USDT perps; also 556 crypto CFDs on MT5 | 1-Step 10 % / 3 % daily / 6 % static; 2-Phase 5 % daily / 10 % fixed; no time limit | Weekend allowed; stop not required in general; bans HFT, arbitrage, cross-account hedging | split up to 90 %; payout ~8 h | **Probably yes**; confirm position caps and funding pass-through |
| Breakout / Kraken | 50+ pairs, 5x BTC / ETH, 2x others | 1-Step, 3-6 % static max (snippets) | Weekend allowed; bot rules unpublished | split > 80 % | Unclear (universe thin) |
| Bitfunded | 100+ pairs on own platform | 2-Step 8 + 5 %, 1-Step 10 % | **Bots / API banned, max 5 open positions, 7-10 day holding limit** | 0.04 % a side; 80 % | **No** |

## CFD and futures firms (short)

FundingPips 2-Step Flex 10 / 8 %, 4 % daily, 12 % max, weekend holds not on Master accounts; The5ers Hyper Growth 10 %,
6 % stop-out, 3 % daily pause; FundedNext Stellar 8 / 5 %, 5 % / 10 % static, EAs allowed. Topstep: end-of-day trailing
max loss, 90 % split; Apex: intraday trailing incl. unrealised, live accounts ban automation. None lists the perp
universe Strategy 20 needs.

## What it changes

Strategy 20 (and its I-83 twin) is a candidate for goal 1 at a Bybit-based crypto prop firm (HyroTrader, Crypto Fund
Trader): weekend holds and no stop are allowed. Open before any money: the firm's low-cap and position rules, fills on
a demo feed, and whether the weekly book's daily swings fit a 3-5 % daily loss limit (next: simulate Strategy 20's
daily-marked book against these rules). Signing up or paying a fee is the user's decision.
