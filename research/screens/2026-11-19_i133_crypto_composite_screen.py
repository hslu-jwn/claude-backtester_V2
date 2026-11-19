"""I-133 weekly crypto composite screen; rules: knowledge/ideas.md, I-133 A1-A4."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "i78", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py"
)
i78 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i78)

START = pd.Timestamp("2020-05-04")
TEST_START = pd.Timestamp("2024-01-01")
COST, CAP, MIN_NAMES = 20.0, 5000.0, 40


def weeks_table(k, fund, start, signals=True):
    """Build eligible weeks; power does not inspect either signal."""
    weeks = {}
    for m in i78.mondays(k):
        if m < start:
            continue
        w = i78.week_rows(k, fund, m)
        if w.empty:
            continue
        cutoff = m - pd.Timedelta(days=7)
        ok = [s in fund and len(fund[s]) > 0 and fund[s].index[0] <= cutoff for s in w.sym]
        w = w.loc[ok].copy()
        if signals:
            w = w.dropna(subset=["flow"]).copy()
            w["sig"] = [fund[s][(fund[s].index > cutoff) & (fund[s].index <= m)].sum() for s in w.sym]
        if len(w) < MIN_NAMES:
            continue
        if signals:
            flow_sd, carry_sd = w.flow.std(ddof=0), w.sig.std(ddof=0)
            if not np.isfinite(flow_sd) or not np.isfinite(carry_sd) or flow_sd == 0 or carry_sd == 0:
                continue
            w["z_flow"] = (w.flow - w.flow.mean()) / flow_sd
            w["z_carry"] = -(w.sig - w.sig.mean()) / carry_sd
            w["composite"] = (w.z_flow + w.z_carry) / 2
        weeks[m] = w
    return weeks


def legs(w, column):
    ordered = w.sort_values([column, "sym"], kind="mergesort")
    n = len(ordered) // 5
    return ordered.iloc[-n:], ordered.iloc[:n]


def gross(w, column="composite", cap=None):
    long, short = legs(w, column)
    lr, sr = long.ret, short.ret
    if cap is not None:
        lr, sr = lr.clip(-cap, cap), sr.clip(-cap, cap)
    return lr.mean() - sr.mean() - long.fund.mean() + short.fund.mean()


def gates(net, capped):
    mean = net.mean()
    h = len(net) // 2
    halves = (net.iloc[:h].mean(), net.iloc[h:].mean())
    checks = {
        "net > 0": mean > 0,
        "t >= 3.0": i78.tstat(net) >= 3.0,
        "both halves >= 25% of mean": all(x >= 0.25 * mean for x in halves),
        "doubled cost > 0": (net - COST).mean() > 0,
        "without 2 best > 0": net.drop(net.nlargest(2).index).mean() > 0,
        "M6 capped sign and half mean": capped.mean() > 0 and capped.mean() >= 0.5 * mean,
    }
    return checks, halves


def turnover(weeks, column):
    previous = None
    values = []
    for w in weeks.values():
        long, short = legs(w, column)
        current = (set(long.sym), set(short.sym))
        if previous is not None:
            values.append(sum(len(now - old) for now, old in zip(current, previous, strict=True))
                          / sum(len(now) for now in current))
        previous = current
    return np.mean(values)


def selfcheck():
    w = pd.DataFrame({"sym": list("ABCDE"), "flow": [1, 2, 3, 4, 5],
                      "sig": [5, 4, 3, 2, 1], "ret": [10, 20, 30, 40, 50],
                      "fund": [1, 2, 3, 4, 5]})
    w["z_flow"] = (w.flow - w.flow.mean()) / w.flow.std(ddof=0)
    w["z_carry"] = -(w.sig - w.sig.mean()) / w.sig.std(ddof=0)
    w["composite"] = (w.z_flow + w.z_carry) / 2
    assert np.allclose(w.composite, [-np.sqrt(2), -1 / np.sqrt(2), 0, 1 / np.sqrt(2), np.sqrt(2)])
    long, short = legs(w, "composite")
    assert long.sym.tolist() == ["E"] and short.sym.tolist() == ["A"]
    assert gross(w) == 50 - 10 - 5 + 1 == 36
    print("selfcheck OK")


def power(weeks):
    rng = np.random.default_rng(1)
    sds = []
    for _ in range(200):
        spreads = []
        for w in weeks.values():
            r = rng.permutation(w.ret.to_numpy())
            n = len(r) // 5
            spreads.append(r[-n:].mean() - r[:n].mean())
        sds.append(np.std(spreads, ddof=1))
    sd = np.mean(sds)
    se = sd / np.sqrt(len(weeks))
    print(f"POWER: weekly sd mean {sd:.1f} bp; weeks {len(weeks)}; se {se:.1f} bp; "
          f"net mean for t 3.0 {3 * se:.1f} bp/week")


def evaluate(weeks, test=False):
    idx = list(weeks)
    net = pd.Series([gross(w) - COST for w in weeks.values()], index=idx)
    eligible = [len(w) for w in weeks.values()]
    print(f"weeks {len(idx)}; eligible min / median / max {min(eligible)} / "
          f"{np.median(eligible):.1f} / {max(eligible)}")
    print(f"net {net.mean():+.1f} bp/week; t {i78.tstat(net):.2f}; "
          f"win {100 * (net > 0).mean():.1f}%; worst {net.min():+.1f}")
    if test:
        checks = {"net > 0": net.mean() > 0, "t >= 1.8": i78.tstat(net) >= 1.8,
                  "doubled cost > 0": (net - COST).mean() > 0}
        print(f"doubled cost {(net - COST).mean():+.1f}; failed gates "
              f"{[k for k, v in checks.items() if not v] or 'none'}; "
              f"{'PASSED' if all(checks.values()) else 'KILLED'}; capped at UNPROVEN-POSITIVE (not blind)")
        return
    capped = pd.Series([gross(w, cap=CAP) - COST for w in weeks.values()], index=idx)
    checks, halves = gates(net, capped)
    ratios = [x / net.mean() if net.mean() != 0 else np.nan for x in halves]
    print(f"halves {halves[0]:+.1f} / {halves[1]:+.1f}; ratios {ratios[0]:.2f} / {ratios[1]:.2f}; "
          f"doubled {(net - COST).mean():+.1f}; without 2 best {net.drop(net.nlargest(2).index).mean():+.1f}; "
          f"M6 capped {capped.mean():+.1f}")
    failed = [k for k, v in checks.items() if not v]
    print(f"{'KILLED' if failed else 'PASSED'}; failed gates: {failed or 'none'}")
    flow = pd.Series([i78.spread(w, 'flow')[0] - COST for w in weeks.values()], index=idx)
    carry = pd.Series([gross(w, 'z_carry') - COST for w in weeks.values()], index=idx)
    rng = np.random.default_rng(3)
    placebo = []
    disagreement = []
    for w in weeks.values():
        p = w.copy()
        p['composite'] = (p.z_flow + rng.permutation(p.z_carry.to_numpy())) / 2
        placebo.append(gross(p) - COST)
        long, _ = legs(w, 'composite')
        _, carry_short = legs(w, 'z_carry')
        disagreement.append(len(set(long.sym) & set(carry_short.sym)) / len(long))
    print(f"correlation flow {net.corr(flow):+.2f}; carry {net.corr(carry):+.2f}; "
          f"turnover composite {turnover(weeks, 'composite'):.3f}, flow {turnover(weeks, 'flow'):.3f}")
    print(f"carry permutation placebo net {np.mean(placebo):+.1f}, t {i78.tstat(placebo):.2f}; "
          f"composite longs in carry shorts mean share {np.mean(disagreement):.3f}; "
          f"weeks with disagreement {sum(x > 0 for x in disagreement)} / {len(disagreement)}")
    passes = 0
    for seed in range(200):
        rng = np.random.default_rng(seed)
        shuffled, capped_shuffled = [], []
        for w in weeks.values():
            p = w.copy()
            p['composite'] = rng.permutation(p.composite.to_numpy())
            shuffled.append(gross(p) - COST)
            capped_shuffled.append(gross(p, cap=CAP) - COST)
        checks, _ = gates(pd.Series(shuffled), pd.Series(capped_shuffled))
        passes += all(checks.values())
    print(f"shuffled-label control: {passes / 200:.1%} pass (target <= 5%)")


def main(argv):
    if argv == ['--selfcheck']:
        selfcheck()
        return
    if len(argv) != 1 or argv[0] not in ('power', 'run', 'test'):
        raise SystemExit('usage: screen.py --selfcheck | power | run | test')
    mode = argv[0]
    if mode == 'test':
        i78.END = pd.Timestamp('2026-10-31')
        k, fund = i78.load(roots=(i78.ROOT, Path('data/cache/binance_wide_test')))
    else:
        k, fund = i78.load()
    weeks = weeks_table(k, fund, TEST_START if mode == 'test' else START, signals=mode != 'power')
    if len(weeks) < 3:
        raise SystemExit('Fewer than three eligible weeks; cannot evaluate screen.')
    if mode == 'power':
        power(weeks)
    else:
        evaluate(weeks, test=mode == 'test')


if __name__ == '__main__':
    main(sys.argv[1:])
