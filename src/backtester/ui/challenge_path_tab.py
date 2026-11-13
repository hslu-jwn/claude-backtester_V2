"""Real-order challenge paths on the Results page.

Spec: risk-management.md > Challenge path simulator and FTMO rule sets.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from math import isfinite
from pathlib import Path

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, no_update

from backtester.paths import RESULTS_DIR
from backtester.risk.challenge_path import RULE_SETS, simulate
from backtester.ui.run_paths import run_folder

LABELS = {'ftmo_2step': 'FTMO 2-Step', 'ftmo_1step': 'FTMO 1-Step',
          'ftmo_instant': 'FTMO Instant'}
NOTE = ('News and market-break restrictions on funded / Instant accounts are not modelled; '
        'fees are not published.')


def _results():
    # Imported lazily to avoid a cycle with the Results page.
    from backtester.ui.pages import results

    return results


@lru_cache(maxsize=128)
def _simulate(folder: Path, rule: str, risk: float, summary_stamp: int, trades_stamp: int):
    results = _results()
    summary = results._read_json(folder / 'summary.json')
    return simulate(results.read_trades(folder), date.fromisoformat(summary['start']),
                    date.fromisoformat(summary['end']), [rule], risk / 100)


def _report(folder: Path, rule: str, risk: float):
    def stamp(path):
        return path.stat().st_mtime_ns if path.exists() else 0

    return _simulate(folder, rule, risk, stamp(folder / 'summary.json'),
                     stamp(folder / 'trades.csv'))


def figure(report: dict, rule: str, start: str) -> go.Figure:
    """Draw the recorded daily values for one attempt."""
    results = _results()
    attempt = next((a for a in report['rules'][rule]['attempts'] if a['start_date'] == start), None)
    fig = go.Figure()
    if not attempt:
        return fig
    path = attempt['path']
    dates = [report['dates'][row['day']] for row in path]
    for key, name, color, dash, width in (
        ('balance', 'Balance', results.ACCENT, 'solid', 2),
        ('worst', 'Worst equity', results.MUTED, 'solid', 1),
        ('daily_floor', 'Daily loss floor', results.DOWN, 'dash', 1),
        ('max_floor', 'Max loss floor', results.DOWN, 'solid', 1),
    ):
        fig.add_trace(go.Scatter(x=dates, y=[p[key] for p in path], name=name, mode='lines',
                                 opacity=0.45 if key == 'worst' else 1,
                                 line={'color': color, 'dash': dash, 'width': width,
                                       'shape': 'hv' if key.endswith('floor') else 'linear'}))
    for index, target in enumerate(RULE_SETS[rule].targets):
        fig.add_trace(go.Scatter(x=dates, y=[100_000 * (1 + target)] * len(dates),
                                 name=f'Phase {index + 1} target', mode='lines',
                                 line={'color': results.UP, 'dash': 'dash', 'width': 1}))
    labels = {'pass': ('Passed', results.UP), 'daily': ('Daily loss', results.DOWN),
              'max': ('Max loss', results.DOWN), 'open': ('Open', results.MUTED),
              'survived': ('Survived', results.MUTED)}
    by_day = {row['day']: row for row in path}
    for index, phase in enumerate(attempt['phase_results'][:-1]):  # passed phases before the last
        if phase['status'] == 'pass' and phase.get('day') in by_day:
            fig.add_trace(go.Scatter(x=[report['dates'][phase['day']]],
                                     y=[by_day[phase['day']]['balance']],
                                     name=f'Phase {index + 1} passed', mode='markers+text',
                                     text=[f'Phase {index + 1} passed'], textposition='top center',
                                     marker={'color': results.UP, 'size': 9, 'symbol': 'diamond'}))
    label, color = labels[attempt['status']]
    if path:
        value = path[-1]['worst'] if attempt['status'] in ('daily', 'max') else path[-1]['balance']
        fig.add_trace(go.Scatter(x=[dates[-1]], y=[value], name=label, mode='markers+text',
                                 text=[label], textposition='top center',
                                 marker={'color': color, 'size': 10}))
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', margin={'l': 60, 'r': 20, 't': 25, 'b': 45},
                      legend={'orientation': 'h'}, xaxis_title='Date', yaxis_title='Account value')
    return fig


def summary_table(report: dict, rule: str):
    summary = report['rules'][rule]['summary']
    fields = [('Attempts', 'attempts'), ('Pass %', 'pass_pct'), ('Daily %', 'daily_pct'),
              ('Max %', 'max_pct'), ('Open', 'open'), ('Survived', 'survived'),
              ('Median weekdays to funding', 'median_weekdays_to_funding'),
              ('p90 weekdays to funding', 'p90_weekdays_to_funding')]
    def display(value):
        return '—' if value is None else f'{round(value, 1):g}'
    return html.Table([html.Thead(html.Tr([html.Th(label) for label, _ in fields])),
                       html.Tbody(html.Tr([html.Td(display(summary[key])) for _, key in fields]))],
                      className='rs-table')


def layout(folder: Path | None):
    if folder is None or not _results().read_trades(folder):
        return html.Div('No trades in this run', className='pf-note')
    report = _report(folder, 'ftmo_2step', 1.0)
    attempts = report['rules']['ftmo_2step']['attempts']
    starts = [a['start_date'] for a in attempts]
    start = starts[0] if starts else None
    return html.Div([
        html.Div([
            html.Label(['Rule set', dcc.Dropdown(id='cp-rules',
                options=[{'label': LABELS[k], 'value': k} for k in RULE_SETS],
                value='ftmo_2step', clearable=False, searchable=False, className='pf-firm')]),
            html.Label(['Risk %', dcc.Input(id='cp-risk', type='number', value=1.0,
                                           min=0.1, max=5, step=0.1)]),
            html.Label(['Start date', dcc.Dropdown(id='cp-start',
                options=[{'label': s, 'value': s} for s in starts], value=start,
                clearable=False, searchable=False, className='pf-firm')]),
        ], className='pf-inner'),
        dcc.Graph(id='cp-figure', figure=figure(report, 'ftmo_2step', start)),
        html.Div(summary_table(report, 'ftmo_2step'), id='cp-summary', className='pf-table-scroll'),
        html.Div(NOTE, className='pf-note'),
    ])


def update(run_id, rule, risk, start, results_dir=RESULTS_DIR):
    if (rule not in RULE_SETS or isinstance(risk, bool) or not isinstance(risk, (int, float))
            or not isfinite(risk) or not 0.1 <= risk <= 5):
        return no_update, no_update
    folder = run_folder(run_id, results_dir)
    if folder is None or not _results().read_trades(folder):
        return no_update, no_update
    report = _report(folder, rule, float(risk))
    return figure(report, rule, start), summary_table(report, rule)


def register_callbacks(app: Dash, results_dir: Path = RESULTS_DIR) -> None:
    @app.callback(Output('cp-figure', 'figure'), Output('cp-summary', 'children'),
                  Input('cp-rules', 'value'), Input('cp-risk', 'value'),
                  Input('cp-start', 'value'), State('rs-run-id', 'data'))
    def _update(rule, risk, start, run_id):
        return update(run_id, rule, risk, start, results_dir)
