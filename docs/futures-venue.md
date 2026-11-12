# Futures venue, cost model inputs and history source

Decided by Opus on the user's instruction (2026-11-12: "Use a broker that has the best fees and is safe and
allows algo trading. Choose yourself."), after the venue rule in `AGENTS.md` (futures allowed as well as
FTMO CFDs). A cost-model and infrastructure choice, not investment advice. Opening any account, accepting
terms and entering logins are the user's own steps; credentials only ever in the Windows Credential Manager.

## Broker: Interactive Brokers, IBKR Pro, via Interactive Brokers Ireland (IBIE)

Why (research by two subagents, decisive numbers re-read by Opus on IBKR's own pages on 2026-11-12):
1. Cheapest verified all-in cost of the candidates, and the only one confirmed to list CL, MCL, BZ and ICE
   Brent (NinjaTrader EU: CL USD 2.99 / MCL 1.19 per side on its free plan, no Brent; AMP and Optimus:
   US firms without EU investor protection; Saxo: fees not verifiable).
2. EU regulated (Central Bank of Ireland), segregated client money, large listed parent group.
3. Official Python API (TWS API), paper-trading account, no platform fees.

| Contract (per side, <= 1,000 contracts / month) | IBKR commission (fixed) | NYMEX exchange fee (Tier 1) | All-in (before regulatory fee) |
|---|---|---|---|
| CL (NYMEX WTI, 1,000 bbl) | USD 0.85 | USD 1.50 | USD 2.35 |
| MCL (Micro WTI, 100 bbl) | USD 0.25 | USD 0.60 | USD 0.85 |
| BZ (NYMEX Brent last day financial, 1,000 bbl) | USD 0.85 | USD 1.50 | USD 2.35 |
| ICE Brent B | about USD 1.93 tiered / 2.40 fixed | (incl.) | UNVERIFIED by Opus (subagent only) |

Sources (read 2026-11-12): `https://www.interactivebrokers.com/en/pricing/commissions-futures.php` (fixed
USD 0.85 standard, USD 0.25 micro; exchange and regulatory fees on top), `https://www.interactivebrokers.com/en/accounts/fees/NYMEX.php`
(CL / BZ USD 1.50, MCL USD 0.60, Tier 1 non-members). Regulatory (NFA) fee about USD 0.01-0.02 per side:
UNVERIFIED. Market data: NYMEX non-professional L1 about USD 1.55 / month; ICE Futures Europe about USD 155 /
month (subagent, UNVERIFIED by Opus), so live Brent trading via BZ avoids the ICE data fee.
Spread / slippage: one tick per side is the conservative starting assumption (CL / BZ tick 0.01 = USD 10
per contract; MCL 0.01 = USD 1); to be checked against real fills before any money is at risk.

## Historical prices: Norgate Data, futures package (not the broker)

IBKR's API returns expired futures only for contracts that expired in the last two years (IBKR TWS API
docs), so it cannot supply 2010-2021. Choice: **Norgate Data futures package**, USD 148.50 / 6 months or
USD 270 / 12 months (read on `https://norgatedata.com/futurespackage.php`, 2026-11-12), free trial linked.
Coverage (`https://norgatedata.com/data-content-tables.php`): CL from 30 Mar 1983 (read verbatim); ICE
Brent BRN from 1988 (subagent summary of the page). End-of-day with the official settlement as close;
documented roll rule for continuous series. Whether individual EXPIRED contracts are included is not stated
on the page: check in the trial before paying. Delivery: Norgate Data Updater on Windows plus a Python
package. Backtests use ICE Brent BRN history; live trading would use BZ (financially settled on ICE Brent),
so the BZ / BRN basis is a stated assumption of any Brent strategy.

Alternatives kept: FirstRate Data (1-minute, CL / BZ / ICE B from 2008, about USD 299 one-off, UNVERIFIED);
Databento (best API; CL only from 2010-06, ICE Brent only from 2018-12); EIA (free WTI contracts 1-4 to
2024-04, no Brent futures).

## Trial check (2026-11-12)

The user started the Norgate futures trial (Updater signed in, manual updates; Python access via the
`norgatedata` package, which talks to the running Updater at `localhost:38889`). Found: databases Futures
(individual contracts) and Continuous Futures; CL 147 and ICE Brent BRN 171 contract months; continuous
`&CL`, `&BRN` and back-adjusted `&CL_CCB`, `&BRN_CCB` with Delivery Month and Open Interest. **The trial holds
only 2024-11-12 to 2026-11-11** (Norgate's trial history limit), so 2010-2021 coverage and expired 2010s
contracts can only be confirmed with a subscription. BZ and MCL are not in Norgate. The trial window lies
after the development cutoff (one-time test territory): it is used for format checks only, never for a look.

## Next

1. **Decided by the user 2026-11-12: no subscription ("No, stop here").** The futures check of P01 is parked;
   the trial lapses by itself after 3 weeks. `norgatedata` removed from the environment again.
2. Opus / Codex: a read-only loader for Norgate futures (daily settlements, individual contracts, roll) and
   a futures cost model from the table above; then P01 WTI / Brent on futures prices, pre-sample 2010-2014
   plus development, pre-registered.
