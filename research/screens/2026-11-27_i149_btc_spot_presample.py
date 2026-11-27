"""I-149: Strategy 20 on BTC-quoted Binance spot 2018-01 .. 2019-12 (knowledge/ideas.md › I-149).

Card registered 2026-11-27 (commit 6826db1) before any BTC-pair data was read; download by Opus (Mode=auto).
Same rule, verdict and reported items as I-144 (its `weeks` / `run` reused on this root); only the universe differs:
<BASE>BTC pairs converted to USDT with BTCUSDT (open x open, close x close, quote_volume x close; base and taker-buy
volume unchanged, the flow signal is unit-free).
  download  : fetch daily klines of every kept <BASE>BTC pair 2017-10 .. 2019-12 into RAW/klines_1d/
  convert   : RAW -> ROOT/klines_1d in USDT terms (signal-free)
  coverage  : signal-free: weeks with a book; PARK under 52 (power) or under 80 weeks (M4)
  run       : the one look (I-144's verdict)
Run: .venv/Scripts/python.exe research/screens/2026-11-27_i149_btc_spot_presample.py download | convert | coverage | run
"""

import importlib.util
import sys
from pathlib import Path

import pandas as pd

from backtester.data import binance_wide

ROOT = Path("data/cache/binance_spot_btc_presample")
RAW = ROOT / "raw"
BTCUSDT = Path("data/cache/binance_spot_presample/klines_1d/BTCUSDT.csv")
M4_WEEKS = 80  # card: pass chance < 15 % under 80 weeks with a book

spec = importlib.util.spec_from_file_location("i144", "research/screens/2026-11-26_i144_spot_presample.py")
i144 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i144)
i144.ROOT = ROOT  # I-144's weeks() / run() read this root


def keep(symbol):
    base = symbol[:-3]
    return (
        symbol.endswith("BTC")
        and base
        and base not in i144.EXCLUDED
        and not base.endswith(i144.LEVERAGED)
    )


def download():
    _, prefixes = binance_wide._listing("data/spot/monthly/klines/", binance_wide._fetch, "/")
    syms = sorted(s for s in (p.rstrip("/").rsplit("/", 1)[-1] for p in prefixes) if keep(s))
    print(f"{len(prefixes)} spot pairs in the archive, {len(syms)} BTC pairs kept", flush=True)
    (RAW / "klines_1d").mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(syms):
        binance_wide.update_spot(RAW, [s], "2019-12", start_after="2017-09")
        if i % 50 == 0:
            print(f"{i} / {len(syms)}", flush=True)
    print(f"done: {len(list((RAW / 'klines_1d').glob('*.csv')))} pairs with data before 2020")


def to_usdt(d, btc):
    """BTC-quoted daily klines -> USDT terms; days without a BTCUSDT bar are dropped."""
    d = d.merge(btc, on="open_time", how="inner")
    for col, ref in (("open", "b_open"), ("high", "b_close"), ("low", "b_close"), ("close", "b_close")):
        d[col] = d[col] * d[ref]
    d["quote_volume"] = d["quote_volume"] * d["b_close"]
    return d.drop(columns=["b_open", "b_close"])


def convert():
    btc = pd.read_csv(BTCUSDT, usecols=["open_time", "open", "close"]).rename(
        columns={"open": "b_open", "close": "b_close"}
    )
    out = ROOT / "klines_1d"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted((RAW / "klines_1d").glob("*.csv")):
        d = to_usdt(pd.read_csv(p), btc)
        if len(d):
            d.to_csv(out / p.name, index=False)
            n += 1
    print(f"converted {n} pairs")


def coverage():
    i144.coverage()
    _, w = i144.weeks()
    if i144.MIN_WEEKS <= len(w) < M4_WEEKS:
        print(f"PARK on M4: {len(w)} weeks, under {M4_WEEKS}")


def run():
    _, w = i144.weeks()
    if len(w) < M4_WEEKS:
        sys.exit(f"{len(w)} weeks with a book, under {M4_WEEKS}: parked, no return read")
    i144.run()


if __name__ == "__main__":
    if sys.argv[1] == "selftest":
        btc = pd.DataFrame({"open_time": [1, 2], "b_open": [10.0, 20.0], "b_close": [20.0, 30.0]})
        d = pd.DataFrame({"open_time": [1, 2, 3], "open": [1.0] * 3, "high": [2.0] * 3, "low": [0.5] * 3,
                          "close": [1.5] * 3, "volume": [7.0] * 3, "quote_volume": [3.0] * 3,
                          "taker_buy_volume": [4.0] * 3})
        u = to_usdt(d, btc)
        assert list(u.open_time) == [1, 2] and list(u.open) == [10, 20] and list(u.close) == [30, 45]
        assert list(u.quote_volume) == [60, 90] and list(u.volume) == [7, 7] and list(u.taker_buy_volume) == [4, 4]
        assert keep("ETHBTC") and not keep("BTCUSDT") and not keep("USDCBTC") and not keep("BNBUPBTC")
        print("selftest ok")
    else:
        {"download": download, "convert": convert, "coverage": coverage, "run": run}[sys.argv[1]]()
