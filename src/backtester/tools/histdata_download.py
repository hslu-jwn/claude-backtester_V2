"""Download histdata.com's free MetaTrader M1 files (the sample / development years).

    python -m backtester.tools.histdata_download                  # all pairs, 2015-2021-09
    python -m backtester.tools.histdata_download EURUSD XAUUSD --years 2019 2020 --months 2021-01

Per file: GET the download page, read the hidden fields of the plain form `file_down`
(`tk`, date, datemonth, platform, timeframe, fxpair), POST them to `get.php` with the page as
Referer, check that the answer is a real zip with a `DAT_MT_*.csv` inside and save it as
`data/raw/histdata/<OUR_SYMBOL>/HISTDATA_COM_MT_<PAIR>_M1_<period>.zip`, where
`backtester.data.histdata` imports it. Only that plain form post is done: a captcha, login
or script challenge shows up as a non-zip answer and is reported, never worked around.
Existing files are skipped (resumable). Downloads are data: they are only checked and
written, never unpacked or executed.
"""

from __future__ import annotations

import argparse
import io
import time
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol

from backtester.data.histdata import SYMBOL_NAMES

SITE = "http://www.histdata.com"
PAGE_URL = SITE + "/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes/"
POST_URL = SITE + "/get.php"
USER_AGENT = "Mozilla/5.0 (backtester research; polite, 1 request per 2 s)"
DELAY_SECONDS = 2.0  # wait after every file (page + post)
TIMEOUT_SECONDS = 120
MAX_CONSECUTIVE_ERRORS = 3  # network / HTTP errors in a row -> stop
MAX_EMPTY_PAIRS = 3  # pairs in a row without any file -> stop (a block page, not a late start)
FORM_ID = "file_down"
FORM_FIELDS = ("tk", "date", "datemonth", "platform", "timeframe", "fxpair")
FIRST_YEAR, LAST_FULL_YEAR = 2015, 2020  # sample years as year files
MONTHS_YEAR, LAST_MONTH = 2021, 9  # then 2021-01 .. 2021-09 as month files (cut-off 2021-09-14)
DEFAULT_PAIRS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "USDCHF",
    "NZDUSD",
    "EURJPY",
    "GBPJPY",
    "EURGBP",
    "XAUUSD",
    "XAGUSD",
    "SPXUSD",
    "NSXUSD",
    "GRXEUR",
    "UKXGBP",
    "JPXJPY",
    "ETXEUR",
    "WTIUSD",
    "BCOUSD",
    "UDXUSD",
]
DEFAULT_ROOT = Path("data/raw/histdata")


class DownloadError(Exception):
    """The answer is not the file (no form, no zip, wrong content): nothing is saved."""


class HttpError(Exception):
    """Network failure or HTTP status other than 200."""


class Client(Protocol):
    def get(self, url: str) -> str: ...
    def post(self, url: str, data: dict[str, str], referer: str) -> bytes: ...


class RequestsClient:
    def __init__(self) -> None:
        import requests

        self._s = requests.Session()
        self._s.headers["User-Agent"] = USER_AGENT

    @staticmethod
    def _check(r) -> None:
        if r.status_code != 200:
            raise HttpError(f"HTTP {r.status_code} for {r.url}")

    def get(self, url: str) -> str:
        try:
            r = self._s.get(url, timeout=TIMEOUT_SECONDS)
        except OSError as e:  # requests' exceptions are OSErrors
            raise HttpError(str(e)) from e
        self._check(r)
        return r.text

    def post(self, url: str, data: dict[str, str], referer: str) -> bytes:
        try:
            r = self._s.post(url, data=data, headers={"Referer": referer}, timeout=TIMEOUT_SECONDS)
        except OSError as e:
            raise HttpError(str(e)) from e
        self._check(r)
        return r.content


class _FormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.fields: dict[str, str] | None = None
        self._inside = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form" and a.get("id") == FORM_ID:
            self._inside, self.fields = True, {}
        elif tag == "input" and self._inside and a.get("type") == "hidden" and a.get("name"):
            self.fields[a["name"]] = a.get("value") or ""

    def handle_endtag(self, tag):
        if tag == "form":
            self._inside = False


def parse_form(html: str) -> dict[str, str]:
    """The hidden inputs of the download form; DownloadError if it or a field is missing."""
    p = _FormParser()
    p.feed(html)
    if not p.fields:
        raise DownloadError(f"no form {FORM_ID} with hidden fields on the page")
    missing = [f for f in FORM_FIELDS if not p.fields.get(f)]
    if missing:
        raise DownloadError(f"form fields missing: {missing}")
    return {f: p.fields[f] for f in FORM_FIELDS}


def page_url(pair: str, period: str) -> str:
    """Download page of a year ("2019") or a month ("202103")."""
    path = f"{pair.lower()}/{period[:4]}"
    if len(period) == 6:
        path += f"/{int(period[4:])}"
    return PAGE_URL + path


def default_periods() -> list[str]:
    years = [str(y) for y in range(FIRST_YEAR, LAST_FULL_YEAR + 1)]
    return years + [f"{MONTHS_YEAR}{m:02d}" for m in range(1, LAST_MONTH + 1)]


def target_path(root: Path, pair: str, period: str) -> Path:
    symbol = SYMBOL_NAMES.get(pair, pair)
    return Path(root) / symbol / f"HISTDATA_COM_MT_{pair}_M1_{period}.zip"


def _check_zip(pair: str, period: str, body: bytes) -> None:
    if not body.startswith(b"PK\x03\x04"):
        raise DownloadError(f"answer is not a zip file ({len(body)} bytes)")
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            names = z.namelist()
    except zipfile.BadZipFile as e:
        raise DownloadError(f"broken zip: {e}") from e
    want = f"DAT_MT_{pair}_M1_{period}.csv"
    if want not in names:
        raise DownloadError(f"zip has no {want}, only {names}")


def download_period(client: Client, pair: str, period: str, root: Path) -> str:
    """ "skipped" (file exists) or "downloaded". Raises DownloadError / HttpError."""
    path = target_path(root, pair, period)
    if path.exists():
        return "skipped"
    url = page_url(pair, period)
    form = parse_form(client.get(url))
    if form["fxpair"] != pair:
        raise DownloadError(f"page is for {form['fxpair']}, not {pair}")
    body = client.post(POST_URL, form, url)
    _check_zip(pair, period, body)
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(".zip.part")
    part.write_bytes(body)
    part.replace(path)
    return "downloaded"


@dataclass
class RunResult:
    downloaded: list[tuple[str, str]] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)
    missing: list[tuple[str, str]] = field(default_factory=list)
    errors: list[tuple[str, str, str]] = field(default_factory=list)
    stopped: bool = False


def run(
    client: Client,
    pairs: list[str],
    periods: list[str],
    root: Path,
    sleep: Callable[[float], None] = time.sleep,
    log: Callable[[str], None] = print,
) -> RunResult:
    out = RunResult()
    in_a_row = 0  # consecutive HTTP errors
    empty_pairs = 0
    for pair in pairs:
        got = 0
        for period in periods:
            try:
                status = download_period(client, pair, period, root)
            except HttpError as e:
                out.errors.append((pair, period, str(e)))
                log(f"ERROR   {pair} {period}: {e}")
                in_a_row += 1
                if in_a_row >= MAX_CONSECUTIVE_ERRORS:
                    out.stopped = True
                    log(f"STOP: {in_a_row} errors in a row")
                    return out
                sleep(DELAY_SECONDS)
                continue
            except DownloadError as e:
                in_a_row = 0
                out.missing.append((pair, period))
                log(f"MISSING {pair} {period}: {e}")
                sleep(DELAY_SECONDS)
                continue
            in_a_row = 0
            got += 1
            (out.downloaded if status == "downloaded" else out.skipped).append((pair, period))
            log(f"{status.upper():8}{pair} {period}")
            if status == "downloaded":
                sleep(DELAY_SECONDS)
        empty_pairs = 0 if got else empty_pairs + 1
        if empty_pairs >= MAX_EMPTY_PAIRS:
            out.stopped = True
            log(f"STOP: {empty_pairs} pairs in a row without any file")
            return out
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("pairs", nargs="*", default=DEFAULT_PAIRS, help="histdata pair names")
    p.add_argument("--years", nargs="*", help="year files, default 2015-2020")
    p.add_argument("--months", nargs="*", help="month files as YYYY-MM, default 2021-01..09")
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = p.parse_args(argv)
    if args.years is None and args.months is None:
        periods = default_periods()
    else:
        periods = list(args.years or []) + [m.replace("-", "") for m in args.months or []]
    out = run(RequestsClient(), list(args.pairs), periods, args.root)
    print(
        f"downloaded {len(out.downloaded)}, skipped {len(out.skipped)}, "
        f"missing {len(out.missing)}, errors {len(out.errors)}, stopped {out.stopped}"
    )
    return 1 if out.stopped else 0


if __name__ == "__main__":
    raise SystemExit(main())
