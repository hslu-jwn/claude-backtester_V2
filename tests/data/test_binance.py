"""Binance aggTrades -> 1m bars + order flow (ROADMAP 11.9). No network: fake fetch."""

from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
import pytest

from backtester.data.binance import (
    BinanceConfig,
    ChecksumError,
    NotFoundError,
    archive_url,
    download_funding,
    download_month,
    download_symbol,
    parse_trades_zip,
)
from backtester.data.cache import COLUMNS, cache_path, read_cached_day

HEADER = "agg_trade_id,price,quantity,first_trade_id,last_trade_id,transact_time,is_buyer_maker\n"


def ms(*args) -> int:
    return int(datetime(*args, tzinfo=UTC).timestamp() * 1000)


def trade(i, price, qty, first, last, t, maker) -> str:
    return f"{i},{price},{qty},{first},{last},{t},{'true' if maker else 'false'}\n"


def make_zip(csv_text: str, name="x.csv") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(name, csv_text)
    return buf.getvalue()


class FakeArchive:
    """url -> bytes; serves the zip and a matching .CHECKSUM. Records fetched urls."""

    def __init__(self, files: dict[str, bytes], bad_checksum=False):
        self.files, self.bad, self.calls = files, bad_checksum, []

    def __call__(self, url: str, dest: Path) -> None:
        self.calls.append(url)
        if url.endswith(".CHECKSUM"):
            data = self.files.get(url[: -len(".CHECKSUM")])
            if data is None:
                raise NotFoundError(url)
            digest = "0" * 64 if self.bad else hashlib.sha256(data).hexdigest()
            dest.write_text(f"{digest}  {Path(url).name[:-9]}\n")
        else:
            if url not in self.files:
                raise NotFoundError(url)
            dest.write_bytes(self.files[url])


@pytest.fixture
def cfg(tmp_path):
    return BinanceConfig(
        cache_dir=tmp_path / "c", flow_dir=tmp_path / "f", funding_dir=tmp_path / "fu",
        tmp_dir=tmp_path / "tmp",
    )  # fmt: skip


JAN = date(2024, 1, 1)
TODAY = date(2024, 3, 1)
URL = archive_url("aggTrades", "BTCUSDT", "2024-01", False)


def jan_csv(header: bool) -> str:
    rows = [
        # minute 00:00 on Jan 1: two buys, one sell; listed out of price order
        trade(1, "100.0", "1.0", 1, 1, ms(2024, 1, 1, 0, 0, 5), False),
        trade(2, "103.0", "2.0", 2, 4, ms(2024, 1, 1, 0, 0, 20), False),  # 3 trades aggregated
        trade(3, "99.0", "0.5", 5, 5, ms(2024, 1, 1, 0, 0, 30), True),
        trade(4, "101.0", "1.5", 6, 6, ms(2024, 1, 1, 0, 0, 59), True),
        # minute 00:01
        trade(5, "102.0", "1.0", 7, 7, ms(2024, 1, 1, 0, 1, 0), False),
        # Jan 1 23:59 and Jan 2 00:00 (UTC day split)
        trade(6, "110.0", "1.0", 8, 8, ms(2024, 1, 1, 23, 59, 59), False),
        trade(7, "111.0", "2.0", 9, 9, ms(2024, 1, 2, 0, 0, 0), True),
    ]
    return (HEADER if header else "") + "".join(rows)


@pytest.mark.parametrize("header", [True, False])
def test_parse_minute_aggregation_exact(tmp_path, header):
    z = tmp_path / "a.zip"
    z.write_bytes(make_zip(jan_csv(header)))
    bars = parse_trades_zip(z, chunk_rows=3)  # chunk boundary inside minute 0
    m0 = bars.loc[ms(2024, 1, 1) // 60000]
    assert (m0.open, m0.high, m0.low, m0.close) == (100.0, 103.0, 99.0, 101.0)
    assert m0.buy == 3.0 and m0.sell == 2.0
    assert m0.trades == 1 + 3 + 1 + 1
    assert len(bars) == 4  # minutes 00:00, 00:01, 23:59, next day 00:00


def test_open_close_by_trade_time_not_row_order(tmp_path):
    rows = trade(2, "50.0", "1", 2, 2, ms(2024, 1, 1, 0, 0, 40), False) + trade(
        1, "40.0", "1", 1, 1, ms(2024, 1, 1, 0, 0, 10), False
    )
    z = tmp_path / "a.zip"
    z.write_bytes(make_zip(rows))
    for chunk in (1, 10):
        bars = parse_trades_zip(z, chunk_rows=chunk)
        assert (bars.open.iloc[0], bars.close.iloc[0]) == (40.0, 50.0)


def test_microsecond_timestamps_are_normalised(tmp_path):
    z = tmp_path / "a.zip"
    z.write_bytes(make_zip(trade(1, "1", "1", 1, 1, ms(2024, 1, 1, 0, 3) * 1000, False)))
    assert parse_trades_zip(z).index[0] == ms(2024, 1, 1, 0, 3) // 60000


def test_download_month_writes_cache_and_flow_and_deletes_zip(cfg):
    fetch = FakeArchive({URL: make_zip(jan_csv(True))})
    r = download_month("BTCUSDT", JAN, cfg, fetch, TODAY)
    assert not r.skipped and r.bars == 4
    day1 = read_cached_day(cache_path(cfg.cache_dir, "BTCUSDT", date(2024, 1, 1)))
    assert list(day1.columns) == COLUMNS
    assert len(day1) == 3  # 00:00, 00:01, 23:59; no row for minutes without trades
    first = day1.iloc[0]
    assert first.ts == pd.Timestamp("2024-01-01 00:00", tz="UTC")
    assert first.bid_open == first.ask_open == 100.0
    assert first.bid_high == first.ask_high == 103.0
    assert first.bid_volume == first.ask_volume == 5.0
    flow = read_cached_day(cache_path(cfg.flow_dir, "BTCUSDT", date(2024, 1, 1)))
    assert list(flow.columns) == ["ts", "volume", "buy_volume", "sell_volume", "delta", "trades"]
    f0 = flow.iloc[0]
    assert (f0.volume, f0.buy_volume, f0.sell_volume, f0.delta, f0.trades) == (
        5.0,
        3.0,
        2.0,
        1.0,
        6,
    )
    day2 = read_cached_day(cache_path(cfg.cache_dir, "BTCUSDT", date(2024, 1, 2)))
    assert len(day2) == 1 and day2.bid_close.iloc[0] == 111.0  # UTC day split
    # a day with no trades is cached as an empty file
    empty = read_cached_day(cache_path(cfg.cache_dir, "BTCUSDT", date(2024, 1, 15)))
    assert len(empty) == 0 and list(empty.columns) == COLUMNS
    assert not list(cfg.tmp_dir.iterdir())  # zip and checksum deleted


def test_checksum_mismatch_raises_and_writes_nothing(cfg):
    fetch = FakeArchive({URL: make_zip(jan_csv(True))}, bad_checksum=True)
    with pytest.raises(ChecksumError):
        download_month("BTCUSDT", JAN, cfg, fetch, TODAY)
    assert not cfg.cache_dir.exists() and not cfg.flow_dir.exists()
    assert not list(cfg.tmp_dir.iterdir())


def test_resume_skips_done_month(cfg):
    fetch = FakeArchive({URL: make_zip(jan_csv(True))})
    download_month("BTCUSDT", JAN, cfg, fetch, TODAY)
    fetch.calls.clear()
    r = download_month("BTCUSDT", JAN, cfg, fetch, TODAY)
    assert r.skipped and fetch.calls == []


def test_empty_month_writes_empty_days(cfg):
    fetch = FakeArchive({URL: make_zip(HEADER)})
    r = download_month("BTCUSDT", JAN, cfg, fetch, TODAY)
    assert r.bars == 0
    assert len(read_cached_day(cache_path(cfg.cache_dir, "BTCUSDT", date(2024, 1, 31)))) == 0


def test_trades_outside_the_month_are_an_error(cfg):
    rows = trade(1, "1", "1", 1, 1, ms(2024, 2, 1), False)
    fetch = FakeArchive({URL: make_zip(rows)})
    with pytest.raises(ValueError):
        download_month("BTCUSDT", JAN, cfg, fetch, TODAY)
    assert not list(cfg.tmp_dir.iterdir())


def test_falls_back_to_daily_files_and_skips_unpublished_days(cfg):
    d1 = archive_url("aggTrades", "BTCUSDT", "2024-03-01", True)
    csv1 = trade(1, "5", "1", 1, 1, ms(2024, 3, 1, 10), False)
    fetch = FakeArchive({d1: make_zip(csv1)})
    r = download_month("BTCUSDT", date(2024, 3, 1), cfg, fetch, date(2024, 3, 4))
    assert r.daily and r.missing_days == 2 and r.bars == 1  # Mar 2, 3 not published
    assert cache_path(cfg.cache_dir, "BTCUSDT", date(2024, 3, 1)).exists()
    assert not cache_path(cfg.cache_dir, "BTCUSDT", date(2024, 3, 2)).exists()
    assert not cache_path(cfg.cache_dir, "BTCUSDT", date(2024, 3, 4)).exists()  # today: not closed


def test_funding_rates_saved_and_resumable(cfg):
    url = archive_url("fundingRate", "BTCUSDT", "2024-01", False)
    text = "calc_time,funding_interval_hours,last_funding_rate\n"
    text += f"{ms(2024, 1, 1, 8)},8,0.0001\n{ms(2024, 1, 1, 16)},8,-0.00005\n"
    fetch = FakeArchive({url: make_zip(text)})
    assert download_funding("BTCUSDT", [JAN], cfg, fetch) == 2
    out = (cfg.funding_dir / "BTCUSDT.csv").read_text().splitlines()
    assert out[1] == "2024-01-01 08:00:00,8,0.0001" and out[2].endswith("-0.00005")
    fetch.calls.clear()
    assert download_funding("BTCUSDT", [JAN], cfg, fetch) == 2 and fetch.calls == []


def test_download_symbol_end_to_end(cfg):
    fetch = FakeArchive({URL: make_zip(jan_csv(False))})
    results = download_symbol("BTCUSDT", JAN, date(2024, 1, 20), cfg, fetch, today=TODAY)
    assert len(results) == 1 and results[0].bars == 4
