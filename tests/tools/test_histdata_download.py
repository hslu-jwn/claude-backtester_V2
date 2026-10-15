"""histdata.com downloader: form parsing, POST fields, file names, resume, bad responses.

No network: a fake client serves a saved page fixture and in-memory zip files."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from backtester.data.histdata import SYMBOL_NAMES, files_in
from backtester.tools import histdata_download as hd

FIXTURE = Path(__file__).parent / "fixtures" / "histdata_page_eurusd_2019.html"


def make_zip(name: str = "DAT_MT_EURUSD_M1_2019.csv") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(name, "2019.01.02,00:00,1.1,1.2,1.0,1.1,0\n")
    return buf.getvalue()


class FakeClient:
    def __init__(self, page: str | None = None, body: bytes | None = None):
        self.page = FIXTURE.read_text() if page is None else page
        self.body = make_zip() if body is None else body
        self.gets: list[str] = []
        self.posts: list[tuple[str, dict, str]] = []

    def get(self, url: str) -> str:
        self.gets.append(url)
        return self.page

    def post(self, url: str, data: dict, referer: str) -> bytes:
        self.posts.append((url, data, referer))
        return self.body


def test_parse_form_reads_all_hidden_fields():
    form = hd.parse_form(FIXTURE.read_text())
    assert form == {
        "tk": "1507800ad3526972923b836be67de982",
        "date": "2019",
        "datemonth": "2019",
        "platform": "MT",
        "timeframe": "M1",
        "fxpair": "EURUSD",
    }


def test_parse_form_without_form_is_error():
    with pytest.raises(hd.DownloadError):
        hd.parse_form("<html>maintenance</html>")


def test_parse_form_missing_token_is_error():
    html = FIXTURE.read_text().replace('name="tk"', 'name="xx"')
    with pytest.raises(hd.DownloadError):
        hd.parse_form(html)


def test_page_url_year_and_month():
    base = "http://www.histdata.com/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes/"
    assert hd.page_url("EURUSD", "2019") == base + "eurusd/2019"
    assert hd.page_url("GBPJPY", "202103") == base + "gbpjpy/2021/3"


def test_periods_default():
    ps = hd.default_periods()
    assert ps[0] == "2015" and "2020" in ps
    assert ps[-9:] == [f"2021{m:02d}" for m in range(1, 10)]
    assert len(ps) == 6 + 9


def test_target_path_uses_our_symbol_name_and_is_importable(tmp_path):
    p = hd.target_path(tmp_path, "NSXUSD", "2019")
    assert p == tmp_path / "NAS100" / "HISTDATA_COM_MT_NSXUSD_M1_2019.zip"
    p = hd.target_path(tmp_path, "EURUSD", "202101")
    assert p == tmp_path / "EURUSD" / "HISTDATA_COM_MT_EURUSD_M1_202101.zip"


def test_download_posts_form_with_referer_and_saves_zip(tmp_path):
    c = FakeClient()
    status = hd.download_period(c, "EURUSD", "2019", tmp_path)
    assert status == "downloaded"
    url, data, referer = c.posts[0]
    assert url == "http://www.histdata.com/get.php"
    assert referer == hd.page_url("EURUSD", "2019") == c.gets[0]
    assert data["tk"] == "1507800ad3526972923b836be67de982"
    assert data["fxpair"] == "EURUSD" and data["platform"] == "MT"
    path = hd.target_path(tmp_path, "EURUSD", "2019")
    assert path.read_bytes() == make_zip()
    assert not list(path.parent.glob("*.part"))
    # the importer accepts the saved file
    (mf,) = files_in(path)
    assert mf.symbol == "EURUSD" and mf.yearly and mf.month.year == 2019


def test_download_skips_existing_without_requests(tmp_path):
    path = hd.target_path(tmp_path, "EURUSD", "2019")
    path.parent.mkdir(parents=True)
    path.write_bytes(make_zip())
    c = FakeClient()
    assert hd.download_period(c, "EURUSD", "2019", tmp_path) == "skipped"
    assert c.gets == [] and c.posts == []


@pytest.mark.parametrize("body", [b"<html>captcha</html>", b"", b"PK\x03\x04 broken"])
def test_non_zip_response_is_error_and_nothing_saved(tmp_path, body):
    c = FakeClient(body=body)
    with pytest.raises(hd.DownloadError):
        hd.download_period(c, "EURUSD", "2019", tmp_path)
    assert not hd.target_path(tmp_path, "EURUSD", "2019").exists()
    assert not list(tmp_path.rglob("*.part"))


def test_zip_without_matching_csv_is_error(tmp_path):
    c = FakeClient(body=make_zip("evil.exe"))
    with pytest.raises(hd.DownloadError):
        hd.download_period(c, "EURUSD", "2019", tmp_path)
    assert not hd.target_path(tmp_path, "EURUSD", "2019").exists()


def test_run_continues_on_missing_and_stops_on_repeated_http_errors(tmp_path):
    class Boom(FakeClient):
        def get(self, url):
            raise hd.HttpError("503")

    sleeps: list[float] = []
    out = hd.run(
        Boom(),
        ["EURUSD", "GBPUSD"],
        ["2019", "2020", "2021", "2022"],
        tmp_path,
        sleep=sleeps.append,
        log=lambda m: None,
    )
    assert out.stopped
    assert len(out.errors) == hd.MAX_CONSECUTIVE_ERRORS


def test_run_records_missing_and_waits_between_requests(tmp_path):
    c = FakeClient(body=b"<html>no data</html>")
    sleeps: list[float] = []
    out = hd.run(c, ["GRXEUR"], ["2015", "2016"], tmp_path, sleep=sleeps.append, log=lambda m: None)
    assert out.missing == [("GRXEUR", "2015"), ("GRXEUR", "2016")]
    assert not out.stopped
    assert sleeps == [hd.DELAY_SECONDS] * 2


def test_run_downloads_and_skips(tmp_path):
    c = FakeClient()
    out = hd.run(c, ["EURUSD"], ["2019"], tmp_path, sleep=lambda s: None, log=lambda m: None)
    assert out.downloaded == [("EURUSD", "2019")]
    out2 = hd.run(c, ["EURUSD"], ["2019"], tmp_path, sleep=lambda s: None, log=lambda m: None)
    assert out2.skipped == [("EURUSD", "2019")] and out2.downloaded == []


def test_downloaded_content_is_never_executed():
    src = Path(hd.__file__).read_text()
    for banned in ("subprocess", "os.system", "exec(", "eval(", "extractall", "pickle"):
        assert banned not in src


def test_symbol_names_for_histdata_indices_energy_dxy():
    expected = {
        "SPXUSD": "US500",
        "NSXUSD": "NAS100",
        "GRXEUR": "GER40",
        "UKXGBP": "UK100",
        "JPXJPY": "JP225",
        "ETXEUR": "EU50",
        "WTIUSD": "USOIL",
        "BCOUSD": "UKOIL",
        "UDXUSD": "DXY",
    }
    for k, v in expected.items():
        assert SYMBOL_NAMES[k] == v
    assert "EURUSD" not in SYMBOL_NAMES and "XAUUSD" not in SYMBOL_NAMES
