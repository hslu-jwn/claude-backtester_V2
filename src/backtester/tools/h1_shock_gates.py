"""H1 shock rejection gates. Spec: strategy-h1-shock.md > Gates."""
from __future__ import annotations

import argparse
import csv
import json
import math
from bisect import bisect_left
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from backtester.analytics.records import read_trades
from backtester.data.sources import SymbolSources
from backtester.tools.alternating_path_gates import (
    STRESSES,
    block_indices,
    halves,
    integrity_failures,
    net,
)
from backtester.tools.entry_screen import load_m1
from backtester.tools.timed_hold_gates import BLOCK, RESAMPLES, SEED

MODES = ('CONTINUATION', 'REVERSAL')
SYMBOLS = ('XAUUSD', 'GBPUSD', 'GBPJPY', 'NAS100', 'US500')
MIN_EVENTS, MIN_SYMBOL_EVENTS, MIN_SYMBOLS = 100, 20, 3


def key(t):
    return t.symbol, t.entry_time


def common_keys(cells):
    return set.intersection(*(set(map(key, cells[h])) for h in (1, 2, 3)))


def scheduled_integrity_failures(trades, data, hours):
    """Check the scheduled horizon even when a safety stop ended the trade early."""
    bad = []
    for t in trades:
        end = t.entry_time + timedelta(hours=hours)
        interval = SimpleNamespace(entry_time=t.entry_time, exit_time=end)
        lo = np.searchsorted(data.open_s, int(t.entry_time.timestamp()))
        hi = np.searchsorted(data.open_s, int(end.timestamp()))
        times = data.open_s[lo:hi]
        prices = data.open[lo:hi]
        flat = ((prices == data.high[lo:hi]) & (prices == data.low[lo:hi]) &
                (prices == data.close[lo:hi]))
        stale = run = 0
        for i in range(len(times)):
            if flat[i]:
                run = run + 1 if i and flat[i - 1] and times[i] - times[i - 1] == 60 and prices[i] == prices[i - 1] else 1
                stale = max(stale, run)
            else:
                run = 0
        if (integrity_failures([interval], data, max_gap_minutes=5) or stale >= 15 or
                np.any(np.diff(times) <= 0)):
            bad.append(t)
    return bad


def cooldown_suppressed(h1, eligible, cells):
    """Count eligible H1 events absent while a longer cell's cooldown was active."""
    keys = {h: set(map(key, cells[h])) for h in (2, 3)}
    entries = {h: defaultdict(list) for h in (2, 3)}
    for h in (2, 3):
        for t in cells[h]:
            entries[h][t.symbol].append(t.entry_time)
        for times in entries[h].values():
            times.sort()

    def active(t, h):
        times = entries[h][t.symbol]
        i = bisect_left(times, t.entry_time) - 1
        return i >= 0 and t.entry_time < times[i] + timedelta(hours=h)

    return sum(
        1 for t in h1 if key(t) in eligible and any(
            key(t) not in keys[h] and active(t, h)
            for h in (2, 3)))


def same_sign(sign, values):
    return sign != 0 and all(v is not None and sign * v > 0 for v in values)


def clustered(trades, values):
    """UTC entry-day clusters; circular five-day block bootstrap of event-weighted mean."""
    groups = defaultdict(list)
    for t, v in zip(trades, values, strict=True):
        if v is not None and math.isfinite(v):
            groups[t.entry_time.date()].append(v)
    # One day cannot estimate day-clustered uncertainty.
    if len(groups) < 2:
        return None
    sums = np.array([sum(groups[d]) for d in sorted(groups)])
    counts = np.array([len(groups[d]) for d in sorted(groups)])
    rng = np.random.default_rng(SEED)
    n = len(sums)
    samples = np.empty(RESAMPLES)
    for i in range(RESAMPLES):
        idx = block_indices(n, BLOCK, rng.integers(0, n, size=math.ceil(n / BLOCK)))
        samples[i] = sums[idx].sum() / counts[idx].sum()
    return {'events': int(counts.sum()), 'clusters': n, 'mean': float(sums.sum() / counts.sum()),
            'lower_2_5': float(np.quantile(samples, .025)),
            'upper_97_5': float(np.quantile(samples, .975))}


def cell_report(trades, q, start, end, failures):
    """Cell-level numbers; missing raw outcomes always fail raw-sign inference."""
    n = len(trades)
    stress = {s or 'normal': net(trades, s) for s in STRESSES}
    hs = [net(part) for part in halves(trades, start, end)]
    boot = clustered(trades, [t.r_net for t in trades])
    raw = clustered(trades, q)
    ordered = sorted(trades, key=lambda t: t.r_net, reverse=True)
    removed = {str(i): net(ordered) - sum(t.r_net for t in ordered[:i] if t.r_net > 0)
               for i in (1, 5)}
    # Timed-hold convention: positive normal and each individually doubled component.
    gates = {'positive_normal_and_doubled': all(v > 0 for v in stress.values()),
             'positive_both_halves': all(v > 0 for v in hs),
             'minimum_events': n >= MIN_EVENTS,
             'five_event_removal_positive': removed['5'] > 0,
             'net_interval_positive': boot is not None and boot['lower_2_5'] > 0,
             'raw_interval_nonzero': raw is not None and raw['events'] == n and
             (raw['lower_2_5'] > 0 or raw['upper_97_5'] < 0),
             'data_integrity': failures is None or len(failures) == 0}
    return {'events': n, 'net_r': stress, 'halves_net_r': hs, 'raw_q': raw,
            'net_r_interval': boot, 'net_r_without_best_events': removed,
            'integrity_failures': None if failures is None else len(failures), 'gates': gates}


def _q(t, session, h, data):
    if session is None or data is None:
        return None
    signal = int(t.entry_time.timestamp())
    points = [signal - 60, signal + h * 3600 - 60]
    idx = np.searchsorted(data.open_s, points)
    if any(i >= len(data.open_s) or data.open_s[i] != p for i, p in zip(idx, points, strict=True)):
        return None
    a, b = (float(data.close[i]) for i in idx)
    r = session.get('event_return')
    if not r or not math.isfinite(r) or not (math.isfinite(a) and math.isfinite(b) and a > 0 and b > 0):
        return None
    return math.copysign(1, r) * math.log(b / a)


def evaluate(cells, sessions, data, start, end, failures):
    reports = {}
    qs = {}
    for cell, trades in cells.items():
        mode, k, h = cell
        q = [_q(t, sessions[cell].get(key(t)), h, data.get(t.symbol)) for t in trades]
        qs[cell] = q
        label = f'{mode}/{k:g}/{h}'
        report = cell_report(trades, q, start, end, None if failures is None else failures[cell])
        report['direction'] = {}
        report['clock_hour'] = {}
        for t in trades:
            record = sessions[cell].get(key(t), {})
            event_return = record.get('event_return')
            direction = 'up' if event_return and event_return > 0 else 'down' if event_return else 'unknown'
            hour = str(record.get('clock_hour', 'unknown'))
            for split, value in ((report['direction'], direction), (report['clock_hour'], hour)):
                bucket = split.setdefault(value, {'events': 0, 'net_r': 0.0})
                bucket['events'] += 1
                bucket['net_r'] += t.r_net
        march = [t for t in trades if t.entry_time.year == 2020 and t.entry_time.month == 3]
        report['march_2020'] = {'events': len(march), 'net_r': net(march)}
        report['stop_count'] = sum(t.exit_reason.lower() == 'stop_loss' for t in trades if hasattr(t, 'exit_reason'))
        report['symbols'] = {s: {'events': len(part), 'net_r': net(part),
                                'gross_r': sum(t.r_gross for t in part),
                                'raw_q_events': len(vals),
                                'mean_raw_q': (sum(vals) / len(vals) if vals else None)}
                             for s in SYMBOLS
                             for part in [[t for t in trades if t.symbol == s]]
                             for vals in [[v for t, v in zip(trades, q, strict=True)
                                           if t.symbol == s and v is not None]]}
        reports[label] = report
    for (mode, k, h), trades in cells.items():
        cell = (mode, k, h)
        common = common_keys({j: cells[mode, k, j] for j in (1, 2, 3)})
        values = [v for t, v in zip(trades, qs[cell], strict=True) if key(t) in common]
        mean = sum(values) / len(values) if values and all(v is not None for v in values) else None
        all_q = qs[cell]
        sign = int(np.sign(sum(all_q))) if all_q and all(v is not None for v in all_q) else 0
        h1 = (mode, k, 1)
        flagged = {key(t) for t in cells[h1]
                   if sessions[h1].get(key(t), {}).get('three_hour_eligible')}
        report = reports[f'{mode}/{k:g}/{h}']
        supporting = [s for s, v in report['symbols'].items()
                      if v['mean_raw_q'] is not None and sign * v['mean_raw_q'] > 0]
        report['supporting_symbols'] = supporting
        report['gates']['symbol_breadth'] = (len(supporting) >= MIN_SYMBOLS and
            all(report['symbols'][s]['gross_r'] > 0 and
                report['symbols'][s]['raw_q_events'] == report['symbols'][s]['events']
                for s in supporting))
        report['gates']['supporting_symbol_minimum'] = (len(supporting) >= MIN_SYMBOLS and
            all(report['symbols'][s]['events'] >= MIN_SYMBOL_EVENTS for s in supporting))
        report['common_events'] = {'count': len(common), 'mean_raw_q': mean,
                                   'eligible_h1_missing_longer_horizon': len(flagged - common),
                                   'cooldown_suppressed': cooldown_suppressed(
                                       cells[h1], flagged, {j: cells[mode, k, j] for j in (1, 2, 3)}),
                                   'status': ('not enough evidence' if len(common) < MIN_EVENTS else
                                              'missing raw outcomes' if mean is None else 'ok')}
        report['gates']['common_event_sign'] = (len(common) >= MIN_EVENTS and
                                                len(values) == len(common) and same_sign(sign, [mean]))
    # Continuation direction supplies raw q independent of response mode.
    primary = ('CONTINUATION', 3., 1)
    raw = reports['CONTINUATION/3/1']['raw_q']
    primary_q = qs[primary]
    sign = (int(np.sign(sum(primary_q))) if primary_q and
            all(v is not None for v in primary_q) else 0)
    mode = 'CONTINUATION' if sign > 0 else 'REVERSAL' if sign < 0 else None
    selected = (mode, 3., 1)
    chosen = reports.get(f'{mode}/3/1')
    adjacency = {}
    for k, h in ((2., 1), (4., 1), (3., 2)):
        row = reports[f'CONTINUATION/{k:g}/{h}']['raw_q']
        adjacency[f'{k:g}/{h}'] = row['mean'] if row and row['events'] == len(cells['CONTINUATION', k, h]) else None
    common = common_keys({h: cells.get((mode, 3., h), []) for h in (1, 2, 3)}) if mode else set()
    common_q = ([v for t, v in zip(cells[selected], qs[selected], strict=True)
                 if key(t) in common] if mode else [])
    common_mean = sum(common_q) / len(common_q) if common_q and all(v is not None for v in common_q) else None
    flagged = {key(t) for t in cells.get(selected, []) if sessions[selected].get(key(t), {}).get('three_hour_eligible')}
    suppressed = len(flagged - common)
    support = [] if chosen is None else [s for s, v in chosen['symbols'].items()
                                         if v['mean_raw_q'] is not None and sign * v['mean_raw_q'] > 0]
    gates = dict(chosen['gates']) if chosen else {name: False for name in cell_report([], [], start, end, [])['gates']}
    gates['raw_interval_nonzero'] = raw is not None and raw['events'] == len(cells[primary]) and (raw['lower_2_5'] > 0 or raw['upper_97_5'] < 0)
    gates['symbol_breadth'] = (len(support) >= MIN_SYMBOLS and
                               all(chosen['symbols'][s]['gross_r'] > 0 and
                                   chosen['symbols'][s]['raw_q_events'] == chosen['symbols'][s]['events']
                                   for s in support))
    gates['supporting_symbol_minimum'] = len(support) >= MIN_SYMBOLS and all(chosen['symbols'][s]['events'] >= MIN_SYMBOL_EVENTS for s in support)
    gates['adjacent_sign'] = same_sign(sign, adjacency.values())
    gates['common_event_sign'] = len(common) >= MIN_EVENTS and len(common_q) == len(common) and same_sign(sign, [common_mean])
    gates['either_mode_both_halves'] = any(all(x > 0 for x in reports[f'{m}/3/1']['halves_net_r']) for m in MODES)
    return {'cells': reports, 'primary': {'raw_q': raw, 'mapped_mode': mode,
            'adjacent_raw_q': adjacency, 'supporting_symbols': support,
            'common_events': {'count': len(common), 'mean_raw_q': common_mean,
                              'eligible_h1_missing_longer_horizon': suppressed,
                              'cooldown_suppressed': cooldown_suppressed(
                                  cells[selected], flagged, {h: cells[mode, 3., h] for h in (1, 2, 3)}) if mode else 0,
                              'status': ('not enough evidence' if len(common) < MIN_EVENTS else
                                         'missing raw outcomes' if common_mean is None else 'ok')},
            'gates': gates}, 'advances': all(gates.values())}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--skip-integrity', action='store_true')
    args = parser.parse_args(argv)
    with (args.folder / 'variants.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    cells, sessions = {}, {}
    for row in rows:
        cell = (row['set.response_mode'], float(row['set.event_z_threshold']),
                int(float(row['set.holding_hours'])))
        if cell in cells:
            raise SystemExit(f'duplicate cell {cell} (family={row.get("family", "")})')
        folder = args.folder / 'variants' / row['variant_id']
        cells[cell] = read_trades(folder)
        path = folder / 'sessions.json'
        records = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        sessions[cell] = {(symbol, datetime.fromisoformat(r['signal_time'])): r
                          for symbol, entries in records.items() for r in entries
                          if r.get('signal_time') and not r.get('skipped')}
    expected = {(m, float(k), h) for m in MODES for k in (2, 3, 4) for h in (1, 2, 3)}
    if set(cells) != expected:
        raise SystemExit('expected exactly the 18 declared H1 shock cells')
    settings = next(args.folder.glob('variants/*/settings.json'))
    run = json.loads(settings.read_text(encoding='utf-8'))['run']
    start, end = date.fromisoformat(run['start']), date.fromisoformat(run['end'])
    sources = SymbolSources({s: Path(p) for s, p in run['cache_dirs'].items()})
    # Forward closes are needed for raw q even when the integrity check is skipped.
    data = {s: load_m1(s, sources, start, end + timedelta(days=1)) for s in run['symbols']}
    failures = None
    if not args.skip_integrity:
        failures = {}
        for cell, trades in cells.items():
            bad = []
            for symbol, m1 in data.items():
                mine = [t for t in trades if t.symbol == symbol]
                bad.extend(scheduled_integrity_failures(mine, m1, cell[2]))
            # Session defects include stale runs and the scheduled exit after an early stop.
            for t in trades:
                record = sessions[cell].get(key(t))
                if (record is None or record.get('integrity_failed') or record.get('defects')) and t not in bad:
                    bad.append(t)
            failures[cell] = bad
    result = evaluate(cells, sessions, data, start, end, failures)
    result['period'] = {'start': str(start), 'end': str(end)}
    result['skipped_integrity'] = args.skip_integrity
    result['trial_count'] = len(cells)
    result['unavailable_diagnostics'] = {
        'same_clock_non_event_and_shuffled_signs':
            'not computed: trades and session records do not contain non-event returns or shuffled outcomes',
    }
    result['settings'] = {'min_events': MIN_EVENTS, 'min_symbol_events': MIN_SYMBOL_EVENTS,
                          'min_symbols': MIN_SYMBOLS, 'max_gap_minutes': 5,
                          'half_split': 'UTC period midpoint, by exit time',
                          'cluster_date': 'UTC entry date',
                          'skipped_integrity_gate': 'passes by convention when skipped',
                          'bootstrap': {'block_dates': BLOCK, 'resamples': RESAMPLES, 'seed': SEED}}
    (args.folder / 'gates.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print('advances' if result['advances'] else 'rejected', result['primary']['gates'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
