# V2.6d step 2: FTMO fees as the defaults (the user's go, 2026-10-27)

Source of every value: `docs/review/ftmo-fees-2026-10-27.md` (read it first). The user said
"research all the fees from FTMO and implement them": these become the defaults.

## 1. Commissions (engine/costs.py `_BASE_SYMBOL_COSTS`)

- NATGAS and DXY: `commission_pct_per_side=FTMO_METAL_COMMISSION_PCT_SIDE`-like 0.0007 %
  (= 0.000007 as a fraction, the same constant the metals use; rename or add a clearly named
  constant such as `FTMO_PCT_COMMISSION_SIDE` if that reads better, keeping the metals' value).
- Everything else stays (FX $5 round turn, metals 0.0007 % per side, crypto 0.0325 % per side,
  indices and oil 0).

## 2. Currency conversion adjustment (new)

FTMO, 2026-07-28: 0.7 % of the realised profit or loss of a trade whose profit currency differs
from the account currency (USD). A profit is reduced by 0.7 %, a loss increased by 0.7 %.

- `SymbolCosts.profit_currency: str = "USD"` and, per symbol: FX = the quote currency (last three
  letters: USDJPY -> JPY, EURGBP -> GBP, EURAUD -> AUD ...); GER40 / EU50 EUR, UK100 GBP,
  JP225 JPY, AUS200 AUD, HK50 HKD; all other symbols USD (USD-quoted FX, metals, US indices,
  oil, NATGAS, DXY, crypto, Binance).
- `CostConfig.conversion_adjustment: float = 0.007` (0 = off, reproduces old results), with
  `CostConfig.account_currency: str = "USD"`; validated finite and 0 <= x < 1.
- In R: the adjustment is a cost of `conversion_adjustment x |r_gross|` (gross price P/L of the
  trade in R, before the other costs), charged when the trade closes, for symbols whose
  profit currency != the account currency. It lowers `r_net` in both cases (profit smaller,
  loss bigger). Report it like the other costs: a per-trade field `conversion_r` next to
  `swap_r` / commission (find how swap_r / funding_r are carried through `engine/trade.py`,
  `TradeResult`, the trades CSV columns `runner.TRADE_COLUMNS` and `analytics/records.py`,
  and follow the same path; old trades CSVs without the column must still load as 0).
- Partial closes (TP1 / TP2): apply to each part's gross R, so the sum equals the whole.

## 3. Docs and golden lists

- `docs/risk-management.md` > Costs: a short paragraph for the conversion adjustment (rule set
  by the user, 2026-10-27) and the NATGAS / DXY commission change, pointing to the review file.
- The golden lists change for symbols with a non-USD profit currency (GBPJPY in strategy 1) and
  maybe others: run `python -m backtester.tools.golden --check` and report which strategies
  differ and by how much. Do NOT rewrite the golden files: Opus does that after reviewing.

## Rules

Tests first (tests/engine/test_costs.py and the trade / R tests): profit and loss cases, a USD
symbol unaffected, adjustment 0 = old numbers exactly, partial closes, the CSV round trip and
an old CSV without the column. Run the tests of what you change plus tests/engine, tests/analytics
and tests/test_runner*.py; ruff check / format the changed files. Do not start servers, do not
commit / push / branch, do not touch src/backtester/live/, .env or credentials. Never weaken a
test; if an existing test fails because its expected numbers include the new cost, report it
(with the test name and the old / new value) instead of changing it, unless the test pins a
default that this brief changes (then update it and say so).
