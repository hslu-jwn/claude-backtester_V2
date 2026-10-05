"""Dukascopy downloader tests. No network: `.bi5` samples are built here byte by byte in
Dukascopy's format (big-endian: seconds, open, close, low, high, volume)."""

from __future__ import annotations

import dataclasses
import http.client
import lzma
import ssl
import struct
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from backtester.data import download
from backtester.data import dukascopy as duka
from backtester.data.dukascopy import (
    DayStatus,
    DukascopyConfig,
    DukascopyDownloader,
    DukascopyError,
    Side,
    day_url,
    parse_bi5,
)

BASE = "https://example.test/datafeed"
CONFIG = DukascopyConfig(base_url=BASE, request_delay_s=0)


def bi5(*records: tuple[int, int, int, int, int, float]) -> bytes:
    """records: (seconds, open, close, low, high, volume) — Dukascopy's on-disk order."""
    return lzma.compress(b"".join(struct.pack(">5If", *r) for r in records))


# XAUUSD 2026-09-01: two minutes, integer prices with point factor 1000.
# 00:00  O 3450.120  H 3451.000  L 3449.500  C 3450.800   (green)
# 00:01  O 3450.800  H 3450.900  L 3448.000  C 3448.250   (red)
BID_0901 = bi5(
    (0, 3450120, 3450800, 3449500, 3451000, 1.5),
    (60, 3450800, 3448250, 3448000, 3450900, 2.25),
)
ASK_0901 = bi5(
    (0, 3450420, 3451100, 3449800, 3451300, 1.0),
    (60, 3451100, 3448550, 3448300, 3451200, 2.0),
)


def test_url_month_is_zero_based():
    assert day_url("XAUUSD", date(2026, 9, 1), Side.BID, BASE) == (
        f"{BASE}/XAUUSD/2026/08/01/BID_candles_min_1.bi5"
    )
    assert day_url("GBPUSD", date(2026, 1, 31), Side.ASK, BASE) == (
        f"{BASE}/GBPUSD/2026/00/31/ASK_candles_min_1.bi5"
    )


def test_parse_maps_field_order_and_point_factor():
    df = parse_bi5(BID_0901, date(2026, 9, 1), point_factor=1000)
    assert list(df["ts"]) == [
        datetime(2026, 9, 1, 0, 0, tzinfo=UTC),
        datetime(2026, 9, 1, 0, 1, tzinfo=UTC),
    ]
    first = df.iloc[0]
    assert (first.open, first.high, first.low, first.close) == (3450.12, 3451.0, 3449.5, 3450.8)
    assert first.volume == 1.5
    assert df.iloc[1].close == 3448.25


def test_parse_rejects_wrong_field_order():
    # Same candle (O 3450.12, H 3451.0, L 3449.5, C 3450.8) in Dukascopy order O,C,L,H
    # and wrongly in O,H,L,C order: read back, "high" 3450.8 < "close" 3451.0.
    raw = bi5((0, 3450120, 3450800, 3449500, 3451000, 1.0))
    raw_bad = bi5((0, 3450120, 3451000, 3449500, 3450800, 1.0))
    parse_bi5(raw, date(2026, 9, 1), 1000)  # consistent record parses
    with pytest.raises(DukascopyError, match="inconsistent OHLC"):
        parse_bi5(raw_bad, date(2026, 9, 1), 1000)


def test_parse_empty_and_corrupt():
    assert parse_bi5(b"", date(2026, 9, 5), 1000).empty
    with pytest.raises(DukascopyError):
        parse_bi5(b"not lzma", date(2026, 9, 1), 1000)
    with pytest.raises(DukascopyError, match="multiple of 24"):
        parse_bi5(lzma.compress(b"\x00" * 10), date(2026, 9, 1), 1000)


class FakeFeed:
    """URL -> bytes. Missing URLs behave like HTTP 404 (None). Records every request."""

    def __init__(self, files: dict[str, bytes | Exception]):
        self.files = files
        self.requests: list[str] = []

    def __call__(self, url: str) -> bytes | None:
        self.requests.append(url)
        value = self.files.get(url)
        if isinstance(value, Exception):
            raise value
        return value


def url(day: date, side: Side) -> str:
    return day_url("XAUUSD", day, side, BASE)


SEP1, SEP5 = date(2026, 9, 1), date(2026, 9, 5)  # Tuesday, Saturday


@pytest.fixture
def feed():
    return FakeFeed({url(SEP1, Side.BID): BID_0901, url(SEP1, Side.ASK): ASK_0901})


def test_download_writes_bid_and_ask_per_day(tmp_path, feed):
    dl = DukascopyDownloader(tmp_path, CONFIG, feed)
    results = list(dl.download("XAUUSD", SEP1, date(2026, 9, 2), today=date(2026, 10, 4)))

    assert [(r.day, r.status, r.rows) for r in results] == [(SEP1, DayStatus.DOWNLOADED, 2)]
    path = tmp_path / "XAUUSD" / "2026" / "2026-09-01.parquet"
    df = pd.read_parquet(path)
    assert list(df.columns) == [
        "ts",
        *(f"bid_{f}" for f in ("open", "high", "low", "close", "volume")),
        *(f"ask_{f}" for f in ("open", "high", "low", "close", "volume")),
    ]
    assert df["ts"].iloc[0] == pd.Timestamp("2026-09-01 00:00", tz="UTC")
    assert df["bid_close"].iloc[0] == 3450.8
    assert df["ask_close"].iloc[0] == 3451.1
    assert not list(tmp_path.rglob("*.tmp"))


def test_end_is_exclusive_and_today_is_never_requested(tmp_path, feed):
    dl = DukascopyDownloader(tmp_path, CONFIG, feed)
    days = [r.day for r in dl.download("XAUUSD", SEP1, date(2026, 9, 8), today=date(2026, 9, 3))]
    assert days == [SEP1, date(2026, 9, 2)]  # 09-03 is "today": not final yet
    days = [r.day for r in dl.download("XAUUSD", SEP1, date(2026, 9, 3), today=date(2026, 10, 4))]
    assert days[-1] == date(2026, 9, 2)


def test_resume_skips_cached_days(tmp_path, feed):
    dl = DukascopyDownloader(tmp_path, CONFIG, feed)
    list(dl.download("XAUUSD", SEP1, date(2026, 9, 2), today=date(2026, 10, 4)))
    feed.requests.clear()

    results = list(dl.download("XAUUSD", SEP1, date(2026, 9, 2), today=date(2026, 10, 4)))
    assert results[0].status is DayStatus.CACHED
    assert feed.requests == []


def test_weekend_is_cached_as_empty(tmp_path):
    feed = FakeFeed({url(SEP5, Side.BID): b""})  # empty body for bid, 404 for ask
    dl = DukascopyDownloader(tmp_path, CONFIG, feed)
    (result,) = dl.download("XAUUSD", SEP5, date(2026, 9, 6), today=date(2026, 10, 4))

    assert result.status is DayStatus.EMPTY
    df = pd.read_parquet(dl.path_for("XAUUSD", SEP5))
    assert df.empty and "bid_close" in df.columns
    feed.requests.clear()
    list(dl.download("XAUUSD", SEP5, date(2026, 9, 6), today=date(2026, 10, 4)))
    assert feed.requests == []


@pytest.mark.parametrize(
    "files",
    [
        {url(SEP1, Side.BID): BID_0901},  # ask missing
        {url(SEP1, Side.BID): BID_0901, url(SEP1, Side.ASK): DukascopyError("timeout")},
        {url(SEP1, Side.BID): b"garbage", url(SEP1, Side.ASK): ASK_0901},
    ],
    ids=["one-sided", "network-error", "corrupt"],
)
def test_failed_day_is_not_cached_and_retried_next_run(tmp_path, files):
    dl = DukascopyDownloader(tmp_path, CONFIG, FakeFeed(files))
    (result,) = dl.download("XAUUSD", SEP1, date(2026, 9, 2), today=date(2026, 10, 4))
    assert result.status is DayStatus.FAILED and result.error
    assert not dl.path_for("XAUUSD", SEP1).exists()

    fixed = FakeFeed({url(SEP1, Side.BID): BID_0901, url(SEP1, Side.ASK): ASK_0901})
    dl = DukascopyDownloader(tmp_path, CONFIG, fixed)
    (result,) = dl.download("XAUUSD", SEP1, date(2026, 9, 2), today=date(2026, 10, 4))
    assert result.status is DayStatus.DOWNLOADED


def test_bid_and_ask_minutes_are_outer_joined(tmp_path):
    ask_first_minute_only = bi5((0, 3450420, 3451100, 3449800, 3451300, 1.0))
    feed = FakeFeed({url(SEP1, Side.BID): BID_0901, url(SEP1, Side.ASK): ask_first_minute_only})
    dl = DukascopyDownloader(tmp_path, CONFIG, feed)
    list(dl.download("XAUUSD", SEP1, date(2026, 9, 2), today=date(2026, 10, 4)))
    df = pd.read_parquet(dl.path_for("XAUUSD", SEP1))
    assert len(df) == 2
    assert pd.isna(df["ask_close"].iloc[1]) and df["bid_close"].iloc[1] == 3448.25


def test_unknown_symbol_is_rejected(tmp_path):
    dl = DukascopyDownloader(tmp_path, CONFIG, FakeFeed({}))
    with pytest.raises(ValueError, match="point factor"):
        list(dl.download("EURCHF", SEP1, date(2026, 9, 2)))


def test_cli_downloads_range(tmp_path, monkeypatch, capsys):
    feed = FakeFeed(
        {
            day_url("XAUUSD", SEP1, s, DukascopyConfig().base_url): raw
            for s, raw in ((Side.BID, BID_0901), (Side.ASK, ASK_0901))
        }
    )
    monkeypatch.setattr(duka, "http_fetcher", lambda config: feed)
    code = download.main(["XAUUSD", "2026-09-01", "2026-09-03", "--cache-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 0
    assert "downloaded: 1" in out and "empty: 1" in out
    assert "3450.12" in out


class FakeHTTP:
    """Stands in for http.client.HTTPSConnection. Each request takes the next outcome:
    bytes = 200 response, int = that HTTP status with an empty body, Exception = raised."""

    def __init__(self, outcomes: list[bytes | int | Exception]):
        self.outcomes = outcomes
        self.paths: list[str] = []
        self.connections = 0  # connections opened
        self.sleeps: list[float] = []

    def connection(self, host, timeout):
        self.connections += 1
        fake = self

        class Conn:
            def request(self, method, path, headers):
                fake.paths.append(path)
                outcome = fake.outcomes[len(fake.paths) - 1]
                if isinstance(outcome, Exception):
                    raise outcome
                self.outcome = outcome

            def getresponse(self):
                status, body = (
                    (200, self.outcome)
                    if isinstance(self.outcome, bytes)
                    else (
                        self.outcome,
                        b"",
                    )
                )
                return SimpleNamespace(status=status, read=lambda: body)

            def close(self):
                pass

        return Conn()


@pytest.fixture
def fake_http(monkeypatch):
    def install(outcomes):
        fake = FakeHTTP(outcomes)
        monkeypatch.setattr(duka.http.client, "HTTPSConnection", fake.connection)
        monkeypatch.setattr(duka.time, "sleep", fake.sleeps.append)
        return fake

    return install


NO_DELAY = DukascopyConfig(request_delay_s=0, retries=5, busy_backoff_s=5, network_retry_s=2)


def test_http_fetcher_reuses_one_connection(fake_http):
    fake = fake_http([BID_0901, ASK_0901])
    fetch = duka.http_fetcher(NO_DELAY)
    assert fetch(url(SEP1, Side.BID)) == BID_0901
    assert fetch(url(SEP1, Side.ASK)) == ASK_0901
    assert fake.connections == 1
    assert fake.paths == [
        "/datafeed/XAUUSD/2026/08/01/BID_candles_min_1.bi5",
        "/datafeed/XAUUSD/2026/08/01/ASK_candles_min_1.bi5",
    ]


def test_http_fetcher_retries_network_errors_on_a_new_connection(fake_http):
    fake = fake_http(
        [
            TimeoutError("WinError 10060"),
            ssl.SSLError("handshake timed out"),
            http.client.IncompleteRead(b"partial"),
            BID_0901,
        ]
    )
    assert duka.http_fetcher(NO_DELAY)(url(SEP1, Side.BID)) == BID_0901
    assert fake.connections == 4  # a failed connection is never reused
    assert fake.sleeps == [2, 2, 2, 0]  # short network waits, then the polite delay


def test_http_fetcher_backs_off_longer_when_server_is_busy(fake_http):
    fake = fake_http([503, 503, BID_0901])
    assert duka.http_fetcher(NO_DELAY)(url(SEP1, Side.BID)) == BID_0901
    assert fake.sleeps == [0, 5, 0, 10, 0]  # delay + backoff * attempt after each 503
    assert fake.connections == 1  # an HTTP error keeps the connection


def test_http_fetcher_stale_connection_retried_at_once_without_using_an_attempt(fake_http):
    fake = fake_http([BID_0901, http.client.RemoteDisconnected("closed"), ASK_0901])
    fetch = duka.http_fetcher(dataclasses.replace(NO_DELAY, retries=1))
    fetch(url(SEP1, Side.BID))
    assert fetch(url(SEP1, Side.ASK)) == ASK_0901
    assert fake.connections == 2
    assert fake.sleeps == [0, 0]  # no retry wait


def test_http_fetcher_gives_up_after_last_retry(fake_http):
    fake_http([TimeoutError("timed out")] * 3)
    fetch = duka.http_fetcher(dataclasses.replace(NO_DELAY, retries=3))
    with pytest.raises(DukascopyError, match="giving up.*timed out"):
        fetch(url(SEP1, Side.BID))


def test_http_fetcher_stops_at_once_when_rate_limited(fake_http):
    fake = fake_http([429, BID_0901])
    with pytest.raises(duka.RateLimitedError):
        duka.http_fetcher(NO_DELAY)(url(SEP1, Side.BID))
    assert len(fake.paths) == 1  # no retry hammering a blocked IP


def test_cli_stops_whole_run_when_rate_limited(tmp_path, monkeypatch, capsys):
    feed = FakeFeed({})
    calls = 0

    def limited(u):
        nonlocal calls
        calls += 1
        if calls > 2:  # first day (bid + ask) succeeds, then the IP is blocked
            raise duka.RateLimitedError("HTTP 429")
        return feed(u)

    monkeypatch.setattr(duka, "http_fetcher", lambda config: limited)
    code = download.main(["XAUUSD", "2026-09-05", "2026-09-10", "--cache-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert code == 1
    assert "STOPPED" in out and "empty: 1" in out
    assert calls == 3  # nothing requested after the 429
    assert len(list(tmp_path.rglob("*.parquet"))) == 1


def test_http_fetcher_404_means_no_file(fake_http):
    fake_http([404])
    assert duka.http_fetcher(NO_DELAY)(url(SEP5, Side.BID)) is None


# Real Dukascopy file, saved once from
# https://datafeed.dukascopy.com/datafeed/XAUUSD/2026/08/01/BID_candles_min_1.bi5
REAL_BID_FILE = Path(__file__).parent / "fixtures" / "XAUUSD_2026-09-01_BID_candles_min_1.bi5"


@pytest.mark.skipif(not REAL_BID_FILE.exists(), reason=f"sample file missing: {REAL_BID_FILE}")
def test_real_xauusd_file_parses_to_known_candles():
    df = parse_bi5(REAL_BID_FILE.read_bytes(), date(2026, 9, 1), duka.POINT_FACTORS["XAUUSD"])

    assert len(df) == 1440  # Dukascopy fills every minute of the day
    first = df.iloc[0]
    assert first.ts == pd.Timestamp("2026-09-01 00:00", tz="UTC")
    assert (first.open, first.high, first.low, first.close) == (
        4452.165,
        4454.095,
        4446.115,
        4446.535,
    )
    # Gold's daily break (21:00-21:59 UTC in summer) is filled with flat zero-volume minutes.
    brk = df[(df.ts >= "2026-09-01 21:00Z") & (df.ts < "2026-09-01 22:00Z")]
    assert len(brk) == 60 and (brk.volume == 0).all()
    assert (brk.open == brk.high).all() and (brk.low == brk.close).all()
    assert (brk.high == brk.low).all()
