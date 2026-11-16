"""Alpaca US share / ETF minute bars for research (Fable backlog FB-290; the user's go 2026-11-16).

    python -m backtester.data.alpaca SPY QQQ AAPL --start 2016-01 [--end 2026-10]

Source: Alpaca market data v2 `GET /v2/stocks/bars` (free Basic plan: consolidated SIP history,
only the latest 15 minutes withheld), timeframe 1Min, split-adjusted (dividends not adjusted, so
dividend gaps stay real). Keys live only in the Windows Credential Manager:
`python -m keyring set backtester-alpaca key_id` and `... secret` (prompted, never printed).

Writes (git-ignored) one file per symbol and month: `data/cache/alpaca/<SYM>/<YYYY-MM>.csv` with
`COLUMNS` (ts = bar open time in UTC, as Alpaca returns it; all sessions incl. pre / post market).
Resumable: a month file that exists is skipped, except the current month (refetched).
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd

from backtester.paths import DATA_DIR

URL = "https://data.alpaca.markets/v2/stocks/bars"
CACHE_DIR = DATA_DIR / "cache/alpaca"
KEY_SERVICE = "backtester-alpaca"
COLUMNS = ["ts", "open", "high", "low", "close", "volume", "trades", "vwap"]
FIELDS = ["t", "o", "h", "l", "c", "v", "n", "vw"]
PAUSE = 0.35  # free plan: 200 requests a minute

Fetch = Callable[[dict], dict]


def _secret(name: str) -> str | None:
    import keyring

    return keyring.get_password(KEY_SERVICE, name)


def keys() -> tuple[str, str]:
    key_id, secret = _secret("key_id"), _secret("secret")
    if not key_id or not secret:
        raise RuntimeError(
            f"no Alpaca key: run python -m keyring set {KEY_SERVICE} key_id, then the same with secret"
        )
    return key_id, secret


def http_fetch(key_id: str, secret: str) -> Fetch:
    headers = {"APCA-API-KEY-ID": key_id, "APCA-API-SECRET-KEY": secret}

    def fetch(params: dict) -> dict:
        req = urllib.request.Request(f"{URL}?{urllib.parse.urlencode(params)}", headers=headers)
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    time.sleep(PAUSE)
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code not in (429, 500, 502, 503, 504) or attempt == 5:
                    raise RuntimeError(
                        f"Alpaca HTTP {e.code} for {params['symbols']} {params['start'][:7]}"
                    ) from None
            except OSError:
                if attempt == 5:
                    raise
            time.sleep(2.0 * (attempt + 1))
        raise AssertionError("unreachable")

    return fetch


def months(start: date, end: date) -> list[date]:
    out, m = [], start.replace(day=1)
    while m <= end:
        out.append(m)
        m = date(m.year + m.month // 12, m.month % 12 + 1, 1)
    return out


def download_month(symbol: str, month: date, fetch: Fetch, root: Path = CACHE_DIR) -> int:
    nxt = date(month.year + month.month // 12, month.month % 12 + 1, 1)
    params = {
        "symbols": symbol,
        "timeframe": "1Min",
        "start": f"{month:%Y-%m-%d}T00:00:00Z",
        "end": f"{nxt:%Y-%m-%d}T00:00:00Z",
        "limit": 10000,
        "adjustment": "split",
        "feed": "sip",
    }
    rows: list[list] = []
    while True:
        page = fetch(params)
        rows += [[b.get(f) for f in FIELDS] for b in (page.get("bars") or {}).get(symbol, [])]
        token = page.get("next_page_token")
        if not token:
            break
        params = {**params, "page_token": token}
    path = root / symbol / f"{month:%Y-%m}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    pd.DataFrame(rows, columns=COLUMNS).to_csv(tmp, index=False)
    tmp.replace(path)  # atomic: a crash never leaves a half month that resume would skip
    return len(rows)


def download(
    symbol: str,
    month_list: list[date],
    fetch: Fetch,
    root: Path = CACHE_DIR,
    today: date | None = None,
) -> None:
    today = today or datetime.now(UTC).date()
    for m in month_list:
        current = (m.year, m.month) == (today.year, today.month)
        if (root / symbol / f"{m:%Y-%m}.csv").exists() and not current:
            continue
        n = download_month(symbol, m, fetch, root)
        print(f"{symbol} {m:%Y-%m}: {n} bars")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("symbols", nargs="+")
    p.add_argument("--start", default="2016-01")
    p.add_argument("--end", default=None, help="YYYY-MM, default the current month")
    a = p.parse_args(argv)
    end = date.fromisoformat(f"{a.end}-01") if a.end else datetime.now(UTC).date()
    fetch = http_fetch(*keys())
    for s in a.symbols:
        download(s.upper(), months(date.fromisoformat(f"{a.start}-01"), end), fetch)


if __name__ == "__main__":
    main()
