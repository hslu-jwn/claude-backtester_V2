"""The Monte Carlo report route (ui/report_route.py): serves files under results/monte_carlo
only; path traversal is impossible."""

from __future__ import annotations

import pytest
from flask import Flask

from backtester.ui import report_route


@pytest.fixture
def client(tmp_path):
    root = tmp_path / "results"
    (root / "monte_carlo" / "run1").mkdir(parents=True)
    (root / "monte_carlo" / "run1" / "report.html").write_text("<html>REPORT</html>")
    (root / "monte_carlo" / "run1" / "summary.json").write_text('{"a": 1}')
    (root / "monte_carlo" / "run1" / "notes.txt").write_text("not served")
    (root / "secret.txt").write_text("SECRET")
    (root / "run2").mkdir()
    (root / "run2" / "trades.csv").write_text("SECRET")
    (tmp_path / "outside.html").write_text("OUTSIDE")
    app = Flask(__name__)
    report_route.register(app, root)
    return app.test_client()


def test_serves_an_existing_report(client):
    r = client.get("/monte-carlo/run1/report.html")
    assert r.status_code == 200 and b"REPORT" in r.data
    assert r.mimetype == "text/html"
    assert client.get("/monte-carlo/run1/summary.json").status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/monte-carlo/run1/missing.html",
        "/monte-carlo/nope/report.html",
        "/monte-carlo/run1/notes.txt",  # not a report file
        "/monte-carlo/run1",  # a folder
        "/monte-carlo/../secret.txt",
        "/monte-carlo/run1/../../secret.txt",
        "/monte-carlo/run1/../../run2/trades.csv",
        "/monte-carlo/run1/%2e%2e/%2e%2e/secret.txt",
        "/monte-carlo/%2e%2e/outside.html",
        "/monte-carlo/run1/..%2f..%2fsecret.txt",
        "/monte-carlo//etc/passwd",
        "/monte-carlo/C:/Windows/win.ini",
        "/monte-carlo/run1\\..\\..\\secret.txt",
    ],
)
def test_everything_else_is_refused(client, path):
    assert client.get(path, follow_redirects=True).status_code in (400, 404)


def test_safe_path_refuses_parent_and_absolute_names(tmp_path):
    root = tmp_path / "monte_carlo"
    root.mkdir()
    (root / "a").mkdir()
    (root / "a" / "report.html").write_text("x")
    assert report_route.safe_path(root, "a/report.html") == (root / "a" / "report.html").resolve()
    for bad in (
        "../x.html",
        "a/../../x.html",
        "/a/report.html",
        "a\\report.html",
        "",
        "a/",
        "C:/x.html",
    ):
        assert report_route.safe_path(root, bad) is None


def test_a_folder_symlinked_out_of_the_root_is_refused(tmp_path):
    root = tmp_path / "monte_carlo"
    root.mkdir()
    outside = tmp_path / "other"
    outside.mkdir()
    (outside / "report.html").write_text("OUT")
    try:
        (root / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("no symlink right on this machine")
    assert report_route.safe_path(root, "link/report.html") is None
