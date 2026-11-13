"""Challenge path CLI uses saved trades and writes only into the supplied run."""

import csv
import json

import pytest

from backtester.tools import challenge_path as tool


@pytest.fixture
def run(tmp_path):
    folder = tmp_path / "sample"
    folder.mkdir()
    (folder / "summary.json").write_text(
        json.dumps({"symbols": ["XAUUSD"], "start": "2020-01-01", "end": "2020-03-31"}),
        encoding="utf8",
    )
    (folder / "settings.json").write_text("{}", encoding="utf8")
    row = {
        "id": 1,
        "symbol": "XAUUSD",
        "direction": "long",
        "entry_time": "2020-01-01T10:00:00+00:00",
        "entry_candle": "2020-01-01T10:00:00+00:00",
        "entry": 100,
        "initial_stop": 99,
        "exit_time": "2020-01-01T11:00:00+00:00",
        "exit_price": 102,
        "exit_reason": "signal",
        "r_gross": 2,
        "r_net": 2,
        "spread_r": 0,
        "commission_r": 0,
    }
    with (folder / "trades.csv").open("w", newline="", encoding="utf8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    return tmp_path, folder


def test_cli_writes_json_and_markdown(run):
    root, folder = run
    assert (
        tool.main(
            [
                "sample",
                "--results-dir",
                str(root),
                "--watch-days",
                "5",
                "--fee",
                "ftmo_2step=250",
                "ftmo_1step=100",
            ]
        )
        == 0
    )
    report = json.loads((folder / "challenge_path.json").read_text(encoding="utf8"))
    assert set(report["rules"]) == {"ftmo_2step", "ftmo_1step", "ftmo_instant"}
    assert len(report["rules"]["ftmo_2step"]["attempts"]) == 3
    assert report["rules"]["ftmo_2step"]["attempts"][0]["path"]
    md = (folder / "challenge_path.md").read_text(encoding="utf8").lower()
    for expected in (
        "ftmo_2step",
        "before refund",
        "after refund",
        "news",
        "market",
        "instant",
        "fees",
        "not published",
        "open",
        "p90",
    ):
        assert expected in md


@pytest.mark.parametrize(
    "extra",
    [
        ["--rules", "unknown"],
        ["--risk", "nan"],
        ["--risk", "0"],
        ["--watch-days", "0"],
        ["--fee", "ftmo_2step=-1"],
        ["--fee", "bad"],
        ["--fee", "unknown=1"],
        ["--fee", "ftmo_1step=inf"],
    ],
)
def test_bad_input_is_argparse_error(run, extra, capsys):
    root, folder = run
    with pytest.raises(SystemExit) as caught:
        tool.main(["sample", "--results-dir", str(root), *extra])
    assert caught.value.code == 2
    assert "error:" in capsys.readouterr().err
    assert not (folder / "challenge_path.json").exists()


def test_missing_and_malformed_run_are_argparse_errors(tmp_path, capsys):
    with pytest.raises(SystemExit) as caught:
        tool.main(["missing", "--results-dir", str(tmp_path)])
    assert caught.value.code == 2
    assert "Traceback" not in capsys.readouterr().err


def test_malformed_run_structure_is_argparse_error(run, capsys):
    root, folder = run
    (folder / "summary.json").write_text("[]", encoding="utf8")
    with pytest.raises(SystemExit) as caught:
        tool.main(["sample", "--results-dir", str(root)])
    assert caught.value.code == 2
    assert "Traceback" not in capsys.readouterr().err
