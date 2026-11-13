import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

from dash import no_update

from backtester.risk.challenge_path import simulate
from backtester.ui import app as app_module
from backtester.ui import challenge_path_tab as tab
from backtester.ui.pages import results


def trades(values):
    start = date(2020, 1, 1)
    days = [start + timedelta(days=i) for i in range(30)]
    days = [d for d in days if d.weekday() < 5]
    return [SimpleNamespace(entry_time=datetime(d.year, d.month, d.day, 10, tzinfo=UTC),
                            exit_time=datetime(d.year, d.month, d.day, 11, tzinfo=UTC),
                            r_net=r, risk_weight=1.0)
            for d, r in zip(days, values)]


def report(values, rule='ftmo_2step', risk=.01):
    return simulate(trades(values), date(2020, 1, 1), date(2020, 1, 31), [rule], risk)


def test_layout_controls_and_empty_run(tmp_path, monkeypatch):
    folder = tmp_path / 'run'
    folder.mkdir()
    (folder / 'summary.json').write_text(json.dumps({'start': '2020-01-01', 'end': '2020-02-29'}))
    monkeypatch.setattr(results, 'read_trades', lambda _: trades([2] * 9))
    component = tab.layout(folder)
    text = json.dumps(component, default=lambda o: o.to_plotly_json())
    for expected in ('cp-rules', 'cp-risk', 'cp-start', 'ftmo_2step', '2020-01-01', '2020-02-03'):
        assert expected in text
    assert '"min": 0.1' in text and '"max": 5' in text and '"step": 0.1' in text
    assert ('challenge', 'Challenge path') in results.TABS
    monkeypatch.setattr(results, 'read_trades', lambda _: [])
    assert 'No trades in this run' in str(tab.layout(folder))


def test_figures_show_pass_and_trailing_breach():
    rep = report([2] * 9)
    fig = tab.figure(rep, 'ftmo_2step', '2020-01-01')
    names = [trace.name for trace in fig.data]
    assert all(name in names for name in ('Balance', 'Daily loss floor', 'Max loss floor',
                                           'Phase 1 target', 'Phase 2 target', 'Passed'))
    rep = report([2, 2, -3], 'ftmo_1step')
    fig = tab.figure(rep, 'ftmo_1step', '2020-01-01')
    assert fig.data[-1].name in ('Daily loss', 'Max loss')
    floor = next(trace.y for trace in fig.data if trace.name == 'Max loss floor')
    assert list(floor) == sorted(floor)


def test_risk_changes_path_and_invalid_risk(tmp_path, monkeypatch):
    folder = tmp_path / 'run'
    folder.mkdir()
    (folder / 'summary.json').write_text(json.dumps({'start': '2020-01-01', 'end': '2020-01-31'}))
    monkeypatch.setattr(results, 'read_trades', lambda _: trades([2] * 9))
    low = tab.update('run', 'ftmo_2step', 1, '2020-01-01', tmp_path)
    high = tab.update('run', 'ftmo_2step', 2, '2020-01-01', tmp_path)
    assert high[0].data[0].y[0] > low[0].data[0].y[0]
    for risk in (0, None, '', float('nan')):
        assert tab.update('run', 'ftmo_2step', risk, '2020-01-01', tmp_path) == (no_update, no_update)


def test_app_callbacks_register():
    app = app_module.create_app()
    assert sum('cp-figure.figure' in key for key in app.callback_map) == 1


def test_phase_one_pass_is_marked_where_the_verification_restarts():
    """Opus browser check: without a marker the reset to 100,000 after Phase 1 looks like a crash."""
    rep = report([2] * 9)
    attempt = rep['rules']['ftmo_2step']['attempts'][0]
    fig = tab.figure(rep, 'ftmo_2step', '2020-01-01')
    marker = next(trace for trace in fig.data if trace.name == 'Phase 1 passed')
    assert list(marker.x) == [rep['dates'][attempt['phase_results'][0]['day']]]
    assert not any(trace.name == 'Phase 1 passed' for trace in tab.figure(
        report([2, 2, -3], 'ftmo_1step'), 'ftmo_1step', '2020-01-01').data)


def test_summary_numbers_have_one_decimal():
    keys = ('attempts', 'pass_pct', 'daily_pct', 'max_pct', 'open', 'survived',
            'median_weekdays_to_funding', 'p90_weekdays_to_funding')
    summary = dict(zip(keys, (80, 36.2319, 0.0, 63.7681, 11, 0, 118.0, 208.8), strict=True))
    text = str(tab.summary_table({'rules': {'ftmo_2step': {'summary': summary}}}, 'ftmo_2step'))
    for shown in ('36.2', '63.8', '208.8', '118', '80'):
        assert f"'{shown}'" in text
    assert '36.2319' not in text
