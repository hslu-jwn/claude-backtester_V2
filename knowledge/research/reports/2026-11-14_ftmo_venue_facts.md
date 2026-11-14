# FTMO venue facts (2026-11-14, Opus; Fable directions row 8, partial)

Sources: ftmo.com trading-objectives, FAQ (withdrawals) and how-it-works pages, read by a web-fetch subagent on
2026-11-14; the FTMO demo MT5 server read directly (`MetaTrader5.symbols_get`, read-only; Saturday snapshot).

## Rules (ftmo.com, 2026-11-14)

- 2-Step: targets 10 % (Challenge) and 5 % (Verification); max daily loss 5 % of initial capital (from the prior
  day's balance at 00:00 CE(S)T); max loss static 10 %; at least 4 trading days per phase. **No maximum number of
  days** is stated (banner "No time limit"). Matches `risk/challenge_path.py` `ftmo_2step`.
- 1-Step: one phase, target 10 %, daily loss 3 %, max loss end-of-day trailing 10 % (resets to 90 % after a reward
  withdrawal); orders from 2026-10-12: consistency, best day <= 50 % of total closed profit (not a breach; keep
  trading). Matches `ftmo_1step`. Instant account: 3 % daily, 10 % intraday trailing, 30 % consistency.
- Funded: reward 80 % by default after 2-Step (90 % after 1-Step / Instant, or with Scaling / Premium); request
  from the 14th day after the first trade, positions closed; 1-2 business days review plus 1-2 to pay.
- Not checked yet: banned practices, news rule, swap-free / Swing account terms, dividend booking (HANDOFF Open 2).

## Instruments on the FTMO MT5 server: 166 symbols

Forex 28, Exotics 15, Metals 9, Cash (index) CFDs 16, Commodities 2, Agriculture 7, **Equities 59** (46 US / 13 EU:
AAPL AMZN BABA BAC GOOG MSFT NFLX NVDA PFE RACE T TSLA V WMT ZM META GE BA RTX LMT PLTR AMD INTC QCOM AVGO CSCO JNJ
MCD SBUX KO MSTR GME NKE CVX FDX JPM DIS GM IBM ARM SNOW ASML AZN BRK.B XOM SPCX AIRF ALVG BAYGn DBKGn IBE LVMH
VOWG_p TTE SAN ADSGn BMW MBG SIEGn), **Crypto 30**. We cache 34 of them.

Crypto CFDs: all swap -30 %/yr both sides (intraday only). Weekend spread snapshot in bp (plus FTMO's crypto
commission, 0.065 % round turn in the engine, UNVERIFIED for the alts): BTC 0.2, BNB 0.2, AAVE 1.9, ETH 3.3, SOL
4.1, LINK 4.4, DASH 5.3, UNI 5.3, XMR 5.9, XLM 7.3, BAR 8.6, ETC 9.8, IMX 9.9, MANA 11.3, ICP 13.0, DOGE 14.9, XRP
15.6, GRT 18.1, ADA 19.2, VET 21.1, ALGO 24.9, AVAX 26.6, NEAR 28.7, BCH 29.2, DOT 31.8, LTC 34.8, SAND 54.9, GAL
72.5, XTZ 119.8, NEO 714. So an FTMO alt round trip is ~10-40 bp: never cheaper than Binance taker (10 bp), except
BTC / BNB / AAVE / ETH / SOL / LINK at ~7-11 bp. One weekend snapshot: weekday spreads may be lower.

## What it changes

- Binance-found crypto ideas can in principle run on FTMO (goal 1) for ~15 coins we also cache, at ~7-11 bp on
  the six cheapest and 15-40 bp on the rest; intraday holds only.
- Share CFDs open earnings / cross-sectional equity ideas (Fable row 22), but MT5 share history depth and costs
  are not checked (likely too short for a development period before 2021-09-14).
- Side effect: an aborted first read left all 30 crypto CFDs visible in the terminal's Market Watch (harmless;
  hide them by right-click > Hide if unwanted).
