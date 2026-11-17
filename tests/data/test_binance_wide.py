"""Local CSV roots and injected monthly S3 downloads; no network."""

import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import pytest

from backtester.data import binance_wide as data

KLINE = "1704067200000,100,110,90,105,10,1704153599999,6000000,1,6,3600000,0\n"
HEADER = (
    "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
    "taker_buy_volume,taker_buy_quote_volume,ignore\n"
)
FHEADER = "calc_time,funding_interval_hours,last_funding_rate\n"


def write(root, kind, text, sym="BTCUSDT"):
    path = root / kind / f"{sym}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_read_roots_header_and_no_header(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    write(a, "klines_1d", HEADER + KLINE)
    write(
        b,
        "klines_1d",
        KLINE.replace(",105,", ",999,") + KLINE.replace("1704067200000", "1704153600000"),
    )
    write(b, "funding", "1704096000123,8,0.0001\n")
    write(a, "funding", FHEADER + "1704067200000,8,0.0002\n")
    write(b, "klines_1d", HEADER + KLINE, "ETHUSDT")
    d = data.read_klines("BTCUSDT", (a, b))
    assert list(d.columns) == ["open", "close", "volume", "quote_volume", "taker_buy_volume"]
    assert list(d.index) == list(pd.date_range("2024-01-01", periods=2, tz="UTC"))
    assert d.close.tolist() == [105, 105]
    f = data.read_funding("BTCUSDT", (a, b))
    assert f.index.tolist() == [
        pd.Timestamp("2024-01-01", tz="UTC"),
        pd.Timestamp("2024-01-01 08:00", tz="UTC"),
    ]
    assert f.tolist() == [0.0002, 0.0001]
    empty = data.read_funding("NONE", (a, b))
    assert empty.empty and isinstance(empty.index, pd.DatetimeIndex)
    assert str(empty.index.tz) == "UTC"
    assert data.symbols((a, b)) == ["BTCUSDT", "ETHUSDT"]


def zipped(text):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("data.csv", text)
    return stream.getvalue()


@pytest.mark.parametrize("end_month", ["2024-02", "2099-12"])
@pytest.mark.parametrize("cached_funding", [True, False])
def test_update_missing_months_pagination_and_atomic(
    tmp_path,
    monkeypatch,
    end_month,
    cached_funding,
):
    class March2024(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2024, 3, 15, tzinfo=UTC)

    monkeypatch.setattr(data, "datetime", March2024)
    write(tmp_path, "klines_1d", HEADER + KLINE)
    if cached_funding:
        write(tmp_path, "funding", FHEADER + "1704067200000,8,0.0001\n")
    base = "data/futures/um/monthly/"
    calls, replaces = [], []

    def fetch(url, params=None):
        calls.append((url, params))
        if params is not None:
            prefix = params["prefix"]
            if prefix == base + "klines/":
                if not params.get("marker"):
                    return (
                        f'<ListBucketResult xmlns="{data.NS[1:-1]}"><IsTruncated>true</IsTruncated>'
                        f"<NextMarker>page2</NextMarker><CommonPrefixes><Prefix>{prefix}BTCUSDT/</Prefix>"
                        "</CommonPrefixes></ListBucketResult>"
                    ).encode()
                assert params["marker"] == "page2"
                names = ["ETHUSDT", "BTCUSDT_240329", "ETHBTC"]
                contents = "".join(
                    f"<CommonPrefixes><Prefix>{prefix}{s}/</Prefix></CommonPrefixes>" for s in names
                )
            else:
                # January already cached for BTC; March is outside requested complete range.
                contents = "".join(
                    f"<Contents><Key>{prefix}X-2024-{m}.zip</Key></Contents>"
                    for m in ["01", "02", "03"]
                )
            return (
                f'<ListBucketResult xmlns="{data.NS[1:-1]}"><IsTruncated>false</IsTruncated>'
                f"{contents}</ListBucketResult>"
            ).encode()
        key = urlparse(url).path
        timestamp = "1706745600000" if "2024-02" in key else "1704067200000"
        if "/fundingRate/" in key:
            return zipped(FHEADER + f"{timestamp},8,0.0001\n")
        return zipped(
            (HEADER if "2024-02" in key else "") + KLINE.replace("1704067200000", timestamp)
        )

    original_replace = Path.replace

    def replace(path, target):
        assert path.suffix == ".tmp" and target.suffix == ".csv"
        replaces.append(target)
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", replace)
    data.update(tmp_path, end_month, fetch=fetch)
    downloads = [url for url, params in calls if params is None]
    # BTC February x2; new ETH January + February x2; missing BTC funding adds January.
    assert len(downloads) == (6 if cached_funding else 7)
    assert not any("/klines/BTCUSDT/" in url and "2024-01" in url for url in downloads)
    assert not any("2024-03" in url or "ETHBTC" in url or "_240329" in url for url in downloads)
    assert len(replaces) == 4 and not list(tmp_path.rglob("*.tmp"))
    assert len(data.read_klines("BTCUSDT", (tmp_path,))) == 2
    assert len(data.read_klines("ETHUSDT", (tmp_path,))) == 2
    calls.clear()
    data.update(tmp_path, end_month, fetch=fetch)
    assert not [url for url, params in calls if params is None]


def test_failed_download_preserves_existing_file(tmp_path):
    path = write(tmp_path, "klines_1d", HEADER + KLINE)
    original = path.read_bytes()

    def fetch(url, params=None):
        if params is None:
            raise OSError("download failed")
        prefix = params["prefix"]
        contents = (
            f"<CommonPrefixes><Prefix>{prefix}BTCUSDT/</Prefix></CommonPrefixes>"
            if prefix.endswith("klines/")
            else f"<Contents><Key>{prefix}BTCUSDT-2024-02.zip</Key></Contents>"
        )
        return f"<ListBucketResult>{contents}</ListBucketResult>".encode()

    with pytest.raises(OSError, match="download failed"):
        data.update(tmp_path, "2024-02", fetch=fetch)
    assert path.read_bytes() == original


def test_update_spot_appends_complete_months_for_given_symbols(tmp_path, monkeypatch):
    class Dec2026(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 12, 3, tzinfo=UTC)

    monkeypatch.setattr(data, "datetime", Dec2026)
    calls = []

    def fetch(url, params=None):
        calls.append((url, params))
        if params is not None:
            prefix = params["prefix"]
            assert prefix.startswith("data/spot/monthly/klines/")
            months = ["2026-09", "2026-10", "2026-11", "2026-12"] if "BTCUSDT" in prefix else []
            contents = "".join(f"<Contents><Key>{prefix}X-{m}.zip</Key></Contents>" for m in months)
            return f"<ListBucketResult><IsTruncated>false</IsTruncated>{contents}</ListBucketResult>".encode()
        month = urlparse(url).path[-11:-4]
        ts = {"2026-10": "1790812800000", "2026-11": "1793491200000"}[month]
        return zipped(KLINE.replace("1704067200000", ts))

    data.update_spot(
        tmp_path, ["BTCUSDT", "NOSPOTUSDT"], "2099-12", start_after="2026-09", fetch=fetch
    )
    downloads = [urlparse(url).path for url, params in calls if params is None]
    assert [d[-11:-4] for d in downloads] == [
        "2026-10",
        "2026-11",
    ]  # after start_after, complete months only
    assert len(data.read_klines("BTCUSDT", (tmp_path,))) == 2
    assert not (tmp_path / "klines_1d" / "NOSPOTUSDT.csv").exists()
    calls.clear()
    data.update_spot(tmp_path, ["BTCUSDT"], "2099-12", start_after="2026-09", fetch=fetch)
    assert not [url for url, params in calls if params is None]  # resume: nothing new


def test_fetch_percent_encodes_non_ascii_symbols(monkeypatch):
    seen = []

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(url, timeout, context):
        seen.append(url)
        return Response(b"ok")

    monkeypatch.setattr(data.urllib.request, "urlopen", urlopen)
    assert data._fetch(data.CDN + "data/spot/monthly/klines/币安USDT/1d/x.zip") == b"ok"
    data._fetch(data.S3, params={"prefix": "data/spot/币/", "marker": ""})
    assert (
        all(u.isascii() for u in seen)
        and "%E5%B8%81" in seen[0]
        and "prefix=data%2Fspot%2F%E5%B8%81" in seen[1]
    )


def test_fetch_retries_a_dropped_connection_but_not_a_missing_file(monkeypatch):
    import urllib.error

    calls = []

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def flaky(url, timeout, context):
        calls.append(url)
        if len(calls) == 1:
            raise urllib.error.URLError(ConnectionResetError(10054, "reset"))
        return Response(b"ok")

    monkeypatch.setattr(data.time, "sleep", lambda s: None)
    monkeypatch.setattr(data.urllib.request, "urlopen", flaky)
    assert data._fetch(data.CDN + "x.zip") == b"ok" and len(calls) == 2

    def missing(url, timeout, context):
        calls.append(url)
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    calls.clear()
    monkeypatch.setattr(data.urllib.request, "urlopen", missing)
    with pytest.raises(urllib.error.HTTPError):
        data._fetch(data.CDN + "x.zip")
    assert len(calls) == 1
