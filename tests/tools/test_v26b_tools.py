"""CLI regressions for V2.6b, no terminal/network/cache rebuild."""

import io
from datetime import date

import pytest


@pytest.mark.parametrize(
    "extra",
    [
        ["2020-01-02", "2020-01-01"],
        ["2020-01-01", "2020-01-01"],
        ["2020-01-01", "2020-01-02", "--tz", "Not/AZone"],
    ],
)
def test_show_bad_inputs_are_clean(extra, capsys):
    from backtester.tools.show import main

    with pytest.raises(SystemExit) as exc:
        main(["GBPUSD", "M1", *extra])
    assert exc.value.code == 2
    assert "error:" in capsys.readouterr().err


def test_check_uses_preferred_day_sources(tmp_path):
    from backtester.data.cache import cache_path, write_atomic
    from backtester.data.histdata import parse_histdata_mt
    from backtester.data.sources import SymbolSources
    from backtester.tools import check

    day = date(2020, 1, 2)
    for folder, price in [("main", 100), ("pref", 200)]:
        frame = parse_histdata_mt(
            io.StringIO(f"2020.01.02,12:00,{price},{price},{price},{price},0\n")
        )
        write_atomic(frame, cache_path(tmp_path / folder, "GBPUSD", day))
    sources = SymbolSources(
        {"GBPUSD": tmp_path / "main"}, preferred_dirs={"GBPUSD": tmp_path / "pref"}
    )
    result = check.check_symbol(tmp_path / "main", "GBPUSD", sources=sources)
    assert list(result.price_range.loc[2020]) == [200, 200]


def test_rebuild_plan_has_one_valid_job_per_feed_symbol_and_no_overlaps():
    import re
    import shlex
    from itertools import pairwise
    from pathlib import Path

    from backtester.data.histdata import files_in
    from backtester.tools.queue import parser

    plan = Path("scripts/rebuild_cache_v26b.md").read_text(encoding="utf-8")
    seen = set()
    proof_tables = []
    for line in plan.splitlines():
        if not line.startswith("python -m backtester.tools.queue add "):
            continue
        args = parser().parse_args(shlex.split(line)[3:])
        argv = args.argv[1:]
        assert re.fullmatch(r"backtester\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", argv[0])
        if argv[0] == "backtester.data.histdata":
            files = [f for path in argv[1:] for f in files_in(Path(path))]
            assert len({f.symbol for f in files}) == 1
            files.sort(key=lambda f: f.month)
            assert all(a.end <= b.month for a, b in pairwise(files))
            symbol = files[0].symbol
        else:
            assert argv[0] == "backtester.tools.cache_repair"
            if "--prove-clock" in argv:
                assert not proof_tables
                assert not any(module == "backtester.tools.cache_repair" for module, _ in seen)
                proof_tables.append(argv[argv.index("--clock-table") + 1])
                continue
            assert len(proof_tables) == 1
            assert argv[argv.index("--clock-table") + 1] == proof_tables[0]
            symbol = argv[1]
        key = (argv[0], symbol)
        assert key not in seen
        seen.add(key)
    assert sum(module == "backtester.data.histdata" for module, _ in seen) == 21
    assert sum(module == "backtester.tools.cache_repair" for module, _ in seen) == 26
    assert len(proof_tables) == 1


def test_trials_negative_count_rejected(tmp_path, capsys):
    from backtester.tools.trials import main

    path = tmp_path / "trials.jsonl"
    with pytest.raises(SystemExit) as exc:
        main(["--log", str(path), "add", "x", "x", "--count", "-1"])
    assert exc.value.code == 2
    assert not path.exists()


def test_shared_mt5_defaults():
    from backtester.data import mt5_download as d
    from backtester.tools import spread_table as s

    assert s.DEFAULT_NAMES is d.DEFAULT_NAMES
    assert s.DEFAULT_CLOCK is d.DEFAULT_CLOCK
    assert s.DEFAULT_SYMBOLS is d.DEFAULT_SYMBOLS


def test_mc_output_distinguishes_source_seed_runs():
    from backtester.tools.monte_carlo import default_out, parse_args

    base = ["NAS100", "--strategy", "gap_fade", "--start", "2020-01-01", "--end", "2021-01-01"]
    paths = [
        default_out(parse_args(base + extra))
        for extra in [[], ["--source", "mt5"], ["--seed", "123"], ["--runs", "123"]]
    ]
    assert len(set(paths)) == 4
    assert all("seed" in p.name and "runs" in p.name for p in paths)


def test_mc_saved_run_output_distinguishes_seed_runs():
    from backtester.tools.monte_carlo import default_out, parse_args

    assert default_out(parse_args(["--run", "example"])) != default_out(
        parse_args(["--run", "example", "--seed", "123"])
    )


def test_check_reads_by_year_and_preserves_cross_year_gap(tmp_path, monkeypatch):
    from backtester.data.cache import cache_path, write_atomic
    from backtester.data.histdata import parse_histdata_mt
    from backtester.tools import check

    dates = [date(2020, 12, 31), date(2021, 1, 1)]
    for day in dates:
        f = parse_histdata_mt(io.StringIO(f"{day:%Y.%m.%d},12:00,100,101,99,100,0\n"))
        write_atomic(f, cache_path(tmp_path, "GBPUSD", day))
    original = check._read_days
    calls = []

    def read(paths):
        assert len({d.year for d in paths}) <= 1
        calls.append(list(paths))
        return original(paths)

    monkeypatch.setattr(check, "_read_days", read)
    report = check.check_symbol(tmp_path, "GBPUSD")
    assert calls == [[dates[0]], [dates[1]]]
    assert report.traded_minutes == 2
    assert len(report.gaps) == 1
    assert report.gaps[0].minutes == 1439


def test_yearly_check_reports_wrong_year_rows_instead_of_crashing(tmp_path):
    from backtester.data.cache import cache_path, write_atomic
    from backtester.data.histdata import parse_histdata_mt
    from backtester.tools import check

    # Deliberately put 2021 bars in a 2020 file. A data audit must report the defect.
    frame = parse_histdata_mt(io.StringIO("2021.01.04,12:00,100,101,99,100,0\n"))
    write_atomic(frame, cache_path(tmp_path, "GBPUSD", date(2020, 1, 2)))
    write_atomic(frame.iloc[:0], cache_path(tmp_path, "GBPUSD", date(2021, 1, 4)))
    result = check.check_symbol(tmp_path, "GBPUSD")
    assert {f.name: f.count for f in result.integrity}["row in the wrong day file"] == 1


def test_doji_summaries_can_use_the_last_year_of_the_whole_report():
    import pandas as pd

    from backtester.tools.check import doji_by_period

    frame = pd.DataFrame(
        {
            "ts": pd.to_datetime(["2020-01-02", "2020-07-02"], utc=True),
            "open": [100.0, 100.0],
            "high": [101.0, 102.0],
            "low": [99.0, 98.0],
            "close": [100.0, 101.0],
        }
    )
    summary = doji_by_period(frame, 0.1, last_year=2021)
    assert summary.index.tolist() == ["2020"]
    assert summary.loc["2020", "candles"] == 2
    assert summary.loc["2020", "median_range"] == 3.0


def test_history_spots_without_a_midweek_trading_day_are_empty():
    from backtester.tools.check import DEFAULT_CONFIG, history_spot_times

    assert history_spot_times({date(2021, 1, 4)}, DEFAULT_CONFIG) == []


@pytest.mark.parametrize("offset", [0, 1])
def test_mt5_cli_rejects_today_future_before_loading_settings(offset, monkeypatch, capsys):
    from datetime import UTC, datetime, timedelta

    from backtester.live import trading_settings
    from backtester.tools.mt5_download import main

    def forbidden():
        pytest.fail("invalid dates must fail before settings/session")

    monkeypatch.setattr(trading_settings, "load_trading_settings", forbidden)
    with pytest.raises(SystemExit) as exc:
        main(["GBPUSD", "--end", str(datetime.now(UTC).date() + timedelta(days=offset))])
    assert exc.value.code == 2


def test_mt5_cli_unknown_broker_symbol_exits_nonzero_with_fake_terminal(monkeypatch, capsys):
    from contextlib import contextmanager
    from types import SimpleNamespace

    from fake_mt5 import FakeMt5

    from backtester.data.mt5_download import DEFAULT_CLOCK
    from backtester.live import connection, trading_settings
    from backtester.tools.mt5_download import main

    @contextmanager
    def fake_session(*args):
        fake = FakeMt5()
        fake.initialize()
        try:
            yield fake
        finally:
            fake.shutdown()

    monkeypatch.setattr(connection, "session", fake_session)
    monkeypatch.setattr(
        trading_settings,
        "load_trading_settings",
        lambda: SimpleNamespace(symbols={"NAS100": "INVALID"}, server_clock=DEFAULT_CLOCK),
    )
    with pytest.raises(SystemExit) as exc:
        main(["NAS100", "--start", "2018-01-01", "--end", "2018-01-02"])
    assert exc.value.code == 1
    assert "unknown symbol" in capsys.readouterr().err
