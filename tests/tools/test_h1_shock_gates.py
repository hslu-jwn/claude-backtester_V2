from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

from backtester.tools import h1_shock_gates as g


def trade(day, value=1, symbol='XAUUSD', direction='long'):
    t = datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=day)
    return SimpleNamespace(entry_time=t, exit_time=t + timedelta(hours=1), symbol=symbol,
                           direction=direction, r_net=value, r_gross=value, spread_r=0,
                           commission_r=0, swap_r=0, funding_r=0, conversion_r=0)


def test_cluster_and_confidence():
    ts = [trade(0), trade(0), trade(1)]
    report = g.clustered(ts, [1, 1, 1])
    assert report['events'] == 3 and report['clusters'] == 2
    assert report['lower_2_5'] > 0 and report['upper_97_5'] > 0
    assert g.clustered(ts, [-1, -1, -1])['upper_97_5'] < 0
    assert g.clustered([], []) is None


def test_adjacent_and_common_intersection():
    a, b, c = trade(0), trade(1), trade(2)
    cells = {1: [a, b, c], 2: [a, b], 3: [a, c]}
    assert g.common_keys(cells) == {(a.symbol, a.entry_time)}
    assert g.same_sign(1, [0.2, 0.3, 0.1])
    assert not g.same_sign(1, [0.2, -0.3, 0.1])
    assert not g.same_sign(0, [1, 1, 1])


def test_cell_gates_pass_and_fail():
    start, end = date(2020, 1, 1), date(2020, 12, 31)
    ts = [trade(i * 3, symbol=s) for i in range(100) for s in ('XAUUSD', 'GBPUSD', 'GBPJPY')]
    row = g.cell_report(ts, [1.0] * len(ts), start, end, [])
    assert all(row['gates'].values())
    bad = g.cell_report([trade(0, -1)], [-1], start, end, [trade(0)])
    assert not bad['gates']['positive_normal_and_doubled']
    assert not bad['gates']['minimum_events']
    assert not bad['gates']['data_integrity']


def test_end_to_end_skipped_integrity(tmp_path, monkeypatch):
    import csv
    import json

    import numpy as np

    from backtester.analytics.entry_screen import M1Data

    rows = []
    for mode in ('CONTINUATION', 'REVERSAL'):
        for k in (2, 3, 4):
            for h in (1, 2, 3):
                vid = f'{mode}-{k}-{h}'
                rows.append([vid, '', mode, k, h])
                path = tmp_path / 'variants' / vid
                path.mkdir(parents=True)
                (path / 'settings.json').write_text(json.dumps({'run': {'start': '2020-01-01',
                    'end': '2020-12-31', 'symbols': ['XAUUSD'], 'cache_dirs': {}}}))
                (path / 'sessions.json').write_text(json.dumps({'XAUUSD': [{'signal_time':
                    '2020-01-01T00:00:00+00:00', 'event_return': 0.1,
                    'three_hour_eligible': True, 'defects': []}]}))
                with (path / 'trades.csv').open('w', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(['id', 'symbol', 'direction', 'entry_time', 'entry_candle',
                                'entry', 'initial_stop', 'exit_time', 'exit_price', 'exit_reason',
                                'r_gross', 'r_net', 'spread_r', 'commission_r'])
                    w.writerow([1, 'XAUUSD', 'long', '2020-01-01T00:00:00+00:00',
                        '2020-01-01T00:00:00+00:00', 100, 90,
                        f'2020-01-01T0{h}:00:00+00:00', 101, 'time', 1, 1, 0, 0])
    with (tmp_path / 'variants.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['variant_id', 'family', 'set.response_mode', 'set.event_z_threshold',
                    'set.holding_hours'])
        w.writerows(rows)
    base = int(datetime(2020, 1, 1, tzinfo=UTC).timestamp())
    times = np.array([base - 60, base + 3540, base + 7140, base + 10740])
    prices = np.array([100., 101., 102., 103.])
    monkeypatch.setattr(g, 'load_m1', lambda *args: M1Data(times, prices, prices, prices, prices))
    assert g.main([str(tmp_path), '--skip-integrity']) == 0
    out = json.loads((tmp_path / 'gates.json').read_text())
    assert len(out['cells']) == 18 and out['skipped_integrity']
    assert not out['advances'] and out['primary']['common_events']['count'] == 1



def test_single_day_is_insufficient_for_uncertainty():
    ts = [trade(0), trade(0)]
    assert g.clustered(ts, [1, 1]) is None


def test_primary_gates_and_adjacent_failures(monkeypatch):
    start, end = date(2020, 1, 1), date(2020, 12, 31)
    monkeypatch.setattr(g, '_q', lambda t, session, h, data: session['q'])
    monkeypatch.setattr(g, 'RESAMPLES', 100)
    trades = [trade(i * 4, symbol=s) for i in range(80)
              for s in ('XAUUSD', 'GBPUSD', 'GBPJPY')]
    cells = {(m, float(k), h): list(trades) for m in g.MODES for k in (2, 3, 4)
             for h in (1, 2, 3)}
    sessions = {cell: {g.key(t): {'q': 0.1, 'three_hour_eligible': True} for t in ts}
                for cell, ts in cells.items()}
    out = g.evaluate(cells, sessions, {}, start, end, None)
    assert out['primary']['mapped_mode'] == 'CONTINUATION'
    assert out['advances'] and all(out['primary']['gates'].values())
    for record in sessions['CONTINUATION', 4., 1].values():
        record['q'] = -0.1
    out = g.evaluate(cells, sessions, {}, start, end, None)
    assert not out['primary']['gates']['adjacent_sign'] and not out['advances']
    cells['CONTINUATION', 3., 3] = []
    out = g.evaluate(cells, sessions, {}, start, end, None)
    assert not out['primary']['gates']['common_event_sign']
    assert out['primary']['common_events']['eligible_h1_missing_longer_horizon'] == 240


def test_cell_each_gate_rejects_its_failure(monkeypatch):
    monkeypatch.setattr(g, 'RESAMPLES', 100)
    start, end = date(2020, 1, 1), date(2020, 12, 31)
    good = [trade(i * 3) for i in range(100)]
    assert all(g.cell_report(good, [1] * 100, start, end, [])['gates'].values())
    assert not g.cell_report(good[:99], [1] * 99, start, end, [])['gates']['minimum_events']
    assert not g.cell_report(good, [1] * 100, start, end, [good[0]])['gates']['data_integrity']
    negative = [trade(i * 3, -1) for i in range(100)]
    gates = g.cell_report(negative, [0] * 100, start, end, [])['gates']
    assert not gates['positive_normal_and_doubled']
    assert not gates['positive_both_halves']
    assert not gates['five_event_removal_positive']
    assert not gates['net_interval_positive']
    assert not gates['raw_interval_nonzero']
    expensive = [trade(i * 3, 1) for i in range(100)]
    for t in expensive:
        t.spread_r = 2
    assert not g.cell_report(expensive, [1] * 100, start, end, [])['gates']['positive_normal_and_doubled']
    concentrated = [trade(i * 3, 20 if i < 5 else -1) for i in range(100)]
    assert not g.cell_report(concentrated, [1] * 100, start, end, [])['gates']['five_event_removal_positive']


def test_event_removal_only_removes_profitable_events():
    trades = [trade(0, 1), trade(1, -2)]
    result = g.cell_report(trades, [1, 1], date(2020, 1, 1), date(2020, 12, 31), [])
    assert result['net_r_without_best_events']['5'] == -2


def test_common_event_results_are_reported_for_each_threshold_and_mode(monkeypatch):
    monkeypatch.setattr(g, '_q', lambda t, session, h, data: session['q'])
    monkeypatch.setattr(g, 'RESAMPLES', 10)
    ts = [trade(0), trade(1)]
    cells = {(m, float(k), h): list(ts) for m in g.MODES for k in (2, 3, 4)
             for h in (1, 2, 3)}
    sessions = {cell: {g.key(t): {'q': 0.1, 'three_hour_eligible': True} for t in ts}
                for cell in cells}
    out = g.evaluate(cells, sessions, {}, date(2020, 1, 1), date(2020, 12, 31), None)
    for report in out['cells'].values():
        assert report['common_events']['count'] == 2
        assert not report['gates']['common_event_sign']


def test_primary_breadth_and_minimum_per_symbol(monkeypatch):
    monkeypatch.setattr(g, '_q', lambda t, session, h, data: session['q'])
    monkeypatch.setattr(g, 'RESAMPLES', 10)
    ts = [trade(i * 10, symbol=s) for i in range(19)
          for s in ('XAUUSD', 'GBPUSD', 'GBPJPY')]
    cells = {(m, float(k), h): list(ts) for m in g.MODES for k in (2, 3, 4)
             for h in (1, 2, 3)}
    sessions = {cell: {g.key(t): {'q': 0.1} for t in ts} for cell in cells}
    out = g.evaluate(cells, sessions, {}, date(2020, 1, 1), date(2020, 12, 31), None)
    assert out['primary']['gates']['symbol_breadth']
    assert not out['primary']['gates']['supporting_symbol_minimum']
    for cell in sessions:
        for t in ts:
            if t.symbol == 'GBPJPY':
                sessions[cell][g.key(t)]['q'] = -1
    out = g.evaluate(cells, sessions, {}, date(2020, 1, 1), date(2020, 12, 31), None)
    assert not out['primary']['gates']['symbol_breadth']


def test_cell_reports_breadth_gates(monkeypatch):
    monkeypatch.setattr(g, '_q', lambda t, session, h, data: session['q'])
    monkeypatch.setattr(g, 'RESAMPLES', 10)
    ts = [trade(i * 10, symbol=s) for i in range(20)
          for s in ('XAUUSD', 'GBPUSD', 'GBPJPY')]
    cells = {(m, float(k), h): list(ts) for m in g.MODES for k in (2, 3, 4)
             for h in (1, 2, 3)}
    sessions = {cell: {g.key(t): {'q': 0.1} for t in ts} for cell in cells}
    out = g.evaluate(cells, sessions, {}, date(2020, 1, 1), date(2020, 12, 31), None)
    assert out['cells']['CONTINUATION/2/1']['gates']['symbol_breadth']
    assert out['cells']['CONTINUATION/2/1']['gates']['supporting_symbol_minimum']


def test_missing_raw_outcomes_are_not_sufficient_evidence(monkeypatch):
    monkeypatch.setattr(g, '_q', lambda t, session, h, data: None)
    monkeypatch.setattr(g, 'RESAMPLES', 10)
    ts = [trade(i * 2) for i in range(100)]
    cells = {(m, float(k), h): list(ts) for m in g.MODES for k in (2, 3, 4)
             for h in (1, 2, 3)}
    sessions = {cell: {g.key(t): {'three_hour_eligible': True} for t in ts} for cell in cells}
    out = g.evaluate(cells, sessions, {}, date(2020, 1, 1), date(2020, 12, 31), None)
    common = out['cells']['CONTINUATION/3/1']['common_events']
    assert common['status'] == 'missing raw outcomes'
    assert not out['cells']['CONTINUATION/3/1']['gates']['common_event_sign']


def test_cooldown_suppression_count_distinguishes_other_absences():
    a, b, c = trade(0), trade(0), trade(1)
    b.entry_time = a.entry_time + timedelta(hours=1)
    c.entry_time = a.entry_time + timedelta(days=1)
    assert g.cooldown_suppressed([a, b, c], {g.key(t) for t in (a, b, c)},
                                 {1: [a, b, c], 2: [a], 3: [a]}) == 1


def test_integrity_checks_scheduled_horizon_after_early_stop():
    import numpy as np

    from backtester.analytics.entry_screen import M1Data

    t = trade(0)
    t.exit_time = t.entry_time + timedelta(minutes=10)
    base = int(t.entry_time.timestamp())
    times = np.arange(base, base + 59 * 60, 60)
    o = np.linspace(100, 101, len(times))
    data = M1Data(times, o, o + 1, o - 1, o)
    assert g.scheduled_integrity_failures([t], data, 1) == [t]


def test_integrity_accepts_complete_horizon_and_rejects_stale_run():
    import numpy as np

    from backtester.analytics.entry_screen import M1Data

    t = trade(0)
    base = int(t.entry_time.timestamp())
    times = np.arange(base, base + 60 * 60, 60)
    prices = np.linspace(100, 101, len(times))
    data = M1Data(times, prices, prices + 1, prices - 1, prices)
    assert g.scheduled_integrity_failures([t], data, 1) == []
    flat = np.full(len(times), 100.)
    data = M1Data(times, flat, flat, flat, flat)
    assert g.scheduled_integrity_failures([t], data, 1) == [t]


def test_negative_primary_q_maps_to_reversal(monkeypatch):
    monkeypatch.setattr(g, '_q', lambda t, session, h, data: -0.1)
    monkeypatch.setattr(g, 'RESAMPLES', 10)
    ts = [trade(i * 4, symbol=s) for i in range(80)
          for s in ('XAUUSD', 'GBPUSD', 'GBPJPY')]
    cells = {(m, float(k), h): list(ts) for m in g.MODES for k in (2, 3, 4)
             for h in (1, 2, 3)}
    sessions = {cell: {g.key(t): {'three_hour_eligible': True} for t in ts}
                for cell in cells}
    out = g.evaluate(cells, sessions, {}, date(2020, 1, 1), date(2020, 12, 31), None)
    assert out['primary']['mapped_mode'] == 'REVERSAL'
    assert out['advances']
