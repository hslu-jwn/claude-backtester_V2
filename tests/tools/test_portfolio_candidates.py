import json
from datetime import date

import pytest

from backtester.analytics.portfolio_search import Member, search
from backtester.tools import portfolio_candidates as pc


def saved_member(root):
    folder = root / "research" / "grid"
    run = folder / "variants" / "v1"
    run.mkdir(parents=True)
    info = {
        "strategy": "gap_fade",
        "symbols": ["US500"],
        "periods": {"development": {"start": "2020-01-01", "end": "2020-01-02"}},
        "chosen": {"id": "v1", "overrides": {}},
    }
    (folder / "research.json").write_text(json.dumps(info))
    (folder / "variants.csv").write_text("variant_id,flags\nv1,short\n")
    (run / "summary.json").write_text(json.dumps({"start": "2020-01-01", "end": "2020-01-02"}))
    (run / "settings.json").write_text("{}")
    (run / "daily.csv").write_text("date,net_r_exit_booked\n2020-01-01,1\n2020-01-02,-1\n")
    (run / "trades.csv").write_text("id,symbol\n")
    return run


def test_load_chosen_only_and_refuse_test_daily(tmp_path):
    run = saved_member(tmp_path)
    pool, errors = pc.load_members(tmp_path)
    assert not errors
    assert len(pool) == 1
    assert pool[0].id == "grid~v1"
    assert pool[0].values == (1, -1)
    (run / "daily.csv").write_text("date,net_r_exit_booked\n2021-09-14,99\n")
    pool, errors = pc.load_members(tmp_path)
    assert pool == [] and errors


def test_top_ten_queue_has_no_test_or_backtest(tmp_path):
    from backtester.jobs.queue import Queue

    pool = [Member(str(i), (date(2020, 1, 1),), (i,)) for i in range(5)]
    rows = search(pool)
    queue = Queue(tmp_path / "queue")
    ids = pc.queue_top(rows, pool, "net_r", queue, tmp_path)
    assert len(ids) == 10
    assert len(queue.jobs()) == 10
    for job in queue.jobs():
        assert job.argv[0:2] == ["backtester.tools.portfolio", "--existing"]
        assert "--test" not in job.argv and "--retest" not in job.argv
    assert pc.queue_top(rows, pool, "net_r", queue, tmp_path) == []


def test_test_reservation_refuses_same_set_and_failed_attempt(tmp_path):
    pc.reserve_test(["b", "a"], tmp_path)
    with pytest.raises(ValueError, match="already"):
        pc.reserve_test(["a", "b"], tmp_path)


def test_cli_can_select_set_outside_monte_carlo_top_ten(tmp_path, monkeypatch):
    from backtester.analytics.portfolio_search import set_id

    parts = [Member(i, (date(2020, 1, 1),), (1,), folder=i) for i in ("a", "b")]
    sid = set_id(["a", "b"])
    base = tmp_path / "portfolio"
    base.mkdir()
    (base / f"search_{pc.search_hash(parts)}.json").write_text(
        json.dumps({"pool": ["a", "b"], "sets": [{"id": sid, "members": ["a", "b"]}]})
    )
    monkeypatch.setattr(pc, "load_members", lambda *a: (parts, []))
    path = pc.resolve_set(sid, tmp_path)
    assert json.loads(path.read_text())["id"] == sid


def test_parser_test_cli_only_needs_set_id():
    from backtester.tools.portfolio import parse_args

    args = parse_args(["--test", "abc"])
    assert args.test == "abc"


def test_cached_search_content_changes(tmp_path):
    a = Member("a", (date(2020, 1, 1),), (1,))
    b = Member("b", a.days, (2,))
    assert pc.pool_hash([a, b]) == pc.pool_hash([b, a])
    assert pc.pool_hash([a, b]) != pc.pool_hash([a, Member("b", a.days, (3,))])


def test_search_identity_tracks_effective_development_candle_content(tmp_path):
    import pandas as pd

    from backtester.data.cache import cache_path, write_atomic
    from backtester.data.mt5_download import cache_frame
    from backtester.data.sources import SymbolSources

    main, preferred = tmp_path / "main", tmp_path / "preferred"
    sources = SymbolSources({"US500": main}, preferred_dirs={"US500": preferred})
    day = date(2020, 1, 6)
    pool = [Member(i, (day,), (1,), symbols=("US500",)) for i in ("a", "b")]
    frame = cache_frame(
        pd.DataFrame(
            {
                "ts": pd.to_datetime(["2020-01-06T10:00Z"]),
                "open": [100.0],
                "high": [102.0],
                "low": [99.0],
                "close": [101.0],
                "volume": [1.0],
                "spread": [0.1],
            }
        )
    )
    path = cache_path(main, "US500", day)
    write_atomic(frame, path)
    before = pc.search_hash(pool, sources)
    frame["bid_close"] = 100.5
    write_atomic(frame, path)
    assert pc.search_hash(pool, sources) != before
    write_atomic(frame, cache_path(preferred, "US500", day))
    before = pc.search_hash(pool, sources)
    frame["bid_close"] = 100.25
    write_atomic(frame, path)  # shadowed input must not invalidate attribution
    assert pc.search_hash(pool, sources) == before
    write_atomic(frame, cache_path(preferred, "US500", date(2021, 9, 14)))
    assert pc.search_hash(pool, sources) == before


def test_development_summary_excludes_holdout_statistics_but_preserves_trial_count(
    tmp_path,
    monkeypatch,
):
    from dataclasses import replace

    from backtester.analytics import deflated_sharpe as ds
    from backtester.analytics.trial_log import append, count_only, make_record
    from backtester.runner import RunSettings
    from backtester.settings import to_dict
    from backtester.tools import monte_carlo as mc
    from backtester.tools import portfolio

    days = (date(2020, 1, 6), date(2020, 1, 7))
    parts = [Member(i, days, (0, 0), settings=to_dict(RunSettings()), folder=i) for i in ("a", "b")]
    path = tmp_path / "trials.jsonl"
    dev = replace(
        make_record(
            "family", "gap_fade", {}, ["US500"], *days, "research", [], series="a/daily.csv"
        ),
        day_sharpe=0.1,
    )
    for record in (
        dev,
        replace(dev, start="2021-09-14", end="2022-01-01", source="research-test", day_sharpe=99),
        replace(dev, source="research-test", day_sharpe=88),
        replace(dev, start="broken", day_sharpe=77),
        count_only("family", "gap_fade", 5),
    ):
        append(record, path)
    monkeypatch.setattr(pc, "read_trades", lambda *a: [])
    monkeypatch.setattr(portfolio, "combined_fills", lambda *a, **k: None)
    monkeypatch.setattr(portfolio, "portfolio_block", lambda *a: {})
    monkeypatch.setattr(mc, "build_summary", lambda *a, **k: {})
    seen = []
    monkeypatch.setattr(
        ds, "deflated_sharpe", lambda stats, n, sharpes, cfg: seen.append((n, sharpes))
    )
    pc.existing_summary(parts, tmp_path, mc.ToolConfig(runs=2))
    assert seen == [(9, [0.1])]


def test_old_diagnostics_are_requeued_after_development_statistics_fix(tmp_path):
    import hashlib
    from dataclasses import asdict

    from backtester.analytics.portfolio_search import set_id
    from backtester.jobs.queue import Queue

    parts = [Member(i, (date(2020, 1, 6),), (1,), folder=i) for i in ("a", "b")]
    # Version 1 summaries may contain holdout Sharpes and must not be reused.
    old_hash = hashlib.sha256(
        json.dumps([1, [asdict(m) for m in parts]], sort_keys=True, default=str).encode()
    ).hexdigest()[:20]
    folder = tmp_path / "portfolio" / set_id(m.id for m in parts)
    folder.mkdir(parents=True)
    (folder / "summary.json").write_text(json.dumps({"fingerprint": old_hash}))
    jobs = pc.queue_top(search(parts), parts, "net_r", Queue(tmp_path / "queue"), tmp_path)
    assert len(jobs) == 1


def test_artifact_changes_invalidate_fingerprint(tmp_path):
    run = saved_member(tmp_path)
    before, _ = pc.load_members(tmp_path)
    (run / "trades.csv").write_text("id,symbol,extra\n")
    after, _ = pc.load_members(tmp_path)
    assert pc.pool_hash(before) != pc.pool_hash(after)


@pytest.mark.parametrize(
    "days,start",
    [
        ((date(2020, 1, 3), date(2020, 1, 6)), date(2020, 1, 3)),
        ((date(2020, 1, 6),), date(2020, 1, 4)),
    ],
)
def test_worker_reuses_lists_and_preserves_weekend_booking(tmp_path, monkeypatch, days, start):
    from datetime import UTC, datetime
    from types import SimpleNamespace

    from backtester.runner import RunSettings
    from backtester.settings import to_dict
    from backtester.tools import monte_carlo as mc
    from backtester.tools import portfolio

    settings = to_dict(RunSettings())
    settings["run"] = {"start": start.isoformat(), "end": days[-1].isoformat()}
    values = (0, 2) if len(days) == 2 else (2,)
    parts = [Member(i, days, values, settings=settings, folder=i) for i in ("a", "b")]
    at = datetime(2020, 1, 4, 12, tzinfo=UTC)  # Saturday -> Monday, never dropped
    trade = SimpleNamespace(entry_time=at, exit_time=at, r_net=2, r_gross=2, symbol="X")
    monkeypatch.setattr(pc, "read_trades", lambda _: [trade])
    monkeypatch.setattr(
        portfolio, "run_backtests", lambda *a, **k: pytest.fail("backtest forbidden")
    )
    monkeypatch.setattr(portfolio, "combined_fills", lambda *a, **k: None)
    monkeypatch.setattr(portfolio, "portfolio_block", lambda *a: {})
    received = []

    def summary(trades, *args, **kwargs):
        received.extend(trades)
        return {"meta": args[1]}

    monkeypatch.setattr(mc, "build_summary", summary)
    pc.existing_summary(parts, tmp_path, mc.ToolConfig(runs=2))
    assert sum(t.r_net for t in received) == 2
    assert [t.risk_weight for t in received] == [0.5, 0.5]


def test_one_time_test_fixed_mt5_and_trial_log(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from backtester import runner
    from backtester.analytics.portfolio_search import set_id
    from backtester.analytics.trial_log import read_all
    from backtester.data.sources import SymbolSources
    from backtester.runner import RunSettings
    from backtester.settings import to_dict
    from backtester.tools import monte_carlo as mc

    parts = [
        Member(i, (date(2020, 1, 1),), (1,), symbols=("US500",), settings=to_dict(RunSettings()))
        for i in ("b", "a")
    ]
    sid = set_id(m.id for m in parts)
    monkeypatch.setattr(pc, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(pc, "resolve_set", lambda *a: tmp_path / "members.json")
    monkeypatch.setattr(
        pc, "manifest_members", lambda *a: ({"members": [m.id for m in parts]}, parts)
    )
    monkeypatch.setattr(SymbolSources, "cached_days", lambda *a: [date(2021, 9, 14)])
    calls = []

    def run(symbols, start, end, settings, *, sources, workers):
        calls.append((start, end, sources, workers))
        return SimpleNamespace(trades=[])

    monkeypatch.setattr(runner, "run_backtests", run)
    monkeypatch.setattr(mc, "build_summary", lambda *a, **k: {})
    monkeypatch.setattr(mc, "render_report", lambda s: "report")
    pc.run_test(sid, tmp_path, mc.ToolConfig())
    assert len(calls) == 2
    assert all(c[0] == date(2021, 9, 14) and c[3] == 1 for c in calls)
    assert all(not c[2].preferred_dirs for c in calls)
    records = read_all(tmp_path / "trials.jsonl")
    assert len(records) == 1 and records[0].settings == {"member_ids": ["a", "b"]}
    with pytest.raises(ValueError, match="already"):
        pc.run_test(sid, tmp_path, mc.ToolConfig())
    assert len(calls) == 2


def test_missing_daily_rebuilt_by_shared_writer_and_reused(tmp_path, monkeypatch):
    import csv
    from datetime import UTC, datetime
    from types import SimpleNamespace

    from backtester.tools import research_series

    run = saved_member(tmp_path)
    (run / "daily.csv").unlink()
    trade = SimpleNamespace(
        symbol="US500",
        direction="long",
        r_net=2,
        entry_time=datetime(2020, 1, 2, 10, tzinfo=UTC),
        exit_time=datetime(2020, 1, 2, 12, tzinfo=UTC),
    )
    monkeypatch.setattr(pc, "read_trades", lambda _: [trade])
    calls = []
    original = research_series.ensure

    def ensure(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(research_series, "ensure", ensure)
    pool, errors = pc.load_members(tmp_path)
    assert errors == [] and len(pool) == 1
    assert pool[0].values == (0, 2)
    rows = list(csv.DictReader((run / "daily.csv").open()))
    assert [r["date"] for r in rows] == ["2020-01-01", "2020-01-02"]
    assert [float(r["net_r_mtm"]) for r in rows] == [0, 2]
    assert float(rows[1]["position"]) == pytest.approx(2 / 24)
    assert calls[0][0][1:3] == (date(2020, 1, 1), date(2020, 1, 2))
    assert calls[0][1]["trades"] == [trade]
    assert pc.load_members(tmp_path) == (pool, [])
    assert len(calls) == 1


@pytest.mark.parametrize("missing_daily", [False, True])
def test_missing_trades_gives_pipeline_instruction(tmp_path, missing_daily):
    run = saved_member(tmp_path)
    if missing_daily:
        (run / "daily.csv").unlink()
    (run / "trades.csv").unlink()
    pool, errors = pc.load_members(tmp_path)
    assert pool == []
    assert errors == ["grid: Run this grid's pipeline first: Research › Queue a grid"]
    assert (run / "daily.csv").exists() is not missing_daily


@pytest.mark.parametrize("invalid", ["period", "trade"])
def test_missing_daily_retains_development_guards(tmp_path, monkeypatch, invalid):
    from datetime import UTC, datetime
    from types import SimpleNamespace

    from backtester.tools import research_series

    run = saved_member(tmp_path)
    (run / "daily.csv").unlink()
    if invalid == "period":
        (run / "summary.json").write_text('{"start":"2020-01-01","end":"2021-09-14"}')
    at = datetime(2021, 9, 14, 12, tzinfo=UTC)
    monkeypatch.setattr(
        pc,
        "read_trades",
        lambda _: [
            SimpleNamespace(
                entry_time=at,
                exit_time=at,
                r_net=1,
            )
        ],
    )
    monkeypatch.setattr(research_series, "ensure", lambda *a, **k: pytest.fail("unsafe write"))
    pool, errors = pc.load_members(tmp_path)
    assert pool == [] and errors
    assert not (run / "daily.csv").exists()


def test_search_cache_tracks_classifier_and_d1_data(tmp_path, monkeypatch):
    from dataclasses import replace
    from types import SimpleNamespace

    from backtester.analytics import regime

    days = [date(2019, 12, 30)]

    # The content fingerprint now needs the effective file for each synthetic day.
    def path(symbol, day):
        return tmp_path / f"{symbol}-{day}.parquet"

    for day in (date(2019, 12, 30), date(2019, 12, 31)):
        path("X", day).write_bytes(b"synthetic day")
    sources = SimpleNamespace(
        cached_days=lambda s: days, adapter=lambda s: SimpleNamespace(_path=path)
    )
    pool = [Member(i, (date(2020, 1, 2),), (1,), symbols=("X",)) for i in ("a", "b")]
    calls = []

    def regimes(*args):
        calls.append(True)
        return {}

    monkeypatch.setattr(pc, "daily_regimes", regimes)
    classifier = tmp_path / "classifier.py"
    classifier.write_text("version 1")
    monkeypatch.setattr(regime, "__file__", str(classifier))
    pc.cached_search(pool, tmp_path, sources)
    pc.cached_search(pool[::-1], tmp_path, sources)
    assert len(calls) == 1
    config = regime.RegimeConfig()
    monkeypatch.setattr(regime, "RegimeConfig", lambda: replace(config, er_trend=0.4))
    pc.cached_search(pool, tmp_path, sources)
    assert len(calls) == 2
    days.append(date(2019, 12, 31))
    pc.cached_search(pool, tmp_path, sources)
    assert len(calls) == 3
    classifier.write_text("version 2")
    pc.cached_search(pool, tmp_path, sources)
    assert len(calls) == 4
    # Holdout candles cannot alter a development attribution or enter its cache stamp.
    days.append(date(2021, 9, 14))
    pc.cached_search(pool, tmp_path, sources)
    assert len(calls) == 4


@pytest.mark.parametrize("failure", [False, True])
def test_custom_results_cannot_repeat_holdout(tmp_path, monkeypatch, failure):
    from types import SimpleNamespace

    from backtester import runner
    from backtester.analytics.portfolio_search import set_id
    from backtester.analytics.trial_log import read_all
    from backtester.data.sources import SymbolSources
    from backtester.runner import RunSettings
    from backtester.settings import to_dict
    from backtester.tools import monte_carlo as mc

    default = tmp_path / "default"
    monkeypatch.setattr(pc, "RESULTS_DIR", default)
    parts = [
        Member(i, (date(2020, 1, 1),), (1,), symbols=("US500",), settings=to_dict(RunSettings()))
        for i in ("a", "b")
    ]
    sid = set_id(m.id for m in parts)
    monkeypatch.setattr(pc, "resolve_set", lambda *a: tmp_path / "members.json")
    monkeypatch.setattr(
        pc, "manifest_members", lambda *a: ({"members": [m.id for m in parts]}, parts)
    )
    monkeypatch.setattr(SymbolSources, "cached_days", lambda *a: [date(2021, 9, 14)])
    calls = []

    def run(*args, **kwargs):
        calls.append(True)
        if failure:
            raise RuntimeError("interrupted")
        return SimpleNamespace(trades=[])

    monkeypatch.setattr(runner, "run_backtests", run)
    monkeypatch.setattr(mc, "build_summary", lambda *a, **k: {})
    monkeypatch.setattr(mc, "render_report", lambda s: "report")
    if failure:
        with pytest.raises(RuntimeError, match="interrupted"):
            pc.run_test(sid, tmp_path / "first", mc.ToolConfig())
    else:
        pc.run_test(sid, tmp_path / "first", mc.ToolConfig())
    assert len(read_all(default / "trials.jsonl")) == 1
    assert (default / "portfolio" / "tests" / sid / "attempt.json").exists()
    count = len(calls)
    # Reservation alone must survive loss of the log, and vice versa.
    if failure:
        (default / "trials.jsonl").unlink()
    else:
        (default / "portfolio" / "tests" / sid / "attempt.json").unlink()
    with pytest.raises(ValueError, match="already"):
        pc.run_test(sid, tmp_path / "second", mc.ToolConfig())
    assert len(calls) == count
    assert not (tmp_path / "first" / "trials.jsonl").exists()


def test_combined_fills_uses_each_members_saved_costs(monkeypatch):
    from backtester.analytics.random_fills import RandomFillsResult
    from backtester.tools import portfolio

    seen = []

    def fills(trades, cfg, costs):
        seen.append((cfg.seed, costs))
        return RandomFillsResult(2, (1, 2), 1, 1.5, 2)

    monkeypatch.setattr(portfolio, "random_fills", fills)
    result = portfolio.combined_fills(
        [[], []], [0.5, 0.5], {}, 2, 42, component_costs=[{"X": "first"}, {"X": "second"}]
    )
    assert seen == [(42, {"X": "first"}), (43, {"X": "second"})]
    assert result.run_net_r == (1, 2)


def test_daily_regime_ignores_unfinished_day():
    from datetime import UTC, datetime, timedelta
    from types import SimpleNamespace

    from backtester.core.models import Candle

    days = (date(2020, 1, 25),)
    pool = [Member("a", days, (1,), symbols=("X",))]
    candles = [
        Candle(
            datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=i), 100 + i, 101 + i, 99 + i, 100 + i
        )
        for i in range(24)
    ]
    fetched = []

    def fetch(symbol, timeframe, start, end):
        fetched.append(end)
        return [c for c in candles if start <= c.ts < end]

    sources = SimpleNamespace(
        cached_days=lambda s: [c.ts.date() for c in candles],
        adapter=lambda s: SimpleNamespace(fetch=fetch),
    )
    before = pc.daily_regimes(pool, sources)
    # Jan 24 D1 is unfinished at Prague midnight starting Jan 25: its huge crash is unknowable.
    candles[-1] = Candle(candles[-1].ts, 123, 123, 1, 1)
    assert pc.daily_regimes(pool, sources) == before
    assert before["X"][days[0]].startswith("trend_up")
    assert all(d.date() < date(2021, 9, 14) for d in fetched)


def test_existing_summary_real_report_with_small_simulation(tmp_path, monkeypatch):
    from datetime import UTC, datetime, timedelta
    from types import SimpleNamespace

    from backtester.analytics.daily import weekdays
    from backtester.risk.drawdown_bounds import DrawdownBoundsConfig
    from backtester.runner import RunSettings
    from backtester.settings import to_dict
    from backtester.tools import monte_carlo as mc
    from backtester.tools import portfolio

    days = tuple(weekdays(date(2020, 1, 1), date(2020, 2, 28)))
    trades = []
    for i, day in enumerate(days):
        at = datetime.combine(day, datetime.min.time(), UTC) + timedelta(hours=12)
        r = 1 if i % 3 else -1
        trades.append(
            SimpleNamespace(
                symbol="US500",
                entry_time=at,
                exit_time=at + timedelta(hours=1),
                entry=100,
                initial_stop=99,
                exit_reason="signal",
                r_net=r,
                r_gross=r,
                spread_r=0,
                commission_r=0,
                swap_r=0,
                funding_r=0,
            )
        )
    parts = [
        Member(
            i,
            days,
            tuple(t.r_net for t in trades),
            folder=i,
            strategy="session_zone_sweep",
            symbols=("US500",),
            settings=to_dict(RunSettings()),
        )
        for i in ("a", "b")
    ]
    monkeypatch.setattr(pc, "read_trades", lambda _: trades)
    monkeypatch.setattr(portfolio, "run_backtests", lambda *a, **k: pytest.fail("no backtest"))
    config = mc.ToolConfig(
        runs=3, paths=0, bounds=DrawdownBoundsConfig(outer=2, inner=3, horizon_days=5)
    )
    summary = pc.existing_summary(parts, tmp_path, config, log=lambda _: None)
    assert summary["robustness"]["net_r"] == sum(t.r_net for t in trades)
    assert "Portfolio" in portfolio.render_report(summary)
    assert "class='banner'" not in portfolio.render_report(summary, include_verdict=False)
    assert summary["meta"]["source"] == "development"
