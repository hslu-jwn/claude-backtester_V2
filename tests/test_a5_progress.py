"""Delayed worker updates cannot reduce per-symbol progress (audit 13.21)."""

from test_runner import FULL, MON, SETTINGS, write_day

from backtester import runner
from backtester.data.sources import SymbolSources


def test_delayed_symbol_progress_never_goes_backwards(tmp_path, monkeypatch):
    for symbol in ("XAUUSD", "GOLD"):
        write_day(tmp_path, symbol, MON, FULL)
    sources = SymbolSources.single(tmp_path, ["XAUUSD", "GOLD"])

    def delayed(jobs, workers, report, cancel):
        runs = [runner._run_job(job) for job in jobs]
        report(jobs[0].symbol, jobs[0].base_candles)
        report(jobs[0].symbol, 1)
        report(jobs[1].symbol, 2)
        report(jobs[1].symbol, 1)
        report(jobs[1].symbol, jobs[1].base_candles)
        return runs

    monkeypatch.setattr(runner, "_run_parallel", delayed)
    progress = []
    runner.run_backtests(
        ["XAUUSD", "GOLD"],
        MON,
        MON,
        SETTINGS,
        sources,
        workers=2,
        progress=lambda n, total: progress.append(n),
    )
    assert progress == sorted(progress)
